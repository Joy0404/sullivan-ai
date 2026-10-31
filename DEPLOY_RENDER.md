# 무료 배포: Render Free + Neon PostgreSQL

현재 `render.yaml`은 **plan: free**이며 유료 영구 디스크를 생성하지 않습니다.
Render의 무료 사용량 한도 안에서만 운영하고 유료 업그레이드는 하지 않습니다.
Gemini 사용료는 별도이며, 무료 모델·할당량만 사용할 경우 해당 계정 조건을 확인하세요.

## 계정과 프로젝트

- GitHub: `Joy0404/sullivan-ai` (Private)
- Render 워크스페이스: 사용자가 확인한 `sullivan-ai`
- Neon 조직: 사용자가 지정한 `org-empty-cake-14402972`
- 새 Neon 프로젝트가 필요하면 Free 플랜, 프로젝트 이름 `sullivan-ai`, AWS Singapore를 사용합니다.
- 기존 프로젝트가 있으면 먼저 확인하고 재사용합니다. 같은 이름의 프로젝트를 중복 생성하지 않습니다.

2026-11-01: Neon CLI 인증과 기존 `sullivan-ai` 프로젝트(`morning-violet-94530569`) 연결을 완료했습니다.
운영 `production` 스키마와 Pooled 연결을 확인했고 두 DB 환경변수는 Render에 전달했습니다.
현재 상태는 `FREE_DEPLOY_STATUS.md`를 참고하세요.

## 환경변수 — Render 화면에서만 입력

| 변수 | 내용 |
|---|---|
| `DATABASE_URL` | Neon Connect 화면의 **Pooled** PostgreSQL 연결 주소 |
| `DATABASE_URL_UNPOOLED` | 같은 DB의 **Direct / pooling off** 연결 주소; 버전 관리된 스키마 초기화에 사용 |
| `GEMINI_API_KEY` | Gemini API 키. 무료 지원 모델·할당량을 별도로 확인 |
| `DEMO_ACCESS_CODE` | 사용자가 정한 체험 코드 |
| `TRUST_RENDER_PROXY` | `1` |

DB 주소에는 비밀번호가 들어 있으므로 채팅·Git·로그·로컬 `.env`·스크린샷에 넣지 않습니다.
Render의 Environment에서 직접 설정하거나, 연결된 관리 도구로 값이 노출되지 않게 전달합니다.
Render 운영에서는 PostgreSQL 연결에 TLS를 요구합니다.

## 배포

1. Render 무료 웹 서비스를 `Joy0404/sullivan-ai`, main, Dockerfile로 생성합니다.
2. 지역은 Singapore, 플랜은 **Free**, 디스크는 **없음**으로 둡니다.
3. Render가 제공하는 PORT를 사용합니다. 컨테이너가 웹과 API를 함께 제공합니다.
4. DB가 준비되면 위 환경변수를 입력하고 Save, rebuild, and deploy로 적용합니다.
5. 아직 DB·키를 입력하지 않았다면 샘플만 사용할 수 있으며 실제 분석은 차단됩니다.
6. 상태가 Live가 되면 `/health`와 `/`를 확인합니다.

Blueprint를 사용할 경우 아래 주소에서 `render.yaml`을 읽을 수 있습니다.
https://dashboard.render.com/blueprint/new?repo=https://github.com/Joy0404/sullivan-ai
처음에 입력하지 못한 환경변수는 서비스의 Environment에서 추가할 수 있습니다.
기존 유료 서비스·디스크가 있다면 이 파일을 변경하는 것만으로 기존 리소스가 삭제되지는 않습니다.
유료 리소스를 직접 확인해야 하며, 데이터 확인 없이 디스크를 삭제하지 않습니다.

## DB 초기화와 한도

`apps/api/app/db/migrations/001_demo_usage.sql`에 스키마를 버전 관리합니다.
첫 실제 분석 시 Direct 연결로 초기화를 실행하고, 일상적인 한도 확인·차감은 Pooled 연결을 사용합니다.
이미 스키마가 준비되어 있으면 Pooled 연결만으로 사용할 수도 있습니다.
DB에 저장하는 것은 날짜별 IP 해시와 사용 횟수이며 원본 IP·영상·API 키·체험 코드를 저장하지 않습니다.

한도 차감은 PostgreSQL의 단일 INSERT ... ON CONFLICT ... WHERE ... RETURNING 문으로 처리합니다.
여러 프로세스·동시 요청·Render 재시작에도 같은 IP와 한국 날짜의 한도는 3회를 넘지 않습니다.
DB 설정·연결·초기화 오류가 있으면 실제 분석을 차단합니다.

## 무료 서비스의 제약

- Render Free는 15분간 요청이 없으면 잠들며 다시 열릴 때 약 1분이 걸릴 수 있습니다.
- Render의 로컬 파일은 재시작 때 사라집니다. 운영 횟수는 Neon DB에 저장하므로 영향을 받지 않습니다.
- 무료 한도를 넘으면 서비스·빌드·DB가 제한될 수 있습니다. 유료 플랜으로 자동 전환하지 마세요.
- 임시 업로드 영상은 분석 성공·실패·시간 초과 후 삭제를 확인합니다. 분석 실패·삭제 실패는 완료가 아닙니다.
- 공개 URL의 실제 휴대폰 접속과 실제 Gemini 호출·공급자 파일 삭제는 배포 후 별도 확인합니다.

## 검증

`sh scripts/verify_all.sh`가 기존 검증과 새 DB 회귀 검사를 실행합니다.
GitHub Actions의 test 작업은 별도 로컬 PostgreSQL 16 테스트 DB에서 동시 한도·재초기화·날짜 변경을 검증합니다.
이 테스트 DB는 CI 안에서만 쓰는 가짜 비밀번호이며 실제 Neon 자격증명은 사용하지 않습니다.
`python scripts/smoke_service.py https://공개주소`는 유료 호출 없이 웹·API·샘플·차단 상태를 확인합니다.

공식 문서:
- https://render.com/docs/free
- https://neon.com/pricing
- https://neon.com/docs/connect/connection-pooling
