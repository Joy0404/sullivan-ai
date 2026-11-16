# 2026-11-16 프로젝트 기능 검사

이 문서는 수정 전 검사 기록이다. 이후 조치와 최신 검증은 [후속 수정 보고서](../../PROJECT_AUDIT_FIXES_2026-11-16.md)를 참고한다.

검사 결과: **실제 기능 오류 1건과 검증 체계의 회귀를 확인했다. 전체 정상 판정은 불가하다.**

현재 미커밋 작업본을 대상으로 검사했다. 앱·API·기존 검사 소스는 변경하지 않았고 이 폴더에 검사 증거만 추가했다. 기존 학생 CSS diff와 `docs/redesign/refs/`의 git 상태 변화는 없다. 기존 tracked diff는 검사 전후 모두 38개 파일, 1818줄 추가·375줄 삭제다.

## 1. P1: 학생 전환 중 이전 학생의 메모가 새 학생에게 저장됨

위치: [notes.js의 start 함수](../../../apps/extensions/student/notes.js#L101), [기존 메모 복사 호출](../../../apps/extensions/student/notes.js#L182).

영상 정지 완료 응답이 늦는 동안 학생 A가 로그아웃하고 학생 B가 로그인하면, A가 시작한 기존 메모 복사 작업이 B의 필기로 이어질 수 있다. 임시 계정·실제 설치 확장·실제 API/DB에서 **독립적으로 두 번 재현**했다. 두 번째 검사는 메모 입력과 서버 저장도 실제 UI로 수행했다. 지연시킨 경계는 영상 정지 응답 하나다. 유료 공급자나 실제 사용자 데이터는 사용하지 않았다.

재현 순서:

1. 학생 A의 강의에서 한 칸 메모를 저장한다.
2. `기존 한 칸 메모를 새 필기로 복사`를 누르고 영상 정지 응답을 대기시킨다.
3. A가 로그아웃한 뒤 학생 B로 로그인하고 B의 강의를 연다.
4. 이전 정지 응답을 완료시킨다.
5. B의 필기 API에서 A의 본문이 새 항목으로 저장된 것을 확인한다.

`start()`는 `await flush()`와 `await pause()` 이후 계정·강의·epoch를 재확인하지 않는다. 그동안 `reset()`/`load()`가 바꾼 새 `scope`를 `persist()`와 `save()`가 사용한다. 같은 파일의 `edit()`에는 이 재확인이 있지만 `start()`에는 없다. API는 새 학생의 정상 자격으로 온 본문을 저장하므로 클라이언트에서 이전 복사 작업 전체를 취소해야 한다.

수정 시 시작한 계정·강의·epoch를 각 비동기 경계 뒤에 재검사하고, 취소된 `start()`의 호출자가 `save(true)`를 계속 실행하지 않도록 해야 한다. 계정 전환과 강의 전환 각각의 회귀 검사가 필요하다.

증거: [첫 재현](note-race/result.json), [UI 저장을 포함한 재확인](note-race-confirm/result.json), [새 학생 화면](note-race-confirm/cross-account-note.png).

재현용 스크립트: [reproduce-note-account-race.py](reproduce-note-account-race.py). 저장소 루트에서 아래처럼 실행한다. 임시 계정·DB·브라우저 프로필만 사용한다.

```bash
.venv/bin/python docs/verification/2026-11-16-project-audit/reproduce-note-account-race.py
```

## 2. P2: 전체 확장 검증이 새 화면 구조를 따라가지 못함

기본 `verify_all.sh`에는 브라우저 종합 검사가 포함되지 않는다. `verify_extensions.py`의 구성 검사 13그룹을 별도로 실행했으며, **6그룹 통과·7그룹 실패**다. 보고서 경로가 고정된 일부 검사는 같은 함수를 새 증거 경로로 호출했다. 재시작·운영 검사의 기존 결과 파일은 검사 후 원래 내용으로 복원했다.

| 그룹 | 결과 | 관찰 |
| --- | --- | --- |
| student-notes | 통과 | 현재 UI, 실제 키보드·네이티브 패널·필기 저장/복구·보관·내보내기 |
| dashboard | 통과 | 보호자 단계별 준비 상태 |
| remote-login | 통과 | 연결·기기 동의·보호자가 시작하는 학생 로그인 |
| guardian-entry | 통과 | 보호자 진입·키보드 배정 |
| restart | 통과 | 실제 서버 프로세스 2회 재시작, 완료/중단 상태 보존 |
| production | 통과 | 설정 미완료 시작 거부·역할/버전/출처 제한 |
| followup | 실패 | Notes 화면에서 Settings의 숨겨진 `#access-mode`를 조작하다 시간 초과 |
| races | 실패 | 현재 작업에 없는 숨겨진 `#refresh` 조작에서 시간 초과 |
| submission-flow | 실패 | 숨겨진 `#access-mode` 조작에서 시간 초과 |
| universal | 실패 | 누적 phase2의 숨겨진 `#refresh` 조작에서 시간 초과 |
| restoration | 실패 | 누적 phase2의 숨겨진 `#refresh` 조작에서 시간 초과 |
| reaudit | 실패 | 여러 그룹이 동일한 작업 전환 문제로 중단; 18건 전체 확인 불가 |
| optimization | 실패 | 숨겨진 `#refresh` 조작에서 시간 초과 |

이 7건을 실제 제품 기능 7개가 고장났다는 뜻으로 해석하면 안 된다. 작업 선택 버튼으로 적절한 화면을 여는 전제 단계가 검사 코드에 필요하다. 현재 종합 검증은 실패하므로 기능 대응표의 파일·마커 검사 통과만으로 전체 동작을 보장할 수 없다.

증거: [그룹별 종료 코드](browser-checks.json), [followup 로그](followup.log), [누적 재검사 결과](reaudit/results.json).

## 3. 기존 웹 검사: 4그룹 통과·3그룹 실패

| 그룹 | 결과 | 관찰 |
| --- | --- | --- |
| keyboard_navigation | 통과 | Space 조합, 기본 입력, 키보드 이동 |
| student_entry | 통과 | 학생 진입·안내 |
| guardian_sessions | 통과 | 보호자 세션 |
| login_startup | 통과 | 로그인 시작 |
| roles_browser | 실패 | Space를 누른 직후 동기적으로 재생을 단정 |
| voice_preferences | 실패 | Space 후 240ms에 상태 음성을 확인 |
| audio_navigation | 실패 | 학생 음성·재생 확인 이후 보호자로 전환해 샘플 미리보기를 여는 마지막 단계에서 시간 초과 |

앞의 두 검사는 현재 Space 연속 입력 판정 시간 420ms와 맞지 않는다. 음성 설정 검사는 Space 뒤 여유를 준 진단 실행에서 전체 통과했다. 역할 검사도 여유를 주면 최초 재생 확인 단계를 통과했다. 다만 모든 Space에 지연을 넣은 진단 실행은 연속 입력 자체를 바꾸므로 전체 통과의 근거로 사용하지 않았다.

`audio_navigation`의 보호자 미리보기 실패는 별도 진단에서도 관찰했다. 당시 역할은 guardian이었고 session은 null, 미리보기는 숨김, page error는 없었다. 이 실패의 원인이 검사 타이밍인지 제품 동작인지 확정하지 않았으므로 웹 전체 정상 판정에서 제외한다.

증거: [웹 종료 코드](web-checks.json), [음성 설정의 지연 후 통과](web-delayed-voice_preferences.log), [보호자 미리보기 진단](web-audio-diagnostic/docs/verification/diagnostic.json).

## 4. 통과한 기본 검사와 안전 경계

- `PATH="$PWD/.venv/bin:$PATH" bash scripts/verify_all.sh`: 통과.
- API pytest: **281개 통과·4개 건너뜀**. 건너뛴 4개는 전용 PostgreSQL 시험 DB 미설정 때문이다.
- 제출 패키지 pytest: **15개 통과**. 별도 확장 빌드 경계 unittest 3개와 JS 구문·기능 검사도 통과했다.
- 기존 회귀 검사에서 저확신도 HOLD, 문제 모드 정답 차단, 필기 원문 재검증, 분석 상태/샘플 구분, 실제 분석 동의·임시 파일 처리, 학생 원본의 API 비전송을 확인했다. 위 계정 간 메모 경합은 이 통과 결과와 별개로 존재한다.
- 현재 학생 필기 브라우저 검사에서 학생 만들기→샘플 준비→배정을 Tab·키보드 입력·Enter로 완료했다.
- 기록된 axe 검사에서 위반 0건이다. 390px·1280px 캡처를 각 하위 폴더에 보존했다. 실제 보조기기 낭독 검증을 의미하지 않는다.
- 로컬 `dist/extensions`의 역할별 JS는 현재 소스와 일치했다.

증거: [기본 검증 로그](verify-all.log), [학생 필기 결과](student-notes/extension-student-notes-results.json), [재시작](extension-preparation-restart-results.json), [운영 설정](extension-production-results.json).

## 5. 누락과 의도된 범위 변경의 구분

78개 기능 대응표는 구조 검사를 통과했다. 이는 구현 파일·연결 표식이 존재한다는 의미이며 모든 기능의 실환경 통과 증거가 아니다.

2026-11-16 승인된 학생 확장의 발표문·암기표·복습 계획 등 생성 패널 제거는 의도된 범위 변경이다. 원본 파일을 보호자 기기에서 학생 기기로 자동 전달하지 않는 것도 명시된 설계다. DRM 우회와 복잡한 도형 완전 해설은 지원 범위 밖이다. 이 항목들을 새 기능 누락으로 세지 않았다.

실환경 검증이 남은 8개 항목은 실제 YouTube Gemini 분석(F24), 업로드 STT/OCR 분석 및 비정상 종료 시 삭제(F25), 외부 링크 분석 어댑터(F26), OS/코덱별 파일 재생(F33), 실제 사이트·YouTube·권한창 호환(F34), 실제 Gemini 학습 대화(F49), VoiceOver/NVDA 전체 흐름(F61), 실제 마이크·음성 인식(F62)이다. 이번 검사에서는 유료 호출·사람이 듣는 음질·실제 스크린리더를 시험하지 않았다.

가장 먼저 수정할 항목은 **P1 메모 복사 경합**이다. 이어서 작업 전환과 Space 대기 조건을 종합 검사에 반영하고, 보호자 미리보기 실패를 분리 재현한 뒤 전체 브라우저 검증을 다시 통과시켜야 한다.
