# 전체 재검사 18건 수정 결과

로컬 **0.4.3에서 기존 재검사의 확정 문제 18건을 수정했고, 18건의 재현 회귀 검사가 모두 통과했다.** 학생·보호자 확장과 서버에 반영했다. 기존 웹 화면·디자인·Gemini 모델 설정은 변경하지 않았다. 이번 수정 단계에서는 커밋·GitHub 업로드·운영 배포를 하지 않았다.

검증일: 2026-11-14. 작업 폴더: `Sullivan-AI-Develop-local`. [수정 전 감사](EXTENSION_FULL_REAUDIT.md)의 실패 기록은 보존했다. [전체 회귀 결과](verification/2026-11-14-fixes/results.json), [강화한 문장·초점 검사](verification/2026-11-14-fixes/results-forms.json), [해결 상태와 소스 해시](verification/2026-11-14-fixes/resolution.json)를 함께 확인할 수 있다. 두 검사 실행의 제품 소스 해시는 일치한다.

## 수정한 동작

| 번호 | 수정 결과와 확인값 |
| --- | --- |
| R01 | 권한 요청 전 계정·강의·화면 세대를 고정하고, 완료 때 다시 검사한다. A의 권한을 기다리다 B로 이동해도 A 탭을 열거나 B에 연결하지 않는다. |
| R02 | 구간 이동의 늦은 응답을 폐기한다. B의 진도는 **42,000ms를 유지**하며 잘못된 진도 PUT은 0회였다. |
| R03 | 초점 안내·중지·화면 변경이 대기 중인 재생을 취소한다. 실제 MP4는 안내를 보류한 동안 계속 정지했다. |
| R04 | 탭 종료와 다른 수강 화면의 재생권 취득을 앱 음성과 기존 상태 영역에 알린다. 오류 안내 때문에 다른 화면의 재생권을 빼앗지 않는다. |
| R05 | 음성 시험으로 안내를 바꿔도 원래 재생 의도를 유지한다. 시험 종료 뒤 이전 재생이 복원됐다. |
| R06 | Shift+방향키가 강의 구간 이동을 실행하지 않는다. |
| R07 | Space 명령을 끄면 편집 중 두 번 누르기 중지도 실행하지 않는다. 켠 경우의 긴급 중지는 유지한다. |
| R08 | 텍스트 명령창을 다시 열면 이전 실행 명령과 대화상자 반환값을 비운다. |
| R09 | 속도·앱 음량·음높이·영상 음량의 현재 숫자와 단위를 안내한다. 소수점이 문장 분리로 잘리지 않게 처리했다. 비밀번호·자유 입력값은 이 안내 대상이 아니다. |
| R10 | 강의 선택 전에도 표시되고 활성화된 홈 버튼 명령을 실행한다. 실제 권한·마이크 허용이 필요한 버튼은 초점 이동 후 Enter로 확인한다. |
| R11 | 계정의 읽기 방식을 로그인 후 첫 초점 이동보다 먼저 적용한다. 외부 스크린리더 계정의 세션 복원·명시적 로그인 모두 앱 합성 요청 0회였다. |
| R12 | 보호자 미리보기 질문 실패를 재시도 가능한 최종 오류로 바꾼다. 다른 준비 결과로 이동한 뒤 도착한 이전 오류는 새 결과를 덮지 않는다. |
| R13 | 다시 준비하면 1단계로 돌아가며 제목·자료·동의·검증 상태와 최종 요약을 새 작업에 맞춰 초기화한다. |
| R14 | 자료 전체 한도 초과를 제한값·줄이는 방법과 함께 표시하고 자료 입력으로 초점을 옮긴다. 브라우저가 초과 제출을 막으며, 서버도 해당 한도 오류에 구체적인 안내를 반환한다. |
| R15 | 문장별 기본 버튼, 현재 문장 표시, 글자로 된 강조 표시를 제공한다. 2문단·4문장 자료에서 문단 선택 뒤 다음 문장 위치도 맞게 이어졌다. |
| R16 | 음성 밑줄 명령으로 지문을 다시 그려도 원래 문장의 초점을 복원한다. |
| R17 | 늦은 강의 조회·저장이 입력 중인 초점을 빼앗지 않는다. 두 경로 모두 명령 입력칸에 초점이 남았다. |
| R18 | 목록에서 초점을 가진 강의가 사라지면 인접 강의 또는 작업 영역 제목으로 복원한다. 빈 목록에서는 제목에 초점이 남았다. |

인접 경계도 확인했다. 연결 요청의 응답을 기다리는 중 전체 중지를 누르면, 아직 연결 종류가 정해지지 않았어도 원본 영상이 정지한다. 명령창 취소의 재생 복원과 개념 구간 재생도 기존 누적 회귀에서 통과했다.

## 검증 범위

