"""Installed extension regression: keyboard contract, app narration and real side-panel DOM.

Speech/provider inputs are explicit test doubles; video playback and Chrome panel are real.
"""
import json
import time
from playwright.sync_api import expect
from verify_extensions_browser import main,check_layout
from verify_extensions_phase3 import exercise as phase3,SPEECH
from verify_extensions_phase4 import exercise as phase4


def taps(page,count):
    for _ in range(count):page.keyboard.press('Space',delay=35)


def media_checks(guardian,student,output):
    expect(student.locator('#space-enabled')).to_be_checked()
    assert student.locator('[name=invite],[name=access_code]').count()==0
    assert guardian.locator('[name=invite],[name=access_code]').count()==0
    student.locator('#bookmark').focus()
    before=student.locator('#bookmarks li').count()
    taps(student,1)
    student.wait_for_function("() => !document.querySelector('#local-video').paused")
    assert student.locator('#bookmarks li').count()==before
    taps(student,1);student.wait_for_function("() => document.querySelector('#local-video').paused")
    student.evaluate('window.__holdSpeech=true')
    before_speech=student.evaluate('window.__spoken.length')
    student.locator('#read').click();expect(student.locator('#current-description')).to_contain_text('문단')
    student.wait_for_function('(n)=>window.__spoken.length>n',arg=before_speech)
    student.evaluate('window.__stale=window.__spoken.at(-1)')
    taps(student,2);expect(student.locator('#status')).to_contain_text('모두 중지')
    student.evaluate('window.__stale.onend?.();window.__holdSpeech=false')
    assert student.evaluate("document.querySelector('#local-video').paused")
    student.locator('#bookmark').focus();taps(student,3);expect(student.locator('#text-dialog')).to_be_visible()
    expect(student.locator('#text-command')).to_be_focused()
    student.locator('#text-command').fill('10초 앞으로')
    student.keyboard.press('Enter');expect(student.locator('#text-dialog')).to_be_hidden()
    expect(student.locator('#status')).to_contain_text('위치로 이동')
    # Real 3-second threshold with a synthetic recognizer, not a claimed live microphone test.
    student.locator('#voice-consent').check()
    student.evaluate("""() => {window.SpeechRecognition=class {
      start(){window.__voiceStarted=(window.__voiceStarted||0)+1;window.__recognition=this;this.onstart?.();}
      stop(){this.onresult?.({results:[[{transcript:'영상 중지'}]]});this.onend?.();}
      abort(){}
    };}""")
    student.locator('#bookmark').focus();student.keyboard.down('Space')
    student.wait_for_timeout(2700)
    assert student.evaluate('window.__voiceStarted||0')==0
    student.wait_for_function('() => window.__voiceStarted===1',timeout=1200)
    student.keyboard.up('Space');expect(student.locator('#status')).to_contain_text('모두 중지')
    student.locator('#voice-consent').uncheck()
    student.locator('#bookmark').focus();student.keyboard.down('Space')
    expect(student.locator('#voice-permission-dialog')).to_be_visible(timeout=4000);student.keyboard.up('Space')
    student.evaluate("""() => {window.__getMedia=navigator.mediaDevices.getUserMedia;
      navigator.mediaDevices.getUserMedia=()=>new Promise(resolve=>window.__resolveMic=resolve);}""")
    student.locator('#allow-voice').click();student.keyboard.press('Escape')
    student.evaluate("() => window.__resolveMic({getTracks:()=>[{stop(){window.__micStopped=true;}}]})")
    student.wait_for_function('() => window.__micStopped===true')
    assert student.evaluate('window.__voiceStarted')==1
    expect(student.locator('#text-dialog')).to_be_hidden()
    student.evaluate('() => {navigator.mediaDevices.getUserMedia=window.__getMedia;}')
    student.locator('#voice-consent').uncheck()
    # Scope includes all controls, keeps natural order from a heading and has an explicit exit.
    student.locator('#lesson-title').focus();student.keyboard.press('Tab')
    expect(student.get_by_role('link',name='강의 조작',exact=True)).to_be_focused()
    student.locator('#voice-test').focus();student.keyboard.press('Tab');expect(student.locator('#panel-keyboard')).to_be_focused()
    student.keyboard.press('Shift');expect(student.locator('#voice-test')).to_be_focused()
    student.keyboard.press('Shift+Tab');expect(student.locator('#access-mode')).to_be_focused()
    student.locator('#note').fill('입력 중');student.locator('#note').focus()
    student.keyboard.press('Shift');expect(student.locator('#note')).to_be_focused()
    student.keyboard.press('End');student.keyboard.press('Space');expect(student.locator('#note')).to_have_value('입력 중 ')
    first=student.locator('.skip');last=student.locator('main > details > summary')
    last.focus();student.keyboard.press('Tab');expect(first).to_be_focused()
    first.focus();student.keyboard.press('Shift+Tab');expect(last).to_be_focused()
    taps(student,3);expect(student.locator('#text-dialog')).to_be_visible()
    student.locator('#close-dialog').focus();student.keyboard.press('Tab');expect(student.locator('#text-command')).to_be_focused()
    student.keyboard.press('Escape');expect(student.locator('#text-dialog')).to_be_hidden()
    student.keyboard.press('Escape');expect(student.locator('#status')).to_contain_text('해제')
    student.locator('#panel-keyboard').click()
    # App guidance works without touching the selected media and never reads password values.
    student.locator('#access-mode').select_option('app')
    student.evaluate('window.__spoken=[]')
    student.locator('#voice-test').click()
    student.wait_for_function("() => window.__spoken.some(u=>u.text.includes('학생 음성 안내'))")
    student.locator('#note').focus()
    student.wait_for_function("() => window.__spoken.some(u=>u.text.includes('내 메모'))")
    student.locator('#access-mode').select_option('reader')
    count=student.evaluate('window.__spoken.length')
    student.locator('#read').click();expect(student.locator('#reader-description')).not_to_be_empty()
    assert student.evaluate('window.__spoken.length')==count
    student.locator('#access-mode').select_option('app')
    student.locator('#voice-consent').uncheck()
    check_layout(student,'student-keyboard-repair',output)
    # Preserve the starting media state expected by the cumulative regression.
    student.locator('#stop').click()


