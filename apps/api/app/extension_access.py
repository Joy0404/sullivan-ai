"""Independent, role-bound extension sessions; existing web cookies stay separate."""
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from typing import Literal

from fastapi import APIRouter, HTTPException, Request

from app import local_access as accounts

router = APIRouter(prefix='/extension/v1')
Role = Literal['student', 'guardian']
SESSION_SECONDS = 8 * 60 * 60


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def allowed_origin(request):
    origin = request.headers.get('origin')
    own_origin = os.getenv('SULLIVAN_PUBLIC_URL','').rstrip('/') if os.getenv('SULLIVAN_PRODUCTION')=='1' else str(request.base_url).rstrip('/')
    if not origin or origin == own_origin:
        return True
    configured = os.getenv('SULLIVAN_EXTENSION_ORIGINS', '').split(',')
    try:
        configured += ['chrome-extension://'+value for value in json.loads(os.getenv('SULLIVAN_EXTENSION_CLIENTS','{}')).values() if isinstance(value,str)]
    except (ValueError,AttributeError,TypeError):
        pass
    if origin in {value.strip() for value in configured if value.strip()}:
        return bool(re.fullmatch(r'chrome-extension://[a-p]{32}', origin))
    return (request.url.hostname in ('127.0.0.1', 'localhost', '::1')
            and os.getenv('SULLIVAN_PRODUCTION') != '1'
            and bool(re.fullmatch(r'chrome-extension://[a-p]{32}', origin)))


def current(request):
    authorization = request.headers.get('authorization', '')
    client = request.headers.get('x-sullivan-client')
    if not authorization.startswith('Bearer ') or client not in ('student', 'guardian'):
        return None
    token = authorization[7:]
    if not token or len(token) > 200:
        return None
    with accounts.db() as con:
        return con.execute('''SELECT u.* FROM users u JOIN extension_sessions s
            ON s.user=u.id WHERE s.token=? AND s.client=? AND u.role=s.client
            AND s.expires>?''', (digest(token), client, time.time())).fetchone()


def issue(con, ident, role):
    token = secrets.token_urlsafe(32)
    expires = time.time() + SESSION_SECONDS
    con.execute('DELETE FROM extension_sessions WHERE expires<=?', (time.time(),))
    con.execute('INSERT INTO extension_sessions(token,user,client,expires) VALUES(?,?,?,?)', (digest(token), ident, role, expires))
    user = con.execute('SELECT * FROM users WHERE id=?', (ident,)).fetchone()
    return {'token': token, 'expires_at': expires, 'user': accounts.public(user)}


class Login(accounts.Credentials):
    model_config = {'extra': 'forbid'}


def check_client(request, role):
    if request.headers.get('x-sullivan-client') != role:
        raise HTTPException(403, '이 프로그램의 계정으로 로그인해 주세요.')


@router.post('/{role}/session')
def login(role: Role, p: Login, request: Request):
    if os.getenv('SULLIVAN_PRODUCTION') == '1':
        raise HTTPException(403, '운영 서버에서는 브라우저 로그인 버튼을 사용해 주세요.')
    check_client(request, role)
    identity = digest(f'{request.client.host if request.client else "local"}:{p.username}')
    denied = False
    with accounts.db() as con:
        failure = con.execute('SELECT * FROM failures WHERE identity=?', (identity,)).fetchone()
        if failure and failure['count'] >= 5 and failure['until'] > time.time():
            raise HTTPException(429, '로그인 시도가 많습니다. 10분 뒤 다시 시도해 주세요.')
        user = con.execute('SELECT * FROM users WHERE username=?', (p.username,)).fetchone()
        valid = hmac.compare_digest(accounts.password_hash(p.password, user['salt'] if user else '00'*16),
                                    user['password'] if user else '0'*128)
        if not user or not valid:
            count = failure['count']+1 if failure and failure['until'] > time.time() else 1
            con.execute('INSERT OR REPLACE INTO failures VALUES(?,?,?)', (identity, count, time.time()+600))
            denied = True
        else:
            if user['role'] != role or p.role not in (None, role):
                raise HTTPException(403, '이 프로그램의 계정으로 로그인해 주세요.')
            con.execute('DELETE FROM failures WHERE identity=?', (identity,))
            result = issue(con, user['id'], role)
    if denied:
        raise HTTPException(401, '로그인 이름 또는 비밀번호를 확인해 주세요.')
    return result


