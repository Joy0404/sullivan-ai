"""Submission boundaries: inspect ZIP bytes, hostile inputs and extracted runtime."""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys
import zipfile

import pytest

from package_submission import (MANIFEST, PREFIX, PUBLIC_SAMPLES, ROOT,
                                inspect_archive, inspect_current_archive, package_submission)


def write(root: Path, name: str, content: str | bytes = 'fixture') -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode() if isinstance(content, str) else content)
    return path


@pytest.fixture
def submission(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / 'source'
    for name, content in {
        'run_local.py': 'print("sample-ready")\n', 'START_LOCAL.command': '#!/bin/bash\npython3 run_local.py --sample\n',
        'apps/api/requirements.txt': 'fastapi==0.116.1\n', 'apps/api/app/main.py': '# runtime\n',
        'apps/web/index.html': '<html lang="ko"><title>demo</title></html>',
        'docs/SUBMISSION_INSTALL.md': 'Use --sample; no paid key required.',
        'docs/EXTENSION_SUBMISSION_REPORT.md': 'Public submission report.',
        'scripts/verify_all.sh': '#!/bin/sh\npython scripts/verify_project.py\n',
        '.env.example': '# Example only\nGEMINI_API_KEY=\n',
        'deploy/extension.env.example': 'SULLIVAN_PUBLIC_URL=https://replace.example\n',
    }.items():
        write(root, name, content)
    assets = [{'path': name, 'provenance': 'generated' if name.endswith('.mp4') else 'self-authored', 'license': 'CC0-1.0'}
              for name in sorted(PUBLIC_SAMPLES)]
    write(root, 'samples/public-manifest.json', json.dumps({'schema_version': 1, 'assets': assets}))
    for name in PUBLIC_SAMPLES:
        write(root, 'samples/' + name, '[]' if name.endswith('.json') else b'public-fixture')
    extensions = tmp_path / 'extensions'
    for role in ('student', 'guardian'):
        write(extensions, role + '/manifest.json', json.dumps({'manifest_version': 3, 'name': role, 'version': '0.1.0'}))
        write(extensions, role + '/index.html', '<html lang="ko"><title>demo</title></html>')
        write(extensions, role + '/analysis-status.js', 'export const fixture=true;')
    return root, extensions


@pytest.mark.parametrize('change', ['source_bytes', 'new_source', 'extension_bytes', 'new_extension'])
def test_current_source_check_rejects_stale_but_valid_archive(submission, tmp_path, change):
    root, extensions = submission
    output = tmp_path / 'submission.zip'
    package_submission(root, output, extensions)
    assert inspect_current_archive(output, root, extensions)['version']
    original_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    if change == 'source_bytes':
        write(root, 'apps/api/app/main.py', '# changed runtime\n')
    elif change == 'new_source':
        write(root, 'apps/extensions/student/practice-progress.js', 'export const current=true;')
    elif change == 'extension_bytes':
        write(extensions, 'student/analysis-status.js', 'export const updated=true;')
    else:
        write(extensions, 'student/practice-progress.js', 'export const current=true;')
    # Integrity alone still passes, but it must no longer be delivered as current.
    assert inspect_archive(output)['version']
    with pytest.raises(ValueError, match='current source'):
        inspect_current_archive(output, root, extensions)
    assert hashlib.sha256(output.read_bytes()).hexdigest() == original_hash


def test_allowlist_excludes_private_environment_db_backups_caches_and_raw_media(
        submission: tuple[Path, Path], tmp_path: Path) -> None:
    root, extensions = submission
    planted = [
        '.env', '.env.production', 'deploy/actual.env', 'apps/api/app/accounts.sqlite',
        'apps/api/app/data/private/accounts.sqlite', 'apps/api/app/db/old.db',
        'apps/api/app/backup/restore.py', 'apps/api/app/private/notes.py',
        'apps/api/app/__pycache__/x.py', 'apps/api/app/secrets.json',
        'apps/web/upload.mp4', 'samples/private-user.mp4', 'docs/verification/user.txt',
        '.a11y-history/old/findings.json', 'node_modules/x/index.js', '.venv/key.py',
        'unexpected-root.py',
    ]
    for name in planted:
        write(root, name, 'sensitive planted data')
    output = tmp_path / 'submission.zip'
    report = package_submission(root, output, extensions)
    assert report['published'] is False
    checked = inspect_archive(output)
    names = {row['path'] for row in checked['files']}
    assert not names.intersection(planted)
    assert {'.env.example', 'deploy/extension.env.example', 'samples/accessibility-demo.mp4'} <= names
    assert {'dist/extensions/student/manifest.json', 'dist/extensions/guardian/index.html'} <= names
    assert {'scripts/verify_all.sh', 'docs/EXTENSION_SUBMISSION_REPORT.md', 'dist/extensions/student/analysis-status.js'} <= names
    assert len(checked['files']) + 1 == report['files']
    with zipfile.ZipFile(output) as archive:
        assert archive.getinfo(PREFIX + '/START_LOCAL.command').external_attr >> 16 & stat.S_IXUSR
        archive.extractall(tmp_path / 'review')
    result = subprocess.run([sys.executable, 'run_local.py', '--sample'],
                            cwd=tmp_path / 'review' / PREFIX, capture_output=True, text=True, check=True)
    assert result.stdout.strip() == 'sample-ready'


def test_secret_scan_fails_without_printing_or_overwriting_existing_output(
        submission: tuple[Path, Path], tmp_path: Path) -> None:
    root, extensions = submission
    secret = 'AIza' + 'A' * 35
    write(root, 'apps/api/app/leaked.py', 'API_KEY=' + repr(secret))
    output = write(tmp_path, 'old.zip', b'previous-reviewed-output')
    with pytest.raises(ValueError, match='credential') as error:
        package_submission(root, output, extensions)
    assert secret not in str(error.value)
    assert output.read_bytes() == b'previous-reviewed-output'


def test_environment_example_rejects_filled_secret(submission: tuple[Path, Path], tmp_path: Path) -> None:
    root, extensions = submission
    write(root, '.env.example', 'GEMINI_API_KEY=unapproved-value\n')
    with pytest.raises(ValueError, match='non-placeholder'):
        package_submission(root, tmp_path / 'output.zip', extensions)


def test_symlink_input_is_rejected(submission: tuple[Path, Path], tmp_path: Path) -> None:
    root, extensions = submission
    target = write(tmp_path, 'outside.py', 'private data')
    (root / 'apps/api/app/link.py').symlink_to(target)
    with pytest.raises(ValueError, match='Symlink'):
        package_submission(root, tmp_path / 'output.zip', extensions)


def test_sample_manifest_cannot_admit_extra_or_traversing_media(
        submission: tuple[Path, Path], tmp_path: Path) -> None:
    root, extensions = submission
    manifest = root / 'samples/public-manifest.json'
    data = json.loads(manifest.read_text())
    data['assets'].append({'path': '../private.mp4', 'provenance': 'generated', 'license': 'CC0'})
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='declared public'):
        package_submission(root, tmp_path / 'output.zip', extensions)


