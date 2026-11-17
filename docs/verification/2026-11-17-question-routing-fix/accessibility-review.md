# Web Accessibility Audit

An audit of web content, run on 2026-11-17. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-17 |
| Scope | 5 items |
| Skills run | cognitive-accessibility, live-region-controller |
| Tooling | node v24.22.1, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 24 |

Audited:

- `apps/extensions/student/app.js`
- `apps/extensions/student/interaction-feedback.js`
- `apps/extensions/student/speech.js`
- `scripts/test_interaction_feedback.mjs`
- `scripts/verify_student_command_routing.py`

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

24 checks ran and found nothing.

- ASR 종료는 제출 플래그와 음성 세대로 중복 처리를 막으며 원시 인식문을 확인 안내로 출력하지 않습니다.
- COGA-LOCAL-CLARIFY-003 fixed: AMBIGUOUS_REQUEST sends 재생 좀 to local clarification before legacy chat can reach ask().
- COGA-QUESTION-CLARIFY-002 fixed: EXPLANATION_REQUEST preserves the nuclear-fusion process explanation request without a topic noun allowlist.
- COGA-QUESTION-HELP-001 fixed: SUPPORT_REQUEST is anchored to the complete utterance, preserving the contextual inertia question while retaining local operational help.
- Final narrow review: canonical whole return-to-lecture commands precede question logic, while contextual return-process explanation remains a question.
- Final narrow review: commandImpl no longer contains the loose relative-seek substring branches; the resolved intent remains the media-operation authority.
- Final narrow review: exact supported ten-second seeks resolve locally; signed, decimal and unsupported relative seeks clarify locally rather than falling through to media movement.
- Final narrow review: explicit lecture and button invocations retain their legacy intent when their titles or labels contain interrogative or explanation words.
- Final narrow review: normalization removes only trailing punctuation, preserving internal decimal punctuation for conservative relative-seek rejection.
- Final narrow review: the reviewed unit-regression source includes decimal and signed seeks, return-process questions, canonical return controls and lecture/button labels containing question words.
- Leading control plus explanation requests clarify locally; the existing explicit return-to-lecture command remains available.
- Monitored command completion still requires result === true, with held and stale question responses returning false.
- StudentAnnouncer는 진행 중인 학습 설명 뒤에 일반 안내를 대기시키며 명시적인 중지는 기존 취소 경로를 유지합니다.
- Unit and installed-extension regression sources now cover all three original examples, explicit controls, local clarification, preserved questions, held output and stale response cancellation.
- Whole-command play, stop and seek matching still precedes question detection, including reviewed polite and urgent controls.
- command() passes the resolved intent to commandImpl() without a second legacy classification, and question handling preserves the original text before substring branches.
- git diff --name-only -- apps/web was empty at final review time.
- reader_mode의 질문 응답은 읽기 영역을 사용하며 StudentAnnouncer와 StudentSpeech의 앱 TTS 차단을 보존합니다.
- 명시적 question intent는 기존 느슨한 명령 매칭보다 먼저 질문 경로로 전달되며 재생·멈춤 단어를 조작 승인으로 사용하지 않습니다.
- 명시적인 중지는 동작 세대를 변경하고 음성을 취소하므로 대기 중인 질문의 오래된 응답이 새 화면 안내나 음성으로 출력되지 않습니다.
- 전체 발화에 해당하는 명확한 조작 명령은 로컬 경로를 유지하며 모호한 조작은 고정된 확인 문구를 기존 status 경로로 전달합니다.
- 질문 대기와 답변 보류는 기존 상태 안내를 사용하며 낮은 신뢰도 응답은 답변 영역이나 음성에 전달하지 않습니다.
- 최근 명령 피드백은 고정된 질문·조작 라벨과 이유 사전만 사용하며 질문 원문을 포함하지 않습니다.
- 회귀 스크립트는 질문 원문 보존, 단어에 의한 재생·중지 방지, 모호한 조작 안내, 타자 창, 중복 ASR, reader_mode 음성 차단, 보류 및 중지 후 오래된 응답 억제를 검사합니다.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **cognitive-accessibility**: Source-only re-review; no source edits, live providers, user database access or runtime regression execution were performed by this specialist.
- **cognitive-accessibility**: All three initial cognitive-accessibility findings are resolved in the reviewed source; the initial findings are preserved in cognitive-accessibility-initial.json.
- **cognitive-accessibility**: Final source signoff covers the reviewed changes and concrete regressions only; it does not claim complete natural-language recognition.
- **live-region-controller**: 소스와 회귀 검사 코드의 정적 검토입니다. 이번 검토에서 브라우저 검사, 실제 ASR 또는 스크린리더 음성을 실행하지 않았습니다.
- **live-region-controller**: 회귀 스크립트의 ASR 및 모델 응답은 명시적 대역이며 실제 공급자 검증으로 간주하지 않았습니다.
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
    "cognitive-accessibility",
    "live-region-controller"
  ],
  "scope": [
    "apps/extensions/student/app.js",
    "apps/extensions/student/interaction-feedback.js",
    "apps/extensions/student/speech.js",
    "scripts/test_interaction_feedback.mjs",
    "scripts/verify_student_command_routing.py"
  ],
  "findings": [],
  "passed": [
    "ASR 종료는 제출 플래그와 음성 세대로 중복 처리를 막으며 원시 인식문을 확인 안내로 출력하지 않습니다.",
    "COGA-LOCAL-CLARIFY-003 fixed: AMBIGUOUS_REQUEST sends 재생 좀 to local clarification before legacy chat can reach ask().",
    "COGA-QUESTION-CLARIFY-002 fixed: EXPLANATION_REQUEST preserves the nuclear-fusion process explanation request without a topic noun allowlist.",
    "COGA-QUESTION-HELP-001 fixed: SUPPORT_REQUEST is anchored to the complete utterance, preserving the contextual inertia question while retaining local operational help.",
    "Final narrow review: canonical whole return-to-lecture commands precede question logic, while contextual return-process explanation remains a question.",
    "Final narrow review: commandImpl no longer contains the loose relative-seek substring branches; the resolved intent remains the media-operation authority.",
    "Final narrow review: exact supported ten-second seeks resolve locally; signed, decimal and unsupported relative seeks clarify locally rather than falling through to media movement.",
    "Final narrow review: explicit lecture and button invocations retain their legacy intent when their titles or labels contain interrogative or explanation words.",
    "Final narrow review: normalization removes only trailing punctuation, preserving internal decimal punctuation for conservative relative-seek rejection.",
    "Final narrow review: the reviewed unit-regression source includes decimal and signed seeks, return-process questions, canonical return controls and lecture/button labels containing question words.",
    "Leading control plus explanation requests clarify locally; the existing explicit return-to-lecture command remains available.",
    "Monitored command completion still requires result === true, with held and stale question responses returning false.",
    "StudentAnnouncer는 진행 중인 학습 설명 뒤에 일반 안내를 대기시키며 명시적인 중지는 기존 취소 경로를 유지합니다.",
    "Unit and installed-extension regression sources now cover all three original examples, explicit controls, local clarification, preserved questions, held output and stale response cancellation.",
    "Whole-command play, stop and seek matching still precedes question detection, including reviewed polite and urgent controls.",
    "command() passes the resolved intent to commandImpl() without a second legacy classification, and question handling preserves the original text before substring branches.",
    "git diff --name-only -- apps/web was empty at final review time.",
    "reader_mode의 질문 응답은 읽기 영역을 사용하며 StudentAnnouncer와 StudentSpeech의 앱 TTS 차단을 보존합니다.",
    "명시적 question intent는 기존 느슨한 명령 매칭보다 먼저 질문 경로로 전달되며 재생·멈춤 단어를 조작 승인으로 사용하지 않습니다.",
    "명시적인 중지는 동작 세대를 변경하고 음성을 취소하므로 대기 중인 질문의 오래된 응답이 새 화면 안내나 음성으로 출력되지 않습니다.",
    "전체 발화에 해당하는 명확한 조작 명령은 로컬 경로를 유지하며 모호한 조작은 고정된 확인 문구를 기존 status 경로로 전달합니다.",
    "질문 대기와 답변 보류는 기존 상태 안내를 사용하며 낮은 신뢰도 응답은 답변 영역이나 음성에 전달하지 않습니다.",
    "최근 명령 피드백은 고정된 질문·조작 라벨과 이유 사전만 사용하며 질문 원문을 포함하지 않습니다.",
    "회귀 스크립트는 질문 원문 보존, 단어에 의한 재생·중지 방지, 모호한 조작 안내, 타자 창, 중복 ASR, reader_mode 음성 차단, 보류 및 중지 후 오래된 응답 억제를 검사합니다."
  ],
  "notes": [
    {
      "skill": "cognitive-accessibility",
      "note": "Source-only re-review; no source edits, live providers, user database access or runtime regression execution were performed by this specialist."
    },
    {
      "skill": "cognitive-accessibility",
      "note": "All three initial cognitive-accessibility findings are resolved in the reviewed source; the initial findings are preserved in cognitive-accessibility-initial.json."
    },
    {
      "skill": "cognitive-accessibility",
      "note": "Final source signoff covers the reviewed changes and concrete regressions only; it does not claim complete natural-language recognition."
    },
    {
      "skill": "live-region-controller",
      "note": "소스와 회귀 검사 코드의 정적 검토입니다. 이번 검토에서 브라우저 검사, 실제 ASR 또는 스크린리더 음성을 실행하지 않았습니다."
    },
    {
      "skill": "live-region-controller",
      "note": "회귀 스크립트의 ASR 및 모델 응답은 명시적 대역이며 실제 공급자 검증으로 간주하지 않았습니다."
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
  "checks": 24,
  "generated": "2026-11-17",
  "template": "web"
}
```
