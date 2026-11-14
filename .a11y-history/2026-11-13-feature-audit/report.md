# Web Accessibility Audit

An audit of web content, run on 2026-11-13. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-13 |
| Scope | 21 items |
| Skills run | keyboard-navigator, live-region-controller, media-accessibility |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 35 |

Audited:

- `apps/api/app/guardian_preparation.py`
- `apps/api/app/student_learning.py`
- `apps/extensions/guardian/app.js`
- `apps/extensions/guardian/workspace.html`
- `apps/extensions/student/app.js`
- `apps/extensions/student/keyboard.js`
- `apps/extensions/student/media-store.js`
- `apps/extensions/student/media.js`
- `apps/extensions/student/speech.js`
- `apps/extensions/student/video-control.js`
- `apps/extensions/student/workspace.html`
- `apps/web/app.js`
- `apps/web/focus-voice.js`
- `apps/web/keyboard-navigation.js`
- `apps/web/manual/index.html`
- `apps/web/role-portal.js`
- `apps/web/styles.css`
- `apps/web/voice-command-router.js`
- `docs/FEATURE_STATUS.md`
- `scripts/build_extensions.py`
- `scripts/verify_student_repair.py`

## Executive summary

Fail. Critical or serious findings must be fixed before this ships.

The headline numbers for this run.

| Measure | Value |
|---|---|
| Score | 65 out of 100 |
| Grade | D |
| Findings | 21 |
| Blocking (critical plus serious) | 7 |
| Verdict | Fail |

## Severity breakdown

Counts by severity, highest impact first.

| Severity | Count | What it means |
|---|---:|---|
| critical | 0 | Blocks a person from completing the task |
| serious | 7 | Major barrier with a difficult workaround |
| moderate | 12 | Real friction, workaround exists |
| minor | 2 | Noticeable but rarely blocking |

## Findings

21 findings, ordered by severity then by rule.

### Serious (7)

Each row names the rule, the criterion it fails, where it is, and what to change.

| Rule | WCAG | Location | Problem | Fix |
|---|---|---|---|---|
| `PARITY-CONCEPT-SEQUENCE` | n/a | apps/extensions/student/app.js:287 | Concept search lacks the original bounded lecturer-segment then AI-explanation sequence. | Restore a cancellable sequence that remembers the origin, seeks to concept.timestamp_ms, plays through a bounded end_ms, pauses, presents/speaks the AI explanation, and leaves explicit stop/return controls. Preserve manual resume for screen-reader users. |
| `PARITY-FOCUS-PLAYBACK-HOLD` | n/a | apps/extensions/student/app.js:441 | Moving focus no longer pauses video for app guidance or external-reader access, and app focus labels are skipped while lesson speech is active. | Restore a generation-fenced focus playback hold: pause before app guidance, resume only after valid completion, and pause with explicit resume in reader mode; define interruption of lesson speech on navigation. |
| `PARITY-FOCUS-PLAYBACK-HOLD` | n/a | apps/web/focus-voice.js:19-35 versus apps/extensions/student/speech.js:57-76; app.js:441-448 | Extension control/status speech runs over an actively playing lecture instead of preserving the original pause-for-guidance and resume-after-guidance behavior. | Add optional playback coordination for the currently owned connected media view: acknowledge pause before UI speech, remember prior playing state, and resume only after the latest guidance ends with unchanged lesson/session/fence. Keep login guidance independent of any media lease. |
| `PARITY-GUARDIAN-PREVIEW` | n/a | apps/extensions/guardian/app.js:106 | Guardian preparation preview exposes counts, summary and paragraph text but omits the original media and learning review tools. | Provide guardian preview of actual safe visual descriptions, transcript, concepts, review categories, study guide and decision reasons before publication; allow an explicit connected/local-media playback preview and appropriately consented learning-chat preview. |
| `PARITY-HOME-COMMAND-ENTRY` | n/a | apps/web/manual/index.html:70-72; role-portal.js:560-575 versus extensions/student/workspace.html:13,50-55; keyboard.js:28 | Voice and typed commands cannot be opened before selecting a lesson, preventing original home-screen commands such as opening the first lecture or asking for help. | Expose student-wide voice/typed command entry on the home screen, allow Space command entry without a selected lesson, and handle help/list/open-lecture before needLesson(). Keep playback actions guarded when no lesson is loaded. |
| `PARITY-ORIGINAL-FILE-HANDOFF` | n/a | apps/extensions/guardian/app.js:174 | Publishing a local-file lesson no longer delivers a playable original from guardian preparation to the student. | Design an explicit consented handoff between isolated applications, or a clear manual file-delivery workflow with readiness checks and student-side identity validation. Explain that server assignment transfers prepared data, not the original; preserve no-server-storage by default. |
| `PARITY-READER-FOCUS-PAUSE` | n/a | apps/web/focus-voice.js:168-173 versus apps/extensions/student/app.js:441-444 | External-reader mode no longer pauses lecture playback when the student moves focus, so original protection against simultaneous lecture audio and screen-reader speech is lost. | On student focus navigation in reader mode, pause currently owned playing media without auto-resuming; let the student explicitly resume. Do not claim a different media view or infer OS screen-reader speech completion. |

