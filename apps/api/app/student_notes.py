"""Private, student-authored notes. References never persist source text.

No provider calls, source rewrites, guardian summaries or raw media endpoints.
"""
import hashlib
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Literal

from app import local_access as accounts
from app.student_learning import authorize

router = APIRouter(prefix='/extension/v1/student', dependencies=[Depends(authorize)])


def table(con):
    # Deliberately independent of progress and assignment deletion: personal work
    # survives withdrawal, unlinking and legacy progress writes.
    con.execute('''CREATE TABLE IF NOT EXISTS student_notes(
        lecture TEXT NOT NULL, student TEXT NOT NULL, id TEXT NOT NULL,
        body TEXT NOT NULL, started_ms INTEGER NOT NULL, source TEXT,
        revision INTEGER NOT NULL, updated TEXT NOT NULL,
        PRIMARY KEY(lecture,student,id))''')


class Source(BaseModel):
    model_config = {'extra': 'forbid'}
    kind: Literal['sentence', 'visual']
    id: str = Field(min_length=1, max_length=160)
    fingerprint: str = Field(pattern=r'^[a-f0-9]{64}$')


class Note(BaseModel):
    model_config = {'extra': 'forbid'}
    body: str = Field(max_length=30000)
    started_ms: int = Field(ge=0, le=86400000)
    source: Source | None = None
    revision: int = Field(ge=0)


def sources(ident, request):
    # This existing, validated student view applies current assignment, problem
    # policy and low-confidence redaction before we ever build reference text.
    snapshot = accounts.lecture(ident, request)['snapshot']
    result = []
    for paragraph in (snapshot.get('passage') or {}).get('paragraphs', []):
        for sentence in paragraph['sentences']:
            if sentence['text']:
                result.append({'kind': 'sentence', 'id': sentence['sentence_id'],
                               'text': sentence['text'], 'timestamp_ms': sentence['timestamp_ms'],
                               'label': f"{sentence['paragraph_index']}문단 {sentence['sentence_index']}문장"})
    for gap in snapshot['visual_gaps']:
        if (gap['safe_to_speak'] and gap['confidence'] >= .72
                and gap['action'] not in ('HOLD', 'SKIP') and gap['public_description']
                and not (snapshot['session']['problem_mode'] and gap['kind'] == 'answer')):
            result.append({'kind': 'visual', 'id': gap['gap_id'], 'text': gap['public_description'],
                           'timestamp_ms': gap['timestamp_ms'], 'label': '검증된 화면 설명'})
    for entry in result:
        entry['fingerprint'] = hashlib.sha256(entry['text'].encode()).hexdigest()
    return result


def available_sources(ident, request):
    """Index freshly authorized sources for one request; never cache across requests."""
    try:
        return {source_key(entry): entry for entry in sources(ident, request)}
    except HTTPException as error:
        if error.status_code not in (403, 404):
            raise
        return {}


def source_key(source):
    return tuple(source[key] for key in ('kind', 'id', 'fingerprint'))


def resolved(ident, source, request):
    return available_sources(ident, request).get(source_key(source)) if source else None


def public(row):
    return {'id': row['id'], 'body': row['body'], 'started_ms': row['started_ms'],
            'source': json.loads(row['source']) if row['source'] else None,
            'revision': row['revision'], 'updated': row['updated']}


@router.get('/lectures/{ident}/note-sources')
def note_sources(ident: str, request: Request):
    return sources(ident, request)


@router.get('/notebooks')
def notebooks(request: Request):
    user = accounts.require(request, 'student')
    with accounts.db() as con:
        table(con)
        result = []
        for row in con.execute('SELECT lecture,count(*) AS count FROM student_notes WHERE student=? GROUP BY lecture', (user['id'],)):
            try:
                lecture = accounts.own(con, user, row['lecture'])
                title = lecture['title']
            except HTTPException:
                title = '배정이 종료된 강의의 내 필기'
            result.append({'id': row['lecture'], 'title': title, 'count': row['count']})
        return result


@router.get('/lectures/{ident}/notes')
def list_notes(ident: str, request: Request):
    user = accounts.require(request, 'student')
    with accounts.db() as con:
        table(con)
        # An unassigned student cannot use this to inspect anyone else's notes.
        return [public(row) for row in con.execute(
            'SELECT * FROM student_notes WHERE lecture=? AND student=? ORDER BY updated DESC,id', (ident, user['id']))]


