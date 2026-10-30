const assert = require("node:assert/strict");
const { selectDueGap, nextAutomaticGap } = require("../apps/web/playback-scheduler.js");

const gaps = [
  { gap_id: "index", timestamp_ms: 1_000, action: "INDEX_ONLY", safe_to_speak: true, public_description: "index" },
  { gap_id: "first", timestamp_ms: 43_000, action: "DESCRIBE_AT_BREAK", safe_to_speak: true, public_description: "first" },
  { gap_id: "second", timestamp_ms: 80_000, action: "INTERRUPT", safe_to_speak: true, public_description: "second" },
  { gap_id: "hold", timestamp_ms: 90_000, action: "HOLD", safe_to_speak: false, public_description: "" },
];

assert.equal(selectDueGap({ gaps, currentMs: 43_200 })?.gap_id, "first");
assert.equal(selectDueGap({ gaps, previousMs: 42_700, currentMs: 43_350 })?.gap_id, "first");
assert.equal(selectDueGap({ gaps, previousMs: 39_500, currentMs: 46_900 })?.gap_id, "first");
assert.equal(selectDueGap({ gaps, previousMs: 10_000, currentMs: 70_000 }), null);
assert.equal(selectDueGap({ gaps, previousMs: 79_800, currentMs: 80_300, announcedIds: new Set(["first"]) })?.gap_id, "second");
assert.equal(selectDueGap({ gaps, previousMs: 89_800, currentMs: 90_300 }), null);
assert.equal(nextAutomaticGap(gaps, new Set(), 0)?.gap_id, "first");
assert.equal(nextAutomaticGap(gaps, new Set(["first"]), 43_000)?.gap_id, "second");

console.log("Playback scheduler: 8 checks passed");
