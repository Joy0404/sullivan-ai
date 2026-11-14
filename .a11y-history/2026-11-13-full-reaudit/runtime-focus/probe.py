"""Audit-only focus checks in installed extensions; speech/recognition are test boundaries."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from playwright.sync_api import expect
from verify_extensions_browser import main
from verify_extensions_phase3 import SPEECH

OUT=Path(__file__).resolve().parent
RESULT=[]

def snapshot(page):
    return page.evaluate("()=>({focus:document.activeElement.id||document.activeElement.tagName,value:document.querySelector('#command-input').value,lesson:document.querySelector('#lesson-title').textContent})")

def exercise(guardian,student,output):
    student.context.add_init_script(SPEECH);student.evaluate(SPEECH)
    student.locator('#access-mode').select_option('reader')
    saved=student.evaluate("""async()=>{const{request}=await import('./client.js');const l=(await request('/local/lectures'))[0];return{id:l.id,data:await request('/extension/v1/student/lectures/'+l.id)}}""")
    student.locator('#voice-consent').check()
    student.evaluate("""()=>{window.SpeechRecognition=class{start(){window.__recognitionStarted=true;this.onstart?.();}stop(){this.onresult?.({results:[[{transcript:'1문단 밑줄 표시'}]]});this.onend?.();}abort(){}};}""")
    student.locator('#material button').first.focus();before=snapshot(student)
    student.keyboard.down('Space');student.wait_for_function('()=>window.__recognitionStarted===true',timeout=4500);student.keyboard.up('Space')
    expect(student.get_by_role('button',name='1문단 밑줄 해제',exact=True)).to_be_visible()
    after=snapshot(student)
    RESULT.append({'id':'voice_underline_focus','before':before,'after':after,'passed':after['focus']!='BODY','boundary':'Actual 3-second key hold; recognizer transcript is a test double.'})
    student.evaluate("""async(saved)=>{const{request}=await import('./client.js');await request('/local/lectures/'+saved.id+'/progress',{method:'PUT',body:saved.data.progress})}""",saved)

    student.reload();expect(student.locator('#lectures button')).to_have_count(1)
    held=[]
    student.route('**/extension/v1/student/lectures/*',lambda route:held.append(route))
    student.locator('#lectures button').click();student.wait_for_timeout(100)
    assert held
    student.locator('#command-input').focus();student.keyboard.type('입력 중');before=snapshot(student)
    held[0].continue_();expect(student.locator('#lesson')).to_be_visible();after=snapshot(student)
    RESULT.append({'id':'delayed_lecture_focus','before':before,'after':after,'passed':after['focus']=='command-input','boundary':'One real GET response delayed at browser routing boundary.'})
    student.unroute('**/extension/v1/student/lectures/*')

    student.locator('#lectures button').focus();before=snapshot(student)
    student.route('**/local/lectures',lambda route:route.fulfill(status=200,content_type='application/json',body='[]'))
    student.evaluate("document.querySelector('#refresh').click()")
    expect(student.locator('#lectures button')).to_have_count(0);after=snapshot(student)
    RESULT.append({'id':'removed_lecture_focus','before':before,'after':after,'passed':after['focus']!='BODY','boundary':'Simulated empty latest assignment list; refresh activated without changing focused lecture (voice/button-command equivalent).'})
    student.unroute('**/local/lectures')
    student.locator('#refresh').click();expect(student.locator('#lectures button')).to_have_count(1)
    (OUT/'results.json').write_text(json.dumps(RESULT,ensure_ascii=False,indent=2)+'\n');print(json.dumps(RESULT,ensure_ascii=False,indent=2),flush=True)
    return guardian

if __name__=='__main__':main(exercise,phase='focus-audit',output=OUT)