| 검사 | 결과·근거 |
| --- | --- |
| 정적·JS 코어·API·패키지 | API **153 통과·4 건너뜀**, 패키지 3개와 나머지 검사 통과. [실행 로그](verification/2026-11-14-fixes/verify-all.log). PostgreSQL 실DB 4개는 환경 부재로 건너뛰었다. |
| 기존 전체 확장 복원 회귀 | 통과. 실제 설치한 두 확장·PKCE·계정 연결·실제 Chrome 사이드 패널·디코딩 MP4·Space·키보드·준비·배정·저장·복구를 누적 검사했다. [결과](verification/extension-feature-restoration-results.json). |
| 확정 오류 전용 회귀 | 독립 프로필 4그룹 통과, R01–R18 전부 통과. 추가 기능 관찰 30개도 모두 통과했다. [전용 스크립트](../scripts/verify_reaudit_fixes.py), [관찰값](verification/2026-11-14-fixes/supplement/observations.json). CI에서도 실행하도록 추가했다. |
| 접근성 자동·구조 검사 | 누적 복원 회귀 14개 상태에서 axe 위반 0건. 추가 폼·초점·오류 화면도 위반 0건. 390px·1280px 화면을 저장했다. [추가 폼 결과](verification/2026-11-14-fixes/forms/extension-fixed-forms-results.json), [전문 소스 검토](../.a11y-history/2026-11-14-fixes/report.md). |
| 준비 작업 재시작·운영 설정 | 통과. 실제 프로세스 재시작 2회와 운영 설정 시작·거부를 확인했다. [재시작](verification/extension-preparation-restart-results.json), [운영 설정](verification/extension-production-results.json). |

임시 DB·브라우저 프로필·서버와 생성한 영상을 사용했다. 영상·API·DB·worker는 실제로 실행했다. 음성 합성·인식과 지연 응답·권한 완료는 명시적인 시험 장치다. 실제 사용자 DB와 유료 공급자 자격은 사용하지 않았다. 전문 검토와 axe 통과는 실제 스크린리더 낭독 검증을 대신하지 않는다.

재현 명령은 다음과 같다. 브라우저 검사 의존성은 `scripts/requirements-extension-tests.txt`, Chromium, ffmpeg, axe-core다. 이 환경의 ffmpeg 보조 경로는 `/tmp/sullivan-video-test`다.

```bash
PATH="$PWD/.venv/bin:$PATH" bash scripts/verify_all.sh
PYTHONPATH=/tmp/sullivan-video-test SULLIVAN_AXE_SOURCE=/tmp/sullivan-extension-a11y/node_modules/axe-core/axe.min.js .venv/bin/python scripts/verify_feature_restoration.py
PYTHONPATH=/tmp/sullivan-video-test SULLIVAN_AXE_SOURCE=/tmp/sullivan-extension-a11y/node_modules/axe-core/axe.min.js .venv/bin/python scripts/verify_reaudit_fixes.py
.venv/bin/python scripts/verify_preparation_restart.py
.venv/bin/python scripts/verify_extension_production.py
```

## 원본 기능 대응과 남은 확인

[78개 대응표](verification/2026-11-14-fixes/feature-inventory.json)는 **적용 확인 61·부분 적용 4·미적용 0·의도 변경 4·검증 불가 7·기존 미지원 2**다. 78개 모두를 실서비스에서 시험했다는 뜻은 아니다. 수정 전 판정과 문제 번호도 각 항목에 보존했다.

부분 적용 4개는 준비 현황 대시보드의 상세 단계, 공급자 내부 진행률, 실제 강의 사이트 호환성, 보호자에서 학생으로 원본 파일 자동 전달이다. 원본 파일은 별도로 전달하고 학생 기기에서 선택하는 현재 경계를 유지한다.

외부 확인 7개는 실제 YouTube 분석, 업로드 영상 분석 품질, 외부 링크 분석기, OS·코덱 조합, 실제 Gemini 학습 대화, VoiceOver/NVDA 전체 사용, 실제 마이크·Chrome 인식 서비스다. 사람이 듣는 한국어 음질과 실제 대상 사이트 플레이어도 별도 확인이 필요하다. 따라서 이번 결과는 확정된 로컬 오류의 수정 완료이며 스토어 출시 판정은 아니다.

## 로컬 적용

현재 작업 폴더의 샘플 서버도 다시 시작해 학생·보호자 API 버전 0.4.3과 정상 상태를 확인했다. 주소는 `http://127.0.0.1:8770`이며 실제 유료 분석은 꺼져 있다. [서버 확인 결과](verification/2026-11-14-fixes/local-server-results.json).

생성한 폴더는 `dist/extensions/student`, `dist/extensions/guardian`, ZIP은 `dist/releases/0.4.3/`에 있다. Chrome의 `chrome://extensions`에서 **두 확장을 새로고침하고, 열려 있던 기존 확장 탭과 학생 패널을 닫은 뒤 다시 연다.** 각 확장의 버전 0.4.3을 확인한다. ZIP은 로컬 개발용 서버 주소를 사용하며 스토어에 게시하지 않았다.

다시 생성할 때는 프로젝트 루트에서 다음을 실행한다.

```bash
.venv/bin/python scripts/build_extensions.py
.venv/bin/python scripts/package_extensions.py
```
