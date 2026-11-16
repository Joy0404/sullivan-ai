# Web Accessibility Audit

An audit of web content, run on 2026-11-16. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-16 |
| Scope | 6 items |
| Skills run | python-specialist |
| Tooling | node v24.22.1, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 10 |

Audited:

- `apps/api/app/adapters/gemini_agent.py`
- `apps/api/app/adapters/video_link.py`
- `apps/api/app/core/question_evidence.py`
- `apps/api/app/core/token_comparison.py`
- `apps/api/app/core/verification_plan.py`
- `scripts/measure_gemini_tokens.py`

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
| Fixed | 4 |
| New | 0 |
| Persistent | 0 |
| Regressed | 0 |

Score moved from 66 to 100.

## What passed

3 checks ran and found nothing.

- 351 API tests passed; 4 optional external-database tests skipped.
- 67 targeted provider-boundary and comparison tests passed.
- All four specialist findings repaired and covered by regression tests.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **python-specialist**: Scoped Python safety review; not a WCAG conformance or real model quality claim.
- **python-specialist**: Real provider measurements, screen-reader audio and hearing remain unverified.

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
    "python-specialist"
  ],
  "scope": [
    "apps/api/app/adapters/gemini_agent.py",
    "apps/api/app/adapters/video_link.py",
    "apps/api/app/core/question_evidence.py",
    "apps/api/app/core/token_comparison.py",
    "apps/api/app/core/verification_plan.py",
    "scripts/measure_gemini_tokens.py"
  ],
  "findings": [],
  "passed": [
    "351 API tests passed; 4 optional external-database tests skipped.",
    "67 targeted provider-boundary and comparison tests passed.",
    "All four specialist findings repaired and covered by regression tests."
  ],
  "notes": [
    {
      "skill": "python-specialist",
      "note": "Scoped Python safety review; not a WCAG conformance or real model quality claim."
    },
    {
      "skill": "python-specialist",
      "note": "Real provider measurements, screen-reader audio and hearing remain unverified."
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