### Moderate (12)

Each row names the rule, the criterion it fails, where it is, and what to change.

| Rule | WCAG | Location | Problem | Fix |
|---|---|---|---|---|
| `PARITY-ANSWER-SPEECH-PREFERENCE` | n/a | apps/web/app.js:1470,1503,1526 versus apps/extensions/student/app.js:313,326; workspace.html:68 | Disabling the answer-speech checkbox does not mute typed answers when focus guidance remains enabled, unlike the original independent answer and focus speech choices. | Remove focus_voice as an override of the explicit answer-speech preference; retain forced speech only for explicit spoken/read-aloud requests. When answer speech is off, provide the result via a reader announcement or managed result focus without speaking it through focus guidance. |
| `PARITY-CANCEL-RESUMPTION` | n/a | apps/extensions/student/app.js:506 | Cancel or Escape from text-command entry restores focus but no longer resumes the lecture that opening the dialog paused. | Retain the prior playback intention and restore it only on cancellation in the same lesson/account with no subsequent stop; do not resume after submitted commands or explicit stop. |
| `PARITY-EDITOR-DOUBLE-STOP` | n/a | apps/extensions/student/keyboard.js:28 | The original emergency double-Space stop during explanation or pending work is unavailable while focus is in an editor. | Preserve ordinary typed spaces while restoring the original stop-only double-tap path during active output, or explicitly document an approved replacement that is reachable without leaving the field. |
| `PARITY-EXPLORATION-RETURN` | n/a | apps/extensions/student/app.js:289 | Return-to-origin works after concept search but does not cover the original broader exploration workflow or its “곳” voice phrasing. | Capture a fresh media position before paragraph/review/question exploration as well as search, share one stop-and-return operation, and accept both 원래/듣던 곳 and 위치 phrases. Keep explicit play after returning. |
| `PARITY-FIRST-LOGIN-GUIDE` | n/a | apps/extensions/student/app.js:534 | The extension omits the original first-login guide, completion state and replayable onboarding flow. | Restore a student-only guide available before lesson selection, retain completion/reset state, and update its Space instructions to the user’s new contract. |
| `PARITY-GESTURE-INVALIDATION` | n/a | apps/extensions/student/keyboard.js:19 | A pending Space sequence survives Tab or other keyboard navigation, so playback or a voice/text action can fire after the user has moved away. | Cancel pending gestures when a different key, focus change or composition begins; fence delayed tap actions against their initiating context while preserving deliberate multi-tap input. |
| `PARITY-HELP-CONTENT` | n/a | apps/extensions/student/app.js:343 | The “사용법” command requires a lesson and reads only command examples instead of reopening the original complete usage guide. | Handle help before needLesson(), expose the complete updated instructions visibly and audibly, and provide a persistent help button or manual link. |
| `PARITY-HOME-COMMAND-ACCESS` | n/a | apps/extensions/student/keyboard.js:28 | Voice and triple-Space text commands cannot be invoked from student home before selecting a lesson. | Make non-playback command entry available on student home; restrict only playback/seek to an active lesson. Keep the new single-Space playback contract and native text entry. |
| `PARITY-NATURAL-SPEECH-PROFILE` | n/a | apps/web/app.js:1667-1805; index.html:389-399 versus apps/extensions/student/speech.js:27-46; workspace.html:36-48 | Original text-pronunciation normalization, sentence-based breath pauses, opening/closing prosody and warm/calm/clear profiles are replaced with fixed 180-character narration chunks. | Port pure text normalization and sentence/prosody profiles while retaining extension cancellation/fence safety. Add an equivalent narration preview if retaining advanced profiles. Document that original profile/preview controls were hidden in student role; the default speech engine behavior still requires parity. |
| `PARITY-NATURAL-VOICE-SELECTION` | n/a | apps/web/app.js:1617-1664 versus apps/extensions/student/speech.js:38-42,67-69; app.js:525-529 | Extension narration loses the original automatic ranking of Korean Natural/Neural/Online voices and can choose a different default voice from control guidance. | Extract the original pure Korean voice scoring/selection helpers into a shared speech module; use the same selected-or-ranked fallback for narration and UI guidance, preserve explicit user voice choice, and refresh safely when voices load. |
| `PARITY-REVIEW-CATEGORIES` | n/a | apps/extensions/student/app.js:162 | Student review omits original visual/highlight review categories and hides key-segment descriptions behind successful media seeking. | Restore timestamped visual-only and highlighted-sentence review alongside summary/key segments, display each description as readable text, and permit reading/listening without connected media. Render study_guide.overview and add the original review/study-guide read actions. |
| `PARITY-VOICE-READY-CUE` | n/a | apps/extensions/student/app.js:405 | The original audible voice-ready cue is missing, leaving app-voice users without an audible signal that the three-second hold has reached recognition. | Provide a short nonverbal ready cue when recognition actually starts, plus an accessible status; keep the cue separate from speech captured by the recognizer. |

