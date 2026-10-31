# Sullivan AI 시작 안내

공개 서비스 배포는 [DEPLOY_RENDER.md](DEPLOY_RENDER.md)를 따르세요.

## 로컬 샘플 미리보기

1. 압축을 풀고 Docker Desktop을 실행합니다.
2. Windows에서는 `RUN_WINDOWS.bat`을 실행합니다. 다른 환경에서는 프로젝트 루트에서 `docker compose up --build`를 실행합니다.
3. 브라우저에서 로컬 8080 포트를 엽니다.
4. 별의 진화 또는 역사 샘플을 선택합니다. API 키와 체험 코드가 필요 없습니다.
5. 종료할 때 `docker compose down` 또는 `STOP_WINDOWS.bat`을 실행합니다.

웹과 API는 하나의 서버에서 실행됩니다. 별도 8000 포트 서버는 필요 없습니다.
이 로컬 Compose 설정에는 비밀값을 주입하지 않습니다. 실제 분석은 Render Environment를 설정한 서비스에서 이용합니다.

## 실제 분석

먼저 자료 이용 권한을 확인하고, 분석·AI 대화 동의를 직접 체크한 뒤 운영자가 안내한 체험 코드를 입력합니다.
YouTube는 지정된 두 샘플 영상, 로컬 파일은 100MB 이하만 가능합니다.
실제 분석·AI 대화는 같은 IP에서 하루 3회까지이며 실패한 요청도 차감됩니다.
제한 날짜는 한국 시간 자정에 바뀝니다. 샘플과 로컬 보조 대화는 이 제한 없이 이용합니다.

API 키 입력란은 없습니다. 키를 채팅·화면·파일에 붙여 넣지 말고 Render Environment에만 저장하세요.
