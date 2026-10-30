@echo off
chcp 65001 >nul
cd /d "%~dp0"

where docker >nul 2>&1
if errorlevel 1 (
  echo Docker를 찾을 수 없습니다.
  pause
  exit /b 1
)

echo Sullivan AI 컨테이너를 종료합니다.
docker compose down
if errorlevel 1 (
  echo 종료 명령에 실패했습니다. Docker Desktop 실행 상태를 확인하세요.
  pause
  exit /b 1
)

echo 종료가 완료되었습니다.
pause