### Minor (2)

Each row names the rule, the criterion it fails, where it is, and what to change.

| Rule | WCAG | Location | Problem | Fix |
|---|---|---|---|---|
| `PARITY-APP-STATE-FEEDBACK` | n/a | apps/extensions/student/app.js:445 | App voice no longer announces a disclosure’s changed state while its summary retains focus, and omits pressed/current state on refocus. | Restore focused-details toggle announcements and include meaningful aria-pressed/aria-current states in controlDescription without duplicating external-reader speech. |
| `PARITY-TTS-PROSODY` | n/a | apps/extensions/student/speech.js:26 | Lesson narration retains rate, pitch, volume and voice choice but drops the original speech-style and sentence-level prosody behavior. | If full original narration parity is required, reuse sentence-aware chunking, Korean natural-voice ranking and the warm/calm/clear style profiles while retaining the extension cancellation and playback fences. Otherwise document this deliberate reduction. |

## Remediation priorities

The 7 blocking findings, in this order:

1. `PARITY-CONCEPT-SEQUENCE` at apps/extensions/student/app.js:287. Restore a cancellable sequence that remembers the origin, seeks to concept.timestamp_ms, plays through a bounded end_ms, pauses, presents/speaks the AI explanation, and leaves explicit stop/return controls. Preserve manual resume for screen-reader users.
2. `PARITY-FOCUS-PLAYBACK-HOLD` at apps/extensions/student/app.js:441. Restore a generation-fenced focus playback hold: pause before app guidance, resume only after valid completion, and pause with explicit resume in reader mode; define interruption of lesson speech on navigation.
3. `PARITY-FOCUS-PLAYBACK-HOLD` at apps/web/focus-voice.js:19-35 versus apps/extensions/student/speech.js:57-76; app.js:441-448. Add optional playback coordination for the currently owned connected media view: acknowledge pause before UI speech, remember prior playing state, and resume only after the latest guidance ends with unchanged lesson/session/fence. Keep login guidance independent of any media lease.
4. `PARITY-GUARDIAN-PREVIEW` at apps/extensions/guardian/app.js:106. Provide guardian preview of actual safe visual descriptions, transcript, concepts, review categories, study guide and decision reasons before publication; allow an explicit connected/local-media playback preview and appropriately consented learning-chat preview.
5. `PARITY-HOME-COMMAND-ENTRY` at apps/web/manual/index.html:70-72; role-portal.js:560-575 versus extensions/student/workspace.html:13,50-55; keyboard.js:28. Expose student-wide voice/typed command entry on the home screen, allow Space command entry without a selected lesson, and handle help/list/open-lecture before needLesson(). Keep playback actions guarded when no lesson is loaded.
6. `PARITY-ORIGINAL-FILE-HANDOFF` at apps/extensions/guardian/app.js:174. Design an explicit consented handoff between isolated applications, or a clear manual file-delivery workflow with readiness checks and student-side identity validation. Explain that server assignment transfers prepared data, not the original; preserve no-server-storage by default.
7. `PARITY-READER-FOCUS-PAUSE` at apps/web/focus-voice.js:168-173 versus apps/extensions/student/app.js:441-444. On student focus navigation in reader mode, pause currently owned playing media without auto-resuming; let the student explicitly resume. Do not claim a different media view or infer OS screen-reader speech completion.

The remaining 14 moderate and minor findings can follow in normal work.

## What passed

14 checks ran and found nothing.

