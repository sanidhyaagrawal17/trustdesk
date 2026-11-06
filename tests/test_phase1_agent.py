"""Phase 1 Verification Tests for TrustDesk.
Tests LangGraph graph, ChromaDB dense retrieval, test_tfidf_fallback,
deterministic EMI calculator, rule-based eligibility checker, grounding,
deterministic fallback, timeouts, and SSE streaming.
Technical demonstration on synthetic data - not a regulated banking system.
"""

import asyncio
import pytest
from httpx import ASGITransport, AsyncClient

from backend.agent.graph import (
    DETERMINISTIC_FALLBACK_TEXT,
    agent_graph,
    create_agent_graph,
    detect_intent_rule_based,
    run_agent_workflow,
)
from backend.agent.state import AgentState
from backend.api.app import app
from backend.core.grounding import calculate_grounding_score, verify_grounding
from backend.core.llm_client import MockLLMClient
from backend.tools.eligibility_checker import evaluate_eligibility
from backend.tools.emi_calculator import calculate_emi
from backend.tools.faq_tool import SYNTHETIC_FAQ_DATA, faq_engine


# 1. LangGraph Engine Tests
def test_langgraph_import_and_compilation():
    """Confirms real langgraph StateGraph import and successful graph compilation."""
    from langgraph.graph import END, StateGraph

    assert StateGraph is not None
    assert END is not None

    graph = create_agent_graph()
    assert graph is not None
    assert hasattr(graph, "ainvoke")
    assert hasattr(graph, "invoke")


# 2. Real ChromaDB Retrieval Tests
def test_chromadb_initialization_and_count():
    """Verifies real ChromaDB collection is initialized with all 35 synthetic FAQ entries."""
    assert len(SYNTHETIC_FAQ_DATA) == 35
    count = faq_engine.collection.count()
    assert count >= 35


def test_chromadb_dense_semantic_search():
    """Tests semantic retrieval on ChromaDB using a paraphrased query with low word overlap."""
    paraphrased_query = "Can you share how much borrowing charges I will be assessed on a residential property mortgage?"
    results = faq_engine.search(paraphrased_query, n_results=2)
    assert len(results) >= 1
    top_result = results[0]
    # Successfully routes to home loan domain despite zero keyword overlap on 'charges', 'borrowing', 'residential'
    assert top_result["category"] == "home_loan"
    assert top_result["source"] == "chromadb_dense"


# 3. Mandated TF-IDF Fallback Test
def test_tfidf_fallback():
    """Tests in-memory TF-IDF fallback explicitly labelled as test_tfidf_fallback."""
    results = faq_engine.test_tfidf_fallback("processing fee for personal loan", n_results=2)
    assert len(results) == 2
    assert results[0]["source"] == "test_tfidf_fallback"
    assert "fee" in results[0]["answer"].lower() or "personal" in results[0]["answer"].lower()
    assert results[0]["score"] > 0.0


# 4. Deterministic Mathematical EMI Calculator Tests
def test_emi_calculator_deterministic_accuracy():
    """Verifies deterministic EMI formula: E = P * r * (1+r)^n / ((1+r)^n - 1)."""
    # 10 Lakh at 12% per annum (1.0% per month) for 12 months
    # Formula exact: 1,000,000 * 0.01 * (1.01)^12 / ((1.01)^12 - 1) = 88,848.79
    calc = calculate_emi(principal=1000000.0, annual_interest_rate=12.0, tenure_months=12)
    assert pytest.approx(calc["monthly_emi"], rel=1e-3) == 88848.79
    assert calc["total_payment"] > 1000000.0
    assert pytest.approx(calc["total_interest"], rel=1e-3) == (calc["total_payment"] - 1000000.0)


def test_emi_calculator_zero_interest():
    """Verifies zero interest rate edge case (E = P / n)."""
    calc = calculate_emi(principal=60000.0, annual_interest_rate=0.0, tenure_months=12)
    assert calc["monthly_emi"] == 5000.0
    assert calc["total_payment"] == 60000.0
    assert calc["total_interest"] == 0.0


def test_emi_calculator_invalid_inputs():
    """Asserts ValueError on invalid or negative numerical inputs."""
    with pytest.raises(ValueError):
        calculate_emi(principal=-1000.0, annual_interest_rate=10.0, tenure_months=12)
    with pytest.raises(ValueError):
        calculate_emi(principal=10000.0, annual_interest_rate=10.0, tenure_months=0)
    with pytest.raises(ValueError):
        calculate_emi(principal=10000.0, annual_interest_rate=-5.0, tenure_months=12)


# 5. Rule-Based Eligibility Tests (Invented Thresholds)
def test_eligibility_invented_criteria_approved():
    """Verifies approval for applicant satisfying invented criteria (Age 21-60, Salary >= 25k, FOIR <= 50%)."""
    res = evaluate_eligibility(
        age=28,
        monthly_salary=60000.0,
        existing_emis=10000.0,
        requested_loan_amount=200000.0,
        tenure_months=36,
        annual_interest_rate=10.0,
    )
    assert res["is_eligible"] is True
    assert res["max_allowable_emi"] == 20000.0  # 60,000 * 0.50 - 10,000


