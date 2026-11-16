"""Paired independent account, real PKCE popup and recovery flow in installed extensions."""
from verify_extensions_browser import student_control, student_role, student_text
from playwright.sync_api import expect
from verify_extensions_browser import main,check_layout
from verify_extensions_phase3 import exercise as phase3


def browser_login(context,page,username,password,role='student',output=None):
    if role=='guardian' and page.locator('#guardian-start').is_visible():
        page.locator('#guardian-login-choice').click()
    with context.expect_page(timeout=10000) as popup:
        page.locator('#oauth-login').click()
    auth=popup.value
    auth.wait_for_url(f'**/extension/auth/{role}/authorize?*',timeout=10000)
    if output:check_layout(auth,f'hosted-{role}-login',output,skip=False)
    auth.locator('[name=username]').fill(username);auth.locator('[name=password]').fill('incorrect-pass-123')
    auth.locator('button[type=submit]').click()
    expect(auth.locator('[role=alert]')).to_contain_text('로그인 이름')
    expect(auth.locator('[name=username]')).to_have_value(username)
    auth.locator('[name=username]').fill(username);auth.locator('[name=password]').fill(password)
    auth.locator('button[type=submit]').click()
    expect(page.locator('#workspace')).to_be_visible(timeout=10000)


def exercise(guardian,student,output):
    guardian=phase3(guardian,student,output)
    context=student.context
    guardian.locator('#logout').click();expect(guardian.locator('#auth')).to_be_visible()
    browser_login(context,guardian,'guardian','extension-pass-123','guardian',output)
    expect(student.locator('#workspace')).to_be_visible()
    student_control(student, '#logout').click();expect(student.locator('#auth')).to_be_visible()
    student_text(student, '학생 계정 가입',exact=True).click()
    form=student.locator('#signup-form')
    form.locator('[name=name]').fill('연결 학생');form.locator('[name=username]').fill('linkedstudent');form.locator('[name=password]').fill('linked-pass-123')
    form.locator('button').click()
    expect(student.locator('#recovery-output')).to_be_visible()
    recovery=student.locator('#recovery-codes').input_value().splitlines()[0]
    assert len(student.locator('#recovery-codes').input_value().splitlines())==8
    check_layout(student,'student-recovery-codes',output)
    with student.expect_download() as download:student_control(student, '#download-recovery').click()
    assert download.value.suggested_filename=='sullivan-student-recovery.txt'
    student_control(student, '#clear-recovery').click();expect(student.locator('#login-title')).to_be_focused()
    student_control(student, '#remember-login').check()
    browser_login(context,student,'linkedstudent','linked-pass-123',output=output)
    expect(student.locator('#account-name')).to_have_text('연결 학생')
    assert student.evaluate("async()=>Boolean((await chrome.storage.session.get('session')).session.refresh_token)")
    student.evaluate("async()=>await chrome.storage.session.remove('session')")
    student.reload();expect(student.locator('#account-name')).to_have_text('연결 학생')
    expect(student.locator('#workspace')).to_be_visible()
    student_text(student, '로그인 기기 관리',exact=True).click();student_control(student, '#devices-refresh').click()
    expect(student.locator('#devices li')).to_have_count(1)
    guardian.locator('#create-pair-code').click();expect(guardian.locator('#pair-code')).not_to_have_value('')
    code=guardian.locator('#pair-code').input_value()
    student_text(student, '보호자 연결과 공유 범위',exact=True).click()
    student_control(student, '#pair-preview-form [name=code]').fill(code);student_control(student, '#pair-preview-form button').click()
    expect(student.locator('#pair-guardian')).to_contain_text('보호자')
    check_layout(student,'student-pair-confirm',output)
    student_control(student, '#pair-confirm').check();student_control(student, '#pair-confirm-form button').click()
    expect(student.locator('#status')).to_contain_text('확인한 보호자와 연결했습니다')
    guardian.locator('#refresh').click()
    expect(guardian.locator('#students')).to_contain_text('연결 학생')
    guardian.locator('#student-choice').select_option(label='연결 학생')
    guardian.locator('#assign-submit').click()
    expect(guardian.locator('#status')).to_contain_text('샘플 강의를 배정')
    student_control(student, '#refresh').click();expect(student.locator('#lectures button')).to_have_count(1)
    lesson=student_control(student, '#lectures button');lesson.click()
    expect(lesson).not_to_have_attribute('aria-busy','true')
    student_control(student, '#note').fill('연결 학생 개인 기록')
    student_control(student, '#progress-form button').click();expect(student.locator('#status')).to_contain_text('학습 위치와 메모를 저장')
    student_role(student, 'button',name='내 보호자 연결 해제',exact=True).click()
    student_control(student, '#student-unlink-yes').click();expect(student.locator('#status')).to_contain_text('보호자 연결과 이 보호자의 배정 이용을 종료')
    expect(student.locator('#lectures button')).to_have_count(0)
    guardian.locator('#refresh').click();expect(guardian.locator('#students')).not_to_contain_text('연결 학생')
    student_control(student, '#logout').click();expect(student.locator('#auth')).to_be_visible()
    student_text(student, '복구 코드로 비밀번호 변경',exact=True).click()
    form=student.locator('#recover-form')
    form.locator('[name=username]').fill('linkedstudent');form.locator('[name=code]').fill(recovery);form.locator('[name=password]').fill('recovered-pass-123');form.locator('button').click()
    expect(student.locator('#status')).to_contain_text('비밀번호를 변경')
    # Restore the original family account for the shared regression harness.
    student_control(student, '#username').fill('student');student_control(student, '#password').fill('extension-pass-123');student_control(student, '#login-form button').click()
    expect(student.locator('#lectures button')).to_have_count(1)
    return guardian


exercise.checks=phase3.checks+['independent student signup', 'one-time recovery code export', 'actual S256 PKCE browser login for both roles',
    'remembered refresh after session storage reset', 'pair preview and explicit consent', 'paired assignment and progress',
    'unlink removes assignment and guardian lookup', 'account recovery']

if __name__=='__main__':main(exercise,phase='phase4')
