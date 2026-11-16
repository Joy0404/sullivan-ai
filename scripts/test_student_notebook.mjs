import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../apps/extensions/student/learning-response.js',import.meta.url),'utf8');
globalThis.SullivanConcepts={conceptsForSnapshot:s=>s.concept_index,search:(items,query)=>items.filter(item=>query.includes(item.keyword))};
globalThis.fetch=()=>{throw new Error('Deterministic student tools must never call a provider');};
await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const tool=globalThis.SullivanLearning;
const snapshot={review:{core_summary:['하나','둘','셋','넷']},concept_index:[{keyword:'질량',ai_explanation:'준비된 질량 설명'}]};
Object.defineProperty(snapshot,'notes',{get(){throw new Error('Personal notes must not enter grounded context');}});
for(const message of ['1분 발표문','3분 발표문 만들어줘','암기표','복습 계획','추가 학습 도구','학습 가이드 전체 듣기','핵심 용어 카드','두 개념 비교','원인 전개 결과','시간순 흐름','퀴즈 만들어줘','개념 지도 생성']){
  assert.equal(tool.unsupported(message),true,message);
  assert.equal(tool.respond(snapshot,message).text,tool.scope,message);
}
assert.equal(tool.unsupported('세 줄 요약'),false);
assert.equal(tool.respond(snapshot,'세 줄 요약').text,'하나 둘 셋');
assert.equal(tool.respond(snapshot,'질량 설명').text,'질량. 준비된 질량 설명');
assert.match(tool.respond(snapshot,'모르는 내용').text,/찾지 못했습니다/);
console.log('Student notebook scope: 12 removed requests rejected, short summary and grounded fallback retained; no personal notes/provider access PASS');
