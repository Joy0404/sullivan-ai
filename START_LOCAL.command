#!/bin/bash
set -e
cd "$(dirname "$0")"
local_python=""
for candidate in python3.12 python3.11 python3.13 python3 "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(not ((3,11) <= sys.version_info[:2] < (3,14)))' 2>/dev/null; then
    local_python="$candidate"
    break
  fi
done
if [ -z "$local_python" ]; then
  echo 'Python 3.11~3.13을 설치한 뒤 다시 실행하세요. Python 3.12를 권장합니다.'
  read -r -p 'Enter를 눌러 닫기' _answer
  exit 1
fi
if [ ! -x .venv/bin/python ]; then "$local_python" -m venv .venv; fi
if ! .venv/bin/python - <<'PY'
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
import re
for line in Path('apps/api/requirements.txt').read_text().splitlines():
    line=line.strip()
    if not line or line.startswith('#'):continue
    match=re.fullmatch(r'([\w-]+)(?:\[[\w,-]+\])?==([^ ]+)',line)
    if not match:raise SystemExit(1)
    try:installed=version(match[1])
    except PackageNotFoundError:raise SystemExit(1)
    if installed!=match[2]:raise SystemExit(1)
import fastapi,uvicorn,pydantic,pytest,httpx,python_multipart,psycopg
PY
then
  .venv/bin/python -m pip install -r apps/api/requirements.txt
fi
.venv/bin/python run_local.py --port 8770 "$@"
