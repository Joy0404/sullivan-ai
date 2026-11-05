# Web Accessibility Audit

An audit of web content, run on 2026-11-04. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-04 |
| Scope | 4 items |
| Skills run | alt-text-headings, aria-specialist, contrast-master, forms-specialist, keyboard-navigator, live-region-controller |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 40 |

Audited:

- `apps/web/guardian-design.css T3 rules`
- `apps/web/index.html #lecture-form`
- `apps/web/role-portal.js prepare`
- `apps/web/role-portal.js:prepare`

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

40 checks ran and found nothing.

- 1280px: visible native wizard controls reachable by actual Tab, hidden panels not focused
- 320px: visible native wizard controls reachable by actual Tab, hidden panels not focused
- 390px: visible native wizard controls reachable by actual Tab, hidden panels not focused
- All five visible wizard configurations expose exactly one H1, 강의 등록, followed by a correctly ordered H2 for the current stage.
- All scoped aria-labelledby/aria-describedby/aria-controls ID references resolve.
- Back/forward preserves previously entered title
- Chrome AX tree: focused current-stage heading exposes its title and 1/3 stage description.
- Consent and trial code are required for real-video path before entering review
- Corrected validation restores original descriptions and clears aria-invalid.
- Current source and independent Chrome recheck: all15 stage/source/width combinations at320/390/1280 have no wizard text below18px.
- Current step/source/error information uses textual labels and semantic states in addition to color.
- Enter in input advances current step without reaching existing analyzer
- Exactly one native source-choice button exposes aria-pressed=true; other source controls stay hidden.
- Focus brown on white/canvas6.96:1/6.24:1; functional control-border on white/canvas3.70:1/3.32:1.
- Inline validation is announced through the focused field's associated error description; no duplicate assertive region is introduced.
- Material-only TXT path requires no video/cloud consent/code and reaches original submit handler; native file chooser remains keyboard-accessible
- Materials, choices and progress are conveyed by text; active step state has aria-current and the textual fraction.
- Missing and invalid link are rejected in step 2 with focus
- New wizard rules introduce no animation, flashing or automatic media playback; inherited guardian focus remains instant4px and forced-colors uses system focus token.
- Nine measured text/background pairs pass4.5:1 AA, minimum6.19:1; primary white/brand8.70:1.
- No horizontal overflow in step1, step2sample/link/file, or step3 previews at320/390/1280.
- One main landmark, labeled breadcrumb navigation and labeled wizard sections are preserved.
- Original detailed consent text retained verbatim
- Original named form controls exactly preserved
- Preferred-mode/sample selects, Gemini disclosure and all other non-checkbox wizard controls meet the requested48px minimum after stronger selector fixes.
- Prepare focuses step heading with numbered-step description
- Required step-1 field focuses invalid visible input and associates inline error
- Rights are required at final review and capture handler passes valid real submission exactly once
- Sample path hides and disables source-inapplicable required rights consent; Chrome does not expose a misleading mandatory checkbox.
- Sample submission invokes only the sample boundary stub and leaves the analyzer listener untouched.
- Sample submits to existing sample function, not real analyzer; prior source files cleared explicitly on mode choice
- Source reset to sample clears uploaded material values and states explicitly that no new video/upload analysis occurs.
- Source switches expose their pressed state and make the relevant native fields available in normal Tab order.
- Step navigation uses focused heading plus static stage-count description instead of a competing live announcement.
- Successful drag/drop focuses the affected native file input; selected TXT count/name and native file value update without requiring a duplicate live channel.
- Targeted confirmation: sample mode hides/disables the problem-mode and rights inputs, while showing the prepared-policy explanation.
- Targeted confirmation: sample review subject now explicitly says 샘플에 포함된 과목 instead of showing an unused form value.
- Validation moves focus to the visible invalid field; aria-invalid and inline error description are exposed through Chrome AX.
- Wizard contains no meaningful raster images or decorative icons requiring additional alternatives.
- html lang=ko and a descriptive application title are present.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **alt-text-headings**: Heading/landmark review used current source plus script-free Chrome previews, not authenticated API flow.
- **alt-text-headings**: Application-wide document title remains shared across views; step headings and focus identify current wizard content.
- **alt-text-headings**: Actual VoiceOver/NVDA speech was not tested.
- **aria-specialist**: Runtime used an isolated DOM fixture executing current prepare() plus original file/consent handlers; fake sample/analyzer boundaries and zero actual API requests.
- **aria-specialist**: Earlier static concerns about sample required rights state and drop feedback were corrected before final fixture verification.
- **aria-specialist**: Actual VoiceOver/NVDA audio was not tested; authenticated HTTP integration belongs to the parent run.
- **aria-specialist**: Runtime evidence: /tmp/sullivan-t3-work/review/aria-live-runtime.json.
- **contrast-master**: Initial issues VISUAL-T3-TEXT-SIZE and VISUAL-T3-TARGET-SIZE are resolved; evidence in initial/contrast-master.json and final visual-results.json.
- **contrast-master**: Read-only, script-free DOM preview with current CSS; no API authentication/writes/provider requests. Parent separately verifies actual interaction and processing.
- **contrast-master**: Actual VoiceOver/NVDA speech, user-selected OS contrast palette and hardware touch were not tested.
- **contrast-master**: Contrast evidence: contrast-results.json; visual states: visual-results.json.
- **forms-specialist**: Runtime used an isolated current-source DOM fixture with the analyzer/sample boundaries mocked; no API authentication or writes.
- **forms-specialist**: Actual VoiceOver/NVDA speech was not tested.
- **forms-specialist**: Detailed runtime evidence: /tmp/sullivan-t3-work/review/forms-keyboard-runtime.json.
- **forms-specialist**: Initial minor review-summary finding retained in forms-specialist-initial.json; corrected in current source and isolated runtime still passes.
- **keyboard-navigator**: Runtime used an isolated current-source DOM fixture with the analyzer/sample boundaries mocked; no API authentication or writes.
- **keyboard-navigator**: Actual VoiceOver/NVDA speech was not tested.
- **keyboard-navigator**: Detailed runtime evidence: /tmp/sullivan-t3-work/review/forms-keyboard-runtime.json.
- **live-region-controller**: Current-source Chrome fixture checks passed without authentication or backend mutation.
- **live-region-controller**: Native file-picker speech and VoiceOver/NVDA actual utterances were not heard.
- **live-region-controller**: Parent separately validates original progress/success/error announcement behavior through the real local analyzer flow.
- **live-region-controller**: Runtime evidence: /tmp/sullivan-t3-work/review/aria-live-runtime.json.

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
    "apps/web/guardian-design.css T3 rules",
    "apps/web/index.html #lecture-form",
    "apps/web/role-portal.js prepare",
    "apps/web/role-portal.js:prepare"
  ],
  "findings": [],
  "passed": [
    "1280px: visible native wizard controls reachable by actual Tab, hidden panels not focused",
    "320px: visible native wizard controls reachable by actual Tab, hidden panels not focused",
    "390px: visible native wizard controls reachable by actual Tab, hidden panels not focused",
    "All five visible wizard configurations expose exactly one H1, 강의 등록, followed by a correctly ordered H2 for the current stage.",
    "All scoped aria-labelledby/aria-describedby/aria-controls ID references resolve.",
    "Back/forward preserves previously entered title",
    "Chrome AX tree: focused current-stage heading exposes its title and 1/3 stage description.",
    "Consent and trial code are required for real-video path before entering review",
    "Corrected validation restores original descriptions and clears aria-invalid.",
    "Current source and independent Chrome recheck: all15 stage/source/width combinations at320/390/1280 have no wizard text below18px.",
    "Current step/source/error information uses textual labels and semantic states in addition to color.",
    "Enter in input advances current step without reaching existing analyzer",
    "Exactly one native source-choice button exposes aria-pressed=true; other source controls stay hidden.",
    "Focus brown on white/canvas6.96:1/6.24:1; functional control-border on white/canvas3.70:1/3.32:1.",
    "Inline validation is announced through the focused field's associated error description; no duplicate assertive region is introduced.",
    "Material-only TXT path requires no video/cloud consent/code and reaches original submit handler; native file chooser remains keyboard-accessible",
    "Materials, choices and progress are conveyed by text; active step state has aria-current and the textual fraction.",
    "Missing and invalid link are rejected in step 2 with focus",
    "New wizard rules introduce no animation, flashing or automatic media playback; inherited guardian focus remains instant4px and forced-colors uses system focus token.",
    "Nine measured text/background pairs pass4.5:1 AA, minimum6.19:1; primary white/brand8.70:1.",
    "No horizontal overflow in step1, step2sample/link/file, or step3 previews at320/390/1280.",
    "One main landmark, labeled breadcrumb navigation and labeled wizard sections are preserved.",
    "Original detailed consent text retained verbatim",
    "Original named form controls exactly preserved",
    "Preferred-mode/sample selects, Gemini disclosure and all other non-checkbox wizard controls meet the requested48px minimum after stronger selector fixes.",
    "Prepare focuses step heading with numbered-step description",
    "Required step-1 field focuses invalid visible input and associates inline error",
    "Rights are required at final review and capture handler passes valid real submission exactly once",
    "Sample path hides and disables source-inapplicable required rights consent; Chrome does not expose a misleading mandatory checkbox.",
    "Sample submission invokes only the sample boundary stub and leaves the analyzer listener untouched.",
    "Sample submits to existing sample function, not real analyzer; prior source files cleared explicitly on mode choice",
    "Source reset to sample clears uploaded material values and states explicitly that no new video/upload analysis occurs.",
    "Source switches expose their pressed state and make the relevant native fields available in normal Tab order.",
    "Step navigation uses focused heading plus static stage-count description instead of a competing live announcement.",
    "Successful drag/drop focuses the affected native file input; selected TXT count/name and native file value update without requiring a duplicate live channel.",
    "Targeted confirmation: sample mode hides/disables the problem-mode and rights inputs, while showing the prepared-policy explanation.",
    "Targeted confirmation: sample review subject now explicitly says 샘플에 포함된 과목 instead of showing an unused form value.",
    "Validation moves focus to the visible invalid field; aria-invalid and inline error description are exposed through Chrome AX.",
    "Wizard contains no meaningful raster images or decorative icons requiring additional alternatives.",
    "html lang=ko and a descriptive application title are present."
  ],
  "notes": [
    {
      "skill": "alt-text-headings",
      "note": "Heading/landmark review used current source plus script-free Chrome previews, not authenticated API flow."
    },
    {
      "skill": "alt-text-headings",
      "note": "Application-wide document title remains shared across views; step headings and focus identify current wizard content."
    },
    {
      "skill": "alt-text-headings",
      "note": "Actual VoiceOver/NVDA speech was not tested."
    },
    {
      "skill": "aria-specialist",
      "note": "Runtime used an isolated DOM fixture executing current prepare() plus original file/consent handlers; fake sample/analyzer boundaries and zero actual API requests."
    },
    {
      "skill": "aria-specialist",
      "note": "Earlier static concerns about sample required rights state and drop feedback were corrected before final fixture verification."
    },
    {
      "skill": "aria-specialist",
      "note": "Actual VoiceOver/NVDA audio was not tested; authenticated HTTP integration belongs to the parent run."
    },
    {
      "skill": "aria-specialist",
      "note": "Runtime evidence: /tmp/sullivan-t3-work/review/aria-live-runtime.json."
    },
    {
      "skill": "contrast-master",
      "note": "Initial issues VISUAL-T3-TEXT-SIZE and VISUAL-T3-TARGET-SIZE are resolved; evidence in initial/contrast-master.json and final visual-results.json."
    },
    {
      "skill": "contrast-master",
      "note": "Read-only, script-free DOM preview with current CSS; no API authentication/writes/provider requests. Parent separately verifies actual interaction and processing."
    },
    {
      "skill": "contrast-master",
      "note": "Actual VoiceOver/NVDA speech, user-selected OS contrast palette and hardware touch were not tested."
    },
    {
      "skill": "contrast-master",
      "note": "Contrast evidence: contrast-results.json; visual states: visual-results.json."
    },
    {
      "skill": "forms-specialist",
      "note": "Runtime used an isolated current-source DOM fixture with the analyzer/sample boundaries mocked; no API authentication or writes."
    },
    {
      "skill": "forms-specialist",
      "note": "Actual VoiceOver/NVDA speech was not tested."
    },
    {
      "skill": "forms-specialist",
      "note": "Detailed runtime evidence: /tmp/sullivan-t3-work/review/forms-keyboard-runtime.json."
    },
    {
      "skill": "forms-specialist",
      "note": "Initial minor review-summary finding retained in forms-specialist-initial.json; corrected in current source and isolated runtime still passes."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Runtime used an isolated current-source DOM fixture with the analyzer/sample boundaries mocked; no API authentication or writes."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Actual VoiceOver/NVDA speech was not tested."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Detailed runtime evidence: /tmp/sullivan-t3-work/review/forms-keyboard-runtime.json."
    },
    {
      "skill": "live-region-controller",
      "note": "Current-source Chrome fixture checks passed without authentication or backend mutation."
    },
    {
      "skill": "live-region-controller",
      "note": "Native file-picker speech and VoiceOver/NVDA actual utterances were not heard."
    },
    {
      "skill": "live-region-controller",
      "note": "Parent separately validates original progress/success/error announcement behavior through the real local analyzer flow."
    },
    {
      "skill": "live-region-controller",
      "note": "Runtime evidence: /tmp/sullivan-t3-work/review/aria-live-runtime.json."
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
  "checks": 40,
  "generated": "2026-11-04",
  "template": "web"
}
```
