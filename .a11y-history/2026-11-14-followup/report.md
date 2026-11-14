# Web Accessibility Audit

An audit of web content, run on 2026-11-14. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-14 |
| Scope | 5 items |
| Skills run | keyboard-navigator, live-region-controller |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 20 |

Audited:

- `apps/extensions/guardian/app.js`
- `apps/extensions/guardian/workspace.html`
- `apps/extensions/shared/ui.js`
- `apps/extensions/student/app.js`
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

20 checks ran and found nothing.

- error.reported로 공통 오류 영역의 중복 안내를 막음
- 명시 저장·재시도는 저장 중 상태와 반복 실패를 다시 안내함
- 백그라운드 반복 실패의 앱 음성을 억제하고 복구 시 한 번 안내함
- 상태별 총계는 비 live 영역에 표시함
- 성공 뒤 재시도 버튼을 숨기기 전에 기본 저장 버튼으로 초점을 이동함
- 소스 재검토: 기존 Space·Shift·Tab 패널 동작과 Esc 해제 경로를 유지합니다.
- 소스 재검토: 잘못된 위치 입력은 error.field를 통해 해당 기본 number 입력으로 초점을 이동합니다.
- 소스 재검토: 저장 성공 시 재시도 버튼에 초점이 있을 때만 영구적인 저장 submit 버튼으로 옮긴 뒤 재시도 버튼을 숨깁니다.
- 소스 재검토: 저장 재시도는 기본 button으로 추가됐으며 처리 중 DOM에 유지됩니다.
- 소스 재검토: 저장 중 다른 입력으로 이동한 사용자의 초점을 성공 응답이 빼앗지 않습니다.
- 소스 재검토: 준비 목록에서 초점을 가진 작업이 사라지면 인접 작업 또는 preparations-title로 복원합니다.
- 소스 재검토: 준비 상태 필터는 기본 select, 검색은 라벨이 연결된 기본 search 입력이며 두 컨트롤을 다시 생성하지 않습니다.
- 소스 재검토: 준비 상태·검색 입력에 있는 초점은 renderPreparations가 이동하지 않습니다.
- 수동 위치 이동을 동반하는 재시도도 notifySaveFailure를 seek와 save에 전달함
- 수동 저장 완료는 하나의 live region으로 전달함
- 외부 스크린리더 모드는 앱 음성을 차단함
- 준비 running 및 최종 상태 전환을 job-status에 안내함
- 준비 목록 전체는 live region 밖에 있음
- 첫 저장 실패를 중앙 save 처리에서 상태 영역과 앱 음성에 전달함
- 필터 결과 수는 정적 role=status 영역에 값이 바뀔 때만 안내함

## Needs a human

Items a skill could not decide, or could not check automatically.

- **keyboard-navigator**: 범위 내 최종 소스 검토에서 남은 키보드·초점 지적은 없습니다.
- **keyboard-navigator**: 최종 런타임 키보드·회귀 검사는 주 에이전트가 별도로 실행 중이며 이 JSON은 해당 검사 통과를 주장하지 않습니다.
- **keyboard-navigator**: 실제 VoiceOver/NVDA 및 사람이 듣는 음성 검증은 수행하지 않았습니다.
- **live-region-controller**: 최종 소스 재검토에서 이 범위의 미해결 지적 없음
- **live-region-controller**: 실제 VoiceOver/NVDA 발화와 앱 음성 청취는 실행하지 않음
- **live-region-controller**: S10/S11/S13의 합성 음성 경계 회귀 통과는 부모 에이전트가 수행한 근거로 별도 기록함
- **live-region-controller**: 필터 입력에 별도 타이핑 디바운스는 없지만 변한 결과 수만 안내하며 이 범위에서 차단 결함으로 판정하지 않음

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
    "apps/extensions/guardian/workspace.html",
    "apps/extensions/shared/ui.js",
    "apps/extensions/student/app.js",
    "apps/extensions/student/workspace.html"
  ],
  "findings": [],
  "passed": [
    "error.reported로 공통 오류 영역의 중복 안내를 막음",
    "명시 저장·재시도는 저장 중 상태와 반복 실패를 다시 안내함",
    "백그라운드 반복 실패의 앱 음성을 억제하고 복구 시 한 번 안내함",
    "상태별 총계는 비 live 영역에 표시함",
    "성공 뒤 재시도 버튼을 숨기기 전에 기본 저장 버튼으로 초점을 이동함",
    "소스 재검토: 기존 Space·Shift·Tab 패널 동작과 Esc 해제 경로를 유지합니다.",
    "소스 재검토: 잘못된 위치 입력은 error.field를 통해 해당 기본 number 입력으로 초점을 이동합니다.",
    "소스 재검토: 저장 성공 시 재시도 버튼에 초점이 있을 때만 영구적인 저장 submit 버튼으로 옮긴 뒤 재시도 버튼을 숨깁니다.",
    "소스 재검토: 저장 재시도는 기본 button으로 추가됐으며 처리 중 DOM에 유지됩니다.",
    "소스 재검토: 저장 중 다른 입력으로 이동한 사용자의 초점을 성공 응답이 빼앗지 않습니다.",
    "소스 재검토: 준비 목록에서 초점을 가진 작업이 사라지면 인접 작업 또는 preparations-title로 복원합니다.",
    "소스 재검토: 준비 상태 필터는 기본 select, 검색은 라벨이 연결된 기본 search 입력이며 두 컨트롤을 다시 생성하지 않습니다.",
    "소스 재검토: 준비 상태·검색 입력에 있는 초점은 renderPreparations가 이동하지 않습니다.",
    "수동 위치 이동을 동반하는 재시도도 notifySaveFailure를 seek와 save에 전달함",
    "수동 저장 완료는 하나의 live region으로 전달함",
    "외부 스크린리더 모드는 앱 음성을 차단함",
    "준비 running 및 최종 상태 전환을 job-status에 안내함",
    "준비 목록 전체는 live region 밖에 있음",
    "첫 저장 실패를 중앙 save 처리에서 상태 영역과 앱 음성에 전달함",
    "필터 결과 수는 정적 role=status 영역에 값이 바뀔 때만 안내함"
  ],
  "notes": [
    {
      "skill": "keyboard-navigator",
      "note": "범위 내 최종 소스 검토에서 남은 키보드·초점 지적은 없습니다."
    },
    {
      "skill": "keyboard-navigator",
      "note": "최종 런타임 키보드·회귀 검사는 주 에이전트가 별도로 실행 중이며 이 JSON은 해당 검사 통과를 주장하지 않습니다."
    },
    {
      "skill": "keyboard-navigator",
      "note": "실제 VoiceOver/NVDA 및 사람이 듣는 음성 검증은 수행하지 않았습니다."
    },
    {
      "skill": "live-region-controller",
      "note": "최종 소스 재검토에서 이 범위의 미해결 지적 없음"
    },
    {
      "skill": "live-region-controller",
      "note": "실제 VoiceOver/NVDA 발화와 앱 음성 청취는 실행하지 않음"
    },
    {
      "skill": "live-region-controller",
      "note": "S10/S11/S13의 합성 음성 경계 회귀 통과는 부모 에이전트가 수행한 근거로 별도 기록함"
    },
    {
      "skill": "live-region-controller",
      "note": "필터 입력에 별도 타이핑 디바운스는 없지만 변한 결과 수만 안내하며 이 범위에서 차단 결함으로 판정하지 않음"
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
  "checks": 20,
  "generated": "2026-11-14",
  "template": "web"
}
```
