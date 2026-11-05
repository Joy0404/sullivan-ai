# 소개 페이지 활동 안내 정렬 수정

사용자가 지적한 ‘지문·문단 듣기’부터 아래 활동의 글자가 밀린 문제는 소개에 삽입한 기존 학생 화면 PNG에 첫 항목과 나머지 항목의 여백이 다르게 담겨 있던 데서 발생했다.

학생 화면과 학생 CSS는 그대로 두고, 소개의 두 활동 안내를 실제 HTML 텍스트·목록·가이드 링크로 교체했다. 모든 항목에서 제목과 설명의 왼쪽 여백을 24px로 통일했다. 제목 20px·설명 18px, 최소 높이 104px이며 줄바꿈과 키보드 포커스를 확인했다. ‘구성 안내’이며 선택하면 가이드로 이동한다고 명시해 실제 화면 캡처와 구분한다. 나머지 실제 샘플 화면 이미지는 유지했다.

적용 스킬: frontend-design(기존 색·글꼴 유지, 일정한 여백·정렬), accessibility-lead의 키보드·ARIA·제목·대비 4종 전문 검토. 최종 지적 0건. 링크의 중복 aria-label을 제거해 보이는 제목·설명이 그대로 접근성 이름에 포함되게 했다.

- 320·390·640·1280·1920px 가로 넘침/잘린 제목 없음. 활동 링크 8개 모두 24px 여백.
- 390/1280px axe WCAG 2.2/모범 사례 위반 0건.
- Tab/Enter로 가이드 7단계 이동·펼침 확인, 둥근 경계 안 4px 포커스 표시 확인.
- `bash scripts/verify_all.sh`: 121 passed, 4 skipped, 1 warning. 기존 Postgres 4개는 환경 미설정.
- 학생 CSS·앱 JavaScript·서버·API·핵심 안전 로직 변경 없음. 레퍼런스 이미지 커밋 없음.
- 실제 스크린리더 낭독은 미검증.

[390px 화면](intro-alignment-390.png), [1280px 화면](intro-alignment-1280.png), [실측·axe 결과](intro-alignment-results.json), [전문 검토](intro-alignment-accessibility.md).

별도 요청인 3분 이내 OBS 시연은 [2:45 큐시트와 촬영 준비](../demo/HACKATHON_DEMO_3MIN_KO.md), [낭독용 대본](../demo/HACKATHON_VOICEOVER_KO.txt)에 작성했다. 실제 녹화·제출은 수행하지 않았다.
