"""Disposable installed-extension audit; products/tests are not modified.
Speech calls are recorded, provider replies use explicit controlled HTTP routes.
"""
import hashlib,json,os,sys,tempfile,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from playwright.sync_api import expect
import verify_extensions_browser as harness
from verify_extensions_browser import main
from verify_extensions_phase3 import SPEECH,video_fixture
OUT=Path(__file__).resolve().parent
class Complete(BaseException):pass
REPORT={'boundaries':{'extension':'actual installed MV3 extension in disposable Chromium profile','API_DB':'temporary real server/DB; agent-turn responses deliberately controlled','media':'native generated MP4 playback','speech':'recording synthetic callbacks, no audible or OS AT verification'},'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'apps/extensions/student/app.js',ROOT/'apps/extensions/student/speech.js',ROOT/'apps/extensions/student/media.js']},'observations':[]}
def save(): (OUT/'guardian-pair-observations.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+'\n')
def req(page,path,body=None):return page.evaluate('async({path,body})=>{const {request}=await import("./client.js");return request(path,body===null?{}:{method:"POST",body})}',{'path':path,'body':body})
def response(title,text):return json.dumps({'safe_to_speak':True,'confidence':.99,'title':title,'response_text':text,'action':'answer'})
def snap(page):return page.evaluate('()=>({lesson:document.querySelector("#lesson-title").textContent,answerStatus:document.querySelector("#answer-status").textContent,playerStatus:document.querySelector("#player-status").textContent,chat:document.querySelector("#chat-log").textContent,spoken:(window.__spoken||[]).map(u=>u.text)})')
def exercise(g,s,out):
 s.evaluate(SPEECH);s.locator('#access-mode').select_option('app')
 code=req(g,'/extension/v1/guardian/connections/code',{})['code']
 s.get_by_text('보호자 연결과 공유 범위',exact=True).click()
 s.locator('#pair-preview-form [name=code]').fill(code)
 s.evaluate('window.__spoken=[]')
 s.locator('#pair-preview-form button').click();expect(s.locator('#pair-preview')).to_be_visible()
 s.locator('#pair-confirm').focus();s.locator('#pair-confirm-form button').focus();s.wait_for_timeout(150)
 spoken=s.evaluate('(window.__spoken||[]).map(u=>u.text)')
 details=s.locator('#pair-guardian').inner_text()+' '+s.locator('#pair-sharing').inner_text()
 REPORT['observations'].append({'id':'pair-consent-app-guidance','visible_details':details,'spoken_after_preview_and_controls':spoken,'guardian_name_spoken':any('연결할 보호자:' in t for t in spoken),'sharing_scope_spoken':any('기록 개수' in t or '메모·질문' in t for t in spoken)})
 save()
 # Genuine management data, only transport completion held.
 held=[]
 def hold(route):
  response=route.fetch();held.append((route,response))
 g.route('**/local/students/*/progress',hold)
 g.locator('#load-management').click();g.wait_for_timeout(150);assert held
 title=g.locator('#prepare-form [name=title]');title.fill('지금 입력 중인 제목')
 before=g.evaluate('document.activeElement.outerHTML')
 held[0][0].fulfill(response=held[0][1]);expect(g.locator('#management-detail')).to_be_visible()
 after=g.evaluate('document.activeElement.outerHTML')
 REPORT['observations'].append({'id':'guardian-management-delayed-focus','before_release':before,'after_release':after,'focus_stolen':g.locator('#management-detail-title').evaluate('e=>e===document.activeElement')})
 save()
 job=req(g,'/extension/v1/guardian/preparations',{'title':'감사 초점 결과','assets':[{'name':'p.txt','kind':'passage','content':'임시 자료입니다.'}]})
 g.locator('#refresh-preparations').click();control=g.get_by_role('button',name='감사 초점 결과 결과 확인·배정',exact=True);expect(control).to_be_visible()
 held_detail=[]
 def detail(route):
  response=route.fetch();held_detail.append((route,response))
 g.route('**/preparations/'+job['id'],detail)
 control.click();g.wait_for_timeout(100);assert held_detail
 title.fill('새로 입력하는 제목');before=g.evaluate('document.activeElement.outerHTML')
 held_detail[0][0].fulfill(response=held_detail[0][1]);expect(g.locator('#prepared-title')).to_have_text('감사 초점 결과 준비 결과')
 after=g.evaluate('document.activeElement.outerHTML')
 REPORT['observations'].append({'id':'guardian-preparation-delayed-focus','before_release':before,'after_release':after,'focus_stolen':g.locator('#prepared-title').evaluate('e=>e===document.activeElement')})
 REPORT['browser']=s.context.browser.version;save();raise Complete()
try:main(exercise=exercise,phase='guardian-pair-audit',output=OUT)
except Complete:print(json.dumps(REPORT,ensure_ascii=False,indent=2))
except BaseException as error:
 REPORT['probe_error']=str(error);REPORT['traceback']=traceback.format_exc();save();raise
