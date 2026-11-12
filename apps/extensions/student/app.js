import {request} from './client.js';
import {$, node, button, bindForm, status, task, boot} from './ui.js';
import {StudentMedia} from './media.js';
import {StudentSpeech} from './speech.js';
import {saveOriginal, loadOriginal, removeOriginal} from './media-store.js';
import './playback-scheduler.js';
import './narration-context.js';
import './passage-tools.js';
import './concept-tools.js';
import './voice-command-router.js';
import './space-gesture.js';
import './learning-response.js';

let current = null, user = null, lectures = [], generation = 0, actionGeneration = 0;
let positionMs = 0, previousMs = null, originMs = null, currentParagraph = null, sentenceIndex = 0;
let announced = new Set(), tickBusy = false, saveChain = Promise.resolve(), saveTimer, autoSaveAt = 0;
let noteDirty = false, positionDirty = false, saveRevision = 0, recognition = null, voiceGeneration = 0;
let dialogFocus = null, focusTicket = 0;
let playbackStatus = '';
let pairRequest = null;
const defaults = {speech_rate: .95, speech_volume: .9, auto_description: true, reader_mode: false, focus_voice: false};
let settings = {...defaults};
let device = {voice_uri: '', speech_pitch: 1};
const media = new StudentMedia($('local-video'));
const speaker = new StudentSpeech(media, () => ({...settings, ...device}), text => {
  $('current-description').textContent = text;
  $('reader-description').textContent = settings.reader_mode ? `강의를 일시정지했습니다. ${text} 계속 들으려면 강의 재생을 누르세요.` : '';
});
const time = ms => `${Math.floor(ms / 60000)}분 ${Math.floor(ms / 1000) % 60}초`;
const paragraphs = () => SullivanPassages.paragraphsForSnapshot(current?.snapshot || {});
const concepts = () => SullivanConcepts.conceptsForSnapshot(current?.snapshot || {});
const safeGaps = () => (current?.snapshot.visual_gaps || []).filter(g => g.safe_to_speak && g.confidence >= .72 && g.public_description && !['HOLD','SKIP'].includes(g.action) && !(current.snapshot.session.problem_mode && g.kind === 'answer'));
function needLesson() { if (!current) throw new Error('강의를 먼저 선택하세요.'); return current; }
function stopVoice() {
  voiceGeneration++;
  if (recognition) { recognition.onresult = recognition.onend = recognition.onerror = null; try { recognition.abort(); } catch {} }
  recognition = null; $('voice').textContent = '음성 명령 시작';
}
export async function stopAll(announce = true) {
  actionGeneration++; focusTicket++; speaker.cancel(); stopVoice();
  await media.pause().catch(() => {});
  if (announce) status('영상과 앱 음성을 모두 중지했습니다.');
}
function clear() {
  generation++; actionGeneration++; focusTicket++; speaker.cancel(); stopVoice(); clearTimeout(saveTimer);
  gesture.cancel(); media.reset(); current = null; positionMs = 0; previousMs = null; originMs = null;
  announced = new Set(); noteDirty = positionDirty = false;
  playbackStatus = ''; $('reader-description').textContent = ''; $('local-file').value = ''; $('store-original').checked = false;
  $('lesson').hidden = true; $('return-origin').disabled = true;
  for (const id of ['material','search-results','chat-log','review','evidence','bookmarks']) $(id).replaceChildren();
  $('note').value = ''; $('position').value = '0'; $('connection').textContent = '영상을 아직 연결하지 않았습니다.';
  $('current-description').textContent = ''; $('save-status').textContent = '';
  if ($('text-dialog').open) $('text-dialog').close();
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
  const ticket = generation;
  const list = await request('/local/lectures');
  if (ticket !== generation) return;
  lectures = list;
  if (current && !list.some(l => l.id === current.id)) {
    const removed = $('lesson').contains(document.activeElement);
    clear(); if (removed) $('workspace-title').focus();
  }
  const focused = document.activeElement?.dataset.lecture;
  $('lectures').replaceChildren(...list.map(l => {
    const item = node('li'), control = button(`${l.title} 열기`, () => open(l.id));
    control.dataset.lecture = l.id; item.append(control); return item;
  }));
  if (focused) [...$('lectures').querySelectorAll('button')].find(b => b.dataset.lecture === focused)?.focus();
  if (!list.length) $('lectures').append(node('li', '아직 배정된 강의가 없습니다. 보호자에게 배정을 요청하세요.'));
}
async function open(id) {
  if (current && (noteDirty || positionDirty)) await save(true);
  clear(); $('workspace-title').focus(); const ticket = generation;
  const data = await request(`/extension/v1/student/lectures/${id}`);
  if (ticket !== generation) return;
  current = data; current.progress = {bookmarks: [], underlined: [], ...data.progress};
  settings = {...defaults, ...data.settings}; fillPreferences();
  positionMs = data.progress.position_ms || 0;
  $('lesson-title').textContent = data.title; $('source-label').textContent = data.snapshot.session.source_label;
  $('position').value = String(Math.round(positionMs / 1000)); $('note').value = data.progress.note || '';
  renderMaterial(); renderRecords(); renderReview();
  $('open-original').disabled = !['youtube','direct'].includes(data.playback.kind);
  $('connect-active').disabled = $('open-original').disabled;
  $('lesson').hidden = false; $('lesson-title').focus();
  await chrome.storage.local.set({[`last:${user.id}`]: id});
  status('준비된 자료를 열었습니다. 영상은 연결한 뒤 직접 재생하세요.');
}
function renderMaterial() {
  const box = $('material'); box.replaceChildren();
  const article = (title, texts) => {
    if (!texts.length) return;
    const section = node('article'); section.append(node('h4', title), ...texts.map(text => node('p', text))); box.append(section);
  };
  article('강의 요약', current.snapshot.review.core_summary || []);
  for (const p of paragraphs()) {
    const section = node('article'); section.append(node('h4', `${p.paragraph_index}문단 · ${p.flow_role}`), node('p', p.text));
    section.append(button(`${p.paragraph_index}문단 듣기`, () => readParagraph(p)), button(`${p.paragraph_index}문단 강의 구간`, () => seek(p.timestamp_ms)));
    const marked = current.progress.underlined.includes(p.paragraph_id);
    const mark = button(`${p.paragraph_index}문단 밑줄 ${marked ? '해제' : '표시'}`, async () => {
      const set = new Set(current.progress.underlined);
      if (!set.has(p.paragraph_id) && set.size >= 100) throw new Error('밑줄은 100개까지 저장할 수 있습니다.');
      set.has(p.paragraph_id) ? set.delete(p.paragraph_id) : set.add(p.paragraph_id);
      current.progress.underlined = [...set]; renderMaterial();
      [...box.querySelectorAll('button')].find(b => b.dataset.paragraph === p.paragraph_id)?.focus();
      await save(); status('문단 밑줄을 저장했습니다.');
    });
    mark.setAttribute('aria-pressed', String(marked)); mark.dataset.paragraph = p.paragraph_id; section.append(mark); box.append(section);
  }
  article('검증된 화면 설명', safeGaps().map(g => `${time(g.timestamp_ms)}. ${g.public_description}`));
  article('강의 발화', current.snapshot.transcript_segments.map(s => s.text));
  if (!box.childElementCount) box.append(node('p', '표시할 준비된 자료가 없습니다.'));
  $('evidence').replaceChildren(node('h4', '설명 판단 근거'), ...current.snapshot.visual_gaps.map(g => node('p', `${time(g.timestamp_ms)}: ${g.action}. ${g.reason}`)));
}
function renderRecords() {
  $('bookmarks').replaceChildren(...current.progress.bookmarks.map((entry, index) => {
    const item = node('li');
    item.append(button(`${time(entry.timestamp_ms || 0)} ${entry.note || '북마크'}`, () => seek(entry.timestamp_ms || 0)),
      button(`${index + 1}번 북마크 삭제`, async () => {
        current.progress.bookmarks.splice(index, 1); renderRecords(); $('records-title').focus(); await save();
      })); return item;
  }));
  if (!current.progress.bookmarks.length) $('bookmarks').append(node('li', '저장한 북마크가 없습니다.'));
}
function renderReview() {
  const snapshot = current.snapshot, guide = snapshot.study_guide;
  const box = $('review'); box.replaceChildren(...(snapshot.review.core_summary || []).map(s => node('p', s)));
  for (const entry of snapshot.review.key_segments || []) box.append(button(`${time(entry.timestamp_ms)} ${entry.title}`, async () => {
    await seek(entry.timestamp_ms); await speaker.say(entry.description);
  }));
  for (const [title, texts] of [['개념 지도', guide.concept_map || []], ['핵심 용어', (guide.glossary || []).map(g => `${g.term}: ${g.definition}`)], ['스스로 확인하기', guide.recall_questions || []]]) {
    if (texts.length) box.append(node('h5', title), ...texts.map(text => node('p', text)));
  }
}
async function save(announce = false, quiet = false) {
  if (!current) return;
  const data = current, ticket = generation, revision = ++saveRevision;
  const payload = {position_ms: Math.max(0, Math.min(86400000, Math.round(positionMs))), note: $('note').value,
    bookmarks: structuredClone(data.progress.bookmarks), underlined: [...data.progress.underlined]};
  if (!quiet) $('save-status').textContent = '학습 기록 저장 중';
  saveChain = saveChain.catch(() => {}).then(() => request(`/local/lectures/${data.id}/progress`, {method: 'PUT', body: payload}));
  await saveChain;
  if (ticket !== generation || current !== data) return;
  if (revision === saveRevision) { data.progress = payload; noteDirty = $('note').value !== payload.note; if (!quiet) $('save-status').textContent = noteDirty ? '추가 메모 저장 대기' : '학습 기록 저장됨'; }
  if (announce) status('학습 위치와 메모를 저장했습니다.');
}
async function seek(ms) {
  needLesson(); await stopAll(false);
  if (!media.kind) throw new Error('영상 구간 이동은 영상을 연결한 뒤 사용할 수 있습니다. 자료 읽기는 계속 이용할 수 있습니다.');
  const state = await media.state();
  const target = Math.max(0, Math.min(Number.isFinite(state.durationMs) ? state.durationMs : 86400000, ms));
  await media.seek(target); positionMs = target; previousMs = null; $('position').value = String(Math.round(target / 1000));
  await save(); status(`${time(target)} 위치로 이동했습니다.`);
}
async function connect(openNew) {
  needLesson(); const url = current.playback.normalized_url || current.playback.playback_url;
  if (!url) throw new Error('이 강의에 연결할 원본 주소가 없습니다.');
  // Called directly from a user activation; permissions are limited to this source's origin.
  const granted = await chrome.permissions.request({origins: [new URL(url).origin + '/*']});
  if (!granted) throw new Error('강의 탭 접근을 허용하지 않았습니다. 준비된 자료는 계속 읽을 수 있습니다.');
  const ticket = generation, savedMs = positionMs;
  await stopAll(false); media.reset();
  status('강의 플레이어에 연결하고 있습니다.');
  await media.connect(url, openNew);
  if (ticket !== generation) return;
  if (openNew) await media.seek(savedMs);
  await media.audio(Number($('video-volume').value), $('video-muted').checked);
  media.ready = true;
  $('connection').textContent = '원본 강의 탭을 연결했습니다. 강의 재생을 눌러 시작하세요.'; previousMs = null;
}
async function connectFile(file) {
  const data = needLesson(), ticket = generation, savedMs = positionMs, account = user.id;
  await stopAll(false); media.reset();
  $('connection').textContent = '선택한 원본의 식별 정보와 재생 형식을 확인하고 있습니다.';
  await media.local(file, data.media_identity);
  if (ticket !== generation) return;
  await media.seek(savedMs);
  await media.audio(Number($('video-volume').value), $('video-muted').checked);
  media.captions(media.verified ? data.snapshot.transcript_segments : [], $('captions').getAttribute('aria-pressed') === 'true');
  $('caption-info').textContent = media.verified && data.snapshot.transcript_segments.length ? '준비된 시점 자막을 연결했습니다. 자막 표시 버튼으로 켜고 끌 수 있습니다.' : '동기화할 자막 또는 원본 식별 정보가 없습니다. 강의 발화 본문을 읽을 수 있습니다.';
  $('connection').textContent = media.verified ? '분석한 원본과 일치하는 로컬 영상입니다. 자동 해설을 사용할 수 있습니다.' : '로컬 영상 수동 재생입니다. 원본 식별 정보가 없어 자동 해설은 꺼집니다.';
  media.ready = true;
  if ($('store-original').checked) {
    status('원본 사본을 이 브라우저에 암호화 보관하고 있습니다.');
    if (ticket !== generation) return;
    await saveOriginal(account, data.id, file); if (ticket === generation) status('원본 사본을 이 브라우저에 암호화 보관했습니다.');
  }
  previousMs = null;
}
async function tick() {
  if (tickBusy || !current || !media.ready) return;
  tickBusy = true; const ticket = generation;
  try {
    const state = await media.state();
    if (ticket !== generation) return;
    $('playback-state').textContent = `${time(state.positionMs)} · ${state.ad ? '광고 중: 해설과 위치 저장 일시 중단' : state.paused ? '정지' : '재생 중'}`;
    const transition = state.ad ? '광고 재생 중입니다. 해설과 위치 저장을 잠시 멈춥니다.' : state.ended ? '강의 재생이 끝났습니다.' : state.paused ? '강의를 일시정지했습니다.' : '강의를 재생하고 있습니다.';
    if (transition !== playbackStatus) { playbackStatus = transition; if (!speaker.active && !(settings.reader_mode && state.paused && $('reader-description').textContent)) $('player-status').textContent = transition; }
    if (!state.ad) {
      positionMs = state.positionMs;
      if (!positionDirty) $('position').value = String(Math.round(positionMs / 1000));
      if (Date.now() - autoSaveAt > 10000 && !positionDirty && !noteDirty) { autoSaveAt = Date.now(); await save(false, true); }
    }
    if (state.ad || !state.verified || !Number.isFinite(state.durationMs)) { previousMs = null; return; }
    if (settings.auto_description && !state.paused && !speaker.active) {
      const gap = SullivanPlayback.selectDueGap({gaps: safeGaps(), announcedIds: announced, previousMs, currentMs: positionMs});
      if (gap) { announced.add(gap.gap_id); await speaker.say(SullivanNarration.compose(gap, concepts())); }
    }
    previousMs = positionMs;
  } catch (error) {
    if (ticket === generation) { speaker.cancel(); media.reset(); $('connection').textContent = error.message; }
  } finally { tickBusy = false; }
}
function readParagraph(p) {
  currentParagraph = p.paragraph_id;
  sentenceIndex = Math.max(0, paragraphs().flatMap(p => p.sentences).findIndex(s => s.sentence_id === p.sentences[0]?.sentence_id));
  return speaker.say(SullivanPassages.paragraphSpeech(p));
}
async function paragraphCommand(query) {
  needLesson(); const sentences = paragraphs().flatMap(p => p.sentences);
  const indexed = query.match(/(?:(\d+)\s*문단\s*)?(\d+)\s*(?:번째\s*)?문장/);
  if (indexed) {
    const p = indexed[1] ? paragraphs().find(p => p.paragraph_index === Number(indexed[1])) : paragraphs().find(p => p.paragraph_id === currentParagraph) || paragraphs()[0];
    const sentence = p?.sentences[Number(indexed[2]) - 1];
    if (!sentence) throw new Error('요청한 문장을 찾지 못했습니다. 문단과 문장 번호를 확인하세요.');
    currentParagraph = p.paragraph_id; sentenceIndex = sentences.findIndex(s => s.sentence_id === sentence.sentence_id);
    return speaker.say(sentence.text);
  }
  if (/강조.*문장/.test(query)) {
    const highlighted = sentences.filter(s => s.highlighted);
    if (!highlighted.length) throw new Error('강조 표시된 문장이 없습니다.');
    return speaker.say(highlighted.map(s => s.text).join(' '));
  }
  if (/다음\s*문장|(?:앞|이전)\s*문장|현재\s*문장/.test(query)) {
    sentenceIndex = Math.max(0, Math.min(sentences.length - 1, sentenceIndex + (/다음/.test(query) ? 1 : /앞|이전/.test(query) ? -1 : 0)));
    const sentence = sentences[sentenceIndex]; if (!sentence) throw new Error('탐색할 문장이 없습니다.');
    return speaker.say(sentence.text);
  }
  if (/밑줄.*(?:표시|해제)/.test(query) && !/듣|읽/.test(query)) {
    const p = SullivanPassages.findByOrdinal(paragraphs(), query) || paragraphs().find(p => p.paragraph_id === currentParagraph) || paragraphs()[0];
    if (!p) throw new Error('밑줄을 표시할 문단이 없습니다.');
    const set = new Set(current.progress.underlined); /해제/.test(query) ? set.delete(p.paragraph_id) : set.add(p.paragraph_id);
    current.progress.underlined = [...set]; renderMaterial(); await save(); return status('문단 밑줄을 저장했습니다.');
  }
  const result = SullivanPassages.resolveCommand({paragraphs: paragraphs(), query, currentId: currentParagraph, underlinedIds: new Set(current.progress.underlined)});
  if (result.items[0]) currentParagraph = result.items[0].paragraph_id;
  await speaker.say(result.speech);
}
async function search(query) {
  needLesson(); const matches = SullivanConcepts.search(concepts(), query);
  if (originMs === null) originMs = positionMs;
  $('return-origin').disabled = false;
  $('search-results').replaceChildren(...matches.map(concept => {
    const item = node('article'); item.append(node('h5', concept.keyword), node('p', concept.ai_explanation),
      button(`${concept.keyword} 설명 듣기`, () => speaker.say(`${concept.keyword}. ${concept.ai_explanation}`)),
      button(`${concept.keyword} 강사 구간 듣기`, async () => { await seek(concept.timestamp_ms); await media.play(); }));
    return item;
  }));
  if (!matches.length) $('search-results').append(node('p', '연결된 개념을 찾지 못했습니다.'));
  $('search-title').focus(); status(`개념 검색 결과 ${matches.length}개입니다.`);
}
function showResponse(title, text, label = '') {
  const item = node('article'); item.append(node('h5', title), node('p', label), node('p', text)); $('chat-log').append(item);
}
async function ask(message, forceSpeak = false) {
  needLesson(); const selected = current, ticket = generation, action = actionGeneration;
  status('강의 근거로 질문을 확인하고 있습니다.');
  let result;
  try {
    result = await request(`/local/lectures/${current.id}/agent-turn`, {method: 'POST', timeout: 190000, body: {message, current_time_ms: positionMs}});
  } catch (error) {
    if (ticket !== generation || action !== actionGeneration) return;
    const fallback = SullivanLearning.respond(selected.snapshot, message, positionMs);
    showResponse(fallback.title, fallback.text, `준비된 자료 기반의 제한적 보조 도구입니다. ${error.message}`);
    status('실제 학습 대화에 연결하지 못해 준비된 자료 기반으로 안내했습니다.');
    if (forceSpeak || $('speak-answer').checked) await speaker.say(fallback.text);
    return;
  }
  if (ticket !== generation || current !== selected || action !== actionGeneration) return;
  if (!result.safe_to_speak || result.confidence < .72) { status('근거가 충분하지 않아 답변을 보류했습니다.'); return; }
  showResponse(result.title, result.response_text, 'Gemini 학습 대화'); status('학습 대화 답변을 준비했습니다.');
  if (result.action === 'pause') return stopAll();
  if (result.action === 'seek' && Number.isFinite(result.target_timestamp_ms)) await seek(result.target_timestamp_ms);
  if (result.action === 'describe_current') return describe();
  if (result.action === 'replay_paragraph') {
    const text = paragraphs().filter(p => result.paragraph_indices.includes(p.paragraph_index)).map(SullivanPassages.paragraphSpeech).join(' ');
    if (text) return speaker.say(text);
  }
  if (forceSpeak || $('speak-answer').checked) await speaker.say(result.response_text);
}
async function describe() {
  needLesson(); const gap = [...safeGaps()].sort((a,b) => Math.abs(a.timestamp_ms-positionMs)-Math.abs(b.timestamp_ms-positionMs))[0];
  if (!gap) throw new Error('현재 자료에 검증된 화면 설명이 없습니다.');
  await speaker.say(`${time(gap.timestamp_ms)}에 준비된 설명입니다. ${SullivanNarration.compose(gap, concepts())}`);
}
export async function command(text, forceSpeak = false) {
  const intent = SullivanVoiceCommands.classify(text);
  if (intent.type === 'pause') return stopAll();
  if (intent.type === 'lecture_list' || intent.type === 'home' || intent.type === 'save_home') { if (current) await save(); await stopAll(false); $('workspace-title').focus(); return; }
  if (intent.type === 'open_lecture') {
    const lesson = intent.ordinal ? lectures[intent.ordinal - 1] : lectures.find(l => l.title.includes(intent.title));
    if (!lesson) throw new Error('강의 번호 또는 제목을 확인하세요.'); return open(lesson.id);
  }
  needLesson();
  if (/사용법|단축키.*알려/.test(text)) return speaker.say($('command-help').textContent, {resume: false});
  if (intent.type === 'play' || intent.type === 'resume_lecture') {
    await stopAll(false); if (intent.type === 'resume_lecture' && originMs !== null) { await media.seek(originMs); originMs = null; $('return-origin').disabled = true; }
    return media.play();
  }
  if (intent.type === 'auto_narration') { settings.auto_description = intent.enabled; fillPreferences(); return savePreferences(); }
  if (intent.type === 'describe') return describe();
  if (intent.type === 'summary_audio' || intent.type === 'summary_three') return speaker.say(SullivanLearning.respond(current.snapshot, '3줄 요약', positionMs).text);
  if (intent.type === 'paragraph' || /문장|강조/.test(text)) return paragraphCommand(text);
  if (intent.type === 'concept' || /찾아|검색/.test(text)) return search(text.replace(/핵심|키워드|개념|찾아\s*줘|검색해\s*줘|검색|해줘/g, '').trim() || '전체');
  if (/10초.*(?:전|뒤로)|뒤로.*10초/.test(text)) return seek(positionMs - 10000);
  if (/10초.*(?:후|앞으로)|앞으로.*10초/.test(text)) return seek(positionMs + 10000);
  if (/듣던.*위치|원래.*위치/.test(text)) { if (originMs !== null) return seek(originMs); throw new Error('저장한 탐색 전 위치가 없습니다.'); }
  if (/학습 기록|북마크|메모/.test(text)) { $('records-title').focus(); return; }
  if (intent.type === 'panel') {
    const target = {'review-panel': 'review-title', 'study-panel': 'review-title', 'chat-panel': 'chat-title', 'watch-panel': 'player-title', 'passage-panel': 'search-title', 'evidence-panel': 'evidence'}[intent.panelId];
    if (target) { $(target).closest('details')?.setAttribute('open', ''); $(target).focus(); return; }
  }
  if (intent.type === 'button') {
    const buttons = [...$('workspace').querySelectorAll('button')].filter(b => b.getClientRects().length && !b.disabled && !b.dataset.busy);
    const match = buttons.find(b => SullivanVoiceCommands.normalize(b.textContent) === SullivanVoiceCommands.normalize(intent.label));
    if (match) { match.click(); return; } throw new Error('버튼 이름을 정확히 말해 주세요.');
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
  settings = {...defaults, ...response.settings}; fillPreferences();
  device = {voice_uri: $('speech-voice').value, speech_pitch: Number($('speech-pitch').value)};
  await chrome.storage.local.set({[`keys:${user.id}`]: {space: $('space-enabled').checked, shift: $('shift-previous').checked, ...device}});
  status('내 학습 설정을 저장했습니다.');
}
function openDialog(reason = '명령을 입력하고 Enter로 실행하세요. Esc는 취소입니다.') {
  stopAll(false); dialogFocus = document.activeElement;
  $('dialog-help').textContent = reason;
  if (!$('text-dialog').open) $('text-dialog').showModal(); $('text-command').focus();
}
function startVoice() {
  if (recognition) { recognition.stop(); return; }
  if (!$('voice-consent').checked) { openDialog('음성 인식 동의를 확인하지 않아 타자 명령을 열었습니다. 명령을 입력하고 Enter로 실행하세요.'); return; }
  const Recognizer = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognizer) { openDialog('음성 인식을 지원하지 않아 타자 명령을 열었습니다. 명령을 입력하고 Enter로 실행하세요.'); return; }
  stopAll(false); const ticket = ++voiceGeneration; let transcript = '';
  recognition = new Recognizer(); recognition.lang = 'ko-KR'; recognition.interimResults = true;
  recognition.onresult = event => { transcript = [...event.results].map(result => result[0].transcript).join(' '); };
  recognition.onerror = () => { if (ticket === voiceGeneration) { stopVoice(); openDialog('마이크를 사용할 수 없어 타자 명령을 열었습니다. 명령을 입력하고 Enter로 실행하세요.'); } };
  recognition.onend = () => {
    if (ticket !== voiceGeneration) return;
    recognition = null; $('voice').textContent = '음성 명령 시작';
    if (transcript.trim()) command(transcript, true).catch(error => status(error.message, true));
    else $('voice-status').textContent = '인식된 명령이 없습니다. 다시 말하거나 타자로 입력하세요.';
  };
  try { recognition.start(); $('voice').textContent = '음성 명령 마치기'; $('voice-status').textContent = '명령을 말한 뒤 버튼을 다시 누르거나 길게 누른 Space를 떼세요.'; }
  catch { stopVoice(); openDialog('음성 인식을 시작하지 못해 타자 명령을 열었습니다. 명령을 입력하고 Enter로 실행하세요.'); }
}
const gesture = SullivanSpaceGesture.create({hold: startVoice, release: () => { recognition?.stop(); },
  doubleTap: () => stopAll().catch(() => {}), taps: count => {
    if (count >= 3) openDialog();
    else if (count === 1 && spaceTarget?.isConnected && spaceTarget.getClientRects().length && !spaceTarget.disabled) spaceTarget.click();
  }});
