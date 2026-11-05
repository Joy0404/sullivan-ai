# Codex 시작 프롬프트 (복사해서 붙여 넣기)

- 작업 하나 = 새 Codex 세션 하나.
- 아래 블록을 그대로 붙여 넣으면 Codex가 **계획만** 먼저 보여준다. 계획이 맞으면 `진행해`라고 입력한다.
- 자세한 내용은 모두 `docs/redesign/RESKIN_PLAYBOOK.md`에 있다. 프롬프트는 "어느 절을 읽을지"만 알려준다.

---

## T0 규칙 등록
```
목표: 리스킨 작업 규칙을 저장소에 등록한다.
맥락: docs/redesign/RESKIN_PLAYBOOK.md 의 0, 2, 7(T0), 9절만 읽어라.
제약: AGENTS.md 기존 내용은 지우지 말고 맨 아래에 10줄 이내로 추가. .gitignore 에 docs/redesign/refs/ 추가. 다른 파일 수정 금지.
완료 기준: 변경 diff만 보여주고, git status 에 refs 이미지가 나오지 않는지 확인해. 먼저 계획만 보여줘.
```

## T1 보호자 소개 랜딩 + 사용 가이드
```
목표: 로그인 없이 보는 보호자 소개 페이지 /intro/ 와 사용 가이드 /guide/ 를 만든다.
맥락: RESKIN_PLAYBOOK.md 1, 2, 3, 5, 6, 7(T1), 9, 10절. 레퍼런스는 refs/ 의 R1a, R1b, R1c, R2a, R2b, R3a, R3c, R3d, R5 만 열어 봐.
      스킬: frontend-design 과 hallmark 로 방향 → 구현 → web-design-guidelines → accessibility → hallmark 마무리 점검. 각 스킬은 SKILL.md 를 먼저 읽고 따라.
제약: 플레이북 2절 범위만 수정. 레퍼런스 복제 금지. 서버 코드 수정 금지.
완료 기준: 플레이북 9절 + T1 완료 기준, 10절 형식으로 보고. 먼저 계획만 보여줘.
```

## T2 보호자 홈 (준비 현황)
```
목표: 보호자 준비실 첫 화면을 할 일 목록 + 학생 + 강의 + 도움 패널 구조로 바꾼다.
맥락: RESKIN_PLAYBOOK.md 2, 4(A1~A6, M), 5, 6, 7(T2), 9, 10절. 이미지는 current/D1, D6, D7 과 refs/R4, R7a, R7b.
      스킬: hallmark(방향, 5-2 설정 사용) → 구현 → web-design-guidelines → accessibility → hallmark 마무리.
제약: 학생 화면 파일·함수 수정 금지(플레이북 2절). API 형식 변경 금지.
완료 기준: 세 상태 캡처(학생 0명 / 강의 0개 / 배정 완료), 10절 형식 보고. 먼저 계획만 보여줘.
```

## T3 강의 등록 3단계 마법사
```
목표: 강의 등록 긴 폼을 3단계 마법사로 나눈다.
맥락: RESKIN_PLAYBOOK.md 2, 4(B1~B6), 5, 6, 7(T3), 9, 10절. 이미지는 current/D2 와 refs/R6a, R6b, R7a, R8.
      스킬: hallmark → 구현 → web-design-guidelines → accessibility(폼 오류·포커스 중점) → hallmark 마무리.
제약: 폼 name 과 제출 데이터는 그대로. 동의 원문 삭제 금지.
완료 기준: 단계별 캡처 3장 + 오류 캡처, 10절 형식 보고. 먼저 계획만 보여줘.
```

## T4 결과 검토 → 배정, 용어 정리
```
목표: 분석 결과를 먼저 보여주고 배정은 하단 고정 바로 옮기며, 보호자 화면 용어를 쉬운 말로 바꾼다.
맥락: RESKIN_PLAYBOOK.md 2, 4(C1~C4, D1, E1), 7(T4), 8, 9, 10절. 이미지는 current/D3, D4, D5.
      스킬: 구현 → web-design-guidelines → accessibility → hallmark 마무리.
제약: body[data-role="guardian"] 에서만 바뀌게. 내부 코드값은 데이터는 두고 표시만 매핑.
완료 기준: 8절 용어 전부 반영, 10절 형식 보고. 먼저 계획만 보여줘.
```

## T5 (선택) 보호자용 학습 현황
```
목표: 보호자가 학생별 강의 진도(위치, 밑줄·북마크·메모 개수)를 보게 한다.
맥락: RESKIN_PLAYBOOK.md 1(서버 구조), 7(T5), 9, 10절. apps/api/app/local_access.py 의 progress 테이블.
      스킬: security-best-practices 로 권한 검사 확인 → accessibility 로 카드 확인.
제약: 읽기 전용 GET API 1개만. 메모 본문은 보내지 않음. 보호자 본인 학생만.
완료 기준: 403 테스트 2개(다른 보호자, 학생 본인), 카드 캡처, 10절 형식 보고. 먼저 계획만 보여줘.
```

## T6 학생 화면 버그 2건
```
목표: ① 강의를 열면 자동 재생되는 문제 ② 로그인 이름 pattern 정규식 오류를 고친다.
맥락: RESKIN_PLAYBOOK.md 4절 마지막 문단, 7(T6), 10절.
제약: 스타일·레이아웃 변경 금지. 원인 파일만 최소 수정.
완료 기준: 열고 3초 뒤 재생 위치가 그대로인 테스트, 콘솔 pattern 오류 0, 기존 학생 테스트 통과. 먼저 원인 분석만 보여줘.
```
