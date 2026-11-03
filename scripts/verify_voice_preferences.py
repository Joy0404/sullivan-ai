"""Reproduce the real UI preference reset; speech-engine events are simulated, not heard audio."""
from pathlib import Path
import os,sys,socket,tempfile,threading,time,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps/api'))
import uvicorn
from playwright.sync_api import sync_playwright
SPEECH='''window.__spoken=[];window.__started=0;window.__resumed=0;window.__paused=true;
speechSynthesis.resume=()=>{window.__resumed++;window.__paused=false;};speechSynthesis.cancel=()=>{};
speechSynthesis.speak=u=>{window.__spoken.push(u.text);if(window.__fail){u.onerror?.({error:'not-allowed'});return;}if(window.__stall||window.__paused)return;window.__started++;u.onstart?.();u.onend?.();};'''
def main():
 with tempfile.TemporaryDirectory(prefix='sullivan-voice-check-') as temp:
  os.environ['SULLIVAN_ACCOUNTS_DB']=str(Path(temp)/'accounts.sqlite');os.environ['SULLIVAN_ROLE_AUTH']='1';os.environ['GEMINI_API_KEY']=''
  from app.main import app
  sock=socket.socket();sock.bind(('127.0.0.1',0));base=f'http://127.0.0.1:{sock.getsockname()[1]}'
  server=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False));thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
  while not server.started:time.sleep(.01)
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch();context=browser.new_context();context.add_init_script(SPEECH)
    h={'X-Local-Request':'1'};api=context.request
    assert api.post(base+'/local/setup',headers=h,data={'username':'guardian','password':'test-pass-123'}).status==200
    student=api.post(base+'/local/students',headers=h,data={'username':'student1','password':'test-pass-123','name':'학생'}).json()['id']
    session=api.post(base+'/v1/lectures',headers=h,data={'title':'음성 설정 검사','problem_mode':True}).json()['session_id']
    assert api.post(base+'/v1/lectures/'+session+'/analysis',headers=h,data={'passage_text':'음성 안내 테스트 지문입니다.'}).status==200
    ident=api.post(base+'/local/lectures',headers=h,data={'title':'음성 설정 검사','students':[student],'session_id':session}).json()['id'];api.put(base+'/local/lectures/'+ident+'/ready',headers=h)
    api.post(base+'/local/logout',headers=h)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base)
    page.locator('#login-username').fill('student1');page.locator('#login-password').fill('test-pass-123');page.locator('#login-submit').press('Enter')
    page.get_by_role('button',name='사용법 확인 완료').wait_for();page.get_by_role('button',name='사용법 확인 완료').press('Enter')
    page.locator('#onboarding-card').wait_for(state='detached')
    page.locator('#assigned-list button').first.press('Enter');page.locator('#command-surface').wait_for(state='visible')
    page.locator('#student-preferences summary').press('Enter');page.locator('#focus-voice').focus();page.keyboard.press('Space')
    page.wait_for_function('Portal.user.settings.focus_voice===true')
    assert page.evaluate("async()=> (await (await fetch('/local/me')).json()).settings.focus_voice")
    page.locator('#focus-voice-test').press('Enter');page.wait_for_timeout(220)
    assert page.evaluate('__started>0&&__resumed>0&&__spoken.some(t=>t.includes("버튼 음성 안내 시험"))')
    page.locator('#auto-narration').focus();page.keyboard.press('Space');page.wait_for_timeout(240)
    assert page.evaluate('__spoken.at(-1).includes("꺼져 있습니다")')
    page.keyboard.press('Space');page.wait_for_timeout(240)
    assert page.evaluate('__spoken.at(-1).includes("켜져 있습니다")')
    page.locator('#speech-rate').focus();page.keyboard.press('ArrowDown');page.wait_for_timeout(240)
    rate=page.locator('#speech-rate').input_value()
    assert page.evaluate('__spoken.at(-1)').endswith(rate+'배')
    page.locator('#student-preferences summary').press('Enter');page.wait_for_timeout(240)
    assert page.evaluate('__spoken.at(-1).includes("접혀 있습니다")')
    page.locator('#student-preferences summary').press('Enter');page.wait_for_timeout(240)
    assert page.evaluate('__spoken.at(-1).includes("펼쳐져 있습니다")')
    page.evaluate('Portal.error("시험 안내")')
    assert page.locator(':focus').get_attribute('id')=='portal-feedback'
    assert page.locator('#portal-feedback').get_attribute('aria-describedby')=='portal-feedback-copy'
    assert page.evaluate('__spoken.filter(t=>t==="시험 안내").length')==1
    page.locator('#learner-home').press('Enter');page.locator('#portal-home').wait_for(state='visible')
    page.locator('#assigned-list button').first.press('Enter');page.wait_for_function("document.activeElement.matches('[data-learn-panel][data-purpose=paragraph]')")
    assert page.evaluate('Portal.focusVoice') and page.locator('#focus-voice').is_checked()
    page.reload();page.locator('#portal-home').wait_for(state='visible');assert page.evaluate('Portal.focusVoice')
    page.locator('#assigned-list button').first.press('Enter');page.wait_for_function("document.activeElement.matches('[data-learn-panel][data-purpose=paragraph]')")
    page.keyboard.press('Tab');page.wait_for_timeout(240)
    assert page.locator(':focus').get_attribute('data-purpose')=='search'
    assert page.evaluate('__spoken.at(-1).includes("원하는 내용 찾기")&&__started>0'),page.evaluate('({last:__spoken.at(-1),focus:document.activeElement.outerHTML})')
    page.locator('#student-preferences summary').press('Enter');page.evaluate('window.__fail=true');page.locator('#focus-voice-test').press('Enter')
    assert '차단' in page.locator('#focus-voice-status').inner_text()
    page.evaluate('window.__fail=false;window.__stall=true');page.locator('#focus-voice-test').press('Enter');page.wait_for_timeout(1900)
    assert '시작이 확인되지' in page.locator('#focus-voice-status').inner_text()
    assert not errors,errors
    result={'preference_ui_to_server':True,'persists_on_lecture_switch':True,'persists_on_reload':True,'paused_engine_resumed':True,'explicit_test_button_speaks_in_gesture':True,'checkbox_select_disclosure_changes_spoken':True,'focused_feedback_named_and_spoken_once':True,'browser_error_reported':True,'missing_start_reported':True,'page_errors':errors,'real_audio':'not verified; browser speech events mocked'}
    out=ROOT/'docs/verification/voice-preferences-results.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False));browser.close()
  finally:server.should_exit=True;thread.join(timeout=5)
if __name__=='__main__':main()
