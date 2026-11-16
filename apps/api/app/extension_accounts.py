"""Role-bound accounts, S256 authorization codes, rotating sessions and explicit pairing."""
import base64
import hashlib
import hmac
import html
import json
import os
import re
import secrets
import time
from typing import Literal
from urllib.parse import urlencode, urlsplit
from uuid import uuid4

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel, Field, SecretStr

from app import local_access as accounts
from app.extension_access import digest, current, issue

router = APIRouter(prefix='/extension/v1')
auth_router = APIRouter(prefix='/extension/auth')
Role = Literal['guardian', 'student']
VERSION = '0.4.9'


def production():
    return os.getenv('SULLIVAN_PRODUCTION') == '1'


def check_version(request):
    minimum = os.getenv('SULLIVAN_MIN_EXTENSION_VERSION', '0.1.0')
    def parts(value):
        if not re.fullmatch(r'\d+\.\d+\.\d+', value): return (-1,)
        return tuple(map(int, value.split('.')))
    if parts(request.headers.get('x-sullivan-version', '0.1.0')) < parts(minimum):
        raise HTTPException(426, '확장 프로그램을 새로고침하거나 업데이트한 뒤 다시 로그인하세요.')


def require(request, role=None):
    user = current(request)
    if user is None: raise HTTPException(401, '확장에서 다시 로그인해 주세요.')
    if role and user['role'] != role: raise HTTPException(403, '이 계정으로 사용할 수 없는 기능입니다.')
    return user


def client_allowed(role, client, redirect, request):
    if not re.fullmatch('[a-p]{32}', client): return False
    if redirect != f'https://{client}.chromiumapp.org/oauth': return False
    try: configured = json.loads(os.getenv('SULLIVAN_EXTENSION_CLIENTS', '{}'))
    except ValueError: return False
    if not isinstance(configured,dict):return False
    if configured.get(role) == client: return True
    return not production() and request.url.hostname in ('127.0.0.1', 'localhost', '::1') and not configured


def public_origin(request):
    configured = os.getenv('SULLIVAN_PUBLIC_URL', '').rstrip('/')
    if production():
        parsed = urlsplit(configured)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise HTTPException(503, '운영 서버 주소 설정을 확인해 주세요.')
        return configured
    return str(request.base_url).rstrip('/')


def attempt(con, key, limit=5, seconds=600):
    row = con.execute('SELECT * FROM failures WHERE identity=?', (key,)).fetchone()
    if row and row['count'] >= limit and row['until'] > time.time():
        raise HTTPException(429, '시도가 많습니다. 잠시 뒤 다시 시도해 주세요.')
    return row['count'] if row and row['until'] > time.time() else 0


def fail(con, key, count, seconds=600):
    con.execute('INSERT OR REPLACE INTO failures VALUES(?,?,?)', (key, count + 1, time.time() + seconds))


def authenticate(con, username, password, role, request):
    key = digest(f'{request.client.host if request.client else "local"}:{username}')
    count = attempt(con, key)
    user = con.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
    valid = hmac.compare_digest(accounts.password_hash(password, user['salt'] if user else '00'*16), user['password'] if user else '0'*128)
    if not user or not valid or user['role'] != role:
        fail(con, key, count); return None
    con.execute('DELETE FROM failures WHERE identity=?', (key,))
    return user


def revoke_family(con, family):
    con.execute('UPDATE auth_families SET revoked=1 WHERE id=?', (family,))
    con.execute('DELETE FROM extension_sessions WHERE family=?', (family,))


def revoke_user(con, ident):
    from app.remote_login import revoke_devices
    revoke_devices(con, user=ident)
    con.execute('DELETE FROM sessions WHERE user=?', (ident,))
    con.execute('DELETE FROM extension_sessions WHERE user=?', (ident,))
    con.execute('UPDATE auth_families SET revoked=1 WHERE user=?', (ident,))
    con.execute('DELETE FROM auth_codes WHERE user=?', (ident,))


def recovery_codes(con, ident):
    codes = [secrets.token_urlsafe(12) for _ in range(8)]
    con.execute('DELETE FROM recovery_codes WHERE user=?', (ident,))
    con.executemany('INSERT INTO recovery_codes VALUES(?,?,0)', [(digest(code), ident) for code in codes])
    return codes


