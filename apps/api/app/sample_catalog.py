"""Built-in, precomputed samples. No provider calls or client-supplied snapshots."""
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
import json
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from app.models import AnalysisStatus, LectureSession, LectureSnapshot

@lru_cache(maxsize=1)
def catalog():
    path=Path(__file__).resolve().parents[2]/'web'/'sample-catalog.json'
    result=json.loads(path.read_text(encoding='utf-8'))
    result['accessibility']={'title':'판서 차이·부분 보류 시연 샘플','subject':'수학·그래프 접근성','announcement':'사전 준비 샘플 · 이번 실행에서 새 영상 분석 없음'}
    return result

def prepared_sample(sample_id):
    spec=catalog().get(sample_id)
    if spec is None:raise HTTPException(404,'지원하는 샘플을 선택해 주세요.')
    if sample_id=='accessibility':
        from app.core.lecture_agent import LectureAgent
        from app.models import AnalysisPackageInput,LectureCreate
        agent=LectureAgent()
        session=agent.create_session(LectureCreate(title=spec['title'],subject=spec['subject'],source_label='자체 제작 판서·그래프 시연용 강의',problem_mode=False))
        agent.set_analysis_status(session.session_id,'sample')
        package=AnalysisPackageInput.model_validate_json((Path(__file__).resolve().parents[3]/'samples/accessibility-demo.json').read_text())
        return spec,agent.analyze(session.session_id,package)
    data=deepcopy(spec['snapshot'])
    data['session']=LectureSession(session_id='sample-'+uuid4().hex,title=spec['title'],subject=spec['subject'],source_label=f'사전 준비된 {sample_id} 샘플 · 이번 실행에서 새 영상 분석 없음',preferred_mode='slides',problem_mode=False,created_at=datetime.now(timezone.utc).isoformat()).model_dump(mode='json')
    data['analysis_status']=AnalysisStatus(state='sample',run_id=uuid4().hex,recorded_at=datetime.now(timezone.utc).isoformat()).model_dump(mode='json')
    return spec,LectureSnapshot.model_validate(data)