let spaceTarget = null, shiftOnly = false, spaceHandled = false;
const editing = target => Boolean(target?.closest('input,textarea,select,[contenteditable=true],dialog'));
document.addEventListener('keydown', event => {
  if (event.key !== 'Shift') shiftOnly = false; else shiftOnly = !event.repeat && !event.ctrlKey && !event.altKey && !event.metaKey;
  if (!current || event.ctrlKey || event.altKey || event.metaKey || editing(event.target)) return;
  if (event.code === 'Space' && $('space-enabled').checked) {
    event.preventDefault(); if (event.repeat) return;
    spaceHandled = true; spaceTarget = event.target.closest('button,summary,a[href]'); gesture.down();
  }
  if (['ArrowLeft','ArrowRight'].includes(event.key)) { event.preventDefault(); seek(positionMs + (event.key === 'ArrowLeft' ? -10000 : 10000)).catch(error => status(error.message, true)); }
});
document.addEventListener('keyup', event => {
  if (event.code === 'Space' && spaceHandled) { event.preventDefault(); spaceHandled = false; gesture.up(); }
  if (event.key === 'Shift' && shiftOnly && $('shift-previous').checked && !editing(event.target)) {
    const controls = [...document.querySelectorAll('button,input,textarea,select,summary,a[href]')].filter(e => e.getClientRects().length && !e.disabled);
    controls[Math.max(0, controls.indexOf(document.activeElement) - 1)]?.focus();
  }
});
window.addEventListener('blur', () => { gesture.cancel(); spaceHandled = false; if (recognition) stopVoice(); });
document.addEventListener('focusin', event => {
  if (!current || !settings.focus_voice || settings.reader_mode || editing(event.target) || !event.target.matches('button,a,summary')) return;
  const label = event.target.getAttribute('aria-label') || event.target.textContent;
  const ticket = ++focusTicket;
  setTimeout(() => { if (ticket === focusTicket && event.target === document.activeElement) speaker.say(label).catch(() => {}); }, 120);
});
chrome.runtime.onMessage.addListener(message => {
  if (message.type === 'student-stop') { if (Number.isSafeInteger(message.fence)) media.fence = Math.max(media.fence, message.fence); stopAll().catch(() => {}); }
  if (message.type === 'student-lease-lost' && message.view === media.view) { stopAll(false); gesture.cancel(); media.reset(); $('connection').textContent = '다른 수강 화면에서 재생을 시작했습니다. 이 화면에서 연결하면 다시 사용할 수 있습니다.'; }
});
function action(id, handler) { $(id).addEventListener('click', () => task($(id), handler)); }
action('refresh', async () => { await refresh(); status('강의 목록을 갱신했습니다.'); });
action('resume', async () => { const state = await chrome.storage.local.get(`last:${user.id}`); const id = state[`last:${user.id}`]; if (!lectures.some(l => l.id === id)) throw new Error('최근 강의가 없거나 배정이 끝났습니다. 목록에서 선택하세요.'); await open(id); });
action('full-view', () => chrome.tabs.create({url: chrome.runtime.getURL('index.html') + (current ? `?lecture=${current.id}` : '')}));
action('open-original', () => connect(true)); action('connect-active', () => connect(false));
action('disconnect', async () => { await stopAll(false); media.reset(); $('connection').textContent = '영상 연결을 해제했습니다.'; });
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
action('play', async () => { await stopAll(false); await media.play(); });
action('stop', () => stopAll()); action('describe', describe);
action('back', () => seek(Math.max(0, positionMs - 10000))); action('forward', () => seek(positionMs + 10000));
action('return-origin', async () => { if (originMs !== null) { await seek(originMs); originMs = null; $('return-origin').disabled = true; } });
action('read', () => { needLesson(); return speaker.say([...(current.snapshot.review.core_summary || []), ...paragraphs().map(SullivanPassages.paragraphSpeech), ...safeGaps().map(g => g.public_description)].join(' ')); });
action('read-underlined', () => paragraphCommand('밑줄 친 문단'));
action('voice', startVoice); action('type-command', openDialog);
action('run-tool', async () => { needLesson(); const result = SullivanLearning.respond(current.snapshot, $('learning-tool').value, positionMs); showResponse(result.title, result.text, '준비된 자료 기반 학습 도구'); if ($('speak-answer').checked) await speaker.say(result.text); else { $('chat-log').focus(); status('학습 도구를 만들었습니다. 결과를 읽어 주세요.'); } });
action('bookmark', async () => { needLesson(); if (current.progress.bookmarks.length >= 100) throw new Error('북마크는 100개까지 저장할 수 있습니다.'); current.progress.bookmarks.push({id: crypto.randomUUID(), timestamp_ms: positionMs, note: `${time(positionMs)} 북마크`}); renderRecords(); await save(); status('현재 위치를 북마크했습니다.'); });
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
  $('text-dialog').close(); await closed; await command(text);
});
$('close-dialog').addEventListener('click', () => $('text-dialog').close());
$('text-dialog').addEventListener('close', () => { if (dialogFocus?.isConnected && dialogFocus.getClientRects().length) dialogFocus.focus(); else $('command-title').focus(); });
bindForm('preferences-form', async () => {
  const form = $('preferences-form');
  settings = Object.fromEntries(Object.keys(defaults).map(key => [key, form.elements[key].type === 'checkbox' ? form.elements[key].checked : Number(form.elements[key].value)]));
  if (settings.reader_mode) settings.focus_voice = false;
  speaker.cancel(); await savePreferences();
});
bindForm('progress-form', async ({position}) => {
  if (media.kind && positionDirty) await seek(Number(position) * 1000);
  else if (positionDirty) positionMs = Number(position) * 1000;
  positionDirty = false; await save(true);
});
$('position').addEventListener('input', () => { positionDirty = true; });
$('note').addEventListener('input', () => { noteDirty = true; clearTimeout(saveTimer); saveTimer = setTimeout(() => save().catch(error => { $('save-status').textContent = `아직 저장하지 못했습니다. ${error.message}`; }), 700); });
window.addEventListener('pagehide', () => { speaker.cancel(); stopVoice(); media.reset(); });
setInterval(tick, 500);
function voices() {
  const list = (window.speechSynthesis?.getVoices?.() || []).filter(voice => voice.lang.toLowerCase().startsWith('ko'));
  $('speech-voice').replaceChildren(node('option', '브라우저 기본 한국어 음성', {value: ''}), ...list.map(voice => node('option', voice.name, {value: voice.voiceURI})));
  if (list.some(voice => voice.voiceURI === device.voice_uri)) $('speech-voice').value = device.voice_uri;
}
window.speechSynthesis?.addEventListener?.('voiceschanged', voices);
await chrome.storage.local.setAccessLevel({accessLevel: 'TRUSTED_CONTEXTS'});
await boot(async account => {
  user = account; settings = {...defaults, ...account.settings}; fillPreferences();
  const local = await chrome.storage.local.get(`keys:${user.id}`);
  device = {voice_uri: local[`keys:${user.id}`]?.voice_uri || '', speech_pitch: local[`keys:${user.id}`]?.speech_pitch || 1};
  voices(); $('speech-pitch').value = String(device.speech_pitch);
  $('space-enabled').checked = Boolean(local[`keys:${user.id}`]?.space); $('shift-previous').checked = Boolean(local[`keys:${user.id}`]?.shift);
  await refresh();
  await refreshConnections();
  const requested = new URL(location.href).searchParams.get('lecture');
  if (requested && lectures.some(l => l.id === requested)) await open(requested);
}, () => { clear(); user = null; lectures = []; pairRequest=null;$('pair-preview').hidden=true;$('student-unlink-confirm').hidden=true;$('my-connections').replaceChildren();$('pair-preview-form').reset();$('lectures').replaceChildren(); });
