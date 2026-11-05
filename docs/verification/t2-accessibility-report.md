# Web Accessibility Audit

An audit of web content, run on 2026-11-04. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-04 |
| Scope | 15 items |
| Skills run | alt-text-headings, aria-specialist, contrast-master, forms-specialist, keyboard-navigator, live-region-controller |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 46 |

Audited:

- `/tmp/sullivan-t2-work/snapshots/assigned.html`
- `/tmp/sullivan-t2-work/snapshots/empty.html`
- `/tmp/sullivan-t2-work/snapshots/no-lectures.html`
- `apps/web/guardian-design.css`
- `apps/web/guardian-design.css (guardian dashboard rules)`
- `apps/web/guardian-design.css guardian rules`
- `apps/web/index.html #guardian-dashboard`
- `apps/web/index.html#guardian-dashboard`
- `apps/web/role-portal.js loadGuardian and renderGuardianLectures`
- `apps/web/role-portal.js loadGuardian/renderGuardianLectures`
- `apps/web/role-portal.js:loadGuardian`
- `apps/web/role-portal.js:renderGuardianLectures`
- `apps/web/tokens.css (read only)`
- `apps/web/workspace-design.css (read only)`
- `docs/verification/t2-assigned-390.png`

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

46 checks ran and found nothing.

