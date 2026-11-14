# Web Accessibility Audit

An audit of web content, run on 2026-11-14. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-14 |
| Scope | 12 items |
| Skills run | aria-specialist, forms-specialist, keyboard-navigator, live-region-controller, media-accessibility, modal-specialist |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 35 |

Audited:

- `apps/api/app/guardian_preparation.py`
- `apps/api/app/main.py:123`
- `apps/extensions/guardian/app.js`
- `apps/extensions/guardian/workspace.html`
- `apps/extensions/shared/ui.js`
- `apps/extensions/student/app.js`
- `apps/extensions/student/keyboard.js`
- `apps/extensions/student/media.js`
- `apps/extensions/student/speech.js`
- `apps/extensions/student/worker.js`
- `apps/extensions/student/workspace.html`
- `scripts/build_extensions.py`

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

35 checks ran and found nothing.

- Additional reviewed boundary: Stop during a pending claim now sends a worker pause even before kind is assigned.
- Cancel playback restoration requires unchanged lesson/view/generation/action/fence/focus ownership, and media.play rechecks play revision after its RPC.
- Changed reading-mode and voice-test controls remain native labelled select/button elements; no substitute custom ARIA widget was introduced.
- FIX-R15-PARAGRAPH-CURSOR resolved: resolver-selected paragraphs now align sentenceIndex to the selected paragraph’s first sentence and rerender the current-sentence marker before reading; subsequent next/previous commands use that cursor.
- Microphone fallback context is cleared by permission close and explicit stop; recognition completion through its own button remains distinct from abort.
- Narration channels remain separate: app guidance updates speech-status, lesson content updates current-description and conditional reader-description, and full reader answers use answer-status. Mode checks suppress app guidance for external-reader mode.
- Native dialog naming, visible Cancel, modal Tab scope and Escape remain intact.
- Numeric voice guidance reads safe native input values without replacing native labels, roles or validation; password contents and arbitrary text inputs are excluded.
- Past-state snapshots may survive an intentional pause but cannot survive a changed media view/generation.
- R01: account/lesson/view/action is captured before host permission; context is checked after permission and connection awaits.
- R01: app connection context is captured before permission awaits and checked before media reset and subsequent mutations; media methods also validate view/generation/fence.
- R02: app seek validates the selected lesson after the media seek response before updating position or saving; local media seek validates its own scope before mutating currentTime.
- R02: media operations reject stale view/generation/fence; app seek rechecks context before updating position or saving progress.
- R03: StudentMedia invalidates pending play with playRevision when speech is cancelled or pauses media; play rechecks its scope and revision before applying local playback. StudentSpeech preserves wantsPlayback as the prior playback intention before its hold.
- R03: pause/reset and speech cancellation invalidate pending play through a separate playRevision, retaining legitimate wantsPlayback intent.
- R03: play revision and speech cancellation invalidate pending playback; native play completion/rejection rechecks ownership. Expected cancelled operations do not trigger a new connection reset or user error.
- R04: autonomous tick failure and matching lease loss share loseConnection, synchronously cancel active output and reset media before connectionNotice. Reset makes lessonReady false, so app guidance is detached from the former lease; reader feedback uses the existing connection status region.
- R05: voice-test calls speaker.cancel(true), and StudentAnnouncer preserves delegated resume intention when replacing guidance; StudentSpeech retains the intention while holding an already-paused lecture and checks its fence before resuming.
- R06/R07: Shift-modified arrows remain native; disabling Space also disables editor double-stop.
- R08: each new text-command session resets input value and returnValue.
- R09: controlDescription exposes only allowlisted numeric settings with units; input announcements debounce for 180 milliseconds, change flushes immediately, and current focus, focusTicket, generation and validity guard delivery.
- R10: visible enabled non-inert home button dispatch occurs before needLesson; accessible names are used and protected permission actions require Enter.
- R11: shared signedIn invokes beforeUserFocus before exposing and focusing the workspace. Student mode application cancels pending speech before that focus; local and browser login success statuses follow signedIn.
- R12 failure uses the same polite local preview-answer target as loading and success, avoiding an additional duplicate global alert.
- R12: guardian preview captures preparation identity, preparationGeneration and question revision. Both success and error settle the existing preview-answer status only for the matching request; stale replies are discarded and a local terminal error replaces pending text without rethrowing a duplicate global error.
- R12: preview questions use preparation/request validity guards and replace pending output with an actionable terminal error only for the matching request.
- R13: retry resets form and validation state, restores source selection, moves guided entry to step 0 and refreshes the view before focusing the title.
- R14: material counting uses Unicode code points; aggregate errors associate specific visible text with the invalid materials field and return guided entry to its material step. The authoritative server bound has a targeted sanitized error.
- R15: native per-sentence controls expose sentence identity, visible highlighted status, current-sentence cursor and stable focus keys while retaining paragraph reading/underline controls.
- R16: sentence/paragraph controls carry stable material keys; rerender restores the active replacement or a visible heading fallback.
- R17: keyboard/pointer/input/focus revisions guard delayed lesson focus, including both focus moves after a pending dirty save.
- R18: focused lecture replacement is restored; removed items use a remaining list control or workspace-title fallback, preserving outside focus.
- Reviewed changed feedback targets: connection, speech-status, reader-description and preview-answer are persistent existing status regions; terminal text updates use textContent without replacing their live-region elements.
- Submit awaits close before command execution; Cancel restores focus without duplicate native-close guidance.
- The account-mode hook runs before programmatic workspace-title focus, and preserves the existing initial interaction guard instead of adding a delayed focus movement.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **keyboard-navigator**: Final scoped source re-review of the requested cancellation/focus fixes; no product/test edits.
- **keyboard-navigator**: Independent ephemeral Node boundary checks: pending play followed by guidance pause was cancelled with zero local play calls; stale seek after reset changed no time; allowPause state snapshot still rejected a view change.
- **keyboard-navigator**: Independent mocked claim check observed worker actions claim then pause when stopping before claim completion. This is not an actual browser/video observation.
- **keyboard-navigator**: Parent reports the existing complete extension regression passed; the R01-R18 browser regression was still running when this source review completed. No fresh physical keyboard, microphone or VoiceOver/NVDA execution by this specialist.
- **modal-specialist**: Final source review only; no product/test edits or live microphone/screen-reader execution.
- **modal-specialist**: The independent mocked media checks described in keyboard.json verify module cancellation boundaries, not actual Chrome permission UI or audio timing.
- **modal-specialist**: No remaining actionable findings within the requested fix scope at this snapshot.
- **live-region-controller**: 2026-11-14 final static source re-review of implemented fixes R03, R04, R05, R09, R11 and R12; this supersedes the pre-implementation safeguards in this directory.
- **live-region-controller**: This specialist did not run the installed extension, actual OS speech, VoiceOver or NVDA during this final re-review. Synthetic speech callbacks and browser/media regressions run by the implementing agent are separate evidence and are not proof of audible or assistive-technology output.
- **live-region-controller**: Scope is the requested fix set and narration ordering, not a new full-product conformance certification.
- **aria-specialist**: 2026-11-14 final static source re-review of implemented fixes R03, R04, R05, R09, R11 and R12; this supersedes the pre-implementation safeguards in this directory.
- **aria-specialist**: This specialist did not run the installed extension, actual OS speech, VoiceOver or NVDA during this final re-review. Synthetic speech callbacks and browser/media regressions run by the implementing agent are separate evidence and are not proof of audible or assistive-technology output.
- **aria-specialist**: Scope is the requested fix set and narration ordering, not a new full-product conformance certification.
- **forms-specialist**: Final 0.4.3 source re-review on 2026-11-14: no unresolved findings in this specialist’s reviewed R01–R03 and R12–R15 scope.
- **forms-specialist**: No product/test edits or independent runtime, OS screen-reader, audible TTS or live-provider validation were performed during this fixes review. Parent regression/API verification is separate.
- **media-accessibility**: Final 0.4.3 source re-review on 2026-11-14: no unresolved findings in this specialist’s reviewed R01–R03 and R12–R15 scope.
- **media-accessibility**: No product/test edits or independent runtime, OS screen-reader, audible TTS or live-provider validation were performed during this fixes review. Parent regression/API verification is separate.

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
    "aria-specialist",
    "forms-specialist",
    "keyboard-navigator",
    "live-region-controller",
    "media-accessibility",
    "modal-specialist"
  ],
  "scope": [
    "apps/api/app/guardian_preparation.py",
    "apps/api/app/main.py:123",
    "apps/extensions/guardian/app.js",
    "apps/extensions/guardian/workspace.html",
    "apps/extensions/shared/ui.js",
    "apps/extensions/student/app.js",
    "apps/extensions/student/keyboard.js",
    "apps/extensions/student/media.js",
    "apps/extensions/student/speech.js",
    "apps/extensions/student/worker.js",
    "apps/extensions/student/workspace.html",
    "scripts/build_extensions.py"
  ],
  "findings": [],
  "passed": [
    "Additional reviewed boundary: Stop during a pending claim now sends a worker pause even before kind is assigned.",
    "Cancel playback restoration requires unchanged lesson/view/generation/action/fence/focus ownership, and media.play rechecks play revision after its RPC.",
    "Changed reading-mode and voice-test controls remain native labelled select/button elements; no substitute custom ARIA widget was introduced.",
    "FIX-R15-PARAGRAPH-CURSOR resolved: resolver-selected paragraphs now align sentenceIndex to the selected paragraph’s first sentence and rerender the current-sentence marker before reading; subsequent next/previous commands use that cursor.",
    "Microphone fallback context is cleared by permission close and explicit stop; recognition completion through its own button remains distinct from abort.",
    "Narration channels remain separate: app guidance updates speech-status, lesson content updates current-description and conditional reader-description, and full reader answers use answer-status. Mode checks suppress app guidance for external-reader mode.",
    "Native dialog naming, visible Cancel, modal Tab scope and Escape remain intact.",
    "Numeric voice guidance reads safe native input values without replacing native labels, roles or validation; password contents and arbitrary text inputs are excluded.",
    "Past-state snapshots may survive an intentional pause but cannot survive a changed media view/generation.",
    "R01: account/lesson/view/action is captured before host permission; context is checked after permission and connection awaits.",
    "R01: app connection context is captured before permission awaits and checked before media reset and subsequent mutations; media methods also validate view/generation/fence.",
    "R02: app seek validates the selected lesson after the media seek response before updating position or saving; local media seek validates its own scope before mutating currentTime.",
    "R02: media operations reject stale view/generation/fence; app seek rechecks context before updating position or saving progress.",
    "R03: StudentMedia invalidates pending play with playRevision when speech is cancelled or pauses media; play rechecks its scope and revision before applying local playback. StudentSpeech preserves wantsPlayback as the prior playback intention before its hold.",
    "R03: pause/reset and speech cancellation invalidate pending play through a separate playRevision, retaining legitimate wantsPlayback intent.",
    "R03: play revision and speech cancellation invalidate pending playback; native play completion/rejection rechecks ownership. Expected cancelled operations do not trigger a new connection reset or user error.",
    "R04: autonomous tick failure and matching lease loss share loseConnection, synchronously cancel active output and reset media before connectionNotice. Reset makes lessonReady false, so app guidance is detached from the former lease; reader feedback uses the existing connection status region.",
    "R05: voice-test calls speaker.cancel(true), and StudentAnnouncer preserves delegated resume intention when replacing guidance; StudentSpeech retains the intention while holding an already-paused lecture and checks its fence before resuming.",
    "R06/R07: Shift-modified arrows remain native; disabling Space also disables editor double-stop.",
    "R08: each new text-command session resets input value and returnValue.",
    "R09: controlDescription exposes only allowlisted numeric settings with units; input announcements debounce for 180 milliseconds, change flushes immediately, and current focus, focusTicket, generation and validity guard delivery.",
    "R10: visible enabled non-inert home button dispatch occurs before needLesson; accessible names are used and protected permission actions require Enter.",
    "R11: shared signedIn invokes beforeUserFocus before exposing and focusing the workspace. Student mode application cancels pending speech before that focus; local and browser login success statuses follow signedIn.",
    "R12 failure uses the same polite local preview-answer target as loading and success, avoiding an additional duplicate global alert.",
    "R12: guardian preview captures preparation identity, preparationGeneration and question revision. Both success and error settle the existing preview-answer status only for the matching request; stale replies are discarded and a local terminal error replaces pending text without rethrowing a duplicate global error.",
    "R12: preview questions use preparation/request validity guards and replace pending output with an actionable terminal error only for the matching request.",
    "R13: retry resets form and validation state, restores source selection, moves guided entry to step 0 and refreshes the view before focusing the title.",
    "R14: material counting uses Unicode code points; aggregate errors associate specific visible text with the invalid materials field and return guided entry to its material step. The authoritative server bound has a targeted sanitized error.",
    "R15: native per-sentence controls expose sentence identity, visible highlighted status, current-sentence cursor and stable focus keys while retaining paragraph reading/underline controls.",
    "R16: sentence/paragraph controls carry stable material keys; rerender restores the active replacement or a visible heading fallback.",
    "R17: keyboard/pointer/input/focus revisions guard delayed lesson focus, including both focus moves after a pending dirty save.",
    "R18: focused lecture replacement is restored; removed items use a remaining list control or workspace-title fallback, preserving outside focus.",
    "Reviewed changed feedback targets: connection, speech-status, reader-description and preview-answer are persistent existing status regions; terminal text updates use textContent without replacing their live-region elements.",
    "Submit awaits close before command execution; Cancel restores focus without duplicate native-close guidance.",
    "The account-mode hook runs before programmatic workspace-title focus, and preserves the existing initial interaction guard instead of adding a delayed focus movement."
  ],
  "notes": [
    {
      "skill": "keyboard-navigator",
      "note": "Final scoped source re-review of the requested cancellation/focus fixes; no product/test edits."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Independent ephemeral Node boundary checks: pending play followed by guidance pause was cancelled with zero local play calls; stale seek after reset changed no time; allowPause state snapshot still rejected a view change."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Independent mocked claim check observed worker actions claim then pause when stopping before claim completion. This is not an actual browser/video observation."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Parent reports the existing complete extension regression passed; the R01-R18 browser regression was still running when this source review completed. No fresh physical keyboard, microphone or VoiceOver/NVDA execution by this specialist."
    },
    {
      "skill": "modal-specialist",
      "note": "Final source review only; no product/test edits or live microphone/screen-reader execution."
    },
    {
      "skill": "modal-specialist",
      "note": "The independent mocked media checks described in keyboard.json verify module cancellation boundaries, not actual Chrome permission UI or audio timing."
    },
    {
      "skill": "modal-specialist",
      "note": "No remaining actionable findings within the requested fix scope at this snapshot."
    },
    {
      "skill": "live-region-controller",
      "note": "2026-11-14 final static source re-review of implemented fixes R03, R04, R05, R09, R11 and R12; this supersedes the pre-implementation safeguards in this directory."
    },
    {
      "skill": "live-region-controller",
      "note": "This specialist did not run the installed extension, actual OS speech, VoiceOver or NVDA during this final re-review. Synthetic speech callbacks and browser/media regressions run by the implementing agent are separate evidence and are not proof of audible or assistive-technology output."
    },
    {
      "skill": "live-region-controller",
      "note": "Scope is the requested fix set and narration ordering, not a new full-product conformance certification."
    },
    {
      "skill": "aria-specialist",
      "note": "2026-11-14 final static source re-review of implemented fixes R03, R04, R05, R09, R11 and R12; this supersedes the pre-implementation safeguards in this directory."
    },
    {
      "skill": "aria-specialist",
      "note": "This specialist did not run the installed extension, actual OS speech, VoiceOver or NVDA during this final re-review. Synthetic speech callbacks and browser/media regressions run by the implementing agent are separate evidence and are not proof of audible or assistive-technology output."
    },
    {
      "skill": "aria-specialist",
      "note": "Scope is the requested fix set and narration ordering, not a new full-product conformance certification."
    },
    {
      "skill": "forms-specialist",
      "note": "Final 0.4.3 source re-review on 2026-11-14: no unresolved findings in this specialist’s reviewed R01–R03 and R12–R15 scope."
    },
    {
      "skill": "forms-specialist",
      "note": "No product/test edits or independent runtime, OS screen-reader, audible TTS or live-provider validation were performed during this fixes review. Parent regression/API verification is separate."
    },
    {
      "skill": "media-accessibility",
      "note": "Final 0.4.3 source re-review on 2026-11-14: no unresolved findings in this specialist’s reviewed R01–R03 and R12–R15 scope."
    },
    {
      "skill": "media-accessibility",
      "note": "No product/test edits or independent runtime, OS screen-reader, audible TTS or live-provider validation were performed during this fixes review. Parent regression/API verification is separate."
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
  "checks": 35,
  "generated": "2026-11-14",
  "template": "web"
}
```
