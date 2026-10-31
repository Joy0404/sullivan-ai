> 현재 배포는 **Render Free + Neon PostgreSQL**입니다. 유료 디스크는 생성하지 않습니다. 최신 설정은 [DEPLOY_RENDER.md](DEPLOY_RENDER.md)를 따르세요.

# Sullivan AI · Render 공개 체험판

FastAPI 하나가 웹 화면과 API를 같은 주소에서 제공합니다. Render 배포 방법은
[DEPLOY_RENDER.md](DEPLOY_RENDER.md)를 따르세요.

## 실행 및 검증

샘플 미리보기: `docker compose up --build` 후 로컬 8080 포트에서 확인합니다.
Windows에서는 Docker Desktop 실행 후 `RUN_WINDOWS.bat`을 사용할 수 있습니다.

개발 실행: `pip install -r apps/api/requirements.txt` 후 `apps/api`에서
`uvicorn app.main:app --host 0.0.0.0 --port 8080 --no-proxy-headers --no-access-log`.
별도 웹 서버는 필요하지 않습니다. `/health`가 서버 상태를 반환합니다.

전체 검사: `sh scripts/verify_all.sh`.
API 검사: `cd apps/api && PYTHONPATH=. python -m pytest -q`.

## 작동 방식

- 별의 진화·왜란과 호란 샘플은 사전 준비된 결과이며 API 키·체험 코드 없이 작동합니다.
- 로컬 영상은 기본적으로 브라우저에서 재생합니다. 자막·지문·분석 JSON을 직접 처리합니다.
- 실제 분석과 Gemini 학습 대화는 사용자의 명시적 동의, 체험 코드, IP별 하루 3회 제한을 모두 통과해야 합니다.
- 하루는 한국 시간 자정 기준이며 실패·시간 초과를 포함해 공급자 호출을 시도한 횟수를 셉니다. 대화도 같은 한도를 사용합니다.
- 영상은 100,000,000바이트 이하, 분석은 180초에 취소합니다. 취소 후 파일 삭제는 별도 제한 시간 안에서 마칩니다.
- 링크 실제 분석은 기존 두 샘플 YouTube 영상만 허용합니다. 임의의 외부 링크 분석은 공개 API에서 실행하지 않습니다.
- 임시 로컬 파일과 Gemini 파일을 정리한 뒤에만 업로드 분석 결과를 완료 처리합니다. 삭제 확인 실패는 오류입니다.
- 확신도 0.72 미만의 시각정보와 문제 모드의 정답은 기존 안전 계층에서 차단합니다.
- 음성 안내·문단 탐색·밑줄 재생·브라우저 보관함을 유지합니다. 보관함에는 사용자가 저장한 원본이 남을 수 있습니다.

## 비밀정보

`GEMINI_API_KEY`, `DEMO_ACCESS_CODE`는 Render Environment에만 저장합니다.
브라우저에 API 키를 입력하거나 API 요청 본문으로 전달하지 않습니다.
`.env`, 캐시, 사용량 DB, 원본 영상은 Git·배포 ZIP에 포함하지 않습니다.

원본 ZIP에는 `.env`가 들어 있었으나 이 작업본에서는 제외했습니다. 원본 ZIP을 재배포하지 마세요.
기존 Git 이력은 제공되지 않아 검사할 수 없습니다.

## 자료

- [배포 안내](DEPLOY_RENDER.md)
- [로컬 실행](START_HERE.md)
- [테스트 계획](docs/TEST_PLAN.md)
- [안전·저작권](docs/SAFETY_COPYRIGHT.md)
- [분석 데이터 계약](docs/ANALYSIS_PACKAGE.md)
