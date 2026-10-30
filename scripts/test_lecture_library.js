const assert = require("node:assert/strict");
const library = require("../apps/web/lecture-library.js");

const records = [
  { id: "recent", title: "별의 진화", subject: "과학", updated_at: "2026-09-20T08:00:00Z" },
  { id: "history", title: "왜란과 호란", subject: "역사", updated_at: "2026-09-19T08:00:00Z" },
];

assert.equal(library.findRequested(records, "최근 강의 다시 열어줘").id, "recent");
assert.equal(library.findRequested(records, "별의 진화 요약 들려줘").id, "recent");
assert.equal(library.findRequested(records, "왜란과 호란 다시 재생").id, "history");
assert.equal(library.findRequested(records, "수학 강의"), null);
assert.equal(library.requestIntent("별의 진화 요약 들려줘"), "summary");
assert.equal(library.requestIntent("최근 강의 다시 열어줘"), "open");
assert.match(library.summaryText({ study_guide: { overview: "핵심 요약", concept_map: ["A에서 B"] } }), /핵심 요약.*A에서 B/);
assert.equal(library.summaryText({}), "저장된 요약이 없습니다.");

console.log("Lecture library: 8 checks passed");
