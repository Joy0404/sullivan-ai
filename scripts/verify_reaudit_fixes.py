"""Regression checks for all R01–R18, in disposable installed-extension profiles.

Video decoding, API, DB and worker are real. Speech/recognition and delayed
transport/permissions are explicit test boundaries; no paid service or user DB.
"""
from verify_extensions_browser import student_disclosure, student_control, student_text
import argparse
from base64 import b64encode
import hashlib
import json
from pathlib import Path
import traceback

from playwright.sync_api import expect
from starlette.responses import HTMLResponse
from starlette.routing import Route
import audit_extension_recheck as audit
from build_extensions import ROOT, VERSION
import verify_extensions_browser as browser
from verify_extensions_phase3 import exercise as phase3, SPEECH

OUT=ROOT/'docs/verification/2026-11-14-fixes'
CHECKS={}
GROUPS=[]
EXTRA={}


class Complete(BaseException):
    pass


def checked(ident,passed,observed,strict=True):
    CHECKS[ident]={'result':'passed' if passed else 'failed','observed':observed}
    (OUT/'checks.json').write_text(json.dumps(CHECKS,ensure_ascii=False,indent=2)+'\n')
    if strict:assert passed,(ident,observed)
    print(ident,'PASS' if passed else 'FAIL',flush=True)


def request(page,path,method='GET',body=None):
    return page.evaluate("""async({path,method,body})=>{const{request}=await import('./client.js');return await request(path,{method,...(body===null?{}:{body})});}""",dict(path=path,method=method,body=body))


def open_lesson(page,ident):
    control=student_control(page,f'#lectures button[data-lecture="{ident}"]');title=control.inner_text().removesuffix(' 열기');control.click()
    # Reopening the same lecture can await an earlier progress save. Its old
    # visible title is not evidence that the requested open has completed.
    expect(control).not_to_have_attribute('aria-busy','true')
    expect(page.locator('#lesson')).to_be_visible()
    expect(page.locator('#lesson-title')).to_have_text(title)


def paused(page,value=True):
    page.wait_for_function('(v)=>document.querySelector("#local-video").paused===v',arg=value,timeout=5000)


def supplement(guardian,student,output):
    original=audit.phase3
    def prepare_home(g,s,o):
        phase3.student_check=audit.media_probes
        result=phase3(g,s,o)
        return result
    audit.phase3=prepare_home;audit.OUT=output;audit.OBS.clear()
    try:guardian=audit.exercise(guardian,student,output)
    finally:audit.phase3=original
    mapping={'pending_play_then_focus':'R03','voice_test_resume':'R05','shift_arrow':'R06',
        'disabled_space_editor':'R07','stale_command':'R08','numeric_value_guidance':'R09','home_button_command':'R10'}
    for observation in audit.OBS:
        if observation['id'] in mapping:checked(mapping[observation['id']],observation['result']=='passed',observation,strict=False)
    assert len(audit.OBS)==30 and all(o['result']=='passed' for o in audit.OBS),audit.OBS
    return guardian


