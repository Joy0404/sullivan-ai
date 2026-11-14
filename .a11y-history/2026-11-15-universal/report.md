# Web Accessibility Audit

An audit of web content, run on 2026-11-14. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-14 |
| Scope | 6 items |
| Skills run | keyboard-navigator, live-region-controller |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 19 |

Audited:

- `apps/extensions/guardian/app.js`
- `apps/extensions/guardian/workspace.html`
- `apps/extensions/student/app.js`
- `apps/extensions/student/media.js`
- `apps/extensions/student/workspace.html`
- `docs/verification/2026-11-15-universal/round4/results.json`

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

19 checks ran and found nothing.

- grant-player는 설명된 출처 목록과 연결된 기본 button이며 Enter로 권한을 요청합니다.
- round9 U09.connection_focus_preserved 결과에서 정상 재생 버튼 복귀와 지연 연결 중 메모 초점 보존이 모두 통과함을 확인했습니다.
- voiceschanged는 현재 음성 선택값을 보존하고 계정 초기화만 device.voice_uri로 재설정합니다.
- 권한 거부 후 버튼이 유지되어 다시 허용하거나 자료 읽기를 계속할 수 있습니다.
- 권한 거절 시 같은 버튼 재시도와 자료 읽기를 안내함
- 권한 대기 중 실제 초점 변화 여부와 내부 stopAll 이후 기준 세대를 구분해 정상 연결은 재생 버튼으로 복귀하고 새 입력은 보존합니다.
- 권한 버튼이 사라질 때 그 버튼에 초점이 있으면 재생 또는 원본 연결 버튼으로 복원하며 다른 입력 초점은 이동하지 않습니다.
- 로컬 디코더 실패는 재생 리소스를 정리하고 상태 영역에 대체 형식을 알리며 다른 입력으로 이동한 초점을 빼앗지 않습니다.
- 로컬 메타정보 등록 입력 설명과 준비 결과 메시지는 원본 미전송·영상 분석 미실행을 구분함
- 로컬 코덱 오류를 최종 상태로 알리고 재생 가능한 파일 대안을 제공함
- 로컬 파일 식별·디코더 확인 시작도 connectionNotice를 통해 상태 영역과 앱 음성에 안내함
- 보존된 round4 결과에서 기본 Enter 거부·재허용, 음성 선택 보존, 디코더 실패 정리 및 검사 화면 axe 0건을 확인했습니다.
- 보호자 local 방식은 원본 파일 선택을 표시·필수화하고 실제 분석 동의는 숨김·비활성화합니다. video 방식은 실제 분석 동의를 요구합니다.
- 사이트 연결의 진행·최종 결과가 같은 connection live region을 사용함
- 음성 명령은 권한 버튼으로 초점을 안내하고 실제 Enter로 요청을 계속하도록 합니다.
- 자료 없는 질문·학습 도구 요청은 자료 또는 실제 분석 필요를 명시함
- 재생용 등록과 영상 분석 미실행을 학생 열기 상태에서 구분함
- 추가 권한 origin 목록을 앱 음성 안내와 버튼의 리더 설명에 전달함
- 취소·강의 전환 뒤 늦은 오류를 폐기함

## Needs a human

Items a skill could not decide, or could not check automatically.

