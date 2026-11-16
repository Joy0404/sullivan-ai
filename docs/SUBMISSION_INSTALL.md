# Sullivan AI 제출본 설치와 실행

이 ZIP은 소스 코드·의존성 목록·학생/보호자 확장 설치 폴더·직접 만든 공개 데모 자료를 포함한다. 기존 사용자 계정·학습 기록·비밀번호·API 키·업로드 원본은 포함하지 않는다. 스토어 게시물은 아니다.

## 1. 압축 해제와 서버 실행

ZIP을 원하는 위치에 풀고 `Sullivan-AI` 폴더에서 실행한다. 저장소를 복제하거나 `.git` 폴더를 복원할 필요는 없다. Python **3.11~3.13**과 최신 데스크톱 Chrome이 필요하며 Python 3.12를 권장한다. 의존성 최초 설치에는 인터넷이 필요하다.

macOS·Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r apps/api/requirements.txt
.venv/bin/python run_local.py --sample --no-open --port 8770
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r apps/api/requirements.txt
.venv\Scripts\python.exe run_local.py --sample --no-open --port 8770
```

macOS에서는 `bash START_LOCAL.command --sample --no-open --port 8770`으로 가상환경과 의존성 설치를 함께 실행할 수도 있다. 서버가 실행된 터미널은 열어 둔다. 서버 주소는 `http://127.0.0.1:8770`이며 종료는 해당 터미널의 Ctrl+C다. 계정 DB는 실행 후 이 압축 해제 폴더의 `data/private/`에 새로 생성된다.

`--sample` 실행은 **Gemini 키 없이 동작**한다. 사전 준비 샘플과 입력 자료의 처리이며, 영상을 새로 AI 분석했다고 표시하지 않는다. 선택한 학생 영상은 브라우저에서 재생하고 API로 전송하지 않는다. 실제 영상 분석은 별도 공급자 설정과 원본 임시 전송 동의가 필요한 별도 기능이다.

## 2. 두 확장 설치

Chrome에서 `chrome://extensions`를 열고 개발자 모드를 켠다. ‘압축해제된 확장 프로그램을 로드합니다’로 다음 두 **폴더**를 각각 선택한다.

- `Sullivan-AI/dist/extensions/guardian`: 보호자 관리 탭.
- `Sullivan-AI/dist/extensions/student`: 학생 학습 사이드 패널.

설치 뒤 폴더를 이동하거나 지우면 Chrome이 파일을 찾지 못한다. 같은 기능의 예전 개발 확장이 설치돼 있으면 시험에 사용할 두 확장을 구분해 연다. 제출본의 확장 설정은 로컬 서버 8770 포트를 사용한다.

## 3. 키 없는 첫 사용

1. 보호자 확장을 처음 열면 사용 설명서가 먼저 나타난다. ‘설명서를 확인하고 시작하기’를 누른 뒤 ‘회원가입’을 선택하고 계정을 만든다. 복구 코드를 보관한 뒤 로그인한다. 로컬 시험 계정은 회원가입 화면의 ‘로컬 개발 계정 만들기’로도 만들 수 있다. 다음 접속에는 로그인·회원가입 선택부터 나타나며 ‘보호자 설명서’는 필요할 때 다시 연다. 제출본에는 기존 계정이나 공용 비밀번호가 없다.
2. ‘학생 계정 만들기’에서 시험용 학생을 만들고 ‘샘플 강의 배정’에서 과학·역사 또는 ‘판서 차이·부분 보류 시연 샘플’을 배정한다.
3. 학생 확장에서 방금 만든 학생 계정으로 로그인하고 배정된 강의를 연다. 준비된 지문·설명·복습·메모 저장을 사용할 수 있다.
4. `samples/`의 데모 JSON·자막·지문은 직접 작성한 공개 자료다. 보호자의 ‘새 강의 준비’에서 자료로 등록할 수 있다. 데모 MP4는 학생 기기에서 직접 파일로 선택한다. `samples/public-manifest.json`에 출처와 공개 이용 조건을 명시한다.
5. 별도 가입한 학생을 연결할 때는 보호자의 일회용 코드를 학생이 입력하고 보호자 이름·공유 범위를 직접 확인한다. ‘기기 로그인 지원’은 별도 선택 항목이다. 한 번 승인하면 이후 보호자 화면에서 해당 학생의 로그인을 시작할 수 있다. 처음 승인과 Chrome 실행은 필요하다.

Space 명령·타자 대체·외부 스크린리더 선택은 확장 안의 사용법에서 확인한다. 한국어 앱 음성은 Chrome과 OS에 설치된 음성을 사용하므로 음질·제공 음성은 기기마다 다르다. 영상은 Chrome이 지원하는 코덱에서만 재생하며 DRM 우회·보호 영상 다운로드는 제공하지 않는다.

## 4. 소스 검사와 재빌드

Node.js가 있으면 Python 검사와 JS 구문·코어 검사를 함께 실행할 수 있다.

```bash
PATH="$PWD/.venv/bin:$PATH" bash scripts/verify_all.sh
.venv/bin/python -m pytest scripts/test_package_submission.py -q
.venv/bin/python scripts/build_extensions.py
.venv/bin/python scripts/package_submission.py
```

패키지 생성은 `dist/submission/sullivan-submission-버전.zip`에 새 ZIP을 만든다. 생성 도구는 지정한 소스 경로와 파일 형식만 선택하고, 임시 폴더에서 확장을 새로 빌드한 후 ZIP 내부 경로·심볼릭 링크·개인 파일·알려진 자격증명 패턴·체크섬을 검사한다. 작업 폴더 전체나 Git 추적 파일 전체를 압축하지 않는다.

브라우저 회귀 검사는 선택 의존성 `scripts/requirements-extension-tests.txt`, Chromium 및 axe-core가 필요하다. 관련 설치 방법은 `apps/extensions/README.md`에 있다. 일반 설치·키 없는 샘플 사용에는 이 검사 도구가 필요하지 않다.

## 5. 환경 예제와 제출 파일 확인

`.env.example`과 `deploy/extension.env.example`은 **설정 예제**다. 로컬 샘플 사용 시 복사하거나 운영 설정을 켤 필요가 없다. 실제 비밀 값은 제출물에 넣지 않는다. Render·Docker·운영 설정은 기존 웹/API 호환을 위한 소스이며 로컬 실행의 필수 서비스가 아니다.

`SUBMISSION_MANIFEST.json`에는 제출 버전, 포함 파일별 SHA-256·크기, 제외 정책이 기록된다. 다음 명령으로 추출 전 ZIP 자체를 검사할 수 있다.

```bash
.venv/bin/python scripts/package_submission.py --inspect /path/to/sullivan-submission-version.zip
```

알려진 키·토큰·개인 키 패턴 검사는 임의 문장의 모든 개인정보를 식별하는 보장이 아니다. 새로운 자료를 추가해 다시 제출할 때는 직접 작성한 공개 샘플만 `samples/public-manifest.json`에 등록하고 실제 키·원본·사용자 DB·메모·로그를 넣지 않는다. 현재 실제 사용자·유료 공급자·실제 스크린리더 음성으로 검증한 범위는 별도 보고와 구분한다.
