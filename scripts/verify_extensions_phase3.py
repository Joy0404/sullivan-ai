"""Real media/extension flow with a generated video and explicitly mocked speech/provider boundaries."""
from verify_extensions_browser import student_disclosure, student_control, student_role, student_text
import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from unittest.mock import patch
from starlette.responses import HTMLResponse
from starlette.routing import Route

from playwright.sync_api import expect
from verify_extensions_browser import main, check_layout
from verify_extensions_phase2 import exercise as phase2

SPEECH = '''(() => {
  window.__spoken=[]; window.__holdSpeech=false;
  window.SpeechSynthesisUtterance=class { constructor(text){this.text=text;} };
  Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{
    speak(u){window.__spoken.push(u);u.onstart?.(); if(!window.__holdSpeech)setTimeout(()=>u.onend?.(),50);}, cancel(){}}});
})();'''


def video_fixture(path):
    binary = os.getenv('SULLIVAN_FFMPEG') or shutil.which('ffmpeg')
    if not binary:
        from imageio_ffmpeg import get_ffmpeg_exe
        binary = get_ffmpeg_exe()
    subprocess.run([binary, '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=160x90:r=10',
        '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=8000', '-t', '8', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-movflags', '+faststart', '-y', str(path)], check=True)


def exercise(guardian, student, output):
    guardian = phase2(guardian, student, output)
    context = student.context
    context.add_init_script(SPEECH); student.evaluate(SPEECH)
    from app import main as api, local_access
    from app.models import AnalysisPackageInput, AgentTurnResponse
    package = AnalysisPackageInput.model_validate({
        'transcript_segments': [{'segment_id': 'intro', 'start_ms': 0, 'end_ms': 7000, 'text': '연습용 영상의 자막입니다.'}],
        'passage_text': '합의 원리를 살펴봅니다.\n\n두 수를 함께 묶는 과정을 설명합니다.',
        'visual_observations': [{'observation_id': 'native-board', 'timestamp_ms': 700, 'screen_type': 'board',
            'kind': 'formula', 'text': '검증된 판서 A+B', 'confidence': .98, 'importance': .99}],
        'study_guide': {'overview': '합의 원리 학습', 'concept_map': ['두 수에서 합으로 연결'],
            'glossary': [{'term': '합의 원리', 'definition': '두 수를 함께 묶어 살펴보는 원리입니다.'}], 'recall_questions': ['합의 원리를 설명해 보세요.']}})
    async def analyze(path, **kwargs):
        kwargs['cleanup_report']['provider'] = 'deleted'
        return package
    with tempfile.TemporaryDirectory(prefix='sullivan-media-') as temp:
        fixture = Path(temp) / 'native.mp4'; video_fixture(fixture)
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'fixture-key', 'DEMO_ACCESS_CODE': 'fixture-code'}), patch.object(api, 'analyze_uploaded_video_with_gemini', analyze):
            form = guardian.locator('#prepare-form')
            guardian.locator('#prepare-source').select_option('video')
            form.locator('[name=title]').fill('동기화 테스트 강의')
            guardian.locator('#prepare-video').set_input_files(str(fixture))
            guardian.locator('#prepare-rights').check(); guardian.locator('#prepare-consent').check()
            form.locator('button[type=submit]').click()
            expect(guardian.locator('#status')).to_contain_text('준비를 접수했습니다')
            guardian.locator('#refresh-preparations').click()
            guardian.get_by_role('button', name='동기화 테스트 강의 결과 확인·배정', exact=True).click()
            expect(guardian.locator('#prepared-title')).to_have_text('동기화 테스트 강의 준비 결과')
            guardian.locator('#publish-students').get_by_label('학생 하나', exact=True).check()
            expect(guardian.locator('#publish-students input')).to_be_checked()
            guardian.locator('#publish-form button').click()
            expect(guardian.locator('#status')).to_contain_text('학생에게 배정했습니다')
        student_control(student, '#refresh').click()
        student_control(student, '#lectures button').filter(has_text='동기화 테스트 강의 열기').click()
        expect(student.locator('#lesson')).to_be_visible()
        student_disclosure(student, '내 기기의 영상 연결·보관')
        student_control(student, '#local-file').set_input_files({'name': 'wrong.mp4', 'mimeType': 'video/mp4', 'buffer': b'different original'})
        student_control(student, '#connect-file').click()
        expect(student.locator('#connection')).to_contain_text('다른 파일')
        student_control(student, '#local-file').set_input_files(str(fixture))
        student_control(student, '#store-original').check(); student_control(student, '#video-muted').check()
        sent_media = []
        student.on('request', lambda request: sent_media.append(request.url) if request.method == 'POST' and 'multipart/form-data' in request.headers.get('content-type', '') else None)
        student_control(student, '#connect-file').click()
        expect(student.locator('#connection')).to_contain_text('분석한 원본과 일치')
        assert not sent_media
        student.locator('#task-listen-button').press('Enter')
        expect(student.locator('#local-video')).to_be_visible()
        student.wait_for_function("document.querySelector('#local-video').textTracks[0]?.cues?.length > 0")
        student_control(student, '#captions').click()
        assert student.evaluate("document.querySelector('#local-video').textTracks[0].mode") == 'hidden'
        student_control(student, '#captions').click()
        student_control(student, '#play').click()
        expect(student.locator('#reader-description')).to_contain_text('검증된 판서')
        assert student.evaluate("document.querySelector('#local-video').paused")
        # Turn app speech on and automatic descriptions off to exercise cancellation deterministically.
        student_text(student, '음성·해설·키보드 설정', exact=True).click()
        student_control(student, '#preferences-form [name=reader_mode]').uncheck()
        student_control(student, '#preferences-form [name=auto_description]').uncheck()
        student_control(student, '#space-enabled').check()
        student_control(student, '#preferences-form button[type=submit]').click()
        expect(student.locator('#status')).to_have_text('내 학습 설정을 저장했습니다.')
        if getattr(exercise,'student_check',None):exercise.student_check(guardian,student,output)
        student_control(student, '#play').click()
        student.evaluate('window.__holdSpeech=true')
        before = student.evaluate('window.__spoken.length')
        student_control(student, '#read').click()
        student.wait_for_function('(n)=>window.__spoken.length>n', arg=before)
        assert student.evaluate("document.querySelector('#local-video').paused")
        student_control(student, '#stop').click()
        student.evaluate('window.__spoken.at(-1).onend?.()')
        expect(student.locator('#read')).not_to_have_attribute('aria-busy', 'true')
        assert student.evaluate("document.querySelector('#local-video').paused")
        student.evaluate('window.__holdSpeech=false')
        # First voice use requires an accessible consent dialog after exactly 3 seconds.
        student_control(student, '#type-command').focus(); student.keyboard.down('Space')
        expect(student.locator('#voice-permission-dialog')).to_be_visible(timeout=4000)
        student.keyboard.up('Space'); student.keyboard.press('Escape')
        expect(student.locator('#type-command')).to_be_focused()
        student_control(student, '#type-command').click()
        student_control(student, '#text-command').fill('강의 목록')
        student_control(student, '#dialog-form button[type=submit]').click()
        expect(student.locator('#home-title')).to_be_focused()
        summary = student_text(student, '음성·해설·키보드 설정', exact=True)
        summary.focus(); student.keyboard.press('Enter')
        expect(student.locator('#preferences-form')).to_be_hidden()
        summary.press('Enter'); expect(student.locator('#preferences-form')).to_be_visible()
        student_control(student, '#position').fill('2'); student_control(student, '#progress-form button').click()
        expect(student.locator('#status')).to_have_text('학습 위치와 메모를 저장했습니다.')
        student_control(student, '#bookmark').click(); expect(student.locator('#bookmarks li')).to_have_count(1)
        student_control(student, '#paragraph-selection').select_option(index=1)
        student_control(student, '#selected-underline').click()
        expect(student.locator('#selected-underline')).to_have_attribute('aria-pressed', 'true')
        student_control(student, '#paragraph-form [name=query]').fill('다음 문장'); student_control(student, '#paragraph-form button').click()
        student_control(student, '#search-form [name=query]').fill('합의 원리'); student_control(student, '#search-form button').click()
        expect(student.locator('#search-results')).to_contain_text('두 수를 함께 묶어')
        # The approved minimal notebook scope rejects removed generation tools.
        student_control(student, '#chat-input').fill('퀴즈 만들어줘')
        student_control(student, '#chat-form button').click()
        expect(student.locator('#status')).to_contain_text('자동 학습 도구 생성은 제공하지 않습니다')
        with student.expect_download() as download:
            student_control(student, '#export-notes').click()
        assert download.value.suggested_filename == 'sullivan-study-notes.md'
        check_layout(student, 'student-phase3', output)
        lesson_id = student.evaluate("async()=>{const{request}=await import('./client.js');return (await request('/local/lectures')).find(l=>l.title==='동기화 테스트 강의').id;}")
        # A delayed provider response from the old view must not speak after another view claims playback.
        with local_access.db() as con: con.execute('UPDATE lectures SET chat_allowed=1 WHERE id=?', (lesson_id,))
        async def delayed(*args, **kwargs):
            await asyncio.sleep(1.5)
            return AgentTurnResponse(action='answer', title='늦은 답변', response_text='늦게 도착한 답변은 실행하면 안 됩니다.', decision_reason='test', confidence=.99)
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'fixture-key'}), patch('app.adapters.gemini_agent.run_agent_turn', delayed):
            student_control(student, '#chat-input').fill('합의 원리를 설명해 주세요.')
            student_control(student, '#chat-form button').click()
            full = context.new_page(); full.goto(student.url.split('#')[0].split('?')[0] + '?lecture=' + lesson_id)
            expect(full.locator('#lesson')).to_be_visible()
            student_disclosure(full, '내 기기의 영상 연결·보관')
            student_control(full, '#load-original').click()
            expect(full.locator('#connection')).to_contain_text('분석한 원본과 일치')
            expect(student.locator('#connection')).to_contain_text('다른 수강 화면')
            expect(student.locator('#chat-form button')).not_to_have_attribute('aria-busy', 'true', timeout=5000)
            assert '늦은 답변' not in student.locator('#chat-log').inner_text()
        student_control(student, '#read').click()
        expect(full.locator('#connection')).to_contain_text('다른 수강 화면')
        # Validate the isolated tab adapter with a real decoded native player, not a mocked video object.
        from base64 import b64encode
        with local_access.db() as con:
            identity = json.loads(con.execute('SELECT identity FROM lecture_media WHERE lecture=?', (lesson_id,)).fetchone()[0])
        server_origin = full.evaluate("async()=>{const{SERVER}=await import('./config.js');return SERVER;}")
        source = server_origin + '/native-player.mp4'
        document = f'<html lang="ko"><title>Native video fixture</title><video muted src="data:video/mp4;base64,{b64encode(fixture.read_bytes()).decode()}"></video></html>'
        native_route = Route('/native-player.mp4', lambda request: HTMLResponse(document))
        api.app.router.routes.insert(0, native_route)
        with local_access.db() as con:
            con.execute('UPDATE lectures SET playback=? WHERE id=?', (json.dumps({'kind':'direct','normalized_url':source}), lesson_id))
        full.reload(); expect(full.locator('#lesson')).to_be_visible()
        student_control(full, '#video-muted').check(); student_control(full, '#open-original').click()
        expect(full.locator('#connection')).to_contain_text('원본 강의 탭을 연결')
        native = next(page for page in context.pages if page.url == source)
        native.wait_for_selector('video', timeout=5000)
        student_control(full, '#play').click(); native.wait_for_function('document.querySelector("video") && !document.querySelector("video").paused', timeout=5000)
        full.locator('#stop').click(); native.wait_for_function('document.querySelector("video").paused')
        full.locator('#play').click(); native.wait_for_function('!document.querySelector("video").paused')
        full.close(); native.wait_for_function('document.querySelector("video").paused', timeout=6500)
        native.close()
        api.app.router.routes.remove(native_route)
        guardian.get_by_role('button', name='동기화 테스트 강의 배정 수정', exact=True).click()
        guardian.locator('#withdraw').click(); guardian.locator('#withdraw-yes').click()
        expect(guardian.locator('#status')).to_contain_text('배정을 회수했습니다.')
        student_control(student, '#refresh').click(); expect(student.locator('#lectures button')).to_have_count(1)
    return guardian


exercise.checks = ['native local video pause/play/seek', 'fingerprint-verified file, no student upload',
    'encrypted original reload', 'caption track and toggle', 'automatic prepared narration in reader mode',
    'late TTS stop cancellation', 'optional Space and modal fallback', 'bookmark and underline persistence',
    'concept search and removed-generation rejection', 'notes export', 'cross-view delayed answer cancellation',
    'isolated native tab control', 'closed-view playback watchdog']

if __name__ == '__main__':
    main(exercise, phase='phase3')
