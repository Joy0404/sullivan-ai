# Web Accessibility Audit

An audit of web content, run on 2026-11-13. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-13 |
| Scope | 23 items |
| Skills run | accessibility-lead, alt-text-headings, aria-specialist, contrast-master, forms-specialist, live-region-controller, media-accessibility |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 53 |

Audited:

- `apps/api/app/guardian_preparation.py`
- `apps/api/app/main.py:123`
- `apps/extensions/guardian/app.js`
- `apps/extensions/guardian/workspace.html`
- `apps/extensions/shared/accounts.html`
- `apps/extensions/shared/accounts.js`
- `apps/extensions/shared/base.css`
- `apps/extensions/shared/client.js`
- `apps/extensions/shared/ui.js`
- `apps/extensions/student/app.js`
- `apps/extensions/student/keyboard.js`
- `apps/extensions/student/media-store.js`
- `apps/extensions/student/media.js`
- `apps/extensions/student/speech.js`
- `apps/extensions/student/video-control.js`
- `apps/extensions/student/workspace.html`
- `apps/web/app.js:946`
- `apps/web/passage-tools.js`
- `apps/web/tokens.css`
- `docs/EXTENSION_FEATURE_AUDIT.md`
- `docs/EXTENSION_FEATURE_RESTORATION.md`
- `generated student/guardian extension interfaces`
- `scripts/build_extensions.py`

## Executive summary

Fail. Critical or serious findings must be fixed before this ships.

The headline numbers for this run.

| Measure | Value |
|---|---|
| Score | 83 out of 100 |
| Grade | B |
| Findings | 18 |
| Blocking (critical plus serious) | 4 |
| Verdict | Fail |

## Severity breakdown

Counts by severity, highest impact first.

| Severity | Count | What it means |
|---|---:|---|
| critical | 0 | Blocks a person from completing the task |
| serious | 4 | Major barrier with a difficult workaround |
| moderate | 12 | Real friction, workaround exists |
| minor | 2 | Noticeable but rarely blocking |

## Findings

18 findings, ordered by severity then by rule.

### Serious (4)

Each row names the rule, the criterion it fails, where it is, and what to change.

| Rule | WCAG | Location | Problem | Fix |
|---|---|---|---|---|
| `AUDIT-PENDING-PLAY-FOCUS` | n/a | apps/extensions/student/media.js:56 | 새 초점 음성 안내 중 늦은 재생 완료가 영상을 다시 켠다. | play 응답 후에도 안내 소유권과 초점/작업 티켓을 검사하거나 안내 hold와 재생을 하나의 취소 체계로 묶어라. |
| `AUDIT-STALE-PERMISSION-SOURCE` | n/a | apps/extensions/student/app.js:248 | 이전 강의의 권한 완료가 다른 강의에 이전 원본 영상을 연결한다. | 권한 요청 전 lesson/view/generation을 캡처하고 완료 후 동일한지 검사한 뒤 연결하라. 변경되면 요청을 취소하고 기존 원본을 새 강의에 적용하지 말라. |
| `AUDIT-STALE-SEEK-PROGRESS` | n/a | apps/extensions/student/app.js:245 | 이전 구간 이동 완료가 새 강의의 학습 위치를 덮어쓴다. | media.seek 이후에도 저장 전 lesson/action/view를 검사하고 작업 시작 때 선택한 강의에만 결과를 반영하라. |
| `LIVE-APP-VOICE-DIRECT-STATUS` | n/a | apps/extensions/student/app.js:304-305,537,553 | Playback failures and learning-view ownership loss stop the lecture but update only ARIA text, bypassing built-in app speech for students without an external screen reader. | Route important connection-loss and lease-loss messages through a mode-aware announcement helper: app TTS when enabled, persistent ARIA in reader mode, deduplicated to avoid polling spam. Preserve ordinary silent progress updates. |

### Moderate (12)

Each row names the rule, the criterion it fails, where it is, and what to change.

