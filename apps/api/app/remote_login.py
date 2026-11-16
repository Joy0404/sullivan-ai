"""Guardian requests reach only an explicitly enrolled student Chrome device.

Guardians never receive student credentials. Device proofs are hashed at rest;
requests expire and are consumed in the same transaction that issues a session.
"""
import secrets
import time
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, SecretStr

from app import local_access as accounts
from app.extension_access import digest
from app.extension_accounts import client_allowed, require, revoke_family, token_pair

router = APIRouter(prefix='/extension/v1')


def checked_client(client, request):
    redirect = f'https://{client}.chromiumapp.org/oauth'
    if (request.headers.get('x-sullivan-client') != 'student'
            or request.headers.get('origin') != f'chrome-extension://{client}'
            or not client_allowed('student', client, redirect, request)):
        raise HTTPException(403, '처음 승인한 학생용 확장에서만 로그인 지원을 사용할 수 있습니다.')


def revoke_devices(con, *, user=None, device=None, family=None, keep_family=None):
    clause, values = ('id=?', (device,)) if device else ('family=?', (family,)) if family else ('student=? OR guardian=?', (user, user))
    rows = con.execute('SELECT id,family FROM remote_login_devices WHERE '+clause, values).fetchall()
    for row in rows:
        con.execute('UPDATE remote_login_devices SET revoked=1,presence=\'revoked\' WHERE id=?', (row['id'],))
        con.execute("UPDATE remote_login_requests SET state='cancelled' WHERE device=? AND state IN ('pending','issued')", (row['id'],))
        if row['family'] and row['family'] != keep_family: revoke_family(con, row['family'])


def transaction_user(con, request, role):
    authorization = request.headers.get('authorization', '')
    user = con.execute('''SELECT u.*,s.family AS login_family FROM users u JOIN extension_sessions s ON s.user=u.id
        WHERE s.token=? AND s.client=? AND u.role=? AND s.expires>?''',
        (digest(authorization[7:] if authorization.startswith('Bearer ') else ''), role, role, time.time())).fetchone()
    if not user or request.headers.get('x-sullivan-client') != role:
        raise HTTPException(401, '다시 로그인해 주세요.')
    return user


def enroll(con, user, client, request):
    checked_client(client, request)
    active = transaction_user(con, request, 'student')
    if active['id'] != user['id']: raise HTTPException(401, '학생 계정이 변경됐습니다. 다시 로그인해 주세요.')
    user = active
    guardian = con.execute("SELECT id,name FROM users WHERE id=? AND role='guardian'", (user['guardian'],)).fetchone()
    if not guardian: raise HTTPException(409, '보호자 연결 코드를 먼저 확인하고 연결을 승인하세요.')
    # One explicitly approved Chrome profile per student. A newly approved
    # device replaces the old one, rather than logging in forgotten devices.
    for row in con.execute('SELECT id FROM remote_login_devices WHERE student=? AND revoked=0', (user['id'],)).fetchall():
        revoke_devices(con, device=row['id'], keep_family=user['login_family'])
    ident, secret = uuid4().hex, secrets.token_urlsafe(32)
    con.execute('INSERT INTO remote_login_devices(id,secret,student,guardian,client,created,family) VALUES(?,?,?,?,?,?,?)',
                (ident, digest(secret), user['id'], guardian['id'], client, time.time(), user['login_family']))
    return {'device_id': ident, 'device_secret': secret, 'student_id': user['id'], 'student_name': user['name'],
            'guardian_name': guardian['name'], 'client_id': client}


class Enrollment(BaseModel):
    model_config = {'extra': 'forbid'}
    client_id: str = Field(pattern=r'^[a-p]{32}$')
    confirm: bool


@router.post('/student/remote-login/devices', status_code=201)
def enroll_device(p: Enrollment, request: Request):
    user = require(request, 'student')
    if not p.confirm: raise HTTPException(400, '로그아웃 후에도 이 기기의 보호자 로그인 지원을 허용할지 확인하세요.')
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        return enroll(con, user, p.client_id, request)


class Proof(BaseModel):
    model_config = {'extra': 'forbid'}
    client_id: str = Field(pattern=r'^[a-p]{32}$')
    device_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    device_secret: SecretStr = Field(min_length=40, max_length=100)


class Poll(Proof):
    presence: Literal['ready', 'signed_in', 'other_account'] = 'ready'


