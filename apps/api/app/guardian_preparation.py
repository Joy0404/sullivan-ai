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
from pydantic import BaseModel, Field, SecretStr, model_validator
from starlette.datastructures import Headers

from app import local_access as accounts
from app.models import AnalysisPackageInput, AssetInput, LectureCreate, LectureSnapshot, VideoLinkInput
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


class Prepare(BaseModel):
    model_config = {'extra': 'forbid'}
    title: str = Field(min_length=1, max_length=160)
    subject: str = Field(default='일반', min_length=1, max_length=80)
    problem_mode: bool = True
    assets: list[TextAsset] = Field(default_factory=list, max_length=20)
    analysis: AnalysisPackageInput | None = None
    link: VideoLinkInput | None = None

    @model_validator(mode='after')
    def bounded_input(self):
        if not self.assets and self.analysis is None and self.link is None:
            raise ValueError('준비할 자료를 선택해 주세요.')
        if len(self.model_dump_json()) > MAX_TEXT:
            raise ValueError('한 번에 준비할 텍스트 자료는 100만 자 이하여야 합니다.')
        return self


def recover(con):
    con.execute('''UPDATE preparations SET state='interrupted', message=?, updated=?
        WHERE instance<>? AND state IN ('queued','running')''',
        ('서버가 재시작되어 중단됐습니다. 자료를 다시 선택하고 준비를 요청하세요. 자동으로 재분석하지 않습니다.', time.time(), INSTANCE))


def own(con, guardian, ident):
    row = con.execute('SELECT * FROM preparations WHERE id=? AND guardian=?', (ident, guardian)).fetchone()
    if not row:
        raise HTTPException(404, '본인의 준비 작업을 찾을 수 없습니다.')
    return row


def public(row, detail=False):
    result = {key: row[key] for key in ('id', 'session_id', 'title', 'subject', 'source_kind', 'state', 'message', 'updated')}
    result['playback'] = json.loads(row['playback'])
    if detail and row['state'] == 'completed':
        result['snapshot'] = json.loads(row['snapshot'])
    return result


def completed_snapshot(con, guardian, session_id):
    row = con.execute('SELECT * FROM preparations WHERE session_id=? AND guardian=?', (session_id, guardian)).fetchone()
    if row is None:
        return None
    if row['state'] != 'completed' or not row['snapshot']:
        raise HTTPException(409, '준비 완료된 자료만 배정할 수 있습니다.')
    return LectureSnapshot.model_validate_json(row['snapshot'])


def new_job(request, title, subject, problem_mode, source_kind):
    from app.main import agent
    user = accounts.require(request, 'guardian')
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        recover(con)
        active = con.execute("SELECT guardian FROM preparations WHERE state IN ('queued','running')").fetchall()
        if len(active) >= 4 or sum(row['guardian'] == user['id'] for row in active) >= 2:
            raise HTTPException(429, '진행 중인 준비 작업을 완료한 뒤 다시 요청해 주세요.')
        session = agent.create_session(LectureCreate(title=title, subject=subject,
            problem_mode=problem_mode, source_label={'materials': '보호자가 등록한 학습자료',
            'link': '보호자가 등록한 링크·자료', 'video': '동의한 파일 실제 분석 · 원본 미보관'}[source_kind]))
        ident = uuid4().hex
        con.execute('INSERT INTO owners VALUES(?,?)', (session.session_id, user['id']))
        con.execute('INSERT INTO preparations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
            (ident, user['id'], session.session_id, title, subject, source_kind, 'queued',
             '준비 요청을 접수했습니다.', None, '{}', INSTANCE, time.time()))
        return public(own(con, user['id'], ident))


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
            for asset in payload.assets:
                main.agent.register_asset(session_id, AssetInput(asset_id=uuid4().hex, name=asset.name,
                    kind=asset.kind, content_text=asset.content, size_bytes=len(asset.content.encode())))
            if payload.analysis is not None:
                main.agent.analyze(session_id, payload.analysis)
            if payload.link:
                result = await main.register_video_link(session_id, payload.link, request)
                if payload.link.request_analysis and result.analysis_status != 'completed':
                    raise HTTPException(503, result.message)
                if result.playback_kind in ('youtube', 'direct'):
                    playback = {'kind': result.playback_kind, 'normalized_url': result.normalized_url}
        if video:
            asset_id = uuid4().hex
            main.agent.register_asset(session_id, AssetInput(asset_id=asset_id, name=video.filename,
                kind='video', media_type=video.content_type or 'application/octet-stream', size_bytes=video_fields['size_bytes']))
            await main.analyze_uploaded_video_file(session_id, request, video=video, asset_id=asset_id,
                rights_confirmed=True, cloud_analysis_consent=True, access_code=video_fields['access_code'])
            playback = {'kind': 'local-reference', 'name': video.filename,
                'size_bytes': video_fields['size_bytes'], 'sha256': video_fields['sha256']}
        snapshot = main.agent.snapshot(session_id)
        if not (snapshot.passage or snapshot.transcript_segments or snapshot.safe_description_count):
            raise HTTPException(400, '배정할 수 있는 지문·자막·검증된 설명이 없습니다. 자료 형식과 분석 결과를 확인하세요.')
        update(ident, 'completed', '자료 준비를 완료했습니다. 확인 후 학생에게 배정하세요.', snapshot, playback)
    except asyncio.CancelledError:
        update(ident, 'interrupted', '서버 종료로 중단됐습니다. 자료를 다시 선택해 준비하세요.')
        raise
    except HTTPException as error:
        # Messages from existing gates/cleanup are user-safe; never persist provider responses/codes.
        update(ident, 'failed', str(error.detail)[:1500])
    except Exception:
        update(ident, 'failed', '자료 준비에 실패했습니다. 자료와 서버 연결을 확인하고 다시 준비하세요.')
    finally:
        if video:
            await video.close()


