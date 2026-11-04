"""Real local HTTP/browser startup flow; native process boundary held for cancellation tests."""
from pathlib import Path
import json,os,socket,sys,tempfile,threading,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps/api'))
import uvicorn
from playwright.sync_api import sync_playwright,expect

def main():
 with tempfile.TemporaryDirectory(prefix='sullivan-startup-') as tmp:
  os.environ.update(SULLIVAN_ROLE_AUTH='1',SULLIVAN_ACCOUNTS_DB=str(Path(tmp)/'accounts.sqlite'),GEMINI_API_KEY='',SULLIVAN_SYSTEM_LOGIN_VOICE='1')
  for key in ['DATABASE_URL','DATABASE_URL_UNPOOLED','RENDER']:os.environ.pop(key,None)
  from app.main import app
  from app import login_voice
  login_voice.PLATFORM='darwin';login_voice.korean_voice=lambda:'Yuna'
  login_voice.SAY=type('Binary',(),{'is_file':lambda self:True})()
  processes=[];hold=[False]
  class Process:
   def __init__(self,args,**kwargs):
    assert args==['/usr/bin/say','-v','Yuna','학생 로그인'];self.stopped=False;self.release=threading.Event();self.done=False
    if not hold[0]:self.release.set()
    processes.append(self)
   def poll(self):return -15 if self.stopped else 0 if self.done else None
   def wait(self,timeout):
    assert self.release.wait(timeout);self.done=True;return -15 if self.stopped else 0
   def terminate(self):self.stopped=True;self.release.set()
   def kill(self):self.terminate()
  sock=socket.socket();sock.bind(('127.0.0.1',0));base=f'http://127.0.0.1:{sock.getsockname()[1]}'
  server=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False))
  thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
  while not server.started:time.sleep(.01)
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch();context=browser.new_context()
    login_voice.subprocess.Popen=Process
    context.add_init_script('''window.__spoken=[];speechSynthesis.resume=()=>{};speechSynthesis.cancel=()=>{};
      window.__nativeActivation=[];const originalFetch=fetch.bind(window);window.fetch=(url,options)=>{if(url==='/local/login-voice'&&JSON.parse(options.body).action==='start')__nativeActivation.push(navigator.userActivation.hasBeenActive);return originalFetch(url,options);};
      speechSynthesis.speak=u=>{__spoken.push(u.text);if(!navigator.userActivation.hasBeenActive){u.onerror?.({error:'not-allowed'});return;}u.onstart?.();u.onend?.();};''')
    # Popen is replaced only after Chromium's driver/browser have launched.
    api=context.request;h={'X-Local-Request':'1'}
    assert api.post(base+'/local/setup',headers=h,data={'username':'guardian','password':'fixture-pass-123'}).status==200
    api.post(base+'/local/logout',headers=h)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base);expect(page.locator('#login-role-student')).to_be_focused()
    page.wait_for_function('Portal.loginNative&&Portal.loginReady')
    page.wait_for_timeout(200)
    assert len(processes)==1 and processes[-1].done
    assert page.evaluate('__nativeActivation')==[False]
    assert page.evaluate('__spoken')==[]
    page.evaluate('SullivanFocusVoice.readInitial(document.activeElement)');assert len(processes)==1
    page.reload();page.wait_for_function('Portal.loginNative&&Portal.loginReady');page.wait_for_timeout(200)
    expect(page.locator('#login-role-student')).to_be_focused()
    assert len(processes)==2 and processes[-1].done and page.evaluate('__spoken')==[]
    # The native startup process remains cancellable while its HTTP result is pending.
    hold[0]=True;page.reload();page.wait_for_function('Portal.loginNative&&Portal.loginReady')
    page.wait_for_timeout(120);current=processes[-1];assert not current.done
    page.keyboard.press('Tab');expect(page.locator('#login-role-guardian')).to_be_focused()
    page.wait_for_timeout(200);assert current.stopped
    expect(page.locator('#login-role-guardian')).to_be_focused()
    assert page.evaluate('__spoken.at(-1)')=='보호자 로그인'
    page.keyboard.press('Enter');page.wait_for_timeout(150)
    count=page.evaluate('__spoken.length');page.keyboard.press('Tab');page.wait_for_timeout(100)
    assert page.evaluate('__spoken.length')==count and not page.evaluate('Portal.loginVoice')
    # A page hidden/unloaded before completion must not leave native speech running.
    page.reload();page.wait_for_function('Portal.loginNative&&Portal.loginReady');page.wait_for_timeout(120)
    current=processes[-1];page.evaluate('window.dispatchEvent(new PageTransitionEvent("pagehide"))')
    page.wait_for_timeout(200);assert current.stopped
    # A signed-in page must never run the login-only greeting.
    hold[0]=False
    assert api.post(base+'/local/login',headers=h,data={'username':'guardian','password':'fixture-pass-123','role':'guardian'}).status==200
    count=len(processes);page.reload();expect(page.locator('#guardian-dashboard')).to_be_visible();page.wait_for_timeout(150)
    assert len(processes)==count
    # A lost native response may not start browser speech until stop is confirmed.
    api.post(base+'/local/logout',headers=h);hold[0]=True
    pending_stops=[];native_id=[];workers=[]
    def lose_response(route):
     payload=route.request.post_data_json
     if payload['action']=='start':
      native_id.append(payload['ident'])
      worker=threading.Thread(target=lambda:login_voice.speak(payload['ident']));worker.start();workers.append(worker)
      while not processes or processes[-1].done:time.sleep(.001)
      route.abort()
     else:pending_stops.append(route)
    page.route('**/local/login-voice',lose_response);page.reload()
    page.wait_for_function('Portal.loginNative&&Portal.loginReady');page.wait_for_timeout(100)
    assert pending_stops and page.evaluate('__spoken')==[]
    page.locator('#login-role-guardian').press('Enter')
    page.wait_for_timeout(80)
    for route in pending_stops:route.fulfill(status=503,content_type='application/json',body='{}')
    page.wait_for_timeout(150)
    assert '보호자 로그인을 선택해' in page.locator('#login-voice-status').inner_text()
    assert not page.evaluate('Portal.loginVoice')
    for ident in native_id:login_voice.stop(ident)
    for worker in workers:worker.join(2)
    page.unroute('**/local/login-voice',lose_response)
    assert not errors,errors
    result={'native_start_without_browser_activation':True,'one_native_start_per_reload':True,
      'no_duplicate_browser_startup_speech':True,'native_cancel_on_tab_and_guardian_choice':True,
      'native_cancel_on_pagehide':True,'authenticated_page_has_no_login_greeting':True,
      'lost_native_response_waits_for_stop':True,'late_stop_failure_keeps_guardian_status':True,
      'page_errors':errors,'scope':'real Chromium and HTTP; native process mocked; no heard screen-reader verification'}
    out=ROOT/'docs/verification/login-startup-results.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False));browser.close()
  finally:
   for process in processes:process.terminate()
   server.should_exit=True;thread.join(timeout=5)

if __name__=='__main__':main()
