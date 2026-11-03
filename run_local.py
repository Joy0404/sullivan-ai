"""Local-only launcher. Provider keys stay in process memory, never in files."""
import argparse
import getpass
import http.client
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import threading
import time
import webbrowser
import socket

ROOT = Path(__file__).resolve().parent

def port_available(port):
    try:
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(('127.0.0.1', port))
        return True
    except OSError:
        return False


def local_server(port):
    """Identify this workspace's listener without reading arguments or secrets."""
    try:
        result = subprocess.run(
            ['lsof', '-nP', '-t', f'-iTCP:{port}', '-sTCP:LISTEN'],
            capture_output=True, text=True, timeout=3, check=True,
        )
        pids = {int(line) for line in result.stdout.splitlines() if line.strip()}
        if len(pids) != 1:
            return None
        pid = pids.pop()
        result = subprocess.run(
            ['lsof', '-a', '-p', str(pid), '-d', 'cwd', '-Fn'],
            capture_output=True, text=True, timeout=3, check=True,
        )
        if not any(line.startswith('n') and Path(line[1:]).resolve() == ROOT
                   for line in result.stdout.splitlines()):
            return None
        def read_public(path):
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
            try:
                connection.request('GET', path)
                response = connection.getresponse()
                if response.status != 200:
                    raise ValueError('not a Sullivan endpoint')
                return json.loads(response.read(16_384))
            finally:
                connection.close()
        status, health = read_public('/local/status'), read_public('/health')
        if (not isinstance(status, dict) or not isinstance(health, dict)
                or not status.get('instance') or not status.get('build')
                or health.get('product') != 'sullivan-ai-internet-lecture-agent'):
            return None
        return {'pid': pid, 'build': status['build'],
                'sample': health.get('real_analysis_access') == 'disabled'}
    except (OSError, ValueError, subprocess.SubprocessError, http.client.HTTPException):
        return None


def handle_existing(args, build):
    """Reuse or explicitly restart only an identified Sullivan workspace."""
    if port_available(args.port):
        return False
    server = local_server(args.port)
    if server is None:
        raise RuntimeError(
            f'{args.port} 포트를 다른 프로그램이나 확인할 수 없는 서버가 사용 중입니다. '
            '자동으로 종료하지 않았습니다. 해당 실행 창에서 종료한 뒤 다시 실행하세요.')
    if args.restart:
        # Recheck ownership immediately before signaling; never stop an unknown listener.
        confirmed = local_server(args.port)
        if not confirmed or confirmed['pid'] != server['pid']:
            raise RuntimeError('실행 중인 서버가 바뀌었습니다. 자동으로 종료하지 않았습니다.')
        print('이 작업본의 기존 서버를 종료하고 다시 시작합니다.', flush=True)
        os.kill(server['pid'], signal.SIGINT)
        deadline = time.monotonic() + 10
        while not port_available(args.port):
            if time.monotonic() >= deadline:
                raise RuntimeError('서버 종료를 기다리는 시간이 지났습니다. 기존 실행 창을 확인하세요.')
            time.sleep(.1)
        return False
    if server['build'] != build:
        raise RuntimeError('이 작업본의 이전 버전 서버가 실행 중입니다. '
                           'bash START_LOCAL.command --restart 로 다시 시작하세요.')
    if args.sample and not server['sample']:
        raise RuntimeError('현재 서버에는 실제 분석이 설정되어 있습니다. 샘플 전용으로 바꾸려면 '
                           'bash START_LOCAL.command --restart --sample 을 실행하세요.')
    print('이 작업본이 이미 실행 중입니다. 기존 앱을 엽니다.')
    if server['sample']:
        print('현재 샘플 전용 모드입니다. 실제 Gemini 분석을 새로 설정하려면\n'
              'bash START_LOCAL.command --restart 를 실행하세요.')
    else:
        print('기존 서버의 실제 분석 설정을 유지합니다.')
    url = f'http://127.0.0.1:{args.port}'
    print(f'접속 주소: {url}\n기존 계정과 저장된 학습 기록은 유지됩니다.')
    if not args.no_open:
        webbrowser.open(url)
    return True


