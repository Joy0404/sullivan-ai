const assert = require("node:assert/strict");
const { conceptsForSnapshot, search, mentioned, categories } = require("../apps/web/concept-tools.js");

const snapshot = {
  concept_index: [
    { concept_id: "cause", keyword: "도요토미 히데요시", aliases: ["풍신수길"], category: "원인·배경", timestamp_ms: 1_000, end_ms: 8_000, ai_explanation: "대륙 침략을 추진했다.", importance: 0.9 },
    { concept_id: "flow", keyword: "임진왜란 전개", aliases: ["침입 경로"], category: "전개·흐름", timestamp_ms: 10_000, end_ms: 20_000, flow: "부산에서 평양까지", importance: 1 },
    { concept_id: "result", keyword: "왜란의 영향", aliases: ["전쟁 결과"], category: "결과·영향", timestamp_ms: 30_000, end_ms: 40_000, importance: 0.8 },
  ],
};

const concepts = conceptsForSnapshot(snapshot);
assert.equal(concepts.length, 3);
assert.equal(search(concepts, "풍신수길")[0].concept_id, "cause");
assert.equal(search(concepts, "전개")[0].concept_id, "flow");
assert.equal(search(concepts, "결과")[0].concept_id, "result");
assert.equal(mentioned(concepts, "임진왜란 침입 경로를 설명해줘")[0].concept_id, "flow");
assert.deepEqual(categories(concepts), ["원인·배경", "전개·흐름", "결과·영향"]);
assert.equal(conceptsForSnapshot({ study_guide: { glossary: [{ term: "주계열성", definition: "안정된 별" }] } }).length, 1);

console.log("Concept tools: 7 checks passed");
