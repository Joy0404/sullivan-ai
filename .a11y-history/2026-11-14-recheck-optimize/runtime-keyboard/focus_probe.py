"""Disposable installed-extension focus audit. Product and existing tests are untouched."""
from pathlib import Path
import hashlib
import json
import sys
import traceback

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from playwright.sync_api import expect
from verify_extensions_browser import main
from verify_extensions_phase2 import exercise as phase2

OUT=Path(__file__).resolve().parent
RESULT={'boundary':'Real Chromium installed extensions and API; list GET delivery held explicitly; temporary account DB/profile only.', 'cases':[]}
class AuditComplete(BaseException):pass

def snapshot(page):
 return page.evaluate("""()=>{const e=document.activeElement;return {tag:e.tagName,id:e.id,text:e.textContent.slice(0,140),type:e.type,
   inLectures:!!e.closest('#lectures'),inPublish:!!e.closest('#publish-students'),oldConnected:window.__auditOldFocus?.isConnected};}""")

def hook(guardian,student,output):
 guardian=phase2(guardian,student,output)
 RESULT['browser']=guardian.context.browser.version
 for role,page in [('guardian',guardian),('student',student)]:
  text=page.evaluate("async()=>await(await fetch('./app.js')).text()")
  RESULT[role+'_built_app_sha256']=hashlib.sha256(text.encode()).hexdigest()
 try:
  for kind in ['button','checkbox','removed_item']:
   case={'name':'guardian_delayed_refresh_'+kind}
   held=[]
   def hold(route):held.append(route)
   guardian.route('**/local/students',hold)
   guardian.route('**/local/lectures',hold)
   try:
    guardian.locator('#refresh').click()
    guardian.wait_for_function("document.querySelector('#refresh').dataset.busy==='true'")
    for _ in range(100):
     if len(held)>=2:break
     guardian.wait_for_timeout(10)
    assert len(held)==2, len(held)
    if kind=='checkbox':
     target=guardian.locator('#publish-students input').first
    elif kind=='removed_item':
     target=guardian.locator('#lectures button').filter(has_text='수정된 지문 강의 배정 수정')
    else:target=guardian.locator('#lectures button').first
    target.focus()
    guardian.evaluate('window.__auditOldFocus=document.activeElement')
    case['before']=snapshot(guardian)
    if kind=='removed_item':
     removed=guardian.evaluate("""async()=>{const{request}=await import('./client.js');
      // Resolve the existing lecture through the item title without releasing the held list requests.
      const item=document.activeElement.closest('li');return {title:item.querySelector('p').textContent};}""")
     from app import local_access
     with local_access.db() as con:
      row=con.execute('SELECT id FROM lectures WHERE title=?',('수정된 지문 강의',)).fetchone()
     assert row is not None
     ident=row['id'] if hasattr(row,'keys') else row[0]
     guardian.evaluate("""async(id)=>{const{request}=await import('./client.js');await request('/local/lectures/'+id,{method:'DELETE'});}""",ident)
     case['removed']=dict(removed,id=ident)
    for route in held:route.continue_()
    expect(guardian.locator('#refresh')).not_to_have_attribute('aria-busy','true')
    case['after']=snapshot(guardian)
    case['reproduced']=case['after']['tag']=='BODY' and case['after']['oldConnected'] is False
    guardian.screenshot(path=str(OUT/(kind+'-after.png')),full_page=True)
   except Exception:case['probe_error']=traceback.format_exc()
   finally:
    guardian.unroute('**/local/students',hold)
    guardian.unroute('**/local/lectures',hold)
    for route in held:
     try:route.continue_()
     except Exception:pass
    RESULT['cases'].append(case)
    (OUT/'focus-results.json').write_text(json.dumps(RESULT,ensure_ascii=False,indent=2)+'\n')

  case={'name':'student_modal_close_after_logout'}
  try:
   student.evaluate("""()=>{window.__auditFocusEvents=[];
    document.addEventListener('focusin',event=>window.__auditFocusEvents.push({event:'focus',id:event.target.id,tag:event.target.tagName}));
    document.querySelector('#text-dialog').addEventListener('close',()=>window.__auditFocusEvents.push({event:'close',active:document.activeElement.id}));}""")
   student.locator('#voice-test').focus()
   for _ in range(3):student.keyboard.press('Space',delay=35)
   expect(student.locator('#text-dialog')).to_be_visible()
   case['before']=snapshot(student)
   student.evaluate("async()=>await(await import('./client.js')).forgetSession()")
   expect(student.locator('#auth')).to_be_visible()
   student.wait_for_timeout(150)
   case['after']=snapshot(student)
   case['events']=student.evaluate('window.__auditFocusEvents')
   case['reproduced']=case['after']['id']=='voice-test' and any(e.get('id') in ['username','oauth-login'] for e in case['events'])
   student.screenshot(path=str(OUT/'modal-logout-after.png'),full_page=True)
  except Exception:case['probe_error']=traceback.format_exc()
  RESULT['cases'].append(case)
 finally:(OUT/'focus-results.json').write_text(json.dumps(RESULT,ensure_ascii=False,indent=2)+'\n')
 raise AuditComplete()

if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 try:main(hook,phase='focus-recheck',output=OUT)
 except AuditComplete:print(json.dumps(RESULT,ensure_ascii=False,indent=2))