@router.get('/preparations')
def listing(request: Request):
    user = accounts.require(request, 'guardian')
    with accounts.db() as con:
        recover(con)
        return [public(row) for row in con.execute('SELECT * FROM preparations WHERE guardian=? ORDER BY updated DESC', (user['id'],))]


@router.get('/preparations/{ident}')
def detail(ident: str, request: Request):
    user = accounts.require(request, 'guardian')
    with accounts.db() as con:
        recover(con)
        return public(own(con, user['id'], ident), detail=True)


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
    job = new_job(request, payload.title, payload.subject, payload.problem_mode, 'link' if payload.link else 'materials')
    background.add_task(run, job['id'], job['session_id'], request, payload=payload)
    return job


@router.post('/preparations/video-file-analysis', status_code=202)
async def create_video(request: Request, background: BackgroundTasks, video: UploadFile = File(...),
    title: str = Form(..., min_length=1, max_length=160), subject: str = Form('일반', min_length=1, max_length=80),
    problem_mode: bool = Form(True), rights_confirmed: bool = Form(False),
    cloud_analysis_consent: bool = Form(False), access_code: str = Form('', max_length=200)):
    accounts.require(request, 'guardian')
    if not rights_confirmed or not cloud_analysis_consent:
        raise HTTPException(400, '원본 영상 임시 전송에 별도로 동의해야 실제 분석할 수 있습니다.')
    from app.core.demo_gate import server_gemini_key, check_access_code, DemoGateError, MAX_VIDEO_BYTES
    if not server_gemini_key():
        raise HTTPException(503, '서버에 실제 분석 연결이 없습니다. 분석 공급자에게 원본을 전송하지 않았습니다.')
    try:
        check_access_code(access_code)
    except DemoGateError as error:
        raise HTTPException(error.status_code, error.message) from None
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
        job = new_job(request, title, subject, problem_mode, 'video')
        background.add_task(run, job['id'], job['session_id'], request, video=copied,
            video_fields={'access_code': access_code, 'size_bytes': size, 'sha256': fingerprint.hexdigest()})
        return job
    except BaseException:
        memory.close()
        raise
    finally:
        await video.close()


class Withdraw(BaseModel):
    students: list[str] = Field(min_length=1, max_length=50)


class PublishPrepared(Withdraw):
    model_config = {'extra': 'forbid'}
    chat_consent: bool = False
    access_code: SecretStr | None = None


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
            ready=True, chat_consent=payload.chat_consent, access_code=payload.access_code))
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
