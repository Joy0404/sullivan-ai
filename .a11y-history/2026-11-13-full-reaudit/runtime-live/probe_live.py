"""Audit-only installed-extension observations; no product/test changes.

Media decoding, extension workers, HTTP and DOM are real. Speech synthesis is a
recording test double so this never claims audible output or real OS AT speech.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from playwright.sync_api import expect
from starlette.responses import HTMLResponse
from starlette.routing import Route
from verify_extensions_browser import main
from verify_extensions_phase3 import video_fixture, SPEECH

OUTPUT = Path(__file__).resolve().parent
OBSERVATIONS = []


def snapshot(page):
    return page.evaluate("""() => ({connection:document.querySelector('#connection')?.textContent,
      error:document.querySelector('#error')?.textContent,
      status:document.querySelector('#status')?.textContent,
      accessMode:document.querySelector('#access-mode')?.value,
      spoken:(window.__spoken||[]).map(u=>u.text),events:window.__statusEvents||[]})""")


def reset_recording(page):
    page.evaluate("""() => {window.__spoken=[];window.__statusEvents=[];
      if(!window.__auditStatusListener){window.__auditStatusListener=true;
        window.addEventListener('sullivan-status',event=>window.__statusEvents.push(event.detail));}}
    """)


def exercise(guardian, student, output):
    from app import main as api, local_access
    from base64 import b64encode

    context = student.context
    context.add_init_script(SPEECH)
    student.evaluate(SPEECH)
    old_user = student.evaluate("async()=>{const{request}=await import('./client.js');return await request('/local/me')}")
    lesson_id = student.evaluate("async()=>{const{request}=await import('./client.js');return (await request('/local/lectures'))[0].id}")
    with local_access.db() as con:
        old_playback = con.execute('SELECT playback FROM lectures WHERE id=?', (lesson_id,)).fetchone()[0]
    with tempfile.TemporaryDirectory(prefix='live-audit-media-') as temporary:
        fixture = Path(temporary) / 'native.mp4'
        video_fixture(fixture)
        origin = student.evaluate("async()=>{const{SERVER}=await import('./config.js');return SERVER}")
        source = origin + '/live-audit-native.mp4'
        document = ('<!doctype html><html lang="ko"><title>Audit native media</title>'
                    '<video muted loop src="data:video/mp4;base64,'
                    + b64encode(fixture.read_bytes()).decode() + '"></video></html>')
        route = Route('/live-audit-native.mp4', lambda request: HTMLResponse(document))
        api.app.router.routes.insert(0, route)
        with local_access.db() as con:
            con.execute('UPDATE lectures SET playback=? WHERE id=?',
                        (json.dumps({'kind': 'direct', 'normalized_url': source}), lesson_id))
        try:
            student.reload()
            expect(student.locator('#lectures button')).to_have_count(1)
            student.locator('#lectures button').click()
            expect(student.locator('#lesson')).to_be_visible()
            student.locator('#access-mode').select_option('app')
            # Disable prepared automatic descriptions for this unrelated failure audit.
            student.get_by_text('음성·해설·키보드 설정', exact=True).click()
            student.locator('#preferences-form [name=auto_description]').uncheck()
            student.locator('#preferences-form button[type=submit]').click()
            expect(student.locator('#status')).to_have_text('내 학습 설정을 저장했습니다.')

            def connect_native():
                student.locator('#open-original').click()
                expect(student.locator('#connection')).to_contain_text('원본 강의 탭을 연결')
                native = next(page for page in context.pages if page.url == source)
                native.wait_for_function('()=>Boolean(document.querySelector("video")?.readyState>=1)')
                student.locator('#play').click()
                native.wait_for_function('()=>!document.querySelector("video").paused')
                student.wait_for_timeout(350)
                return native

            native = connect_native()
            reset_recording(student)
            before = snapshot(student)
            native.close()
            expect(student.locator('#connection')).not_to_have_text(before['connection'], timeout=7000)
            student.wait_for_timeout(700)
            after = snapshot(student)
            OBSERVATIONS.append({'id': 'LIVE-APP-VOICE-DIRECT-STATUS-tab-error',
                'boundary': 'Real original video tab closed; actual worker state RPC fails',
                'before': before, 'after': after,
                'product_invariant_passed': bool(after['spoken']),
                'observed': 'Connection text changed after real tab closure; compare spoken/event arrays.'})
            student.screenshot(path=str(output / 'student-tab-error.png'), full_page=True)

            native = connect_native()
            full = context.new_page()
            full.goto(student.url.split('?')[0].split('#')[0])
            expect(full.locator('#workspace')).to_be_visible()
            student.wait_for_timeout(250)
            reset_recording(student)
            before = snapshot(student)
            claim = full.evaluate("""async()=>await chrome.runtime.sendMessage({type:'student-media',
              view:'audit-other-learning-view',action:'claim'})""")
            expect(student.locator('#connection')).to_contain_text('다른 수강 화면', timeout=5000)
            native.wait_for_function('()=>document.querySelector("video").paused')
            student.wait_for_timeout(700)
            after = snapshot(student)
            OBSERVATIONS.append({'id': 'LIVE-APP-VOICE-DIRECT-STATUS-lease-loss',
                'boundary': 'Another installed extension document obtains an actual worker lease',
                'claim_response': claim, 'before': before, 'after': after,
                'original_video_paused': native.evaluate('document.querySelector("video").paused'),
                'product_invariant_passed': bool(after['spoken'])})
            student.screenshot(path=str(output / 'student-lease-loss.png'), full_page=True)
            full.close(); native.close()

            # Genuine configured-server failure: no Gemini key is set by the harness.
            guardian.evaluate("""async()=>{const{request}=await import('./client.js');
              return await request('/extension/v1/guardian/preparations',{method:'POST',body:{
                title:'Live error audit prep',assets:[{name:'audit.txt',kind:'passage',content:'감사용 지문입니다.'}]}})}""")
            guardian.locator('#refresh-preparations').click()
            ready = guardian.get_by_role('button', name='Live error audit prep 결과 확인·배정', exact=True)
            expect(ready).to_be_visible(); ready.click()
            form = guardian.locator('#preview-question-form')
            form.locator('[name=message]').fill('지문의 핵심을 알려 주세요.')
            form.locator('[name=analysis_consent]').check()
            with guardian.expect_response(lambda response: '/agent-turn' in response.url) as received:
                form.locator('button').click()
            response = received.value
            expect(guardian.locator('#error')).to_contain_text('실제 학습 대화 연결')
            guardian.wait_for_timeout(700)
            pending = guardian.locator('#preview-answer').inner_text()
            OBSERVATIONS.append({'id': 'LIVE-GUARDIAN-PREVIEW-PENDING-ERROR',
                'http_status': response.status, 'http_body': response.json(),
                'result_status': pending, 'global_error': guardian.locator('#error').inner_text(),
                'product_invariant_passed': '확인하고 있습니다' not in pending})
            guardian.screenshot(path=str(output / 'guardian-preview-error.png'), full_page=True)

            # Check actual enqueue order with server reader prefs and no local override.
            with local_access.db() as con:
                settings = dict(old_user['settings'])
                settings.update(reader_mode=True, focus_voice=False)
                con.execute('UPDATE users SET settings=? WHERE id=?', (json.dumps(settings), old_user['id']))
            student.evaluate("async()=>await chrome.storage.local.remove('student-accessibility')")
            reader = context.new_page()
            reader.goto(student.url.split('?')[0].split('#')[0])
            expect(reader.locator('#workspace')).to_be_visible()
            expect(reader.locator('#access-mode')).to_have_value('reader')
            expect(reader.locator('#lectures button')).to_have_count(1)
            reader.wait_for_timeout(400)
            observed = snapshot(reader)
            OBSERVATIONS.append({'id': 'LIVE-READER-SETTING-FOCUS-RACE',
                'server_reader_mode': True, 'local_override_removed': True, 'after': observed,
                'product_invariant_passed': not observed['spoken'],
                'interpretation': 'Recorded speechSynthesis calls only; no claim that real audio was heard.'})
            reader.screenshot(path=str(output / 'student-reader-initial-mode.png'), full_page=True)
            reader.close()
        finally:
            with local_access.db() as con:
                con.execute('UPDATE lectures SET playback=? WHERE id=?', (old_playback, lesson_id))
                con.execute('UPDATE users SET settings=? WHERE id=?', (json.dumps(old_user['settings']), old_user['id']))
            api.app.router.routes.remove(route)
            # Restore the cumulative harness's original record without source changes.
            student.evaluate("""async(id)=>{const{request}=await import('./client.js');
              return await request('/local/lectures/'+id+'/progress',{method:'PUT',body:{
                position_ms:42000,note:'확장 분리 검증 메모',bookmarks:[],underlined:[]}})}""", lesson_id)
    report = {'browser': context.browser.version, 'actual_extensions': 2,
        'boundaries': {'HTTP': 'real temporary server/DB', 'worker': 'real installed extension',
                       'media': 'real decoded generated video', 'speech': 'recording test double',
                       'OS_screen_reader': 'not run'},
        'source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (ROOT/'apps/extensions/student/app.js', ROOT/'apps/extensions/student/speech.js',
                         ROOT/'apps/extensions/guardian/app.js', ROOT/'apps/extensions/shared/ui.js')},
        'observations': OBSERVATIONS}
    (output / 'observations.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return guardian


if __name__ == '__main__':
    try:
        main(exercise, phase='runtime-live-audit-harness', output=OUTPUT)
    except BaseException as error:
        (OUTPUT / 'probe-error.json').write_text(json.dumps({'error': str(error), 'observations': OBSERVATIONS},
            ensure_ascii=False, indent=2)+'\n')
        raise
