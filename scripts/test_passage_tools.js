const assert = require("node:assert/strict");
const passages = require("../apps/web/passage-tools.js");

const snapshot = {
  passage: {
    paragraphs: [
      { paragraph_id: "p1", paragraph_index: 1, flow_role: "문제 제기", sentences: [{ sentence_index: 1, text: "첫 문단 내용입니다.", timestamp_ms: 1_000 }] },
      { paragraph_id: "p2", paragraph_index: 2, flow_role: "원인 분석", sentences: [{ sentence_index: 1, text: "둘째 문단 내용입니다.", timestamp_ms: 2_000 }] },
      { paragraph_id: "p3", paragraph_index: 3, flow_role: "결론", sentences: [{ sentence_index: 1, text: "셋째 문단 내용입니다.", timestamp_ms: 3_000 }] },
    ],
  },
};

const items = passages.paragraphsForSnapshot(snapshot);
assert.equal(items.length, 3);
assert.equal(items[1].text, "둘째 문단 내용입니다.");
assert.equal(passages.resolveCommand({ paragraphs: items, query: "2문단 다시 들려줘" }).items[0].paragraph_id, "p2");
assert.equal(passages.resolveCommand({ paragraphs: items, query: "다음 문단", currentId: "p1" }).items[0].paragraph_id, "p2");
assert.equal(passages.resolveCommand({ paragraphs: items, query: "앞 문단", currentId: "p3" }).items[0].paragraph_id, "p2");
assert.equal(passages.resolveCommand({ paragraphs: items, query: "결론" }).items[0].paragraph_id, "p3");
assert.match(passages.resolveCommand({ paragraphs: items, query: "전체 흐름" }).speech, /문제 제기.*원인 분석.*결론/);
assert.deepEqual(
  passages.resolveCommand({ paragraphs: items, query: "밑줄 친 문단 다시 들려줘", underlinedIds: new Set(["p1", "p3"]) }).items.map((item) => item.paragraph_id),
  ["p1", "p3"],
);
assert.equal(passages.resolveCommand({ paragraphs: items, query: "밑줄 친 문단", underlinedIds: new Set() }).type, "not-found");
assert.match(passages.paragraphSpeech(items[1]), /2문단, 원인 분석/);

console.log("Passage tools: 10 checks passed");