@router.put('/lectures/{ident}/notes/{note_id}')
def put_note(ident: str, note_id: str, payload: Note, request: Request):
    import re
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', note_id):
        raise HTTPException(422, '필기 항목 식별자를 확인하세요.')
    user = accounts.require(request, 'student')
    source = payload.source.model_dump() if payload.source else None
    # Check a new or changed reference immediately; no caller-supplied text.
    with accounts.db() as con:
        table(con)
        row = con.execute('SELECT * FROM student_notes WHERE lecture=? AND student=? AND id=?',
                          (ident, user['id'], note_id)).fetchone()
        if row is None:
            # The owner may continue a personal notebook after withdrawal. A
            # new reference still requires current source authorization below.
            if not con.execute('SELECT 1 FROM student_notes WHERE lecture=? AND student=?', (ident, user['id'])).fetchone():
                accounts.own(con, user, ident)
            if payload.revision != 0:
                raise HTTPException(409, '필기 버전이 바뀌었습니다. 초안은 유지됩니다.')
            count = con.execute('SELECT count(*) FROM student_notes WHERE lecture=? AND student=?', (ident, user['id'])).fetchone()[0]
            if count >= 1000:
                raise HTTPException(413, '강의당 필기는 1000개까지 저장할 수 있습니다.')
    if source and (not row or source != json.loads(row['source'] or 'null')) and not resolved(ident, source, request):
        raise HTTPException(403, '이 원문은 현재 연결할 수 없습니다. 원문 없이 필기할 수 있습니다.')
    encoded = json.dumps(source, ensure_ascii=False) if source else None
    with accounts.db() as con:
        table(con)
        con.execute('BEGIN IMMEDIATE')
        latest = con.execute('SELECT * FROM student_notes WHERE lecture=? AND student=? AND id=?', (ident, user['id'], note_id)).fetchone()
        if latest and latest['body'] == payload.body and latest['started_ms'] == payload.started_ms and latest['source'] == encoded:
            return public(latest)  # Retry after an ambiguous network completion.
        if (latest and latest['revision'] != payload.revision) or (not latest and payload.revision != 0):
            raise HTTPException(409, '다른 화면에서 필기가 바뀌었습니다. 초안을 새 필기로 보존하세요.')
        if not latest:
            # The preflight count can change while source authorization runs.
            # Serialize the final capacity check with insertion across tabs.
            count = con.execute('SELECT count(*) FROM student_notes WHERE lecture=? AND student=?', (ident, user['id'])).fetchone()[0]
            if count >= 1000:
                raise HTTPException(413, '강의당 필기는 1000개까지 저장할 수 있습니다.')
        revision = (latest['revision'] if latest else 0) + 1
        updated = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
        con.execute('INSERT OR REPLACE INTO student_notes VALUES(?,?,?,?,?,?,?,?)',
                    (ident, user['id'], note_id, payload.body, payload.started_ms, encoded, revision, updated))
        return public(con.execute('SELECT * FROM student_notes WHERE lecture=? AND student=? AND id=?', (ident, user['id'], note_id)).fetchone())


class NoteVersion(BaseModel):
    model_config = {'extra': 'forbid'}
    revision: int = Field(ge=1)


@router.delete('/lectures/{ident}/notes/{note_id}')
def delete_note(ident: str, note_id: str, payload: NoteVersion, request: Request):
    user = accounts.require(request, 'student')
    with accounts.db() as con:
        table(con)
        con.execute('BEGIN IMMEDIATE')
        row = con.execute('SELECT * FROM student_notes WHERE lecture=? AND student=? AND id=?', (ident, user['id'], note_id)).fetchone()
        if row is None:
            raise HTTPException(404, '내 필기 항목을 찾을 수 없습니다.')
        if payload.revision != row['revision']:
            raise HTTPException(409, '필기가 바뀌었습니다. 목록을 다시 확인하세요.')
        deleted = con.execute('DELETE FROM student_notes WHERE lecture=? AND student=? AND id=? AND revision=?', (ident, user['id'], note_id, payload.revision))
        if deleted.rowcount != 1:
            raise HTTPException(409, '필기가 바뀌었습니다. 목록을 다시 확인하세요.')
    return {'ok': True}


@router.get('/lectures/{ident}/notes/{note_id}/source')
def note_source(ident: str, note_id: str, request: Request):
    user = accounts.require(request, 'student')
    with accounts.db() as con:
        table(con)
        row = con.execute('SELECT source FROM student_notes WHERE lecture=? AND student=? AND id=?', (ident, user['id'], note_id)).fetchone()
        if row is None:
            raise HTTPException(404, '내 필기 항목을 찾을 수 없습니다.')
    source = resolved(ident, json.loads(row['source']) if row['source'] else None, request)
    return {'available': bool(source), 'source': source,
            'message': '' if source else '현재 확인할 수 있는 연결 원문이 없습니다. 학생 필기는 그대로 보존됩니다.'}


@router.get('/lectures/{ident}/notes-export')
def export_notes(ident: str, request: Request):
    entries = list_notes(ident, request)
    current_sources = available_sources(ident, request) if any(entry['source'] for entry in entries) else {}
    lines = ['# 내 필기', '', '학생 작성 내용입니다. 연결 원문은 별도 표시합니다.', '']
    for entry in entries:
        lines += [f"## {entry['started_ms'] // 1000}초에 시작한 필기", '', entry['body'], '']
        source = current_sources.get(source_key(entry['source'])) if entry['source'] else None
        lines += ['연결 원문 (읽기 전용):', source['text'] if source else '현재 연결 원문 없음 또는 공개 불가', '']
    return {'text': '\n'.join(lines)}
