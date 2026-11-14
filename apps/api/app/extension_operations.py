"""Production preflight and a single-process lease for the private SQLite runtime."""
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit


def diagnose():
    errors=[]
    if os.getenv('SULLIVAN_PRODUCTION')!='1':return {'ready':False,'mode':'development','errors':['운영 모드가 아닙니다.'],'protocol':1}
    origin=os.getenv('SULLIVAN_PUBLIC_URL','').rstrip('/')
    try:
        parsed=urlsplit(origin)
        valid=parsed.scheme=='https' and bool(parsed.hostname) and parsed.hostname not in ('localhost','127.0.0.1','::1') and not any((parsed.path,parsed.query,parsed.fragment,parsed.username,parsed.password))
        parsed.port  # Validate malformed ports without exposing the configured value.
    except ValueError:valid=False
    if not valid:errors.append('SULLIVAN_PUBLIC_URL에 실제 HTTPS 출처를 지정하세요.')
    if not re.fullmatch(r'\d+\.\d+\.\d+',os.getenv('SULLIVAN_MIN_EXTENSION_VERSION','0.1.0')):
        errors.append('최소 확장 버전은 숫자.숫자.숫자 형식이어야 합니다.')
    try:
        clients=json.loads(os.getenv('SULLIVAN_EXTENSION_CLIENTS','{}'))
        assert isinstance(clients,dict) and set(clients)=={'student','guardian'}
        assert all(isinstance(value,str) and re.fullmatch('[a-p]{32}',value) for value in clients.values())
        assert clients['student']!=clients['guardian']
    except (ValueError,AssertionError,TypeError):errors.append('서로 다른 학생·보호자 확장 ID를 SULLIVAN_EXTENSION_CLIENTS에 등록하세요.')
    database=os.getenv('SULLIVAN_ACCOUNTS_DB','')
    path=Path(database)
    if not database or not path.is_absolute() or not path.parent.is_dir() or not os.access(path.parent,os.W_OK):
        errors.append('SULLIVAN_ACCOUNTS_DB는 쓰기 가능한 영속 볼륨의 절대 경로여야 합니다.')
    if os.getenv('SULLIVAN_PERSISTENT_STORAGE')!='1':errors.append('영속 볼륨을 연결하고 SULLIVAN_PERSISTENT_STORAGE=1을 지정하세요.')
    if os.getenv('SULLIVAN_ROLE_AUTH','1')=='0':errors.append('운영 모드에서 역할 인증을 끌 수 없습니다.')
    if os.getenv('WEB_CONCURRENCY','1')!='1':errors.append('현재 SQLite 작업 실행기는 서버 프로세스 한 개만 지원합니다.')
    return {'ready':not errors,'mode':'production','errors':errors,'protocol':1,'database':'configured' if database else 'missing','single_process':True}


@asynccontextmanager
async def lifespan(app):
    lease=None
    if os.getenv('SULLIVAN_PRODUCTION')=='1':
        result=diagnose()
        if not result['ready']:raise RuntimeError('운영 설정 오류: '+' '.join(result['errors']))
        try:
            import fcntl
        except ImportError as error:raise RuntimeError('운영 서버는 POSIX 파일 잠금을 지원해야 합니다. 로컬 개발은 운영 모드 없이 실행하세요.') from error
        lock_path=Path(os.environ['SULLIVAN_ACCOUNTS_DB']).resolve().with_suffix('.server-lock')
        lease=lock_path.open('a')
        try:fcntl.flock(lease.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            lease.close();raise RuntimeError('같은 계정 DB를 사용하는 서버가 이미 실행 중입니다.') from None
        from app.local_access import db
        from app.guardian_preparation import recover
        with db() as con:recover(con)
    try:yield
    finally:
        if lease:lease.close()
