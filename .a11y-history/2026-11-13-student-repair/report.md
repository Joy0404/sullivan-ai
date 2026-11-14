# Web Accessibility Audit

An audit of web content, run on 2026-11-13. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-13 |
| Scope | 18 items |
| Skills run | aria-specialist, contrast-master, forms-specialist, keyboard-navigator, live-region-controller, modal-specialist |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 42 |

Audited:

- `apps/api/app/extension_accounts.py`
- `apps/extensions/guardian/app.js`
- `apps/extensions/guardian/workspace.html`
- `apps/extensions/shared/base.css`
- `apps/extensions/shared/ui.js`
- `apps/extensions/student/app.js`
- `apps/extensions/student/keyboard.js`
- `apps/extensions/student/speech.js`
- `apps/extensions/student/video-control.js`
- `apps/extensions/student/worker.js`
- `apps/extensions/student/workspace.html`
- `apps/web/guardian-design.css`
- `apps/web/intro.css`
- `apps/web/student-design.css`
- `apps/web/styles.css`
- `apps/web/tokens.css`
- `apps/web/workspace-design.css`
- `scripts/build_extensions.py`

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

42 checks ran and found nothing.

- Account authentication, recovery-code controls and guardian/student pairing controls remain available; recovery and pairing code inputs retain descriptive labels.
- App guidance now starts before selecting a lesson and covers named native fields.
- App-wide access mode and voice test are named native select/button controls available before login.
- Builder copies original tokens.css into each extension and loads it before base.css, keeping token definitions authoritative.
- Calculated normal text contrast: ink #172c48 on white 14.09:1; muted #465c73 on white 6.91:1; white on navy 14.09:1; white on blue hover #164b8b 8.70:1.
- Changed caption/underline controls retain native buttons with correct pressed state.
- Closing restores the prior visible focus target; text command submission awaits the close event before executing navigation.
- Control boundary #6f87a3 has 3.70:1 contrast on white and 3.32:1 on canvas. Lower contrast --line is restricted to decorative article and section separators.
- Escape outside a modal releases containment; visible instructions explain Escape and F6, and the panel-mode button re-enables containment.
- From programmatically focused headings/results, Tab selects the next DOM-adjacent control rather than restarting the page.
- Generated learning tools skip both app TTS and result-region focus in reader mode, avoiding duplicate full-result delivery.
- Guardian analysis forms no longer request administrator usage codes, and submission no longer reads those removed controls.
- Keyboard handlers are installed only in the extension document; injected video-control code contains no host keyboard interception.
- Links remain underlined by native styling, errors use text in addition to color, and reduced-motion handling is present.
- Microphone permission is requested from an explicit native action; granted streams have their tracks stopped after permission preparation.
- Native field values are excluded from control descriptions; passwords are identified without speaking values.
- New microphone consent dialog has native dialog semantics and valid labelledby/describedby IDs.
- New reader-description and answer-status regions are persistent status regions.
- Ordinary and fallback answers skip StudentSpeech in reader mode, leaving answer-status as the single full-answer channel.
- Original authoritative palette comes from apps/web/tokens.css. The final web learning-desk-4 cascade uses white surfaces and navy #172c48 primary actions, with blue #164b8b accents; the extension now reproduces those choices.
- Pending gestures reset on pointer interaction, window blur and document hiding.
- Pending microphone completion is fenced by request generation, account, lesson and open-dialog state; close, cancellation and context clearing invalidate the request.
- Reader-mode uses native live regions and suppresses UI TTS.
- Reading-mode select is natively labelled; voice testing uses a native button. Microphone consent uses a labelled native dialog with an associated explanation, explicit consent/start and cancellation buttons, and a text-input alternative.
- Server signup no longer expects an invite code. The optional signup-disabled policy gives a visible explanation rather than requesting a removed field.
- Shared status updates dispatch a student-only speech event.
- Space commands default on with keymap migration: single tap toggles playback, double tap stops output, triple tap opens text input, and hold threshold is explicitly 3000 milliseconds.
- Space in text fields, checkboxes, radio controls and native dialogs keeps native behavior; Enter remains the documented button activation key.
- Speech absence and blocked UI guidance provide visible recovery feedback.
- Standalone Shift moves backward; Shift+Tab and modifier chords do not trigger an extra backward step; text entry remains native.
- Student and guardian signup forms no longer contain administrator invite fields; retained identity and password fields have native labels, autocomplete tokens and visible associated requirements.
- Student pairing checkbox and confirmation button reference guardian identity and sharing scope through aria-describedby.
- Tab and Shift+Tab cycle among visible enabled controls in the extension document, scoped to an open native dialog when present.
- Tab remains within the open dialog, background content is natively inert and Escape retains native dialog dismissal.
- Text and microphone permission overlays use native dialog elements with showModal, heading-based names, concise descriptions and visible cancel buttons.
- Text dialog initially focuses its labelled command input; permission dialog focuses its explicitly named consent/permission action.
- The 4px focus ring #8c4700 has 6.96:1 contrast on white and 6.24:1 on canvas. It is offset from controls; native forced-color adaptation remains enabled.
- The action handler invokes sidePanel.open during its user activation, then requests panel focus; original connection permissions run from the native button handler.
- The former silent option is accurately named “초점·상태 음성 끄기”; its completion message explains that explicit material-listening controls remain available.
- UI announcements use a separate announcer without media claim/state calls.
- Unsupported or failed recognition has a keyboard-accessible text-command fallback.
- Voice consent uses a labelled native dialog with typed fallback and named microphone permission control.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **keyboard-navigator**: Static source re-review only. Actual Chrome native panel targeting, permission UI and physical keyboard behavior require the parent runtime verification.
- **keyboard-navigator**: Baseline defects corrected during review: disabled-by-default gesture settings, focused-control click on single Space, 600ms hold inheritance, missing containment, heading focus adjacency and conflicting generic keyboard instructions.
- **keyboard-navigator**: Persisted separately: modal.json.
- **modal-specialist**: Source review only; no claim of live screen-reader testing or actual Chrome microphone-prompt execution.
- **modal-specialist**: The asynchronous microphone completion race observed during review was corrected before this final re-review.
- **live-region-controller**: All reported live-region source findings have been corrected.
- **live-region-controller**: Static source re-review only; actual VoiceOver/NVDA announcement ordering and audible TTS were not executed.
- **live-region-controller**: Browser and native side-panel verification are being performed independently by the parent agent.
- **aria-specialist**: All reported semantic source findings have been corrected.
- **aria-specialist**: Static semantic re-review only; no real assistive-technology execution was performed.
- **contrast-master**: Final source review and WCAG sRGB contrast calculations on 2026-11-13; no browser rendering or assistive-technology session was run by this specialist.
- **contrast-master**: The separate forms-specialist current-state report is persisted alongside this file as forms.json with no outstanding findings.
- **forms-specialist**: Final source review on 2026-11-13; no browser or assistive-technology session was executed by this specialist. Existing unrelated forms were not exhaustively re-audited.

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
    "contrast-master",
    "forms-specialist",
    "keyboard-navigator",
    "live-region-controller",
    "modal-specialist"
  ],
  "scope": [
    "apps/api/app/extension_accounts.py",
    "apps/extensions/guardian/app.js",
    "apps/extensions/guardian/workspace.html",
    "apps/extensions/shared/base.css",
    "apps/extensions/shared/ui.js",
    "apps/extensions/student/app.js",
    "apps/extensions/student/keyboard.js",
    "apps/extensions/student/speech.js",
    "apps/extensions/student/video-control.js",
    "apps/extensions/student/worker.js",
    "apps/extensions/student/workspace.html",
    "apps/web/guardian-design.css",
    "apps/web/intro.css",
    "apps/web/student-design.css",
    "apps/web/styles.css",
    "apps/web/tokens.css",
    "apps/web/workspace-design.css",
    "scripts/build_extensions.py"
  ],
  "findings": [],
  "passed": [
    "Account authentication, recovery-code controls and guardian/student pairing controls remain available; recovery and pairing code inputs retain descriptive labels.",
    "App guidance now starts before selecting a lesson and covers named native fields.",
    "App-wide access mode and voice test are named native select/button controls available before login.",
    "Builder copies original tokens.css into each extension and loads it before base.css, keeping token definitions authoritative.",
    "Calculated normal text contrast: ink #172c48 on white 14.09:1; muted #465c73 on white 6.91:1; white on navy 14.09:1; white on blue hover #164b8b 8.70:1.",
    "Changed caption/underline controls retain native buttons with correct pressed state.",
    "Closing restores the prior visible focus target; text command submission awaits the close event before executing navigation.",
    "Control boundary #6f87a3 has 3.70:1 contrast on white and 3.32:1 on canvas. Lower contrast --line is restricted to decorative article and section separators.",
    "Escape outside a modal releases containment; visible instructions explain Escape and F6, and the panel-mode button re-enables containment.",
    "From programmatically focused headings/results, Tab selects the next DOM-adjacent control rather than restarting the page.",
    "Generated learning tools skip both app TTS and result-region focus in reader mode, avoiding duplicate full-result delivery.",
    "Guardian analysis forms no longer request administrator usage codes, and submission no longer reads those removed controls.",
    "Keyboard handlers are installed only in the extension document; injected video-control code contains no host keyboard interception.",
    "Links remain underlined by native styling, errors use text in addition to color, and reduced-motion handling is present.",
    "Microphone permission is requested from an explicit native action; granted streams have their tracks stopped after permission preparation.",
    "Native field values are excluded from control descriptions; passwords are identified without speaking values.",
    "New microphone consent dialog has native dialog semantics and valid labelledby/describedby IDs.",
    "New reader-description and answer-status regions are persistent status regions.",
    "Ordinary and fallback answers skip StudentSpeech in reader mode, leaving answer-status as the single full-answer channel.",
    "Original authoritative palette comes from apps/web/tokens.css. The final web learning-desk-4 cascade uses white surfaces and navy #172c48 primary actions, with blue #164b8b accents; the extension now reproduces those choices.",
    "Pending gestures reset on pointer interaction, window blur and document hiding.",
    "Pending microphone completion is fenced by request generation, account, lesson and open-dialog state; close, cancellation and context clearing invalidate the request.",
    "Reader-mode uses native live regions and suppresses UI TTS.",
    "Reading-mode select is natively labelled; voice testing uses a native button. Microphone consent uses a labelled native dialog with an associated explanation, explicit consent/start and cancellation buttons, and a text-input alternative.",
    "Server signup no longer expects an invite code. The optional signup-disabled policy gives a visible explanation rather than requesting a removed field.",
    "Shared status updates dispatch a student-only speech event.",
    "Space commands default on with keymap migration: single tap toggles playback, double tap stops output, triple tap opens text input, and hold threshold is explicitly 3000 milliseconds.",
    "Space in text fields, checkboxes, radio controls and native dialogs keeps native behavior; Enter remains the documented button activation key.",
    "Speech absence and blocked UI guidance provide visible recovery feedback.",
    "Standalone Shift moves backward; Shift+Tab and modifier chords do not trigger an extra backward step; text entry remains native.",
    "Student and guardian signup forms no longer contain administrator invite fields; retained identity and password fields have native labels, autocomplete tokens and visible associated requirements.",
    "Student pairing checkbox and confirmation button reference guardian identity and sharing scope through aria-describedby.",
    "Tab and Shift+Tab cycle among visible enabled controls in the extension document, scoped to an open native dialog when present.",
    "Tab remains within the open dialog, background content is natively inert and Escape retains native dialog dismissal.",
    "Text and microphone permission overlays use native dialog elements with showModal, heading-based names, concise descriptions and visible cancel buttons.",
    "Text dialog initially focuses its labelled command input; permission dialog focuses its explicitly named consent/permission action.",
    "The 4px focus ring #8c4700 has 6.96:1 contrast on white and 6.24:1 on canvas. It is offset from controls; native forced-color adaptation remains enabled.",
    "The action handler invokes sidePanel.open during its user activation, then requests panel focus; original connection permissions run from the native button handler.",
    "The former silent option is accurately named “초점·상태 음성 끄기”; its completion message explains that explicit material-listening controls remain available.",
    "UI announcements use a separate announcer without media claim/state calls.",
    "Unsupported or failed recognition has a keyboard-accessible text-command fallback.",
    "Voice consent uses a labelled native dialog with typed fallback and named microphone permission control."
  ],
  "notes": [
    {
      "skill": "keyboard-navigator",
      "note": "Static source re-review only. Actual Chrome native panel targeting, permission UI and physical keyboard behavior require the parent runtime verification."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Baseline defects corrected during review: disabled-by-default gesture settings, focused-control click on single Space, 600ms hold inheritance, missing containment, heading focus adjacency and conflicting generic keyboard instructions."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Persisted separately: modal.json."
    },
    {
      "skill": "modal-specialist",
      "note": "Source review only; no claim of live screen-reader testing or actual Chrome microphone-prompt execution."
    },
    {
      "skill": "modal-specialist",
      "note": "The asynchronous microphone completion race observed during review was corrected before this final re-review."
    },
    {
      "skill": "live-region-controller",
      "note": "All reported live-region source findings have been corrected."
    },
    {
      "skill": "live-region-controller",
      "note": "Static source re-review only; actual VoiceOver/NVDA announcement ordering and audible TTS were not executed."
    },
    {
      "skill": "live-region-controller",
      "note": "Browser and native side-panel verification are being performed independently by the parent agent."
    },
    {
      "skill": "aria-specialist",
      "note": "All reported semantic source findings have been corrected."
    },
    {
      "skill": "aria-specialist",
      "note": "Static semantic re-review only; no real assistive-technology execution was performed."
    },
    {
      "skill": "contrast-master",
      "note": "Final source review and WCAG sRGB contrast calculations on 2026-11-13; no browser rendering or assistive-technology session was run by this specialist."
    },
    {
      "skill": "contrast-master",
      "note": "The separate forms-specialist current-state report is persisted alongside this file as forms.json with no outstanding findings."
    },
    {
      "skill": "forms-specialist",
      "note": "Final source review on 2026-11-13; no browser or assistive-technology session was executed by this specialist. Existing unrelated forms were not exhaustively re-audited."
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
  "checks": 42,
  "generated": "2026-11-13",
  "template": "web"
}
```
