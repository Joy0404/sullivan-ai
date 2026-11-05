"""Local launcher lifecycle checks; no credentials, accounts or providers."""
import argparse
import importlib.util
from pathlib import Path
import shutil
import signal
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('sullivan_launcher', ROOT / 'run_local.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def args():
    return argparse.Namespace(port=8770, restart=False, sample=False,
                              no_open=True)


@pytest.fixture
def occupied(monkeypatch):
    monkeypatch.setattr(launcher, 'port_available', lambda port: False)
    monkeypatch.setattr(launcher, 'local_server', lambda port: {
        'pid': 12345, 'build': 'current-build', 'sample': True})
    monkeypatch.setattr(launcher.os, 'kill', lambda *a: pytest.fail('Unexpected process termination'))


def test_duplicate_reuses_sample_without_prompting_for_secrets(occupied, monkeypatch, capsys):
    monkeypatch.setattr(launcher.getpass, 'getpass', lambda *a: pytest.fail('Must not prompt'))
    monkeypatch.setattr(launcher.webbrowser, 'open', lambda *a: pytest.fail('no-open was requested'))
    assert launcher.handle_existing(args(), 'current-build')
    output = capsys.readouterr().out
    assert '이미 실행 중' in output and '샘플 전용' in output and '--restart' in output


def test_duplicate_opens_the_verified_app(occupied, monkeypatch):
    opened = []
    monkeypatch.setattr(launcher.webbrowser, 'open', lambda url: opened.append(url))
    options = args(); options.no_open = False
    assert launcher.handle_existing(options, 'current-build')
    assert opened == ['http://127.0.0.1:8770']


def test_unknown_listener_is_never_stopped(occupied, monkeypatch):
    monkeypatch.setattr(launcher, 'local_server', lambda port: None)
    options = args(); options.restart = True
    with pytest.raises(RuntimeError, match='자동으로 종료하지'):
        launcher.handle_existing(options, 'current-build')


def test_outdated_build_requires_explicit_restart(occupied):
    with pytest.raises(RuntimeError, match='--restart'):
        launcher.handle_existing(args(), 'new-build')


def test_sample_flag_does_not_silently_reuse_a_real_provider(occupied, monkeypatch):
    monkeypatch.setattr(launcher, 'local_server', lambda port: {
        'pid': 12345, 'build': 'current-build', 'sample': False})
    options = args(); options.sample = True
    with pytest.raises(RuntimeError, match='--restart --sample'):
        launcher.handle_existing(options, 'current-build')


def test_listener_change_cancels_restart(occupied, monkeypatch):
    servers = iter([{'pid': 12345, 'build': 'current-build', 'sample': True},
                    {'pid': 67890, 'build': 'current-build', 'sample': True}])
    monkeypatch.setattr(launcher, 'local_server', lambda port: next(servers))
    options = args(); options.restart = True
    with pytest.raises(RuntimeError, match='서버가 바뀌었습니다'):
        launcher.handle_existing(options, 'current-build')


@pytest.mark.skipif(not shutil.which('lsof'), reason='Local process identity requires lsof')
@pytest.mark.parametrize('same_workspace', [True, False])
def test_actual_disposable_listener_is_identified_and_restarted(tmp_path, same_workspace):
    script = tmp_path / 'fixture_server.py'
    script.write_text('''from http.server import BaseHTTPRequestHandler, HTTPServer
import json
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = ({"instance":"launcher-fixture","build":"fixture-build"}
                if self.path == "/local/status" else
                {"product":"sullivan-ai-internet-lecture-agent","real_analysis_access":"disabled"})
        body=json.dumps(data).encode();self.send_response(200)
        self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*args):pass
with HTTPServer(("127.0.0.1",0),Handler) as server:
    print(server.server_port,flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
''')
    process = subprocess.Popen([sys.executable, '-u', str(script)], cwd=ROOT if same_workspace else tmp_path,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    try:
        port = int(process.stdout.readline())
        info = launcher.local_server(port)
        if not same_workspace:
            assert info is None
            options = args(); options.port = port; options.restart = True
            with pytest.raises(RuntimeError, match='자동으로 종료하지'):
                launcher.handle_existing(options, 'fixture-build')
            assert process.poll() is None
            return
        assert info == {'pid': process.pid, 'build': 'fixture-build', 'sample': True}
        options = args(); options.port = port; options.restart = True
        assert launcher.handle_existing(options, 'fixture-build') is False
        process.wait(timeout=5)
        assert launcher.port_available(port)
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            process.wait(timeout=5)
        process.stdout.close()
