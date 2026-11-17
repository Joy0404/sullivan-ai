"""Compare note export against a git revision using generated local data only.

No user database, provider call, raw media or persistent source cache is used.
The baseline reuses the same current authorization/sanitization boundary so
this measurement isolates export's repeated source retrieval.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'apps/api'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-ref', required=True)
    parser.add_argument('--notes', type=int, default=200)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.notes <= 1000 or args.repeats < 1:
        parser.error('notes must be 1..1000 and repeats must be positive')
    old_source = subprocess.check_output(['git','show',args.baseline_ref+':apps/api/app/student_notes.py'],cwd=ROOT)
    with tempfile.TemporaryDirectory(prefix='sullivan-export-benchmark-') as temporary:
        os.environ.update(SULLIVAN_ACCOUNTS_DB=str(Path(temporary)/'accounts.sqlite'),
                          SULLIVAN_ROLE_AUTH='1', SULLIVAN_PRODUCTION='0',
                          GEMINI_API_KEY='', LINK_ANALYZER_URL='', DEMO_USAGE_DB=str(Path(temporary)/'usage.sqlite'))
        for name in ('DATABASE_URL','DATABASE_URL_UNPOOLED','RENDER'):
            os.environ.pop(name, None)
        from fastapi.testclient import TestClient
        from app.main import app
        from app import local_access, student_notes
        baseline = types.ModuleType('_note_export_baseline')
        sys.modules[baseline.__name__] = baseline
        exec(compile(old_source, '<baseline-student-notes>', 'exec'), baseline.__dict__)
        def headers(role, token=None):
            return {'X-Sullivan-Client':role, 'X-Local-Request':'1',
                    **({'Authorization':'Bearer '+token} if token else {})}
        with TestClient(app, base_url='http://127.0.0.1') as client:
            password='generated-test-pass-123'
            guardian=client.post('/extension/v1/guardian/register',headers=headers('guardian'),json={'username':'benchmark-guardian','password':password}).json()
            gh=headers('guardian',guardian['token'])
            sid=client.post('/local/students',headers=gh,json={'username':'benchmark-student','password':password}).json()['id']
            signed=client.post('/extension/v1/student/session',headers=headers('student'),json={'username':'benchmark-student','password':password}).json()
            sh=headers('student',signed['token'])
            ident=client.post('/local/samples/science/assign',headers=gh,json={'students':[sid]}).json()['id']
            endpoint=f'/extension/v1/student/lectures/{ident}'
            candidate=client.get(endpoint+'/note-sources',headers=sh).json()[0]
            ref={key:candidate[key] for key in ('kind','id','fingerprint')}
            with local_access.db() as con:
                student_notes.table(con)
                con.executemany('INSERT INTO student_notes VALUES(?,?,?,?,?,?,?,?)',[
                    (ident,sid,f'generated-{i}',f'직접 생성한 시험 필기 {i}',i*1000,json.dumps(ref),1,'2026-11-16')
                    for i in range(args.notes)])
            route=next(route for route in app.routes if route.path=='/extension/v1/student/lectures/{ident}/notes-export')
            original_call=route.dependant.call
            original_lecture=local_access.lecture
            reads=[]
            def counted(*params,**kwargs):
                reads.append(1)
                return original_lecture(*params,**kwargs)
            local_access.lecture=counted
            measurements={}
            output_hashes=set()
            try:
                for name, call in [('before',baseline.export_notes),('after',student_notes.export_notes)]:
                    route.dependant.call=call
                    elapsed=[];counts=[]
                    for _ in range(args.repeats):
                        reads.clear();start=time.perf_counter()
                        response=client.get(endpoint+'/notes-export',headers=sh)
                        elapsed.append((time.perf_counter()-start)*1000)
                        assert response.status_code==200
                        output_hashes.add(hashlib.sha256(response.content).hexdigest())
                        counts.append(len(reads))
                    measurements[name]={'milliseconds':elapsed,'median_ms':statistics.median(elapsed),'snapshot_reads':counts}
            finally:
                local_access.lecture=original_lecture
                route.dependant.call=original_call
            assert len(output_hashes)==1,'export content changed'
    result={'kind':'generated-local-HTTP-benchmark','baseline_ref':args.baseline_ref,
            'baseline_source_sha256':hashlib.sha256(old_source).hexdigest(),
            'current_source_sha256':hashlib.sha256((ROOT/'apps/api/app/student_notes.py').read_bytes()).hexdigest(),
            'notes':args.notes,'repeats':args.repeats,'measurements':measurements,
            'identical_output':True,'provider_calls':0,'user_database_used':False,
            'boundary':'Local processing benchmark only; timings vary by machine. No Gemini token or live model quality claim.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
