# Web Accessibility Audit

An audit of web content, run on 2026-11-12. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-12 |
| Scope | 10 items |
| Skills run | forms-specialist, keyboard-navigator, live-region-controller |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 17 |

Audited:

- `apps/api/app/extension_accounts.py`
- `apps/extensions/guardian/app.js`
- `apps/extensions/guardian/workspace.html`
- `apps/extensions/shared/accounts.html`
- `apps/extensions/shared/accounts.js`
- `apps/extensions/shared/client.js`
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

17 checks ran and found nothing.

- Current generated login heading is programmatically focusable and the remember-login label identifies its browser-login scope.
- Device removal moves focus to the account heading; logout and session expiry restore focus to a visible login control.
- Generated pages include persistent role=status and role=alert containers before requests complete; status helper updates textContent.
- Guardian and student unlink execution buttons reference their visible consequence questions; cancellation controls are present.
- Guardian pairing code is readonly, selectable and associated with expiry and single-use instructions.
- Inline logout-all confirmation moves focus to confirmation and cancel restores the originating button.
- Manual student connection refresh reports completion; pairing and unlink success report completion.
- Pairing preview is exposed through focus on its heading rather than making the code/details a verbose live region.
- Pairing preview moves focus to its heading; pairing success and student/guardian unlink move focus before awaiting list refresh, preserving it if refresh fails.
- Phase-4 controls use native buttons, inputs, details/summary and forms; no positive tabindex or custom keyboard trap was found.
- Rechecked student pairing consent: both the required checkbox and submission button now reference the visible guardian identity and sharing scope through aria-describedby="pair-guardian pair-sharing".
- Recovery-code output uses a labelled readonly textarea with explicit download and clear actions; raw codes are not placed in live-region announcements.
- Reviewed phase-4 native control labels, autocomplete tokens, visible password limits, paste-compatible password/recovery inputs and preserved hosted-login username on authentication failure.
- Signup and recovery-code regeneration move focus to the newly revealed recovery heading; clearing the codes focuses the visible login/account heading.
- Signup, password recovery, code download, device refresh/removal, logout-all and login/logout have concise status or error feedback.
- Skip link targets a focusable main landmark; generated login and account headings support programmatic focus.
- Task helper preserves focus and marks busy controls with aria-busy and aria-disabled; routine success uses polite status and failures use alert.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **forms-specialist**: Source review only; no assistive-technology session or browser flow was executed by this specialist. Final current-state review on 2026-11-12 confirms FORM-PAIR-CONSENT-CONTEXT is resolved.
- **keyboard-navigator**: Static source review of the current phase-4 implementation; browser and assistive-technology behavior were not executed by this specialist.
- **keyboard-navigator**: Earlier review findings concerning the login focus target and async pairing/unlink focus ordering were corrected before this final reread.
- **live-region-controller**: Static source review only; announcements were not listened to with a screen reader.
- **live-region-controller**: No delayed-network timing measurement was performed; aria-busy is present on the initiating control.
- **live-region-controller**: The missing manual connection-refresh completion announcement was corrected before this final reread.

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
    "apps/api/app/extension_accounts.py",
    "apps/extensions/guardian/app.js",
    "apps/extensions/guardian/workspace.html",
    "apps/extensions/shared/accounts.html",
    "apps/extensions/shared/accounts.js",
    "apps/extensions/shared/client.js",
    "apps/extensions/shared/ui.js",
    "apps/extensions/student/app.js",
    "apps/extensions/student/workspace.html",
    "scripts/build_extensions.py"
  ],
  "findings": [],
  "passed": [
    "Current generated login heading is programmatically focusable and the remember-login label identifies its browser-login scope.",
    "Device removal moves focus to the account heading; logout and session expiry restore focus to a visible login control.",
    "Generated pages include persistent role=status and role=alert containers before requests complete; status helper updates textContent.",
    "Guardian and student unlink execution buttons reference their visible consequence questions; cancellation controls are present.",
    "Guardian pairing code is readonly, selectable and associated with expiry and single-use instructions.",
    "Inline logout-all confirmation moves focus to confirmation and cancel restores the originating button.",
    "Manual student connection refresh reports completion; pairing and unlink success report completion.",
    "Pairing preview is exposed through focus on its heading rather than making the code/details a verbose live region.",
    "Pairing preview moves focus to its heading; pairing success and student/guardian unlink move focus before awaiting list refresh, preserving it if refresh fails.",
    "Phase-4 controls use native buttons, inputs, details/summary and forms; no positive tabindex or custom keyboard trap was found.",
    "Rechecked student pairing consent: both the required checkbox and submission button now reference the visible guardian identity and sharing scope through aria-describedby=\"pair-guardian pair-sharing\".",
    "Recovery-code output uses a labelled readonly textarea with explicit download and clear actions; raw codes are not placed in live-region announcements.",
    "Reviewed phase-4 native control labels, autocomplete tokens, visible password limits, paste-compatible password/recovery inputs and preserved hosted-login username on authentication failure.",
    "Signup and recovery-code regeneration move focus to the newly revealed recovery heading; clearing the codes focuses the visible login/account heading.",
    "Signup, password recovery, code download, device refresh/removal, logout-all and login/logout have concise status or error feedback.",
    "Skip link targets a focusable main landmark; generated login and account headings support programmatic focus.",
    "Task helper preserves focus and marks busy controls with aria-busy and aria-disabled; routine success uses polite status and failures use alert."
  ],
  "notes": [
    {
      "skill": "forms-specialist",
      "note": "Source review only; no assistive-technology session or browser flow was executed by this specialist. Final current-state review on 2026-11-12 confirms FORM-PAIR-CONSENT-CONTEXT is resolved."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Static source review of the current phase-4 implementation; browser and assistive-technology behavior were not executed by this specialist."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Earlier review findings concerning the login focus target and async pairing/unlink focus ordering were corrected before this final reread."
    },
    {
      "skill": "live-region-controller",
      "note": "Static source review only; announcements were not listened to with a screen reader."
    },
    {
      "skill": "live-region-controller",
      "note": "No delayed-network timing measurement was performed; aria-busy is present on the initiating control."
    },
    {
      "skill": "live-region-controller",
      "note": "The missing manual connection-refresh completion announcement was corrected before this final reread."
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
  "checks": 17,
  "generated": "2026-11-12",
  "template": "web"
}
```
