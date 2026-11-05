# Web Accessibility Audit

An audit of web content, run on 2026-11-04. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-04 |
| Scope | 23 items |
| Skills run | alt-text-headings, aria-specialist, contrast-master, forms-specialist, keyboard-navigator, live-region-controller |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 34 |

Audited:

- `apps/web/app.js:180`
- `apps/web/app.js:276`
- `apps/web/guardian-design.css`
- `apps/web/guide/guide.js`
- `apps/web/guide/index.html`
- `apps/web/index.html`
- `apps/web/index.html:162`
- `apps/web/intro.css`
- `apps/web/intro/img/guardian-assign.png`
- `apps/web/intro/img/guardian-prepare-step2.png`
- `apps/web/intro/img/guardian-prepare-step3.png`
- `apps/web/intro/img/guardian-prepare.png`
- `apps/web/intro/img/guardian-review.png`
- `apps/web/intro/img/guardian-settings.png`
- `apps/web/intro/img/guardian-student.png`
- `apps/web/intro/index.html`
- `apps/web/role-portal.js`
- `apps/web/role-portal.js:326`
- `apps/web/workspace-design.css`
- `scripts/verify_keyboard_navigation.py`
- `scripts/verify_keyboard_navigation.py:27`
- `scripts/verify_roles_browser.py`
- `scripts/verify_roles_browser.py:81`

## Executive summary

Pass. No critical or serious findings.

The headline numbers for this run.

| Measure | Value |
|---|---|
| Score | 97 out of 100 |
| Grade | A |
| Findings | 3 |
| Blocking (critical plus serious) | 0 |
| Verdict | Pass |

## Severity breakdown

Counts by severity, highest impact first.

| Severity | Count | What it means |
|---|---:|---|
| critical | 0 | Blocks a person from completing the task |
| serious | 0 | Major barrier with a difficult workaround |
| moderate | 2 | Real friction, workaround exists |
| minor | 1 | Noticeable but rarely blocking |

## Findings

3 findings, ordered by severity then by rule.

### Moderate (2)

Each row names the rule, the criterion it fails, where it is, and what to change.

| Rule | WCAG | Location | Problem | Fix |
|---|---|---|---|---|
| `GUIDE-CAPTURE-OVERLAY` | n/a | apps/web/guide/index.html:80 | The refreshed review screenshot permanently embeds the assignment bar over the first entries of both lower review cards. | Recapture guardian-review.png with the fixed assignment bar outside the review-card capture or temporarily hidden for capture; verify all four cards and their first entries remain visible. Update dimensions if changed. |
| `LIVE-STALE-401-SESSION` | n/a | apps/web/role-portal.js:17 | A stale guardian progress401 clears a newly authenticated student’s UI session and moves focus to login even though the student remains authenticated. | Capture an authentication generation or requesting user identity before fetch; process401 by signing out only if that generation is still current. Abort or invalidate pending progress requests on role changes. Test an old guardian401 after student login and a current-session401. |

### Minor (1)

Each row names the rule, the criterion it fails, where it is, and what to change.

| Rule | WCAG | Location | Problem | Fix |
|---|---|---|---|---|
| `ARIA-STUDENT-IDENTITY` | n/a | apps/web/role-portal.js:201 | Students sharing a display name receive identical roster headings and disclosure descriptions, leaving guardians unable to distinguish their accounts. | Use a human-readable unique identity such as `${s.name} (${s.username})` in each roster h3, keeping summaries/settings links described by that h3; use the same identity in progress status strings. Add a duplicate-name regression case. |

## Remediation priorities

The remaining 3 moderate and minor findings can follow in normal work.

## What passed

31 checks ran and found nothing.