def device_from_proof(con, p, request):
    checked_client(p.client_id, request)
    row = con.execute('''SELECT d.* FROM remote_login_devices d JOIN users s ON s.id=d.student
        JOIN users g ON g.id=d.guardian WHERE d.id=? AND d.secret=? AND d.client=?
        AND d.revoked=0 AND s.guardian=d.guardian AND s.role='student' AND g.role='guardian' ''',
        (p.device_id, digest(p.device_secret.get_secret_value()), p.client_id)).fetchone()
    if not row: raise HTTPException(401, '이 기기의 로그인 지원이 해제됐습니다. 학생이 다시 로그인해 승인하세요.')
    return row


@router.post('/student/remote-login/poll')
def poll(p: Poll, request: Request):
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        device = device_from_proof(con, p, request)
        now = time.time()
        con.execute('UPDATE remote_login_devices SET seen=?,presence=? WHERE id=?', (now, p.presence, device['id']))
        con.execute("UPDATE remote_login_requests SET state='expired' WHERE device=? AND state IN ('pending','issued') AND expires<=?", (device['id'], now))
        if p.presence == 'signed_in':
            con.execute("UPDATE remote_login_requests SET state='completed' WHERE device=? AND state='issued'", (device['id'],))
        pending = con.execute("SELECT * FROM remote_login_requests WHERE device=? AND state='pending' ORDER BY created DESC LIMIT 1", (device['id'],)).fetchone()
        if not pending: return {'state': 'waiting'}
        if p.presence == 'other_account': return {'state': 'other_account'}
        if p.presence == 'signed_in':
            con.execute("UPDATE remote_login_requests SET state='already_signed_in' WHERE id=?", (pending['id'],))
            return {'state': 'already_signed_in'}
        if device['family']: revoke_family(con, device['family'])
        session = token_pair(con, device['student'], 'student', device['client'])
        con.execute('UPDATE remote_login_devices SET family=? WHERE id=?', (session['family_id'], device['id']))
        con.execute("UPDATE remote_login_requests SET state='issued' WHERE id=?", (pending['id'],))
        return {'state': 'issued', 'session': session}


@router.post('/student/remote-login/disable')
def disable(p: Proof, request: Request):
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        device = device_from_proof(con, p, request)
        revoke_devices(con, device=device['id'])
    return {'ok': True}


def guardian_device(con, guardian, student):
    row = con.execute("SELECT id FROM users WHERE id=? AND guardian=? AND role='student'", (student, guardian['id'])).fetchone()
    if not row: raise HTTPException(403, '연결된 학생의 로그인만 지원할 수 있습니다.')
    return con.execute('SELECT * FROM remote_login_devices WHERE student=? AND guardian=? AND revoked=0 ORDER BY created DESC LIMIT 1', (student, guardian['id'])).fetchone()


def public_state(con, device):
    if not device: return {'enabled': False, 'state': 'not_enrolled'}
    now = time.time()
    con.execute("UPDATE remote_login_requests SET state='expired' WHERE device=? AND state IN ('pending','issued') AND expires<=?", (device['id'], now))
    recent = con.execute('SELECT id,state,expires FROM remote_login_requests WHERE device=? ORDER BY created DESC LIMIT 1', (device['id'],)).fetchone()
    return {'enabled': True, 'state': recent['state'] if recent else 'ready',
            'request_id': recent['id'] if recent else None, 'expires_at': recent['expires'] if recent else None,
            'online': device['seen'] > now-90, 'presence': device['presence'] if device['seen'] > now-90 else 'offline'}


@router.get('/guardian/students/{student}/remote-login')
def state(student: str, request: Request):
    guardian = require(request, 'guardian')
    with accounts.db() as con: return public_state(con, guardian_device(con, guardian, student))


@router.post('/guardian/students/{student}/remote-login')
def start(student: str, request: Request):
    guardian = require(request, 'guardian')
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        guardian = transaction_user(con, request, 'guardian')
        device = guardian_device(con, guardian, student)
        if not device: raise HTTPException(409, '학생 기기에서 처음 한 번 로그인하고 보호자 로그인 지원을 승인해야 합니다.')
        current = public_state(con, device)
        if current['state'] not in ('pending','issued'):
            ident, now = uuid4().hex, time.time()
            con.execute('INSERT INTO remote_login_requests(id,device,guardian,created,expires) VALUES(?,?,?,?,?)', (ident, device['id'], guardian['id'], now, now+300))
        return public_state(con, device)


@router.delete('/guardian/students/{student}/remote-login')
def stop(student: str, request: Request):
    guardian = require(request, 'guardian')
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        guardian = transaction_user(con, request, 'guardian')
        device = guardian_device(con, guardian, student)
        if device: revoke_devices(con, device=device['id'])
    return {'ok': True}
