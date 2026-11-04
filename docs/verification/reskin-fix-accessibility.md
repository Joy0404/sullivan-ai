# Web Accessibility Audit

An audit of web content, run on 2026-11-04. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-04 |
| Scope | 4 items |
| Skills run | forms-specialist, live-region-controller |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 10 |

Audited:

- `apps/web/role-portal.js:198-225`
- `apps/web/role-portal.js:342`
- `apps/web/role-portal.js:383`
- `scripts/verify_roles_browser.py:81`

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

10 checks ran and found nothing.

- Chrome accessibility tree retained polite atomic role=status semantics and exposed each student name in the status text.
- Closed LIVE-PROGRESS-STUDENT-CONTEXT: all three concurrent loading messages included their corresponding student name.
- Focused browser interception confirmed the submitted /video-link URL and analysis consent match the visible link source and review. The request was intercepted before any provider call.
- Observed exactly six status text mutations: one loading and one completion per disclosure, with no page errors.
- P1 FORMS-WIZARD-RESET-SOURCE closed: a link plus supplemental TXT remains link mode after home/reopen; URL and consent remain visible, and step-3 review includes the retained URL.
- Returned empty results, HTTP500, and populated results to three simultaneously open disclosures while focus remained on #guardian-prepare; each completion message identified its corresponding student.
- Reviewed durable regression in scripts/verify_roles_browser.py: link plus TXT → home/reopen → visible URL/consent → review/FormData agreement → file switch with URL/consent clearing.
- Switching from file to link clears the inactive video input. Source-change handlers completed without recursion or browser errors in the focused scenario.
- Switching to file/material mode clears video_url, unchecks and disables text-only analysis consent, omits that consent from FormData, and rebuilds the visible review as 학습자료만 준비 / 동의하지 않음.
- The P1 fix preserves form names, API request structure, authentication and provider settings.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **forms-specialist**: Read-only recheck of the current working diff on 2026-11-05. No product or test edits made by this review.
- **forms-specialist**: Runtime: Chrome/156.0.8078.80 with Puppeteer against fresh disposable TemporaryDirectory account/usage databases on port 8892. Provider configuration removed; external requests blocked. Configured health was browser-mocked only for payload capture, and /video-link was intercepted with HTTP400.
- **forms-specialist**: Proof: /tmp/final-wizard-fix-recheck-results.json; focused script: /tmp/final-wizard-fix-recheck.cjs. The full durable browser script was reviewed here, not rerun in this focused recheck.
- **forms-specialist**: P1-only scope: previously documented baseline cancellation, username-format-help and reset-label issues were not reclassified or expanded.
- **live-region-controller**: Targeted read-only recheck of the current working diff; no broader scan or product edits.
- **live-region-controller**: Evidence: /tmp/sullivan-aria-recheck-results.json. Used fresh disposable SQLite accounts on port 8893, mocked playback, and blocked external requests.
- **live-region-controller**: Verification covers DOM, focus, and Chrome accessibility-tree output; no VoiceOver or NVDA speech session was run.

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
    "live-region-controller"
  ],
  "scope": [
    "apps/web/role-portal.js:198-225",
    "apps/web/role-portal.js:342",
    "apps/web/role-portal.js:383",
    "scripts/verify_roles_browser.py:81"
  ],
  "findings": [],
  "passed": [
    "Chrome accessibility tree retained polite atomic role=status semantics and exposed each student name in the status text.",
    "Closed LIVE-PROGRESS-STUDENT-CONTEXT: all three concurrent loading messages included their corresponding student name.",
    "Focused browser interception confirmed the submitted /video-link URL and analysis consent match the visible link source and review. The request was intercepted before any provider call.",
    "Observed exactly six status text mutations: one loading and one completion per disclosure, with no page errors.",
    "P1 FORMS-WIZARD-RESET-SOURCE closed: a link plus supplemental TXT remains link mode after home/reopen; URL and consent remain visible, and step-3 review includes the retained URL.",
    "Returned empty results, HTTP500, and populated results to three simultaneously open disclosures while focus remained on #guardian-prepare; each completion message identified its corresponding student.",
    "Reviewed durable regression in scripts/verify_roles_browser.py: link plus TXT → home/reopen → visible URL/consent → review/FormData agreement → file switch with URL/consent clearing.",
    "Switching from file to link clears the inactive video input. Source-change handlers completed without recursion or browser errors in the focused scenario.",
    "Switching to file/material mode clears video_url, unchecks and disables text-only analysis consent, omits that consent from FormData, and rebuilds the visible review as 학습자료만 준비 / 동의하지 않음.",
    "The P1 fix preserves form names, API request structure, authentication and provider settings."
  ],
  "notes": [
    {
      "skill": "forms-specialist",
      "note": "Read-only recheck of the current working diff on 2026-11-05. No product or test edits made by this review."
    },
    {
      "skill": "forms-specialist",
      "note": "Runtime: Chrome/156.0.8078.80 with Puppeteer against fresh disposable TemporaryDirectory account/usage databases on port 8892. Provider configuration removed; external requests blocked. Configured health was browser-mocked only for payload capture, and /video-link was intercepted with HTTP400."
    },
    {
      "skill": "forms-specialist",
      "note": "Proof: /tmp/final-wizard-fix-recheck-results.json; focused script: /tmp/final-wizard-fix-recheck.cjs. The full durable browser script was reviewed here, not rerun in this focused recheck."
    },
    {
      "skill": "forms-specialist",
      "note": "P1-only scope: previously documented baseline cancellation, username-format-help and reset-label issues were not reclassified or expanded."
    },
    {
      "skill": "live-region-controller",
      "note": "Targeted read-only recheck of the current working diff; no broader scan or product edits."
    },
    {
      "skill": "live-region-controller",
      "note": "Evidence: /tmp/sullivan-aria-recheck-results.json. Used fresh disposable SQLite accounts on port 8893, mocked playback, and blocked external requests."
    },
    {
      "skill": "live-region-controller",
      "note": "Verification covers DOM, focus, and Chrome accessibility-tree output; no VoiceOver or NVDA speech session was run."
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
  "generated": "2026-11-04",
  "template": "web"
}
```
