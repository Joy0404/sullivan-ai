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
  assert.match((await controlVideo('state', null, expected)).error, /영상을 찾지|지원하지/);
  assert.match((await controlVideo('state', null, 'https://www.youtube.com/watch?v=other')).error, /변경/);
  const video = {currentTime: 0, duration: 10, paused: true, ended: false, pause() { this.paused = true; }, async play() { this.paused = false; }};
  globalThis.document.querySelector = selector => selector.startsWith('video') ? video : null;
  assert.equal((await controlVideo('seek', 2000, expected)).positionMs, 2000);
  await controlVideo('release', null, expected);
}


// Generic pages: prefer the main player, traverse open roots and pin it.
{
  const url='https://lecture.example/course#/lesson/1';globalThis.location={href:url};
  const make=(width,duration)=>({currentTime:0,duration,paused:true,isConnected:true,
    getBoundingClientRect(){return {width,height:width/2};},pause(){this.paused=true;},async play(){this.paused=false;}});
  const thumbnail=make(10,30),main=make(640,1000);
  const shadow={querySelectorAll(selector){return selector==='video'?[main]:[];}};
  globalThis.document={querySelector(){return null;},querySelectorAll(selector){return selector==='video'?[thumbnail]:selector==='*'?[{shadowRoot:shadow}]:[];}};
  assert.equal((await controlVideo('state',null,url)).durationMs,1000000);
  assert.match((await controlVideo('state',null,url.replace('/1','/2'))).error,/변경/);
  main.isConnected=false;assert.match((await controlVideo('play',null,url)).error,/플레이어가 변경/);
  await controlVideo('release',null,url);
  main.isConnected=true;main.mediaKeys={};
  assert.match((await controlVideo('play',null,url)).error,/보호된/);
  assert.equal(main.paused,true);
  const frame={tagName:'IFRAME',src:'https://player.example/embed?id=private',contentDocument:null};
  document.querySelectorAll=selector=>selector==='*'?[frame]:[];
  const probe=await controlVideo('probe',null,null);
  assert.equal(probe.found,false);assert.deepEqual(probe.permissionOrigins,['https://player.example/*']);
}
console.log('Generic player: shadow/main selection, pinned target, SPA identity, protected media and origin-only discovery PASS');

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
  for (let i = 0; i < 3; i++) { assert.ok(utterances.at(-1).text.length <= 180); utterances.at(-1).onend(); await new Promise(resolve=>setTimeout(resolve,150));await flush(); }
  await work; assert.equal(media.plays, 1);
}
{
  const {media,speaker}=setup();const work=speaker.say('나'.repeat(400));await flush();
  const count=utterances.length;utterances.at(-1).onend();await flush();media.fence++;speaker.cancel();await work;
  await new Promise(resolve=>setTimeout(resolve,160));assert.equal(utterances.length,count);assert.equal(media.plays,0);
}
{
  const {media, speaker} = setup(); media.state = async () => { throw new Error('연결 해제'); };
  await assert.rejects(speaker.say('해설'), /연결 해제/); assert.equal(speaker.active, false);
}
{
  const {speaker}=setup();const work=speaker.say('현재 0.4입니다.');await flush();
  assert.equal(utterances.at(-1).text,'현재 0점4입니다.');utterances.at(-1).onend();await work;
}
console.log('Student speech: cancellation, stale completion, overlapping focus, chunking, reader mode and connection loss PASS');