def media_races(guardian,student,output):
    from app import local_access,main as api
    student_control(student, '#access-mode').select_option('silent')
    lessons=request(student,'/local/lectures');old=next(l for l in lessons if l['title']=='동기화 테스트 강의');new=next(l for l in lessons if l['id']!=old['id'])
    video=bytes(student.evaluate('async()=>Array.from(new Uint8Array(await(await fetch(document.querySelector("#local-video").src)).arrayBuffer()))'))
    origin=student.evaluate('async()=>(await import("./config.js")).SERVER');source=origin+'/fixed-media-race'
    route=Route('/fixed-media-race',lambda req:HTMLResponse('<video autoplay muted loop src="data:video/mp4;base64,'+b64encode(video).decode()+'"></video>'))
    api.app.router.routes.insert(0,route)
    with local_access.db() as con:con.execute('UPDATE lectures SET playback=? WHERE id=?',(json.dumps({'kind':'direct','normalized_url':source}),old['id']))
    try:
        open_lesson(student,old['id'])
        student.evaluate("""()=>{window.__permissions=chrome.permissions.request;chrome.permissions.request=()=>new Promise(resolve=>window.__allow=resolve);}""")
        student_control(student, '#open-original').click();student.wait_for_function('()=>Boolean(window.__allow)')
        open_lesson(student,new['id']);expect(student.locator('#lesson-title')).to_have_text(new['title'])
        student.evaluate('window.__allow(true)');expect(student.locator('#open-original')).not_to_have_attribute('aria-busy','true')
        lease=student.evaluate('async()=>(await chrome.storage.session.get("playbackLease")).playbackLease||null')
        checked('R01',lease is None and not any(p.url==source for p in student.context.pages),{'lesson':student.locator('#lesson-title').inner_text(),'lease':lease})
        student.evaluate('()=>{chrome.permissions.request=window.__permissions;}')
        open_lesson(student,old['id'])
        student_disclosure(student, '내 기기의 영상 연결·보관')
        student_control(student, '#load-original').click();expect(student.locator('#connection')).to_contain_text('분석한 원본과 일치')
        before=request(student,'/extension/v1/student/lectures/'+new['id'])['progress']
        writes=[]
        student.on('request',lambda r:writes.append(r.post_data_json) if r.method=='PUT' and f'/lectures/{new["id"]}/progress' in r.url else None)
        student.evaluate("""async()=>{const{StudentMedia}=await import('./media.js');window.__send=StudentMedia.prototype.send;
          StudentMedia.prototype.send=async function(action,...args){const value=await window.__send.call(this,action,...args);if(action==='seek')await new Promise(resolve=>window.__seek=resolve);return value;};
          const{command}=await import('./app.js');command('10초 앞으로').then(()=>window.__done=true).catch(error=>{window.__done=true;window.__cancelled=error.cancelled;});}""")
        student.wait_for_function('()=>Boolean(window.__seek)');open_lesson(student,new['id']);expect(student.locator('#lesson-title')).to_have_text(new['title'])
        student.evaluate('window.__seek()');student.wait_for_function('()=>window.__done===true')
        after=request(student,'/extension/v1/student/lectures/'+new['id'])['progress']
        checked('R02',before==after and not writes,{'before':before,'after':after,'writes':writes})
        student.evaluate('async()=>{const{StudentMedia}=await import("./media.js");StudentMedia.prototype.send=window.__send;}')
        open_lesson(student,old['id'])
        student.evaluate("""()=>{window.__runtimeSend=chrome.runtime.sendMessage;chrome.runtime.sendMessage=async message=>{
          const result=await window.__runtimeSend(message);if(message.type==='student-media'&&message.action==='claim')return new Promise(resolve=>window.__claimReply=()=>resolve(result));return result;};}""")
        with student.context.expect_page() as opened:student_control(student, '#open-original').click()
        native=opened.value;student.wait_for_function('()=>Boolean(window.__claimReply)')
        native.wait_for_function('()=>Boolean(document.querySelector("video")&&!document.querySelector("video").paused)')
        student_control(student, '#stop').click();native.wait_for_function('()=>document.querySelector("video").paused')
        student.evaluate('window.__claimReply()');expect(student.locator('#open-original')).not_to_have_attribute('aria-busy','true')
        assert native.evaluate('document.querySelector("video").paused')
        EXTRA['stop_during_pending_claim']={'passed':True,'video_paused':True}
        student.evaluate('()=>{chrome.runtime.sendMessage=window.__runtimeSend;}');native.close()
    finally:api.app.router.routes.remove(route)
    raise Complete()


