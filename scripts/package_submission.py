"""Build an allowlisted, credential-free source submission; never publish it."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from typing import Any
import zipfile

from build_extensions import LEARNING_MODULES, ROOT, STUDENT_MODULES, VERSION, build

PREFIX = 'Sullivan-AI'
MANIFEST = 'SUBMISSION_MANIFEST.json'
ROOT_FILES = frozenset({
    'AGENTS.md', 'README.md', 'START_HERE.md', 'CONTRIBUTING.md',
    'START_LOCAL.command', 'RUN_WINDOWS.bat', 'STOP_WINDOWS.bat', 'run_local.py',
    'package.json', 'package-lock.json', 'Dockerfile', '.dockerignore', '.gitignore',
    'render.yaml', 'railway.json', 'docker-compose.yml', '.env.example',
    'DEPLOY_RENDER.md', 'DEPLOY_RAILWAY.md',
})
DOC_FILES = frozenset({
    'SUBMISSION_INSTALL.md', 'extension-feature-contract.json', 'SAFETY_COPYRIGHT.md',
    'ANALYSIS_PACKAGE.md', 'ARCHITECTURE.md', 'PRODUCT_SPEC.md', 'TEST_PLAN.md',
    'EXTENSION_DEVELOPMENT_PLAN.md', 'EXTENSION_OPERATIONS.md',
    'EXTENSION_CHROME_PLAYBACK.md', 'EXTENSION_REMOTE_LOGIN.md',
    'EXTENSION_SUBMISSION_REPORT.md',
})
TREE_SUFFIXES = {
    'apps/api/app': {'.py', '.sql'},
    'apps/api/tests': {'.py'},
    'apps/extensions': {'.js', '.html', '.css', '.md'},
    'apps/web': {'.js', '.html', '.css', '.json', '.md', '.png'},
    'scripts': {'.py', '.js', '.mjs', '.txt', '.sh'},
    'packages/test-fixtures': {'.json'},
    'packages/contracts': {'.json'},
    'docs/demo': {'.md', '.txt'},
}
EXAMPLES = frozenset({'.env.example', 'deploy/extension.env.example'})
PUBLIC_SAMPLES = frozenset({
    'accessibility-demo.json', 'accessibility-demo.srt',
    'accessibility-demo.txt', 'accessibility-demo.mp4',
})
MEDIA_SUFFIXES = frozenset({'.mp4', '.webm', '.mov', '.m4v', '.mkv', '.avi', '.mpg', '.mpeg', '.ts', '.mp3', '.wav'})
BLOCKED_PARTS = frozenset({
    '.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', '.cache', '.a11y-history', 'verification',
    'test-results', 'playwright-report', 'data', 'private', 'backups', 'backup',
})
BLOCKED_SUFFIXES = frozenset({'.db', '.sqlite', '.sqlite3', '.bak', '.backup', '.pyc', '.pyo', '.pem', '.key', '.p12', '.pfx', '.zip', '.log'})
SECRET_PATTERNS = (
    re.compile(rb'AIza[0-9A-Za-z_-]{30,}'),
    re.compile(rb'\bsk-(?:proj-)?[0-9A-Za-z_-]{20,}'),
    re.compile(rb'\b(?:ghp_|gho_|github_pat_)[0-9A-Za-z_]{24,}'),
    re.compile(rb'\bAKIA[0-9A-Z]{16}\b'),
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(rb'\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}'),
)
MAX_FILE_BYTES = 64_000_000
MAX_TOTAL_BYTES = 128_000_000
REQUIRED_SOURCE = frozenset({'run_local.py', 'START_LOCAL.command', 'apps/api/requirements.txt',
                             'apps/api/app/main.py', 'apps/web/index.html', 'docs/SUBMISSION_INSTALL.md'})
EXTENSION_BASE = frozenset({'client.js', 'ui.js', 'accounts.js', 'base.css', 'tokens.css',
                            'app.js', 'worker.js', 'config.js', 'manifest.json', 'index.html', 'analysis-status.js',
                            'icons/16.png', 'icons/32.png', 'icons/48.png', 'icons/128.png'})


def safe_name(name: str) -> bool:
    """Archive paths always use relative POSIX names, with no alternate separators."""
    path = PurePosixPath(name)
    return bool(name and '\\' not in name and ':' not in name and '\x00' not in name
                and not path.is_absolute() and all(part not in ('', '.', '..') for part in name.split('/')))


def forbidden(name: str) -> bool:
    path = PurePosixPath(name)
    if not safe_name(name):
        return True
    if any(part.lower() in BLOCKED_PARTS for part in path.parts):
        return True
    basename = path.name.lower()
    if basename.startswith('.env') or '.env.' in basename or basename.endswith('.env'):
        return name not in EXAMPLES
    return (path.suffix.lower() in BLOCKED_SUFFIXES or basename.endswith('~')
            or bool(re.match(r'(?:secrets?|credentials?)(?:[._-]|$)', basename)))


def allowlisted(name: str) -> bool:
    if name == MANIFEST or name in ROOT_FILES | EXAMPLES | {'apps/api/requirements.txt', '.github/workflows/ci.yml'}:
        return True
    if name.startswith('docs/') and name[5:] in DOC_FILES:
        return True
    if name in {'samples/' + sample for sample in PUBLIC_SAMPLES} | {'samples/public-manifest.json'}:
        return True
    for role in ('student', 'guardian'):
        prefix = f'dist/extensions/{role}/'
        names = EXTENSION_BASE
        if role == 'student':
            names |= frozenset(STUDENT_MODULES + LEARNING_MODULES + ('learning-response.js', 'speech-profile.js'))
        else:
            names |= frozenset({'entry.js'})
        if name.startswith(prefix):
            return name[len(prefix):] in names
    for directory, suffixes in TREE_SUFFIXES.items():
        if name.startswith(directory + '/') and PurePosixPath(name).suffix.lower() in suffixes:
            return not name.endswith('.png') or name.startswith('apps/web/intro/img/')
    return False


def scan_content(name: str, content: bytes) -> None:
    """Reject recognizable credential material without ever echoing its value."""
    if any(pattern.search(content) for pattern in SECRET_PATTERNS):
        raise ValueError('Recognizable credential/private-key material detected; package not written.')
    for match in re.finditer(rb'postgres(?:ql)?://[^\s/:]+:([^\s/@]+)@', content):
        if match.group(1).lower() not in {b'ci-only', b'test', b'password', b'postgres', b'replace_me', b'your_password'}:
            raise ValueError('Database credential detected; package not written.')
    if name in EXAMPLES:
        for line in content.decode('utf-8').splitlines():
            match = re.match(r'\s*([A-Z_]*(?:API_KEY|ACCESS_TOKEN|SECRET|PASSWORD|ACCESS_CODE))\s*=\s*(.*)', line)
            if match and match.group(2).strip().strip('\'"') and not re.search(
                    r'(?i)replace|example|placeholder|your[_ -]|<[^>]+>', match.group(2)):
                raise ValueError('Environment example contains a non-placeholder credential.')


def validate_public_manifest(data: Any) -> set[str]:
    if not isinstance(data, dict):
        raise ValueError('Public sample provenance manifest is invalid.')
    rows = data.get('assets', [])
    if data.get('schema_version') != 1 or not isinstance(rows, list):
        raise ValueError('Public sample provenance manifest is invalid.')
    assets: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Public sample provenance entry is invalid.')
        path = row.get('path', '')
        license_name = row.get('license')
        if (not isinstance(path, str) or path not in PUBLIC_SAMPLES or path in assets
                or row.get('provenance') not in {'self-authored', 'generated'}
                or not isinstance(license_name, str) or not license_name.strip()):
            raise ValueError('Only explicitly declared public demonstration samples are permitted.')
        assets.add(path)
    if assets != PUBLIC_SAMPLES:
        raise ValueError('All four public demonstration samples and their provenance are required.')
    return {'samples/' + name for name in assets} | {'samples/public-manifest.json'}


def public_assets(root: Path) -> set[str]:
    manifest = root / 'samples/public-manifest.json'
    if manifest.is_symlink():
        raise ValueError('Symlink in public sample manifest.')
    return validate_public_manifest(json.loads(manifest.read_text(encoding='utf-8')))


def source_files(root: Path) -> tuple[dict[str, Path], dict[str, int]]:
    selected: dict[str, Path] = {}
    excluded: Counter[str] = Counter()
    sample_names = public_assets(root)

    def add(file: Path, name: str) -> None:
        if file.is_symlink() or any(parent.is_symlink() for parent in file.parents if parent != root.parent):
            raise ValueError('Symlink is not permitted in submission inputs.')
        if forbidden(name):
            excluded['private_or_generated'] += 1
            return
        if file.is_file():
            selected[name] = file

    for name in ROOT_FILES | EXAMPLES | {'apps/api/requirements.txt', '.github/workflows/ci.yml'}:
        if (root / name).exists():
            add(root / name, name)
    for name in DOC_FILES:
        if (root / 'docs' / name).exists():
            add(root / 'docs' / name, 'docs/' + name)
    for directory, suffixes in TREE_SUFFIXES.items():
        tree = root / directory
        if tree.is_symlink():
            raise ValueError('Symlink source directory is not permitted.')
        for file in sorted(tree.rglob('*')) if tree.exists() else []:
            name = file.relative_to(root).as_posix()
            if file.is_symlink():
                raise ValueError('Symlink is not permitted in submission inputs.')
            if not file.is_file():
                continue
            if file.suffix.lower() not in suffixes:
                excluded['not_allowlisted_type'] += 1
            elif file.suffix.lower() == '.png' and not name.startswith('apps/web/intro/img/'):
                excluded['not_public_ui_asset'] += 1
            else:
                add(file, name)
    for name in sample_names:
        if not (root / name).is_file():
            raise ValueError('A required public demonstration sample is missing.')
        add(root / name, name)
    if not REQUIRED_SOURCE <= selected.keys():
        raise ValueError('Submission is missing required runtime or installation files.')
    return selected, dict(excluded)


def inspect_archive(path: Path) -> dict[str, Any]:
    """Verify actual archive entries, content and checksums before delivery/extraction."""
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len({entry.filename for entry in entries}) != len(entries):
            raise ValueError('Duplicate archive path.')
        for entry in entries:
            if not safe_name(entry.filename) or not entry.filename.startswith(PREFIX + '/'):
                raise ValueError('Unsafe archive path.')
            relative = entry.filename[len(PREFIX) + 1:]
            mode = entry.external_attr >> 16
            if entry.is_dir() or stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                raise ValueError('Archive must contain regular files only.')
            if forbidden(relative) or not allowlisted(relative):
                raise ValueError('Private/generated or non-allowlisted path in archive.')
            if entry.file_size > MAX_FILE_BYTES:
                raise ValueError('Oversized archive entry.')
        if sum(entry.file_size for entry in entries) > MAX_TOTAL_BYTES:
            raise ValueError('Oversized submission archive.')
        manifest = json.loads(archive.read(PREFIX + '/' + MANIFEST))
        rows = manifest['files']
        if len({row['path'] for row in rows}) != len(rows):
            raise ValueError('Duplicate manifest entry.')
        if not REQUIRED_SOURCE <= {row['path'] for row in rows}:
            raise ValueError('Required runtime files missing from archive.')
        expected = {PREFIX + '/' + row['path'] for row in rows} | {PREFIX + '/' + MANIFEST}
        if expected != {entry.filename for entry in entries}:
            raise ValueError('Archive manifest entries do not match actual files.')
        public_names = validate_public_manifest(json.loads(archive.read(PREFIX + '/samples/public-manifest.json')))
        if not public_names <= {row['path'] for row in rows}:
            raise ValueError('Declared public demonstration sample missing from archive.')
        for row in rows:
            name = row['path']
            content = archive.read(PREFIX + '/' + name)
            if hashlib.sha256(content).hexdigest() != row['sha256'] or len(content) != row['bytes']:
                raise ValueError('Archive checksum mismatch.')
            if PurePosixPath(name).suffix.lower() in MEDIA_SUFFIXES and name != 'samples/accessibility-demo.mp4':
                raise ValueError('Only the declared generated public sample video is allowed.')
            scan_content(name, content)
        scan_content(MANIFEST, archive.read(PREFIX + '/' + MANIFEST))
        return manifest


def package_submission(root: Path = ROOT, output: Path | None = None,
                       extensions: Path | None = None, server: str = 'http://127.0.0.1:8770') -> dict[str, Any]:
    if root.is_symlink():
        raise ValueError('Symlink source root is not permitted.')
    root = root.resolve()
    output = output or root / 'dist/submission' / f'sullivan-submission-{VERSION}.zip'
    selected, excluded = source_files(root)
    with tempfile.TemporaryDirectory(prefix='sullivan-submission-') as temporary:
        workspace = Path(temporary)
        if extensions is None:
            if root != ROOT.resolve():
                raise ValueError('An alternate source root requires explicitly built extension inputs.')
            extensions = build(server, workspace / 'extensions')
        if extensions.is_symlink():
            raise ValueError('Symlink extension directory is not permitted.')
        for role in ('student', 'guardian'):
            folder = extensions / role
            if folder.is_symlink():
                raise ValueError('Symlink extension directory is not permitted.')
            if not (folder / 'manifest.json').is_file() or not (folder / 'index.html').is_file():
                raise ValueError('Both generated extension install folders are required.')
            for file in sorted(folder.rglob('*')):
                relative = file.relative_to(folder).as_posix()
                name = f'dist/extensions/{role}/{relative}'
                if file.is_symlink():
                    raise ValueError('Symlink in extension install folder.')
                if file.is_file():
                    if forbidden(name) or not allowlisted(name):
                        raise ValueError('Unexpected/private file in extension install folder.')
                    selected[name] = file
        contents: dict[str, bytes] = {}
        for name, file in sorted(selected.items()):
            if file.stat().st_size > MAX_FILE_BYTES:
                raise ValueError('Oversized submission input.')
            content = file.read_bytes()
            scan_content(name, content)
            contents[name] = content
        if sum(map(len, contents.values())) > MAX_TOTAL_BYTES:
            raise ValueError('Submission exceeds maximum uncompressed size.')
        manifest: dict[str, Any] = {
            'schema_version': 1, 'version': VERSION, 'package_type': 'local-source-submission',
            'server': server, 'published': False, 'archive_root': PREFIX,
            'files': [{'path': name, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
                      for name, content in contents.items()],
            'exclusion_policy': {'selection': 'Explicit roots, extensions and public sample provenance; independent of git tracking.',
                'excluded': ['Actual environment files/credentials', 'User/account databases and backups',
                             'Private/raw media except declared generated demonstration MP4',
                             'Git, virtualenv, node_modules, caches, old verification and accessibility dumps'],
                'recognized_secret_scan': 'API key/token/private-key signatures, credential-bearing PostgreSQL URLs and non-placeholder environment-example credentials',
                'limitations': 'Signature scans do not prove arbitrary text contains no secret; review source before distribution.',
                'counts_in_selected_trees': excluded},
        }
        staged = workspace / 'submission.zip'
        with zipfile.ZipFile(staged, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in {**contents, MANIFEST: (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()}.items():
                info = zipfile.ZipInfo(PREFIX + '/' + name, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                executable = name.endswith(('.command', '.sh'))
                info.external_attr = (stat.S_IFREG | (0o755 if executable else 0o644)) << 16
                archive.writestr(info, content)
        inspect_archive(staged)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(staged.read_bytes())
    return {'version': VERSION, 'file': str(output), 'files': len(contents) + 1,
            'bytes': output.stat().st_size, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'published': False}


def inspect_current_archive(path: Path, root: Path = ROOT,
                            extensions: Path | None = None) -> dict[str, Any]:
    """Reject an internally valid archive whose sources or generated UI are stale."""
    actual = inspect_archive(path)
    with tempfile.TemporaryDirectory(prefix='sullivan-current-submission-') as temporary:
        current = Path(temporary) / 'current.zip'
        package_submission(root, current, extensions, server=actual['server'])
        expected = inspect_archive(current)
    fingerprints = lambda manifest: {row['path']: (row['bytes'], row['sha256']) for row in manifest['files']}
    if actual['version'] != expected['version'] or fingerprints(actual) != fingerprints(expected):
        raise ValueError('Submission archive does not match current source and generated extensions. Rebuild it before delivery.')
    return actual


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--server', default='http://127.0.0.1:8770')
    parser.add_argument('--inspect', type=Path, help='Validate an existing archive without extracting it.')
    parser.add_argument('--check-current', action='store_true', help='With --inspect, also compare against current source and freshly built extensions.')
    args = parser.parse_args()
    if args.check_current and not args.inspect:
        parser.error('--check-current requires --inspect')
    if args.inspect:
        checked = inspect_current_archive(args.inspect) if args.check_current else inspect_archive(args.inspect)
        print(json.dumps({'result': 'passed', 'version': checked['version'], 'files': len(checked['files']) + 1,
                          **({'current_source_match': True} if args.check_current else {})}))
    else:
        print(json.dumps(package_submission(output=args.output, server=args.server), ensure_ascii=False, indent=2))
