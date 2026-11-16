"""Generic page/frame/shadow player and MIME-independent files in installed extensions."""
from verify_extensions_browser import student_control
import argparse
from base64 import b64encode
import json
from pathlib import Path
from starlette.responses import HTMLResponse
from starlette.routing import Route
from playwright.sync_api import expect
import verify_extensions_browser as browser
from verify_extensions_phase3 import exercise as phase3
from verify_reaudit_fixes import Complete, request, open_lesson

checks={}
def record(name,passed,observed):
    checks[name]={'passed':bool(passed),'observed':observed};print(name,'PASS' if passed else 'FAIL',flush=True)


def exercise(guardian,student,output):
    from app import main as api, local_access
    student_control(student, '#access-mode').select_option('silent')
    lesson=next(row for row in request(student,'/local/lectures') if row['title']=='동기화 테스트 강의')
    binary=bytes(student.evaluate('async()=>Array.from(new Uint8Array(await(await fetch(document.querySelector("#local-video").src)).arrayBuffer()))'))
    # Empty MIME is common with drag/drop or platform file associations.
    student_control(student, '#store-original').uncheck()
    student_control(student, '#local-file').set_input_files({'name':'lecture.unknown','mimeType':'','buffer':binary})
    student_control(student, '#connect-file').click();expect(student.locator('#connection')).to_contain_text('분석한 원본과 일치')
    record('U01.empty_mime_file',True,student.locator('#connection').inner_text())
    student_control(student, '#local-file').set_input_files({'name':'broken.mkv','mimeType':'video/x-matroska','buffer':b'not a decodable video'})
    student_control(student, '#connect-file').click();expect(student.locator('#connection')).to_contain_text('원본과 다른 파일')
    record('U02.mismatch_fails_closed',student.locator('#local-video').evaluate('e=>!e.getAttribute("src")'),student.locator('#connection').inner_text())
    identity=request(student,f'/extension/v1/student/lectures/{lesson["id"]}')['media_identity']
    with local_access.db() as con:con.execute('DELETE FROM lecture_media WHERE lecture=?',(lesson['id'],))
    open_lesson(student,lesson['id'])
    student_control(student, '#local-file').set_input_files({'name':'undecodable.video','mimeType':'','buffer':b'not a video'})
    student_control(student, '#connect-file').click();expect(student.locator('#connection')).to_contain_text('코덱')
    record('U06.decode_failure_cleans_up',student.locator('#local-video').evaluate('e=>!e.getAttribute("src")'),student.locator('#connection').inner_text())
    with local_access.db() as con:con.execute('INSERT INTO lecture_media VALUES(?,?)',(lesson['id'],json.dumps(identity)))
    open_lesson(student,lesson['id'])
    # Voice list changes preserve a user's unsaved explicit choice.
    student.evaluate('''()=>{speechSynthesis.getVoices=()=>[{lang:'ko-KR',name:'Basic',voiceURI:'basic'},
      {lang:'ko-KR',name:'Neural Natural',voiceURI:'natural'}];window.__nativeSynth.dispatchEvent(new Event('voiceschanged'));}''')
    student_control(student, '#speech-voice').select_option('basic')
    student.evaluate("window.__nativeSynth.dispatchEvent(new Event('voiceschanged'))")
    record('U03.unsaved_voice_preserved',student.locator('#speech-voice').input_value()=='basic',student.locator('#speech-voice').input_value())
    origin=student.evaluate('async()=>(await import("./config.js")).SERVER')
    data='data:video/mp4;base64,'+b64encode(binary).decode()
    routes=[
        Route('/generic-course',lambda req:HTMLResponse('<html lang="ko"><title>Generic lecture</title><iframe width="700" height="400" src="/shadow-player"></iframe></html>')),
        Route('/shadow-player',lambda req:HTMLResponse('<html><div id="host"></div><script>document.querySelector("#host").attachShadow({mode:"open"}).innerHTML='+json.dumps('<video muted style="width:640px;height:360px" src="'+data+'"></video>')+';</script></html>')),
        Route('/cross-course',lambda req:HTMLResponse('<html><iframe width="700" height="400" src="'+origin.replace('127.0.0.1','localhost')+'/shadow-player"></iframe></html>')),
    ]
    api.app.router.routes[0:0]=routes
    try:
        source=origin+'/generic-course#/lesson/7'
        with local_access.db() as con:con.execute('UPDATE lectures SET playback=? WHERE id=?',(json.dumps({'kind':'external','normalized_url':source}),lesson['id']))
        open_lesson(student,lesson['id']);student_control(student, '#open-original').click()
        expect(student.locator('#connection')).to_contain_text('원본 강의 탭을 연결')
        expect(student.locator('#open-original')).to_be_focused()
        native=next(page for page in student.context.pages if page.url==source)
        student_control(student, '#play').click()
        native.frames[1].wait_for_function('()=>!document.querySelector("#host").shadowRoot.querySelector("video").paused')
        student_control(student, '#stop').click()
        native.frames[1].wait_for_function('()=>document.querySelector("#host").shadowRoot.querySelector("video").paused')
        record('U04.generic_same_origin_shadow_frame',True,{'frame_count':len(native.frames),'root':native.url})
        student_control(student, '#disconnect').click();native.close()
        student.evaluate('''async()=>{
          const {StudentMedia}=await import('./media.js');window.__originalConnect=StudentMedia.prototype.connect;
          StudentMedia.prototype.connect=async function(...args){await new Promise(resolve=>window.__resumeConnect=resolve);return window.__originalConnect.apply(this,args);};
        }''')
        student_control(student, '#open-original').click();expect(student.locator('#connection')).to_contain_text('연결하고 있습니다')
        student.locator('#note').evaluate('e=>{const details=e.closest("details");if(details)details.open=true;}')
        student_control(student, '#note').fill('연결을 기다리는 동안 쓰는 메모')
        student.evaluate('window.__resumeConnect()')
        expect(student.locator('#connection')).to_contain_text('원본 강의 탭을 연결')
        expect(student.locator('#note')).to_be_focused()
        record('U09.connection_focus_preserved',True,{'initial_connection':'settings connection control retains focus','delayed_connection':'newer note focus preserved'})
        student.evaluate('async()=>{const {StudentMedia}=await import("./media.js");StudentMedia.prototype.connect=window.__originalConnect;}')
        student_control(student, '#disconnect').click()
        next(page for page in student.context.pages if page.url==source).close()
        source=origin+'/cross-course'
        with local_access.db() as con:con.execute('UPDATE lectures SET playback=? WHERE id=?',(json.dumps({'kind':'external','normalized_url':source}),lesson['id']))
        open_lesson(student,lesson['id'])
        student.evaluate('''async origin=>{
          const {StudentMedia}=await import('./media.js');window.__mediaSend=StudentMedia.prototype.send;
          window.__frameAllowed=false;window.__grantDecision=false;
          StudentMedia.prototype.send=async function(action,...args){
            if(action==='pause'&&!window.__frameAllowed)throw Object.assign(new Error('시험: 영상 제공 사이트 권한 필요'),{permissionOrigins:[origin+'/*']});
            return window.__mediaSend.call(this,action,...args);
          };
          const original=chrome.permissions.request;
          chrome.permissions.request=async options=>{
            if(options.origins.some(value=>value.startsWith(origin))){window.__frameAllowed=window.__grantDecision;return window.__grantDecision;}
            return original(options);
          };
        }''',origin.replace('127.0.0.1','localhost'))
        student_control(student, '#open-original').click()
        expect(student.locator('#grant-player')).to_be_visible()
        expect(student.locator('#player-permission-help')).to_contain_text('localhost')
        student.bring_to_front();student_control(student, '#grant-player').focus();student.keyboard.press('Enter')
        expect(student.locator('#connection')).to_contain_text('허용하지 않았습니다')
        expect(student.locator('#grant-player')).to_be_visible()
        student.evaluate('window.__grantDecision=true')
        student_control(student, '#grant-player').focus();student.keyboard.press('Enter')
        expect(student.locator('#connection')).to_contain_text('원본 강의 탭을 연결')
        expect(student.locator('#grant-player')).to_be_hidden()
        native=next(page for page in student.context.pages if page.url==source)
        student_control(student, '#play').click()
        native.frames[1].wait_for_function('()=>!document.querySelector("#host").shadowRoot.querySelector("video").paused')
        student_control(student, '#stop').click()
        native.frames[1].wait_for_function('()=>document.querySelector("#host").shadowRoot.querySelector("video").paused')
        record('U05.cross_origin_frame_permission',True,{'frame_count':len(native.frames),'lease':student.evaluate('async()=>(await chrome.storage.session.get("playbackLease")).playbackLease')})
        native.close()
        # A URL alone creates a usable playback assignment without pretending
        # that a video analyzer ran or sending an ungrounded content question.
        form=guardian.locator('#prepare-form')
        guardian.locator('#prepare-source').select_option('link')
        form.locator('[name=title]').fill('링크만 등록 검사')
        guardian.locator('#material-files').set_input_files([]);form.locator('[name=passage]').fill('')
        guardian.locator('#prepare-url').fill('https://lecture.example/course#/lesson/1')
        form.locator('[name=request_analysis]').uncheck();guardian.locator('#prepare-rights').check()
        form.locator('button[type=submit]').click();expect(guardian.locator('#status')).to_contain_text('준비를 접수했습니다')
        guardian.locator('#refresh-preparations').click()
        guardian.get_by_role('button',name='링크만 등록 검사 결과 확인·배정',exact=True).click()
        expect(guardian.locator('#prepared-title')).to_have_text('링크만 등록 검사 준비 결과')
        guardian.locator('#publish-students').get_by_label('학생 하나',exact=True).check()
        expect(guardian.locator('#publish-students input').first).to_be_checked()
        guardian.locator('#publish-form button').click();expect(guardian.locator('#status')).to_contain_text('학생에게 배정했습니다')
        student_control(student, '#refresh').click();student_control(student, '#lectures button').filter(has_text='링크만 등록 검사 열기').click()
        expect(student.locator('#source-label')).to_contain_text('영상 분석은 실행하지 않았습니다')
        expect(student.locator('#open-original')).to_be_enabled()
        turns=[];student.on('request',lambda req:turns.append(req.url) if req.url.endswith('/agent-turn') else None)
        student_control(student, '#chat-input').fill('강의 내용 요약');student_control(student, '#chat-form button').click()
        expect(student.locator('#status')).to_contain_text('내용 질문에는')
        record('U07.link_only_is_playback_not_analysis',not turns,{'agent_turns':len(turns),'source_label':student.locator('#source-label').inner_text()})
        # Local playback registration sends only explicit metadata, never raw
        # media. No analyzer or credentials are required for the playback path.
        registrations=[]
        guardian.on('request',lambda req:registrations.append(req) if req.method=='POST' and req.url.endswith('/preparations') else None)
        guardian.locator('#prepare-source').select_option('local')
        form.locator('[name=title]').fill('원본 미전송 파일 검사')
        guardian.locator('#prepare-video').set_input_files({'name':'lecture.unknown','mimeType':'','buffer':binary})
        form.locator('button[type=submit]').click();expect(guardian.locator('#status')).to_contain_text('준비를 접수했습니다')
        guardian.locator('#refresh-preparations').click()
        guardian.get_by_role('button',name='원본 미전송 파일 검사 결과 확인·배정',exact=True).click()
        expect(guardian.locator('#prepared-title')).to_have_text('원본 미전송 파일 검사 준비 결과')
        guardian.locator('#publish-students').get_by_label('학생 하나',exact=True).check()
        guardian.locator('#publish-form button').click();expect(guardian.locator('#status')).to_contain_text('학생에게 배정했습니다')
        student_control(student, '#refresh').click();student_control(student, '#lectures button').filter(has_text='원본 미전송 파일 검사 열기').click()
        expect(student.locator('#source-label')).to_contain_text('영상 분석은 실행하지 않았습니다')
        student_control(student, '#local-file').set_input_files({'name':'lecture.unknown','mimeType':'','buffer':binary})
        student_control(student, '#connect-file').click();expect(student.locator('#connection')).to_contain_text('수동 재생')
        student_control(student, '#play').click();student.wait_for_function('()=>!document.querySelector("#local-video").paused')
        student_control(student, '#stop').click();student.wait_for_function('()=>document.querySelector("#local-video").paused')
        body=registrations[0].post_data_json if len(registrations)==1 else {}
        record('U08.local_metadata_only_playback',body.get('local_file')=={'name':'lecture.unknown','size_bytes':len(binary)} and not body.get('assets') and not body.get('analysis'),
          {'requests':len(registrations),'content_type':registrations[0].headers.get('content-type') if registrations else None,'body':body,'connection':student.locator('#connection').inner_text()})
        browser.check_layout(student,'student-universal-playback',output)
    finally:
        for route in routes:api.app.router.routes.remove(route)
    raise Complete()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    phase3.student_check=exercise
    original_build=browser.build
    def build_fixture(*args,**kwargs):
        packages=original_build(*args,**kwargs)
        path=Path(packages)/'student/manifest.json';manifest=json.loads(path.read_text())
        # Pregrant only the disposable localhost child to exercise actual frame
        # injection. Native prompt completion/denial is a separate explicit fixture.
        manifest['host_permissions'].append('http://localhost/*');path.write_text(json.dumps(manifest))
        return packages
    browser.build=build_fixture
    def run(guardian,student,output):
        # Use the panel branch in a controllable workspace document; Chrome's
        # actual side-panel opening remains in the production regression suite.
        student.add_init_script('chrome.extension.getViews=()=>[]')
        student.reload();expect(student.locator('#lectures button').first).to_be_visible()
        student.evaluate('window.__nativeSynth=window.speechSynthesis')
        return phase3(guardian,student,output)
    try:browser.main(run,phase='universal',output=args.output)
    except Complete:pass
    report={'result':'passed' if len(checks)==9 and all(c['passed'] for c in checks.values()) else 'failed','checks':checks,'axe':browser.AXE_RESULTS,
      'boundary':'Actual installed extensions/API/DB/decoded media, real iframe/shadow DOM injection with fixture localhost host pregrant. Panel-context detection, native permission need/deny/allow completion and speech/analyzer are explicit test fixtures; no paid site scraping.'}
    (args.output/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(report['result']!='passed')