@pytest.mark.parametrize('name', ['../escape.py', '/absolute.py', 'Sullivan-AI/../escape.py',
                                   'Sullivan-AI\\escape.py', 'Sullivan-AI/.env',
                                   'Sullivan-AI/data/private/accounts.sqlite'])
def test_archive_inspection_rejects_unsafe_or_private_paths(tmp_path: Path, name: str) -> None:
    output = tmp_path / 'hostile.zip'
    with zipfile.ZipFile(output, 'w') as archive:
        info = zipfile.ZipInfo(name)
        info.external_attr = (stat.S_IFREG | 0o644) << 16
        archive.writestr(info, 'never extract')
    with pytest.raises(ValueError):
        inspect_archive(output)


def test_archive_inspection_rejects_symlinks(tmp_path: Path) -> None:
    output = tmp_path / 'hostile.zip'
    with zipfile.ZipFile(output, 'w') as archive:
        info = zipfile.ZipInfo(PREFIX + '/app.py')
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, '/private/file')
    with pytest.raises(ValueError, match='regular'):
        inspect_archive(output)


def test_archive_checksum_cannot_hide_content_tampering(submission: tuple[Path, Path], tmp_path: Path) -> None:
    root, extensions = submission
    source = tmp_path / 'source.zip'
    package_submission(root, source, extensions)
    tampered = tmp_path / 'tampered.zip'
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(tampered, 'w') as target:
        for entry in original.infolist():
            content = original.read(entry.filename)
            target.writestr(entry, b'changed' if entry.filename.endswith('/run_local.py') else content)
    with pytest.raises(ValueError, match='checksum'):
        inspect_archive(tampered)


