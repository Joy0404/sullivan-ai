import sys, json, time, tempfile, hashlib
from pathlib import Path

sys.path.insert(0, str(Path('scripts').resolve()))
from verify_extensions_browser import main
from verify_extensions_phase3 import video_fixture
from playwright.sync_api import expect

out = Path('.a11y-history/2026-11-14-recheck-optimize/runtime-forms-media').resolve()
out.mkdir(parents=True, exist_ok=True)
observed = {}

def persist():
    (out / 'observations.json').write_text(json.dumps(observed, ensure_ascii=False, indent=2) + '\n')

def probe(guardian, student, output):
    from app import local_access
    guardian.evaluate("""()=>{const original=File.prototype.text;window.fileReadStarted=false;window.fileReadGate=new Promise(resolve=>window.releaseFileRead=resolve);File.prototype.text=async function(){const text=await original.call(this);if(this.name==='account-a-private.txt'){window.fileReadStarted=true;await window.fileReadGate;}return text;};}""")
    guardian.locator('#prepare-form [name=title]').fill('Account A private import')
    guardian.locator('#material-files').set_input_files({'name': 'account-a-private.txt', 'mimeType': 'text/plain', 'buffer': b'PRIVATE_A_MATERIAL. This learning text belongs to account A.'})
    guardian.locator('#prepare-form button[type=submit]').click()
    guardian.wait_for_function('()=>window.fileReadStarted===true')
    guardian.locator('#logout').click()
    expect(guardian.locator('#auth')).to_be_visible()
    if not guardian.locator('#register-form').is_visible():
        guardian.get_by_text('로컬 개발 계정 만들기', exact=True).click()
    form = guardian.locator('#register-form')
    form.locator('[name=name]').fill('Synthetic Guardian B')
    form.locator('[name=username]').fill('guardian_new_account')
    form.locator('[name=password]').fill('extension-pass-123')
    form.locator('button').click()
    expect(guardian.locator('#workspace')).to_be_visible()
    expect(guardian.locator('#account-name')).to_have_text('Synthetic Guardian B')
    with guardian.expect_response(lambda r: r.request.method == 'POST' and r.url.endswith('/extension/v1/guardian/preparations')) as response:
        guardian.evaluate('window.releaseFileRead()')
    guardian.wait_for_function("()=>document.getElementById('preparations').textContent.includes('Account A private import')")
    with local_access.db() as con:
        row = con.execute("SELECT p.title,p.state,p.snapshot,u.username AS owner FROM preparations p JOIN users u ON p.guardian=u.id WHERE p.title='Account A private import'").fetchone()
        observed['crossAccountFileRead'] = {'httpStatus': response.value.status, 'currentAccount': guardian.locator('#account-name').inner_text(), 'storedOwner': row['owner'], 'title': row['title'], 'state': row['state'], 'containsAccountAMaterial': 'PRIVATE_A_MATERIAL' in (row['snapshot'] or '')}
    persist()
    guardian.locator('#prepare-guided').click()
    guardian.locator('#prepare-form [name=title]').fill('Invalid JSON focus probe')
    guardian.locator('#prepare-next').click()
    guardian.locator('#material-files').set_input_files({'name': 'broken.json', 'mimeType': 'application/json', 'buffer': b'{'})
    guardian.locator('#prepare-next').click()
    guardian.locator('#prepare-form button[type=submit]').click()
    expect(guardian.locator('#error')).to_contain_text('JSON')
    observed['guidedInvalidJson'] = guardian.evaluate("""()=>({stage:document.getElementById('prepare-step').textContent,error:document.getElementById('error').textContent,localError:document.getElementById('material-validation').textContent,fileVisible:!!document.getElementById('material-files').getClientRects().length,fileInvalid:document.getElementById('material-files').getAttribute('aria-invalid'),active:document.activeElement.id||document.activeElement.textContent.trim()})""")
    guardian.screenshot(path=str(output / 'guided-invalid-json.png'), full_page=True)
    persist()
    guardian.locator('#prepare-back').click()
    guardian.locator('#material-files').set_input_files({'name': 'large.txt', 'mimeType': 'text/plain', 'buffer': b'x' * 300001})
    guardian.locator('#prepare-next').click()
    guardian.locator('#prepare-form button[type=submit]').click()
    expect(guardian.locator('#material-files')).to_be_focused()
    observed['guidedPerFileLimit'] = guardian.evaluate("""()=>({stage:document.getElementById('prepare-step').textContent,localError:document.getElementById('material-validation').textContent,fileVisible:!!document.getElementById('material-files').getClientRects().length,fileInvalid:document.getElementById('material-files').getAttribute('aria-invalid'),active:document.activeElement.id})""")
    persist()
    with tempfile.TemporaryDirectory(prefix='sullivan-synthetic-preview-') as temporary:
        movie = Path(temporary) / 'preview.mp4'
        video_fixture(movie)
        raw = movie.read_bytes()
        identity = {'kind': 'local-reference', 'name': 'preview.mp4', 'size_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        with local_access.db() as con:
            owner = con.execute("SELECT id FROM users WHERE username='guardian_new_account'").fetchone()[0]
            snapshot = con.execute('SELECT snapshot FROM lectures LIMIT 1').fetchone()[0]
            for ident in ['preview-a', 'preview-b']:
                con.execute('INSERT INTO preparations(id,guardian,session_id,title,subject,source_kind,state,message,snapshot,playback,instance,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', (ident, owner, ident + '-session', ident, '일반', 'video', 'completed', '검사용 준비 완료', snapshot, json.dumps(identity), 'audit', time.time()))
        guardian.locator('#refresh-preparations').click()
        guardian.get_by_role('button', name='preview-a 결과 확인·배정', exact=True).click()
        expect(guardian.locator('#prepared-detail')).to_be_visible()
        guardian.locator('#preview-file').set_input_files(str(movie))
        guardian.wait_for_function('()=>document.getElementById("preview-video").readyState>=1')
        guardian.evaluate('document.getElementById("preview-video").play()')
        guardian.wait_for_function('()=>document.getElementById("preview-video").paused===false')
        guardian.evaluate("""()=>{const original=window.fetch;window.previewRequestStarted=false;window.previewGate=new Promise(resolve=>window.releasePreviewFailure=resolve);window.fetch=async(...args)=>{if(String(args[0]).endsWith('/extension/v1/guardian/preparations/preview-b')){window.previewRequestStarted=true;await window.previewGate;throw new Error('Synthetic held fetch failure');}return original(...args);};}""")
        guardian.get_by_role('button', name='preview-b 결과 확인·배정', exact=True).click()
        guardian.wait_for_function('()=>window.previewRequestStarted===true')
        observed['hiddenPreviewPending'] = guardian.evaluate("""()=>({panelHidden:document.getElementById('prepared-detail').hidden,videoPaused:document.getElementById('preview-video').paused,videoHidden:!document.getElementById('preview-video').getClientRects().length,hasSource:!!document.getElementById('preview-video').getAttribute('src')})""")
        guardian.evaluate('window.releasePreviewFailure()')
        expect(guardian.locator('#error')).to_contain_text('서버')
        observed['hiddenPreviewFailed'] = guardian.evaluate("""()=>({panelHidden:document.getElementById('prepared-detail').hidden,videoPaused:document.getElementById('preview-video').paused,videoHidden:!document.getElementById('preview-video').getClientRects().length,hasSource:!!document.getElementById('preview-video').getAttribute('src')})""")
        guardian.evaluate('document.getElementById("preview-video").pause()')
        persist()
    print(json.dumps(observed, ensure_ascii=False))
    return guardian

main(probe, phase='recheck-optimize-forms-media', output=out)
