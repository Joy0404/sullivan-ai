"""Exercise sample publication over HTTP across a real server-process restart."""
from pathlib import Path
import json,os,socket,subprocess,sys,tempfile,time
import httpx

ROOT=Path(__file__).resolve().parents[1]

def main():
 with tempfile.TemporaryDirectory(prefix='sullivan-restart-') as temp:
  with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
  base=f'http://127.0.0.1:{port}'
  env=dict(os.environ)
  for key in ['GEMINI_API_KEY','DEMO_ACCESS_CODE','DATABASE_URL','DATABASE_URL_UNPOOLED','RENDER']:env.pop(key,None)
  env.update(SULLIVAN_ROLE_AUTH='1',SULLIVAN_ACCOUNTS_DB=str(Path(temp)/'accounts.sqlite'),PYTHONDONTWRITEBYTECODE='1')
  process=None
  def start():
   nonlocal process
   process=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(port),'--log-level','error','--no-access-log'],cwd=ROOT/'apps/api',env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   for _ in range(120):
    try:
     r=httpx.get(base+'/local/status',timeout=.4)
     if r.status_code==200:return r.json()['instance']
    except httpx.HTTPError:pass
    if process.poll() is not None:raise AssertionError('Test server exited')
    time.sleep(.05)
   raise AssertionError('Test server did not start')
  def stop():
   if process and process.poll() is None:process.terminate();process.wait(timeout=10)
  try:
   first=start();headers={'X-Local-Request':'1'}
   with httpx.Client(base_url=base,headers=headers) as guardian,httpx.Client(base_url=base,headers=headers) as student:
    assert guardian.post('/local/setup',json={'username':'guardian','password':'test-pass-123'}).status_code==200
    ident=guardian.post('/local/students',json={'username':'student1','password':'test-pass-123','name':'학생'}).json()['id']
    assert student.post('/local/login',json={'username':'student1','password':'test-pass-123','role':'student'}).status_code==200
    ids=[]
    for sample in ['science','history']:
     result=guardian.post('/local/samples/'+sample+'/assign',json={'students':[ident]})
     assert result.status_code==200 and result.json()['ready'];ids.append(result.json()['id'])
    assert [x['id'] for x in student.get('/local/lectures').json()]==ids
    stop();second=start();assert first!=second
    assert [x['id'] for x in student.get('/local/lectures').json()]==ids
    for ident in ids:
     data=student.get('/local/lectures/'+ident)
     assert data.status_code==200 and data.json()['snapshot']['active_mode']!='waiting'
    result={'both_samples_without_preview':True,'actual_process_restart':True,'student_session_and_assignments_persist':True,'snapshots_open_after_restart':True,'real_providers':'not called'}
    target=ROOT/'docs/verification/sample-restart-results.json';target.write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
  finally:stop()
if __name__=='__main__':main()
