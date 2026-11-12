# Web Accessibility Audit

An audit of web content, run on 2026-11-12. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-12 |
| Scope | 6 items |
| Skills run | forms-specialist, keyboard-navigator, live-region-controller |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 29 |

Audited:

- `apps/extensions/guardian/app.js`
- `apps/extensions/guardian/workspace.html`
- `apps/extensions/shared/base.css`
- `apps/extensions/shared/client.js`
- `apps/extensions/shared/ui.js`
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

29 checks ran and found nothing.

- Background connection failures are deduplicated by message and use a polite region; successful reconnection is announced once.
- Independent registration/login keep password-manager autocomplete and allow password entry without cognitive challenges.
- Known job IDs announce transitions to completed, failed or interrupted once; unchanged polling snapshots and the initial snapshot do not announce.
- Live messages use textContent and persistent region elements.
- Material and video size/processing explanations are visible and associated with their file inputs.
- Missing student selection focuses the corresponding fieldset before reporting an error.
- Native required, numeric bounds, string length and username pattern validation remain available.
- Persistent polite #job-status and #connection-status regions exist before job updates.
- Polling avoids rebuilding unchanged job lists and restores the focused job action by stable job ID when a changed list is rendered.
- Preparation submission immediately announces upload/request progress before awaiting a potentially long network request.
- Preparation submissions seed the job-state map so fast completion can still produce a terminal-state announcement.
- Preparation, publishing, assignment editing, settings, and order controls use native keyboard-operable elements without positive tabindex or single-key interception.
- Publishing, settings, reordering, refresh and logout retain explicit success feedback.
- Re-review confirmed inactive preparation controls are disabled as well as hidden; isolated Chromium reproduction now submits materials mode after an invalid hidden link.
- Reordering has explicit up/down buttons, disables out-of-range actions, and restores focus to an available action on the moved lecture.
- Required preparation fields/consents have visible indication and associated instructions describe file-versus-pasted-passage alternatives.
- Reviewed inputs, file controls, selects and textareas have native wrapping labels.
- Shared asynchronous task handling retains native focus and suppresses duplicate activation with guarded aria-disabled and aria-busy states.
- Shared asynchronous task helper preserves native focus using aria-disabled/aria-busy and guards repeated activation.
- Skip link, native details/summary, and visible focus styling remain available; no keyboard trap or sticky focus obstruction was found in reviewed source.
- Source, URL and original-file changes reset rights and transmission consent; changing analysis mode resets transmission consent.
- Student assignment checkboxes are grouped by fieldset/legend with a minimum-selection instruction.
- Success and error messages use persistent status/alert regions; failed submissions retain entered values.
- Successful preparation, publishing, editing, student management, and result opening explicitly focus visible headings with tabindex=-1.
- The full job list remains non-live, preventing full-list rereading on each poll.
- Video source likewise disables the hidden URL and material inputs while enabling its required original-file input.
- Withdrawal confirmation button is associated with the affected-course/student-count question via aria-describedby.
- Withdrawal confirmation is an inline nonmodal region; opening focuses its confirm button, cancellation returns to the invoking button, and completion focuses the editor heading.
- Withdrawal requires a separate confirmation action and exposes a cancellation path.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **forms-specialist**: All three previously reported findings are resolved within the reviewed scope.
- **forms-specialist**: Source re-review plus isolated Chromium regression; full installed-extension flow was reported by the parent agent, not executed by this specialist.
- **forms-specialist**: Actual screen-reader audio was not tested. No remaining forms findings identified in this phase-2 review.
- **keyboard-navigator**: Source review only: no complete extension browser, actual screen-reader, or platform file-dialog execution was performed by this specialist.
- **keyboard-navigator**: No critical or serious keyboard finding was identified within the current phase-2 scope.
- **keyboard-navigator**: Live announcements for automatically changing job statuses are outside this keyboard review and should be checked with the dynamic-content review.
- **live-region-controller**: All three initial live-region findings have been corrected in the reviewed source.
- **live-region-controller**: Static source re-review only; actual VoiceOver/NVDA announcement order and speech were not executed.
- **live-region-controller**: No critical or serious live-region findings remain within this scope.
- **live-region-controller**: Persisted to .a11y-history/2026-11-12-extensions-phase2/live.json.

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
    "forms-specialist",
    "keyboard-navigator",
    "live-region-controller"
  ],
  "scope": [
    "apps/extensions/guardian/app.js",
    "apps/extensions/guardian/workspace.html",
    "apps/extensions/shared/base.css",
    "apps/extensions/shared/client.js",
    "apps/extensions/shared/ui.js",
    "scripts/build_extensions.py"
  ],
  "findings": [],
  "passed": [
    "Background connection failures are deduplicated by message and use a polite region; successful reconnection is announced once.",
    "Independent registration/login keep password-manager autocomplete and allow password entry without cognitive challenges.",
    "Known job IDs announce transitions to completed, failed or interrupted once; unchanged polling snapshots and the initial snapshot do not announce.",
    "Live messages use textContent and persistent region elements.",
    "Material and video size/processing explanations are visible and associated with their file inputs.",
    "Missing student selection focuses the corresponding fieldset before reporting an error.",
    "Native required, numeric bounds, string length and username pattern validation remain available.",
    "Persistent polite #job-status and #connection-status regions exist before job updates.",
    "Polling avoids rebuilding unchanged job lists and restores the focused job action by stable job ID when a changed list is rendered.",
    "Preparation submission immediately announces upload/request progress before awaiting a potentially long network request.",
    "Preparation submissions seed the job-state map so fast completion can still produce a terminal-state announcement.",
    "Preparation, publishing, assignment editing, settings, and order controls use native keyboard-operable elements without positive tabindex or single-key interception.",
    "Publishing, settings, reordering, refresh and logout retain explicit success feedback.",
    "Re-review confirmed inactive preparation controls are disabled as well as hidden; isolated Chromium reproduction now submits materials mode after an invalid hidden link.",
    "Reordering has explicit up/down buttons, disables out-of-range actions, and restores focus to an available action on the moved lecture.",
    "Required preparation fields/consents have visible indication and associated instructions describe file-versus-pasted-passage alternatives.",
    "Reviewed inputs, file controls, selects and textareas have native wrapping labels.",
    "Shared asynchronous task handling retains native focus and suppresses duplicate activation with guarded aria-disabled and aria-busy states.",
    "Shared asynchronous task helper preserves native focus using aria-disabled/aria-busy and guards repeated activation.",
    "Skip link, native details/summary, and visible focus styling remain available; no keyboard trap or sticky focus obstruction was found in reviewed source.",
    "Source, URL and original-file changes reset rights and transmission consent; changing analysis mode resets transmission consent.",
    "Student assignment checkboxes are grouped by fieldset/legend with a minimum-selection instruction.",
    "Success and error messages use persistent status/alert regions; failed submissions retain entered values.",
    "Successful preparation, publishing, editing, student management, and result opening explicitly focus visible headings with tabindex=-1.",
    "The full job list remains non-live, preventing full-list rereading on each poll.",
    "Video source likewise disables the hidden URL and material inputs while enabling its required original-file input.",
    "Withdrawal confirmation button is associated with the affected-course/student-count question via aria-describedby.",
    "Withdrawal confirmation is an inline nonmodal region; opening focuses its confirm button, cancellation returns to the invoking button, and completion focuses the editor heading.",
    "Withdrawal requires a separate confirmation action and exposes a cancellation path."
  ],
  "notes": [
    {
      "skill": "forms-specialist",
      "note": "All three previously reported findings are resolved within the reviewed scope."
    },
    {
      "skill": "forms-specialist",
      "note": "Source re-review plus isolated Chromium regression; full installed-extension flow was reported by the parent agent, not executed by this specialist."
    },
    {
      "skill": "forms-specialist",
      "note": "Actual screen-reader audio was not tested. No remaining forms findings identified in this phase-2 review."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Source review only: no complete extension browser, actual screen-reader, or platform file-dialog execution was performed by this specialist."
    },
    {
      "skill": "keyboard-navigator",
      "note": "No critical or serious keyboard finding was identified within the current phase-2 scope."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Live announcements for automatically changing job statuses are outside this keyboard review and should be checked with the dynamic-content review."
    },
    {
      "skill": "live-region-controller",
      "note": "All three initial live-region findings have been corrected in the reviewed source."
    },
    {
      "skill": "live-region-controller",
      "note": "Static source re-review only; actual VoiceOver/NVDA announcement order and speech were not executed."
    },
    {
      "skill": "live-region-controller",
      "note": "No critical or serious live-region findings remain within this scope."
    },
    {
      "skill": "live-region-controller",
      "note": "Persisted to .a11y-history/2026-11-12-extensions-phase2/live.json."
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
  "checks": 29,
  "generated": "2026-11-12",
  "template": "web"
}
```
