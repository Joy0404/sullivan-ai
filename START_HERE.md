# Sullivan AI Windows 노트북 실행 전체 안내

이 문서는 `Sullivan-AI-v4.14-uploaded-video-ai.zip`을 받은 Windows 10/11 노트북에서 처음 실행하는 과정부터 종료, 재실행, 업로드 영상 AI 분석과 오류 해결까지 순서대로 설명한다.

## 1. 필요한 것

- Windows 10/11 64비트 노트북
- 인터넷 연결: Docker 이미지 최초 설치와 YouTube 재생에 필요
- Chrome 또는 Edge 권장: 한국어 TTS와 음성 인식 지원 여부는 브라우저에 따라 다름
- 스피커 또는 이어폰
- 음성 명령을 사용할 경우 마이크
- 권장 여유 공간 3GB 이상

샘플 강의와 로컬 보조 기능에는 Gemini API 키가 필요 없다. 실제 공개 YouTube 또는 별도 동의한 로컬 영상의 발화·화면을 새로 분석하거나, AI 학습 대화에서 Gemini가 다음 행동을 직접 선택하는 시연에는 키가 필요하다.

## 2. ZIP 압축 풀기

1. `Sullivan-AI-v4.14-uploaded-video-ai.zip`을 다운로드한다.
2. 파일을 마우스 오른쪽 버튼으로 누르고 `모두 압축 풀기`를 선택한다.
3. 예를 들어 `C:\Users\사용자이름\Downloads\Sullivan-AI-v4.14-uploaded-video-ai` 폴더에 압축을 푼다.
4. 폴더 안에 `docker-compose.yml`, `README.md`, `START_HERE.md`, `RUN_WINDOWS.bat`, `STOP_WINDOWS.bat`, `apps` 폴더가 있는지 확인한다.

ZIP 파일 내부에서 직접 실행하지 말고 반드시 압축을 먼저 푼다.

## 3. 권장 실행법: Docker Desktop

### 3-1. WSL 2 준비

1. 시작 메뉴에서 `PowerShell`을 검색한다.
2. `Windows PowerShell` 또는 `터미널`을 마우스 오른쪽 버튼으로 눌러 `관리자 권한으로 실행`한다.
3. 다음 명령을 실행한다.

```powershell
wsl --install
```

4. 설치 또는 다시 시작 안내가 나오면 노트북을 재부팅한다.
5. 재부팅 후 일반 PowerShell에서 다음 명령으로 상태를 확인한다.

```powershell
wsl --status
wsl --version
```

이미 WSL이 설치되어 있다면 설치 명령을 다시 실행할 필요가 없다. `wsl --install` 대신 도움말만 표시되는 구형 Windows에서는 Windows 업데이트를 먼저 적용한다.

### 3-2. Docker Desktop 설치

1. 공식 설치 페이지 `https://docs.docker.com/desktop/setup/install/windows-install/`에서 Windows용 Docker Desktop을 받는다.
2. 설치 화면에서 WSL 2 기반 실행 옵션을 사용한다.
3. 설치 후 Docker Desktop을 실행한다.
4. 약관 화면이 나오면 내용을 확인하고 진행한다.
5. Docker Desktop이 `Engine running` 상태가 될 때까지 기다린다.

PowerShell을 새로 열고 다음 세 명령을 확인한다.

```powershell
docker --version
docker compose version
docker info
```

세 번째 명령이 서버 정보까지 출력하면 준비가 끝난 것이다. `docker daemon` 연결 오류가 나오면 Docker Desktop이 완전히 켜지지 않은 상태다.

### 3-3. Sullivan AI 실행

PowerShell을 열고 압축을 푼 폴더로 이동한다. 아래 경로는 예시이므로 실제 폴더 위치에 맞춘다.

```powershell
cd "$env:USERPROFILE\Downloads\Sullivan-AI-v4.14-uploaded-video-ai"
```

파일이 있는지 확인한다.

```powershell
Get-ChildItem
```

`docker-compose.yml`이 보이면 다음 명령을 실행한다.

```powershell
docker compose up --build
```

최초 실행은 Python 이미지와 패키지를 받기 때문에 몇 분 걸릴 수 있다. 화면에 `app` 서비스가 실행되면 정상이다. API와 웹 화면이 같은 주소에서 함께 열린다.

- 웹 + API: `http://localhost:8000`

명령 창을 닫지 않은 상태에서 Chrome 또는 Edge를 열고 다음 주소로 접속한다.

```text
http://localhost:8000
```

### 3-4. 더블클릭으로 실행

Docker Desktop이 실행 중이라면 프로젝트 폴더의 `RUN_WINDOWS.bat`을 더블클릭해도 된다. 이 파일은 컨테이너를 백그라운드에서 시작한 뒤 브라우저를 연다.

