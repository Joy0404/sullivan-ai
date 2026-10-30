@echo off
chcp 65001 >nul
cd /d "%~dp0"

where docker >nul 2>&1
if errorlevel 1 (
  echo Docker를 찾을 수 없습니다. START_HERE.md의 Docker Desktop 설치 단계를 먼저 진행하세요.
  pause
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo Docker Desktop이 실행 중이 아닙니다. Docker Desktop을 켜고 Engine running 상태에서 다시 실행하세요.
  pause
  exit /b 1
)

echo Sullivan AI를 시작합니다. 최초 실행은 몇 분 걸릴 수 있습니다.
docker compose up -d --build
if errorlevel 1 (
  echo 실행에 실패했습니다. START_HERE.md의 포트 충돌 해결 항목을 확인하세요.
  pause
  exit /b 1
)

echo.
docker compose ps
echo.
echo 브라우저에서 http://localhost:8000 을 엽니다.
start "" "http://localhost:8000"
pause
