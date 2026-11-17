"""Installed-extension question/control regressions with explicit ASR/HTTP doubles."""
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
    browser.student_control(student, '#speak-answer').uncheck()
    requests, deferred, uploads = [], [], []
    mode = {'value': 'answer'}
    student.on('request', lambda r: uploads.append(r.url) if r.method == 'POST' and 'multipart/form-data' in r.headers.get('content-type', '') else None)

    def response(route, text='검사 응답입니다.', safe=True):
        route.fulfill(status=200, content_type='application/json', body=json.dumps({
            'title': '검사 응답', 'response_text': text, 'safe_to_speak': safe,
            'confidence': .99 if safe else .2, 'action': 'answer',
        }))

    def route_question(route):
        requests.append(route.request.post_data_json)
        if mode['value'] == 'pending':
            deferred.append(route)
        elif mode['value'] == 'hold':
            response(route, 'HELD_ANSWER_MUST_NOT_APPEAR', False)
        else:
            response(route)

    student.route('**/agent-turn', route_question)

    def command(text):
        return student.evaluate("async text=>(await import('./app.js')).command(text)", text)

    def enter(selector):
        target = browser.student_control(student, selector)
        target.focus();student.keyboard.press('Enter')

    question = '강의 재생 중에 나온 주계열성 개념은 무슨 뜻이야?'
    for text in (question, '영상이 멈췄을 때 관성은 어떻게 작용해?', '핵융합이 멈추는 과정을 설명해줘', '강의 재생 중 x < 7과 x ≤ 7의 차이가 뭐야?'):
        before = len(requests)
        assert command(text) is True
        assert len(requests) == before + 1 and requests[-1]['message'] == text
    expect(student.locator('#interaction-result')).to_have_text('강의 질문: 완료.')
    CHECKS['question_without_connected_video_uses_question_endpoint'] = True

    with tempfile.TemporaryDirectory(prefix='sullivan-routing-media-') as temporary:
        fixture = Path(temporary) / 'lecture.mp4';video_fixture(fixture)
        browser.student_control(student, '#local-file').set_input_files(fixture)
        browser.student_control(student, '#video-muted').check();enter('#connect-file')
        expect(student.locator('#connection')).to_contain_text('로컬 영상')
        student.evaluate("document.querySelector('#local-video').currentTime=0")
        before = len(requests)
        assert command(question) is True
        assert len(requests) == before + 1 and requests[-1]['message'] == question
        assert student.evaluate("document.querySelector('#local-video').paused")
        CHECKS['play_word_in_question_does_not_start_video'] = True

        assert command('영상 재생해 줄래?') is True
        student.wait_for_function("()=>!document.querySelector('#local-video').paused")
        before = len(requests)
        stop_question = '핵융합이 멈추면 별은 어떻게 변해?'
        assert command(stop_question) is True
        assert len(requests) == before + 1 and requests[-1]['message'] == stop_question
        assert not student.evaluate("document.querySelector('#local-video').paused")
        CHECKS['stop_word_in_question_does_not_stop_video'] = True

        before = len(requests)
        assert command('영상 좀 중지해 주세요') is True
        assert student.evaluate("document.querySelector('#local-video').paused")
        assert len(requests) == before
        assert command('영상 재생 같은 거') is False
        assert command('재생 좀') is False
        assert command('1.0초 뒤로') is False
        expect(student.locator('#status')).to_contain_text('조작 명령이 분명하지 않습니다')
        assert command('왜 재생이 안돼?') is True
        expect(student.locator('#onboarding-title')).to_be_focused()
        assert student.evaluate("document.querySelector('#local-video').paused") and len(requests) == before
        CHECKS['clear_stop_and_ambiguous_control_help_stay_local'] = True

        # Execute through the real text dialog, rather than only its shared handler.
        enter('#type-command');expect(student.locator('#text-command')).to_be_focused()
        student.locator('#text-command').fill(stop_question)
        before = len(requests);student.keyboard.press('Enter')
        expect(student.locator('#text-dialog')).not_to_be_visible()
        expect(student.locator('#interaction-result')).to_have_text('강의 질문: 완료.')
        assert len(requests) == before + 1 and requests[-1]['message'] == stop_question
        assert student.evaluate("document.querySelector('#local-video').paused")
        CHECKS['typed_dialog_preserves_question_text_and_paused_state'] = True

        browser.student_control(student, '#access-mode').select_option('reader')
        expect(student.locator('#status')).to_contain_text('외부 스크린리더 모드입니다.')
        student.evaluate("""()=>{
          window.__spoken=[];
          document.querySelector('#voice-consent').checked=true;
          window.SpeechRecognition=class {start(){this.onstart?.();}abort(){}stop(){
            this.onresult?.({results:[[{transcript:'핵융합이 멈추면 별은 어떻게 변해?'}]]});
            const end=this.onend;end?.();end?.();
          }};
        }""")
        before = len(requests);enter('#voice');enter('#voice')
        expect(student.locator('#interaction-result')).to_have_text('강의 질문: 완료.')
        assert len(requests) == before + 1 and requests[-1]['message'] == stop_question
        assert student.evaluate('window.__spoken.length') == 0
        assert student.evaluate("document.querySelector('#local-video').paused")
        CHECKS['asr_final_question_once_without_reader_mode_app_tts'] = True

        mode['value'] = 'hold'
        assert command(stop_question) is False
        expect(student.locator('#status')).to_contain_text('보류')
        assert 'HELD_ANSWER_MUST_NOT_APPEAR' not in student.locator('body').inner_text()
        assert '핵융합' not in student.locator('#interaction-result').inner_text()
        CHECKS['question_routing_preserves_hold_and_feedback_privacy'] = True

        mode['value'] = 'pending'
        count = student.locator('#chat-log article').count()
        with student.expect_request('**/agent-turn'):
            student.evaluate("""()=>{
              window.__routingFinished=false;
              import('./app.js').then(({command})=>command('강의 재생 중 판서의 원리를 설명해줘'))
                .finally(()=>window.__routingFinished=true);
            }""")
        student.wait_for_timeout(100);assert len(deferred) == 1
        enter('#stop');response(deferred[0], 'STALE_RESPONSE_MUST_NOT_APPEAR')
        student.wait_for_function('()=>window.__routingFinished')
        assert student.locator('#chat-log article').count() == count
        assert 'STALE_RESPONSE_MUST_NOT_APPEAR' not in student.locator('body').inner_text()
        assert student.evaluate("document.querySelector('#local-video').paused")
        CHECKS['explicit_stop_fences_pending_learning_question'] = True
        browser.check_layout(student, 'student-question-routing', output)
    assert uploads == []
    CHECKS['no_raw_media_uploads'] = True
    raise Complete()


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args();args.output.mkdir(parents=True, exist_ok=True)
    try:
        browser.main(exercise, phase='student-command-routing', output=args.output)
    except Complete:
        pass
    report = {'result': 'passed' if len(CHECKS) == 9 else 'failed', 'checks': CHECKS,
              'axe': browser.AXE_RESULTS,
              'boundary': 'Actual installed extensions, keyboard/text dialog, generated video and temporary API/DB. ASR and model response explicitly mocked; no paid model or actual screen-reader audio verification.'}
    (args.output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    raise SystemExit(report['result'] != 'passed')
