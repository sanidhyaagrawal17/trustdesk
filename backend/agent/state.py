"""State definitions for LangGraph agent workflow.
Technical demonstration on synthetic data - not a regulated banking system.
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """LangGraph agent state dictionary."""

    query: str
    channel: str  # "trusted" or "untrusted"
    trace_id: str
    intent: Optional[str]  # "faq", "emi_calculation", "eligibility_check", "fallback"
    tool_inputs: Dict[str, Any]
    tool_outputs: Dict[str, Any]
    retrieved_sources: List[str]
    response_text: str
    retriever_used: str  # "chroma", "test_tfidf_fallback", or "none"
    grounding_score: float
    is_grounded: bool
    fallback_triggered: bool
    retry_count: int
    error: Optional[str]
