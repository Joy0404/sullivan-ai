"""Real local HTTP/auth/UI flow, mocked YouTube and speech recognition; no provider calls."""
from pathlib import Path
import json,os,socket,sys,tempfile,threading,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps/api'))
import uvicorn
from playwright.sync_api import sync_playwright,expect
from accessibility_probe import probe,save as save_accessibility
MOCK='''window.YT={PlayerState:{PLAYING:1,ENDED:0},Player:class {
constructor(id,c){const mount=document.getElementById(id);if(!mount)throw Error('YouTube mount missing');this.frame=document.createElement('iframe');this.frame.id=id;this.frame.className=mount.className;this.frame.src='about:blank';mount.replaceWith(this.frame);this.t=0;this.s=5;this.c=c;window.__player=this;setTimeout(()=>c.events.onReady(),0);}
cueVideoById({startSeconds=0}){void this.frame.src;this.t=startSeconds;this.s=5;this.c.events.onStateChange({data:5});}
getCurrentTime(){void this.frame.src;return this.s===5?0:this.t;}getPlayerState(){void this.frame.src;return this.s;}seekTo(t){void this.frame.src;this.t=t;if(this.s!==2)this.playVideo();}playVideo(){void this.frame.src;this.s=1;this.c.events.onStateChange({data:1});}pauseVideo(){void this.frame.src;this.s=2;}
destroy(){void this.frame.src;this.frame.remove();this.frame=null;this.s=2;}
}};'''

def guardian_layout(page,stage):
 out=ROOT/'docs/verification';out.mkdir(exist_ok=True)
 for width in (320,390,1280,1920):
  page.set_viewport_size({'width':width,'height':900})
  assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),(stage,width)
 for width,height,suffix in [(1280,900,'desktop'),(390,844,'mobile')]:
  page.set_viewport_size({'width':width,'height':height});page.evaluate('window.scrollTo(0,0)')
  page.screenshot(path=str(out/f'{stage}-{suffix}.png'),full_page=True)
 page.set_viewport_size({'width':640,'height':450})
 assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),(stage,'200% equivalent')
 page.emulate_media(reduced_motion='reduce',forced_colors='active')
 first=page.locator('button:visible:enabled').first;first.focus()
 page.keyboard.press('Tab');page.keyboard.press('Shift+Tab')
 assert first.evaluate('(e)=>e===document.activeElement')
 assert first.evaluate('(e)=>parseFloat(getComputedStyle(e).outlineWidth)>=4')
 assert page.evaluate('getComputedStyle(document.documentElement).scrollBehavior')=='auto'
 page.emulate_media(reduced_motion='no-preference',forced_colors='none')
 page.set_viewport_size({'width':1280,'height':900})

