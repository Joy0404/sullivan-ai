# Web Accessibility Audit

An audit of web content, run on 2026-11-04. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-04 |
| Scope | 7 items |
| Skills run | accessibility-lead, alt-text-headings, contrast-master, keyboard-navigator |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 24 |

Audited:

- `apps/web/guardian-design.css T5 rules`
- `apps/web/guardian-design.css:guardian-learning-progress rules`
- `apps/web/role-portal.js loadGuardian guardian-learning-progress`
- `apps/web/role-portal.js:loadGuardian guardian-learning-progress block`
- `docs/verification/t5-progress-1280.png`
- `docs/verification/t5-progress-390.png`
- `loadGuardian guardian-learning-progress`

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

24 checks ran and found nothing.

- A pending successful response after role/user switch does not render records or a completion announcement.
- A response for a detached roster disclosure does not update the removed records or status.
- Async success appends semantic read-only records and updates persistent status without moving focus
- Completion updates the existing status once, leaves the record list outside the live region and preserves summary focus.
- Current parent screenshots1280/390 show readable four-row position/underline/bookmark/note counts and saved-time fallback text.
- Current-source independent Chrome fixture at320/390/1280: no new progress text below18px and no horizontal overflow, including a long lecture title and two lecture rows.
- Each lecture progress group has a real h4 and a description list with four dt/dd pairs.
- Existing focus token on canvas passes6.24:1; row separators are decorative and do not carry state by color alone.
- Failure gives a persistent polite retry instruction without focus theft; close/re-open retries successfully.
- Failure keeps summary focus; close/reopen with Enter/Space retries successfully and reports empty state
- Long lecture titles wrap within the progress group at320/390px; the parent student/card reading association remains clear.
- Native details/summary has a visible descriptive label; aria-describedby identifies the owning student.
- Native disclosure has the student name as description and exposes expanded state; loading status is polite in Chrome AX.
- Native heading/list/description-list structures label location and all counts; missing timestamp is explicit; private note getters stay unread.
- Native summary target height is at least48px and there is no horizontal overflow at320,390,1280px
- Native 学習/학습 현황 disclosure measures53.69px and preserves the existing immediate4px focus outline.
- No new images, icon-only controls, SVGs or color-only information require alternatives.
- Parent alignment refinement confirmed: progress-containing student copy grows with flex:1 and the Settings action aligns at the student row start.
- Position and count units are textual; valid saved time and missing saved-time fallback are expressed in words.
- Progress label/count/title text inherits dark ink on canvas12.62:1, muted saved/status text6.19:1, and disclosure brand text7.79:1; all exceedAA4.5:1.
- Real Tab reaches native summary; Enter opens progress and focus stays on summary during loading
- Space collapses; Enter reopens cached records without another request; Tab and Shift+Tab pass between progress and settings without traps
- Space toggles the native details; re-opening loaded data does not duplicate the request or announcement.
- Visible heading order is H1 guardian room → H2 student management → H3 student name → H4 assigned lecture titles, without skipped levels.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **alt-text-headings**: Reviewed source, independent current-function rendered fixture and both parent actual screenshots.
- **alt-text-headings**: No parent API mutations or authentication. Actual screen-reader speech was not tested.
- **contrast-master**: Used current loadGuardian function in an isolated DOM fixture with all request responses intercepted in memory; no authentication or parentserver8880 calls/writes.
- **contrast-master**: Initial screenshot Settings centering was a nonblocking association note; current align-items:flex-start refinement resolves it.
- **contrast-master**: No actual VoiceOver/NVDA speech or OS high-contrast palette testing.
- **contrast-master**: Runtime evidence: /tmp/sullivan-t5-work/review/visual-results.json.
- **keyboard-navigator**: Runtime used the exact current progress block in an isolated DOM with all requests mocked; no authentication or mutation of parent server8880.
- **keyboard-navigator**: Runtime evidence: /tmp/sullivan-t5-work/review/keyboard-runtime.json.
- **keyboard-navigator**: Actual VoiceOver/NVDA speech and assistive-device touch interaction were not tested.
- **accessibility-lead**: ARIA/live-region specialist final response was interrupted by its usage limit. Lead re-ran its completed runtime fixture and reviewed source. No final specialist verdict claimed.
- **accessibility-lead**: Real screen-reader speech not tested.

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
    "accessibility-lead",
    "alt-text-headings",
    "contrast-master",
    "keyboard-navigator"
  ],
  "scope": [
    "apps/web/guardian-design.css T5 rules",
    "apps/web/guardian-design.css:guardian-learning-progress rules",
    "apps/web/role-portal.js loadGuardian guardian-learning-progress",
    "apps/web/role-portal.js:loadGuardian guardian-learning-progress block",
    "docs/verification/t5-progress-1280.png",
    "docs/verification/t5-progress-390.png",
    "loadGuardian guardian-learning-progress"
  ],
  "findings": [],
  "passed": [
    "A pending successful response after role/user switch does not render records or a completion announcement.",
    "A response for a detached roster disclosure does not update the removed records or status.",
    "Async success appends semantic read-only records and updates persistent status without moving focus",
    "Completion updates the existing status once, leaves the record list outside the live region and preserves summary focus.",
    "Current parent screenshots1280/390 show readable four-row position/underline/bookmark/note counts and saved-time fallback text.",
    "Current-source independent Chrome fixture at320/390/1280: no new progress text below18px and no horizontal overflow, including a long lecture title and two lecture rows.",
    "Each lecture progress group has a real h4 and a description list with four dt/dd pairs.",
    "Existing focus token on canvas passes6.24:1; row separators are decorative and do not carry state by color alone.",
    "Failure gives a persistent polite retry instruction without focus theft; close/re-open retries successfully.",
    "Failure keeps summary focus; close/reopen with Enter/Space retries successfully and reports empty state",
    "Long lecture titles wrap within the progress group at320/390px; the parent student/card reading association remains clear.",
    "Native details/summary has a visible descriptive label; aria-describedby identifies the owning student.",
    "Native disclosure has the student name as description and exposes expanded state; loading status is polite in Chrome AX.",
    "Native heading/list/description-list structures label location and all counts; missing timestamp is explicit; private note getters stay unread.",
    "Native summary target height is at least48px and there is no horizontal overflow at320,390,1280px",
    "Native 学習/학습 현황 disclosure measures53.69px and preserves the existing immediate4px focus outline.",
    "No new images, icon-only controls, SVGs or color-only information require alternatives.",
    "Parent alignment refinement confirmed: progress-containing student copy grows with flex:1 and the Settings action aligns at the student row start.",
    "Position and count units are textual; valid saved time and missing saved-time fallback are expressed in words.",
    "Progress label/count/title text inherits dark ink on canvas12.62:1, muted saved/status text6.19:1, and disclosure brand text7.79:1; all exceedAA4.5:1.",
    "Real Tab reaches native summary; Enter opens progress and focus stays on summary during loading",
    "Space collapses; Enter reopens cached records without another request; Tab and Shift+Tab pass between progress and settings without traps",
    "Space toggles the native details; re-opening loaded data does not duplicate the request or announcement.",
    "Visible heading order is H1 guardian room → H2 student management → H3 student name → H4 assigned lecture titles, without skipped levels."
  ],
  "notes": [
    {
      "skill": "alt-text-headings",
      "note": "Reviewed source, independent current-function rendered fixture and both parent actual screenshots."
    },
    {
      "skill": "alt-text-headings",
      "note": "No parent API mutations or authentication. Actual screen-reader speech was not tested."
    },
    {
      "skill": "contrast-master",
      "note": "Used current loadGuardian function in an isolated DOM fixture with all request responses intercepted in memory; no authentication or parentserver8880 calls/writes."
    },
    {
      "skill": "contrast-master",
      "note": "Initial screenshot Settings centering was a nonblocking association note; current align-items:flex-start refinement resolves it."
    },
    {
      "skill": "contrast-master",
      "note": "No actual VoiceOver/NVDA speech or OS high-contrast palette testing."
    },
    {
      "skill": "contrast-master",
      "note": "Runtime evidence: /tmp/sullivan-t5-work/review/visual-results.json."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Runtime used the exact current progress block in an isolated DOM with all requests mocked; no authentication or mutation of parent server8880."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Runtime evidence: /tmp/sullivan-t5-work/review/keyboard-runtime.json."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Actual VoiceOver/NVDA speech and assistive-device touch interaction were not tested."
    },
    {
      "skill": "accessibility-lead",
      "note": "ARIA/live-region specialist final response was interrupted by its usage limit. Lead re-ran its completed runtime fixture and reviewed source. No final specialist verdict claimed."
    },
    {
      "skill": "accessibility-lead",
      "note": "Real screen-reader speech not tested."
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
  "checks": 24,
  "generated": "2026-11-04",
  "template": "web"
}
```
