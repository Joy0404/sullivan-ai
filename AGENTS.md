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

## Redesign
- 리스킨 작업은 `docs/redesign/RESKIN_PLAYBOOK.md`의 해당 작업 절과 2·9절을 따른다.
- T6 외에는 `apps/web/student-design.css`와 학생 영역 `#portal-home`, `#learner-tools`, `#learning-records`, `#text-command-dialog`를 수정하지 않는다.
- T6 외에는 `apps/web/role-portal.js`의 학생 함수 `loadStudent`, `openLectureList`, `openLecture`, `purpose`, `play`, `command`, `records` 및 제스처 관련 함수를 수정하지 않는다.
- 서버 API 요청·응답 형식, 인증 방식, 폼 `name`, Gemini 키·모델·호출 설정은 변경하지 않는다.
- 완료 시 `bash scripts/verify_all.sh` 통과와 테스트 수 유지, 학생 CSS diff 없음(T6 제외)을 확인한다.
- 1280px·390px 화면 캡처를 `docs/verification/`에 저장한다.
- 키보드만으로 보호자 흐름(학생 만들기 → 샘플 준비 → 배정)을 완료한다.
- axe 위반 0과 `git status`에 레퍼런스 이미지가 포함되지 않음을 확인하며, `docs/redesign/refs/`는 커밋하지 않는다.
