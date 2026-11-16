"""Account/lecture fences for delayed notebook creation in installed MV3.

Disposable accounts, actual UI/API/DB. Only the media pause acknowledgment is
held; no user database, paid provider or real speech service is used.
"""
import argparse
import json
from pathlib import Path

from playwright.sync_api import expect
import verify_extensions_browser as browser
from verify_reaudit_fixes import Complete, prepare, request


def exercise(guardian, student, output):
    original = request(student, '/local/me')['id']
    first = request(student, '/local/lectures')[0]['id']
    second_student = request(guardian, '/local/students', 'POST', {
        'name': 'Notebook second student', 'username': 'notebook-second',
        'password': 'extension-pass-123'})['id']
    assigned = request(guardian, '/local/samples/science/assign', 'POST', {'students': [second_student]})['id']
    job = prepare(guardian, '별도 필기 강의', {'assets': [
        {'name': 'notes.txt', 'kind': 'passage', 'content': '다른 강의의 안전한 지문입니다.'}]})
    other = request(guardian, f'/extension/v1/guardian/preparations/{job["id"]}/publish',
                    'POST', {'students': [original]})['id']
    student.evaluate("""async()=>{
      const {StudentMedia}=await import('./media.js');const pause=StudentMedia.prototype.pause;
      StudentMedia.prototype.pause=async function(...args){
        const result=await pause.apply(this,args);
        if(window.__holdNotebookPause){window.__holdNotebookPause=false;window.__notebookPaused=true;
          await new Promise(resolve=>window.__releaseNotebookPause=resolve);}
        return result;
      };
    }""")
    checks = []

    def open_lesson(ident):
        student.locator('#task-home-button').press('Enter')
        student.locator('#refresh').click()
        student.locator(f'#lectures button[data-lecture="{ident}"]').click()
        expect(student.locator('#lesson')).to_be_visible()
        student.locator('#task-notes-button').press('Enter')
        expect(student.locator('#new-note')).to_be_enabled()

    def hold_copy(marker):
        student.locator('#note').fill(marker)
        student.locator('#progress-form button').click()
        expect(student.locator('#status')).to_have_text('학습 위치와 메모를 저장했습니다.')
        student.evaluate('window.__notebookPaused=false;window.__holdNotebookPause=true')
        student.locator('#import-legacy-note').click()
        student.wait_for_function('window.__notebookPaused===true')

    def preserve_new_editor(ident, marker, label):
        student.locator('#new-note').click()
        student.locator('#note-body').fill(marker)
        student.locator('#save-note').click()
        expect(student.locator('#note-save-status')).to_have_text('필기를 저장했습니다.')
        student.evaluate('window.__releaseNotebookPause()')
        expect(student.locator('#import-legacy-note')).not_to_have_attribute('aria-busy', 'true')
        student.wait_for_timeout(1100)  # An obsolete debounce must not write later.
        notes = request(student, f'/extension/v1/student/lectures/{ident}/notes')
        assert [note['body'] for note in notes] == [marker], notes
        expect(student.locator('#note-body')).to_have_value(marker)
        drafts = student.evaluate("async()=>Object.entries(await chrome.storage.local.get(null)).filter(([key])=>key.startsWith('note-draft:')).map(([key,value])=>({key,body:value.body}))")
        assert not any(row['body'].startswith('PRIVATE_PREVIOUS_') for row in drafts), drafts
        checks.append(label)

    open_lesson(first)
    # New typing must cancel a pending conflict copy without deleting its draft.
    student.locator('#new-note').click()
    student.locator('#note-body').fill('충돌 전 필기')
    student.locator('#save-note').click()
    expect(student.locator('#note-save-status')).to_have_text('필기를 저장했습니다.')
    saved = request(student, f'/extension/v1/student/lectures/{first}/notes')[0]
    request(student, f'/extension/v1/student/lectures/{first}/notes/{saved["id"]}', 'PUT', {
        'body': '다른 화면의 본문', 'started_ms': saved['started_ms'], 'source': None, 'revision': saved['revision']})
    student.locator('#note-body').fill('내가 보존할 충돌 초안')
    student.locator('#save-note').click()
    expect(student.locator('#copy-note-draft')).to_be_visible()
    student.evaluate('window.__notebookPaused=false;window.__holdNotebookPause=true')
    student.locator('#copy-note-draft').click()
    student.wait_for_function('window.__notebookPaused===true')
    latest = '내가 보존할 충돌 초안 그리고 새로 입력한 말'
    student.locator('#note-body').fill(latest)
    student.evaluate('window.__releaseNotebookPause()')
    expect(student.locator('#copy-note-draft')).not_to_have_attribute('aria-busy', 'true')
    expect(student.locator('#note-body')).to_have_value(latest)
    student.wait_for_timeout(1100)
    drafts = student.evaluate("async()=>Object.entries(await chrome.storage.local.get(null)).filter(([key])=>key.startsWith('note-draft:')).map(([,value])=>value.body)")
    assert latest in drafts, drafts
    student.locator('#copy-note-draft').click()
    student.locator('#save-note').click()
    expect(student.locator('#note-save-status')).to_have_text('필기를 저장했습니다.')
    bodies = [note['body'] for note in request(student, f'/extension/v1/student/lectures/{first}/notes')]
    assert sorted(bodies) == sorted(['다른 화면의 본문', latest]), bodies
    checks.append('typing during delayed conflict copy preserves latest editor and draft; explicit retry keeps both server notes')
    hold_copy('PRIVATE_PREVIOUS_LECTURE')
    open_lesson(other)
    preserve_new_editor(other, '새 강의에서 내가 작성한 필기', 'late legacy copy cannot enter another lecture or replace its editor')
    open_lesson(first)
    hold_copy('PRIVATE_PREVIOUS_ACCOUNT')
    student.locator('#logout').click()
    expect(student.locator('#auth')).to_be_visible()
    student.locator('#username').fill('notebook-second')
    student.locator('#password').fill('extension-pass-123')
    student.locator('#login-form button').click()
    expect(student.locator('#workspace')).to_be_visible()
    open_lesson(assigned)
    preserve_new_editor(assigned, '새 학생이 직접 작성한 필기', 'late legacy copy cannot enter another account or save its active editor')
    browser.check_layout(student, 'notebook-race-safe-editor', output, skip=False)
    (output/'results.json').write_text(json.dumps({
        'result': 'passed', 'checks': checks, 'raw_media_uploaded': False,
        'boundary': __doc__.strip()}, ensure_ascii=False, indent=2)+'\n')
    raise Complete()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        browser.main(exercise, phase='notebook-races', output=args.output)
    except Complete:
        pass
