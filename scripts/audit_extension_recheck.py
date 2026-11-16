"""Independent audit probes; record failures without changing product code or user data.

Uses installed extensions, real decoded fixture media, disposable accounts and explicit
speech/network/permission boundary doubles. A completed audit is not a passing product.
"""
from verify_extensions_browser import student_control
import json
from pathlib import Path
from playwright.sync_api import expect
from verify_extensions_browser import main, check_layout
from verify_extensions_phase3 import exercise as phase3

OUT=Path(__file__).resolve().parents[1]/'docs/verification/2026-11-13-full-reaudit/supplement'
OBS=[]


def record(ident, expected, observed, passed, ids, detail=''):
    OBS.append(dict(id=ident,features=ids,expected=expected,observed=observed,
        result='passed' if passed else 'failed',detail=detail))
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'observations.json').write_text(json.dumps(OBS,ensure_ascii=False,indent=2)+'\n')
    print(ident,OBS[-1]['result'],flush=True)


def attempt(ident, operation, ids):
    try:operation()
    except Exception as error:
        OBS.append(dict(id=ident,features=ids,result='inconclusive',error=str(error)[:1800]))
        (OUT/'observations.json').write_text(json.dumps(OBS,ensure_ascii=False,indent=2)+'\n')
        print(ident,'inconclusive',str(error)[:200],flush=True)


def paused(student,value=True):
    student.wait_for_function('(v)=>document.querySelector("#local-video").paused===v',arg=value,timeout=5000)


def reset(student):
    student.evaluate("""async()=>{
      window.__releaseAuditPlay?.();window.__releaseAuditPlay=null;window.__holdSpeech=false;
      const{StudentMedia}=await import('./media.js');if(window.__auditSend){StudentMedia.prototype.send=window.__auditSend;window.__auditSend=null;}
    }""")
    student_control(student, '#space-enabled').check()
    student_control(student, '#stop').click();paused(student)
    student.evaluate('document.querySelector("#local-video").currentTime=0')


