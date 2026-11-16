"""Guardian preparations: durable safe results, explicit media consent, recoverable failures.

Background work is local to ONE server process. On process restart unfinished
jobs become interrupted; no paid call or original-file upload is auto-retried.
"""
import asyncio
import hashlib
import json
import tempfile
import time
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field, model_validator
from pydantic_core import PydanticCustomError
from starlette.datastructures import Headers

from app import local_access as accounts
from app.models import AnalysisPackageInput, AssetInput, LectureCreate, LectureSnapshot, VideoLinkInput, AgentTurnInput
from app.runtime import INSTANCE

def authorize(request: Request):
    from app.extension_access import current
    user = current(request)
    if user is None:
        raise HTTPException(401, '확장 프로그램에서 다시 로그인해 주세요.')
    if user['role'] != 'guardian':
        raise HTTPException(403, '보호자만 사용할 수 있습니다.')


router = APIRouter(prefix='/extension/v1/guardian', dependencies=[Depends(authorize)])
MAX_TEXT = 1_000_000


class TextAsset(BaseModel):
    model_config = {'extra': 'forbid'}
    name: str = Field(min_length=1, max_length=240)
    kind: Literal['subtitle', 'passage']
    content: str = Field(min_length=1, max_length=300_000)


class LocalPlayback(BaseModel):
    model_config = {'extra': 'forbid'}
    name: str = Field(min_length=1, max_length=240)
    size_bytes: int = Field(gt=0, le=9007199254740991)


class Prepare(BaseModel):
    model_config = {'extra': 'forbid'}
    title: str = Field(min_length=1, max_length=160)
    subject: str = Field(default='일반', min_length=1, max_length=80)
    problem_mode: bool = True
    source_label: str = Field(default='', max_length=120)
    preferred_mode: Literal['auto', 'board', 'passage', 'slides'] = 'auto'
    assets: list[TextAsset] = Field(default_factory=list, max_length=20)
    analysis: AnalysisPackageInput | None = None
    link: VideoLinkInput | None = None
    local_file: LocalPlayback | None = None

    @model_validator(mode='after')
    def bounded_input(self):
        if not self.assets and self.analysis is None and self.link is None and self.local_file is None:
            raise ValueError('준비할 자료를 선택해 주세요.')
        if self.local_file and self.link:
            raise ValueError('로컬 파일과 영상 링크는 별도 강의로 등록하세요.')
        if len(self.model_dump_json()) > MAX_TEXT:
            raise PydanticCustomError('preparation_text_limit','입력 정보와 자료 전체는 100만 자 이하여야 합니다. 파일 수나 지문 길이를 줄이거나 여러 강의로 나누어 준비하세요.')
        return self


def recover(con):
    from app.analysis_provenance import read_status, record_status
    for row in con.execute("SELECT session_id FROM preparations WHERE instance<>? AND state IN ('queued','running')", (INSTANCE,)).fetchall():
        status = read_status(con, row['session_id'])
        if status.state=='analyzing':record_status(row['session_id'], 'failed', status.provider, con=con)
    con.execute('''UPDATE preparations SET state='interrupted', message=?, updated=?
        WHERE instance<>? AND state IN ('queued','running')''',
        ('서버가 재시작되어 중단됐습니다. 자료를 다시 선택하고 준비를 요청하세요. 자동으로 재분석하지 않습니다.', time.time(), INSTANCE))


def own(con, guardian, ident):
    row = con.execute('SELECT * FROM preparations WHERE id=? AND guardian=?', (ident, guardian)).fetchone()
    if not row:
        raise HTTPException(404, '본인의 준비 작업을 찾을 수 없습니다.')
    return row


def public(row, detail=False, con=None):
    from app.analysis_provenance import read_status
    if con is None:
        with accounts.db() as opened:return public(row, detail, opened)
    result = {key: row[key] for key in ('id', 'session_id', 'title', 'subject', 'source_kind', 'state', 'message', 'updated')}
    result['playback'] = json.loads(row['playback'])
    result['analysis_status'] = read_status(con, row['session_id']).model_dump(mode='json')
    if detail and row['state'] == 'completed':
        result['snapshot'] = json.loads(row['snapshot'])
    return result


def completed_snapshot(con, guardian, session_id):
    row = con.execute('SELECT * FROM preparations WHERE session_id=? AND guardian=?', (session_id, guardian)).fetchone()
    if row is None:
        return None
    if row['state'] != 'completed' or not row['snapshot']:
        raise HTTPException(409, '준비 완료된 자료만 배정할 수 있습니다.')
    from app.analysis_provenance import read_status
    snapshot=LectureSnapshot.model_validate_json(row['snapshot'])
    return snapshot.model_copy(update={'analysis_status':read_status(con,session_id)})


