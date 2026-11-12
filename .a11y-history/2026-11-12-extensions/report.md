# Web Accessibility Audit

An audit of web content, run on 2026-11-12. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-12 |
| Scope | 13 items |
| Skills run | forms-specialist, keyboard-navigator |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 16 |

Audited:

- `/Users/joy/Documents/Codex/Sullivan-AI-Develop-local/apps/extensions/guardian/app.js`
- `/Users/joy/Documents/Codex/Sullivan-AI-Develop-local/apps/extensions/guardian/workspace.html`
- `/Users/joy/Documents/Codex/Sullivan-AI-Develop-local/apps/extensions/shared/client.js`
- `/Users/joy/Documents/Codex/Sullivan-AI-Develop-local/apps/extensions/shared/ui.js`
- `/Users/joy/Documents/Codex/Sullivan-AI-Develop-local/apps/extensions/student/workspace.html`
- `/Users/joy/Documents/Codex/Sullivan-AI-Develop-local/scripts/build_extensions.py`
- `apps/extensions/guardian/app.js`
- `apps/extensions/guardian/workspace.html`
- `apps/extensions/shared/base.css`
- `apps/extensions/shared/ui.js`
- `apps/extensions/student/app.js`
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

16 checks ran and found nothing.

- An isolated Chromium execution of the current task() helper retained focus during and after the pending action and blocked duplicate activation.
- CSS provides a 4px focus-visible outline; no sticky header obscures focus.
- Existing-account login submits only username and password, avoiding registration name validation.
- Failed requests preserve entered values, while successful account creation clears submitted credentials.
- First-in-DOM skip link targets the main landmark with tabindex=-1; no positive tabindex or single-character shortcut interception was found.
- Guardian registration has a separate form with a required name and new-password autocomplete.
- Initial restoration keeps the authentication subtree hidden until restoration completes and tracks keyboard/pointer interaction before assigning initial focus.
- Native buttons, inputs, selects and details/summary support keyboard operation without custom keyboard traps.
- Password-manager autocomplete and unrestricted password input support accessible authentication.
- Persistent role=status and role=alert regions provide submission feedback.
- Re-review confirmed focused asynchronous controls now use aria-disabled/aria-busy plus a duplicate-action guard instead of native disabling.
- Reviewed controls use native wrapping labels and native required, pattern, length, and range validation.
- Successful login, logout, student creation and lesson opening explicitly assign a destination focus.
- The manual playback-position explanation is associated with its numeric input.
- Username format guidance is visible and programmatically associated.
- Visible 8–128-character password instructions are associated with login, guardian registration, and student creation inputs.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **forms-specialist**: Re-review of current source after remediation; both previously reported moderate findings are resolved.
- **forms-specialist**: Static form review only; no screen-reader or browser execution was performed by this specialist.
- **forms-specialist**: No critical or serious forms findings remain within the reviewed phase-1 scope.
- **keyboard-navigator**: The two initial source-review findings KEYBOARD-ASYNC-FOCUS and KEYBOARD-RESTORE-FOCUS were corrected in the reviewed revision.
- **keyboard-navigator**: This is a source re-review with an isolated Chromium helper probe, not a full extension or screen-reader audit.
- **keyboard-navigator**: Actual side-panel focus transfer and VoiceOver/NVDA end-to-end verification remain necessary.

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
    "keyboard-navigator"
  ],
  "scope": [
    "/Users/joy/Documents/Codex/Sullivan-AI-Develop-local/apps/extensions/guardian/app.js",
    "/Users/joy/Documents/Codex/Sullivan-AI-Develop-local/apps/extensions/guardian/workspace.html",
    "/Users/joy/Documents/Codex/Sullivan-AI-Develop-local/apps/extensions/shared/client.js",
    "/Users/joy/Documents/Codex/Sullivan-AI-Develop-local/apps/extensions/shared/ui.js",
    "/Users/joy/Documents/Codex/Sullivan-AI-Develop-local/apps/extensions/student/workspace.html",
    "/Users/joy/Documents/Codex/Sullivan-AI-Develop-local/scripts/build_extensions.py",
    "apps/extensions/guardian/app.js",
    "apps/extensions/guardian/workspace.html",
    "apps/extensions/shared/base.css",
    "apps/extensions/shared/ui.js",
    "apps/extensions/student/app.js",
    "apps/extensions/student/workspace.html",
    "scripts/build_extensions.py"
  ],
  "findings": [],
  "passed": [
    "An isolated Chromium execution of the current task() helper retained focus during and after the pending action and blocked duplicate activation.",
    "CSS provides a 4px focus-visible outline; no sticky header obscures focus.",
    "Existing-account login submits only username and password, avoiding registration name validation.",
    "Failed requests preserve entered values, while successful account creation clears submitted credentials.",
    "First-in-DOM skip link targets the main landmark with tabindex=-1; no positive tabindex or single-character shortcut interception was found.",
    "Guardian registration has a separate form with a required name and new-password autocomplete.",
    "Initial restoration keeps the authentication subtree hidden until restoration completes and tracks keyboard/pointer interaction before assigning initial focus.",
    "Native buttons, inputs, selects and details/summary support keyboard operation without custom keyboard traps.",
    "Password-manager autocomplete and unrestricted password input support accessible authentication.",
    "Persistent role=status and role=alert regions provide submission feedback.",
    "Re-review confirmed focused asynchronous controls now use aria-disabled/aria-busy plus a duplicate-action guard instead of native disabling.",
    "Reviewed controls use native wrapping labels and native required, pattern, length, and range validation.",
    "Successful login, logout, student creation and lesson opening explicitly assign a destination focus.",
    "The manual playback-position explanation is associated with its numeric input.",
    "Username format guidance is visible and programmatically associated.",
    "Visible 8–128-character password instructions are associated with login, guardian registration, and student creation inputs."
  ],
  "notes": [
    {
      "skill": "forms-specialist",
      "note": "Re-review of current source after remediation; both previously reported moderate findings are resolved."
    },
    {
      "skill": "forms-specialist",
      "note": "Static form review only; no screen-reader or browser execution was performed by this specialist."
    },
    {
      "skill": "forms-specialist",
      "note": "No critical or serious forms findings remain within the reviewed phase-1 scope."
    },
    {
      "skill": "keyboard-navigator",
      "note": "The two initial source-review findings KEYBOARD-ASYNC-FOCUS and KEYBOARD-RESTORE-FOCUS were corrected in the reviewed revision."
    },
    {
      "skill": "keyboard-navigator",
      "note": "This is a source re-review with an isolated Chromium helper probe, not a full extension or screen-reader audit."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Actual side-panel focus transfer and VoiceOver/NVDA end-to-end verification remain necessary."
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
  "checks": 16,
  "generated": "2026-11-12",
  "template": "web"
}
```