| Rule | WCAG | Location | Problem | Fix |
|---|---|---|---|---|
| `AUDIT-DELAYED-LECTURE-FOCUS` | n/a | apps/extensions/student/app.js:128 | 강의가 늦게 열리면 사용자가 입력 중인 명령창에서 초점을 빼앗는다. | 강의 조회 전후의 사용자 상호작용을 비교해 사용자가 이미 이동했으면 강의 제목으로 강제 이동하지 말라. |
| `AUDIT-DISABLED-EDITOR-SPACE` | n/a | apps/extensions/student/keyboard.js:40 | Space 명령을 꺼도 입력 중 두 번 누르기 중지가 실행된다. | 편집 중 중지 분기도 Space 설정을 존중하도록 하거나 항상 활성인 긴급 중지 예외를 명확히 구분·설명하라. |
| `AUDIT-HOME-BUTTON-COMMAND` | n/a | apps/extensions/student/app.js:402 | 홈에 표시된 버튼의 실행 명령이 강의 선택 전에는 거부된다. | 강의가 필요 없는 버튼 명령을 needLesson 이전에 처리하고 실제 보이는 허용 버튼에만 적용하라. |
| `AUDIT-REMOVED-LECTURE-FOCUS` | n/a | apps/extensions/student/app.js:92 | 초점이 있던 강의가 새 목록에서 사라지면 초점이 BODY로 떨어진다. | 목록 교체 후 원래 항목이 없으면 다음 항목이나 목록 제목으로 초점을 복원하라. |
| `AUDIT-SHIFT-ARROW` | n/a | apps/extensions/student/keyboard.js:35 | Shift+방향키가 기본 수정키 동작 대신 강의를 이동시킨다. | Shift 등 수정키 조합은 강의 탐색에서 제외하고 기본 편집·선택 동작을 유지하라. |
| `AUDIT-VOICE-UNDERLINE-FOCUS` | n/a | apps/extensions/student/app.js:334 | 문단 안에서 음성으로 밑줄을 표시하면 초점이 BODY로 떨어진다. | 재렌더링 후 기존 문단/문장에 대응하는 컨트롤로 초점을 복원하고 입력 경로를 보존하라. |
| `FORM-AGGREGATE-LIMIT-ERROR` | 3.3.1 A | apps/extensions/guardian/app.js:185 | An aggregate material-size validation failure produces only a generic request-format error, without identifying the exceeded limit. | Validate the documented total text limit before submitting and identify the affected materials input, or return a specific sanitized aggregate-limit error. Preserve selected files and give an actionable split/reduce instruction. |
| `FORM-GUIDED-RETRY-STEP` | n/a | apps/extensions/guardian/app.js:84 | Retrying a preparation while guided entry is on step 3 leaves replacement metadata hidden and the final summary stale. | Reset guided prepareStep to the first step, refresh the step view and summary, then focus the visible title or first-step legend when loading a failed/interrupted preparation for retry. |
| `LIVE-NUMERIC-SETTING-VALUE-SILENCE` | n/a | apps/extensions/student/speech.js:92-104; apps/extensions/student/app.js:534-536; workspace.html:53-57 | Built-in guidance names numeric speed, volume and pitch fields without their current values and does not announce arrow-key changes, so app-only users cannot verify adjustments. | Include nonsensitive numeric setting values and units in control guidance and announce committed or debounced changes for these specific fields. Continue excluding password, account and free-text values. |
| `LIVE-READER-SETTING-FOCUS-RACE` | n/a | apps/extensions/shared/ui.js:53-61 versus apps/extensions/student/app.js:631-632 | Login focuses the workspace before applying the account’s external-reader preference, allowing app TTS to start under the previous default mode. | Apply student mode before the authenticated focus move, or suppress/cancel initial guidance until account preferences have been applied. Retain the user-navigation guard for delayed restoration. |
| `LIVE-VOICE-TEST-RESUME-LOSS` | n/a | apps/extensions/student/app.js:538-540; apps/extensions/student/speech.js:4,14-15 | Clicking the app voice test while its focused-control guidance is holding playback discards the saved playing state, leaving the lecture paused after the test. | Preserve the currently held playback intent when replacing control guidance with the explicit test, then resume only with unchanged view/lesson/fence. Do not force play when initially paused. |
| `MEDIA-HIGHLIGHT-SENTENCE-PARITY` | n/a | apps/extensions/student/app.js:140 | Passage rendering drops the original per-sentence controls and explicit highlighted-sentence markers even when highlighted data is present. | Render sentences as individually labelled native controls or equivalent navigable items and expose highlighted status in visible text/programmatic names. Preserve paragraph reading and underline controls alongside sentence selection. |

### Minor (2)

Each row names the rule, the criterion it fails, where it is, and what to change.

| Rule | WCAG | Location | Problem | Fix |
|---|---|---|---|---|
| `AUDIT-STALE-TEXT-COMMAND` | n/a | apps/extensions/student/app.js:442 | 다시 연 타자 명령창에 이전 실행 명령이 남는다. | 원본과 같이 새 명령 입력을 초기화하고 이전 명령 재사용은 명시적으로 제공하라. |
| `LIVE-GUARDIAN-PREVIEW-PENDING-ERROR` | n/a | apps/extensions/guardian/app.js:162-168; apps/extensions/shared/ui.js:21 | A failed guardian preview question leaves its result status saying the answer is still being checked even after the global error is announced. | When the request fails, replace the pending preview status with a terminal failure for the same preparation, or clear it before forwarding the error. Guard against replacing a newer selection’s status. |

## Remediation priorities

The 4 blocking findings, in this order:

1. `AUDIT-PENDING-PLAY-FOCUS` at apps/extensions/student/media.js:56. play 응답 후에도 안내 소유권과 초점/작업 티켓을 검사하거나 안내 hold와 재생을 하나의 취소 체계로 묶어라.
2. `AUDIT-STALE-PERMISSION-SOURCE` at apps/extensions/student/app.js:248. 권한 요청 전 lesson/view/generation을 캡처하고 완료 후 동일한지 검사한 뒤 연결하라. 변경되면 요청을 취소하고 기존 원본을 새 강의에 적용하지 말라.
3. `AUDIT-STALE-SEEK-PROGRESS` at apps/extensions/student/app.js:245. media.seek 이후에도 저장 전 lesson/action/view를 검사하고 작업 시작 때 선택한 강의에만 결과를 반영하라.
4. `LIVE-APP-VOICE-DIRECT-STATUS` at apps/extensions/student/app.js:304-305,537,553. Route important connection-loss and lease-loss messages through a mode-aware announcement helper: app TTS when enabled, persistent ARIA in reader mode, deduplicated to avoid polling spam. Preserve ordinary silent progress updates.

The remaining 14 moderate and minor findings can follow in normal work.

## What passed

35 checks ran and found nothing.

