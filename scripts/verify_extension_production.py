"""Exercise production startup policy locally with synthetic IDs and a temporary DB.

This verifies application configuration, not public TLS or a real deployment.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

import httpx

ROOT=Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='sullivan-production-') as temporary:
        temp=Path(temporary)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        env=os.environ|{'PYTHONPATH':str(ROOT/'apps/api'),'SULLIVAN_PRODUCTION':'1',
            'SULLIVAN_PUBLIC_URL':'https://sullivan.example','SULLIVAN_ROLE_AUTH':'1',
            'SULLIVAN_EXTENSION_CLIENTS':json.dumps({'student':'a'*32,'guardian':'b'*32}),
            'SULLIVAN_ACCOUNTS_DB':str(temp/'accounts.sqlite'),'SULLIVAN_PERSISTENT_STORAGE':'1',
            'SULLIVAN_MIN_EXTENSION_VERSION':'0.4.0','WEB_CONCURRENCY':'1','SULLIVAN_SIGNUP_ENABLED':'1',
            'GEMINI_API_KEY':'','DEMO_USAGE_DB':str(temp/'usage.sqlite')}
        for key in ('DATABASE_URL','DATABASE_URL_UNPOOLED','RENDER'):env.pop(key,None)
        command=[sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(port),'--no-access-log']
        invalid=env|{'SULLIVAN_PERSISTENT_STORAGE':'0'}
        with tempfile.TemporaryFile() as logs:
            refused=subprocess.run(command,env=invalid,cwd=ROOT,stdout=logs,stderr=logs,timeout=15)
            assert refused.returncode!=0,'Incomplete production configuration started'
            process=subprocess.Popen(command,env=env,cwd=ROOT,stdout=logs,stderr=logs)
            try:
                deadline=time.monotonic()+15
                with httpx.Client(base_url=f'http://127.0.0.1:{port}',timeout=.5) as client:
                    while True:
                        if process.poll() is not None:raise RuntimeError('Configured production process exited')
                        try:
                            if client.get('/health').status_code==200:break
                        except httpx.HTTPError:pass
                        if time.monotonic()>deadline:raise RuntimeError('Production startup timed out')
                        time.sleep(.05)
                    headers={'X-Sullivan-Client':'student','X-Sullivan-Version':'0.4.0'}
                    response=client.get('/extension/v1/student/capabilities',headers=headers)
                    assert response.status_code==200 and response.json()['production']
                    assert response.json()['signup_enabled'] is True
                    assert client.post('/extension/v1/student/session',headers=headers,json={'username':'fixture','password':'fixture-pass-123'}).status_code==403
                    assert client.get('/extension/v1/student/capabilities',headers=headers|{'X-Sullivan-Version':'0.3.0'}).status_code==426
                    assert client.get('/extension/v1/student/capabilities',headers=headers|{'Origin':'chrome-extension://'+'c'*32}).status_code==403
            finally:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
    report={'result':'passed','checks':['incomplete configuration refuses startup','configured production process starts',
        'signup enabled without administrator code','raw password extension login blocked','old version rejected','unregistered origin rejected'],
        'limitations':['Synthetic HTTPS configuration over internal loopback HTTP; public TLS and store IDs not verified']}
    (ROOT/'docs/verification/extension-production-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
