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
def save(): (OUT/'observations.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+'\n')
def req(page,path,body=None):return page.evaluate('async({path,body})=>{const {request}=await import("./client.js");return request(path,body===null?{}:{method:"POST",body})}',{'path':path,'body':body})
def response(title,text):return json.dumps({'safe_to_speak':True,'confidence':.99,'title':title,'response_text':text,'action':'answer'})
def snap(page):return page.evaluate('()=>({lesson:document.querySelector("#lesson-title").textContent,answerStatus:document.querySelector("#answer-status").textContent,playerStatus:document.querySelector("#player-status").textContent,chat:document.querySelector("#chat-log").textContent,spoken:(window.__spoken||[]).map(u=>u.text)})')
def exercise(g,s,out):
 s.evaluate(SPEECH);s.locator('#access-mode').select_option('app')
 pending=[]
 s.route('**/local/lectures/*/agent-turn',lambda route:pending.append(route))
 form=s.locator('#chat-form');form.locator('[name=question]').fill('감사 질문 A');form.locator('button').click()
 s.wait_for_function('()=>document.querySelector("#chat-form button").dataset.busy==="true"')
 cmd=s.locator('#command-form');cmd.locator('[name=command]').fill('감사 질문 B');cmd.locator('button').click()
 s.wait_for_timeout(150)
 assert len(pending)==2,len(pending)
 pending[1].fulfill(status=200,content_type='application/json',body=response('B 응답','B 최신 응답입니다.'))
 expect(s.locator('#chat-log')).to_contain_text('B 최신 응답입니다.')
 expect(cmd.locator('button')).not_to_have_attribute('aria-busy','true')
 before=snap(s)
 pending[0].fulfill(status=200,content_type='application/json',body=response('A 응답','A 이전 응답입니다.'))
 expect(form.locator('button')).not_to_have_attribute('aria-busy','true')
 after=snap(s)
 REPORT['observations'].append({'id':'parallel-question-order','request_messages':[r.request.post_data_json['message'] for r in pending],'before_release_A':before,'after_release_A':after,'failure_observed':'A 이전 응답입니다.' in after['chat'] and any('A 이전 응답입니다.' in t for t in after['spoken'])})
 save()
 s.locator('#access-mode').select_option('reader')
 form.locator('[name=question]').fill('A 강의 reader 답변');form.locator('button').click();s.wait_for_timeout(100)
 pending[2].fulfill(status=200,content_type='application/json',body=response('A 전용 답변','이 문장은 A 강의에서만 나온 답변입니다.'))
 expect(s.locator('#answer-status')).to_contain_text('A 강의에서만')
 # Native local playback populates player-status through the real tick path.
 with tempfile.TemporaryDirectory(prefix='live-recheck-video-') as tmp:
  fixture=Path(tmp)/'native.mp4';video_fixture(fixture)
  s.get_by_text('내 기기의 영상 연결·보관',exact=True).click()
  s.locator('#local-file').set_input_files(str(fixture));s.locator('#video-muted').check();s.locator('#connect-file').click()
  expect(s.locator('#local-video')).to_be_visible();s.locator('#play').click()
  expect(s.locator('#player-status')).to_have_text('강의를 재생하고 있습니다.')
  # Assign a second real sample without touching the selected lecture.
  student_id=g.locator('#student-choice').input_value();samples=g.locator('#assign-form [name=sample] option').evaluate_all('(es)=>es.map(e=>e.value)')
  assert len(samples)>1,samples
  req(g,f'/local/samples/{samples[1]}/assign',{'students':[student_id]})
  s.locator('#refresh').click();expect(s.locator('#lectures button')).to_have_count(2)
  before=snap(s);titles=s.locator('#lectures button').all_text_contents();target=next(t for t in titles if t!=before['lesson']+' 열기')
  s.get_by_role('button',name=target,exact=False).click();expect(s.locator('#lesson-title')).not_to_have_text(before['lesson'])
  after=snap(s)
  REPORT['observations'].append({'id':'cross-lesson-live-status','before_open_new':before,'after_open_new':after,'answer_failure_observed':after['answerStatus']==before['answerStatus'] and bool(after['answerStatus']),'player_failure_observed':after['playerStatus']==before['playerStatus'] and '재생하고' in after['playerStatus'],'new_media_hidden':not s.locator('#local-video').is_visible()})
  s.screenshot(path=str(OUT/'new-lesson-stale-status.png'),full_page=True)
  save()
 REPORT['browser']=s.context.browser.version
 save();raise Complete()
PAGES=[]
original_layout=harness.check_layout
original_expect=harness.expect
def layout(page,*args,**kwargs):
 if page not in PAGES:PAGES.append(page)
 return original_layout(page,*args,**kwargs)
class AuditExpectation:
 def __init__(self,assertion):self.assertion=assertion
 def __getattr__(self,name):
  def check(*args,**kwargs):
   try:return getattr(self.assertion,name)(*args,**kwargs)
   except BaseException:
    REPORT['failure_dom']=[{'url':p.url,'text':p.locator('body').inner_text(),'session':p.evaluate('async()=>await chrome.storage.session.get("session")')} for p in PAGES if not p.is_closed()]
    save();raise
  return check
harness.check_layout=layout
harness.expect=lambda locator:AuditExpectation(original_expect(locator))
try:main(exercise=exercise,phase='fresh-live-audit',output=OUT)
except Complete:print(json.dumps(REPORT,ensure_ascii=False,indent=2))
except BaseException as error:
 REPORT['probe_error']=str(error);REPORT['traceback']=traceback.format_exc();save();raise
