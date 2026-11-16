"""Real installed extensions: one-time pairing, guardian login and closed-view wake."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import expect
import verify_extensions_browser as browser
from verify_reaudit_fixes import Complete

checks = {}
def record(name, observed):
    checks[name] = {'passed': True, 'observed': observed}
    print(name, 'PASS', flush=True)


def exercise(guardian, student, output):
    from app import local_access
    student.locator('#task-settings-button').focus();student.keyboard.press('Enter')
    student.locator('#access-mode').select_option('silent')
    student.evaluate('window.__remoteNotices=[];window.addEventListener("sullivan-status",e=>window.__remoteNotices.push(e.detail.text))')
    guardian.locator('#create-pair-code').focus();guardian.keyboard.press('Enter')
    expect(guardian.locator('#pair-code')).not_to_have_value('')
    student.get_by_text('보호자 연결과 공유 범위', exact=True).click()
    student.locator('#pair-preview-form [name=code]').fill(guardian.locator('#pair-code').input_value())
    student.locator('#pair-preview-form button').focus();student.keyboard.press('Enter')
    expect(student.locator('#pair-preview')).to_be_visible()
    assert student.evaluate('window.__remoteNotices.some(text=>text.includes("연결할 보호자: 보호자")&&text.includes("공유 범위"))')
    expect(student.locator('#pair-remote-login')).not_to_be_checked()
    student.locator('#pair-confirm').check();student.locator('#pair-remote-login').check()
    student.locator('#pair-confirm-form button').focus();student.keyboard.press('Enter')
    expect(student.locator('#status')).to_contain_text('확인한 보호자와 연결')
    expect(student.locator('#remote-device-disable')).to_be_visible()
    guardian.locator('#refresh').click();expect(guardian.locator('#remote-student option')).to_have_count(1)
    guardian.locator('#remote-login-refresh').click()
    expect(guardian.locator('#guardian-remote-status')).to_contain_text('요청을 보낼 수 있습니다')
    record('REMOTE01.one_time_pair_and_device_approval', 'Native pair form, separate unchecked device consent, guardian dropdown')
    browser.check_layout(student, 'student-approved-login-device', output)
    browser.check_layout(guardian, 'guardian-student-login', output)
    guardian_identity=guardian.evaluate('async()=>(await chrome.storage.session.get("session")).session.user.id')
    student_identity=student.evaluate('async()=>(await chrome.storage.session.get("session")).session.user.id')
    student.locator('#logout').click();expect(student.locator('#auth')).to_be_visible()
    expect(student.locator('#remote-device-disable')).to_be_visible()
    guardian.locator('#remote-login-start').focus();guardian.keyboard.press('Enter')
    expect(guardian.locator('#guardian-remote-status')).to_contain_text('응답을 기다립니다')
    expect(student.locator('#workspace')).to_be_visible(timeout=15000)
    expect(student.locator('#account-name')).to_have_text('학생 하나')
    guardian.locator('#remote-login-refresh').click()
    expect(guardian.locator('#guardian-remote-status')).to_contain_text('로그인을 완료')
    assert guardian.evaluate('async()=>(await chrome.storage.session.get("session")).session.user.id')==guardian_identity
    record('REMOTE02.guardian_starts_student_login', 'Student logged out, then actual worker/server login without password; guardian remains guardian')
    # The background module must work without any open student extension view.
    student.locator('#logout').click();expect(student.locator('#auth')).to_be_visible()
    student.evaluate('async()=>await chrome.runtime.sendMessage({type:"student-remote-poll"})')
    guardian.locator('#remote-login-refresh').click();expect(guardian.locator('#guardian-remote-status')).to_contain_text('이전 로그인 요청은 완료됐습니다')
    context=student.context
    worker=next(w for w in context.service_workers if w.url.startswith(student.url.split('/index.html')[0]))
    student.close()
    guardian.locator('#remote-login-start').focus();guardian.keyboard.press('Enter')
    expect(guardian.locator('#guardian-remote-status')).to_contain_text('응답을 기다립니다')
    with context.expect_page(timeout=15000) as opened:
        worker.evaluate('async()=>await chrome.alarms.create("student-remote-login",{when:Date.now()+100,periodInMinutes:1})')
    student=opened.value;student.wait_for_load_state('domcontentloaded')
    expect(student.locator('#workspace')).to_be_visible(timeout=10000)
    assert student.evaluate('async()=>(await chrome.storage.session.get("session")).session.user.id')==student_identity
    alarm=worker.evaluate('async()=>await chrome.alarms.get("student-remote-login")')
    assert alarm['periodInMinutes']==1
    record('REMOTE03.closed_view_background_opens_student', {'real_alarm_event': True, 'alarm_period_minutes': 1})
    student.locator('#task-settings-button').focus();student.keyboard.press('Enter')
    student.locator('#access-mode').select_option('silent')
    guardian.locator('#remote-login-refresh').click();expect(guardian.locator('#guardian-remote-status')).to_contain_text('로그인을 완료')
    browser.check_layout(student, 'student-remote-logged-in', output)
    # Revoke on the guardian side: device proof and its remote session fail closed.
    guardian.locator('#remote-login-stop').focus();guardian.keyboard.press('Enter')
    expect(guardian.locator('#guardian-remote-status')).to_contain_text('처음 한 번 로그인')
    expect(guardian.locator('#remote-login-start')).to_be_focused()
    student.evaluate('async()=>await chrome.runtime.sendMessage({type:"student-remote-poll"})')
    expect(student.locator('#auth')).to_be_visible(timeout=10000)
    expect(student.locator('#remote-device-disable')).to_be_hidden()
    with local_access.db() as con:
        assert not con.execute('SELECT 1 FROM remote_login_devices WHERE student=? AND revoked=0',(student_identity,)).fetchone()
    record('REMOTE04.guardian_revoke_ends_remote_session', 'Device proof removed and remote session invalidated; focus restored')
    # Existing linked accounts can approve a device later, without re-pairing.
    student.locator('#username').fill('student');student.locator('#password').fill('extension-pass-123')
    student.locator('#login-form button').click();expect(student.locator('#workspace')).to_be_visible()
    student.locator('#task-settings-button').focus();student.keyboard.press('Enter')
    student.get_by_text('보호자 연결과 공유 범위',exact=True).click()
    student.locator('#remote-consent').check();student.locator('#remote-device-enable').focus();student.keyboard.press('Enter')
    expect(student.locator('#remote-device-enable')).to_be_disabled()
    expect(student.locator('#remote-access-title')).to_be_focused()
    student.locator('#logout').click();expect(student.locator('#auth')).to_be_visible()
    expect(student.locator('#remote-consent')).not_to_be_checked()
    student.locator('#remote-device-disable').focus();student.keyboard.press('Enter')
    expect(student.locator('#remote-device-disable')).to_be_hidden()
    expect(student.locator('#remote-access-title')).to_be_focused()
    record('REMOTE05.logged_out_student_can_disable', 'Existing account opt-in, enable focus preserved, logout clears transient consent, disable without signing in')
    browser.check_layout(student, 'student-logged-out-support-disabled', output)
    guardian.locator('#remote-login-start').focus()
    guardian.evaluate('''async student=>{const {request}=await import('./client.js');
      await request('/extension/v1/guardian/connections/unlink',{method:'POST',body:{student,confirm:true}});
      document.querySelector('#refresh').click();}''',student_identity)
    expect(guardian.locator('#remote-login-start')).to_be_disabled()
    expect(guardian.locator('#connections-title')).to_be_focused()
    record('REMOTE06.last_student_removal_preserves_focus', 'Async list refresh moves focus before disabling empty student controls')
    ids=guardian.evaluate('''async()=>{const {request}=await import('./client.js');const ids=[];
      for(const [username,name] of [['remote-a','학생 가'],['remote-b','학생 나']]){
        ids.push((await request('/local/students',{method:'POST',body:{username,name,password:'extension-pass-123'}})).id);
      }return ids;}''')
    guardian.locator('#refresh').click();expect(guardian.locator('#remote-student option')).to_have_count(2)
    guardian.locator('#remote-student').select_option(ids[1]);expect(guardian.locator('#guardian-remote-status')).to_contain_text('학생 나:')
    held=[];error_current=[False]
    def remote_transport(route):
        if route.request.method!='GET':route.continue_();return
        if '/'+ids[0]+'/' in route.request.url:held.append(route);return
        if error_current[0]:route.fulfill(status=503,content_type='application/json',body=json.dumps({'detail':'현재 학생 연결 오류 검사'}));return
        route.continue_()
    guardian.route('**/guardian/students/*/remote-login',remote_transport)
    guardian.locator('#remote-student').select_option(ids[0]);expect(guardian.locator('#guardian-remote-status')).to_have_text('학생 가: 로그인 지원 상태를 확인하고 있습니다.')
    guardian.wait_for_timeout(100);assert held
    guardian.locator('#remote-student').select_option(ids[1]);expect(guardian.locator('#guardian-remote-status')).to_contain_text('학생 나: 학생 기기에서 처음 한 번')
    held.pop().fulfill(status=503,content_type='application/json',body=json.dumps({'detail':'이전 학생 오류 유출 금지'}));guardian.wait_for_timeout(150)
    assert '이전 학생 오류' not in guardian.locator('#guardian-remote-status').inner_text()+guardian.locator('#error').inner_text()
    record('REMOTE07.student_selection_discards_stale_status', 'New student checking state immediately replaces prior student; late previous error suppressed')
    error_current[0]=True;guardian.locator('#remote-login-refresh').click()
    expect(guardian.locator('#guardian-remote-status')).to_contain_text('학생 나: 현재 학생 연결 오류 검사')
    error_current[0]=False;guardian.locator('#remote-login-refresh').click()
    expect(guardian.locator('#guardian-remote-status')).to_contain_text('학생 나: 학생 기기에서 처음 한 번')
    record('REMOTE08.current_status_error_and_recovery', 'Current-student error is announced locally; successful retry restores current status')
    guardian.unroute('**/guardian/students/*/remote-login')
    raise Complete()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    try:browser.main(exercise,phase='remote-login',output=args.output)
    except Complete:pass
    report={'result':'passed' if len(checks)==8 else 'failed','checks':checks,'axe':browser.AXE_RESULTS,
      'boundary':'Installed extensions, real worker/API/SQLite, native pairing forms and password-free guardian request. Closed-view real alarm scheduled early in unpacked fixture; normal cadence/sleep timing and assistive-technology audio not certified.'}
    (args.output/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(report['result']!='passed')
