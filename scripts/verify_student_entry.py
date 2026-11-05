"""Reproduce cued-YouTube seek autoplay and measure student preference controls."""
from pathlib import Path
import json,os,socket,sys,tempfile,threading,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps/api'))
import uvicorn
from playwright.sync_api import sync_playwright,expect
from verify_roles_browser import MOCK

# Unlike the earlier paused-only mock, this models the documented CUED behavior:
# seekTo starts playback unless paused; cueVideoById waits for explicit play.
PLAYER=MOCK+'''const BasePlayer=YT.Player;
YT.Player=class extends BasePlayer {
 constructor(...args){super(...args);this.s=5;this.queued=null;this.log=[];}
 cueVideoById({videoId,startSeconds=0}){this.log.push('cue');this.queued=startSeconds;this.t=0;this.s=5;this.c.events.onStateChange({data:5});}
 getCurrentTime(){return this.s===5?0:super.getCurrentTime();}
 seekTo(t){this.log.push('seek');super.seekTo(t);if(this.s!==2)this.playVideo();}
 playVideo(){this.log.push('play');if(this.queued!==null){this.t=this.queued;this.queued=null;}super.playVideo();}
};
speechSynthesis.resume=()=>{};speechSynthesis.cancel=()=>{};
speechSynthesis.speak=u=>{u.onstart?.();u.onend?.();};'''

