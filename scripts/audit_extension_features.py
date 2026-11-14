"""Read-only product audit against the original manual, using disposable accounts/media.

Known parity failures are recorded as findings, never converted to passing tests.
No provider keys, live recognition, or user databases are used.
"""
import json
from pathlib import Path
from playwright.sync_api import expect
from verify_extensions_browser import main
import verify_student_repair as repair
from verify_extensions_phase3 import exercise as phase3
from verify_extensions_phase4 import exercise as phase4

ROOT=Path(__file__).resolve().parents[1]
OBS=[]


def record(ident,title,expected,observed,passed,detail='',level='browser'):
    OBS.append(dict(id=ident,title=title,expected=expected,observed=observed,
        result='passed' if passed else 'gap-reproduced',detail=detail,evidence_level=level))


def media_probes(guardian,student,output):
    student.locator('#access-mode').select_option('app')
    student.locator('#play').click()
    student.wait_for_function("() => !document.querySelector('#local-video').paused")
    before=student.evaluate('window.__spoken.length')
    student.locator('#note').focus()
    student.wait_for_function('(count)=>window.__spoken.length>count',arg=before)
    paused=student.evaluate("document.querySelector('#local-video').paused")
    record('focus_pause','앱 초점 음성 중 영상 정지',True,paused,paused,'음성 요청은 관찰됨. 영상은 실제 디코딩 MP4, TTS만 시험 장치.')
    student.locator('#stop').click()
    student.locator('#access-mode').select_option('reader')
    student.locator('#play').click();student.wait_for_function("() => !document.querySelector('#local-video').paused")
    student.locator('#note').focus();student.wait_for_timeout(300)
    paused=student.evaluate("document.querySelector('#local-video').paused")
    record('reader_pause','외부 스크린리더 모드 초점 이동 시 영상 정지',True,paused,paused,'외부 스크린리더의 실제 낭독이 아닌 모드·영상 상태 검사.')
    student.locator('#stop').click()
    # Inspect independent answer mute against app focus guidance.
    student.locator('#access-mode').select_option('app')
    student.locator('#speak-answer').uncheck()
    before=student.evaluate('window.__spoken.length')
    response=student.evaluate("""async()=>{const {command}=await import('./app.js');await command('합의 원리의 학습 계획을 만들어 주세요.');return document.querySelector('#chat-log').innerText;}""")
    speeches=student.evaluate('(n)=>window.__spoken.slice(n).map(u=>u.text)',before)
    answer_text=student.locator('#chat-log article').last.locator('p').last.inner_text()
    normalized=' '.join(answer_text.split())
    answer_speech=any(len(text)>10 and normalized.startswith(' '.join(text.split())) for text in speeches)
    record('answer_mute','답변 음성 체크 해제의 독립 적용',False,answer_speech,not answer_speech,'앱 초점 안내는 켜고 답변 음성만 끔. 준비 자료 기반 대체 답변 경로.')
    student.locator('#speak-answer').check()
    # Navigation should invalidate a pending Space sequence, as in the original.
    student.locator('#bookmark').focus();repair.taps(student,1);student.keyboard.press('Tab');student.wait_for_timeout(650)
    unexpected_play=student.evaluate("!document.querySelector('#local-video').paused")
    record('pending_space','Space 뒤 Tab 이동 시 지연 명령 취소',False,unexpected_play,not unexpected_play)
    student.locator('#stop').click()
    # Opening then cancelling typed entry originally restored prior playback.
    student.locator('#play').click();student.wait_for_function("() => !document.querySelector('#local-video').paused")
    student.locator('#type-command').click();expect(student.locator('#text-dialog')).to_be_visible()
    student.keyboard.press('Escape');student.wait_for_timeout(250)
    resumed=student.evaluate("!document.querySelector('#local-video').paused")
    record('cancel_resume','텍스트 명령 취소 후 이전 재생 복원',True,resumed,resumed,'최신 2회 중지는 별개. 아무 명령도 실행하지 않고 취소한 경우.')
    student.locator('#stop').click()
    student.locator('#access-mode').select_option('reader')
    # Exercise every original learning-tool choice through real extension controls.
    options=student.locator('#learning-tool option').all_text_contents()
    for name in options:
        before=student.locator('#chat-log article').count()
        student.locator('#learning-tool').select_option(label=name);student.locator('#run-tool').click()
        expect(student.locator('#chat-log article')).to_have_count(before+1)
        text=student.locator('#chat-log article').last.inner_text()
        title=student.locator('#chat-log article').last.locator('h5').inner_text()
        record('tool_'+str(options.index(name)+1),name,'비어 있지 않은 도구 결과',title,bool(text.strip()),'실제 제어·준비자료 기반 결과. 두 개념 미제공 시 비교는 추가 입력 안내. 모델 품질 검사가 아님.')
    for query in ['1문단','다음 문단','이전 문단','전체 지문','지문 흐름','1문단 1문장','다음 문장']:
        # Original whole-passage/flow actions are the dedicated paragraph form,
        # not the global chat router. Exercise the corresponding visible form.
        student.evaluate("() => {document.querySelector('#reader-description').textContent='';document.querySelector('#answer-status').textContent='';}")
        student.locator('#paragraph-form [name=query]').fill(query)
        student.locator('#paragraph-form button').click()
        expect(student.locator('#reader-description')).not_to_be_empty()
        result={'text':student.locator('#reader-description').inner_text()}
        expected={'1문단':['1문단','합의 원리'],'다음 문단':['2문단','두 수'],'이전 문단':['1문단'],
            '전체 지문':['1문단','2문단'],'지문 흐름':['흐름','2문단'],
            '1문단 1문장':['합의 원리'],'다음 문장':['두 수']}[query]
        okay=all(term in result.get('text','') for term in expected) and not result.get('error')
        record('passage_'+str(len(OBS)),query,expected,result,okay,'이전 출력 초기화 후 해당 문단·문장 내용까지 검사. OS 낭독 미검증.')
    student.locator('#access-mode').select_option('app')
    student.locator('#search-form [name=query]').fill('합의 원리');student.locator('#search-form button').click()
    expect(student.locator('#search-results')).not_to_be_empty()
    labels=student.locator('#search-results button').all_text_contents()
    record('concept_sequence','강사 구간 다음 AI 설명 자동 연결','구간 종료 뒤 자동 AI 설명',labels,False,
        '서로 독립된 설명 듣기 / 강사 구간 듣기 버튼. 코드에도 end_ms 구간 감시·연결 상태 기계 없음.','browser+source')
    student.locator('#back').focus();student.keyboard.press('ArrowRight')
    expect(student.locator('#status')).to_contain_text('위치로 이동')
    record('arrow_seek','방향키 10초 이동','위치 변경 안내',student.locator('#status').inner_text(),True)
    student.locator('#stop').click()


