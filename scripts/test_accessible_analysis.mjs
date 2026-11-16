import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const moduleFrom=async path=>import(`data:text/javascript;base64,${Buffer.from(readFileSync(new URL(path,import.meta.url),'utf8')).toString('base64')}`);
const {createLessonData,safeHoldNoticeText}=await moduleFrom('../apps/extensions/student/lesson-data.js');
const {StudentSpeech,StudentAnnouncer}=await moduleFrom('../apps/extensions/student/speech.js');
const {analysisLabel}=await moduleFrom('../apps/extensions/shared/analysis-status.js');
globalThis.SullivanPassages={paragraphsForSnapshot:()=>[]};globalThis.SullivanConcepts={conceptsForSnapshot:()=>[]};
const hold={gap_id:'held',action:'HOLD',safe_to_speak:false,confidence:.4,kind:'number',timestamp_ms:5,public_description:'PRIVATE_CANDIDATE',source_text:'PRIVATE_CANDIDATE',hold_notices:[{code:'visual_uncertain',location:'vertical_axis_unit',text:'PRIVATE_PROVIDER_TEXT'}]};
const data=createLessonData({session:{problem_mode:true},visual_gaps:[hold]});
assert.equal(data.gaps.length,0);assert.equal(data.notices.length,1);assert.equal(data.notices[0].notice_only,true);
assert.equal(data.notices[0].source_text,null);assert.equal(data.notices[0].public_description,'‘세로축의 단위’ 부분은 확실치 않아서 설명을 보류하겠습니다.');
assert.ok(!JSON.stringify(data.playbackGaps).includes('PRIVATE'));
assert.equal(safeHoldNoticeText({...hold,kind:'answer'},true),'');
assert.match(safeHoldNoticeText({...hold,hold_notices:[{code:'visual_uncertain',location:'PRIVATE_LOCATION'}]}),/‘이 장면의 판서’/);
const partial={...hold,gap_id:'partial',safe_to_speak:true,confidence:.99,kind:'graph',action:'DESCRIBE_AT_BREAK',source_text:'증가합니다.',public_description:'값이 증가합니다. ‘세로축의 단위’ 부분은 확실치 않아서 설명을 보류하겠습니다.'};
const partialData=createLessonData({session:{problem_mode:false},visual_gaps:[partial]});
assert.equal(partialData.playbackGaps.length,1);assert.equal(partialData.notices.length,0);
assert.equal(analysisLabel({state:'not_run',source_label:'Gemini 분석 완료'}),'영상 분석 미실행');
assert.equal(analysisLabel({state:'completed',provider:'gemini'}),'분석 상태 확인 불가');
assert.equal(analysisLabel({state:'completed',provider:'gemini',run_id:'server',recorded_at:'now'}),'Gemini 분석 완료');
console.log('Safe HOLD notices, partial single delivery, problem answers and provenance labels PASS');

let utterances=[];
globalThis.SpeechSynthesisUtterance=class {constructor(text){this.text=text;}};
globalThis.speechSynthesis={speak(u){utterances.push(u);},cancel(){},getVoices(){return [];}};
const flush=async()=>{for(let i=0;i<20;i++)await Promise.resolve();};
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function fixture(reader=false){
  const media={fence:0,paused:false,wantsPlayback:true,plays:0,async state(){return {paused:this.paused};},async pause(){this.paused=true;},async play(){this.paused=false;this.plays++;}};
  const settings=()=>({focus_voice:true,reader_mode:reader,speech_rate:1,speech_volume:1});
  const output=[];const speaker=new StudentSpeech(media,settings,text=>output.push(text));
  const announcer=new StudentAnnouncer(settings,()=>{});announcer.lessonSpeaker=speaker;announcer.lessonReady=()=>true;
  speaker.beforeSpeak=purpose=>{if(purpose!=='guidance')announcer.cancel(true);};
  return {speaker,announcer,media,output};
}
{
  utterances=[];const {speaker,announcer}=fixture();const lesson='가'.repeat(400);const work=speaker.say(lesson);await flush();
  announcer.say('다음 버튼');assert.equal(utterances.length,1);
  for(let i=0;i<3;i++){utterances.at(-1).onend();await wait(150);await flush();}
  await work;for(let i=0;i<6&&utterances.at(-1).text!=='다음 버튼';i++)await wait(100);
  assert.equal(utterances.slice(0,3).map(u=>u.text).join(''),lesson);assert.equal(utterances.at(-1).text,'다음 버튼');
  utterances.at(-1).onend();await flush();announcer.cancel();
}
{
  utterances=[];const {speaker,announcer,media}=fixture();const work=speaker.say('나'.repeat(400));await flush();announcer.say('취소된 초점 안내');announcer.cancel();speaker.cancel();await work;await wait(160);
  assert.equal(utterances.length,1);assert.equal(media.plays,0);
}
{
  utterances=[];const {speaker,output,media}=fixture(true);await speaker.say(data.notices[0].public_description);
  assert.equal(utterances.length,0);assert.deepEqual(output,[data.notices[0].public_description]);assert.equal(media.paused,true);
}
{
  utterances=[];const {speaker}=fixture();const work=speaker.say('확인한 설명').catch(e=>e);await flush();utterances.at(-1).onerror({error:'synthesis-failed'});assert.equal((await work).mediaFailure,undefined);
  const failed=fixture();failed.media.state=async()=>{throw new Error('media failed');};const error=await failed.speaker.say('설명').catch(e=>e);assert.equal(error.mediaFailure,true);
}
console.log('Complete lesson before focus guidance, explicit stop, reader-only delivery and TTS/media errors PASS');
{
  utterances=[];const {speaker,announcer,media}=fixture();
  const work=speaker.say('실패할 해설').catch(e=>e);await flush();announcer.say('대기한 초점 안내');
  utterances[0].onerror({error:'synthesis-failed'});await work;
  for(let i=0;i<6&&utterances.length<2;i++)await wait(100);
  assert.equal(utterances.at(-1).text,'대기한 초점 안내');utterances.at(-1).onend();await flush();
  assert.equal(media.plays,0);assert.equal(media.paused,true);assert.equal(media.wantsPlayback,false);announcer.cancel();
}
console.log('Queued focus guidance cannot resume video after a narration failure PASS');
