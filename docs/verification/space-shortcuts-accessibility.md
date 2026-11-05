# Web Accessibility Audit

An audit of web content, run on 2026-11-05. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-05 |
| Scope | 7 items |
| Skills run | keyboard-navigator |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 11 |

Audited:

- `apps/web/app.js:1502`
- `apps/web/index.html:319`
- `apps/web/role-portal.js:558`
- `apps/web/role-portal.js:618`
- `apps/web/space-gesture.js`
- `apps/web/voice-command-router.js`
- `scripts/verify_keyboard_navigation.py:76`

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

11 checks ran and found nothing.

- Delayed intercepted agent success and error responses cannot speak, restart playback or replace stopped-output status after double Space; both output-generation boundaries passed.
- Double Space stops without clicking the focused button; triple Space opens text commands without first navigating or activating; Enter/Space/Escape dialog flow restores the relevant origin.
- Final 28-case browser matrix passed after the latest changes: single native-button Space is deferred once; paused/playing toggles remain correct; Enter is immediate and cancels any pending single activation.
- Global student shortcuts work on lesson buttons, student home, header logout and onboarding controls. Native checkbox single Space still toggles after its documented delay; text inputs, select controls and modifier chords retain their expected behavior.
- Guardian and signed-out native single Space remain immediate and do not open student gestures.
- Hold starts recognition after stopping current app narration. Pre-threshold focus/window cancellation, active-recognition Tab cancellation and post-release window cancellation leave no delayed fallback dialog.
- No-recognition fallback opens a usable empty text dialog and Escape returns to student home. Voice lecture-list command from the home header focuses the assigned lecture instead of jumping to a hidden command surface.
- Reviewed durable browser regressions and updated help text for deferred activation, global student use, editor emergency stopping and cancellation.
- Text-modal hold on Close followed by Tab now aborts recognition and preserves the existing draft after the full 1500ms finalization window.
- Three-line summary contains exactly three lines; double Space stops speech/playback and invalidates late utterance completion. Ordinary typing a b c does not trigger emergency stop; two consecutive editor spaces preserve both characters and stop active narration.
- Typed lecture-list/numbered selection and stop-summary/resume-lecture/stop-video aliases execute the intended actions.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **keyboard-navigator**: Verdict: no remaining reproducible keyboard defect found in the final working diff. There are 35 targeted runtime checks across the main matrix and focused boundaries; no browser errors.
- **keyboard-navigator**: Three interim cancellation defects were reported and fixed during review: active recognition surviving focus movement, delayed finalization reopening after blur, and the modal exemption erasing an existing draft. Final checks confirm each is closed; they are not outstanding findings.
- **keyboard-navigator**: Durable evidence: docs/verification/space-shortcuts/keyboard-specialist-results.json. Detailed scripts/results are under /tmp/space-fix-audit/. Main matrix was rerun after the last non-Space/editor-timer/narration-cancellation changes.
- **keyboard-navigator**: Chrome/156.0.8078.80 with Puppeteer. Used only a disposable server on port 8892 with temporary account and usage databases. Provider settings removed; recognition, synthesis, YouTube and delayed agent responses mocked. No real microphone, provider or private account/database access. Native screen-reader speech and physical ASR accuracy were not tested.
- **keyboard-navigator**: No product or test edits by this reviewer; only requested audit/evidence artifacts were written.

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
    "apps/web/app.js:1502",
    "apps/web/index.html:319",
    "apps/web/role-portal.js:558",
    "apps/web/role-portal.js:618",
    "apps/web/space-gesture.js",
    "apps/web/voice-command-router.js",
    "scripts/verify_keyboard_navigation.py:76"
  ],
  "findings": [],
  "passed": [
    "Delayed intercepted agent success and error responses cannot speak, restart playback or replace stopped-output status after double Space; both output-generation boundaries passed.",
    "Double Space stops without clicking the focused button; triple Space opens text commands without first navigating or activating; Enter/Space/Escape dialog flow restores the relevant origin.",
    "Final 28-case browser matrix passed after the latest changes: single native-button Space is deferred once; paused/playing toggles remain correct; Enter is immediate and cancels any pending single activation.",
    "Global student shortcuts work on lesson buttons, student home, header logout and onboarding controls. Native checkbox single Space still toggles after its documented delay; text inputs, select controls and modifier chords retain their expected behavior.",
    "Guardian and signed-out native single Space remain immediate and do not open student gestures.",
    "Hold starts recognition after stopping current app narration. Pre-threshold focus/window cancellation, active-recognition Tab cancellation and post-release window cancellation leave no delayed fallback dialog.",
    "No-recognition fallback opens a usable empty text dialog and Escape returns to student home. Voice lecture-list command from the home header focuses the assigned lecture instead of jumping to a hidden command surface.",
    "Reviewed durable browser regressions and updated help text for deferred activation, global student use, editor emergency stopping and cancellation.",
    "Text-modal hold on Close followed by Tab now aborts recognition and preserves the existing draft after the full 1500ms finalization window.",
    "Three-line summary contains exactly three lines; double Space stops speech/playback and invalidates late utterance completion. Ordinary typing a b c does not trigger emergency stop; two consecutive editor spaces preserve both characters and stop active narration.",
    "Typed lecture-list/numbered selection and stop-summary/resume-lecture/stop-video aliases execute the intended actions."
  ],
  "notes": [
    {
      "skill": "keyboard-navigator",
      "note": "Verdict: no remaining reproducible keyboard defect found in the final working diff. There are 35 targeted runtime checks across the main matrix and focused boundaries; no browser errors."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Three interim cancellation defects were reported and fixed during review: active recognition surviving focus movement, delayed finalization reopening after blur, and the modal exemption erasing an existing draft. Final checks confirm each is closed; they are not outstanding findings."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Durable evidence: docs/verification/space-shortcuts/keyboard-specialist-results.json. Detailed scripts/results are under /tmp/space-fix-audit/. Main matrix was rerun after the last non-Space/editor-timer/narration-cancellation changes."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Chrome/156.0.8078.80 with Puppeteer. Used only a disposable server on port 8892 with temporary account and usage databases. Provider settings removed; recognition, synthesis, YouTube and delayed agent responses mocked. No real microphone, provider or private account/database access. Native screen-reader speech and physical ASR accuracy were not tested."
    },
    {
      "skill": "keyboard-navigator",
      "note": "No product or test edits by this reviewer; only requested audit/evidence artifacts were written."
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
  "checks": 11,
  "generated": "2026-11-05",
  "template": "web"
}
```
