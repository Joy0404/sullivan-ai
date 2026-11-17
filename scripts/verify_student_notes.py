"""Real installed MV3 keyboard/authoring regressions with temporary accounts.

No paid calls or user DB/media. Real Chromium keys and decoded public sample;
speech boundary is explicitly stubbed, not a screen-reader or voice evaluation.
"""
import json
from pathlib import Path
import time
from playwright.sync_api import expect
from verify_extensions_browser import main, check_layout
from verify_extensions_phase3 import SPEECH


def enter(page, target):
    page.locator(target).focus()
    page.keyboard.press('Enter')


def task(page, name):
    enter(page, '#task-'+name+'-button')


def tabbable(page):
    return page.evaluate("""async()=>{const {installStudentKeyboard}=await import('./keyboard.js');
      // Main app owns actual keyboard input; use only its pure candidate list.
      // Expose a one-off independent document to avoid duplicate event handlers.
      return [...document.querySelectorAll('button,input,select,textarea,summary,a[href]')].filter(e=>e.getClientRects().length&&!e.closest('[hidden]')&&!e.disabled&&!e.closest('details:not([open])')).map(e=>e.id||e.textContent.slice(0,40));}""")


def native_panel_keys(student):
    from verify_student_repair import Target
    root=student.context.browser.new_browser_cdp_session()
    before={target['targetId'] for target in root.send('Target.getTargets')['targetInfos']}
    student.evaluate("""async()=>{const windowId=(await chrome.windows.getCurrent()).id;const b=document.createElement('button');b.id='native-test-open';b.textContent='검사 패널 열기';b.onclick=()=>chrome.sidePanel.open({windowId});document.body.append(b);}""")
    enter(student,'#native-test-open')
    deadline=time.monotonic()+12;target=None
    while time.monotonic()<deadline:
        target=next((target for target in root.send('Target.getTargets')['targetInfos'] if target['targetId'] not in before and target['url'].startswith(student.url.split('index.html')[0])),None)
        if target:break
        student.wait_for_timeout(40)
    assert target,'Native panel target missing'
    panel=Target(root,target['targetId'],student)
    def panel_key(key,code=None,modifiers=0):
        for kind in ('keyDown','keyUp'):panel.send('Input.dispatchKeyEvent',{'type':kind,'key':key,'code':code or key,'modifiers':modifiers,'windowsVirtualKeyCode':{'Tab':9,'Enter':13,'Escape':27}[key],**({'text':'\r','unmodifiedText':'\r'} if kind=='keyDown' and key=='Enter' else {})})
    panel.key=panel_key
    while not panel.evaluate("Boolean(document.querySelector('#workspace')&&!document.querySelector('#workspace').hidden)"):
        assert time.monotonic()<deadline,'Native panel startup timed out'
        student.wait_for_timeout(40)
    panel.evaluate("document.querySelector('#task-settings-button').click()")
    panel.evaluate("[...document.querySelectorAll('summary')].find(e=>e.textContent==='내 기기의 영상 연결·보관').focus()")
    panel.key('Tab');assert panel.evaluate('document.activeElement.id')=='video-volume',panel.evaluate("({active:document.activeElement.id,settingsHidden:document.querySelector('#task-settings').hidden,open:document.querySelector('#local-file').closest('details').open})")
    panel.key('Tab',modifiers=8);assert panel.evaluate("document.activeElement.textContent")=='내 기기의 영상 연결·보관'
    panel.key('Enter');panel.key('Tab');assert panel.evaluate('document.activeElement.id')=='local-file'
    panel.key('Escape');assert '해제' in panel.evaluate("document.querySelector('#status').textContent")
    panel.evaluate("(async()=>{if(chrome.sidePanel.close)await chrome.sidePanel.close({windowId:(await chrome.windows.getCurrent()).id});})()")
    root.detach();student.locator('#native-test-open').evaluate('(e)=>e.remove()')