def token_pair(con, ident, role, client, family=None):
    now = time.time()
    if not family:
        family = uuid4().hex
        con.execute('INSERT INTO auth_families VALUES(?,?,?,?,?,0)', (family, ident, client, now, now + 30*86400))
    access, refresh = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    # Rotation does not extend the original family lifetime.
    expires = con.execute('SELECT expires FROM auth_families WHERE id=?', (family,)).fetchone()[0]
    access_expires=min(now+900,expires)
    con.execute('INSERT INTO extension_sessions(token,user,client,expires,family) VALUES(?,?,?,?,?)', (digest(access), ident, role, access_expires, family))
    con.execute('INSERT INTO refresh_tokens VALUES(?,?,?,0)', (digest(refresh), family, expires))
    user = con.execute('SELECT * FROM users WHERE id=?', (ident,)).fetchone()
    return {'access_token': access, 'token_type': 'Bearer', 'expires_in': int(access_expires-now), 'expires_at': access_expires,
            'refresh_token': refresh, 'family_id': family, 'user': accounts.public(user)}


@router.get('/{role}/capabilities')
def capabilities(role: Role, request: Request):
    return {'version': VERSION, 'protocol': 1, 'minimum_version': os.getenv('SULLIVAN_MIN_EXTENSION_VERSION', '0.1.0'),
            'production': production(), 'pkce': 'S256', 'signup_enabled': os.getenv('SULLIVAN_SIGNUP_ENABLED','1')!='0',
            'role': role, 'raw_media_transfer': False}


class Signup(accounts.Credentials):
    model_config = {'extra': 'forbid'}


@router.post('/{role}/accounts', status_code=201)
def signup(role: Role, p: Signup, request: Request):
    if request.headers.get('x-sullivan-client') != role or p.role not in (None, role): raise HTTPException(403, '이 프로그램의 계정으로 가입하세요.')
    if os.getenv('SULLIVAN_SIGNUP_ENABLED','1')=='0':raise HTTPException(403,'지금은 신규 가입을 받지 않습니다.')
    key = digest(f'signup:{request.client.host if request.client else "local"}')
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        count = attempt(con, key, limit=10, seconds=3600)
        ident = accounts.create_user(con, p, role)
        fail(con, key, count, seconds=3600)
        codes = recovery_codes(con, ident)
    # Signup never silently authenticates or links a student to a guardian.
    return {'username': p.username, 'role': role, 'recovery_codes': codes}


class Recover(BaseModel):
    username: str = Field(min_length=3, max_length=60)
    code: SecretStr
    password: str = Field(min_length=8, max_length=128)


@router.post('/{role}/recover')
def recover(role: Role, p: Recover, request: Request):
    key = digest(f'recovery:{request.client.host if request.client else "local"}:{p.username}')
    denied = False
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        count = attempt(con, key)
        user = con.execute('SELECT * FROM users WHERE username=? AND role=?', (p.username, role)).fetchone()
        code = con.execute('SELECT * FROM recovery_codes WHERE code=?', (digest(p.code.get_secret_value()),)).fetchone()
        if not user or not code or code['user'] != user['id'] or code['used']:
            fail(con, key, count); denied = True
        else:
            con.execute('UPDATE recovery_codes SET used=1 WHERE code=?', (code['code'],))
            salt = secrets.token_hex(16)
            con.execute('UPDATE users SET salt=?,password=? WHERE id=?', (salt, accounts.password_hash(p.password, salt), user['id']))
            revoke_user(con, user['id'])
            con.execute('DELETE FROM failures WHERE identity=?', (key,))
    if denied: raise HTTPException(400, '계정과 사용하지 않은 복구 코드를 확인하세요.')
    return {'ok': True, 'message': '비밀번호를 변경하고 기존 기기의 로그인을 종료했습니다. 다시 로그인하세요.'}


class Reauthenticate(BaseModel):
    password: SecretStr


@router.post('/{role}/recovery-codes')
def regenerate(role: Role, p: Reauthenticate, request: Request):
    user = require(request, role)
    with accounts.db() as con:
        verified = authenticate(con, user['username'], p.password.get_secret_value(), role, request)
        codes = recovery_codes(con, user['id']) if verified else None
    if not codes: raise HTTPException(400, '현재 비밀번호를 확인하세요.')
    return {'recovery_codes': codes}


@router.get('/{role}/devices')
def devices(role: Role, request: Request):
    user = require(request, role)
    with accounts.db() as con:
        return [dict(row) for row in con.execute('SELECT id,created,expires FROM auth_families WHERE user=? AND revoked=0 AND expires>? ORDER BY created DESC', (user['id'], time.time()))]