@router.post('/guardian/register')
def register(p: Login, request: Request):
    check_client(request, 'guardian')
    # Only the loopback development server supports direct registration in phase 1.
    if os.getenv('SULLIVAN_PRODUCTION') == '1' or request.url.hostname not in ('127.0.0.1', 'localhost', '::1'):
        raise HTTPException(403, '현재 개발 버전은 로컬 서버에서만 계정을 만들 수 있습니다.')
    if p.role not in (None, 'guardian'):
        raise HTTPException(403, '보호자 계정만 만들 수 있습니다.')
    with accounts.db() as con:
        return issue(con, accounts.create_user(con, p, 'guardian'), 'guardian')


@router.get('/{role}/session')
def me(role: Role, request: Request):
    check_client(request, role)
    user = current(request)
    if user is None:
        raise HTTPException(401, '다시 로그인해 주세요.')
    return accounts.public(user)


@router.delete('/{role}/session')
def logout(role: Role, request: Request):
    me(role, request)
    with accounts.db() as con:
        con.execute('BEGIN IMMEDIATE')
        from app.remote_login import transaction_user
        user = transaction_user(con, request, role)
        if role == 'student':
            con.execute("UPDATE remote_login_requests SET state='cancelled' WHERE state IN ('pending','issued') AND device IN (SELECT id FROM remote_login_devices WHERE student=?)", (user['id'],))
        row=con.execute('SELECT family FROM extension_sessions WHERE token=?', (digest(request.headers['authorization'][7:]),)).fetchone()
        if row and row['family']:
            from app.extension_accounts import revoke_family
            revoke_family(con,row['family'])
        con.execute('DELETE FROM extension_sessions WHERE token=? AND client=?',
                    (digest(request.headers['authorization'][7:]), role))
    return {'ok': True}


async def guard(request, call_next):
    """Validate extension traffic even if the legacy demo's auth is disabled."""
    path = request.url.path
    if path.startswith('/extension/auth/'):
        return await call_next(request)
    is_extension = path.startswith('/extension/')
    has_bearer = 'authorization' in request.headers
    if not is_extension and not has_bearer:
        return await call_next(request)
    try:
        if not allowed_origin(request):
            raise HTTPException(403, '허용된 확장 프로그램에서 연결해 주세요.')
        if request.headers.get('x-sullivan-client') not in ('student', 'guardian'):
            raise HTTPException(403, '프로그램 식별 정보가 필요합니다.')
        if path.startswith('/extension/v1/'):
            role=path.split('/')[3]
            if role in ('student','guardian') and request.headers.get('x-sullivan-client')!=role:
                raise HTTPException(403,'이 프로그램의 계정 기능만 사용할 수 있습니다.')
        from app.extension_accounts import check_version
        check_version(request)
        if has_bearer:
            user = current(request)
            if user is None:
                raise HTTPException(401, '다시 로그인해 주세요.')
            if path.startswith('/local/'):
                if path in ('/local/login', '/local/logout', '/local/setup', '/local/login-voice', '/local/status'):
                    raise HTTPException(403, '확장 전용 로그인 기능을 사용해 주세요.')
                # Legacy handlers enforce role and ownership; the guard also runs
                # when the legacy public demo mode disables its own guard.
            elif path.startswith('/v1/'):
                accounts.require(request, 'guardian')
                parts = path.split('/')
                if len(parts) > 3 and parts[2] == 'lectures':
                    with accounts.db() as con:
                        owner = con.execute('SELECT guardian FROM owners WHERE session=?', (parts[3],)).fetchone()
                        if not owner or owner[0] != user['id']:
                            raise HTTPException(403, '다른 계정의 분석 세션입니다.')
            elif not is_extension:
                raise HTTPException(403, '지원하지 않는 확장 요청입니다.')
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        return response
    except HTTPException as error:
        from fastapi.responses import JSONResponse
        return JSONResponse({'detail': error.detail}, status_code=error.status_code,
                            headers={'Cache-Control': 'no-store'})
