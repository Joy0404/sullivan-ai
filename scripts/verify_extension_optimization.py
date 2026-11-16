"""Independent recheck boundaries and a repeatable long-passage measurement.

Disposable real extensions/API/DB and decoded MP4; controlled save failures.
"""
from verify_extensions_browser import student_control
import argparse
import json
from pathlib import Path
import time

from playwright.sync_api import expect
import verify_extensions_browser as browser
from verify_extensions_phase3 import exercise as phase3
from verify_reaudit_fixes import request, prepare, open_lesson, Complete

CHECKS = {}
MEASUREMENTS = {}


def record(name, passed, observed):
    CHECKS[name] = {'passed': bool(passed), 'observed': observed}
    print(name, 'PASS' if passed else 'FAIL', flush=True)


def data_checks(guardian, student, output):
    base = request(student, '/local/lectures')[0]
    passage = ' '.join(f'긴 지문의 {i}번째 문장입니다.' for i in range(1, 601))
    job = prepare(guardian, '긴 지문 측정', {'analysis': {'passage_text': passage}})
    assert job['state'] == 'completed'
    target = request(guardian, '/local/students')[0]['id']
    lecture = request(guardian, f'/extension/v1/guardian/preparations/{job["id"]}/publish',
                      'POST', {'students': [target]})
    student_control(student, '#refresh').click()
    open_lesson(student, lecture['id'])
    student_control(student, '#access-mode').select_option('reader')
    student.evaluate('''()=>{window.__passageCalls=0;
      const original=SullivanPassages.paragraphsForSnapshot;
      SullivanPassages.paragraphsForSnapshot=(...args)=>{window.__passageCalls++;return original(...args);};}''')
    measure = student.evaluate('''async()=>{const{command}=await import('./app.js');
      const started=performance.now();await command('1문단');return {
        normalization_calls:window.__passageCalls,elapsed_ms:performance.now()-started,
        sentence_controls:document.querySelectorAll('[data-sentence-id]').length};}''')
    assert measure['sentence_controls'] == 600
    MEASUREMENTS['long_passage'] = measure
    record('P01.reuse_prepared_passage', measure['normalization_calls'] <= 1, measure)
    student_control(student, '#position').fill('77')
    open_lesson(student, base['id'])
    progress = request(student, f'/extension/v1/student/lectures/{lecture["id"]}')['progress']
    record('N01.unsaved_position_on_switch', progress['position_ms'] == 77000,
           {'expected_ms': 77000, 'saved_ms': progress['position_ms']})
    raise Complete()


def save_checks(guardian, student, output):
    student_control(student, '#access-mode').select_option('silent')
    lesson = next(l for l in request(student, '/local/lectures') if l['title'] == '동기화 테스트 강의')
    failures = []
    def fail_save(route):
        failures.append(route.request.post_data_json)
        route.fulfill(status=503, content_type='application/json', body='{"detail":"시험 저장 실패"}')
    student.route(f'**/local/lectures/{lesson["id"]}/progress', fail_save)
    deadline = time.monotonic() + 13
    while not failures and time.monotonic() < deadline:
        student.wait_for_timeout(100)
    assert failures, 'Automatic save did not run'
    student.wait_for_timeout(100)
    info = {'connection': student.locator('#connection').inner_text(),
            'video_has_source': student.locator('#local-video').evaluate('e=>Boolean(e.getAttribute("src"))'),
            'save_feedback': student.locator('#save-status').inner_text()}
    record('N02.save_failure_keeps_media', info['video_has_source'] and '끊겼습니다' not in info['connection'], info)
    record('N03.save_failure_feedback', '저장' in info['save_feedback'] and '실패' in info['save_feedback'], info['save_feedback'])
    raise Complete()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--group', choices=['data', 'save'])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    groups = []
    for name, exercise in [('data', data_checks), ('save', save_checks)]:
        if args.group and args.group != name:
            continue
        output = args.output / name
        output.mkdir(exist_ok=True)
        if name == 'save':
            phase3.student_check = exercise
            exercise = phase3
        try:
            browser.main(exercise, phase='optimization-'+name, output=output)
        except Complete:
            pass
        groups.append(name)
    report = {'result': 'passed' if all(c['passed'] for c in CHECKS.values()) else 'failed',
              'groups': groups, 'checks': CHECKS, 'measurements': MEASUREMENTS,
              'boundary': '600-sentence fixture; synthetic speech; real extension/API/DB/video; injected save 503'}
    (args.output/'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(report['result'] != 'passed')
