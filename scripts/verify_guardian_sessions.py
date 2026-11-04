"""Guardian async identity/session regressions; disposable DB and mocked delayed responses."""
from pathlib import Path
import json, os, socket, sys, tempfile, threading, time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps/api'))
import uvicorn
from playwright.sync_api import sync_playwright, expect
from verify_roles_browser import MOCK


def main():
 with tempfile.TemporaryDirectory(prefix='sullivan-session-check-') as tmp:
  os.environ.update(SULLIVAN_ACCOUNTS_DB=tmp+'/accounts.sqlite',DEMO_USAGE_DB=tmp+'/usage.sqlite',SULLIVAN_ROLE_AUTH='1',SULLIVAN_SYSTEM_LOGIN_VOICE='0')
  for key in ['GEMINI_API_KEY','DEMO_ACCESS_CODE','DATABASE_URL','DATABASE_URL_UNPOOLED','RENDER','LINK_ANALYZER_URL','LINK_ANALYZER_TOKEN']:os.environ.pop(key,None)
  from app.main import app
  sock=socket.socket();sock.bind(('127.0.0.1',0));base=f'http://127.0.0.1:{sock.getsockname()[1]}'
  server=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False))
  thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
  while not server.started:time.sleep(.01)
  checks=[]
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch();context=browser.new_context(viewport={'width':1280,'height':900})
    context.add_init_script(MOCK+'speechSynthesis.speak=()=>{};speechSynthesis.cancel=()=>{};')
    api=context.request;headers={'X-Local-Request':'1'}
    assert api.post(base+'/local/setup',headers=headers,data={'username':'guardian','password':'test-pass-123'}).status==200
    for username in ['student.one','student.two']:
     assert api.post(base+'/local/students',headers=headers,data={'username':username,'password':'test-pass-123','name':'같은 이름'}).status==200
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) or r.request.url=='about:blank' else r.abort())
    def home():page.wait_for_function("document.body.dataset.role==='guardian' && document.querySelector('#guardian-dashboard').getAttribute('aria-busy')==='false'")
    def login(username,role):
     page.locator('#login-role-'+role).press('Enter');page.locator('#login-username').fill(username);page.locator('#login-password').fill('test-pass-123')
     if role=='student':page.locator('#login-focus-voice').uncheck()
     page.locator('#login-submit').press('Enter')
     page.wait_for_function("Portal.user && !document.querySelector('#login-submit').disabled")
     if role=='guardian':home()
     else:
      if page.locator('#onboarding-done').count():page.locator('#onboarding-done').press('Enter')
      page.wait_for_function("document.body.dataset.role==='student' && !document.querySelector('#portal-home').classList.contains('hidden')")
    page.goto(base);home()
    headings=page.locator('.guardian-student h3').all_text_contents()
    assert headings==['같은 이름 (student.one)','같은 이름 (student.two)']
    for width in [320,390,1280]:
     page.set_viewport_size({'width':width,'height':900});assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.set_viewport_size({'width':1280,'height':900})
    # Distinct identity in both live status and disclosure description.
    page.locator('.guardian-learning-progress summary').nth(0).press('Enter')
    page.wait_for_function("document.querySelector('.guardian-learning-progress [role=status]').textContent.includes('아직 배정')")
    assert 'student.one' in page.locator('.guardian-learning-progress [role=status]').first.inner_text()
    checks.append('duplicate display names have unique visible and live identities')
    for target,old_status in [('student',401),('guardian',401),('student',200)]:
     page.reload();home();held=[]
     page.route('**/local/students/*/progress',lambda route:held.append(route))
     page.locator('.guardian-learning-progress summary').first.press('Enter');page.wait_for_function("document.querySelector('.guardian-learning-progress [role=status]').textContent.includes('불러오고')")
     while not held:page.wait_for_timeout(10)
     page.locator('#portal-logout').press('Enter');login('student.one' if target=='student' else 'guardian',target)
     before=page.evaluate('({id:Portal.user.id,role:Portal.user.role,focus:document.activeElement.id})')
     held[0].fulfill(status=old_status,content_type='application/json',body=json.dumps({'detail':'old request'} if old_status==401 else {'lectures':[]}))
     page.wait_for_timeout(150)
     after=page.evaluate('({id:Portal.user?.id,role:Portal.user?.role,focus:document.activeElement.id})')
     assert after==before,(before,after)
     assert api.get(base+'/local/me').json()['id']==before['id']
     page.unroute('**/local/students/*/progress')
     checks.append(f'old {old_status} preserves newly logged-in {target}, including same guardian identity')
     if target=='student':page.locator('#portal-logout').press('Enter');login('guardian','guardian')
    # A genuine current-session 401 must retain the original fail-closed behavior.
    page.reload();home();page.route('**/local/students/*/progress',lambda r:r.fulfill(status=401,content_type='application/json',body='{"detail":"expired current session"}'))
    page.locator('.guardian-learning-progress summary').first.press('Enter')
    page.wait_for_function("!Portal.user && document.body.dataset.role==='signed-out'")
    expect(page.locator('#login-role-student')).to_be_focused();page.unroute('**/local/students/*/progress')
    checks.append('current-session 401 still signs out and focuses login')
    login('guardian','guardian');page.locator('#guardian-prepare').press('Enter');page.locator('#wizard-next').press('Enter');page.locator('button[data-wizard-source=link]').press('Enter')
    page.locator('#video-url').fill('https://example.com/lecture.mp4');page.locator('#portal-logout').press('Enter');login('guardian','guardian')
    page.locator('#guardian-prepare').press('Enter');page.locator('#wizard-next').press('Enter');page.locator('button[data-wizard-source=link]').press('Enter')
    assert page.locator('#video-url').input_value()=='' and page.locator('#video-link-state').inner_text()=='링크 미입력'
    checks.append('logout resets link value and displayed link state')
    page.locator('#lecture-form [data-guardian-home]').press('Enter');home();held=[]
    page.route('**/local/samples/*/assign',lambda route:held.append(route));page.locator('#guardian-sample-panel > summary').evaluate('(e)=>e.parentElement.open=true')
    page.locator('#sample-assign-student').select_option(index=1);page.locator('#sample-assign-submit').press('Enter')
    page.wait_for_function("document.querySelector('#sample-assign-status').textContent.includes('student.one')")
    assert page.locator('#sample-assign-status').get_attribute('role')=='status'
    while not held:page.wait_for_timeout(10)
    held[0].continue_();page.wait_for_function("!document.querySelector('#sample-assign-submit').disabled")
    assert page.locator('#sample-assign-status').inner_text()==''
    assert '준비 완료' in page.locator('#sample-assign-receipt').inner_text()
    checks.append('sample assignment has persistent polite loading status, cleared on completion')
    assert not errors,errors
    out=ROOT/'docs/verification';out.mkdir(parents=True,exist_ok=True)
    (out/'guardian-session-results.json').write_text(json.dumps({'passed':True,'checks':checks,'page_errors':errors,'providers':'blocked; no paid analysis','screen_reader':'not tested'},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(checks,ensure_ascii=False));browser.close()
  finally:server.should_exit=True;thread.join(timeout=5)

if __name__=='__main__':main()