def new_job(request, title, subject, problem_mode, source_kind, source_label='', preferred_mode='auto'):
    from app.main import agent
    user = accounts.require(request, 'guardian')
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        recover(con)
        active = con.execute("SELECT guardian FROM preparations WHERE state IN ('queued','running')").fetchall()
        if len(active) >= 4 or sum(row['guardian'] == user['id'] for row in active) >= 2:
            raise HTTPException(429, '진행 중인 준비 작업을 완료한 뒤 다시 요청해 주세요.')
        session = agent.create_session(LectureCreate(title=title, subject=subject,
            problem_mode=problem_mode, preferred_mode=preferred_mode, source_label=source_label.strip() or {'materials': '보호자가 등록한 학습자료',
            'link': '보호자가 등록한 링크·자료', 'video': '동의한 파일 실제 분석 · 원본 미보관',
            'local': '로컬 재생용 등록 · 원본 미전송 · 영상 분석 미실행'}[source_kind]))
        ident = uuid4().hex
        from app.analysis_provenance import record_status
        record_status(session.session_id, 'not_run', con=con)
        con.execute('INSERT INTO owners VALUES(?,?)', (session.session_id, user['id']))
        con.execute('INSERT INTO preparations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
            (ident, user['id'], session.session_id, title, subject, source_kind, 'queued',
             '준비 요청을 접수했습니다.', None, '{}', INSTANCE, time.time()))
        return public(own(con, user['id'], ident), con=con)


def update(ident, state, message, snapshot=None, playback=None):
    with accounts.db() as con:
        con.execute('''UPDATE preparations SET state=?,message=?,snapshot=?,playback=?,updated=?
            WHERE id=? AND instance=?''', (state, message, snapshot.model_dump_json() if snapshot else None,
            json.dumps(playback or {}, ensure_ascii=False), time.time(), ident, INSTANCE))


async def run(ident, session_id, request, payload=None, video=None, video_fields=None):
    from app import main
    update(ident, 'running', '자료를 처리하고 있습니다. 화면을 닫아도 서버에서 계속 처리합니다.')
    playback = {'kind': 'none'}
    try:
        if payload:
            update(ident, 'running', '자막·지문과 분석 자료를 등록하고 있습니다.')
            for asset in payload.assets:
                main.agent.register_asset(session_id, AssetInput(asset_id=uuid4().hex, name=asset.name,
                    kind=asset.kind, content_text=asset.content, size_bytes=len(asset.content.encode())))
            if payload.analysis is not None:
                main.agent.analyze(session_id, payload.analysis)
            if payload.local_file:
                playback = {'kind': 'local-reference', **payload.local_file.model_dump()}
            if payload.link:
                update(ident, 'running', '동의한 링크를 확인하고 있습니다. 실제 분석 요청 시 공급자 응답을 기다립니다.')
                result = await main.register_video_link(session_id, payload.link, request)
                if payload.link.request_analysis and result.analysis_status != 'completed':
                    raise HTTPException(503, result.message)
                if result.playback_kind in ('youtube', 'direct', 'external'):
                    from app.adapters.video_link import normalize_extension_video_link
                    source = normalize_extension_video_link(payload.link.url)
                    playback = {'kind': source.playback_kind, 'normalized_url': source.normalized_url}
        if video:
            update(ident, 'running', '동의한 원본을 임시 분석하고 있습니다. 완료 후 임시 사본을 삭제합니다.')
            asset_id = uuid4().hex
            main.agent.register_asset(session_id, AssetInput(asset_id=asset_id, name=video.filename,
                kind='video', media_type=video.content_type or 'application/octet-stream', size_bytes=video_fields['size_bytes']))
            await main.analyze_uploaded_video_file(session_id, request, video=video, asset_id=asset_id,
                rights_confirmed=True, cloud_analysis_consent=True)
            playback = {'kind': 'local-reference', 'name': video.filename,
                'size_bytes': video_fields['size_bytes'], 'sha256': video_fields['sha256']}
        update(ident, 'running', '분석 결과에 문제 보호·신뢰도 기준을 적용하고 학습자료를 구성합니다.')
        snapshot = main.agent.snapshot(session_id)
        playback_only = bool(payload and (payload.local_file or payload.link and not payload.link.request_analysis))
        if not (snapshot.passage or snapshot.transcript_segments or snapshot.safe_description_count or any(g.hold_notices for g in snapshot.visual_gaps)) and not playback_only:
            raise HTTPException(400, '배정할 수 있는 지문·자막·검증된 설명이 없습니다. 자료 형식과 분석 결과를 확인하세요.')
        message = '자료 준비를 완료했습니다. 확인 후 학생에게 배정하세요.'
        if playback_only and not (snapshot.passage or snapshot.transcript_segments or snapshot.safe_description_count):
            message = '원본 링크 등록을 완료했습니다. 영상 분석은 실행하지 않았습니다. 재생·단축키·기록을 이용하고, 내용 질문·자동 해설은 자료나 실제 분석 연결 후 사용하세요.'
            if payload.local_file:message = '로컬 파일 재생용 등록을 완료했습니다. 원본은 전송하지 않았고 영상 분석은 실행하지 않았습니다. 학생 기기에서 원본을 선택해 재생·명령·기록을 이용하세요.'
        update(ident, 'completed', message, snapshot, playback)
    except asyncio.CancelledError:
        from app.analysis_provenance import read_status,record_status
        with accounts.db() as con:
            status=read_status(con,session_id)
            if status.state=='analyzing':record_status(session_id,'failed',status.provider,con=con)
        update(ident, 'interrupted', '서버 종료로 중단됐습니다. 자료를 다시 선택해 준비하세요.')
        raise
    except HTTPException as error:
        # Messages from existing gates/cleanup are user-safe; never persist provider responses/codes.
        if video or payload and payload.link and payload.link.request_analysis:
            from app.analysis_provenance import record_status
            record_status(session_id, 'failed', 'gemini' if video or 'youtu' in payload.link.url else 'adapter')
        update(ident, 'failed', str(error.detail)[:1500])
    except Exception:
        if video or payload and payload.link and payload.link.request_analysis:
            from app.analysis_provenance import record_status
            record_status(session_id, 'failed', 'gemini' if video or 'youtu' in payload.link.url else 'adapter')
        update(ident, 'failed', '자료 준비에 실패했습니다. 자료와 서버 연결을 확인하고 다시 준비하세요.')
    finally:
        if video:
            await video.close()


