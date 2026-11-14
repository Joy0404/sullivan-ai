// Runs only in this extension document; never installs handlers in lecture tabs.
export function installStudentKeyboard({gesture, enabled, hasLesson, onError, seek, position, releasePanel, onFocus, active=()=>hasLesson(), outputActive=()=>false, emergencyStop=()=>{}, abortGesture=()=>{}}) {
  const selector='button,a[href],input:not([type=hidden]),textarea,select,summary,[tabindex],[contenteditable=true]';
  const visible=e=>Boolean(e?.getClientRects().length && !e.closest('[hidden],[inert]') && getComputedStyle(e).visibility!=='hidden' && !e.matches(':disabled'));
  const textEntry=e=>Boolean(e?.closest('textarea,select,[contenteditable=true],input:not([type=checkbox]):not([type=radio]):not([type=button]):not([type=submit])'));
  const nativeSpace=e=>textEntry(e)||Boolean(e?.closest('input[type=checkbox],input[type=radio]'));
  const modal=()=>[...document.querySelectorAll('dialog[open]')].at(-1);
  const controls=()=>[...(modal()||document).querySelectorAll(selector)].filter(e=>visible(e)&&e.tabIndex>=0);
  let contained=true,shift=null,spaceDown=false,editingTap=0;
  function move(backward){
    const list=controls(),active=document.activeElement;if(!list.length)return;
    const index=list.indexOf(active);
    const adjacent=backward?list.filter(e=>e.compareDocumentPosition(active)&Node.DOCUMENT_POSITION_FOLLOWING).at(-1):list.find(e=>active.compareDocumentPosition(e)&Node.DOCUMENT_POSITION_FOLLOWING);
    const target=index<0 ? adjacent||(backward?list.at(-1):list[0]) : list[(index+(backward?-1:1)+list.length)%list.length];
    target.focus();
  }
  function reset(event){shift=null;spaceDown=false;editingTap=0;abortGesture(event);gesture.cancel();}
  function cancelPending(event){editingTap=0;abortGesture(event);spaceDown=false;gesture.cancel();}
  function enter(){contained=true;onFocus?.();}
  document.addEventListener('keydown',event=>{
    if(event.isComposing){reset();return;}
    if(event.code!=='Space'&&event.key!=='Shift')cancelPending(event);
    if(event.key!=='Shift')shift=null;
    else if(!event.repeat&&!event.ctrlKey&&!event.altKey&&!event.metaKey&&!textEntry(event.target))shift={target:event.target,code:event.code};
    if(event.ctrlKey||event.altKey||event.metaKey)return;
    if(event.key==='Escape'&&!modal()){
      reset();contained=false;releasePanel();return;
    }
    if(event.key==='Tab'&&(contained||modal())){event.preventDefault();move(event.shiftKey);return;}
    if(event.code==='Space'&&enabled()&&active()&&!event.shiftKey&&!nativeSpace(event.target)&&!modal()){
      event.preventDefault();event.stopImmediatePropagation();if(!event.repeat&&!spaceDown){spaceDown=true;gesture.down();}return;
    }
    if(hasLesson()&&!event.shiftKey&&!textEntry(event.target)&&!modal()&&['ArrowLeft','ArrowRight'].includes(event.key)){
      event.preventDefault();seek(position()+(event.key==='ArrowLeft'?-10000:10000)).catch(onError);
    }
  },true);
  document.addEventListener('keyup',event=>{
    if(event.code==='Space'&&enabled()&&nativeSpace(event.target)&&outputActive()&&!event.isComposing&&!event.ctrlKey&&!event.altKey&&!event.metaKey&&!event.shiftKey){
      const now=performance.now();if(editingTap&&now-editingTap<420){editingTap=0;emergencyStop();}else editingTap=now;
    }
    if(event.code==='Space'&&spaceDown){event.preventDefault();event.stopImmediatePropagation();spaceDown=false;gesture.up();}
    if(event.key==='Shift'){
      const candidate=shift;shift=null;
      if(contained&&candidate&&candidate.target===document.activeElement&&candidate.code===event.code&&!event.ctrlKey&&!event.altKey&&!event.metaKey&&!event.shiftKey){event.preventDefault();move(true);}
    }
  },true);
  document.addEventListener('focusin',cancelPending);
  document.addEventListener('compositionstart',reset,true);
  document.addEventListener('pointerdown',event=>{reset(event);contained=true;},true);
  window.addEventListener('blur',reset);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)reset();});
  return {enter,reset,controls,move,release(){reset();contained=false;}};
}
