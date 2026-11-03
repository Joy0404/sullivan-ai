"""Isolated HTTP/browser checks; manually completed speech and mock YouTube, no paid calls."""
from pathlib import Path
import json, os, socket, sys, tempfile, threading, time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/api'))
import uvicorn
from playwright.sync_api import sync_playwright, expect
from verify_roles_browser import MOCK

SPEECH = '''window.__speeches=[];window.__manualSpeech=false;
speechSynthesis.resume=()=>{};speechSynthesis.cancel=()=>{};
speechSynthesis.speak=u=>{
 window.__speeches.push({text:u.text,playing:isPlaybackRunning()});window.__activeSpeech=u;
 if(window.__failSpeech){u.onerror?.({error:'not-allowed'});return;}
 if(window.__stallSpeech)return;
 u.onstart?.();if(!window.__manualSpeech)u.onend?.();
};
window.__finishSpeech=()=>{const u=window.__activeSpeech;window.__activeSpeech=null;u?.onend?.();};'''

def main():
 with tempfile.TemporaryDirectory(prefix='sullivan-audio-nav-') as tmp:
  os.environ.update(SULLIVAN_ACCOUNTS_DB=str(Path(tmp)/'accounts.sqlite'), SULLIVAN_ROLE_AUTH='1', GEMINI_API_KEY='')
  for key in ['DATABASE_URL','DATABASE_URL_UNPOOLED','RENDER']:os.environ.pop(key,None)
  from app.main import app
  sock=socket.socket();sock.bind(('127.0.0.1',0));base=f'http://127.0.0.1:{sock.getsockname()[1]}'
  server=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False))
  thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
  while not server.started:time.sleep(.01)
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch();context=browser.new_context()
    context.add_init_script(MOCK.replace("this.frame.src='about:blank'", "this.frame.src='https://player-test.invalid/embed'")+SPEECH)
    api=context.request;headers={'X-Local-Request':'1'}
    assert api.post(base+'/local/setup',headers=headers,data={'username':'guardian','password':'test-pass-123'}).status==200
    student=api.post(base+'/local/students',headers=headers,data={'username':'student','password':'test-pass-123','name':'학생'}).json()['id']
    api.put(base+'/local/students/'+student+'/settings',headers=headers,data={'focus_voice':True,'auto_description':False})
    result=api.post(base+'/local/samples/science/assign',headers=headers,data={'students':[student]})
    # Use the same atomic preparation/assignment endpoint as the guardian form.
    assert result.status==200,result.text
    api.post(base+'/local/logout',headers=headers)
    assert api.post(base+'/local/login',headers=headers,data={'username':'student','password':'test-pass-123','role':'student'}).status==200
    api.post(base+'/local/onboarding',headers=headers,data={})
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def route(r):
     if r.request.url.startswith(base):r.continue_()
     elif r.request.url=='https://player-test.invalid/embed':r.fulfill(content_type='text/html',body='<title>mock player</title>'+''.join(f'<button>영상 내부 {i}</button>' for i in range(12)))
     else:r.abort()
    page.route('**/*',route);page.goto(base)
    page.locator('#assigned-list button').first.press('Enter');expect(page.locator('#learner-play')).to_be_focused()
    page.wait_for_function('document.querySelector("#lecture-youtube").tagName==="IFRAME"')
    page.wait_for_timeout(240)
    page.evaluate('window.__manualSpeech=true;__player.t=45;__player.playVideo()')
    page.locator('#learner-describe').focus();page.wait_for_function('SullivanFocusVoice.holdsPlayback()')
    assert page.evaluate('!isPlaybackRunning() && __speeches.at(-1).playing===false')
    expect(page.locator('#learner-play')).to_have_text('강의 일시정지')
    page.evaluate('__finishSpeech()');assert page.evaluate('isPlaybackRunning()&&!SullivanFocusVoice.holdsPlayback()')
    # A provider's delayed pause must be acknowledged before any label is spoken.
    page.evaluate('''window.__normalPause=__player.pauseVideo.bind(__player);window.__pauseRequested=false;
      __player.pauseVideo=()=>{if(!__pauseRequested){__pauseRequested=true;setTimeout(__normalPause,260);}};
      window.__speechCount=__speeches.length;''')
    page.locator('#learner-stop').focus();page.wait_for_timeout(220)
    assert page.evaluate('isPlaybackRunning()&&__speeches.length===__speechCount')
    page.wait_for_function('__speeches.length>__speechCount')
    assert page.evaluate('__speeches.at(-1).playing===false')
    page.evaluate('__player.pauseVideo=__normalPause;__finishSpeech()')
    # A provider that never pauses must not be talked over.
    page.evaluate('__player.pauseVideo=()=>{};window.__speechCount=__speeches.length')
    page.locator('#learner-describe').focus();expect(page.locator('#focus-voice-status')).to_contain_text('안내를 보류',timeout=3500)
    assert page.evaluate('__speeches.length===__speechCount&&!SullivanFocusVoice.holdsPlayback()')
    page.evaluate('__player.pauseVideo=__normalPause')
    # Already-paused lectures never start merely because a label finished.
    page.evaluate('pausePlayback()');page.locator('#learner-stop').focus();page.wait_for_timeout(220)
    page.evaluate('__finishSpeech()');assert not page.evaluate('isPlaybackRunning()')
    # Moving quickly keeps one pause; an old completion cannot resume over a new label.
    page.evaluate('__player.playVideo()');page.locator('#learner-describe').focus();page.wait_for_function('SullivanFocusVoice.holdsPlayback()')
    page.evaluate('window.__staleEnd=__activeSpeech.onend');page.locator('#learner-stop').focus();page.wait_for_timeout(220)
    page.evaluate('__staleEnd()');assert not page.evaluate('isPlaybackRunning()')
    page.evaluate('__finishSpeech()');assert page.evaluate('isPlaybackRunning()')
    # Pause activation during a temporary announcement means pause, not play.
    page.locator('#learner-play').focus();page.wait_for_function('SullivanFocusVoice.holdsPlayback()')
    page.evaluate('window.__staleEnd=__activeSpeech.onend');page.keyboard.press('Enter');page.evaluate('__staleEnd()')
    assert page.evaluate('!isPlaybackRunning()&&!SullivanFocusVoice.holdsPlayback()')
    page.evaluate('__player.playVideo()');page.locator('#learner-describe').focus();page.wait_for_function('SullivanFocusVoice.holdsPlayback()')
    page.evaluate('window.__staleEnd=__activeSpeech.onend');page.locator('#learner-stop').press('Enter');page.evaluate('__staleEnd()')
    assert not page.evaluate('isPlaybackRunning()')
    # Label failure and a missing start callback release the temporary pause.
    page.evaluate('__player.playVideo();window.__failSpeech=true');page.locator('#learner-describe').focus();page.wait_for_timeout(240)
    assert page.evaluate('isPlaybackRunning()&&!SullivanFocusVoice.holdsPlayback()')
    page.evaluate('window.__failSpeech=false;window.__stallSpeech=true');page.locator('#learner-stop').focus()
    page.wait_for_function('SullivanFocusVoice.holdsPlayback()');page.wait_for_timeout(1900)
    assert page.evaluate('isPlaybackRunning()&&!SullivanFocusVoice.holdsPlayback()')
    page.evaluate('window.__stallSpeech=false')
    # Arrow movement shares button behavior and does not move focus or overlap speech.
    page.locator('#command-surface').focus();page.evaluate('__player.t=45')
    page.keyboard.press('ArrowLeft');assert page.evaluate('__player.t===35&&!isPlaybackRunning()'),page.evaluate('({time:__player.t,playing:isPlaybackRunning(),hold:SullivanFocusVoice.holdsPlayback(),last:__speeches.at(-1),modal:document.querySelector(\'dialog[open],[aria-modal="true"]:not(.hidden)\')?.outerHTML,focus:document.activeElement.outerHTML})')
    expect(page.locator('#command-surface')).to_be_focused();page.evaluate('__finishSpeech()')
    assert page.evaluate('isPlaybackRunning()');page.keyboard.press('ArrowRight');assert page.evaluate('__player.t===45')
    page.evaluate('__finishSpeech();__player.t=2');page.keyboard.press('ArrowLeft');assert page.evaluate('__player.t===0')
    page.evaluate('__finishSpeech()')
    # Modifiers, text carets, selects and native command dialogs retain their keys.
    before=page.evaluate('__player.t');page.keyboard.press('Shift+ArrowRight');page.keyboard.press('Control+ArrowRight')
    assert page.evaluate('__player.t')==before
    page.locator('[data-learn-panel=chat-panel]').press('Enter');page.wait_for_timeout(220);page.evaluate('__finishSpeech()')
    page.locator('#chat-input').fill('abc');page.keyboard.press('ArrowLeft')
    assert page.locator('#chat-input').evaluate('(e)=>e.selectionStart')==2
    assert page.evaluate('__player.t')==before
    page.locator('#student-preferences summary').press('Enter');page.locator('#speech-volume').focus();page.keyboard.press('ArrowLeft')
    assert page.evaluate('__player.t')==before
    page.locator('#command-surface').focus()
    for _ in range(3):page.keyboard.press('Space')
    expect(page.locator('#text-command-input')).to_be_focused();page.keyboard.press('ArrowLeft')
    assert page.evaluate('__player.t')==before
    page.keyboard.press('Escape');expect(page.locator('#command-surface')).to_be_focused()
    # Native Tab, Shift+Tab and Shift alone each skip twelve cross-origin controls.
    page.locator('[data-learn-panel=watch-panel]').press('Enter')
    page.evaluate('''const stage=document.querySelector('.video-stage');
      for(const [id,position] of [['test-before','beforebegin'],['test-after','afterend']]){
       const b=document.createElement('button');b.id=id;b.textContent=id;stage.insertAdjacentElement(position,b);
      }''')
    assert page.locator('.video-stage').evaluate('(e)=>e.inert')
    assert page.locator('#lecture-youtube').get_attribute('tabindex')=='-1'
    page.locator('#test-before').focus();page.keyboard.press('Tab');expect(page.locator('#test-after')).to_be_focused()
    page.keyboard.press('Shift');expect(page.locator('#test-before')).to_be_focused()
    page.locator('#test-after').focus();page.keyboard.press('Shift+Tab');expect(page.locator('#test-before')).to_be_focused()
    page.evaluate('document.querySelector("#lecture-video").classList.remove("hidden")')
    assert not page.locator('#lecture-video').evaluate('(e)=>e.controls')
    page.locator('#test-before').focus();page.keyboard.press('Tab');expect(page.locator('#test-after')).to_be_focused()
    page.evaluate('document.querySelectorAll("#test-before,#test-after").forEach(e=>e.remove())')
    # Exercise native browser video pause/resume as well as the SDK boundary.
    page.evaluate('''async()=>{
      pausePlayback();state.linkedPlaybackKind='local';const canvas=document.createElement('canvas');
      canvas.width=160;canvas.height=90;window.__localStream=canvas.captureStream(10);
      window.__drawing=setInterval(()=>canvas.getContext('2d').fillRect(0,0,160,90),50);
      const video=document.querySelector('#lecture-video');video.srcObject=__localStream;await video.play();
    }''')
    page.locator('#learner-describe').focus();page.wait_for_function('SullivanFocusVoice.holdsPlayback()')
    assert page.locator('#lecture-video').evaluate('(e)=>e.paused')
    page.evaluate('__finishSpeech()');page.wait_for_function('!document.querySelector("#lecture-video").paused')
    page.evaluate('''pausePlayback();clearInterval(__drawing);__localStream.getTracks().forEach(t=>t.stop());
      document.querySelector('#lecture-video').srcObject=null;state.linkedPlaybackKind='youtube';''')
    # Replacing a previous AI explanation must not leave a stale speech token.
    page.evaluate('speak("기존 해설")');page.wait_for_function('__activeSpeech?.text==="기존 해설"')
    page.locator('#learner-stop').focus();page.wait_for_timeout(240)
    assert page.evaluate('!state.speechInProgress&&__activeSpeech.text.includes("영상, 해설 모두 중지")')
    page.evaluate('__finishSpeech()');expect(page.locator('#focus-voice-status')).to_contain_text('처리가 끝났')
    # External readers pause on focus, and wait for an explicit resume.
    page.evaluate('SullivanFocusVoice.cancel();Portal.focusVoice=false;Portal.readerMode=true;__player.playVideo()')
    page.locator('#learner-describe').focus();assert not page.evaluate('isPlaybackRunning()')
    page.wait_for_timeout(240);assert not page.evaluate('isPlaybackRunning()')
    page.locator('#learner-play').press('Enter');assert page.evaluate('isPlaybackRunning()')
    # Navigating home revokes the old notice's permission to resume.
    page.evaluate('Portal.readerMode=false;Portal.focusVoice=true');page.locator('#learner-stop').focus()
    page.wait_for_function('SullivanFocusVoice.holdsPlayback()');page.evaluate('window.__staleEnd=__activeSpeech.onend')
    page.locator('#learner-home').press('Enter');expect(page.locator('#portal-home')).to_be_visible();page.evaluate('__staleEnd()')
    assert not page.evaluate('isPlaybackRunning()')
    # Guardian media interaction is restored on the same browser after role change.
    api.post(base+'/local/logout',headers=headers);api.post(base+'/local/login',headers=headers,data={'username':'guardian','password':'test-pass-123','role':'guardian'})
    page.reload();page.locator('#guardian-prepare').wait_for();page.wait_for_function('document.querySelector("#guardian-dashboard").getAttribute("aria-busy")==="false"')
    page.locator('#guardian-science').press('Enter');page.locator('#guardian-publish').wait_for()
    assert not page.locator('.video-stage').evaluate('(e)=>e.inert')
    assert page.locator('#lecture-video').evaluate('(e)=>e.controls')
    assert not errors,errors
    result={'notice_pauses_before_speech_and_resumes':True,'waits_for_delayed_provider_pause':True,
      'unconfirmed_provider_pause_withholds_speech':True,'paused_lecture_stays_paused':True,
      'rapid_navigation_ignores_stale_completion':True,'explicit_pause_stop_and_home_prevent_resume':True,
      'speech_failure_and_start_timeout_release_hold':True,'arrow_seek_and_start_boundary':True,
      'editing_select_modifiers_dialog_preserved':True,'native_tab_shift_and_shift_tab_skip_embedded_controls':True,
      'native_video_controls_skipped':True,'guardian_controls_restored':True,'external_reader_requires_explicit_resume':True,
      'actual_native_video_pause_resume':True,'replaces_prior_explanation_without_stale_token':True,
      'page_errors':errors,'actual_screen_reader_and_heard_audio':'not tested',
      'providers':'YouTube/TTS mocked; twelve controls in a real cross-origin iframe fixture; no Gemini calls'}
    (ROOT/'docs/verification/audio-navigation-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False));browser.close()
  finally:server.should_exit=True;thread.join(timeout=5)

if __name__=='__main__':main()
