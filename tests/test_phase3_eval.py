"""Phase 3 Verification Tests for TrustDesk.
Tests synthetic ML intent dataset (120 queries, 4 classes),
scikit-learn pipeline reporting Macro F1, dynamically computed N_test,
keyword baseline comparison (no assert on minimum F1),
40-question golden set eval with split [Eval - Mock LLM] and [Eval - Live LLM] reporting,
and CI workflow verification with Redis/PostgreSQL containers.
Technical demonstration on synthetic data - not a regulated banking system.
"""

from pathlib import Path
import pytest
import yaml

from backend.eval.golden_set import (
    GOLDEN_SET_QUESTIONS,
    evaluate_suite,
    run_full_golden_set_evaluation,
)
from backend.ml.dataset import SYNTHETIC_INTENT_DATASET
from backend.ml.intent_classifier import IntentClassifier, intent_classifier


# 1. Synthetic Intent Dataset Tests
def test_synthetic_dataset_shape_and_classes():
    """Verifies synthetic dataset has exactly 120 queries across 4 balanced classes (30 each)."""
    assert len(SYNTHETIC_INTENT_DATASET) == 120

    classes = {}
    for item in SYNTHETIC_INTENT_DATASET:
        c = item["intent"]
        classes[c] = classes.get(c, 0) + 1

    expected_classes = {"faq", "emi_calculation", "eligibility_check", "fallback"}
    assert set(classes.keys()) == expected_classes
    for c in expected_classes:
        assert classes[c] == 30, f"Class {c} expected 30 samples, got {classes[c]}"


# 2. Scikit-Learn Intent Classifier & Metric Evaluation Tests
def test_intent_classifier_evaluation_metrics():
    """Verifies ML evaluation: reports Macro F1, dynamically computed N_test,

    synthetic label, and comparison against keyword baseline.
    CRITICAL RULE: Does NOT assert a minimum F1 threshold in pytest.
    """
    classifier = IntentClassifier(random_state=42)
    results = classifier.train_and_evaluate(test_size=0.25)

    # 1. Dynamic N_test verification (computed from data split, not hardcoded)
    assert "n_test" in results
    assert results["n_test"] == int(120 * 0.25)
    assert results["n_train"] == int(120 * 0.75)
    assert results["n_test"] + results["n_train"] == 120

    # 2. Synthetic dataset designation
    assert results["dataset_designation"] == "synthetic"
    assert "synthetic" in results["evaluation_label"].lower()

    # 3. Macro F1 metric presence and validity (no minimum threshold asserted)
    assert "macro_f1_ml" in results
    assert isinstance(results["macro_f1_ml"], float)
    assert 0.0 <= results["macro_f1_ml"] <= 1.0

    # 4. Comparison against dual keyword baselines on identical test split
    assert "keyword_baseline_simple_macro_f1" in results
    assert "keyword_baseline_enhanced_macro_f1" in results
    assert isinstance(results["keyword_baseline_simple_macro_f1"], float)
    assert isinstance(results["keyword_baseline_enhanced_macro_f1"], float)

    # 5. Per-class precision/recall and confusion matrix
    assert "per_class_metrics" in results
    for cls in results["classes"]:
        assert cls in results["per_class_metrics"]
        assert "precision" in results["per_class_metrics"][cls]
        assert "recall" in results["per_class_metrics"][cls]
        assert "f1_score" in results["per_class_metrics"][cls]

    assert "confusion_matrix" in results
    assert len(results["confusion_matrix"]["matrix"]) == len(results["classes"])


def test_intent_classifier_prediction():
    """Verifies classifier prediction output format and confidence estimation."""
    intent_classifier.train_and_evaluate()

    intent, conf = intent_classifier.predict("What is the interest rate on home loans?")
    assert intent in {"faq", "emi_calculation", "eligibility_check", "fallback"}
    assert 0.0 <= conf <= 1.0


# 3. 40-Question Golden Set Evaluation Tests
def test_golden_set_composition():
    """Verifies golden set contains exactly 40 questions across the required 5 categories."""
    assert len(GOLDEN_SET_QUESTIONS) == 40

    categories = {}
    for q in GOLDEN_SET_QUESTIONS:
        cat = q["expected_category"]
        categories[cat] = categories.get(cat, 0) + 1

    assert categories.get("faq") == 20
    assert categories.get("eligibility_check") == 5
    assert categories.get("emi_calculation") == 5
    assert categories.get("fallback") == 5
    assert categories.get("injection_refusal") == 5


@pytest.mark.asyncio
async def test_golden_set_mock_llm_evaluation():
    """Verifies golden set execution labeled explicitly as [Eval - Mock LLM] with per-category pass rates."""
    mock_results = await evaluate_suite(client_type="mock")

    assert mock_results["evaluation_label"] == "[Eval - Mock LLM]"
    assert mock_results["status"] == "completed"
    assert mock_results["dataset_type"] == "synthetic_golden_set"
    assert mock_results["total_questions"] == 40
    assert mock_results["injections_intercepted"] == 5
    assert mock_results["concordance_rate"] > 0.80
    assert mock_results["average_grounding_score"] > 0.0
    assert "MockLLMClient" in mock_results["model_runtime"]
    assert "per_category_pass_rates" in mock_results
    assert "faq" in mock_results["per_category_pass_rates"]
    assert "eligibility_check" in mock_results["per_category_pass_rates"]
    assert "emi_calculation" in mock_results["per_category_pass_rates"]
    assert "injection_refusal" in mock_results["per_category_pass_rates"]
    assert "fallback" in mock_results["per_category_pass_rates"]


