"""Original-feature regressions in two installed extensions with real decoded video.

Speech/recognition/provider are explicit test doubles. No live microphone or paid API.
Historical gap audit files are preserved separately.
"""
from verify_extensions_browser import student_control, student_role, student_text
import json
import os
from unittest.mock import patch
from playwright.sync_api import expect
from verify_extensions_browser import main, check_layout
from verify_extensions_phase3 import exercise as phase3, SPEECH
from verify_extensions_phase4 import exercise as phase4
import verify_student_repair as repair


def wait_paused(page, paused=True):
    try:page.wait_for_function('(paused)=>document.querySelector("#local-video").paused===paused', arg=paused,timeout=5000)
    except Exception:
        print(page.evaluate("()=>({paused:document.querySelector('#local-video').paused,time:document.querySelector('#local-video').currentTime,focus:document.activeElement.id,status:document.querySelector('#status').textContent,spoken:window.__spoken.slice(-3).map(x=>x.text)})"),flush=True)
        raise


def media_checks(guardian, student, output):
    student.evaluate("""()=>{const Original=window.AudioContext;window.__readyCues=0;window.AudioContext=class extends Original{constructor(){super();window.__readyCues++;}};}""")
    repair.media_checks(guardian, student, output)
    assert student.evaluate('window.__readyCues')==1
    student_control(student, '#voice-consent').check()
    for activation in ('click','Enter'):
        count=student.evaluate('window.__voiceStarted')
        if activation=='click':student_control(student, '#voice').click()
        else:student_control(student, '#voice').focus();student.keyboard.press('Enter')
        student.wait_for_function('(n)=>window.__voiceStarted===n+1',arg=count)
        if activation=='click':student_control(student, '#voice').click()
        else:student.keyboard.press('Enter')
        expect(student.locator('#status')).to_contain_text('모두 중지')
        assert student.evaluate('window.__voiceStarted')==count+1
    student_control(student, '#voice-consent').uncheck()
    student_control(student, '#access-mode').select_option('app')
    student.evaluate('window.__holdSpeech=true')
    student_control(student, '#play').click(); wait_paused(student,False)
    before=student.evaluate('window.__spoken.length')
    student_control(student, '#note').focus()
    student.wait_for_function('(n)=>window.__spoken.length>n',arg=before);wait_paused(student)
    student.evaluate('window.__spoken.at(-1).onend?.();window.__holdSpeech=false');wait_paused(student,False)
    student_control(student, '#access-mode').select_option('reader')
    student_control(student, '#play').click();wait_paused(student,False)
    student_control(student, '#note').focus();wait_paused(student)
    student.wait_for_timeout(250);wait_paused(student)
    student_control(student, '#access-mode').select_option('app')
    student_control(student, '#speak-answer').uncheck()
    student.evaluate('window.__spoken=[]')
    answer=student.evaluate("""async()=>{const{command}=await import('./app.js');await command('합의 원리의 학습 계획을 만들어 주세요.');return document.querySelector('#chat-log article:last-child p:last-child').textContent;}""")
    speeches=student.evaluate('window.__spoken.map(u=>u.text)')
    assert not any(len(s)>15 and ' '.join(answer.split()).startswith(' '.join(s.split())) for s in speeches)
    student_control(student, '#speak-answer').check()
    student_control(student, '#stop').click();student_control(student, '#bookmark').focus()
    repair.taps(student,1);student.keyboard.press('Tab');student.wait_for_timeout(600);wait_paused(student)
    # Both button entry and triple-Space cancellation restore the original playback intent.
    for mode in ('button','triple'):
        print('Checking cancel resume:',mode,flush=True)
        student.evaluate('document.querySelector("#local-video").currentTime=0')
        student_control(student, '#play').click();wait_paused(student,False)
        if mode=='button':student_control(student, '#type-command').click()
        else:
            student_control(student, '#bookmark').focus();repair.taps(student,3)
        expect(student.locator('#text-dialog')).to_be_visible()
        student.keyboard.press('Escape');expect(student.locator('#text-dialog')).to_be_hidden();wait_paused(student,False)
        student_control(student, '#stop').click()
    # Executing one dialog must not poison the next dialog's Cancel returnValue.
    student_control(student, '#type-command').click();student_control(student, '#text-command').fill('영상 중지');student.keyboard.press('Enter')
    expect(student.locator('#text-dialog')).to_be_hidden()
    student_control(student, '#play').click();wait_paused(student,False)
    student_control(student, '#type-command').click();student_control(student, '#close-dialog').click();wait_paused(student,False)
    student_control(student, '#stop').click()
    student_control(student, '#search-form [name=query]').fill('합의 원리');student_control(student, '#search-form button').click()
    student.evaluate('window.__spoken=[]')
    student_role(student, 'button',name='합의 원리 강사 구간 듣기',exact=True).click();wait_paused(student,False)
    student.evaluate('document.querySelector("#local-video").currentTime=7.8')
    student.wait_for_function("()=>document.querySelector('#current-description').textContent.includes('합의 원리.')",timeout=5000)
    wait_paused(student)
    student.evaluate("async()=>{const{command}=await import('./app.js');await command('원래 듣던 곳으로');}")
    expect(student.locator('#return-origin')).to_be_disabled()
    # Native editor spaces remain literal; only consecutive spaces during output stop.
    student_control(student, '#note').focus();student_control(student, '#note').fill('')
    student.evaluate('window.__holdSpeech=true')
    student_control(student, '#read').click();expect(student.locator('#current-description')).to_contain_text('문단')
    student_control(student, '#note').focus();student.keyboard.press('Space');student.keyboard.press('a');student.keyboard.press('Space')
    expect(student.locator('#note')).to_have_value(' a ')
    student.keyboard.press('Space');expect(student.locator('#status')).to_contain_text('모두 중지')
    student.evaluate('window.__holdSpeech=false')
    summary=student_text(student, '음성·해설·키보드 설정',exact=True)
    summary.focus();student.keyboard.press('Enter');student.wait_for_function("()=>window.__spoken.some(u=>u.text.includes('접힘'))")
    student.keyboard.press('Enter');student.wait_for_function("()=>window.__spoken.some(u=>u.text.includes('펼쳐짐'))")
    student.evaluate('document.querySelector("#local-video").currentTime=0')
    student_control(student, '#play').click();wait_paused(student,False);student_control(student, '#preview-voice').click()
    expect(student.locator('#preview-voice')).not_to_have_attribute('aria-busy','true');wait_paused(student,False)
    student_control(student, '#stop').click()
    student_control(student, '#paragraph-selection').select_option(index=0)
    student_control(student, '#selected-underline').click()
    student.wait_for_function("()=>window.__spoken.some(u=>u.text.includes('선택됨'))")
    student_control(student, '#selected-underline').click()
    # An explicit Stop must win while an earlier Play is still awaiting its pause acknowledgement.
    student.evaluate("""async()=>{const{StudentMedia}=await import('./media.js');window.__pause=StudentMedia.prototype.pause;
      StudentMedia.prototype.pause=async function(invalidate=true){await window.__pause.call(this,invalidate);if(invalidate)await new Promise(r=>setTimeout(r,200));};}""")
    student_control(student, '#play').click();student_control(student, '#stop').click();student.wait_for_timeout(350);wait_paused(student)
    student.evaluate("async()=>{const{StudentMedia}=await import('./media.js');StudentMedia.prototype.pause=window.__pause;}")
    # Complete guardian preview uses the same original locally, without another media upload.
    file=student.locator('#local-file').evaluate("async e=>({name:e.files[0].name,mimeType:e.files[0].type,bytes:[...new Uint8Array(await e.files[0].arrayBuffer())]})")
    guardian.locator('#preview-file').set_input_files({'name':file['name'],'mimeType':file['mimeType'],'buffer':bytes(file['bytes'])})
    expect(guardian.locator('#preview-playback')).to_contain_text('분석한 원본과 일치')
    guardian.wait_for_function("()=>document.querySelector('#preview-video').textTracks[0]?.cues?.length>0")
    with guardian.expect_download() as download:guardian.locator('#preview-export').click()
    assert download.value.suggested_filename=='sullivan-prepared-notes.md'
    for title in ['강의 발화·자막','검증된 화면 설명','개념 탐색','복습 핵심 구간','화면에만 있는 정보','강조 문장','학습 가이드','설명 판단 근거']:
        expect(guardian.get_by_text(title,exact=True)).to_be_visible()
    from app.models import AgentTurnResponse
    async def preview_reply(*args,**kwargs):
        return AgentTurnResponse(action='answer',title='미리보기 답변',response_text='두 수를 함께 묶어 살펴봅니다.',decision_reason='시험 자료',confidence=.99)
    with patch.dict(os.environ,{'GEMINI_API_KEY':'fixture-key'}),patch('app.adapters.gemini_agent.run_agent_turn',preview_reply):
        guardian.locator('#preview-question-form [name=message]').fill('합의 원리를 설명해 주세요.')
        guardian.locator('#preview-question-form [name=analysis_consent]').check();guardian.locator('#preview-question-form button').click()
        expect(guardian.locator('#preview-answer')).to_contain_text('두 수를 함께 묶어')
    check_layout(guardian,'guardian-full-preview',output)
    check_layout(student,'student-restored-learning',output)
    student_control(student, '#stop').click()


