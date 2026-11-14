import {request, signIn} from './client.js';
import {$, node, button, bindForm, status, task, boot} from './ui.js';

let generation = 0;
let students = [], lectures = [], preparation = null, editing = null, managing = null;
let order = [], poll = null, jobsFingerprint = '';
let preparations = [];
const preparationLabels = {queued: '접수', running: '진행 중', completed: '준비 완료', failed: '실패', interrupted: '중단'};
const settingDefaults = {auto_description: true, problem_mode: true, speech_rate: .95, speech_volume: .9, reader_mode: false, focus_voice: false};
let jobStates = new Map(), pollError = '';
let managementGeneration = 0;
let preparationGeneration = 0;
let unlinking = null;
let previewUrl=null,previewCaptionUrl=null,previewFileGeneration=0,previewQuestion=0;
let editRevision=0, refreshRevision=0, preparationListRevision=0;
const api = '/extension/v1/guardian';
const checked = id => [...$(id).querySelectorAll('input:checked')].map(input => input.value);

function options(id, selected = $(id).value) {
  $(id).replaceChildren(...students.map(s => node('option', s.name, {value: s.id})));
  if (students.some(s => s.id === selected)) $(id).value = selected;
}
function choices(id, selected = checked(id)) {
  $(id).querySelectorAll('label').forEach(label => label.remove());
  for (const student of students) {
    const label = node('label', undefined, {className: 'check'});
    label.append(node('input', undefined, {type: 'checkbox', value: student.id, checked: selected.includes(student.id)}),
      document.createTextNode(student.name));
    $(id).append(label);
  }
}
function selection(id) {
  const ids = checked(id);
  if (!ids.length) { $(id).focus(); throw new Error('배정할 학생을 한 명 이상 선택하세요.'); }
  return ids;
}

function renderSteps() {
  const hasStudents = students.length > 0;
  const prepared = preparations.some(job => job.state === 'completed');
  const hasLectures = lectures.length > 0 || prepared;
  const studentIds = new Set(students.map(student => student.id));
  const assigned = lectures.some(lecture => lecture.ready && lecture.students.some(id => studentIds.has(id)));
  const customized = students.some(student => Object.entries(settingDefaults).some(([key,value]) => (student.settings?.[key] ?? value) !== value));
  for (const [id, state] of [['student',hasStudents?'완료':'할 차례'],
    ['lecture',hasLectures?'완료':hasStudents?'할 차례':'아직'],
    ['assignment',assigned?'완료':hasStudents&&hasLectures?'할 차례':'아직'],
    ['settings',customized?'완료':'기본값']]) $('setup-'+id).textContent = state;
  $('setup-assignment-link').href = prepared && !lectures.length ? '#preparations-title' : '#lectures-title';
  const next = !hasStudents ? '학생용 확장에 가입한 학생과 일회용 코드로 연결하세요.'
    : !hasLectures ? '강의를 준비하고 결과를 확인하세요.'
    : !assigned ? '준비 결과나 강의 목록에서 학생을 선택해 배정하고 공개하세요.'
    : '학생별 기본 설정을 확인하세요. 학생은 학생용 확장에서 배정된 강의를 엽니다. 파일 강의는 같은 원본도 별도로 전달하세요.';
  const message = `다음 단계: ${next}`;
  if ($('next-step').textContent !== message) $('next-step').textContent = message;
}

async function refresh() {
  const ticket = generation, revision = ++refreshRevision;
  const results = await Promise.all([request('/local/students'), request('/local/lectures')]);
  if (ticket !== generation || revision !== refreshRevision) return;
  [students, lectures] = results;
  $('connection-students').replaceChildren(...students.map(student=>{
    const item=node('li');item.append(node('p',student.name),button(`${student.name} 연결 해제`,()=>{
      unlinking=student.id;$('guardian-unlink-question').textContent=`${student.name} 학생과 연결을 해제할까요? 이 보호자의 강의 배정과 이후 기록 조회를 중단하고 학생 개인 기록은 보존합니다.`;
      $('guardian-unlink-confirm').hidden=false;$('guardian-unlink-yes').focus();
    }));return item;
  }));
  if(managing && !students.some(s=>s.id===managing)){managing=null;$('management-detail').hidden=true;$('progress-summary').replaceChildren();$('lecture-order').replaceChildren();}
  $('students').replaceChildren(...students.map(s => node('li', `${s.name} (${s.username})`)));
  if (!students.length) $('students').append(node('li', '아직 연결된 학생이 없습니다. 학생 계정을 먼저 만들어 주세요.'));
  options('student-choice'); options('manage-student'); choices('publish-students');
  $('assign-submit').disabled = !students.length;
  $('load-management').disabled = !students.length;
  $('lectures').replaceChildren(...lectures.map(l => {
    const item = node('li');
    item.append(node('p', `${l.title} · ${l.ready ? '공개 완료' : '비공개'} · 배정 학생 ${l.students.length}명`),
      button(`${l.title} 배정 수정`, () => edit(l.id)));
    if (!l.ready && l.students.length) item.append(button(`${l.title} 학생에게 공개`, async () => {
      await request(`/local/lectures/${l.id}/ready`, {method: 'PUT'}); await refresh();
      $('lectures-title').focus(); status('강의를 학생에게 공개했습니다.');
    }));
    return item;
  }));
  if (!lectures.length) $('lectures').append(node('li', '아직 준비한 강의가 없습니다.'));
  renderSteps();
}

