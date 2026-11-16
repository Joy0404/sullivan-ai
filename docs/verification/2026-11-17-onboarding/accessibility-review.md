# Web Accessibility Audit

An audit of web content, run on 2026-11-16. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-16 |
| Scope | 11 items |
| Skills run | keyboard-navigator, live-region-controller |
| Tooling | node v24.22.1, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 16 |

Audited:

- `apps/extensions/guardian/app.js`
- `apps/extensions/guardian/entry.html`
- `apps/extensions/guardian/entry.js`
- `apps/extensions/guardian/workspace.html`
- `apps/extensions/shared/ui.js`
- `apps/extensions/student/app.js`
- `apps/extensions/student/interaction-feedback.js`
- `apps/extensions/student/keyboard.js`
- `apps/extensions/student/practice-progress.js`
- `apps/extensions/student/speech.js`
- `apps/extensions/student/workspace.html`

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

- Guardian guide hides underlying content and restores focus to its invoking help button.
- Guardian setup shortcuts focus visible connection-code and student-selection controls without submitting forms.
- Lesson changes suspend practice tickets, and account changes configure separate practice state.
- Native command dialogs provide modal containment; closing restores a visible invoking control or fallback.
- New onboarding, practice, status and help actions use native keyboard-operable buttons.
- Student keyboard traversal excludes hidden, inert, disabled and collapsed-details descendants.
- Student practice opening and closing explicitly move focus to visible elements.
- StudentAnnouncer와 StudentSpeech는 reader_mode에서 앱 TTS를 실행하지 않습니다.
- 검토 범위에서 남아 있는 serious 또는 critical 실시간 안내 결함을 발견하지 못했습니다.
- 동일한 현재 상태 재요청은 live region을 비운 뒤 다음 애니메이션 프레임에서 다시 전달하며, 요청 순서·계정·강의 유효성을 재확인합니다.
- 보호자 next-step은 aria-live=off로 유지되어 기존 완료 안내와 경쟁하지 않습니다.
- 새 피드백 문구는 고정된 공개 문구 사전을 사용합니다.
- 연습 기록 저장 실패는 기존 status 경로로 안내하며 계정과 연습 로드 세대가 바뀌면 오래된 오류 안내를 억제합니다.
- 원시 음성 인식문은 새 확인 UI나 live region에 출력하지 않습니다.
- 음성 인식 취소와 종료에서 오래된 듣기 안내를 정리합니다.
- 학생의 연습 다음 단계는 실제 조작 결과 확인 후 기존 status 경로로 전달합니다.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **keyboard-navigator**: Source review only; runtime keyboard navigation, focus visibility and browser-specific focus behavior were not independently exercised.
- **keyboard-navigator**: No files were edited and no provider or user database calls were made.
- **keyboard-navigator**: Optional usability improvement: when Space commands are disabled, practice-start could explain how to enable them before instructing the student to use Space.
- **live-region-controller**: 정적 소스 재검토 결과입니다. 실제 스크린리더 음성, 반복 안내의 접근성 트리 반영 시점, 안내 순서는 실행 검증하지 않았습니다.
- **live-region-controller**: 보호자 next-step은 읽어서 확인하는 문맥 안내이며 자동 음성 안내로 검증하거나 간주하지 않았습니다.
- **live-region-controller**: 파일 수정, 실시간 공급자 호출, 사용자 데이터베이스 접근을 수행하지 않았습니다.

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
    "apps/extensions/guardian/app.js",
    "apps/extensions/guardian/entry.html",
    "apps/extensions/guardian/entry.js",
    "apps/extensions/guardian/workspace.html",
    "apps/extensions/shared/ui.js",
    "apps/extensions/student/app.js",
    "apps/extensions/student/interaction-feedback.js",
    "apps/extensions/student/keyboard.js",
    "apps/extensions/student/practice-progress.js",
    "apps/extensions/student/speech.js",
    "apps/extensions/student/workspace.html"
  ],
  "findings": [],
  "passed": [
    "Guardian guide hides underlying content and restores focus to its invoking help button.",
    "Guardian setup shortcuts focus visible connection-code and student-selection controls without submitting forms.",
    "Lesson changes suspend practice tickets, and account changes configure separate practice state.",
    "Native command dialogs provide modal containment; closing restores a visible invoking control or fallback.",
    "New onboarding, practice, status and help actions use native keyboard-operable buttons.",
    "Student keyboard traversal excludes hidden, inert, disabled and collapsed-details descendants.",
    "Student practice opening and closing explicitly move focus to visible elements.",
    "StudentAnnouncer와 StudentSpeech는 reader_mode에서 앱 TTS를 실행하지 않습니다.",
    "검토 범위에서 남아 있는 serious 또는 critical 실시간 안내 결함을 발견하지 못했습니다.",
    "동일한 현재 상태 재요청은 live region을 비운 뒤 다음 애니메이션 프레임에서 다시 전달하며, 요청 순서·계정·강의 유효성을 재확인합니다.",
    "보호자 next-step은 aria-live=off로 유지되어 기존 완료 안내와 경쟁하지 않습니다.",
    "새 피드백 문구는 고정된 공개 문구 사전을 사용합니다.",
    "연습 기록 저장 실패는 기존 status 경로로 안내하며 계정과 연습 로드 세대가 바뀌면 오래된 오류 안내를 억제합니다.",
    "원시 음성 인식문은 새 확인 UI나 live region에 출력하지 않습니다.",
    "음성 인식 취소와 종료에서 오래된 듣기 안내를 정리합니다.",
    "학생의 연습 다음 단계는 실제 조작 결과 확인 후 기존 status 경로로 전달합니다."
  ],
  "notes": [
    {
      "skill": "keyboard-navigator",
      "note": "Source review only; runtime keyboard navigation, focus visibility and browser-specific focus behavior were not independently exercised."
    },
    {
      "skill": "keyboard-navigator",
      "note": "No files were edited and no provider or user database calls were made."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Optional usability improvement: when Space commands are disabled, practice-start could explain how to enable them before instructing the student to use Space."
    },
    {
      "skill": "live-region-controller",
      "note": "정적 소스 재검토 결과입니다. 실제 스크린리더 음성, 반복 안내의 접근성 트리 반영 시점, 안내 순서는 실행 검증하지 않았습니다."
    },
    {
      "skill": "live-region-controller",
      "note": "보호자 next-step은 읽어서 확인하는 문맥 안내이며 자동 음성 안내로 검증하거나 간주하지 않았습니다."
    },
    {
      "skill": "live-region-controller",
      "note": "파일 수정, 실시간 공급자 호출, 사용자 데이터베이스 접근을 수행하지 않았습니다."
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
