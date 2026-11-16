"""Focused installed-extension checks for token-free guardian quick start."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import expect
import verify_extensions_browser as browser
from verify_reaudit_fixes import Complete


checks = {}


def exercise(guardian, student, output):
    errors = []
    guardian.on('pageerror', lambda error: errors.append(str(error)))

    def enter(selector):
        control = guardian.locator(selector)
        expect(control).to_be_visible()
        control.focus()
        guardian.keyboard.press('Enter')

    # The existing fixture really created a local student and assigned a server sample.
    expect(guardian.locator('#setup-student')).to_contain_text('연결된 계정 1명')
    expect(guardian.locator('#setup-sample')).to_contain_text('공개·배정된 샘플 1개')
    expect(guardian.locator('#setup-observed')).to_contain_text('서버 연결·배정 목록 확인:')
    expect(guardian.locator('#setup-observed')).to_contain_text('로컬 시험 계정')
    expect(guardian.locator('#setup-progress-title').locator('..')).to_contain_text('열기·재생 성공은 이 안내에서 확인할 수 없습니다')
    checks['server_evidence_only'] = True

    guardian.locator('#prepare-form [name=title]').fill('시작 안내 이동 중 보존할 초안')
    posts = []
    guardian.on('request', lambda request: posts.append(request.url) if request.method == 'POST' else None)
    enter('#setup-connect')
    expect(guardian.locator('#create-pair-code')).to_be_focused()
    enter('#setup-sample-action')
    expect(guardian.locator('#student-choice')).to_be_focused()
    assert posts == [], posts
    expect(guardian.locator('#prepare-form [name=title]')).to_have_value('시작 안내 이동 중 보존할 초안')
    checks['jumps_preserve_drafts_without_requests'] = True

    enter('#guardian-help')
    expect(guardian.locator('#guardian-guide-title')).to_be_focused()
    expect(guardian.locator('#guardian-guide-full')).not_to_have_attribute('open', '')
    expect(guardian.locator('#guardian-content')).to_be_hidden()
    guardian.keyboard.press('Tab')
    expect(guardian.locator('#guardian-guide-done')).to_be_focused()
    guardian.keyboard.press('Tab')
    expect(guardian.locator('#guardian-guide-full > summary')).to_be_focused()
    guardian.keyboard.press('Enter')
    expect(guardian.locator('#guardian-guide-full')).to_have_attribute('open', '')
    expect(guardian.locator('#guardian-guide-help')).to_be_visible()
    enter('#guardian-guide-done')
    expect(guardian.locator('#guardian-help')).to_be_focused()
    expect(guardian.locator('#prepare-form [name=title]')).to_have_value('시작 안내 이동 중 보존할 초안')
    checks['full_manual_optional_reopenable'] = True
    browser.check_layout(guardian, 'guardian-onboarding-connected', output)

    # A real unlink must remove connection/sample completion; a new code is not consent.
    enter('#connection-students button')
    enter('#guardian-unlink-yes')
    expect(guardian.locator('#setup-student')).to_contain_text('연결된 학생 없음')
    expect(guardian.locator('#setup-sample')).to_have_text('학생 연결 후 선택할 수 있습니다.')
    enter('#setup-sample-action')
    expect(guardian.locator('#connections-title')).to_be_focused()
    enter('#setup-connect')
    guardian.keyboard.press('Enter')
    expect(guardian.locator('#pair-code')).not_to_have_value('')
    expect(guardian.locator('#setup-student')).to_contain_text('연결된 학생 없음')
    enter('#setup-refresh')
    expect(guardian.locator('#status')).to_have_text('목록을 갱신했습니다.')
    expect(guardian.locator('#setup-refresh')).to_be_focused()
    expect(guardian.locator('#setup-sample')).to_have_text('학생 연결 후 선택할 수 있습니다.')
    checks['code_does_not_complete_connection_or_assignment'] = True
    browser.check_layout(guardian, 'guardian-onboarding-awaiting-student', output)

    # Even a restored session must explicitly finish the concise first guide.
    guardian.evaluate("async()=>chrome.storage.local.remove('guardian-guide-v1-seen')")
    guardian.reload()
    expect(guardian.locator('#guardian-guide-title')).to_be_focused()
    expect(guardian.locator('#guardian-content')).to_be_hidden()
    expect(guardian.locator('#guardian-guide-full')).not_to_have_attribute('open', '')
    expect(guardian.locator('#guardian-guide-done')).to_be_enabled()
    guardian.keyboard.press('Tab')
    expect(guardian.locator('#guardian-guide-done')).to_be_focused()
    guardian.keyboard.press('Enter')
    expect(guardian.locator('#guardian-start')).to_be_visible()
    expect(guardian.locator('#workspace')).to_be_hidden()
    checks['first_guide_gate_preserved'] = True
    assert not errors, errors
    raise Complete()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        browser.main(exercise, phase='guardian-onboarding', output=args.output)
    except Complete:
        pass
    report = {
        'result': 'passed' if len(checks) == 5 else 'failed',
        'checks': checks,
        'axe': browser.AXE_RESULTS,
        'boundary': 'Installed extensions and existing local endpoints with a temporary DB/profile; no provider credentials. Real screen-reader audio and separate-device student playback are not verified.',
    }
    (args.output / 'guardian-onboarding-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    raise SystemExit(report['result'] != 'passed')