def exercise(guardian,student,output):
    phase3.student_check=media_probes
    guardian=phase4(guardian,student,output)
    repair.native_panel(student)
    # A new extension document represents the lecture-list/home state.
    student.reload();expect(student.locator('#workspace')).to_be_visible()
    expect(student.locator('#lesson')).to_be_hidden()
    student.locator('#workspace-title').focus();repair.taps(student,3);student.wait_for_timeout(600)
    opened=student.locator('#text-dialog').is_visible()
    record('home_text','홈에서 Space 세 번 텍스트 명령',True,opened,opened)
    result=student.evaluate("""async()=>{const{command}=await import('./app.js');try{await command('사용법 알려줘');return {help:document.querySelector('#reader-description').textContent};}catch(e){return {error:e.message};}}""")
    record('home_help','강의 선택 전 사용법 명령','사용법 안내',result,not result.get('error') and bool(result.get('help')))
    visible_voice=student.locator('#voice').is_visible()
    record('home_voice','홈의 음성 명령 시작 버튼',True,visible_voice,visible_voice)
    user=student.evaluate("async()=>{const{request}=await import('./client.js');return await request('/local/me');}")
    help_ui=student.locator('[id*=onboarding]').count()
    record('onboarding','최초 안내 및 보호자의 안내 다시 표시','사용법 안내 UI와 완료 처리',{'onboarded':user['onboarded'],'onboarding_controls':help_ui},help_ui>0,
        'reset_onboarding은 서버에 저장되지만 학생 확장은 onboarded를 소비하지 않음.','browser+source')
    delete_buttons=[name for name in guardian.get_by_role('button').all_text_contents() if '삭제' in name]
    record('guardian_delete','보호자 강의 삭제 UI','삭제 제어',delete_buttons,bool(delete_buttons),
        'DELETE API는 남아 있으나 확장에는 배정 회수만 있음.','browser+source')
    # Snapshot all observations even if the shared final regression later fails.
    path=ROOT/'docs/verification/extension-feature-audit-observations.json'
    path.write_text(json.dumps({'version':'0.4.1','basis':'original manual + original code + user updated key contract',
        'observations':OBS,'limitations':['Speech synthesis and recognition use test doubles; no real VoiceOver/NVDA or paid provider call',
        'Probes use temporary database and profile; no user data changed']},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'observations':len(OBS),'passed':sum(o['result']=='passed' for o in OBS),
        'gaps_reproduced':[o['id'] for o in OBS if o['result']!='passed']},ensure_ascii=False))
    return guardian


exercise.checks=phase4.checks+['native side-panel keyboard containment','manual-based learning tools and passage commands','functional parity probes recorded separately, including failures']
if __name__=='__main__':
    main(exercise,phase='feature-audit')
    path=ROOT/'docs/verification/extension-feature-audit-results.json'
    report=json.loads(path.read_text());report['regression_result']=report['result']
    report['result']='completed-with-parity-gaps'
    report['parity_probes']={'total':len(OBS),'passed':sum(o['result']=='passed' for o in OBS),
        'gaps':[o['id'] for o in OBS if o['result']=='gap-reproduced']}
    report['limitations']=['Actual native panel and decoded video; speech synthesis/recognition and providers use test doubles. Actual VoiceOver/NVDA, live microphone, Korean audio quality and real lecture sites not verified.']
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'audit_result':report['result'],'parity_probes':report['parity_probes']},ensure_ascii=False))