Windows SmartScreen이 경고하면 파일을 먼저 메모장으로 열어 내용을 확인한다. 파일은 이 폴더에서 `docker compose up -d --build`만 실행한다.

## 4. 샘플 시연

1. `http://localhost:8000`을 연다.
2. `샘플 1 · 과학 — 별의 진화` 또는 `샘플 2 · 역사 — 왜란과 호란의 발발과 영향`을 선택한다.
3. 선택한 샘플의 사전 준비된 접근성 결과가 즉시 열린다. 현재 영상을 새로 분석한 것처럼 표시하지 않는다.
4. `자동 정지·해설`을 켠 채 영상을 처음부터 재생한다. 상태 표시가 `다음 0:43`으로 바뀌고, 0분 43초 판서 장면에서 영상이 자동으로 멈춘 뒤 화면을 설명하고 이어서 재생한다.
5. 왼쪽 메뉴에서 다음 기능을 확인한다.
   - `강의 화면`: 재생 중 중요한 시각정보 해설
   - `핵심 탐색`: 키워드·인물·원인·전개·결과·비교·정책 흐름 검색, 강사 구간 뒤 AI 재설명
   - `접근성 복습`: 타임스탬프가 연결된 복습
   - `AI 학습 노트`: 요약·개념 지도·용어·회상 질문
   - `AI 학습 대화`: 음성 또는 키보드로 결과물 요청
   - `안전·판단 근거`: 개인정보·저작권·확신도·개입 이유 확인
6. `AI 학습 대화`에서 `3줄 요약`, `핵심 키워드`, `원인·전개·결과`, `개념 비교`, `시험 암기표`, `복습 계획`, `자기점검 퀴즈`, `발표문`을 만들 수 있다.
7. `AI 응답 자동으로 듣기`가 켜져 있으면 결과를 한국어 음성으로 읽는다.

## 5. 마이크와 음성 사용

1. Chrome 또는 Edge에서 Sullivan AI를 연다.
2. 어느 화면에서든 `Space` 키를 2초 이상 계속 누른다.
3. 첫 번째 띠링 뒤 영상 시작·멈춤, 화면 해설, 요약, 탐색, 샘플, 저장·홈 이동 등 사용할 수 있는 명령을 음성으로 안내합니다. 이때 Space를 떼어도 안내가 중간에 끊기지 않습니다.
4. 안내 도중 Space를 다시 0.65초 이상 누르면 남은 명령 목록을 생략하고 두 번째 띠링과 함께 마이크가 켜집니다. 누르고 있는 동안 “샘플 1 시작해줘”, “영상 시작해줘”, “현재 화면 설명해줘”, “영상 멈춰”, “요약을 읽어줘”, “밑줄 친 문단 다시 들려줘”, “홈으로 돌아가”처럼 말합니다.
5. 안내를 끝까지 들었다면 다음에 Space를 2초 이상 누를 때 목록을 반복하지 않고 바로 마이크가 켜집니다.
6. 브라우저가 `localhost에서 마이크 사용` 권한을 물으면 `허용`을 선택한다. 권한 창 때문에 앱 포커스가 잠시 바뀌어도 명령 세션은 유지됩니다.
7. 말을 마친 뒤 `Space` 키를 떼면 인식을 끝내고 한 번만 실행합니다. 인식 엔진이 무음 때문에 잠시 끝나도 누르고 있는 동안 자동 재연결합니다. 자유 형식 학습 결과물은 화면에 표시되고 음성으로도 읽습니다.
8. 말하기 어려운 장소에서는 `Space`를 빠르게 세 번 누릅니다. 텍스트 명령창이 열리고 입력칸에 자동으로 포커스되므로 클릭하지 말고 바로 타이핑한 뒤 Enter를 누릅니다.
9. 음성 또는 텍스트로 `자유 모드`라고 명령하면 마우스 클릭과 화면의 모든 버튼을 제한 없이 직접 사용할 수 있습니다. Space 한 번은 영상 재생·일시정지, `←/→`는 10초 이동이며 기존 `Alt` 단축키도 그대로 사용할 수 있습니다.
10. 자유 모드를 끝낼 때는 Space를 빠르게 두 번 누릅니다. 에이전트 명령 모드로 돌아오며 영상의 현재 재생 상태는 유지합니다.
11. 일반 모드에서 TTS나 명령 안내를 끝내려면 Space를 빠르게 두 번 누릅니다. 세 번 입력과 구분하기 위해 최대 0.65초 뒤 실행됩니다.
12. YouTube 화면을 클릭한 뒤에도 앱이 자동으로 명령 초점을 되찾습니다. 일반 에이전트 화면에서도 `←/→` 또는 `Alt+←/→`로 영상을 10초씩 이동할 수 있습니다.
13. 텍스트 입력칸에서 Space는 평소처럼 공백을 입력합니다.
14. 영상과 음성을 모두 멈춘 상태로 유지하려면 `Esc` 키를 누르거나 “영상 멈춰”라고 말합니다.

