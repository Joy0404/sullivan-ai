"""Installed guardian first guide, account choices and optional help regressions."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import expect
import verify_extensions_browser as browser
from verify_reaudit_fixes import Complete

checks = {}
def record(name, evidence):
    checks[name] = {'passed': True, 'evidence': evidence}
    print(name, 'PASS', flush=True)


def exercise(guardian, student, output):
    errors = []
    for page in (guardian, student):
        page.on('pageerror', lambda error: errors.append(str(error)))
    def enter(control):
        expect(guardian.locator(control)).to_be_visible()
        expect(guardian.locator(control)).to_be_enabled()
        guardian.locator(control).focus();guardian.keyboard.press('Enter')
    def login(username='guardian', password='extension-pass-123'):
        enter('#guardian-login-choice')
        expect(guardian.locator('#login-title')).to_be_focused()
        guardian.locator('#username').fill(username);guardian.locator('#password').fill(password)
        enter('#login-form button')
        expect(guardian.locator('#workspace')).to_be_visible()
    def tab_to(selector):
        control = guardian.locator(selector)
        expect(control).to_be_visible()
        for _ in range(160):
            if control.evaluate('element => element === document.activeElement'):
                return
            guardian.keyboard.press('Tab')
        raise AssertionError(f'Control not reachable with Tab: {selector}')
    def key_enter(selector):
        tab_to(selector); guardian.keyboard.press('Enter')
    assert guardian.evaluate("async()=> (await chrome.storage.local.get('guardian-guide-v1-seen'))['guardian-guide-v1-seen']")
    record('ENTRY01.first_guide_then_choice', 'Shared installed bootstrap confirms guide-only view, heading focus, explicit completion then two choices and hidden forms')
    # Reopening must not discard an existing preparation or force a logout.
    guardian.locator('#prepare-form [name=title]').fill('보존할 준비 초안')
    enter('#guardian-help');expect(guardian.locator('#guardian-guide-title')).to_be_focused()
    expect(guardian.locator('#guardian-content')).to_be_hidden();expect(guardian.locator('#logout')).not_to_be_visible()
    enter('#guardian-guide-done');expect(guardian.locator('#guardian-help')).to_be_focused()
    expect(guardian.locator('#prepare-form [name=title]')).to_have_value('보존할 준비 초안')
    expect(guardian.locator('#workspace')).to_be_visible()
    record('ENTRY02.optional_help_preserves_work', 'Authenticated guide hides underlying controls, then returns focus and draft')
    enter('#logout');expect(guardian.locator('#guardian-start')).to_be_visible()
    guardian.reload();expect(guardian.locator('#guardian-start')).to_be_visible()
    expect(guardian.locator('#guardian-guide')).to_be_hidden()
    expect(guardian.locator('#guardian-login-choice')).to_be_focused()
    expect(guardian.locator('#username')).not_to_be_visible();expect(guardian.locator('#signup-form')).not_to_be_visible()
    guardian.keyboard.press('Tab');expect(guardian.locator('#guardian-signup-choice')).to_be_focused()
    guardian.keyboard.press('Shift+Tab');expect(guardian.locator('#guardian-login-choice')).to_be_focused()
    key_enter('#guardian-help');expect(guardian.locator('#guardian-guide-title')).to_be_focused()
    guardian.keyboard.press('Tab');expect(guardian.locator('#guardian-guide-done')).to_be_focused()
    guardian.keyboard.press('Space');expect(guardian.locator('#guardian-help')).to_be_focused()
    browser.check_layout(guardian,'guardian-return-account-choice',output)
    record('ENTRY03.return_visit_skips_guide', 'Persistent profile completion survives reload and logout; neither form appears before selection')
    enter('#guardian-login-choice')
    expect(guardian.locator('#guardian-signup-view')).to_be_hidden()
    browser.check_layout(guardian,'guardian-selected-login',output)
    guardian.locator('#username').fill('guardian')
    enter('#guardian-login-back');expect(guardian.locator('#guardian-login-choice')).to_be_focused()
    enter('#guardian-signup-choice');expect(guardian.locator('#guardian-signup-title')).to_be_focused()
    enter('#guardian-signup-back');expect(guardian.locator('#guardian-login-choice')).to_be_focused()
    enter('#guardian-login-choice');expect(guardian.locator('#username')).to_have_value('guardian')
    guardian.locator('#password').fill('incorrect-pass-123');enter('#login-form button')
    expect(guardian.locator('#error')).not_to_be_empty();expect(guardian.locator('#guardian-login-view')).to_be_visible()
    guardian.locator('#password').fill('extension-pass-123');enter('#login-form button')
    expect(guardian.locator('#workspace')).to_be_visible()
    record('ENTRY04.form_choice_back_and_login', 'Choice/back preserves draft, failed credentials stay in login view, valid login opens workspace')
    # A valid session never bypasses the requested entry choices on a new visit.
    guardian.reload();expect(guardian.locator('#guardian-start')).to_be_visible()
    expect(guardian.locator('#guardian-guide')).to_be_hidden()
    expect(guardian.locator('#workspace')).to_be_hidden()
    expect(guardian.locator('#account-controls')).to_be_hidden()
    expect(guardian.locator('#guardian-login-choice')).to_be_focused()
    enter('#guardian-help');expect(guardian.locator('#guardian-guide-title')).to_be_focused()
    enter('#guardian-guide-done')
    expect(guardian.locator('#guardian-help')).to_be_focused()
    expect(guardian.locator('#guardian-start')).to_be_visible()
    browser.check_layout(guardian,'guardian-return-with-session',output)
    enter('#guardian-login-choice');expect(guardian.locator('#workspace')).to_be_visible()
    expect(guardian.locator('#workspace-title')).to_be_focused()
    record('ENTRY05.existing_session_preserved', 'Returning with a valid session first shows account choices and optional guide; Login explicitly resumes the session')
    enter('#logout');enter('#guardian-signup-choice')
    expect(guardian.locator('#guardian-signup-title')).to_be_focused()
    expect(guardian.locator('#logout')).not_to_have_attribute('aria-busy','true')
    expect(guardian.locator('#guardian-signup-view')).to_be_visible()
    form=guardian.locator('#signup-form')
    form.locator('[name=name]').fill('새 보호자');form.locator('[name=username]').fill('entry-guardian')
    form.locator('[name=password]').fill('entry-password-123')
    enter('#signup-form button')
    expect(guardian.locator('#recovery-title')).to_be_focused()
    expect(guardian.locator('#guardian-login-view')).to_be_visible()
    assert len(guardian.locator('#recovery-codes').input_value().splitlines())==8
    expect(guardian.locator('#username')).to_have_value('entry-guardian')
    browser.check_layout(guardian,'guardian-signup-recovery',output)
    enter('#clear-recovery');expect(guardian.locator('#login-title')).to_be_focused()
    guardian.locator('#password').fill('entry-password-123');enter('#login-form button')
    expect(guardian.locator('#workspace')).to_be_visible()
    record('ENTRY06.signup_and_recovery_then_login', 'Public signup yields 8 recovery codes, routes to login, preserves new username, login succeeds')
    # Continue from the new account using only sequential keys for the guardian workflow.
    key_enter('details:has(#student-form) > summary')
    for field, value in [('name','키보드 학생'), ('username','entry-keyboard-student'), ('password','keyboard-pass-123')]:
        tab_to(f'#student-form [name={field}]');guardian.keyboard.insert_text(value)
    key_enter('#student-form button')
    expect(guardian.locator('#student-choice option')).to_have_count(1)
    tab_to('#student-choice');guardian.keyboard.press('Home')
    tab_to('#assign-form [name=sample]');guardian.keyboard.press('Home')
    expect(guardian.locator('#assign-form p')).to_contain_text('새 AI 분석을 실행하지 않습니다')
    key_enter('#assign-submit')
    expect(guardian.locator('#lectures li')).to_have_count(1)
    browser.check_layout(guardian,'guardian-keyboard-assignment',output)
    record('ENTRY09.sequential_keyboard_flow', 'Actual Tab/Shift+Tab/Enter/Space navigate choices, optional guide, student creation and prepared sample selection/assignment; no mouse or programmatic focus in the workflow')
    enter('#guardian-help')
    # Real sign-out while the guide is visible models expiry/device revocation.
    guardian.evaluate("async()=>{const {signOut}=await import('./client.js');await signOut();}")
    expect(guardian.locator('#guardian-guide')).to_be_visible()
    expect(guardian.locator('#guardian-guide-title')).to_be_focused()
    enter('#guardian-guide-done');expect(guardian.locator('#guardian-start')).to_be_visible()
    expect(guardian.locator('#guardian-login-choice')).to_be_focused()
    record('ENTRY07.session_exit_during_guide', 'Guide stays readable through actual session exit; close returns to current account choices')
    guardian.evaluate("async()=>chrome.storage.local.remove('guardian-guide-v1-seen')")
    guardian.reload();expect(guardian.locator('#guardian-guide')).to_be_visible()
    guardian.reload();expect(guardian.locator('#guardian-guide')).to_be_visible()
    expect(guardian.locator('#guardian-content')).to_be_hidden()
    assert not guardian.evaluate("async()=> (await chrome.storage.local.get('guardian-guide-v1-seen'))['guardian-guide-v1-seen']")
    guardian.evaluate("""()=>{const set=chrome.storage.local.set.bind(chrome.storage.local);chrome.storage.local.set=async value=>{if(Object.hasOwn(value,'guardian-guide-v1-seen'))throw new Error('fixture storage failure');return set(value);};}""")
    expect(guardian.locator('#guardian-guide-done')).to_be_enabled();enter('#guardian-guide-done')
    expect(guardian.locator('#guardian-start')).to_be_visible()
    expect(guardian.locator('#error')).to_contain_text('다음 방문에 설명서가 다시 나타날 수 있습니다')
    guardian.reload();expect(guardian.locator('#guardian-guide')).to_be_visible()
    expect(guardian.locator('#guardian-guide-done')).to_be_enabled();enter('#guardian-guide-done')
    record('ENTRY08.storage_failure_is_recoverable', 'Injected local preference write failure allows login choices and clearly explains repeat; next successful completion persists')
    login()
    # Opening a fresh program tab, rather than reloading, also starts at choices.
    reopened = guardian.context.new_page()
    reopened.on('pageerror', lambda error: errors.append(str(error)))
    try:
        reopened.goto(guardian.url)
        expect(reopened.locator('#guardian-start')).to_be_visible()
        expect(reopened.locator('#guardian-guide')).to_be_hidden()
        expect(reopened.locator('#workspace')).to_be_hidden()
        expect(reopened.locator('#guardian-login-choice')).to_be_focused()
        reopened.keyboard.press('Tab');expect(reopened.locator('#guardian-signup-choice')).to_be_focused()
        reopened.keyboard.press('Shift+Tab');reopened.keyboard.press('Enter')
        expect(reopened.locator('#workspace')).to_be_visible()
        reopened.evaluate("async()=>chrome.storage.local.remove('guardian-guide-v1-seen')")
        reopened.reload();expect(reopened.locator('#guardian-guide')).to_be_visible()
        expect(reopened.locator('#guardian-guide-title')).to_be_focused()
        expect(reopened.locator('#guardian-content')).to_be_hidden()
        expect(reopened.locator('#guardian-guide-done')).to_be_enabled()
        reopened.keyboard.press('Tab');expect(reopened.locator('#guardian-guide-done')).to_be_focused()
        reopened.keyboard.press('Enter')
        expect(reopened.locator('#guardian-start')).to_be_visible()
        expect(reopened.locator('#workspace')).to_be_hidden()
        record('ENTRY11.first_guide_precedes_restored_session', 'Without a guide completion record, even an authenticated profile must confirm the guide before account choices; Enter completion never auto-opens workspace')
    finally:
        reopened.close()
    record('ENTRY10.new_program_tab_starts_with_choices', 'New tab in the same installed profile skips the confirmed guide, shows choices before a restored workspace, and resumes only after keyboard selection')
    assert student.locator('#workspace').is_visible()
    assert not errors, errors
    raise Complete()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    try:browser.main(exercise,phase='guardian-entry',output=args.output)
    except Complete:pass
    report={'result':'passed' if len(checks)==11 else 'failed','checks':checks,'axe':browser.AXE_RESULTS,
        'boundary':'Two real installed extensions, temporary DB/profile and actual account endpoints; local storage failure is explicitly injected. Human screen-reader audio not verified.'}
    (args.output/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(report['result']!='passed')