def guardian_keyboard_flow(guardian):
    # Actual Tab traversal and native typing only: create → prepared sample → assign.
    def tab_to(selector):
        for _ in range(200):
            if guardian.locator(selector).evaluate('(e)=>e===document.activeElement'):return
            guardian.keyboard.press('Tab')
        raise AssertionError('Guardian keyboard target unreachable: '+selector)
    summary=guardian.locator('summary',has_text='학생 계정 만들기')
    if summary.evaluate('(e)=>e.parentElement.open'):summary.focus();guardian.keyboard.press('Enter')
    guardian.locator('#workspace-title').focus()
    tab_to('summary:has-text("학생 계정 만들기")');guardian.keyboard.press('Enter')
    tab_to('#student-form [name=name]');guardian.keyboard.insert_text('Keyboard 검증 학생')
    guardian.keyboard.press('Tab');guardian.keyboard.type('keyboard-notes')
    guardian.keyboard.press('Tab');guardian.keyboard.type('extension-pass-123')
    guardian.keyboard.press('Tab');guardian.keyboard.press('Enter')
    expect(guardian.locator('#student-choice option')).to_have_count(2)
    tab_to('#student-choice');guardian.keyboard.type('k')
    assert guardian.locator('#student-choice').evaluate("e=>e.selectedOptions[0].textContent")== 'Keyboard 검증 학생', guardian.locator('#student-choice').evaluate("e=>({selected:e.selectedOptions[0].textContent,options:[...e.options].map(o=>o.textContent)})")
    guardian.keyboard.press('Tab')
    guardian.keyboard.press('Tab');guardian.keyboard.press('Enter')
    expect(guardian.locator('#status')).to_contain_text('배정')


