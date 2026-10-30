"""Dependency-light project verification for local and CI use."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def verify_python_syntax() -> int:
    paths = [path for path in ROOT.rglob("*.py") if "__pycache__" not in path.parts]
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return len(paths)


def verify_json() -> int:
    paths = [
        ROOT / "packages" / "contracts" / "events.schema.json",
        ROOT / "packages" / "test-fixtures" / "lecture_analysis_demo.json",
    ]
    for path in paths:
        json.loads(path.read_text(encoding="utf-8"))
    return len(paths)


def verify_web_contract() -> int:
    html = (ROOT / "apps" / "web" / "index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "apps" / "web" / "app.js").read_text(encoding="utf-8")
    ids = set(re.findall(r'id=["\']([^"\']+)', html))
    direct_refs = set(
        re.findall(r'\$\(["\']#([A-Za-z][\w:-]*)["\']\)', javascript)
    )
    missing = sorted(direct_refs - ids)
    if missing:
        raise AssertionError(f"app.js가 참조하지만 HTML에 없는 ID: {missing}")
    return len(direct_refs)


def verify_safety_markers() -> int:
    models = (ROOT / "apps" / "api" / "app" / "models.py").read_text(encoding="utf-8")
    gap = (ROOT / "apps" / "api" / "app" / "core" / "visual_gap.py").read_text(encoding="utf-8")
    web = (ROOT / "apps" / "web" / "app.js").read_text(encoding="utf-8")
    html = (ROOT / "apps" / "web" / "index.html").read_text(encoding="utf-8")
    api = (ROOT / "apps" / "api" / "app" / "main.py").read_text(encoding="utf-8")
    video_adapter = (ROOT / "apps" / "api" / "app" / "adapters" / "video_link.py").read_text(encoding="utf-8")
    required = {
        "HOLD action": "HOLD" in models and "GapAction.HOLD" in gap,
        "problem answer block": 'observation.kind == "answer"' in gap,
        "low confidence block": "observation.confidence < 0.72" in gap,
        "safe TTS gate": "gap?.safe_to_speak" in web,
        "local video object URL": "URL.createObjectURL(file)" in web,
        "explicit local video cloud consent": "local-video-ai-consent" in html and "cloud_analysis_consent" in api,
        "temporary local video deletion": "os.unlink(temporary_path)" in api,
        "provider video deletion": "cleanup_client.delete" in video_adapter,
        "uploaded video two-pass analysis": "analyze_uploaded_video_with_gemini" in video_adapter and "_verification_prompt(draft)" in video_adapter,
    }
    failed = [name for name, ok in required.items() if not ok]
    if failed:
        raise AssertionError(f"안전 기준 누락: {failed}")
    return len(required)


def verify_playback_and_voice() -> int:
    web = (ROOT / "apps" / "web" / "app.js").read_text(encoding="utf-8")
    html = (ROOT / "apps" / "web" / "index.html").read_text(encoding="utf-8")
    scheduler = (ROOT / "apps" / "web" / "playback-scheduler.js").read_text(encoding="utf-8")
    sample = (ROOT / "apps" / "web" / "sample-data.js").read_text(encoding="utf-8")
    history_sample = (ROOT / "apps" / "web" / "sample-data-history.js").read_text(encoding="utf-8")
    concepts = (ROOT / "apps" / "web" / "concept-tools.js").read_text(encoding="utf-8")
    narration = (ROOT / "apps" / "web" / "narration-context.js").read_text(encoding="utf-8")
    passages = (ROOT / "apps" / "web" / "passage-tools.js").read_text(encoding="utf-8")
    library = (ROOT / "apps" / "web" / "lecture-library.js").read_text(encoding="utf-8")
    voice_commands = (ROOT / "apps" / "web" / "voice-command-router.js").read_text(encoding="utf-8")
    required = {
        "crossing scheduler": "selectDueGap" in scheduler and "lateToleranceMs = 5_000" in scheduler,
        "youtube state synchronization": "onStateChange" in web and "processPlaybackTime" in web,
        "automatic pause": "narrateGap(gap, { automatic: true })" in web,
        "natural voice selection": "voiceScore" in web and "voiceschanged" in web,
        "voice chooser": 'id="speech-voice"' in html,
        "voice prosody controls": all(marker in html for marker in ['id="speech-style"', 'id="speech-pitch"', 'id="speech-volume"']),
        "early sample checkpoint": 'timestamp_ms: 43000' in sample and 'action: "DESCRIBE_AT_BREAK"' in sample,
        "dual sample catalog": "thJxqtTgSNY" in web and "sample-data-history.js" in html,
        "lecturer first concept playback": "playConceptSequence" in web and "conceptSequenceTimer" in web,
        "grounded concept search": "conceptsForSnapshot" in concepts and "mentioned" in concepts,
        "history safety hold": 'action: "HOLD"' in history_sample and 'safe_to_speak: false' in history_sample,
        "contextual concise narration": "contextFor" in narration and "compose" in narration and "SullivanNarration" in web,
        "voice preview": 'id="preview-voice"' in html and "음성 미리 듣기 후 자동 재생" in web,
        "underlined paragraph replay": "resolveCommand" in passages and "underlinedParagraphIds" in web and 'id="paragraph-voice-command"' in html,
        "paragraph speech pauses playback": "replayParagraphs" in web and "speakWithPlaybackPause" in web,
        "separate paragraph quick commands": "$$('[data-command]')" in web and "data-paragraph-command" in html,
        "local lecture library": "indexedDB" in library and "video_blob" in web and 'id="saved-lecture-list"' in html,
        "save and return home": "saveCurrentLectureAndReturnHome" in web and 'id="save-and-home"' in html,
        "saved lecture voice request": "findRequested" in library and 'id="saved-lecture-voice"' in html,
        "grounded Gemini action agent": "requestAgentTurn" in web and "/agent-turn" in web and 'id="agent-model-status"' in html,
        "client agent privacy boundary": "safeSnapshotForAgent" in web and "source_text: null" in web,
        "global hold space voice": "startSpaceVoiceRecognition" in web and "2_000" in web and "playSpaceVoiceReadyChime" in web,
        "release executes voice command": "finishSpaceVoiceGesture" in web and "executeGlobalVoiceCommand" in web,
        "double space returns to lecture": "handleQuickSpaceTap" in web and "cancelVoiceGuidanceAndResume" in web and "1_000" in web,
        "space command guide": "SPACE_COMMAND_GUIDE" in web and "beginSpaceVoiceRecognition" in web,
        "second hold skips command guide": "skipGuideAndBeginListening" in web and "guideSkipTimer" in web and "650" in web,
        "speech recognition auto restart": "startSpaceRecognitionEngine" in web and "recognitionRestartTimer" in web,
        "microphone permission blur guard": "visibilitychange" in web and "permission popover" in web,
        "triple space text command": "openTextCommandDialog" in web and 'id="text-command-input"' in html and "open_text_command" in voice_commands,
        "free keyboard and pointer control mode": "enterFreeControlMode" in web and "exitFreeControlMode" in web and "마우스 클릭과 화면의 모든 버튼" in web and "free_mode" in voice_commands,
        "direct arrow seeking": "plainArrow" in web and "seekRelative(-10_000)" in web and "seekRelative(10_000)" in web,
        "youtube keyboard conflict guard": "disablekb: 1" in web and "restoreGlobalSpaceFocus" in web,
        "voice command router": "SullivanVoiceCommands" in voice_commands and "summary_audio" in voice_commands,
        "visual mismatch regression": "gap-star-birth-board" in sample and "gap-star-hr-axis" not in sample,
    }
    failed = [name for name, ok in required.items() if not ok]
    if failed:
        raise AssertionError(f"재생·음성 기준 누락: {failed}")
    return len(required)


def verify_no_legacy_product() -> int:
    forbidden_paths = [
        ROOT / "apps" / "api" / "app" / "core" / "classroom_engine.py",
        ROOT / "docs" / "WINDOWS_3PERSON_COMPLETE_GUIDE.md",
        ROOT / "docs" / "TEAM_AND_BRANCHES.md",
    ]
    forbidden_paths.extend((ROOT / "docs" / "team").glob("*.md"))
    forbidden_paths.extend((ROOT / "docs" / "progress").glob("*.md"))
    existing = [str(path.relative_to(ROOT)) for path in forbidden_paths if path.exists()]
    if existing:
        raise AssertionError(f"폐기된 교실·3인 구조가 남아 있습니다: {existing}")
    return len(forbidden_paths)


def main() -> None:
    print(f"Python syntax: {verify_python_syntax()} files")
    print(f"JSON: {verify_json()} files")
    print(f"Web contract: {verify_web_contract()} DOM ids")
    print(f"Safety markers: {verify_safety_markers()} checks")
    print(f"Playback and voice: {verify_playback_and_voice()} checks")
    print(f"Legacy removal: {verify_no_legacy_product()} checks")
    print("Verification complete")


if __name__ == "__main__":
    main()
