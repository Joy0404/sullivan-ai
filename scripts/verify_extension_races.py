"""Adversarial input/response order in real installed extensions and decoded MP4."""
from verify_extensions_browser import student_control
import argparse
import json
from pathlib import Path
from playwright.sync_api import expect
import verify_extensions_browser as browser
from verify_extensions_phase3 import exercise as media_flow
from verify_reaudit_fixes import Complete, request

checks={}
def record(name,passed,observed):
    checks[name]={'passed':bool(passed),'observed':observed};print(name,'PASS' if passed else 'FAIL',flush=True)


def races(guardian,student,output):
    student_control(student, '#access-mode').select_option('silent')
    lesson=next(row for row in request(student,'/local/lectures') if row['title']=='동기화 테스트 강의')
    pattern=f'**/local/lectures/{lesson["id"]}/progress'
    writes=[]
    student.on('request',lambda req:writes.append(req.post_data_json) if req.method=='PUT' and req.url.endswith(f'/lectures/{lesson["id"]}/progress') else None)
    student_control(student, '#position').fill('2');student_control(student, '#progress-form button').click()
    expect(student.locator('#progress-form button')).not_to_have_attribute('aria-busy','true')
    record('RACE01.single_position_write',len(writes)==1,{'writes':len(writes)})
    writes.clear();held=[]
    student.route(pattern,lambda route:route.continue_() if held else held.append(route))
    student_control(student, '#position').fill('3');student_control(student, '#progress-form button').click()
    student.wait_for_function('()=>document.querySelector("#save-status").textContent.includes("저장 중")')
    student.wait_for_timeout(100);assert held
    student_control(student, '#position').fill('5')
    held[0].continue_()
    expect(student.locator('#progress-form button')).not_to_have_attribute('aria-busy','true')
    student.unroute(pattern)
    saved=request(student,f'/extension/v1/student/lectures/{lesson["id"]}')['progress']
    record('RACE02.new_position_stays_pending',saved['position_ms']==3000 and student.locator('#position').input_value()=='5',{'saved_ms':saved['position_ms'],'field':student.locator('#position').input_value(),'writes':writes})
    student_control(student, '#progress-form button').click();expect(student.locator('#progress-form button')).not_to_have_attribute('aria-busy','true')
    # The edit form must retain new typing while its previous value is being saved.
    rows=request(guardian,'/local/lectures');first,second=rows[:2]
    guardian.get_by_role('button',name=first['title']+' 배정 수정',exact=True).click()
    form=guardian.locator('#edit-form');form.locator('[name=title]').fill('처음 저장한 제목')
    held=[];edit_pattern=f'**/local/lectures/{first["id"]}'
    guardian.route(edit_pattern,lambda route:held.append(route))
    form.locator('button').click();guardian.wait_for_timeout(100);assert held
    form.locator('[name=title]').fill('응답을 기다리며 새로 입력한 제목')
    form.locator('input[type=checkbox]').first.uncheck()
    held[0].continue_()
    expect(form.locator('button')).not_to_have_attribute('aria-busy','true')
    guardian.unroute(edit_pattern)
    record('RACE03.editor_keeps_new_input',form.locator('[name=title]').input_value()=='응답을 기다리며 새로 입력한 제목' and not form.locator('input[type=checkbox]').first.is_checked()
           and form.locator('input[type=checkbox]').first.evaluate('e=>e===document.activeElement'),{'value':form.locator('[name=title]').input_value(),'checkbox_checked':form.locator('input[type=checkbox]').first.is_checked(),'focus':guardian.evaluate('document.activeElement.id||document.activeElement.name')})
    guardian.get_by_role('button',name='처음 저장한 제목 배정 수정',exact=True).click()
    held=[];withdraw_pattern=f'**/lectures/{first["id"]}/withdraw'
    guardian.route(withdraw_pattern,lambda route:held.append(route))
    guardian.locator('#withdraw').click();guardian.locator('#withdraw-yes').click();guardian.wait_for_timeout(100);assert held
    guardian.get_by_role('button',name=second['title']+' 배정 수정',exact=True).click()
    form.locator('[name=title]').fill('다른 강의에서 입력 중')
    held[0].continue_()
    expect(guardian.locator('#withdraw-yes')).not_to_have_attribute('aria-busy','true')
    guardian.unroute(withdraw_pattern)
    record('RACE04.withdraw_keeps_other_editor',form.locator('[name=title]').input_value()=='다른 강의에서 입력 중' and form.locator('[name=title]').evaluate('e=>e===document.activeElement'),{'value':form.locator('[name=title]').input_value(),'focus':guardian.evaluate('document.activeElement.id||document.activeElement.name')})
    # A late older poll must not turn a completed job back into running.
    job={'id':'race-job','title':'응답 순서 검사','subject':'일반','state':'completed','message':'완료 확인','updated':1}
    held=[]
    def jobs(route):
        if not held:held.append(route)
        else:route.fulfill(status=200,content_type='application/json',body=json.dumps([job]))
    guardian.route('**/extension/v1/guardian/preparations',jobs)
    guardian.locator('#refresh-preparations').click();guardian.wait_for_timeout(100);assert held
    guardian.locator('#refresh').click()
    expect(guardian.get_by_role('button',name='응답 순서 검사 결과 확인·배정',exact=True)).to_be_visible()
    held[0].fulfill(status=200,content_type='application/json',body=json.dumps([{**job,'state':'running','message':'오래된 진행 상태'}]))
    expect(guardian.locator('#refresh-preparations')).not_to_have_attribute('aria-busy','true')
    record('RACE05.stale_poll_does_not_regress',guardian.get_by_role('button',name='응답 순서 검사 결과 확인·배정',exact=True).is_visible(),guardian.locator('#preparations').inner_text())
    guardian.unroute('**/extension/v1/guardian/preparations')
    browser.check_layout(guardian,'guardian-editor-races',output)
    browser.check_layout(student,'student-position-races',output)
    raise Complete()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    media_flow.student_check=races
    try:browser.main(media_flow,phase='races',output=args.output)
    except Complete:pass
    result={'result':'passed' if len(checks)==5 and all(c['passed'] for c in checks.values()) else 'failed','checks':checks,'axe':browser.AXE_RESULTS,
            'boundary':'Real installed extensions/API/DB/decoded MP4; explicit delayed PUT/withdraw transport; synthetic speech; no actual user DB or paid provider'}
    (args.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(result['result']!='passed')