def exercise(guardian, student, output):
    guardian_keyboard_flow(guardian)
    student.evaluate(SPEECH)
    errors=[];requests=[]
    student.on('request',lambda req:requests.append({'url':req.url,'method':req.method,'content_type':req.headers.get('content-type',''),'body':req.post_data if req.method!='GET' and 'application/json' in req.headers.get('content-type','') else None}))
    student.on('pageerror',lambda error:errors.append(str(error)))
    # Move account reading preferences to Settings; external reader suppresses app TTS.
    task(student,'settings')
    student.locator('#access-mode').select_option('reader')
    summary=student.locator('summary',has_text='내 기기의 영상 연결·보관')
    summary.focus();student.keyboard.press('Tab');expect(student.locator('#video-volume')).to_be_focused()
    student.keyboard.press('Shift+Tab');expect(summary).to_be_focused()
    student.keyboard.press('Enter');student.keyboard.press('Tab');expect(student.locator('#local-file')).to_be_focused()
    # A nested disclosure remains excluded until both ancestors are open.
    student.evaluate("""()=>{const outer=document.querySelector('#local-file').closest('details');const nested=document.createElement('details');nested.id='test-nested';nested.innerHTML='<summary id="nested-summary">중첩 검사</summary><input id="nested-input" aria-label="중첩 입력">';outer.append(nested);}""")
    student.locator('#nested-summary').focus();student.keyboard.press('Tab');expect(student.locator('#video-volume')).to_be_focused()
    student.locator('#nested-summary').focus();student.keyboard.press('Enter');student.keyboard.press('Tab');expect(student.locator('#nested-input')).to_be_focused()
    student.keyboard.press('Shift+Tab');expect(student.locator('#nested-summary')).to_be_focused()
    summary.focus();student.keyboard.press('Enter');student.keyboard.press('Tab');expect(student.locator('#video-volume')).to_be_focused()
    summary.focus();student.keyboard.press('Shift');expect(student.locator('#disconnect')).to_be_focused()
    student.evaluate("document.querySelector('#test-nested').remove()")
    # A visible but unfocusable candidate cannot trap the loop.
    student.evaluate("document.querySelector('#video-volume').focus=()=>{}")
    summary.focus();student.keyboard.press('Tab');expect(student.locator('#video-muted')).to_be_focused()
    student.evaluate("delete document.querySelector('#video-volume').focus")
    student.keyboard.press('Escape');expect(student.locator('#status')).to_contain_text('해제')
    enter(student,'#panel-keyboard')
    # F6 goes to Chrome: only observe that the app does not cancel it.
    student.evaluate("document.addEventListener('keydown',e=>{if(e.key==='F6')window.__f6Prevented=e.defaultPrevented;})")
    student.keyboard.press('F6');assert student.evaluate('window.__f6Prevented') is False
    task(student,'listen')
    listen_controls=tabbable(student)
    assert 'notes-query' not in listen_controls and 'search-form' not in listen_controls and 'local-file' not in listen_controls
    check_layout(student,'notes-listening',output)
    # From the listening heading, reverse Tab reaches the persistent task controls
    # without traversing sentence/source/result controls.
    student.locator('#player-title').focus()
    path=[]
    for _ in range(15):
        student.keyboard.press('Shift+Tab');path.append(student.evaluate('document.activeElement.id'))
        if path[-1]=='task-notes-button':break
    assert path[-1]=='task-notes-button' and 'sentence-selection' not in path
    student.keyboard.press('Enter');assert student.locator('#task-notes').evaluate('(e)=>e.contains(document.activeElement)')
    # Select an explicit safe sentence in Find; source is readable text, not buttons.
    task(student,'find')
    assert student.locator('#material button').count()==0
    sentence=student.locator('#sentence-selection').input_value()
    source_text=student.locator('#selected-source').inner_text()
    enter(student,'#selected-underline');expect(student.locator('#selected-underline')).to_have_attribute('aria-pressed','true')
    enter(student,'#selected-note');expect(student.locator('#note-body')).to_be_focused()
    student.locator('#note-body').fill('첫 번째 생각\n나의 풀이를 남깁니다.')
    student.keyboard.press('End');student.keyboard.press('Space');student.keyboard.type('abc')
    expect(student.locator('#note-body')).to_have_value('첫 번째 생각\n나의 풀이를 남깁니다. abc')
    student.keyboard.press('ArrowLeft');student.keyboard.press('Shift');expect(student.locator('#note-body')).to_be_focused()
    # Real browser composition event path plus Korean text insertion. This is not
    # a native OS Korean IME evaluation.
    student.locator('#note-body').dispatch_event('compositionstart')
    student.keyboard.insert_text('한글')
    student.locator('#note-body').dispatch_event('compositionend')
    student.wait_for_timeout(1300)
    expect(student.locator('#note-save-status')).to_have_text('필기를 저장했습니다.')
    expect(student.locator('#note-body')).to_be_focused()
    student.keyboard.press('ControlOrMeta+z');student.keyboard.press('ControlOrMeta+Shift+z')
    # Freeze cursor independently of clicking source confirmation.
    student.locator('#note-body').evaluate('(e)=>e.setSelectionRange(3,5)')
    student.locator('#note-body').dispatch_event('select')
    cursor=student.locator('#note-body').evaluate('(e)=>[e.selectionStart,e.selectionEnd]')
    enter(student,'#show-note-source');expect(student.locator('#note-source-dialog')).to_be_visible()
    expect(student.locator('#note-source-text')).to_contain_text(source_text)
    student.keyboard.press('Tab');expect(student.locator('#close-note-source')).to_be_focused()
    student.keyboard.press('Shift+Tab');expect(student.locator('#close-note-source')).to_be_focused()
    student.keyboard.press('Enter');expect(student.locator('#note-body')).to_be_focused()
    assert student.locator('#note-body').evaluate('(e)=>[e.selectionStart,e.selectionEnd]')==cursor
    check_layout(student,'notes-editor',output,skip=False)
    saved=student.locator('#note-body').input_value()
    # Separate free note; word search and explicit selection preserve existing note.
    enter(student,'#new-note');student.locator('#note-body').fill('두 번째 자유 필기 검색용 단어')
    enter(student,'#save-note');expect(student.locator('#note-save-status')).to_have_text('필기를 저장했습니다.')
    # Switching away before debounce still saves; failure is globally announced.
    student.locator('#note-body').fill('두 번째 자유 필기 검색용 단어 · 작업 전환')
    task(student,'listen');student.wait_for_timeout(1300)
    task(student,'notes');expect(student.locator('#note-save-status')).to_have_text('필기를 저장했습니다.')
    student.locator('#notes-query').fill('첫 번째');expect(student.locator('#notes-list option')).to_have_count(1)
    enter(student,'#open-note');expect(student.locator('#note-body')).to_have_value(saved)
    # Failure preserves the editor, local draft, cursor and undo. Reload restores it.
    student.route('**/notes/*',lambda route:route.abort() if route.request.method=='PUT' else route.continue_())
    student.locator('#note-body').fill(saved+'\n오프라인 초안')
    task(student,'listen');student.wait_for_timeout(1500)
    expect(student.locator('#error')).to_contain_text('필기 저장 실패')
    expect(student.locator('#player-title')).to_be_focused()
    task(student,'notes');expect(student.locator('#note-save-status')).to_contain_text('저장 실패')
    expect(student.locator('#note-body')).to_be_focused()
    drafts=student.evaluate("async()=>Object.entries(await chrome.storage.local.get(null)).filter(([key])=>key.startsWith('note-draft:')).map(([,value])=>value)")
    assert any('오프라인 초안' in draft['body'] for draft in drafts)
    assert all(not any(key in (draft.get('source') or {}) for key in ('text','public_description','source_text')) for draft in drafts)
    student.reload();expect(student.locator('#workspace')).to_be_visible()
    student.locator('#lectures button').click();expect(student.locator('#lesson')).to_be_visible();task(student,'notes')
    expect(student.locator('#note-body')).to_have_value(saved+'\n오프라인 초안')
    student.unroute('**/notes/*');enter(student,'#save-note');expect(student.locator('#note-save-status')).to_have_text('필기를 저장했습니다.')
    # Task return restores editing cursor and listening position, never autoplays.
    student.locator('#note-body').focus();student.locator('#note-body').evaluate('(e)=>e.setSelectionRange(2,2)');student.locator('#note-body').dispatch_event('select')
    task(student,'listen');expect(student.locator('#task-notes')).to_be_hidden()
    task(student,'notes');expect(student.locator('#note-body')).to_be_focused()
    assert student.locator('#note-body').evaluate('(e)=>e.selectionStart')==2
    assert student.locator('#position').input_value()=='42'
    # Existing memo remains after explicit copying. Underlines and bookmarks survive.
    enter(student,'#import-legacy-note');expect(student.locator('#note-body')).to_have_value('확장 분리 검증 메모')
    expect(student.locator('#note')).to_have_value('확장 분리 검증 메모')
    enter(student,'#bookmark');assert student.locator('#bookmarks li').count()>=1
    assert student.locator('#bookmarks button').count()==0
    with student.expect_download() as download:enter(student,'#export-my-notes')
    text=Path(download.value.path()).read_text();assert saved in text and '연결 원문 (읽기 전용)' in text
    # Revoke an already-selected source after the view loaded; recheck every
    # source lookup/export. Student-authored text remains private and intact.
    from app import local_access
    # Read the active assigned lecture id from the student's own visible list.
    ident=student.locator('#lectures button').first.get_attribute('data-lecture')
    student.locator('#notes-query').fill('첫 번째');enter(student,'#open-note')
    with local_access.db() as con:assert con.execute('UPDATE lectures SET ready=0 WHERE id=?',(ident,)).rowcount==1
    try:
        enter(student,'#show-note-source');expect(student.locator('#note-source-load-status')).to_contain_text('현재')
        assert student.locator('#note-source-text').inner_text()==''
        student.keyboard.press('Escape');expect(student.locator('#note-body')).to_be_focused()
        with student.expect_download() as revoked_download:enter(student,'#export-my-notes')
        revoked_text=Path(revoked_download.value.path()).read_text()
        assert source_text not in revoked_text and saved in revoked_text
        task(student,'find');enter(student,'#export-notes');expect(student.locator('#error')).to_contain_text('배정된 준비 완료')
    finally:
        with local_access.db() as con:con.execute('UPDATE lectures SET ready=1 WHERE id=?',(ident,))
    # Simulate a second authenticated view changing the same note. The old
    # editor must keep its words, and copy recovery must preserve both records.
    task(student,'notes');student.locator('#notes-query').fill('두 번째');enter(student,'#open-note')
    student.evaluate('''async()=>{const {request}=await import('./client.js');const id=document.querySelector('#lectures button').dataset.lecture;const notes=await request('/extension/v1/student/lectures/'+id+'/notes');const entry=notes.find(n=>n.body.includes('두 번째'));await request('/extension/v1/student/lectures/'+id+'/notes/'+entry.id,{method:'PUT',body:{body:'다른 화면에서 보존한 개인 풀이',source:entry.source,started_ms:entry.started_ms,revision:entry.revision}});}''')
    student.locator('#note-body').fill('충돌해도 보존할 내 초안')
    student.wait_for_timeout(1300);expect(student.locator('#copy-note-draft')).to_be_visible()
    enter(student,'#copy-note-draft');expect(student.locator('#note-body')).to_have_value('충돌해도 보존할 내 초안')
    enter(student,'#save-note');expect(student.locator('#note-save-status')).to_have_text('필기를 저장했습니다.')
    with student.expect_download() as recovered_download:enter(student,'#export-my-notes')
    recovered_text=Path(recovered_download.value.path()).read_text();assert '다른 화면에서 보존한 개인 풀이' in recovered_text and '충돌해도 보존할 내 초안' in recovered_text
    # Removed commands do not hit chat provider/fallback generators.
    before=len([r for r in requests if '/agent-turn' in r['url']])
    enter(student,'#type-command');student.locator('#text-command').fill('1분 발표문 만들어줘');student.keyboard.press('Enter')
    expect(student.locator('#status')).to_contain_text('제공하지 않습니다')
    assert len([r for r in requests if '/agent-turn' in r['url']])==before
    task(student,'find');student.locator('#chat-input').fill('암기표 만들어줘');enter(student,'#chat-form button')
    expect(student.locator('#status')).to_contain_text('제공하지 않습니다')
    assert len([r for r in requests if '/agent-turn' in r['url']])==before
    for control_id in ('learning-tool','run-tool','read-study','command-input'):assert student.locator('#'+control_id).count()==0
    # A silent app is only correct if the reader result remains exposed while
    # Find is active; its live output must not live inside hidden Listen.
    student.evaluate('window.__spoken=[]');enter(student,'#read')
    expect(student.locator('#reader-description')).to_be_visible()
    selected=student.locator('#selected-source').inner_text()
    enter(student,'#selected-read')
    expect(student.locator('#reader-description')).to_contain_text(selected)
    assert selected in student.locator('#reader-description').aria_snapshot()
    expect(student.locator('#selected-read')).to_be_focused()
    enter(student,'#selected-paragraph-read')
    expect(student.locator('#reader-description')).to_contain_text(selected)
    expect(student.locator('#reader-description')).to_have_count(1)
    task(student,'notes');expect(student.locator('#reader-description')).to_be_visible()
    assert student.evaluate('window.__spoken.length')==0
    task(student,'find')
    # Public self-authored video: browser file stays local; Space contract is intact.
    task(student,'settings');summary.focus();student.keyboard.press('Enter')
    student.locator('#local-file').set_input_files(str(Path(__file__).resolve().parents[1]/'samples/accessibility-demo.mp4'))
    enter(student,'#connect-file');expect(student.locator('#connection')).to_contain_text('수동 재생')
    task(student,'listen');student.locator('#play').focus()
    student.keyboard.press('Space',delay=35);student.wait_for_function("()=>!document.querySelector('#local-video').paused")
    task(student,'notes');student.locator('#notes-query').fill('첫 번째');enter(student,'#open-note')
    student.wait_for_function("()=>document.querySelector('#local-video').paused")
    enter(student,'#show-note-source');expect(student.locator('#note-source-dialog')).to_be_visible();student.keyboard.press('Escape')
    assert student.evaluate("document.querySelector('#local-video').paused")
    enter(student,'#save-note');assert student.evaluate("document.querySelector('#local-video').paused")
    task(student,'listen');student.locator('#play').focus();student.keyboard.press('Space',delay=35)
    try:student.wait_for_function("()=>!document.querySelector('#local-video').paused",timeout=5000)
    except Exception:
        print('PLAYBACK DIAGNOSTIC',student.evaluate("()=>({focus:document.activeElement.id,error:document.querySelector('#error').textContent,status:document.querySelector('#status').textContent,connection:document.querySelector('#connection').textContent,paused:document.querySelector('#local-video').paused,position:document.querySelector('#local-video').currentTime,duration:document.querySelector('#local-video').duration,keys:document.querySelector('#space-enabled').checked})"),flush=True)
        raise

    student.keyboard.press('Space',delay=35);student.keyboard.press('Space',delay=35);student.wait_for_function("()=>document.querySelector('#local-video').paused")
    student.keyboard.press('Space',delay=35);student.keyboard.press('Space',delay=35);student.keyboard.press('Space',delay=35)
    expect(student.locator('#text-dialog')).to_be_visible();student.keyboard.press('Escape')
    expect(student.locator('#text-dialog')).to_be_hidden()
    student.locator('#play').focus();student.keyboard.down('Space');expect(student.locator('#voice-permission-dialog')).to_be_visible(timeout=4000);student.keyboard.up('Space');student.keyboard.press('Escape')
    expect(student.locator('#play')).to_be_focused()
    uploads=[request for request in requests if request['method'] in ('POST','PUT') and ('application/json' not in request['content_type'])]
    assert not uploads,uploads
    # Cleanup only test-created local connection; preserve baseline memo/location.
    task(student,'settings');enter(student,'#disconnect');student.locator('#position').fill('42');enter(student,'#save-position')
    task(student,'find');check_layout(student,'notes-find',output)
    task(student,'settings');check_layout(student,'notes-settings',output)
    task(student,'notes');check_layout(student,'notes-final',output)
    native_panel_keys(student)
    # A withdrawn lecture's personal notebook remains reachable after reload,
    # without re-exposing its source or another lecture's legacy records.
    with local_access.db() as con:assert con.execute('UPDATE lectures SET ready=0 WHERE id=?',(ident,)).rowcount==1
    try:
        student.reload();expect(student.locator('#workspace')).to_be_visible();expect(student.locator('#lectures button')).to_have_count(0)
        expect(student.locator('#reader-description')).to_be_empty()
        task(student,'settings');enter(student,'#refresh-notebooks');expect(student.locator('#notebook-lecture option')).to_have_count(1)
        enter(student,'#open-notebook');expect(student.locator('#notes-title')).to_be_visible()
        student.locator('#notes-query').fill('충돌해도');expect(student.locator('#notes-list option')).to_have_count(1);enter(student,'#open-note')
        expect(student.locator('#note-body')).to_have_value('충돌해도 보존할 내 초안')
        expect(student.locator('#legacy-records')).to_be_hidden();expect(student.locator('#new-note')).to_be_disabled()
        student.locator('#note-body').fill('충돌해도 보존할 내 초안 · 배정 종료 뒤 수정')
        enter(student,'#save-note');expect(student.locator('#note-save-status')).to_have_text('필기를 저장했습니다.')
        with student.expect_download() as archive_download:enter(student,'#export-my-notes')
        assert '배정 종료 뒤 수정' in Path(archive_download.value.path()).read_text()
        check_layout(student,'notes-archive',output,skip=False)
    finally:
        with local_access.db() as con:con.execute('UPDATE lectures SET ready=1 WHERE id=?',(ident,))
    assert not errors,errors
    (output/'student-notes-paths.json').write_text(json.dumps({'listening_controls':listen_controls,'listen_heading_to_notes_reverse_tabs':path,'source_id':sentence,'requests_raw_media':0,'checks':'actual Chromium keyboard; synthetic speech/composition boundary; temporary accounts'},ensure_ascii=False,indent=2))
    return guardian


exercise.checks=['closed/nested details real Tab/Shift+Tab, failed focus fallback','task isolation and cursor return','multiple private notes, explicit safe source','auto-save and offline draft reload/retry','search/edit/legacy memo copy/export','removed command rejection before provider','reader mode suppresses app TTS','local public video no upload, Space/Shift gestures','actual native Chrome side-panel closed-details keys','guardian create/sample/assign with Tab/type-ahead/Enter only','hidden-task save failure and conflict-copy recovery','withdrawn notebook reopen/edit/export after reload','saved-note/source close/save never resumes decoded video']

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'docs/verification/2026-11-16-student-notes')
    args=parser.parse_args()
    main(exercise,'student-notes',args.output)
