"""Print configuration readiness without printing any credentials or client IDs."""
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'apps/api'))
from app.extension_operations import diagnose
if __name__=='__main__':
    result=diagnose();print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['ready'] else 1)