def exercise(guardian,student,output):
    phase3.student_check=media_checks
    guardian=phase4(guardian,student,output)
    repair.native_panel(student)
    student_control(student, '#logout').click();expect(student.locator('#auth')).to_be_visible();student.evaluate(SPEECH)
    student_control(student, '#access-mode').select_option('app');student_control(student, '#access-mode').focus();student_control(student, '#username').focus()
    student.wait_for_function("()=>window.__spoken.some(u=>u.text.includes('로그인 이름'))")
    student_control(student, '#password').fill('never-read-this-password');student_control(student, '#password').focus()
    assert not student.evaluate("window.__spoken.some(u=>u.text.includes('never-read-this-password'))")
    student_control(student, '#username').fill('student');student_control(student, '#password').fill('extension-pass-123');student_control(student, '#login-form button').click()
    expect(student.locator('#workspace')).to_be_visible()
    student.reload();expect(student.locator('#workspace')).to_be_visible();expect(student.locator('#lesson')).to_be_hidden()
    student_control(student, '#workspace-title').focus();repair.taps(student,3)
    expect(student.locator('#text-dialog')).to_be_visible()
    student_control(student, '#text-command').fill('사용법 알려줘');student.keyboard.press('Enter')
    expect(student.locator('#onboarding-card')).to_be_visible();expect(student.locator('#voice')).to_be_visible()
    student_control(student, '#onboarding-done').click();expect(student.locator('#onboarding-card')).to_be_hidden()
    assert student.evaluate("async()=>{const{request}=await import('./client.js');return (await request('/local/me')).onboarded;}")
    # Guardian reset is consumed on the next student login, including reader mode notice.
    guardian.locator('#manage-student').select_option(label='학생 하나');guardian.locator('#load-management').click()
    expect(guardian.locator('#management-detail')).to_be_visible()
    guardian.locator('#settings-form [name=reset_onboarding]').check();guardian.locator('#settings-form button').click()
    expect(guardian.locator('#status')).to_contain_text('학생 기본 설정을 저장')
    student.reload();expect(student.locator('#onboarding-card')).to_be_visible()
    expect(student.locator('#voice-status')).to_contain_text('처음 사용 안내')
    # Delete a disposable lecture, preserving the base family's lecture/progress.
    guardian.get_by_role('button',name='동기화 테스트 강의 배정 수정',exact=True).click()
    guardian.locator('#delete-lecture').click();expect(guardian.locator('#delete-question')).to_contain_text('학습 기록도 삭제')
    guardian.locator('#delete-no').click();expect(guardian.locator('#delete-confirm')).to_be_hidden()
    guardian.locator('#delete-lecture').click();guardian.locator('#delete-yes').click()
    expect(guardian.locator('#status')).to_contain_text('삭제했습니다')
    expect(guardian.get_by_role('button',name='동기화 테스트 강의 배정 수정',exact=True)).to_have_count(0)
    # Guided form validates step 1, then exposes source and final summary separately.
    guardian.locator('#prepare-guided').click();guardian.locator('#prepare-form [name=title]').fill('')
    guardian.locator('#prepare-next').click();expect(guardian.locator('#prepare-form [name=title]')).to_be_focused()
    guardian.locator('#prepare-form [name=title]').fill('단계 안내 검증');guardian.locator('#prepare-next').click()
    expect(guardian.locator('#prepare-step')).to_contain_text('2/3')
    # Back to choose materials, then finish all three steps with a truthful summary.
    guardian.locator('#prepare-back').click();guardian.locator('#prepare-source').select_option('materials');guardian.locator('#prepare-next').click()
    guardian.locator('#prepare-form [name=passage]').fill('단계 확인에 사용하는 학습 지문입니다.');guardian.locator('#prepare-next').click()
    expect(guardian.locator('#prepare-step')).to_contain_text('3/3');expect(guardian.locator('#prepare-summary')).to_contain_text('단계 안내 검증')
    expect(guardian.locator('#prepare-form button[type=submit]')).to_be_visible()
    guardian.locator('#prepare-back').click();guardian.locator('#prepare-back').click();expect(guardian.locator('#prepare-step')).to_contain_text('1/3')
    guardian.locator('#prepare-guided').click()
    check_layout(student,'student-home-help',output)
    return guardian


exercise.checks=phase4.checks+repair.exercise.checks+[
    'focus TTS pauses real video then resumes; reader focus pauses without resume',
    'answer mute independent of focus voice; pending Space cancelled by Tab',
    'button/triple-Space text cancel resume; execute-then-cancel reset',
    'bounded concept playback then AI explanation; original-place command',
    'native input emergency double stop and interrupted sequence',
    'guardian full preview and SHA-verified local captions',
    'home typed help and onboarding completion/reset',
    'confirmed guardian deletion; three-step form validation',
    'explicit Stop wins against delayed Play acknowledgement',
    'guardian preview question consent and rendered provider result (provider stub)',
    'recognizer readiness schedules WebAudio cue; disclosure/pressed guidance',
    'natural voice/style preview resumes previously playing lecture',
    'voice command button finishes transcript by mouse or Enter without restarting recognition',
]
if __name__=='__main__':main(exercise,phase='feature-restoration')
