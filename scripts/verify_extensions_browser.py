"""Install both real MV3 packages in one temporary Chromium profile and exercise phase 1."""
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/api'))
from build_extensions import build
import uvicorn
from playwright.sync_api import sync_playwright, expect
from browser_fixtures import offline_video_fixtures
AXE_RESULTS = []


def student_control(page, selector):
    """Open the owning task through its visible button before acting.

    Assertions keep using ordinary locators, so this cannot make a hidden-state
    assertion pass or bypass a disabled control or modal. Ancestor disclosures
    are opened through their native summary, never by changing hidden/open.
    """
    control = page.locator(selector) if isinstance(selector, str) else selector
    if control.count():
        tasks = control.evaluate_all("elements=>[...new Set(elements.map(e=>{const task=e.closest('section[id^=task-]');return task?.hidden?task.id.slice(5):null;}))]")
        if len(tasks) == 1 and (hidden_task := tasks[0]):
            page.locator(f'#task-{hidden_task}-button').click()
            expect(page.locator(f'#task-{hidden_task}')).to_be_visible()
    if control.count() == 1:
        while True:
            handle = control.evaluate_handle("e=>{let p=e.parentElement,closed=null;while(p){if(p.tagName==='DETAILS'&&!p.open&&!p.querySelector(':scope > summary')?.contains(e))closed=p;p=p.parentElement;}return closed;}")
            disclosure = handle.as_element()
            if not disclosure:
                handle.dispose()
                break
            disclosure.query_selector(':scope > summary').click()
            handle.dispose()
    return control


def student_text(page, text, **options):
    return student_control(page, page.get_by_text(text, **options))


def student_role(page, role, **options):
    # Discover the target's owning task before exposing it. Normal assertions
    # deliberately keep get_by_role's default visible-only behavior.
    options.setdefault('include_hidden', True)
    return student_control(page, page.get_by_role(role, **options))


def student_disclosure(page, text):
    summary = student_text(page, text, exact=True)
    if not summary.evaluate('e=>e.closest("details").open'):
        summary.press('Enter')
    return summary


def check_layout(page, name, output, skip=True):
    axe_source = os.getenv('SULLIVAN_AXE_SOURCE')
    if axe_source:
        page.evaluate(Path(axe_source).read_text())
        violations = page.evaluate("async () => (await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}})).violations.map(v => ({id:v.id, impact:v.impact, nodes:v.nodes.map(n=>n.target)}))")
        assert not violations, (name, violations)
        AXE_RESULTS.append({'screen': name, 'version': page.evaluate('axe.version'), 'violations': len(violations)})
    for width in (390, 1280):
        page.set_viewport_size({'width': width, 'height': 900})
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), (name, width)
        page.screenshot(path=str(output / f'extension-{name}-{width}.png'), full_page=True)
    controls = page.locator('input:visible,textarea:visible,select:visible,button:visible')
    for index in range(controls.count()):
        control = controls.nth(index)
        if control.is_disabled():
            continue
        # Real accessibility-tree names from Chromium, without inspecting input values.
        assert control.aria_snapshot().strip(), (name, index)
    if skip:
        page.locator('.skip').focus()
        page.keyboard.press('Enter')
        expect(page.locator('#main')).to_be_focused()
        page.keyboard.press('Tab')
        assert page.evaluate("document.activeElement.tagName !== 'BODY'")


