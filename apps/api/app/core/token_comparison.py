"""Strict paired usage arithmetic. Unknown usage never becomes a saving."""
TOKEN_FIELDS = ("input_tokens", "output_tokens", "reasoning_tokens", "cache_tokens", "total_tokens")
QUALITY_CHECKS = ("required_information", "reading_and_explanation_times", "answer_quality",
                  "long_passage_and_underline", "spoken_board_index_only", "keyboard_and_reader")
REQUIRED_CASES = {"inequality", "axis-unit", "long-passage-underline", "already-spoken", "blur", "answer", "late-question"}


def stage_totals(records):
    result = {}
    for stage in ("analysis", "verification", "question"):
        group = [r for r in records if r["stage"] == stage]
        result[stage] = {"requests": len(group), "retries": sum(bool(r["retry"]) for r in group),
                         "failed_requests": sum(not r["success"] for r in group)}
        for field in TOKEN_FIELDS:
            result[stage][field] = (sum(r[field] for r in group)
                                   if group and all(type(r.get(field)) is int and r[field] >= 0 for r in group) else None)
        result[stage]["measurement"] = "measured" if group and result[stage]["total_tokens"] is not None else "미측정" if group else "no-call"
    return result


def evaluate_pairs(pairs, *, live, case_tags, balanced_order, expected_cases=None, expected_repeats=None):
    reasons = []
    if not live: reasons.append("live-provider-measurement-pending")
    if not REQUIRED_CASES <= set(case_tags): reasons.append("required-quality-cases-missing")
    if not balanced_order: reasons.append("balanced-AB-BA-runs-required")
    if expected_cases is not None or expected_repeats is not None:
        expected = {(case, repeat) for case in range(expected_cases or 0) for repeat in range(expected_repeats or 0)}
        actual = [(pair.get("case_index"), pair.get("repeat")) for pair in pairs]
        if not expected or len(actual) != len(expected) or set(actual) != expected:
            reasons.append("complete-case-repetitions-required")
        if any(pair.get("order") != (["baseline", "experimental"] if pair.get("repeat", 0) % 2 == 0
                                     else ["experimental", "baseline"]) for pair in pairs):
            reasons.append("balanced-AB-BA-runs-required")
    sums = {"baseline": 0, "experimental": 0}
    complete = bool(pairs)
    for pair in pairs:
        for route in sums:
            run = pair.get(route, {})
            records = run.get("usage", [])
            if (not run.get("completed") or not run.get("cleanup_ok") or not records
                    or any(type(r.get("total_tokens")) is not int or r["total_tokens"] < 0 for r in records)):
                complete = False
            else:
                sums[route] += sum(r["total_tokens"] for r in records)
        review = pair.get("quality", {})
        if (any(review.get(check) is not True for check in QUALITY_CHECKS)
                or type(review.get("held_leaks")) is not int or review.get("held_leaks") != 0
                or type(review.get("answer_leaks")) is not int or review.get("answer_leaks") != 0
                or review.get("no_regression") is not True):
            reasons.append("quality-review-pending-or-failed")
        a = pair.get("baseline", {}).get("models")
        b = pair.get("experimental", {}).get("models")
        if not a or a != b: reasons.append("model-conditions-differ")
        actual_models = []
        for route in sums:
            used = {}
            for record in pair.get(route, {}).get("usage", []):
                used.setdefault(record["stage"], set()).add(record.get("model"))
            actual_models.append(used)
        if (actual_models[0] != actual_models[1]
                or any(not model or model == "unknown" for used in actual_models for group in used.values() for model in group)):
            reasons.append("model-conditions-differ")
        if not pair.get("same_inputs"): reasons.append("input-conditions-differ")
    if not complete: reasons.append("complete-usage-including-retries-required")
    if complete and sums["experimental"] >= sums["baseline"]: reasons.append("total-tokens-did-not-decrease")
    # A percentage exists only for complete, genuinely live identical inputs
    # and models. Failed quality is reported independently of the arithmetic.
    comparable = live and complete and balanced_order and not any(
        reason in reasons for reason in ("model-conditions-differ", "input-conditions-differ",
                                         "complete-case-repetitions-required", "balanced-AB-BA-runs-required"))
    return {"eligible_for_submission": not reasons, "default_route": "baseline",
            "reasons": sorted(set(reasons)),
            "stage_comparison": {route: stage_totals([record for pair in pairs for record in pair.get(route, {}).get("usage", [])])
                                 for route in sums},
            "paired_total_tokens": sums if comparable else None,
            "reduction_percent": (round((1 - sums["experimental"] / sums["baseline"]) * 100, 2)
                                  if comparable and sums["baseline"] > 0 else None)}
