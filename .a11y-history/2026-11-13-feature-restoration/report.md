# Web Accessibility Audit

An audit of web content, run on 2026-11-13. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-13 |
| Scope | 9 items |
| Skills run | aria-specialist, forms-specialist, keyboard-navigator, live-region-controller, media-accessibility, modal-specialist |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 42 |

Audited:

- `apps/api/app/guardian_preparation.py`
- `apps/extensions/guardian/app.js`
- `apps/extensions/guardian/workspace.html`
- `apps/extensions/student/app.js`
- `apps/extensions/student/keyboard.js`
- `apps/extensions/student/media.js`
- `apps/extensions/student/speech.js`
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

## Delta tracking

Movement since the previous report.

| Change | Count |
|---|---:|
| Fixed | 0 |
| New | 0 |
| Persistent | 0 |
| Regressed | 0 |

Score moved from 100 to 100.

## What passed

42 checks ran and found nothing.

- Answer speech remains independent of focus guidance, and ordinary reader answers use one full-answer channel.
- Automatic first-use help now updates the persistent voice-status region when focus is intentionally retained.
- Bounded lecturer-to-AI playback is present with cancellation and media fences; guarded seek callers stop stale continuations.
- Concept startup rejects advertisements and unknown duration before computing a bounded content endpoint.
- Delegated guidance uses purpose=guidance and updates speech-status instead of replacing the current lesson explanation.
- Dialog returnValue resets on every open; submitted commands await close before executing.
- Editor emergency stop ignores modifier chords and interrupted/cross-focus tap sequences.
- External-reader focus pauses ready media and does not automatically resume over reader speech.
- Final re-read confirms original opening/closing prosody adjustments are restored alongside sentence chunking, voice ranking and speech-style profiles.
- First-use help, persistent replay button and reader status notice restored; help completion preserves focus when user has moved away.
- Guardian prepared-note export downloads only summary and study-guide text as local Markdown; it does not transfer original video or held visual candidates.
- Guardian preview exposes transcript, safe visual descriptions, concepts, review categories, study material, decision reasons, consented chat and explicit original-file delivery instructions.
- Guidance status and lesson description have separate output channels.
- Guided entry uses fieldset/legend grouping, announced stage text and focus on the current legend; invalid native controls receive focus.
- Guided material validation now exempts missing files/passage only for an actual checked link-analysis source; stale disabled checkbox state cannot bypass the check.
- Home command and onboarding headings retain a coherent workspace heading hierarchy.
- Home command controls, help-before-lesson handling and first-use onboarding are present.
- Inter-chunk delay is cancellable and narration rechecks cancellation generation before subsequent chunks and prior-state resume.
- Invalid concept runs clear their timer, including reader-mode focus changes; stop and stale seek checks fence both playback and AI handoff.
- Local media state snapshots before its await; triple-Space retains sequence-start playback state across the intermediate stop.
- Microphone completion remains fenced against cancellation and context changes; voiceFallback is cleared on permission close and explicit stop.
- Narration restores sentence-aware chunking, ranked Korean voice selection and warm/calm/clear profiles from the original source.
- Native labelled dialogs retain visible cancel controls, modal Tab scope and Escape dismissal.
- New style and preview controls use native labelled HTML.
- Non-Space navigation, focus change and composition reset cancel pending gestures and recognition.
- Onboarding availability is delivered through an existing persistent status region.
- Opening and closing rate/pitch modifiers and punctuation-sensitive 70/130ms inter-chunk delays are present.
- Original Korean voice scoring, pronunciation normalization and sentence chunk helpers are packaged and shared by narration and guidance.
- Permanent deletion confirmation names the lecture and affected assignments/records, describes retained preparation/files, associates the question with execution, and provides cancellation/focus return.
- Prepared-note export is a descriptively named native type=button control, guarded against missing preparation; completion/error uses the existing accessible status mechanism and the control remains in place.
- Preview questions require explicit Gemini-data consent; server rejects missing consent.
- Reader answer and narration status regions remain persistent and native controls retain accessible names and states.
- Ready-media focus/status guidance uses acknowledged pause and guarded conditional resume; login guidance remains independent of media.
- Review now uses visual_only_information, renders key-segment descriptions visibly, includes highlighted material and study overview, and supports reading without connected video.
- Source label and explanation focus have native labels, bounded input and explicit selectable modes; both JSON and multipart submissions preserve the values.
- Student-home gesture scope and visible voice/text command entry restored.
- Text-modal cancellation restores focus without triggering native-close focus guidance, and resumes only with unchanged lesson/view/generation/action/fence/focus revision.
- Updated Space contract, DOM-adjacent Tab, standalone Shift and explicit Escape exit retained.
- Verified guardian-local preview originals receive generated WebVTT captions; unverified or missing timed captions are explained.
- Voice preview now preserves prior playback intent through the default state-aware resume path.
- Voice-button pointerdown/focusin/Enter completion preserves recognition until startVoice calls recognition.stop(); unrelated interaction and reset still abort recognition.
- Voice-recognition and microphone failure fallbacks carry the playback snapshot captured before stopping.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **keyboard-navigator**: Final source re-review after parent notification. Earlier restoration observations were corrected before this snapshot.
- **keyboard-navigator**: Ephemeral Node mocked-event checks: home gesture down/up 1/1, Space-letter-Space stops 0, consecutive editor double stops 1, Ctrl+Space pair stops 0, focus-change aborts 1.
- **keyboard-navigator**: No product/test edits; no physical keyboard or live browser/screen-reader execution by this specialist. Browser regression is handled separately by the parent.
- **keyboard-navigator**: Final incremental source review: reset/cancelPending forward the initiating event and only #voice pointerdown/focusin/Enter bypass recognition abort. No new findings.
- **keyboard-navigator**: Parent reports browser mouse/Enter start-to-completion regression passed with one recognizer start and transcript execution; this specialist did not independently rerun that browser test.
- **modal-specialist**: Final source re-review after parent notification; earlier snapshot, cancellation and fallback observations were corrected.
- **modal-specialist**: No actual microphone, physical keyboard, screen-reader or browser-timing execution by this specialist; parent runs browser regression separately.
- **modal-specialist**: Only audit JSON artifacts were written.
- **modal-specialist**: Final incremental source review: reset/cancelPending forward the initiating event and only #voice pointerdown/focusin/Enter bypass recognition abort. No new findings.
- **modal-specialist**: Parent reports browser mouse/Enter start-to-completion regression passed with one recognizer start and transcript execution; this specialist did not independently rerun that browser test.
- **live-region-controller**: All reported restoration findings are corrected in the current reviewed source.
- **live-region-controller**: Final static source review only; actual Korean TTS/audio quality and VoiceOver/NVDA speech were not executed or verified.
- **live-region-controller**: Original Mac native startup greeting remains a documented platform difference; browser startup sound is subject to browser policy.
- **live-region-controller**: No product or test files were modified by this review.
- **aria-specialist**: No remaining source-level ARIA findings in the reviewed restoration scope.
- **aria-specialist**: Static semantic review only; actual screen-reader speech, announcement ordering and audio output were not executed or verified.
- **aria-specialist**: No product or test files were modified by this review.
- **media-accessibility**: Final source re-review on 2026-11-13 includes the preview-export addition. No unresolved findings in the reviewed scope. No live media, caption-quality, TTS, browser, assistive-technology or provider tests were executed by this specialist.
- **media-accessibility**: Independent extension origins require explicit manual delivery of the same original video to the student; the preview UI explains this limitation.
- **media-accessibility**: Parent separately reports two-extension regression and 14-screen axe checks passed with zero violations; those checks were not executed by this specialist.
- **forms-specialist**: Final source re-review on 2026-11-13 includes the preview-export addition. No unresolved findings in the reviewed scope. No live media, caption-quality, TTS, browser, assistive-technology or provider tests were executed by this specialist.
- **forms-specialist**: Independent extension origins require explicit manual delivery of the same original video to the student; the preview UI explains this limitation.
- **forms-specialist**: Parent separately reports two-extension regression and 14-screen axe checks passed with zero violations; those checks were not executed by this specialist.

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
    "apps/extensions/guardian/app.js",
    "apps/extensions/guardian/workspace.html",
    "apps/extensions/student/app.js",
    "apps/extensions/student/keyboard.js",
    "apps/extensions/student/media.js",
    "apps/extensions/student/speech.js",
    "apps/extensions/student/workspace.html",
    "scripts/build_extensions.py"
  ],
  "findings": [],
  "passed": [
    "Answer speech remains independent of focus guidance, and ordinary reader answers use one full-answer channel.",
    "Automatic first-use help now updates the persistent voice-status region when focus is intentionally retained.",
    "Bounded lecturer-to-AI playback is present with cancellation and media fences; guarded seek callers stop stale continuations.",
    "Concept startup rejects advertisements and unknown duration before computing a bounded content endpoint.",
    "Delegated guidance uses purpose=guidance and updates speech-status instead of replacing the current lesson explanation.",
    "Dialog returnValue resets on every open; submitted commands await close before executing.",
    "Editor emergency stop ignores modifier chords and interrupted/cross-focus tap sequences.",
    "External-reader focus pauses ready media and does not automatically resume over reader speech.",
    "Final re-read confirms original opening/closing prosody adjustments are restored alongside sentence chunking, voice ranking and speech-style profiles.",
    "First-use help, persistent replay button and reader status notice restored; help completion preserves focus when user has moved away.",
    "Guardian prepared-note export downloads only summary and study-guide text as local Markdown; it does not transfer original video or held visual candidates.",
    "Guardian preview exposes transcript, safe visual descriptions, concepts, review categories, study material, decision reasons, consented chat and explicit original-file delivery instructions.",
    "Guidance status and lesson description have separate output channels.",
    "Guided entry uses fieldset/legend grouping, announced stage text and focus on the current legend; invalid native controls receive focus.",
    "Guided material validation now exempts missing files/passage only for an actual checked link-analysis source; stale disabled checkbox state cannot bypass the check.",
    "Home command and onboarding headings retain a coherent workspace heading hierarchy.",
    "Home command controls, help-before-lesson handling and first-use onboarding are present.",
    "Inter-chunk delay is cancellable and narration rechecks cancellation generation before subsequent chunks and prior-state resume.",
    "Invalid concept runs clear their timer, including reader-mode focus changes; stop and stale seek checks fence both playback and AI handoff.",
    "Local media state snapshots before its await; triple-Space retains sequence-start playback state across the intermediate stop.",
    "Microphone completion remains fenced against cancellation and context changes; voiceFallback is cleared on permission close and explicit stop.",
    "Narration restores sentence-aware chunking, ranked Korean voice selection and warm/calm/clear profiles from the original source.",
    "Native labelled dialogs retain visible cancel controls, modal Tab scope and Escape dismissal.",
    "New style and preview controls use native labelled HTML.",
    "Non-Space navigation, focus change and composition reset cancel pending gestures and recognition.",
    "Onboarding availability is delivered through an existing persistent status region.",
    "Opening and closing rate/pitch modifiers and punctuation-sensitive 70/130ms inter-chunk delays are present.",
    "Original Korean voice scoring, pronunciation normalization and sentence chunk helpers are packaged and shared by narration and guidance.",
    "Permanent deletion confirmation names the lecture and affected assignments/records, describes retained preparation/files, associates the question with execution, and provides cancellation/focus return.",
    "Prepared-note export is a descriptively named native type=button control, guarded against missing preparation; completion/error uses the existing accessible status mechanism and the control remains in place.",
    "Preview questions require explicit Gemini-data consent; server rejects missing consent.",
    "Reader answer and narration status regions remain persistent and native controls retain accessible names and states.",
    "Ready-media focus/status guidance uses acknowledged pause and guarded conditional resume; login guidance remains independent of media.",
    "Review now uses visual_only_information, renders key-segment descriptions visibly, includes highlighted material and study overview, and supports reading without connected video.",
    "Source label and explanation focus have native labels, bounded input and explicit selectable modes; both JSON and multipart submissions preserve the values.",
    "Student-home gesture scope and visible voice/text command entry restored.",
    "Text-modal cancellation restores focus without triggering native-close focus guidance, and resumes only with unchanged lesson/view/generation/action/fence/focus revision.",
    "Updated Space contract, DOM-adjacent Tab, standalone Shift and explicit Escape exit retained.",
    "Verified guardian-local preview originals receive generated WebVTT captions; unverified or missing timed captions are explained.",
    "Voice preview now preserves prior playback intent through the default state-aware resume path.",
    "Voice-button pointerdown/focusin/Enter completion preserves recognition until startVoice calls recognition.stop(); unrelated interaction and reset still abort recognition.",
    "Voice-recognition and microphone failure fallbacks carry the playback snapshot captured before stopping."
  ],
  "notes": [
    {
      "skill": "keyboard-navigator",
      "note": "Final source re-review after parent notification. Earlier restoration observations were corrected before this snapshot."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Ephemeral Node mocked-event checks: home gesture down/up 1/1, Space-letter-Space stops 0, consecutive editor double stops 1, Ctrl+Space pair stops 0, focus-change aborts 1."
    },
    {
      "skill": "keyboard-navigator",
      "note": "No product/test edits; no physical keyboard or live browser/screen-reader execution by this specialist. Browser regression is handled separately by the parent."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Final incremental source review: reset/cancelPending forward the initiating event and only #voice pointerdown/focusin/Enter bypass recognition abort. No new findings."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Parent reports browser mouse/Enter start-to-completion regression passed with one recognizer start and transcript execution; this specialist did not independently rerun that browser test."
    },
    {
      "skill": "modal-specialist",
      "note": "Final source re-review after parent notification; earlier snapshot, cancellation and fallback observations were corrected."
    },
    {
      "skill": "modal-specialist",
      "note": "No actual microphone, physical keyboard, screen-reader or browser-timing execution by this specialist; parent runs browser regression separately."
    },
    {
      "skill": "modal-specialist",
      "note": "Only audit JSON artifacts were written."
    },
    {
      "skill": "modal-specialist",
      "note": "Final incremental source review: reset/cancelPending forward the initiating event and only #voice pointerdown/focusin/Enter bypass recognition abort. No new findings."
    },
    {
      "skill": "modal-specialist",
      "note": "Parent reports browser mouse/Enter start-to-completion regression passed with one recognizer start and transcript execution; this specialist did not independently rerun that browser test."
    },
    {
      "skill": "live-region-controller",
      "note": "All reported restoration findings are corrected in the current reviewed source."
    },
    {
      "skill": "live-region-controller",
      "note": "Final static source review only; actual Korean TTS/audio quality and VoiceOver/NVDA speech were not executed or verified."
    },
    {
      "skill": "live-region-controller",
      "note": "Original Mac native startup greeting remains a documented platform difference; browser startup sound is subject to browser policy."
    },
    {
      "skill": "live-region-controller",
      "note": "No product or test files were modified by this review."
    },
    {
      "skill": "aria-specialist",
      "note": "No remaining source-level ARIA findings in the reviewed restoration scope."
    },
    {
      "skill": "aria-specialist",
      "note": "Static semantic review only; actual screen-reader speech, announcement ordering and audio output were not executed or verified."
    },
    {
      "skill": "aria-specialist",
      "note": "No product or test files were modified by this review."
    },
    {
      "skill": "media-accessibility",
      "note": "Final source re-review on 2026-11-13 includes the preview-export addition. No unresolved findings in the reviewed scope. No live media, caption-quality, TTS, browser, assistive-technology or provider tests were executed by this specialist."
    },
    {
      "skill": "media-accessibility",
      "note": "Independent extension origins require explicit manual delivery of the same original video to the student; the preview UI explains this limitation."
    },
    {
      "skill": "media-accessibility",
      "note": "Parent separately reports two-extension regression and 14-screen axe checks passed with zero violations; those checks were not executed by this specialist."
    },
    {
      "skill": "forms-specialist",
      "note": "Final source re-review on 2026-11-13 includes the preview-export addition. No unresolved findings in the reviewed scope. No live media, caption-quality, TTS, browser, assistive-technology or provider tests were executed by this specialist."
    },
    {
      "skill": "forms-specialist",
      "note": "Independent extension origins require explicit manual delivery of the same original video to the student; the preview UI explains this limitation."
    },
    {
      "skill": "forms-specialist",
      "note": "Parent separately reports two-extension regression and 14-screen axe checks passed with zero violations; those checks were not executed by this specialist."
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
  "checks": 42,
  "generated": "2026-11-13",
  "template": "web"
}
```
