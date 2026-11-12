import {request, signIn} from './client.js';
import {$, node, button, bindForm, status, task, boot} from './ui.js';

let generation = 0;
let students = [], lectures = [], preparation = null, editing = null, managing = null;
let order = [], poll = null, jobsFingerprint = '';
let jobStates = new Map(), pollError = '';
let managementGeneration = 0;
let preparationGeneration = 0;
let unlinking = null;
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

async function refresh() {
  const ticket = generation;
  const results = await Promise.all([request('/local/students'), request('/local/lectures')]);
  if (ticket !== generation) return;
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
}

async function refreshPreparations() {
  const ticket = generation;
  const jobs = await request(`${api}/preparations`);
  if (ticket !== generation) return;
  if (pollError) { pollError = ''; $('connection-status').textContent = '서버 연결이 복구됐습니다.'; }
  const fingerprint = JSON.stringify(jobs);
  if (fingerprint === jobsFingerprint) return;
  jobsFingerprint = fingerprint;
  const focus = document.activeElement?.dataset.job;
  const labels = {queued: '접수', running: '진행 중', completed: '준비 완료', failed: '실패', interrupted: '중단'};
  const changed = jobs.filter(job => jobStates.has(job.id) && jobStates.get(job.id) !== job.state && ['completed', 'failed', 'interrupted'].includes(job.state));
  if (changed.length) $('job-status').textContent = changed.map(job => `${job.title}: ${labels[job.state]}. ${job.message}`).join(' ');
  jobStates = new Map(jobs.map(job => [job.id, job.state]));
  $('preparations').replaceChildren(...jobs.map(job => {
    const item = node('article');
    item.append(node('h4', job.title), node('p', `${labels[job.state] || job.state}. ${job.message}`));
    const action = job.state === 'completed'
      ? button(`${job.title} 결과 확인·배정`, () => openPreparation(job.id))
      : ['failed', 'interrupted'].includes(job.state)
        ? button(`${job.title} 다시 준비`, () => {
          const form = $('prepare-form'); form.elements.title.value = job.title; form.elements.subject.value = job.subject;
          form.elements.source.value = job.source_kind === 'video' ? 'video' : job.source_kind === 'link' ? 'link' : 'materials';
          $('prepare-rights').checked = false; $('prepare-consent').checked = false;
          $('prepare-video').value = ''; $('material-files').value = '';
          syncSource(); form.elements.title.focus();
          status('자료와 동의를 다시 선택한 뒤 준비를 시작하세요. 이전 요청을 자동 재실행하지 않습니다.');
        }) : null;
    if (action) { action.dataset.job = job.id; item.append(action); }
    return item;
  }));
  if (!jobs.length) $('preparations').append(node('p', '아직 준비 작업이 없습니다. 새 강의 준비에서 자료를 선택하세요.'));
  if (focus) [...$('preparations').querySelectorAll('button')].find(b => b.dataset.job === focus)?.focus();
}

async function openPreparation(id) {
  const ticket = generation;
  const selected = ++preparationGeneration;
  preparation = null; $('prepared-detail').hidden = true;
  const job = await request(`${api}/preparations/${id}`);
  if (ticket !== generation || selected !== preparationGeneration) return;
  preparation = job;
  $('prepared-title').textContent = `${job.title} 준비 결과`;
  const snapshot = job.snapshot;
  $('prepared-preview').replaceChildren(node('p', snapshot.session.source_label),
    node('p', `자막 ${snapshot.transcript_segments.length}개, 지문 ${snapshot.passage?.paragraphs.length || 0}문단, 공개 가능한 화면 설명 ${snapshot.safe_description_count}개, 보류 ${snapshot.held_count}개.`),
    ...snapshot.review.core_summary.map(text => node('p', text)),
    ...(snapshot.passage?.paragraphs || []).map(p => node('p', p.sentences.map(s => s.text).join(' '))));
  choices('publish-students', []);
  $('publish-form').reset();
  $('prepared-detail').hidden = false;
  $('prepared-title').focus();
}

function syncSource() {
  const form = $('prepare-form');
  const source = form.elements.source.value;
  const actual = source === 'video' || (source === 'link' && form.elements.request_analysis.checked);
  for (const [id, active] of [['material-input', source !== 'video'], ['link-input', source === 'link'], ['video-input', source === 'video']]) {
    $(id).querySelectorAll('input,select,textarea').forEach(control => { control.disabled = !active; });
  }
  $('material-input').hidden = source === 'video';
  $('link-input').hidden = source !== 'link'; $('video-input').hidden = source !== 'video';
  $('prepare-url').required = source === 'link'; $('prepare-video').required = source === 'video';
  $('analysis-consents').hidden = source === 'materials';
  $('prepare-rights').disabled = source === 'materials';
  $('prepare-rights').required = source !== 'materials';
  $('prepare-consent').required = actual; $('prepare-consent').disabled = !actual;
  form.elements.access_code.disabled = !actual;
}
async function materialPayload() {
  const form = $('prepare-form');
  const payload = {title: form.elements.title.value, subject: form.elements.subject.value,
    problem_mode: form.elements.problem_mode.checked, assets: []};
  if (form.elements.passage.value.trim()) payload.assets.push({name: '직접 입력 지문', kind: 'passage', content: form.elements.passage.value});
  for (const file of $('material-files').files) {
    if (file.size > 1_200_000) throw new Error('자료 파일은 30만 자 이내로 나눠 주세요.');
    const content = await file.text();
    if (content.length > 300000) throw new Error('자료 파일은 30만 자 이내로 나눠 주세요.');
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
    analysis_consent: form.elements.consent.checked, access_code: form.elements.access_code.value};
  if (!payload.assets.length && !payload.analysis && !payload.link?.request_analysis) throw new Error('지문·자막·분석 JSON을 넣거나 실제 링크 분석을 선택하세요.');
  return payload;
}