- App guidance now covers login/home controls and protects password field contents.
- Both original describe-now (web/app.js:860–865) and extension describe (student/app.js:330–333) select the nearest prepared safe gap. Fresh current-frame OCR/vision is not an implemented original capability lost in this migration; the extension explicitly announces the prepared timestamp.
- Current reader-mode ordinary answers have a single full-answer delivery channel.
- Extension code retains safe-gap confidence/problem-mode filtering, due-gap scheduling, pause/speech/resume, cancellation fencing, video volume/mute, transcript text and dynamically generated WebVTT captions for verified local originals.
- Extension code retains source-tab/manual-local playback, concept search, paragraph/sentence reading, underlines, bookmarks, notes export and prepared study tools; these are not completely absent.
- Extension retains speed, volume, pitch and explicit Korean-voice selection plus per-device preference storage.
- External-reader lesson-description delivery avoids browser TTS and does not guess reader completion to resume playback.
- Lesson narration still pauses playback before output and uses generation/fence checks before resuming.
- Login/field app voice, password-value exclusion, checkbox/select state descriptions, voice selection, reader mode and speech testing are present.
- Panel-only event handlers and extension open/stop commands are present; lecture-host keys are not intercepted.
- Recovery of encrypted student-local originals remains explicit and scoped by account plus lecture; no raw-media delivery endpoint was found in the inspected student API.
- Tab/Shift+Tab, standalone Shift, DOM-adjacent heading traversal, native field typing, explicit Escape exit and native dialog containment are present.
- The updated user Space contract is implemented and is treated as an intentional override of the older manual’s single-Space button behavior and shorter hold timing.
- Typed, speech-recognition and local fallback command engines remain present for an opened lesson.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **keyboard-navigator**: This is an original-feature parity inspection, not a WCAG conformance result: n/a findings record missing original behavior without asserting a specific WCAG failure.
- **keyboard-navigator**: No product or test files were edited. Findings and parity notes only were written.
- **keyboard-navigator**: Static source comparison only; no fresh browser, physical keyboard, real microphone, VoiceOver or NVDA test was performed.
- **keyboard-navigator**: The existing repair test covers selected-lesson gestures and containment, not complete original-feature parity. See keyboard-parity-notes.md for evidence and test gaps.
- **live-region-controller**: Functional parity audit, not a complete WCAG audit. All findings use n/a because they concern implemented product behavior rather than asserted conformance failures.
- **live-region-controller**: No actual Korean audio, VoiceOver or NVDA was heard or executed.
- **live-region-controller**: Original advanced speech-style/voice-preview controls live in .player-tools, which styles.css:674 hides for student role; only speed, volume and auto-narration are moved to student preferences. Their engine effects still run by default.
- **live-region-controller**: Original Mac native initial-login greeting is replaced with browser focus speech and an explicit start/test control. This is a changed platform boundary; automatic first audio after reload is not established by source inspection.
- **live-region-controller**: Neither original nor extension reader mode starts or detects an OS screen reader.
- **live-region-controller**: Persisted accompanying detailed parity notes to live-parity-notes.md.
- **media-accessibility**: Inspection only on 2026-11-13: no tests, media playback, microphone, TTS voices, provider calls or Chrome extension flows were executed. All findings are implementation parity gaps, not demonstrated WCAG failures.
- **media-accessibility**: Actual Gemini/link analysis requires configured services, network access and valid consent. Source wiring is not evidence that a live provider or a particular lecture currently succeeds.
- **media-accessibility**: Original media handoff was limited to the same web origin/browser profile; it never established cross-device automatic video delivery. Separate extension origins cannot inherit that IndexedDB automatically.
- **media-accessibility**: Detailed evidence, retained features and limitations are recorded in parity-notes.md alongside this report.

## Next steps

1. Fix the 7 blocking findings above, starting with any repeated component.
2. Re-run this audit and check the delta section for regressions.
3. Wire the scan into continuous integration so the next regression is caught before review.

Automated checks find a minority of accessibility barriers. A passing score is a floor, not a guarantee.

## Findings data

The merged findings, embedded so the next run can compute a delta without parsing this document.