def test_eligibility_age_too_young():
    """Verifies rejection when age < 21 under invented threshold."""
    res = evaluate_eligibility(age=19, monthly_salary=40000.0)
    assert res["is_eligible"] is False
    assert any("below the invented minimum" in r for r in res["reasons"])


def test_eligibility_age_too_old():
    """Verifies rejection when age > 60 under invented threshold."""
    res = evaluate_eligibility(age=64, monthly_salary=80000.0)
    assert res["is_eligible"] is False
    assert any("exceeds the invented maximum" in r for r in res["reasons"])


def test_eligibility_min_salary_breach():
    """Verifies rejection when monthly salary < INR 25,000 under invented threshold."""
    res = evaluate_eligibility(age=25, monthly_salary=20000.0)
    assert res["is_eligible"] is False
    assert any("below the invented threshold of INR 25,000" in r for r in res["reasons"])


def test_eligibility_foir_limit_breach():
    """Verifies rejection when existing obligations breach the 50% FOIR cutoff."""
    res = evaluate_eligibility(
        age=32,
        monthly_salary=50000.0,
        existing_emis=28000.0,  # 28k > 25k (50% of 50k)
    )
    assert res["is_eligible"] is False
    assert any("FOIR" in r for r in res["reasons"])
    assert res["max_allowable_emi"] == 0.0


# 6. Intent Routing Heuristics Tests
def test_intent_routing_rules():
    """Verifies keyword-based intent classification for agent routing."""
    assert detect_intent_rule_based("Calculate EMI for 500000 at 9% for 5 years") == "emi_calculation"
    assert detect_intent_rule_based("What is my monthly installment for 1000000?") == "emi_calculation"
    assert detect_intent_rule_based("Am I eligible with 40000 salary?") == "eligibility_check"
    assert detect_intent_rule_based("What is the minimum age to qualify?") == "eligibility_check"
    assert detect_intent_rule_based("What is the home loan interest rate?") == "faq"
    assert detect_intent_rule_based("hi") == "fallback"


# 7. Token-Overlap Grounding Guardrail Tests
def test_token_overlap_grounding_positive():
    """Tests grounding verification where response tokens overlap with reference text."""
    reference = ["Home loan interest rates in TrustDesk range between 8.35% and 9.75% per annum."]
    response = "TrustDesk home loan interest rates range from 8.35% to 9.75% per annum."

    score = calculate_grounding_score(response, reference)
    assert score > 0.50

    eval_res = verify_grounding(response, reference, threshold=0.35)
    assert eval_res["is_grounded"] is True
    assert eval_res["advisory"] == ""


def test_token_overlap_grounding_negative():
    """Tests grounding flag when response contains ungrounded claims."""
    reference = ["Vehicle hypothecation places a legal lien on the vehicle registration."]
    hallucinated = "Quantum cryptocurrency derivatives provide zero down payment mortgages on Mars."

    score = calculate_grounding_score(hallucinated, reference)
    assert score < 0.20

    eval_res = verify_grounding(hallucinated, reference, threshold=0.35)
    assert eval_res["is_grounded"] is False
    assert "[Grounding Advisory]" in eval_res["advisory"]
    assert "[Grounding Advisory]" in eval_res["verified_text"]


# 8. Agent Graph End-to-End & Fallback Tests
@pytest.mark.asyncio
async def test_agent_workflow_faq_flow():
    """Tests end-to-end execution of agent graph for FAQ queries."""
    result = await run_agent_workflow(
        query="What is the maximum tenure for a home loan?",
        channel="untrusted",
    )
    assert result["intent"] == "faq"
    assert result["fallback_triggered"] is False
    assert len(result["retrieved_sources"]) > 0
    assert result["grounding_score"] > 0.0


@pytest.mark.asyncio
async def test_agent_workflow_deterministic_fallback():
    """Tests that out-of-scope or empty queries trigger deterministic fallback."""
    result = await run_agent_workflow(
        query="x",
        channel="untrusted",
    )
    assert result["fallback_triggered"] is True
    assert DETERMINISTIC_FALLBACK_TEXT in result["response_text"]


@pytest.mark.asyncio
async def test_agent_workflow_timeout_fallback():
    """Tests that timeout triggers deterministic fallback safely."""
    # Force timeout by providing negative timeout
    result = await run_agent_workflow(
        query="What is the interest rate?",
        timeout_seconds=0.0001,
        max_retries=0,
    )
    assert result["fallback_triggered"] is True
    assert DETERMINISTIC_FALLBACK_TEXT in result["response_text"]


# 9. SSE Streaming API Endpoint Test
@pytest.mark.asyncio
async def test_sse_chat_streaming_endpoint():
    """Tests /api/chat/stream endpoint for SSE event protocol conformance."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/chat/stream",
            json={
                "message": "What is the processing fee for a personal loan?",
                "channel": "untrusted",
            },
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        content = response.text
        # Verify SSE event names and contents
        assert "event: status" in content
        assert "event: token" in content
        assert "event: metadata" in content
        assert "event: done" in content
        assert "trace_id" in content

        # Verify metadata specifies chroma retriever for normal FAQ runs
        import json
        lines = content.split("\n")
        metadata_line = next(line for i, line in enumerate(lines) if "event: metadata" in lines[i-1] and line.startswith("data: "))
        metadata_payload = json.loads(metadata_line[6:])
        assert metadata_payload["retriever_used"] == "chroma"
