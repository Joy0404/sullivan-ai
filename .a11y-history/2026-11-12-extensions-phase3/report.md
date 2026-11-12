# Web Accessibility Audit

An audit of web content, run on 2026-11-12. Read the executive summary for the verdict, the priorities section for what to do first, and the findings tables for detail.

## Metadata

What was audited, with what, and under which settings.

| Field | Value |
|---|---|
| Date | 2026-11-12 |
| Scope | 10 items |
| Skills run | forms-specialist, keyboard-navigator, live-region-controller, media-accessibility, modal-specialist |
| Tooling | node v26.13.0, a11y-mcp-server 7.1.0 |
| Scan configuration | defaults, no config file found |
| Checks counted | 60 |

Audited:

- `apps/extensions/shared/base.css`
- `apps/extensions/shared/ui.js`
- `apps/extensions/student/app.js`
- `apps/extensions/student/media-store.js`
- `apps/extensions/student/media.js`
- `apps/extensions/student/speech.js`
- `apps/extensions/student/video-control.js`
- `apps/extensions/student/worker.js`
- `apps/extensions/student/workspace.html`
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

60 checks ran and found nothing.

- A visible focus outline and first-in-DOM skip link remain present.
- A visible native cancellation button closes the dialog.
- All four original media review findings are corrected in the reviewed source.
- An isolated Chromium regression confirms corrected submission ends at the intended destination, while Escape and cancellation return to the trigger.
- Arrow shortcuts remain inside the student extension, without site-wide key interception.
- Cancellation and Escape have an explicit trigger/fallback focus restoration path.
- Changing assignments clears the selected local file and optional storage checkbox.
- Chat announces completed response availability without repeatedly reading the full transcript.
- Command input has associated command examples and editing-key guidance.
- Connection loss and explicit stop have accessible status feedback.
- Continuous timestamps are non-live, while playback state transitions are deduplicated.
- Evidence navigation now targets a focusable destination.
- Failed requests preserve entered questions, commands and notes.
- File connection announces checking and optional encryption through the persistent connection status.
- Fingerprint-verified local media receives a generated WebVTT captions track from valid timed transcript cues.
- Indexed sentence navigation uses the existing text-command path without intercepting editing keys.
- Input, textarea, select and dialog editing retain normal Space and arrow behavior.
- Lesson open, search, record deletion and underline toggling provide focus destinations.
- Local playback state includes ended, enabling the deduplicated end-of-playback announcement.
- Local-file help now lists MP4/WebM/MOV/M4V, codec limitations and 100MB conditions.
- Local-file privacy and identity-matching instructions are linked with aria-describedby.
- Login and registration retain username/password guidance and password-manager autocomplete.
- Matching Space keyup is delivered even after a dialog receives focus, releasing held gestures.
- Media readiness gates prevent player polling before initial metadata and seek setup complete.
- Native buttons, links, inputs, selects and details remain in normal Tab order; no positive tabindex found.
- Native modality provides background inertness, tab containment and Escape dismissal.
- Native playback and stop controls, cancellation fences, explicit storage consent and prepared-description labelling remain intact.
- Native required validation prevents empty command submission.
- Note input save requests are debounced before submission.
- Opening another lesson now immediately focuses the visible workspace heading before the asynchronous request; request failure leaves a valid focus destination.
- Optional Shift preserves edited fields and does not double-handle Shift+Tab.
- Optional Space now defers activation for summaries and links as well as buttons.
- Optional browser storage and network-backed speech recognition each require an explicit checkbox.
- Periodic checkpoints skip dirty notes, leaving debounced note-saving feedback distinct.
- Playback ownership loss invalidates pending voice, focus speech and AI actions.
- Playback transitions are deduplicated and announced independently of continuously changing non-live timestamps.
- Playback transitions update their dedicated persistent player-status region and no longer clear shared user errors.
- Position entry uses a native numeric control with bounds and an associated explanation.
- Reader-description remains mounted when empty; app TTS does not populate that reader announcement channel.
- Reader-mode announcement text is disabled while app TTS is used, avoiding that duplicate speech channel.
- Reader-mode descriptions are copied into a persistent polite status region with pause and manual-resume guidance.
- Reader-mode explanations use a persistent polite region with manual-resume guidance.
- Reader-mode pause announcements avoid duplicating a currently available explanation.
- Remote connection, file verification and encrypted-copy processing have loading messages.
- Reviewed inputs, selects, checkboxes and textarea controls have native wrapping labels.
- Routine playback checkpoints use quiet saves and do not announce saving/saved every ten seconds.
- Search results announce a concise count while keeping the full result list non-live.
- Separate labelled native video volume and mute controls now update local and remote audio.
- Settings use native numeric bounds and checkboxes rather than custom widgets.
- Shared asynchronous submission uses guarded aria-disabled/aria-busy and persistent status/error regions.
- Shared status and error regions are persistent and use textContent.
- Shared tasks preserve focus with aria-disabled rather than native disabling during requests.
- Submitted commands now await the dialog close event before executing destination navigation.
- The app-speech volume setting is labelled distinctly from video audio.
- The command input is explicitly focused on opening.
- The local captions toggle exposes aria-pressed; missing caption or identity data has explicit status text.
- The modal uses native dialog.showModal() with Escape support and explicit focus restoration.
- The reader explanation channel is suppressed while app TTS is used.
- The text command uses native dialog.showModal() with a valid heading reference.
- Voice fallback reasons are populated inside the modal before showModal and associated with dialog and input through aria-describedby.