마이크를 실수로 차단했다면 주소창 왼쪽의 사이트 설정 아이콘에서 `마이크 → 허용`으로 바꾼 뒤 페이지를 새로 고친다. 음성 인식은 브라우저와 Windows 음성 서비스 지원 상태에 따라 사용할 수 없을 수 있으며, 이 경우 키보드 입력은 그대로 동작한다.

## 6. 내 영상과 자료 사용

1. 첫 화면에서 강의명과 과목을 입력한다.
2. 다음 중 하나만 선택한다.
   - 노트북의 MP4/WebM 영상 파일
   - 이용·분석 권한이 있는 공개 영상 URL
3. 로컬 영상 자체에서 실제 발화·판서·슬라이드를 추출하려면 `선택한 영상의 실제 발화·판서·슬라이드를 Gemini로 임시 분석`을 체크한다. 원본 전송을 원하지 않으면 체크하지 않는다.
4. 서버 `.env`에 키가 없으면 첫 화면의 Gemini API 키 칸에 본인의 키를 입력한다. 키는 저장되지 않는다.
5. 필요하면 SRT/VTT 자막, TXT/MD 지문, 표준 분석 JSON을 추가한다.
6. 이용·분석 권한 확인란을 선택한다.
7. 시험 문제의 최종 정답을 숨기고 힌트와 개념만 받고 싶을 때만 `문제 보호 모드`를 켠다.
8. 일반 강의나 문제 풀이 전체 화면 설명이 필요하면 문제 보호 모드를 끈 상태로 둔다.
9. `업로드 자료로 시작`을 누르고 분석 완료 화면이 100%가 될 때까지 기다린다.

별도 분석 체크를 하지 않은 로컬 영상 원본은 브라우저 객체 URL로만 재생되며 API로 전송되지 않는다. 체크한 경우에만 API가 임시 파일을 만들고 Gemini Files API로 전달하여 실제 음성 전사와 화면/OCR 관측을 생성한다. 분석 성공·실패 뒤 로컬 임시 파일과 Gemini 파일 삭제를 즉시 시도한다. 공급자 삭제 요청이 실패한 경우에도 Files API 파일은 최대 48시간 뒤 자동 삭제된다.

## 7. 실제 YouTube·업로드 영상 AI 분석: 선택 사항

샘플만 사용할 때는 이 단계를 건너뛴다.

### 화면에서 일회성 키 사용

첫 화면의 Gemini API 키 입력란에 키를 넣으면 YouTube 또는 별도 동의한 업로드 영상 분석과 현재 실행의 에이전트 대화에 사용한다. 영상 분석은 장면 탐색과 독립 시각 근거 재검증의 두 호출로 수행되어, 실제 화면과 맞지 않는 판서·그래프 설명을 걸러낸다. 키는 세션 응답이나 강의 보관함에 저장하지 않으며 새로고침하면 브라우저 메모리에서 사라진다.

### `.env` 파일에 로컬 설정

프로젝트 폴더의 PowerShell에서 실행한다.

```powershell
Copy-Item .env.example .env
notepad .env
```

다음 줄에 본인의 키를 입력하고 저장한다.

```dotenv
GEMINI_API_KEY=본인의_키
GEMINI_MODEL=gemini-2.5-flash
```

그 후 컨테이너를 다시 시작한다.

```powershell
docker compose down
docker compose up --build
```

`.env` 파일이나 API 키를 발표 자료, Git 저장소, 메신저에 공유하지 않는다. 분석 기능 사용 가능 여부와 비용·사용량은 해당 API 계정 정책을 따른다.

## 8. 정상 실행 확인

다른 PowerShell 창에서 다음 명령을 실행한다.

```powershell
Invoke-RestMethod http://localhost:8000/health
```

`status`가 `ok`이면 API가 정상이다. 웹 서비스는 다음 명령으로 확인한다.

```powershell
Invoke-WebRequest http://localhost:8000 -UseBasicParsing | Select-Object StatusCode
```

`200`이 나오면 웹이 정상이다.

컨테이너 상태와 로그는 다음 명령으로 확인한다.

```powershell
docker compose ps
docker compose logs --tail 100 app
docker compose logs --tail 100 web
```

## 9. 종료와 재실행

`docker compose up --build`를 실행한 PowerShell에서 `Ctrl+C`를 누른 다음 다음 명령을 실행한다.

```powershell
docker compose down
```

백그라운드 실행이나 더블클릭 실행을 종료하려면 `STOP_WINDOWS.bat`을 더블클릭해도 된다.

