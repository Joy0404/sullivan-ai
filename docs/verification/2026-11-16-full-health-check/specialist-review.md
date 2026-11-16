# Web Accessibility Audit

An audit of web content, run on 2026-11-16. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-16 |
| Scope | 4 items |
| Skills run | accessibility-lead |
| Tooling | node v24.22.1, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 10 |

Audited:

- `apps/api/app/local_access.py`
- `apps/api/app/student_notes.py`
- `apps/extensions/student/notes.js`
- `apps/extensions/student/workspace.html`

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
| Fixed | 10 |
| New | 0 |
| Persistent | 0 |
| Regressed | 0 |

Score moved from 36 to 100.

## What passed

4 checks ran and found nothing.

- API 360 passed, 4 optional database tests skipped.
- All recorded findings repaired with deterministic regression coverage.
- Reader output visibility, accessibility-tree text, keyboard and focus tested in installed Chromium extensions.
- Seven isolated legacy web browser suites passed.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **accessibility-lead**: Full extension acceptance is reported separately.
- **accessibility-lead**: Actual VoiceOver/NVDA, native speech quality, live Gemini and external lecture sites remain unverified.
- **accessibility-lead**: A score in this generated scoped report is not a claim of whole-product accessibility conformance.

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
    "accessibility-lead"
  ],
  "scope": [
    "apps/api/app/local_access.py",
    "apps/api/app/student_notes.py",
    "apps/extensions/student/notes.js",
    "apps/extensions/student/workspace.html"
  ],
  "findings": [],
  "passed": [
    "API 360 passed, 4 optional database tests skipped.",
    "All recorded findings repaired with deterministic regression coverage.",
    "Reader output visibility, accessibility-tree text, keyboard and focus tested in installed Chromium extensions.",
    "Seven isolated legacy web browser suites passed."
  ],
  "notes": [
    {
      "skill": "accessibility-lead",
      "note": "Full extension acceptance is reported separately."
    },
    {
      "skill": "accessibility-lead",
      "note": "Actual VoiceOver/NVDA, native speech quality, live Gemini and external lecture sites remain unverified."
    },
    {
      "skill": "accessibility-lead",
      "note": "A score in this generated scoped report is not a claim of whole-product accessibility conformance."
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
  "generated": "2026-11-16",
  "template": "web"
}
```