- A first-in-document skip link points to focusable #main.
- Both pages have one H1; workspace and account sections use H2, principal tools H3/H4, generated concept/chat sections H5.
- Caption/underline and guided-entry toggles update native button aria-pressed state.
- Connected guidance and external-reader focus now pause playback; no-lesson guidance remains available.
- Current-screen description still selects a nearest prepared safe gap; the original implemented the same behavior. The extension announces the prepared timestamp rather than claiming fresh-frame analysis.
- Forced-colors emulation preserved native system text/background, control boundaries and focus outlines. The stylesheet does not suppress forced-color adjustment.
- Fresh generated student and guardian HTML has no missing aria-labelledby/describedby/controls ID targets.
- Fresh rendered Chromium checks using the current shared CSS and original token sheet measured normal text/primary button contrast at 14.09:1, primary hover at 8.70:1, secondary hover/notice text at 12.26:1 and error text at 7.31:1.
- Fresh source inspection confirms bounded lecturer-to-AI sequencing with cancellation fences, advertisement/unknown-duration handling, origin tracking and stop controls.
- Freshly inspected native labels, autocomplete and password instructions for both generated login/signup/recovery interfaces, plus guardian assignment/settings and student learning/preferences/record forms.
- Freshly reread current source instead of reusing prior clean reports.
- Generated role-specific page titles identify student versus guardian purpose.
- Guardian preview exposes transcript, safe descriptions, concepts, review categories, study guide, reasons, explicit file-delivery instructions and consented questions.
- Guardian terminal job transitions and connection failures use persistent deduplicated status channels.
- Home command entry and onboarding are reachable before selecting a lesson.
- Links retain an underline; errors and toggle/selection semantics do not depend solely on color. Reduced-motion handling is present and no authored animation was found.
- Local/preview videos have accessible names, app/native controls, textual materials and conditional prepared-caption tracks.
- Narration cancellation generation and media fence protect normal stale completion and prior-state resume paths.
- Native buttons, selects, checkboxes, fields, details and dialogs retain appropriate names and semantics.
- Native dialogs have named headings and explanatory descriptions.
- Native player controls and separate student playback/stop/volume/mute/caption controls are present; original files are selected locally and student storage is opt-in and account/lecture scoped.
- Natural Korean voice selection, pronunciation normalization, sentence chunking, style/edge prosody and cancellable breath delays are implemented.
- No inline img/svg/image-input content was found in generated pages; manifest icons use the role-specific extension name rather than unlabeled page graphics.
- Ordinary reader answers avoid duplicating full response through two narration channels.
- Pairing consent references guardian identity and sharing scope; unlink, withdrawal and permanent deletion actions associate visible consequence questions and provide cancellation.
- Persistent status/alert containers exist before updates; rapidly changing playback time remains non-live.
- Recovery codes are readonly/selectable, downloadable and explicitly clearable; prepared-note export uses a labelled native button and accessible status feedback.
- Review includes summary, key-segment descriptions, visual-only information, highlighted review entries and study-guide material; text remains available without connected video.
- Source label and preferred mode are carried by both JSON and multipart contracts. Preview questions require explicit data-transfer consent.
- Source switches disable irrelevant native controls and required states; guided entry groups steps with fieldsets/legends and validates ordinary required fields. The retry exception is reported separately.
- Temporary generation of both packages confirmed lang=ko, exactly one title and one main per page.
- Text fields, textareas, selects, primary/secondary buttons, links and summary controls all retained a computed visible focus outline in the probe.
- Text input, textarea and select boundaries measured 3.70:1 against white. The 4px focus outline with 3px offset measured 6.96:1 against white.
- The static generated student outline contains 19 heading elements and guardian contains 17, including hidden states; neither has a downward skipped level.
- Verified student-local media and guardian preview media generate WebVTT caption tracks from timed transcript segments. Missing identity/timed caption data is disclosed; caption accuracy was not evaluated.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **accessibility-lead**: 제품 소스를 수정하지 않은 추가 브라우저 재현 결과다. 기능 동등성 문제이며 n/a는 WCAG 위반을 단정하지 않음을 뜻한다.
- **live-region-controller**: 원본 소스 재검토 후 부모 에이전트가 실제 임시 Chromium 확장 문서에서 다섯 항목 모두를 재현했다. 음성은 호출 기록용 시험 장치이며 실제 사람이 듣는 음성·OS 스크린리더 실행을 주장하지 않는다.
- **live-region-controller**: runtime-live의 최초 환경 오류 및 runtime-keyboard의 최초 CSP 검사 도구 오류는 제품 오류로 세지 않았다. 수정한 감사 스크립트로 새 임시 프로필에서 재실행했다.
- **forms-specialist**: Fresh 0.4.2 audit on 2026-11-13. Two completed isolated Chromium 156.0.8078.4 actual-extension DOM probe runs used synthetic accounts/data and temporary profiles. No product/test source was edited.
- **forms-specialist**: Reproduce FORM-GUIDED-RETRY-STEP: ensure a failed/interrupted preparation exists; enable 3-step entry; complete metadata and materials to reach step 3; click that job’s 다시 준비 button. The replaced title is hidden in step 1 while the stage and summary remain on step 3. The probe seeded a synthetic failed job in its temporary database.
- **forms-specialist**: Reproduce FORM-AGGREGATE-LIMIT-ERROR: use full entry, fill a title, choose four .txt files containing 260,001 ASCII characters each, then submit. Observe HTTP 422 and the generic alert despite the documented 1,000,000-character total limit.
- **forms-specialist**: Evidence: runtime-forms-media/probe-results.json, runtime-forms-media/guided-retry-result.png, runtime-form-limits/probe-results.json and runtime-form-limits/total-limit-error.png.
- **forms-specialist**: No real assistive-technology, audible TTS, microphone, external video-site or live-provider tests were performed. Axe was not enabled in these specialist probe runs.
- **media-accessibility**: Fresh 0.4.2 audit on 2026-11-13. The highlighted-passage result was observed in an actual temporary-profile extension DOM probe; no real audio, AT or provider behavior was tested.
- **media-accessibility**: F44 reproduction: supply a snapshot passage with at least one sentence highlighted=true, open it in the student extension, and inspect the passage. Highlight identity and individual sentence controls are absent. Probe evidence is runtime-forms-media/probe-results.json.
- **media-accessibility**: F16 remains a simpler dashboard: lists and next-step text exist, while the original detailed status/dashboard experience remains partial. F23 still reports coarse queued/running/completed/failed/interrupted states without provider internal stages; neither limitation is counted as a new WCAG violation here.
- **media-accessibility**: F34 remains conditional: source-tab control requires a compatible standard HTML video and rejects DRM; actual YouTube/target-site compatibility was not independently tested by this specialist.
- **media-accessibility**: F36 remains explicit manual original-file delivery. Hash/size metadata and prepared materials are shared; automatic transfer between independent extension origins is not implemented.
- **media-accessibility**: F56 source retains dirty-note, error and retry paths, but fresh offline/reconnection fault injection is handled separately by the parent agent and is not claimed as this specialist’s verification.
- **media-accessibility**: The generic harness success list includes historical phase labels; only the explicitly described custom probes and baseline harness assertions were executed here. No inference of full media/learning parity should be made from that list.
- **aria-specialist**: Static source and temporary generated-HTML inspection only; no actual assistive-technology execution.
- **aria-specialist**: App-only speech-delivery omissions are in live.json; no duplicate formal ARIA finding is asserted.
- **aria-specialist**: Named region density is high in the learning surface, but no conformance failure is inferred from count alone.
- **alt-text-headings**: Static generated-HTML parser and dynamic-generation source inspection; not a rendered accessibility-tree or media-alternative completeness certification.
- **alt-text-headings**: No actual video/audio quality or screen-reader heading traversal was executed.
- **alt-text-headings**: Actual lesson-specific full-tab title differentiation remains a usability consideration; generic application titles were not marked as a conformance failure.
- **contrast-master**: Fresh 0.4.2 review on 2026-11-13. Shared palette values were also collected from both actual extension pages. Detailed normal/hover/focus/forced-color measurements used a standalone Chromium DOM loaded with the exact current CSS and tokens.
- **contrast-master**: Evidence: contrast-runtime.json and runtime-forms-media/probe-results.json. No manual screen magnifier or assistive-technology session was performed.
- **contrast-master**: Native video chrome and arbitrary user-provided video content were not certified for contrast or caption quality by these CSS measurements.

