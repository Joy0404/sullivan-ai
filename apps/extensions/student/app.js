import {request} from './client.js';
import {$, node, button, bindForm, status, task, boot} from './ui.js';
import {StudentMedia} from './media.js';
import {StudentSpeech, StudentAnnouncer, controlDescription} from './speech.js';
import {installStudentKeyboard} from './keyboard.js';
import {createLessonData} from './lesson-data.js';
import {saveOriginal, loadOriginal, removeOriginal} from './media-store.js';
import './playback-scheduler.js';
import './narration-context.js';
import './passage-tools.js';
import './concept-tools.js';
import './voice-command-router.js';
import './space-gesture.js';
import './learning-response.js';
import './speech-profile.js';

let current = null, user = null, lectures = [], generation = 0, actionGeneration = 0, lectureRequest=0;
let positionMs = 0, previousMs = null, originMs = null, currentParagraph = null, sentenceIndex = 0;
let announced = new Set(), tickBusy = false, saveChain = Promise.resolve(), saveTimer, autoSaveAt = 0;
let noteDirty = false, positionDirty = false, recordsDirty = false, positionEditRevision = 0, saveRevision = 0, recognition = null, voiceGeneration = 0, microphoneGeneration=0;
let dialogFocus = null, focusTicket = 0, dialogResume=null, conceptRun=null, pendingRequests=0, suppressFocus=false;
let originPlaying=false;
let lessonData=null,questionRevision=0,saveFailed=false;
let voiceFallback=null;
let playbackStatus = '';
let pendingPlayerPermission=null;
let refreshRevision = 0;
let pairRequest = null;
const inPanel=!chrome.extension.getViews({type:'tab'}).includes(window);
const defaults = {speech_rate: .95, speech_volume: .9, auto_description: true, reader_mode: false, focus_voice: true};
const accessSaved=(await chrome.storage.local.get('student-accessibility'))['student-accessibility']||{};
let settings = {...defaults, ...accessSaved};
function applySettings(saved={}){
  settings={...defaults,...saved};
  if(Object.keys(accessSaved).length)Object.assign(settings,accessSaved);
  else if(!('focus_voice' in saved)&&!settings.reader_mode)settings.focus_voice=true;
  $('access-mode').value=settings.reader_mode?'reader':settings.focus_voice?'app':'silent';
}
let device = {voice_uri: '', speech_pitch: 1};
const media = new StudentMedia($('local-video'));
const speaker = new StudentSpeech(media, () => ({...settings, ...device}), (text,state={}) => {
  if(state.purpose==='guidance'){ $('speech-status').textContent=text; return; }
  $('current-description').textContent = text;
  $('reader-description').textContent = settings.reader_mode||state.unavailable ? `강의를 일시정지했습니다. ${text} 계속 들으려면 강의 재생을 누르세요.` : '';
});
const announcer=new StudentAnnouncer(()=>({...settings,...device}),text=>{$('speech-status').textContent=text;},()=>Boolean(recognition));
announcer.lessonSpeaker=speaker;announcer.lessonReady=()=>Boolean(current&&media.kind&&media.ready);
speaker.beforeSpeak=purpose=>{if(purpose!=='guidance')announcer.cancel(true);};
function reportError(error){if(!error.cancelled&&!error.reported)status(error.message,true);}
function connectionNotice(text){$('connection').textContent=text;if(!settings.reader_mode)announcer.say(text);}
function clearPlayerPermission(){
  pendingPlayerPermission=null;
  if(document.activeElement===$('grant-player'))(media.ready?$('play'):$('open-original')).focus();
  $('grant-player').hidden=true;$('player-permission-help').textContent='';
}
function playerPermission(error,context){
  const origins=(error.permissionOrigins||[]).filter(origin=>{try{const url=new URL(origin);return ['http:','https:'].includes(url.protocol)&&!url.username&&!url.password;}catch{return false;}}).slice(0,8);
  if(!origins.length)return false;
  pendingPlayerPermission={...context,origins};
  $('player-permission-help').textContent=`이 강의의 영상 제공 사이트: ${origins.map(origin=>new URL(origin).origin).join(', ')}. 영상 재생·이동을 연결하려면 아래 버튼에서 허용하세요. 강의 내용이나 계정 정보를 이 사이트로 새로 전송하지 않습니다.`;
  $('grant-player').hidden=false;connectionNotice(`영상 제공 사이트 ${origins.map(origin=>new URL(origin).origin).join(', ')}의 추가 연결 허용이 필요합니다. 아래 허용 버튼을 누르거나 준비된 자료를 계속 읽으세요.`);return true;
}
function loseConnection(text){stopAll(false).catch(reportError);gesture.cancel();media.reset();connectionNotice(text);}
const time = ms => `${Math.floor(ms / 60000)}분 ${Math.floor(ms / 1000) % 60}초`;
const paragraphs = () => lessonData?.paragraphs || [];
const sentences = () => lessonData?.sentences || [];
const concepts = () => lessonData?.concepts || [];
const safeGaps = () => lessonData?.gaps || [];
const hasLearningMaterial = () => Boolean(current&&(paragraphs().length||current.snapshot.transcript_segments.length||safeGaps().length));
function needLesson() { if (!current) throw new Error('강의를 먼저 선택하세요.'); return current; }
function stopVoice() {
  voiceGeneration++;
  if (recognition) { recognition.onresult = recognition.onend = recognition.onerror = null; try { recognition.abort(); } catch {} }
  recognition = null; $('voice').textContent = '음성 명령 시작';
}
export async function stopAll(announce = true) {
  clearPlayerPermission();
  lectureRequest++;
  cancelConcept();dialogResume=null;voiceFallback=null;
  actionGeneration++; microphoneGeneration++; focusTicket++; announcer.cancel(); speaker.cancel(); stopVoice();
  const stopped=actionGeneration;
  await media.pause().catch(() => {});
  if (announce && stopped===actionGeneration) status('영상과 앱 음성을 모두 중지했습니다.');
}
function clear() {
  clearPlayerPermission();
  lectureRequest++;
  generation++; actionGeneration++; microphoneGeneration++; focusTicket++; announcer.cancel(); speaker.cancel(); stopVoice(); clearTimeout(saveTimer);
  cancelConcept();dialogResume=null;dialogFocus=null;voiceFallback=null;keyboard.reset(); media.reset(); current = null;lessonData=null; positionMs = 0; previousMs = null; originMs = null;saveFailed=false;
  announced = new Set(); noteDirty = positionDirty = recordsDirty = false;
  $('retry-save').hidden = true;
  playbackStatus = ''; $('reader-description').textContent = ''; $('local-file').value = ''; $('store-original').checked = false;
  $('lesson').hidden = true; $('return-origin').disabled = true;
  for (const id of ['material','search-results','chat-log','review','evidence','bookmarks']) $(id).replaceChildren();
  $('note').value = ''; $('position').value = '0'; $('connection').textContent = '영상을 아직 연결하지 않았습니다.';
  for(const id of ['current-description','save-status','answer-status','player-status','playback-state','speech-status'])$(id).textContent='';
  for(const dialog of document.querySelectorAll('dialog[open]'))dialog.close();
}
async function refreshConnections(){
  const list=await request('/extension/v1/student/connections');
  $('my-connections').replaceChildren(...list.map(connection=>{
    const item=node('li');item.append(node('p',`연결된 보호자: ${connection.name}`),button('내 보호자 연결 해제',()=>{$('student-unlink-confirm').hidden=false;$('student-unlink-yes').focus();}));return item;
  }));
  if(!list.length)$('my-connections').append(node('li','연결된 보호자가 없습니다. 일회용 코드를 확인해 연결할 수 있습니다.'));
}
bindForm('pair-preview-form',async payload=>{
  pairRequest=null;$('pair-preview').hidden=true;
  const result=await request('/extension/v1/student/connections/preview',{method:'POST',body:payload});
  pairRequest=result.request_id;$('pair-guardian').textContent=`연결할 보호자: ${result.guardian_name}`;$('pair-sharing').textContent=result.sharing;
  $('pair-confirm').checked=false;$('pair-preview').hidden=false;$('pair-preview-title').focus();
});
bindForm('pair-confirm-form',async()=>{
  if(!pairRequest)throw new Error('연결할 보호자를 먼저 확인하세요.');
  await request('/extension/v1/student/connections/confirm',{method:'POST',body:{request_id:pairRequest,confirm:$('pair-confirm').checked}});
  pairRequest=null;$('workspace-title').focus();$('pair-preview').hidden=true;await refreshConnections();await refresh();status('확인한 보호자와 연결했습니다. 보호자가 강의를 배정하면 목록에 나타납니다.');
});
$('refresh-connections').addEventListener('click',()=>task($('refresh-connections'),async()=>{await refreshConnections();status('내 보호자 연결을 확인했습니다.');}));
$('student-unlink-no').addEventListener('click',()=>{$('student-unlink-confirm').hidden=true;$('workspace-title').focus();});
$('student-unlink-yes').addEventListener('click',()=>task($('student-unlink-yes'),async()=>{
  await request('/extension/v1/student/connections/unlink',{method:'POST',body:{student:user.id,confirm:true}});
  clear();$('workspace-title').focus();$('student-unlink-confirm').hidden=true;await refreshConnections();await refresh();status('보호자 연결과 이 보호자의 배정 이용을 종료했습니다. 내 개인 기록은 보존했습니다.');
}));
async function refresh() {
  const ticket = generation, revision = ++refreshRevision;
  const list = await request('/local/lectures');
  if (ticket !== generation || revision !== refreshRevision) return;
  const active=document.activeElement,focused=active?.dataset.lecture;
  const focusedIndex=lectures.findIndex(l=>l.id===focused);
  let focusRemoved=false;
  lectures = list;
  if (current && !list.some(l => l.id === current.id)) {
    focusRemoved=$('lesson').contains(active);
    clear();
  }
  $('lectures').replaceChildren(...list.map(l => {
    const item = node('li'), control = button(`${l.title} 열기`, () => open(l.id));
    control.dataset.lecture = l.id;control.setAttribute('aria-label',`강의 ${list.indexOf(l)+1}. ${l.title} 열기`); item.append(control); return item;
  }));
  if (!list.length) $('lectures').append(node('li', '아직 배정된 강의가 없습니다. 보호자에게 배정을 요청하세요.'));
  if(focused){const controls=[...$('lectures').querySelectorAll('button')];(controls.find(b=>b.dataset.lecture===focused)||controls[Math.min(Math.max(0,focusedIndex),controls.length-1)]||$('workspace-title')).focus();}
  else if(focusRemoved)$('workspace-title').focus();
}
async function open(id) {
  let selectedRequest=++lectureRequest;const interaction=focusTicket;
  if (current && (noteDirty || positionDirty || recordsDirty || saveFailed)){
    const enteredPosition=$('position').value;
    await save(true);
    if(selectedRequest===lectureRequest&&(noteDirty||recordsDirty||(positionDirty&&$('position').value!==enteredPosition))){status('새로 입력한 학습 기록이 있습니다. 저장한 뒤 강의를 다시 선택하세요.');return;}
  }
  if(selectedRequest!==lectureRequest)return;
  const canMoveFocus=interaction===focusTicket||$('lesson').contains(document.activeElement);
  clear();selectedRequest=lectureRequest;if(canMoveFocus)$('workspace-title').focus(); const ticket = generation,focus=focusTicket;
  const data = await request(`/extension/v1/student/lectures/${id}`);
  if (ticket !== generation||selectedRequest!==lectureRequest) return;
  current = data; current.progress = {bookmarks: [], underlined: [], ...data.progress};
  lessonData=createLessonData(data.snapshot);
  applySettings(data.settings); fillPreferences();
  positionMs = data.progress.position_ms || 0;
  $('lesson-title').textContent = data.title; $('source-label').textContent = data.snapshot.session.source_label;
  if(!hasLearningMaterial())$('source-label').textContent+=' · 원본 재생용으로 등록됨: 영상 분석은 실행하지 않았습니다. 재생·명령·기록을 이용할 수 있으며 내용 질문·해설에는 자료 또는 실제 분석 연결이 필요합니다.';
  $('position').value = String(Math.round(positionMs / 1000)); $('note').value = data.progress.note || '';
  renderMaterial(); renderRecords(); renderReview();
  $('open-original').disabled = !['youtube','direct','external'].includes(data.playback.kind);
  $('connect-active').disabled = $('open-original').disabled;
  $('lesson').hidden = false;if(canMoveFocus&&focus===focusTicket)$('lesson-title').focus();
  await chrome.storage.local.set({[`last:${user.id}`]: id});
  if(ticket===generation&&selectedRequest===lectureRequest)status(hasLearningMaterial()?'준비된 자료를 열었습니다. 영상은 연결한 뒤 직접 재생하세요.':'원본 재생용 강의를 열었습니다. 영상 분석은 실행하지 않았습니다. 연결 후 재생·명령·기록을 이용하세요.');
}
function renderMaterial() {
  const box = $('material'),active=document.activeElement;
  const selectedSentence=sentences()[sentenceIndex],underlined=new Set(current.progress.underlined);
  const focused=box.contains(active)?active.dataset.materialKey:null,focusedParagraph=active?.dataset.paragraphId;
  box.replaceChildren();
  const article = (title, texts) => {
    if (!texts.length) return;
    const section = node('article'); section.append(node('h4', title), ...texts.map(text => node('p', text))); box.append(section);
  };
  article('강의 요약', current.snapshot.review.core_summary || []);
  for (const p of paragraphs()) {
    const section = node('article'),heading=node('h4',`${p.paragraph_index}문단 · ${p.flow_role}`,{tabIndex:-1});heading.dataset.paragraphId=p.paragraph_id;section.append(heading);
    const text=node('p');
    for(const sentence of p.sentences){
      const control=button(`${p.paragraph_index}문단 ${sentence.sentence_index}문장. ${sentence.text}`,async()=>{
        const lesson=needLesson(),ticket=generation;rememberExploration();currentParagraph=p.paragraph_id;
        sentenceIndex=lessonData.sentenceIndices.get(sentence.sentence_id)??0;
        if(media.ready&&Number.isFinite(sentence.timestamp_ms)&&!await seek(sentence.timestamp_ms))return;
        if(current!==lesson||ticket!==generation)return;renderMaterial();await speaker.say(sentence.text);
      });
      control.classList.add('secondary','sentence');control.dataset.sentenceId=sentence.sentence_id;control.dataset.materialKey=`sentence:${sentence.sentence_id}`;control.dataset.paragraphId=p.paragraph_id;
      if(currentParagraph===p.paragraph_id&&selectedSentence?.sentence_id===sentence.sentence_id)control.setAttribute('aria-current','true');
      if(sentence.highlighted)control.append(node('strong',' 강조',{className:'highlight-label'}));
      text.append(control);
    }
    section.append(text);
    const read=button(`${p.paragraph_index}문단 듣기`,()=>readParagraph(p)),jump=button(`${p.paragraph_index}문단 강의 구간`,()=>seek(p.timestamp_ms));
    read.dataset.materialKey=`read:${p.paragraph_id}`;jump.dataset.materialKey=`jump:${p.paragraph_id}`;
    read.dataset.paragraphId=jump.dataset.paragraphId=p.paragraph_id;section.append(read,jump);
    const marked = underlined.has(p.paragraph_id);
    const mark = button(`${p.paragraph_index}문단 밑줄 ${marked ? '해제' : '표시'}`, async () => {
      const selected=current,ticket=generation;
      const set = new Set(current.progress.underlined);
      if (!set.has(p.paragraph_id) && set.size >= 100) throw new Error('밑줄은 100개까지 저장할 수 있습니다.');
      set.has(p.paragraph_id) ? set.delete(p.paragraph_id) : set.add(p.paragraph_id);
      current.progress.underlined = [...set]; recordsDirty = true; renderMaterial();
      await save();if(current===selected&&ticket===generation)status(`${p.paragraph_index}문단 밑줄 ${set.has(p.paragraph_id)?'선택됨':'선택 해제됨'}. 저장했습니다.`);
    });
    mark.setAttribute('aria-pressed', String(marked));mark.dataset.materialKey=`mark:${p.paragraph_id}`;mark.dataset.paragraphId=p.paragraph_id; mark.dataset.paragraph = p.paragraph_id; section.append(mark); box.append(section);
  }
  article('검증된 화면 설명', safeGaps().map(g => `${time(g.timestamp_ms)}. ${g.public_description}`));
  article('강의 발화', current.snapshot.transcript_segments.map(s => s.text));
  if (!box.childElementCount) box.append(node('p', '표시할 준비된 자료가 없습니다.'));
  $('evidence').replaceChildren(node('h4', '설명 판단 근거'), ...current.snapshot.visual_gaps.map(g => node('p', `${time(g.timestamp_ms)}: ${g.action}. ${g.reason}`)));
  if(focused){const controls=[...box.querySelectorAll('[data-material-key]')];(controls.find(e=>e.dataset.materialKey===focused)||[...box.querySelectorAll('h4[data-paragraph-id]')].find(e=>e.dataset.paragraphId===focusedParagraph)||$('lesson-title')).focus();}
}
function renderRecords() {
  $('bookmarks').replaceChildren(...current.progress.bookmarks.map((entry, index) => {
    const item = node('li');
    item.append(button(`${time(entry.timestamp_ms || 0)} ${entry.note || '북마크'}`, () => seek(entry.timestamp_ms || 0)),
      button(`${index + 1}번 북마크 삭제`, async () => {
        current.progress.bookmarks.splice(index, 1); recordsDirty = true; renderRecords(); $('records-title').focus(); await save();
      })); return item;
  }));
  if (!current.progress.bookmarks.length) $('bookmarks').append(node('li', '저장한 북마크가 없습니다.'));
}
function rememberExploration(){
  if(!current||originMs!==null)return;originMs=positionMs;
  originPlaying=Boolean(speaker.resumeIntent?.playing)||(media.kind==='local'?!media.video.paused:playbackStatus.includes('재생하고'));
  $('return-origin').disabled=false;
}
async function returnToOrigin(){
  needLesson();if(originMs===null)throw new Error('탐색 전 위치가 없습니다.');
  const target=originMs,playing=originPlaying;if(!await seek(target,{announce:!playing}))return;originMs=null;originPlaying=false;$('return-origin').disabled=true;
  if(playing)await media.play(media.fence);
}
function cancelConcept(){if(conceptRun){clearInterval(conceptRun.timer);conceptRun=null;}}
async function playConcept(concept){
  needLesson();rememberExploration();if(!await seek(concept.timestamp_ms,{announce:false}))return;
  const run={lesson:current.id,action:actionGeneration,fence:media.fence,busy:false};conceptRun=run;
  const valid=()=>run===conceptRun&&run.action===actionGeneration&&run.lesson===current?.id&&run.fence===media.fence;
  const state=await media.state();
  if(!valid()){if(run===conceptRun)cancelConcept();return;}
  if(state.ad||!Number.isFinite(state.durationMs)){cancelConcept();throw new Error('광고가 끝나고 원본 강의 길이를 확인한 뒤 구간 듣기를 다시 선택하세요.');}
  const end=Math.min(concept.end_ms||concept.timestamp_ms+10000,concept.timestamp_ms+22000,state.durationMs);
  try{await media.play(run.fence);}catch(error){if(run===conceptRun)cancelConcept();if(error.cancelled)return;throw error;}
  if(!valid()){if(run===conceptRun)cancelConcept();return;}
  run.timer=setInterval(async()=>{
    if(!valid()){if(run===conceptRun)cancelConcept();clearInterval(run.timer);return;}
    if(run.busy)return;run.busy=true;
    try{const state=await media.state();if(!valid()||state.ad||!Number.isFinite(state.positionMs))return;
      if(state.positionMs>=end||state.ended){clearInterval(run.timer);await media.pause(false);if(!valid())return;conceptRun=null;await speaker.say(`${concept.keyword}. ${concept.ai_explanation}`,{resume:false});}
    }catch(error){if(run===conceptRun){cancelConcept();reportError(error);}}finally{run.busy=false;}
  },100);
}
function showHelp(focus=true){
  $('onboarding-card').hidden=false;
  if(!focus)$('voice-status').textContent='처음 사용 안내가 열려 있습니다. 사용법 안내 버튼에서 단축키와 음성 모드를 확인하세요.';
  if(focus)$('onboarding-title').focus();
  if(settings.focus_voice&&!settings.reader_mode)announcer.say($('onboarding-copy').textContent);
}
function voiceReadyCue(){
  try{const context=new (window.AudioContext||window.webkitAudioContext)();context.resume();const tone=context.createOscillator(),gain=context.createGain();tone.frequency.value=740;gain.gain.value=.08;
    tone.connect(gain).connect(context.destination);tone.start();tone.stop(context.currentTime+.12);tone.onended=()=>context.close();}catch{}
}
actionLater();
function actionLater(){
  $('show-help').addEventListener('click',()=>showHelp());
  $('onboarding-done').addEventListener('click',()=>task($('onboarding-done'),async()=>{const account=user;await request('/local/onboarding',{method:'POST'});if(user!==account)return;user.onboarded=1;const focused=$('onboarding-card').contains(document.activeElement);$('onboarding-card').hidden=true;if(focused)$('workspace-title').focus();status('사용법을 확인했습니다.');}));
  $('preview-voice').addEventListener('click',()=>task($('preview-voice'),async()=>{announcer.cancel(true);device={voice_uri:$('speech-voice').value,speech_pitch:Number($('speech-pitch').value),speech_style:$('speech-style').value};await speaker.say('강의의 흐름을 함께 살펴봅니다. AI는 검증된 화면 정보를 안내합니다.');}));
  $('read-review').addEventListener('click',()=>task($('read-review'),async()=>{needLesson();rememberExploration();await speaker.say($('review').textContent);}));
  $('read-study').addEventListener('click',()=>task($('read-study'),async()=>{needLesson();rememberExploration();const g=current.snapshot.study_guide;await speaker.say([g.overview,...g.concept_map,...g.glossary.map(x=>`${x.term}. ${x.definition}`),...g.recall_questions].filter(Boolean).join(' '));}));
}
function renderReview() {
  const snapshot = current.snapshot, guide = snapshot.study_guide;
  const box = $('review'); box.replaceChildren(...(snapshot.review.core_summary || []).map(s => node('p', s)));
  for (const entry of snapshot.review.key_segments || []) box.append(button(`${time(entry.timestamp_ms)} ${entry.title}`, async () => {
    rememberExploration();if(media.ready&&!await seek(entry.timestamp_ms))return;await speaker.say(entry.description);
  }),node('p',entry.description));
  box.append(...[...(snapshot.review.visual_only_information||[]),...(snapshot.review.highlighted_sentences||[])].map(entry=>node('p',`${time(entry.timestamp_ms)}. ${entry.description}`)));
  if(guide.overview)box.append(node('p',guide.overview));
  for (const [title, texts] of [['개념 지도', guide.concept_map || []], ['핵심 용어', (guide.glossary || []).map(g => `${g.term}: ${g.definition}`)], ['스스로 확인하기', guide.recall_questions || []]]) {
    if (texts.length) box.append(node('h5', title), ...texts.map(text => node('p', text)));
  }
}
async function save(announce = false, quiet = false, savedPosition, notifyFailure = announce) {
  if (!current) return;
  const movedPosition = savedPosition !== undefined;
  if (savedPosition === undefined && positionDirty) {
    if (!$('position').checkValidity()) {
      const error = new Error('학습 위치는 0~86400초 이내의 정수로 입력하세요.'); error.field = $('position'); throw error;
    }
    savedPosition = Number($('position').value) * 1000;
  }
  savedPosition ??= positionMs;
  const data = current, ticket = generation, revision = ++saveRevision;
  const enteredPosition = $('position').value, editRevision = positionEditRevision;
  const payload = {position_ms: Math.max(0, Math.min(86400000, Math.round(savedPosition))), note: $('note').value,
    bookmarks: structuredClone(data.progress.bookmarks), underlined: [...data.progress.underlined]};
  clearTimeout(saveTimer);
  if (!quiet && (!saveFailed || notifyFailure)) $('save-status').textContent = '학습 기록 저장 중';
  saveChain = saveChain.catch(() => {}).then(() => {
    if (ticket !== generation || current !== data) throw Object.assign(new Error('이전 화면의 저장을 취소했습니다.'), {cancelled: true});
    return request(`/local/lectures/${data.id}/progress`, {method: 'PUT', body: payload});
  });
  try { await saveChain; }
  catch (error) {
    if (ticket !== generation || current !== data || error.cancelled) throw Object.assign(error, {cancelled: true});
    const message = `아직 저장하지 못했습니다. ${error.message} 연결을 확인한 뒤 학습 기록 다시 저장을 누르세요. 이 화면을 닫으면 미저장 기록을 잃을 수 있습니다.`;
    $('save-status').textContent = message; $('retry-save').hidden = false;
    if (!saveFailed || notifyFailure) announcer.say(message);
    saveFailed = true; error.reported = true; throw error;
  }
  if (ticket !== generation || current !== data) return;
  if (revision === saveRevision) {
    data.progress = {...data.progress, position_ms: payload.position_ms, note: payload.note};
    noteDirty = $('note').value !== payload.note;
    recordsDirty = JSON.stringify([data.progress.bookmarks, data.progress.underlined]) !== JSON.stringify([payload.bookmarks, payload.underlined]);
    if (positionDirty && (movedPosition || !media.ready) && editRevision === positionEditRevision && enteredPosition === $('position').value && Number(enteredPosition) * 1000 === payload.position_ms) {
      positionDirty = false; if (!media.ready) positionMs = payload.position_ms;
    }
    const recovered = saveFailed; saveFailed = false;
    if (document.activeElement === $('retry-save')) $('progress-form').querySelector('button[type=submit]').focus();
    $('retry-save').hidden = true;
    if (announce) { $('save-status').textContent = ''; status(noteDirty||positionDirty||recordsDirty ? '이전에 입력한 기록을 저장했습니다. 새로 입력한 기록은 저장 대기 중입니다.' : '학습 위치와 메모를 저장했습니다.'); }
    else if (!quiet || recovered) {
      const message = noteDirty || positionDirty || recordsDirty ? '추가 학습 기록 저장 대기' : recovered ? '연결이 복구되어 학습 기록을 저장했습니다.' : '학습 기록 저장됨';
      $('save-status').textContent = message;
      if (recovered) announcer.say(message);
    }
  }
}
async function seek(ms,{announce=true,notifySaveFailure=false,announceSave=false}={}) {
  const selected=needLesson(),ticket=generation,editRevision=positionEditRevision;const stopping=stopAll(false),action=actionGeneration;await stopping;
  if(selected!==current||ticket!==generation||action!==actionGeneration)return false;
  if (!media.kind) throw new Error('영상 구간 이동은 영상을 연결한 뒤 사용할 수 있습니다. 자료 읽기는 계속 이용할 수 있습니다.');
  const state = await media.state();
  if(selected!==current||ticket!==generation||action!==actionGeneration)return false;
  const target = Math.max(0, Math.min(Number.isFinite(state.durationMs) ? state.durationMs : 86400000, ms));
  await media.seek(target);
  if(selected!==current||ticket!==generation||action!==actionGeneration)return false;
  positionMs = target; previousMs = null; if(editRevision===positionEditRevision)$('position').value = String(Math.round(target / 1000));
  await save(announceSave,false,target,notifySaveFailure);if(selected!==current||ticket!==generation||action!==actionGeneration)return false;
  if(announceSave)return true;
  const message=`${time(target)} 위치로 이동했습니다.`;
  if(announce)status(message);else{$('status').textContent=message;$('error').textContent='';} // A sequence announces its own explanation after playback.
  return true;
}
async function connect(openNew) {
  const selected=needLesson(),ticket=generation,account=user?.id,action=actionGeneration,view=media.view,focus=focusTicket;
  const url = selected.playback.normalized_url || selected.playback.playback_url;
  if (!url) throw new Error('이 강의에 연결할 원본 주소가 없습니다.');
  // Called directly from a user activation; permissions are limited to this source's origin.
  const granted = await chrome.permissions.request({origins: [new URL(url).origin + '/*']});
  if(ticket!==generation||selected!==current||account!==user?.id||action!==actionGeneration||view!==media.view)return;
  if (!granted) throw new Error('강의 탭 접근을 허용하지 않았습니다. 준비된 자료는 계속 읽을 수 있습니다.');
  const canRestoreFocus=focus===focusTicket,savedMs=positionMs,stopped=stopAll(false),connectingAction=actionGeneration;
  const connectionFocus=canRestoreFocus?focusTicket:null;await stopped;
  const valid=()=>ticket===generation&&selected===current&&account===user?.id&&connectingAction===actionGeneration;
  if(!valid())return;media.reset();
  $('error').textContent='';connectionNotice('강의 플레이어에 연결하고 있습니다.');
  const context={valid,openNew,savedMs,focus:connectionFocus,view:media.view};
  try{await media.connect(url,openNew);if(valid())await finishConnection(context);}
  catch(error){if(!valid()||error.cancelled)return;if(playerPermission(error,context))return;media.reset();connectionNotice(error.message);error.reported=true;throw error;}
}
async function finishConnection(context){
  const {valid,openNew,savedMs,focus}=context;
  if(!valid())return;
  if(openNew)await media.seek(savedMs);if(!valid())return;
  await media.audio(Number($('video-volume').value),$('video-muted').checked);if(!valid())return;
  media.ready=true;clearPlayerPermission();previousMs=null;
  connectionNotice('원본 강의 탭을 연결했습니다. 강의 재생을 눌러 시작하세요.');
  if(inPanel&&focus===focusTicket){window.focus();$('play').focus();}
}
async function grantPlayer(){
  const context=pendingPlayerPermission;
  if(!context||!context.valid()||context.view!==media.view){clearPlayerPermission();throw new Error('현재 강의에서 원본 연결을 다시 선택하세요.');}
  const granted=await chrome.permissions.request({origins:context.origins});
  if(!context.valid()||context.view!==media.view)return;
  if(!granted){connectionNotice('영상 제공 사이트 연결을 허용하지 않았습니다. 같은 버튼으로 다시 시도하거나 준비된 자료를 읽을 수 있습니다.');return;}
  try{await media.send('pause');if(context.valid())await finishConnection(context);}
  catch(error){if(!context.valid()||error.cancelled)return;if(playerPermission(error,context))return;clearPlayerPermission();media.reset();connectionNotice(error.message);error.reported=true;throw error;}
}
async function connectFile(file) {
  const data = needLesson(), ticket = generation, savedMs = positionMs, account = user.id;
  const stopped=stopAll(false),action=actionGeneration;await stopped;
  const valid=()=>ticket===generation&&data===current&&account===user?.id&&action===actionGeneration;
  if(!valid())return;media.reset();
  connectionNotice('선택한 원본의 식별 정보와 재생 형식을 확인하고 있습니다.');
  try{await media.local(file, data.media_identity);
  if (!valid()) return;
  await media.seek(savedMs);
  if(!valid())return;
  await media.audio(Number($('video-volume').value), $('video-muted').checked);
  if(!valid())return;
  media.captions(media.verified ? data.snapshot.transcript_segments : [], $('captions').getAttribute('aria-pressed') === 'true');
  $('caption-info').textContent = media.verified && data.snapshot.transcript_segments.length ? '준비된 시점 자막을 연결했습니다. 자막 표시 버튼으로 켜고 끌 수 있습니다.' : '동기화할 자막 또는 원본 식별 정보가 없습니다. 강의 발화 본문을 읽을 수 있습니다.';
  connectionNotice(media.verified ? '분석한 원본과 일치하는 로컬 영상입니다. 자동 해설을 사용할 수 있습니다.' : '로컬 영상 수동 재생입니다. 원본 식별 정보가 없어 자동 해설은 꺼집니다.');
  media.ready = true;
  }catch(error){if(!valid()||error.cancelled)return;media.reset();connectionNotice(error.message);error.reported=true;throw error;}
  if ($('store-original').checked) {
    status('원본 사본을 이 브라우저에 암호화 보관하고 있습니다.');
    if (!valid()) return;
    await saveOriginal(account, data.id, file); if (valid()) status('원본 사본을 이 브라우저에 암호화 보관했습니다.');
  }
  previousMs = null;
}
async function tick() {
  if (tickBusy || !current || !media.ready) return;
  tickBusy = true; const ticket = generation,view=media.view;
  try {
    const state = await media.state();
    if (ticket !== generation||view!==media.view) return;
    $('playback-state').textContent = `${time(state.positionMs)} · ${state.ad ? '광고 중: 해설과 위치 저장 일시 중단' : state.paused ? '정지' : '재생 중'}`;
    const transition = state.ad ? '광고 재생 중입니다. 해설과 위치 저장을 잠시 멈춥니다.' : state.ended ? '강의 재생이 끝났습니다.' : state.paused ? '강의를 일시정지했습니다.' : '강의를 재생하고 있습니다.';
    if (transition !== playbackStatus) { playbackStatus = transition; if (!speaker.active && !(settings.reader_mode && state.paused && $('reader-description').textContent)) $('player-status').textContent = transition; }
    if (!state.ad) {
      positionMs = state.positionMs;
      if (!positionDirty) $('position').value = String(Math.round(positionMs / 1000));
      if (Date.now() - autoSaveAt > 10000 && !positionDirty && !noteDirty) {
        autoSaveAt = Date.now();
        try{await save(false,true);}catch(error){reportError(error);}
        if(ticket!==generation||view!==media.view)return;
      }
    }
    if (state.ad || !state.verified || !Number.isFinite(state.durationMs)) { previousMs = null; return; }
    if (settings.auto_description && !state.paused && !speaker.active && !conceptRun) {
      const gap = SullivanPlayback.selectDueGap({gaps: safeGaps(), announcedIds: announced, previousMs, currentMs: positionMs});
      if (gap) { announced.add(gap.gap_id); await speaker.say(SullivanNarration.compose(gap, concepts())); }
    }
    previousMs = positionMs;
  } catch (error) {
    if (!error.cancelled&&ticket === generation&&view===media.view)loseConnection('원본 강의 연결이 끊겼습니다. 원본 탭을 다시 열거나 파일을 다시 연결해 주세요.');
  } finally { tickBusy = false; }
}
function readParagraph(p) {
  rememberExploration();
  currentParagraph = p.paragraph_id;
  sentenceIndex = lessonData.sentenceIndices.get(p.sentences[0]?.sentence_id)??0;
  renderMaterial();
  return speaker.say(SullivanPassages.paragraphSpeech(p));
}
async function paragraphCommand(query) {
  needLesson(); rememberExploration(); const allSentences = sentences();
  const indexed = query.match(/(?:(\d+)\s*문단\s*)?(\d+)\s*(?:번째\s*)?문장/);
  if (indexed) {
    const p = indexed[1] ? paragraphs().find(p => p.paragraph_index === Number(indexed[1])) : paragraphs().find(p => p.paragraph_id === currentParagraph) || paragraphs()[0];
    const sentence = p?.sentences[Number(indexed[2]) - 1];
    if (!sentence) throw new Error('요청한 문장을 찾지 못했습니다. 문단과 문장 번호를 확인하세요.');
    currentParagraph = p.paragraph_id; sentenceIndex = lessonData.sentenceIndices.get(sentence.sentence_id)??0;renderMaterial();
    return speaker.say(sentence.text);
  }
  if (/강조.*문장/.test(query)) {
    const highlighted = allSentences.filter(s => s.highlighted);
    if (!highlighted.length) throw new Error('강조 표시된 문장이 없습니다.');
    return speaker.say(highlighted.map(s => s.text).join(' '));
  }
  if (/다음\s*문장|(?:앞|이전)\s*문장|현재\s*문장/.test(query)) {
    sentenceIndex = Math.max(0, Math.min(allSentences.length - 1, sentenceIndex + (/다음/.test(query) ? 1 : /앞|이전/.test(query) ? -1 : 0)));
    const sentence = allSentences[sentenceIndex]; if (!sentence) throw new Error('탐색할 문장이 없습니다.');
    currentParagraph=lessonData.sentenceParagraphs.get(sentence.sentence_id)||currentParagraph;renderMaterial();
    return speaker.say(sentence.text);
  }
  if (/밑줄.*(?:표시|해제)/.test(query) && !/듣|읽/.test(query)) {
    const selected=current,ticket=generation;
    const p = SullivanPassages.findByOrdinal(paragraphs(), query) || paragraphs().find(p => p.paragraph_id === currentParagraph) || paragraphs()[0];
    if (!p) throw new Error('밑줄을 표시할 문단이 없습니다.');
    const set = new Set(current.progress.underlined);
    if(!/해제/.test(query)&&!set.has(p.paragraph_id)&&set.size>=100)throw new Error('밑줄은 100개까지 저장할 수 있습니다.');
    /해제/.test(query) ? set.delete(p.paragraph_id) : set.add(p.paragraph_id);
    current.progress.underlined = [...set]; recordsDirty = true; renderMaterial(); await save();if(current===selected&&ticket===generation)status(`${p.paragraph_index}문단 밑줄 ${set.has(p.paragraph_id)?'선택됨':'선택 해제됨'}. 저장했습니다.`);return;
  }
  const result = SullivanPassages.resolveCommand({paragraphs: paragraphs(), query, currentId: currentParagraph, underlinedIds: new Set(current.progress.underlined)});
  if (result.items[0]){currentParagraph = result.items[0].paragraph_id;sentenceIndex=lessonData.sentenceIndices.get(result.items[0].sentences[0]?.sentence_id)??0;renderMaterial();}
  await speaker.say(result.speech);
}
async function search(query) {
  needLesson(); const matches = SullivanConcepts.search(concepts(), query);
  rememberExploration();
  $('search-results').replaceChildren(...matches.map(concept => {
    const item = node('article'); item.append(node('h5', concept.keyword), node('p', concept.ai_explanation),
      button(`${concept.keyword} 설명 듣기`, () => speaker.say(`${concept.keyword}. ${concept.ai_explanation}`)),
      button(`${concept.keyword} 강사 구간 듣기`, () => playConcept(concept)));
    return item;
  }));
  if (!matches.length) $('search-results').append(node('p', '연결된 개념을 찾지 못했습니다.'));
  $('search-title').focus(); status(`개념 검색 결과 ${matches.length}개입니다.`);
}
function showResponse(title, text, label = '') {
  const item = node('article'); item.append(node('h5', title), node('p', label), node('p', text)); $('chat-log').append(item);
  if(settings.reader_mode)$('answer-status').textContent=`${title}. ${label}. ${text}`;
}
async function ask(message,forceSpeak=false){pendingRequests++;try{return await askImpl(message,forceSpeak);}finally{pendingRequests--;}}
async function askImpl(message, forceSpeak = false) {
  if(current&&!hasLearningMaterial()){status('내용 질문에는 자막·지문 또는 실제 분석 결과가 필요합니다. 원본 재생·중지·이동·기록 명령은 사용할 수 있습니다.');return;}
  needLesson(); rememberExploration(); const selected = current, ticket = generation, action = actionGeneration;
  const question=++questionRevision,valid=()=>ticket===generation&&current===selected&&action===actionGeneration&&question===questionRevision;
  announcer.cancel();speaker.cancel();
  status('강의 근거로 질문을 확인하고 있습니다.');
  let result;
  try {
    result = await request(`/local/lectures/${current.id}/agent-turn`, {method: 'POST', timeout: 190000, body: {message, current_time_ms: positionMs}});
  } catch (error) {
    if (!valid()) return;
    const fallback = SullivanLearning.respond(selected.snapshot, message, positionMs);
    showResponse(fallback.title, fallback.text, `준비된 자료 기반의 제한적 보조 도구입니다. ${error.message}`);
    status('실제 학습 대화에 연결하지 못해 준비된 자료 기반으로 안내했습니다.');
    if (!settings.reader_mode && (forceSpeak || $('speak-answer').checked)) await speaker.say(fallback.text);
    return;
  }
  if (!valid()) return;
  if (!result.safe_to_speak || result.confidence < .72) { status('근거가 충분하지 않아 답변을 보류했습니다.'); return; }
  showResponse(result.title, result.response_text, 'Gemini 학습 대화'); status('학습 대화 답변을 준비했습니다.');
  if (result.action === 'pause') return stopAll();
  if (result.action === 'seek' && Number.isFinite(result.target_timestamp_ms)&&!await seek(result.target_timestamp_ms))return;
  if (result.action === 'describe_current') return describe();
  if (result.action === 'replay_paragraph') {
    const text = paragraphs().filter(p => result.paragraph_indices.includes(p.paragraph_index)).map(SullivanPassages.paragraphSpeech).join(' ');
    if (text) return speaker.say(text);
  }
  if (!settings.reader_mode && (forceSpeak || $('speak-answer').checked)) await speaker.say(result.response_text);
}
async function describe() {
  needLesson(); rememberExploration(); const gap = [...safeGaps()].sort((a,b) => Math.abs(a.timestamp_ms-positionMs)-Math.abs(b.timestamp_ms-positionMs))[0];
  if (!gap) throw new Error('현재 자료에 검증된 화면 설명이 없습니다.');
  await speaker.say(`${time(gap.timestamp_ms)}에 준비된 설명입니다. ${SullivanNarration.compose(gap, concepts())}`);
}
export async function command(text, forceSpeak = false) {
  const intent = SullivanVoiceCommands.classify(text);
  if(/사용법|단축키.*알려/.test(text)){showHelp();return;}
  if(/^(?:결과\s*)?[0-9]+(?:번)?(?:\s*선택)?$/.test(text)){const item=SullivanConcepts.search(concepts(),$('search-form').elements.query.value)[Number(text.match(/[0-9]+/)[0])-1];if(item)return playConcept(item);}
  if(/원래.*(?:곳|위치)|듣던.*(?:곳|위치)/.test(text))return returnToOrigin();
  if (intent.type === 'pause') return stopAll();
  if (intent.type === 'lecture_list' || intent.type === 'home' || intent.type === 'save_home') { if (current) await save(); await stopAll(false); $('workspace-title').focus(); return; }
  if (intent.type === 'open_lecture') {
    const lesson = intent.ordinal ? lectures[intent.ordinal - 1] : lectures.find(l => l.title.includes(intent.title));
    if (!lesson) throw new Error('강의 번호 또는 제목을 확인하세요.'); return open(lesson.id);
  }
  if (intent.type === 'button') {
    const buttons = [...$('workspace').querySelectorAll('button')].filter(b => b.getClientRects().length&&!b.closest('[hidden],[inert]')&&!b.disabled&&b.getAttribute('aria-disabled')!=='true'&&!b.dataset.busy);
    const name=b=>b.getAttribute('aria-label')||(b.getAttribute('aria-labelledby')||'').split(/\s+/).map(id=>$(id)?.textContent||'').join(' ').trim()||b.textContent;
    const match = buttons.find(b => SullivanVoiceCommands.normalize(name(b)) === SullivanVoiceCommands.normalize(intent.label));
    if(!match)throw new Error('화면에 표시된 버튼 이름을 정확히 말해 주세요.');
    if(['open-original','connect-active','microphone-permission','grant-player'].includes(match.id)){match.focus();status('선택한 버튼에서 Enter를 눌러 연결 또는 마이크 허용을 계속하세요.');return;}
    match.click();return;
  }
  needLesson();
  if (intent.type === 'play' || intent.type === 'resume_lecture') {
    return startPlayback(intent.type==='resume_lecture');
  }
  if (intent.type === 'auto_narration') { settings.auto_description = intent.enabled; fillPreferences(); return savePreferences(); }
  if (intent.type === 'describe') return describe();
  if (intent.type === 'summary_audio' || intent.type === 'summary_three') {if(!hasLearningMaterial())throw new Error('요약에는 자막·지문 또는 실제 분석 결과가 필요합니다.');return speaker.say(SullivanLearning.respond(current.snapshot, '3줄 요약', positionMs).text);}
  if (intent.type === 'paragraph' || /문장|강조|지문.*흐름|전체.*지문/.test(text)) return paragraphCommand(text);
  if (intent.type === 'concept' || /찾아|검색/.test(text)) return search(text.replace(/핵심|키워드|개념|찾아\s*줘|검색해\s*줘|검색|해줘/g, '').trim() || '전체');
  if (/10초.*(?:전|뒤로)|뒤로.*10초/.test(text)) return seek(positionMs - 10000);
  if (/10초.*(?:후|앞으로)|앞으로.*10초/.test(text)) return seek(positionMs + 10000);
  if (/학습 기록|북마크|메모/.test(text)) { $('records-title').focus(); return; }
  if (intent.type === 'panel') {
    const target = {'review-panel': 'review-title', 'study-panel': 'review-title', 'chat-panel': 'chat-title', 'watch-panel': 'player-title', 'passage-panel': 'search-title', 'evidence-panel': 'evidence'}[intent.panelId];
    if (target) { $(target).closest('details')?.setAttribute('open', ''); $(target).focus(); return; }
  }
  await ask(text, forceSpeak);
}
function fillPreferences() {
  for (const key of Object.keys(defaults)) {
    const field = $('preferences-form').elements[key]; if (field.type === 'checkbox') field.checked = settings[key]; else field.value = settings[key];
  }
}
async function savePreferences() {
  const response = await request('/extension/v1/student/preferences', {method: 'PUT', body: Object.fromEntries(Object.keys(defaults).map(key => [key, settings[key]]))});
  applySettings(response.settings); fillPreferences();
  device = {voice_uri: $('speech-voice').value, speech_pitch: Number($('speech-pitch').value),speech_style:$('speech-style').value};
  await chrome.storage.local.set({[`keys:${user.id}`]: {keymap:2,space: $('space-enabled').checked, voice_consent:$('voice-consent').checked, ...device}});
  status('내 학습 설정을 저장했습니다.');
}
function capturePlayback(){
  const playing=speaker.resumeIntent?.fence===media.fence&&speaker.resumeIntent.playing;
  return current&&media.ready?media.state({allowPause:true}).then(state=>({...state,paused:state.paused&&!playing})).catch(()=>({paused:true})):Promise.resolve({paused:true});
}
function openDialog(reason = '명령을 입력하고 Enter로 실행하세요. Esc는 취소입니다.',previous=capturePlayback()) {
  const context={lesson:current?.id,view:media.view,generation};
  const stopped=stopAll(false);dialogFocus=document.activeElement;
  dialogResume={...context,action:actionGeneration,fence:media.fence,previous,stopped};
  $('dialog-help').textContent=reason;
  $('text-dialog').returnValue='';$('text-command').value='';
  if(!$('text-dialog').open)$('text-dialog').showModal();$('text-command').focus();
}