async function refreshPreparations() {
  const ticket = generation, revision = ++preparationListRevision;
  const jobs = await request(`${api}/preparations`);
  if (ticket !== generation || revision !== preparationListRevision) return;
  if (pollError) { pollError = ''; $('connection-status').textContent = '서버 연결이 복구됐습니다.'; }
  const fingerprint = JSON.stringify(jobs);
  if (fingerprint === jobsFingerprint) return;
  jobsFingerprint = fingerprint;
  const changed = jobs.filter(job => jobStates.has(job.id) && jobStates.get(job.id) !== job.state && ['running', 'completed', 'failed', 'interrupted'].includes(job.state));
  if (changed.length) $('job-status').textContent = changed.map(job => `${job.title}: ${preparationLabels[job.state]}. ${job.message}`).join(' ');
  jobStates = new Map(jobs.map(job => [job.id, job.state]));
  preparations = jobs;
  renderSteps();
  $('preparation-counts').textContent = `전체 ${jobs.length}개 · ` + Object.entries(preparationLabels).map(([state,label]) => `${label} ${jobs.filter(job => job.state === state).length}개`).join(' · ');
  renderPreparations();
}

function renderPreparations() {
  const active = document.activeElement, focus = active?.dataset.job;
  const previous = [...$('preparations').querySelectorAll('button')].findIndex(control => control === active);
  const state = $('preparation-filter').value, query = $('preparation-search').value.trim().toLocaleLowerCase('ko-KR');
  const jobs = preparations.filter(job => (state === 'all' || state === 'active' && ['queued','running'].includes(job.state)
    || state === 'attention' && ['failed','interrupted'].includes(job.state) || job.state === state)
    && `${job.title} ${job.subject}`.toLocaleLowerCase('ko-KR').includes(query));
  const result = `${preparations.length}개 중 ${jobs.length}개 준비 작업이 표시됩니다.`;
  if ($('preparation-results').textContent !== result) $('preparation-results').textContent = result;
  $('preparations').replaceChildren(...jobs.map(job => {
    const item = node('article');
    item.append(node('h4', job.title), node('p', `${preparationLabels[job.state] || job.state}. ${job.message}`),
      node('p', `${job.subject} · 마지막 상태 확인 ${new Date(job.updated * 1000).toLocaleString('ko-KR')}`));
    const action = job.state === 'completed'
      ? button(`${job.title} 결과 확인·배정`, () => openPreparation(job.id))
      : ['failed', 'interrupted'].includes(job.state)
        ? button(`${job.title} 다시 준비`, () => {
          const form = $('prepare-form');form.reset();form.elements.title.value = job.title; form.elements.subject.value = job.subject;
          form.elements.source.value = job.source_kind === 'video' ? 'video' : job.source_kind === 'local' ? 'local' : job.source_kind === 'link' ? 'link' : 'materials';
          $('prepare-rights').checked = false; $('prepare-consent').checked = false;
          $('prepare-video').value = ''; $('material-files').value = '';
          clearMaterialValidation();syncSource();prepareStep=0;prepareStepView();form.elements.title.focus();
          status('자료와 동의를 다시 선택한 뒤 준비를 시작하세요. 이전 요청을 자동 재실행하지 않습니다.');
        }) : null;
    if (action) { action.dataset.job = job.id; item.append(action); }
    return item;
  }));
  if (!jobs.length) $('preparations').append(node('p', preparations.length ? '조건에 맞는 준비 작업이 없습니다. 상태나 검색어를 바꾸세요.' : '아직 준비 작업이 없습니다. 새 강의 준비에서 자료를 선택하세요.'));
  if (focus) {
    const controls = [...$('preparations').querySelectorAll('button')];
    (controls.find(control => control.dataset.job === focus) || controls[Math.min(Math.max(previous,0),controls.length-1)] || $('preparations-title')).focus();
  }
}
$('preparation-filter').addEventListener('change', renderPreparations);
$('preparation-search').addEventListener('input', renderPreparations);

