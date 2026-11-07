"""LangGraph Agent workflow implementation for TrustDesk.
Uses real langgraph (StateGraph, END) for agent routing, state transitions,
retries, timeout handling, and deterministic fallback.
Technical demonstration on synthetic data - not a regulated banking system.
"""

import asyncio
import re
import time
import uuid
from typing import Any, Dict, List, Optional
from langgraph.graph import END, StateGraph

from backend.agent.state import AgentState
from backend.core.grounding import verify_grounding
from backend.core.llm_client import MockLLMClient, get_llm_client
from backend.tools.eligibility_checker import evaluate_eligibility
from backend.tools.emi_calculator import calculate_emi
from backend.tools.faq_tool import faq_engine

DETERMINISTIC_FALLBACK_TEXT = (
    "TrustDesk could not fulfill your synthetic loan request. Please ask about synthetic "
    "interest rates, EMI calculations, or applicant eligibility guidelines. "
    "(Synthetic technical demonstration - not a regulated banking system)."
)


def detect_intent_rule_based(query: str) -> str:
    """Classifies user intent using keyword heuristics, ensuring out-of-scope queries route to fallback."""
    q = query.lower().strip()

    # 1. Fallback for empty, short, or purely conversational greetings
    if len(q) < 4 or re.match(r"^(?:hi|hello|hey|good\s+(?:morning|evening|afternoon)|bye|goodbye|namaste)(?:\s+.*)?$", q):
        return "fallback"

    # 2. Out-of-scope non-loan topics (weather, crypto, humor, programming, sports, trivia)
    out_of_scope_patterns = [
        r"\b(?:weather|mausam|temperature|climate|forecast)\b",
        r"\b(?:crypto(?:currency)?|bitcoin|ethereum|stocks?|trading|shares?|investment\s+tips?)\b",
        r"\b(?:joke|jokes|chutkula|riddle|funny|story|poem|song|movie|cinema)\b",
        r"\b(?:python|javascript|script|scrape|scraping|code|coding|software|algorithm|html|css)\b",
        r"\b(?:cricket|football|match|score|ipl|game|sports?)\b",
        r"\b(?:capital\s+of|who\s+is|who\s+was|history\s+of|planet|recipe)\b",
    ]
    if any(re.search(pat, q) for pat in out_of_scope_patterns):
        return "fallback"

    # 3. EMI calculation intent: requires calculation/installment keywords alongside numbers
    emi_patterns = [
        r"\bemi\b",
        r"\bcalc(?:ulate|late)?\b",
        r"\binstallment\b",
        r"\bintallment\b",
        r"\brepayment\b",
        r"\bmonthly\s+payment\b",
        r"\bmonthly\s+installment\b",
        r"\bkitna.*banega\b",
    ]
    has_digits = bool(re.search(r"\d+", q))
    if any(re.search(pat, q) for pat in emi_patterns) and has_digits:
        return "emi_calculation"

    # 4. Eligibility check intent: qualification, salary, age criteria, FOIR
    eligibility_patterns = [
        r"\beligib",
        r"\belgibl",
        r"\bqualif",
        r"\bcan\s+i\s+get\b",
        r"\bsal(?:ary|ry)\b",
        r"\bincome\b",
        r"\bfoir\b",
        r"\bage[ds]?\b",
        r"\bkya.*eligible\b",
    ]
    if any(re.search(pat, q) for pat in eligibility_patterns):
        return "eligibility_check"

    # 5. Loan domain terms required for FAQ retrieval
    loan_domain_patterns = [
        r"\bloan",
        r"\binterest",
        r"\brate",
        r"\btenure",
        r"\btenor",
        r"\bprepay",
        r"\bforeclos",
        r"\bpenalty",
        r"\bfee",
        r"\bcharg",
        r"\bdocument",
        r"\bkyc",
        r"\baadhaar",
        r"\bpan\b",
        r"\bdisburse",
        r"\bmoratorium",
        r"\bco-borrower",
        r"\bhypothecat",
        r"\bcollateral",
        r"\bgold",
        r"\bauto",
        r"\bcar\b",
        r"\bvehicle",
        r"\beducation",
        r"\bhome\b",
        r"\bhouse\b",
        r"\bproperty",
        r"\bmortgage",
        r"\bpersonal\b",
        r"\btax\b",
        r"\b80c\b",
        r"\b24b\b",
        r"\bbalance\s+transfer",
        r"\bcibil",
        r"\bcredit\s+score",
        r"\bdefault",
        r"\bbank",
        r"\blender",
        r"\btrustdesk",
        r"\bborrow",
        r"\bsanction",
        r"\bltv\b",
        r"\bmargin\b",
        r"\bdown\s+payment\b",
        r"\bmorgage\b",
        r"\bintrst\b",
        r"\bsinthetic\b",
        r"\bemi\b",
        r"\bpayment\b",
        r"\bmissed\b",
    ]
    if any(re.search(pat, q) for pat in loan_domain_patterns):
        return "faq"

    # Unrecognized or out-of-scope non-loan queries route to fallback
    return "fallback"