- Account name and guide link are native DOM text/link, populated with textContent rather than HTML.
- All three rendered scenario snapshots expose exactly one visible H1: 보호자 준비실.
- All10 measured text/background pairs pass4.5:1 AA; token-based normal, hover and active pairs also pass4.5:1.
- Calculated focus-ring contrast exceeds3:1 on paper, canvas, brand-soft and amber-soft; functional input/control borders exceed3:1 on the adjacent white surface.
- Chrome AX tree exposes preparation status with polite live behavior.
- Chrome MutationObserver fixture: reloading unchanged totals produces0 mutations; changed totals update existing status node exactly once.
- Chrome accessible names preserve task label/state boundaries, e.g. 학생 계정 만들기 완료.
- Chrome isolated fixture: all scoped ARIA ID references resolve.
- Chrome runtime fixture: all 56 visible controls in the fully expanded guardian dashboard were reached using real Tab at 320, 390 and 1280px; focus stayed visible and enabled, with no missing controls or keyboard traps.
- Chrome runtime with in-memory response fixture: successful lecture edits and simulated server validation failures leave visible, focused feedback after any rerender.
- Chrome runtime with in-memory response fixture: successful settings saves focus the named feedback group.
- Chrome runtime: Tab then Shift+Tab returned to the same next-action control at 320, 390 and 1280px.
- Chrome runtime: a student-card settings link selects that student before the existing settings renderer populates controls.
- Chrome runtime: crossing to the mobile breakpoint moves focus from help content to the summary before closing the disclosure.
- Chrome runtime: each student settings link selects the intended student and focuses the expanded settings summary.
- Chrome runtime: lecture management opens and closes with Space; the mobile help link opens help and focuses its summary.
- Chrome runtime: student settings and sample-assignment controls are disabled when no linked student exists; the visible explanatory hint remains available.
- Chrome runtime: submitting a lecture form with an empty title invokes native required-field validation and focuses the title input.
- Chrome runtime: submitting sample assignment without selecting among multiple students focuses the required student selector.
- Chrome runtime: the assignment task now keeps its focused H2 visible at y=23.9..57.5px after the scroll fix.
- Chrome runtime: the no-student next action opens the moved create disclosure and focuses its first input; the settings task opens its native summary even while controls are unavailable.
- Chrome runtime: typing a password shorter than eight characters and submitting leaves focus on the password field with tooShort validity.
- Confirmed fix in current source and Chrome fixture: when Help auto-collapses from1280px to390px with focus inside, focus returns to its SUMMARY and remains visible.
- DOM order is task status, students, lectures and preparation; the no-student create form moves before task status as explicitly required; the responsive layout does not reorder the content visually with CSS.
- Dashboard home loading uses aria-busy and inert while fetching, then restores normal state.
- Focus-visible has instant4px outlines and4px offset; Chrome forced-colors preview exposes a4px system Highlight outline.
- Guardian data rendered by new code is limited to owned student/lecture metadata; analysis candidate text is not read or emitted.
- HTML lang remains ko; the existing product page title still describes the lecture accessibility application.
- Independent Chrome read-only snapshots: all-expanded empty, no-lectures and assigned states at320,390,640,1280px have no horizontal overflow.
- Independent rendered CSS inspection found no text below18px inside the new guardian dashboard and account tools in all12 scenario/width combinations; mobile logout fix confirmed.
- Names, lecture counts, assignment targets, preparation states and management actions are actual text nodes, not images, generated icons or CSS-only content.
- Native disclosure state and focus communicate task navigation without extra duplicate live messages.
- Native settings and Manage disclosures expose expanded state and accessible names.
- No assertive live region or streaming analysis content was introduced by T2.
- No motion or flashing is introduced; new dashboard reduced-motion rules disable animation/transition and existing forced-colors handling is retained.
- No raster image, chart, SVG or decorative icon was introduced in the guardian dashboard, so no new visual-only meaning needs alternative text.
- Preparation status exists in initial DOM, uses role=status and aria-atomic=true, and is filled with textContent without replacing the live node.
- Static and Chrome runtime: moved account creation controls retain native labels, names, required attributes, new-password autocomplete and minimum password length; empty submission focuses the first required input.
- Static: native links, buttons and disclosures retain natural DOM tab order; no positive tabindex or mouse-only actions were introduced in T2.
- Static: settings groups and assignment checkbox groups use native fieldsets and legends, with wrapping labels and original submission contracts intact.
- Status meaning is explicit in Korean text (완료, 할 차례, 아직, 기본값, 준비 완료/준비 중); color is supplementary.
- Student Settings links select the matching student before opening settings.
- Student/assignment/settings outcomes keep the existing focused feedback group; non-focused order outcomes use existing polite announce().
- Task links use native anchors; keyboard activation opens applicable details and focuses a visible input, summary or heading.
- The dashboard heading outline progresses H1 to H2 sections and H3 student/lecture/settings/sample subheadings, with no skipped levels.
- The main landmark and skip-link target remain; a separately labeled native aside identifies guardian help.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **alt-text-headings**: This is a targeted T2 audit; frozen student regions and existing media players were not re-audited as new findings.
- **alt-text-headings**: Heading structure was inspected in actual parent-exported rendered snapshots at320,390,640,1280px, including expanded details. The screenshot was visually inspected for readability.
- **alt-text-headings**: Parent owns actual authenticated and keyboard flow tests. This specialist performed no authentication or API writes; actual screen-reader utterances are unverified.
- **aria-specialist**: Runtime used current source functions in an isolated DOM fixture with mocked read-only student/lecture data; no API calls, authentication or app edits.
- **aria-specialist**: Actual VoiceOver/NVDA speech and Safari accessibility navigation were not tested.
- **aria-specialist**: Parent separately validates authenticated integration.
- **aria-specialist**: Runtime evidence: /tmp/sullivan-t2-work/review/aria-live-runtime.json.
- **aria-specialist**: Initial ARIA-FOCUS-RESPONSIVE-001 was resolved; original finding retained in aria-specialist-initial.json.
- **contrast-master**: Initial read-only static preview identified mobile logout text14.4px; parent added guardian-only font-size1.125rem and current snapshots confirm18px. No remaining finding.
- **contrast-master**: Top-right 도움 link was allowed to wrap vertically; parent added no-wrap/flex-shrink0 and the actual390px screenshot confirms a single readable line.
- **contrast-master**: Runtime inspection used exported rendered DOM snapshots with all scripts removed; no authentication or API mutation was performed by this specialist. The parent owns actual authenticated interaction tests.
- **contrast-master**: Actual OS high-contrast settings and VoiceOver/NVDA speech were not tested. Color preference was emulated in Chrome.
- **contrast-master**: Decorative low-contrast row separators do not carry sole meaning; actionable links, controls and states have text identification.
- **contrast-master**: Evidence: /tmp/sullivan-t2-work/review/visual-snapshot-measurements.json, measured-text-contrast.json, contrast-calculations.json and visual-static-measurements.json.
- **forms-specialist**: All save/error responses were fulfilled by browser request interception; no API mutation or authentication request reached a backend.
- **forms-specialist**: Runtime results: /tmp/sullivan-t2-work/review/forms-fixture-runtime.json.
- **forms-specialist**: The existing login-name pattern issue is reserved for T6; T2 does not alter that pattern or authentication. Actual screen-reader speech was not tested.
- **keyboard-navigator**: One moderate assignment-focus scrolling finding was fixed and rechecked; initial evidence is in initial/keyboard-navigator.json and keyboard-fixture-initial-runtime.json.
- **keyboard-navigator**: Independent fixture intercepted every /local/* request in memory and aborted provider requests. It neither authenticated against nor mutated the real or temporary API database.
- **keyboard-navigator**: Runtime results: /tmp/sullivan-t2-work/review/keyboard-fixture-runtime.json. Actual VoiceOver/NVDA utterances were not tested.
- **live-region-controller**: No real screen-reader utterance was heard; checks cover DOM, Chrome accessibility tree and mutation behavior.
- **live-region-controller**: Read-only mocked data boundaries in isolated fixture; authenticated integration is validated by parent.
- **live-region-controller**: Runtime evidence: /tmp/sullivan-t2-work/review/aria-live-runtime.json.

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
    "/tmp/sullivan-t2-work/snapshots/assigned.html",
    "/tmp/sullivan-t2-work/snapshots/empty.html",
    "/tmp/sullivan-t2-work/snapshots/no-lectures.html",
    "apps/web/guardian-design.css",
    "apps/web/guardian-design.css (guardian dashboard rules)",
    "apps/web/guardian-design.css guardian rules",
    "apps/web/index.html #guardian-dashboard",
    "apps/web/index.html#guardian-dashboard",
    "apps/web/role-portal.js loadGuardian and renderGuardianLectures",
    "apps/web/role-portal.js loadGuardian/renderGuardianLectures",
    "apps/web/role-portal.js:loadGuardian",
    "apps/web/role-portal.js:renderGuardianLectures",
    "apps/web/tokens.css (read only)",
    "apps/web/workspace-design.css (read only)",
    "docs/verification/t2-assigned-390.png"
  ],
  "findings": [],
  "passed": [
    "Account name and guide link are native DOM text/link, populated with textContent rather than HTML.",
    "All three rendered scenario snapshots expose exactly one visible H1: 보호자 준비실.",
    "All10 measured text/background pairs pass4.5:1 AA; token-based normal, hover and active pairs also pass4.5:1.",
    "Calculated focus-ring contrast exceeds3:1 on paper, canvas, brand-soft and amber-soft; functional input/control borders exceed3:1 on the adjacent white surface.",
    "Chrome AX tree exposes preparation status with polite live behavior.",
    "Chrome MutationObserver fixture: reloading unchanged totals produces0 mutations; changed totals update existing status node exactly once.",
    "Chrome accessible names preserve task label/state boundaries, e.g. 학생 계정 만들기 완료.",
    "Chrome isolated fixture: all scoped ARIA ID references resolve.",
    "Chrome runtime fixture: all 56 visible controls in the fully expanded guardian dashboard were reached using real Tab at 320, 390 and 1280px; focus stayed visible and enabled, with no missing controls or keyboard traps.",
    "Chrome runtime with in-memory response fixture: successful lecture edits and simulated server validation failures leave visible, focused feedback after any rerender.",
    "Chrome runtime with in-memory response fixture: successful settings saves focus the named feedback group.",
    "Chrome runtime: Tab then Shift+Tab returned to the same next-action control at 320, 390 and 1280px.",
    "Chrome runtime: a student-card settings link selects that student before the existing settings renderer populates controls.",
    "Chrome runtime: crossing to the mobile breakpoint moves focus from help content to the summary before closing the disclosure.",
    "Chrome runtime: each student settings link selects the intended student and focuses the expanded settings summary.",
    "Chrome runtime: lecture management opens and closes with Space; the mobile help link opens help and focuses its summary.",
    "Chrome runtime: student settings and sample-assignment controls are disabled when no linked student exists; the visible explanatory hint remains available.",
    "Chrome runtime: submitting a lecture form with an empty title invokes native required-field validation and focuses the title input.",
    "Chrome runtime: submitting sample assignment without selecting among multiple students focuses the required student selector.",
    "Chrome runtime: the assignment task now keeps its focused H2 visible at y=23.9..57.5px after the scroll fix.",
    "Chrome runtime: the no-student next action opens the moved create disclosure and focuses its first input; the settings task opens its native summary even while controls are unavailable.",
    "Chrome runtime: typing a password shorter than eight characters and submitting leaves focus on the password field with tooShort validity.",
    "Confirmed fix in current source and Chrome fixture: when Help auto-collapses from1280px to390px with focus inside, focus returns to its SUMMARY and remains visible.",
    "DOM order is task status, students, lectures and preparation; the no-student create form moves before task status as explicitly required; the responsive layout does not reorder the content visually with CSS.",
    "Dashboard home loading uses aria-busy and inert while fetching, then restores normal state.",
    "Focus-visible has instant4px outlines and4px offset; Chrome forced-colors preview exposes a4px system Highlight outline.",
    "Guardian data rendered by new code is limited to owned student/lecture metadata; analysis candidate text is not read or emitted.",
    "HTML lang remains ko; the existing product page title still describes the lecture accessibility application.",
    "Independent Chrome read-only snapshots: all-expanded empty, no-lectures and assigned states at320,390,640,1280px have no horizontal overflow.",
    "Independent rendered CSS inspection found no text below18px inside the new guardian dashboard and account tools in all12 scenario/width combinations; mobile logout fix confirmed.",
    "Names, lecture counts, assignment targets, preparation states and management actions are actual text nodes, not images, generated icons or CSS-only content.",
    "Native disclosure state and focus communicate task navigation without extra duplicate live messages.",
    "Native settings and Manage disclosures expose expanded state and accessible names.",
    "No assertive live region or streaming analysis content was introduced by T2.",
    "No motion or flashing is introduced; new dashboard reduced-motion rules disable animation/transition and existing forced-colors handling is retained.",
    "No raster image, chart, SVG or decorative icon was introduced in the guardian dashboard, so no new visual-only meaning needs alternative text.",
    "Preparation status exists in initial DOM, uses role=status and aria-atomic=true, and is filled with textContent without replacing the live node.",
    "Static and Chrome runtime: moved account creation controls retain native labels, names, required attributes, new-password autocomplete and minimum password length; empty submission focuses the first required input.",
    "Static: native links, buttons and disclosures retain natural DOM tab order; no positive tabindex or mouse-only actions were introduced in T2.",
    "Static: settings groups and assignment checkbox groups use native fieldsets and legends, with wrapping labels and original submission contracts intact.",
    "Status meaning is explicit in Korean text (완료, 할 차례, 아직, 기본값, 준비 완료/준비 중); color is supplementary.",
    "Student Settings links select the matching student before opening settings.",
    "Student/assignment/settings outcomes keep the existing focused feedback group; non-focused order outcomes use existing polite announce().",
    "Task links use native anchors; keyboard activation opens applicable details and focuses a visible input, summary or heading.",
    "The dashboard heading outline progresses H1 to H2 sections and H3 student/lecture/settings/sample subheadings, with no skipped levels.",
    "The main landmark and skip-link target remain; a separately labeled native aside identifies guardian help."
  ],
  "notes": [
    {
      "skill": "alt-text-headings",
      "note": "This is a targeted T2 audit; frozen student regions and existing media players were not re-audited as new findings."
    },
    {
      "skill": "alt-text-headings",
      "note": "Heading structure was inspected in actual parent-exported rendered snapshots at320,390,640,1280px, including expanded details. The screenshot was visually inspected for readability."
    },
    {
      "skill": "alt-text-headings",
      "note": "Parent owns actual authenticated and keyboard flow tests. This specialist performed no authentication or API writes; actual screen-reader utterances are unverified."
    },
    {
      "skill": "aria-specialist",
      "note": "Runtime used current source functions in an isolated DOM fixture with mocked read-only student/lecture data; no API calls, authentication or app edits."
    },
    {
      "skill": "aria-specialist",
      "note": "Actual VoiceOver/NVDA speech and Safari accessibility navigation were not tested."
    },
    {
      "skill": "aria-specialist",
      "note": "Parent separately validates authenticated integration."
    },
    {
      "skill": "aria-specialist",
      "note": "Runtime evidence: /tmp/sullivan-t2-work/review/aria-live-runtime.json."
    },
    {
      "skill": "aria-specialist",
      "note": "Initial ARIA-FOCUS-RESPONSIVE-001 was resolved; original finding retained in aria-specialist-initial.json."
    },
    {
      "skill": "contrast-master",
      "note": "Initial read-only static preview identified mobile logout text14.4px; parent added guardian-only font-size1.125rem and current snapshots confirm18px. No remaining finding."
    },
    {
      "skill": "contrast-master",
      "note": "Top-right 도움 link was allowed to wrap vertically; parent added no-wrap/flex-shrink0 and the actual390px screenshot confirms a single readable line."
    },
    {
      "skill": "contrast-master",
      "note": "Runtime inspection used exported rendered DOM snapshots with all scripts removed; no authentication or API mutation was performed by this specialist. The parent owns actual authenticated interaction tests."
    },
    {
      "skill": "contrast-master",
      "note": "Actual OS high-contrast settings and VoiceOver/NVDA speech were not tested. Color preference was emulated in Chrome."
    },
    {
      "skill": "contrast-master",
      "note": "Decorative low-contrast row separators do not carry sole meaning; actionable links, controls and states have text identification."
    },
    {
      "skill": "contrast-master",
      "note": "Evidence: /tmp/sullivan-t2-work/review/visual-snapshot-measurements.json, measured-text-contrast.json, contrast-calculations.json and visual-static-measurements.json."
    },
    {
      "skill": "forms-specialist",
      "note": "All save/error responses were fulfilled by browser request interception; no API mutation or authentication request reached a backend."
    },
    {
      "skill": "forms-specialist",
      "note": "Runtime results: /tmp/sullivan-t2-work/review/forms-fixture-runtime.json."
    },
    {
      "skill": "forms-specialist",
      "note": "The existing login-name pattern issue is reserved for T6; T2 does not alter that pattern or authentication. Actual screen-reader speech was not tested."
    },
    {
      "skill": "keyboard-navigator",
      "note": "One moderate assignment-focus scrolling finding was fixed and rechecked; initial evidence is in initial/keyboard-navigator.json and keyboard-fixture-initial-runtime.json."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Independent fixture intercepted every /local/* request in memory and aborted provider requests. It neither authenticated against nor mutated the real or temporary API database."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Runtime results: /tmp/sullivan-t2-work/review/keyboard-fixture-runtime.json. Actual VoiceOver/NVDA utterances were not tested."
    },
    {
      "skill": "live-region-controller",
      "note": "No real screen-reader utterance was heard; checks cover DOM, Chrome accessibility tree and mutation behavior."
    },
    {
      "skill": "live-region-controller",
      "note": "Read-only mocked data boundaries in isolated fixture; authenticated integration is validated by parent."
    },
    {
      "skill": "live-region-controller",
      "note": "Runtime evidence: /tmp/sullivan-t2-work/review/aria-live-runtime.json."
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
  "checks": 46,
  "generated": "2026-11-04",
  "template": "web"
}
```