function startVoice(previous=capturePlayback()) {
  if (recognition) { recognition.stop(); return; }
  if (!$('voice-consent').checked) {
    stopAll(false);voiceFallback={previous,view:media.view,lesson:current?.id,generation};dialogFocus=document.activeElement;
    $('voice-permission-dialog').showModal();$('allow-voice').focus();return;
  }
  const Recognizer = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognizer) { openDialog('음성 인식을 지원하지 않아 타자 명령을 열었습니다. 명령을 입력하고 Enter로 실행하세요.',previous); return; }
  stopAll(false); const ticket = ++voiceGeneration; let transcript = '';
  recognition = new Recognizer(); recognition.lang = 'ko-KR'; recognition.interimResults = true;
  recognition.continuous=false;
  recognition.onstart=()=>{voiceReadyCue();$('voice-status').textContent='명령을 말해 주세요. 말한 뒤 Space를 떼면 실행합니다.';};
  recognition.onresult = event => { transcript = [...event.results].map(result => result[0].transcript).join(' '); };
  recognition.onerror = () => { if (ticket === voiceGeneration) { stopVoice(); openDialog('마이크를 사용할 수 없어 타자 명령을 열었습니다. 명령을 입력하고 Enter로 실행하세요.',previous); } };
  recognition.onend = () => {
    if (ticket !== voiceGeneration) return;
    recognition = null; $('voice').textContent = '음성 명령 시작';
    if (transcript.trim()) command(transcript, true).catch(reportError);
    else $('voice-status').textContent = '인식된 명령이 없습니다. 다시 말하거나 타자로 입력하세요.';
  };
  try { recognition.start(); $('voice').textContent = '음성 명령 마치기'; $('voice-status').textContent = '명령을 말한 뒤 버튼을 다시 누르거나 길게 누른 Space를 떼세요.'; }
  catch { stopVoice(); openDialog('음성 인식을 시작하지 못해 타자 명령을 열었습니다. 명령을 입력하고 Enter로 실행하세요.',previous); }
}
async function prepareMicrophone(){
  if(!navigator.mediaDevices?.getUserMedia)throw new Error('이 화면에서 마이크 권한을 요청할 수 없습니다. 전체 수강 화면에서 마이크를 허용하세요.');
  const stream=await navigator.mediaDevices.getUserMedia({audio:true});stream.getTracks().forEach(track=>track.stop());
}
$('microphone-permission').addEventListener('click',()=>task($('microphone-permission'),async()=>{
  if(!$('voice-consent').checked){dialogFocus=document.activeElement;$('voice-permission-dialog').showModal();$('allow-voice').focus();return;}
  const ticket=++microphoneGeneration,account=user?.id,lesson=current?.id;await prepareMicrophone();
  if(ticket===microphoneGeneration&&account===user?.id&&lesson===current?.id)$('voice-status').textContent='마이크를 허용했습니다. Space를 3초 누르고 명령을 말한 뒤 떼세요.';
}));
$('allow-voice').addEventListener('click',()=>task($('allow-voice'),async()=>{
  $('voice-consent').checked=true;$('voice-consent').dispatchEvent(new Event('change'));
  const ticket=++microphoneGeneration,account=user?.id,lesson=current?.id;
  const valid=()=>ticket===microphoneGeneration&&$('voice-permission-dialog').open&&account===user?.id&&lesson===current?.id;
  const fallback=voiceFallback,previous=fallback&&fallback.view===media.view&&fallback.lesson===current?.id&&fallback.generation===generation?fallback.previous:capturePlayback();
  try{await prepareMicrophone();if(!valid())return;$('voice-permission-dialog').close();startVoice(previous);}
  catch(error){if(!valid())return;$('voice-permission-dialog').close();openDialog('마이크 사용을 허용하지 못했습니다. Chrome의 마이크 권한을 확인하거나 명령을 입력하세요.',previous);}
}));
$('cancel-voice-permission').addEventListener('click',()=>$('voice-permission-dialog').close());
$('voice-permission-dialog').addEventListener('close',()=>{voiceFallback=null;microphoneGeneration++;if(dialogFocus?.isConnected&&dialogFocus.getClientRects().length)dialogFocus.focus();});
async function startPlayback(returnToSaved=false){
  const selected=needLesson(),ticket=generation,stopped=stopAll(false),action=actionGeneration,fence=media.fence;
  const valid=()=>selected===current&&ticket===generation&&action===actionGeneration&&fence===media.fence;
  await stopped;if(!valid())return;
  if(returnToSaved&&originMs!==null){await media.seek(originMs);if(!valid())return;originMs=null;$('return-origin').disabled=true;}
  await media.play(fence);
}
async function togglePlayback(){
  needLesson();const action=actionGeneration,ticket=generation;const state=await media.state();
  if(action!==actionGeneration||ticket!==generation)return;
  if(!state.paused)return stopAll();
  await startPlayback();
}
let sequencePrevious=null;
const sequence=SullivanSpaceGesture.create({holdMs:3000,hold:startVoice,release:()=>recognition?.stop(),
  doubleTap:()=>stopAll().catch(reportError),taps:count=>{
    if(count>=3)openDialog(undefined,sequencePrevious);else if(count===1)togglePlayback().catch(reportError);sequencePrevious=null;
  }});
