# Web Accessibility Audit

An audit of web content, run on 2026-11-14. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-14 |
| Scope | 4 items |
| Skills run | keyboard-navigator |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 10 |

Audited:

- `apps/extensions/guardian/app.js`
- `apps/extensions/student/app.js`
- `docs/verification/2026-11-15-races/round1/results.json`
- `scripts/verify_extension_races.py`

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

7 checks ran and found nothing.

- Guardian edit-save completion does not remount the edit form, preserving new title, subject, checkbox values and current input focus.
- Guardian latest-request guards prevent an older list/poll response from replacing newer state.
- Guardian withdrawal only remounts an unchanged editor; form input and focus events advance editRevision so newer edits remain intact.
- Guardian withdrawal snapshots its original lecture and student IDs before awaiting the request.
- Preserved round1 results show RACE01–RACE05 passed, including title focus preservation and pending student position input; checked screens have axe violations 0.
- Student saveProgress no longer follows the seek save with a second save, so later position input remains pending.
- Student seek retains the field value when the position edit revision changes, and save success distinguishes pending newer input.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **keyboard-navigator**: Final review found no remaining keyboard/input preservation defect in the requested paths; no source files edited.
- **keyboard-navigator**: This review inspected source and the parent-produced round1 result; no independent runtime or VoiceOver/NVDA audio test was performed.
- **keyboard-navigator**: Checkbox preservation is supported by source inspection; round1 runtime assertions focus on title inputs, not checkbox changes.
- **keyboard-navigator**: RACE02 observed.writes references the live list and later contains a second explicitly submitted write; copy the list when recording if a point-in-time observation is intended. This is report evidence hygiene, not a product failure.

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
    "apps/extensions/guardian/app.js",
    "apps/extensions/student/app.js",
    "docs/verification/2026-11-15-races/round1/results.json",
    "scripts/verify_extension_races.py"
  ],
  "findings": [],
  "passed": [
    "Guardian edit-save completion does not remount the edit form, preserving new title, subject, checkbox values and current input focus.",
    "Guardian latest-request guards prevent an older list/poll response from replacing newer state.",
    "Guardian withdrawal only remounts an unchanged editor; form input and focus events advance editRevision so newer edits remain intact.",
    "Guardian withdrawal snapshots its original lecture and student IDs before awaiting the request.",
    "Preserved round1 results show RACE01–RACE05 passed, including title focus preservation and pending student position input; checked screens have axe violations 0.",
    "Student saveProgress no longer follows the seek save with a second save, so later position input remains pending.",
    "Student seek retains the field value when the position edit revision changes, and save success distinguishes pending newer input."
  ],
  "notes": [
    {
      "skill": "keyboard-navigator",
      "note": "Final review found no remaining keyboard/input preservation defect in the requested paths; no source files edited."
    },
    {
      "skill": "keyboard-navigator",
      "note": "This review inspected source and the parent-produced round1 result; no independent runtime or VoiceOver/NVDA audio test was performed."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Checkbox preservation is supported by source inspection; round1 runtime assertions focus on title inputs, not checkbox changes."
    },
    {
      "skill": "keyboard-navigator",
      "note": "RACE02 observed.writes references the live list and later contains a second explicitly submitted write; copy the list when recording if a point-in-time observation is intended. This is report evidence hygiene, not a product failure."
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
  "checks": 10,
  "generated": "2026-11-14",
  "template": "web"
}
```