@router.delete('/{role}/devices/{ident}')
def revoke_device(role: Role, ident: str, request: Request):
    user = require(request, role)
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        from app.remote_login import transaction_user
        user = transaction_user(con, request, role)
        if not con.execute('SELECT 1 FROM auth_families WHERE id=? AND user=?', (ident, user['id'])).fetchone(): raise HTTPException(404, '내 로그인 기기를 찾지 못했습니다.')
        from app.remote_login import revoke_devices
        revoke_devices(con, family=ident)
        revoke_family(con, ident)
    return {'ok': True}


@router.post('/{role}/logout-all')
def logout_all(role: Role, request: Request):
    user = require(request, role)
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        from app.remote_login import transaction_user
        user = transaction_user(con, request, role)
        revoke_user(con, user['id'])
    return {'ok': True}


@router.post('/guardian/connections/code')
def pairing_code(request: Request):
    user = require(request, 'guardian')
    code = base64.b32encode(secrets.token_bytes(10)).decode()
    with accounts.db() as con:
        con.execute('UPDATE pair_codes SET expires=0 WHERE guardian=? AND consumed_by IS NULL', (user['id'],))
        con.execute('INSERT INTO pair_codes VALUES(?,?,?,NULL)', (digest(code), user['id'], time.time()+600))
    return {'code': '-'.join(code[index:index+4] for index in range(0,16,4)), 'expires_in': 600}


class PairCode(BaseModel):
    code: str = Field(min_length=10, max_length=40)


@router.post('/student/connections/preview')
def pairing_preview(p: PairCode, request: Request):
    user = require(request, 'student')
    key = digest('pair:' + user['id'])
    denied = False
    with accounts.db() as con:
        count = attempt(con, key)
        code = re.sub(r'[-\s]', '', p.code).upper()
        row = con.execute('SELECT p.*,u.name FROM pair_codes p JOIN users u ON u.id=p.guardian WHERE p.code=? AND p.expires>? AND p.consumed_by IS NULL', (digest(code), time.time())).fetchone()
        if not row:
            fail(con, key, count); denied = True
        else:
            ident = uuid4().hex
            con.execute('INSERT INTO pair_requests VALUES(?,?,?,?,?)', (ident, row['code'], user['id'], row['guardian'], time.time()+300))
            result = {'request_id': ident, 'guardian_name': row['name'], 'sharing': '배정 강의, 학습 위치와 기록 개수 요약, 학습 기본 설정. 메모·질문 원문은 공유하지 않습니다.'}
    if denied: raise HTTPException(400, '유효한 일회용 연결 코드를 확인하세요.')
    return result


class PairConfirm(BaseModel):
    request_id: str = Field(min_length=32, max_length=32)
    confirm: bool
    remote_login: bool = False
    client_id: str = Field(default='', max_length=32)


@router.post('/student/connections/confirm')
def pairing_confirm(p: PairConfirm, request: Request):
    user = require(request, 'student')
    if not p.confirm: raise HTTPException(400, '공유 범위를 확인하고 직접 연결을 승인하세요.')
    result = {'ok': True}
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = con.execute('''SELECT r.*,c.expires AS code_expires,c.consumed_by FROM pair_requests r
            JOIN pair_codes c ON c.code=r.code WHERE r.id=? AND r.student=? AND r.expires>?''', (p.request_id, user['id'], time.time())).fetchone()
        if not row or row['code_expires'] <= time.time() or row['consumed_by'] is not None: raise HTTPException(409, '연결 요청이 만료되거나 이미 사용됐습니다. 새 코드를 받아 주세요.')
        current_guardian = con.execute('SELECT guardian FROM users WHERE id=?', (user['id'],)).fetchone()[0]
        if current_guardian and current_guardian != row['guardian']: raise HTTPException(409, '기존 보호자 연결을 먼저 해제하세요.')
        con.execute('UPDATE users SET guardian=? WHERE id=?', (row['guardian'], user['id']))
        con.execute('UPDATE pair_codes SET consumed_by=? WHERE code=?', (user['id'], row['code']))
        con.execute('DELETE FROM pair_requests WHERE code=?', (row['code'],))
        if p.remote_login:
            from app.remote_login import enroll
            linked = con.execute('SELECT * FROM users WHERE id=?', (user['id'],)).fetchone()
            result['remote_login'] = enroll(con, linked, p.client_id, request)
    return result