## Needs a human

Items a skill could not decide, or could not check automatically.

- **keyboard-navigator**: All five findings reported during this review have been corrected.
- **keyboard-navigator**: Source re-review plus an earlier isolated Chromium hidden-subtree focus probe; no complete installed-extension or actual screen-reader run by this specialist.
- **keyboard-navigator**: No critical or serious keyboard findings remain within the reviewed scope.
- **forms-specialist**: Both initially reported form findings are resolved.
- **forms-specialist**: Source re-review only; no full extension form execution or actual screen-reader audio was performed.
- **forms-specialist**: Visible speech-rate range and step guidance remains an optional usability improvement.
- **media-accessibility**: Updated .a11y-history/2026-11-12-extensions-phase3/media.json.
- **media-accessibility**: Source re-review only; caption synchronization, actual speech quality, YouTube playback and real VoiceOver/NVDA audio were not executed by this specialist.
- **media-accessibility**: No critical or serious media findings remain within the reviewed source scope.
- **media-accessibility**: No media findings remain in this source re-review; runtime and real-content limitations still apply.
- **modal-specialist**: The previous modal submission focus-order finding is resolved.
- **modal-specialist**: Source re-review plus isolated Chromium regression; this specialist did not execute the complete installed-extension flow or actual screen-reader audio.
- **modal-specialist**: Updated .a11y-history/2026-11-12-extensions-phase3/modal.json.
- **live-region-controller**: All three previously reported live-region findings are corrected in the reviewed source.
- **live-region-controller**: Updated .a11y-history/2026-11-12-extensions-phase3/live.json.
- **live-region-controller**: Source re-review only; actual VoiceOver/NVDA announcement ordering and speech quality were not executed by this specialist.
- **live-region-controller**: No critical, serious, moderate or minor findings remain in this source re-review.

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
    "forms-specialist",
    "keyboard-navigator",
    "live-region-controller",
    "media-accessibility",
    "modal-specialist"
  ],
  "scope": [
    "apps/extensions/shared/base.css",
    "apps/extensions/shared/ui.js",
    "apps/extensions/student/app.js",
    "apps/extensions/student/media-store.js",
    "apps/extensions/student/media.js",
    "apps/extensions/student/speech.js",
    "apps/extensions/student/video-control.js",
    "apps/extensions/student/worker.js",
    "apps/extensions/student/workspace.html",
    "scripts/build_extensions.py"
  ],
  "findings": [],
  "passed": [
    "A visible focus outline and first-in-DOM skip link remain present.",
    "A visible native cancellation button closes the dialog.",
    "All four original media review findings are corrected in the reviewed source.",
    "An isolated Chromium regression confirms corrected submission ends at the intended destination, while Escape and cancellation return to the trigger.",
    "Arrow shortcuts remain inside the student extension, without site-wide key interception.",
    "Cancellation and Escape have an explicit trigger/fallback focus restoration path.",
    "Changing assignments clears the selected local file and optional storage checkbox.",
    "Chat announces completed response availability without repeatedly reading the full transcript.",
    "Command input has associated command examples and editing-key guidance.",
    "Connection loss and explicit stop have accessible status feedback.",
    "Continuous timestamps are non-live, while playback state transitions are deduplicated.",
    "Evidence navigation now targets a focusable destination.",
    "Failed requests preserve entered questions, commands and notes.",
    "File connection announces checking and optional encryption through the persistent connection status.",
    "Fingerprint-verified local media receives a generated WebVTT captions track from valid timed transcript cues.",
    "Indexed sentence navigation uses the existing text-command path without intercepting editing keys.",
    "Input, textarea, select and dialog editing retain normal Space and arrow behavior.",
    "Lesson open, search, record deletion and underline toggling provide focus destinations.",
    "Local playback state includes ended, enabling the deduplicated end-of-playback announcement.",
    "Local-file help now lists MP4/WebM/MOV/M4V, codec limitations and 100MB conditions.",
    "Local-file privacy and identity-matching instructions are linked with aria-describedby.",
    "Login and registration retain username/password guidance and password-manager autocomplete.",
    "Matching Space keyup is delivered even after a dialog receives focus, releasing held gestures.",
    "Media readiness gates prevent player polling before initial metadata and seek setup complete.",
    "Native buttons, links, inputs, selects and details remain in normal Tab order; no positive tabindex found.",
    "Native modality provides background inertness, tab containment and Escape dismissal.",
    "Native playback and stop controls, cancellation fences, explicit storage consent and prepared-description labelling remain intact.",
    "Native required validation prevents empty command submission.",
    "Note input save requests are debounced before submission.",
    "Opening another lesson now immediately focuses the visible workspace heading before the asynchronous request; request failure leaves a valid focus destination.",
    "Optional Shift preserves edited fields and does not double-handle Shift+Tab.",
    "Optional Space now defers activation for summaries and links as well as buttons.",
    "Optional browser storage and network-backed speech recognition each require an explicit checkbox.",
    "Periodic checkpoints skip dirty notes, leaving debounced note-saving feedback distinct.",
    "Playback ownership loss invalidates pending voice, focus speech and AI actions.",
    "Playback transitions are deduplicated and announced independently of continuously changing non-live timestamps.",
    "Playback transitions update their dedicated persistent player-status region and no longer clear shared user errors.",
    "Position entry uses a native numeric control with bounds and an associated explanation.",
    "Reader-description remains mounted when empty; app TTS does not populate that reader announcement channel.",
    "Reader-mode announcement text is disabled while app TTS is used, avoiding that duplicate speech channel.",
    "Reader-mode descriptions are copied into a persistent polite status region with pause and manual-resume guidance.",
    "Reader-mode explanations use a persistent polite region with manual-resume guidance.",
    "Reader-mode pause announcements avoid duplicating a currently available explanation.",
    "Remote connection, file verification and encrypted-copy processing have loading messages.",
    "Reviewed inputs, selects, checkboxes and textarea controls have native wrapping labels.",
    "Routine playback checkpoints use quiet saves and do not announce saving/saved every ten seconds.",
    "Search results announce a concise count while keeping the full result list non-live.",
    "Separate labelled native video volume and mute controls now update local and remote audio.",
    "Settings use native numeric bounds and checkboxes rather than custom widgets.",
    "Shared asynchronous submission uses guarded aria-disabled/aria-busy and persistent status/error regions.",
    "Shared status and error regions are persistent and use textContent.",
    "Shared tasks preserve focus with aria-disabled rather than native disabling during requests.",
    "Submitted commands now await the dialog close event before executing destination navigation.",
    "The app-speech volume setting is labelled distinctly from video audio.",
    "The command input is explicitly focused on opening.",
    "The local captions toggle exposes aria-pressed; missing caption or identity data has explicit status text.",
    "The modal uses native dialog.showModal() with Escape support and explicit focus restoration.",
    "The reader explanation channel is suppressed while app TTS is used.",
    "The text command uses native dialog.showModal() with a valid heading reference.",
    "Voice fallback reasons are populated inside the modal before showModal and associated with dialog and input through aria-describedby."
  ],
  "notes": [
    {
      "skill": "keyboard-navigator",
      "note": "All five findings reported during this review have been corrected."
    },
    {
      "skill": "keyboard-navigator",
      "note": "Source re-review plus an earlier isolated Chromium hidden-subtree focus probe; no complete installed-extension or actual screen-reader run by this specialist."
    },
    {
      "skill": "keyboard-navigator",
      "note": "No critical or serious keyboard findings remain within the reviewed scope."
    },
    {
      "skill": "forms-specialist",
      "note": "Both initially reported form findings are resolved."
    },
    {
      "skill": "forms-specialist",
      "note": "Source re-review only; no full extension form execution or actual screen-reader audio was performed."
    },
    {
      "skill": "forms-specialist",
      "note": "Visible speech-rate range and step guidance remains an optional usability improvement."
    },
    {
      "skill": "media-accessibility",
      "note": "Updated .a11y-history/2026-11-12-extensions-phase3/media.json."
    },
    {
      "skill": "media-accessibility",
      "note": "Source re-review only; caption synchronization, actual speech quality, YouTube playback and real VoiceOver/NVDA audio were not executed by this specialist."
    },
    {
      "skill": "media-accessibility",
      "note": "No critical or serious media findings remain within the reviewed source scope."
    },
    {
      "skill": "media-accessibility",
      "note": "No media findings remain in this source re-review; runtime and real-content limitations still apply."
    },
    {
      "skill": "modal-specialist",
      "note": "The previous modal submission focus-order finding is resolved."
    },
    {
      "skill": "modal-specialist",
      "note": "Source re-review plus isolated Chromium regression; this specialist did not execute the complete installed-extension flow or actual screen-reader audio."
    },
    {
      "skill": "modal-specialist",
      "note": "Updated .a11y-history/2026-11-12-extensions-phase3/modal.json."
    },
    {
      "skill": "live-region-controller",
      "note": "All three previously reported live-region findings are corrected in the reviewed source."
    },
    {
      "skill": "live-region-controller",
      "note": "Updated .a11y-history/2026-11-12-extensions-phase3/live.json."
    },
    {
      "skill": "live-region-controller",
      "note": "Source re-review only; actual VoiceOver/NVDA announcement ordering and speech quality were not executed by this specialist."
    },
    {
      "skill": "live-region-controller",
      "note": "No critical, serious, moderate or minor findings remain in this source re-review."
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
  "checks": 60,
  "generated": "2026-11-12",
  "template": "web"
}
```