{
  const source=readFileSync(new URL('../apps/extensions/student/media.js',import.meta.url),'utf8');
  const {StudentMedia}=await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
  const make=()=>{
    const video={paused:false,currentTime:0,duration:8,plays:0,pause(){this.paused=true;},async play(){this.plays++;this.paused=false;},
      querySelectorAll(){return [];},removeAttribute(){},load(){}};
    const media=new StudentMedia(video);media.kind='local';media.ready=true;return {media,video};
  };
  let deferred;
  globalThis.chrome={runtime:{async sendMessage(message){if(message.action===deferred?.action)return new Promise(resolve=>deferred.resolve=resolve);return {ok:true};}}};
  {
    const{media,video}=make();deferred={action:'play'};
    const work=media.play().catch(error=>error);await flush();await media.pause(false);deferred.resolve({ok:true});
    assert.equal((await work).cancelled,true);assert.equal(video.plays,0);assert.equal(media.wantsPlayback,true);
  }
  {
    const{media,video}=make();deferred={action:'seek'};
    const work=media.seek(7000).catch(error=>error);await flush();media.reset();media.kind='local';video.currentTime=1;
    deferred.resolve({ok:true});assert.equal((await work).cancelled,true);assert.equal(video.currentTime,1);
  }
  {
    const{media}=make();deferred={action:'state'};
    const past=media.state({allowPause:true});await flush();await media.pause();deferred.resolve({ok:true});
    assert.equal((await past).paused,false);
    deferred={action:'state'};const stale=media.state({allowPause:true}).catch(error=>error);await flush();media.reset();
    deferred.resolve({ok:true});assert.equal((await stale).cancelled,true);
  }
  {
    const{media}=make();media.kind=null;deferred={action:'claim'};
    const calls=[];const original=chrome.runtime.sendMessage;chrome.runtime.sendMessage=message=>{calls.push(message.action);return original(message);};
    const claim=media.claim('https://example.com/lesson').catch(error=>error);await flush();await media.pause();
    assert.deepEqual(calls,['claim','pause']);deferred.resolve({ok:true});assert.equal((await claim).cancelled,true);
    chrome.runtime.sendMessage=original;
  }
  deferred=null;
  {
    class LoadingVideo extends EventTarget {
      pause(){} load(){} querySelectorAll(){return [];} removeAttribute(){this.src='';}
    }
    const video=new LoadingVideo(),media=new StudentMedia(video);
    const loading=media.local(new Blob(['synthetic pending metadata'],{type:''}),null).catch(error=>error);
    await flush();assert.ok(media.pendingLocal);media.reset();
    assert.equal((await loading).cancelled,true);assert.equal(media.pendingLocal,null);assert.equal(video.src,'');
  }
}
console.log('Student media: pending play hold, stale seek, past-state pause snapshot and changed-view rejection PASS');

// Exercise the listener boundary independently of browser speech/network timing.
{
  const listeners={};globalThis.document={addEventListener(name,handler){listeners[name]=handler;}};
  globalThis.window={addEventListener(){}};
  const source=readFileSync(new URL('../apps/extensions/student/keyboard.js',import.meta.url),'utf8');
  const {installStudentKeyboard}=await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
  let stops=0,aborts=0,downs=0,ups=0;
  const input={closest(selector){return selector.startsWith('textarea')?this:null;}};
  const control={closest(){return null;}};
  installStudentKeyboard({gesture:{down(){downs++;},up(){ups++;},cancel(){}},enabled:()=>true,hasLesson:()=>false,active:()=>true,
    outputActive:()=>true,emergencyStop(){stops++;},abortGesture(){aborts++;}});
  document.querySelectorAll=()=>[];
  const fire=(name,code,target=input,extra={})=>listeners[name]({key:code==='Space'?' ':code,code,target,preventDefault(){},stopImmediatePropagation(){},...extra});
  fire('keyup','Space');fire('keydown','KeyA');fire('keyup','Space');assert.equal(stops,0);
  fire('keyup','Space');assert.equal(stops,1);
  fire('keyup','Space',input,{ctrlKey:true});fire('keyup','Space',input,{ctrlKey:true});assert.equal(stops,1);
  listeners.focusin();assert.ok(aborts>0);
  fire('keydown','Space',control);fire('keyup','Space',control);assert.equal(downs,1);assert.equal(ups,1);
  const before=aborts;listeners.compositionstart();assert.equal(aborts,before+1);
}
console.log('Student keyboard: home gesture, native editing, interrupted double-space, modifiers and IME cancellation PASS');