async function openPreparation(id) {
  const ticket = generation;
  const selected = ++preparationGeneration;
  preparation = null; $('prepared-detail').hidden = true;
  const job = await request(`${api}/preparations/${id}`);
  if (ticket !== generation || selected !== preparationGeneration) return;
  preparation = job;
  $('prepared-title').textContent = `${job.title} 준비 결과`;
  const snapshot = job.snapshot;
  resetPreview();
  const box=$('prepared-preview');box.replaceChildren(node('p', snapshot.session.source_label),
    node('p', `자막 ${snapshot.transcript_segments.length}개, 지문 ${snapshot.passage?.paragraphs.length || 0}문단, 공개 가능한 화면 설명 ${snapshot.safe_description_count}개, 보류 ${snapshot.held_count}개.`),
    ...snapshot.review.core_summary.map(text => node('p', text)),
    ...(snapshot.passage?.paragraphs || []).map(p => node('p', p.sentences.map(s => s.text).join(' '))));
  const section=(title,texts)=>{const detail=node('details');detail.append(node('summary',title),...texts.map(t=>node('p',t)));if(!texts.length)detail.append(node('p','등록된 내용이 없습니다.'));box.append(detail);};
  const stamp=ms=>`${Math.floor(ms/60000)}분 ${Math.floor(ms/1000)%60}초`;
  section('강의 발화·자막',snapshot.transcript_segments.map(s=>`${stamp(s.start_ms)}. ${s.text}`));
  section('검증된 화면 설명',snapshot.visual_gaps.filter(g=>g.safe_to_speak&&g.confidence>=.72&&g.public_description&&!['HOLD','SKIP'].includes(g.action)&&!(snapshot.session.problem_mode&&g.kind==='answer')).map(g=>`${stamp(g.timestamp_ms)}. ${g.public_description}`));
  section('개념 탐색',snapshot.concept_index.map(c=>`${stamp(c.timestamp_ms)}. ${c.keyword}. 강사 설명: ${c.lecturer_point}. AI 설명: ${c.ai_explanation}. ${c.flow}`));
  for(const [title,key] of [['복습 핵심 구간','key_segments'],['화면에만 있는 정보','visual_only_information'],['강조 문장','highlighted_sentences']]){
    const detail=node('details');detail.append(node('summary',title));
    for(const entry of snapshot.review[key]||[]){detail.append(node('p',`${stamp(entry.timestamp_ms)}. ${entry.title}. ${entry.description}`),button(`${entry.title} 미리보기 위치로 이동`,()=>{if(!$('preview-video').src)throw new Error('같은 원본 파일을 먼저 연결하세요.');$('preview-video').pause();$('preview-video').currentTime=entry.timestamp_ms/1000;status(`${stamp(entry.timestamp_ms)} 위치로 이동했습니다.`);}));}box.append(detail);
  }
  const guide=snapshot.study_guide;
  section('학습 가이드',[guide.overview,...guide.concept_map,...guide.glossary.map(g=>`${g.term}: ${g.definition}`),...guide.recall_questions].filter(Boolean));
  section('설명 판단 근거',snapshot.visual_gaps.map(g=>`${stamp(g.timestamp_ms)}. ${g.action}. ${g.reason}`));
  const identity=job.playback;
  $('preview-playback').textContent=identity.kind==='local-reference'?`학생 원본 전달 필요: ${identity.name} (${identity.size_bytes}바이트). 학생에게 같은 파일을 전달하고 학생용 확장의 원본 파일 연결에서 선택하세요. 연결 전에도 준비된 자료를 읽을 수 있습니다.`:identity.normalized_url?'학생은 등록된 원본 주소를 열고 탭 연결을 허용하면 재생할 수 있습니다.':'원본 영상 주소가 없는 자료입니다. 학생은 영상 연결 없이 준비된 학습자료를 읽을 수 있습니다.';
  if(identity.normalized_url&&['http:','https:'].includes(new URL(identity.normalized_url).protocol))box.append(node('a','등록된 원본 주소 열기 (새 탭)',{href:identity.normalized_url,target:'_blank',rel:'noopener'}));
  choices('publish-students', []);
  $('publish-form').reset();
  $('prepared-detail').hidden = false;
  $('prepared-title').focus();
}

