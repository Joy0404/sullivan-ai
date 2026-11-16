#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_DIR"

python scripts/verify_project.py
python scripts/test_build_extensions.py
python scripts/check_extension_contract.py

if command -v node >/dev/null 2>&1; then
  node --check apps/web/app.js
  node --check apps/web/role-portal.js
  node --check apps/web/focus-voice.js
  node --check apps/web/space-gesture.js
  node --check apps/web/keyboard-navigation.js
  for source in apps/extensions/shared/*.js apps/extensions/student/*.js apps/extensions/guardian/*.js; do
    node --check "$source"
  done
  node scripts/test_space_gesture.js
  node scripts/test_playback_scheduler.js
  node scripts/test_concept_tools.js
  node scripts/test_sample_catalog.js
  node scripts/test_narration_context.js
  node scripts/test_passage_tools.js
  node scripts/test_lecture_library.js
  node scripts/test_voice_command_router.js
  node scripts/test_student_core.mjs
  node scripts/test_student_notebook.mjs
  node scripts/test_extension_client.mjs
  node scripts/test_remote_login.mjs
  node scripts/test_accessible_analysis.mjs
else
  echo "WARN: node가 없어 JavaScript 구문 검사를 건너뜁니다."
fi

if python -c "import pytest" >/dev/null 2>&1; then
  (cd apps/api && PYTHONPATH=. python -m pytest -q)
  python -m pytest scripts/test_package_submission.py -q
else
  echo "INFO: pytest가 없어 정적 검증 결과만 사용합니다."
fi
