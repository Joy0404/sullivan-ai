"""Real installed guardian dashboard transitions; disposable API/list fixtures."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import expect
import verify_extensions_browser as browser
from verify_reaudit_fixes import Complete, request

checks = []


def exercise(guardian, student, output):
    def states(expected):
        for name, value in zip(('student','lecture','assignment','settings'), expected):
            if name == 'student':
                value = '서버 목록에서 연결된 계정 1명 확인' if value == '완료' else '연결된 학생 없음 · 학생의 연결 동의 후 목록을 새로고침하세요'
            expect(guardian.locator('#setup-'+name)).to_have_text(value)
        checks.append(expected)

    states(['완료','완료','완료','기본값'])
    people = request(guardian, '/local/students')
    lessons = request(guardian, '/local/lectures')
    guardian.get_by_text('직접 준비한 강의와 학생 설정 단계', exact=True).focus()
    guardian.keyboard.press('Enter')
    expect(guardian.locator('#setup-progress')).to_be_visible()
    def lists(students, lectures, jobs):
        guardian.unroute('**/local/students'); guardian.unroute('**/local/lectures')
        guardian.unroute('**/extension/v1/guardian/preparations')
        for pattern, data in [('**/local/students', students), ('**/local/lectures', lectures),
                              ('**/extension/v1/guardian/preparations', jobs)]:
            def respond(data):
                return lambda route: route.fulfill(status=200, content_type='application/json', body=json.dumps(data))
            guardian.route(pattern, respond(data))
        guardian.evaluate('document.querySelector("#refresh").click()')
        expect(guardian.locator('#refresh')).not_to_have_attribute('aria-busy','true')
    guardian.locator('#setup-assignment-link').focus()
    lists(people, [{**lecture, 'ready': False} for lecture in lessons], [])
    states(['완료','완료','할 차례','기본값'])
    expect(guardian.locator('#setup-assignment-link')).to_be_focused()
    guardian.keyboard.press('Enter'); expect(guardian.locator('#lectures-title')).to_be_focused()
    jobs = [{'id':'fixture','title':'준비된 자료','subject':'일반','state':'completed','message':'자료 준비 완료', 'updated':1}]
    lists(people, [], jobs)
    states(['완료','완료','할 차례','기본값'])
    expect(guardian.locator('#setup-assignment-link')).to_have_attribute('href','#preparations-title')
    guardian.locator('#setup-assignment-link').focus(); guardian.keyboard.press('Enter')
    expect(guardian.locator('#preparations-title')).to_be_focused()
    lists(people, [], [])
    states(['완료','할 차례','아직','기본값'])
    lists([], [], [])
    states(['할 차례','아직','아직','기본값'])
    lists([{**person,'settings':{**person['settings'],'speech_rate':1.1}} for person in people], lessons, [])
    states(['완료','완료','완료','완료'])
    browser.check_layout(guardian, 'guardian-stage-dashboard', output)
    for width in (390,1280):
        guardian.set_viewport_size({'width':width,'height':900})
        guardian.locator('#setup-progress').scroll_into_view_if_needed()
        guardian.screenshot(path=str(output/f'guardian-stages-{width}.png'))
    raise Complete()


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    try:browser.main(exercise,phase='stage-dashboard',output=args.output)
    except Complete:pass
    assert len(checks)==6
    (args.output/'results.json').write_text(json.dumps({'result':'passed','state_transitions':checks,
        'axe':browser.AXE_RESULTS,'boundary':'Actual installed extensions; disposable API/DB. Dashboard list transitions use explicit response fixtures; no live screen reader audio.'},ensure_ascii=False,indent=2)+'\n')
