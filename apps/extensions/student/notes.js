// Private authoring only. Source labels/text are fetched afresh and never cached
// in drafts; a draft contains the student's words and an opaque reference.
import {request} from './client.js';
import {$, node, task, status} from './ui.js';

export function createNotebook({context, position, pause, reportError}) {
  let scope=null, epoch=0, rows=[], drafts=[], active=null, timer, saving=null, composing=false;
  let sources=[], cursor=null, sourceTicket=0, sourceReturn=null, countTimer, editorTicket=0;
  const endpoint=()=>`/extension/v1/student/lectures/${scope.lecture}`;
  const valid=ticket=>scope&&ticket===epoch&&context()?.account===scope.account&&context()?.lecture===scope.lecture;
  const prefix=()=>`note-draft:${scope.account}:${scope.lecture}:`;
  const key=(entry,selected=scope)=>`note-draft:${selected.account}:${selected.lecture}:${entry.draftId}`;
  function requireCurrent(ticket,editor){
    if(!valid(ticket)||(editor!==undefined&&editor!==editorTicket))throw Object.assign(new Error('이전 필기 작업을 취소했습니다.'),{cancelled:true});
  }
  const title=entry=>entry.body.trim().split(/\n/)[0].slice(0,90)||'빈 필기';
  function state(text){if($('note-save-status').textContent!==text)$('note-save-status').textContent=text;}
  function capture(){if(active){active.body=$('note-body').value;active.cursor=[$('note-body').selectionStart,$('note-body').selectionEnd,$('note-body').selectionDirection];cursor=active.cursor;}}
  async function persist(entry=active,selected=scope){
    if(!entry||!selected)return;
    const storageKey=`note-draft:${selected.account}:${selected.lecture}:${entry.draftId}`;
    const copy=structuredClone(entry);
    await chrome.storage.local.set({[storageKey]:copy});
  }
  function updateList(){
    const selected=$('notes-list').value,query=$('notes-query').value.toLocaleLowerCase();
    const entries=[...drafts,...rows.filter(row=>!drafts.some(draft=>draft.id===row.id))];
    const filtered=entries.filter(entry=>entry.body.toLocaleLowerCase().includes(query));
    $('notes-list').replaceChildren(...filtered.map(entry=>node('option',`${entry.draftId?'초안 · ':''}${title(entry)}`,{value:entry.draftId||entry.id})));
    $('notes-list').value=filtered.some(entry=>(entry.draftId||entry.id)===selected)?selected:(filtered[0]?.draftId||filtered[0]?.id||'');
    clearTimeout(countTimer);
    countTimer=setTimeout(()=>{const text=`필기 ${filtered.length}개. 검색은 학생 작성 내용에서만 찾습니다.`;if($('notes-count').textContent!==text)$('notes-count').textContent=text;},350);
    $('open-note').disabled=!filtered.length;
  }
  function paint(){
    $('note-editor').hidden=!active;
    if(!active)return;
    $('note-body').value=active.body;cursor=active.cursor||[active.body.length,active.body.length,'none'];
    $('note-start').textContent=`필기 시작 시점: ${Math.floor(active.started_ms/1000)}초. ${active.source?'학생이 선택한 원문에 연결됨':'자유 필기 · 연결 원문 없음'}`;
    $('copy-note-draft').hidden=true;$('note-delete-confirm').hidden=true;
    state(active.dirty?'이 기기에 보존된 초안입니다. 저장·재시도할 수 있습니다.':'저장된 필기입니다.');
    restoreCursor();
  }
  function restoreCursor(){
    if(!active||!$('task-notes').hidden){
      if(active){$('note-body').focus();if(cursor)$('note-body').setSelectionRange(...cursor);}
    }
  }
  function changed(){
    if(!active)return;editorTicket++;capture();const wasDirty=active.dirty;active.dirty=true;
    if(!wasDirty)state('저장 대기 중입니다. 이 기기에 초안을 보존합니다.');
    if(!drafts.includes(active))drafts.unshift(active);
    persist().catch(error=>state(`기기 초안 보존 실패: ${error.message}. 화면을 유지하고 지금 저장을 누르세요.`));
    clearTimeout(timer);if(!composing)timer=setTimeout(()=>save().catch(reportError),900);
    // Do not announce every keystroke, rebuild the editor or alter its undo stack.
  }
  async function save(explicit=false){
    if(!active||!scope)return;
    const ticket=epoch;
    if(!valid(ticket))return;
    capture();if(composing)return;
    if(saving){await saving;if(!valid(ticket))return;if(active?.dirty)return save(explicit);return;}
    const entry=active,selected=scope,path=endpoint(),data={body:entry.body,started_ms:entry.started_ms,source:entry.source,revision:entry.revision};
    clearTimeout(timer);
    // The durable local draft is written before the network request starts.
    let localSaved=true;
    try{await persist(entry,selected);}catch{localSaved=false;state('기기에 초안을 보존하지 못했습니다. 서버 저장을 시도합니다. 화면을 유지하세요.');}
    if(!valid(ticket))return;
    const work=(async()=>{
      try{
        const result=await request(`${path}/notes/${entry.id}`,{method:'PUT',body:data});
        if(!valid(ticket))return;
        rows=[result,...rows.filter(row=>row.id!==result.id)];
        entry.revision=result.revision;
        entry.dirty=entry.body!==data.body;
        if(entry.dirty)await persist(entry,selected);
        else{await chrome.storage.local.remove(key(entry,selected));if(!valid(ticket))return;drafts=drafts.filter(draft=>draft!==entry);}
        if(!valid(ticket))return;
        if(entry===active){state(entry.dirty?'새로 입력한 내용은 저장 대기 중입니다.':'필기를 저장했습니다.');$('copy-note-draft').hidden=true;}
        if(entry.failed&&$('task-notes').hidden)status('필기 저장 연결이 복구되었습니다.');
        entry.failed=false;
        // Only update the list after a save, and never move editing focus.
        updateList();
      }catch(error){
        if(!valid(ticket)||error.cancelled)return;
        entry.dirty=true;await persist(entry,selected).catch(()=>{localSaved=false;});
        if(!valid(ticket))return;
        if(!entry.failed&&$('task-notes').hidden)status(`필기 저장 실패. ${localSaved?'초안은 이 기기에 보존됩니다.':'기기 보존도 실패했습니다. 화면을 유지하세요.'} 필기에서 지금 저장·재시도를 누르세요.`,true);
        entry.failed=true;
        if(entry===active){
          state(`저장 실패. ${localSaved?'초안을 이 기기에 유지합니다.':'기기 보존도 실패했습니다. 이 화면을 유지하세요.'} ${error.message} 지금 저장·재시도로 다시 시도하세요.`);
          $('copy-note-draft').hidden=error.status!==409;
        }
        error.reported=true;if(explicit)throw error;
      }
    })();
    saving=work;try{await work;}finally{if(saving===work)saving=null;}
  }
  // Switching tasks preserves the debounce; it must not silently cancel saving.
  async function flush(){capture();if(active?.dirty)await persist();}
  async function edit(entry){
    const ticket=epoch,editor=++editorTicket;
    await flush();requireCurrent(ticket,editor);if(active?.dirty)save().catch(reportError);
    await pause();requireCurrent(ticket,editor);
    active=entry.draftId?entry:{...entry,draftId:crypto.randomUUID(),dirty:false};
    paint();
  }
  async function start(source=null,body='',startedMs=position(),savePrevious=true){
    if(!scope)throw new Error('강의를 먼저 선택하세요.');
    const ticket=epoch,selected=scope,editor=++editorTicket;
    await flush();requireCurrent(ticket,editor);if(savePrevious&&active?.dirty)save().catch(reportError);
    await pause();requireCurrent(ticket,editor);
    const entry={id:crypto.randomUUID(),draftId:crypto.randomUUID(),body,started_ms:Math.max(0,Math.min(86400000,Math.round(startedMs))),source,revision:0,dirty:true,cursor:[body.length,body.length,'none']};
    // Preserve only under the initiating account, then recheck before publishing
    // the editor or allowing callers (legacy/conflict copy) to continue saving.
    await persist(entry,selected);requireCurrent(ticket,editor);
    active=entry;drafts.unshift(entry);updateList();paint();
    clearTimeout(timer);timer=setTimeout(()=>{if(valid(ticket)&&active===entry)save().catch(reportError);},900);
  }
  async function load(){
    await flush();const selected=context();if(!selected)return;
    const ticket=++epoch;editorTicket++;clearTimeout(timer);scope=selected;active=null;rows=[];drafts=[];sources=[];saving=null;
    $('notes-title').textContent=`내 필기 · ${selected.title||'선택한 강의'}`;
    for(const id of ['new-note','new-linked-note','note-source-selection','import-legacy-note'])$(id).disabled=selected.allowNew===false;
    $('legacy-records').hidden=selected.allowNew===false;
    $('note-editor').hidden=true;$('notes-query').value='';$('note-source-preview').textContent='';
    $('note-source-selection').replaceChildren(node('option','원문 없이 필기',{value:''}));
    const all=await chrome.storage.local.get(null);if(!valid(ticket))return;
    drafts=Object.entries(all).filter(([name])=>name.startsWith(prefix())).map(([,value])=>value);
    updateList();
    try{
      const result=await request(`${endpoint()}/notes`);if(!valid(ticket))return;
      rows=result;updateList();
      if(drafts.length&&!active){active=drafts[0];$('note-editor').hidden=false; // Restore without replacing a newly started editor.
        $('note-body').value=active.body;cursor=active.cursor||[0,0,'none'];
        $('note-start').textContent=`${Math.floor(active.started_ms/1000)}초에 시작한 초안`;
        state('이 기기에 미저장 초안이 있습니다. 수정하거나 지금 저장·재시도하세요.');}
    }catch(error){if(valid(ticket)){state('필기 목록을 불러오지 못했습니다. 이 기기의 초안은 유지됩니다.');reportError(error);}}
    try{
      const result=await request(`${endpoint()}/note-sources`);if(!valid(ticket))return;
      sources=result;
      $('note-source-selection').replaceChildren(node('option','원문 없이 필기',{value:''}),...sources.map((source,index)=>node('option',`${source.label} · ${source.text.slice(0,100)}`,{value:String(index)})));
    }catch(error){if(valid(ticket))$('note-source-preview').textContent='현재 연결할 수 있는 공개 원문이 없습니다. 자유 필기는 가능합니다.';}
  }
  function reset(){
    capture();if(active?.dirty)persist().catch(()=>{});clearTimeout(timer);sourceTicket++;epoch++;editorTicket++;scope=null;active=null;drafts=[];rows=[];sources=[];saving=null;cursor=null;
    $('note-editor').hidden=true;$('notes-list').replaceChildren();$('note-body').value='';$('note-source-text').textContent='';$('note-source-preview').textContent='';$('note-source-selection').replaceChildren(node('option','원문 없이 필기',{value:''}));
    clearTimeout(countTimer);$('note-save-status').textContent='';$('notes-count').textContent='';$('note-source-load-status').textContent='';
    if($('note-source-dialog').open)$('note-source-dialog').close();
  }
  function selectedSource(){const value=$('note-source-selection').value;return value===''?null:sources[Number(value)];}
  function ref(source){return source?{kind:source.kind,id:source.id,fingerprint:source.fingerprint}:null;}
  function on(id,action){$(id).addEventListener('click',()=>task($(id),action));}
  $('note-body').addEventListener('input',changed);
  $('note-body').addEventListener('compositionstart',()=>{composing=true;clearTimeout(timer);});
  $('note-body').addEventListener('compositionend',()=>{composing=false;changed();});
  $('note-body').addEventListener('select',capture);$('note-body').addEventListener('blur',capture);
  $('notes-query').addEventListener('input',updateList);
  $('note-source-selection').addEventListener('change',()=>{$('note-source-preview').textContent=selectedSource()?.text||'연결 원문 없음. 자유 필기를 시작할 수 있습니다.';});
  on('new-note',()=>start());
  on('new-linked-note',()=>{const source=selectedSource();if(!source)throw new Error('연결할 문장이나 식을 직접 선택하세요. 자유 필기는 원문 선택 없이 가능합니다.');return start(ref(source));});
  on('open-note',()=>{const value=$('notes-list').value;const entry=drafts.find(d=>d.draftId===value)||rows.find(row=>row.id===value);if(entry)return edit(entry);});
  on('save-note',()=>save(true));
  on('copy-note-draft',async()=>{
    const ticket=epoch,selected=scope;
    capture();if(saving)await saving;requireCurrent(ticket);
    const original=active;if(!original)return;
    // First durably preserve the student's conflict draft as a new item. Then
    // remove only that superseded local draft, never the other view's record.
    await start(null,original.body,original.started_ms,false);
    requireCurrent(ticket);await chrome.storage.local.remove(key(original,selected));requireCurrent(ticket);drafts=drafts.filter(draft=>draft!==original);
    const result=await request(`${endpoint()}/notes`);if(valid(ticket)){rows=result;updateList();}
  });
  on('show-note-source',async()=>{
    if(!active)return;capture();sourceReturn=active;const ticket=epoch,requestTicket=++sourceTicket;
    await pause();if(!valid(ticket)||active!==sourceReturn||$('task-notes').hidden)return;
    $('note-source-text').textContent='';$('note-source-load-status').textContent='연결 원문을 다시 확인하고 있습니다.';$('note-source-dialog').showModal();$('note-source-title').focus();
    try{
      let result;
      if(active.revision){result=await request(`${endpoint()}/notes/${active.id}/source`);}
      else{const list=await request(`${endpoint()}/note-sources`);const source=list.find(s=>active.source&&s.kind===active.source.kind&&s.id===active.source.id&&s.fingerprint===active.source.fingerprint);result={available:!!source,source};}
      if(valid(ticket)&&requestTicket===sourceTicket&&$('note-source-dialog').open){$('note-source-text').textContent=result.available?`${result.source.label}. ${result.source.text}`:'';$('note-source-load-status').textContent=result.available?'연결 원문을 준비했습니다. 읽기 전용 본문에서 확인하고 필기 커서로 돌아가세요.':'현재 확인할 수 있는 연결 원문이 없습니다. 학생 필기는 보존됩니다.';}
    }catch(error){if(valid(ticket)&&requestTicket===sourceTicket)$('note-source-load-status').textContent=`원문 확인 실패. ${error.message} 닫고 다시 시도하세요.`;}
  });
  on('close-note-source',()=>$('note-source-dialog').close());
  $('note-source-dialog').addEventListener('close',()=>{sourceTicket++;$('note-source-text').textContent='';if(active&&active===sourceReturn)restoreCursor();sourceReturn=null;});
  on('delete-note',()=>{$('note-delete-confirm').hidden=false;$('cancel-note-delete').focus();});
  on('cancel-note-delete',()=>{$('note-delete-confirm').hidden=true;$('delete-note').focus();});
  on('confirm-note-delete',async()=>{
    const entry=active,ticket=epoch;clearTimeout(timer);if(saving)await saving;if(!valid(ticket)||entry!==active)return;
    if(entry.revision)await request(`${endpoint()}/notes/${entry.id}`,{method:'DELETE',body:{revision:entry.revision}});
    if(!valid(ticket))return;
    await chrome.storage.local.remove(key(entry));drafts=drafts.filter(d=>d!==entry);rows=rows.filter(row=>row.id!==entry.id);active=null;$('note-editor').hidden=true;updateList();$('notes-list').focus();
  });
  on('import-legacy-note',async()=>{
    const ticket=epoch;
    const body=$('note').value;if(!body.trim())throw new Error('복사할 기존 메모가 없습니다.');
    // Copy only on an explicit student action. The legacy progress record stays intact.
    await start(null,body);requireCurrent(ticket);await save(true);
  });
  on('export-my-notes',async()=>{
    const ticket=epoch;
    await flush();requireCurrent(ticket);if(active?.dirty)await save(true);requireCurrent(ticket);
    if(drafts.some(d=>d.dirty))throw new Error('미저장 초안이 있습니다. 각 항목을 저장한 뒤 내보내세요. 초안은 유지됩니다.');
    const result=await request(`${endpoint()}/notes-export`);if(!valid(ticket))return;
    const format=$('note-export-format').value,url=URL.createObjectURL(new Blob([result.text],{type:`text/${format==='md'?'markdown':'plain'};charset=utf-8`}));
    const link=node('a','',{href:url,download:`sullivan-my-notes.${format}`});link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    state('내 필기 파일을 내보냈습니다. 연결 원문은 현재 권한으로 다시 확인했습니다.');
  });
  return {load,reset,flush,restoreCursor,async startAtSource(id){
    const startedMs=position(),ticket=epoch,list=await request(`${endpoint()}/note-sources`);if(!valid(ticket))return;
    const source=list.find(s=>s.kind==='sentence'&&s.id===id);if(!source)throw new Error('현재 공개된 문장을 직접 선택한 뒤 필기하세요.');await start(ref(source),'',startedMs);
  }};
}