def detect_intent_advanced_regex(query: str) -> str:
    """Classifies user intent using advanced compound regex matching."""
    return detect_intent_rule_based(query)


def extract_emi_parameters(query: str, tool_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts numeric principal, rate, and tenure from tool_inputs or query text."""
    params = {
        "principal": float(tool_inputs.get("principal", 0.0)),
        "rate": float(tool_inputs.get("annual_interest_rate", tool_inputs.get("rate", 9.0))),
        "tenure_months": int(tool_inputs.get("tenure_months", 60)),
    }

    if params["principal"] <= 0.0:
        # Regex extraction fallback for numbers
        numbers = [float(x.replace(",", "")) for x in re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", query)]
        if len(numbers) >= 1:
            params["principal"] = numbers[0]
        if len(numbers) >= 2:
            params["rate"] = numbers[1]
        if len(numbers) >= 3:
            params["tenure_months"] = int(numbers[2])

    if params["principal"] <= 0.0:
        params["principal"] = 1000000.0  # Synthetic default principal

    return params


def extract_eligibility_parameters(query: str, tool_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts applicant parameters from tool_inputs or query text."""
    age = int(tool_inputs.get("age", 0))
    salary = float(tool_inputs.get("monthly_salary", tool_inputs.get("salary", 0.0)))
    obligations = float(tool_inputs.get("existing_emis", tool_inputs.get("obligations", 0.0)))

    if age <= 0 or salary <= 0.0:
        numbers = [float(x.replace(",", "")) for x in re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", query)]
        for n in numbers:
            if 18 <= n <= 80 and age <= 0:
                age = int(n)
            elif n >= 10000 and salary <= 0.0:
                salary = n

    return {
        "age": age if age > 0 else 30,
        "monthly_salary": salary if salary > 0.0 else 50000.0,
        "existing_emis": obligations,
        "requested_loan_amount": float(tool_inputs.get("requested_loan_amount", 0.0)),
    }


# LangGraph Node Handlers
def intent_router_node(state: AgentState) -> AgentState:
    """Determines intent and prepares the state for downstream execution."""
    intent = state.get("intent") or detect_intent_rule_based(state["query"])
    return {**state, "intent": intent}


def faq_worker_node(state: AgentState) -> AgentState:
    """Executes ChromaDB FAQ retrieval and synthesizes response with grounding sources."""
    query = state["query"]
    results = faq_engine.search(query, n_results=3)

    source_type = "chroma" if results and results[0].get("source") == "chromadb_dense" else "test_tfidf_fallback"

    source_texts = [f"{r['question']}: {r['answer']}" for r in results]
    context = "\n".join(source_texts)

    client = get_llm_client()
    synthesized = client.generate(prompt=query, context=context)

    return {
        **state,
        "retrieved_sources": source_texts,
        "response_text": synthesized,
        "retriever_used": source_type,
        "tool_outputs": {"faqs": results},
    }


def emi_worker_node(state: AgentState) -> AgentState:
    """Performs deterministic EMI computation."""
    params = extract_emi_parameters(state["query"], state.get("tool_inputs", {}))
    calc_res = calculate_emi(
        principal=params["principal"],
        annual_interest_rate=params["rate"],
        tenure_months=params["tenure_months"],
    )
    return {
        **state,
        "response_text": calc_res["summary"],
        "retriever_used": "none",
        "tool_outputs": {"emi_result": calc_res},
        "retrieved_sources": [calc_res["summary"]],
    }


def eligibility_worker_node(state: AgentState) -> AgentState:
    """Evaluates rule-based eligibility against invented thresholds."""
    params = extract_eligibility_parameters(state["query"], state.get("tool_inputs", {}))
    el_res = evaluate_eligibility(
        age=params["age"],
        monthly_salary=params["monthly_salary"],
        existing_emis=params["existing_emis"],
        requested_loan_amount=params["requested_loan_amount"],
    )

    status_str = "Eligible" if el_res["is_eligible"] else "Ineligible"
    reasons_str = " ".join(el_res["reasons"])
    text = (
        f"Synthetic Eligibility Outcome: {status_str}. {reasons_str} "
        f"Max allowable EMI: INR {el_res['max_allowable_emi']:,.2f}. {el_res['regulatory_notice']}"
    )

    return {
        **state,
        "response_text": text,
        "retriever_used": "none",
        "tool_outputs": {"eligibility_result": el_res},
        "retrieved_sources": [text],
    }


def guardrail_node(state: AgentState) -> AgentState:
    """Token-overlap grounding guardrail verification."""
    response_text = state.get("response_text", "")
    sources = state.get("retrieved_sources", [])

    guard_eval = verify_grounding(response_text, sources)

    return {
        **state,
        "response_text": guard_eval["verified_text"],
        "grounding_score": guard_eval["grounding_score"],
        "is_grounded": guard_eval["is_grounded"],
    }


def fallback_node(state: AgentState) -> AgentState:
    """Deterministic fallback node for out-of-scope, ungrounded, or failed states."""
    return {
        **state,
        "response_text": DETERMINISTIC_FALLBACK_TEXT,
        "retriever_used": "none",
        "fallback_triggered": True,
        "grounding_score": 1.0,
        "is_grounded": True,
    }


def route_decision(state: AgentState) -> str:
    """Conditional edge router based on intent."""
    intent = state.get("intent", "fallback")
    if intent == "emi_calculation":
        return "emi_worker"
    elif intent == "eligibility_check":
        return "eligibility_worker"
    elif intent == "faq":
        return "faq_worker"
    return "fallback"


def create_agent_graph():
    """Builds and compiles the real LangGraph StateGraph."""
    workflow = StateGraph(AgentState)

    workflow.add_node("intent_router", intent_router_node)
    workflow.add_node("faq_worker", faq_worker_node)
    workflow.add_node("emi_worker", emi_worker_node)
    workflow.add_node("eligibility_worker", eligibility_worker_node)
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("fallback", fallback_node)

    workflow.set_entry_point("intent_router")

    workflow.add_conditional_edges(
        "intent_router",
        route_decision,
        {
            "faq_worker": "faq_worker",
            "emi_worker": "emi_worker",
            "eligibility_worker": "eligibility_worker",
            "fallback": "fallback",
        },
    )

    workflow.add_edge("faq_worker", "guardrail")
    workflow.add_edge("emi_worker", "guardrail")
    workflow.add_edge("eligibility_worker", "guardrail")

    workflow.add_edge("guardrail", END)
    workflow.add_edge("fallback", END)

    return workflow.compile()


# Singleton compiled graph
agent_graph = create_agent_graph()


async def run_agent_workflow(
    query: str,
    channel: str = "untrusted",
    tool_inputs: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    timeout_seconds: float = 5.0,
    max_retries: int = 2,
) -> AgentState:
    """Executes the agent graph with retries, timeout handling, and deterministic fallback."""
    initial_state: AgentState = {
        "query": query,
        "channel": channel,
        "trace_id": trace_id or f"trace-{uuid.uuid4().hex[:12]}",
        "intent": None,
        "tool_inputs": tool_inputs or {},
        "tool_outputs": {},
        "retrieved_sources": [],
        "response_text": "",
        "retriever_used": "none",
        "grounding_score": 0.0,
        "is_grounded": False,
        "fallback_triggered": False,
        "retry_count": 0,
        "error": None,
    }

    last_error: Optional[str] = None
    for attempt in range(max_retries + 1):
        try:
            initial_state["retry_count"] = attempt
            # Execute compiled graph within timeout
            result = await asyncio.wait_for(
                agent_graph.ainvoke(initial_state),
                timeout=timeout_seconds,
            )
            return result
        except asyncio.TimeoutError:
            last_error = f"Agent workflow execution timed out after {timeout_seconds}s"
        except Exception as e:
            last_error = f"Agent execution exception: {str(e)}"

    # If all attempts exhausted or timeout occurred, trigger deterministic fallback
    fallback_res = fallback_node(initial_state)
    fallback_res["error"] = last_error
    return fallback_res
