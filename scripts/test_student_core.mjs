import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const moduleSource = readFileSync(new URL('../apps/extensions/student/speech.js', import.meta.url), 'utf8');
const {StudentSpeech} = await import(`data:text/javascript;base64,${Buffer.from(moduleSource).toString('base64')}`);
const bridgeSource = readFileSync(new URL('../apps/extensions/student/video-control.js', import.meta.url), 'utf8');
const {controlVideo} = await import(`data:text/javascript;base64,${Buffer.from(bridgeSource).toString('base64')}`);
{
  const expected = 'https://www.youtube.com/watch?v=fixture';
  globalThis.location = {href: expected};
  globalThis.document = {querySelector() { return null; }};
  assert.match((await controlVideo('state', null, expected)).error, /지원하지/);
  assert.match((await controlVideo('state', null, 'https://www.youtube.com/watch?v=other')).error, /변경/);
  const video = {currentTime: 0, duration: 10, paused: true, ended: false, pause() { this.paused = true; }, async play() { this.paused = false; }};
  globalThis.document.querySelector = selector => selector.startsWith('video') ? video : null;
  assert.equal((await controlVideo('seek', 2000, expected)).positionMs, 2000);
  await controlVideo('release', null, expected);
}

let utterances = [];
globalThis.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
globalThis.speechSynthesis = {speak(utterance) { utterances.push(utterance); }, cancel() {}};
const flush = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };
function setup(reader = false) {
  const media = {fence: 0, paused: false, plays: 0, pauses: 0,
    async state() { return {paused: this.paused}; }, async pause() { this.paused = true; this.pauses++; },
    async play(fence) { assert.equal(fence, this.fence); this.paused = false; this.plays++; }};
  return {media, speaker: new StudentSpeech(media, () => ({speech_rate: 1, speech_volume: .8, reader_mode: reader}), () => {})};
}
{
  const {media, speaker} = setup();
  const work = speaker.say('첫 해설'); await flush();
  assert.equal(media.paused, true);
  const stale = utterances.at(-1); media.fence++; speaker.cancel(); await work;
  stale.onend(); await flush(); assert.equal(media.plays, 0); assert.equal(speaker.active, false);
}
{
  const {media, speaker} = setup();
  const first = speaker.say('첫 초점 안내'); await flush();
  const stale = utterances.at(-1); const second = speaker.say('다음 초점 안내'); await flush();
  stale.onend(); await first; assert.equal(media.plays, 0);
  utterances.at(-1).onend(); await second; assert.equal(media.plays, 1);
}
{
  const {media, speaker} = setup(true); const before = utterances.length;
  await speaker.say('스크린리더 본문'); assert.equal(utterances.length, before); assert.equal(media.plays, 0); assert.equal(media.paused, true);
}
{
  const {media, speaker} = setup(); const work = speaker.say('가'.repeat(400)); await flush();
  for (let i = 0; i < 3; i++) { assert.ok(utterances.at(-1).text.length <= 180); utterances.at(-1).onend(); await flush(); }
  await work; assert.equal(media.plays, 1);
}
{
  const {media, speaker} = setup(); media.state = async () => { throw new Error('연결 해제'); };
  await assert.rejects(speaker.say('해설'), /연결 해제/); assert.equal(speaker.active, false);
}
console.log('Student speech: cancellation, stale completion, overlapping focus, chunking, reader mode and connection loss PASS');