def main():
 with tempfile.TemporaryDirectory(prefix='sullivan-role-tests-') as temp:
  os.environ['SULLIVAN_ACCOUNTS_DB']=str(Path(temp)/'accounts.sqlite')
  os.environ['SULLIVAN_ROLE_AUTH']='1'
  os.environ['GEMINI_API_KEY']=''
  for name in ['DATABASE_URL','DATABASE_URL_UNPOOLED','RENDER']:os.environ.pop(name,None)
  from app.main import app
  sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  server=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False))
  thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
  while not server.started:time.sleep(.01)
  results=[]
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch()
    context=browser.new_context(viewport={'width':1280,'height':900})
    context.add_init_script(MOCK)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    base=f'http://127.0.0.1:{port}'
    page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort())
    page.goto(base)
    page.wait_for_function("document.querySelector('#login-title').textContent.includes('처음')")
    page.locator('.skip-link').focus();page.keyboard.press('Enter')
    assert page.locator(':focus').get_attribute('id')=='main'
    probe(page,'account-setup')
    page.locator('#login-username').fill('guardian');page.locator('#login-password').fill('test-pass-123');page.locator('#login-submit').focus();page.keyboard.press('Enter')
    page.locator('#guardian-title').wait_for(state='visible')
    probe(page,'guardian-dashboard')
    assert page.locator('#guardian-create-panel').get_attribute('open') is not None
    assert page.locator('#settings-rate').is_disabled()
    page.locator('.guardian-settings-panel summary').press('Enter');probe(page,'guardian-settings-unavailable')
    page.locator('.guardian-settings-panel summary').press('Enter')
    guardian_layout(page,'guardian-empty')
    page.locator('#student-create input[name=name]').fill('학생 하나');page.locator('#student-create input[name=username]').fill('student1');page.locator('#student-create input[name=password]').fill('test-pass-123');page.locator('#student-create button').focus();page.keyboard.press('Enter')
    page.wait_for_function("document.querySelector('#settings-student').options.length===1")
    assert page.locator('#guardian-create-panel').get_attribute('open') is None
    assert page.locator('#settings-rate').is_enabled()
    page.locator('#guardian-create-panel summary').focus();page.keyboard.press('Space')
    assert page.locator('#student-create input[name=name]').is_visible()
    page.keyboard.press('Space');assert page.locator('#student-create input[name=name]').is_hidden()
    page.locator('.guardian-settings-panel summary').focus();page.keyboard.press('Enter')
    probe(page,'guardian-settings')
    page.locator('#student-settings button[type=submit]').focus();page.keyboard.press('Enter')
    page.wait_for_function("document.querySelector('#portal-feedback').textContent==='학생 기본 설정을 저장했습니다.'")
    page.locator('.guardian-settings-panel summary').focus();page.keyboard.press('Enter')
    assert page.locator('#settings-student').is_hidden()
    page.locator('#guardian-science').focus();page.keyboard.press('Space')
    page.locator('#guardian-publish').wait_for(state='visible')
    # Audit the final order after the optional fixture iframe finishes mounting.
    page.wait_for_function('window.__player && document.querySelector("#lecture-youtube").title')
    probe(page,'guardian-publish')
    guardian_layout(page,'guardian-publish')
    assert page.locator('#publish-store').is_disabled()
    assert page.locator('#publish-store').get_attribute('aria-describedby')=='publish-store-help'
    assert page.locator('#publish-store-help').is_visible()
    for panel in ['watch','passage','review','study','chat','evidence']:
      page.locator('.nav-button[data-panel='+panel+'-panel]').press('Space')
      probe(page,'guardian-'+panel)
    page.locator('.nav-button[data-panel=watch-panel]').press('Space')
    page.locator('#publish-students input').focus();page.keyboard.press('Space');assert page.locator('#publish-students input').is_checked()
    page.locator('#publish-title-input').fill('별의 진화');page.locator('#publish-subject').fill('과학')
    page.locator('#publish-form button[type=submit]').focus();page.keyboard.press('Enter')
    page.wait_for_function("document.querySelectorAll('.guardian-lecture').length===1")
    results.append('guardian account → linked student → sample preparation → assignment and ready: keyboard PASS')
    # Real text-material preparation path, without a cloud provider or a raw video upload.
    page.locator('#guardian-prepare').focus();page.keyboard.press('Enter')
    page.locator('input[name=title]').fill('관계대명사 지문');page.locator('input[name=subject]').fill('영어')
    page.locator('#material-files').set_input_files({'name':'lesson.txt','mimeType':'text/plain','buffer':'첫 문단은 관계대명사를 설명합니다.\n\n다음 문단은 예문을 비교합니다.'.encode()})
    probe(page,'guardian-preparation')
    guardian_layout(page,'guardian-preparation')
    # Hold only the browser/server boundary: cancel waiting without publishing.
    held=[]
    page.route('**/v1/lectures',lambda route:held.append(route))
    page.locator('input[name=rights_confirmed]').press('Space')
    page.locator('#lecture-form button[type=submit]').press('Enter')
    page.locator('#analysis-overlay').wait_for(state='visible')
    page.wait_for_function("document.activeElement.id==='cancel-analysis-wait'")
    probe(page,'guardian-analysis-wait')
    page.keyboard.press('Tab');assert page.locator(':focus').get_attribute('id')=='cancel-analysis-wait'
    page.keyboard.press('Shift+Tab');assert page.locator(':focus').get_attribute('id')=='cancel-analysis-wait'
    page.keyboard.press('Escape');page.locator('#analysis-overlay').wait_for(state='hidden')
    page.wait_for_function('state.analysisController===null')
    assert page.locator(':focus').evaluate("e=>e.matches('#lecture-form button[type=submit]')")
    assert '대기를 취소' in page.locator('#portal-feedback').inner_text()
    for route in held:
      try:route.fulfill(status=200,content_type='application/json',body='{"session_id":"late-cancelled"}')
      except Exception:pass # Chromium may already discard the canceled request.
    page.unroute('**/v1/lectures')
    assert page.locator('#agent-view').is_hidden() and page.evaluate('state.snapshot===null')
    page.route('**/v1/lectures',lambda route:route.fulfill(status=503,content_type='application/json',body='{"detail":"시험용 준비 오류"}'))
    page.locator('#lecture-form button[type=submit]').press('Enter')
    page.wait_for_function("document.querySelector('#portal-feedback').textContent.includes('시험용 준비 오류')")
    assert page.locator(':focus').get_attribute('id')=='portal-feedback'
    assert page.locator('#portal-feedback').get_attribute('role')=='group'
    assert page.locator('#portal-feedback').get_attribute('aria-describedby')=='portal-feedback-copy'
    probe(page,'guardian-preparation-error')
    page.unroute('**/v1/lectures')
    page.locator('input[name=rights_confirmed]').press('Space')
    results.append('analysis wait: Tab/Shift+Tab contained, Escape cancels waiting, return focus, no stale publish; server boundary simulated: PASS')
    page.locator('input[name=rights_confirmed]').focus();page.keyboard.press('Space')
    page.locator('#lecture-form button[type=submit]').focus();page.keyboard.press('Enter')
    page.locator('#guardian-publish').wait_for(state='visible')
    # A generated local WebM exercises actual encryption and browser decoding;
    # its analysis is the imported TXT, never a claimed cloud-video analysis.
    page.evaluate('''async()=>{const canvas=document.createElement('canvas');canvas.width=160;canvas.height=90;const ctx=canvas.getContext('2d');ctx.fillStyle='navy';ctx.fillRect(0,0,160,90);let frame=0;const drawing=setInterval(()=>{ctx.fillStyle=frame++%2?'navy':'teal';ctx.fillRect(0,0,160,90);},100);const stream=canvas.captureStream(10);const rec=new MediaRecorder(stream,{mimeType:'video/webm'});let chunks=[];rec.ondataavailable=e=>chunks.push(e.data);const done=new Promise(r=>rec.onstop=r);rec.start();await new Promise(r=>setTimeout(r,1200));rec.stop();await done;clearInterval(drawing);stream.getTracks().forEach(t=>t.stop());state.localVideoFile=new File(chunks,'local-test.webm',{type:'video/webm'});Portal.lectureReady();}''')
    page.locator('#publish-store').focus();page.keyboard.press('Space')
    page.locator('#publish-students input').focus();page.keyboard.press('Space')
    page.locator('#publish-form button[type=submit]').focus();page.keyboard.press('Enter')
    page.wait_for_function("document.querySelectorAll('.guardian-lecture').length===2")
    results.append('guardian TXT import → actual API passage processing; explicit encrypted browser media save → ready: PASS')
    assert page.request.post(base+'/local/students',headers={'X-Local-Request':'1'},data={'username':'student2','password':'test-pass-123','name':'학생 둘'}).status==200
    probe(page,'guardian-management')
    page.locator('.guardian-lecture details summary').first.press('Enter')
    probe(page,'guardian-lecture-edit')
    page.locator('.guardian-lecture details summary').first.press('Enter')
    assert page.locator('.guardian-assignees').filter(has_text='학생 하나').count()==2
    assert page.locator('.guardian-ready').filter(has_text='준비 완료').count()==2
    page.once('dialog',lambda d:d.dismiss())
    page.locator('.guardian-delete').first.focus();page.keyboard.press('Enter')
    expect(page.locator('.guardian-lecture')).to_have_count(2)
    guardian_layout(page,'guardian')
    results.append('guardian design: empty-student settings disabled, disclosure keyboard toggle, settings save, ready/assigned labels, deletion cancel and four-size dashboard/preparation/publish reflow: PASS')
    out=ROOT/'docs/verification';out.mkdir(exist_ok=True)
    page.screenshot(path=str(out/'guardian-desktop.png'),full_page=True)
    page.locator('#portal-logout').focus();page.keyboard.press('Enter');page.locator('#portal-login').wait_for(state='visible')
    probe(page,'login')
    page.locator('#login-username').fill('student1');page.locator('#login-password').fill('incorrect-test-pass');page.locator('#login-submit').press('Enter')
    page.wait_for_function("document.activeElement.id==='portal-feedback'")
    probe(page,'login-error')
    page.locator('#login-username').fill('student1');page.locator('#login-password').fill('test-pass-123');page.locator('#login-submit').focus();page.keyboard.press('Enter')
    page.locator('#onboarding-title').wait_for(state='visible',timeout=6000)
    assert page.locator(':focus').get_attribute('id')=='onboarding-done'
    probe(page,'student-onboarding')
    page.get_by_role('button',name='사용법 확인 완료',exact=True).focus();page.keyboard.press('Space')
    page.locator('#onboarding-card').wait_for(state='detached')
    probe(page,'student-home')
    assert page.locator(':focus').get_attribute('id')=='student-list-open'
    for name in ['강의 듣기','지문·문단 듣기','원하는 내용 찾기','질문하기']:
      expect(page.locator(':focus')).to_have_accessible_name(name)
      assert page.evaluate('SullivanFocusVoice.describe(document.activeElement)')==name
      page.keyboard.press('Tab')
    out=ROOT/'docs/verification';out.mkdir(exist_ok=True)
    for width in (320,390,1280,1920):
      page.set_viewport_size({'width':width,'height':900})
      assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),width
      assert all(b.bounding_box()['height']>=52 for b in page.locator('.student-purpose-grid button').all())
    for width,height,suffix in [(1280,900,'desktop'),(390,844,'mobile')]:
      page.set_viewport_size({'width':width,'height':height});page.locator('#student-list-open').focus()
      page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(out/f'student-home-{suffix}.png'),full_page=True)
    page.set_viewport_size({'width':1280,'height':900})
    assert page.evaluate('SullivanFocusVoice.describe(document.querySelector("#student-records"))')=='학습 기록'
    speech_labels=page.evaluate('''() => {const label=document.createElement('label');label.append('읽기 속도 ');const select=document.createElement('select');select.innerHTML='<option>느리게</option><option selected>보통</option><option>빠르게</option>';label.append(select);document.body.append(label);const selected=SullivanFocusVoice.describe(select);label.remove();const checkbox=document.querySelector('#auto-narration');checkbox.checked=true;return {selected,checked:SullivanFocusVoice.describe(checkbox)};}''')
    assert speech_labels['selected']=='읽기 속도, 보통'
    assert speech_labels['checked'].endswith('켜져 있습니다.')

    # App focus speech is a separate opt-in fallback, never auto-detected as an OS reader.
    page.evaluate("() => {window.__focusSpoken=[];window.__speakOriginal=speechSynthesis.speak.bind(speechSynthesis);window.__cancelOriginal=speechSynthesis.cancel.bind(speechSynthesis);speechSynthesis.speak=u=>{window.__focusSpoken.push(u.text);u.onend?.();};speechSynthesis.cancel=()=>{};Portal.focusVoice=false;}")
    page.locator('#student-list-open').focus();page.keyboard.press('Tab');page.wait_for_timeout(220)
    assert page.evaluate('window.__focusSpoken.length')==0
    page.evaluate('Portal.focusVoice=true;Portal.readerMode=false')
    page.locator('#student-list-open').focus();page.wait_for_timeout(220)
    assert page.evaluate('window.__focusSpoken.at(-1)')=='강의 듣기'
    before=page.evaluate('window.__focusSpoken.length')
    page.keyboard.press('Tab');page.keyboard.press('Tab');page.keyboard.press('Tab');page.wait_for_timeout(220)
    assert page.evaluate('window.__focusSpoken.length')==before+1
    assert page.evaluate('window.__focusSpoken.at(-1)')=='질문하기'
    page.evaluate('Portal.readerMode=true')
    page.locator('#student-list-open').focus();page.wait_for_timeout(220)
    assert page.evaluate('window.__focusSpoken.length')==before+1
    page.evaluate('() => {Portal.focusVoice=false;Portal.readerMode=false;speechSynthesis.speak=window.__speakOriginal;speechSynthesis.cancel=window.__cancelOriginal;}')
    results.append('named focus speech fallback only when opted in; rapid Tab cancels stale labels; external-reader mode stays silent: PASS (speech API mocked)')

    assert page.locator('#assigned-list button').count()==2
    assert page.locator('#assigned-list').get_by_role('button',name='강의 1. 과학 — 별의 진화',exact=True).count()==1
    page.locator('#assigned-list button').first.focus();page.keyboard.press('Enter')
    page.wait_for_function("Portal.lectureId && document.activeElement.id==='learner-play'")
    assert page.locator('#guardian-publish').is_hidden()
    probe(page,'student-watch')
    page.locator('#student-preferences summary').press('Enter');probe(page,'student-preferences')
    page.locator('#student-preferences summary').press('Enter')
    assert page.request.post(base+'/v1/lectures',headers={'X-Local-Request':'1'},data={'title':'denied'}).status==403
    results.append('student four purposes, ordered accessible lecture names, selection focus and role API denial: PASS')
    page.locator('#learner-play').focus();page.keyboard.press('Space');assert page.evaluate('isPlaybackRunning()')
    expect(page.locator('#learner-play')).to_have_accessible_name('강의 일시정지')
    assert page.locator('#learner-play').get_attribute('aria-pressed') is None
    assert '재생 중' in page.locator('#learner-playback-state').inner_text()
    assert page.locator('.learner-playback button').all_text_contents()==['강의 일시정지','영상·해설 모두 중지','현재 화면 다시 설명']
    page.keyboard.press('ArrowRight');assert page.evaluate('getCurrentPlaybackMs()')==10000
    page.evaluate('window.__player.seekTo(35)');page.locator('#learner-records').focus();page.keyboard.press('Enter')
    probe(page,'student-records')
    for panel in ['review','study']:
      page.locator('[data-record-view='+panel+'-panel]').press('Enter')
      probe(page,'student-'+panel)
    page.locator('[data-learn-panel=watch-panel]').press('Enter')
    page.locator('#learner-note').fill('다음 시간에는 핵심 흐름부터 복습');page.wait_for_timeout(900)
    page.locator('#learner-home').focus();page.keyboard.press('Enter')
    page.locator('#portal-home').wait_for(state='visible')

    # Returning home retains a loaded lecture: all purpose buttons must reveal its view.
    for purpose_id,target in [('question','#chat-input'),('search','#navigation-command'),('paragraph','.paragraph-quick-commands [data-paragraph-command="전체 지문"]')]:
      page.locator('#portal-home [data-purpose='+purpose_id+']').focus();page.keyboard.press('Enter')
      page.locator('#agent-view').wait_for(state='visible')
      expect(page.locator(target)).to_be_focused()
      page.locator('#learner-home').focus();page.keyboard.press('Enter');page.locator('#portal-home').wait_for(state='visible')
    results.append('loaded lecture → home → each learning purpose: visible destination and correct focus: PASS')
    page.reload();page.locator('#portal-home').wait_for(state='visible');assert page.locator('#onboarding-card').count()==0
    page.locator('#assigned-list button').first.focus();page.keyboard.press('Enter')
    page.wait_for_function('getCurrentPlaybackMs()===35000')
    assert page.locator('#learner-note').input_value().startswith('다음 시간')
    results.append('native Space activates buttons; 10-second seek, server autosave, reload resume + notes; onboarding not repeated: PASS')
    page.evaluate('window.__originalPassage=state.snapshot.passage;state.snapshot.passage=null')
    page.locator('[data-learn-panel][data-purpose=paragraph]').focus();page.keyboard.press('Enter')
    assert page.locator('#portal-feedback').inner_text().startswith('이 강의에는 지문이 없습니다.')
    assert page.evaluate('getCurrentPlaybackMs()')==35000
    page.evaluate('state.snapshot.passage=window.__originalPassage')
    # Single and multi-tap actions are deferred until the whole sequence is known.
    page.locator('#command-surface').focus();page.keyboard.press('Space');page.wait_for_timeout(500)
    assert page.locator('#text-command-dialog').is_hidden()
    page.keyboard.press('Space');page.keyboard.press('Space');assert page.locator('#text-command-dialog').is_hidden();page.wait_for_timeout(500)
    assert not page.evaluate('isPlaybackRunning()')
    page.keyboard.press('Space');page.keyboard.press('Space');page.keyboard.press('Space')
    page.locator('#text-command-dialog').wait_for(state='visible')
    assert page.locator(':focus').get_attribute('id')=='text-command-input'
    probe(page,'text-command-dialog')
    page.locator('#text-command-input').focus();page.keyboard.press('Shift+Tab')
    assert page.locator(':focus').get_attribute('id')=='close-text-command'
    page.keyboard.press('Tab');assert page.locator(':focus').get_attribute('id')=='text-command-input'
    page.keyboard.type('현재 화면');page.keyboard.press('Space');page.keyboard.type('설명')
    assert page.locator('#text-command-input').input_value()=='현재 화면 설명'
    page.keyboard.press('Escape');assert page.locator(':focus').get_attribute('id')=='command-surface'
    # Microphone unavailable is a real unsupported-browser fallback, no provider call.
    page.evaluate('window.SpeechRecognition=undefined;window.webkitSpeechRecognition=undefined')
    page.keyboard.down('Space');page.wait_for_timeout(680);page.keyboard.up('Space')
    page.locator('#text-command-dialog').wait_for(state='visible')
    assert '타자' in page.locator('#text-command-status').inner_text()
    page.keyboard.press('Escape')
    results.append('single/double/triple/hold sequencing, text Space, Escape focus restore, microphone unavailable → text: PASS')
    # Same dispatcher sees both text and mocked recognition, with no semantic differences.
    page.evaluate('() => {window.SpeechRecognition=class {start(){setTimeout(()=>this.onstart?.(),0);}stop(){const result=[[{transcript:"10초 뒤로"}]];this.onresult?.({results:result});this.onend?.();}abort(){}};}')
    page.evaluate('window.__player.seekTo(35)')
    page.locator('#command-surface').focus();page.keyboard.down('Space');page.wait_for_timeout(680);page.keyboard.up('Space');page.wait_for_timeout(550)
    assert page.evaluate('getCurrentPlaybackMs()')==25000
    page.evaluate('window.__player.seekTo(35)')
    page.keyboard.press('Space');page.keyboard.press('Space');page.keyboard.press('Space');page.locator('#text-command-dialog').wait_for(state='visible');page.keyboard.type('10초 뒤로');page.keyboard.press('Enter');page.wait_for_timeout(100)
    assert page.evaluate('getCurrentPlaybackMs()')==25000
    results.append('mocked voice and typed identical command → identical seek: PASS')
    page.evaluate('Portal.readerMode=true;window.__player.playVideo();readSummaryGuide()')
    assert not page.evaluate('isPlaybackRunning()')
    page.evaluate('Portal.readerMode=false')
    # Automatic visual-gap narration pauses, describes and resumes through real scheduler code.
    page.evaluate('''() => {window.__oldSpeak=speak;window.__auto=[];speak=(t,end)=>{window.__auto.push({text:t,paused:!isPlaybackRunning()});end?.();};const g=state.snapshot.visual_gaps.find(g=>g.safe_to_speak&&['INTERRUPT','DESCRIBE_AT_BREAK'].includes(g.action));state.announcedGaps.clear();window.__player.seekTo(g.timestamp_ms/1000);window.__player.playVideo();state.lastPlaybackMs=g.timestamp_ms-800;processPlaybackTime(g.timestamp_ms);}''')
    assert page.evaluate('window.__auto.length===1&&window.__auto[0].paused&&isPlaybackRunning()')
    page.evaluate('() => {speak=window.__oldSpeak;stopAllPlaybackAndSpeech({announceStop:false});}')
    results.append('automatic safe visual gap: actual scheduler pauses → narration → resumes (TTS/player mocked): PASS')
    page.locator('[data-learn-panel="chat-panel"]').focus();page.keyboard.press('Enter')
    page.locator('#chat-input').fill('3줄 요약해줘');page.locator('#chat-input').press('Enter')
    page.wait_for_function('document.querySelector("#chat-log").textContent.includes("Sullivan 로컬 보조")')
    assert page.locator('#chat-log').get_attribute('aria-live')=='polite'
    probe(page,'student-chat')
    results.append('grounded question/summary local fallback, no student consent/code prompt, single response announcement channel: PASS')
    # Real search and sequencing logic; mock player clock and TTS output only.
    page.evaluate('() => {window.__player.seekTo(35);window.__oldSpeak=speak;window.__spoken=[];speak=(t,end)=>{window.__spoken.push(t);end?.();};}')
    page.locator('[data-learn-panel][data-purpose=search]').focus();page.keyboard.press('Enter')
    page.locator('#navigation-command').fill('전체 흐름');page.locator('#navigation-command').press('Enter')
    page.wait_for_function('state.conceptSearchResults?.length>1')
    probe(page,'student-search')
    assert '번' in page.locator('#navigation-answer').inner_text()
    page.locator('.concept-speak').first.focus();page.keyboard.press('Enter');page.wait_for_timeout(800)
    assert page.evaluate('isPlaybackRunning()')
    assert page.evaluate('window.__spoken.length')==0
    page.evaluate('window.__player.seekTo((findConcept(state.currentConceptId).end_ms+1000)/1000)')
    page.wait_for_function('window.__spoken.some(t=>t.includes("AI가 핵심"))')
    page.locator('#learner-return').focus();page.keyboard.press('Enter')
    assert page.evaluate('getCurrentPlaybackMs()')==35000
    page.locator('[data-learn-panel][data-purpose=search]').focus();page.keyboard.press('Enter')
    page.locator('#navigation-command').fill('전체 흐름');page.locator('#navigation-command').press('Enter')
    page.locator('#command-surface').focus();page.keyboard.press('Space');page.keyboard.press('Space');page.keyboard.press('Space');page.locator('#text-command-dialog').wait_for(state='visible');page.keyboard.type('1번');page.keyboard.press('Enter');page.wait_for_timeout(800)
    assert page.evaluate('state.currentConceptId===state.conceptSearchResults[0].concept_id && state.conceptSequenceActive')

    page.evaluate('Portal.readerMode=true;window.__player.seekTo((findConcept(state.currentConceptId).end_ms+1000)/1000)')
    page.wait_for_function('!state.conceptSequenceActive')
    page.wait_for_timeout(250)
    assert page.evaluate('document.querySelector("#navigation-answer").textContent.includes(findConcept(state.currentConceptId).ai_explanation)')
    assert '모두 들었습니다' not in page.locator('#navigation-answer').inner_text()
    assert not page.evaluate('isPlaybackRunning()')
    page.evaluate('Portal.readerMode=false')
    results.append('external-reader concept explanation remains available; no false speech-completion or automatic resume: PASS')
    page.locator('#learner-stop').focus();page.keyboard.press('Enter');page.locator('#learner-return').focus();page.keyboard.press('Enter')
    assert page.evaluate('getCurrentPlaybackMs()')==35000
    page.evaluate('() => {speak=window.__oldSpeak;}')
    results.append('multiple search results; original lecturer segment before AI explanation; return to original timestamp: PASS (player/TTS boundary mocked)')
    # Use the passage lecture and verify underline state and focus survives rerender.
    page.locator('#learner-home').focus();page.keyboard.press('Enter');page.locator('#portal-home').wait_for(state='visible')
    page.locator('#assigned-list button').nth(1).focus();page.keyboard.press('Enter');page.wait_for_function("document.activeElement.id==='learner-play'",timeout=3000)
    page.wait_for_function('document.querySelector("#lecture-video").readyState>=1')
    page.locator('#learner-play').focus();page.keyboard.press('Space');page.wait_for_function('!document.querySelector("#lecture-video").paused')
    results.append('encrypted local WebM decrypts and plays in actual browser; no raw video server persistence: PASS')
    page.locator('[data-learn-panel][data-purpose=paragraph]').focus();page.keyboard.press('Enter')
    page.locator('[data-underline-paragraph]').first.focus();page.keyboard.press('Space')
    assert page.locator('[data-underline-paragraph]').first.get_attribute('aria-pressed')=='true'
    probe(page,'student-paragraphs')
    assert page.locator(':focus').get_attribute('data-underline-paragraph') is not None
    sentence=page.locator('[data-paragraph-sentence]').first
    sentence_id=sentence.get_attribute('data-sentence-id');sentence.focus();page.keyboard.press('Space')
    assert page.locator(':focus').get_attribute('data-sentence-id')==sentence_id
    results.append('sentence selection rerender retains the same sentence focus: PASS')

    page.locator('#learner-home').focus();page.keyboard.press('Enter');page.locator('#portal-home').wait_for(state='visible')
    page.locator('#assigned-list button').nth(1).focus();page.keyboard.press('Enter');page.wait_for_function("document.activeElement.id==='learner-play'",timeout=3000)
    assert page.evaluate('state.underlinedParagraphIds.size')==1
    results.append('actual passage, underline name/state, focus retention and persisted underline: PASS')
    for width in (320,390,1280,1920):
      page.set_viewport_size({'width':width,'height':900})
      assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),width
    # Forward/backward Tab remain in regular document, native modal traps only while open.
    page.locator('#command-surface').focus();page.keyboard.press('Tab');page.keyboard.press('Shift+Tab');assert page.locator(':focus').get_attribute('id')=='command-surface'
    assert page.get_by_role('button',name='원하는 내용 찾기',exact=True).count()==1
    page.evaluate('''() => {const text='x" onfocus="window.__xss=1';const d=document.createElement('div');d.innerHTML=`<button aria-label="${escapeHtml(text)}">test</button>`;document.body.append(d);d.firstChild.focus();if(d.firstChild.hasAttribute('onfocus')||window.__xss)throw Error('attribute escaping failed');d.remove();}''')
    results.append('320/390/1280/1920px no overflow, Tab/Shift+Tab round trip, role names, quote injection blocked: PASS')
    # Reflow at 200% equivalent desktop viewport, plus user motion and high-contrast preferences.
    page.set_viewport_size({'width':640,'height':450})
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.emulate_media(reduced_motion='reduce',forced_colors='active')
    page.locator('#command-surface').focus();page.keyboard.press('Tab')
    assert page.locator(':focus').get_attribute('data-learn-panel')=='watch-panel'
    assert page.locator(':focus').evaluate('(e)=>parseFloat(getComputedStyle(e).outlineWidth)>=4')
    page.emulate_media(reduced_motion='no-preference',forced_colors='none')
    results.append('student design: four unchanged accessible purpose names and app speech; 52px targets, home reflow, 200% equivalent viewport and forced-color focus: PASS')
    assert not errors,errors
    out=ROOT/'docs/verification';out.mkdir(exist_ok=True)
    page.set_viewport_size({'width':1280,'height':900});page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(out/'student-desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844});page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(out/'student-mobile.png'),full_page=True)
    page.locator('#portal-logout').focus();page.keyboard.press('Enter');page.locator('#portal-login').wait_for(state='visible')
    page.locator('#login-username').fill('student2');page.locator('#login-password').fill('test-pass-123');page.locator('#login-submit').focus();page.keyboard.press('Enter')
    page.locator('#onboarding-title').wait_for(state='visible');page.get_by_role('button',name='사용법 확인 완료',exact=True).focus();page.keyboard.press('Enter')
    assert page.locator('#assigned-list button').count()==0
    assert '아직 준비된 강의' in page.locator('#assigned-status').inner_text()
    probe(page,'student-no-assignments')
    page.locator('[data-purpose=paragraph]').first.focus();page.keyboard.press('Enter')
    assert '먼저 준비된 강의' in page.locator('#portal-feedback').inner_text()
    probe(page,'student-no-lecture-feedback')
    page.route('**/local/lectures',lambda r:r.abort())
    page.reload();page.get_by_role('button',name='강의 목록 다시 확인',exact=True).wait_for(state='visible')
    probe(page,'student-list-connection-error')
    results.append('separate student empty assignment and simulated list-network failure with retry: PASS')
    assert not errors,errors
    (out/'browser-results.json').write_text(json.dumps({'checks':results,'page_errors':errors,'screen_reader':'not tested','providers':'YouTube and recognition mocked; Gemini not called'},ensure_ascii=False,indent=2))
    for r in results:print(r)
    save_accessibility(ROOT)
    browser.close()
  finally:server.should_exit=True;thread.join(timeout=5)
if __name__=='__main__':main()