function resetPreview(){previewQuestion++;previewFileGeneration++;$('preview-video').pause();$('preview-video').removeAttribute('src');$('preview-video').querySelectorAll('track').forEach(t=>t.remove());$('preview-video').load();$('preview-video').hidden=true;if(previewUrl)URL.revokeObjectURL(previewUrl);if(previewCaptionUrl)URL.revokeObjectURL(previewCaptionUrl);previewUrl=previewCaptionUrl=null;$('preview-file').value='';$('preview-answer').textContent='';$('preview-question-form').reset();}
$('preview-export').addEventListener('click',()=>task($('preview-export'),async()=>{
  if(!preparation)throw new Error('준비 결과를 먼저 여세요.');const {snapshot,title}=preparation,g=snapshot.study_guide;
  const text=[`# ${title}`,'',...snapshot.review.core_summary,'','## 학습 개요',g.overview,'','## 개념 지도',...g.concept_map,'','## 핵심 용어',...g.glossary.map(x=>`${x.term}: ${x.definition}`),'','## 확인 질문',...g.recall_questions].join('\n');
  const url=URL.createObjectURL(new Blob([text],{type:'text/markdown;charset=utf-8'}));node('a','',{href:url,download:'sullivan-prepared-notes.md'}).click();setTimeout(()=>URL.revokeObjectURL(url),1000);status('준비된 학습 노트를 내보냈습니다.');
}));
$('preview-file').addEventListener('change',()=>task($('preview-file'),async()=>{
  const file=$('preview-file').files[0],selected=preparation,ticket=++previewFileGeneration;if(!file||!selected)return;
  if(!file.size)throw new Error('내용이 있는 영상 파일을 선택하세요.');
  const identity=selected.playback;
  if(identity.sha256){
    if(file.size!==identity.size_bytes||file.size>100000000)throw new Error('분석한 원본과 크기가 다릅니다. 같은 파일을 선택하세요.');
    const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',await file.arrayBuffer()))].map(n=>n.toString(16).padStart(2,'0')).join('');
    if(hash!==identity.sha256)throw new Error('분석한 원본과 다른 파일입니다. 미리보기를 연결하지 않았습니다.');
  }
  if(preparation!==selected||ticket!==previewFileGeneration)return;
  if(previewUrl)URL.revokeObjectURL(previewUrl);previewUrl=URL.createObjectURL(file);$('preview-video').src=previewUrl;$('preview-video').hidden=false;
  $('preview-video').querySelectorAll('track').forEach(t=>t.remove());if(previewCaptionUrl)URL.revokeObjectURL(previewCaptionUrl);previewCaptionUrl=null;
  const segments=selected.snapshot.transcript_segments;
  if(identity.sha256&&segments.length){
    const stamp=ms=>`${String(Math.floor(ms/3600000)).padStart(2,'0')}:${String(Math.floor(ms/60000)%60).padStart(2,'0')}:${String(Math.floor(ms/1000)%60).padStart(2,'0')}.${String(ms%1000).padStart(3,'0')}`;
    const cues=segments.filter(s=>s.end_ms>s.start_ms).map(s=>`${stamp(s.start_ms)} --> ${stamp(s.end_ms)}\n${s.text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}`).join('\n\n');
    previewCaptionUrl=URL.createObjectURL(new Blob([`WEBVTT\n\n${cues}\n`],{type:'text/vtt'}));
    const track=node('track',undefined,{kind:'captions',label:'준비된 한국어 자막',srclang:'ko',src:previewCaptionUrl});$('preview-video').append(track);track.track.mode='showing';
  }
  $('preview-playback').textContent=identity.sha256?'분석한 원본과 일치합니다. 이 화면에서만 재생합니다. 같은 파일을 학생에게 별도로 전달하세요.':'선택한 파일을 이 화면에서만 재생합니다. 분석 원본과의 동일성은 확인되지 않았습니다.';
  if(!identity.sha256||!segments.length)$('preview-playback').textContent+=' 이 파일에 연결할 검증된 시간 자막은 없습니다.';
}));
bindForm('preview-question-form',async payload=>{
  if(!preparation)throw new Error('준비 결과를 먼저 여세요.');const selected=preparation,ticket=preparationGeneration,question=++previewQuestion;
  const valid=()=>preparation===selected&&ticket===preparationGeneration&&question===previewQuestion;
  $('preview-video').pause();$('preview-answer').textContent='준비 자료의 근거로 답변을 확인하고 있습니다.';
  try{
    const result=await request(`${api}/preparations/${selected.id}/agent-turn`,{method:'POST',timeout:190000,body:{message:payload.message,analysis_consent:Boolean(payload.analysis_consent),current_time_ms:Math.round($('preview-video').currentTime*1000)}});
    if(valid())$('preview-answer').textContent=result.safe_to_speak&&result.confidence>=.72?`${result.title}. ${result.response_text}`:'근거가 충분하지 않아 답변을 보류했습니다.';
  }catch(error){if(valid())$('preview-answer').textContent=`답변을 만들지 못했습니다. ${error.message} 연결과 동의를 확인한 뒤 다시 질문하세요.`;}
});
$('preview-video').addEventListener('error',()=>{
  if(previewUrl&&$('preview-video').error)$('preview-playback').textContent='Chrome이 이 파일의 영상 형식 또는 코덱을 재생하지 못했습니다. 재생 가능한 MP4·WebM을 선택하세요. 준비된 자료는 계속 검토할 수 있습니다.';
});

