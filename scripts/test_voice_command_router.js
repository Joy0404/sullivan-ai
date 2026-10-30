const assert = require("node:assert/strict");
const commands = require("../apps/web/voice-command-router.js");

assert.equal(commands.classify("영상 멈춰").type, "pause");
assert.equal(commands.classify("계속 재생해").type, "play");
assert.equal(commands.classify("영상 시작해줘").type, "play");
assert.equal(commands.classify("자유 모드로 바꿔줘").type, "free_mode");
assert.equal(commands.classify("홈으로 돌아가").type, "home");
assert.equal(commands.classify("현재 칠판 화면 설명해줘").type, "describe");
assert.deepEqual(commands.classify("샘플 1 시작해줘"), { type: "sample", sampleId: "science" });
assert.deepEqual(commands.classify("왜란과 호란 샘플 보여줘"), { type: "sample", sampleId: "history" });
assert.equal(commands.classify("요약을 음성으로 들려줘").type, "summary_audio");
assert.equal(commands.classify("밑줄 친 문단 다시 들려줘").type, "paragraph");
assert.equal(commands.classify("주계열성 핵심 개념 찾아줘").type, "concept");
assert.deepEqual(commands.classify("자동 해설 켜줘"), { type: "auto_narration", enabled: true });
assert.deepEqual(commands.classify("자동 해설 꺼줘"), { type: "auto_narration", enabled: false });
assert.deepEqual(commands.classify("학습 노트 열어줘"), { type: "panel", panelId: "study-panel" });
assert.deepEqual(commands.classify("요약 버튼 눌러"), { type: "button", label: "요약" });
assert.equal(commands.classify("이 내용을 발표문으로 만들어줘").type, "chat");
assert.equal(commands.isDoubleTap(1000, 1999), true);
assert.equal(commands.isDoubleTap(1000, 2001), false);
assert.equal(commands.classifyTapSequence(1), "single_tap");
assert.equal(commands.classifyTapSequence(2), "cancel_guidance");
assert.equal(commands.classifyTapSequence(3), "open_text_command");
assert.equal(commands.classifyTapSequence(1, { freeMode: true }), "toggle_playback");
assert.equal(commands.classifyTapSequence(2, { freeMode: true }), "exit_free_mode");

console.log("Voice command router: 23 checks passed");
