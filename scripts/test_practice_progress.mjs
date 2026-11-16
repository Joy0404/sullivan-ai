import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source = readFileSync(new URL('../apps/extensions/student/practice-progress.js', import.meta.url), 'utf8');
const {createPracticeProgress, PRACTICE_VERSION} = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const practice = createPracticeProgress();
const start = (lessonId = 'sample') => practice.start({lessonId, sample: true, connected: true});
const statuses = () => practice.current().steps.map(step => step.status);
assert.equal(start(), null, 'Account is required');
assert.equal(practice.serializable(), null);
practice.configure('account-a');
for (const args of [{lessonId: 'sample', sample: false, connected: true}, {lessonId: 'sample', sample: true, connected: false}, {sample: true, connected: true}, {lessonId: 'sample', sample: 'true', connected: true}]) {
  assert.equal(practice.start(args), null);
}
assert.deepEqual(statuses(), ['untried', 'untried', 'untried']);
let ticket = start();
const event = (name, details = {}) => practice.observe(name, {lessonId: 'sample', ticket, ...details});
assert.equal(event('toggle', {playing: false}), false, 'A pause without actual play is not a success');
assert.equal(event('stop', {paused: true}), false, 'Steps cannot complete out of order');
assert.equal(event('dialog', {tripleSpace: true}), false);
assert.equal(event('typed_status'), false);
assert.equal(event('voice_status'), false);
assert.equal(event('toggle', {playing: true, ticket: {...ticket}}), false, 'Copied ticket is invalid');
assert.equal(event('toggle', {playing: true, lessonId: 'wrong'}), false);
assert.equal(event('toggle', {playing: false}), false);
assert.equal(event('toggle', {playing: true}), false, 'Play evidence is not a completed step');
assert.equal(event('toggle', {playing: false}), true);
assert.equal(event('toggle', {playing: false}), false, 'Repeated events do not change progress');
assert.equal(event('stop', {paused: false}), false);
assert.equal(event('stop', {paused: true}), true);
assert.equal(event('typed_status'), false, 'A status command without triple-Space dialog is insufficient');
assert.equal(event('dialog', {tripleSpace: false}), false);
assert.equal(event('typed_status'), false);
assert.equal(event('dialog', {tripleSpace: true}), false);
assert.equal(event('typed_status'), true);
assert.equal(practice.current().completed, true);
assert.equal(event('voice_status'), true);
assert.equal(event('voice_status'), false);
assert.equal(practice.current().voiceCompleted, true);
const saved = JSON.parse(JSON.stringify(practice.serializable()));
assert.deepEqual(Object.keys(saved).sort(), ['accountId', 'steps', 'version', 'voiceCompleted']);
assert.equal(Object.isFrozen(practice.current()), true);
assert.equal(Object.isFrozen(practice.current().steps), true);
assert.equal(practice.current().steps.every(Object.isFrozen), true);
practice.configure('account-b', saved);
assert.deepEqual(statuses(), ['untried', 'untried', 'untried'], 'Another account cannot inherit progress');
assert.equal(event('voice_status'), false);
practice.configure('account-a', saved);
assert.equal(practice.current().completed, true);
assert.equal(practice.current().active, false, 'Stored progress cannot restore an active session');
const stale = ticket;
ticket = start();
assert.deepEqual(statuses(), ['untried', 'untried', 'untried'], 'A repeat starts fresh');
assert.equal(event('toggle', {playing: true, ticket: stale}), false, 'Previous run of same lesson is stale');
assert.equal(event('toggle', {playing: false}), false);
event('toggle', {playing: true});
event('toggle', {playing: false});
practice.suspend();
assert.deepEqual(statuses(), ['done', 'untried', 'untried']);
assert.equal(event('stop', {paused: true}), false, 'Suspended events are stale');
practice.skip();
assert.deepEqual(statuses(), ['done', 'skipped', 'skipped']);
assert.equal(practice.current().completed, false);
const skipped = practice.serializable();
practice.configure('account-a', skipped);
assert.deepEqual(statuses(), ['done', 'skipped', 'skipped']);
practice.reset();
assert.deepEqual(statuses(), ['untried', 'untried', 'untried']);

// Reject invalid versions, wrong account, impossible ordering and unknown statuses.
for (const forged of [
  {...saved, version: PRACTICE_VERSION + 1}, {...saved, accountId: 'other'},
  {...saved, steps: {toggle: 'untried', stop: 'done', typed: 'done'}},
  {...saved, steps: {toggle: 'done', stop: 'skipped', typed: 'untried'}},
  {...saved, steps: {toggle: 'done', stop: 'done', typed: 'PRIVATE_QUESTION'}},
  {...saved, steps: {toggle: 'untried', stop: 'untried', typed: 'untried'}, voiceCompleted: true},
  {...saved, voiceCompleted: 'true'}, Object.create(saved), [], null,
]) {
  practice.configure('account-a', forged);
  assert.deepEqual(statuses(), ['untried', 'untried', 'untried']);
  assert.equal(practice.current().voiceCompleted, false);
}
const privateText = 'PRIVATE_QUESTION_NOTE_ASR_정답_보류후보';
practice.configure('account-a', {...saved, raw: privateText});
ticket = practice.start({lessonId: privateText, sample: true, connected: true});
practice.observe(privateText, {ticket, lessonId: privateText, transcript: privateText});
assert.equal(JSON.stringify(practice.current()).includes(privateText), false);
assert.equal(JSON.stringify(practice.serializable()).includes(privateText), false);
assert.equal(JSON.stringify(practice.current()).includes('account-a'), false);

const originalFetch = globalThis.fetch;
let calls = 0;
globalThis.fetch = () => { calls += 1; throw new Error('Network forbidden'); };
try { practice.configure('account-a'); start(); practice.current(); practice.serializable(); practice.skip(); practice.reset(); }
finally { globalThis.fetch = originalFetch; }
assert.equal(calls, 0);
console.log('Practice progress: actual ordered sample actions, account/version isolation, stale tickets, safe persistence, skip/repeat and zero network PASS');