def media_probes(guardian,student,output):
    def play_focus_race():
        student_control(student, '#access-mode').select_option('app');reset(student)
        student.evaluate("""async()=>{
          const{StudentMedia}=await import('./media.js');window.__auditSend=StudentMedia.prototype.send;
          StudentMedia.prototype.send=async function(action,...args){const value=await window.__auditSend.call(this,action,...args);
            if(action==='play')return new Promise(resolve=>window.__releaseAuditPlay=()=>resolve(value));return value;};
          window.__holdSpeech=true;window.__spoken=[];
        }""")
        student_control(student, '#play').click();student.wait_for_function('()=>Boolean(window.__releaseAuditPlay)')
        student_control(student, '#note').focus();student.wait_for_function("()=>window.__spoken.some(u=>u.text.includes('내 메모'))")
        before=student.locator('#local-video').evaluate('v=>v.paused')
        student.evaluate('window.__releaseAuditPlay()');student.wait_for_timeout(200)
        observed={'before_release_paused':before,'after_release_paused':student.locator('#local-video').evaluate('v=>v.paused'),'guidance_held':student.evaluate('window.__holdSpeech')}
        record('pending_play_then_focus','새 초점 안내가 끝날 때까지 영상 정지',observed,observed['after_release_paused'],['F35','F41'], '지연된 worker play 응답만 제어. 영상은 실제 MP4, 음성은 종료를 보류한 시험 장치.')
        student.screenshot(path=str(output/'pending-play-focus.png'),full_page=True)
        reset(student)
    attempt('pending_play_then_focus',play_focus_race,['F35','F41'])
    reset(student)

    def voice_test_resume():
        student_control(student, '#access-mode').select_option('app');student_control(student, '#play').click();paused(student,False)
        student.evaluate('window.__holdSpeech=true;window.__spoken=[]')
        student_control(student, '#voice-test').focus();student.wait_for_function("()=>window.__spoken.some(u=>u.text.includes('음성 안내 시작'))")
        student.evaluate('window.__holdSpeech=false');student_control(student, '#voice-test').click();student.wait_for_timeout(2300)
        observed={'paused_after_test':student.locator('#local-video').evaluate('v=>v.paused'),'texts':student.evaluate('window.__spoken.map(u=>u.text)')}
        record('voice_test_resume','재생 중 시작한 음성 시험이 끝나면 기존 재생 복원',observed,not observed['paused_after_test'],['F41','F57'])
    attempt('voice_test_resume',voice_test_resume,['F41','F57']);reset(student)

    def modified_arrow():
        student_control(student, '#access-mode').select_option('silent')
        student.evaluate('document.querySelector("#local-video").currentTime=2');student.wait_for_timeout(600)
        student_control(student, '#bookmark').focus();before=student.locator('#local-video').evaluate('v=>v.currentTime')
        student.keyboard.press('Shift+ArrowRight');student.wait_for_timeout(300)
        after=student.locator('#local-video').evaluate('v=>v.currentTime')
        record('shift_arrow','수정키 조합은 강의 10초 이동을 실행하지 않음',{'before':before,'after':after},abs(before-after)<.1,['F35','F68'])
    attempt('shift_arrow',modified_arrow,['F35','F68']);reset(student)

    def disabled_space():
        student_control(student, '#access-mode').select_option('app');student_control(student, '#space-enabled').uncheck()
        student.evaluate('window.__holdSpeech=true');student_control(student, '#read').click()
        expect(student.locator('#current-description')).to_contain_text('문단')
        student_control(student, '#note').focus();student.evaluate('document.querySelector("#status").textContent=""')
        student.keyboard.press('Space');student.keyboard.press('Space');student.wait_for_timeout(150)
        observed={'space_enabled':student.locator('#space-enabled').is_checked(),'status':student.locator('#status').inner_text()}
        record('disabled_space_editor','Space 명령 사용을 끄면 편집 중 제스처도 실행하지 않음',observed,'모두 중지' not in observed['status'],['F65','F69'])
    attempt('disabled_space_editor',disabled_space,['F65','F69']);reset(student)

    def stale_command():
        student_control(student, '#type-command').click();student_control(student, '#text-command').fill('영상 중지');student.keyboard.press('Enter')
        expect(student.locator('#text-dialog')).to_be_hidden()
        student_control(student, '#type-command').click();value=student.locator('#text-command').input_value()
        record('stale_command','새 명령창은 이전 실행 명령을 지운 빈 입력으로 시작',value,value=='',['F67'])
        student.keyboard.press('Escape')
    attempt('stale_command',stale_command,['F67']);reset(student)

    def number_guidance():
        student_control(student, '#access-mode').select_option('app');student.evaluate('window.__spoken=[]')
        student_control(student, '#video-volume').focus();student_control(student, '#video-volume').fill('0.4')
        student.locator('#video-volume').dispatch_event('change');student.wait_for_timeout(350)
        texts=student.evaluate('window.__spoken.map(u=>u.text)')
        record('numeric_value_guidance','앱 안내에 현재 변경한 영상 음량 0.4 포함',texts,any('0.4' in t or '0점4' in t for t in texts),['F57','F58'])
        student_control(student, '#video-volume').fill('0.9');student.locator('#video-volume').dispatch_event('change')
    attempt('numeric_value_guidance',number_guidance,['F57','F58']);reset(student)

    def failed_save_retry():
        student_control(student, '#access-mode').select_option('reader')
        student.route('**/local/lectures/*/progress',lambda route:route.fulfill(status=503,content_type='application/json',body='{"detail":"감사 시험: 저장 실패"}'))
        student_control(student, '#note').fill('재검사 저장 실패 후 재시도')
        expect(student.locator('#save-status')).to_contain_text('아직 저장하지 못했습니다',timeout=4000)
        failure=student.locator('#save-status').inner_text();student.unroute('**/local/lectures/*/progress')
        student_control(student, '#progress-form button').click();expect(student.locator('#status')).to_have_text('학습 위치와 메모를 저장했습니다.')
        stored=student.evaluate("""async()=>{const{request}=await import('./client.js');const list=await request('/local/lectures');const l=list.find(l=>l.title==='동기화 테스트 강의');return(await request('/extension/v1/student/lectures/'+l.id)).progress.note;}""")
        record('save_failure_retry','실패 표시 후 수동 재시도에서 메모 실제 저장',{'failure':failure,'stored':stored},stored=='재검사 저장 실패 후 재시도',['F54','F56'])
    attempt('save_failure_retry',failed_save_retry,['F54','F56'])
    student.unroute('**/local/lectures/*/progress')

    def offline_reconnect():
        student.context.set_offline(True);student_control(student, '#note').fill('재검사 오프라인 메모')
        try:expect(student.locator('#save-status')).to_contain_text('아직 저장하지 못했습니다',timeout=4000)
        finally:student.context.set_offline(False)
        failure=student.locator('#save-status').inner_text();student_control(student, '#progress-form button').click()
        expect(student.locator('#status')).to_have_text('학습 위치와 메모를 저장했습니다.')
        stored=student.evaluate("""async()=>{const{request}=await import('./client.js');const l=(await request('/local/lectures')).find(l=>l.title==='동기화 테스트 강의');return(await request('/extension/v1/student/lectures/'+l.id)).progress.note;}""")
        record('offline_reconnect','오프라인 실패 표시와 연결 후 저장 재시도',{'failure':failure,'after':student.locator('#status').inner_text(),'stored':stored},stored=='재검사 오프라인 메모',['F56'])
    attempt('offline_reconnect',offline_reconnect,['F56'])
    student.context.set_offline(False)

    student_control(student, '#access-mode').select_option('reader')
    for query,terms in [('1문단',['1문단','합의 원리']),('다음 문단',['2문단','두 수']),('이전 문단',['1문단']),('전체 지문',['1문단','2문단']),('지문 흐름',['흐름']),('1문단 1문장',['합의 원리']),('다음 문장',['두 수'])]:
        def passage(query=query,terms=terms):
            student.evaluate('document.querySelector("#reader-description").textContent=""')
            student_control(student, '#paragraph-form [name=query]').fill(query);student_control(student, '#paragraph-form button').click()
            expect(student.locator('#reader-description')).not_to_be_empty();text=student.locator('#reader-description').inner_text()
            record('passage_'+query,terms,text,all(term in text for term in terms),['F43'])
        attempt('passage_'+query,passage,['F43'])
    # Preserve the eleven original cases under the approved notebook scope:
    # one short summary remains, ten generation requests must now be rejected.
    for label in ['3줄 요약','핵심 용어 카드','두 개념 비교','원인 전개 결과','시간순 흐름','암기표','복습 계획','퀴즈','1분 발표문','3분 발표문','개념 지도 생성']:
        def learning(label=label):
            before=student.locator('#chat-log article').count()
            student.evaluate("async label=>await(await import('./app.js')).command(label)",label)
            if label=='3줄 요약':
                body=student.locator('#reader-description').inner_text()
                passed=bool(body.strip())
            else:
                body=student.locator('#status').inner_text()
                passed='자동 학습 도구 생성은 제공하지 않습니다' in body and student.locator('#chat-log article').count()==before
            record('tool_'+label,'짧은 요약 유지 또는 제거된 생성 요청 차단',{'text':body[:600]},passed,['F51'],'2026-11-16 승인 범위. 실제 모델 품질 검증은 아님.')
        attempt('tool_'+label,learning,['F51'])
    student_control(student, '#access-mode').select_option('app');reset(student)


