"""Build two self-contained MV3 packages. Never copy the opposite role's UI."""
import argparse
import json
from pathlib import Path
import shutil
from urllib.parse import urlsplit
from extension_icons import icon

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'apps/extensions'
STUDENT_MODULES = ('media.js', 'speech.js', 'video-control.js', 'media-store.js', 'keyboard.js', 'lesson-data.js', 'notes.js', 'remote-login-worker.js', 'remote-login-ui.js')
LEARNING_MODULES = ('playback-scheduler.js', 'narration-context.js', 'passage-tools.js',
                    'concept-tools.js', 'voice-command-router.js', 'space-gesture.js')
VERSION = '0.4.9'


def learning_response():
    """Student-only minimal fallback; broader web tools remain in the web."""
    return (SOURCE / 'student/learning-response.js').read_text()


def speech_profile():
    source=(ROOT/'apps/web/app.js').read_text()
    scoring=source[source.index('function voiceScore('):source.index('\nfunction koreanVoices(')].replace('natural|neural|online','natural|neural|online|enhanced|premium|고품질|향상')
    preparation=source[source.index('function prepareSpeechText('):source.index('\nfunction speak(text, onEnd)')]
    return '(function(root){'+scoring+preparation+'''
    function voices(list){return list.filter(v=>String(v.lang).toLowerCase().startsWith('ko')).sort((a,b)=>voiceScore(b)-voiceScore(a));}
    function select(list,uri){const ranked=voices(list);return ranked.find(v=>v.voiceURI===uri)||ranked[0];}
    root.SullivanSpeechProfile={voiceScore,voices,select,prepareSpeechText,speechChunks};
    })(globalThis);
    '''