- A held successful progress response after roster replacement populated neither the detached disclosure nor its replacement.
- Actual link and synthetic-file submissions reached browser-intercepted analysis boundaries with the intended visible source; no request reached the analysis API/provider.
- All 12 directed switches from the four starting states to link/file/sample agreed with visible selection and FormData: sample clears media/materials; file clears URL; link clears video; switches reset consent.
- All ten guide image width/height attributes exactly match decoded natural dimensions; all guide images loaded, retain meaningful alternative text and functional full-size image links.
- All ten guide images decoded successfully and retained nonempty alt text and named image links; same-hash navigation reopened step4 and focused its disclosure.
- All tested keyboard focus indicators remained visible 4px outlines with minimum measured ring/background contrast 6.24:1.
- At published HEAD 312a607b330f2d1aef0311b2477cc54db6b3a478, file→link→file→sample source changes completed without recursion or page errors; source buttons exposed the selected pressed state and inactive sources/consent were cleared.
- Clearing a selected video while retaining text produced materials-only mode with disabled/unchecked consent, omitted consent in FormData and correct rebuilt review.
- Editing URL, replacing video and replacing materials after returning from step 3 rebuilt review with the replacement values (3 cases).
- File+materials → sample cleared input selections and opened the explicitly labeled deterministic sample without an analysis request.
- Forward/back and reopened wizard transitions focused their current step headings; selected source buttons remained consistent with visible source controls.
- Fresh audit of HEAD 312a607: 48 current runtime view/size checks covering intro, fully expanded guide, expanded guardian dashboard, all three sample wizard steps and all six results panels found no text contrast or horizontal-overflow failures.
- Fully expanded guide and current guardian views retain a single visible h1 and orderly heading structure across 320/390/1280 and the 200% desktop layout check.
- Guide bulk expansion exposed its status and matching expanded panel states; refreshed images are outside live regions.
- Materials-only TXT completed actual deterministic local processing and the uploaded text appeared in snapshot.passage; no video-analysis request occurred.
- Missing consent focused the consent checkbox with aria-invalid and wizard-error-2 association; missing code focused its input; missing rights focused the step-3 checkbox; empty link focused video-url.
- Missing consent, code and rights were rejected in the relevant step; empty link focused video-url before any analysis request.
- Previous GUIDE-STALE-SCREENSHOTS resolved: visually inspected all seven refreshed guardian PNGs; final wizard steps 1/3,2/3,3/3 match the three screenshots, captions and alternative text at guide/index.html:73.
- Previous PROJECT-TEXT-018 resolved: all 39 visible .concept-meta b/.concept-meta time/.sentence > em labels compute to 18px at 320/390/1280 and 200% desktop layout equivalent; workspace-design.css:183 now includes b,time,em.
- Published 312a607 P1 fix remains closed: link+materials, file+materials, materials-only and sample drafts preserved source, values, consent and review through wizard back/next and breadcrumb home/reopen (4 cases).
- Reviewed durable predecessor expectations and current wizard navigation in original keyboard/browser scripts; the formerly stale source selectors now explicitly target buttons.
- Reviewed original durable browser regression: it traverses current wizard steps, waits for the settled home dashboard, asserts link+text restoration, visible consent, review/FormData agreement and inactive link/consent clearing.
- Sample screenshots and explanatory text continue to identify prepared results and do not claim new video analysis.
- Seven refreshed guardian images retain the existing accessible palette; no new contrast regression found.
- Source switching cleared inactive values and removed disabled text-only consent from submission without moving focus onto a hidden source control.
- Student-name prefixes remain present in concurrent loading, empty, and error status messages; messages stay polite persistent status nodes.
- The refreshed review heading now matches the current “강의 후 화면 정보 복습” runtime heading, and assignment/settings/student-creation captures match their current controls.
- Updated guide had no broken aria-controls, aria-labelledby, or aria-describedby references; all eight expanded states matched panel visibility.
- Wizard Enter/Space actions remained operable across source selection, previous/next, home/reopen and review submission in the focused matrix.
- Wizard review focused #wizard-title-3 and described the active text-only material source after link removal.
- Wizard source clearing and nested input/change events produced coherent final source/consent state and no page errors.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **forms-specialist**: Verdict: no new reproducible form, source-state, contract or safety defect found in this focused 27-case review at HEAD 312a607. Evidence: /tmp/reaudit-312a607/matrix-results.json; executable reproduction: /tmp/reaudit-312a607/matrix.cjs.
- **forms-specialist**: Chrome/156.0.8078.80 with Puppeteer at 1280×900. A private server on port 8892 used disposable TemporaryDirectory account/usage databases only. Provider configuration removed; external traffic blocked. Health was browser-mocked only for two submission checks, and both video analysis endpoints were intercepted before network execution. Video inputs were synthetic text fixtures, not user media.
- **forms-specialist**: An initial harness assertion read nonexistent snapshot.passage_document, so its TXT verification failed after 25 passing cases. Corrected the harness to snapshot.passage and reran the entire matrix: all 27 passed; no browser errors.
- **forms-specialist**: Changes after step 3 were exercised by returning to step 2 and editing the actual source controls, matching the available user flow. Arbitrary scripted mutations of hidden inputs are outside the UI contract.
- **forms-specialist**: No product/test edits. The full original browser scripts were source-reviewed here, not rerun by this specialist; the parent separately reported all three originals passing. Previously documented baseline late-cancel focus behavior was not presented as new.
- **keyboard-navigator**: Verdict: no new reproducible keyboard defect found in the latest source-state fix. Shared focused evidence: /tmp/reaudit-312a607/matrix-results.json (27/27 passing).
- **keyboard-navigator**: The matrix intentionally focuses a control before Enter/Space to isolate transition behavior; it does not claim a fresh full-site Tab-order or screen-reader speech audit. The parent separately reported the original three browser suites passing.
- **keyboard-navigator**: Known late-cancel focus loss in the baseline analysis-finishing delay remains previously documented, outside this latest-fix review and not a new finding.
- **keyboard-navigator**: Read-only review at published HEAD 312a607; disposable databases only; external/provider traffic blocked. No product edits.
- **aria-specialist**: The duplicate-name case is a residual T5 identity gap, not a newly introduced regression in the latest fix. This is recorded outside a specific WCAG failure because the labels are valid but insufficiently distinct for the supported account model.
- **aria-specialist**: Actual VoiceOver/NVDA was unavailable; evidence is browser DOM, keyboard focus, and Chrome AX data. No speech output is claimed.
- **aria-specialist**: Used isolated temporary SQLite, disposable accounts on8893, synthetic files, mocked responses, and blocked nonlocal requests. No product edits or private databases.
- **aria-specialist**: Committed browser verification covers source reset/review/FormData cases at scripts/verify_roles_browser.py:81-102, but contains no progress duplicate-name or delayed-progress/auth-switch assertion.
- **live-region-controller**: The401 behavior originates in the unchanged generic request helper and is exposed by the newly added asynchronous T5 progress path; it was not introduced by the latest student-name/source-reset fix.
- **live-region-controller**: Duplicate display-name progress messages remain ambiguous; the shared identity defect is reported once in aria-specialist.json.
- **live-region-controller**: Known baseline sample-assignment loading silence, late-cancel behavior, and stale URL labels were excluded from new findings.
- **live-region-controller**: Actual VoiceOver/NVDA was unavailable. Verification uses real browser DOM/focus/AX, disposable local accounts, held mock responses, and no provider calls.
- **live-region-controller**: Evidence: /tmp/reaudit-312a607/aria-live-results.json and /tmp/reaudit-312a607/stale401-results.json. Source assertions in committed browser tests do not exercise stale progress401 after role changes.
- **contrast-master**: Evidence: /tmp/reaudit-312a607/evidence.json and concept-labels-390.png. Chrome 156.0.8078.80; Puppeteer 25.16.0; 2026-11-05.
- **contrast-master**: 200% was checked using its desktop layout equivalent: 1280x900 physical pixels represented by 640x450 CSS pixels at deviceScaleFactor 2. Browser toolbar zoom itself was not automated.
- **contrast-master**: Disposable API on 127.0.0.1:8894 used temporary account databases; external requests were blocked and no provider/private-database access occurred.
- **contrast-master**: Reports contain new regressions only; no product edits.
- **alt-text-headings**: P2 screenshot-capture defect only. This is not an observed runtime focus-blocking regression or a proven WCAG alternative-text failure; guide instructions remain available as real text.
- **alt-text-headings**: Fresh evidence: /tmp/reaudit-312a607/evidence.json and guide-review-image-390.png. No historical audit conclusion was used as current proof.
- **alt-text-headings**: No product files edited.

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
    "apps/web/app.js:180",
    "apps/web/app.js:276",
    "apps/web/guardian-design.css",
    "apps/web/guide/guide.js",
    "apps/web/guide/index.html",
    "apps/web/index.html",
    "apps/web/index.html:162",
    "apps/web/intro.css",
    "apps/web/intro/img/guardian-assign.png",
    "apps/web/intro/img/guardian-prepare-step2.png",
    "apps/web/intro/img/guardian-prepare-step3.png",
    "apps/web/intro/img/guardian-prepare.png",
    "apps/web/intro/img/guardian-review.png",
    "apps/web/intro/img/guardian-settings.png",
    "apps/web/intro/img/guardian-student.png",
    "apps/web/intro/index.html",
    "apps/web/role-portal.js",
    "apps/web/role-portal.js:326",
    "apps/web/workspace-design.css",
    "scripts/verify_keyboard_navigation.py",
    "scripts/verify_keyboard_navigation.py:27",
    "scripts/verify_roles_browser.py",
    "scripts/verify_roles_browser.py:81"
  ],
  "findings": [
    {
      "rule": "GUIDE-CAPTURE-OVERLAY",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/web/guide/index.html:80",
      "summary": "The refreshed review screenshot permanently embeds the assignment bar over the first entries of both lower review cards.",
      "fix": "Recapture guardian-review.png with the fixed assignment bar outside the review-card capture or temporarily hidden for capture; verify all four cards and their first entries remain visible. Update dimensions if changed.",
      "evidence": "In the 962×1240 guardian-review.png, the white assignment bar spans approximately y820–900 and masks the first entries beneath “강사가 강조한 문장” and “다시 볼 핵심 구간”. Also visible in /tmp/reaudit-312a607/guide-review-image-390.png.",
      "component": "Guide step 5 illustrative screenshot",
      "foundBy": [
        "alt-text-headings"
      ]
    },
    {
      "rule": "LIVE-STALE-401-SESSION",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/web/role-portal.js:17",
      "summary": "A stale guardian progress401 clears a newly authenticated student’s UI session and moves focus to login even though the student remains authenticated.",
      "fix": "Capture an authentication generation or requesting user identity before fetch; process401 by signing out only if that generation is still current. Abort or invalidate pending progress requests on role changes. Test an old guardian401 after student login and a current-session401.",
      "evidence": "Hold guardian GET /students/:id/progress, log out, log in as student via UI, wait for loaded home and enabled login submit, then return held401. Before: student, focus student-list-open; after: user=null, signed-out, focus login-role-student. /local/me returns200 for the same student both times; no page errors. /tmp/reaudit-312a607/stale401-results.json",
      "component": "guardian-learning-progress",
      "foundBy": [
        "live-region-controller"
      ]
    },
    {
      "rule": "ARIA-STUDENT-IDENTITY",
      "wcag": "n/a",
      "severity": "minor",
      "location": "apps/web/role-portal.js:201",
      "summary": "Students sharing a display name receive identical roster headings and disclosure descriptions, leaving guardians unable to distinguish their accounts.",
      "fix": "Use a human-readable unique identity such as `${s.name} (${s.username})` in each roster h3, keeping summaries/settings links described by that h3; use the same identity in progress status strings. Add a duplicate-name regression case.",
      "evidence": "Created distinct accounts audit.student.a and audit.student.b, both named 동명이인. Chrome AX shows both articles named 동명이인 and both 학습 현황 disclosures described only as 동명이인; neither roster card contains its username. Concurrent status messages also prefix only 동명이인. /tmp/reaudit-312a607/aria-live-results.json",
      "component": "guardian-student",
      "confidence": "medium",
      "foundBy": [
        "aria-specialist"
      ]
    }
  ],
  "passed": [
    "A held successful progress response after roster replacement populated neither the detached disclosure nor its replacement.",
    "Actual link and synthetic-file submissions reached browser-intercepted analysis boundaries with the intended visible source; no request reached the analysis API/provider.",
    "All 12 directed switches from the four starting states to link/file/sample agreed with visible selection and FormData: sample clears media/materials; file clears URL; link clears video; switches reset consent.",
    "All ten guide image width/height attributes exactly match decoded natural dimensions; all guide images loaded, retain meaningful alternative text and functional full-size image links.",
    "All ten guide images decoded successfully and retained nonempty alt text and named image links; same-hash navigation reopened step4 and focused its disclosure.",
    "All tested keyboard focus indicators remained visible 4px outlines with minimum measured ring/background contrast 6.24:1.",
    "At published HEAD 312a607b330f2d1aef0311b2477cc54db6b3a478, file→link→file→sample source changes completed without recursion or page errors; source buttons exposed the selected pressed state and inactive sources/consent were cleared.",
    "Clearing a selected video while retaining text produced materials-only mode with disabled/unchecked consent, omitted consent in FormData and correct rebuilt review.",
    "Editing URL, replacing video and replacing materials after returning from step 3 rebuilt review with the replacement values (3 cases).",
    "File+materials → sample cleared input selections and opened the explicitly labeled deterministic sample without an analysis request.",
    "Forward/back and reopened wizard transitions focused their current step headings; selected source buttons remained consistent with visible source controls.",
    "Fresh audit of HEAD 312a607: 48 current runtime view/size checks covering intro, fully expanded guide, expanded guardian dashboard, all three sample wizard steps and all six results panels found no text contrast or horizontal-overflow failures.",
    "Fully expanded guide and current guardian views retain a single visible h1 and orderly heading structure across 320/390/1280 and the 200% desktop layout check.",
    "Guide bulk expansion exposed its status and matching expanded panel states; refreshed images are outside live regions.",
    "Materials-only TXT completed actual deterministic local processing and the uploaded text appeared in snapshot.passage; no video-analysis request occurred.",
    "Missing consent focused the consent checkbox with aria-invalid and wizard-error-2 association; missing code focused its input; missing rights focused the step-3 checkbox; empty link focused video-url.",
    "Missing consent, code and rights were rejected in the relevant step; empty link focused video-url before any analysis request.",
    "Previous GUIDE-STALE-SCREENSHOTS resolved: visually inspected all seven refreshed guardian PNGs; final wizard steps 1/3,2/3,3/3 match the three screenshots, captions and alternative text at guide/index.html:73.",
    "Previous PROJECT-TEXT-018 resolved: all 39 visible .concept-meta b/.concept-meta time/.sentence > em labels compute to 18px at 320/390/1280 and 200% desktop layout equivalent; workspace-design.css:183 now includes b,time,em.",
    "Published 312a607 P1 fix remains closed: link+materials, file+materials, materials-only and sample drafts preserved source, values, consent and review through wizard back/next and breadcrumb home/reopen (4 cases).",
    "Reviewed durable predecessor expectations and current wizard navigation in original keyboard/browser scripts; the formerly stale source selectors now explicitly target buttons.",
    "Reviewed original durable browser regression: it traverses current wizard steps, waits for the settled home dashboard, asserts link+text restoration, visible consent, review/FormData agreement and inactive link/consent clearing.",
    "Sample screenshots and explanatory text continue to identify prepared results and do not claim new video analysis.",
    "Seven refreshed guardian images retain the existing accessible palette; no new contrast regression found.",
    "Source switching cleared inactive values and removed disabled text-only consent from submission without moving focus onto a hidden source control.",
    "Student-name prefixes remain present in concurrent loading, empty, and error status messages; messages stay polite persistent status nodes.",
    "The refreshed review heading now matches the current “강의 후 화면 정보 복습” runtime heading, and assignment/settings/student-creation captures match their current controls.",
    "Updated guide had no broken aria-controls, aria-labelledby, or aria-describedby references; all eight expanded states matched panel visibility.",
    "Wizard Enter/Space actions remained operable across source selection, previous/next, home/reopen and review submission in the focused matrix.",
    "Wizard review focused #wizard-title-3 and described the active text-only material source after link removal.",
    "Wizard source clearing and nested input/change events produced coherent final source/consent state and no page errors."
  ],
  "notes": [
    {
      "skill": "forms-specialist",
      "note": "Verdict: no new reproducible form, source-state, contract or safety defect found in this focused 27-case review at HEAD 312a607. Evidence: /tmp/reaudit-312a607/matrix-results.json; executable reproduction: /tmp/reaudit-312a607/matrix.cjs."
    },
    {
      "skill": "forms-specialist",
      "note": "Chrome/156.0.8078.80 with Puppeteer at 1280×900. A private server on port 8892 used disposable TemporaryDirectory account/usage databases only. Provider configuration removed; external traffic blocked. Health was browser-mocked only for two submission checks, and both video analysis endpoints were intercepted before network execution. Video inputs were synthetic text fixtures, not user media."
    },
    {
      "skill": "forms-specialist",
      "note": "An initial harness assertion read nonexistent snapshot.passage_document, so its TXT verification failed after 25 passing cases. Corrected the harness to snapshot.passage and reran the entire matrix: all 27 passed; no browser errors."
    },
    {
      "skill": "forms-specialist",
      "note": "Changes after step 3 were exercised by returning to step 2 and editing the actual source controls, matching the available user flow. Arbitrary scripted mutations of hidden inputs are outside the UI contract."
    },
    {
      "skill": "forms-specialist",
      "note": "No product/test edits. The full original browser scripts were source-reviewed here, not rerun by this specialist; the parent separately reported all three originals passing. Previously documented baseline late-cancel focus behavior was not presented as new."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Verdict: no new reproducible keyboard defect found in the latest source-state fix. Shared focused evidence: /tmp/reaudit-312a607/matrix-results.json (27/27 passing)."
    },
    {
      "skill": "keyboard-navigator",
      "note": "The matrix intentionally focuses a control before Enter/Space to isolate transition behavior; it does not claim a fresh full-site Tab-order or screen-reader speech audit. The parent separately reported the original three browser suites passing."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Known late-cancel focus loss in the baseline analysis-finishing delay remains previously documented, outside this latest-fix review and not a new finding."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Read-only review at published HEAD 312a607; disposable databases only; external/provider traffic blocked. No product edits."
    },
    {
      "skill": "aria-specialist",
      "note": "The duplicate-name case is a residual T5 identity gap, not a newly introduced regression in the latest fix. This is recorded outside a specific WCAG failure because the labels are valid but insufficiently distinct for the supported account model."
    },
    {
      "skill": "aria-specialist",
      "note": "Actual VoiceOver/NVDA was unavailable; evidence is browser DOM, keyboard focus, and Chrome AX data. No speech output is claimed."
    },
    {
      "skill": "aria-specialist",
      "note": "Used isolated temporary SQLite, disposable accounts on8893, synthetic files, mocked responses, and blocked nonlocal requests. No product edits or private databases."
    },
    {
      "skill": "aria-specialist",
      "note": "Committed browser verification covers source reset/review/FormData cases at scripts/verify_roles_browser.py:81-102, but contains no progress duplicate-name or delayed-progress/auth-switch assertion."
    },
    {
      "skill": "live-region-controller",
      "note": "The401 behavior originates in the unchanged generic request helper and is exposed by the newly added asynchronous T5 progress path; it was not introduced by the latest student-name/source-reset fix."
    },
    {
      "skill": "live-region-controller",
      "note": "Duplicate display-name progress messages remain ambiguous; the shared identity defect is reported once in aria-specialist.json."
    },
    {
      "skill": "live-region-controller",
      "note": "Known baseline sample-assignment loading silence, late-cancel behavior, and stale URL labels were excluded from new findings."
    },
    {
      "skill": "live-region-controller",
      "note": "Actual VoiceOver/NVDA was unavailable. Verification uses real browser DOM/focus/AX, disposable local accounts, held mock responses, and no provider calls."
    },
    {
      "skill": "live-region-controller",
      "note": "Evidence: /tmp/reaudit-312a607/aria-live-results.json and /tmp/reaudit-312a607/stale401-results.json. Source assertions in committed browser tests do not exercise stale progress401 after role changes."
    },
    {
      "skill": "contrast-master",
      "note": "Evidence: /tmp/reaudit-312a607/evidence.json and concept-labels-390.png. Chrome 156.0.8078.80; Puppeteer 25.16.0; 2026-11-05."
    },
    {
      "skill": "contrast-master",
      "note": "200% was checked using its desktop layout equivalent: 1280x900 physical pixels represented by 640x450 CSS pixels at deviceScaleFactor 2. Browser toolbar zoom itself was not automated."
    },
    {
      "skill": "contrast-master",
      "note": "Disposable API on 127.0.0.1:8894 used temporary account databases; external requests were blocked and no provider/private-database access occurred."
    },
    {
      "skill": "contrast-master",
      "note": "Reports contain new regressions only; no product edits."
    },
    {
      "skill": "alt-text-headings",
      "note": "P2 screenshot-capture defect only. This is not an observed runtime focus-blocking regression or a proven WCAG alternative-text failure; guide instructions remain available as real text."
    },
    {
      "skill": "alt-text-headings",
      "note": "Fresh evidence: /tmp/reaudit-312a607/evidence.json and guide-review-image-390.png. No historical audit conclusion was used as current proof."
    },
    {
      "skill": "alt-text-headings",
      "note": "No product files edited."
    }
  ],
  "counts": {
    "critical": 0,
    "serious": 0,
    "moderate": 2,
    "minor": 1
  },
  "components": [],
  "score": 97,
  "grade": "A",
  "penalty": 4.7,
  "checks": 34,
  "generated": "2026-11-04",
  "template": "web"
}
```