def select_model(api_key):
    import httpx
    # Read model availability without uploading media or invoking generation.
    try:
        result = httpx.get('https://generativelanguage.googleapis.com/v1beta/models', headers={'x-goog-api-key':api_key}, timeout=20)
        if result.status_code != 200:
            raise RuntimeError(f'Gemini 키 확인 실패 (HTTP {result.status_code}). 키와 API 사용 권한을 확인하세요.')
        names = [m['name'].removeprefix('models/') for m in result.json().get('models',[]) if 'generateContent' in m.get('supportedGenerationMethods',[])]
    except httpx.HTTPError:
        raise RuntimeError('Gemini 서버에 연결할 수 없습니다. 네트워크 연결을 확인하세요.') from None
    model = 'gemini-2.5-flash'
    if model not in names:
        raise RuntimeError('이 키의 모델 목록에 gemini-2.5-flash가 없습니다. 다른 모델로 전환하지 않았습니다.')
    return model

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample',action='store_true',help='키 없이 샘플 기능만 실행')
    parser.add_argument('--no-open',action='store_true')
    parser.add_argument('--restart',action='store_true',help='확인된 이 작업본의 서버만 종료하고 새로 설정해 실행')
    parser.add_argument('--port',type=int,default=8767)
    args = parser.parse_args()
    os.chdir(ROOT)
    sys.path.insert(0,str(ROOT/'apps/api'))
    from app.runtime import BUILD
    if handle_existing(args, BUILD):
        return
    print(f'실행 작업본: {ROOT.name}\n빌드: {BUILD}')
    os.environ['SULLIVAN_ROLE_AUTH']='1'
    os.environ['SULLIVAN_ACCOUNTS_DB']=str(ROOT/'data/private/accounts.sqlite')
    # This isolated copy never uses the deployed Render / Neon database.
    for name in ['RENDER','DATABASE_URL','DATABASE_URL_UNPOOLED','TRUST_RENDER_PROXY','LINK_ANALYZER_URL','LINK_ANALYZER_TOKEN']:
        os.environ.pop(name,None)
    os.environ['RESTRICT_SAMPLE_LINKS']='0'
    os.environ['LOCAL_TEST_UNLIMITED']='1'
    os.environ['DEMO_USAGE_DB']=str(ROOT/'data/private/local-usage.sqlite')
    if not args.sample:
        key = os.getenv('GEMINI_API_KEY','').strip() or getpass.getpass('Gemini API 키 (입력은 화면에 표시되지 않음): ').strip()
        if not key:raise RuntimeError('실제 분석용 키가 필요합니다. 키 없는 실행은 --sample을 사용하세요.')
        model = select_model(key)
        code = getpass.getpass('사이트에 입력할 체험 비밀번호를 정하세요 (입력 숨김): ').strip()
        if not code:raise RuntimeError('체험 비밀번호를 입력하세요.')
        os.environ.update(GEMINI_API_KEY=key,DEMO_ACCESS_CODE=code,GEMINI_MODEL=model,GEMINI_AGENT_MODEL=model)
        print(f'실제 분석 준비 완료 · 모델: {model}')
    else:
        os.environ.pop('GEMINI_API_KEY',None)
        os.environ.pop('DEMO_ACCESS_CODE',None)
        print('샘플 전용 실행: 실제 Gemini 호출 없음')
    url = f'http://127.0.0.1:{args.port}'
    print(f'접속 주소: {url}\n종료: 이 창에서 Control+C\n테스트용 분석 횟수 제한 없음 · 영상 100MB 이하 · 분석 최대 3분')
    if not args.no_open:
        threading.Timer(2,lambda:webbrowser.open(url)).start()
    import uvicorn
    uvicorn.run('app.main:app',host='127.0.0.1',port=args.port,proxy_headers=False,access_log=False)

if __name__=='__main__':
    try:main()
    except (RuntimeError,OSError) as error:
        print(str(error),file=sys.stderr)
        raise SystemExit(1)
