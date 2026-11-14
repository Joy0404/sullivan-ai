# Web Accessibility Audit

An audit of web content, run on 2026-11-14. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-14 |
| Scope | 4 items |
| Skills run | keyboard-navigator |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 10 |

Audited:

- `apps/extensions/guardian/app.js`
- `apps/extensions/guardian/workspace.html`
- `docs/verification/2026-11-14-closure/dashboard/results.json`
- `scripts/verify_extension_dashboard.py`

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

6 checks ran and found nothing.

- 네 단계 링크의 목적지 headings에는 tabindex=-1이 있고 숨겨진 details 안에 있지 않습니다.
- 단계별 대시보드는 순서 있는 목록과 기본 링크를 사용하며 DOM 순서대로 Tab 탐색할 수 있습니다.
- 보존된 실행 결과에서 6개 상태 전환과 기본 링크 Enter 후 목적지 초점을 검사한 회귀가 passed이고 해당 화면 axe 위반은 0건입니다.
- 전체 단계 목록은 live region 밖에 있고 next-step 상태는 문구가 바뀔 때만 갱신합니다.
- 정적 링크를 다시 생성하지 않고 상태 문구와 목적지 주소만 갱신하므로 갱신 중 링크 초점을 보존합니다.
- 준비 완료·미배정 작업이 있고 공개 강의가 없는 경우 배정 링크가 실제 준비 결과 목록으로 연결됩니다.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **keyboard-navigator**: 코드를 수정하지 않았습니다. 최종 JSON은 /tmp/sullivan-closure-keyboard.json에 저장했습니다.
- **keyboard-navigator**: 본 재검토는 소스 및 부모 에이전트가 실행한 결과 파일 확인입니다. 별도의 브라우저 회귀를 다시 실행하지 않았습니다.
- **keyboard-navigator**: 실제 VoiceOver/NVDA 발화·사용성은 확인하지 않았습니다.

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
    "keyboard-navigator"
  ],
  "scope": [
    "apps/extensions/guardian/app.js",
    "apps/extensions/guardian/workspace.html",
    "docs/verification/2026-11-14-closure/dashboard/results.json",
    "scripts/verify_extension_dashboard.py"
  ],
  "findings": [],
  "passed": [
    "네 단계 링크의 목적지 headings에는 tabindex=-1이 있고 숨겨진 details 안에 있지 않습니다.",
    "단계별 대시보드는 순서 있는 목록과 기본 링크를 사용하며 DOM 순서대로 Tab 탐색할 수 있습니다.",
    "보존된 실행 결과에서 6개 상태 전환과 기본 링크 Enter 후 목적지 초점을 검사한 회귀가 passed이고 해당 화면 axe 위반은 0건입니다.",
    "전체 단계 목록은 live region 밖에 있고 next-step 상태는 문구가 바뀔 때만 갱신합니다.",
    "정적 링크를 다시 생성하지 않고 상태 문구와 목적지 주소만 갱신하므로 갱신 중 링크 초점을 보존합니다.",
    "준비 완료·미배정 작업이 있고 공개 강의가 없는 경우 배정 링크가 실제 준비 결과 목록으로 연결됩니다."
  ],
  "notes": [
    {
      "skill": "keyboard-navigator",
      "note": "코드를 수정하지 않았습니다. 최종 JSON은 /tmp/sullivan-closure-keyboard.json에 저장했습니다."
    },
    {
      "skill": "keyboard-navigator",
      "note": "본 재검토는 소스 및 부모 에이전트가 실행한 결과 파일 확인입니다. 별도의 브라우저 회귀를 다시 실행하지 않았습니다."
    },
    {
      "skill": "keyboard-navigator",
      "note": "실제 VoiceOver/NVDA 발화·사용성은 확인하지 않았습니다."
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
  "checks": 10,
  "generated": "2026-11-14",
  "template": "web"
}
```
