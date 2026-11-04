# Web Accessibility Audit

An audit of web content, run on 2026-11-04. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-04 |
| Scope | 10 items |
| Skills run | alt-text-headings, aria-specialist, contrast-master, keyboard-navigator, live-region-controller |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 37 |

Audited:

- `apps/web/guide/guide.js`
- `apps/web/guide/index.html`
- `apps/web/intro.css`
- `apps/web/intro/img/*.png`
- `apps/web/intro/index.html`
- `apps/web/tokens.css`
- `http://127.0.0.1:8871/guide/`
- `http://127.0.0.1:8871/intro/`
- `http://127.0.0.1:8873/guide/`
- `http://127.0.0.1:8873/intro/`

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

37 checks ran and found nothing.

- All four decorative inline SVG icons are hidden with aria-hidden=true; their meaning is supplied by adjacent headings and prose.
- Calculated WCAG sRGB contrasts for all text/focus/control tokens against used paper, canvas, brand-soft and amber-soft backgrounds; body/muted/brand text pairs exceed 4.5:1, focus pairs exceed 3:1, functional control-border pairs exceed 3:1.
- Chrome accessibility tree: 8 named per-step buttons and one named expand-all button expose expanded state.
- Chrome accessibility tree: a status node exposes polite live behavior.
- Chrome forced-colors emulation supplied system foreground/background/border and Highlight outline; source uses declared system tokens.
- Chrome runtime and code inspection: individual accordion disclosure uses focused button aria-expanded; deep links open the selected panel and move focus to its toggle, avoiding duplicate speech from extra live messages.
- Chrome runtime inspection at 1280px and 390px found actual text/background pairs matching the reviewed token combinations; body text is 18px.
- Chrome runtime with MutationObserver: expand-all and collapse-all produce one concise Korean text update each (8개 단계를 모두 펼쳤습니다./8개 단계를 모두 접었습니다.).
- Chrome runtime: FAQ native details toggles with Enter/Space.
- Chrome runtime: JavaScript disabled leaves all eight guide panels readable and enhancement-only expand-all control hidden.
- Chrome runtime: all aria-controls/labelledby/describedby references resolve in both routes.
- Chrome runtime: hashchange opens selected step and focuses its toggle; same-hash activation reopens a collapsed selected step; initial hash opens requested step.
- Chrome runtime: per-step Enter/Space and expand-all Enter/Space keep aria-expanded synchronized with panel hidden state.
- Chrome runtime: the status node is not display:none or visibility:hidden; clipped sr-only styling retains accessibility exposure.
- Code and Chrome runtime: one initially empty guide-status role=status live region is present before any user action, with aria-atomic=true.
- Code inspection: decorative SVG icons and visual expand/collapse helper words are aria-hidden, while the step number remains in the accessible button label.
- Code inspection: initial page load does not populate an announcement; per-step initial visibility is conveyed through native content/expanded states.
- Code inspection: textContent updates the persistent status node, with no assertive region, timer, streaming transcript, or parallel live announcement.
- Control circle border #6f87a3 has 3.70:1 against white, with dark numbered text carrying the step information independently.
- Each page has one h1, a logical h1→h2→h3 outline, one main landmark, descriptive unique Korean page title, lang=ko, a working target for the skip link, and page-level header/footer.
- Guide navigation landmarks have distinct names: 주 메뉴 and 가이드 단계.
- Guide screenshots supplement full textual action instructions; image links explicitly identify the numbered step and original-size action.
- Native anchors/buttons/details-summary are used for links, accordion controls, and FAQ disclosure; no redundant implicit roles.
- No animation, flashing, autoplay or color-only state mechanism exists on the two public pages; reduced-motion and forced-colors fallbacks are provided.
- Outline focus color #8c4700 has at least 6.06:1 contrast against the reviewed light backgrounds; focus-visible uses instant 4px outlines with 4px offset.
- Primary text white/brand is 8.70:1; primary hover white/ink is 14.09:1; actual active-without-hover state retained white/brand at 8.70:1 on both routes at both widths.
- Runtime Chrome inspection at 320, 390, 640 and 1280 CSS-pixel widths, with guide fully expanded, found no text/control elements extending beyond the viewport and document scrollWidth equalled viewport width.
- Runtime Chrome with JavaScript disabled: all eight guide sections remain visible, the inactive expand-all control remains hidden, and the skip link focuses main.
- Runtime Chrome, widths 320/390/1280: all-expanded intro FAQ and guide states support full forward Tab and backward Shift+Tab traversal with no hidden targets, missing focus indicator or keyboard trap.
- Runtime Chrome, widths 320/390/1280: expand-all and collapse-all respond to Enter and Space, and hidden state matches the visible accordion state.
- Runtime Chrome, widths 320/390/1280: first Tab reaches the skip link; Enter focuses main; focused controls remain inside the viewport with an immediate solid 4px outline.
- Runtime Chrome, widths 320/390/1280: keyboard activation of guide step links opens the requested panel and focuses its toggle; activating a same-hash link reopens a collapsed panel; direct initial #step-7 URL opens that step.
- Runtime Chrome, widths 320/390/1280: native FAQ summaries and guide disclosure buttons toggle with Enter and Space.
- Runtime Chrome, widths 320/390/1280: real Tab traversal reaches every visible link, native summary and button in each default page state; hidden guide panels are absent from the Tab order.
- Runtime at widths 320,390,640,1280 found no horizontal overflow or clipped text/control boxes; layout adapts to a single column for narrow viewports.
- Static inspection: no positive tabindex, custom arrow-key widget, keyboard shortcut interception, or modal requiring additional focus trapping is introduced.
- Visually inspected all 12 unique local screenshot PNGs and compared all 13 image occurrences against their alt, caption, surrounding instructions, and link action labels; alternatives accurately convey each screenshot purpose.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **alt-text-headings**: No real VoiceOver/NVDA speech session performed; conclusions concern markup, visual comparison, and browser layout.
- **alt-text-headings**: Screenshots depict example app UI; repeating every incidental sample value in their alt would duplicate nonessential instructional detail.
- **alt-text-headings**: Offscreen lazy-loaded images were not forced to load in the layout run; all local screenshot files were opened and visually inspected directly.
- **aria-specialist**: Revalidation used a temporary static HTTP server on localhost:8897 and headless Chrome. Evidence: /tmp/sullivan-t1-work/revalidated/aria-live-runtime.json.
- **aria-specialist**: No actual VoiceOver/NVDA audio testing was performed.
- **aria-specialist**: The introduction has four named major content regions within main; these are the product behavior, safety, student preview and FAQ sections, with no nested named region proliferation.
- **contrast-master**: The low-contrast --line token (1.74:1 on white) is used for decorative separators and screenshot outlines, not as the sole identifier of an action, selection, or required UI control.
- **contrast-master**: No dark theme is offered; color-scheme is intentionally light. Forced-colors was emulated, not tested with a physical user-selected OS palette.
- **contrast-master**: Disabled buttons do not currently occur on these public pages and are outside the mandatory contrast exemption; source gives disabled text/background/border tokens and cursor.
- **contrast-master**: Raw runtime evidence: /tmp/sullivan-t1-work/revalidated/contrast-measurements.json, contrast-active-measurements.json, visual-measurements.json.
- **keyboard-navigator**: Saved findings: /tmp/sullivan-t1-work/revalidated/keyboard-navigator.json.
- **keyboard-navigator**: Runtime evidence: /tmp/sullivan-t1-work/revalidated/keyboard-runtime-results.json (13 grouped checks) and keyboard-expanded-results.json (12 traversal checks). Browser: Chrome/156.0.8078.80.
- **keyboard-navigator**: Independent temporary static server at 127.0.0.1:8873 served the actual app web files; no application files were edited. No authenticated guardian/sample assignment flow is included in this specialist scope.
- **keyboard-navigator**: Actual VoiceOver/NVDA speech and assistive-technology interaction were not tested. Computed keyboard focus and keyboard-driven browser behavior were tested.
- **live-region-controller**: Revalidation used a temporary static HTTP server on localhost:8897 and headless Chrome. Evidence: /tmp/sullivan-t1-work/revalidated/aria-live-runtime.json.
- **live-region-controller**: Observed DOM mutations and Chrome accessibility properties do not prove actual VoiceOver/NVDA utterances; no assistive-technology audio testing was performed.

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
    "keyboard-navigator",
    "live-region-controller"
  ],
  "scope": [
    "apps/web/guide/guide.js",
    "apps/web/guide/index.html",
    "apps/web/intro.css",
    "apps/web/intro/img/*.png",
    "apps/web/intro/index.html",
    "apps/web/tokens.css",
    "http://127.0.0.1:8871/guide/",
    "http://127.0.0.1:8871/intro/",
    "http://127.0.0.1:8873/guide/",
    "http://127.0.0.1:8873/intro/"
  ],
  "findings": [],
  "passed": [
    "All four decorative inline SVG icons are hidden with aria-hidden=true; their meaning is supplied by adjacent headings and prose.",
    "Calculated WCAG sRGB contrasts for all text/focus/control tokens against used paper, canvas, brand-soft and amber-soft backgrounds; body/muted/brand text pairs exceed 4.5:1, focus pairs exceed 3:1, functional control-border pairs exceed 3:1.",
    "Chrome accessibility tree: 8 named per-step buttons and one named expand-all button expose expanded state.",
    "Chrome accessibility tree: a status node exposes polite live behavior.",
    "Chrome forced-colors emulation supplied system foreground/background/border and Highlight outline; source uses declared system tokens.",
    "Chrome runtime and code inspection: individual accordion disclosure uses focused button aria-expanded; deep links open the selected panel and move focus to its toggle, avoiding duplicate speech from extra live messages.",
    "Chrome runtime inspection at 1280px and 390px found actual text/background pairs matching the reviewed token combinations; body text is 18px.",
    "Chrome runtime with MutationObserver: expand-all and collapse-all produce one concise Korean text update each (8개 단계를 모두 펼쳤습니다./8개 단계를 모두 접었습니다.).",
    "Chrome runtime: FAQ native details toggles with Enter/Space.",
    "Chrome runtime: JavaScript disabled leaves all eight guide panels readable and enhancement-only expand-all control hidden.",
    "Chrome runtime: all aria-controls/labelledby/describedby references resolve in both routes.",
    "Chrome runtime: hashchange opens selected step and focuses its toggle; same-hash activation reopens a collapsed selected step; initial hash opens requested step.",
    "Chrome runtime: per-step Enter/Space and expand-all Enter/Space keep aria-expanded synchronized with panel hidden state.",
    "Chrome runtime: the status node is not display:none or visibility:hidden; clipped sr-only styling retains accessibility exposure.",
    "Code and Chrome runtime: one initially empty guide-status role=status live region is present before any user action, with aria-atomic=true.",
    "Code inspection: decorative SVG icons and visual expand/collapse helper words are aria-hidden, while the step number remains in the accessible button label.",
    "Code inspection: initial page load does not populate an announcement; per-step initial visibility is conveyed through native content/expanded states.",
    "Code inspection: textContent updates the persistent status node, with no assertive region, timer, streaming transcript, or parallel live announcement.",
    "Control circle border #6f87a3 has 3.70:1 against white, with dark numbered text carrying the step information independently.",
    "Each page has one h1, a logical h1→h2→h3 outline, one main landmark, descriptive unique Korean page title, lang=ko, a working target for the skip link, and page-level header/footer.",
    "Guide navigation landmarks have distinct names: 주 메뉴 and 가이드 단계.",
    "Guide screenshots supplement full textual action instructions; image links explicitly identify the numbered step and original-size action.",
    "Native anchors/buttons/details-summary are used for links, accordion controls, and FAQ disclosure; no redundant implicit roles.",
    "No animation, flashing, autoplay or color-only state mechanism exists on the two public pages; reduced-motion and forced-colors fallbacks are provided.",
    "Outline focus color #8c4700 has at least 6.06:1 contrast against the reviewed light backgrounds; focus-visible uses instant 4px outlines with 4px offset.",
    "Primary text white/brand is 8.70:1; primary hover white/ink is 14.09:1; actual active-without-hover state retained white/brand at 8.70:1 on both routes at both widths.",
    "Runtime Chrome inspection at 320, 390, 640 and 1280 CSS-pixel widths, with guide fully expanded, found no text/control elements extending beyond the viewport and document scrollWidth equalled viewport width.",
    "Runtime Chrome with JavaScript disabled: all eight guide sections remain visible, the inactive expand-all control remains hidden, and the skip link focuses main.",
    "Runtime Chrome, widths 320/390/1280: all-expanded intro FAQ and guide states support full forward Tab and backward Shift+Tab traversal with no hidden targets, missing focus indicator or keyboard trap.",
    "Runtime Chrome, widths 320/390/1280: expand-all and collapse-all respond to Enter and Space, and hidden state matches the visible accordion state.",
    "Runtime Chrome, widths 320/390/1280: first Tab reaches the skip link; Enter focuses main; focused controls remain inside the viewport with an immediate solid 4px outline.",
    "Runtime Chrome, widths 320/390/1280: keyboard activation of guide step links opens the requested panel and focuses its toggle; activating a same-hash link reopens a collapsed panel; direct initial #step-7 URL opens that step.",
    "Runtime Chrome, widths 320/390/1280: native FAQ summaries and guide disclosure buttons toggle with Enter and Space.",
    "Runtime Chrome, widths 320/390/1280: real Tab traversal reaches every visible link, native summary and button in each default page state; hidden guide panels are absent from the Tab order.",
    "Runtime at widths 320,390,640,1280 found no horizontal overflow or clipped text/control boxes; layout adapts to a single column for narrow viewports.",
    "Static inspection: no positive tabindex, custom arrow-key widget, keyboard shortcut interception, or modal requiring additional focus trapping is introduced.",
    "Visually inspected all 12 unique local screenshot PNGs and compared all 13 image occurrences against their alt, caption, surrounding instructions, and link action labels; alternatives accurately convey each screenshot purpose."
  ],
  "notes": [
    {
      "skill": "alt-text-headings",
      "note": "No real VoiceOver/NVDA speech session performed; conclusions concern markup, visual comparison, and browser layout."
    },
    {
      "skill": "alt-text-headings",
      "note": "Screenshots depict example app UI; repeating every incidental sample value in their alt would duplicate nonessential instructional detail."
    },
    {
      "skill": "alt-text-headings",
      "note": "Offscreen lazy-loaded images were not forced to load in the layout run; all local screenshot files were opened and visually inspected directly."
    },
    {
      "skill": "aria-specialist",
      "note": "Revalidation used a temporary static HTTP server on localhost:8897 and headless Chrome. Evidence: /tmp/sullivan-t1-work/revalidated/aria-live-runtime.json."
    },
    {
      "skill": "aria-specialist",
      "note": "No actual VoiceOver/NVDA audio testing was performed."
    },
    {
      "skill": "aria-specialist",
      "note": "The introduction has four named major content regions within main; these are the product behavior, safety, student preview and FAQ sections, with no nested named region proliferation."
    },
    {
      "skill": "contrast-master",
      "note": "The low-contrast --line token (1.74:1 on white) is used for decorative separators and screenshot outlines, not as the sole identifier of an action, selection, or required UI control."
    },
    {
      "skill": "contrast-master",
      "note": "No dark theme is offered; color-scheme is intentionally light. Forced-colors was emulated, not tested with a physical user-selected OS palette."
    },
    {
      "skill": "contrast-master",
      "note": "Disabled buttons do not currently occur on these public pages and are outside the mandatory contrast exemption; source gives disabled text/background/border tokens and cursor."
    },
    {
      "skill": "contrast-master",
      "note": "Raw runtime evidence: /tmp/sullivan-t1-work/revalidated/contrast-measurements.json, contrast-active-measurements.json, visual-measurements.json."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Saved findings: /tmp/sullivan-t1-work/revalidated/keyboard-navigator.json."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Runtime evidence: /tmp/sullivan-t1-work/revalidated/keyboard-runtime-results.json (13 grouped checks) and keyboard-expanded-results.json (12 traversal checks). Browser: Chrome/156.0.8078.80."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Independent temporary static server at 127.0.0.1:8873 served the actual app web files; no application files were edited. No authenticated guardian/sample assignment flow is included in this specialist scope."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Actual VoiceOver/NVDA speech and assistive-technology interaction were not tested. Computed keyboard focus and keyboard-driven browser behavior were tested."
    },
    {
      "skill": "live-region-controller",
      "note": "Revalidation used a temporary static HTTP server on localhost:8897 and headless Chrome. Evidence: /tmp/sullivan-t1-work/revalidated/aria-live-runtime.json."
    },
    {
      "skill": "live-region-controller",
      "note": "Observed DOM mutations and Chrome accessibility properties do not prove actual VoiceOver/NVDA utterances; no assistive-technology audio testing was performed."
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
  "checks": 37,
  "generated": "2026-11-04",
  "template": "web"
}
```
