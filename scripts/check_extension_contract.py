"""Structural feature ledger guard. Behavioral evidence comes from verify_extensions.py."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'docs/extension-feature-contract.json'
EXTERNAL_ACCEPTANCE = {'F24','F25','F26','F33','F34','F49','F61','F62'}


def check(data, root=ROOT):
    rows = data['features']
    assert len(rows) == 78 and {row['id'] for row in rows} == {f'F{i:02}' for i in range(1,79)}, 'Feature IDs missing or duplicated'
    for row in rows:
        assert row['implementation'] in ('implemented','design_change','unsupported'), (row['id'],'unresolved implementation')
        assert row['verification'] in ('automated','external_pending'), (row['id'],'invalid verification')
        assert row['requirement'] and row['limits'], row['id']
        assert row['sources'] and row['regressions'], (row['id'],'missing evidence mapping')
        for name in row['sources'] + row['regressions']:
            assert (root/name).is_file(), (row['id'], 'missing file', name)
        for name, markers in row.get('markers', {}).items():
            source = (root/name).read_text()
            for marker in markers:assert marker in source, (row['id'],'missing marker',marker)
    # Pending real-service checks cannot disappear through a status/count edit.
    pending = {row['id'] for row in rows if row['verification'] == 'external_pending'}
    assert pending == set(data['external_acceptance']) == EXTERNAL_ACCEPTANCE, 'External evidence checklist mismatch'
    assert {r['id'] for r in rows if r['implementation']=='design_change'} == {'F01','F03','F07','F36','F76'}, 'Design changes require explicit scope review'
    assert {r['id'] for r in rows if r['implementation']=='unsupported'} == {'F77','F78'}, 'Unsupported scope changed'
    assert data['release_ready'] is False, 'Release requires a separately reviewed live acceptance record'
    return {'features':len(rows),'declared_implementation_gaps':0,'external_pending':sorted(pending),'release_ready':False}


def self_test(data):
    import copy
    for mutate in (
        lambda d: d['features'].pop(),
        lambda d: d['features'][0].update(implementation='missing'),
        lambda d: d['features'][0].update(regressions=[]),
        lambda d: d.update(release_ready=True),
        lambda d: d['features'][0].update(sources=['missing-source.js']),
        lambda d: d['features'][15].update(markers={'apps/extensions/guardian/workspace.html':['missing-dashboard-control']}),
        lambda d: d['features'][1].update(implementation='design_change'),
    ):
        changed=copy.deepcopy(data);mutate(changed)
        try:check(changed)
        except AssertionError:pass
        else:raise AssertionError('Contract guard accepted missing scope or false completion')


if __name__ == '__main__':
    data=json.loads(CONTRACT.read_text()); result=check(data);self_test(data)
    print('Extension contract:',json.dumps(result,ensure_ascii=False),'(negative guards passed)')
