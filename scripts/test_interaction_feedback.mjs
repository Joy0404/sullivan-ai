import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source = readFileSync(new URL('../apps/extensions/student/interaction-feedback.js', import.meta.url), 'utf8');
const {classifyLocalCommand, createInteractionFeedback} = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

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
    const intent = classifyLocalCommand(phrase);
    const ticket = feedback.begin(intent.type);
    feedback.update(ticket, 'success');
    feedback.current();
  }
  feedback.reset();
} finally { globalThis.fetch = originalFetch; }
assert.equal(networkCalls, 0);
console.log('Interaction feedback: local controls, private-text isolation, immutable state, stale/reset fences, single completion and zero network PASS');
