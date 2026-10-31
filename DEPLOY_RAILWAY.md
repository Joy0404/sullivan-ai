> 현재 배포 대상은 Render입니다. 이 문서는 이전 설정 참고용이며 현재 배포에는 DEPLOY_RENDER.md를 사용하세요.

# Railway 배포 안내 (GitHub 비공개 저장소 기준)

Sullivan AI는 컨테이너 하나로 배포합니다. FastAPI 서버가 API와 웹 화면(`apps/web`)을 **같은 공개 주소**에서 함께 제공하고, 웹은 포트 없이 상대 경로(`/health`, `/v1/...`)로 API를 부릅니다.

- 빌드: 저장소 루트의 `Dockerfile`
- 설정: `railway.json` (Dockerfile 빌드, `/health` 상태 확인, 실패 시 재시작)
- 포트: Railway가 넣어 주는 `PORT` 환경변수를 사용합니다. 직접 설정할 필요가 없습니다.

## 1. 올리기 전에 확인

1. 프로젝트 폴더에 `.env`가 있어도 됩니다. 단 **GitHub에 올라가면 안 됩니다.** `.gitignore`와 `.dockerignore`가 `.env`, `__pycache__/`, `.pytest_cache/`를 제외합니다.
2. 첫 커밋 전에 아래 명령으로 올라갈 파일 목록을 확인합니다. 결과에 `.env`, `__pycache__`, `.pytest_cache`가 **없어야** 합니다.

   ```bash
   git add -A
   git status --short
   git ls-files | grep -E "(^|/)\.env$|__pycache__|\.pytest_cache" || echo "OK: 비밀·캐시 파일 없음"
   ```

3. Gemini API 키가 ZIP·메신저·문서로 전달된 적이 있다면 Google AI Studio에서 **새 키를 발급하고 이전 키를 삭제**한 뒤 새 키만 Railway에 넣습니다.

## 2. Railway Variables 입력 목록

Railway 서비스 → **Variables** 탭에 입력합니다. 비밀 값은 여기에만 저장합니다.

| 이름 | 필수 | 예시 값 | 설명 |
|---|---|---|---|
| `GEMINI_API_KEY` | 실제 분석 시 필수 | (Google AI Studio 키) | 비밀. 화면·로그·응답에 출력되지 않습니다. |
| `DEMO_ACCESS_CODE` | 실제 분석 시 필수 | (직접 정한 체험 코드) | 비밀. 없으면 실제 분석과 Gemini 대화가 꺼지고 샘플만 작동합니다. |
| `DEMO_DAILY_LIMIT` | 선택 | `3` | 같은 IP의 하루 실제 분석 횟수 (한국 시간 자정 기준 초기화) |
| `ALLOWED_SAMPLE_VIDEO_IDS` | 선택 | `R0dqsl3Vgns,thJxqtTgSNY` | 실제 분석을 허용할 YouTube 영상 ID (쉼표 구분) |
| `ANALYSIS_TIMEOUT_SECONDS` | 선택 | `180` | 분석 제한 시간(초). 넘으면 중단하고 시간 초과를 안내합니다. |
| `MAX_UPLOAD_VIDEO_BYTES` | 선택 | `104857600` | 업로드 영상 최대 크기 (100MB) |
| `GEMINI_MODEL` | 선택 | `gemini-2.5-flash` | 영상 분석 모델 |
| `GEMINI_FALLBACK_MODEL` | 선택 | `gemini-2.5-flash` | 대체 모델 |
| `GEMINI_AGENT_MODEL` | 선택 | `gemini-2.5-flash` | 학습 대화 에이전트 모델 |
| `APP_ENV` | 선택 | `production` | 표시용 |

`PORT`는 Railway가 자동으로 넣으므로 **입력하지 않습니다.**

## 3. 배포 순서

1. GitHub에서 **Private** 저장소를 새로 만듭니다 (README·.gitignore 자동 추가는 끕니다).
2. 프로젝트 폴더에서:

   ```bash
   git init
   git add -A
   git status --short          # .env, __pycache__, .pytest_cache 가 없는지 확인
   git commit -m "Sullivan AI: single-service Railway deployment"
   git branch -M main
   git remote add origin https://github.com/<계정>/<저장소>.git
   git push -u origin main
   ```