def live_feedback(guardian,student,output):
    from app import local_access,main as api
    user=request(student,'/local/me');lesson=next(l for l in request(student,'/local/lectures') if l['title']=='동기화 테스트 강의')
    binary=bytes(student.evaluate('async()=>Array.from(new Uint8Array(await(await fetch(document.querySelector("#local-video").src)).arrayBuffer()))'))
    source=student.evaluate('async()=>(await import("./config.js")).SERVER')+'/fixed-live-feedback'
    route=Route('/fixed-live-feedback',lambda req:HTMLResponse('<video muted loop src="data:video/mp4;base64,'+b64encode(binary).decode()+'"></video>'))
    api.app.router.routes.insert(0,route)
    with local_access.db() as con:con.execute('UPDATE lectures SET playback=? WHERE id=?',(json.dumps({'kind':'direct','normalized_url':source}),lesson['id']))
    try:
        open_lesson(student,lesson['id']);student_control(student, '#access-mode').select_option('app')
        def connect():
            student_control(student, '#open-original').click();expect(student.locator('#connection')).to_contain_text('원본 강의 탭을 연결')
            native=next(p for p in student.context.pages if p.url==source)
            student_control(student, '#play').click();native.wait_for_function('()=>!document.querySelector("video").paused');student.wait_for_timeout(150)
            student.evaluate('window.__spoken=[]');return native
        native=connect();native.close();expect(student.locator('#connection')).to_contain_text('연결이 끊겼습니다')
        student.wait_for_function('()=>window.__spoken.some(u=>u.text.includes("연결이 끊겼습니다"))')
        tab_words=student.evaluate('window.__spoken.map(u=>u.text)')
        native=connect();full=student.context.new_page();full.goto(student.url.split('#')[0].split('?')[0]);expect(full.locator('#workspace')).to_be_visible()
        student.evaluate('window.__spoken=[]')
        full.evaluate('async()=>await chrome.runtime.sendMessage({type:"student-media",view:"regression-new-view",action:"claim"})')
        expect(student.locator('#connection')).to_contain_text('다른 수강 화면')
        student.wait_for_function('()=>window.__spoken.some(u=>u.text.includes("다른 수강 화면"))')
        lease=full.evaluate('async()=>(await chrome.storage.session.get("playbackLease")).playbackLease')
        checked('R04',lease['view']=='regression-new-view' and native.evaluate('document.querySelector("video").paused'),{'tab_failure_words':tab_words,'lease_words':student.evaluate('window.__spoken.map(u=>u.text)'),'lease_owner':lease['view']})
        full.close();native.close()

        job=prepare(guardian,'실패 응답 검사',{'assets':[{'name':'p.txt','kind':'passage','content':'질문 실패를 확인하는 자료입니다.'}]})
        guardian.locator('#refresh-preparations').click();guardian.get_by_role('button',name='실패 응답 검사 결과 확인·배정',exact=True).click()
        form=guardian.locator('#preview-question-form');form.locator('[name=message]').fill('자료를 설명해 주세요.');form.locator('[name=analysis_consent]').check();form.locator('button').click()
        expect(guardian.locator('#preview-answer')).to_contain_text('답변을 만들지 못했습니다')
        failure=guardian.locator('#preview-answer').inner_text();assert '확인하고 있습니다' not in failure
        held=[];guardian.route('**/preparations/*/agent-turn',lambda route:held.append(route))
        form.locator('button').click();guardian.wait_for_timeout(100);assert held
        newer=prepare(guardian,'새 결과 검사',{'assets':[{'name':'new.txt','kind':'passage','content':'새 결과에는 이전 실패가 나타나면 안 됩니다.'}]})
        guardian.locator('#refresh-preparations').click();guardian.get_by_role('button',name='새 결과 검사 결과 확인·배정',exact=True).click()
        held[0].fulfill(status=503,content_type='application/json',body='{"detail":"이전 요청 실패"}')
        expect(form.locator('button')).not_to_have_attribute('aria-busy','true')
        checked('R12',guardian.locator('#preview-answer').inner_text()=='',{'terminal_error':failure,'newer_result':guardian.locator('#preview-answer').inner_text()})
        guardian.unroute('**/preparations/*/agent-turn')

        with local_access.db() as con:con.execute('UPDATE users SET settings=? WHERE id=?',(json.dumps({**user['settings'],'reader_mode':True,'focus_voice':False}),user['id']))
        student.evaluate('async()=>await chrome.storage.local.remove("student-accessibility")')
        reader=student.context.new_page();reader.goto(student.url.split('#')[0].split('?')[0]);expect(reader.locator('#workspace')).to_be_visible();expect(reader.locator('#access-mode')).to_have_value('reader');reader.wait_for_timeout(250)
        initial=reader.evaluate('window.__spoken.map(u=>u.text)');assert not initial,initial
        reader.locator('#logout').click();expect(reader.locator('#auth')).to_be_visible();reader.evaluate('window.__spoken=[]')
        reader.locator('#username').fill('student');reader.locator('#password').fill('extension-pass-123');reader.locator('#login-form button').click();expect(reader.locator('#workspace')).to_be_visible();reader.wait_for_timeout(200)
        checked('R11',reader.evaluate('window.__spoken.length')==0,{'initial_words':initial,'login_words':reader.evaluate('window.__spoken.map(u=>u.text)')})
        reader.close()
    finally:api.app.router.routes.remove(route)
    raise Complete()


def prepare(guardian,title,payload):
    job=request(guardian,'/extension/v1/guardian/preparations','POST',{'title':title,**payload})
    for _ in range(60):
        result=request(guardian,'/extension/v1/guardian/preparations/'+job['id'])
        if result['state'] not in ['queued','running']:return result
        guardian.wait_for_timeout(50)
    raise AssertionError('Preparation did not reach a terminal state')


