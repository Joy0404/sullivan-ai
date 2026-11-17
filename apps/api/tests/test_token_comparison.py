from copy import deepcopy

import pytest

from app.core.token_comparison import QUALITY_CHECKS, REQUIRED_CASES, evaluate_pairs, stage_totals


def pair():
    def run(total):
        return {"completed": True, "cleanup_ok": True, "models": {"model": "gemini-2.5-flash"},
                "usage": [{"stage": "analysis", "retry": False, "success": True, "model": "gemini-2.5-flash",
                           "input_tokens": total-20, "output_tokens": 20, "reasoning_tokens": None,
                           "cache_tokens": None, "total_tokens": total}]}
    return {"baseline": run(100), "experimental": run(80), "same_inputs": True,
            "quality": {**{key: True for key in QUALITY_CHECKS}, "no_regression": True, "held_leaks": 0, "answer_leaks": 0}}


def gate(pairs, **kwargs):
    return evaluate_pairs(pairs, live=True, case_tags=REQUIRED_CASES, balanced_order=True, **kwargs)


def test_synthetic_fixture_counts_cannot_approve_or_claim_savings():
    result = evaluate_pairs([pair()], live=False, case_tags=REQUIRED_CASES, balanced_order=True)
    assert not result["eligible_for_submission"]
    assert result["reduction_percent"] is None
    assert result["default_route"] == "baseline"


def test_only_complete_equivalent_live_pair_has_percentage_default_stays_baseline():
    result = gate([pair()])
    assert result["eligible_for_submission"] and result["reduction_percent"] == 20
    assert result["default_route"] == "baseline"


@pytest.mark.parametrize("defect", ["unmeasured", "model", "inputs", "quality", "held", "answer", "cleanup", "no-saving"])
def test_incomplete_failed_or_leaking_pair_cannot_promote(defect):
    data = pair()
    if defect == "unmeasured": data["experimental"]["usage"][0]["total_tokens"] = None
    if defect == "model": data["experimental"]["models"] = {"model": "other"}
    if defect == "inputs": data["same_inputs"] = False
    if defect == "quality": data["quality"].pop("answer_quality")
    if defect == "held": data["quality"]["held_leaks"] = 1
    if defect == "answer": data["quality"]["answer_leaks"] = 1
    if defect == "cleanup": data["experimental"]["cleanup_ok"] = False
    if defect == "no-saving": data["experimental"]["usage"][0]["total_tokens"] = 101
    assert not gate([data])["eligible_for_submission"]


def test_retry_costs_are_included_and_unknown_counts_are_not_zero_filled():
    data = pair()
    retry = deepcopy(data["experimental"]["usage"][0])
    retry.update(total_tokens=30, stage="verification", retry=True, success=False)
    data["experimental"]["usage"].append(retry)
    assert not gate([data])["eligible_for_submission"]
    totals = stage_totals(data["experimental"]["usage"])
    assert totals["verification"]["retries"] == 1
    assert totals["verification"]["failed_requests"] == 1
    assert totals["verification"]["total_tokens"] == 30
    assert totals["verification"]["cache_tokens"] is None
    retry["total_tokens"] = None
    assert gate([data])["reduction_percent"] is None


@pytest.mark.parametrize("model", ["gemini-other", "unknown", None])
def test_actual_provider_models_must_match_even_when_configuration_matches(model):
    data = pair()
    data["experimental"]["usage"][0]["model"] = model
    result = gate([data])
    assert "model-conditions-differ" in result["reasons"]
    assert not result["eligible_for_submission"] and result["reduction_percent"] is None


def test_every_manifest_case_and_balanced_repeat_must_be_measured():
    pairs = []
    for repeat in range(2):
        for case in range(2):
            data = pair()
            data.update(case_index=case, repeat=repeat,
                        order=["baseline", "experimental"] if repeat == 0 else ["experimental", "baseline"])
            pairs.append(data)
    assert gate(pairs, expected_cases=2, expected_repeats=2)["eligible_for_submission"]
    for incomplete in (pairs[:2], pairs[:3], [pairs[0], pairs[0], *pairs[2:]]):
        result = gate(incomplete, expected_cases=2, expected_repeats=2)
        assert not result["eligible_for_submission"] and result["reduction_percent"] is None
    pairs[-1]["order"].reverse()
    assert not gate(pairs, expected_cases=2, expected_repeats=2)["eligible_for_submission"]
