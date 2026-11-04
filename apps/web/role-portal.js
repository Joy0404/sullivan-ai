/* Local role portal. Reuses the original player, safety-filtered narration,
   concept search, passage tools, review, notebook, and grounded chat. */
window.Portal = (() => {
  const ui = {user:null, lectureId:null, readerMode:false, focusVoice:false, loginRole:null, loginVoice:true,loginReady:false,loginNative:false,localVoiceProfile:null,compatible:false};
  const requiredBuild='sullivan-roles-20261102-r2';
  let students=[], lectures=[], current=null, originMs=null, focusedPurpose='watch-panel';
  let savePromise=Promise.resolve(), progressTimer=null, opening=false, sampleSession=null;
  let lastFocus=null, wasPlaying=false, recognition=null, transcript='', released=false, finalized=false;
  let setup=false;
  const views=['portal-login','portal-home','guardian-dashboard','setup-view','agent-view'];
  const el=id=>document.getElementById(id);
  function node(tag,text,props={}) {const n=document.createElement(tag);if(text!==undefined)n.textContent=text;Object.assign(n,props);return n;}
  function button(text,action,props={}) {const b=node('button',text,{type:'button',...props});b.addEventListener('click',()=>Promise.resolve(action()).catch(e=>error(e.message)));return b;}
  async function request(path,options={}) {
    const res=await fetch('/local'+path,{...options,headers:{'Content-Type':'application/json','X-Local-Request':'1',...options.headers}});
    const data=await res.json().catch(()=>({}));
    if(!res.ok) {if(res.status===401 && !['/login','/me'].includes(path)) await signedOut();throw new Error(data.detail||'요청을 완료하지 못했습니다. 다시 시도해 주세요.');}
    return data;
  }
  const send=(path,data,method='POST')=>request(path,{method,body:JSON.stringify(data)});
  const focusTicket=()=>window.SullivanKeyboard?.ticket();
  function focusFirst(place,ticket) {
    const targets={
      login:['#login-role-student','#login-role-guardian'],
      setup:['#login-username'],
      guardian:students.length?['#guardian-prepare']:['#student-create input[name="name"]','#guardian-prepare'],
      home:['#student-list-open'],
      prepare:['#lecture-form input[name="title"]'],
      publish:students.length?['#publish-students input:not(:checked)','#publish-title-input']:['#guardian-publish [data-guardian-home]','#publish-title-input'],
      watch:ui.user?.role==='guardian'?['#describe-now']:['#learner-play:not(:disabled)','[data-learn-panel][data-purpose="paragraph"]','#command-surface'],
      paragraph:['.paragraph-quick-commands [data-paragraph-command="전체 지문"]','#long-passage-title'],
      search:['#navigation-command'],question:['#chat-input'],
      records:['#learner-note'],review:['#read-review'],study:['#read-study-guide'],
      help:['#onboarding-card button'],analysis:['#cancel-analysis-wait']
    }[place]||[place];
    const focused=window.SullivanKeyboard.focus(targets,ticket);
    if(focused&&place==='login')SullivanFocusVoice.readInitial(el('login-role-student'));
    return focused;
  }
  function focusPanel(panel) {
    if(panel==='watch-panel')return focusFirst('watch');
    if(panel==='chat-panel')return focusFirst('question');
    if(panel==='review-panel')return focusFirst('review');
    if(panel==='study-panel')return focusFirst('study');
    if(panel==='passage-panel')return focusFirst(focusedPurpose==='paragraph'?'paragraph':'search');
    return window.SullivanKeyboard.focus(el(panel).querySelector('h2'));
  }
  function show(id) {for(const v of views)el(v).classList.toggle('hidden',v!==id);el('portal-feedback').classList.add('hidden');}
  function feedback(text,focus=false) {
    const box=el('portal-feedback');el('portal-feedback-copy').textContent=text;box.classList.remove('hidden');
    // A focused message is announced through focus, not a simultaneous live update.
    if(focus)box.focus();
    if((ui.user?.role==='student'&&ui.focusVoice&&!ui.readerMode)||(!ui.user&&ui.loginVoice))SullivanFocusVoice.message(text);
    else if(!focus)announce(text);
  }
  function error(text,back) {
    if(back) {show('setup-view');el(back).classList.remove('hidden');}
    feedback(text,true);
  }
  function loginUI() {
    const guardian=ui.loginRole==='guardian';
    el('login-role-student').disabled=setup;
    el('login-role-student').setAttribute('aria-pressed',String(ui.loginRole==='student'));
    el('login-role-guardian').setAttribute('aria-pressed',String(guardian));
    el('setup-name-label').classList.toggle('hidden',!setup);
    el('login-title').textContent=setup?'처음 보호자 계정 만들기':ui.loginRole==='student'?'학생 로그인':guardian?'보호자 로그인':'Sullivan AI 로그인';
    el('login-submit').textContent=setup?'보호자 계정 만들기':'로그인';
    el('login-submit').disabled=!ui.compatible;
    el('login-help').textContent=setup?'처음에는 보호자 계정을 먼저 만들어 주세요. 학생 계정은 보호자 준비실에서 만들 수 있습니다.':'학생 로그인 또는 보호자 로그인을 선택한 뒤 로그인 이름과 비밀번호를 입력하세요.';
    el('login-focus-voice').checked=ui.loginVoice;el('login-focus-voice').disabled=guardian;
    el('login-voice-test').disabled=guardian;
    el('login-voice-status').textContent=guardian?'보호자 로그인을 선택해 앱 음성을 중지했습니다.':'Tab은 다음, Shift만 눌렀다 떼면 이전으로 이동합니다. 입력 중 Shift와 Shift+Tab은 원래대로 사용합니다. 이름과 비밀번호 값은 읽지 않습니다.';
  }
  function chooseLogin(role) {
    if(setup&&role==='student')return;
    el('portal-feedback').classList.add('hidden');
    SullivanFocusVoice.cancel();ui.loginRole=role;ui.loginVoice=role==='student';loginUI();
    if(ui.loginVoice)SullivanFocusVoice.message('학생 로그인입니다. Tab 키로 로그인 이름과 비밀번호를 입력하세요. 학생 로그인 후에도 앱 음성 안내가 계속됩니다.');
    else stopAllPlaybackAndSpeech({announceStop:false});
    el('login-username').focus();
  }
  async function signedOut() {
    stopAllPlaybackAndSpeech({announceStop:false});stopVoice();
    SullivanFocusVoice.cancel();
    stopCurrentLectureForNavigation();
    ui.user=null;ui.focusVoice=false;ui.readerMode=false;ui.loginRole=null;ui.loginVoice=true;ui.loginReady=true;ui.lectureId=null;current=null;state.snapshot=null;state.session=null;
    state.localVideoFile=null;state.pendingLinkResult=null;state.savedLectures=[];state.bookmarks=[];state.underlinedParagraphIds.clear();state.conceptSearchResults=null;
    el('lecture-video').removeAttribute('src');el('lecture-video').load();el('lecture-form').reset();
    for(const id of ['asset-list','transcript-list','passage-document','long-passage-document','review-summary','review-visual','review-highlight','review-segments','study-overview','concept-map','study-glossary','recall-questions','evidence-list','chat-log','current-description','video-file-name','material-preview'])el(id).replaceChildren();
    for(const id of ['chat-input','learner-note','bookmark-note','navigation-command','paragraph-navigation-command'])el(id).value='';
    state.demoAccessCode='';el('demo-access-code').value='';el('login-password').value='';
    document.body.dataset.role='signed-out';el('portal-logout').classList.add('hidden');el('account-name').textContent='';
    syncMediaNavigation();
    show('portal-login');loginUI();focusFirst(setup?'setup':'login');
  }
  function settings() {
    syncMediaNavigation();
    const p=ui.user?.settings||{};
    ui.readerMode=Boolean(p.reader_mode);el('reader-mode').checked=ui.readerMode;
    ui.focusVoice=Boolean(p.focus_voice)&&!ui.readerMode;el('focus-voice').checked=ui.focusVoice;
    el('auto-narration').checked=p.auto_description!==false;
    el('speech-rate').value=String(p.speech_rate||.95);el('speech-volume').value=String(p.speech_volume??.9);
    syncChatChannel();
  }
  async function authenticated(user) {
    const continueVoice=user.role==='student'&&ui.loginRole==='student';
    if(continueVoice)user.settings={...user.settings,focus_voice:ui.loginVoice,reader_mode:ui.loginVoice?false:user.settings?.reader_mode};
    SullivanFocusVoice.cancel();ui.loginVoice=false;ui.loginReady=false;
    ui.user=user;document.body.dataset.role=user.role;el('account-name').textContent=`${user.name} (${user.role==='student'?'학생':'보호자'})`;
    el('portal-logout').classList.remove('hidden');el('login-password').value='';settings();
    if(continueVoice)await saveSpeechPreferences();
    await home();
    if(user.role==='student'&&!user.onboarded) {
      showHelp(true);
    }
  }
  async function home() {
    const ticket=focusTicket();
    stopVoice();stopAllPlaybackAndSpeech({announceStop:false});
    await saveProgress();el('text-command-dialog').close();el('text-command-dialog').classList.add('hidden');
    if(!ui.user)return signedOut();
    if(ui.user.role==='guardian') {
      show('guardian-dashboard');el('guardian-dashboard').setAttribute('aria-busy','true');
      el('guardian-dashboard').inert=true;
      try {await loadGuardian();}
      finally {el('guardian-dashboard').inert=false;el('guardian-dashboard').setAttribute('aria-busy','false');}
      focusFirst('guardian',ticket);
    }
    else {
      show('portal-home');focusFirst('home');
      // A slow list response must not pull focus back after the student tabs on.
      await loadStudent();
    }
  }
  async function loadStudent() {
    const box=el('assigned-list');lectures=[];box.replaceChildren();el('assigned-status').textContent='강의 목록 확인 중';
    try {
      lectures=await request('/lectures');
      el('assigned-status').textContent=lectures.length?'강의를 고르면 저장된 위치부터 열립니다. 자동으로 재생하지 않습니다.':'아직 준비된 강의가 없습니다. 보호자가 준비하면 여기에 나타납니다. 사용법을 연습할 수 있습니다.';
      lectures.forEach((l,i)=>{
        // Canonical samples repeat their field and series in the original title.
        // Keep the full title in the lesson view; use its topic in the list.
        const title=l.sample_id?l.title.split(' · ').at(-1):l.title;
        const subject=l.sample_id?l.subject.split(' · ')[0]:l.subject;
        box.append(button(`강의 ${i+1}. ${subject} — ${title}`,()=>openLecture(l.id),{className:'assigned-lecture'}));
      });
      return true;
    }catch(e){el('assigned-status').textContent='목록을 불러오지 못했습니다. 연결을 확인하고 다시 시도하세요.';box.append(button('강의 목록 다시 확인',openLectureList));return false;}
  }
  async function openLectureList() {
    if(ui.user?.role!=='student')return;
    const loaded=await loadStudent();
    if(ui.user?.role!=='student')return;
    const first=el('assigned-list').querySelector('button');
    if(first)first.focus();else {el('assigned-title').focus();if(loaded)feedback('아직 준비된 강의가 없습니다. 보호자가 이 학생에게 배정하고 준비 완료한 강의가 여기에 표시됩니다.');}
  }
  async function loadGuardian() {
    students=await request('/students');lectures=await request('/lectures');
    const account=el('account-name');
    account.replaceChildren(node('span',ui.user.name==='보호자'?'보호자님':`보호자 ${ui.user.name}님`),node('a','가이드',{href:'/guide/'}));
    const select=el('settings-student'),old=select.value;select.replaceChildren();
    students.forEach(s=>select.append(node('option',`${s.name} (${s.username})`,{value:s.id})));if(students.some(s=>s.id===old))select.value=old;
    const sampleSelect=el('sample-assign-student'),sampleOld=sampleSelect.value;sampleSelect.replaceChildren(node('option',students.length?'배정할 학생 선택':'학생 계정을 먼저 만들어 주세요',{value:''}));
    students.forEach(s=>sampleSelect.append(node('option',`${s.name} (${s.username})`,{value:s.id})));
    sampleSelect.value=students.some(s=>s.id===sampleOld)?sampleOld:students.length===1?students[0].id:'';
    el('sample-assign-fields').disabled=!students.length;
    el('guardian-settings-fields').disabled=!students.length;
    el('guardian-create-panel').open=!students.length;
    const createPanel=el('guardian-create-panel');
    createPanel.classList.toggle('guardian-first-task',!students.length);
    if(students.length)el('guardian-students').after(createPanel);
    else el('guardian-main').prepend(createPanel);
    const hasStudents=students.length>0,hasLectures=lectures.length>0;
    if(hasStudents&&!hasLectures)el('guardian-sample-panel').open=true;
    const assigned=lectures.filter(l=>l.ready&&l.students.some(id=>students.some(s=>s.id===id)));
    const hasAssignments=assigned.length>0;
    const defaults={auto_description:true,problem_mode:true,speech_rate:.95,speech_volume:.9,reader_mode:false,focus_voice:false};
    const customSettings=students.some(s=>Object.entries(defaults).some(([key,value])=>(s.settings?.[key]??value)!==value));
    const states=[
      ['student',hasStudents?'완료':'할 차례'],
      ['lecture',hasLectures?'완료':hasStudents?'할 차례':'아직'],
      ['assignment',hasAssignments?'완료':hasLectures&&hasStudents?'할 차례':'아직'],
      ['settings',customSettings?'완료':'기본값']
    ];
    for(const [key,value] of states){const status=el('guardian-task-'+key);status.textContent=value;status.dataset.state=value;}
    const next=!hasStudents?['create','학생 계정 만들기','학생 계정을 먼저 만들어 주세요.','step-2']:
      !hasLectures?['prepare','강의 준비하기','샘플로 연습하거나 내 강의를 준비해 주세요.','step-4']:
      !hasAssignments?['assign','배정할 강의 확인하기','강의의 관리에서 배정 학생과 준비 상태를 확인해 주세요.','step-6']:
      ['settings','학생별 설정 확인하기','강의 배정을 마쳤습니다. 학생에게 맞는 기본 설정을 확인해 보세요.','step-3'];
    const targets={create:'guardian-create-panel',prepare:'guardian-preparation',assign:'guardian-lectures',settings:'guardian-settings-panel',help:'guardian-help'};
    el('guardian-next').textContent=next[1];el('guardian-next').dataset.guardianTarget=next[0];el('guardian-next').href='#'+targets[next[0]];
    el('guardian-next-hint').textContent=next[2];el('guardian-help-context').textContent=next[2];
    el('guardian-help-guide').href='/guide/#'+next[3];el('guardian-help-guide').textContent=next[1]+' 안내';
    const summary=`학생 ${students.length}명, 준비한 강의 ${lectures.length}개, 준비 완료한 배정 강의 ${assigned.length}개입니다.`;
    if(el('guardian-progress-status').textContent!==summary)el('guardian-progress-status').textContent=summary;
    const roster=el('guardian-students');roster.replaceChildren();
    if(!hasStudents)roster.append(node('p','학생 계정을 만들면 여기에 이름과 배정 강의가 표시됩니다.'));
    for(const s of students){
      const card=node('article',undefined,{className:'guardian-student'}),titleId='guardian-student-'+s.id;
      card.setAttribute('aria-labelledby',titleId);
      const copy=node('div');copy.append(node('h3',s.name,{id:titleId}),node('p',`배정 강의 ${lectures.filter(l=>l.students.includes(s.id)).length}개`));
      const settingsLink=node('a','설정',{href:'#guardian-settings-panel'});settingsLink.dataset.guardianTarget='settings';settingsLink.dataset.student=s.id;settingsLink.setAttribute('aria-describedby',titleId);
      card.append(copy,settingsLink);roster.append(card);
    }
    const dashboard=el('guardian-dashboard');
    if(!dashboard.dataset.navigationBound){
      dashboard.dataset.navigationBound='true';
      dashboard.addEventListener('click',event=>{
        const link=event.target.closest('a[data-guardian-target]');if(!link||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
        event.preventDefault();const action=link.dataset.guardianTarget,target=el(targets[action]);if(!target)return;
        if(link.dataset.student){el('settings-student').value=link.dataset.student;el('settings-student').dispatchEvent(new Event('change'));}
        if(target.tagName==='DETAILS')target.open=true;
        const focus=action==='create'?target.querySelector('input'):action==='settings'?target.querySelector('summary'):action==='prepare'?el('guardian-preparation-title'):action==='assign'?el('guardian-lectures-title'):target.querySelector('summary');
        focus?.focus({preventScroll:true});(focus||target).scrollIntoView({block:'start'});
      });
      const desktop=matchMedia('(min-width: 960px)');
      const helpLayout=()=>{const help=el('guardian-help');if(!desktop.matches&&help.contains(document.activeElement))help.querySelector('summary').focus({preventScroll:true});help.open=desktop.matches;};desktop.addEventListener('change',helpLayout);helpLayout();
    }
    el('guardian-student-hint').textContent=students.length?'선택한 학생의 기본 안내 방식을 설정하세요. 학생은 수강 중 읽기 속도와 음량을 직접 조절할 수 있습니다.':'먼저 학생 계정을 만들어 주세요. 설정은 학생을 연결한 뒤 저장할 수 있습니다.';
    fillSettings();renderGuardianLectures();
    const estimate=await navigator.storage?.estimate?.().catch(()=>null);
    el('storage-estimate').textContent=estimate?`이 브라우저 사용량 약 ${formatBytes(estimate.usage)}. 원본은 명시적으로 저장한 경우에만 브라우저에 있습니다.`:'브라우저 저장 공간 정보를 제공하지 않습니다.';
  }
  function fillSettings() {
    const s=students.find(s=>s.id===el('settings-student').value)?.settings||{};
    el('settings-auto').checked=s.auto_description!==false;el('settings-problem').checked=s.problem_mode!==false;
    el('settings-reader').checked=!!s.reader_mode;el('settings-focus-voice').checked=!!s.focus_voice&&!s.reader_mode;el('settings-volume').value=String(s.speech_volume??.9);el('settings-rate').value=String(s.speech_rate||.95);el('settings-reset').checked=false;
  }
  function studentChecks(container,selected=[]) {
    container.replaceChildren();students.forEach(s=>{const label=node('label');const input=node('input',undefined,{type:'checkbox',value:s.id,checked:selected.includes(s.id)});label.append(input,document.createTextNode(`${s.name} (${s.username})`));container.append(label);});
  }
  const checked=container=>[...container.querySelectorAll('input:checked')].map(n=>n.value);
  function renderGuardianLectures() {
    const box=el('guardian-lectures');box.replaceChildren();
    const orderStudent=students.find(s=>s.id===el('settings-student').value);
    el('guardian-order-help').textContent=orderStudent?`강의 순서 기준: ${orderStudent.name} (${orderStudent.username}). 학생 관리에서 학생을 바꿀 수 있습니다.`:'학생을 연결하면 학생별 강의 순서를 관리할 수 있습니다.';
    if(!lectures.length)box.append(node('p','아직 배정한 강의가 없습니다. 학생 계정을 만든 뒤 샘플 또는 자료를 준비하세요.'));
    for(const l of lectures) {
      const titleId='guardian-lecture-title-'+l.id;
      const card=node('article',undefined,{className:'guardian-lecture'});card.setAttribute('aria-labelledby',titleId);
      const heading=node('div',undefined,{className:'guardian-lecture-heading'});
      heading.append(node('h3',`${l.subject} — ${l.title}`,{id:titleId}),node('p',l.ready?'준비 완료':'준비 중. 학생에게 아직 보이지 않습니다.',{className:'guardian-ready '+(l.ready?'is-ready':'is-waiting')}));
      card.append(heading,node('p',l.students.length?'배정 학생: '+l.students.map(id=>students.find(s=>s.id===id)?.name||'연결된 학생').join(', '):'배정된 학생이 없습니다.',{className:'guardian-assignees'}));
      const edit=node('details');edit.append(node('summary','관리'));
      edit.firstChild.setAttribute('aria-describedby',titleId);
      const form=node('form');const title=node('input',undefined,{value:l.title,required:true,maxLength:160}),subject=node('input',undefined,{value:l.subject,required:true,maxLength:80});
      for(const [name,input]of [['강의 제목',title],['과목',subject]]){const label=node('label',name);label.append(input);form.append(label);}
      const assignments=node('fieldset');assignments.append(node('legend','배정 학생'));const checks=node('div');studentChecks(checks,l.students);assignments.append(checks);form.append(assignments,node('button','수정 저장',{type:'submit'}));
      form.addEventListener('submit',async e=>{e.preventDefault();try{await send('/lectures/'+l.id,{title:title.value,subject:subject.value,students:checked(checks)},'PUT');await loadGuardian();feedback('강의 정보와 배정을 저장했습니다.',true);}catch(e){error(e.message);}});edit.append(form);
      const selected=el('settings-student').value;
      const actions=node('div',undefined,{className:'guardian-lecture-actions'});
      if(!l.ready&&l.playback_kind!=='local')actions.append(button('준비 완료로 제공',async()=>{await request('/lectures/'+l.id+'/ready',{method:'PUT'});await loadGuardian();feedback('강의를 준비 완료로 제공했습니다. 학생의 강의 듣기에서 목록을 다시 확인할 수 있습니다.',true);}));
      if(selected&&l.students.includes(selected)){
        // Fetch actual student order from the dedicated guardian endpoint rather than assuming creation order.
        actions.append(button('순서 앞당기기',()=>moveLecture(l.id,selected,-1)),button('순서 뒤로 보내기',()=>moveLecture(l.id,selected,1)));
      }
      actions.append(button('강의 삭제',async()=>{if(!confirm('배정과 학습 기록, 이 브라우저의 저장 영상을 삭제할까요?'))return;await request('/lectures/'+l.id,{method:'DELETE'});await mediaRemove(l.id);await loadGuardian();feedback('강의와 배정 기록을 삭제했습니다.',true);},{className:'guardian-delete'}));
      for(const action of actions.children)action.setAttribute('aria-describedby',titleId);
      edit.append(actions);card.append(edit);box.append(card);
    }
  }
  async function moveLecture(id,student,delta) {
    const order=await request('/students/'+student+'/order');const index=order.indexOf(id),next=index+delta;
    if(index<0||next<0||next>=order.length)return feedback('이미 목록의 끝입니다.');
    [order[index],order[next]]=[order[next],order[index]];await send('/order',{student,lectures:order},'PUT');feedback('강의 순서를 변경했습니다.');
  }
  function prepare() {show('setup-view');el('lecture-form').classList.remove('hidden');el('student-library').classList.add('hidden');focusFirst('prepare');}
  async function assignSample(e) {
    e.preventDefault();const submit=el('sample-assign-submit');if(submit.disabled)return;
    const guardian=ui.user?.id,student=students.find(s=>s.id===el('sample-assign-student').value);
    if(!student)return feedback('먼저 배정할 학생을 선택해 주세요.',true);
    submit.disabled=true;
    el('sample-assign-receipt').textContent='선택한 샘플의 배정을 저장하고 있습니다.';
    try {
      const receipt=await send('/samples/'+el('sample-assign-kind').value+'/assign',{students:[student.id]});
      if(ui.user?.id!==guardian)return;
      const text=`${receipt.title} 강의를 ${student.name} (${student.username}) 학생에게 배정하고 준비 완료로 저장했습니다. 학생으로 로그인해 강의 듣기를 누르세요.`;
      el('sample-assign-receipt').textContent=text;
      try {await loadGuardian();}catch {el('sample-assign-receipt').textContent=text+' 준비실 목록 갱신은 다시 시도해 주세요.';}
      feedback(text,true);
    }catch(error){const text='샘플 배정을 저장하지 못했습니다. '+error.message;el('sample-assign-receipt').textContent=text;feedback(text,true);}
    finally{submit.disabled=false;}
  }
  function lectureReady() {
    if(!ui.user)return;
    show('agent-view');el('learning-records').classList.add('hidden');
    el('guardian-publish').classList.toggle('hidden',ui.user.role!=='guardian');el('learner-tools').classList.toggle('hidden',ui.user.role!=='student');
    el('learner-title').textContent=current?.title||state.session?.title||'강의';
    el('learner-source').textContent=state.isSample?'사전 준비된 샘플 결과입니다. 이번에 영상을 새로 분석하지 않았습니다.':'보호자가 준비한 강의입니다.';
    if(ui.user.role==='guardian') {
      if(sampleSession!==state.session?.session_id){sampleSession=state.session?.session_id;el('publish-title-input').value=state.session?.title||'';el('publish-subject').value=state.session?.subject||'일반';studentChecks(el('publish-students'));el('publish-store').checked=false;el('publish-chat').checked=false;}
      el('publish-store').disabled=!state.localVideoFile;
    }
    syncPlayback();
    if(ui.user.role==='guardian')focusFirst('publish');
  }
  async function openLecture(id) {
    const ticket=focusTicket();
    if(opening)return;opening=true;stopAllPlaybackAndSpeech({announceStop:false});await saveProgress();
    ui.restoring=true;
    try {
      const data=await request('/lectures/'+id);
      ui.lectureId=id;current=data;state.conceptSearchResults=null;originMs=null;el('learner-return').disabled=true;
      state.snapshot=data.snapshot;state.session=data.snapshot.session;state.session.title=data.title;
      state.isSample=data.snapshot.session.source_label?.includes('샘플')||false;
      state.currentSavedLectureId=null;state.pendingLinkResult=null;state.announcedGaps.clear();state.bookmarks=data.progress.bookmarks||[];
      state.underlinedParagraphIds=new Set(data.progress.underlined||[]);el('learner-note').value=data.progress.note||'';
      state.currentParagraphId=null;state.localVideoFile=null;state.linkedPlaybackKind=null;
      if(state.videoUrl){URL.revokeObjectURL(state.videoUrl);state.videoUrl=null;}
      disposeYouTubePlayer();
      el('lecture-video').removeAttribute('src');el('lecture-video').load();
      el('lecture-title').textContent=data.title;el('lecture-meta').textContent=data.subject;
      el('current-description').textContent='필요한 화면 해설이 이곳에 표시됩니다.';el('description-reason').textContent='검증된 화면 정보만 안내합니다.';
      el('learner-play').disabled=data.playback.kind==='none';
      renderAll();selectPanel('watch-panel');
      settings();
      if(data.playback.kind==='local') {
        const encrypted=await mediaGet(id);
        if(!encrypted)throw new Error('이 브라우저에 저장한 원본이 없습니다. 다른 강의를 선택하거나 보호자에게 원본을 다시 준비해 달라고 요청하세요.');
        const key=await crypto.subtle.importKey('raw',unhex(data.media_key),'AES-GCM',false,['decrypt']);
        const bytes=await crypto.subtle.decrypt({name:'AES-GCM',iv:encrypted.iv},key,await encrypted.blob.arrayBuffer());
        state.videoUrl=URL.createObjectURL(new Blob([bytes],{type:encrypted.type}));state.linkedPlaybackKind='local';
        el('linked-playback-note').textContent='보호자가 저장에 동의한 브라우저 원본입니다. 수강 중 서버로 다시 전송하지 않습니다.';el('linked-playback-note').classList.remove('hidden');
        const video=el('lecture-video');video.autoplay=false;video.pause();video.src=state.videoUrl;video.classList.remove('hidden');el('lecture-youtube').classList.add('hidden');el('video-placeholder').classList.add('hidden');
        video.addEventListener('loadedmetadata',()=>seekTo(data.progress.position_ms||0),{once:true});
      }else if(['youtube','direct'].includes(data.playback.kind)) {
        state.pendingLinkResult={...data.playback,playback_kind:data.playback.kind,analysis_status:'saved'};
        try{await setupLinkPlayback(state.pendingLinkResult,{positionMs:data.progress.position_ms||0});}catch(e){feedback('영상 연결이 지연됩니다. 재생을 다시 시도하거나 지문·질문 기능을 사용하세요.');}
      }else {
        el('lecture-video').classList.add('hidden');el('lecture-youtube').classList.add('hidden');el('video-placeholder').classList.remove('hidden');document.querySelector('#video-placeholder strong').textContent='텍스트 학습자료';document.querySelector('#video-placeholder p').textContent='원본 영상 없이 지문·핵심·질문 기능을 사용할 수 있습니다.';el('linked-playback-note').textContent='텍스트 학습자료입니다. 영상 분석을 실행한 것으로 표시하지 않습니다.';
      }
      try{localStorage.setItem('sullivan-last-'+ui.user.id,id);}catch{}
      el('command-surface').setAttribute('aria-label',`${data.title}. 수강 중 빠른 명령`);syncPlayback();focusFirst('watch',ticket);
    } catch(e){ui.lectureId=null;current=null;state.snapshot=null;state.session=null;show('portal-home');await loadStudent();error(e.message);}finally{opening=false;ui.restoring=false;}
  }
  function selectPanel(id) {
    $$('.view-panel').forEach(n=>n.classList.toggle('hidden',n.id!==id));
    $$('[data-learn-panel]').forEach(n=>{const match=n.dataset.learnPanel===id && (!n.dataset.purpose||n.dataset.purpose===focusedPurpose);if(match)n.setAttribute('aria-current','page');else n.removeAttribute('aria-current');});
    $$('.nav-button').forEach(n=>{n.classList.toggle('active',n.dataset.panel===id);n.setAttribute('aria-pressed',String(n.dataset.panel===id));});
  }
  async function purpose(which,focus=true) {
    if(!state.snapshot||!ui.lectureId) {
      let last=null;try{last=localStorage.getItem('sullivan-last-'+ui.user.id);}catch{}
      if(last&&lectures.some(l=>l.id===last))await openLecture(last);
      if(!state.snapshot||!ui.lectureId){el('assigned-title').focus();return feedback('먼저 준비된 강의를 하나 골라 주세요.');}
    }
    if(which==='paragraph'&&!getParagraphs().length){show('agent-view');focusFirst('watch');return feedback('이 강의에는 지문이 없습니다. 듣던 위치는 그대로입니다.');}
    stopAllPlaybackAndSpeech({announceStop:false});
    if(originMs===null){originMs=getCurrentPlaybackMs();el('learner-return').disabled=false;}
    show('agent-view');
    focusedPurpose=which;
    const panel=which==='question'?'chat-panel':'passage-panel';selectPanel(panel);
    el('passage-panel').dataset.purpose=which;
    if(focus)focusFirst(which);
  }
  function showHelp(first=false) {
    let box=el('onboarding-card');
    if(!box){
      box=node('section',undefined,{id:'onboarding-card',className:'portal-surface'});
      const h=node('h2','사용법');h.tabIndex=-1;h.id='onboarding-title';h.setAttribute('aria-describedby','onboarding-copy');
      const copy=node('div',undefined,{id:'onboarding-copy'}),list=node('ul');
      const instructions=[
        '버튼 이동: Tab은 다음, Shift만 눌렀다 떼면 이전으로 이동합니다. Shift+Tab도 이전입니다. 글자를 입력할 때 Shift는 대문자나 문자 선택에 그대로 사용합니다.',
        '강의 고르기: 강의 듣기에서 제목을 골라 Enter 또는 Space로 여세요. 영상이 있으면 재생 버튼에서 시작합니다. 왼쪽 방향키는 10초 전, 오른쪽은 10초 앞으로 이동합니다. 입력칸에서는 글자 이동에 사용합니다. 영상 내부 조작은 건너뛰고 앱 버튼으로 이동합니다.',
        '빠른 명령: 빠른 명령 영역으로 이동해 Space를 길게 누른 채 말하고 떼면 실행합니다. 두 번은 영상과 음성 중지, 세 번은 타자 명령입니다.',
        '타자 입력: Space는 띄어쓰기, Enter는 전송, Esc는 취소입니다.',
        '지문·문단 듣기, 원하는 내용 찾기, 질문하기도 직접 선택할 수 있습니다.'
      ];
      instructions.forEach(text=>list.append(node('li',text)));copy.append(list);box.append(h,copy);
      const done=button('사용법 확인 완료',async()=>{
        done.disabled=true;box.setAttribute('aria-busy','true');
        // Move once in the key gesture. Saving later must not steal focus.
        if(ui.lectureId&&state.snapshot){show('agent-view');focusFirst('watch');}else focusFirst('home');
        try {await send('/onboarding',{});ui.user.onboarded=1;box.remove();}
        catch(error){done.disabled=false;box.removeAttribute('aria-busy');throw error;}
      });
      done.id='onboarding-done';done.setAttribute('aria-describedby','onboarding-copy');box.append(done);
      el('portal-home-help').before(box);
    }
    focusFirst('help');
    if(ui.focusVoice&&!ui.readerMode)SullivanFocusVoice.message(box.querySelector('#onboarding-copy').textContent);
    // The focused confirmation describes the guide; app speech uses one channel.
  }
  function syncPlayback() {
    const held=SullivanFocusVoice.holdsPlayback(),playing=isPlaybackRunning()||held;el('learner-play').textContent=playing?'강의 일시정지':'강의 재생';
    const label=current?.playback.kind==='none'?'원본 영상 없는 자료입니다. 지문·핵심·질문 기능을 이용하세요.':state.snapshot?(held?'버튼 안내를 위해 잠시 정지합니다. 안내가 끝나면 이어 듣습니다.':playing?'강의 재생 중':'강의 일시정지. 재생 버튼으로 이어 들으세요.'):'강의를 먼저 선택하세요.';
    if(el('learner-playback-state').textContent!==label)el('learner-playback-state').textContent=label;
  }
  async function play() {
    if(!state.snapshot)return feedback('먼저 강의를 선택하세요.');
    const playing=isPlaybackRunning()||SullivanFocusVoice.holdsPlayback();SullivanFocusVoice.cancel();
    if(playing){pausePlayback();return syncPlayback();}
    try {
      if(state.linkedPlaybackKind==='youtube') {if(!state.youtubePlayer?.playVideo)throw new Error();state.youtubePlayer.playVideo();}
      else {if(!el('lecture-video').getAttribute('src'))throw new Error();await el('lecture-video').play();}
    }catch{feedback('영상을 재생할 수 없습니다. 지문·핵심 탐색을 이용하거나 연결 뒤 다시 시도하세요.');}
    syncPlayback();
  }
  async function saveProgress() {
    if(ui.user?.role!=='student'||!ui.lectureId||!state.snapshot||ui.restoring)return;
    const ident=ui.lectureId;
    const payload={position_ms:Math.round(getCurrentPlaybackMs()),bookmarks:state.bookmarks.map(b=>({...b})),underlined:[...state.underlinedParagraphIds],note:el('learner-note').value};
    savePromise=savePromise.catch(()=>{}).then(async()=>{
      try{await send('/lectures/'+ident+'/progress',payload,'PUT');el('progress-state').textContent='학습 위치와 기록 저장됨';}
      catch{el('progress-state').textContent='기록을 저장하지 못했습니다. 연결을 확인한 뒤 다시 저장하세요.';}
    });
    await savePromise;
  }
  function moveLesson(delta) {
    seekRelative(delta,{announceMove:false});
    const message=`${delta<0?'뒤로':'앞으로'} 10초 이동했습니다.`;
    if(ui.focusVoice&&!ui.readerMode)SullivanFocusVoice.message(message);else announce(message);
  }
  async function mediaStore(id,value,mode='readwrite') {
    return new Promise((resolve,reject)=>{const r=indexedDB.open('sullivan-encrypted-media',1);r.onupgradeneeded=()=>r.result.createObjectStore('media');r.onerror=()=>reject(r.error);r.onsuccess=()=>{const d=r.result,t=d.transaction('media',mode),store=t.objectStore('media');const q=value===undefined?store.get(id):value===null?store.delete(id):store.put(value,id);let result;q.onsuccess=()=>{result=q.result;};t.oncomplete=()=>{d.close();resolve(result);};t.onerror=()=>{d.close();reject(t.error);};t.onabort=()=>{d.close();reject(t.error||new Error('브라우저 저장을 완료하지 못했습니다.'));};};});
  }
  const mediaGet=id=>mediaStore(id,undefined,'readonly'),mediaRemove=id=>mediaStore(id,null);
  const unhex=s=>new Uint8Array(s.match(/../g).map(v=>parseInt(v,16)));
  async function publish(e) {
    e.preventDefault();const submit=e.submitter||el('publish-form').querySelector('button[type="submit"]');
    if(submit.disabled)return;submit.disabled=true;
    const guardian=ui.user?.id;
    try {
      const assignments=checked(el('publish-students'));if(!assignments.length)throw new Error('배정할 학생을 선택해 주세요.');
      if(state.localVideoFile&&!el('publish-store').checked)throw new Error('파일 강의를 전달하려면 브라우저 원본 저장에 별도로 동의해 주세요. 기본으로 저장하지 않습니다.');
      const result=await send('/lectures',{title:el('publish-title-input').value,subject:el('publish-subject').value,students:assignments,session_id:state.session.session_id,sample_id:state.isSample?state.activeSampleId:null,playback:state.localVideoFile?{kind:'local',name:state.localVideoFile.name}:state.pendingLinkResult?{kind:state.pendingLinkResult.playback_kind,normalized_url:state.pendingLinkResult.normalized_url}:{kind:'none'},store_local_media:!!state.localVideoFile,ready:!state.localVideoFile,chat_consent:el('publish-chat').checked,access_code:el('publish-chat').checked?el('demo-access-code').value:undefined});
      if(state.localVideoFile){const iv=crypto.getRandomValues(new Uint8Array(12));const key=await crypto.subtle.importKey('raw',unhex(result.media_key),'AES-GCM',false,['encrypt']);const bytes=await crypto.subtle.encrypt({name:'AES-GCM',iv},key,await state.localVideoFile.arrayBuffer());await mediaStore(result.id,{iv,blob:new Blob([bytes]),type:state.localVideoFile.type});}
      if(!result.ready)await request('/lectures/'+result.id+'/ready',{method:'PUT'});
      if(ui.user?.id!==guardian)return;
      let refreshed=true;try{await home();}catch{show('guardian-dashboard');refreshed=false;}
      feedback('강의 준비와 배정을 완료했습니다. 로그아웃한 뒤 학생 계정으로 로그인해 주세요.'+(refreshed?'':' 배정은 저장됐지만 준비실 목록 갱신은 다시 시도해 주세요.'),true);
    }catch(e){error(e.message);}finally{submit.disabled=false;}
  }
  function rememberSearch() {if(originMs===null){originMs=getCurrentPlaybackMs();el('learner-return').disabled=false;}}
  async function command(value,source='text') {
    const text=String(value||'').trim();if(!text)return feedback('명령을 입력해 주세요.');
    if(/^(이거|그거|설명해줘|다시 설명해줘|비교해줘|찾아줘)$/.test(text))return typeDialog('어떤 개념이나 문단을 원하나요? 이름이나 문단 번호를 함께 입력해 주세요.');
    if(/사용법|단축키.*알려/.test(text)){await home();showHelp();return;}
    if(/원래.*(곳|위치)|듣던.*(곳|위치)/.test(text)){el('learner-return').click();return;}
    if(/학습 기록|북마크|메모/.test(text)){records();return;}
    if(/10초.*(전|뒤로)|뒤로.*10초/.test(text)){seekRelative(-10000);return;}
    if(/10초.*(후|앞으로)|앞으로.*10초/.test(text)){seekRelative(10000);return;}
    const intent=SullivanVoiceCommands.classify(text);
    if(intent.type==='home'||intent.type==='save_home'){await home();return;}
    if(intent.type==='play'){if(!isPlaybackRunning())await play();return;}
    if(intent.type==='pause'){stopAllPlaybackAndSpeech();return;}
    if(intent.type==='sample'||intent.type==='saved'||intent.type==='free_mode'||intent.panelId==='evidence-panel')return feedback('배정된 강의는 강의 목록에서 고를 수 있습니다. 준비·관리는 보호자 기능입니다.');
    if(intent.type==='paragraph'){await purpose('paragraph',false);if(getParagraphs().length){if(/밑줄.*(표시|해제)|문단.*밑줄/.test(text)&&!/(듣|읽|낭독)/.test(text)){const p=SullivanPassages.findByOrdinal?.(getParagraphs(),text)||getParagraphs().find(p=>p.paragraph_id===state.currentParagraphId)||getParagraphs()[0];const wantsOff=/해제/.test(text);if(state.underlinedParagraphIds.has(p.paragraph_id)!==!wantsOff)toggleParagraphUnderline(p.paragraph_id);}else runParagraphCommand(text);}return;}
    if(intent.type==='concept'||/찾아|검색/.test(text)){rememberSearch();await purpose('search',false);el('navigation-command').value=text.replace(/핵심|키워드|개념|찾아\s*줘|찾아|검색해\s*줘|검색|해줘/g,'').trim()||'전체 흐름';el('navigation-form').requestSubmit();return;}
    if(/^(?:결과\s*)?[0-9]+(?:번)?(?:\s*선택)?$/.test(text)) {
      const i=Number(text.match(/[0-9]+/)[0])-1;const matches=state.conceptSearchResults||getConcepts();if(matches[i]){playConceptSequence(matches[i]);return;}return feedback('선택할 결과 번호를 다시 알려 주세요.');
    }
    if(intent.type==='describe'){$('#describe-now').click();return;}
    if(intent.type==='panel'){selectPanel(intent.panelId);return;}
    if(intent.type==='chat')await purpose('question',false);
    if(intent.type==='summary_audio' && ui.readerMode){readSummaryGuide();return;}
    // Voice and text enter the same existing intent/action engine.
    await executeGlobalVoiceCommand(text,wasPlaying,{source});
  }
  async function records() {
    if(!state.snapshot||!ui.lectureId){let last=null;try{last=localStorage.getItem('sullivan-last-'+ui.user.id);}catch{}if(last&&lectures.some(l=>l.id===last))await openLecture(last);}
    if(!state.snapshot)return feedback('강의를 고른 뒤 학습 기록을 열 수 있습니다.');
    show('agent-view');
    el('learning-records').classList.remove('hidden');focusFirst('records');
  }
  function stopVoice() {if(recognition){recognition.onend=null;recognition.onerror=null;try{recognition.abort();}catch{}}recognition=null;el('space-voice-overlay').classList.add('hidden');}
  function typeDialog(message='명령을 입력하고 Enter로 보내세요. Esc로 취소합니다.') {
    stopVoice();lastFocus=document.activeElement;pausePlayback();
    const dialog=el('text-command-dialog');dialog.classList.remove('hidden');if(!dialog.open)dialog.showModal();
    el('text-command-status').textContent=message;el('text-command-input').value='';el('text-command-input').focus();
  }
  function closeDialog(resume=false) {el('text-command-dialog').close();el('text-command-dialog').classList.add('hidden');if(resume&&wasPlaying)resumePlayback();if(lastFocus?.isConnected&&lastFocus.getClientRects().length)lastFocus.focus();else el('command-surface').focus();}
  function finishVoice() {
    if(finalized)return;finalized=true;const text=transcript;stopVoice();
    if(!text)return typeDialog('말을 인식하지 못했습니다. 같은 명령을 타자로 입력해 주세요.');
    command(text,'voice').then(()=>{if(!el('text-command-dialog').open&&!el('agent-view').classList.contains('hidden'))el('command-surface').focus();}).catch(e=>error(e.message));
  }
  function startVoice() {
    pausePlayback();released=false;finalized=false;transcript='';
    const R=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(!R)return typeDialog('마이크 음성 입력을 사용할 수 없습니다. 타자로 같은 명령을 입력해 주세요.');
    playSpaceVoiceReadyChime();recognition=new R();recognition.lang='ko-KR';recognition.interimResults=false;
    recognition.onstart=()=>{if(released){try{recognition.stop();}catch{}}};
    recognition.onresult=e=>{transcript=[...e.results].map(r=>r[0].transcript).join(' ');if(released)finishVoice();};
    recognition.onerror=()=>{finalized=true;typeDialog('마이크를 사용할 수 없거나 인식에 실패했습니다. 타자 입력으로 계속하세요.');};
    recognition.onend=()=>{if(released)finishVoice();};
    el('space-voice-overlay').classList.remove('hidden');el('space-voice-title').textContent='말씀하세요';el('space-voice-text').textContent='키를 떼면 요청을 처리합니다.';
    try{recognition.start();}catch{typeDialog('마이크를 시작하지 못했습니다. 타자로 입력해 주세요.');}
  }
  const gesture=SullivanSpaceGesture.create({hold:startVoice,release:()=>{ui.gesturePending=false;released=true;if(recognition){try{recognition.stop();}catch{}setTimeout(finishVoice,1500);}},taps:count=>{ui.gesturePending=false;if(count>=3)typeDialog();else if(count===2){stopVoice();stopAllPlaybackAndSpeech();}else if(wasPlaying)resumePlayback();},cancel:()=>{ui.gesturePending=false;stopVoice();}});
  el('command-surface').addEventListener('keydown',e=>{if(e.code!=='Space')return;e.preventDefault();if(e.repeat)return;if(!ui.gesturePending) {wasPlaying=isPlaybackRunning();ui.gesturePending=true;}pausePlayback();gesture.down();});
  document.addEventListener('keyup',e=>{if(e.code!=='Space'||!ui.gesturePending)return;e.preventDefault();gesture.up();});
  el('command-surface').addEventListener('blur',()=>{if(!recognition&&!el('text-command-dialog').open)gesture.cancel();});
  // Own the native modal handlers, avoiding the legacy custom-dialog path.
  el('text-command-form').addEventListener('submit',e=>{e.preventDefault();e.stopImmediatePropagation();const value=el('text-command-input').value.trim();if(!value){el('text-command-status').textContent='명령을 입력해 주세요.';return;}closeDialog();command(value,'text').catch(e=>error(e.message));},true);
  el('close-text-command').addEventListener('click',e=>{e.stopImmediatePropagation();closeDialog(true);},true);
  el('text-command-dialog').addEventListener('cancel',e=>{e.preventDefault();closeDialog(true);});
  el('text-command-dialog').addEventListener('keydown',e=>{
    if(e.key==='Escape'){e.stopImmediatePropagation();e.preventDefault();closeDialog(true);}
    else if(e.key==='Tab'){
      const controls=[...el('text-command-dialog').querySelectorAll('input:not([disabled]),button:not([disabled]),textarea:not([disabled]),select:not([disabled]),[tabindex="0"]')].filter(n=>n.getClientRects().length);
      const first=controls[0],last=controls.at(-1);
      if(first&&((e.shiftKey&&document.activeElement===first)||(!e.shiftKey&&document.activeElement===last))){e.preventDefault();(e.shiftKey?last:first).focus();}
    }
  },true);
  openTextCommandDialog=typeDialog;
  closeTextCommandDialog=()=>closeDialog();
  async function saveSpeechPreferences() {
    if(ui.user?.role!=='student')return;
    const prefs={focus_voice:ui.focusVoice,reader_mode:ui.readerMode};
    ui.user.settings={...ui.user.settings,...prefs}; // Apply immediately; opening a lecture must not reset this choice.
    try{await send('/preferences',prefs,'PUT');}
    catch{el('focus-voice-status').textContent='현재 화면에는 적용했습니다. 설정 저장에 실패했다면 서버를 재시작한 뒤 다시 선택해 주세요.';}
  }
  function syncChatChannel(){el('chat-log').setAttribute('aria-live',el('auto-speak-chat').checked&&!ui.readerMode?'off':'polite');}
  el('auto-speak-chat').addEventListener('change',syncChatChannel);
  for(const id of ['voice-command','paragraph-voice-command','chat-voice']){el(id).textContent='타자';el(id).setAttribute('aria-label','타자 명령 입력');}
  for(const id of ['voice-command','paragraph-voice-command','chat-voice'])el(id).addEventListener('click',e=>{e.stopImmediatePropagation();lastFocus=e.currentTarget;wasPlaying=isPlaybackRunning();pausePlayback();typeDialog('Space 길게 명령은 빠른 명령 영역에서 사용할 수 있습니다. 이곳에서는 같은 명령을 타자로 입력해 주세요.');},true);
  el('reader-mode').addEventListener('change',()=>{ui.readerMode=el('reader-mode').checked;if(ui.readerMode){ui.focusVoice=false;el('focus-voice').checked=false;SullivanFocusVoice.cancel();}stopAllPlaybackAndSpeech({announceStop:false});syncChatChannel();saveSpeechPreferences();});
  el('focus-voice').addEventListener('change',()=>{if(el('focus-voice').checked&&(!('speechSynthesis' in window)||!('SpeechSynthesisUtterance' in window))){el('focus-voice').checked=false;ui.focusVoice=false;feedback('이 브라우저는 앱 음성 안내를 지원하지 않습니다. 외부 스크린리더를 사용해 주세요.',true);return;}ui.focusVoice=el('focus-voice').checked;if(ui.focusVoice){ui.readerMode=false;el('reader-mode').checked=false;SullivanFocusVoice.read(document.activeElement);}else SullivanFocusVoice.cancel();syncChatChannel();saveSpeechPreferences();});
  el('focus-voice-test').addEventListener('click',()=>{ui.focusVoice=true;ui.readerMode=false;el('focus-voice').checked=true;el('reader-mode').checked=false;SullivanFocusVoice.test();syncChatChannel();saveSpeechPreferences();});
  el('settings-reader').addEventListener('change',()=>{if(el('settings-reader').checked)el('settings-focus-voice').checked=false;});
  el('settings-focus-voice').addEventListener('change',()=>{if(el('settings-focus-voice').checked)el('settings-reader').checked=false;});
  // Reuse existing reading preferences, with a short student-facing subset visible.
  for(const id of ['speech-rate','speech-volume','auto-narration']){const n=el(id);el('student-reading-preferences').append(n.closest('label'));}
  el('login-role-student').addEventListener('click',()=>chooseLogin('student'));
  el('login-role-guardian').addEventListener('click',()=>chooseLogin('guardian'));
  el('login-focus-voice').addEventListener('change',()=>{ui.loginVoice=el('login-focus-voice').checked;SullivanFocusVoice.cancel();if(ui.loginVoice)SullivanFocusVoice.message('로그인 앱 음성 안내를 켰습니다.');else el('login-voice-status').textContent='로그인 앱 음성 안내를 껐습니다. 학생 로그인을 선택하거나 로그인 음성 시작·시험을 누르면 다시 켤 수 있습니다.';});
  el('login-voice-test').addEventListener('click',()=>{if(ui.loginRole==='guardian')return;ui.loginVoice=true;el('login-focus-voice').checked=true;SullivanFocusVoice.message('로그인 음성 안내 시험입니다. Tab 키로 학생 로그인이나 보호자 로그인을 선택하세요.');});
  el('portal-login-form').addEventListener('submit',async e=>{e.preventDefault();const b=el('login-submit');b.disabled=true;try{const user=await send(setup?'/setup':'/login',{username:el('login-username').value,password:el('login-password').value,name:el('setup-name').value,role:setup?'guardian':ui.loginRole});setup=false;await authenticated(user);}catch(e){error(e.message);}finally{b.disabled=false;}});
  el('portal-logout').addEventListener('click',async()=>{await saveProgress();await send('/logout',{});await signedOut();});
  el('student-create').addEventListener('submit',async e=>{e.preventDefault();try{await send('/students',Object.fromEntries(new FormData(e.target)));e.target.reset();await loadGuardian();feedback('학생 계정을 만들었습니다. 학생에게 로그인 이름과 비밀번호를 직접 알려 주세요.',true);}catch(e){error(e.message);}});
  el('student-settings').addEventListener('submit',async e=>{e.preventDefault();try{await send('/students/'+el('settings-student').value+'/settings',{auto_description:el('settings-auto').checked,problem_mode:el('settings-problem').checked,reader_mode:el('settings-reader').checked,focus_voice:el('settings-focus-voice').checked,speech_rate:Number(el('settings-rate').value),speech_volume:Number(el('settings-volume').value),reset_onboarding:el('settings-reset').checked},'PUT');await loadGuardian();feedback('학생 기본 설정을 저장했습니다.',true);}catch(e){error(e.message);}});
  el('settings-student').addEventListener('change',()=>{fillSettings();renderGuardianLectures();});
  el('guardian-prepare').addEventListener('click',prepare);
  el('sample-assign-form').addEventListener('submit',assignSample);
  el('guardian-science').addEventListener('click',()=>openSampleSession('science'));
  el('guardian-history').addEventListener('click',()=>openSampleSession('history'));
  $$('[data-guardian-home]').forEach(b=>b.addEventListener('click',home));
  el('publish-form').addEventListener('submit',publish);
  el('student-list-open').addEventListener('click',()=>openLectureList().catch(e=>error(e.message)));
  $$('[data-purpose]').forEach(b=>b.addEventListener('click',()=>purpose(b.dataset.purpose).catch(e=>error(e.message))));
  $$('[data-learn-panel]:not([data-purpose])').forEach(b=>b.addEventListener('click',()=>{selectPanel(b.dataset.learnPanel);focusPanel(b.dataset.learnPanel);}));
  el('learner-home').addEventListener('click',home);el('learner-play').addEventListener('click',play);
  document.addEventListener('keydown',e=>{
    if(!['ArrowLeft','ArrowRight'].includes(e.key)||e.defaultPrevented||e.altKey||e.ctrlKey||e.metaKey||e.shiftKey||e.isComposing||
       ui.user?.role!=='student'||el('agent-view').classList.contains('hidden')||!state.snapshot||
       el('learner-play').disabled||document.querySelector('dialog[open],[aria-modal="true"]:not(.hidden)')||
       e.target.closest('input,textarea,select,[contenteditable]:not([contenteditable="false"]),[role="textbox"],[role="slider"],[role="spinbutton"],[role="combobox"]'))return;
    e.preventDefault();moveLesson(e.key==='ArrowLeft'?-10000:10000);
  });
  el('learner-describe').addEventListener('click',()=>el('describe-now').click());el('learner-stop').addEventListener('click',()=>{stopVoice();stopAllPlaybackAndSpeech();});
  el('learner-return').addEventListener('click',()=>{if(originMs===null)return;stopAllPlaybackAndSpeech({announceStop:false});seekTo(originMs);originMs=null;el('learner-return').disabled=true;selectPanel('watch-panel');focusFirst('watch');feedback('원래 듣던 위치로 돌아왔습니다. 재생 버튼으로 이어 들으세요.');});
  for(const id of ['student-help','learner-help'])el(id).addEventListener('click',async()=>{await home();showHelp();});
  for(const id of ['student-records','learner-records'])el(id).addEventListener('click',()=>records().catch(e=>error(e.message)));
  el('records-close').addEventListener('click',()=>{el('learning-records').classList.add('hidden');el('learner-records').focus();});
  $$('[data-record-view]').forEach(b=>b.addEventListener('click',()=>{selectPanel(b.dataset.recordView);focusPanel(b.dataset.recordView);}));
  el('learner-note').addEventListener('input',()=>{clearTimeout(progressTimer);progressTimer=setTimeout(saveProgress,600);});
  $$('.nav-button').forEach(b=>b.addEventListener('click',()=>{selectPanel(b.dataset.panel);focusPanel(b.dataset.panel);}));
  document.addEventListener('click',e=>{if(e.target.closest('[data-underline-paragraph],#add-bookmark'))setTimeout(saveProgress,0);});
  el('navigation-form').addEventListener('submit',rememberSearch,true);
  document.addEventListener('click',e=>{if(e.target.closest('.concept-speak'))rememberSearch();},true);
  for(const event of ['play','pause','ended'])el('lecture-video').addEventListener(event,()=>{syncPlayback();saveProgress();});
  el('lecture-video').addEventListener('error',()=>{if(ui.user?.role==='student'&&state.snapshot)feedback('영상 파일을 재생하지 못했습니다. 지문이나 질문 기능으로 계속 학습할 수 있습니다.');});
  setInterval(()=>{if(ui.user?.role==='student'&&!el('agent-view').classList.contains('hidden')){syncPlayback();if(isPlaybackRunning())saveProgress();}},5000);
  document.addEventListener('visibilitychange',()=>{if(document.hidden){gesture.cancel();saveProgress();}});
  document.querySelector('.brand').addEventListener('click',e=>{e.preventDefault();home();});
  // Analysis modal: trap its single action, allow Escape, restore context on cancel.
  let analysisWasOpen=false;
  new MutationObserver(()=>{
    const modal=el('analysis-overlay'),busy=!modal.classList.contains('hidden');
    for(const id of ['setup-view','guardian-dashboard','portal-home','portal-login','agent-view'])el(id).inert=busy;
    document.querySelector('.topbar').inert=busy;document.querySelector('.skip-link').inert=busy;document.querySelector('.app-runtime').inert=busy;
    if(busy&&!analysisWasOpen){focusFirst('analysis');}
    if(!busy&&analysisWasOpen){const previous=state.analysisFocus;state.analysisFocus=null;if(modal.contains(document.activeElement)&&previous?.isConnected&&!previous.disabled&&previous.getClientRects().length)previous.focus();}
    analysisWasOpen=busy;
  }).observe(el('analysis-overlay'),{attributes:true,attributeFilter:['class']});
  el('analysis-overlay').addEventListener('keydown',e=>{
    if(e.key==='Escape'){e.preventDefault();e.stopImmediatePropagation();el('cancel-analysis-wait').click();}
    else if(e.key==='Tab'){e.preventDefault();el('cancel-analysis-wait').focus();}
  },true);
  (async()=>{const initialFocus=focusTicket();try{
    const status=await request('/status');ui.compatible=status.build===requiredBuild;
    el('runtime-info').textContent=ui.compatible?`학습 책상 화면 4 / 학생·보호자 로컬 r2 / ${location.host} / 실행 ${status.instance}`:'실행 중인 서버가 이전 버전입니다.';
    setup=status.needs_setup;ui.loginNative=Boolean(status.system_login_voice);ui.localVoiceProfile=ui.loginNative?status.system_login_voice_profile||null:null;loginUI();
    if(!ui.compatible){error('화면과 서버 버전이 다릅니다. Sullivan-AI-student-guardian-local의 실행기를 다시 시작한 뒤 새로고침하세요. 계정을 다시 만들 필요는 없습니다.');return;}
    let user=null;try{user=await request('/me');}catch{}
    if(user)await authenticated(user);else {ui.loginReady=true;focusFirst(setup?'setup':'login',initialFocus);}
  }catch(e){error('로컬 서버에 연결하지 못했습니다. 실행기를 확인한 뒤 새로고침해 주세요.');}})();
  Object.assign(ui,{home,lectureReady,error,feedback,saveProgress,command,openLecture,showHelp,syncPlayback});return ui;
})();
