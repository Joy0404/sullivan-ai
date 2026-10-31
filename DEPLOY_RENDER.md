# Sullivan AI Render 배포

비공개 GitHub 저장소 `Joy0404/sullivan-ai`의 `render.yaml`이 설정의 기준입니다.
FastAPI 하나가 웹과 API를 같은 공개 HTTPS 주소에서 제공합니다.

## 구성과 비용

- 워크스페이스: 사용자가 확인한 `sullivan-ai`
- 서비스: `sullivan-ai`, Docker, Singapore, 단일 인스턴스·worker
- 컴퓨트: `0.5c-512mb` (기존 명칭 Starter)
- 영구 디스크: `/var/data`, 1GB. 영상은 이 디스크에 저장하지 않습니다.
- 상태 확인: `/health`, 포트: Render가 제공하는 `PORT` (기본 10000)
- 공개 요금 기준 서버 $7 + 디스크 $0.25로 월 약 $7.25부터. Gemini 사용료·초과 사용량·세금은 별도입니다.

무료 플랜은 영구 디스크를 지원하지 않으므로 사용하지 않습니다.
메모리 기록 대신 디스크의 SQLite를 사용해 재시작·재배포 후에도 한도를 유지합니다.
디스크가 실제로 마운트되지 않았거나 DB가 디스크 밖이면 실제 분석은 차단됩니다.
단일 인스턴스 제약이 있으며 디스크 서비스 재배포 시 잠깐 중단될 수 있습니다.

## 배포 순서

1. Render Dashboard에서 아래 Blueprint 링크를 엽니다.
   https://dashboard.render.com/blueprint/new?repo=https://github.com/Joy0404/sullivan-ai
2. GitHub 연결이 별도로 요청되면 비공개 저장소 `Joy0404/sullivan-ai`에 접근을 허용합니다.
3. 워크스페이스 `sullivan-ai`, 브랜치 `main`, 서비스·디스크·요금을 확인합니다.
4. `GEMINI_API_KEY`와 `DEMO_ACCESS_CODE`를 **Render 화면에서 직접** 입력합니다. 채팅·파일·GitHub에 값을 넣지 마세요.
5. Apply/Deploy Blueprint로 생성합니다. 현재 연결 도구는 영구 디스크·Blueprint 생성 기능을 제공하지 않아 이 최초 적용은 Dashboard에서 해야 합니다.
6. 배포가 Live가 될 때까지 확인하고 `https://서비스주소.onrender.com/health`와 `/`를 엽니다.
7. 이후 `main` 변경은 CI 검사가 통과하면 자동 배포됩니다.

배포가 Live라는 상태와 실제 Gemini 호출이 성공했다는 상태는 다릅니다. 실제 호출은 아래 체크를 별도로 진행합니다.

## 환경변수

| 변수 | 설정 |
|---|---|
| `GEMINI_API_KEY` | 사용자가 Render Environment에서 직접 입력하는 실제 키 |
| `DEMO_ACCESS_CODE` | 사용자가 정한 체험 코드; Render에만 저장 |
| `DEMO_USAGE_DB` | `/var/data/demo_usage.sqlite` |
| `DEMO_DATA_DIR` | `/var/data` |
| `TRUST_RENDER_PROXY` | `1` |
| `DEMO_DAILY_LIMIT` | `3`; 코드에서도 최대 3으로 제한 |
| `MAX_UPLOAD_VIDEO_BYTES` | `100000000`; 코드에서도 최대 100MB로 제한 |
| `ANALYSIS_TIMEOUT_SECONDS` | `180`; 코드에서도 최대 180초로 제한 |
| `ALLOWED_SAMPLE_VIDEO_IDS` | `R0dqsl3Vgns,thJxqtTgSNY` |
| `GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL`, `GEMINI_AGENT_MODEL` | 계정에서 사용 가능한 모델; 기본 `gemini-2.5-flash` |

`RENDER=true`와 `PORT`는 플랫폼이 제공합니다. Blueprint의 비밀값은 `sync: false`이며 파일에는 실제 값을 저장하지 않습니다.
나중에 비밀값을 수정할 때는 서비스 Environment에서 바꾸고 변경을 반영하는 배포를 실행하세요.

