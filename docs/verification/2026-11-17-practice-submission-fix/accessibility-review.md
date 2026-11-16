# Web Accessibility Audit

An audit of web content, run on 2026-11-16. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-16 |
| Scope | 3 items |
| Skills run | keyboard-navigator, live-region-controller |
| Tooling | node v24.22.1, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 16 |

Audited:

- `apps/extensions/student/app.js`
- `apps/extensions/student/speech.js`
- `scripts/verify_student_onboarding.py`

## Executive summary

Pass. No critical or serious findings.

The headline numbers for this run.

| Measure | Value |
|---|---|
| Score | 100 out of 100 |
| Grade | A |
| Findings | 0 |
| Blocking (critical plus serious) | 0 |
| Verdict | Pass |

## Severity breakdown

Counts by severity, highest impact first.

| Severity | Count | What it means |
|---|---:|---|
| critical | 0 | Blocks a person from completing the task |
| serious | 0 | Major barrier with a difficult workaround |
| moderate | 0 | Real friction, workaround exists |
| minor | 0 | Noticeable but rarely blocking |

## Findings

No findings. Every check listed under "What passed" ran and came back clean.

## Remediation priorities

Nothing to remediate.

## What passed

16 checks ran and found nothing.

- Disabled Space commands produce actionable guidance instead of starting inaccessible shortcut practice.
- Pause failures leave practice inactive and surface an error through the shared task handler.
- Pending starts validate account identity, lesson identity, application generation, action generation, media view, media generation, media fence and readiness after asynchronous operations.
- Regression source includes actual video playback before start, injected pause failure, delayed-start skip, moved-focus preservation, and subsequent real Space gestures.
- Skipping increments practiceStartRevision before hiding the card and returning focus to context-help; a pending start cannot reopen it.
- The captured focus ticket prevents completion from changing tasks or moving focus after intervening keyboard input or focus movement.
- The practice-start control uses the shared task busy guard, preventing duplicate pending activations without removing keyboard focus.
- reader_mode에서는 StudentAnnouncer가 앱 음성을 실행하지 않고 StudentSpeech도 TTS 전에 반환합니다.
- startPractice awaits stopAll and requires a subsequent paused, non-advertisement media state before starting practice.
- startPractice는 중지 요청 성공과 실제 paused=true 및 광고 아님을 확인한 뒤에만 연습을 시작하고 시작 안내를 전달합니다.
- 나중에 하기와 계정·강의·동작·미디어 변경은 대기 중인 시작 결과를 무효화하므로 오래된 시작 안내나 연습 카드 재열기를 억제합니다.
- 대기 중 사용자가 이동하면 focusTicket 검사로 작업 화면과 키보드 초점을 보존합니다.
- 연습 시작은 기존 음성과 재생 의도를 취소한 뒤 영상을 멈추며 자동 재생을 요청하지 않습니다.
- 중지 실패는 기존 task 오류 경로로 짧은 재시도 안내를 전달하며 완료 상태를 만들지 않습니다.
- 회귀 스크립트는 실제 스크린리더 음성 평가와 브라우저 ASR을 검증했다고 주장하지 않습니다.
- 회귀 스크립트는 중지 실패, 대기 중 건너뛰기, 재생 중 시작의 일시정지 확인, 대기 중 새 초점 보존을 명시적으로 검사합니다.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **keyboard-navigator**: Source review only: the installed-browser regression suite was inspected but not independently executed in this specialist review.
- **keyboard-navigator**: No live model or user database calls were made; only this findings file was written.
- **live-region-controller**: 소스와 회귀 검사 코드에 대한 정적 검토입니다. 이번 검토에서 브라우저 검사나 실제 스크린리더 음성을 실행하지 않았습니다.
- **live-region-controller**: 계정·강의 변경 무효화는 소스의 유효성 가드로 확인했으며 해당 전환을 이번 검토에서 실행하지 않았습니다.
- **live-region-controller**: 요청된 JSON 보고서 파일만 추가했습니다. 소스 수정, 실시간 모델 호출, 사용자 데이터베이스 접근을 수행하지 않았습니다.