def exercise(guardian,student,output):
    phase3.student_check=media_probes
    guardian=phase3(guardian,student,output)
    expect(student.locator('#lesson')).to_be_hidden()
    result=student.evaluate("""async()=>{const{command}=await import('./app.js');try{await command('배정된 강의 새로고침 버튼 눌러');return{ok:true};}catch(error){return{ok:false,error:error.message};}}""")
    record('home_button_command','강의 선택 전 표시된 홈 버튼 명령 실행',result,result['ok'],['F66'])
    student_control(student, '#type-command').click();student.locator('#text-command').fill('1번 강의 열어줘');student.locator('#dialog-form button[type=submit]').click()
    expect(student.locator('#lesson')).to_be_visible()
    record('home_open_numbered','홈 타자 명령으로 1번 강의 열기',student.locator('#lesson-title').inner_text(),True,['F66'])
    student_control(student, '#access-mode').select_option('reader')
    student_control(student, '#read-review').click();expect(student.locator('#reader-description')).not_to_be_empty()
    record('read_review_without_video','영상 미연결 상태에서 복습 읽기',student.locator('#reader-description').inner_text()[:500],True,['F52'])
    student.evaluate("async()=>await(await import('./app.js')).command('학습 가이드 전체 듣기')")
    expect(student.locator('#status')).to_contain_text('자동 학습 도구 생성은 제공하지 않습니다')
    record('removed_guide_rejected','제거된 학습 가이드 전체 듣기 차단',student.locator('#status').inner_text(),True,['F51'])
    student_control(student, '#access-mode').select_option('app')
    check_layout(student,'supplement-student-no-video',output)
    return guardian


exercise.checks=['independent targeted probes are recorded in observations.json; inspect their individual verdicts']
if __name__=='__main__':
    main(exercise,phase='full-supplement',output=OUT)
    report={'audit_completed':True,'result':'failed' if any(o['result']=='failed' for o in OBS) else 'incomplete' if any(o['result']=='inconclusive' for o in OBS) else 'passed',
        'observations':len(OBS),'passed':sum(o['result']=='passed' for o in OBS),'failed':sum(o['result']=='failed' for o in OBS),'inconclusive':sum(o['result']=='inconclusive' for o in OBS),
        'limitations':['Speech and delayed transport/permissions are explicit test boundaries. Real video and Chrome extension documents used; no actual OS screen reader or live provider.']}
    harness_path=OUT/'extension-full-supplement-results.json'
    harness=json.loads(harness_path.read_text());harness['baseline_regression_result']=harness.pop('result')
    harness['result']='completed-with-failures' if report['failed'] else report['result']
    harness['audit_results']='audit-results.json';harness['individual_observations']='observations.json'
    harness_path.write_text(json.dumps(harness,ensure_ascii=False,indent=2)+'\n')
    (OUT/'audit-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False),flush=True)
