# Web Accessibility Audit

An audit of web content, run on 2026-11-04. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-04 |
| Scope | 9 items |
| Skills run | aria-specialist, keyboard-navigator, live-region-controller |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 17 |

Audited:

- `apps/web/index.html:137`
- `apps/web/role-portal.js:14`
- `apps/web/role-portal.js:14-18`
- `apps/web/role-portal.js:201-232`
- `apps/web/role-portal.js:392-406`
- `apps/web/role-portal.js:696`
- `apps/web/role-portal.js:81-109`
- `scripts/verify_guardian_sessions.py`
- `scripts/verify_roles_browser.py:159`

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

- A 60-character username remained complete in DOM and AX identity; page had no horizontal overflow at390px and1280px.
- A current-session progress401 still signed out and focused #login-role-student.
- A server error retains focus on #portal-feedback rather than restoring the submit control.
- All targeted browser cases completed with zero page errors.
- An actual current-generation 401 remains effective: after expiring the disposable server session without changing client generation, opening progress signs out the UI and focuses #login-role-student.
- An explicit focus handoff from a second modal-close observer to rights_confirmed remains in place after queued restoration, exercising the guard against overriding another focus decision.
- An old progress401 after the same guardian logged in again preserved the guardian identity and #guardian-prepare focus.
- Cancellation during the 100% finishing delay restores #wizard-submit after it is re-enabled, clears the received snapshot and keeps the result view hidden; the previously documented late-cancel defect is closed.
- Closed ARIA-STUDENT-IDENTITY: same-name students had distinct full name(username) roster headings and Chrome AX disclosure descriptions.
- Closed LIVE-STALE-401-SESSION: after fully settled student login, an old guardian progress401 preserved the student ID, role, and #student-list-open focus; /local/me remained200 for that student.
- Concurrent progress loading, empty, and error updates identified same-name students using their distinct usernames.
- Early analysis cancellation by Escape restores focus to the re-enabled #wizard-submit and leaves no snapshot/result view.
- Holding sample assignment for2100ms produced exactly one loading live mutation naming the student. Completion focused #portal-feedback once, cleared #sample-assign-status, and did not duplicate the completion text in a live node.
- Logout reset both #video-url value and #video-link-state label to the empty state.
- Normal completion focuses #guardian-result-title; queued restoration does not pull focus back to the hidden wizard. A following user Tab remains in the result flow.
- Reviewed the durable late-cancel regression: it waits for 100%, presses Escape, waits for the controller to settle, asserts submit focus and snapshot=null, then retries normal preparation.
- Sample assignment loading uses an existing role=status node; its visible receipt retains ordinary paragraph semantics.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **aria-specialist**: Targeted read-only product recheck of the current working diff; no product edits.
- **aria-specialist**: Actual VoiceOver/NVDA unavailable; verification covers Chrome DOM, keyboard focus, and AX behavior.
- **aria-specialist**: Evidence: /tmp/sullivan-session-fix/results.json. Used disposable SQLite accounts on8893, synthetic fixtures, mocked delayed responses, and blocked nonlocal requests.
- **aria-specialist**: Reviewed scripts/verify_guardian_sessions.py: it includes duplicate-name identity, old401 after student/same-guardian login, current401 signout, logout URL-label reset, and assignment status checks. This specialist ran an independent Puppeteer harness rather than the durable script.
- **live-region-controller**: No reproducible issues remain in this targeted scope. Findings arrays intentionally empty after fixes.
- **live-region-controller**: Actual VoiceOver/NVDA unavailable; announcement evidence is DOM mutations, focus events, and Chrome AX rather than observed speech.
- **live-region-controller**: Evidence: /tmp/sullivan-session-fix/results.json and /tmp/sullivan-session-fix/audit.cjs. Isolated SQLite and disposable accounts; no providers or private databases were accessed.
- **live-region-controller**: The durable scripts/verify_guardian_sessions.py was inspected; the independent harness additionally checked a60-character username, exact loading/completion event counts, and AX identity text.
- **keyboard-navigator**: Verdict: no reproducible defect found in the targeted focus restoration and ordinary-401 recheck. Six runtime checks passed against the working diff based on HEAD 312a607.
- **keyboard-navigator**: Evidence: /tmp/session-fix-keyboard/results.json; executable check: /tmp/session-fix-keyboard/check.cjs. Chrome/156.0.8078.80 with Puppeteer, 1280×900.
- **keyboard-navigator**: Only a disposable server on port 8892 with temporary account/usage databases was used. Provider configuration removed and external/analysis routes blocked; no provider endpoint was requested. No product or test edits by this reviewer.
- **keyboard-navigator**: The handoff check uses a second MutationObserver to place focus during the same close checkpoint; the normal-completion check also verifies the subsequent user Tab. Stale-401 role-switch handling and same-name identity presentation are reviewed separately by the parent team.

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
    "aria-specialist",
    "keyboard-navigator",
    "live-region-controller"
  ],
  "scope": [
    "apps/web/index.html:137",
    "apps/web/role-portal.js:14",
    "apps/web/role-portal.js:14-18",
    "apps/web/role-portal.js:201-232",
    "apps/web/role-portal.js:392-406",
    "apps/web/role-portal.js:696",
    "apps/web/role-portal.js:81-109",
    "scripts/verify_guardian_sessions.py",
    "scripts/verify_roles_browser.py:159"
  ],
  "findings": [],
  "passed": [
    "A 60-character username remained complete in DOM and AX identity; page had no horizontal overflow at390px and1280px.",
    "A current-session progress401 still signed out and focused #login-role-student.",
    "A server error retains focus on #portal-feedback rather than restoring the submit control.",
    "All targeted browser cases completed with zero page errors.",
    "An actual current-generation 401 remains effective: after expiring the disposable server session without changing client generation, opening progress signs out the UI and focuses #login-role-student.",
    "An explicit focus handoff from a second modal-close observer to rights_confirmed remains in place after queued restoration, exercising the guard against overriding another focus decision.",
    "An old progress401 after the same guardian logged in again preserved the guardian identity and #guardian-prepare focus.",
    "Cancellation during the 100% finishing delay restores #wizard-submit after it is re-enabled, clears the received snapshot and keeps the result view hidden; the previously documented late-cancel defect is closed.",
    "Closed ARIA-STUDENT-IDENTITY: same-name students had distinct full name(username) roster headings and Chrome AX disclosure descriptions.",
    "Closed LIVE-STALE-401-SESSION: after fully settled student login, an old guardian progress401 preserved the student ID, role, and #student-list-open focus; /local/me remained200 for that student.",
    "Concurrent progress loading, empty, and error updates identified same-name students using their distinct usernames.",
    "Early analysis cancellation by Escape restores focus to the re-enabled #wizard-submit and leaves no snapshot/result view.",
    "Holding sample assignment for2100ms produced exactly one loading live mutation naming the student. Completion focused #portal-feedback once, cleared #sample-assign-status, and did not duplicate the completion text in a live node.",
    "Logout reset both #video-url value and #video-link-state label to the empty state.",
    "Normal completion focuses #guardian-result-title; queued restoration does not pull focus back to the hidden wizard. A following user Tab remains in the result flow.",
    "Reviewed the durable late-cancel regression: it waits for 100%, presses Escape, waits for the controller to settle, asserts submit focus and snapshot=null, then retries normal preparation.",
    "Sample assignment loading uses an existing role=status node; its visible receipt retains ordinary paragraph semantics."
  ],
  "notes": [
    {
      "skill": "aria-specialist",
      "note": "Targeted read-only product recheck of the current working diff; no product edits."
    },
    {
      "skill": "aria-specialist",
      "note": "Actual VoiceOver/NVDA unavailable; verification covers Chrome DOM, keyboard focus, and AX behavior."
    },
    {
      "skill": "aria-specialist",
      "note": "Evidence: /tmp/sullivan-session-fix/results.json. Used disposable SQLite accounts on8893, synthetic fixtures, mocked delayed responses, and blocked nonlocal requests."
    },
    {
      "skill": "aria-specialist",
      "note": "Reviewed scripts/verify_guardian_sessions.py: it includes duplicate-name identity, old401 after student/same-guardian login, current401 signout, logout URL-label reset, and assignment status checks. This specialist ran an independent Puppeteer harness rather than the durable script."
    },
    {
      "skill": "live-region-controller",
      "note": "No reproducible issues remain in this targeted scope. Findings arrays intentionally empty after fixes."
    },
    {
      "skill": "live-region-controller",
      "note": "Actual VoiceOver/NVDA unavailable; announcement evidence is DOM mutations, focus events, and Chrome AX rather than observed speech."
    },
    {
      "skill": "live-region-controller",
      "note": "Evidence: /tmp/sullivan-session-fix/results.json and /tmp/sullivan-session-fix/audit.cjs. Isolated SQLite and disposable accounts; no providers or private databases were accessed."
    },
    {
      "skill": "live-region-controller",
      "note": "The durable scripts/verify_guardian_sessions.py was inspected; the independent harness additionally checked a60-character username, exact loading/completion event counts, and AX identity text."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Verdict: no reproducible defect found in the targeted focus restoration and ordinary-401 recheck. Six runtime checks passed against the working diff based on HEAD 312a607."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Evidence: /tmp/session-fix-keyboard/results.json; executable check: /tmp/session-fix-keyboard/check.cjs. Chrome/156.0.8078.80 with Puppeteer, 1280×900."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Only a disposable server on port 8892 with temporary account/usage databases was used. Provider configuration removed and external/analysis routes blocked; no provider endpoint was requested. No product or test edits by this reviewer."
    },
    {
      "skill": "keyboard-navigator",
      "note": "The handoff check uses a second MutationObserver to place focus during the same close checkpoint; the normal-completion check also verifies the subsequent user Tab. Stale-401 role-switch handling and same-name identity presentation are reviewed separately by the parent team."
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
  "generated": "2026-11-04",
  "template": "web"
}
```
