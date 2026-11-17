import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';

const source = readFileSync(new URL('../apps/extensions/student/interaction-feedback.js', import.meta.url), 'utf8');
const {classifyLocalCommand, resolveStudentIntent, createInteractionFeedback} = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const legacy = createRequire(import.meta.url)('../apps/web/voice-command-router.js').classify;

// State/help controls are handled locally before any academic-question routing.
for (const text of ['현재 상태', '지금 상태', '무슨 작업 중', '최근 명령', '현재 상태 알려줘', '지금 뭐 하고 있어', '현재 작업 알려줘']) assert.equal(classifyLocalCommand(text).type, 'status');
for (const text of ['사용법', '도움말', '지금 할 수 있는 명령', '사용법 알려줘', '도움말 알려줘', '단축키 알려줘']) assert.equal(classifyLocalCommand(text).type, 'help');
for (const [text, type] of [['강의 재생', 'play'], ['재생해 줘', 'play'], ['영상 일시 정지', 'pause'], ['영상 중지', 'stop'], ['전체 중지', 'stop']]) {
  assert.deepEqual(classifyLocalCommand(text), {type});
}
assert.deepEqual(classifyLocalCommand('10초 뒤로'), {type: 'seek', deltaMs: -10000});
assert.deepEqual(classifyLocalCommand('앞으로 10초'), {type: 'seek', deltaMs: 10000});
assert.equal(Object.isFrozen(classifyLocalCommand('도움말')), true);
for (const text of [null, {}, '', '상태 전이가 무엇인가요?', '현재 상태와 평형 상태의 차이', '재생 에너지란?', '재생해 주면 어떤 현상이 생기나?', '영상 중지 원리를 설명해 줘', '10초 뒤에 나타나는 변화는?', '문제 만들어 줘', '필기 대신 작성해 줘', '도움말을 강의 내용과 비교해 줘', '도움말\u0000']) {
  assert.equal(classifyLocalCommand(text), null, `Should remain outside local controls: ${String(text)}`);
}

// Use the actual shared router: local exclusion alone used to fall into a
// second, substring-based classification and operate media for these questions.
assert.equal(legacy('핵융합이 멈추면 별은 어떻게 변해?').type, 'pause');
assert.equal(legacy('강의 재생 중에 나온 주계열성 개념은 무슨 뜻이야?').type, 'play');
for (const question of [
  '강의 재생 중에 나온 주계열성 개념은 무슨 뜻이야?', '핵융합이 멈추면 별은 어떻게 변해?',
  '핵융합이멈추면별은어떻게변해?', '재생해 주면 어떤 현상이 생기나?',
  '영상 중지 원리를 설명해 줘', '10초 뒤에 나타나는 변화는 왜 생겨?',
  '밑줄 친 문단과 다음 문단의 차이를 설명해 줘', '현재 화면에 나온 단위는 무슨 뜻이야?',
  '강의 재생 중 핵융합 실패 이유가 뭐야?', '왜란 이후의 상황은 왜 달라져?',
  '강의 재생 중에 나온 개념을 설명해줘', '핵융합이 멈춘 현상을 설명해줘',
  '이 공식의 사용법은 무엇인가요?',
  '영상이 멈췄을 때 관성은 어떻게 작용해?', '핵융합이 멈추는 과정을 설명해줘',
  '핵융합이 멈추고 나면 어떻게 변해?',
  '강의 재생 중 x < 7과 x ≤ 7의 차이가 뭐야?',
  '강의로 돌아오는 과정을 설명해줘',
  '"멈춰"라는 말의 의미를 알려줘',
]) {
  assert.deepEqual(resolveStudentIntent(question, legacy), {type: 'question'}, question);
}
for (const command of [
  '멈춰', '영상 중지', '영상중지', '영상을 중지해줘', '영상 좀 중지해 주세요',
  '동영상 중지', '강의 중지', '강의를 정지해줘', '재생 중지', '음성 중지', '설명 중지',
  '해설 중지', '낭독 중지', '중지', '정지', '중지해 주세요', '영상 좀 잠시 멈춰 줄래?',
  '영상 멈춰 주시겠어요?', '세줄 요약 멈춰',
]) assert.ok(['stop', 'pause'].includes(resolveStudentIntent(command, legacy).type), command);
for (const command of ['강의 재생', '계속 재생해', '영상 시작해줘', '영상 재생해 줄래?', '다시 영상 틀어 주세요']) {
  assert.equal(resolveStudentIntent(command, legacy).type, 'play', command);
}
for (const command of ['요약 멈추고 강의로 돌아와', '세줄 요약 중지하고 강의로 돌아오기', '강의로 돌아와', '강의 이어 듣기']) {
  assert.equal(resolveStudentIntent(command, legacy).type, 'resume_lecture', command);
}
for (const text of ['왜 재생이 안돼?', '영상이 멈췄어', '마이크 사용법', '단축키 알려줘']) assert.equal(resolveStudentIntent(text, legacy).type, 'help', text);
for (const text of ['영상 재생 같은 거', '멈추는 그런 동작', '재생 좀', '영상 재생 좀 부탁', '영상 멈추고 개념 설명해줘', '강의로 돌아오는 그런 동작', '1.0초 뒤로', '1,0초 뒤로', '-10초 뒤로', '+10초 앞으로', '10초 정도 앞으로', null, {}, '', '가'.repeat(2001)]) assert.equal(resolveStudentIntent(text, legacy).type, 'clarify');
assert.deepEqual(resolveStudentIntent('10초 뒤로 이동해줘', legacy), {type:'seek', deltaMs:-10000});
assert.deepEqual(resolveStudentIntent('10초 전 이동해 주세요', legacy), {type:'seek', deltaMs:-10000});
assert.deepEqual(resolveStudentIntent('앞으로 10초 이동해 주세요', legacy), {type:'seek', deltaMs:10000});
for (const text of ['합의 원리 강의 열어줘', '왜 수학을 배우는가 강의 열어줘', '의미 설명 강의 열어줘', '무엇인가요 버튼 눌러', '왜란과 호란 샘플 보여줘', '주계열성 핵심 개념 찾아줘', '현재 칠판 화면 설명해줘', '3줄 요약해줘', '자동 해설 중지']) {
  assert.deepEqual(resolveStudentIntent(text, legacy), legacy(text), text);
}