@router.get('/{role}/connections')
def connections(role: Role, request: Request):
    user = require(request, role)
    with accounts.db() as con:
        if role == 'guardian': rows = con.execute("SELECT id,name,username FROM users WHERE guardian=? AND role='student'", (user['id'],)).fetchall()
        else: rows = con.execute('SELECT id,name,username FROM users WHERE id=?', (user['guardian'],)).fetchall()
        return [dict(row) for row in rows]


class Unlink(BaseModel):
    student: str
    confirm: bool


@router.post('/{role}/connections/unlink')
def unlink(role: Role, p: Unlink, request: Request):
    user = require(request, role)
    if not p.confirm: raise HTTPException(400, '연결 해제의 영향을 확인하고 승인하세요.')
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = con.execute("SELECT * FROM users WHERE id=? AND role='student'", (p.student,)).fetchone()
        if not row or (role == 'student' and row['id'] != user['id']) or (role == 'guardian' and row['guardian'] != user['id']): raise HTTPException(403, '본인의 연결만 해제할 수 있습니다.')
        guardian = row['guardian']
        from app.remote_login import revoke_devices
        revoke_devices(con, user=row['id'])
        con.execute('UPDATE users SET guardian=NULL WHERE id=?', (row['id'],))
        con.execute('DELETE FROM assignments WHERE student=? AND lecture IN (SELECT id FROM lectures WHERE guardian=?)', (row['id'], guardian))
        con.execute('DELETE FROM pair_requests WHERE student=?', (row['id'],))
    return {'ok': True}


@auth_router.get('/{role}/authorize', response_class=HTMLResponse)
def authorize(role: Role, request: Request, client_id: str, redirect_uri: str, code_challenge: str, state: str, code_challenge_method: str = 'S256', response_type: str = 'code'):
    if response_type != 'code' or code_challenge_method != 'S256' or not re.fullmatch(r'[A-Za-z0-9_-]{43}', code_challenge) or not 32 <= len(state) <= 200 or not client_allowed(role, client_id, redirect_uri, request):
        raise HTTPException(400, '로그인 요청의 출처와 인증 방식을 확인하세요.')
    public_origin(request)
    ticket, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    with accounts.db() as con:
        con.execute('DELETE FROM auth_requests WHERE expires<?', (time.time(),))
        con.execute('INSERT INTO auth_requests VALUES(?,?,?,?,?,?,?,?)', (digest(ticket), client_id, role, redirect_uri, code_challenge, state, digest(csrf), time.time()+300))
    response = auth_page(role, ticket, redirect=redirect_uri)
    response.set_cookie('sullivan_auth_'+role, csrf, httponly=True, secure=production(), samesite='lax', max_age=300, path='/extension/auth/'+role)
    return response


