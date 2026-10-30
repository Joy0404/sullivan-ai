const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const narration = require("../apps/web/narration-context.js");

const context = vm.createContext({ window: {} });
for (const name of ["sample-data.js", "sample-data-history.js"]) {
  vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "apps", "web", name), "utf8"), context, { filename: name });
}

const samples = context.window.SULLIVAN_SAMPLE_LIBRARY;
for (const sample of Object.values(samples)) {
  const automatic = sample.visual_gaps.filter((gap) => ["INTERRUPT", "DESCRIBE_AT_BREAK"].includes(gap.action));
  for (const gap of automatic) {
    const cue = narration.contextFor(gap, sample.concept_index);
    const spoken = narration.compose(gap, sample.concept_index);
    assert.equal(cue.prepared, true, `${gap.gap_id} needs a prepared concise context`);
    assert.ok(cue.lead.length <= 42, `${gap.gap_id} lead is too long`);
    assert.ok(cue.bridge.length <= 42, `${gap.gap_id} bridge is too long`);
    assert.ok(spoken.includes(gap.public_description));
    assert.ok(spoken.split(/[.!?]/).filter(Boolean).length <= 4);
  }
}

assert.equal(narration.compose({ public_description: "화면 핵심", timestamp_ms: 0 }, []), "화면 핵심.");
console.log("Contextual narration: 89 checks passed");