bindForm('prepare-form', async () => {
  const form = $('prepare-form');
  let result;
  status(form.elements.source.value === 'video' ? '원본 영상을 전송하고 준비를 요청하고 있습니다. 접수될 때까지 기다려 주세요.' : '자료 준비를 요청하고 있습니다.');
  if (form.elements.source.value === 'video') {
    const file = $('prepare-video').files[0];
    if (!file || !file.size || file.size > 100000000) throw new Error('100MB 이하의 원본 영상을 선택하세요.');
    if (!form.elements.rights.checked || !form.elements.consent.checked) throw new Error('영상 이용 권한과 임시 전송 동의를 확인하세요.');
    const body = new FormData();
    for (const key of ['title', 'subject', 'access_code']) body.set(key, form.elements[key].value);
    body.set('problem_mode', String(form.elements.problem_mode.checked));
    body.set('rights_confirmed', 'true'); body.set('cloud_analysis_consent', 'true'); body.set('video', file);
    result = await request(`${api}/preparations/video-file-analysis`, {method: 'POST', body, timeout: 120000});
  } else result = await request(`${api}/preparations`, {method: 'POST', body: await materialPayload()});
  form.elements.access_code.value = '';
  jobStates.set(result.id, result.state);
  await refreshPreparations();
  $('preparations-title').focus();
  status(`${result.title} 준비를 접수했습니다. 상태 새로고침으로 진행을 확인할 수 있습니다.`);
});
bindForm('publish-form', async () => {
  if (!preparation) throw new Error('준비 결과를 먼저 확인하세요.');
  const form = $('publish-form');
  const result = await request(`${api}/preparations/${preparation.id}/publish`, {method: 'POST',
    body: {students: selection('publish-students'), chat_consent: form.elements.chat_consent.checked, access_code: form.elements.access_code.value}});
  form.elements.access_code.value = '';
  await refresh(); $('lectures-title').focus();
  status(result.already_published ? '이미 배정한 자료입니다. 강의 목록에서 수정할 수 있습니다.' : '확인한 자료를 학생에게 배정했습니다.');
});

function edit(id) {
  editing = lectures.find(l => l.id === id);
  if (!editing) return;
  $('edit-form').elements.title.value = editing.title; $('edit-form').elements.subject.value = editing.subject;
  choices('edit-students', editing.students);
  $('withdraw').disabled = !editing.students.length;
  $('withdraw-confirm').hidden = true; $('edit-panel').hidden = false; $('edit-title').focus();
}
bindForm('edit-form', async ({title, subject}) => {
  if (!editing) throw new Error('강의를 먼저 선택하세요.');
  const ident = editing.id;
  await request(`/local/lectures/${ident}`, {method: 'PUT', body: {title, subject, students: selection('edit-students')}});
  await refresh(); if (editing?.id === ident) edit(ident);
  status('강의와 배정을 저장했습니다. 비공개 강의는 목록에서 공개할 수 있습니다.');
});
$('withdraw').addEventListener('click', () => {
  $('withdraw-question').textContent = `${editing.title}의 배정 학생 ${editing.students.length}명 모두에게서 강의를 회수할까요?`;
  $('withdraw-confirm').hidden = false; $('withdraw-yes').focus();
});
$('withdraw-no').addEventListener('click', () => { $('withdraw-confirm').hidden = true; $('withdraw').focus(); });
$('withdraw-yes').addEventListener('click', () => task($('withdraw-yes'), async () => {
  await request(`${api}/lectures/${editing.id}/withdraw`, {method: 'POST', body: {students: editing.students}});
  await refresh(); edit(editing.id); status('배정을 회수했습니다. 자료와 학생 개인 기록은 삭제하지 않았습니다.');
}));

const settingDefaults = {auto_description: true, problem_mode: true, speech_rate: .95, speech_volume: .9, reader_mode: false, focus_voice: false};
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
const showUser = await boot(async () => {
  const capability=await request(`${api}/capabilities`);
  $('student-form').closest('details').hidden=capability.production;
  generation++; await refresh(); await refreshPreparations();
  clearInterval(poll);
  poll = setInterval(() => { if (!document.hidden) refreshPreparations().catch(error => {
    if (pollError !== error.message) { pollError = error.message; $('connection-status').textContent = error.message; }
  }); }, 5000);
}, () => {
  generation++;
  managementGeneration++;
  clearInterval(poll); students = []; lectures = []; preparation = null; editing = null; managing = null; jobsFingerprint = '';
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