def auth_page(role, ticket, error='', username='', redirect=''):
    label = '학생' if role == 'student' else '보호자'
    escape = html.escape
    body = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sullivan AI {label} 로그인</title><link rel="stylesheet" href="/extension/auth/style.css"></head><body><main><h1>{label} 로그인</h1><p>이 페이지에서 로그인한 뒤 {label} 확장으로 돌아갑니다.</p><p role="alert">{escape(error)}</p><form method="post" action="/extension/auth/{role}/authorize"><input type="hidden" name="ticket" value="{escape(ticket, quote=True)}"><label>로그인 이름<input name="username" required minlength="3" maxlength="60" autocomplete="username" value="{escape(username,quote=True)}"></label><label>비밀번호<input name="password" type="password" required minlength="8" maxlength="128" autocomplete="current-password" aria-describedby="password-help"></label><p id="password-help">비밀번호는 8~128자입니다.</p><button type="submit">로그인하고 확장으로 돌아가기</button></form></main></body></html>'''
    callback_origin=f'https://{urlsplit(redirect).netloc}' if redirect else ''
    # Same-origin keeps the native form's Origin intact for CSRF validation while
    # suppressing referrers on the cross-origin Chromium callback.
    return HTMLResponse(body, headers={'Cache-Control':'no-store','Content-Security-Policy':f"default-src 'none'; style-src 'self'; form-action 'self' {callback_origin}; frame-ancestors 'none'; base-uri 'none'", 'Referrer-Policy':'same-origin'})


@auth_router.get('/style.css')
def auth_style():
    return Response('body{font:18px/1.6 sans-serif;background:#f6f7f3;color:#152e33}main{max-width:32rem;margin:3rem auto;padding:1.5rem}form,label{display:grid;gap:.6rem}form{gap:1rem}input,button{font:inherit;padding:.7rem;max-width:100%;box-sizing:border-box}button{background:#176358;color:white;border:0}*:focus-visible{outline:4px solid #9d4114;outline-offset:3px}', media_type='text/css')


@auth_router.post('/{role}/authorize')
def authorize_submit(role: Role, request: Request, ticket: str = Form(..., max_length=100), username: str = Form(..., max_length=60), password: str = Form(..., min_length=8, max_length=128)):
    if request.headers.get('origin') != public_origin(request): raise HTTPException(403, '로그인 페이지에서 다시 시도하세요.')
    denied = False
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = con.execute('SELECT * FROM auth_requests WHERE ticket=? AND role=? AND expires>?', (digest(ticket), role, time.time())).fetchone()
        csrf = request.cookies.get('sullivan_auth_'+role, '')
        if not row or not hmac.compare_digest(digest(csrf), row['csrf']): raise HTTPException(403, '로그인 요청이 만료됐습니다. 확장에서 다시 시작하세요.')
        user = authenticate(con, username, password, role, request)
        if not user: denied = True
        else:
            code = secrets.token_urlsafe(32)
            con.execute('INSERT INTO auth_codes VALUES(?,?,?,?,?,?,?,0)', (digest(code), user['id'], row['client'], role, row['redirect'], row['challenge'], time.time()+60))
            con.execute('DELETE FROM auth_requests WHERE ticket=?', (row['ticket'],))
            target = row['redirect'] + '?' + urlencode({'code':code,'state':row['state']})
    if denied: return auth_page(role, ticket, '로그인 이름·비밀번호·프로그램 유형을 확인하세요.', username, row['redirect'])
    response = RedirectResponse(target, status_code=303, headers={'Cache-Control':'no-store','Referrer-Policy':'no-referrer'})
    response.delete_cookie('sullivan_auth_'+role, path='/extension/auth/'+role)
    return response


@router.post('/{role}/token')
async def token(role: Role, request: Request):
    data = await request.form()
    client = str(data.get('client_id',''))
    redirect = str(data.get('redirect_uri',''))
    if not client_allowed(role, client, redirect, request): raise HTTPException(400, '인증 프로그램과 반환 주소를 확인하세요.')
    denied = None
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        if data.get('grant_type') == 'authorization_code':
            verifier = str(data.get('code_verifier',''))
            if not re.fullmatch(r'[A-Za-z0-9._~-]{43,128}', verifier): raise HTTPException(400, '인증 검증값을 확인하세요.')
            challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
            row = con.execute('SELECT * FROM auth_codes WHERE code=?', (digest(str(data.get('code',''))),)).fetchone()
            if not row or row['used'] or row['expires'] <= time.time() or row['client'] != client or row['role'] != role or row['redirect'] != redirect or not hmac.compare_digest(row['challenge'], challenge): raise HTTPException(400, '만료되거나 유효하지 않은 로그인 코드입니다.')
            con.execute('UPDATE auth_codes SET used=1 WHERE code=?', (row['code'],))
            result = token_pair(con, row['user'], role, client)
        elif data.get('grant_type') == 'refresh_token':
            row = con.execute('''SELECT r.*,f.user,f.client,f.revoked,u.role FROM refresh_tokens r
                JOIN auth_families f ON f.id=r.family JOIN users u ON u.id=f.user WHERE r.token=?''', (digest(str(data.get('refresh_token',''))),)).fetchone()
            if not row or row['revoked'] or row['expires'] <= time.time() or row['client'] != client or row['role'] != role: raise HTTPException(401, '다시 로그인해 주세요.')
            if row['used']:
                revoke_family(con, row['family']); denied = '이미 사용한 갱신 자격이 재사용되어 해당 기기의 로그인을 종료했습니다.'
            else:
                con.execute('UPDATE refresh_tokens SET used=1 WHERE token=?', (row['token'],))
                con.execute('DELETE FROM extension_sessions WHERE family=?', (row['family'],))
                result = token_pair(con, row['user'], role, client, row['family'])
        else: raise HTTPException(400, '지원하지 않는 인증 방식입니다.')
    if denied: raise HTTPException(401, denied)
    return result