class Target:
    def __init__(self,root,ident,pump):
        self.root,self.pump,self.seq,self.replies=root,pump,0,{}
        self.session=root.send('Target.attachToTarget',{'targetId':ident,'flatten':False})['sessionId']
        def receive(event):
            if event.get('sessionId')==self.session:
                message=json.loads(event['message'])
                if 'id' in message:self.replies[message['id']]=message
        root.on('Target.receivedMessageFromTarget',receive)
    def send(self,method,params=None):
        self.seq+=1;ident=self.seq
        self.root.send('Target.sendMessageToTarget',{'sessionId':self.session,'message':json.dumps({'id':ident,'method':method,'params':params or {}})})
        deadline=time.monotonic()+10
        while ident not in self.replies:
            if time.monotonic()>deadline:raise RuntimeError('Panel CDP request timed out: '+method)
            self.pump.wait_for_timeout(10)
        result=self.replies.pop(ident)
        if 'error' in result:raise RuntimeError(result['error'])
        return result.get('result',{})
    def evaluate(self,expression):
        result=self.send('Runtime.evaluate',{'expression':expression,'returnByValue':True,'awaitPromise':True})
        if 'exceptionDetails' in result:raise RuntimeError(result['exceptionDetails'])
        return result['result'].get('value')
    def key(self,key,code=None,modifiers=0):
        for kind in ('keyDown','keyUp'):self.send('Input.dispatchKeyEvent',{'type':kind,'key':key,'code':code or key,'modifiers':modifiers,'windowsVirtualKeyCode':9 if key=='Tab' else 27 if key=='Escape' else 16})


