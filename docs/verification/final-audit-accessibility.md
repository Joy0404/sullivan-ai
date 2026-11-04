# Web Accessibility Audit

An audit of web content, run on 2026-11-04. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-04 |
| Scope | 12 items |
| Skills run | alt-text-headings, aria-specialist, contrast-master, forms-specialist, keyboard-navigator, live-region-controller |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 39 |

Audited:

- `apps/web/guardian-design.css`
- `apps/web/guide/guide.js`
- `apps/web/guide/index.html`
- `apps/web/index.html`
- `apps/web/index.html:162`
- `apps/web/index.html:40`
- `apps/web/index.html:94`
- `apps/web/intro.css`
- `apps/web/intro/index.html`
- `apps/web/role-portal.js`
- `apps/web/role-portal.js:326`
- `apps/web/workspace-design.css`

## Executive summary

Fail. Critical or serious findings must be fixed before this ships.

The headline numbers for this run.

| Measure | Value |
|---|---|
| Score | 93 out of 100 |
| Grade | A |
| Findings | 6 |
| Blocking (critical plus serious) | 1 |
| Verdict | Fail |

## Severity breakdown

Counts by severity, highest impact first.

| Severity | Count | What it means |
|---|---:|---|
| critical | 0 | Blocks a person from completing the task |
| serious | 1 | Major barrier with a difficult workaround |
| moderate | 4 | Real friction, workaround exists |
| minor | 1 | Noticeable but rarely blocking |

## Findings

6 findings, ordered by severity then by rule.

### Serious (1)

Each row names the rule, the criterion it fails, where it is, and what to change.

| Rule | WCAG | Location | Problem | Fix |
|---|---|---|---|---|
| `FORMS-WIZARD-RESET-SOURCE` | n/a | apps/web/role-portal.js:379 | Returning to preparation changes a link-plus-materials draft to file mode while retaining and submitting the now-hidden video link. | Restore the explicitly selected source on wizard-reset; when inferring, check video files, then video_url, then materials. Exclude inactive source values from submission and add a regression test that review, consent visibility, and submitted source agree after home/reopen. |

### Moderate (4)

Each row names the rule, the criterion it fails, where it is, and what to change.

| Rule | WCAG | Location | Problem | Fix |
|---|---|---|---|---|
| `FORMS-WIZARD-HARNESS-STALE` | n/a | scripts/verify_roles_browser.py:100 | The roles browser check still submits the former one-page form without traversing the new three-step wizard. | Advance from step 1, explicitly select the file/material source in step 2, attach materials, advance to step 3, confirm rights, then submit. Assert the current step heading and retain overlay cancellation/focus coverage. |
| `GUIDE-STALE-SCREENSHOTS` | n/a | apps/web/guide/index.html:73 | The guide still illustrates pre-T3/T4 screens while its text instructs guardians to use the final three-step wizard and renamed review UI. | Recapture guardian-prepare.png from the current three-step sample wizard, provide the step views needed to explain navigation, and refresh guardian-review.png after T4. Keep alt text, captions and surrounding instructions aligned with those final screens. |
| `KEYBOARD-HARNESS-PREDECESSOR-STALE` | n/a | scripts/verify_keyboard_navigation.py:29 | The keyboard browser check hard-codes a pre-redesign predecessor for the preparation button and fails before later regression coverage runs. | Calculate or assert the predecessor from the current guardian DOM/tab order for both Shift-alone and Shift+Tab, then retain the editing, capitalization and assignment assertions after that check. |
| `LIVE-PROGRESS-STUDENT-CONTEXT` | 4.1.3 AA | apps/web/role-portal.js:209 | Concurrent student progress announcements omit student identity, so screen-reader users cannot tell whose request completed or failed. | Include s.name in every loading, success, empty, and error status string, for example `${s.name} 학생의 학습 현황을 불러오지 못했습니다. 접었다가 다시 펼치면 재시도합니다.` Keep the existing persistent role=status node and polite behavior. |

### Minor (1)

Each row names the rule, the criterion it fails, where it is, and what to change.

