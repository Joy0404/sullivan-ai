# Web Accessibility Audit

An audit of web content, run on 2026-11-04. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-04 |
| Scope | 7 items |
| Skills run | alt-text-headings, aria-specialist, contrast-master, forms-specialist, keyboard-navigator, live-region-controller |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 41 |

Audited:

- `apps/web/index.html #guardian-result-summary and #guardian-publish`
- `apps/web/index.html guardian-result-summary/guardian-publish`
- `apps/web/role-portal.js loadGuardian display mapping`
- `apps/web/role-portal.js loadGuardian presentation observer`
- `apps/web/role-portal.js:loadGuardian presentation observer`
- `apps/web/workspace-design.css T4`
- `apps/web/workspace-design.css T4 guardian rules`

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

41 checks ran and found nothing.

- All13 measured text/background pairs passAA; minimum contrast6.19:1. Primary white/brand8.70:1.
- All9 watch/evidence/chat previews at320/390/1280 have no result text below18px and no non-checkbox controls below48px after typography/target fixes.
- Assignment form retains native labeled title/subject inputs, fieldset/legend and labeled student checkboxes.
- Authoritative safe_description_count includes INTERRUPT and respects explicit zero; candidate getters remain unread.
- Checkbox labels use24px plus flexible text grid at320,390,1280px without horizontal overflow.
- Checkboxes and long labels occupy separate24px/minmax grid columns without overlap.
- Concurrent fresh aria-label updates remain intact because restoration checks the prior displayed attribute before overwriting.
- Current-source isolated Chrome at320,390,1280px: all traversed controls, including final runtime summary, remain outside the fixed bar after targeted padding fix.
- Disabled source-storage choice retains its visible aria-describedby explanation.
- Evidence timestamp and action are separate flex items with an explicit12px gap; status text and semantic labels accompany color.
- First new guardian result focuses its visible h1 instead of the lower assignment form.
- First result is conveyed through focused summary heading; no competing summary live region is introduced.
- Fixed assignment link navigates to the form heading; it does not prematurely submit or imply a completed assignment.
- Fixed native action link focuses the publish heading within the viewport.
- Generated student checkbox identity labels are excluded from translation.
- Guardian labels/enums restore on student and signed-out roles; raw enum metadata remains unchanged.
- Guardian summary and publish now have16px inline gutters; no horizontal overflow at the three tested widths.
- Independent actual Tab traversal of watch result at320/390/1280 reached30–31 controls with no control fully obscured by fixed assignment bar.
- Instant guardian focus outline and functional control borders use previously measured token pairs above3:1; fixed bar has explicit focus-visible styling.
- Korean page language, application title, skip link and main landmark are preserved.
- Metadata count test used throwing getters for candidate text fields; observer accessed none.
- Native fixed CTA Enter focuses publish-title at visible y23..64px while bar starts819px.
- New result summary and assignment block expose descriptive section labels.
- No horizontal overflow at320,390,1280px.
- No new meaningful images or unlabeled decorative icons were introduced; the shared existing media placeholder uses existing labeled controls.
- One visible result H1 precedes tab navigation and the current H2 panel, with H3 subheads where needed and the final assignment H2.
- Original publish form submit handler retains selected-student and explicit local-storage consent validation, with existing feedback focus.
- Quick-command aria-label maps to 핵심 개념 찾기 only for guardian and restores its original student/signed-out value.
- Restoration preserves fresh content written to the same text node at a role transition.
- Result summary and workspace precede assignment form in DOM source order.
- Reversible accessible-label mapping introduces no added live channel.
- Role changes restore UI copy without translation stacking or a second announcement channel.
- Safe count metadata updates (including zero) preserve same-result deliberate focus and do not rewrite candidate text.
- Same-result observer pass produced zero mutations in the shared live region.
- Same-result presentation updates preserve deliberate publish-heading focus.
- Sample summary explicitly states that no new video analysis occurred.
- Source confirms one-time new-result title focus and tabIndex=-1, while shared lectureReady and student functions are unchanged.
- Summary quantities are text in a description list, not color or decorative marks.
- Summary/moved form ID references resolve; native description list labels each count.
- The fixed assignment link has a clear text label and a real heading fragment destination.
- The moved assignment controls occur after result content in DOM order.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **alt-text-headings**: Independent script-free preview and source review; parent owns actual authenticated mapping/flow tests.
- **alt-text-headings**: Actual VoiceOver/NVDA speech not tested.
- **aria-specialist**: Current-source isolated Chrome fixture; no backend auth or mutation.
- **aria-specialist**: Initial identity-label finding and first-result focus/restoration concerns were corrected and rechecked.
- **aria-specialist**: Runtime evidence: /tmp/sullivan-t4-work/review/aria-live-runtime.json.
- **aria-specialist**: Actual VoiceOver/NVDA audio not tested.
- **contrast-master**: Resolved initial findings VISUAL-T4-TEXT-SIZE, VISUAL-T4-TARGET-SIZE and VISUAL-T4-GUTTER; initial/contrast-master.json retains evidence.
- **contrast-master**: Checks used script-free current-source fixture without authentication or API writes; parent separately tests actual sample content, mapping and flows.
- **contrast-master**: Actual VoiceOver/NVDA speech, physical touch and user-selected OS contrast palette not tested.
- **contrast-master**: Evidence: visual-results.json, footer-focus-results.json, contrast-results.json in this directory.
- **forms-specialist**: Forms review covers unchanged submission semantics by source inspection and current rendered layout; no real API submission was performed by this specialist.
- **forms-specialist**: Runtime evidence: keyboard-layout-runtime.json. Actual VoiceOver/NVDA speech was not tested.
- **keyboard-navigator**: Runtime evidence: keyboard-layout-runtime.json. Fixture uses current DOM/CSS without API authentication or mutation; parent validates actual result observer integration.
- **keyboard-navigator**: Initial fixed-footer blocker retained in keyboard-navigator-initial.json.
- **keyboard-navigator**: Actual VoiceOver/NVDA speech was not tested.
- **live-region-controller**: Source inspection and isolated Chrome DOM/AX tests; real authenticated integration is parent-owned.
- **live-region-controller**: No actual screen-reader utterances or live TTS output were heard.

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
    "forms-specialist",
    "keyboard-navigator",
    "live-region-controller"
  ],
  "scope": [
    "apps/web/index.html #guardian-result-summary and #guardian-publish",
    "apps/web/index.html guardian-result-summary/guardian-publish",
    "apps/web/role-portal.js loadGuardian display mapping",
    "apps/web/role-portal.js loadGuardian presentation observer",
    "apps/web/role-portal.js:loadGuardian presentation observer",
    "apps/web/workspace-design.css T4",
    "apps/web/workspace-design.css T4 guardian rules"
  ],
  "findings": [],
  "passed": [
    "All13 measured text/background pairs passAA; minimum contrast6.19:1. Primary white/brand8.70:1.",
    "All9 watch/evidence/chat previews at320/390/1280 have no result text below18px and no non-checkbox controls below48px after typography/target fixes.",
    "Assignment form retains native labeled title/subject inputs, fieldset/legend and labeled student checkboxes.",
    "Authoritative safe_description_count includes INTERRUPT and respects explicit zero; candidate getters remain unread.",
    "Checkbox labels use24px plus flexible text grid at320,390,1280px without horizontal overflow.",
    "Checkboxes and long labels occupy separate24px/minmax grid columns without overlap.",
    "Concurrent fresh aria-label updates remain intact because restoration checks the prior displayed attribute before overwriting.",
    "Current-source isolated Chrome at320,390,1280px: all traversed controls, including final runtime summary, remain outside the fixed bar after targeted padding fix.",
    "Disabled source-storage choice retains its visible aria-describedby explanation.",
    "Evidence timestamp and action are separate flex items with an explicit12px gap; status text and semantic labels accompany color.",
    "First new guardian result focuses its visible h1 instead of the lower assignment form.",
    "First result is conveyed through focused summary heading; no competing summary live region is introduced.",
    "Fixed assignment link navigates to the form heading; it does not prematurely submit or imply a completed assignment.",
    "Fixed native action link focuses the publish heading within the viewport.",
    "Generated student checkbox identity labels are excluded from translation.",
    "Guardian labels/enums restore on student and signed-out roles; raw enum metadata remains unchanged.",
    "Guardian summary and publish now have16px inline gutters; no horizontal overflow at the three tested widths.",
    "Independent actual Tab traversal of watch result at320/390/1280 reached30–31 controls with no control fully obscured by fixed assignment bar.",
    "Instant guardian focus outline and functional control borders use previously measured token pairs above3:1; fixed bar has explicit focus-visible styling.",
    "Korean page language, application title, skip link and main landmark are preserved.",
    "Metadata count test used throwing getters for candidate text fields; observer accessed none.",
    "Native fixed CTA Enter focuses publish-title at visible y23..64px while bar starts819px.",
    "New result summary and assignment block expose descriptive section labels.",
    "No horizontal overflow at320,390,1280px.",
    "No new meaningful images or unlabeled decorative icons were introduced; the shared existing media placeholder uses existing labeled controls.",
    "One visible result H1 precedes tab navigation and the current H2 panel, with H3 subheads where needed and the final assignment H2.",
    "Original publish form submit handler retains selected-student and explicit local-storage consent validation, with existing feedback focus.",
    "Quick-command aria-label maps to 핵심 개념 찾기 only for guardian and restores its original student/signed-out value.",
    "Restoration preserves fresh content written to the same text node at a role transition.",
    "Result summary and workspace precede assignment form in DOM source order.",
    "Reversible accessible-label mapping introduces no added live channel.",
    "Role changes restore UI copy without translation stacking or a second announcement channel.",
    "Safe count metadata updates (including zero) preserve same-result deliberate focus and do not rewrite candidate text.",
    "Same-result observer pass produced zero mutations in the shared live region.",
    "Same-result presentation updates preserve deliberate publish-heading focus.",
    "Sample summary explicitly states that no new video analysis occurred.",
    "Source confirms one-time new-result title focus and tabIndex=-1, while shared lectureReady and student functions are unchanged.",
    "Summary quantities are text in a description list, not color or decorative marks.",
    "Summary/moved form ID references resolve; native description list labels each count.",
    "The fixed assignment link has a clear text label and a real heading fragment destination.",
    "The moved assignment controls occur after result content in DOM order."
  ],
  "notes": [
    {
      "skill": "alt-text-headings",
      "note": "Independent script-free preview and source review; parent owns actual authenticated mapping/flow tests."
    },
    {
      "skill": "alt-text-headings",
      "note": "Actual VoiceOver/NVDA speech not tested."
    },
    {
      "skill": "aria-specialist",
      "note": "Current-source isolated Chrome fixture; no backend auth or mutation."
    },
    {
      "skill": "aria-specialist",
      "note": "Initial identity-label finding and first-result focus/restoration concerns were corrected and rechecked."
    },
    {
      "skill": "aria-specialist",
      "note": "Runtime evidence: /tmp/sullivan-t4-work/review/aria-live-runtime.json."
    },
    {
      "skill": "aria-specialist",
      "note": "Actual VoiceOver/NVDA audio not tested."
    },
    {
      "skill": "contrast-master",
      "note": "Resolved initial findings VISUAL-T4-TEXT-SIZE, VISUAL-T4-TARGET-SIZE and VISUAL-T4-GUTTER; initial/contrast-master.json retains evidence."
    },
    {
      "skill": "contrast-master",
      "note": "Checks used script-free current-source fixture without authentication or API writes; parent separately tests actual sample content, mapping and flows."
    },
    {
      "skill": "contrast-master",
      "note": "Actual VoiceOver/NVDA speech, physical touch and user-selected OS contrast palette not tested."
    },
    {
      "skill": "contrast-master",
      "note": "Evidence: visual-results.json, footer-focus-results.json, contrast-results.json in this directory."
    },
    {
      "skill": "forms-specialist",
      "note": "Forms review covers unchanged submission semantics by source inspection and current rendered layout; no real API submission was performed by this specialist."
    },
    {
      "skill": "forms-specialist",
      "note": "Runtime evidence: keyboard-layout-runtime.json. Actual VoiceOver/NVDA speech was not tested."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Runtime evidence: keyboard-layout-runtime.json. Fixture uses current DOM/CSS without API authentication or mutation; parent validates actual result observer integration."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Initial fixed-footer blocker retained in keyboard-navigator-initial.json."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Actual VoiceOver/NVDA speech was not tested."
    },
    {
      "skill": "live-region-controller",
      "note": "Source inspection and isolated Chrome DOM/AX tests; real authenticated integration is parent-owned."
    },
    {
      "skill": "live-region-controller",
      "note": "No actual screen-reader utterances or live TTS output were heard."
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
  "checks": 41,
  "generated": "2026-11-04",
  "template": "web"
}
```
