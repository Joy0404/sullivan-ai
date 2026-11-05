"""Two real local sessions; speech and YouTube boundaries mocked, no real accounts."""
from pathlib import Path
import json,os,socket,sys,tempfile,threading,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps/api'))
import uvicorn
from playwright.sync_api import sync_playwright,expect
from verify_roles_browser import MOCK

SPEECH='''window.__spoken=[];window.__cancels=0;
speechSynthesis.resume=()=>{};speechSynthesis.cancel=()=>{window.__cancels++;};
speechSynthesis.speak=u=>{window.__spoken.push(u.text);u.onstart?.();u.onend?.();};'''

def login_check(page,kind,out):
 for width in (320,390,1280,1920):
  page.set_viewport_size({'width':width,'height':900})
  assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
 page.set_viewport_size({'width':1280,'height':900})
 page.screenshot(path=str(out/f'login-{kind}.png'),full_page=True)
 source=os.getenv('SULLIVAN_AXE_SOURCE')
 if source:
  page.add_script_tag(path=source)
  violations=page.evaluate("async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}})).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))")
  assert not violations,violations

def main():
 with tempfile.TemporaryDirectory(prefix='sullivan-login-assignment-') as temp:
  os.environ['SULLIVAN_ACCOUNTS_DB']=str(Path(temp)/'accounts.sqlite')
  os.environ['SULLIVAN_ROLE_AUTH']='1';os.environ['GEMINI_API_KEY']=''
  for name in ['DATABASE_URL','DATABASE_URL_UNPOOLED','RENDER']:os.environ.pop(name,None)
  from app.main import app
  sock=socket.socket();sock.bind(('127.0.0.1',0));base=f'http://127.0.0.1:{sock.getsockname()[1]}'
  server=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False))
  thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
  while not server.started:time.sleep(.01)
  out=ROOT/'docs/verification';out.mkdir(exist_ok=True)
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch();errors=[]
    def surface():
     c=browser.new_context(viewport={'width':1280,'height':900});c.add_init_script(MOCK+SPEECH)
     page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
     page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort())
     page.goto(base);page.wait_for_function('window.Portal && document.querySelector("#login-title").textContent.includes("로그인") || document.querySelector("#login-title").textContent.includes("처음")')
     return page
    guardian=surface()
    guardian.wait_for_function("document.querySelector('#login-title').textContent.includes('처음')")
    guardian.locator('#login-username').focus();guardian.keyboard.press('Tab');guardian.wait_for_timeout(240)
    assert guardian.evaluate('__spoken.at(-1)')=='비밀번호'
    guardian.locator('#login-role-guardian').press('Space');guardian.wait_for_timeout(240)
    count=guardian.evaluate('__spoken.length')
    guardian.locator('#login-username').focus();guardian.keyboard.press('Tab');guardian.wait_for_timeout(240)
    assert guardian.evaluate('__spoken.length')==count
    login_check(guardian,'guardian',out)
    guardian.locator('#login-username').fill('guardian');guardian.locator('#login-password').fill('test-pass-123');guardian.locator('#login-submit').press('Enter')
    guardian.locator('#guardian-title').wait_for(state='visible')
    h={'X-Local-Request':'1'}
    student_id=guardian.request.post(base+'/local/students',headers=h,data={'username':'student1','password':'test-pass-123','name':'학생'}).json()['id']
    # A separate session is already open before the guardian assigns the sample.
    student=surface()
    expect(student.locator('#login-role-student')).to_be_focused()
    student.wait_for_function('Portal.compatible && __spoken.includes("학생 로그인")')
    assert student.evaluate('__spoken.filter(t=>t==="학생 로그인").length')==1
    student.locator('#login-role-student').press('Space')
    student.wait_for_timeout(240)
    assert student.evaluate('__spoken.some(t=>t.includes("학생 로그인입니다"))')
    student.locator('#login-role-guardian').press('Space')
    student.locator('#login-username').fill('student1');student.locator('#login-password').fill('test-pass-123');student.locator('#login-submit').press('Enter')
    student.wait_for_function("document.querySelector('#portal-feedback').textContent.includes('로그인 유형')")
    assert student.evaluate('Portal.user===null')
    student.locator('#login-role-student').press('Space');student.wait_for_timeout(240)
    login_check(student,'student',out)
    student.locator('#login-submit').press('Enter');student.get_by_role('button',name='사용법 확인 완료').wait_for()
    held_onboarding=[]
    student.route('**/local/onboarding',lambda route:held_onboarding.append(route))
    student.get_by_role('button',name='사용법 확인 완료').press('Enter')
    assert student.locator(':focus').get_attribute('id')=='student-list-open'
    student.keyboard.press('Tab')
    assert student.locator(':focus').get_attribute('data-purpose')=='paragraph'
    assert len(held_onboarding)==1
    held_onboarding[0].continue_()
    student.locator('#onboarding-card').wait_for(state='detached')
    assert student.locator(':focus').get_attribute('data-purpose')=='paragraph'
    student.unroute('**/local/onboarding')
    assert student.locator('#assigned-list button').count()==0
    assert student.evaluate('Portal.focusVoice')
    assert student.request.get(base+'/local/me').json()['settings']['focus_voice'] is True
    guardian.locator('.brand').press('Enter');guardian.locator('#guardian-science').wait_for(state='visible')
    guardian.wait_for_function("document.querySelector('#guardian-dashboard').getAttribute('aria-busy')==='false'")
    ready_calls=[]
    guardian.route('**/local/lectures/*/ready',lambda route:(ready_calls.append(1),route.abort()))
    guardian.locator('#guardian-science').press('Space');guardian.locator('#publish-students input[value="'+student_id+'"]').press('Space')
    # requestSubmit() produces SubmitEvent.submitter == null; this used to throw
    # before sending any assignment request.
    guardian.evaluate('document.querySelector("#publish-form").requestSubmit()')
    expect(guardian.locator('.guardian-lecture')).to_have_count(1)
    assert not ready_calls # Non-file publication no longer depends on a second request.
    assert guardian.request.get(base+'/local/lectures').json()[0]['ready']
    guardian.unroute('**/local/lectures/*/ready')
    student.locator('#student-list-open').press('Enter')
    expect(student.locator('#assigned-list .assigned-lecture')).to_have_count(1)
    assert student.locator('#assigned-list .assigned-lecture').first.evaluate('e=>e===document.activeElement')
    student.wait_for_timeout(240)
    assert student.evaluate('__spoken.at(-1).includes("별의 진화")')
    student.locator('#assigned-list .assigned-lecture').first.press('Enter')
    student.wait_for_function("Portal.lectureId && document.activeElement.id==='learner-play'")
    assert student.evaluate('Portal.focusVoice')
    student.locator('#learner-home').press('Enter');student.locator('#portal-home').wait_for(state='visible')
    student.reload();student.locator('#portal-home').wait_for(state='visible');assert student.evaluate('Portal.focusVoice')
    # Recover a pre-existing draft using the guardian action, without reassigning.
    snapshot=guardian.evaluate('state.snapshot')
    old=guardian.request.post(base+'/local/lectures',headers=h,data={'title':'기존 대기 샘플','students':[student_id],'sample_id':'science','snapshot':snapshot}).json()['id']
    assert len(student.request.get(base+'/local/lectures').json())==1
    guardian.locator('.brand').press('Enter')
    draft=guardian.locator('.guardian-lecture').filter(has_text='기존 대기 샘플')
    draft.get_by_role('button',name='준비 완료로 제공').press('Space')
    guardian.wait_for_function("document.querySelector('#portal-feedback').textContent.includes('준비 완료로 제공했습니다')")
    student.locator('#student-list-open').press('Enter');expect(student.locator('#assigned-list .assigned-lecture')).to_have_count(2)
    # The new primary path works without opening a preview or fetching browser data.
    guardian.reload();guardian.locator('#guardian-title').wait_for(state='visible')
    assert guardian.evaluate('Object.keys(SullivanSamples.catalog).length')==0
    guardian.route('**/sample-catalog.json',lambda route:route.abort())
    for sample,count in [('history',3),('science',4)]:
     guardian.locator('#sample-assign-kind').select_option(sample)
     guardian.locator('#sample-assign-submit').press('Enter')
     expect(guardian.locator('.guardian-lecture')).to_have_count(count)
     assert '준비 완료로 저장' in guardian.locator('#sample-assign-receipt').inner_text()
    student.locator('#student-list-open').press('Enter');expect(student.locator('#assigned-list .assigned-lecture')).to_have_count(4)
    guardian.route('**/local/samples/history/assign',lambda route:route.fulfill(status=503,content_type='application/json',body='{"detail":"시험용 저장 실패"}'))
    guardian.locator('#sample-assign-kind').select_option('history');guardian.locator('#sample-assign-submit').press('Enter')
    guardian.wait_for_function("document.querySelector('#sample-assign-receipt').textContent.includes('저장하지 못했습니다')")
    assert len(guardian.request.get(base+'/local/lectures').json())==4
    guardian.unroute('**/local/samples/history/assign')
    wrong=guardian.context.new_page();wrong.add_init_script(SPEECH)
    wrong.route('**/local/status',lambda route:route.fulfill(status=200,content_type='application/json',body='{"needs_setup":false}'))
    wrong.goto(base);wrong.wait_for_function("document.querySelector('#portal-feedback').textContent.includes('서버 버전')")
    assert wrong.locator('#login-submit').is_disabled() and wrong.evaluate('Portal.user===null')
    wrong.close()
    guardian.locator('#portal-logout').press('Enter');guardian.locator('#portal-login').wait_for(state='visible')
    guardian.locator('#login-role-guardian').press('Space');login_check(guardian,'guardian',out)
    before=guardian.evaluate('__spoken.length')
    guardian.locator('#login-username').fill('guardian');guardian.locator('#login-password').fill('test-pass-123');guardian.locator('#login-submit').press('Enter')
    guardian.locator('#guardian-title').wait_for(state='visible')
    assert guardian.evaluate('Portal.user.role==="guardian"&&!Portal.focusVoice')
    assert guardian.evaluate('__spoken.length')==before
    # A delayed initial list must not steal focus after the student tabs onward.
    assigned=student.request.get(base+'/local/lectures').json();held=[]
    student.route('**/local/lectures',lambda route:held.append(route))
    student.reload(wait_until='domcontentloaded')
    student.wait_for_function("document.activeElement.id==='student-list-open'")
    student.keyboard.press('Tab')
    assert student.locator(':focus').get_attribute('data-purpose')=='paragraph'
    assert len(held)==1
    held[0].fulfill(status=200,content_type='application/json',body=json.dumps(assigned))
    expect(student.locator('#assigned-list .assigned-lecture')).to_have_count(len(assigned))
    assert student.locator(':focus').get_attribute('data-purpose')=='paragraph'
    student.unroute('**/local/lectures')
    for page in (guardian,student):
     assert not page.evaluate('__spoken.some(t=>t.includes("test-pass-123")||t.includes("student1"))')
    assert not errors,errors
    result={'initial_student_login_focus_and_single_voice_request':True,'login_tab_voice_default':True,'guardian_selection_stops_voice':True,'student_selection_continues_and_persists_voice':True,'wrong_role_rejected_without_session':True,'sample_assignment_ready_atomic':True,'already_logged_in_student_refreshes_list':True,'existing_pending_sample_recovered':True,'credential_values_not_spoken':True,'four_size_login_reflow':True,'login_axe_violations':0 if os.getenv('SULLIVAN_AXE_SOURCE') else 'not run','page_errors':errors,'real_audio':'not heard; speech and YouTube mocked'}
    result.update(both_samples_direct_ui_without_preview_data=True,submit_without_submitter_saves=True,failed_save_not_reported_as_success=True,outdated_server_detected=True,delayed_initial_list_keeps_keyboard_focus=True,delayed_onboarding_keeps_keyboard_focus=True)
    (out/'login-assignment-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False));browser.close()
  finally:server.should_exit=True;thread.join(timeout=5)
if __name__=='__main__':main()
