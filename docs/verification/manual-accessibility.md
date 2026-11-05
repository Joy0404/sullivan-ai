# Web Accessibility Audit

An audit of web content, run on 2026-11-05. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-05 |
| Scope | 1 item |
| Skills run | alt-text-headings, aria-specialist |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 17 |

Audited:

- `apps/web/manual/index.html`

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

- ARIA specialist: all aria-labelledby, aria-describedby, aria-controls, and fragment references resolve; static implementation-status text does not use unnecessary live semantics.
- ARIA specialist: native header, navigation, main, footer, button, and details semantics are exposed correctly in Chrome AX; no redundant interactive roles or custom controls found.
- Applied both contrast-master and alt-text-headings to the current manual only.
- Body and table text compute to 18px; 390px screenshots of guardian and keyboard tables show readable wrapped columns without clipped content.
- Five semantic tables have captions and explicit col/row header scope; all table-of-contents targets resolve.
- Fresh Chrome runtime at 320/390/1280: no measured horizontal overflow, text contrast failures or invisible/low-contrast keyboard focus indicators.
- Fresh closed-state regression check: all six answers become visible before printing and all six disclosures return to closed afterward.
- Keyboard navigator: activating the TOC trouble anchor scrolls to that chapter; the following Tab reaches its first summary, preserving destination navigation.
- Keyboard navigator: all six details summaries open with Enter, close with Space, retain focus, and show a4px focus outline.
- Keyboard navigator: the first Tab reveals the skip link with a4px focus outline; Enter focuses main#content. Verified at1280px and390px.
- Keyboard navigator: the visible native type=button print control has accessible name 인쇄·PDF 저장; both Enter and Space invoke its print handler.
- Listeners are registered on window beforeprint/afterprint; the fix covers browser printing as well as the window.print() button.
- MANUAL-PRINT-DISCLOSURES resolved: beforeprint opens all six native disclosures and exposes every answer in Chrome print media.
- Mixed state regression check: two initially open and four initially closed disclosures return to their exact original states after afterprint.
- No positive tabindex values, broken anchors, custom keyboard traps, or browser page errors were found; mobile viewport had no horizontal overflow.
- One h1 with orderly h2/h3 sections, lang=ko, descriptive page title, one main, labeled navigation and a skip-to-content link.
- Print CSS hides page actions/navigation, uses black text with 11pt body and 10pt tables, defines A4 margins, and applies heading/table-row break rules.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **aria-specialist**: Combined aria-specialist and keyboard-navigator targeted read-only review, as dispatched by accessibility-lead.
- **aria-specialist**: Evidence: /tmp/sullivan-manual-a11y/results.json and /tmp/sullivan-manual-a11y/audit.cjs. Public port8770 manual only; no actual account, login, or database access.
- **aria-specialist**: Actual VoiceOver/NVDA unavailable. DOM, keyboard interaction, computed focus styling, and Chrome AX were checked.
- **aria-specialist**: window.print was temporarily replaced inside the disposable browser page to count native button activation; no system print dialog or PDF output was audited.
- **alt-text-headings**: Narrow recheck of the prior print-disclosures finding only; no broad re-audit or product edits.
- **alt-text-headings**: Independent event/visibility evidence: /tmp/manual-review/print-recheck.json. Actual browser PDF generation is being verified separately by the parent.

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
    "alt-text-headings",
    "aria-specialist"
  ],
  "scope": [
    "apps/web/manual/index.html"
  ],
  "findings": [],
  "passed": [
    "ARIA specialist: all aria-labelledby, aria-describedby, aria-controls, and fragment references resolve; static implementation-status text does not use unnecessary live semantics.",
    "ARIA specialist: native header, navigation, main, footer, button, and details semantics are exposed correctly in Chrome AX; no redundant interactive roles or custom controls found.",
    "Applied both contrast-master and alt-text-headings to the current manual only.",
    "Body and table text compute to 18px; 390px screenshots of guardian and keyboard tables show readable wrapped columns without clipped content.",
    "Five semantic tables have captions and explicit col/row header scope; all table-of-contents targets resolve.",
    "Fresh Chrome runtime at 320/390/1280: no measured horizontal overflow, text contrast failures or invisible/low-contrast keyboard focus indicators.",
    "Fresh closed-state regression check: all six answers become visible before printing and all six disclosures return to closed afterward.",
    "Keyboard navigator: activating the TOC trouble anchor scrolls to that chapter; the following Tab reaches its first summary, preserving destination navigation.",
    "Keyboard navigator: all six details summaries open with Enter, close with Space, retain focus, and show a4px focus outline.",
    "Keyboard navigator: the first Tab reveals the skip link with a4px focus outline; Enter focuses main#content. Verified at1280px and390px.",
    "Keyboard navigator: the visible native type=button print control has accessible name 인쇄·PDF 저장; both Enter and Space invoke its print handler.",
    "Listeners are registered on window beforeprint/afterprint; the fix covers browser printing as well as the window.print() button.",
    "MANUAL-PRINT-DISCLOSURES resolved: beforeprint opens all six native disclosures and exposes every answer in Chrome print media.",
    "Mixed state regression check: two initially open and four initially closed disclosures return to their exact original states after afterprint.",
    "No positive tabindex values, broken anchors, custom keyboard traps, or browser page errors were found; mobile viewport had no horizontal overflow.",
    "One h1 with orderly h2/h3 sections, lang=ko, descriptive page title, one main, labeled navigation and a skip-to-content link.",
    "Print CSS hides page actions/navigation, uses black text with 11pt body and 10pt tables, defines A4 margins, and applies heading/table-row break rules."
  ],
  "notes": [
    {
      "skill": "aria-specialist",
      "note": "Combined aria-specialist and keyboard-navigator targeted read-only review, as dispatched by accessibility-lead."
    },
    {
      "skill": "aria-specialist",
      "note": "Evidence: /tmp/sullivan-manual-a11y/results.json and /tmp/sullivan-manual-a11y/audit.cjs. Public port8770 manual only; no actual account, login, or database access."
    },
    {
      "skill": "aria-specialist",
      "note": "Actual VoiceOver/NVDA unavailable. DOM, keyboard interaction, computed focus styling, and Chrome AX were checked."
    },
    {
      "skill": "aria-specialist",
      "note": "window.print was temporarily replaced inside the disposable browser page to count native button activation; no system print dialog or PDF output was audited."
    },
    {
      "skill": "alt-text-headings",
      "note": "Narrow recheck of the prior print-disclosures finding only; no broad re-audit or product edits."
    },
    {
      "skill": "alt-text-headings",
      "note": "Independent event/visibility evidence: /tmp/manual-review/print-recheck.json. Actual browser PDF generation is being verified separately by the parent."
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
  "generated": "2026-11-05",
  "template": "web"
}
```
