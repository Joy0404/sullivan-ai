"""Isolated audit probes; no product or existing test changes.

Uses the phase-3 hook with temporary accounts/profile and a real decoded video.
Only permissions completion and one worker reply delivery are delayed explicitly.
"""
import json
import sys
import traceback
from base64 import b64encode
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from playwright.sync_api import expect
from starlette.responses import HTMLResponse
from starlette.routing import Route
from verify_extensions_browser import main
from verify_extensions_phase3 import exercise as phase3

OUT = Path(__file__).resolve().parent
RESULT = {'scope': 'installed 0.4.2 extensions, temporary DB/profile, phase3 student_check hook',
          'boundaries': 'real decoded video and real API/extension worker; permission promise and one reply delivery explicitly delayed',
          'cases': [], 'page_errors': []}


class AuditComplete(BaseException):
    pass


def inspect(page):
    return page.evaluate("""async()=>{const{request}=await import('./client.js');
      const{playbackLease}=await chrome.storage.session.get('playbackLease');
      return {title:document.querySelector('#lesson-title').textContent,
        connection:document.querySelector('#connection').textContent,
        position:document.querySelector('#position').value,
        status:document.querySelector('#status').textContent,
        error:document.querySelector('#error').textContent,
        focus:document.activeElement.id||document.activeElement.tagName,
        lease:playbackLease,lectures:await request('/local/lectures')};}""")


def lesson(page, ident):
    return page.evaluate("""async(id)=>{const{request}=await import('./client.js');
      return await request('/extension/v1/student/lectures/'+id);}""", ident)


def open_lesson(page, ident, title):
    page.locator(f'#lectures button[data-lecture="{ident}"]').click()
    expect(page.locator('#lesson-title')).to_have_text(title)
    expect(page.locator('#lesson')).to_be_visible()


def hook(guardian, student, output):
    from app import local_access, main as api
    student.on('pageerror', lambda error: RESULT['page_errors'].append(str(error)))
    student.locator('#access-mode').select_option('silent')
    initial = inspect(student)
    old = next(x for x in initial['lectures'] if x['title'] == '동기화 테스트 강의')
    new = next(x for x in initial['lectures'] if x['id'] != old['id'])
    RESULT['lesson_ids'] = {'old': old['id'], 'new': new['id']}

    # Reuse the actual MP4 that phase3 already fingerprint-verified and decoded.
    video = bytes(student.evaluate("""async()=>Array.from(new Uint8Array(await
      (await fetch(document.querySelector('#local-video').src)).arrayBuffer()))"""))
    origin = student.evaluate("async()=> (await import('./config.js')).SERVER")
    source = origin + '/audit-keyboard-native-player'
    html = f'<html lang="ko"><title>Audit native source</title><video muted src="data:video/mp4;base64,{b64encode(video).decode()}"></video></html>'
    route = Route('/audit-keyboard-native-player', lambda request: HTMLResponse(html))
    api.app.router.routes.insert(0, route)
    with local_access.db() as con:
        con.execute('UPDATE lectures SET playback=? WHERE id=?',
                    (json.dumps({'kind': 'direct', 'normalized_url': source}), old['id']))
    try:
        case = {'name': 'permission_completion_after_lesson_switch', 'old_source': source}
        try:
            open_lesson(student, old['id'], old['title'])
            student.evaluate("""()=>{window.__originalPermission=chrome.permissions.request;
              chrome.permissions.request=(args)=>{window.__permissionArgs=args;
                return new Promise(resolve=>window.__releasePermission=resolve);};}""")
            student.locator('#open-original').click()
            student.wait_for_function('()=>typeof window.__releasePermission==="function"')
            open_lesson(student, new['id'], new['title'])
            case['before_release'] = inspect(student)
            case['new_lesson_playback'] = lesson(student, new['id'])['playback']
            student.evaluate('window.__releasePermission(true)')
            expect(student.locator('#connection')).to_contain_text('원본 강의 탭을 연결', timeout=15000)
            case['after_release'] = inspect(student)
            case['reproduced'] = (case['after_release']['title'] == new['title'] and
                                  case['after_release']['lease']['url'] == source)
            case['release_impact'] = 'block release: old source is attached under a different lesson and marked connected/verified' if case['reproduced'] else 'not reproduced'
            student.screenshot(path=str(OUT / 'permission-after-switch.png'), full_page=True)
        except Exception:
            case['probe_error'] = traceback.format_exc()
        finally:
            student.evaluate('() => {if(window.__originalPermission)chrome.permissions.request=window.__originalPermission;}')
            RESULT['cases'].append(case)
            (OUT / 'results.json').write_text(json.dumps(RESULT, ensure_ascii=False, indent=2)+'\n')

        # Start the second case from a fresh document and its stored original.
        for page in list(student.context.pages):
            if page.url == source:
                page.close()
        student.reload()
        expect(student.locator('#workspace')).to_be_visible()
        student.locator('#access-mode').select_option('silent')
        open_lesson(student, old['id'], old['title'])
        student.get_by_text('내 기기의 영상 연결·보관', exact=True).click()
        student.locator('#load-original').click()
        expect(student.locator('#connection')).to_contain_text('분석한 원본과 일치')
        case = {'name': 'seek_reply_after_lesson_switch'}
        try:
            case['new_progress_before'] = lesson(student, new['id'])['progress']
            writes = []
            def record(request):
                if request.method == 'PUT' and '/progress' in request.url:
                    writes.append({'url': request.url, 'body': request.post_data_json})
            student.on('request', record)
            student.evaluate("""async()=>{const{StudentMedia}=await import('./media.js');
              window.__originalSend=StudentMedia.prototype.send;window.__delaySeek=true;
              StudentMedia.prototype.send=async function(action,...rest){
                const result=await window.__originalSend.call(this,action,...rest);
                if(action==='seek'&&window.__delaySeek){window.__delaySeek=false;
                  await new Promise(resolve=>window.__releaseSeek=resolve);}
                return result;
              };
              const{command}=await import('./app.js');
              window.__seekPending=command('10초 앞으로').then(()=>window.__seekDone=true).catch(error=>window.__seekError=error.message);
            }""")
            student.wait_for_function('()=>typeof window.__releaseSeek==="function"')
            open_lesson(student, new['id'], new['title'])
            case['before_release'] = inspect(student)
            student.evaluate('window.__releaseSeek()')
            student.wait_for_function('()=>window.__seekDone===true||Boolean(window.__seekError)')
            case['after_release'] = inspect(student)
            case['new_progress_after'] = lesson(student, new['id'])['progress']
            case['writes'] = writes
            case['reproduced'] = (case['new_progress_before']['position_ms'] != case['new_progress_after']['position_ms'])
            case['release_impact'] = 'block release: old seek writes the newly selected lesson position/progress' if case['reproduced'] else 'not reproduced'
            student.screenshot(path=str(OUT / 'seek-after-switch.png'), full_page=True)
        except Exception:
            case['probe_error'] = traceback.format_exc()
        finally:
            student.evaluate("""async()=>{if(window.__originalSend){const{StudentMedia}=await import('./media.js');StudentMedia.prototype.send=window.__originalSend;}}""")
            RESULT['cases'].append(case)
    finally:
        api.app.router.routes.remove(route)
        (OUT / 'results.json').write_text(json.dumps(RESULT, ensure_ascii=False, indent=2)+'\n')
    raise AuditComplete()


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    phase3.student_check = hook
    try:
        main(phase3, phase='full-reaudit-keyboard', output=OUT)
    except AuditComplete:
        print(json.dumps(RESULT, ensure_ascii=False, indent=2))