def main():
 baseline=os.getenv('SULLIVAN_ENTRY_BASELINE')=='1'
 with tempfile.TemporaryDirectory(prefix='sullivan-student-entry-') as tmp:
  os.environ.update(SULLIVAN_ACCOUNTS_DB=str(Path(tmp)/'accounts.sqlite'),SULLIVAN_ROLE_AUTH='1',GEMINI_API_KEY='')
  for key in ['DATABASE_URL','DATABASE_URL_UNPOOLED','RENDER']:os.environ.pop(key,None)
  from app.main import app
  sock=socket.socket();sock.bind(('127.0.0.1',0));base=f'http://127.0.0.1:{sock.getsockname()[1]}'
  server=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False))
  thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
  while not server.started:time.sleep(.01)
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch();context=browser.new_context();context.add_init_script(PLAYER)
    api=context.request;headers={'X-Local-Request':'1'}
    assert api.post(base+'/local/setup',headers=headers,data={'username':'guardian','password':'test-pass-123'}).status==200
    student=api.post(base+'/local/students',headers=headers,data={'username':'student','password':'test-pass-123','name':'학생'}).json()['id']
    api.put(base+'/local/students/'+student+'/settings',headers=headers,data={'focus_voice':False,'auto_description':False})
    assert api.post(base+'/local/samples/science/assign',headers=headers,data={'students':[student]}).status==200
    api.post(base+'/local/logout',headers=headers)
    assert api.post(base+'/local/login',headers=headers,data={'username':'student','password':'test-pass-123','role':'student'}).status==200
    api.post(base+'/local/onboarding',headers=headers,data={})
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort())
    page.goto(base);page.locator('#assigned-list button').first.press('Enter');expect(page.locator('#learner-play')).to_be_focused()
    first={'playing':page.evaluate('isPlaybackRunning()'),'calls':page.evaluate('__player.log')}
    if not baseline:
     assert not first['playing'] and 'play' not in first['calls'],first
     position=page.evaluate('getCurrentPlaybackMs()');page.wait_for_timeout(3100)
     assert not page.evaluate('isPlaybackRunning()') and page.evaluate('getCurrentPlaybackMs()')==position
     first['paused_after_3_seconds']=True
    # Open via both native activation keys, including a restored non-zero position.
    page.locator('#learner-home').press('Enter');expect(page.locator('#portal-home')).to_be_visible()
    lecture=api.get(base+'/local/lectures').json()[0]['id']
    assert api.put(base+'/local/lectures/'+lecture+'/progress',headers=headers,data={'position_ms':92000,'bookmarks':[],'underlined':[],'note':''}).status==200
    # Reconnect with the saved server position; the previous tab must not save
    # its own older local position over the fixture before opening the lesson.
    page.reload();page.locator('#assigned-list button').first.wait_for()
    page.locator('#assigned-list button').first.press('Space');expect(page.locator('#learner-play')).to_be_focused()
    restored={'playing':page.evaluate('isPlaybackRunning()'),'position_ms':page.evaluate('getCurrentPlaybackMs()'),'calls':page.evaluate('__player.log')}
    if not baseline:
     assert not restored['playing'] and restored['position_ms']==92000 and 'seek' not in restored['calls'],restored
     page.wait_for_timeout(3100)
     assert not page.evaluate('isPlaybackRunning()') and page.evaluate('getCurrentPlaybackMs()')==92000
     restored['paused_after_3_seconds']=True
     page.evaluate('Portal.saveProgress()')
     assert api.get(base+'/local/lectures/'+lecture).json()['progress']['position_ms']==92000
     page.keyboard.press('ArrowRight');assert not page.evaluate('isPlaybackRunning()')
     assert page.evaluate('getCurrentPlaybackMs()')==102000
     page.locator('#learner-play').press('Enter');assert page.evaluate('isPlaybackRunning()&&getCurrentPlaybackMs()===102000')
     page.locator('#learner-stop').press('Enter');assert not page.evaluate('isPlaybackRunning()')
    page.locator('#student-preferences summary').press('Enter')
    out=ROOT/'docs/verification';out.mkdir(parents=True,exist_ok=True)
    layouts=[]
    for width in [320,390,640,1280]:
     page.set_viewport_size({'width':width,'height':900})
     layout=page.evaluate('''()=>{
      const root=document.querySelector('#student-preferences');
      const controls=[...root.querySelectorAll('input,select,button')].filter(e=>e.getClientRects().length);
      const boxes=controls.map(e=>({id:e.id,box:e.getBoundingClientRect().toJSON()}));
      const overlaps=[];
      for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){
       const a=boxes[i],b=boxes[j];
       if(Math.min(a.box.right,b.box.right)-Math.max(a.box.left,b.box.left)>.5&&Math.min(a.box.bottom,b.box.bottom)-Math.max(a.box.top,b.box.top)>.5)overlaps.push([a.id,b.id]);
      }
      const checks=controls.filter(e=>e.type==='checkbox').map(e=>({id:e.id,width:e.getBoundingClientRect().width,padding:getComputedStyle(e).padding}));
      return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,overlaps,checks,testButtonBackground:getComputedStyle(document.querySelector('#focus-voice-test')).backgroundColor};
     }''')
     layouts.append(layout)
     if width in [390,1280]:page.locator('#student-preferences').screenshot(path=str(out/f'student-entry-{"before" if baseline else "after"}-preferences-{width}.png'))
     if not baseline:
      assert not layout['overflow'] and not layout['overlaps'],layout
      assert all(c['width']<=24.5 and c['padding']=='0px' for c in layout['checks']),layout
      assert layout['testButtonBackground']!='rgb(239, 239, 239)',layout
    if not baseline:
     # Click the actual text, then toggle with Space. Names and native state stay exposed.
     option=page.locator('label[for=focus-voice] span');option.click();expect(page.locator('#focus-voice')).to_be_checked()
     page.locator('#focus-voice').focus();page.keyboard.press('Space');expect(page.locator('#focus-voice')).not_to_be_checked()
     page.locator('#speech-rate').focus();page.keyboard.press('ArrowDown')
     page.locator('#student-preferences summary').press('Enter')
     page.locator('[data-learn-panel=chat-panel]').press('Enter')
     for width in [320,390,1280]:
      page.set_viewport_size({'width':width,'height':900})
      assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
      checkbox=page.locator('#auto-speak-chat');expect(checkbox).to_have_accessible_name('AI 응답 자동으로 듣기')
      assert checkbox.bounding_box()['width']<=24.5
     assert not errors,errors
    result={'baseline':baseline,'initial_entry':first,'restored_entry':restored,'preference_layouts':layouts,'page_errors':errors,
      'scope':'real Chromium and temporary accounts; documented YouTube CUED behavior simulated; no actual screen reader or live provider/audio'}
    (out/f'student-entry-{"before" if baseline else "results"}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False));browser.close()
  finally:server.should_exit=True;thread.join(timeout=5)

if __name__=='__main__':main()
