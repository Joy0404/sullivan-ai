"""Local-only launcher. Provider keys stay in process memory, never in files."""
import argparse
import getpass
import os
from pathlib import Path
import secrets
import sys
import threading
import webbrowser
import socket

ROOT = Path(__file__).resolve().parent

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
    parser.add_argument('--port',type=int,default=8767)
    args = parser.parse_args()
    try:
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',args.port))
    except OSError:
        raise RuntimeError(f'{args.port} 포트에 이미 서버가 있습니다. 이전 실행 창에서 Control+C로 종료한 뒤 이 작업본을 다시 실행하세요.') from None
    os.chdir(ROOT)
    sys.path.insert(0,str(ROOT/'apps/api'))
    from app.runtime import BUILD
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
