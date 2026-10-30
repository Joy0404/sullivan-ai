#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_DIR"

python scripts/verify_project.py

if command -v node >/dev/null 2>&1; then
  node --check apps/web/app.js
  node scripts/test_playback_scheduler.js
  node scripts/test_concept_tools.js
  node scripts/test_sample_catalog.js
  node scripts/test_narration_context.js
  node scripts/test_passage_tools.js
  node scripts/test_lecture_library.js
  node scripts/test_voice_command_router.js
else
  echo "WARN: node가 없어 JavaScript 구문 검사를 건너뜁니다."
fi

if python -c "import pytest" >/dev/null 2>&1; then
  (cd apps/api && PYTHONPATH=. python -m pytest -q)
else
  echo "INFO: pytest가 없어 정적 검증 결과만 사용합니다."
fi