```json a11y-findings
{
  "skills": [
    "keyboard-navigator",
    "live-region-controller",
    "media-accessibility"
  ],
  "scope": [
    "apps/api/app/guardian_preparation.py",
    "apps/api/app/student_learning.py",
    "apps/extensions/guardian/app.js",
    "apps/extensions/guardian/workspace.html",
    "apps/extensions/student/app.js",
    "apps/extensions/student/keyboard.js",
    "apps/extensions/student/media-store.js",
    "apps/extensions/student/media.js",
    "apps/extensions/student/speech.js",
    "apps/extensions/student/video-control.js",
    "apps/extensions/student/workspace.html",
    "apps/web/app.js",
    "apps/web/focus-voice.js",
    "apps/web/keyboard-navigation.js",
    "apps/web/manual/index.html",
    "apps/web/role-portal.js",
    "apps/web/styles.css",
    "apps/web/voice-command-router.js",
    "docs/FEATURE_STATUS.md",
    "scripts/build_extensions.py",
    "scripts/verify_student_repair.py"
  ],
  "findings": [
    {
      "rule": "PARITY-CONCEPT-SEQUENCE",
      "wcag": "n/a",
      "severity": "serious",
      "location": "apps/extensions/student/app.js:287",
      "summary": "Concept search lacks the original bounded lecturer-segment then AI-explanation sequence.",
      "fix": "Restore a cancellable sequence that remembers the origin, seeks to concept.timestamp_ms, plays through a bounded end_ms, pauses, presents/speaks the AI explanation, and leaves explicit stop/return controls. Preserve manual resume for screen-reader users.",
      "evidence": "Original app.js:1041–1085 implements segment timing and AI handoff. Extension :293–294 exposes separate explanation and seek/play buttons; the latter has no segment end or follow-up explanation.",
      "foundBy": [
        "media-accessibility"
      ]
    },
    {
      "rule": "PARITY-FOCUS-PLAYBACK-HOLD",
      "wcag": "n/a",
      "severity": "serious",
      "location": "apps/extensions/student/app.js:441",
      "summary": "Moving focus no longer pauses video for app guidance or external-reader access, and app focus labels are skipped while lesson speech is active.",
      "fix": "Restore a generation-fenced focus playback hold: pause before app guidance, resume only after valid completion, and pause with explicit resume in reader mode; define interruption of lesson speech on navigation.",
      "evidence": "Original focus-voice.js:19-35 manages pause/resume and :167-174 pauses on reader focus. Current focusin only calls announcer.say; speech.js:62 returns in reader mode or when busy, and StudentAnnouncer has no media control.",
      "foundBy": [
        "keyboard-navigator"
      ]
    },
    {
      "rule": "PARITY-FOCUS-PLAYBACK-HOLD",
      "wcag": "n/a",
      "severity": "serious",
      "location": "apps/web/focus-voice.js:19-35 versus apps/extensions/student/speech.js:57-76; app.js:441-448",
      "summary": "Extension control/status speech runs over an actively playing lecture instead of preserving the original pause-for-guidance and resume-after-guidance behavior.",
      "fix": "Add optional playback coordination for the currently owned connected media view: acknowledge pause before UI speech, remember prior playing state, and resume only after the latest guidance ends with unchanged lesson/session/fence. Keep login guidance independent of any media lease.",
      "evidence": "Original holdPlayback/releasePlayback save and restore playback; StudentAnnouncer has no media pause/resume hooks and busy() only checks lesson speech/recognition.",
      "component": "Focus and status app narration",
      "foundBy": [
        "live-region-controller"
      ]
    },
    {
      "rule": "PARITY-GUARDIAN-PREVIEW",
      "wcag": "n/a",
      "severity": "serious",
      "location": "apps/extensions/guardian/app.js:106",
      "summary": "Guardian preparation preview exposes counts, summary and paragraph text but omits the original media and learning review tools.",
      "fix": "Provide guardian preview of actual safe visual descriptions, transcript, concepts, review categories, study guide and decision reasons before publication; allow an explicit connected/local-media playback preview and appropriately consented learning-chat preview.",
      "evidence": "openPreparation renders source label, counts, core_summary and passage sentences only (:106–109). Original manual:55 specifies lecture, concept, visual-review, study-note, chat and evidence inspection before assignment.",
      "foundBy": [
        "media-accessibility"
      ]
    },
    {
      "rule": "PARITY-HOME-COMMAND-ENTRY",
      "wcag": "n/a",
      "severity": "serious",
      "location": "apps/web/manual/index.html:70-72; role-portal.js:560-575 versus extensions/student/workspace.html:13,50-55; keyboard.js:28",
      "summary": "Voice and typed commands cannot be opened before selecting a lesson, preventing original home-screen commands such as opening the first lecture or asking for help.",
      "fix": "Expose student-wide voice/typed command entry on the home screen, allow Space command entry without a selected lesson, and handle help/list/open-lecture before needLesson(). Keep playback actions guarded when no lesson is loaded.",
      "evidence": "Command forms/buttons are descendants of hidden #lesson; Space handlers require hasLesson(); command() calls needLesson() before the help branch.",
      "component": "Student home voice and typed commands",
      "foundBy": [
        "live-region-controller"
      ]
    },
    {
      "rule": "PARITY-ORIGINAL-FILE-HANDOFF",
      "wcag": "n/a",
      "severity": "serious",
      "location": "apps/extensions/guardian/app.js:174",
      "summary": "Publishing a local-file lesson no longer delivers a playable original from guardian preparation to the student.",
      "fix": "Design an explicit consented handoff between isolated applications, or a clear manual file-delivery workflow with readiness checks and student-side identity validation. Explain that server assignment transfers prepared data, not the original; preserve no-server-storage by default.",
      "evidence": "Original role-portal.js:539–553 saves encrypted media later loaded by the student at :443–449. Extension publication persists local-reference hash/size (guardian_preparation.py:140,253–259); student/app.js:209 requires independent file selection.",
      "foundBy": [
        "media-accessibility"
      ]
    },
    {
      "rule": "PARITY-READER-FOCUS-PAUSE",
      "wcag": "n/a",
      "severity": "serious",
      "location": "apps/web/focus-voice.js:168-173 versus apps/extensions/student/app.js:441-444",
      "summary": "External-reader mode no longer pauses lecture playback when the student moves focus, so original protection against simultaneous lecture audio and screen-reader speech is lost.",
      "fix": "On student focus navigation in reader mode, pause currently owned playing media without auto-resuming; let the student explicitly resume. Do not claim a different media view or infer OS screen-reader speech completion.",
      "evidence": "Original readerMode focusin pauses running playback. Extension focusin only calls announcer.say(), which immediately returns in reader_mode.",
      "component": "External-reader navigation",
      "foundBy": [
        "live-region-controller"
      ]
    },
    {
      "rule": "PARITY-ANSWER-SPEECH-PREFERENCE",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/web/app.js:1470,1503,1526 versus apps/extensions/student/app.js:313,326; workspace.html:68",
      "summary": "Disabling the answer-speech checkbox does not mute typed answers when focus guidance remains enabled, unlike the original independent answer and focus speech choices.",
      "fix": "Remove focus_voice as an override of the explicit answer-speech preference; retain forced speech only for explicit spoken/read-aloud requests. When answer speech is off, provide the result via a reader announcement or managed result focus without speaking it through focus guidance.",
      "evidence": "Extension ask() condition includes forceSpeak || speak-answer.checked || settings.focus_voice; original auto-speak-chat was independent of focusVoice.",
      "component": "Independent answer output preference",
      "foundBy": [
        "live-region-controller"
      ]
    },
    {
      "rule": "PARITY-CANCEL-RESUMPTION",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/extensions/student/app.js:506",
      "summary": "Cancel or Escape from text-command entry restores focus but no longer resumes the lecture that opening the dialog paused.",
      "fix": "Retain the prior playback intention and restore it only on cancellation in the same lesson/account with no subsequent stop; do not resume after submitted commands or explicit stop.",
      "evidence": "Original role-portal.js:633 resumes when closeDialog(true), used by cancel/Escape at :686-689. Current openDialog calls stopAll, and its close handler only restores focus.",
      "foundBy": [
        "keyboard-navigator"
      ]
    },
    {
      "rule": "PARITY-EDITOR-DOUBLE-STOP",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/extensions/student/keyboard.js:28",
      "summary": "The original emergency double-Space stop during explanation or pending work is unavailable while focus is in an editor.",
      "fix": "Preserve ordinary typed spaces while restoring the original stop-only double-tap path during active output, or explicitly document an approved replacement that is reachable without leaving the field.",
      "evidence": "Original role-portal.js:676-682 detects editor double taps while speech or agent work is active. Current nativeSpace excludes editors from all gesture handling, with no separate stop-only listener.",
      "foundBy": [
        "keyboard-navigator"
      ]
    },
    {
      "rule": "PARITY-EXPLORATION-RETURN",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/extensions/student/app.js:289",
      "summary": "Return-to-origin works after concept search but does not cover the original broader exploration workflow or its “곳” voice phrasing.",
      "fix": "Capture a fresh media position before paragraph/review/question exploration as well as search, share one stop-and-return operation, and accept both 원래/듣던 곳 and 위치 phrases. Keep explicit play after returning.",
      "evidence": "Extension assigns originMs only in search (:289); paragraph/review seeks do not capture it, and :356 matches 위치 only. Original role-portal.js:465–478 captures origin for learning purposes and :594 accepts 곳 or 위치.",
      "foundBy": [
        "media-accessibility"
      ]
    },
    {
      "rule": "PARITY-FIRST-LOGIN-GUIDE",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/extensions/student/app.js:534",
      "summary": "The extension omits the original first-login guide, completion state and replayable onboarding flow.",
      "fix": "Restore a student-only guide available before lesson selection, retain completion/reset state, and update its Space instructions to the user’s new contract.",
      "evidence": "Original role-portal.js:116-117 calls showHelp for !user.onboarded; :480-506 creates the guide and saves /onboarding. Extension boot only loads settings, lectures and connections.",
      "foundBy": [
        "keyboard-navigator"
      ]
    },
    {
      "rule": "PARITY-GESTURE-INVALIDATION",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/extensions/student/keyboard.js:19",
      "summary": "A pending Space sequence survives Tab or other keyboard navigation, so playback or a voice/text action can fire after the user has moved away.",
      "fix": "Cancel pending gestures when a different key, focus change or composition begins; fence delayed tap actions against their initiating context while preserving deliberate multi-tap input.",
      "evidence": "Original role-portal.js:665 cancels on non-Space keys and :674 cancels on focus change. Current reset only runs for Escape, pointerdown, blur or hidden document; Tab moves focus without cancelling gesture timers.",
      "foundBy": [
        "keyboard-navigator"
      ]
    },
    {
      "rule": "PARITY-HELP-CONTENT",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/extensions/student/app.js:343",
      "summary": "The “사용법” command requires a lesson and reads only command examples instead of reopening the original complete usage guide.",
      "fix": "Handle help before needLesson(), expose the complete updated instructions visibly and audibly, and provide a persistent help button or manual link.",
      "evidence": "Original role-portal.js:563 handles help before lesson checks and opens showHelp; current :343-344 calls needLesson then speaks #command-help, which only contains examples and text-entry guidance.",
      "foundBy": [
        "keyboard-navigator"
      ]
    },
    {
      "rule": "PARITY-HOME-COMMAND-ACCESS",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/extensions/student/keyboard.js:28",
      "summary": "Voice and triple-Space text commands cannot be invoked from student home before selecting a lesson.",
      "fix": "Make non-playback command entry available on student home; restrict only playback/seek to an active lesson. Keep the new single-Space playback contract and native text entry.",
      "evidence": "Space handling requires hasLesson(); app.js:435 supplies Boolean(current). Voice/type-command triggers and command form are inside hidden #lesson. Original role-portal.js:664-674 scopes gestures by student role, not lecture selection.",
      "foundBy": [
        "keyboard-navigator"
      ]
    },
    {
      "rule": "PARITY-NATURAL-SPEECH-PROFILE",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/web/app.js:1667-1805; index.html:389-399 versus apps/extensions/student/speech.js:27-46; workspace.html:36-48",
      "summary": "Original text-pronunciation normalization, sentence-based breath pauses, opening/closing prosody and warm/calm/clear profiles are replaced with fixed 180-character narration chunks.",
      "fix": "Port pure text normalization and sentence/prosody profiles while retaining extension cancellation/fence safety. Add an equivalent narration preview if retaining advanced profiles. Document that original profile/preview controls were hidden in student role; the default speech engine behavior still requires parity.",
      "evidence": "Original prepareSpeechText, speechChunks, styleProfile and 70/130ms pauses are absent; extension applies constant rate/pitch to arbitrary 180-character chunks.",
      "component": "Natural narration engine and advanced preview",
      "foundBy": [
        "live-region-controller"
      ]
    },
    {
      "rule": "PARITY-NATURAL-VOICE-SELECTION",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/web/app.js:1617-1664 versus apps/extensions/student/speech.js:38-42,67-69; app.js:525-529",
      "summary": "Extension narration loses the original automatic ranking of Korean Natural/Neural/Online voices and can choose a different default voice from control guidance.",
      "fix": "Extract the original pure Korean voice scoring/selection helpers into a shared speech module; use the same selected-or-ranked fallback for narration and UI guidance, preserve explicit user voice choice, and refresh safely when voices load.",
      "evidence": "Original voiceScore ranks natural/neural/online and named Korean voices. StudentSpeech only sets an exact saved voice; StudentAnnouncer otherwise takes the first Korean voice.",
      "component": "Automatic Korean voice selection",
      "foundBy": [
        "live-region-controller"
      ]
    },
    {
      "rule": "PARITY-REVIEW-CATEGORIES",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/extensions/student/app.js:162",
      "summary": "Student review omits original visual/highlight review categories and hides key-segment descriptions behind successful media seeking.",
      "fix": "Restore timestamped visual-only and highlighted-sentence review alongside summary/key segments, display each description as readable text, and permit reading/listening without connected media. Render study_guide.overview and add the original review/study-guide read actions.",
      "evidence": "Original app.js:1126–1184 renders all four review categories and overview with read controls. Extension :164–169 renders summary, seek-then-speak key segments and three study lists; seek (:186) throws when no video is connected.",
      "foundBy": [
        "media-accessibility"
      ]
    },
    {
      "rule": "PARITY-VOICE-READY-CUE",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/extensions/student/app.js:405",
      "summary": "The original audible voice-ready cue is missing, leaving app-voice users without an audible signal that the three-second hold has reached recognition.",
      "fix": "Provide a short nonverbal ready cue when recognition actually starts, plus an accessible status; keep the cue separate from speech captured by the recognizer.",
      "evidence": "Original role-portal.js:643 invokes playSpaceVoiceReadyChime and displays a speaking overlay. Extension startVoice updates #voice-status only; StudentAnnouncer is suppressed while recognition is active.",
      "foundBy": [
        "keyboard-navigator"
      ]
    },
    {
      "rule": "PARITY-APP-STATE-FEEDBACK",
      "wcag": "n/a",
      "severity": "minor",
      "location": "apps/extensions/student/app.js:445",
      "summary": "App voice no longer announces a disclosure’s changed state while its summary retains focus, and omits pressed/current state on refocus.",
      "fix": "Restore focused-details toggle announcements and include meaningful aria-pressed/aria-current states in controlDescription without duplicating external-reader speech.",
      "evidence": "Original focus-voice.js:61-63 describes current/pressed and :181-185 handles details toggle. Current listens only to focusin and input/select change; speech.js:79-89 has no pressed/current handling.",
      "foundBy": [
        "keyboard-navigator"
      ]
    },
    {
      "rule": "PARITY-TTS-PROSODY",
      "wcag": "n/a",
      "severity": "minor",
      "location": "apps/extensions/student/speech.js:26",
      "summary": "Lesson narration retains rate, pitch, volume and voice choice but drops the original speech-style and sentence-level prosody behavior.",
      "fix": "If full original narration parity is required, reuse sentence-aware chunking, Korean natural-voice ranking and the warm/calm/clear style profiles while retaining the extension cancellation and playback fences. Otherwise document this deliberate reduction.",
      "evidence": "Original app.js:1691,1714–1775 uses speechChunks, selectedKoreanVoice, style profiles and opening/closing adjustments. Extension splits fixed 180-character chunks and applies one rate/pitch directly.",
      "foundBy": [
        "media-accessibility"
      ]
    }
  ],
  "passed": [
    "App guidance now covers login/home controls and protects password field contents.",
    "Both original describe-now (web/app.js:860–865) and extension describe (student/app.js:330–333) select the nearest prepared safe gap. Fresh current-frame OCR/vision is not an implemented original capability lost in this migration; the extension explicitly announces the prepared timestamp.",
    "Current reader-mode ordinary answers have a single full-answer delivery channel.",
    "Extension code retains safe-gap confidence/problem-mode filtering, due-gap scheduling, pause/speech/resume, cancellation fencing, video volume/mute, transcript text and dynamically generated WebVTT captions for verified local originals.",
    "Extension code retains source-tab/manual-local playback, concept search, paragraph/sentence reading, underlines, bookmarks, notes export and prepared study tools; these are not completely absent.",
    "Extension retains speed, volume, pitch and explicit Korean-voice selection plus per-device preference storage.",
    "External-reader lesson-description delivery avoids browser TTS and does not guess reader completion to resume playback.",
    "Lesson narration still pauses playback before output and uses generation/fence checks before resuming.",
    "Login/field app voice, password-value exclusion, checkbox/select state descriptions, voice selection, reader mode and speech testing are present.",
    "Panel-only event handlers and extension open/stop commands are present; lecture-host keys are not intercepted.",
    "Recovery of encrypted student-local originals remains explicit and scoped by account plus lecture; no raw-media delivery endpoint was found in the inspected student API.",
    "Tab/Shift+Tab, standalone Shift, DOM-adjacent heading traversal, native field typing, explicit Escape exit and native dialog containment are present.",
    "The updated user Space contract is implemented and is treated as an intentional override of the older manual’s single-Space button behavior and shorter hold timing.",
    "Typed, speech-recognition and local fallback command engines remain present for an opened lesson."
  ],
  "notes": [
    {
      "skill": "keyboard-navigator",
      "note": "This is an original-feature parity inspection, not a WCAG conformance result: n/a findings record missing original behavior without asserting a specific WCAG failure."
    },
    {
      "skill": "keyboard-navigator",
      "note": "No product or test files were edited. Findings and parity notes only were written."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Static source comparison only; no fresh browser, physical keyboard, real microphone, VoiceOver or NVDA test was performed."
    },
    {
      "skill": "keyboard-navigator",
      "note": "The existing repair test covers selected-lesson gestures and containment, not complete original-feature parity. See keyboard-parity-notes.md for evidence and test gaps."
    },
    {
      "skill": "live-region-controller",
      "note": "Functional parity audit, not a complete WCAG audit. All findings use n/a because they concern implemented product behavior rather than asserted conformance failures."
    },
    {
      "skill": "live-region-controller",
      "note": "No actual Korean audio, VoiceOver or NVDA was heard or executed."
    },
    {
      "skill": "live-region-controller",
      "note": "Original advanced speech-style/voice-preview controls live in .player-tools, which styles.css:674 hides for student role; only speed, volume and auto-narration are moved to student preferences. Their engine effects still run by default."
    },
    {
      "skill": "live-region-controller",
      "note": "Original Mac native initial-login greeting is replaced with browser focus speech and an explicit start/test control. This is a changed platform boundary; automatic first audio after reload is not established by source inspection."
    },
    {
      "skill": "live-region-controller",
      "note": "Neither original nor extension reader mode starts or detects an OS screen reader."
    },
    {
      "skill": "live-region-controller",
      "note": "Persisted accompanying detailed parity notes to live-parity-notes.md."
    },
    {
      "skill": "media-accessibility",
      "note": "Inspection only on 2026-11-13: no tests, media playback, microphone, TTS voices, provider calls or Chrome extension flows were executed. All findings are implementation parity gaps, not demonstrated WCAG failures."
    },
    {
      "skill": "media-accessibility",
      "note": "Actual Gemini/link analysis requires configured services, network access and valid consent. Source wiring is not evidence that a live provider or a particular lecture currently succeeds."
    },
    {
      "skill": "media-accessibility",
      "note": "Original media handoff was limited to the same web origin/browser profile; it never established cross-device automatic video delivery. Separate extension origins cannot inherit that IndexedDB automatically."
    },
    {
      "skill": "media-accessibility",
      "note": "Detailed evidence, retained features and limitations are recorded in parity-notes.md alongside this report."
    }
  ],
  "counts": {
    "critical": 0,
    "serious": 7,
    "moderate": 12,
    "minor": 2
  },
  "components": [],
  "score": 65,
  "grade": "D",
  "penalty": 61,
  "checks": 35,
  "generated": "2026-11-13",
  "template": "web"
}
```