@router.get('/preparations')
def listing(request: Request):
    user = accounts.require(request, 'guardian')
    with accounts.db() as con:
        recover(con)
        return [public(row, con=con) for row in con.execute('SELECT * FROM preparations WHERE guardian=? ORDER BY updated DESC', (user['id'],))]


@router.get('/preparations/{ident}')
def detail(ident: str, request: Request):
    user = accounts.require(request, 'guardian')
    with accounts.db() as con:
        recover(con)
        return public(own(con, user['id'], ident), detail=True, con=con)


@router.post('/preparations', status_code=202)
def create(payload: Prepare, request: Request, background: BackgroundTasks):
    accounts.require(request, 'guardian')
    # Validate rights, consent and URL before queuing any provider work.
    if payload.link:
        from app.adapters.video_link import normalize_video_link, UnsafeVideoLinkError
        if not payload.link.rights_confirmed or (payload.link.request_analysis and not payload.link.analysis_consent):
            raise HTTPException(400, '영상 이용 권한과 실제 분석 전송 동의를 확인해 주세요.')
        try:
            normalize_video_link(payload.link.url)
        except UnsafeVideoLinkError as error:
            raise HTTPException(400, str(error)) from None
    job = new_job(request, payload.title, payload.subject, payload.problem_mode, 'local' if payload.local_file else 'link' if payload.link else 'materials', payload.source_label, payload.preferred_mode)
    background.add_task(run, job['id'], job['session_id'], request, payload=payload)
    return job


@router.post('/preparations/video-file-analysis', status_code=202)
async def create_video(request: Request, background: BackgroundTasks, video: UploadFile = File(...),
    title: str = Form(..., min_length=1, max_length=160), subject: str = Form('일반', min_length=1, max_length=80),
    problem_mode: bool = Form(True), rights_confirmed: bool = Form(False),
    cloud_analysis_consent: bool = Form(False), source_label: str = Form('', max_length=120),
    preferred_mode: Literal['auto', 'board', 'passage', 'slides'] = Form('auto')):
    accounts.require(request, 'guardian')
    if not rights_confirmed or not cloud_analysis_consent:
        raise HTTPException(400, '원본 영상 임시 전송에 별도로 동의해야 실제 분석할 수 있습니다.')
    from app.core.demo_gate import server_gemini_key, MAX_VIDEO_BYTES
    if not server_gemini_key():
        raise HTTPException(503, '서버에 실제 분석 연결이 없습니다. 분석 공급자에게 원본을 전송하지 않았습니다.')
    # A bounded in-memory copy survives FastAPI closing the request's UploadFile.
    # Only the existing consented analyzer creates temporary disk/provider copies.
    memory = tempfile.SpooledTemporaryFile(max_size=MAX_VIDEO_BYTES + 1)
    try:
        size = 0
        fingerprint = hashlib.sha256()
        while chunk := await video.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_VIDEO_BYTES:
                raise HTTPException(413, '업로드 영상은 100MB 이하여야 합니다.')
            memory.write(chunk)
            fingerprint.update(chunk)
        if not size:
            raise HTTPException(400, '빈 영상은 분석할 수 없습니다.')
        memory.seek(0)
        copied = UploadFile(file=memory, filename=(video.filename or 'video.mp4')[:240],
            headers=Headers({'content-type': video.content_type or 'application/octet-stream'}))
        job = new_job(request, title, subject, problem_mode, 'video', source_label, preferred_mode)
        background.add_task(run, job['id'], job['session_id'], request, video=copied,
            video_fields={'size_bytes': size, 'sha256': fingerprint.hexdigest()})
        return job
    except BaseException:
        memory.close()
        raise
    finally:
        await video.close()