## Next steps

1. Fix the 4 blocking findings above, starting with any repeated component.
2. Re-run this audit and check the delta section for regressions.
3. Wire the scan into continuous integration so the next regression is caught before review.

Automated checks find a minority of accessibility barriers. A passing score is a floor, not a guarantee.

## Findings data

The merged findings, embedded so the next run can compute a delta without parsing this document.

```json a11y-findings
{
  "skills": [
    "accessibility-lead",
    "alt-text-headings",
    "aria-specialist",
    "contrast-master",
    "forms-specialist",
    "live-region-controller",
    "media-accessibility"
  ],
  "scope": [
    "apps/api/app/guardian_preparation.py",
    "apps/api/app/main.py:123",
    "apps/extensions/guardian/app.js",
    "apps/extensions/guardian/workspace.html",
    "apps/extensions/shared/accounts.html",
    "apps/extensions/shared/accounts.js",
    "apps/extensions/shared/base.css",
    "apps/extensions/shared/client.js",
    "apps/extensions/shared/ui.js",
    "apps/extensions/student/app.js",
    "apps/extensions/student/keyboard.js",
    "apps/extensions/student/media-store.js",
    "apps/extensions/student/media.js",
    "apps/extensions/student/speech.js",
    "apps/extensions/student/video-control.js",
    "apps/extensions/student/workspace.html",
    "apps/web/app.js:946",
    "apps/web/passage-tools.js",
    "apps/web/tokens.css",
    "docs/EXTENSION_FEATURE_AUDIT.md",
    "docs/EXTENSION_FEATURE_RESTORATION.md",
    "generated student/guardian extension interfaces",
    "scripts/build_extensions.py"
  ],
  "findings": [
    {
      "rule": "AUDIT-PENDING-PLAY-FOCUS",
      "severity": "serious",
      "location": "apps/extensions/student/media.js:56",
      "summary": "새 초점 음성 안내 중 늦은 재생 완료가 영상을 다시 켠다.",
      "fix": "play 응답 후에도 안내 소유권과 초점/작업 티켓을 검사하거나 안내 hold와 재생을 하나의 취소 체계로 묶어라.",
      "evidence": "supplement/observations.json pending_play_then_focus: before_release_paused=true, after_release_paused=false, guidance_held=true.",
      "component": "음성 안내와 영상 경합",
      "wcag": "n/a",
      "confidence": "high",
      "foundBy": [
        "accessibility-lead"
      ]
    },
    {
      "rule": "AUDIT-STALE-PERMISSION-SOURCE",
      "severity": "serious",
      "location": "apps/extensions/student/app.js:248",
      "summary": "이전 강의의 권한 완료가 다른 강의에 이전 원본 영상을 연결한다.",
      "fix": "권한 요청 전 lesson/view/generation을 캡처하고 완료 후 동일한지 검사한 뒤 연결하라. 변경되면 요청을 취소하고 기존 원본을 새 강의에 적용하지 말라.",
      "evidence": "runtime-keyboard/results.json: 새 강의의 playback은 YouTube이나 연결 lease.url은 이전 강의의 시험용 원본 URL, 연결 완료 표시. 실제 worker·영상 탭, 권한 Promise만 지연.",
      "component": "강의 원본 연결",
      "wcag": "n/a",
      "confidence": "high",
      "foundBy": [
        "accessibility-lead"
      ]
    },
    {
      "rule": "AUDIT-STALE-SEEK-PROGRESS",
      "severity": "serious",
      "location": "apps/extensions/student/app.js:245",
      "summary": "이전 구간 이동 완료가 새 강의의 학습 위치를 덮어쓴다.",
      "fix": "media.seek 이후에도 저장 전 lesson/action/view를 검사하고 작업 시작 때 선택한 강의에만 결과를 반영하라.",
      "evidence": "runtime-keyboard/results.json: 새 강의 위치 42000ms→8000ms, 새 강의 /progress PUT에 position_ms=8000이 실제 전송·저장됨.",
      "component": "진도 저장",
      "wcag": "n/a",
      "confidence": "high",
      "foundBy": [
        "accessibility-lead"
      ]
    },
    {
      "rule": "LIVE-APP-VOICE-DIRECT-STATUS",
      "wcag": "n/a",
      "severity": "serious",
      "location": "apps/extensions/student/app.js:304-305,537,553",
      "summary": "Playback failures and learning-view ownership loss stop the lecture but update only ARIA text, bypassing built-in app speech for students without an external screen reader.",
      "fix": "Route important connection-loss and lease-loss messages through a mode-aware announcement helper: app TTS when enabled, persistent ARIA in reader mode, deduplicated to avoid polling spam. Preserve ordinary silent progress updates.",
      "evidence": "실제 영상 탭 종료 및 다른 확장 화면의 재생 lease 취득에서 영상은 멈추고 connection 텍스트는 바뀌었으나 앱 합성 호출과 sullivan-status 이벤트는 모두 비어 있음. runtime-live/observations.json.",
      "component": "Autonomous connection failure feedback",
      "confidence": "high",
      "foundBy": [
        "live-region-controller"
      ]
    },
    {
      "rule": "AUDIT-DELAYED-LECTURE-FOCUS",
      "severity": "moderate",
      "location": "apps/extensions/student/app.js:128",
      "summary": "강의가 늦게 열리면 사용자가 입력 중인 명령창에서 초점을 빼앗는다.",
      "fix": "강의 조회 전후의 사용자 상호작용을 비교해 사용자가 이미 이동했으면 강의 제목으로 강제 이동하지 말라.",
      "evidence": "runtime-focus/results.json delayed_lecture_focus: 지연 GET 응답 전 command-input에 입력 중, 응답 뒤 lesson-title로 초점 변경.",
      "component": "강의 열기 초점",
      "wcag": "n/a",
      "confidence": "high",
      "foundBy": [
        "accessibility-lead"
      ]
    },
    {
      "rule": "AUDIT-DISABLED-EDITOR-SPACE",
      "severity": "moderate",
      "location": "apps/extensions/student/keyboard.js:40",
      "summary": "Space 명령을 꺼도 입력 중 두 번 누르기 중지가 실행된다.",
      "fix": "편집 중 중지 분기도 Space 설정을 존중하도록 하거나 항상 활성인 긴급 중지 예외를 명확히 구분·설명하라.",
      "evidence": "supplement/observations.json disabled_space_editor: space_enabled=false이나 모두 중지 상태 발생.",
      "component": "Space 설정",
      "wcag": "n/a",
      "confidence": "high",
      "foundBy": [
        "accessibility-lead"
      ]
    },
    {
      "rule": "AUDIT-HOME-BUTTON-COMMAND",
      "severity": "moderate",
      "location": "apps/extensions/student/app.js:402",
      "summary": "홈에 표시된 버튼의 실행 명령이 강의 선택 전에는 거부된다.",
      "fix": "강의가 필요 없는 버튼 명령을 needLesson 이전에 처리하고 실제 보이는 허용 버튼에만 적용하라.",
      "evidence": "supplement/observations.json home_button_command: 내 연결 새로고침 버튼 눌러 → 강의를 먼저 선택하세요. 번호 강의 열기는 별도로 통과.",
      "component": "홈 명령",
      "wcag": "n/a",
      "confidence": "high",
      "foundBy": [
        "accessibility-lead"
      ]
    },
    {
      "rule": "AUDIT-REMOVED-LECTURE-FOCUS",
      "severity": "moderate",
      "location": "apps/extensions/student/app.js:92",
      "summary": "초점이 있던 강의가 새 목록에서 사라지면 초점이 BODY로 떨어진다.",
      "fix": "목록 교체 후 원래 항목이 없으면 다음 항목이나 목록 제목으로 초점을 복원하라.",
      "evidence": "runtime-focus/results.json removed_lecture_focus: 기존 강의 버튼 초점에서 빈 배정 목록 응답을 받고 before=BUTTON, after=BODY.",
      "component": "배정 목록 갱신 초점",
      "wcag": "n/a",
      "confidence": "high",
      "foundBy": [
        "accessibility-lead"
      ]
    },
    {
      "rule": "AUDIT-SHIFT-ARROW",
      "severity": "moderate",
      "location": "apps/extensions/student/keyboard.js:35",
      "summary": "Shift+방향키가 기본 수정키 동작 대신 강의를 이동시킨다.",
      "fix": "Shift 등 수정키 조합은 강의 탐색에서 제외하고 기본 편집·선택 동작을 유지하라.",
      "evidence": "supplement/observations.json shift_arrow: Shift+ArrowRight 후 실제 영상 위치 2초→8초.",
      "component": "수정키 단축키",
      "wcag": "n/a",
      "confidence": "high",
      "foundBy": [
        "accessibility-lead"
      ]
    },
    {
      "rule": "AUDIT-VOICE-UNDERLINE-FOCUS",
      "severity": "moderate",
      "location": "apps/extensions/student/app.js:334",
      "summary": "문단 안에서 음성으로 밑줄을 표시하면 초점이 BODY로 떨어진다.",
      "fix": "재렌더링 후 기존 문단/문장에 대응하는 컨트롤로 초점을 복원하고 입력 경로를 보존하라.",
      "evidence": "runtime-focus/results.json voice_underline_focus: 실제 3초 hold 뒤 시험 인식기 명령 실행, before=BUTTON, after=BODY.",
      "component": "음성 밑줄과 초점",
      "wcag": "n/a",
      "confidence": "high",
      "foundBy": [
        "accessibility-lead"
      ]
    },
    {
      "rule": "FORM-AGGREGATE-LIMIT-ERROR",
      "wcag": "3.3.1 A",
      "severity": "moderate",
      "confidence": "high",
      "location": "apps/extensions/guardian/app.js:185",
      "summary": "An aggregate material-size validation failure produces only a generic request-format error, without identifying the exceeded limit.",
      "fix": "Validate the documented total text limit before submitting and identify the affected materials input, or return a specific sanitized aggregate-limit error. Preserve selected files and give an actionable split/reduce instruction.",
      "evidence": "Four TXT files of 260,001 ASCII characters each pass per-file UI checks but receive HTTP 422. The visible alert is only “요청 형식을 확인해 주세요.”; focus remains on “자료 준비 시작”.",
      "component": "Guardian materials upload",
      "foundBy": [
        "forms-specialist"
      ]
    },
    {
      "rule": "FORM-GUIDED-RETRY-STEP",
      "wcag": "n/a",
      "severity": "moderate",
      "confidence": "high",
      "location": "apps/extensions/guardian/app.js:84",
      "summary": "Retrying a preparation while guided entry is on step 3 leaves replacement metadata hidden and the final summary stale.",
      "fix": "Reset guided prepareStep to the first step, refresh the step view and summary, then focus the visible title or first-step legend when loading a failed/interrupted preparation for retry.",
      "evidence": "Actual extension probe: stage stayed 3/3, replacement titleVisible=false, focus stayed on the retry button, and summary retained the previous title. Handler fills title/source but never resets prepareStep.",
      "component": "Guardian guided preparation retry",
      "foundBy": [
        "forms-specialist"
      ]
    },
    {
      "rule": "LIVE-NUMERIC-SETTING-VALUE-SILENCE",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/extensions/student/speech.js:92-104; apps/extensions/student/app.js:534-536; workspace.html:53-57",
      "summary": "Built-in guidance names numeric speed, volume and pitch fields without their current values and does not announce arrow-key changes, so app-only users cannot verify adjustments.",
      "fix": "Include nonsensitive numeric setting values and units in control guidance and announce committed or debounced changes for these specific fields. Continue excluding password, account and free-text values.",
      "evidence": "실제 확장에서 영상 음량을 0.4로 바꿔도 합성 요청은 영상 음량 (0~1)만 포함하고 0.4는 포함하지 않음. supplement/observations.json numeric_value_guidance.",
      "component": "App-only numeric learning preferences",
      "confidence": "high",
      "foundBy": [
        "live-region-controller"
      ]
    },
    {
      "rule": "LIVE-READER-SETTING-FOCUS-RACE",
      "wcag": "n/a",
      "severity": "moderate",
      "confidence": "high",
      "location": "apps/extensions/shared/ui.js:53-61 versus apps/extensions/student/app.js:631-632",
      "summary": "Login focuses the workspace before applying the account’s external-reader preference, allowing app TTS to start under the previous default mode.",
      "fix": "Apply student mode before the authenticated focus move, or suppress/cancel initial guidance until account preferences have been applied. Retain the user-navigation guard for delayed restoration.",
      "evidence": "기기별 override를 제거하고 서버 reader_mode=true로 새 확장 문서를 열면 최종 모드는 reader이나 speechSynthesis 호출에 내 강의 1회가 기록됨. runtime-live/observations.json.",
      "component": "Authenticated initial voice mode",
      "foundBy": [
        "live-region-controller"
      ]
    },
    {
      "rule": "LIVE-VOICE-TEST-RESUME-LOSS",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/extensions/student/app.js:538-540; apps/extensions/student/speech.js:4,14-15",
      "summary": "Clicking the app voice test while its focused-control guidance is holding playback discards the saved playing state, leaving the lecture paused after the test.",
      "fix": "Preserve the currently held playback intent when replacing control guidance with the explicit test, then resume only with unchanged view/lesson/fence. Do not force play when initially paused.",
      "evidence": "실제 확장·MP4 재생 상태에서 재현: 보류 중인 초점 안내를 음성 시험으로 교체한 뒤 paused_after_test=true. supplement/observations.json voice_test_resume.",
      "component": "App voice start/test",
      "confidence": "high",
      "foundBy": [
        "live-region-controller"
      ]
    },
    {
      "rule": "MEDIA-HIGHLIGHT-SENTENCE-PARITY",
      "wcag": "n/a",
      "severity": "moderate",
      "confidence": "high",
      "location": "apps/extensions/student/app.js:140",
      "summary": "Passage rendering drops the original per-sentence controls and explicit highlighted-sentence markers even when highlighted data is present.",
      "fix": "Render sentences as individually labelled native controls or equivalent navigable items and expose highlighted status in visible text/programmatic names. Preserve paragraph reading and underline controls alongside sentence selection.",
      "evidence": "A synthetic passage with one highlighted sentence rendered only plain combined text and three paragraph-level buttons, with zero highlight markers. Original web/app.js:946 renders sentence buttons and an explicit “강조” marker.",
      "component": "Student passage/highlight navigation; F44",
      "foundBy": [
        "media-accessibility"
      ]
    },
    {
      "rule": "AUDIT-STALE-TEXT-COMMAND",
      "severity": "minor",
      "location": "apps/extensions/student/app.js:442",
      "summary": "다시 연 타자 명령창에 이전 실행 명령이 남는다.",
      "fix": "원본과 같이 새 명령 입력을 초기화하고 이전 명령 재사용은 명시적으로 제공하라.",
      "evidence": "supplement/observations.json stale_command: 영상 중지 실행 후 재개방 값도 영상 중지.",
      "component": "명령창",
      "wcag": "n/a",
      "confidence": "high",
      "foundBy": [
        "accessibility-lead"
      ]
    },
    {
      "rule": "LIVE-GUARDIAN-PREVIEW-PENDING-ERROR",
      "wcag": "n/a",
      "severity": "minor",
      "location": "apps/extensions/guardian/app.js:162-168; apps/extensions/shared/ui.js:21",
      "summary": "A failed guardian preview question leaves its result status saying the answer is still being checked even after the global error is announced.",
      "fix": "When the request fails, replace the pending preview status with a terminal failure for the same preparation, or clear it before forwarding the error. Guard against replacing a newer selection’s status.",
      "evidence": "실제 키 미설정 API의 503 이후 global_error는 표시되나 preview-answer는 준비 자료의 근거로 답변을 확인하고 있습니다에 남음. runtime-live/observations.json.",
      "component": "Guardian preview question result",
      "confidence": "high",
      "foundBy": [
        "live-region-controller"
      ]
    }
  ],
  "passed": [
    "A first-in-document skip link points to focusable #main.",
    "Both pages have one H1; workspace and account sections use H2, principal tools H3/H4, generated concept/chat sections H5.",
    "Caption/underline and guided-entry toggles update native button aria-pressed state.",
    "Connected guidance and external-reader focus now pause playback; no-lesson guidance remains available.",
    "Current-screen description still selects a nearest prepared safe gap; the original implemented the same behavior. The extension announces the prepared timestamp rather than claiming fresh-frame analysis.",
    "Forced-colors emulation preserved native system text/background, control boundaries and focus outlines. The stylesheet does not suppress forced-color adjustment.",
    "Fresh generated student and guardian HTML has no missing aria-labelledby/describedby/controls ID targets.",
    "Fresh rendered Chromium checks using the current shared CSS and original token sheet measured normal text/primary button contrast at 14.09:1, primary hover at 8.70:1, secondary hover/notice text at 12.26:1 and error text at 7.31:1.",
    "Fresh source inspection confirms bounded lecturer-to-AI sequencing with cancellation fences, advertisement/unknown-duration handling, origin tracking and stop controls.",
    "Freshly inspected native labels, autocomplete and password instructions for both generated login/signup/recovery interfaces, plus guardian assignment/settings and student learning/preferences/record forms.",
    "Freshly reread current source instead of reusing prior clean reports.",
    "Generated role-specific page titles identify student versus guardian purpose.",
    "Guardian preview exposes transcript, safe descriptions, concepts, review categories, study guide, reasons, explicit file-delivery instructions and consented questions.",
    "Guardian terminal job transitions and connection failures use persistent deduplicated status channels.",
    "Home command entry and onboarding are reachable before selecting a lesson.",
    "Links retain an underline; errors and toggle/selection semantics do not depend solely on color. Reduced-motion handling is present and no authored animation was found.",
    "Local/preview videos have accessible names, app/native controls, textual materials and conditional prepared-caption tracks.",
    "Narration cancellation generation and media fence protect normal stale completion and prior-state resume paths.",
    "Native buttons, selects, checkboxes, fields, details and dialogs retain appropriate names and semantics.",
    "Native dialogs have named headings and explanatory descriptions.",
    "Native player controls and separate student playback/stop/volume/mute/caption controls are present; original files are selected locally and student storage is opt-in and account/lecture scoped.",
    "Natural Korean voice selection, pronunciation normalization, sentence chunking, style/edge prosody and cancellable breath delays are implemented.",
    "No inline img/svg/image-input content was found in generated pages; manifest icons use the role-specific extension name rather than unlabeled page graphics.",
    "Ordinary reader answers avoid duplicating full response through two narration channels.",
    "Pairing consent references guardian identity and sharing scope; unlink, withdrawal and permanent deletion actions associate visible consequence questions and provide cancellation.",
    "Persistent status/alert containers exist before updates; rapidly changing playback time remains non-live.",
    "Recovery codes are readonly/selectable, downloadable and explicitly clearable; prepared-note export uses a labelled native button and accessible status feedback.",
    "Review includes summary, key-segment descriptions, visual-only information, highlighted review entries and study-guide material; text remains available without connected video.",
    "Source label and preferred mode are carried by both JSON and multipart contracts. Preview questions require explicit data-transfer consent.",
    "Source switches disable irrelevant native controls and required states; guided entry groups steps with fieldsets/legends and validates ordinary required fields. The retry exception is reported separately.",
    "Temporary generation of both packages confirmed lang=ko, exactly one title and one main per page.",
    "Text fields, textareas, selects, primary/secondary buttons, links and summary controls all retained a computed visible focus outline in the probe.",
    "Text input, textarea and select boundaries measured 3.70:1 against white. The 4px focus outline with 3px offset measured 6.96:1 against white.",
    "The static generated student outline contains 19 heading elements and guardian contains 17, including hidden states; neither has a downward skipped level.",
    "Verified student-local media and guardian preview media generate WebVTT caption tracks from timed transcript segments. Missing identity/timed caption data is disclosed; caption accuracy was not evaluated."
  ],
  "notes": [
    {
      "skill": "accessibility-lead",
      "note": "제품 소스를 수정하지 않은 추가 브라우저 재현 결과다. 기능 동등성 문제이며 n/a는 WCAG 위반을 단정하지 않음을 뜻한다."
    },
    {
      "skill": "live-region-controller",
      "note": "원본 소스 재검토 후 부모 에이전트가 실제 임시 Chromium 확장 문서에서 다섯 항목 모두를 재현했다. 음성은 호출 기록용 시험 장치이며 실제 사람이 듣는 음성·OS 스크린리더 실행을 주장하지 않는다."
    },
    {
      "skill": "live-region-controller",
      "note": "runtime-live의 최초 환경 오류 및 runtime-keyboard의 최초 CSP 검사 도구 오류는 제품 오류로 세지 않았다. 수정한 감사 스크립트로 새 임시 프로필에서 재실행했다."
    },
    {
      "skill": "forms-specialist",
      "note": "Fresh 0.4.2 audit on 2026-11-13. Two completed isolated Chromium 156.0.8078.4 actual-extension DOM probe runs used synthetic accounts/data and temporary profiles. No product/test source was edited."
    },
    {
      "skill": "forms-specialist",
      "note": "Reproduce FORM-GUIDED-RETRY-STEP: ensure a failed/interrupted preparation exists; enable 3-step entry; complete metadata and materials to reach step 3; click that job’s 다시 준비 button. The replaced title is hidden in step 1 while the stage and summary remain on step 3. The probe seeded a synthetic failed job in its temporary database."
    },
    {
      "skill": "forms-specialist",
      "note": "Reproduce FORM-AGGREGATE-LIMIT-ERROR: use full entry, fill a title, choose four .txt files containing 260,001 ASCII characters each, then submit. Observe HTTP 422 and the generic alert despite the documented 1,000,000-character total limit."
    },
    {
      "skill": "forms-specialist",
      "note": "Evidence: runtime-forms-media/probe-results.json, runtime-forms-media/guided-retry-result.png, runtime-form-limits/probe-results.json and runtime-form-limits/total-limit-error.png."
    },
    {
      "skill": "forms-specialist",
      "note": "No real assistive-technology, audible TTS, microphone, external video-site or live-provider tests were performed. Axe was not enabled in these specialist probe runs."
    },
    {
      "skill": "media-accessibility",
      "note": "Fresh 0.4.2 audit on 2026-11-13. The highlighted-passage result was observed in an actual temporary-profile extension DOM probe; no real audio, AT or provider behavior was tested."
    },
    {
      "skill": "media-accessibility",
      "note": "F44 reproduction: supply a snapshot passage with at least one sentence highlighted=true, open it in the student extension, and inspect the passage. Highlight identity and individual sentence controls are absent. Probe evidence is runtime-forms-media/probe-results.json."
    },
    {
      "skill": "media-accessibility",
      "note": "F16 remains a simpler dashboard: lists and next-step text exist, while the original detailed status/dashboard experience remains partial. F23 still reports coarse queued/running/completed/failed/interrupted states without provider internal stages; neither limitation is counted as a new WCAG violation here."
    },
    {
      "skill": "media-accessibility",
      "note": "F34 remains conditional: source-tab control requires a compatible standard HTML video and rejects DRM; actual YouTube/target-site compatibility was not independently tested by this specialist."
    },
    {
      "skill": "media-accessibility",
      "note": "F36 remains explicit manual original-file delivery. Hash/size metadata and prepared materials are shared; automatic transfer between independent extension origins is not implemented."
    },
    {
      "skill": "media-accessibility",
      "note": "F56 source retains dirty-note, error and retry paths, but fresh offline/reconnection fault injection is handled separately by the parent agent and is not claimed as this specialist’s verification."
    },
    {
      "skill": "media-accessibility",
      "note": "The generic harness success list includes historical phase labels; only the explicitly described custom probes and baseline harness assertions were executed here. No inference of full media/learning parity should be made from that list."
    },
    {
      "skill": "aria-specialist",
      "note": "Static source and temporary generated-HTML inspection only; no actual assistive-technology execution."
    },
    {
      "skill": "aria-specialist",
      "note": "App-only speech-delivery omissions are in live.json; no duplicate formal ARIA finding is asserted."
    },
    {
      "skill": "aria-specialist",
      "note": "Named region density is high in the learning surface, but no conformance failure is inferred from count alone."
    },
    {
      "skill": "alt-text-headings",
      "note": "Static generated-HTML parser and dynamic-generation source inspection; not a rendered accessibility-tree or media-alternative completeness certification."
    },
    {
      "skill": "alt-text-headings",
      "note": "No actual video/audio quality or screen-reader heading traversal was executed."
    },
    {
      "skill": "alt-text-headings",
      "note": "Actual lesson-specific full-tab title differentiation remains a usability consideration; generic application titles were not marked as a conformance failure."
    },
    {
      "skill": "contrast-master",
      "note": "Fresh 0.4.2 review on 2026-11-13. Shared palette values were also collected from both actual extension pages. Detailed normal/hover/focus/forced-color measurements used a standalone Chromium DOM loaded with the exact current CSS and tokens."
    },
    {
      "skill": "contrast-master",
      "note": "Evidence: contrast-runtime.json and runtime-forms-media/probe-results.json. No manual screen magnifier or assistive-technology session was performed."
    },
    {
      "skill": "contrast-master",
      "note": "Native video chrome and arbitrary user-provided video content were not certified for contrast or caption quality by these CSS measurements."
    }
  ],
  "counts": {
    "critical": 0,
    "serious": 4,
    "moderate": 12,
    "minor": 2
  },
  "components": [],
  "score": 83,
  "grade": "B",
  "penalty": 46,
  "checks": 53,
  "generated": "2026-11-13",
  "template": "web"
}
```
