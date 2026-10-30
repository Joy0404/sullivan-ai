# Render 배포 안내 (GitHub 비공개 저장소 기준)

Railway 신규 가입이 중단된 동안 쓰는 배포 방법입니다. 같은 `Dockerfile`로 컨테이너 하나를 띄우며, FastAPI가 API와 웹 화면을 **같은 공개 주소**에서 함께 제공합니다. 동작 규칙(체험 코드, 하루 3회, 100MB, 3분 제한, 샘플 영상 목록, 파일 삭제 안내)은 [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md)의 4번과 같습니다.

- 설정 파일: 저장소 루트의 `render.yaml` (Blueprint)
- 플랜: `free`, 지역: `singapore` (한국에서 가장 가까운 지역, 만든 뒤 바꿀 수 없음)
- 포트: Render가 넣어 주는 `PORT`(기본 10000)를 사용합니다. 직접 설정하지 않습니다.
- 상태 확인: `/health`

## 1. Environment 변수

`render.yaml`에 비밀이 아닌 값은 미리 들어 있습니다. **비밀 값 두 개만** 처음 만들 때 Render 화면에서 직접 입력합니다.

| 이름 | 입력 방법 | 설명 |
|---|---|---|
| `GEMINI_API_KEY` | 생성 화면에서 직접 입력 | 비밀. 새로 발급한 키를 넣습니다. |
| `DEMO_ACCESS_CODE` | 생성 화면에서 직접 입력 | 비밀. 직접 정한 체험 코드 |
| `DEMO_DAILY_LIMIT` | 자동 (`3`) | 같은 IP 하루 실제 분석 횟수 |
| `ALLOWED_SAMPLE_VIDEO_IDS` | 자동 | 실제 분석을 허용할 YouTube 영상 ID |
| `ANALYSIS_TIMEOUT_SECONDS` | 자동 (`180`) | 분석 제한 시간(초) |
| `MAX_UPLOAD_VIDEO_BYTES` | 자동 (`104857600`) | 업로드 최대 100MB |
| `GEMINI_MODEL` 등 | 자동 | `gemini-2.5-flash` |
| `CLIENT_IP_HEADER` | 선택 | 방문자 IP를 담은 헤더 이름을 고정할 때만 입력 |

비밀 값은 나중에 서비스 → **Environment** 탭에서 바꿀 수 있습니다. 바꾸면 자동으로 다시 배포됩니다.

## 2. 배포 순서

1. <https://dashboard.render.com> 에 GitHub 계정으로 가입·로그인합니다.
2. 오른쪽 위 **New → Blueprint**를 누릅니다.
3. GitHub 연결을 승인하고, 저장소 접근은 `Joy0404/sullivan-ai`만 허용합니다.
4. 저장소 `sullivan-ai`를 고르면 `render.yaml`을 읽어 `sullivan-ai` 웹 서비스가 표시됩니다.
5. `GEMINI_API_KEY`, `DEMO_ACCESS_CODE` 칸에 값을 넣고 **Deploy Blueprint**를 누릅니다.
6. 빌드가 끝나면 서비스 화면 위쪽에 `https://sullivan-ai-xxxx.onrender.com` 주소가 생깁니다.
7. 이후 `main` 브랜치에 커밋을 올리면 자동으로 다시 배포됩니다.

## 3. 무료 플랜에서 알아 둘 점

- 15분 정도 접속이 없으면 서버가 잠듭니다. 다음 첫 접속은 30초~1분 걸릴 수 있습니다.
- 하루 횟수 기록은 서버 메모리에 있어서, 잠들거나 재배포·재시작하면 **초기화**됩니다. 체험 코드가 실제 분석의 1차 관문입니다.
- 방문자 IP는 `CF-Connecting-IP` → `True-Client-IP` → `X-Real-IP` → `X-Forwarded-For`의 마지막 값 순서로 찾습니다. Render가 어떤 헤더를 넣는지 확인되면 `CLIENT_IP_HEADER`로 고정하는 것이 안전합니다.
- 무료 인스턴스는 메모리가 512MB입니다. 업로드 영상은 메모리가 아니라 임시 파일로 받으므로 100MB 제한 안에서는 문제없습니다.

## 4. 완료 확인

- [ ] `https://<주소>/health` 가 `"status": "ok"`, `"real_analysis_access": "trial-code-required"` 를 반환
- [ ] 휴대폰과 PC 시크릿 창에서 `https://<주소>/` 이 열림
- [ ] 샘플 1·2가 체험 코드 없이 열림
- [ ] 코드 없이 / 틀린 코드 / 동의 없이 / 목록 밖 영상 → 각각 분석하지 않고 안내
- [ ] 개발자 도구 Network 탭에 `localhost`, `:8000` 요청 없음
- [ ] Render **Logs**와 화면 어디에도 API 키·체험 코드가 보이지 않음

## 5. 문제가 생겼을 때 확인할 것

| 증상 | 확인할 것 |
|---|---|
| 빌드 실패 | 서비스 → **Events / Logs**에서 Docker 빌드 단계 오류 확인 |
| `Health check failed`로 배포 실패 | Logs에 `Uvicorn running on http://0.0.0.0:10000`이 있는지 확인. Environment에 `PORT`를 직접 넣었다면 지웁니다. |
| 첫 접속이 매우 느림 | 무료 플랜이 잠들었다 깨어나는 중입니다. 1분 정도 기다립니다. |
| "체험 코드가 설정되지 않아…" | Environment에 `DEMO_ACCESS_CODE`가 있는지 확인 |
| "Gemini API 키가 설정되지 않아…" | Environment의 `GEMINI_API_KEY` 철자·앞뒤 공백 확인 |
| "Gemini API 키가 유효하지 않거나…" | Google AI Studio에서 키 상태·사용 제한 확인 |
| 하루 횟수가 예상과 다름 | 서버가 잠들었다 깨어나 초기화됐는지 확인. 여러 사람이 한 사람으로 묶이면 `CLIENT_IP_HEADER` 설정 |
| 휴대폰에서 음성·마이크가 안 됨 | 주소가 `https://`인지 확인. 브라우저 마이크 권한 허용 |
