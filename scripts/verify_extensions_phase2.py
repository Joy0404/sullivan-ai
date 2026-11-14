"""Actual extension preparation/management flow; no paid model calls."""
from playwright.sync_api import expect
from verify_extensions_browser import main, check_layout


def exercise(guardian, student, output):
    form = guardian.locator('#prepare-form')
    form.locator('[name=title]').fill('새 지문 강의')
    form.locator('[name=subject]').fill('국어')
    guardian.locator('#prepare-source').select_option('link')
    guardian.locator('#prepare-url').fill('invalid-url')
    guardian.locator('#prepare-source').select_option('materials')
    # A hidden malformed URL must not block the now-active text form.
    expect(guardian.locator('#prepare-url')).to_be_disabled()
    form.locator('[name=passage]').fill('첫 문단은 관찰을 설명합니다.\n\n둘째 문단은 결과를 정리합니다.')
    guardian.locator('#material-files').set_input_files({
        'name': 'subtitles.srt', 'mimeType': 'text/plain',
        'buffer': b'1\n00:00:01,000 --> 00:00:04,000\nTest subtitle\n'})
    form.locator('button[type=submit]').focus()
    guardian.keyboard.press('Enter')
    expect(guardian.locator('#status')).to_contain_text('준비를 접수했습니다')
    # Closing the extension document must not lose the server-side job/result.
    url, context = guardian.url, guardian.context
    guardian.close()
    guardian = context.new_page()
    guardian.goto(url)
    expect(guardian.locator('#workspace')).to_be_visible()
    guardian.locator('#refresh-preparations').click()
    ready = guardian.get_by_role('button', name='새 지문 강의 결과 확인·배정', exact=True)
    expect(ready).to_be_visible()
    ready.focus(); guardian.keyboard.press('Enter')
    expect(guardian.locator('#prepared-preview')).to_contain_text('첫 문단은 관찰')
    guardian.locator('#publish-students').get_by_label('학생 하나', exact=True).check()
    guardian.locator('#publish-form button').focus(); guardian.keyboard.press('Enter')
    expect(guardian.locator('#status')).to_have_text('확인한 자료를 학생에게 배정했습니다.')
    expect(guardian.locator('#lectures li')).to_have_count(2)
    student.locator('#refresh').click()
    expect(student.locator('#lectures button')).to_have_count(2)
    student.locator('#lectures button').filter(has_text='새 지문 강의 열기').click()
    expect(student.locator('#material')).to_contain_text('둘째 문단은 결과')
    # Current record summaries show counts, not the student's private note text.
    guardian.locator('#load-management').focus(); guardian.keyboard.press('Enter')
    expect(guardian.locator('#management-detail')).to_be_visible()
    guardian.locator('#settings-form [name=speech_rate]').fill('1.1')
    guardian.locator('#settings-form [name=reader_mode]').check()
    guardian.locator('#settings-form button').focus(); guardian.keyboard.press('Enter')
    expect(guardian.locator('#status')).to_have_text('학생 기본 설정을 저장했습니다.')
    rate = student.evaluate("async () => {const {request}=await import('./client.js'); return (await request('/local/me')).settings.speech_rate;}")
    assert rate == 1.1
    guardian.get_by_role('button', name='새 지문 강의 위로', exact=True).click()
    expect(guardian.locator('#lecture-order li').first).to_contain_text('새 지문 강의')
    student.locator('#refresh').click()
    expect(student.locator('#lectures button').first).to_have_text('새 지문 강의 열기')
    guardian.get_by_role('button', name='새 지문 강의 배정 수정', exact=True).click()
    guardian.locator('#edit-form [name=title]').fill('수정된 지문 강의')
    guardian.locator('#edit-form button').focus(); guardian.keyboard.press('Enter')
    expect(guardian.locator('#status')).to_contain_text('강의와 배정을 저장')
    check_layout(guardian, 'guardian-phase2', output)
    guardian.locator('#withdraw').focus(); guardian.keyboard.press('Enter')
    expect(guardian.locator('#withdraw-question')).to_contain_text('수정된 지문 강의')
    expect(guardian.locator('#withdraw-yes')).to_be_focused()
    guardian.locator('#withdraw-no').click()
    expect(guardian.locator('#withdraw')).to_be_focused()
    guardian.locator('#withdraw').press('Enter')
    guardian.locator('#withdraw-yes').press('Enter')
    expect(guardian.locator('#status')).to_contain_text('배정을 회수했습니다.')
    student.locator('#refresh').click()
    expect(student.locator('#lectures button')).to_have_count(1)
    expect(student.locator('#lesson')).to_be_hidden()
    return guardian


if __name__ == '__main__':
    main(exercise)