def build(server='http://127.0.0.1:8770', output=None):
    parsed = urlsplit(server)
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment
            or (parsed.scheme == 'http' and parsed.hostname not in ('127.0.0.1', 'localhost', '::1'))):
        raise ValueError('서버 주소는 HTTPS 출처 또는 로컬 HTTP 출처여야 합니다.')
    server = server.rstrip('/')
    output = Path(output) if output else ROOT / 'dist/extensions'
    for role, label in [('student', '학생'), ('guardian', '보호자')]:
        target = output / role
        target.mkdir(parents=True, exist_ok=True)
        expected = {'client.js', 'ui.js', 'accounts.js', 'analysis-status.js', 'base.css', 'tokens.css', 'app.js', 'worker.js', 'config.js', 'manifest.json', 'index.html', 'icons'}
        if role == 'guardian':expected.add('entry.js')
        if role == 'student':
            expected.update(STUDENT_MODULES + LEARNING_MODULES + ('learning-response.js', 'speech-profile.js'))
        if {path.name for path in target.iterdir()} - expected:
            raise ValueError(f'빌드 폴더에 예상하지 않은 파일이 있습니다. 새 출력 폴더를 사용하세요: {target}')
        icons=target/'icons';icons.mkdir(exist_ok=True)
        if {path.name for path in icons.iterdir()}-{'16.png','32.png','48.png','128.png'}:raise ValueError('아이콘 폴더에 예상하지 않은 파일이 있습니다.')
        for size in (16,32,48,128):(icons/f'{size}.png').write_bytes(icon(role,size))
        for name in ('client.js', 'ui.js', 'accounts.js', 'analysis-status.js', 'base.css'):
            shutil.copyfile(SOURCE / 'shared' / name, target / name)
        shutil.copyfile(ROOT/'apps/web/tokens.css',target/'tokens.css')
        for name in ('app.js', 'worker.js'):
            shutil.copyfile(SOURCE / role / name, target / name)
        if role == 'student':
            for name in STUDENT_MODULES:
                shutil.copyfile(SOURCE / role / name, target / name)
            for name in LEARNING_MODULES:
                shutil.copyfile(ROOT / 'apps/web' / name, target / name)
            (target / 'learning-response.js').write_text(learning_response())
            (target / 'speech-profile.js').write_text(speech_profile())
        (target / 'config.js').write_text(f'export const ROLE = {json.dumps(role)};\nexport const SERVER = {json.dumps(server)};\nexport const VERSION = "{VERSION}";\n')
        manifest = {'manifest_version': 3, 'name': f'Sullivan AI {label}', 'version': VERSION,
                    'description': f'{label} 전용 분리 개발 버전: 독립 로그인과 강의 자료 연결',
                    'minimum_chrome_version': '116', 'permissions': ['storage', 'identity'],
                    'host_permissions': [f'{parsed.scheme}://{"["+parsed.hostname+"]" if ":" in parsed.hostname else parsed.hostname}/*'],
                    'background': {'service_worker': 'worker.js'},
                    'action': {'default_title': f'Sullivan AI {label} 열기', 'default_icon': {str(size):f'icons/{size}.png' for size in (16,32)}},
                    'icons': {str(size):f'icons/{size}.png' for size in (16,32,48,128)},
                    'content_security_policy': {'extension_pages': "script-src 'self'; object-src 'none'"}}
        if role == 'student':
            manifest['permissions'] += ['sidePanel', 'scripting', 'activeTab', 'alarms']
            manifest['optional_host_permissions'] = ['https://*/*', 'http://*/*']
            manifest['background']['type'] = 'module'
            manifest['side_panel'] = {'default_path': 'index.html'}
            manifest['commands'] = {'_execute_action': {'suggested_key': {'default': 'Alt+Shift+S'}, 'description': '학생 학습 패널 열기'},
                'stop-learning': {'suggested_key': {'default': 'Alt+Shift+X'}, 'description': '영상과 앱 음성 모두 중지'}}
        (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
        register = '''<details><summary>로컬 개발 계정 만들기</summary>
        <form id="register-form">
          <label>보호자 이름<input name="name" required minlength="1" maxlength="80" autocomplete="name"></label>
          <label>새 로그인 이름<input name="username" required minlength="3" maxlength="60" pattern="[a-zA-Z0-9_.\\-]+" autocomplete="username" aria-describedby="register-username-help"></label>
          <p id="register-username-help">영문·숫자·밑줄·마침표·하이픈, 3자 이상.</p>
          <label>새 비밀번호<input name="password" type="password" required minlength="8" maxlength="128" autocomplete="new-password" aria-describedby="register-password-help"></label>
          <p id="register-password-help">비밀번호는 8~128자로 입력하세요.</p>
          <button type="submit" class="secondary">보호자 개발 계정 생성</button>
        </form></details>''' if role == 'guardian' else ''
        workspace = (SOURCE / role / 'workspace.html').read_text()
        account_sections = (SOURCE / 'shared/accounts.html').read_text()
        dev_hidden = ' hidden' if parsed.scheme == 'https' else ''
        student_access='''<section class="student-access" aria-labelledby="access-title"><h2 id="access-title">읽기와 키보드 안내</h2>
<label>읽기 방식<select id="access-mode"><option value="app">앱 음성 안내</option><option value="reader">VoiceOver·NVDA 등 외부 스크린리더</option><option value="silent">초점·상태 음성 끄기</option></select></label>
<div class="actions"><button id="voice-test" type="button">음성 안내 시작·시험</button><button id="panel-keyboard" type="button" class="secondary">패널 키보드 모드 사용 중</button></div>
<p id="speech-status" role="status" aria-atomic="true">Tab은 다음 항목, Shift 또는 Shift+Tab은 이전 항목입니다. Esc는 패널 키보드 모드 해제, F6는 Chrome 영역 이동입니다.</p>
<p>강의에서 Space 한 번: 재생·정지 / 두 번: 영상·음성·진행 기능 중지 / 세 번: 텍스트 명령 / 3초 누르기: 음성 명령. 버튼 실행은 Enter를 사용하세요. 입력칸과 체크 상자의 Space는 기본 동작을 유지합니다.</p></section>''' if role=='student' else ''
        keyboard_help='Tab과 Shift+Tab은 패널 안에서 이동합니다. Shift만 누르면 이전 항목, Enter는 버튼 실행입니다. 강의에서 Space 1회는 재생·정지, 2회는 전체 중지, 3회는 텍스트 명령, 3초 누르기는 음성 명령입니다. Esc로 패널 키보드 모드를 해제하고 F6로 Chrome 영역을 이동할 수 있습니다.' if role=='student' else 'Tab과 Shift+Tab으로 이동하고 Enter 또는 Space로 버튼을 선택하세요. 오류는 안내 영역에서 확인할 수 있습니다.'
        remote_access='''<section aria-labelledby="remote-access-title"><h2 id="remote-access-title" tabindex="-1">보호자 로그인 지원</h2>
<p id="remote-login-help">처음 한 번 가입·로그인하고 보호자 연결을 승인하세요. 이 기기에서 로그인 지원도 허용하면, 다음부터 보호자가 학생 이름을 골라 로그인할 수 있습니다. 로그아웃 후에도 허용한 이 Chrome 기기에서 작동합니다. 지원 해제로 언제든 중지할 수 있습니다. Chrome이 꺼져 있거나 기기가 잠자기 상태면 다시 켠 뒤 요청을 확인합니다.</p>
<p id="remote-device-status" role="status" aria-atomic="true"></p><button id="remote-device-disable" type="button" hidden>이 기기의 보호자 로그인 지원 해제</button></section>''' if role=='student' else ''
        auth_html = f'''<section id="auth" hidden aria-labelledby="login-title"><h2 id="login-title" tabindex="-1">{label} 로그인</h2>
<p>이 프로그램은 {label} 계정만 사용합니다. 운영 서버에서는 브라우저 로그인으로 계정을 확인합니다.</p>
<label class="check"><input id="remember-login" type="checkbox"{' checked' if role=='student' else ''}>브라우저 로그인에서 내 기기 로그인 유지 (선택)</label><button id="oauth-login" type="button">브라우저에서 {label} 로그인</button>
<form id="login-form"{dev_hidden}><label>로그인 이름<input id="username" name="username" required minlength="3" maxlength="60" autocomplete="username" pattern="[a-zA-Z0-9_.\\-]+" aria-describedby="username-help"></label>
<p id="username-help">영문·숫자·밑줄·마침표·하이픈, 3자 이상.</p>
<label>비밀번호<input id="password" name="password" type="password" required minlength="8" maxlength="128" autocomplete="current-password" aria-describedby="password-help"></label>
<p id="password-help">비밀번호는 8~128자입니다.</p>
<button type="submit">{label} 로그인</button></form><div{dev_hidden}>{register}</div>
<details><summary>{label} 계정 가입</summary><form id="signup-form">
<label>이름<input name="name" required maxlength="80" autocomplete="name"></label><label>새 로그인 이름<input name="username" required minlength="3" maxlength="60" pattern="[a-zA-Z0-9_.\\-]+" autocomplete="username" aria-describedby="signup-name-help"></label><p id="signup-name-help">영문·숫자·밑줄·마침표·하이픈, 3~60자.</p>
<label>새 비밀번호<input name="password" type="password" required minlength="8" maxlength="128" autocomplete="new-password" aria-describedby="signup-pass-help"></label><p id="signup-pass-help">8~128자. 가입 후 표시되는 복구 코드를 별도로 보관하세요.</p><button type="submit">{label} 계정 만들기</button></form></details>
<details><summary>복구 코드로 비밀번호 변경</summary><form id="recover-form"><label>로그인 이름<input name="username" required minlength="3" maxlength="60" autocomplete="username"></label><label>사용하지 않은 복구 코드<input name="code" required autocomplete="off"></label><label>새 비밀번호<input name="password" type="password" required minlength="8" maxlength="128" autocomplete="new-password" aria-describedby="recover-help"></label><p id="recover-help">8~128자. 변경하면 기존 기기의 로그인을 모두 종료합니다.</p><button type="submit">비밀번호 변경</button></form></details></section>'''
        guardian_entry = ''
        guardian_help = ''
        content_open = content_close = ''
        if role == 'guardian':
            auth_html = (SOURCE/'guardian/auth.html').read_text().replace('{{DEV_HIDDEN}}', dev_hidden).replace('{{REGISTER}}', register)
            guardian_entry = (SOURCE/'guardian/entry.html').read_text()
            guardian_help = '<button id="guardian-help" type="button" class="secondary" hidden>보호자 설명서</button>'
            content_open, content_close = '<div id="guardian-content">', '</div>'
            shutil.copyfile(SOURCE/'guardian/entry.js',target/'entry.js')
        html = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sullivan AI {label}</title><link rel="stylesheet" href="tokens.css"><link rel="stylesheet" href="base.css"><script type="module" src="app.js"></script></head>
<body><a class="skip" href="#main">본문으로 이동</a>
<header><p>Sullivan AI · {label} 전용</p><span id="account-name"></span>{guardian_help}<button id="logout" type="button" hidden>로그아웃</button></header>
<main id="main" tabindex="-1"><h1>Sullivan AI {label}</h1>
{student_access}
<p id="status" role="status"></p><p id="error" role="alert"></p>
{remote_access}
{guardian_entry}
{content_open}
{auth_html}
{account_sections}
<div id="workspace" hidden>{workspace}</div>
{content_close}
<details><summary>키보드 사용 안내</summary><p>{keyboard_help}</p></details>
</main><footer><p>분리 개발 버전 {VERSION} · 기존 웹도 계속 이용할 수 있습니다.</p></footer></body></html>
'''
        (target / 'index.html').write_text(html)
        print(target)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', default='http://127.0.0.1:8770')
    args = parser.parse_args()
    build(args.server)