const changes = [];
const feedback = createInteractionFeedback({onChange: value => changes.push(value)});
assert.equal(feedback.current().phase, 'idle');
const play = feedback.begin('play');
assert.equal(feedback.current().summary, '강의 재생: 처리 중.');
assert.equal(feedback.update({...play}, 'success'), false, 'A copied ticket cannot publish');
assert.equal(feedback.update(play, 'success'), true);
const completed = feedback.current();
const completionCount = changes.length;
assert.equal(feedback.update(play, 'success'), false);
assert.equal(feedback.update(play, 'fail', 'failed'), false, 'One result cannot finalize twice');
assert.equal(changes.length, completionCount);
assert.equal(feedback.current(), completed);
assert.equal(Object.isFrozen(completed), true);
assert.throws(() => { completed.label = 'changed'; }, TypeError);

// Replacing work or resetting an account/lecture/view invalidates every old result.
const old = feedback.begin('question');
const latest = feedback.begin('stop');
const beforeOld = changes.length;
assert.equal(feedback.update(old, 'success'), false);
assert.equal(changes.length, beforeOld);
assert.equal(feedback.update(latest, 'cancel', 'cancelled'), true);
const epoch = feedback.current().epoch;
const beforeReset = feedback.begin('listen');
feedback.reset();
assert.equal(feedback.current().epoch, epoch + 1);
const resetCount = changes.length;
assert.equal(feedback.update(beforeReset, 'success'), false);
assert.equal(changes.length, resetCount);
assert.equal(feedback.current().summary, '최근 명령이 없습니다.');
const afterReset = feedback.begin('help');
assert.equal(feedback.update(beforeReset, 'running'), false);
assert.equal(feedback.update(afterReset, 'success'), true);

// Only dictionary keys survive. Raw questions, notes, ASR, errors and objects do not.
const privateText = 'PRIVATE_ASR_보호후보_정답_학생필기_개인질문';
const privateTicket = feedback.begin(privateText);
assert.equal(feedback.current().actionId, 'command');
assert.equal(feedback.current().label, '강의 요청');
assert.equal(feedback.update(privateTicket, privateText, privateText), false);
assert.equal(feedback.update(privateTicket, 'listening', privateText), true);
assert.equal(feedback.current().reason, '');
assert.equal(feedback.update(privateTicket, 'recognized'), true);
assert.equal(feedback.update(privateTicket, 'fail', 'unrecognized'), true);
assert.match(feedback.current().summary, /타자로 입력/);
for (const unknown of ['__proto__', 'constructor', 'toString', {toString() { throw new Error('Must not coerce input'); }}]) {
  const ticket = feedback.begin(unknown);
  assert.equal(feedback.current().actionId, 'command');
  assert.equal(feedback.update(ticket, 'fail', unknown), true);
  assert.equal(feedback.current().reason, '');
}
assert.equal(JSON.stringify(changes).includes(privateText), false);
assert.equal(changes.every(Object.isFrozen), true);

// Every local command/state operation runs even when network APIs are forbidden.
const originalFetch = globalThis.fetch;
let networkCalls = 0;
globalThis.fetch = () => { networkCalls += 1; throw new Error('No network allowed'); };
try {
  for (const phrase of ['현재 상태', '사용법', '강의 재생', '영상 중지', '10초 앞으로']) {
    const intent = resolveStudentIntent(phrase, legacy);
    const ticket = feedback.begin(intent.type);
    feedback.update(ticket, 'success');
    feedback.current();
  }
  for (const text of ['영상 재생 같은 거', '핵융합이 멈추면 별은 어떻게 변해?', '왜 재생이 안돼?']) resolveStudentIntent(text, legacy);
  feedback.reset();
} finally { globalThis.fetch = originalFetch; }
assert.equal(networkCalls, 0);
console.log('Interaction feedback: local controls, private-text isolation, immutable state, stale/reset fences, single completion and zero network PASS');
