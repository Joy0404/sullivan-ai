"""Real keyboard and role-flow regressions using an isolated local account DB."""
from pathlib import Path
import json,os,socket,sys,tempfile,threading,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps/api'))
import uvicorn
from playwright.sync_api import sync_playwright,expect
from verify_roles_browser import MOCK

def main():
 with tempfile.TemporaryDirectory(prefix='sullivan-keyboard-') as tmp:
  os.environ.update(SULLIVAN_ACCOUNTS_DB=str(Path(tmp)/'accounts.sqlite'),SULLIVAN_ROLE_AUTH='1',GEMINI_API_KEY='')
  for key in ['DATABASE_URL','DATABASE_URL_UNPOOLED','RENDER']:os.environ.pop(key,None)
  from app.main import app
  sock=socket.socket();sock.bind(('127.0.0.1',0));base=f'http://127.0.0.1:{sock.getsockname()[1]}'
  server=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False));thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
  while not server.started:time.sleep(.01)
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch();context=browser.new_context(viewport={'width':1280,'height':900})
    context.add_init_script(MOCK+"speechSynthesis.resume=()=>{};speechSynthesis.cancel=()=>{};speechSynthesis.speak=u=>{u.onstart?.();u.onend?.();};")
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort())
    page.goto(base);expect(page.locator('#login-username')).to_be_focused()
    page.locator('#login-username').fill('guardian');page.locator('#login-password').fill('test-pass-123');page.locator('#login-submit').press('Enter')
    expect(page.locator('#student-create input[name=name]')).to_be_focused()
    # Shift alone follows the same predecessor as native Shift+Tab, including fields.
    page.locator('#guardian-prepare').focus();page.keyboard.press('Shift')
    expect(page.locator('#guardian-settings-panel > summary')).to_be_focused()
    page.locator('#guardian-prepare').focus();page.keyboard.press('Shift+Tab')
    expect(page.locator('#guardian-settings-panel > summary')).to_be_focused()
    # Capital letters and selection cannot cause a second backward move on release.
    field=page.locator('#student-create input[name=name]');field.fill('');field.focus();page.keyboard.press('Shift+A')
    assert field.input_value()=='A';expect(field).to_be_focused()
    page.keyboard.press('Shift+ArrowLeft');expect(field).to_be_focused()
    page.keyboard.press('Shift');expect(field).to_be_focused()
    field.fill('학생');page.locator('#student-create input[name=username]').fill('student');page.locator('#student-create input[name=password]').fill('test-pass-123')
    page.locator('#student-create button').press('Enter');page.wait_for_function("document.querySelector('#sample-assign-student').options.length===2")
    # Reload has a useful first action rather than a non-interactive page heading.
    page.reload();expect(page.locator('#guardian-prepare')).to_be_focused()
    page.locator('#guardian-prepare').press('Enter');expect(page.locator('#wizard-title-1')).to_be_focused()
    page.locator('#lecture-form [data-guardian-home]').press('Enter');expect(page.locator('#guardian-prepare')).to_be_focused()
    page.locator('#sample-assign-submit').press('Enter');page.wait_for_function("document.querySelectorAll('.guardian-lecture').length===1")
    page.locator('#portal-logout').press('Enter');expect(page.locator('#login-role-student')).to_be_focused()
    page.locator('#login-role-student').press('Enter');expect(page.locator('#login-username')).to_be_focused()
    page.locator('#login-username').fill('student');page.locator('#login-password').fill('test-pass-123');page.locator('#login-submit').press('Enter')
    expect(page.locator('#onboarding-done')).to_be_focused()
    page.locator('#onboarding-done').press('Enter');page.locator('#onboarding-card').wait_for(state='detached');expect(page.locator('#student-list-open')).to_be_focused()
    names=['강의 듣기','지문·문단 듣기','원하는 내용 찾기','질문하기']
    for name in names:
     expect(page.locator(':focus')).to_have_accessible_name(name);page.keyboard.press('Tab')
    # New DOM order reaches a lesson before the two help/record controls.
    expect(page.locator('#assigned-list button').first).to_be_focused()
    page.keyboard.press('Shift');expect(page.locator('[data-purpose=question]').first).to_be_focused()
    page.locator('#assigned-list button').first.press('Enter');expect(page.locator('#learner-play')).to_be_focused()
    assert page.locator('.learner-playback button').all_text_contents()==['강의 재생','영상·해설 모두 중지','현재 화면 다시 설명']
    page.keyboard.press('Tab');expect(page.locator('#learner-stop')).to_be_focused()
    page.keyboard.press('Tab');expect(page.locator('#learner-describe')).to_be_focused()
    page.keyboard.press('Shift');expect(page.locator('#learner-stop')).to_be_focused()
    page.keyboard.press('Shift');expect(page.locator('#learner-play')).to_be_focused()
    page.locator('[data-learn-panel][data-purpose=paragraph]').press('Enter');expect(page.locator('[data-paragraph-command="전체 지문"]')).to_be_focused()
    page.locator('[data-learn-panel][data-purpose=search]').press('Enter');expect(page.locator('#navigation-command')).to_be_focused()
    page.locator('[data-learn-panel=chat-panel]').press('Enter');expect(page.locator('#chat-input')).to_be_focused()
    page.keyboard.press('Shift+A');assert page.locator('#chat-input').input_value()=='A';expect(page.locator('#chat-input')).to_be_focused()
    page.locator('#learner-records').press('Enter');expect(page.locator('#learner-note')).to_be_focused()
    page.locator('[data-record-view=review-panel]').press('Enter');expect(page.locator('#read-review')).to_be_focused()
    page.locator('[data-record-view=study-panel]').press('Enter');expect(page.locator('#read-study-guide')).to_be_focused()
    # Ctrl/Alt/Meta chords must never turn into Shift-alone navigation on release.
    page.locator('#learner-play').focus();page.keyboard.down('Shift');page.keyboard.down('Control');page.keyboard.up('Control');page.keyboard.up('Shift');expect(page.locator('#learner-play')).to_be_focused()
    page.locator('#command-surface').focus();page.keyboard.press('Space');page.keyboard.press('Space');page.keyboard.press('Space')
    expect(page.locator('#text-command-input')).to_be_focused()
    page.locator('#close-text-command').focus();page.keyboard.press('Shift');expect(page.locator('#text-command-input')).to_be_focused()
    page.keyboard.press('Shift');expect(page.locator('#text-command-input')).to_be_focused()
    page.keyboard.press('Shift+Tab');expect(page.locator('#close-text-command')).to_be_focused()
    page.keyboard.press('Escape');expect(page.locator('#command-surface')).to_be_focused()
    # A Shift released after losing window focus cannot move a newly focused control.
    page.locator('#learner-describe').focus();page.keyboard.down('Shift');page.evaluate('window.dispatchEvent(new Event("blur"))');page.keyboard.up('Shift');expect(page.locator('#learner-describe')).to_be_focused()
    for width in [320,390,1280,1920]:
     page.set_viewport_size({'width':width,'height':900});assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert not errors,errors
    result={'three_playback_buttons_in_requested_order':True,'shift_alone_previous':True,'native_shift_tab_single_move':True,'shift_typing_selection_and_modifier_chords_preserved':True,'modal_scope_and_escape':True,'window_blur_cancels_shift':True,'role_and_learning_first_focus':True,'four_core_actions_within_four_tabs':True,'lecture_before_help_in_tab_order':True,'viewport_widths':[320,390,1280,1920],'page_errors':errors,'real_screen_reader':'not tested','providers':'mocked; no real accounts or provider calls'}
    (ROOT/'docs/verification/keyboard-navigation-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
    browser.close()
  finally:
   server.should_exit=True;thread.join(timeout=5)

if __name__=='__main__':main()