def native_panel(student):
    context=student.context
    root=context.browser.new_browser_cdp_session()
    before={t['targetId'] for t in root.send('Target.getTargets')['targetInfos']}
    student.evaluate("""async()=>{
      const win=await chrome.windows.getCurrent();const b=document.createElement('button');b.id='verify-native-panel';b.textContent='검사용 학습 패널 열기';
      b.onclick=()=>chrome.sidePanel.open({windowId:win.id});document.body.append(b);
    }""")
    student.locator('#verify-native-panel').click()
    deadline=time.monotonic()+10
    while True:
        targets=root.send('Target.getTargets')['targetInfos']
        target=next((t for t in targets if t['targetId'] not in before and t['url'].startswith(student.url.split('index.html')[0])),None)
        if target:break
        if time.monotonic()>deadline:raise RuntimeError('Actual Chrome side panel did not appear')
        student.wait_for_timeout(50)
    panel=Target(root,target['targetId'],student)
    deadline=time.monotonic()+10
    while not panel.evaluate("Boolean(document.querySelector('#workspace')&&!document.querySelector('#workspace').hidden)"):
        if time.monotonic()>deadline:raise RuntimeError('Native panel account restore timed out')
        student.wait_for_timeout(50)
    student.evaluate("() => chrome.runtime.sendMessage({type:'student-focus-panel'}).catch(()=>{})")
    assert panel.evaluate('document.activeElement.id')=='workspace-title'
    panel.evaluate("document.querySelector('#voice-test').focus()")
    panel.key('Tab');assert panel.evaluate('document.activeElement.id')=='panel-keyboard'
    panel.key('Tab',modifiers=8);assert panel.evaluate('document.activeElement.id')=='voice-test'
    panel.evaluate("document.querySelector('.skip').focus()")
    panel.key('Tab',modifiers=8);assert panel.evaluate("document.activeElement.matches('main > details > summary')")
    panel.key('Tab');assert panel.evaluate("document.activeElement.matches('.skip')")
    panel.key('Escape');assert '해제' in panel.evaluate("document.querySelector('#status').textContent")
    panel.evaluate("document.querySelector('#panel-keyboard').click()")
    panel.evaluate("(async()=>{if(chrome.sidePanel.close)await chrome.sidePanel.close({windowId:(await chrome.windows.getCurrent()).id});})()")
    root.detach()
    student.locator('#verify-native-panel').evaluate('(node)=>node.remove()')


def exercise(guardian,student,output):
    phase3.student_check=media_checks
    guardian=phase4(guardian,student,output)
    native_panel(student)
    # Logged-out focus still receives app guidance.
    student.locator('#logout').click();expect(student.locator('#auth')).to_be_visible()
    student.evaluate(SPEECH);student.locator('#access-mode').select_option('app')
    student.locator('#access-mode').focus();student.locator('#username').focus();student.wait_for_function("() => window.__spoken.some(u=>u.text.includes('로그인 이름'))")
    student.locator('#password').fill('never-read-this-password');student.locator('#password').focus()
    assert not student.evaluate("window.__spoken.some(u=>u.text.includes('never-read-this-password'))")
    student.locator('#username').fill('student');student.locator('#password').fill('extension-pass-123');student.locator('#login-form button').click()
    expect(student.locator('#workspace')).to_be_visible()
    return guardian


exercise.checks=phase4.checks+['single Space toggles video without clicking focused control','double Space cancels stale speech',
    'triple Space opens typed command and executes seek','voice starts after 3000ms and executes transcript on release (recognizer stub)',
    'Tab/Shift+Tab/standalone Shift scope and explicit Escape exit','actual Chrome side-panel target keyboard containment',
    'app speech before login and on named fields, no password speech','external-reader output without app TTS','no administrator/invite/analysis code fields']

if __name__=='__main__':main(exercise,phase='student-repair')
