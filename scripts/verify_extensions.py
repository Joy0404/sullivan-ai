"""One fail-closed acceptance command; all reports belong to one source fingerprint."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import importlib.util
from check_extension_contract import ROOT, CONTRACT, check


def fingerprint():
    paths = [p for base in ('apps/extensions','apps/api/app','apps/web','scripts')
             for p in (ROOT/base).rglob('*') if p.is_file() and p.suffix in ('.py','.js','.html','.css','.mjs')]
    paths += [CONTRACT,ROOT/'package.json',ROOT/'package-lock.json']
    return hashlib.sha256(''.join(str(p.relative_to(ROOT))+hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(paths)).encode()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'docs/verification/extension-acceptance');args=parser.parse_args()
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    if not shutil.which('node') or importlib.util.find_spec('pytest') is None:
        raise SystemExit('Full acceptance requires Node and pytest; no skipped checks allowed here.')
    if not Path(os.getenv('SULLIVAN_AXE_SOURCE','')).is_file():
        raise SystemExit('Full acceptance requires SULLIVAN_AXE_SOURCE pointing to axe.min.js.')
    contract=check(json.loads(CONTRACT.read_text())); before=fingerprint()
    jobs=[('project',['bash','scripts/verify_all.sh']),
          ('student-notes',[sys.executable,'scripts/verify_student_notes.py']),
          ('notebook-races',[sys.executable,'scripts/verify_notebook_races.py','--output',str(output/'notebook-races')]),
          ('dashboard',[sys.executable,'scripts/verify_extension_dashboard.py','--output',str(output/'dashboard')]),
          ('followup',[sys.executable,'scripts/verify_extension_followup.py','--output',str(output/'followup')]),
          ('races',[sys.executable,'scripts/verify_extension_races.py','--output',str(output/'races')]),
          ('remote-login',[sys.executable,'scripts/verify_remote_login.py','--output',str(output/'remote-login')]),
          ('guardian-entry',[sys.executable,'scripts/verify_guardian_entry.py','--output',str(output/'guardian-entry')]),
          ('submission-flow',[sys.executable,'scripts/verify_submission_browser.py','--output',str(output/'submission-flow')]),
          ('universal',[sys.executable,'scripts/verify_extension_universal.py','--output',str(output/'universal')]),
          ('restoration',[sys.executable,'scripts/verify_feature_restoration.py']),
          ('reaudit',[sys.executable,'scripts/verify_reaudit_fixes.py','--output',str(output/'reaudit')]),
          ('optimization',[sys.executable,'scripts/verify_extension_optimization.py','--output',str(output/'optimization')]),
          ('restart',[sys.executable,'scripts/verify_preparation_restart.py']),
          ('production',[sys.executable,'scripts/verify_extension_production.py'])]
    report={'result':'running','source_sha256':before,'contract':contract,'checks':[],
            'boundary':'Structural ledger plus local regressions; external acceptance remains pending.'}
    target=output/'results.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    env=os.environ.copy();env['PATH']=str(Path(sys.executable).parent)+os.pathsep+env.get('PATH','')
    for name, command in jobs:
        print('Verifying',name,flush=True)
        with (output/f'{name}.log').open('w') as log:
            code=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
        report['checks'].append({'name':name,'exit_code':code})
        unchanged=before==fingerprint()
        report['result']='failed' if code or not unchanged else 'running'
        report['source_unchanged']=unchanged
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        if code or not unchanged:raise SystemExit(f'{name} failed or sources changed; see {output}')
    report['result']='passed';target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Local implementation acceptance passed. External acceptance remains pending.',flush=True)


if __name__=='__main__':main()
