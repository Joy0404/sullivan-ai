import json
from pathlib import Path
import sys

import pytest
from app import local_access
from app.extension_operations import diagnose, lifespan
from test_extension_access import family

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from manage_extension_data import copy_database
from package_extensions import package


def configured(monkeypatch,tmp_path):
    monkeypatch.setenv('SULLIVAN_PRODUCTION','1')
    monkeypatch.setenv('SULLIVAN_PUBLIC_URL','https://sullivan.example')
    monkeypatch.setenv('SULLIVAN_EXTENSION_CLIENTS',json.dumps({'student':'a'*32,'guardian':'b'*32}))
    monkeypatch.setenv('SULLIVAN_ACCOUNTS_DB',str(tmp_path/'accounts.sqlite'))
    monkeypatch.setenv('SULLIVAN_PERSISTENT_STORAGE','1')
    monkeypatch.setenv('SULLIVAN_ROLE_AUTH','1')
    monkeypatch.setenv('WEB_CONCURRENCY','1')


def test_preflight_refuses_incomplete_production_and_exposes_no_secrets(monkeypatch,tmp_path):
    monkeypatch.setenv('SULLIVAN_PRODUCTION','1')
    monkeypatch.delenv('SULLIVAN_PUBLIC_URL',raising=False)
    monkeypatch.delenv('SULLIVAN_EXTENSION_CLIENTS',raising=False)
    assert not diagnose()['ready']
    configured(monkeypatch,tmp_path)
    assert diagnose()['ready']
    monkeypatch.setenv('SULLIVAN_SIGNUP_INVITE','short')
    assert not diagnose()['ready']
    assert 'short' not in json.dumps(diagnose())


def test_exclusive_production_process_lease(monkeypatch,tmp_path):
    import asyncio
    configured(monkeypatch,tmp_path)
    async def run():
        async with lifespan(None):
            with pytest.raises(RuntimeError,match='이미 실행'):
                async with lifespan(None):pass
        async with lifespan(None):pass
    asyncio.run(run())


def test_copy_migration_preserves_data_and_original_but_revokes_sessions(family,tmp_path):
    client,guardian,student_id,student=family
    from test_extension_access import headers
    gh=headers('guardian',guardian['token'])
    client.post('/local/samples/science/assign',headers=gh,json={'students':[student_id]})
    source=tmp_path/'accounts.sqlite'
    backup=tmp_path/'before.sqlite'
    saved=copy_database(source,backup)
    assert saved['rows']['users']==2
    target=tmp_path/'migrated.sqlite'
    report=copy_database(source,target,migrate=True)
    assert report['rows']==saved['rows']
    assert report['sessions_invalidated']
    import sqlite3
    with sqlite3.connect(source) as con:assert con.execute('SELECT COUNT(*) FROM extension_sessions').fetchone()[0]==2
    with sqlite3.connect(target) as con:assert con.execute('SELECT COUNT(*) FROM extension_sessions').fetchone()[0]==0
    with pytest.raises(ValueError,match='이미'):copy_database(source,target)


def test_release_packages_only_generated_files_and_requires_https(tmp_path):
    import zipfile
    import hashlib
    report=package(output=tmp_path/'local')
    assert report['published'] is False
    for artifact in report['artifacts']:
        assert hashlib.sha256((tmp_path/'local'/artifact['file']).read_bytes()).hexdigest()==artifact['sha256']
        with zipfile.ZipFile(tmp_path/'local'/artifact['file']) as archive:
            names=archive.namelist()
            assert 'manifest.json' in names and 'icons/128.png' in names
            assert not any('.env' in name or '.sqlite' in name or name.endswith('.py') for name in names)
            assert json.loads(archive.read('manifest.json'))['version']=='0.4.0'
            if artifact['role']=='guardian':assert 'media.js' not in names
            else:assert 'student-form' not in archive.read('index.html').decode()
    with pytest.raises(ValueError):package('http://127.0.0.1:8770',tmp_path/'bad',release=True)