function syncSource() {
  const form = $('prepare-form');
  const source = form.elements.source.value;
  const actual = source === 'video' || (source === 'link' && form.elements.request_analysis.checked);
  for (const [id, active] of [['material-input', source !== 'video'], ['link-input', source === 'link'], ['video-input', source === 'video'||source==='local']]) {
    $(id).querySelectorAll('input,select,textarea').forEach(control => { control.disabled = !active; });
  }
  $('material-input').hidden = source === 'video';
  $('link-input').hidden = source !== 'link'; $('video-input').hidden = !['video','local'].includes(source);
  $('prepare-url').required = source === 'link'; $('prepare-video').required = ['video','local'].includes(source);
  $('analysis-consents').hidden = ['materials','local'].includes(source);
  $('prepare-rights').disabled = ['materials','local'].includes(source);
  $('prepare-rights').required = !['materials','local'].includes(source);
  $('prepare-consent').required = actual; $('prepare-consent').disabled = !actual;
}
async function materialPayload() {
  clearMaterialValidation();
  const form = $('prepare-form');
  const payload = {title: form.elements.title.value, subject: form.elements.subject.value,
    source_label:form.elements.source_label.value,preferred_mode:form.elements.preferred_mode.value,problem_mode: form.elements.problem_mode.checked, assets: []};
  if (form.elements.passage.value.trim()) payload.assets.push({name: '직접 입력 지문', kind: 'passage', content: form.elements.passage.value});
  for (const file of $('material-files').files) {
    if (file.size > 1_200_000) materialFailure('자료 파일은 하나당 30만 자 이내로 나눠 주세요.');
    const content = await file.text();
    if (exceedsCharacters(content,300000)) materialFailure('자료 파일은 하나당 30만 자 이내로 나눠 주세요.');
    const extension = file.name.split('.').pop().toLowerCase();
    if (extension === 'json') {
      if (payload.analysis) throw new Error('분석 JSON은 한 개만 선택하세요.');
      try { payload.analysis = JSON.parse(content); } catch { throw new Error('분석 JSON의 형식을 확인하세요.'); }
    } else if (['srt', 'vtt', 'txt', 'md'].includes(extension)) {
      payload.assets.push({name: file.name, kind: ['srt', 'vtt'].includes(extension) ? 'subtitle' : 'passage', content});
    } else throw new Error('SRT·VTT·TXT·MD·JSON 자료를 선택하세요.');
  }
  if (form.elements.source.value === 'link') payload.link = {url: form.elements.url.value,
    rights_confirmed: form.elements.rights.checked, request_analysis: form.elements.request_analysis.checked,
    analysis_consent: form.elements.consent.checked};
  if(form.elements.source.value==='local'){
    const file=$('prepare-video').files[0];if(!file||!file.size)throw new Error('내용이 있는 원본 파일을 선택하세요.');
    payload.local_file={name:[...file.name].slice(0,240).join(''),size_bytes:file.size};
  }
  if (!payload.assets.length && !payload.analysis && !payload.link && !payload.local_file) throw new Error('지문·자막·분석 JSON 또는 영상 링크·로컬 파일을 넣으세요.');
  if(payload.assets.length>20)materialFailure('자막과 지문 자료는 한 강의에 20개까지 넣을 수 있습니다. 자료를 나누어 준비하세요.');
  if(exceedsCharacters(JSON.stringify(payload),1000000))materialFailure('입력 정보와 자료 전체가 100만 자를 넘었습니다. 파일 수나 지문 길이를 줄이거나 여러 강의로 나누어 준비하세요.');
  return payload;
}
function exceedsCharacters(text,limit){let count=0;for(const character of text)if(++count>limit)return true;return false;}
function clearMaterialValidation(){const field=$('material-files');field.removeAttribute('aria-invalid');$('material-validation').textContent='';}
function materialFailure(message){
  $('material-validation').textContent=message;$('material-files').setAttribute('aria-invalid','true');
  if(guided){prepareStep=1;prepareStepView();}
  const error=new Error('학습자료 입력을 확인해 주세요.');error.field=$('material-files');throw error;
}
$('material-files').addEventListener('change',clearMaterialValidation);
$('prepare-form').elements.passage.addEventListener('input',clearMaterialValidation);

bindForm('prepare-form', async () => {
  const form = $('prepare-form');
  let result;
  status(form.elements.source.value === 'video' ? '원본 영상을 전송하고 준비를 요청하고 있습니다. 접수될 때까지 기다려 주세요.' : '자료 준비를 요청하고 있습니다.');
  if (form.elements.source.value === 'video') {
    const file = $('prepare-video').files[0];
    if (!file || !file.size || file.size > 100000000) throw new Error('100MB 이하의 원본 영상을 선택하세요.');
    if (!form.elements.rights.checked || !form.elements.consent.checked) throw new Error('영상 이용 권한과 임시 전송 동의를 확인하세요.');
    const body = new FormData();
    for (const key of ['title', 'subject','source_label','preferred_mode']) body.set(key, form.elements[key].value);
    body.set('problem_mode', String(form.elements.problem_mode.checked));
    body.set('rights_confirmed', 'true'); body.set('cloud_analysis_consent', 'true'); body.set('video', file);
    result = await request(`${api}/preparations/video-file-analysis`, {method: 'POST', body, timeout: 120000});
  } else{
    const payload=await materialPayload();
    try{result=await request(`${api}/preparations`, {method: 'POST', body:payload});}
    catch(error){if(error.status===422&&error.message.includes('자료 전체'))materialFailure(error.message);throw error;}
  }
  jobStates.set(result.id, result.state);
  await refreshPreparations();
  $('preparations-title').focus();
  status(`${result.title} 준비를 접수했습니다. 상태 새로고침으로 진행을 확인할 수 있습니다.`);
});
bindForm('publish-form', async () => {
  if (!preparation) throw new Error('준비 결과를 먼저 확인하세요.');
  const form = $('publish-form');
  const result = await request(`${api}/preparations/${preparation.id}/publish`, {method: 'POST',
    body: {students: selection('publish-students'), chat_consent: form.elements.chat_consent.checked}});
  await refresh(); $('lectures-title').focus();
  status(result.already_published ? '이미 배정한 자료입니다. 강의 목록에서 수정할 수 있습니다.' : '확인한 자료를 학생에게 배정했습니다.');
});

