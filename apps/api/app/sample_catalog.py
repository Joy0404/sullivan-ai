"""Built-in, precomputed samples. No provider calls or client-supplied snapshots."""
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
import json
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from app.models import LectureSession, LectureSnapshot

@lru_cache(maxsize=1)
def catalog():
    path=Path(__file__).resolve().parents[2]/'web'/'sample-catalog.json'
    return json.loads(path.read_text(encoding='utf-8'))

def prepared_sample(sample_id):
    spec=catalog().get(sample_id)
    if spec is None:raise HTTPException(404,'지원하는 샘플을 선택해 주세요.')
    data=deepcopy(spec['snapshot'])
    data['session']=LectureSession(session_id='sample-'+uuid4().hex,title=spec['title'],subject=spec['subject'],source_label=f'사전 준비된 {sample_id} 샘플 · 이번 실행에서 새 영상 분석 없음',preferred_mode='slides',problem_mode=False,created_at=datetime.now(timezone.utc).isoformat()).model_dump(mode='json')
    return spec,LectureSnapshot.model_validate(data)