| Rule | WCAG | Location | Problem | Fix |
|---|---|---|---|---|
| `PROJECT-TEXT-018` | n/a | apps/web/workspace-design.css:183 | Guardian concept categories, timestamps and sentence emphasis remain 14px, below the project’s required 18px text size. | Extend the guardian-only workspace typography rule to .concept-meta b, .concept-meta time and .sentence > em (or include b, time and em) with font-size:1.125rem; preserve student styling. |

## Remediation priorities

The 1 blocking finding:

1. `FORMS-WIZARD-RESET-SOURCE` at apps/web/role-portal.js:379. Restore the explicitly selected source on wizard-reset; when inferring, check video files, then video_url, then materials. Exclude inactive source values from submission and add a regression test that review, consent visibility, and submitted source agree after home/reopen.

The remaining 5 moderate and minor findings can follow in normal work.

## What passed

33 checks ran and found nothing.

- All tested interactive controls have visible 4px keyboard focus outlines; ring #8c4700 contrasted with white/canvas/amber-soft backgrounds. Detailed computed styles in visual-focus-evidence.json.
- Each page uses lang=ko, one main landmark, a skip link, and distinct labels for multiple navigation landmarks; decorative inline SVGs are aria-hidden.
- Early analysis cancellation via Escape returned focus to #wizard-submit.
- Explicit switch to sample clears selected video, link, supplemental materials and consent before opening the visibly labeled deterministic sample.
- Guardian flow and intro/guide button elements meet 48px minimum height; 24px native checkbox visuals have associated text labels.
- Guardian result-page Tab sweeps at 1280×900 and 390×900 found no focused control entirely covered by the fixed assignment bar and no missing focus outline in the inspected tab sequence.
- Guide bulk expansion updated the existing #guide-status polite region exactly once; individual and hash disclosure changes exposed state through the focused button.
- Guide deep links open the corresponding disclosure; same-hash navigation reopens a collapsed disclosure; individual and expand-all/collapse-all buttons expose correct expanded states.
- Guide hash navigation reopened a collapsed current step and focused its disclosure button; aria-expanded matched panel visibility.
- Guide native button disclosures support Enter/Space, preserve focus, expose aria-expanded, reopen for same-hash links and operate through expand-all/collapse-all.
- Guide toggle-all aria-controls resolved to all eight panel IDs and all aria-expanded values tracked bulk expansion.
- HEAD 48b3ac10c459b53076294376122e63d235dd1dee: runtime reference scan found no missing aria-labelledby, aria-describedby, or aria-controls targets.
- Independent headless Chrome/Puppeteer runtime on HEAD 48b3ac1 using port 8894 and disposable accounts; no provider requests permitted.
- Intro and expanded guide have one visible h1 and sequential h2/h3 outlines; current guardian dashboard/wizard/result views also expose one visible h1 with orderly subheadings.
- Intro, guide, guardian dashboard, wizard steps and result panels reflow without measured horizontal overflow at 320, 390 and 1280 CSS px.
- Intro/guide explicitly label prepared sample results, state no new video was analyzed, identify prototype/user-test status, and qualify real analysis with configuration and consent requirements.
- Isolated keyboard-only flow completed guardian setup → student creation → sample preview → student selection → publish; feedback and focus were checked after each transition.
- Keyboard alone completed first guardian setup, student creation, sample preview and final assignment using Tab/Enter/Space; all required controls were reachable.
- Measured visible text foreground/background combinations in intro, fully expanded guide, guardian dashboard, all wizard steps and all six result panels: no WCAG 1.4.3 contrast failures.
- No missing alt attributes, unverifiable user counts, fabricated outcomes or unqualified VoiceOver/NVDA certification claims found.
- Reduced-motion preference produced no visible animations or transitions in guardian results.
- T4 guardian navigation terms changed only in guardian mode, restored on logout, and remained original after student authentication.
- T4 opening a sample focused #guardian-result-title once; the result summary was hidden after logout and in student mode.
- T4 sample opening focused the result heading and issued one separate sample-source status; no duplicate result-heading focus was observed.
- T5 HTTP401 during progress fetch returned focus to the login choice without announcing a stale progress error.
- T5 a response released after loadGuardian replaced the roster did not populate the detached disclosure or the replacement.
- T5 a response released after logout did not populate visible or hidden progress content and did not steal focus from #login-role-student.
- T5 native details disclosures expose their expanded state; summaries describe their student through the matching h3 ID.
- T5 opening a disclosure produced one visible polite loading mutation; a delayed successful response produced one visible polite completion mutation.
- Visually inspected all 12 unique local screenshots referenced by intro/guide; all images have meaningful alt text, and guide image links have functional accessible names.
- Wizard forward/back navigation focuses the current heading; invalid URL and missing-consent errors focus their associated inputs.
- Wizard invalid URL and missing consent return to step 2, focus the offending input, set aria-invalid and associate the visible step error with aria-describedby.
- Wizard previous/next preserves entered values; each normal transition focuses its step heading and updates aria-current=step.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **forms-specialist**: Audit at HEAD 48b3ac1 on 2026-11-05, Chrome/156.0.8078.80 with Puppeteer. Server port 8892 used only disposable TemporaryDirectory accounts and usage databases; API keys/analyzer settings removed. External requests blocked. The unexpected link submission was captured and stopped by browser interception; real analysis was never invoked.
- **forms-specialist**: Reproduction artifacts: /tmp/final-wizard-reset-results.json and /tmp/final-wizard-reset.cjs. General keyboard/form exploration: /tmp/final-forms-audit-results.json.
- **forms-specialist**: Baseline edge, not a T3 regression: replacing a selected file or editing a populated link keeps checked analysis consent. The app.js syncAnalysisConsent behavior already existed before T0–T6.
- **forms-specialist**: Baseline edge: logout resets the URL value but leaves #video-link-state text 링크 입력됨 and .ready=true; observed again after login and reopening link source. The reset line and app indicator handling predate T0–T6.
- **forms-specialist**: Baseline markup omitted username format instructions. On current Chrome, entering ab in either login or student creation focuses the field with only 요청한 형식과 일치시키세요.; no aria-describedby explains the allowed characters or 3–60 length. Before T6, the malformed pattern was not enforced; this is not reported as a new implementation defect.
- **keyboard-navigator**: Audit at HEAD 48b3ac1 with Chrome/156.0.8078.80 and Puppeteer against disposable-account server 8892. No production/account database access and no provider calls.
- **keyboard-navigator**: Reproducible baseline defect, not introduced by T0–T6: apps/web/role-portal.js:690 clears state.analysisFocus while #wizard-submit is disabled if cancellation happens during finishAnalysisProgress’s 100%/750ms delay. Materials-only upload → rights check → submit → wait for 100% → Escape resulted in activeElement BODY; next Tab reached footer 실행 정보. Earlier cancellation restored #wizard-submit. Identical focus-restoration logic exists at baseline 36ef70b:527.
- **keyboard-navigator**: Late-cancel proof: /tmp/final-forms-edge-results.json and /tmp/final-forms-edge.cjs. Focus/occlusion sweep: /tmp/final-keyboard-sweep-results.json.
- **keyboard-navigator**: Native screen-reader spoken output was not observed; programmatic focus, relationships, state and DOM announcements were inspected. Product files were not edited.
- **aria-specialist**: Read-only product audit in headless Chrome using Puppeteer, an ephemeral SQLite test server on port 8893, disposable accounts, and a mocked YouTube player; external requests were blocked.
- **aria-specialist**: No VoiceOver or NVDA session was run; findings and passes describe DOM, focus, and Chrome accessibility-tree evidence.
- **aria-specialist**: Evidence: /tmp/sullivan-aria-audit-results.json, /tmp/sullivan-aria-races-results.json, /tmp/sullivan-aria-concurrent-results.json.
- **live-region-controller**: HEAD 48b3ac10c459b53076294376122e63d235dd1dee; Chrome DOM/focus/AX evidence, no VoiceOver or NVDA speech verification. Confidence on concurrent-message interpretation is medium.
- **live-region-controller**: Pre-existing gap, excluded from reskin regressions: #sample-assign-receipt lacks live semantics. Holding POST /local/samples/science/assign for 3 seconds visibly displayed a saving message with no live mutation or focus message until completion; the same markup and assignSample behavior exist in baseline 36ef70b.
- **live-region-controller**: Evidence: /tmp/sullivan-aria-audit-results.json, /tmp/sullivan-aria-races-results.json, /tmp/sullivan-aria-concurrent-results.json. Real providers and actual user data were not accessed.
- **contrast-master**: The 18px finding is a stricter RESKIN_PLAYBOOK section 6 requirement, not a WCAG minimum-font-size failure.
- **contrast-master**: Audit date 2026-11-05; Puppeteer 25.16.0, local Google Chrome; read-only product audit, only disposable account data and audit artifacts created.
- **contrast-master**: Login’s existing 14–16px typography and 44px voice-test control were observed but excluded from findings because the redesign permits only one added login link.
- **alt-text-headings**: Screenshot drift is instructional consistency debt rather than a proven WCAG 1.1.1 failure; existing alt text describes the old images accurately.
- **alt-text-headings**: Current screen runtime evidence: visual-runtime-evidence.json. Current wizard/result screenshots: current-wizard-step1-390.png and current-results-390.png.
- **alt-text-headings**: The app retains a generic Sullivan AI document title across guardian internal views; unique intro and guide titles are present. No WCAG title failure asserted for the single-document workflow.

