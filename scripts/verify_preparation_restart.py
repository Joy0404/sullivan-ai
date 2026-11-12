"""Real process restart with a temporary DB and a controlled pending-job delay."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
SERVER = '''
import asyncio,sys,uvicorn
from app.main import app
from app import guardian_preparation as preparation
if sys.argv[2] == 'delayed':
    original = preparation.run
    async def delayed(ident, *args, **kwargs):
        preparation.update(ident, 'running', '재시작 검증을 위한 테스트 지연')
        await asyncio.sleep(60)
        await original(ident, *args, **kwargs)
    preparation.run = delayed
uvicorn.run(app, host='127.0.0.1', port=int(sys.argv[1]), log_level='error', access_log=False)
'''


def main():
    with tempfile.TemporaryDirectory(prefix='sullivan-restart-') as temporary:
        temp = Path(temporary)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        env = os.environ | {'PYTHONPATH': str(ROOT / 'apps/api'), 'SULLIVAN_ACCOUNTS_DB': str(temp / 'accounts.sqlite'),
            'SULLIVAN_ROLE_AUTH': '1', 'SULLIVAN_PRODUCTION':'0', 'SULLIVAN_MIN_EXTENSION_VERSION':'0.1.0', 'GEMINI_API_KEY': '', 'DEMO_USAGE_DB': str(temp / 'usage.sqlite')}
        process = None
        def start(delayed=False):
            nonlocal process
            process = subprocess.Popen([sys.executable, '-c', SERVER, str(port), 'delayed' if delayed else 'normal'],
                env=env, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                try:
                    if httpx.get(base + '/health', timeout=.3).status_code == 200:
                        return
                except httpx.HTTPError:
                    pass
                time.sleep(.05)
            raise RuntimeError('Restart test server did not start')
        def stop(force=False):
            if process and process.poll() is None:
                process.kill() if force else process.terminate()
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
        try:
            start()
            with httpx.Client(base_url=base, timeout=10) as client:
                headers = {'X-Sullivan-Client': 'guardian', 'X-Local-Request': '1'}
                registered = client.post('/extension/v1/guardian/register', headers=headers,
                    json={'username': 'restartguardian', 'password': 'restart-pass-123'}).json()
                headers['Authorization'] = 'Bearer ' + registered['token']
                student = client.post('/local/students', headers=headers,
                    json={'username': 'restartstudent', 'password': 'restart-pass-123'}).json()['id']
                payload = {'title': '재시작 후 배정할 자료', 'assets': [{'name': '지문.txt', 'kind': 'passage', 'content': '완료한 지문은 서버 재시작 뒤에도 남습니다.'}]}
                complete = client.post('/extension/v1/guardian/preparations', headers=headers, json=payload).json()['id']
                for _ in range(50):
                    job = client.get('/extension/v1/guardian/preparations/' + complete, headers=headers).json()
                    if job['state'] == 'completed': break
                    time.sleep(.05)
                assert job['state'] == 'completed'
                stop(); start(delayed=True)
                publish = client.post('/extension/v1/guardian/preparations/' + complete + '/publish',
                    headers=headers, json={'students': [student]})
                assert publish.status_code == 200, publish.text
                pending = client.post('/extension/v1/guardian/preparations', headers=headers,
                    json=payload | {'title': '중단될 작업'}).json()['id']
                assert client.get('/extension/v1/guardian/preparations/' + pending, headers=headers).json()['state'] == 'running'
                stop(force=True); start()
                interrupted = client.get('/extension/v1/guardian/preparations/' + pending, headers=headers).json()
                assert interrupted['state'] == 'interrupted'
                assert client.post('/extension/v1/guardian/preparations/' + pending + '/publish',
                    headers=headers, json={'students': [student]}).status_code == 409
                assert client.get('/extension/v1/guardian/preparations/' + complete, headers=headers).json()['state'] == 'completed'
            report = {'result': 'passed', 'actual_process_restarts': 2, 'controlled_pending_job_delay': True,
                'checks': ['persisted account and independent session', 'completed result published after restart',
                    'killed running job becomes interrupted', 'interrupted output cannot publish', 'no automatic provider retry'],
                'limitations': ['Single-process server; no paid provider call or original-video crash recovery tested']}
            (ROOT / 'docs/verification/extension-preparation-restart-results.json').write_text(json.dumps(report, indent=2)+'\n')
            print(json.dumps(report, indent=2))
        finally:
            stop()


if __name__ == '__main__':
    main()
