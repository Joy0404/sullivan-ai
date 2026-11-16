"""Paired AB/BA live benchmark with content-free output; dry-run by default.

Run with repository .venv Python. The private manifest/video/questions remain
local. --live --owned-media explicitly enables existing ephemeral Files upload.
Reports never store videos, subtitles, questions, model text, paths or API keys.
Manual quality review is performed locally; this command never promotes a route.
"""
import argparse
import asyncio
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))
from app.adapters.video_link import analyze_uploaded_video_with_gemini
from app.adapters.gemini_agent import run_agent_turn
from app.adapters.usage_metrics import capture_usage
from app.core.lecture_agent import LectureAgent
from app.core.token_comparison import evaluate_pairs, stage_totals, QUALITY_CHECKS
from app.core.token_optimization import experimental_route
from app.models import LectureCreate


def models():
    return {name: value if value.startswith("gemini-") and len(value) < 120 and all(c.isalnum() or c in "-._" for c in value) else "unknown"
            for name in ("GEMINI_MODEL", "GEMINI_FALLBACK_MODEL", "GEMINI_AGENT_MODEL")
            for value in [os.getenv(name, "gemini-2.5-flash").strip()]}


def quality_review(value, pair):
    keys = (*QUALITY_CHECKS, "no_regression", "held_leaks", "answer_leaks")
    clean = {key: value.get(key) for key in keys if type(value.get(key)) in {bool, int}}
    if not all(value.get(route + "_output_sha256") == pair.get(route, {}).get("output_sha256")
               and pair.get(route, {}).get("output_sha256") for route in ("baseline", "experimental")):
        clean["no_regression"] = False
    return clean