class Withdraw(BaseModel):
    students: list[str] = Field(min_length=1, max_length=50)


@router.post('/preparations/{ident}/agent-turn')
async def preview_chat(ident: str, payload: AgentTurnInput, request: Request):
    """Only the owner's persisted, filtered result can become model context."""
    user = accounts.require(request, 'guardian')
    with accounts.db() as con:
        row = own(con, user['id'], ident)
        snapshot = completed_snapshot(con, user['id'], row['session_id'])
    if not payload.analysis_consent:
        raise HTTPException(400, '준비된 학습자료를 학습 대화 공급자에게 전송하는 데 동의해 주세요.')
    if not (snapshot.passage or snapshot.transcript_segments or snapshot.safe_description_count):
        raise HTTPException(400, '내용 질문에는 자막·지문 또는 실제 분석 결과가 필요합니다. 링크 등록은 영상 분석이 아닙니다.')
    from app.adapters.gemini_agent import run_agent_turn, AgentTurnError, AgentUnavailableError
    from app.core.demo_gate import limiter, client_ip, analysis_timeout_seconds, server_gemini_key, DemoGateError
    if not server_gemini_key():
        raise HTTPException(503, '서버에 실제 학습 대화 연결이 없습니다. 준비된 자료를 확인해 주세요.')
    try:
        await asyncio.to_thread(limiter.consume, client_ip(request))
        return await asyncio.wait_for(run_agent_turn(snapshot, message=payload.message,
            current_time_ms=payload.current_time_ms), timeout=analysis_timeout_seconds())
    except DemoGateError as error:
        raise HTTPException(error.status_code, error.message) from None
    except asyncio.TimeoutError:
        raise HTTPException(504, '학습 대화 응답 시간이 초과되었습니다.') from None
    except (AgentTurnError, AgentUnavailableError) as error:
        raise HTTPException(502, str(error)) from None


class PublishPrepared(Withdraw):
    model_config = {'extra': 'forbid'}
    chat_consent: bool = False


@router.post('/preparations/{ident}/publish')
def publish(ident: str, payload: PublishPrepared, request: Request):
    user = accounts.require(request, 'guardian')
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = own(con, user['id'], ident)
        completed_snapshot(con, user['id'], row['session_id'])
        previous = con.execute('SELECT lecture FROM preparation_publications WHERE preparation=?', (ident,)).fetchone()
        if previous:
            assigned = {r[0] for r in con.execute('SELECT student FROM assignments WHERE lecture=?', (previous[0],))}
            if set(payload.students) != assigned:
                raise HTTPException(409, '이미 배정한 자료입니다. 강의 목록에서 배정을 수정하세요.')
            return {'id': previous[0], 'already_published': True}
        result = accounts.publish_prepared(con, user, accounts.Publish(title=row['title'], subject=row['subject'],
            students=payload.students, session_id=row['session_id'], playback=json.loads(row['playback']),
            ready=True, chat_consent=payload.chat_consent),extension=True)
        con.execute('INSERT INTO preparation_publications VALUES(?,?)', (ident, result['id']))
        identity = json.loads(row['playback'])
        if identity.get('kind') == 'local-reference':
            con.execute('INSERT INTO lecture_media VALUES(?,?)', (result['id'], json.dumps(identity)))
        return result


@router.post('/lectures/{ident}/withdraw')
def withdraw(ident: str, payload: Withdraw, request: Request):
    user = accounts.require(request, 'guardian')
    with accounts.db() as con:
        accounts.own(con, user, ident)
        assigned = {row[0] for row in con.execute('SELECT student FROM assignments WHERE lecture=?', (ident,))}
        if len(set(payload.students)) != len(payload.students) or not set(payload.students) <= assigned:
            raise HTTPException(400, '현재 배정된 학생을 선택해 주세요.')
        con.executemany('DELETE FROM assignments WHERE lecture=? AND student=?', [(ident, student) for student in payload.students])
        if not con.execute('SELECT 1 FROM assignments WHERE lecture=?', (ident,)).fetchone():
            con.execute('UPDATE lectures SET ready=0 WHERE id=?', (ident,))
    return {'ok': True}