3. [Railway](https://railway.com) → **New Project** → **Deploy from GitHub repo** → 방금 만든 비공개 저장소를 선택합니다. 처음이면 Railway GitHub 앱에 해당 저장소 접근 권한을 줍니다.
4. 서비스 → **Variables**에 2번 표의 값을 입력합니다. 입력하면 자동으로 다시 배포됩니다.
5. 서비스 → **Settings → Networking → Generate Domain**으로 공개 주소(`https://<이름>.up.railway.app`)를 만듭니다.
6. **Settings → Deploy → Replicas는 1**로 둡니다. 하루 횟수 기록이 서버 메모리에 있어 여러 대로 늘리면 횟수가 나뉘어 계산됩니다.
7. 배포가 끝나면 아래 6번 완료 확인을 진행합니다.

## 4. 동작 규칙 요약

- **샘플 기능**: API 키와 체험 코드 없이 항상 작동합니다.
- **실제 분석** (로컬 영상 업로드 / YouTube 링크): 아래를 **모두** 만족해야 실행됩니다.
  1. 사용자가 분석 동의에 직접 체크
  2. 체험 코드가 `DEMO_ACCESS_CODE`와 일치
  3. 같은 IP 기준 오늘 3회 이하 (넘으면 "오늘 체험 횟수를 모두 사용했어요")
- 업로드 영상은 100MB 이하만, 분석은 3분을 넘으면 중단합니다.
- YouTube 링크는 `ALLOWED_SAMPLE_VIDEO_IDS`에 있는 영상만 분석합니다.
- 분석이 끝나면(성공·실패·시간 초과 모두) 서버 임시 파일과 Gemini에 올린 파일을 삭제합니다. 삭제를 확인하지 못하면 화면에 그대로 알립니다.
- **Gemini 학습 대화**도 체험 코드가 맞을 때만 서버 키를 씁니다. 코드가 없으면 로컬 보조 대화로 답합니다 (횟수 제한 없음).
- 방문자가 Gemini 키를 직접 입력하는 기능은 없습니다. 서버는 Railway Variables의 키만 사용합니다.

## 5. 알려 둘 한계

- 하루 횟수는 **서버 메모리**에 저장합니다. 재배포·재시작 때 초기화되고, Replicas 1개일 때만 정확합니다.
- 방문자 IP는 Railway 프록시가 넣는 `X-Real-IP`를 사용합니다 (없으면 `X-Forwarded-For`의 마지막 값). 같은 와이파이·회사망 사용자는 같은 IP로 묶일 수 있습니다.
- 3분 제한은 요청 처리 시간 기준입니다. 영상 업로드 전송 시간은 포함되지 않습니다.

## 6. 완료 확인

- [ ] `https://<도메인>/health` 가 `"status": "ok"` 와 `"real_analysis_access": "trial-code-required"` 를 반환
- [ ] 휴대폰과 PC 시크릿 창에서 `https://<도메인>/` 이 열림
- [ ] 샘플 1·2가 체험 코드 없이 열리고 재생·해설이 작동
- [ ] 체험 코드 없이 / 틀린 코드로 실제 분석 → 분석하지 않고 코드 안내
- [ ] 동의 체크 없이 링크 분석 → 동의 안내
- [ ] 목록에 없는 YouTube 링크 → "지정된 샘플 YouTube 영상만" 안내
- [ ] 같은 기기에서 4번째 실제 분석 → "오늘 체험 횟수를 모두 사용했어요"
- [ ] 브라우저 개발자 도구 Network 탭에 `localhost`나 `:8000` 요청이 없음
- [ ] Railway **Deploy Logs**와 화면 어디에도 API 키·체험 코드가 보이지 않음

## 7. 문제가 생겼을 때 확인할 것

| 증상 | 확인할 것 |
|---|---|
| 배포가 `Healthcheck failed`로 실패 | Deploy Logs에 `Uvicorn running on http://0.0.0.0:<PORT>`가 있는지 확인. Variables에 `PORT`를 직접 넣었다면 지웁니다. |
| 공개 주소가 열리지 않음 | Settings → Networking에서 도메인을 만들었는지, 배포 상태가 Active인지 확인 |
| 화면은 열리는데 "분석 서버에 연결할 수 없습니다" | 브라우저 Network 탭에서 `/health` 응답 확인. 오래된 캐시라면 새로고침(Ctrl+F5) |
| "체험 코드가 설정되지 않아…" | Variables에 `DEMO_ACCESS_CODE`가 있는지, 저장 후 재배포됐는지 확인 |
| "Gemini API 키가 설정되지 않아…" | Variables의 `GEMINI_API_KEY` 이름 철자·앞뒤 공백 확인 |
| "Gemini API 키가 유효하지 않거나…" | Google AI Studio에서 키 상태·사용 제한·결제 설정 확인 |
| "Gemini 사용 한도에 도달했습니다" | Google AI Studio 할당량 확인. `DEMO_DAILY_LIMIT`을 낮추는 것도 방법 |
| 업로드가 바로 실패 | 영상이 100MB 이하이고 MP4·WebM·MOV·M4V 형식인지 확인 |
| "분석 시간이 3분을 넘어 중단했어요" | 더 짧은 영상으로 시도. 필요하면 `ANALYSIS_TIMEOUT_SECONDS` 조정 |
| 횟수 제한이 예상과 다르게 동작 | Replicas가 1인지, 최근 재배포로 초기화되지 않았는지 확인 |
| 휴대폰에서 음성·마이크가 안 됨 | 공개 주소가 `https://`인지 확인. 브라우저 마이크 권한 허용 |
