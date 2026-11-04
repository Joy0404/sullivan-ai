# 세션·보호자 흐름 수정 및 검증

최근 재검사에서 확인한 3건을 수정했다. 추가로 이전 검사에서 별도로 기록했던 완료 직전 취소 포커스·오래된 링크 표시·샘플 배정 중 안내도 수정했다.

- **오래된 401:** 공통 요청이 시작할 때 브라우저 인증 세대를 저장한다. 로그인·로그아웃 때 세대를 바꾸고, 같은 세대의 401에만 화면 로그아웃을 적용한다. 학생 전환뿐 아니라 같은 보호자 재로그인도 보호한다. 현재 세션의 401은 계속 로그아웃·로그인 포커스로 처리한다. 서버 인증·쿠키·요청/응답 형식은 변경하지 않았다.
- **가이드 이미지:** 실제 샘플 UI를 1280×3000 뷰포트로 다시 촬영했다. 고정 바와 캡처 영역의 교차 면적이 0이고, 네 복습 카드 첫 항목이 모두 보임을 이미지로 확인했다. 자연 크기는 기존 962×1240과 같다. 조작 요소를 숨기거나 이미지를 합성하지 않았다.
- **동명이인:** 학생 카드 제목과 로딩·완료·빈 결과·실패 안내에 `이름 (로그인 이름)`을 사용한다. 긴 로그인 이름도 줄바꿈해 읽을 수 있다.
- **완료 직전 취소:** 제출 버튼이 다시 활성화되는 다음 마이크로태스크에서 포커스를 복원한다. 정상 결과/오류/다른 조작으로 옮긴 포커스를 빼앗지 않는다.
- **오래된 링크 표시:** 로그아웃으로 폼 값을 초기화할 때 링크 표시도 함께 초기화한다.
- **샘플 배정 안내:** 지속적인 polite status로 배정 중임을 학생 식별자와 함께 알린다. 완료는 기존 포커스 피드백으로 전달하며, 로딩 status를 비워 완료 문구가 중복 낭독되지 않게 한다.

## 검사 결과

- `bash scripts/verify_all.sh`: **121 passed, 4 skipped, 1 warning**. 정적/JavaScript/안전 검사 통과.
- `scripts/verify_guardian_sessions.py` 신규 저장소 회귀 검사 통과: 동명이인 식별, 이전 401 뒤 학생 로그인 유지, 같은 보호자 재로그인 유지, 오래된 200 무시, 현재 401의 정상 로그아웃, 링크 표시 초기화, 샘플 로딩 안내.
- `verify_roles_browser.py` 전체 통과. 100% 완료 지연 중 취소하는 회귀 검사를 추가했고, 기존 이른 취소·자료 처리·암호화 원본·학생 흐름도 유지한다.
- `verify_keyboard_navigation.py`, `verify_student_entry.py` 통과. 학생 첫 진입·92초 복원 후 3.1초 정지 유지 포함.
- 독립 ARIA/라이브 영역 재검토: 학생·동일 보호자 전환의 오래된 401 무시, 현재 401 처리, 60자 로그인 이름, 단일 로딩 상태·단일 완료 포커스 확인. 지적 0건.
- 독립 키보드 재검토 6개 통과: 이른/늦은 취소, 정상 완료, 서버 오류, 사용자 포커스 이동, 현재 401. 지적 0건.
- 보호자·펼친 가이드 390/1280px axe **0건**. 320/390/1280px 긴 로그인 이름 가로 넘침 없음.
- 학생 CSS·학생 함수·핵심 app.js·서버·안전 코드 변경 없음. 새로운 인증 세대는 클라이언트의 오래된 응답 판별용이며 서버 인증 방식은 같다. 레퍼런스 이미지는 추적하지 않는다.

실행한 검사에서는 이번에 확인된 실패가 재현되지 않았다. 소프트웨어 전체의 절대적인 무오류를 보장하지는 않는다. 실제 VoiceOver/NVDA 낭독·외부 영상/유료 분석은 미검증이며, 기존 Postgres 검사 4개는 환경 미설정으로 건너뛴다.

## 근거

[세션 회귀 결과](guardian-session-fix/session-results.json), [독립 세션 재검토](guardian-session-fix/independent-session-results.json), [포커스 재검토](guardian-session-fix/independent-focus-results.json), [역할 검사](guardian-session-fix/roles-results.json), [키보드 검사](guardian-session-fix/keyboard-results.json), [학생 진입 검사](guardian-session-fix/entry-results.json).

[접근성 통합 재검토](guardian-session-fix-accessibility.md), [axe 결과](guardian-session-fix-axe.json), [이미지 좌표·크기](guardian-session-fix/capture.json), [변경 범위](guardian-session-fix/scope.json).

화면: [1280px](guardian-session-fix-1280.png), [390px](guardian-session-fix-390.png), [가림을 제거한 실제 복습 캡처](../../apps/web/intro/img/guardian-review.png).