def forms_focus(guardian,student,output):
    student.context.add_init_script(SPEECH);student.evaluate(SPEECH)
    failed=prepare(guardian,'다시 준비할 작업',{'assets':[{'name':'invalid.srt','kind':'subtitle','content':'not a subtitle'}]});assert failed['state']=='failed'
    guardian.locator('#refresh-preparations').click();guardian.locator('#prepare-guided').click()
    form=guardian.locator('#prepare-form');form.locator('[name=title]').fill('이전 제목');guardian.locator('#prepare-next').click();form.locator('[name=passage]').fill('이전 지문입니다.');guardian.locator('#prepare-next').click()
    expect(guardian.locator('#prepare-step')).to_contain_text('3/3')
    guardian.get_by_role('button',name='다시 준비할 작업 다시 준비',exact=True).click()
    expect(guardian.locator('#prepare-step')).to_contain_text('1/3');expect(form.locator('[name=title]')).to_be_focused()
    guardian.locator('#prepare-next').click();form.locator('[name=passage]').fill('새 자료입니다.');guardian.locator('#prepare-next').click()
    summary=guardian.locator('#prepare-summary').inner_text();checked('R13','다시 준비할 작업' in summary and '이전 제목' not in summary,summary)
    guardian.locator('#prepare-guided').click();form.locator('[name=title]').fill('전체 자료 제한');form.locator('[name=passage]').fill('')
    guardian.locator('#material-files').set_input_files([{'name':f'{i}.txt','mimeType':'text/plain','buffer':b'x'*260001} for i in range(4)])
    sent=[];guardian.on('request',lambda r:sent.append(r.url) if r.method=='POST' and r.url.endswith('/guardian/preparations') else None)
    form.locator('button[type=submit]').click();expect(guardian.locator('#material-validation')).to_contain_text('100만');expect(guardian.locator('#material-files')).to_be_focused()
    checked('R14',not sent and guardian.locator('#material-files').get_attribute('aria-invalid')=='true',{'error':guardian.locator('#material-validation').inner_text(),'sent':list(sent)})

    job=prepare(guardian,'문장과 강조 검사',{'analysis':{'passage_text':'중요한 강조 문장입니다. 일반 문장입니다.\n\n둘째 문단 첫 문장입니다. 둘째 문단 다음 문장입니다.','highlighted_texts':['중요한 강조 문장입니다.']}})
    assert job['state']=='completed'
    students=request(guardian,'/local/students');target=next(s for s in students if s['username']=='student')
    published=request(guardian,'/extension/v1/guardian/preparations/'+job['id']+'/publish','POST',{'students':[target['id']]})
    student_control(student, '#refresh').click();open_lesson(student,published['id']);student_control(student, '#access-mode').select_option('reader')
    controls=student.locator('#material [data-sentence-id]');expect(controls).to_have_count(4)
    assert controls.first.evaluate('e=>e.tagName')=='STRONG'
    student_control(student, '#sentence-selection').select_option(index=0)
    student_control(student, '#selected-read').click();expect(student.locator('#reader-description')).to_contain_text('중요한 강조 문장')
    student_control(student, '#paragraph-form [name=query]').fill('다음 문장');student_control(student, '#paragraph-form button').click();expect(student.locator('#reader-description')).to_contain_text('일반 문장')
    expect(student.locator('#sentence-selection')).to_have_value(controls.nth(1).get_attribute('data-sentence-id'))
    student_control(student, '#paragraph-form [name=query]').fill('2문단');student_control(student, '#paragraph-form button').click();expect(student.locator('#reader-description')).to_contain_text('2문단')
    student_control(student, '#paragraph-form [name=query]').fill('다음 문장');student_control(student, '#paragraph-form button').click();expect(student.locator('#reader-description')).to_contain_text('둘째 문단 다음 문장')
    selected=student.locator('#sentence-selection').input_value()
    checked('R15',selected==controls.nth(3).get_attribute('data-sentence-id'),{'sentence_texts':controls.count(),'selected_sentence':selected,'paragraph_cursor_synced':True})
    student_control(student, '#voice-consent').check();student.evaluate('()=>{window.SpeechRecognition=class{start(){window.__started=true;this.onstart?.();}stop(){this.onresult?.({results:[[{transcript:"1문단 밑줄 표시"}]]});this.onend?.();}abort(){}};}')
    student_control(student, '#paragraph-selection').select_option(index=0)
    student_control(student, '#selected-read').focus();student.keyboard.down('Space');student.wait_for_function('()=>window.__started===true',timeout=4500);student.keyboard.up('Space')
    expect(student.locator('#selected-underline')).to_have_attribute('aria-pressed','true')
    checked('R16',student.evaluate('document.activeElement.id')=='selected-read',student.evaluate('document.activeElement.outerHTML'))
    student.reload();expect(student.locator('#lectures button')).to_have_count(2)
    held=[];student.route('**/extension/v1/student/lectures/*',lambda route:held.append(route));student_control(student, '#lectures button').first.click();student.wait_for_timeout(100);assert held
    student_control(student, '#type-command').click();student.locator('#text-command').fill('입력 중');held[0].continue_()
    expect(student.locator('#lectures button').first).not_to_have_attribute('aria-busy','true')
    # Opening the command dialog explicitly stops/cancels an in-flight open.
    expect(student.locator('#lesson')).to_be_hidden()
    checked('R17',student.locator('#text-command').evaluate('e=>e===document.activeElement'),student.evaluate('document.activeElement.id'))
    student.keyboard.press('Escape')
    expect(student.locator('#type-command')).to_be_focused()
    student.unroute('**/extension/v1/student/lectures/*')
    student_control(student, '#lectures button').first.focus();student.route('**/local/lectures',lambda route:route.fulfill(status=200,content_type='application/json',body='[]'))
    student.evaluate('document.querySelector("#refresh").click()');expect(student.locator('#lectures button')).to_have_count(0)
    checked('R18',student.locator('#workspace-title').evaluate('e=>e===document.activeElement'),student.evaluate('document.activeElement.id||document.activeElement.tagName'))
    student.unroute('**/local/lectures');student_control(student, '#refresh').click();expect(student.locator('#lectures button')).to_have_count(2)
    base=next(l for l in request(student,'/local/lectures') if l['id']!=published['id']);saved=request(student,'/extension/v1/student/lectures/'+base['id'])['progress'];open_lesson(student,base['id'])
    saves=[];student.route(f'**/local/lectures/{base["id"]}/progress',lambda route:saves.append(route))
    student_control(student, '#note').fill('저장 대기 중인 메모');student_control(student, f'#lectures button[data-lecture="{published["id"]}"]').click()
    student.wait_for_timeout(100);assert saves
    student_control(student, '#type-command').click();student.locator('#text-command').fill('입력 유지')
    for _ in range(60):
        while saves:saves.pop(0).continue_()
        if not student.locator(f'#lectures button[data-lecture="{published["id"]}"]').get_attribute('aria-busy'):break
        student.wait_for_timeout(50)
    expect(student.locator('#lesson-title')).to_have_text(base['title']);expect(student.locator('#text-command')).to_be_focused()
    EXTRA['focus_during_delayed_save']={'passed':True,'focus':student.evaluate('document.activeElement.id'),'dialog_cancels_pending_open':True}
    student.keyboard.press('Escape')
    expect(student.locator('#type-command')).to_be_focused()
    student.unroute(f'**/local/lectures/{base["id"]}/progress');request(student,'/local/lectures/'+base['id']+'/progress','PUT',saved)
    request(guardian,'/local/lectures/'+published['id'],'DELETE')
    student_control(student, '#refresh').click();expect(student.locator('#lectures button')).to_have_count(1)
    browser.check_layout(guardian,'fixed-guardian-errors',output);browser.check_layout(student,'fixed-student-focus',output)
    return guardian


