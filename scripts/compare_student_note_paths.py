import os,sys,tempfile,socket,threading,time,json,hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'apps/api'))
from build_extensions import build
import argparse
parser=argparse.ArgumentParser(description='Compare identical prepared sample navigation against a read-only backup tree.');parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,default=ROOT/'docs/verification/2026-11-16-student-notes/paths-before-after.json');args=parser.parse_args();old=args.baseline.resolve()
namespace={'__file__':str(old/'scripts/build_extensions.py'),'__name__':'backup_builder'}
exec(compile((old/'scripts/build_extensions.py').read_text(),namespace['__file__'],'exec'),namespace)
with tempfile.TemporaryDirectory(prefix='student-path-comparison-') as d:
 temp=Path(d);os.environ.update(SULLIVAN_ACCOUNTS_DB=str(temp/'accounts.sqlite'),SULLIVAN_ROLE_AUTH='1',SULLIVAN_PRODUCTION='0',GEMINI_API_KEY='',DEMO_USAGE_DB=str(temp/'usage.sqlite'))
 from app.main import app
 import uvicorn
 sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];origin=f'http://127.0.0.1:{port}'
 server=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False));thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
 while not server.started:time.sleep(.02)
 from fastapi.testclient import TestClient
 c=TestClient(app,base_url=origin)
 def headers(role,token=''):return {'X-Sullivan-Client':role,'X-Local-Request':'1',**({'Authorization':'Bearer '+token} if token else {})}
 guardian=c.post('/extension/v1/guardian/register',headers=headers('guardian'),json={'username':'comparison-parent','password':'extension-pass-123'}).json()
 student=c.post('/local/students',headers=headers('guardian',guardian['token']),json={'username':'comparison-student','password':'extension-pass-123','name':'비교 학생'}).json()
 ident=c.post('/local/samples/science/assign',headers=headers('guardian',guardian['token']),json={'students':[student['id']]}).json()['id']
 result={}
 try:
  with sync_playwright() as pw:
   for label,builder in [('before',namespace['build']),('after',build)]:
    packages=builder(origin,temp/label);path=packages/'student'
    context=pw.chromium.launch_persistent_context(str(temp/(label+'-profile')),channel='chromium',headless=True,args=[f'--disable-extensions-except={path}',f'--load-extension={path}'])
    worker=context.service_workers[0] if context.service_workers else context.wait_for_event('serviceworker');extension=worker.url.split('/')[2]
    page=context.new_page();page.goto(f'chrome-extension://{extension}/index.html');expect(page.locator('#username')).to_be_visible()
    page.locator('#access-mode').select_option('silent');page.locator('#username').fill('comparison-student');page.locator('#password').fill('extension-pass-123');page.locator('#login-form button').focus();page.keyboard.press('Enter');expect(page.locator('#lectures button')).to_have_count(1)
    page.locator('#lectures button').focus();page.keyboard.press('Enter');expect(page.locator('#lesson')).to_be_visible();expect(page.locator('#material')).not_to_be_empty()
    snapshot=page.evaluate("async id=>{const{request}=await import('./client.js');return (await request('/extension/v1/student/lectures/'+id)).snapshot;}",ident)
    stamp=hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    if label=='before':
     page.locator('#lesson-title').focus();visited=[];stuck=None
     for step in range(300):
      previous=page.evaluate('document.activeElement.outerHTML');page.keyboard.press('Tab');active=page.evaluate('document.activeElement.outerHTML');visited.append(page.evaluate('document.activeElement.id||document.activeElement.textContent.slice(0,40)'))
      if page.locator('#note').evaluate('(e)=>e===document.activeElement'):break
      if active==previous:stuck={'step':step+1,'control':visited[-1]};break
     # Controlled comparison with every disclosure opened to bypass the known trap.
     page.evaluate("document.querySelectorAll('details').forEach(e=>e.open=true)");page.locator('#lesson-title').focus()
     expanded=[]
     for _ in range(400):
      page.keyboard.press('Tab');expanded.append(page.evaluate('document.activeElement.id||document.activeElement.textContent.slice(0,40)'))
      if page.locator('#note').evaluate('(e)=>e===document.activeElement'):break
     assert expanded[-1]=='note',expanded[-8:]
     page.evaluate("document.querySelectorAll('details').forEach(e=>e.open=false)");page.locator('#lesson-title').focus()
     nav_keys=0
     for _ in range(20):
      page.keyboard.press('Tab');nav_keys+=1
      if page.get_by_role('link',name='학습 기록',exact=True).evaluate('(e)=>e===document.activeElement'):break
     page.keyboard.press('Enter');nav_keys+=1
     for _ in range(30):
      page.keyboard.press('Tab');nav_keys+=1
      if page.locator('#note').evaluate('(e)=>e===document.activeElement'):break
     assert page.locator('#note').evaluate('(e)=>e===document.activeElement')
     result[label]={'advertised_records_link_keys_to_memo':nav_keys,'snapshot_sha256':stamp,'paragraphs':len(snapshot['passage']['paragraphs']),'sentences':snapshot['passage']['sentence_count'],'closed_default_stuck':stuck,'default_tab_path':visited,'all_details_open_forward_tabs_to_legacy_memo':len(expanded),'sentence_buttons':page.locator('#material button.sentence').count()}
    else:
     page.locator('#player-title').focus();visited=[]
     for _ in range(30):
      page.keyboard.press('Shift+Tab');visited.append(page.evaluate('document.activeElement.id'))
      if visited[-1]=='task-notes-button':break
     assert visited[-1]=='task-notes-button';page.keyboard.press('Enter');expect(page.locator('#notes-title')).to_be_focused();page.keyboard.press('Tab');expect(page.locator('#new-note')).to_be_focused();page.keyboard.press('Enter');expect(page.locator('#note-body')).to_be_focused()
     result[label]={'snapshot_sha256':stamp,'reverse_tabs_to_notes_task':len(visited),'then':['Enter opens Notes','Tab reaches New Note','Enter starts editor'],'total_keys_to_editor':len(visited)+3,'sentence_buttons':page.locator('#material button.sentence').count()}
    context.close()
 finally:server.should_exit=True;thread.join(timeout=10)
 assert result['before']['snapshot_sha256']==result['after']['snapshot_sha256']
 output=args.output;output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
