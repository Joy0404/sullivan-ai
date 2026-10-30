const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const context = vm.createContext({ window: {} });
for (const name of ["sample-data.js", "sample-data-history.js"]) {
  const source = fs.readFileSync(path.join(__dirname, "..", "apps", "web", name), "utf8");
  vm.runInContext(source, context, { filename: name });
}

const library = context.window.SULLIVAN_SAMPLE_LIBRARY;
assert.deepEqual(Object.keys(library), ["science", "history"]);
assert.ok(library.science.concept_index.length >= 19);
assert.ok(library.history.concept_index.length >= 35);
const correctedBoard = library.science.visual_gaps.find((gap) => gap.timestamp_ms === 235000);
assert.equal(correctedBoard.gap_id, "gap-star-birth-board");
assert.equal(correctedBoard.screen_type, "board");
assert.match(correctedBoard.public_description, /성운.*중력 수축.*원시별.*주계열성/);
assert.doesNotMatch(JSON.stringify(correctedBoard), /H-R|광도.*표면 온도/);

for (const [sampleId, expectedAutomatic] of [["science", 10], ["history", 12]]) {
  const sample = library[sampleId];
  const automatic = sample.visual_gaps.filter((gap) => ["INTERRUPT", "DESCRIBE_AT_BREAK"].includes(gap.action));
  assert.equal(automatic.length, expectedAutomatic);
  assert.ok(automatic.every((gap) => gap.safe_to_speak && gap.confidence >= 0.72 && gap.public_description));
  const held = sample.visual_gaps.filter((gap) => gap.confidence < 0.72);
  assert.ok(held.length > 0);
  assert.ok(held.every((gap) => gap.action === "HOLD" && !gap.safe_to_speak && !gap.public_description));
}

console.log("Sample catalog: 14 checks passed");