@offline_video_fixtures
def main(exercise=None, phase='phase2', output=None):
    with tempfile.TemporaryDirectory(prefix='sullivan-extensions-') as temporary:
        temp = Path(temporary)
        os.environ['SULLIVAN_ACCOUNTS_DB'] = str(temp / 'accounts.sqlite')
        os.environ['SULLIVAN_ROLE_AUTH'] = '1'
        os.environ['SULLIVAN_PRODUCTION'] = '0'
        for key in ('SULLIVAN_PUBLIC_URL','SULLIVAN_EXTENSION_CLIENTS','SULLIVAN_MIN_EXTENSION_VERSION','SULLIVAN_SIGNUP_INVITE'):
            os.environ.pop(key,None)
        os.environ['GEMINI_API_KEY'] = ''
        os.environ['DEMO_USAGE_DB'] = str(temp / 'usage.sqlite')
        for key in ('DATABASE_URL', 'DATABASE_URL_UNPOOLED', 'RENDER'):
            os.environ.pop(key, None)
        from app.main import app
        sock = socket.socket()
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, log_level='error', access_log=False))
        thread = threading.Thread(target=lambda: server.run(sockets=[sock]), daemon=True)
        thread.start()
        deadline = time.monotonic() + 10
        while not server.started:
            if time.monotonic() > deadline:
                raise RuntimeError('Test server failed to start')
            time.sleep(.02)
        output = Path(output) if output else ROOT / 'docs/verification'
        output.mkdir(parents=True,exist_ok=True)
        packages = build(f'http://127.0.0.1:{port}', temp / 'packages')
        paths = ','.join(str(packages / role) for role in ('student', 'guardian'))
        errors = []
        try:
            with sync_playwright() as playwright:
                context = playwright.chromium.launch_persistent_context(str(temp / 'profile'),
                    channel='chromium', headless=True,
                    args=[f'--disable-extensions-except={paths}', f'--load-extension={paths}'])
                try:
                    deadline = time.monotonic() + 15
                    while len(context.service_workers) < 2:
                        if time.monotonic() > deadline:
                            raise RuntimeError('Both extension workers did not start')
                        context.wait_for_event('serviceworker', timeout=15000)
                    ids = {}
                    for worker in context.service_workers:
                        name = worker.evaluate('chrome.runtime.getManifest().name')
                        ids['student' if '학생' in name else 'guardian'] = worker.url.split('/')[2]
                    assert len(set(ids.values())) == 2
                    guardian, student = context.new_page(), context.new_page()
                    for page in (guardian, student):
                        page.on('pageerror', lambda error: errors.append(str(error)))
                    guardian.goto(f'chrome-extension://{ids["guardian"]}/index.html')
                    student.goto(f'chrome-extension://{ids["student"]}/index.html')
                    expect(guardian.locator('#guardian-guide')).to_be_visible()
                    expect(guardian.locator('#guardian-guide-title')).to_be_focused()
                    expect(guardian.locator('#guardian-content')).to_be_hidden()
                    check_layout(guardian, 'guardian-first-guide', output)
                    expect(guardian.locator('#guardian-guide-done')).to_be_enabled()
                    guardian.locator('#guardian-guide-done').focus();guardian.keyboard.press('Enter')
                    expect(guardian.locator('#guardian-start')).to_be_visible()
                    expect(guardian.locator('#guardian-login-choice')).to_be_focused()
                    expect(guardian.locator('#login-form')).to_be_hidden()
                    expect(guardian.locator('#signup-form')).to_be_hidden()
                    expect(student.locator('#auth')).to_be_visible()
                    check_layout(student, 'student-login', output)
                    check_layout(guardian, 'guardian-account-choice', output)
                    guardian.locator('#guardian-signup-choice').focus();guardian.keyboard.press('Enter')
                    expect(guardian.locator('#guardian-signup-title')).to_be_focused()
                    check_layout(guardian, 'guardian-signup', output)
                    guardian.get_by_text('로컬 개발 계정 만들기', exact=True).click()
                    registration = guardian.locator('#register-form')
                    registration.locator('[name=name]').fill('보호자')
                    registration.locator('[name=username]').fill('guardian')
                    registration.locator('[name=password]').fill('extension-pass-123')
                    registration.locator('button').click()
                    expect(guardian.locator('#workspace')).to_be_visible()
                    guardian.get_by_text('학생 계정 만들기', exact=True).click()
                    creation = guardian.locator('#student-form')
                    creation.locator('[name=name]').fill('학생 하나')
                    creation.locator('[name=username]').fill('student')
                    creation.locator('[name=password]').fill('extension-pass-123')
                    creation.locator('button').click()
                    expect(guardian.locator('#student-choice option')).to_have_count(1)
                    guardian.locator('#assign-submit').click()
                    expect(guardian.locator('#lectures li')).to_have_count(1)
                    student.locator('#username').fill('student')
                    student.locator('#password').fill('extension-pass-123')
                    student.locator('#login-form button').click()
                    try:
                        expect(student.locator('#lectures button')).to_have_count(1)
                    except Exception:
                        diagnostic={'page_errors':errors,'status':student.locator('#status').inner_text(),
                            'error':student.locator('#error').inner_text(),'workspace_visible':student.locator('#workspace').is_visible(),
                            'account':student.locator('#account-name').inner_text(),
                            'session':student.evaluate('async()=>{const {session}=await chrome.storage.session.get("session");return session?{user:session.user?.id,role:session.user?.role,has_token:Boolean(session.token)}:null;}')}
                        (output/'startup-failure.json').write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2)+'\n')
                        raise
                    student.locator('#lectures button').click()
                    expect(student.locator('#lesson')).to_be_visible()
                    expect(student.locator('#lesson-title')).to_be_focused()
                    expect(student.locator('#material')).not_to_be_empty()
                    # 2026-11-16: position is managed in Settings; the preserved
                    # legacy memo is in Notes, outside the listening Tab cycle.
                    student.locator('#task-settings-button').focus();student.keyboard.press('Enter')
                    student.locator('#position').fill('42')
                    student.locator('#task-notes-button').focus();student.keyboard.press('Enter')
                    student.locator('#note').fill('확장 분리 검증 메모')
                    student.locator('#progress-form button').focus()
                    student.keyboard.press('Enter')
                    expect(student.locator('#status')).to_have_text('학습 위치와 메모를 저장했습니다.')
                    expect(student.locator('#progress-form button')).to_be_focused()
                    check_layout(student, 'student-material', output)
                    check_layout(guardian, 'guardian-workspace', output)
                    if exercise:
                        guardian = exercise(guardian, student, output)
                    guardian.locator('#logout').click()
                    expect(guardian.locator('#auth')).to_be_visible()
                    expect(student.locator('#workspace')).to_be_visible()
                    student.reload()
                    expect(student.locator('#lectures button')).to_have_count(1)
                    student.locator('#lectures button').click()
                    student.locator('#task-notes-button').focus();student.keyboard.press('Enter')
                    expect(student.locator('#note')).to_have_value('확장 분리 검증 메모')
                    expect(student.locator('#position')).to_have_value('42')
                    # Wrong-role account must remain at the student login screen.
                    student.locator('#logout').click()
                    expect(student.locator('#auth')).to_be_visible()
                    student.locator('#username').fill('guardian')
                    student.locator('#password').fill('extension-pass-123')
                    student.locator('#login-form button').focus()
                    student.keyboard.press('Enter')
                    expect(student.locator('#error')).to_contain_text('이 프로그램의 계정')
                    expect(student.locator('#login-form button')).to_be_focused()
                    expect(student.locator('#workspace')).to_be_hidden()
                    assert not errors, errors
                    report = {'browser': context.browser.version, 'result': 'passed',
                        'actual_extensions': 2, 'same_profile': True,
                        'checks': ['independent registration/login', 'student creation', 'sample assignment',
                                   'safe material reading', 'progress persistence', 'independent logout',
                                   'wrong-role rejection', 'focus after save/error', '390/1280 layout', 'skip link'],
                        'limitations': ['No real screen-reader audio, TTS quality or external player verification']}
                    if exercise:
                        report['checks'] += ['material preparation', 'job state recovery after tab close',
                            'source switch validation', 'student settings', 'assignment editing',
                            'lecture order', 'confirmed withdrawal', 'student refresh after withdrawal']
                        report['checks'] += getattr(exercise, 'checks', [])
                    report['axe'] = {'enabled': bool(os.getenv('SULLIVAN_AXE_SOURCE')),
                        'screens': AXE_RESULTS,
                        'scope': 'check_layout screens, WCAG A/AA tags', 'violations': 0 if os.getenv('SULLIVAN_AXE_SOURCE') else None}
                    report['checks']=list(dict.fromkeys(report['checks']))
                    if phase in ('phase3','phase4','student-repair','feature-restoration'):
                        report['limitations'] = ['Native decoded video fixture; actual YouTube compatibility, real speech recognition, speech quality and VoiceOver/NVDA audio not verified']
                    (output / (f'extension-{phase}-results.json' if exercise else 'extension-phase1-results.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
                    print(json.dumps(report, ensure_ascii=False, indent=2))
                finally:
                    context.close()
        finally:
            server.should_exit = True
            thread.join(timeout=10)


if __name__ == '__main__':
    main()
