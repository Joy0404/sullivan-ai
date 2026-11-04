/* Opt-in app speech fallback. This neither starts nor detects an OS screen reader. */
window.SullivanFocusVoice = (() => {
  let timer=null, watchdog=null, token=0, utterance=null, playbackHold=null, initialNotice=null, nativeStop=null, nativeUnconfirmedUntil=0;
  function nativeRequest(action,ident) {
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),action==='stop'?1500:10000);
    return fetch('/local/login-voice',{method:'POST',headers:{'Content-Type':'application/json','X-Local-Request':'1'},body:JSON.stringify({action,ident}),keepalive:action==='stop',signal:controller.signal}).finally(()=>clearTimeout(timeout));
  }
  async function stopNative(ident) {
    try {
      const response=await nativeRequest('stop',ident);
      if(!response.ok||!(await response.json()).cancelled)throw Error('Unconfirmed stop');
      nativeUnconfirmedUntil=0;
    }catch(error){nativeUnconfirmedUntil=Date.now()+9000;throw error;}
  }
  function holdsPlayback() {
    return Boolean(playbackHold && window.Portal?.user?.id===playbackHold.user &&
      window.Portal.lectureId===playbackHold.lecture && state.snapshot===playbackHold.snapshot);
  }
  function releasePlayback() {
    const resume=holdsPlayback();playbackHold=null;
    if(resume && enabled() && !window.Portal.gesturePending &&
       !document.getElementById('agent-view').classList.contains('hidden') &&
       !document.querySelector('dialog[open]') && !state.speechInProgress && !state.conceptSequenceActive &&
       !isPlaybackRunning())resumePlayback();
    window.Portal?.syncPlayback?.();
  }
  function holdPlayback() {
    if(!holdsPlayback())playbackHold=null;
    const playing=isPlaybackRunning();
    if(state.speechInProgress)stopAllPlaybackAndSpeech({announceStop:false});
    if(playing && window.Portal?.user?.role==='student' && state.snapshot) {
      playbackHold={user:window.Portal.user.id,lecture:window.Portal.lectureId,snapshot:state.snapshot};
    }
    if(holdsPlayback())pausePlayback({forFocusNotice:true});
    window.Portal?.syncPlayback?.();
  }
  function textWithoutControls(node) {
    if(node.nodeType===Node.TEXT_NODE)return node.nodeValue;
    if(node.nodeType!==Node.ELEMENT_NODE||node.matches('input,select,textarea,button,[aria-hidden="true"]'))return '';
    return [...node.childNodes].map(textWithoutControls).join('');
  }
  function label(element) {
    const labelled=element.getAttribute('aria-labelledby');
    if(labelled)return labelled.split(/\s+/).map(id=>{const n=document.getElementById(id);return n?textWithoutControls(n):'';}).join(' ').trim();
    if(element.getAttribute('aria-label'))return element.getAttribute('aria-label').trim();
    if(element.labels?.length)return [...element.labels].map(textWithoutControls).join(' ').replace(/\s+/g,' ').trim();
    return (element.innerText||element.textContent||'').replace(/\s+/g,' ').trim();
  }
  function describe(element) {
    const name=label(element);if(!name)return '';
    // Native roles stay in the accessibility tree. App speech only adds useful
    // state, rather than reciting technical role names after every focus move.
    if(element.type==='checkbox')return `${name}. ${element.checked?'켜져 있습니다':'꺼져 있습니다'}.`;
    if(element.tagName==='SELECT') {
      const choice=element.selectedOptions?.[0]?.textContent?.trim();
      return choice?`${name}, ${choice}`:name;
    }
    if(element.tagName==='SUMMARY')return `${name}. ${element.parentElement.open?'펼쳐져 있습니다':'접혀 있습니다'}.`;
    if(element.getAttribute('aria-current'))return `${name}. 현재 화면입니다.`;
    if(element.getAttribute('aria-pressed')==='true')return `${name}. 선택되어 있습니다.`;
    return name;
  }
  function status(text) {
    const output=document.getElementById(window.Portal?.user?'focus-voice-status':'login-voice-status');
    if(output)output.textContent=window.Portal?.user?text:text.replaceAll('음성 시작·시험','로그인 음성 시작·시험');
  }
  function cancel({ keepPlayback = false, resume = false } = {}) {
    clearTimeout(timer);clearTimeout(watchdog);token+=1;
    if(initialNotice) {
      const notice=initialNotice;initialNotice=null;notice.phase='cancelled';
      if(notice.channel==='native') {
        const stopping=stopNative(notice.ident).catch(()=>{}).finally(()=>{if(nativeStop===stopping)nativeStop=null;});
        nativeStop=stopping;
      }
    }
    if(utterance){const old=utterance;utterance=null;old.onend=old.onerror=old.onstart=null;window.speechSynthesis?.cancel();}
    if(resume)releasePlayback();
    else if(!keepPlayback)playbackHold=null;
  }
  function enabled() {
    const portal=window.Portal;if(!portal)return false;
    if(!portal.user)return portal.loginVoice&&!document.getElementById('portal-login').classList.contains('hidden');
    return portal.focusVoice&&!portal.readerMode&&portal.user.role==='student';
  }
  function say(text,current,pauseDeadline=performance.now()+1500,notice=null) {
    if(!enabled()||current!==token)return;
    if(nativeStop){nativeStop.finally(()=>say(text,current,pauseDeadline,notice));return;}
    if(Date.now()<nativeUnconfirmedUntil){status('시작 안내의 중지를 확인하지 못했습니다. 잠시 후 음성 시작·시험을 눌러 주세요.');return;}
    if(!('speechSynthesis' in window)||!('SpeechSynthesisUtterance' in window)) {
      cancel({resume:true});
      status('이 브라우저에서는 앱 음성 안내를 사용할 수 없습니다. 외부 스크린리더를 사용해 주세요.');return;
    }
    holdPlayback();
    current=token; // Stopping an earlier lesson explanation also invalidates its focus notice.
    // Embedded providers acknowledge pause asynchronously. Do not start speech
    // over their audio merely because pauseVideo() has been called.
    if(holdsPlayback()&&isPlaybackRunning()) {
      if(performance.now()>=pauseDeadline) {
        cancel({resume:true});status('영상 정지를 확인하지 못해 음성 안내를 보류했습니다. 영상·해설 모두 중지 후 다시 시도해 주세요.');return;
      }
      timer=setTimeout(()=>say(text,current,pauseDeadline,notice),40);return;
    }
    const spoken=prepareSpeechText(text.replace(/[—–]/g, ", ").replace(/([0-9.]+)×/g, "$1배"));
    const speech=new SpeechSynthesisUtterance(spoken);utterance=speech;speech.lang='ko-KR';
    const voice=selectedKoreanVoice();if(voice)speech.voice=voice;
    speech.rate=Number(document.getElementById('speech-rate').value)||.95;
    speech.volume=Number(document.getElementById('speech-volume').value)||.9;
    let started=false;
    speech.onstart=()=>{if(current!==token)return;started=true;clearTimeout(watchdog);
      if(notice===initialNotice&&notice)notice.phase='started';
      watchdog=setTimeout(()=>{if(current===token){cancel({resume:true});status('음성 안내가 지연되어 중지했습니다. 다시 안내하려면 음성 시작·시험을 눌러 주세요.');}},Math.min(120000,Math.max(12000,spoken.length*260)));
      if(!notice&&window.Portal?.user)status('브라우저에서 음성 재생을 시작했습니다. 소리가 없으면 탭 음소거와 출력 장치를 확인해 주세요.');};
    speech.onend=()=>{if(current!==token)return;clearTimeout(watchdog);utterance=null;if(notice===initialNotice&&notice)notice.phase='completed';releasePlayback();if(!notice&&window.Portal?.user)status('음성 재생 처리가 끝났습니다. 다음 버튼으로 이동할 수 있습니다.');};
    speech.onerror=e=>{if(current!==token)return;clearTimeout(watchdog);utterance=null;if(notice===initialNotice&&notice){notice.phase='failed';notice.error=e.error;}releasePlayback();if(['canceled','interrupted'].includes(e.error))return;
      const messages={'not-allowed':'브라우저가 자동 음성을 차단했습니다. 음성 시작·시험 버튼을 눌러 주세요.','language-unavailable':'한국어 음성을 사용할 수 없습니다. 기기 음성 설정을 확인해 주세요.','voice-unavailable':'선택한 음성을 사용할 수 없습니다. 음성 설정을 확인해 주세요.','audio-busy':'다른 음성 출력이 사용 중입니다. 잠시 후 음성 시작·시험을 눌러 주세요.'};
      status(messages[e.error]||'브라우저 음성 재생에 실패했습니다. 음성 시작·시험을 눌러 다시 확인해 주세요.');};
    try {
      // Resume explicitly: a paused synthesizer accepts utterances but produces no audio.
      window.speechSynthesis.resume();
      watchdog=setTimeout(()=>{if(current===token&&!started){cancel({resume:true});status('음성 재생 시작이 확인되지 않습니다. 음성 시작·시험 버튼을 누르고 브라우저 음소거·출력 설정을 확인해 주세요.');}},1800);
      window.speechSynthesis.speak(speech);
    }catch{cancel({resume:true});status('음성 재생을 시작하지 못했습니다. 브라우저의 음성 지원과 출력 설정을 확인해 주세요.');}
  }
  function read(element) {
    if(!window.Portal?.user&&element.id==='login-role-student') {readInitial(element);return;}
    cancel({keepPlayback:true});if(!enabled()){playbackHold=null;return;}
    const text=describe(element);if(!text){releasePlayback();return;}const current=token;
    // Login Tab focus occurs in the keyboard gesture; speak there so browsers
    // can accept the first utterance without a prior mouse click.
    if(!window.Portal.user){if(document.activeElement===element)say(text,current);return;}
    timer=setTimeout(()=>{if(document.activeElement===element)say(text,current);},160);
  }
  function readInitial(element,retry=false) {
    if(!enabled()||!window.Portal.loginReady||window.Portal.user||element.disabled||document.activeElement!==element)return;
    const previous=initialNotice?.target===element?initialNotice:null;
    if(previous&&['pending','started','completed'].includes(previous.phase))return;
    if(previous?.phase==='failed'&&(!retry||previous.retries>=1))return;
    cancel();
    const notice={target:element,phase:'pending',channel:window.Portal.loginNative?'native':'browser',ident:crypto.randomUUID(),token,retries:retry?(previous?.retries||0)+1:0};
    initialNotice=notice;
    if(notice.channel==='browser'){say(describe(element),token,undefined,notice);return;}
    nativeRequest('start',notice.ident).then(async response=>{
      if(!response.ok)throw Error('Local startup unavailable');
      const result=await response.json();
      if(initialNotice!==notice||token!==notice.token||!enabled()||document.activeElement!==element)return;
      if(result.completed)notice.phase='completed';
      else if(result.cancelled)notice.phase='cancelled';
      else throw Error('Local startup incomplete');
    }).catch(async()=>{
      if(initialNotice!==notice||token!==notice.token||!enabled()||document.activeElement!==element)return;
      try{await stopNative(notice.ident);}catch{
        if(initialNotice!==notice||token!==notice.token||!enabled()||document.activeElement!==element)return;
        notice.phase='failed';status('시작 안내 상태를 확인하지 못했습니다. 잠시 후 로그인 음성 시작·시험을 눌러 주세요.');return;
      }
      if(initialNotice!==notice||token!==notice.token||!enabled()||document.activeElement!==element)return;
      notice.channel='browser';notice.phase='pending';say(describe(element),token,undefined,notice);
    });
  }
  function test() {
    cancel({keepPlayback:true});
    // Called synchronously by an explicit button gesture, before any network request.
    say('버튼 음성 안내 시험입니다. 탭 키로 이동하면 버튼 이름을 읽습니다.',token);
  }
  function message(text) {cancel({keepPlayback:true});say(text,token);}
  document.addEventListener('focusin',e=>{
    const target=e.target;
    // An external reader's speech completion is not observable. Pause and let
    // its user resume explicitly, instead of guessing a reading duration.
    if(window.Portal?.readerMode && window.Portal.user?.role==='student' &&
       !document.getElementById('agent-view').classList.contains('hidden') && isPlaybackRunning())pausePlayback();
    if(target.matches?.('button,a[href],input,select,textarea,summary'))read(target);
    else cancel({resume:true});
  });
  document.addEventListener('change',e=>{
    if(enabled()&&document.activeElement===e.target&&e.target.matches('input[type="checkbox"],select'))read(e.target);
  });
  document.addEventListener('toggle',e=>{
    if(!enabled()||e.target.tagName!=='DETAILS')return;
    const summary=e.target.querySelector(':scope > summary');
    if(document.activeElement===summary)read(summary);
  },true);
  window.addEventListener('blur',()=>cancel());
  window.addEventListener('pagehide',()=>cancel());
  document.addEventListener('visibilitychange',()=>{if(document.hidden)cancel();});
  window.speechSynthesis?.addEventListener?.('voiceschanged',()=>{
    if(initialNotice?.phase==='failed'&&['voice-unavailable','language-unavailable','synthesis-unavailable'].includes(initialNotice.error))readInitial(initialNotice.target,true);
  });
  return {describe,read,readInitial,cancel,test,message,holdsPlayback};
})();
