# Web Accessibility Audit

An audit of web content, run on 2026-11-04. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-04 |
| Scope | 5 items |
| Skills run | alt-text-headings, aria-specialist, contrast-master, keyboard-navigator |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 18 |

Audited:

- `apps/web/intro.css`
- `apps/web/intro.css:75`
- `apps/web/intro/index.html`
- `apps/web/intro/index.html:33`
- `apps/web/intro/index.html:94`

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

18 checks ran and found nothing.

- All eight links retain native anchor semantics and /guide/#step-7 destinations.
- All eight native activity links were reached by actual Tab navigation at 320px, 390px and 1280px widths (24 focus checks).
- At 320/390/1280 all 24 measured title/body pairs share exactly the same 24px left inset; no clipped or overflowing preview content.
- At 320/390/1280 all eight links retain 20px titles, 18px descriptions and heights above 104px.
- At intro/index.html:33 and :94 both captions explicitly call these activity-composition guides and explain that selection opens the guide; no claim that the replacements are actual screenshots.
- Both replacement previews use native figure/list/link/strong/span HTML rather than screenshots; four links have functional labels and valid /guide/#step-7 destinations.
- Enter activated each of the eight links and navigated to /guide/#step-7 with the corresponding disclosure expanded.
- Every activity label had the common 24px left inset. Text-range geometry and scroll widths showed no clipped labels or horizontal overflow at all three widths.
- Every focused activity link matched :focus-visible with a solid 4px outline and -6px inset, keeping the indicator inside the rounded overflow container.
- Final markup removes aria-label from all eight activity links; each Chrome AX native link name includes its complete visible activity title and hint.
- Keyboard focus stays inside each link with a visible 4px outline and -6px offset; white-on-brand focus contrast is 8.70:1, brown #8c4700 on white is 6.96:1.
- Measured white text on brand #164b8b is 8.70:1; ink text on white is 14.09:1.
- No page or preview horizontal overflow at 320/390/1280.
- Replacement preserves the page’s existing h1→h2→h3 hierarchy; remaining three real screenshots retain meaningful alt text and sample qualification.
- The two figure captions explicitly identify an activity overview and explain that each item opens the guide.
- The two previews retain native figure/figcaption and ul/li semantics with captions identifying activity composition guidance; no false interactive activity controls.
- Visual inspection of the 320px first-item and 390px last-item focus captures confirmed visible outlines and readable, unclipped labels.
- Visually inspected focused primary/secondary hero rows at 390px: outlines are not clipped by the rounded list, and text remains clear of the inset ring.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **aria-specialist**: This final payload supersedes the earlier claim that link names contain 사용법 보기; final names derive from the full visible title and hint.
- **aria-specialist**: Targeted read-only public-port8770 DOM/AX recheck; no auth, database, provider, or product edits.
- **aria-specialist**: Actual assistive technology unavailable. Evidence: /tmp/sullivan-intro-alignment/final-aria-results.json.
- **keyboard-navigator**: Verdict: no reproducible keyboard or label-clipping defect found in the targeted intro alignment working diff. No broader audit performed.
- **keyboard-navigator**: Evidence: /tmp/intro-alignment-keyboard/results.json; script: /tmp/intro-alignment-keyboard/check.cjs; focus screenshots: /tmp/intro-alignment-keyboard/focus-{320,390,1280}-{0,3,4,7}.png.
- **keyboard-navigator**: Chrome/156.0.8078.80 with Puppeteer, viewport height 900px. Used the existing public server on port 8770; only public intro/guide assets were requested. Auth/API paths and external traffic were blocked; none were attempted. No account database access or product edits.
- **alt-text-headings**: Targeted review of current working diff only; no product edits. Evidence: /tmp/intro-alignment/evidence.json, hero-focus-390.png and secondary-focus-390.png. Chrome 156.0.8078.80; public page on port 8770; external requests blocked.
- **contrast-master**: Targeted review of current working diff only; no product edits. Evidence: /tmp/intro-alignment/evidence.json, hero-focus-390.png and secondary-focus-390.png. Chrome 156.0.8078.80; public page on port 8770; external requests blocked.

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
    "aria-specialist",
    "contrast-master",
    "keyboard-navigator"
  ],
  "scope": [
    "apps/web/intro.css",
    "apps/web/intro.css:75",
    "apps/web/intro/index.html",
    "apps/web/intro/index.html:33",
    "apps/web/intro/index.html:94"
  ],
  "findings": [],
  "passed": [
    "All eight links retain native anchor semantics and /guide/#step-7 destinations.",
    "All eight native activity links were reached by actual Tab navigation at 320px, 390px and 1280px widths (24 focus checks).",
    "At 320/390/1280 all 24 measured title/body pairs share exactly the same 24px left inset; no clipped or overflowing preview content.",
    "At 320/390/1280 all eight links retain 20px titles, 18px descriptions and heights above 104px.",
    "At intro/index.html:33 and :94 both captions explicitly call these activity-composition guides and explain that selection opens the guide; no claim that the replacements are actual screenshots.",
    "Both replacement previews use native figure/list/link/strong/span HTML rather than screenshots; four links have functional labels and valid /guide/#step-7 destinations.",
    "Enter activated each of the eight links and navigated to /guide/#step-7 with the corresponding disclosure expanded.",
    "Every activity label had the common 24px left inset. Text-range geometry and scroll widths showed no clipped labels or horizontal overflow at all three widths.",
    "Every focused activity link matched :focus-visible with a solid 4px outline and -6px inset, keeping the indicator inside the rounded overflow container.",
    "Final markup removes aria-label from all eight activity links; each Chrome AX native link name includes its complete visible activity title and hint.",
    "Keyboard focus stays inside each link with a visible 4px outline and -6px offset; white-on-brand focus contrast is 8.70:1, brown #8c4700 on white is 6.96:1.",
    "Measured white text on brand #164b8b is 8.70:1; ink text on white is 14.09:1.",
    "No page or preview horizontal overflow at 320/390/1280.",
    "Replacement preserves the page’s existing h1→h2→h3 hierarchy; remaining three real screenshots retain meaningful alt text and sample qualification.",
    "The two figure captions explicitly identify an activity overview and explain that each item opens the guide.",
    "The two previews retain native figure/figcaption and ul/li semantics with captions identifying activity composition guidance; no false interactive activity controls.",
    "Visual inspection of the 320px first-item and 390px last-item focus captures confirmed visible outlines and readable, unclipped labels.",
    "Visually inspected focused primary/secondary hero rows at 390px: outlines are not clipped by the rounded list, and text remains clear of the inset ring."
  ],
  "notes": [
    {
      "skill": "aria-specialist",
      "note": "This final payload supersedes the earlier claim that link names contain 사용법 보기; final names derive from the full visible title and hint."
    },
    {
      "skill": "aria-specialist",
      "note": "Targeted read-only public-port8770 DOM/AX recheck; no auth, database, provider, or product edits."
    },
    {
      "skill": "aria-specialist",
      "note": "Actual assistive technology unavailable. Evidence: /tmp/sullivan-intro-alignment/final-aria-results.json."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Verdict: no reproducible keyboard or label-clipping defect found in the targeted intro alignment working diff. No broader audit performed."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Evidence: /tmp/intro-alignment-keyboard/results.json; script: /tmp/intro-alignment-keyboard/check.cjs; focus screenshots: /tmp/intro-alignment-keyboard/focus-{320,390,1280}-{0,3,4,7}.png."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Chrome/156.0.8078.80 with Puppeteer, viewport height 900px. Used the existing public server on port 8770; only public intro/guide assets were requested. Auth/API paths and external traffic were blocked; none were attempted. No account database access or product edits."
    },
    {
      "skill": "alt-text-headings",
      "note": "Targeted review of current working diff only; no product edits. Evidence: /tmp/intro-alignment/evidence.json, hero-focus-390.png and secondary-focus-390.png. Chrome 156.0.8078.80; public page on port 8770; external requests blocked."
    },
    {
      "skill": "contrast-master",
      "note": "Targeted review of current working diff only; no product edits. Evidence: /tmp/intro-alignment/evidence.json, hero-focus-390.png and secondary-focus-390.png. Chrome 156.0.8078.80; public page on port 8770; external requests blocked."
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
  "checks": 18,
  "generated": "2026-11-04",
  "template": "web"
}
```