const gesture={down(){sequencePrevious??=capturePlayback();sequence.down();},up(){sequence.up();},cancel(){sequence.cancel();sequencePrevious=null;}};
const keyboard=installStudentKeyboard({gesture,enabled:()=>$('space-enabled').checked,hasLesson:()=>Boolean(current),active:()=>Boolean(user),outputActive:()=>speaker.active||Boolean(recognition)||pendingRequests>0,
  emergencyStop:()=>stopAll().catch(reportError),abortGesture:event=>{
    // Finishing recognition through its own button must submit, rather than abort, the transcript.
    if(event?.target?.closest?.('#voice')&&(['pointerdown','focusin'].includes(event.type)||(event.type==='keydown'&&event.key==='Enter')))return;
    stopVoice();
  },
  onError:reportError,seek,position:()=>positionMs,
  releasePanel:()=>{stopAll(false);$('panel-keyboard').textContent='패널 키보드 모드 다시 시작';status('패널 키보드 모드를 해제했습니다. F6 또는 Tab으로 브라우저 영역으로 이동할 수 있습니다.');},
  onFocus:()=>{$('panel-keyboard').textContent='패널 키보드 모드 사용 중';}
});
window.addEventListener('blur',()=>{announcer.cancel();if(recognition)stopVoice();});
for(const event of ['keydown','pointerdown','input'])document.addEventListener(event,()=>{if(!suppressFocus)focusTicket++;},true);
document.addEventListener('focusin',event=>{
  if(suppressFocus||(dialogResume&&!$('text-dialog').open))return;
  focusTicket++;
  if(!event.target.matches?.('button,a[href],summary,input,textarea,select,[tabindex="-1"]'))return;
  if(settings.reader_mode&&current&&media.ready){cancelConcept();speaker.cancel();media.pause().catch(reportError);return;}
  announcer.say(controlDescription(event.target));
});
document.addEventListener('toggle',event=>{
  if(event.target.tagName==='DETAILS'&&document.activeElement===event.target.querySelector('summary'))announcer.say(controlDescription(document.activeElement));
},true);
document.addEventListener('change',event=>{
  if(event.target.matches('input[type=checkbox],select')&&event.target===document.activeElement)announcer.say(controlDescription(event.target));
  if(event.target.matches('input[name=speech_rate],input[name=speech_volume],#speech-pitch,#video-volume'))announceNumber(event.target,true);
});
let numberAnnouncement;
function announceNumber(element,immediate=false){
  clearTimeout(numberAnnouncement);const focus=focusTicket,ticket=generation;
  const say=()=>{if(element===document.activeElement&&focus===focusTicket&&ticket===generation&&element.checkValidity())announcer.say(controlDescription(element));};
  if(immediate)say();else numberAnnouncement=setTimeout(say,180);
}
document.addEventListener('input',event=>{if(event.target.matches('input[name=speech_rate],input[name=speech_volume],#speech-pitch,#video-volume'))announceNumber(event.target);});
window.addEventListener('sullivan-status',event=>announcer.say(event.detail.text));
$('voice-test').addEventListener('click',()=>{
  if(settings.reader_mode){status('외부 스크린리더 모드입니다. 앱 음성을 시험하려면 앱 음성 안내를 선택하세요.');return;}
  speaker.cancel(true);announcer.say('Sullivan 학생 음성 안내입니다. Tab은 다음 항목, Shift는 이전 항목입니다. 스페이스 한 번은 영상 재생과 정지, 두 번은 전체 중지, 세 번은 텍스트 명령, 3초 누르기는 음성 명령입니다.',{force:true});
});
$('access-mode').addEventListener('change',async()=>{
  announcer.cancel();speaker.cancel();
  accessSaved.reader_mode=$('access-mode').value==='reader';accessSaved.focus_voice=$('access-mode').value==='app';
  Object.assign(settings,accessSaved);fillPreferences();
  await chrome.storage.local.set({'student-accessibility':accessSaved});
  status(settings.reader_mode?'외부 스크린리더 모드입니다. 앱 음성을 끄고 결과를 읽기 영역으로 안내합니다.':settings.focus_voice?'앱 음성 안내를 켰습니다.':'초점과 상태의 앱 음성 안내를 껐습니다. 자료 듣기 버튼은 계속 사용할 수 있습니다.');
});
$('panel-keyboard').addEventListener('click',()=>{keyboard.enter();$('workspace').hidden?$('oauth-login').focus():$('workspace-title').focus();});
chrome.runtime.onMessage.addListener(message => {
  if(message.type==='student-focus-panel'&&inPanel){window.focus();keyboard.enter();const target=$('workspace').hidden?$('oauth-login'):current?$('lesson-title'):$('workspace-title');target.focus();}
  if (message.type === 'student-stop') { if (Number.isSafeInteger(message.fence)) media.fence = Math.max(media.fence, message.fence); stopAll().catch(() => {}); }
  if (message.type === 'student-lease-lost' && message.view === media.view)loseConnection('다른 수강 화면에서 재생을 시작했습니다. 이 화면에서 연결하면 다시 사용할 수 있습니다.');
});
function action(id, handler) { $(id).addEventListener('click', () => task($(id), handler)); }
action('refresh', async () => { await refresh(); status('강의 목록을 갱신했습니다.'); });
action('resume', async () => { const state = await chrome.storage.local.get(`last:${user.id}`); const id = state[`last:${user.id}`]; if (!lectures.some(l => l.id === id)) throw new Error('최근 강의가 없거나 배정이 끝났습니다. 목록에서 선택하세요.'); await open(id); });
action('full-view', () => chrome.tabs.create({url: chrome.runtime.getURL('index.html') + (current ? `?lecture=${current.id}` : '')}));
action('open-original', () => connect(true)); action('connect-active', () => connect(false));
action('grant-player',grantPlayer);
action('disconnect', async () => { await stopAll(false); media.reset(); connectionNotice('영상 연결을 해제했습니다.'); });
action('connect-file', () => connectFile($('local-file').files[0]));
action('captions', () => { const enabled = $('captions').getAttribute('aria-pressed') !== 'true'; $('captions').setAttribute('aria-pressed', String(enabled)); for (const track of $('local-video').textTracks) track.mode = enabled ? 'showing' : 'hidden'; status(enabled ? '로컬 자막 표시를 켰습니다.' : '로컬 자막 표시를 껐습니다.'); });
$('video-volume').addEventListener('change', () => media.audio(Number($('video-volume').value), $('video-muted').checked).catch(error => status(error.message, true)));
$('video-muted').addEventListener('change', () => media.audio(Number($('video-volume').value), $('video-muted').checked).catch(error => status(error.message, true)));
action('load-original', async () => {
  const lesson = needLesson(), account = user.id, ticket = generation;
  const file = await loadOriginal(account, lesson.id);
  if (ticket !== generation || user?.id !== account || current?.id !== lesson.id) return;
  await connectFile(file);
});
action('remove-original', async () => { needLesson(); await removeOriginal(user.id, current.id); status('이 브라우저의 보관 사본을 삭제했습니다. 선택한 원본 파일은 삭제하지 않았습니다.'); });
action('play',()=>startPlayback());
action('stop', () => stopAll()); action('describe', describe);
action('back', () => seek(Math.max(0, positionMs - 10000))); action('forward', () => seek(positionMs + 10000));
action('return-origin',returnToOrigin);
action('read', () => { needLesson();rememberExploration(); return speaker.say([...(current.snapshot.review.core_summary || []), ...paragraphs().map(SullivanPassages.paragraphSpeech), ...safeGaps().map(g => g.public_description)].join(' ')); });
action('read-underlined', () => paragraphCommand('밑줄 친 문단'));
action('voice', startVoice); action('type-command', openDialog);
action('run-tool', async () => { needLesson(); if(!hasLearningMaterial()){status('학습 도구에는 자막·지문 또는 실제 분석 결과가 필요합니다.');return;} const result = SullivanLearning.respond(current.snapshot, $('learning-tool').value, positionMs); showResponse(result.title, result.text, '준비된 자료 기반 학습 도구'); if (!settings.reader_mode&&$('speak-answer').checked) await speaker.say(result.text); else { if(!settings.reader_mode)$('chat-log').focus(); status('학습 도구를 만들었습니다. 결과를 읽어 주세요.'); } });
action('bookmark', async () => { needLesson(); if (current.progress.bookmarks.length >= 100) throw new Error('북마크는 100개까지 저장할 수 있습니다.'); current.progress.bookmarks.push({id: crypto.randomUUID(), timestamp_ms: positionMs, note: `${time(positionMs)} 북마크`}); recordsDirty = true; renderRecords(); await save(); status('현재 위치를 북마크했습니다.'); });
action('export-notes', () => {
  needLesson(); const guide = current.snapshot.study_guide;
  const text = [`# ${current.title}`, '', ...current.snapshot.review.core_summary, '', '## 개념 지도', ...guide.concept_map, '', '## 핵심 용어', ...guide.glossary.map(g => `- ${g.term}: ${g.definition}`), '', '## 확인 질문', ...guide.recall_questions, '', '## 내 메모', $('note').value, '', '## 북마크', ...current.progress.bookmarks.map(b => `- ${time(b.timestamp_ms)} ${b.note || ''}`)].join('\n');
  const url = URL.createObjectURL(new Blob([text], {type: 'text/markdown;charset=utf-8'})), link = node('a', '', {href: url, download: 'sullivan-study-notes.md'});
  link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); status('학습 노트 파일을 내보냈습니다.');
});
bindForm('command-form', async ({command: text}) => { await command(text); });
bindForm('paragraph-form', async ({query}) => paragraphCommand(query));
bindForm('search-form', async ({query}) => search(query));
bindForm('chat-form', async ({question}) => ask(question));
bindForm('dialog-form', async ({command: text}) => {
  const closed = new Promise(resolve => $('text-dialog').addEventListener('close', resolve, {once: true}));
  $('text-dialog').close('execute'); await closed; await command(text);
});
$('close-dialog').addEventListener('click', () => $('text-dialog').close());
$('text-dialog').addEventListener('close',async()=>{
  const restore=dialogResume;dialogResume=null;
  if(!restore||restore.generation!==generation||restore.lesson!==current?.id||restore.view!==media.view)return;
  announcer.cancel();speaker.cancel();
  suppressFocus=true;if(dialogFocus?.isConnected&&dialogFocus.getClientRects().length)dialogFocus.focus();else $('command-title').focus();suppressFocus=false;
  const focus=focusTicket;
  if($('text-dialog').returnValue==='execute'||!restore)return;
  await restore.stopped;const state=await restore.previous;
  if(!state.paused&&focus===focusTicket&&restore.lesson===current?.id&&restore.view===media.view&&restore.generation===generation&&restore.action===actionGeneration&&restore.fence===media.fence)await media.play(restore.fence).catch(reportError);
});
bindForm('preferences-form', async () => {
  const form = $('preferences-form');
  settings = Object.fromEntries(Object.keys(defaults).map(key => [key, form.elements[key].type === 'checkbox' ? form.elements[key].checked : Number(form.elements[key].value)]));
  if (settings.reader_mode) settings.focus_voice = false;
  accessSaved.reader_mode=settings.reader_mode;accessSaved.focus_voice=settings.focus_voice;
  await chrome.storage.local.set({'student-accessibility':accessSaved});
  announcer.cancel();speaker.cancel(); await savePreferences();
});
async function saveProgress() {
  needLesson(); const selected=current,ticket=generation;
  if (!$('position').checkValidity()) { const error=new Error('학습 위치는 0~86400초 이내의 정수로 입력하세요.');error.field=$('position');throw error; }
  if (media.kind && positionDirty) {
    await seek(Number($('position').value) * 1000,{announce:false,notifySaveFailure:true,announceSave:true});return;
  }
  if (current===selected&&ticket===generation) await save(true);
}
bindForm('progress-form', saveProgress);
action('retry-save', saveProgress);
$('position').addEventListener('input', () => { positionDirty = true; positionEditRevision++; });
$('note').addEventListener('input', () => { noteDirty = true; clearTimeout(saveTimer); saveTimer = setTimeout(() => save().catch(reportError), 700); });
window.addEventListener('pagehide', () => { announcer.cancel(); speaker.cancel(); stopVoice(); media.reset(); });
setInterval(tick, 500);
function voices(reset=false) {
  const selected=reset?device.voice_uri:$('speech-voice').value;
  const list = SullivanSpeechProfile.voices(window.speechSynthesis?.getVoices?.() || []);
  $('speech-voice').replaceChildren(node('option', '자연스러운 한국어 음성 자동 선택', {value: ''}), ...list.map(voice => node('option', voice.name, {value: voice.voiceURI})));
  if (list.some(voice => voice.voiceURI === selected)) $('speech-voice').value = selected;
}
window.speechSynthesis?.addEventListener?.('voiceschanged',()=>voices());
await chrome.storage.local.setAccessLevel({accessLevel: 'TRUSTED_CONTEXTS'});
applySettings();
$('voice-consent').addEventListener('change',async()=>{if(!$('voice-consent').checked)stopVoice();if(user){const key=`keys:${user.id}`;const saved=(await chrome.storage.local.get(key))[key]||{};await chrome.storage.local.set({[key]:{...saved,voice_consent:$('voice-consent').checked}});}});
await boot(async account => {
  user = account; applySettings(account.settings); fillPreferences();
  const local = await chrome.storage.local.get(`keys:${user.id}`);
  device = {voice_uri: local[`keys:${user.id}`]?.voice_uri || '', speech_pitch: local[`keys:${user.id}`]?.speech_pitch || 1,speech_style:local[`keys:${user.id}`]?.speech_style||'warm'};
  voices(true); $('speech-pitch').value = String(device.speech_pitch);$('speech-style').value=device.speech_style;
  $('space-enabled').checked = local[`keys:${user.id}`]?.keymap===2 ? local[`keys:${user.id}`].space!==false : true;
  $('voice-consent').checked=Boolean(local[`keys:${user.id}`]?.voice_consent);
  await refresh();
  await refreshConnections();
  if(!account.onboarded)showHelp(false);
  const requested = new URL(location.href).searchParams.get('lecture');
  if (requested && lectures.some(l => l.id === requested)) await open(requested);
}, () => { clear();$('onboarding-card').hidden=true; user = null; lectures = []; pairRequest=null;$('pair-preview').hidden=true;$('student-unlink-confirm').hidden=true;$('my-connections').replaceChildren();$('pair-preview-form').reset();$('lectures').replaceChildren(); },{beforeUserFocus:account=>{announcer.cancel();speaker.cancel();applySettings(account.settings);}});
