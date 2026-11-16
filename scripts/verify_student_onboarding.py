"""Installed MV3 tutorial checks; real media/keyboard, explicit ASR and response mocks."""
import argparse
import json
from pathlib import Path
import tempfile

from playwright.sync_api import expect
import verify_extensions_browser as browser
from verify_extensions_phase3 import video_fixture, SPEECH
from verify_reaudit_fixes import Complete

CHECKS = {}


def exercise(guardian, student, output):
    student.evaluate(SPEECH)
    browser.student_control(student, '#access-mode').select_option('silent')
    turns, uploads = [], []
    student.on('request', lambda r: turns.append(r.url) if '/agent-turn' in r.url else None)
    student.on('request', lambda r: uploads.append(r.url) if r.method == 'POST' and 'multipart/form-data' in r.headers.get('content-type', '') else None)

    def enter(selector):
        target = browser.student_control(student, selector)
        target.focus()
        student.keyboard.press('Enter')

    def command(text):
        return student.evaluate("async text=>(await import('./app.js')).command(text)", text)

    enter('#show-practice')
    expect(student.locator('#practice-title')).to_be_focused()
    enter('#practice-start')
    expect(student.locator('#status')).to_contain_text('먼저 영상 연결')
    expect(student.locator('#practice-steps')).not_to_contain_text('실습 완료')
    CHECKS['no_simulated_completion_without_media'] = True

    with tempfile.TemporaryDirectory(prefix='sullivan-practice-media-') as temporary:
        fixture = Path(temporary) / 'practice.mp4'
        video_fixture(fixture)
        enter('#practice-connect')
        expect(student.locator('#connection-title')).to_be_focused()
        browser.student_control(student, '#local-file').set_input_files(fixture)
        browser.student_control(student, '#video-muted').check()
        enter('#connect-file')
        expect(student.locator('#connection')).to_contain_text('로컬 영상')
        # The sample's saved position may exceed this generated eight-second fixture.
        student.evaluate("document.querySelector('#local-video').currentTime=0")

        # Failed stopping must preserve progress and allow a real retry.
        student.evaluate("""async()=>{
          const{StudentMedia}=await import('./media.js');window.__practicePause=StudentMedia.prototype.pause;
          StudentMedia.prototype.pause=async function(...args){await window.__practicePause.apply(this,args);throw new Error('injected pause failure');};
        }""")
        enter('#practice-start')
        expect(student.locator('#error')).to_contain_text('영상이 멈춘 것을 확인하지 못했습니다')
        expect(student.locator('#practice-start')).not_to_have_attribute('aria-busy', 'true')
        expect(student.locator('#practice-steps')).not_to_contain_text('실습 완료')
        student.evaluate("async()=>{const{StudentMedia}=await import('./media.js');StudentMedia.prototype.pause=window.__practicePause;}")
        CHECKS['pause_failure_does_not_start_practice'] = True

        def delay_pause():
            student.evaluate("""async()=>{
              const{StudentMedia}=await import('./media.js');window.__releasePractice=null;
              StudentMedia.prototype.pause=async function(...args){await window.__practicePause.apply(this,args);await new Promise(resolve=>window.__releasePractice=resolve);};
            }""")
        def finish_pause():
            student.evaluate("async()=>{const{StudentMedia}=await import('./media.js');StudentMedia.prototype.pause=window.__practicePause;window.__releasePractice();}")
            expect(student.locator('#practice-start')).not_to_have_attribute('aria-busy', 'true')

        delay_pause();enter('#practice-start')
        student.wait_for_function('()=>Boolean(window.__releasePractice)')
        enter('#practice-skip');finish_pause()
        expect(student.locator('#practice-card')).to_be_hidden()
        expect(student.locator('#context-help')).to_be_focused()
        CHECKS['pending_start_skip_cannot_reopen_or_steal_focus'] = True
        enter('#show-practice')

        assert command('영상 재생') is True
        student.wait_for_function("()=>!document.querySelector('#local-video').paused")
        enter('#practice-start')
        expect(student.locator('#practice-start')).not_to_have_attribute('aria-busy', 'true')
        student.wait_for_function("()=>document.querySelector('#local-video').paused")
        expect(student.locator('#practice-steps li').nth(0)).to_contain_text('미시도')
        expect(student.locator('#practice-title')).to_be_focused()
        CHECKS['playing_practice_start_pauses_before_first_space'] = True

        delay_pause();enter('#practice-start')
        student.wait_for_function('()=>Boolean(window.__releasePractice)')
        enter('#task-notes-button');student.locator('#new-note').focus();finish_pause()
        expect(student.locator('#task-notes')).to_be_visible()
        expect(student.locator('#new-note')).to_be_focused()
        CHECKS['pending_start_preserves_new_keyboard_focus'] = True
        student.locator('#practice-title').focus()
        student.keyboard.press('Space')
        student.wait_for_function("()=>!document.querySelector('#local-video').paused")
        student.wait_for_timeout(100)
        student.keyboard.press('Space')
        expect(student.locator('#practice-steps li').nth(0)).to_contain_text('실습 완료')
        expect(student.locator('#status')).to_contain_text('Space 두 번')
        student.keyboard.press('Space');student.keyboard.press('Space')
        expect(student.locator('#practice-steps li').nth(1)).to_contain_text('실습 완료')
        student.wait_for_timeout(450)
        for _ in range(3):
            student.keyboard.press('Space')
        expect(student.locator('#text-dialog')).to_be_visible()
        expect(student.locator('#text-command')).to_be_focused()
        student.locator('#text-command').fill('현재 상태')
        student.keyboard.press('Enter')
        expect(student.locator('#practice-steps li').nth(2)).to_contain_text('실습 완료')
        expect(student.locator('#status')).to_contain_text('기본 조작 연습을 완료')
        CHECKS['actual_space_play_pause_stop_and_typed_status'] = True

        assert command('영상 재생') is True
        expect(student.locator('#interaction-result')).to_have_text('강의 재생: 완료.')
        assert command('전체 중지') is True
        expect(student.locator('#interaction-result')).to_have_text('전체 중지: 완료.')
        assert command('현재 상태') is True
        expect(student.locator('#status')).to_contain_text('전체 중지: 완료')
        command('도움말')
        expect(student.locator('#onboarding-title')).to_be_focused()
        assert turns == [] and uploads == [], (turns, uploads)
        CHECKS['controls_help_status_practice_zero_model_requests_and_uploads'] = True

        # Recognition completion and errors are mocked; actual browser ASR is unverified.
        student.evaluate("""()=>{
          window.__statusMessages=[];window.addEventListener('sullivan-status',e=>window.__statusMessages.push(e.detail.text));
          window.SpeechRecognition=class {start(){this.onstart?.();}abort(){}stop(){
            this.onresult?.({results:[[{transcript:'현재 상태'}]]});const end=this.onend;end?.();end?.();
          }};
          document.querySelector('#voice-consent').checked=true;
        }""")
        enter('#voice');enter('#voice')
        expect(student.locator('#practice-instruction')).to_contain_text('선택형 음성 입력 연습을 완료')
        assert student.evaluate("window.__statusMessages.filter(t=>t.includes('새 명령 대기')).length") == 1
        CHECKS['duplicate_final_recognition_runs_once'] = True
        student.evaluate("()=>{window.SpeechRecognition=class {start(){setTimeout(()=>this.onerror?.({error:'not-allowed'}),10);}abort(){}};}")
        enter('#voice')
        expect(student.locator('#text-dialog')).to_be_visible()
        expect(student.locator('#text-command')).to_be_focused()
        expect(student.locator('#interaction-result')).to_contain_text('실패')
        enter('#close-dialog')
        CHECKS['asr_failure_keeps_typed_fallback_and_real_failure'] = True

        # No question/request text may enter recent-command feedback or stored practice.
        responses = []
        def held(route):
            responses.append(1)
            route.fulfill(status=200, content_type='application/json', body=json.dumps({
                'title': '보류', 'safe_to_speak': False, 'confidence': .2,
                'response_text': 'DO_NOT_EXPOSE_HELD_ANSWER', 'action': 'answer',
            }))
        student.route('**/agent-turn', held)
        question = '강의 후반부 핵심의 의미를 비교해 주세요. PRIVATE_QUESTION'
        student.evaluate("async q=>{const{command}=await import('./app.js');await Promise.all([command(q),command(q)]);}", question)
        assert len(responses) == 1, responses
        expect(student.locator('#status')).to_contain_text('보류')
        expect(student.locator('#interaction-result')).to_contain_text('실패')
        assert 'DO_NOT_EXPOSE_HELD_ANSWER' not in student.locator('body').inner_text()
        assert 'PRIVATE_QUESTION' not in student.locator('#interaction-result').inner_text()
        storage = student.evaluate('async()=>chrome.storage.local.get(null)')
        progress = {key: value for key, value in storage.items() if key.startswith('practice:')}
        assert len(progress) == 1 and 'PRIVATE_QUESTION' not in json.dumps(progress)
        CHECKS['pending_question_dedup_and_held_response_privacy'] = True
        student.unroute('**/agent-turn', held)

        browser.student_control(student, '#access-mode').select_option('reader')
        expect(student.locator('#status')).to_contain_text('외부 스크린리더 모드입니다.')
        student.evaluate("()=>{window.__spoken=[];window.__statusMessages=[];}")
        assert command('현재 상태') is True and command('현재 상태') is True
        assert student.evaluate('window.__spoken.length') == 0
        assert student.evaluate('window.__statusMessages.length') == 2
        expect(student.locator('#voice-status')).to_be_empty()
        CHECKS['repeated_status_reader_mode_without_app_speech'] = True

        browser.check_layout(student, 'student-practice-complete', output)
        student.reload()
        expect(student.locator('#workspace')).to_be_visible()
        enter('#show-practice')
        expect(student.locator('#practice-steps')).to_contain_text('실습 완료')
        expect(student.locator('#interaction-result')).to_have_text('최근 명령이 없습니다.')
        CHECKS['account_scoped_practice_restored_recent_command_session_only'] = True
        browser.check_layout(student, 'student-practice-restored', output)
    assert uploads == []
    raise Complete()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        browser.main(exercise, phase='student-onboarding', output=args.output)
    except Complete:
        pass
    report = {'result': 'passed' if len(CHECKS) == 12 else 'failed', 'checks': CHECKS,
              'axe': browser.AXE_RESULTS,
              'boundary': 'Real installed extensions, keyboard, generated media and temporary API/DB. ASR and unsafe question response explicitly mocked. No paid model call or actual screen-reader audio evaluation.'}
    (args.output / 'student-onboarding-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    raise SystemExit(report['result'] != 'passed')