@pytest.mark.asyncio
async def test_golden_set_live_llm_reporting_isolation():
    """Verifies that [Eval - Live LLM] is reported distinctly and separated from the mock suite."""
    live_results = await evaluate_suite(client_type="live", live_provider=None)

    assert live_results["evaluation_label"] == "[Eval - Live LLM]"
    assert live_results["status"] in ("skipped", "completed")
    assert "timestamp" in live_results


@pytest.mark.asyncio
async def test_full_golden_set_dual_split_report():
    """Verifies run_full_golden_set_evaluation returns [Eval - Mock LLM], [Eval - Live LLM], and [Eval - Stress Test]."""
    full_report = await run_full_golden_set_evaluation()

    assert "[Eval - Mock LLM]" in full_report
    assert "[Eval - Live LLM]" in full_report
    assert "[Eval - Stress Test (10 Questions)]" in full_report
    assert full_report["[Eval - Mock LLM]"]["total_questions"] == 40
    assert full_report["[Eval - Stress Test (10 Questions)]"]["total_questions"] == 10


def test_independent_evaluation_suite_frozen_router():
    """Verifies independent evaluation of 12 novel queries on frozen router.
    Confirms out-of-scope performance (4/6) and documents keyword absence failure mode (0/6).
    """
    from backend.eval.independent_set import evaluate_independent_set_on_router

    results = evaluate_independent_set_on_router()
    assert results["total_queries"] == 12
    assert results["out_of_scope_n"] == 6
    assert results["in_domain_n"] == 6
    assert results["out_of_scope_matched"] == 4
    assert results["in_domain_matched"] == 0
    assert results["overall_concordance"] == 0.3333


def test_independent_20_query_evaluation_before_and_after_hybrid_router():
    """Verifies evaluation of 20 development queries before (rule router) and after (hybrid router).
    Demonstrates jump from 9/20 (45.0%) to 17 direct, 3 clarifying, and 0 misrouted.
    """
    from backend.eval.independent_set_20 import evaluate_independent_20_on_router
    from backend.agent.graph import detect_intent_rule_based, route_intent_hybrid

    # Before change (rule-based router)
    res_before = evaluate_independent_20_on_router(router_func=detect_intent_rule_based)
    assert res_before["total_queries"] == 20
    assert res_before["matched_count"] == 9
    assert res_before["concordance_rate"] == 0.45

    # After change (hybrid router): 17 direct matches, 3 clarifying, 0 misrouted
    def hybrid_adapter(q: str) -> str:
        intent, _conf, _path = route_intent_hybrid(q)
        return intent

    res_after = evaluate_independent_20_on_router(router_func=hybrid_adapter)
    assert res_after["total_queries"] == 20
    assert res_after["matched_count"] == 17
    assert res_after["concordance_rate"] == 0.85

    clarified = [r for r in res_after["results"] if r["predicted"] == "clarify"]
    misrouted = [r for r in res_after["results"] if r["predicted"] != "clarify" and not r["matched"]]
    assert len(clarified) == 3
    assert len(misrouted) == 0


@pytest.mark.asyncio
async def test_low_confidence_query_returns_clarifying_question():
    """Verifies that an ambiguous or low-confidence query yields a clarifying question rather than refusal."""
    from backend.agent.graph import CLARIFYING_QUESTION_TEXT, run_agent_workflow

    result = await run_agent_workflow(
        query="Purani gaadi khareedne ke liye paise mil sakte hain kya bank se?",
        channel="untrusted",
    )
    assert result["intent"] == "clarify"
    assert CLARIFYING_QUESTION_TEXT in result["response_text"]
    assert result["fallback_triggered"] is False


# 4. CI Workflow Configuration Verification
def test_ci_workflow_yaml_structure():
    """Verifies .github/workflows/ci.yml defines Redis and PostgreSQL service containers and markers."""
    ci_path = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ci.yml"
    assert ci_path.exists(), "ci.yml must exist"

    with open(ci_path, "r", encoding="utf-8") as f:
        ci_config = yaml.safe_load(f)

    jobs = ci_config.get("jobs", {})
    assert "test" in jobs
    test_job = jobs["test"]

    # Verify service containers
    services = test_job.get("services", {})
    assert "redis" in services
    assert "postgres" in services
    assert "redis:7-alpine" in services["redis"]["image"]
    assert "postgres:16-alpine" in services["postgres"]["image"]

    # Verify steps contain fast unit and live integration targets
    steps = test_job.get("steps", [])
    step_commands = [s.get("run", "") for s in steps if "run" in s]

    assert any('pytest -m "not integration"' in cmd for cmd in step_commands)
    assert any('pytest -m "integration"' in cmd for cmd in step_commands)
    assert any("REQUIRE_INTEGRATION" in str(s.get("env", {})) for s in steps)


def test_blind_15_query_evaluation_frozen_router():
    """Verifies evaluation of 15 novel blind queries on the frozen hybrid router (commit 3eebf52).
    Results: 9 pass, 4 clarify, 2 false refusal, 0 misroute out of N=15.
    """
    from backend.agent.graph import route_intent_hybrid
    from backend.eval.blind_set_15 import evaluate_blind_15_on_router, FROZEN_ROUTER_COMMIT

    assert FROZEN_ROUTER_COMMIT == "3eebf52"
    res = evaluate_blind_15_on_router(route_intent_hybrid)

    assert res["total"] == 15
    assert res["pass_count"] == 9
    assert res["clarify_count"] == 4
    assert res["false_refusal_count"] == 2
    assert res["misroute_count"] == 0
