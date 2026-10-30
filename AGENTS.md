# Gyeotnun coding instructions

## Mission

Build one integrated internet-lecture accessibility agent. The product identifies important information that exists on screen but was not spoken, restores non-visual access to long passages, and preserves the student's own learning process.

## Non-negotiable rules

1. Never claim that the deterministic demo analyzed an uploaded video.
2. Raw video stays in the browser unless the user explicitly configures an ephemeral licensed analyzer. Do not persist raw media by default.
3. Do not bypass DRM, download protected streams, or scrape paid lecture sites.
4. Any visual observation below confidence `0.72` must be `HOLD`; its candidate text must not enter `public_description`, review, or TTS.
5. In problem mode, observations classified as `answer` stay blocked on every output path.
6. Spoken and visual data from one scene are comparison signals, not automatically independent truth sources.
7. If the lecturer already communicated the same information, prefer `INDEX_ONLY` instead of interrupting playback.
8. Preserve timestamps and reasons for every decision so review items are traceable.
9. Provider SDKs belong behind `app/adapters/interfaces.py`; the core must remain deterministic and testable.
10. New safety behavior requires a regression test.

## Workflow

This repository uses one product and a main-first workflow. Do not recreate person-specific branches, ownership folders, or classroom-camera features.

Before finishing a change:

```bash
python scripts/verify_project.py
cd apps/api && python -m pytest -q
node --check ../web/app.js
```

Also verify keyboard focus, screen-reader live announcements, problem-mode blocking, and that uploaded video is never sent to the API.

## Definition of done

- The demo path works without paid credentials and is visibly labeled.
- Real adapters fail closed when unconfigured.
- Low-confidence and answer content cannot leak through UI, TTS, review, or API source text.
- Uploaded subtitles and passages are actually processed.
- Documentation distinguishes implemented, deterministic demo, and adapter-required features.
