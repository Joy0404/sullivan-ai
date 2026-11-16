"""Progress recovery and preparation discovery in disposable installed extensions.

Real browser/API/DB; only save failures are injected. No paid analysis or user DB.
"""
from verify_extensions_browser import student_control, student_role
import argparse
import json
from pathlib import Path

from playwright.sync_api import expect
import verify_extensions_browser as browser
from verify_reaudit_fixes import Complete, open_lesson, prepare, request
from verify_extensions_phase3 import SPEECH

CHECKS = {}


def record(name, passed, observed):
    CHECKS[name] = {'passed': bool(passed), 'observed': observed}
    print(name, 'PASS' if passed else 'FAIL', flush=True)


def tab_to(page, selector):
    """Navigate by real Tab events; never programmatically focus the target."""
    target = page.locator(selector)
    for _ in range(250):
        if target.evaluate('e=>e===document.activeElement'):
            return
        page.keyboard.press('Tab')
    raise AssertionError(f'Cannot reach {selector} with Tab')


def choose_with_keys(page, selector, value):
    index = page.locator(selector).evaluate('(e,value)=>[...e.options].findIndex(option=>option.value===value)', value)
    assert index >= 0
    tab_to(page, selector)
    current = page.locator(selector).evaluate('e=>e.selectedIndex')
    if current != index:
        # macOS headless Chromium does not deliver native popup arrow changes.
        # Typeahead is a real native keyboard path; use an ASCII fixture name.
        label = page.locator(selector).evaluate('(e,index)=>e.options[index].text', index)
        assert label.isascii()
        page.keyboard.type(label)
    page.keyboard.press('Tab')
    expect(page.locator(selector)).to_have_value(value)


def capture_viewports(page, selector, name, output):
    # Full-page screenshots of very long extension documents can be tiled by
    # Chromium. Also retain the actual viewport at the changed control.
    for width in (390, 1280):
        page.set_viewport_size({'width': width, 'height': 900})
        page.locator(selector).scroll_into_view_if_needed()
        page.screenshot(path=str(output / f'extension-{name}-viewport-{width}.png'))