function edit(id,{focus=true}={}) {
  editRevision++;
  editing = lectures.find(l => l.id === id);
  if (!editing) return;
  $('edit-form').elements.title.value = editing.title; $('edit-form').elements.subject.value = editing.subject;
  choices('edit-students', editing.students);
  $('withdraw').disabled = !editing.students.length;
  $('withdraw-confirm').hidden = true;$('delete-confirm').hidden=true; $('edit-panel').hidden = false; if(focus)$('edit-title').focus();
}
$('edit-panel').addEventListener('focusin',()=>editRevision++);
$('edit-form').addEventListener('input',()=>editRevision++);
$('delete-lecture').addEventListener('click',()=>{if(!editing)return;$('delete-question').textContent=`${editing.title} 강의를 영구 삭제할까요? 이 강의의 배정과 학생의 학습 기록도 삭제됩니다. 준비 결과와 기기의 원본 파일은 유지됩니다.`;$('delete-confirm').hidden=false;$('delete-yes').focus();});
$('delete-no').addEventListener('click',()=>{$('delete-confirm').hidden=true;$('delete-lecture').focus();});
$('delete-yes').addEventListener('click',()=>task($('delete-yes'),async()=>{
  if(!editing)throw new Error('삭제할 강의를 선택하세요.');const selected=editing;
  await request(`/local/lectures/${selected.id}`,{method:'DELETE'});
  if(editing===selected){editing=null;$('edit-panel').hidden=true;$('delete-confirm').hidden=true;$('lectures-title').focus();}
  await refresh();status('강의와 해당 배정·학습 기록을 삭제했습니다.');
}));
bindForm('edit-form', async ({title, subject}) => {
  if (!editing) throw new Error('강의를 먼저 선택하세요.');
  const ident = editing.id, ticket=generation;
  await request(`/local/lectures/${ident}`, {method: 'PUT', body: {title, subject, students: selection('edit-students')}});
  if(ticket!==generation)return;
  await refresh();if(ticket!==generation)return;
  if(editing?.id===ident){editing=lectures.find(lecture=>lecture.id===ident)||editing;$('withdraw').disabled=!editing.students.length;}
  status('강의와 배정을 저장했습니다. 비공개 강의는 목록에서 공개할 수 있습니다.');
});
$('withdraw').addEventListener('click', () => {
  $('withdraw-question').textContent = `${editing.title}의 배정 학생 ${editing.students.length}명 모두에게서 강의를 회수할까요?`;
  $('withdraw-confirm').hidden = false; $('withdraw-yes').focus();
});
$('withdraw-no').addEventListener('click', () => { $('withdraw-confirm').hidden = true; $('withdraw').focus(); });
$('withdraw-yes').addEventListener('click', () => task($('withdraw-yes'), async () => {
  if(!editing)throw new Error('회수할 강의를 먼저 선택하세요.');
  const selected=editing,revision=editRevision,ticket=generation,active=document.activeElement;
  await request(`${api}/lectures/${selected.id}/withdraw`, {method: 'POST', body: {students: [...selected.students]}});
  if(ticket!==generation)return;await refresh();if(ticket!==generation)return;
  if(editing?.id===selected.id){
    if(revision===editRevision)edit(selected.id,{focus:document.activeElement===active});
    else {editing=lectures.find(lecture=>lecture.id===selected.id)||editing;$('withdraw').disabled=!editing.students.length;}
  }
  status('배정을 회수했습니다. 자료와 학생 개인 기록은 삭제하지 않았습니다.');
}));

