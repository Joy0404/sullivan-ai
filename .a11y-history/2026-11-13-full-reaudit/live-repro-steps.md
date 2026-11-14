# Fresh 0.4.2 live/output audit reproduction steps

Reviewed 2026-11-13. These are source-derived reproduction instructions, except the isolated mocked-media state reproduction explicitly described below. No real VoiceOver/NVDA or audible TTS was run. No fixes were applied.

## LIVE-VOICE-TEST-RESUME-LOSS

1. In app-voice mode, connect a supported lecture and start playback.
2. Move keyboard focus to “음성 안내 시작·시험”. Its ordinary focus guidance pauses the lecture and retains a playing resume intent.
3. Activate that button before the focused-control guidance finishes.
4. Finish the explicit voice-test utterance.
5. Expected: originally playing lecture resumes once, provided there was no intervening stop/view change. Source result: handler's `speaker.cancel()` clears the saved playing intent; test sees an already paused media state and does not resume.

Isolated confirmation: imported the actual `speech.js` into Node; mocked SpeechSynthesis and media with fence 0, initial paused=false; delegated focus guidance; executed the handler's `speaker.cancel(); announcer.say(test,{force:true})`; completed the final utterance callback. Logged before click: paused=true, resumeIntent.playing=true. Logged after test: paused=true, plays=0, resumeIntent=null. This verifies control flow only, not Chrome audio behavior.

## LIVE-APP-VOICE-DIRECT-STATUS

1. Use app-voice mode without an OS screen reader.
2. Connect and play a lecture.
3. Either close/change the connected video tab so `tick()` receives a state error, or start playback from another student learning view so this view receives `student-lease-lost`.
4. Expected: stopped playback is accompanied by a concise spoken cause/recovery instruction.
5. Source result: media is reset, `#connection` text changes, but no `sullivan-status` event reaches StudentAnnouncer; the cause is available only as live-region text for external AT.

## LIVE-READER-SETTING-FOCUS-RACE

1. Use an account whose server preference has reader_mode=true and focus_voice=false.
2. Use a fresh browser profile with no `student-accessibility` key, leaving current pre-authentication settings at app defaults.
3. Log in, or restore that account while no keyboard/pointer interaction has occurred.
4. Observe the order of authenticated focus and mode application.
5. Source order: shared `signedIn()` makes workspace visible and focuses its title first; the student focus handler can enqueue app TTS; only then does `onUser()` apply the account's reader preference. Mode application itself does not cancel that already queued announcement.
6. Expected: known account mode applies before authenticated focus guidance. Needs real-browser/AT confirmation; reported with medium confidence.

## LIVE-NUMERIC-SETTING-VALUE-SILENCE

1. In app-voice mode without an external reader, open a lesson and its voice preferences.
2. Focus reading speed, app speech volume, or pitch.
3. Change the number with arrow keys and then leave/re-enter the field.
4. Expected: allowed nonsensitive setting values are spoken, e.g. reading speed 1.05 or volume 0.8.
5. Source result: guidance speaks the wrapping label only; number changes do not match the checkbox/select change listener. Native screen readers can access the values, but app-only guidance cannot.

## LIVE-GUARDIAN-PREVIEW-PENDING-ERROR

1. In guardian extension, open a completed preparation and enter a preview question with the required transmission consent.
2. Make the agent-turn endpoint reject, e.g. missing Gemini connection or a controlled network failure.
3. Expected: preview result leaves the pending state and identifies failure/retry.
4. Source result: global alert is populated by shared `task()`, but `#preview-answer` still says “준비 자료의 근거로 답변을 확인하고 있습니다.” indefinitely.