## Next steps

1. Keep the current checks in continuous integration so this does not regress.
2. Re-audit when the interface changes materially, or quarterly.
3. Confirm the automated result with a manual screen reader and keyboard pass.

Automated checks find a minority of accessibility barriers. A passing score is a floor, not a guarantee.

## Findings data

The merged findings, embedded so the next run can compute a delta without parsing this document.

```json a11y-findings
{
  "skills": [
    "keyboard-navigator",
    "live-region-controller"
  ],
  "scope": [
    "apps/extensions/student/app.js",
    "apps/extensions/student/speech.js",
    "scripts/verify_student_onboarding.py"
  ],
  "findings": [],
  "passed": [
    "Disabled Space commands produce actionable guidance instead of starting inaccessible shortcut practice.",
    "Pause failures leave practice inactive and surface an error through the shared task handler.",
    "Pending starts validate account identity, lesson identity, application generation, action generation, media view, media generation, media fence and readiness after asynchronous operations.",
    "Regression source includes actual video playback before start, injected pause failure, delayed-start skip, moved-focus preservation, and subsequent real Space gestures.",
    "Skipping increments practiceStartRevision before hiding the card and returning focus to context-help; a pending start cannot reopen it.",
    "The captured focus ticket prevents completion from changing tasks or moving focus after intervening keyboard input or focus movement.",
    "The practice-start control uses the shared task busy guard, preventing duplicate pending activations without removing keyboard focus.",
    "reader_mode에서는 StudentAnnouncer가 앱 음성을 실행하지 않고 StudentSpeech도 TTS 전에 반환합니다.",
    "startPractice awaits stopAll and requires a subsequent paused, non-advertisement media state before starting practice.",
    "startPractice는 중지 요청 성공과 실제 paused=true 및 광고 아님을 확인한 뒤에만 연습을 시작하고 시작 안내를 전달합니다.",
    "나중에 하기와 계정·강의·동작·미디어 변경은 대기 중인 시작 결과를 무효화하므로 오래된 시작 안내나 연습 카드 재열기를 억제합니다.",
    "대기 중 사용자가 이동하면 focusTicket 검사로 작업 화면과 키보드 초점을 보존합니다.",
    "연습 시작은 기존 음성과 재생 의도를 취소한 뒤 영상을 멈추며 자동 재생을 요청하지 않습니다.",
    "중지 실패는 기존 task 오류 경로로 짧은 재시도 안내를 전달하며 완료 상태를 만들지 않습니다.",
    "회귀 스크립트는 실제 스크린리더 음성 평가와 브라우저 ASR을 검증했다고 주장하지 않습니다.",
    "회귀 스크립트는 중지 실패, 대기 중 건너뛰기, 재생 중 시작의 일시정지 확인, 대기 중 새 초점 보존을 명시적으로 검사합니다."
  ],
  "notes": [
    {
      "skill": "keyboard-navigator",
      "note": "Source review only: the installed-browser regression suite was inspected but not independently executed in this specialist review."
    },
    {
      "skill": "keyboard-navigator",
      "note": "No live model or user database calls were made; only this findings file was written."
    },
    {
      "skill": "live-region-controller",
      "note": "소스와 회귀 검사 코드에 대한 정적 검토입니다. 이번 검토에서 브라우저 검사나 실제 스크린리더 음성을 실행하지 않았습니다."
    },
    {
      "skill": "live-region-controller",
      "note": "계정·강의 변경 무효화는 소스의 유효성 가드로 확인했으며 해당 전환을 이번 검토에서 실행하지 않았습니다."
    },
    {
      "skill": "live-region-controller",
      "note": "요청된 JSON 보고서 파일만 추가했습니다. 소스 수정, 실시간 모델 호출, 사용자 데이터베이스 접근을 수행하지 않았습니다."
    }
  ],
  "counts": {
    "critical": 0,
    "serious": 0,
    "moderate": 0,
    "minor": 0
  },
  "components": [],
  "score": 100,
  "grade": "A",
  "penalty": 0,
  "checks": 16,
  "generated": "2026-11-16",
  "template": "web"
}
```
