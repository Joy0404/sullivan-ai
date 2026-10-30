const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const playback = require("../apps/web/playback-scheduler.js");
const narration = require("../apps/web/narration-context.js");
const passages = require("../apps/web/passage-tools.js");

const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(require.resolve("../apps/web/sample-data-history.js"), "utf8"), sandbox);
const snapshot = sandbox.window.SULLIVAN_SAMPLE_LIBRARY.history;
const events = [];

const dueGap = playback.selectDueGap({ gaps: snapshot.visual_gaps, previousMs: 726_700, currentMs: 727_200 });
assert.equal(dueGap.gap_id, "gap-history-invasion-route");
events.push("영상 재생");
events.push("자동 정지");
events.push(`화면 해설: ${narration.compose(dueGap, snapshot.concept_index)}`);
events.push("자동 재생");

const paragraphs = passages.paragraphsForSnapshot(snapshot);
assert.equal(paragraphs.length, 4);
const flow = passages.resolveCommand({ paragraphs, query: "긴 지문 전체 흐름" });
assert.equal(flow.type, "flow");
assert.match(flow.speech, /임진왜란 원인과 전개.*호란 이후/);
events.push(`긴 지문 흐름: ${flow.speech}`);

const underlinedIds = new Set(["history-p1", "history-p3"]);
const replay = passages.resolveCommand({ paragraphs, query: "밑줄 친 문단 다시 들려줘", underlinedIds });
assert.equal(replay.type, "underlined");
assert.deepEqual(Array.from(replay.items, (item) => Number(item.paragraph_index)), [1, 3]);
assert.match(replay.speech, /도요토미 히데요시/);
assert.match(replay.speech, /친명 배금|친명배금/);
events.push("영상 자동 정지");
events.push(`밑줄 문단 낭독: ${replay.speech}`);
events.push("낭독 완료 뒤 자동 재생");

console.log("=== Sullivan AI 실제 역사 강의 가상 재생 기록 ===");
events.forEach((event, index) => console.log(`${index + 1}. ${event}`));
console.log("Simulation: auto pause/narration + long-passage flow + underlined paragraph replay passed");