## Next steps

1. Fix the blocking finding above.
2. Re-run this audit and check the delta section for regressions.
3. Wire the scan into continuous integration so the next regression is caught before review.

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
    "apps/web/guardian-design.css",
    "apps/web/guide/guide.js",
    "apps/web/guide/index.html",
    "apps/web/index.html",
    "apps/web/index.html:162",
    "apps/web/index.html:40",
    "apps/web/index.html:94",
    "apps/web/intro.css",
    "apps/web/intro/index.html",
    "apps/web/role-portal.js",
    "apps/web/role-portal.js:326",
    "apps/web/workspace-design.css"
  ],
  "findings": [
    {
      "rule": "FORMS-WIZARD-RESET-SOURCE",
      "wcag": "n/a",
      "severity": "serious",
      "location": "apps/web/role-portal.js:379",
      "component": "T3 guardian lecture preparation wizard",
      "summary": "Returning to preparation changes a link-plus-materials draft to file mode while retaining and submitting the now-hidden video link.",
      "fix": "Restore the explicitly selected source on wizard-reset; when inferring, check video files, then video_url, then materials. Exclude inactive source values from submission and add a regression test that review, consent visibility, and submitted source agree after home/reopen.",
      "evidence": "Repro: choose link, enter URL, attach TXT, check consent, enter code; breadcrumb home, reopen preparation, Next twice. Source becomes file; URL/consent/code hide; review says 학습자료만 준비. With browser-only mocked configured health, intercepted /video-link body still had the original URL, request_analysis:true and analysis_consent:true. No provider call occurred.",
      "foundBy": [
        "forms-specialist"
      ]
    },
    {
      "rule": "FORMS-WIZARD-HARNESS-STALE",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "scripts/verify_roles_browser.py:100",
      "component": "T3 browser verification",
      "summary": "The roles browser check still submits the former one-page form without traversing the new three-step wizard.",
      "fix": "Advance from step 1, explicitly select the file/material source in step 2, attach materials, advance to step 3, confirm rights, then submit. Assert the current step heading and retain overlay cancellation/focus coverage.",
      "evidence": "Lines 100–110 fill title/materials and press rights/submit directly, then wait for the analysis overlay. They never operate #wizard-next or [data-wizard-source=file]. The parent audit reproduced the original script timing out at the overlay wait; source inspection confirms the stale sequence.",
      "foundBy": [
        "forms-specialist"
      ]
    },
    {
      "rule": "GUIDE-STALE-SCREENSHOTS",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "apps/web/guide/index.html:73",
      "summary": "The guide still illustrates pre-T3/T4 screens while its text instructs guardians to use the final three-step wizard and renamed review UI.",
      "fix": "Recapture guardian-prepare.png from the current three-step sample wizard, provide the step views needed to explain navigation, and refresh guardian-review.png after T4. Keep alt text, captions and surrounding instructions aligned with those final screens.",
      "evidence": "Guide :69 describes steps 1–3, but :73 guardian-prepare.png shows one long form with “선택한 자료 실제 분석” and no step navigation. Current screenshot current-wizard-step1-390.png shows “1/3 단계” and “다음 단계”. At :80 guardian-review.png says “강의 후 접근성 복습”; runtime review1280 says “강의 후 화면 정보 복습”.",
      "component": "Guide steps 4 and 5 screenshots",
      "foundBy": [
        "alt-text-headings"
      ]
    },
    {
      "rule": "KEYBOARD-HARNESS-PREDECESSOR-STALE",
      "wcag": "n/a",
      "severity": "moderate",
      "location": "scripts/verify_keyboard_navigation.py:29",
      "component": "T2 guardian navigation verification",
      "summary": "The keyboard browser check hard-codes a pre-redesign predecessor for the preparation button and fails before later regression coverage runs.",
      "fix": "Calculate or assert the predecessor from the current guardian DOM/tab order for both Shift-alone and Shift+Tab, then retain the editing, capitalization and assignment assertions after that check.",
      "evidence": "Lines 28–31 demand the student-create submit button after both backward gestures from #guardian-prepare. T2 moved guardian sections/controls. The parent audit reproduced this assertion failure; the audited current UI completed student creation and assignment with keyboard alone.",
      "foundBy": [
        "keyboard-navigator"
      ]
    },
    {
      "rule": "LIVE-PROGRESS-STUDENT-CONTEXT",
      "wcag": "4.1.3 AA",
      "severity": "moderate",
      "confidence": "medium",
      "location": "apps/web/role-portal.js:209",
      "summary": "Concurrent student progress announcements omit student identity, so screen-reader users cannot tell whose request completed or failed.",
      "fix": "Include s.name in every loading, success, empty, and error status string, for example `${s.name} 학생의 학습 현황을 불러오지 못했습니다. 접었다가 다시 펼치면 재시도합니다.` Keep the existing persistent role=status node and polite behavior.",
      "evidence": "Reproduced with two disposable students: open both disclosures, hold both GET /progress, focus #guardian-prepare, return first lectures=[] and second HTTP500. Separate unnamed AX status nodes emit only “아직 배정된 강의가 없습니다.” and “학습 현황을 불러오지 못했습니다. 접었다가 다시 펼치면 재시도합니다.” Student identity appears only in ancestor cards. /tmp/sullivan-aria-concurrent-results.json",
      "component": "guardian-learning-progress",
      "foundBy": [
        "live-region-controller"
      ]
    },
    {
      "rule": "PROJECT-TEXT-018",
      "wcag": "n/a",
      "severity": "minor",
      "location": "apps/web/workspace-design.css:183",
      "summary": "Guardian concept categories, timestamps and sentence emphasis remain 14px, below the project’s required 18px text size.",
      "fix": "Extend the guardian-only workspace typography rule to .concept-meta b, .concept-meta time and .sentence > em (or include b, time and em) with font-size:1.125rem; preserve student styling.",
      "evidence": "At 320/390/1280, computed .concept-meta b and time and .sentence > em are 14px. The selector at line 183 omits b/time/em; styles.css:798 and :490 set 0.875rem. Runtime: .a11y-history/final-audit/visual-runtime-evidence.json, passage320/passage390/passage1280.",
      "component": "Guardian core-concept and passage review",
      "foundBy": [
        "contrast-master"
      ]
    }
  ],
  "passed": [
    "All tested interactive controls have visible 4px keyboard focus outlines; ring #8c4700 contrasted with white/canvas/amber-soft backgrounds. Detailed computed styles in visual-focus-evidence.json.",
    "Each page uses lang=ko, one main landmark, a skip link, and distinct labels for multiple navigation landmarks; decorative inline SVGs are aria-hidden.",
    "Early analysis cancellation via Escape returned focus to #wizard-submit.",
    "Explicit switch to sample clears selected video, link, supplemental materials and consent before opening the visibly labeled deterministic sample.",
    "Guardian flow and intro/guide button elements meet 48px minimum height; 24px native checkbox visuals have associated text labels.",
    "Guardian result-page Tab sweeps at 1280×900 and 390×900 found no focused control entirely covered by the fixed assignment bar and no missing focus outline in the inspected tab sequence.",
    "Guide bulk expansion updated the existing #guide-status polite region exactly once; individual and hash disclosure changes exposed state through the focused button.",
    "Guide deep links open the corresponding disclosure; same-hash navigation reopens a collapsed disclosure; individual and expand-all/collapse-all buttons expose correct expanded states.",
    "Guide hash navigation reopened a collapsed current step and focused its disclosure button; aria-expanded matched panel visibility.",
    "Guide native button disclosures support Enter/Space, preserve focus, expose aria-expanded, reopen for same-hash links and operate through expand-all/collapse-all.",
    "Guide toggle-all aria-controls resolved to all eight panel IDs and all aria-expanded values tracked bulk expansion.",
    "HEAD 48b3ac10c459b53076294376122e63d235dd1dee: runtime reference scan found no missing aria-labelledby, aria-describedby, or aria-controls targets.",
    "Independent headless Chrome/Puppeteer runtime on HEAD 48b3ac1 using port 8894 and disposable accounts; no provider requests permitted.",
    "Intro and expanded guide have one visible h1 and sequential h2/h3 outlines; current guardian dashboard/wizard/result views also expose one visible h1 with orderly subheadings.",
    "Intro, guide, guardian dashboard, wizard steps and result panels reflow without measured horizontal overflow at 320, 390 and 1280 CSS px.",
    "Intro/guide explicitly label prepared sample results, state no new video was analyzed, identify prototype/user-test status, and qualify real analysis with configuration and consent requirements.",
    "Isolated keyboard-only flow completed guardian setup → student creation → sample preview → student selection → publish; feedback and focus were checked after each transition.",
    "Keyboard alone completed first guardian setup, student creation, sample preview and final assignment using Tab/Enter/Space; all required controls were reachable.",
    "Measured visible text foreground/background combinations in intro, fully expanded guide, guardian dashboard, all wizard steps and all six result panels: no WCAG 1.4.3 contrast failures.",
    "No missing alt attributes, unverifiable user counts, fabricated outcomes or unqualified VoiceOver/NVDA certification claims found.",
    "Reduced-motion preference produced no visible animations or transitions in guardian results.",
    "T4 guardian navigation terms changed only in guardian mode, restored on logout, and remained original after student authentication.",
    "T4 opening a sample focused #guardian-result-title once; the result summary was hidden after logout and in student mode.",
    "T4 sample opening focused the result heading and issued one separate sample-source status; no duplicate result-heading focus was observed.",
    "T5 HTTP401 during progress fetch returned focus to the login choice without announcing a stale progress error.",
    "T5 a response released after loadGuardian replaced the roster did not populate the detached disclosure or the replacement.",
    "T5 a response released after logout did not populate visible or hidden progress content and did not steal focus from #login-role-student.",
    "T5 native details disclosures expose their expanded state; summaries describe their student through the matching h3 ID.",
    "T5 opening a disclosure produced one visible polite loading mutation; a delayed successful response produced one visible polite completion mutation.",
    "Visually inspected all 12 unique local screenshots referenced by intro/guide; all images have meaningful alt text, and guide image links have functional accessible names.",
    "Wizard forward/back navigation focuses the current heading; invalid URL and missing-consent errors focus their associated inputs.",
    "Wizard invalid URL and missing consent return to step 2, focus the offending input, set aria-invalid and associate the visible step error with aria-describedby.",
    "Wizard previous/next preserves entered values; each normal transition focuses its step heading and updates aria-current=step."
  ],
  "notes": [
    {
      "skill": "forms-specialist",
      "note": "Audit at HEAD 48b3ac1 on 2026-11-05, Chrome/156.0.8078.80 with Puppeteer. Server port 8892 used only disposable TemporaryDirectory accounts and usage databases; API keys/analyzer settings removed. External requests blocked. The unexpected link submission was captured and stopped by browser interception; real analysis was never invoked."
    },
    {
      "skill": "forms-specialist",
      "note": "Reproduction artifacts: /tmp/final-wizard-reset-results.json and /tmp/final-wizard-reset.cjs. General keyboard/form exploration: /tmp/final-forms-audit-results.json."
    },
    {
      "skill": "forms-specialist",
      "note": "Baseline edge, not a T3 regression: replacing a selected file or editing a populated link keeps checked analysis consent. The app.js syncAnalysisConsent behavior already existed before T0–T6."
    },
    {
      "skill": "forms-specialist",
      "note": "Baseline edge: logout resets the URL value but leaves #video-link-state text 링크 입력됨 and .ready=true; observed again after login and reopening link source. The reset line and app indicator handling predate T0–T6."
    },
    {
      "skill": "forms-specialist",
      "note": "Baseline markup omitted username format instructions. On current Chrome, entering ab in either login or student creation focuses the field with only 요청한 형식과 일치시키세요.; no aria-describedby explains the allowed characters or 3–60 length. Before T6, the malformed pattern was not enforced; this is not reported as a new implementation defect."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Audit at HEAD 48b3ac1 with Chrome/156.0.8078.80 and Puppeteer against disposable-account server 8892. No production/account database access and no provider calls."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Reproducible baseline defect, not introduced by T0–T6: apps/web/role-portal.js:690 clears state.analysisFocus while #wizard-submit is disabled if cancellation happens during finishAnalysisProgress’s 100%/750ms delay. Materials-only upload → rights check → submit → wait for 100% → Escape resulted in activeElement BODY; next Tab reached footer 실행 정보. Earlier cancellation restored #wizard-submit. Identical focus-restoration logic exists at baseline 36ef70b:527."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Late-cancel proof: /tmp/final-forms-edge-results.json and /tmp/final-forms-edge.cjs. Focus/occlusion sweep: /tmp/final-keyboard-sweep-results.json."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Native screen-reader spoken output was not observed; programmatic focus, relationships, state and DOM announcements were inspected. Product files were not edited."
    },
    {
      "skill": "aria-specialist",
      "note": "Read-only product audit in headless Chrome using Puppeteer, an ephemeral SQLite test server on port 8893, disposable accounts, and a mocked YouTube player; external requests were blocked."
    },
    {
      "skill": "aria-specialist",
      "note": "No VoiceOver or NVDA session was run; findings and passes describe DOM, focus, and Chrome accessibility-tree evidence."
    },
    {
      "skill": "aria-specialist",
      "note": "Evidence: /tmp/sullivan-aria-audit-results.json, /tmp/sullivan-aria-races-results.json, /tmp/sullivan-aria-concurrent-results.json."
    },
    {
      "skill": "live-region-controller",
      "note": "HEAD 48b3ac10c459b53076294376122e63d235dd1dee; Chrome DOM/focus/AX evidence, no VoiceOver or NVDA speech verification. Confidence on concurrent-message interpretation is medium."
    },
    {
      "skill": "live-region-controller",
      "note": "Pre-existing gap, excluded from reskin regressions: #sample-assign-receipt lacks live semantics. Holding POST /local/samples/science/assign for 3 seconds visibly displayed a saving message with no live mutation or focus message until completion; the same markup and assignSample behavior exist in baseline 36ef70b."
    },
    {
      "skill": "live-region-controller",
      "note": "Evidence: /tmp/sullivan-aria-audit-results.json, /tmp/sullivan-aria-races-results.json, /tmp/sullivan-aria-concurrent-results.json. Real providers and actual user data were not accessed."
    },
    {
      "skill": "contrast-master",
      "note": "The 18px finding is a stricter RESKIN_PLAYBOOK section 6 requirement, not a WCAG minimum-font-size failure."
    },
    {
      "skill": "contrast-master",
      "note": "Audit date 2026-11-05; Puppeteer 25.16.0, local Google Chrome; read-only product audit, only disposable account data and audit artifacts created."
    },
    {
      "skill": "contrast-master",
      "note": "Login’s existing 14–16px typography and 44px voice-test control were observed but excluded from findings because the redesign permits only one added login link."
    },
    {
      "skill": "alt-text-headings",
      "note": "Screenshot drift is instructional consistency debt rather than a proven WCAG 1.1.1 failure; existing alt text describes the old images accurately."
    },
    {
      "skill": "alt-text-headings",
      "note": "Current screen runtime evidence: visual-runtime-evidence.json. Current wizard/result screenshots: current-wizard-step1-390.png and current-results-390.png."
    },
    {
      "skill": "alt-text-headings",
      "note": "The app retains a generic Sullivan AI document title across guardian internal views; unique intro and guide titles are present. No WCAG title failure asserted for the single-document workflow."
    }
  ],
  "counts": {
    "critical": 0,
    "serious": 1,
    "moderate": 4,
    "minor": 1
  },
  "components": [],
  "score": 93,
  "grade": "A",
  "penalty": 13.4,
  "checks": 39,
  "generated": "2026-11-04",
  "template": "web"
}
```