def run(name,exercise):
    output=OUT/name;output.mkdir(parents=True,exist_ok=True);browser.AXE_RESULTS.clear()
    try:
        try:browser.main(exercise,phase='fixed-'+name,output=output)
        except Complete:pass
    except BaseException:
        GROUPS.append({'group':name,'result':'failed','error':traceback.format_exc()});print(GROUPS[-1]['error'],flush=True)
    else:GROUPS.append({'group':name,'result':'passed'})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--group',choices=['supplement','media','live','forms']);parser.add_argument('--output',type=Path,default=OUT);args=parser.parse_args();OUT=args.output.resolve();OUT.mkdir(parents=True,exist_ok=True)
    if args.group in (None,'supplement'):run('supplement',supplement)
    if args.group in (None,'media'):
        phase3.student_check=media_races;run('media',phase3)
    if args.group in (None,'live'):
        phase3.student_check=live_feedback;run('live',phase3)
    if args.group in (None,'forms'):run('forms',forms_focus)
    missing=sorted(set(f'R{i:02d}' for i in range(1,19))-CHECKS.keys()) if not args.group else []
    report={'version':VERSION,'result':'passed' if not missing and all(g['result']=='passed' for g in GROUPS) else 'failed','groups':GROUPS,'issues':CHECKS,'missing':missing,
        'additional_boundaries':EXTRA,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'apps/extensions').rglob('*') if p.is_file() and p.suffix in ('.js','.html','.css')},
        'boundaries':['Temporary DB/profile and real decoded video/API/worker','Speech/recognition and delayed replies are explicit test doubles','Actual VoiceOver/NVDA, microphone and live provider quality not verified']}
    (OUT/(f'results-{args.group}.json' if args.group else 'results.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(report['result']!='passed')
