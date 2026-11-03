"""Dev-only AX-tree/keyboard and optional axe probe, without reading field values."""
import json,os
from pathlib import Path

observations=[]

def probe(page,screen):
    if screen != 'guardian-loading':
        page.wait_for_function("document.querySelector('#guardian-dashboard')?.getAttribute('aria-busy')!=='true'")
    cdp=page.context.new_cdp_session(page)
    cdp.send('Accessibility.enable')
    original=page.evaluate_handle('document.activeElement')
    # Start at the document's first available control and traverse actual Tab order.
    selector='button:not([disabled]),input:not([disabled]):not([type=hidden]),select:not([disabled]),textarea:not([disabled]),a[href],summary,[tabindex="0"]'
    candidates=page.locator(selector)
    first=None
    for i in range(candidates.count()):
        candidate=candidates.nth(i)
        if candidate.is_visible() and candidate.is_enabled() and not candidate.evaluate('n=>!!n.closest("[inert]")'):
            first=candidate;break
    seen=[];keys=set();forward=[]
    if first:
        first.focus()
        for _ in range(min(candidates.count()+5,180)):
            active=page.evaluate('({tag:document.activeElement.tagName,id:document.activeElement.id,type:document.activeElement.getAttribute("type")})')
            if active['tag'] in ('BODY','HTML'):break
            remote=cdp.send('Runtime.evaluate',{'expression':'document.activeElement','objectGroup':'focus-audit'})['result']
            obj=remote.get('objectId')
            tree=cdp.send('Accessibility.getPartialAXTree',{'objectId':obj,'fetchRelatives':False})['nodes'] if obj else []
            exposed=next((n for n in tree if not n.get('ignored')),None)
            assert exposed,f'{screen}: focused control is ignored by AX: {active}'
            name=exposed.get('name',{}).get('value','')
            role=exposed.get('role',{}).get('value','')
            assert name.strip(),f'{screen}: empty accessible name on focused {active}'
            key=exposed.get('backendDOMNodeId')
            if key in keys:break
            keys.add(key)
            forward.append(key)
            seen.append({'id':active['id'],'role':role,'name':name,'states':{p['name']:p.get('value',{}).get('value') for p in exposed.get('properties',[]) if p['name'] in ('focused','pressed','checked','expanded','disabled','current')}})
            page.keyboard.press('Tab')
        # Starting at the boundary (body or the first repeated control), reverse
        # traversal must reproduce the same sequence without a custom key trap.
        reverse=[];reverse_keys=set()
        for _ in range(min(candidates.count()+5,180)):
            page.keyboard.press('Shift+Tab')
            if page.evaluate("['BODY','HTML'].includes(document.activeElement.tagName)"):break
            remote=cdp.send('Runtime.evaluate',{'expression':'document.activeElement','objectGroup':'focus-audit'})['result']
            obj=remote.get('objectId')
            tree=cdp.send('Accessibility.getPartialAXTree',{'objectId':obj,'fetchRelatives':False})['nodes'] if obj else []
            exposed=next((n for n in tree if not n.get('ignored')),None)
            assert exposed,f'{screen}: reverse focus ignored by AX'
            key=exposed.get('backendDOMNodeId')
            if key in reverse_keys:break
            reverse_keys.add(key);reverse.append(key)
        assert reverse==list(reversed(forward)),f'{screen}: forward/backward focus order differs'
    if original.as_element() and original.as_element().is_visible():original.evaluate('n=>n.focus()')
    original.dispose()
    cdp.send('Runtime.releaseObjectGroup',{'objectGroup':'focus-audit'});cdp.detach()
    axe_path=os.getenv('SULLIVAN_AXE_SOURCE')
    violations=[]
    if axe_path:
        page.add_script_tag(path=axe_path)
        result=page.evaluate('''async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}})''')
        violations=[{'id':v['id'],'impact':v['impact'],'description':v['description'],'nodes':[{'target':n['target'],'summary':n.get('failureSummary','')} for n in v['nodes']]} for v in result['violations']]
    observations.append({'screen':screen,'browser':page.context.browser.version,'axe_version':page.evaluate('window.axe?.version') if axe_path else None,'keyboard_ax_controls':seen,'reverse_tab_coverage':True,'axe_violations':violations})
    save(Path(__file__).resolve().parents[1])
    if violations:print(json.dumps(violations,ensure_ascii=False),flush=True)
    if axe_path:assert not violations,f'{screen}: accessibility violations remain; see focus-accessibility-results.json'
    print(f'AX audit {screen}: {len(seen)} named focused controls; axe findings {len(violations)}',flush=True)

def save(root):
    out=Path(root)/'docs/verification/focus-accessibility-results.json'
    out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps({'scope':'Browser AX tree + keyboard + optional axe; no actual screen-reader audio','screens':observations},ensure_ascii=False,indent=2))