def exercise(guardian, student, output):
    student_control(student, '#access-mode').select_option('silent')
    base = request(student, '/local/lectures')[0]
    owner = request(guardian, '/local/students')[0]['id']
    job = prepare(guardian, '저장 복구 검사', {'assets': [
        {'name': 'p.txt', 'kind': 'passage', 'content': '첫 문단을 읽습니다.\n\n다음 문단으로 이동합니다.'}]})
    other = request(guardian, f'/extension/v1/guardian/preparations/{job["id"]}/publish',
                    'POST', {'students': [owner]})
    student_control(student, '#refresh').click()
    expect(student.locator('#lectures button')).to_have_count(2)
    student_control(student, '#position').fill('77')
    student_control(student, '#note').fill('위치와 함께 자동 저장하는 메모')
    expect(student.locator('#save-status')).to_contain_text('저장됨')
    saved = request(student, f'/extension/v1/student/lectures/{base["id"]}')['progress']
    record('S01.note_autosave_preserves_entered_position', saved['position_ms'] == 77000, saved['position_ms'])
    student_control(student, '#position').fill('83')
    student.evaluate("async()=>await(await import('./app.js')).command('강의 목록')")
    saved = request(student, f'/extension/v1/student/lectures/{base["id"]}')['progress']
    record('S02.home_saves_entered_position', saved['position_ms'] == 83000, saved['position_ms'])
    # Establish a clean baseline before a failed bookmark write.
    student_control(student, '#progress-form button').click()
    expect(student.locator('#status')).to_have_text('학습 위치와 메모를 저장했습니다.')
    failures = []
    pattern = f'**/local/lectures/{base["id"]}/progress'

    def fail_save(route):
        failures.append(route.request.post_data_json)
        route.fulfill(status=503, content_type='application/json', body='{"detail":"시험 저장 실패"}')

    student.route(pattern, fail_save)
    student_control(student, '#bookmark').click()
    expect(student.locator('#bookmark')).not_to_have_attribute('aria-busy', 'true')
    student_control(student, f'#lectures button[data-lecture="{other["id"]}"]').click()
    expect(student.locator(f'#lectures button[data-lecture="{other["id"]}"]')).not_to_have_attribute('aria-busy', 'true')
    retained = student.locator('#lesson-title').inner_text() == base['title']
    record('S03.failed_bookmark_blocks_switch', retained, student.locator('#lesson-title').inner_text())
    retry = student.locator('#retry-save')
    record('S04.actionable_save_failure', retry.is_visible() and '저장' in student.locator('#save-status').inner_text(), student.locator('#save-status').inner_text())
    browser.check_layout(student, 'student-save-recovery', output)
    capture_viewports(student, '#retry-save', 'student-save-recovery', output)
    student.unroute(pattern)
    if retained and retry.is_visible():
        retry.focus()
        student.keyboard.press('Enter')
        expect(retry).to_be_hidden()
        expect(student.locator('#progress-form button')).to_be_focused()
        saved = request(student, f'/extension/v1/student/lectures/{base["id"]}')['progress']
        record('S05.retry_retains_bookmark_and_focus', len(saved['bookmarks']) == 1, len(saved['bookmarks']))
    else:
        record('S05.retry_retains_bookmark_and_focus', False, 'No retry path')
    # The browser must retain invalid and failed manual position edits.
    open_lesson(student, base['id'])
    student_control(student, '#position').fill('99')
    student.route(pattern, fail_save)
    student_control(student, '#progress-form button').click()
    expect(student.locator('#progress-form button')).not_to_have_attribute('aria-busy', 'true')
    student_control(student, f'#lectures button[data-lecture="{other["id"]}"]').click()
    expect(student.locator(f'#lectures button[data-lecture="{other["id"]}"]')).not_to_have_attribute('aria-busy', 'true')
    record('S06.failed_manual_position_blocks_switch', student.locator('#lesson-title').inner_text() == base['title'], student.locator('#position').input_value())
    student.unroute(pattern)
    if student.locator('#retry-save').is_visible():
        student_control(student, '#retry-save').click()
        expect(student.locator('#retry-save')).to_be_hidden()
        saved = request(student, f'/extension/v1/student/lectures/{base["id"]}')['progress']
        record('S07.retry_keeps_entered_position', saved['position_ms'] == 99000, saved['position_ms'])
    else:
        record('S07.retry_keeps_entered_position', False, 'No retry path')
    open_lesson(student, other['id'])
    # A failed underline has the same recovery guarantee as notes and bookmarks.
    other_pattern = f'**/local/lectures/{other["id"]}/progress'
    student.route(other_pattern, fail_save)
    student_control(student, '#paragraph-selection').select_option(index=0)
    student_control(student, '#selected-underline').click()
    expect(student.locator('#selected-underline')).to_have_attribute('aria-pressed', 'true')
    student_control(student, f'#lectures button[data-lecture="{base["id"]}"]').click()
    expect(student.locator(f'#lectures button[data-lecture="{base["id"]}"]')).not_to_have_attribute('aria-busy', 'true')
    record('S08.failed_underline_blocks_switch', student.locator('#lesson-title').inner_text() == job['title'], student.locator('#lesson-title').inner_text())
    student.unroute(other_pattern)
    student_control(student, '#retry-save').click()
    expect(student.locator('#retry-save')).to_be_hidden()
    saved = request(student, f'/extension/v1/student/lectures/{other["id"]}')['progress']
    record('S09.retry_keeps_underline', len(saved['underlined']) == 1, len(saved['underlined']))
    # A late failed switch must not steal focus from newer typing in Find.
    held=[]
    student.route(other_pattern, lambda route: held.append(route))
    student_control(student, '#note').fill('저장 대기 뒤 새 입력을 보호합니다')
    student_control(student, f'#lectures button[data-lecture="{base["id"]}"]').click()
    student.wait_for_function('document.querySelector("#save-status").textContent.includes("저장 중")')
    assert held
    student_control(student, '#chat-input').fill('새 질문을 입력하는 중')
    for route in held:route.fulfill(status=503,content_type='application/json',body='{"detail":"지연된 저장 실패"}')
    expect(student.locator(f'#lectures button[data-lecture="{base["id"]}"]')).not_to_have_attribute('aria-busy','true')
    expect(student.locator('#chat-input')).to_be_focused()
    expect(student.locator('#error')).to_contain_text('필기에서 학습 기록 다시 저장')
    record('S14.delayed_failure_keeps_newer_focus', student.locator('#task-find').is_visible(), student.locator('#chat-input').input_value())
    student.unroute(other_pattern)
    student_control(student, '#retry-save').click()
    expect(student.locator('#retry-save')).to_be_hidden()
    entered=student.locator('#position').input_value()
    student_control(student, '#position').fill('-1')
    student_control(student, f'#lectures button[data-lecture="{base["id"]}"]').click()
    expect(student.locator('#position')).to_be_focused()
    expect(student.locator('#task-settings')).to_be_visible()
    expect(student.locator('#error')).to_contain_text('학습 위치')
    record('S15.invalid_position_exposes_correction', student.locator('#retry-save').is_hidden(), student.locator('#position').input_value())
    student_control(student, '#position').fill(entered)
    student_control(student, '#save-position').click()
    # App voice receives one failure notice and one recovery notice. This is a
    # synthetic speech boundary, independent of real OS screen-reader audio.
    student.evaluate(SPEECH)
    student_control(student, '#access-mode').select_option('app')
    student.route(other_pattern, fail_save)
    student_control(student, '#note').fill('음성으로 저장 실패 확인')
    student.wait_for_function('()=>window.__spoken.some(u=>u.text.includes("아직 저장하지"))')
    first = student.evaluate('window.__spoken.filter(u=>u.text.includes("아직 저장하지")).length')
    student_control(student, '#note').fill('음성으로 저장 실패 다시 확인')
    student.wait_for_timeout(900)  # Observe the documented 700ms autosave debounce.
    repeat = student.evaluate('window.__spoken.filter(u=>u.text.includes("아직 저장하지")).length')
    record('S10.failure_voice_once', first == repeat == 1, {'first': first, 'after_retry': repeat})
    student_control(student, '#retry-save').click()
    student.wait_for_function('()=>window.__spoken.filter(u=>u.text.includes("아직 저장하지")).length===2')
    record('S13.explicit_retry_failure_voice', True, 'Explicit retry announces repeated failure')
    student.unroute(other_pattern)
    student_control(student, '#note').fill('연결 복구 후 자동 저장')
    expect(student.locator('#retry-save')).to_be_hidden()
    student.wait_for_function('()=>window.__spoken.some(u=>u.text.includes("연결이 복구되어"))')
    record('S11.recovery_voice', True, student.locator('#save-status').inner_text())
    student_control(student, '#access-mode').select_option('silent')
    # Already queued saves must not obtain another account's fresh token.
    held = []
    student.route(other_pattern, lambda route: held.append(route))
    student_control(student, '#note').fill('처음 대기 메모')
    student.wait_for_timeout(900)
    assert len(held) == 1
    student_control(student, '#note').fill('두 번째 대기 메모')
    student.wait_for_timeout(900)
    student_control(student, '#logout').click()
    expect(student.locator('#auth')).to_be_visible()
    held[0].fulfill(status=200, content_type='application/json', body='{}')
    student.wait_for_timeout(300)
    record('S12.logout_cancels_queued_save', len(held) == 1, {'requests': len(held)})
    student.unroute(other_pattern)
    # Preparation discovery uses real persisted jobs and native keyboard controls.
    guardian.locator('#refresh-preparations').click()
    filters = guardian.locator('#preparation-filter')
    record('G01.preparation_dashboard', filters.count() == 1, {'filter': filters.count()})
    if filters.count():
        guardian.locator('#preparation-search').fill('없는 제목')
        expect(guardian.locator('#preparations')).to_contain_text('조건에 맞는 준비 작업이 없습니다')
        expect(guardian.locator('#preparation-search')).to_be_focused()
        guardian.locator('#preparation-search').fill('저장 복구')
        expect(guardian.locator('#preparations article')).to_have_count(1)
        filters.focus(); guardian.keyboard.press('Home'); guardian.keyboard.press('ArrowDown'); guardian.keyboard.press('Tab')
        filters.select_option('completed')
        expect(guardian.locator('#preparations article')).to_have_count(1)
        record('G02.filter_search_and_counts', '준비 완료 1' in guardian.locator('#preparation-counts').inner_text(), guardian.locator('#preparation-counts').inner_text())
        browser.check_layout(guardian, 'guardian-preparation-dashboard', output)
        capture_viewports(guardian, '#preparation-filter', 'guardian-preparation-dashboard', output)
        # Control only the listed job state, to exercise polling announcements
        # and focus recovery without a paid or artificially slow provider.
        jobs = request(guardian, '/extension/v1/guardian/preparations')
        listed = [{**entry, 'state': 'running', 'message': '시험 상태: 처리 시작'} for entry in jobs]
        guardian.route('**/extension/v1/guardian/preparations', lambda route: route.fulfill(
            status=200, content_type='application/json', body=json.dumps(listed)))
        guardian.locator('#preparations button').first.focus()
        guardian.evaluate('document.querySelector("#refresh-preparations").click()')
        expect(guardian.locator('#preparations article')).to_have_count(0)
        expect(guardian.locator('#preparations-title')).to_be_focused()
        record('G03.removed_job_focus_and_running_notice', '진행 중' in guardian.locator('#job-status').inner_text(), guardian.locator('#job-status').inner_text())
        guardian.unroute('**/extension/v1/guardian/preparations')
    # Complete guardian account creation -> sample selection -> assignment
    # using actual keyboard events, including native select and form submit.
    guardian.evaluate('''()=>{window.__followupPointers=0;document.addEventListener('pointerdown',()=>window.__followupPointers++);}''')
    for name, value in [('name', 'Keyboard Student'), ('username', 'keyboard-student'), ('password', 'keyboard-pass-123')]:
        tab_to(guardian, f'#student-form [name={name}]'); guardian.keyboard.type(value)
    tab_to(guardian, '#student-form button'); guardian.keyboard.press('Enter')
    expect(guardian.locator('#student-choice option')).to_have_count(2)
    target = next(person for person in request(guardian, '/local/students') if person['username'] == 'keyboard-student')
    choose_with_keys(guardian, '#student-choice', target['id'])
    choose_with_keys(guardian, '#assign-form [name=sample]', 'science')
    tab_to(guardian, '#assign-submit'); guardian.keyboard.press('Enter')
    expect(guardian.locator('#status')).to_contain_text('샘플 강의를 배정했습니다')
    assigned = request(guardian, '/local/lectures')
    record('G04.keyboard_only_guardian_flow', any(target['id'] in lecture['students'] for lecture in assigned)
           and guardian.evaluate('window.__followupPointers') == 0, {'pointer_events': guardian.evaluate('window.__followupPointers'),
            'selected_student': guardian.locator('#student-choice').input_value(), 'target': target['id']})
    browser.check_layout(guardian, 'guardian-keyboard-assignment', output)
    raise Complete()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('docs/verification/2026-11-14-followup'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    failure = None
    try:
        browser.main(exercise, phase='followup', output=args.output)
    except Complete:
        pass
    except Exception as error:
        import traceback
        failure = traceback.format_exc()
        print(failure, flush=True)
    result = {'result': 'passed' if failure is None and CHECKS and all(c['passed'] for c in CHECKS.values()) else 'failed',
              'checks': CHECKS, 'axe': browser.AXE_RESULTS,
              'error': failure,
              'boundary': 'Disposable installed extensions/API/DB; injected save 503 and listed running state; synthetic speech; no paid services or actual screen reader audio'}
    (args.output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    raise SystemExit(result['result'] != 'passed')