async function management(studentId = $('manage-student').value, focus = true) {
  const ticket = generation;
  const selectionTicket = ++managementGeneration;
  const [summary, sorted] = await Promise.all([request(`/local/students/${studentId}/progress`), request(`/local/students/${studentId}/order`)]);
  if (ticket !== generation || selectionTicket !== managementGeneration) return;
  managing = studentId; order = sorted;
  const student = students.find(s => s.id === studentId);
  if (!student) return;
  $('management-detail-title').textContent = `${student.name} 설정과 학습 현황`;
  const settings = {...settingDefaults, ...student.settings};
  for (const [key] of Object.entries(settingDefaults)) {
    const input = $('settings-form').elements[key];
    if (input.type === 'checkbox') input.checked = settings[key]; else input.value = settings[key];
  }
  $('settings-form').elements.reset_onboarding.checked = false;
  $('progress-summary').replaceChildren(...summary.lectures.map(l => node('li', `${l.title}: ${Math.floor(l.position_ms / 1000)}초, 북마크 ${l.bookmark_count}개, 밑줄 ${l.underlined_count}개, 메모 ${l.note_count}개${l.updated_at ? `, 마지막 저장 ${new Date(l.updated_at).toLocaleString('ko-KR')}` : ', 아직 학습 기록 없음'}`)));
  if (!summary.lectures.length) $('progress-summary').append(node('li', '배정한 강의가 없습니다.'));
  renderOrder(); $('management-detail').hidden = false;
  if (focus) $('management-detail-title').focus();
}
function renderOrder(focusId = null) {
  $('lecture-order').replaceChildren(...order.map((id, index) => {
    const title = lectures.find(l => l.id === id)?.title || '강의';
    const item = node('li'); item.append(node('p', title));
    for (const [delta, label] of [[-1, '위로'], [1, '아래로']]) {
      const control = button(`${title} ${label}`, async () => {
        const studentId = managing;
        const next = [...order]; [next[index], next[index + delta]] = [next[index + delta], next[index]];
        await request('/local/order', {method: 'PUT', body: {student: studentId, lectures: next}});
        if (managing !== studentId) return;
        order = next; renderOrder(id); status('학생의 강의 순서를 저장했습니다.');
      });
      control.disabled = index + delta < 0 || index + delta >= order.length;
      control.dataset.lecture = id; item.append(control);
    }
    return item;
  }));
  if (focusId) [...$('lecture-order').querySelectorAll('button')].find(b => b.dataset.lecture === focusId && !b.disabled)?.focus();
}
bindForm('settings-form', async () => {
  if (!managing) throw new Error('학생 현황을 먼저 여세요.');
  const studentId = managing;
  const form = $('settings-form'); const body = {};
  for (const key of [...Object.keys(settingDefaults), 'reset_onboarding']) {
    const field = form.elements[key]; body[key] = field.type === 'checkbox' ? field.checked : Number(field.value);
  }
  if (body.reader_mode) body.focus_voice = false;
  await request(`/local/students/${studentId}/settings`, {method: 'PUT', body});
  const student = students.find(s => s.id === studentId); if (student) student.settings = body;
  renderSteps();
  if (managing !== studentId) return;
  form.elements.focus_voice.checked = body.focus_voice;
  form.elements.reset_onboarding.checked = false;
  status('학생 기본 설정을 저장했습니다.');
});
$('load-management').addEventListener('click', () => task($('load-management'), () => management()));
bindForm('student-form', async credentials => {
  await request('/local/students', {method: 'POST', body: credentials});
  $('student-form').reset();
  await refresh();
  $('student-choice').focus();
  status('학생 계정을 만들었습니다. 학생용 확장에서 로그인할 수 있습니다.');
});
bindForm('assign-form', async ({student, sample}) => {
  await request(`/local/samples/${sample}/assign`, {method: 'POST', body: {students: [student]}});
  await refresh();
  status('샘플 강의를 배정했습니다. 학생용 확장에서 목록을 새로고침하세요.');
});
$('refresh').addEventListener('click', () => task($('refresh'), async () => { await refresh(); await refreshPreparations(); status('목록을 갱신했습니다.'); }));
$('refresh-preparations').addEventListener('click', () => task($('refresh-preparations'), async () => { await refreshPreparations(); status('준비 상태를 갱신했습니다.'); }));
$('create-pair-code').addEventListener('click',()=>task($('create-pair-code'),async()=>{
  const result=await request(`${api}/connections/code`,{method:'POST'});$('pair-code').value=result.code;$('pair-code').focus();$('pair-code').select();status('10분 동안 한 번 사용할 연결 코드를 만들었습니다. 학생이 직접 확인하고 연결해야 합니다.');
}));
$('guardian-unlink-no').addEventListener('click',()=>{unlinking=null;$('guardian-unlink-confirm').hidden=true;$('connections-title').focus();});
$('guardian-unlink-yes').addEventListener('click',()=>task($('guardian-unlink-yes'),async()=>{
  if(!unlinking)throw new Error('연결 해제할 학생을 선택하세요.');
  await request(`${api}/connections/unlink`,{method:'POST',body:{student:unlinking,confirm:true}});
  unlinking=null;$('connections-title').focus();$('guardian-unlink-confirm').hidden=true;await refresh();status('학생 연결과 배정을 해제했습니다. 학생 개인 기록은 보존했습니다.');
}));
const resetConsent = () => { $('prepare-rights').checked = false; $('prepare-consent').checked = false; syncSource(); };
$('prepare-source').addEventListener('change', resetConsent);
$('prepare-url').addEventListener('change', resetConsent);
$('prepare-video').addEventListener('change', resetConsent);
$('prepare-form').elements.request_analysis.addEventListener('change', () => { $('prepare-consent').checked = false; syncSource(); });
syncSource();
// Full-form entry remains available; guided entry validates each of the original three steps.
const prepareForm=$('prepare-form'),prepareGroups=[];
let guided=false,prepareStep=0;
const children=[...prepareForm.children];
for(const title of ['1. 강의 정보','2. 자료 선택','3. 동의와 최종 확인']){
  const group=node('fieldset');const legend=node('legend',title,{tabIndex:-1});group.append(legend);prepareGroups.push(group);prepareForm.append(group);
}
for(const child of children){const index=['material-input','link-input','video-input'].includes(child.id)?1:child.id==='analysis-consents'||child.type==='submit'?2:0;prepareGroups[index].append(child);}
function prepareStepView(focus=false){
  prepareGroups.forEach((group,index)=>group.hidden=guided&&index!==prepareStep);
  $('prepare-guided').setAttribute('aria-pressed',String(guided));$('prepare-guided').textContent=guided?'전체 입력 화면 사용':'3단계 준비 안내 사용';
  $('prepare-navigation').hidden=!guided;$('prepare-back').disabled=prepareStep===0;$('prepare-next').hidden=prepareStep===2;
  $('prepare-step').textContent=guided?`${prepareStep+1}/3단계: ${prepareGroups[prepareStep].firstElementChild.textContent}`:'';
  $('prepare-summary').hidden=!guided||prepareStep!==2;
  $('prepare-summary').textContent=`${prepareForm.elements.title.value} · ${prepareForm.elements.subject.value} · ${prepareForm.elements.source.selectedOptions[0].textContent} · ${prepareForm.elements.preferred_mode.selectedOptions[0].textContent}. 문제 보호 ${prepareForm.elements.problem_mode.checked?'켜짐':'꺼짐'}. 내용을 확인하고 필요한 동의를 선택한 뒤 준비를 시작하세요.`;
  if(focus)prepareGroups[prepareStep].firstElementChild.focus();
}
function validPrepareStep(index){
  const invalid=[...prepareGroups[index].querySelectorAll('input,select,textarea')].find(field=>!field.disabled&&!field.checkValidity());
  if(invalid){prepareStep=index;prepareStepView();invalid.focus();invalid.reportValidity();return false;}
  if(index===1&&prepareForm.elements.source.value==='materials'&&!$('material-files').files.length&&!prepareForm.elements.passage.value.trim()){status('자막·지문·JSON 자료를 넣으세요.',true);prepareForm.elements.passage.focus();return false;}
  return true;
}
$('prepare-guided').addEventListener('click',()=>{guided=!guided;prepareForm.noValidate=guided;prepareStep=0;prepareStepView(true);});
$('prepare-next').addEventListener('click',()=>{if(validPrepareStep(prepareStep)){prepareStep++;prepareStepView(true);}});
$('prepare-back').addEventListener('click',()=>{prepareStep=Math.max(0,prepareStep-1);prepareStepView(true);});
prepareForm.addEventListener('submit',event=>{
  if(!guided)return;
  if(prepareStep<2){event.preventDefault();event.stopImmediatePropagation();if(validPrepareStep(prepareStep)){prepareStep++;prepareStepView(true);}return;}
  for(let index=0;index<3;index++)if(!validPrepareStep(index)){event.preventDefault();event.stopImmediatePropagation();return;}
},true);
const showUser = await boot(async () => {
  const capability=await request(`${api}/capabilities`);
  $('student-form').closest('details').hidden=capability.production;
  generation++; await refresh(); await refreshPreparations();
  clearInterval(poll);
  poll = setInterval(() => { if (!document.hidden) refreshPreparations().catch(error => {
    if (pollError !== error.message) { pollError = error.message; $('connection-status').textContent = error.message; }
  }); }, 5000);
}, () => {
  preparationGeneration++;resetPreview();
  guided=false;prepareStep=0;prepareForm.noValidate=false;prepareStepView();
  generation++;
  managementGeneration++;
  clearInterval(poll); students = []; lectures = []; preparations = []; preparation = null; editing = null; managing = null; jobsFingerprint = '';
  $('preparation-filter').value = 'all'; $('preparation-search').value = '';
  $('preparation-counts').textContent = ''; $('preparation-results').textContent = '';
  jobStates.clear(); pollError = ''; $('job-status').textContent = ''; $('connection-status').textContent = '';
  unlinking=null;$('guardian-unlink-confirm').hidden=true;$('connection-students').replaceChildren();$('pair-code').value='';
  for (const id of ['students', 'lectures', 'student-choice', 'manage-student', 'preparations', 'prepared-preview', 'progress-summary', 'lecture-order']) $(id).replaceChildren();
  for (const id of ['prepared-detail', 'edit-panel', 'management-detail']) $(id).hidden = true;
  for (const id of ['student-form', 'prepare-form', 'publish-form', 'edit-form', 'settings-form']) $(id).reset();
  choices('publish-students', []); choices('edit-students', []); syncSource();
});
bindForm('register-form', async credentials => {
  await showUser(await signIn(credentials, true));
  $('register-form').reset();
  status('보호자 계정을 만들었습니다.');
});
