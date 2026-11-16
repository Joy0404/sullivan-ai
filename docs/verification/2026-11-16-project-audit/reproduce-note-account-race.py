import sys,json,os
from pathlib import Path
sys.path.insert(0,'scripts')
import verify_extensions_browser as b
from verify_reaudit_fixes import request,Complete
from playwright.sync_api import expect
out=Path('docs/verification/2026-11-16-project-audit/note-race-confirm');out.mkdir(parents=True,exist_ok=True)
os.environ['SULLIVAN_AXE_SOURCE']='/tmp/sullivan-extension-a11y/node_modules/axe-core/axe.min.js'
result={}
def exercise(g,s,output):
    original=request(s,'/local/me')['id']
    second=request(g,'/local/students','POST',{'name':'Race Second Student','username':'race-second','password':'extension-pass-123'})['id']
    assigned=request(g,'/local/samples/science/assign','POST',{'students':[second]})
    old_lecture=request(s,'/local/lectures')[0]['id']
    s.locator('#note').fill('PRIVATE_FIRST_STUDENT_AUDIT_MARKER')
    s.locator('#progress-form button').click()
    expect(s.locator('#status')).to_have_text('학습 위치와 메모를 저장했습니다.')
    s.evaluate("""async()=>{const {StudentMedia}=await import('./media.js');const original=StudentMedia.prototype.pause;window.__holdNextPause=true;StudentMedia.prototype.pause=async function(...args){const result=await original.apply(this,args);if(window.__holdNextPause){window.__holdNextPause=false;window.__pauseHeld=true;await new Promise(resolve=>window.__releaseNotePause=resolve);}return result;};}""")
    s.locator('#import-legacy-note').click();s.wait_for_function('window.__pauseHeld===true')
    s.locator('#logout').click();expect(s.locator('#auth')).to_be_visible()
    s.locator('#username').fill('race-second');s.locator('#password').fill('extension-pass-123');s.locator('#login-form button').click()
    expect(s.locator('#lectures button')).to_have_count(1);s.locator('#lectures button').click();expect(s.locator('#lesson')).to_be_visible()
    s.wait_for_function("document.querySelector('#notes-title').textContent.includes('내 필기')")
    before=request(s,f'/extension/v1/student/lectures/{assigned["id"]}/notes')
    s.evaluate('window.__releaseNotePause()')
    expect(s.locator('#import-legacy-note')).not_to_have_attribute('aria-busy','true')
    s.wait_for_timeout(1100)
    after=request(s,f'/extension/v1/student/lectures/{assigned["id"]}/notes')
    result.update(original_account=original,new_account=second,original_lecture=old_lecture,new_lecture=assigned['id'],before=before,after=after,reproduced=any(n['body']=='PRIVATE_FIRST_STUDENT_AUDIT_MARKER' for n in after),boundary='Real installed extension, actual API/database. Only media pause acknowledgment was delayed; no user data or paid provider.')
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    s.locator('#task-notes-button').click();s.screenshot(path=str(out/'cross-account-note.png'),full_page=True)
    print(json.dumps(result,ensure_ascii=False),flush=True)
    raise Complete()
try:b.main(exercise,phase='note-race',output=out)
except Complete:pass