- **keyboard-navigator**: 보고서 사본: /tmp/sullivan-universal-keyboard-final.json. 코드 수정 없음.
- **keyboard-navigator**: 별도의 런타임 검사를 실행하지 않고 소스 및 부모 실행 결과를 확인했습니다.
- **keyboard-navigator**: 실제 VoiceOver/NVDA 발화와 OS 권한 대화상자 조작은 미검증입니다.
- **keyboard-navigator**: INTERNAL-STOP-FOCUS-REVISION 지적은 최신 소스에서 해결되었습니다. U09는 제어 가능한 확장 문서에서 panel 분기를 실행한 시험이며 실제 Chrome 패널 열기와 구분합니다.
- **live-region-controller**: 최종 소스 재검토 범위의 미해결 지적 없음
- **live-region-controller**: 실제 VoiceOver/NVDA 낭독과 앱 음성 청취는 실행하지 않음
- **live-region-controller**: 이전 LIVE-CONNECTION-TERMINAL·LIVE-PLAYER-ORIGIN-VOICE·LIVE-LOCAL-CONNECT-PROGRESS 지적의 코드 수정을 확인함
- **live-region-controller**: 코드 변경 없이 검토 JSON만 /tmp에 저장함

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
    "apps/extensions/student/app.js",
    "apps/extensions/student/media.js",
    "apps/extensions/student/workspace.html",
    "docs/verification/2026-11-15-universal/round4/results.json"
  ],
  "findings": [],
  "passed": [
    "grant-player는 설명된 출처 목록과 연결된 기본 button이며 Enter로 권한을 요청합니다.",
    "round9 U09.connection_focus_preserved 결과에서 정상 재생 버튼 복귀와 지연 연결 중 메모 초점 보존이 모두 통과함을 확인했습니다.",
    "voiceschanged는 현재 음성 선택값을 보존하고 계정 초기화만 device.voice_uri로 재설정합니다.",
    "권한 거부 후 버튼이 유지되어 다시 허용하거나 자료 읽기를 계속할 수 있습니다.",
    "권한 거절 시 같은 버튼 재시도와 자료 읽기를 안내함",
    "권한 대기 중 실제 초점 변화 여부와 내부 stopAll 이후 기준 세대를 구분해 정상 연결은 재생 버튼으로 복귀하고 새 입력은 보존합니다.",
    "권한 버튼이 사라질 때 그 버튼에 초점이 있으면 재생 또는 원본 연결 버튼으로 복원하며 다른 입력 초점은 이동하지 않습니다.",
    "로컬 디코더 실패는 재생 리소스를 정리하고 상태 영역에 대체 형식을 알리며 다른 입력으로 이동한 초점을 빼앗지 않습니다.",
    "로컬 메타정보 등록 입력 설명과 준비 결과 메시지는 원본 미전송·영상 분석 미실행을 구분함",
    "로컬 코덱 오류를 최종 상태로 알리고 재생 가능한 파일 대안을 제공함",
    "로컬 파일 식별·디코더 확인 시작도 connectionNotice를 통해 상태 영역과 앱 음성에 안내함",
    "보존된 round4 결과에서 기본 Enter 거부·재허용, 음성 선택 보존, 디코더 실패 정리 및 검사 화면 axe 0건을 확인했습니다.",
    "보호자 local 방식은 원본 파일 선택을 표시·필수화하고 실제 분석 동의는 숨김·비활성화합니다. video 방식은 실제 분석 동의를 요구합니다.",
    "사이트 연결의 진행·최종 결과가 같은 connection live region을 사용함",
    "음성 명령은 권한 버튼으로 초점을 안내하고 실제 Enter로 요청을 계속하도록 합니다.",
    "자료 없는 질문·학습 도구 요청은 자료 또는 실제 분석 필요를 명시함",
    "재생용 등록과 영상 분석 미실행을 학생 열기 상태에서 구분함",
    "추가 권한 origin 목록을 앱 음성 안내와 버튼의 리더 설명에 전달함",
    "취소·강의 전환 뒤 늦은 오류를 폐기함"
  ],
  "notes": [
    {
      "skill": "keyboard-navigator",
      "note": "보고서 사본: /tmp/sullivan-universal-keyboard-final.json. 코드 수정 없음."
    },
    {
      "skill": "keyboard-navigator",
      "note": "별도의 런타임 검사를 실행하지 않고 소스 및 부모 실행 결과를 확인했습니다."
    },
    {
      "skill": "keyboard-navigator",
      "note": "실제 VoiceOver/NVDA 발화와 OS 권한 대화상자 조작은 미검증입니다."
    },
    {
      "skill": "keyboard-navigator",
      "note": "INTERNAL-STOP-FOCUS-REVISION 지적은 최신 소스에서 해결되었습니다. U09는 제어 가능한 확장 문서에서 panel 분기를 실행한 시험이며 실제 Chrome 패널 열기와 구분합니다."
    },
    {
      "skill": "live-region-controller",
      "note": "최종 소스 재검토 범위의 미해결 지적 없음"
    },
    {
      "skill": "live-region-controller",
      "note": "실제 VoiceOver/NVDA 낭독과 앱 음성 청취는 실행하지 않음"
    },
    {
      "skill": "live-region-controller",
      "note": "이전 LIVE-CONNECTION-TERMINAL·LIVE-PLAYER-ORIGIN-VOICE·LIVE-LOCAL-CONNECT-PROGRESS 지적의 코드 수정을 확인함"
    },
    {
      "skill": "live-region-controller",
      "note": "코드 변경 없이 검토 JSON만 /tmp에 저장함"
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
  "checks": 19,
  "generated": "2026-11-14",
  "template": "web"
}
```