다음에 다시 실행할 때는 Docker Desktop을 먼저 켠 뒤 프로젝트 폴더에서 실행한다.

```powershell
docker compose up
```

코드가 바뀌었거나 새 ZIP으로 교체했으면 다음을 사용한다.

```powershell
docker compose up --build
```

## 10. 자주 발생하는 오류

### `Bind for 0.0.0.0:8000 failed: port is already allocated`

8000번 포트를 이미 다른 컨테이너나 프로그램이 사용 중이라는 뜻이다.

먼저 실행 중인 Docker 컨테이너를 확인한다.

```powershell
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Ports}}"
```

이전 Sullivan AI API 컨테이너가 8000번 포트를 사용 중임이 확실하다면 해당 ID를 넣어 중지한다.

```powershell
docker stop 컨테이너ID
```

Docker가 아닌 프로그램이라면 다음으로 PID를 확인한다.

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess
Get-Process -Id 위에서_확인한_PID
```

중요한 프로그램이 아닌지 확인한 뒤에만 종료한다.

```powershell
Stop-Process -Id 위에서_확인한_PID
```

그 다음 프로젝트 폴더에서 다시 실행한다.

```powershell
docker compose up --build
```

### `분석 세션을 시작하지 못했습니다` 또는 `Failed to fetch`

1. 브라우저 주소가 `http://localhost:8000`인지 확인한다.
2. Docker Desktop이 실행 중인지 확인한다.
3. 프로젝트 폴더에서 다음을 실행한다.

```powershell
docker compose ps
docker compose logs --tail 100 app
```

4. API가 비정상이면 재시작한다.

```powershell
docker compose down
docker compose up --build
```

샘플 진행은 API가 일시적으로 꺼져 있어도 사전 준비 데이터로 열리지만, 새 강의 세션과 실제 링크 분석에는 API가 필요하다.

### Docker 명령을 찾을 수 없음

Docker Desktop을 설치한 뒤 PowerShell을 모두 닫고 새로 연다. 그래도 안 되면 노트북을 재부팅하고 Docker Desktop 실행 상태를 확인한다.

### Docker Desktop이 시작되지 않음

관리자 PowerShell에서 다음을 실행하고 재부팅한다.

```powershell
wsl --update
wsl --shutdown
```

BIOS/UEFI에서 CPU 가상화가 꺼져 있으면 제조사 안내에 따라 Intel VT-x 또는 AMD-V를 켜야 한다.

### YouTube 영상만 재생되지 않음

학교·회사 네트워크, 광고 차단 확장, 브라우저 보안 정책에서 YouTube 임베드를 차단할 수 있다. 다른 네트워크 또는 확장 기능을 끈 별도 브라우저 프로필에서 확인한다. 영상이 재생되지 않아도 사전 준비된 샘플의 요약·해설·학습 노트는 사용할 수 있다.

### 음성이 나오지 않음

- Windows와 브라우저 탭의 음소거 상태를 확인한다.
- `AI 응답 자동으로 듣기`를 켠다.
- 다른 한국어 음성을 Windows 설정에 설치하거나 Chrome/Edge에서 다시 시도한다.
- `Esc`를 누르면 진행 중인 음성이 중단되므로 다시 결과를 생성한다.

## 11. Docker 없이 Python으로 실행

Docker 설치가 불가능할 때 사용하는 방법이다. Python 3.11 64비트를 설치하고 설치 화면에서 `Add Python to PATH`를 선택한다.

### PowerShell 창 1: API

```powershell
cd "$env:USERPROFILE\Downloads\Sullivan-AI-v4.14-uploaded-video-ai\apps\api"
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

마지막 명령이 실행된 PowerShell 창은 닫지 않는다. API가 웹 화면도 함께 제공하므로 별도 웹 서버는 필요 없다.

Chrome 또는 Edge에서 `http://localhost:8000`을 연다. 종료할 때 PowerShell 창에서 `Ctrl+C`를 누른다.

두 번째 실행부터는 패키지 설치를 반복하지 않고 다음 명령만 실행해도 된다.

```powershell
cd "$env:USERPROFILE\Downloads\Sullivan-AI-v4.14-uploaded-video-ai\apps\api"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 12. 선택적 전체 검증

Docker 없이 Python 환경을 만든 경우 다음으로 프로젝트 구조와 테스트를 확인할 수 있다.

```powershell
cd "$env:USERPROFILE\Downloads\Sullivan-AI-v4.14-uploaded-video-ai"
py scripts\verify_project.py
node scripts\test_playback_scheduler.js
cd apps\api
.\.venv\Scripts\python.exe -m pytest -q
```

정상 버전은 API 자동 테스트 40개와 재생 스케줄러 검사 8개가 통과한다. 재생 스케줄러 검사는 Node.js가 설치된 경우에만 실행하면 된다.