async def measure_run(case, route, manifest_dir, quality_artifact=None):
    report = {"completed": False, "cleanup_ok": False, "models": models(), "usage": [], "oracle": None}
    cleanup = {}
    with capture_usage() as records, (experimental_route() if route == "experimental" else nullcontext()):
        try:
            file = (manifest_dir / case["local_file"]).resolve()
            with file.open("rb") as media:
                report["input_sha256"] = hashlib.file_digest(media, "sha256").hexdigest()
            package = await analyze_uploaded_video_with_gemini(str(file), display_name="paired-owned-benchmark.mp4",
                mime_type=case.get("mime_type", "video/mp4"), title=case["title"], subject=case["subject"],
                problem_mode=case.get("problem_mode", False), api_key=os.environ["GEMINI_API_KEY"], cleanup_report=cleanup)
            agent = LectureAgent()
            session = agent.create_session(LectureCreate(title=case["title"], subject=case["subject"], problem_mode=case.get("problem_mode", False)))
            snapshot = agent.analyze(session.session_id, package)
            public = snapshot.model_dump_json()
            answers = []
            automatic = {"required_public_texts": all(text in public for text in case.get("required_public_texts", [])),
                         "forbidden_public_texts": all(text not in public for text in case.get("forbidden_public_texts", [])),
                         "required_times": all(any(gap.timestamp_ms == value for gap in snapshot.visual_gaps)
                                               for value in case.get("required_timestamps_ms", [])), "question_checks": []}
            for question in case["questions"]:
                result = await run_agent_turn(snapshot, message=question["message"], current_time_ms=question["current_time_ms"])
                output = result.model_dump_json()
                answers.append(result.model_dump(mode="json"))
                automatic["question_checks"].append({"required": all(text in output for text in question.get("required_fragments", [])),
                                                     "forbidden": all(text not in output for text in question.get("forbidden_fragments", [])),
                                                     "spoken": result.safe_to_speak})
            report["oracle"] = automatic
            artifact = json.dumps({"snapshot": snapshot.model_dump(mode="json"), "answers": answers}, ensure_ascii=False, indent=2) + "\n"
            report["output_sha256"] = hashlib.sha256(artifact.encode()).hexdigest()
            if quality_artifact:
                quality_artifact.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                quality_artifact.write_text(artifact)
                quality_artifact.chmod(0o600)
            report["completed"] = True
            with file.open("rb") as media:
                if hashlib.file_digest(media, "sha256").hexdigest() != report["input_sha256"]:
                    report["completed"] = False
        except Exception:
            # Deliberately no exception text, source paths, payload, or response.
            report["failure"] = "provider-or-local-validation-failed"
        report["usage"] = list(records)
        report["cleanup_ok"] = cleanup.get("provider") == "deleted"
    report["stages"] = stage_totals(report["usage"])
    return report


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review", type=Path, help="Private human review keyed by pair-1, pair-2, ...")
    parser.add_argument("--quality-artifacts", type=Path, help="Explicit private quality output directory outside the repo, separate from content-free metrics")
    parser.add_argument("--finalize", action="store_true", help="Review existing --output without any provider calls")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--owned-media", action="store_true")
    args = parser.parse_args()
    if args.quality_artifacts and args.quality_artifacts.resolve().is_relative_to(ROOT):
        parser.error("private quality artifacts must be outside the repository")
    if args.repeats < 2 or args.repeats % 2:
        parser.error("--repeats must be even and at least 2 for balanced AB/BA")
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    cases = manifest["cases"]
    tags = {tag for case in cases for tag in case.get("tags", [])}
    configured = bool(os.getenv("GEMINI_API_KEY", "").strip())
    live = args.live and args.owned_media and configured
    if args.live and not args.owned_media:
        parser.error("--live requires --owned-media for explicitly licensed ephemeral uploads")
    if args.live and manifest.get("ready_for_live") is not True:
        parser.error("fill teacher-approved oracle strings/times/questions and set ready_for_live=true")
    report = {"kind": "live" if live else "미측정", "provider_configured": configured,
              "default_route": "baseline", "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
              "pairs": [], "boundary": "Fixture regressions and live model usage are separate. No automatic promotion."}
    reviews = json.loads(args.review.read_text()) if args.review else {}
    if args.finalize:
        report = json.loads(args.output.read_text())
        if report["manifest_sha256"] != hashlib.sha256(manifest_bytes).hexdigest():
            parser.error("finalize requires the identical manifest")
        live = report.get("kind") == "live"
        for pair in report["pairs"]:
            pair["quality"] = quality_review(reviews.get(pair["id"], {}), pair)
    # The unconfigured/dry path performs no network, upload, or model request.
    if live and not args.finalize:
        for repeat in range(args.repeats):
            for case_index, case in enumerate(cases):
                if not case.get("questions"):
                    raise ValueError("each case requires the same question set for both routes")
                pair = {"id": f"pair-{len(report['pairs'])+1}", "case_index": case_index, "repeat": repeat,
                        "same_inputs": True, "order": [], "quality": {}}
                for route in (("baseline", "experimental") if repeat % 2 == 0 else ("experimental", "baseline")):
                    pair["order"].append(route)
                    artifact_path = args.quality_artifacts / f"{pair['id']}-{route}.json" if args.quality_artifacts else None
                    pair[route] = await measure_run(case, route, args.manifest.parent, artifact_path)
                pair["same_inputs"] = bool(pair["baseline"].get("input_sha256")) and pair["baseline"].get("input_sha256") == pair["experimental"].get("input_sha256")
                pair["quality"] = quality_review(reviews.get(pair["id"], {}), pair)
                # An automatic safety/content oracle failure cannot be approved
                # away by a review file. Human quality checks remain mandatory.
                for route in ("baseline", "experimental"):
                    oracle = pair[route].get("oracle") or {}
                    if (not oracle or any(oracle.get(key) is not True for key in ("required_public_texts", "forbidden_public_texts", "required_times"))
                            or any(not q["required"] or not q["forbidden"] for q in oracle.get("question_checks", []))):
                        pair["quality"]["no_regression"] = False
                report["pairs"].append(pair)
                report["gate"] = evaluate_pairs(report["pairs"], live=live, case_tags=tags, balanced_order=repeat >= 1,
                                                expected_cases=len(cases), expected_repeats=args.repeats)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    # Reapply deterministic oracles after finalize as well. Reviews cannot
    # overrule a measured missing fact or exposed protected fixture string.
    for pair in report["pairs"]:
        for route in ("baseline", "experimental"):
            oracle = pair.get(route, {}).get("oracle") or {}
            if (not oracle or any(oracle.get(key) is not True for key in ("required_public_texts", "forbidden_public_texts", "required_times"))
                    or any(not q["required"] or not q["forbidden"] for q in oracle.get("question_checks", []))):
                pair["quality"]["no_regression"] = False
    orders = [pair["order"][0] for pair in report["pairs"]]
    balanced = bool(orders) and orders.count("baseline") == orders.count("experimental")
    report["gate"] = evaluate_pairs(report["pairs"], live=live, case_tags=tags, balanced_order=balanced,
                                    expected_cases=len(cases), expected_repeats=args.repeats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"kind": report["kind"], "pairs": len(report["pairs"]), "gate": report["gate"]}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