def test_archive_content_scan_rejects_secret_even_with_matching_manifest(
        submission: tuple[Path, Path], tmp_path: Path) -> None:
    root, extensions = submission
    source = tmp_path / 'source.zip'
    package_submission(root, source, extensions)
    secret = ('AIza' + 'B' * 35).encode()
    content = b'API_KEY=' + secret
    with zipfile.ZipFile(source) as archive:
        entries = [(entry, archive.read(entry.filename)) for entry in archive.infolist()]
    manifest = json.loads(next(data for entry, data in entries if entry.filename == PREFIX + '/' + MANIFEST))
    row = next(row for row in manifest['files'] if row['path'] == 'run_local.py')
    row.update(bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
    output = tmp_path / 'secret.zip'
    with zipfile.ZipFile(output, 'w') as archive:
        for entry, data in entries:
            if entry.filename == PREFIX + '/run_local.py':
                data = content
            elif entry.filename == PREFIX + '/' + MANIFEST:
                data = json.dumps(manifest).encode()
            archive.writestr(entry, data)
    with pytest.raises(ValueError, match='credential') as error:
        inspect_archive(output)
    assert secret.decode() not in str(error.value)


def test_extracted_real_api_assigns_and_opens_sample_without_credentials(
        submission: tuple[Path, Path], tmp_path: Path) -> None:
    root, extensions = submission
    # Copy source modules only; never copy this workspace's runtime DB or env.
    for directory in ('apps/api/app', 'packages/test-fixtures', 'packages/contracts', 'apps/web'):
        for source in (ROOT / directory).rglob('*'):
            if source.is_file() and source.suffix in {'.py', '.sql', '.json', '.js', '.html', '.css'} and '__pycache__' not in source.parts:
                write(root, source.relative_to(ROOT).as_posix(), source.read_bytes())
    for name in ('run_local.py', 'START_LOCAL.command', 'scripts/verify_project.py'):
        write(root, name, (ROOT / name).read_bytes())
    output = tmp_path / 'runtime.zip'
    package_submission(root, output, extensions)
    inspect_archive(output)
    with zipfile.ZipFile(output) as archive:
        archive.extractall(tmp_path / 'isolated')
    extracted = tmp_path / 'isolated' / PREFIX
    code = '''
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app,base_url='http://127.0.0.1')
def headers(role,token=None):
    return {'X-Sullivan-Client':role,'X-Local-Request':'1','Origin':'chrome-extension://'+'a'*32,**({'Authorization':'Bearer '+token} if token else {})}
g=client.post('/extension/v1/guardian/register',headers=headers('guardian'),json={'username':'submission-guardian','password':'submission-fixture-pass'});assert g.status_code==200
gh=headers('guardian',g.json()['token'])
s=client.post('/local/students',headers=gh,json={'username':'submission-student','password':'submission-fixture-pass','name':'Demo student'});assert s.status_code==200
login=client.post('/extension/v1/student/session',headers=headers('student'),json={'username':'submission-student','password':'submission-fixture-pass'});assert login.status_code==200
lesson=client.post('/local/samples/science/assign',headers=gh,json={'students':[s.json()['id']]});assert lesson.status_code==200
opened=client.get('/extension/v1/student/lectures/'+lesson.json()['id'],headers=headers('student',login.json()['token']));assert opened.status_code==200
assert opened.json()['snapshot']['transcript_segments']
assert client.get('/health').json()['raw_video_storage']=='disabled'
print('extracted-key-free-sample-pass')
'''
    env = dict(os.environ)
    for name in ('GEMINI_API_KEY', 'DATABASE_URL', 'DATABASE_URL_UNPOOLED', 'RENDER', 'SULLIVAN_EXTENSION_CLIENTS', 'SULLIVAN_PUBLIC_URL', 'LINK_ANALYZER_URL', 'LINK_ANALYZER_TOKEN'):
        env.pop(name, None)
    env.update(PYTHONPATH=str(extracted / 'apps/api'), SULLIVAN_ROLE_AUTH='1',
               SULLIVAN_PRODUCTION='0', SULLIVAN_SIGNUP_ENABLED='1', SULLIVAN_MIN_EXTENSION_VERSION='0.1.0',
               SULLIVAN_ACCOUNTS_DB=str(tmp_path / 'isolated-accounts.sqlite'), DEMO_USAGE_DB=str(tmp_path / 'isolated-usage.sqlite'))
    result = subprocess.run([sys.executable, '-c', code], cwd=extracted, env=env,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr[-2000:]
    assert 'extracted-key-free-sample-pass' in result.stdout
    subprocess.run([sys.executable, 'scripts/verify_project.py'], cwd=extracted,
                   env=env, capture_output=True, text=True, timeout=30, check=True)
    help_result = subprocess.run([sys.executable, 'run_local.py', '--help'], cwd=extracted,
                                 env=env, capture_output=True, text=True, timeout=10, check=True)
    assert '--sample' in help_result.stdout
