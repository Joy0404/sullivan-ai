"""Fixed local Mac startup greeting; never a general text-to-speech endpoint."""
from functools import lru_cache
from ipaddress import ip_address
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

PHRASE = '학생 로그인'
PLATFORM = sys.platform
SAY = Path('/usr/bin/say')
_lock = threading.Lock()
_active = None
_recent = {}

@lru_cache(maxsize=1)
def korean_voice():
    try:
        result = subprocess.run(['/usr/bin/say', '-v', '?'], capture_output=True, text=True, timeout=3, check=True)
        voices = [line.split('ko_KR', 1)[0].strip() for line in result.stdout.splitlines() if 'ko_KR' in line]
        return 'Yuna' if 'Yuna' in voices else next(iter(voices), None)
    except (OSError, subprocess.SubprocessError):
        return None

def available(request):
    if (os.getenv('SULLIVAN_SYSTEM_LOGIN_VOICE') != '1' or PLATFORM != 'darwin'
            or os.getenv('RENDER') == 'true' or not SAY.is_file()):
        return False
    try:
        local = request.client and ip_address(request.client.host).is_loopback
    except ValueError:
        local = False
    return bool(local and request.url.hostname in {'localhost', '127.0.0.1', '::1'} and korean_voice())

def _remember(ident, state):
    now = time.monotonic()
    for key, (_, when) in list(_recent.items()):
        if now - when > 30:
            del _recent[key]
    if len(_recent) >= 256:
        del _recent[next(iter(_recent))]
    _recent[ident] = (state, now)

def stop(ident):
    """Remember early stops too: a late start request may not revive the greeting."""
    process = None
    with _lock:
        _remember(ident, 'cancelled')
        if _active and _active[0] == ident and _active[1].poll() is None:
            process = _active[1]
            process.terminate()
    if process:
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1)

def speak(ident):
    global _active
    with _lock:
        previous = _recent.get(ident)
        if previous:
            return {'completed': previous[0] == 'completed', 'cancelled': previous[0] == 'cancelled'}
        if _active and _active[1].poll() is None:
            _active[1].terminate()
            try:
                _active[1].wait(timeout=1)
            except subprocess.TimeoutExpired:
                _active[1].kill()
                _active[1].wait(timeout=1)
        _remember(ident, 'pending')
        try:
            process = subprocess.Popen(['/usr/bin/say', '-v', korean_voice(), PHRASE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            _remember(ident, 'failed')
            return {'completed': False, 'cancelled': False}
        _active = (ident, process)
    completed = False
    try:
        completed = process.wait(timeout=8) == 0
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)
        completed = False
    finally:
        with _lock:
            if _active and _active[1] is process:
                _active = None
            cancelled = _recent.get(ident, ('', 0))[0] == 'cancelled'
            _remember(ident, 'cancelled' if cancelled else 'completed' if completed else 'failed')
    return {'completed': completed and not cancelled, 'cancelled': cancelled}