## IP와 일일 한도

Render의 공개 Cloudflare 경로가 덮어쓰는 `CF-Connecting-IP`만 신뢰합니다.
`X-Real-IP`, `True-Client-IP`, 임의의 `X-Forwarded-For`로 우회할 수 없도록 대체 경로를 사용하지 않습니다.
값 누락·형식 오류·신뢰 설정 누락 시 실제 분석은 차단됩니다. Uvicorn 프록시 헤더 자동 처리는 꺼 둡니다.
기본 Render 공개 도메인으로 직접 접속하세요. 별도 앞단 프록시나 사설 네트워크 호출에서는 이 IP 설정을 그대로 사용하지 마세요.

하루는 한국 시간 자정 기준입니다. 링크 분석·업로드·Gemini 학습 대화가 한도를 공유합니다.
동의·코드·기본 입력 검사를 통과한 분석 시도는 실패·시간 초과도 1회로 기록합니다.
SQLite 트랜잭션으로 동시 요청을 제한하며 서비스 시작 때 기록을 초기화하지 않습니다.
서버는 디스크의 루트 디렉터리 권한을 준비한 뒤 UID 10001로 권한을 낮춰 실행합니다.

## 검증

```sh
sh scripts/verify_all.sh
python scripts/audit_git_history.py
python scripts/smoke_service.py https://서비스주소.onrender.com
```

Git 이력 검사는 `.git`이 있는 체크아웃에서 실행합니다. ZIP만으로 과거 이력을 복원할 수는 없습니다.
서비스 검사는 키 없이 웹·API·샘플·동의 차단을 확인하며 유료 Gemini 호출을 하지 않습니다.

실제 배포 후 추가 체크:

- 휴대폰의 실제 브라우저와 시크릿 모드에서 화면 열기
- 키·코드 없이 두 샘플 실행, 화면·Network에 개발용 호스트 요청이 없는지 확인
- 동의 미체크·잘못된 코드·허용되지 않은 영상 차단
- 실제 동의와 코드 입력 후 지정 샘플 또는 직접 제작한 100MB 이하 영상 분석
- 성공·실패 후 임시 로컬·Gemini 파일 삭제 확인
- 같은 IP의 네 번째 요청 차단 및 같은 날 재배포 후에도 차단 확인

분석은 180초에 취소하며 원격 삭제에 최대 30초가 추가될 수 있습니다.
삭제 실패·삭제 확인 불가는 HTTP 오류이고 강의 분석 결과를 완료 처리하지 않습니다.
네트워크 단절·프로세스 강제 종료 시 즉시 삭제를 보장할 수 없으며 운영자가 공급자 파일 상태를 확인해야 합니다.

## 문제 확인

- 503 IP 오류: `TRUST_RENDER_PROXY=1`, Render 공개 도메인, `CF-Connecting-IP` 전달 확인
- 503 저장소 오류: 유료 서버의 `/var/data` 디스크 연결, DB 경로·쓰기 권한 확인
- 429: 한국 시간 자정까지 기다림. 동시 접속자가 같은 공인 IP를 공유하면 한도도 공유
- Gemini 오류: Environment의 실제 키, API 권한·할당량·지원 모델 확인. 오류 원문에 키를 붙여 넣지 않음
- 삭제 오류: 완료로 보지 말고 운영자가 남은 파일 확인·삭제
- 새 배포 후 세션 없음: 강의 세션은 메모리 저장이므로 다시 열어야 함. 일일 사용량 DB는 유지

## 공식 근거

- https://render.com/docs/web-services
- https://render.com/docs/disks
- https://render.com/docs/blueprint-spec
- https://render.com/docs/configure-environment-variables
- https://render.com/articles/host-pocketbase-on-render — Render의 CF-Connecting-IP 덮어쓰기 설명
- https://render.com/articles/render-vs-railway — 서버 요금
- https://render.com/articles/how-much-does-cloud-application-hosting-cost-for-small-businesses — 디스크 요금
