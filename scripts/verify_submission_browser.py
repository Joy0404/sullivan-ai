"""Installed Chrome extensions: key-free sample, partial HOLD and provenance UI.

Native TTS engine signals are recorded separately from controlled narration
delivery. No fixture response is represented as a real Gemini analysis.
"""
from verify_extensions_browser import student_disclosure, student_control, student_text
import argparse
import json
import os
from pathlib import Path
from unittest.mock import patch

from playwright.sync_api import expect,TimeoutError as PlaywrightTimeout
import verify_extensions_browser as browser
from verify_reaudit_fixes import Complete
from verify_extensions_phase3 import SPEECH

checks={};native_tts={}
def record(name,observed):
    checks[name]={'passed':True,'observed':observed};print(name,'PASS',flush=True)


def exercise(guardian,student,output):
    student_control(student, '#access-mode').select_option('app')
    student.evaluate('''()=>{
      window.__nativeSynth=window.speechSynthesis;window.__nativeUtterance=window.SpeechSynthesisUtterance;
      window.__nativeProbe={voices:speechSynthesis.getVoices().length,starts:0,ends:0,errors:[]};
      const speak=speechSynthesis.speak.bind(speechSynthesis);window.__nativeSpeak=speak;
      speechSynthesis.speak=u=>{const start=u.onstart,end=u.onend,error=u.onerror;
        u.onstart=e=>{window.__nativeProbe.starts++;start?.(e);};u.onend=e=>{window.__nativeProbe.ends++;end?.(e);};
        u.onerror=e=>{window.__nativeProbe.errors.push(e.error);error?.(e);};return speak(u);};
    }''')
    student_control(student, '#voice-test').click()
    try:student.wait_for_function('()=>window.__nativeProbe.ends>0',timeout=20000)
    except PlaywrightTimeout:pass
    native_tts.update(student.evaluate('window.__nativeProbe'))
    native_tts['verification']='native_start_and_end_observed' if native_tts['starts'] and native_tts['ends'] else 'not_verified'
    (output/'native-tts-probe.json').write_text(json.dumps(native_tts,ensure_ascii=False,indent=2)+'\n')
    student.evaluate('speechSynthesis.cancel()');student_control(student, '#access-mode').select_option('silent')
    student.evaluate(SPEECH)
    guardian.locator('#assign-form [name=sample]').select_option('accessibility')
    guardian.locator('#assign-submit').focus();guardian.keyboard.press('Enter')
    expect(guardian.locator('#lectures')).to_contain_text('사전 준비 샘플')
    student_control(student, '#refresh').click();student_control(student, '#lectures button').filter(has_text='판서 차이·부분 보류 시연 샘플 열기').click()
    expect(student.locator('#analysis-status')).to_have_text('영상 분석 상태: 사전 준비 샘플')
    expect(student.locator('#lesson-title')).to_be_focused()
    record('SUB01.key_free_assignment_and_sample_label','Guardian keyboard assignment, student opens server-labelled prepared sample')
    student_disclosure(student, '내 기기의 영상 연결·보관')
    video=Path(browser.ROOT)/'samples/accessibility-demo.mp4'
    student_control(student, '#local-file').set_input_files(str(video));student_control(student, '#video-muted').check()
    media_posts=[];student.on('request',lambda request:media_posts.append(request.url) if request.method=='POST' and 'multipart/form-data' in request.headers.get('content-type','') else None)
    student_control(student, '#connect-file').click();expect(student.locator('#connection')).to_contain_text('분석한 원본과 일치')
    record('SUB02.local_demo_decodes_without_upload',{'raw_media_posts':len(media_posts)})
    student_text(student, '음성·해설·키보드 설정',exact=True).click()
    student_control(student, '#preferences-form [name=reader_mode]').uncheck();student_control(student, '#preferences-form [name=auto_description]').check()
    student_control(student, '#preferences-form [name=focus_voice]').uncheck();student_control(student, '#preferences-form button[type=submit]').click()
    def begin(seconds):
        student_control(student, '#stop').click();student.evaluate('(seconds)=>{document.querySelector("#local-video").currentTime=seconds;window.__spoken=[];}',seconds)
        student.wait_for_timeout(350);student_control(student, '#play').click()
    begin(.2);student.wait_for_function('()=>document.querySelector("#local-video").currentTime>2.0')
    assert not student.evaluate('window.__spoken.some(u=>/2x|세로축|보류하겠/.test(u.text||u))')
    student_control(student, '#stop').click()
    record('SUB03.spoken_content_is_index_only','First scene advances without automatic formula narration')
    begin(6.0);expect(student.locator('#current-description')).to_contain_text('2x')
    assert '7' in student.locator('#current-description').inner_text()
    debug=student.evaluate('()=>({spoken:window.__spoken,mode:document.querySelector("#access-mode").value,readerChecked:document.querySelector("#preferences-form [name=reader_mode]").checked,readerText:document.querySelector("#reader-description").textContent,speechStatus:document.querySelector("#speech-status").textContent,error:document.querySelector("#error").textContent,engine:String(window.speechSynthesis.speak)})')
    (output/'speech-debug.json').write_text(json.dumps(debug,ensure_ascii=False,indent=2)+'\n')
    student.wait_for_function('()=>window.__spoken.map(u=>u.text||u).join("").includes("7")',timeout=6000)
    record('SUB04.numeric_difference_is_narrated','Current speech 8 does not conceal confirmed board 7')
    begin(12.0);expect(student.locator('#current-description')).to_contain_text('세로축의 단위')
    description=student.locator('#current-description').inner_text()
    assert '값이 증가' in description and description.count('설명을 보류하겠습니다')==1
    student.wait_for_function('()=>window.__spoken.map(u=>u.text||u).join("").includes("설명을 보류하겠습니다")',timeout=6000)
    assert student.evaluate('window.__spoken.map(u=>u.text||u).join("").split("설명을 보류하겠습니다").length-1')==1
    record('SUB05.partial_hold_in_same_narration',description)
    begin(18.0);expect(student.locator('#current-description')).to_contain_text('‘이 장면의 판서’ 부분은 확실치 않아서 설명을 보류하겠습니다.')
    record('SUB06.full_hold_notice_without_candidate',student.locator('#current-description').inner_text())
    def reopen_sample():
        student_control(student, '#stop').click()
        student_control(student, '#lectures button').filter(has_text='판서 차이·부분 보류 시연 샘플 열기').click()
        expect(student.locator('#lesson-title')).to_be_focused()
        student_disclosure(student, '내 기기의 영상 연결·보관')
        student_control(student, '#local-file').set_input_files(str(video));student_control(student, '#connect-file').click()
        expect(student.locator('#connection')).to_contain_text('분석한 원본과 일치')
    # Automatic narration is intentionally once per open lesson; reopen for each routing boundary.
    reopen_sample();student_control(student, '#access-mode').select_option('reader')
    begin(12.0);expect(student.locator('#reader-description')).to_contain_text('세로축의 단위')
    assert student.locator('#local-video').evaluate('v=>v.paused')
    assert student.evaluate('window.__spoken.length')==0
    assert student.locator('#current-description').get_attribute('role') is None
    assert student.locator('#reader-description').get_attribute('role')=='status'
    record('SUB07.reader_single_output_no_app_tts','Reader live region receives combined content once; native app utterances 0')
    browser.check_layout(student,'student-partial-hold-reader',output)
    reopen_sample();student_control(student, '#access-mode').select_option('silent')
    student.evaluate("()=>{speechSynthesis.speak=u=>{window.__spoken.push(u.text);u.onerror?.({error:'synthesis-failed'});};}")
    begin(12.0);expect(student.locator('#reader-description')).to_contain_text('앱 해설 음성을 재생하지 못했습니다')
    expect(student.locator('#connection')).to_contain_text('분석한 원본과 일치')
    assert student.locator('#local-video').evaluate('v=>v.paused')
    expect(student.locator('#reader-description')).to_contain_text('세로축의 단위')
    expect(student.locator('#error')).to_be_empty();expect(student.locator('#speech-status')).to_be_empty();expect(student.locator('#status')).to_be_empty()
    record('SUB08.tts_error_keeps_media_and_reading','TTS failure does not misreport lost video or discard readable notice')
    student.evaluate(SPEECH)
    # Material-only preparation remains not-run even when its source name says Gemini.
    form=guardian.locator('#prepare-form');guardian.locator('#prepare-source').select_option('materials')
    form.locator('[name=title]').fill('출처 이름과 상태 분리 검사')
    form.locator('[name=source_label]').fill('Gemini 분석 완료라고 쓴 사용자 출처')
    form.locator('[name=passage]').fill('직접 등록한 공개 지문입니다.');form.locator('button[type=submit]').click()
    expect(guardian.locator('#status')).to_contain_text('준비를 접수했습니다')
    guardian.locator('#refresh-preparations').click()
    held=[]
    def delayed(route):held.append((route,route.fetch().json()))
    guardian.route('**/guardian/preparations/*',delayed)
    guardian.get_by_role('button',name='출처 이름과 상태 분리 검사 결과 확인·배정',exact=True).click()
    guardian.wait_for_timeout(100);assert held
    guardian.locator('#preparation-search').fill('출처 이름')
    held[0][0].fulfill(status=200,content_type='application/json',body=json.dumps(held[0][1],ensure_ascii=False))
    expect(guardian.locator('#prepared-title')).to_have_text('출처 이름과 상태 분리 검사 준비 결과')
    expect(guardian.locator('#prepared-analysis-status')).to_have_text('영상 분석 상태: 영상 분석 미실행')
    expect(guardian.locator('#preparation-search')).to_be_focused()
    expect(guardian.locator('#status')).to_contain_text('영상 분석 미실행')
    guardian.unroute('**/guardian/preparations/*')
    record('SUB09.source_name_not_status_and_async_focus','Material source may mention Gemini; server label not-run, new search focus retained')
    browser.check_layout(guardian,'guardian-analysis-status',output)
    assert not media_posts
    raise Complete()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    configured=bool(os.getenv('GEMINI_API_KEY','').strip())
    with patch.dict(os.environ,{'GEMINI_API_KEY':'','LINK_ANALYZER_URL':''}):
        try:browser.main(exercise,phase='submission',output=args.output)
        except Complete:pass
    report={'result':'passed' if len(checks)==9 else 'failed','checks':checks,'axe':browser.AXE_RESULTS,'native_tts_probe':native_tts,
      'real_gemini_analysis':{'executed':False,'configured_in_process':configured,'reason':'Key-free prepared sample verification; no Gemini response is represented as live analysis.'},
      'boundary':'Real installed extension/API/DB/decoded self-authored media. Narration text/reader routing and injected synthesis failure use controlled speech boundaries; native engine probe is separate. Human hearing and real screen-reader output unverified.'}
    (args.output/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(report['result']!='passed')
