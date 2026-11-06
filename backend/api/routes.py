"""FastAPI routes for TrustDesk.
Provides SSE streaming endpoint (/api/chat/stream), /api/metrics, and /health.
Enforces channel auth, PII masking precedence, injection detection, and dual-mode audit logging.
Technical demonstration on synthetic data - not a regulated banking system.
"""

import asyncio
import json
import time
import uuid
from typing import Any, AsyncGenerator, Dict, Optional
from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from backend.agent.graph import run_agent_workflow
from backend.audit.audit_logger import audit_logger
from backend.config import settings
from backend.core.metrics import metrics_collector
from backend.security.auth import validate_channel_auth
from backend.security.injection_detector import detect_injection
from backend.security.pii_masker import mask_pii
from backend.state.session_store import session_store

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User query text")
    channel: str = Field("untrusted", description="Client channel: trusted or untrusted")
    session_id: Optional[str] = Field(None, description="Optional session identifier")
    tool_inputs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Pre-parsed tool parameters")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """System status and synthetic mode disclosure."""
    return {
        "status": "healthy",
        "service": "TrustDesk",
        "environment": "synthetic_demonstration",
        "regulatory_notice": "TrustDesk is a technical demonstration on synthetic data, not a regulated banking system.",
        "storage_adapters": {
            "session_store": session_store.backend_type,
            "audit_logger": audit_logger.backend_type,
        },
        "features": settings.features,
    }


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Exposes runtime counters for requests, channels, PII masking, and injection attempts."""
    return {
        "metrics": metrics_collector.get_metrics(),
        "storage_adapters": {
            "session_store": session_store.backend_type,
            "audit_logger": audit_logger.backend_type,
        },
    }


@router.get("/audit/{trace_id}")
async def get_audit_entry(trace_id: str) -> Dict[str, Any]:
    """Retrieves audit entry by trace ID for verification and audits."""
    entry = audit_logger.get_log_by_trace_id(trace_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Trace ID not found in audit logs.")
    return entry


async def chat_event_generator(
    raw_message: str,
    channel: str,
    session_id: Optional[str] = None,
    tool_inputs: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Asynchronous generator streaming SSE events for the chat request."""
    start_time = time.time()
    current_trace_id = trace_id or f"trace-{uuid.uuid4().hex[:12]}"

    metrics_collector.record_request(channel)

    # 1. PII Masking: strictly executed BEFORE session storage, audit logs, and LLM calls
    masked_query, pii_stats = mask_pii(raw_message, channel=channel)
    metrics_collector.record_pii_stats(pii_stats)

    # 2. Session state persistence: store masked user message
    if session_id:
        session_store.save_message(session_id, "user", masked_query)

    # Event 1: Initial acknowledgment & routing status
    yield {
        "event": "status",
        "data": json.dumps({
            "status": "processing",
            "trace_id": current_trace_id,
            "channel": channel,
            "pii_masked": any(v > 0 for v in pii_stats.values()),
        }),
    }
    await asyncio.sleep(0.01)

    # 3. Input injection detection: evaluated on the already-masked text
    injection_eval = detect_injection(masked_query)
    if injection_eval["is_injection"]:
        metrics_collector.record_injection()
        metrics_collector.record_intent("injection_refusal")
        elapsed_ms = (time.time() - start_time) * 1000.0
        metrics_collector.record_latency(elapsed_ms)

        refusal_text = injection_eval["refusal_message"]

        # Audit log injection attempt with masked query
        audit_logger.log_event(
            trace_id=current_trace_id,
            channel=channel,
            masked_query=masked_query,
            intent="injection_refusal",
            retriever_used="none",
            grounding_score=1.0,
            is_grounded=True,
            injection_detected=True,
            response_summary=refusal_text,
            latency_ms=elapsed_ms,
        )

        if session_id:
            session_store.save_message(session_id, "assistant", refusal_text)

        # Stream refusal tokens
        for token in refusal_text.split(" "):
            yield {
                "event": "token",
                "data": json.dumps({"token": token + " ", "trace_id": current_trace_id}),
            }
            await asyncio.sleep(0.01)

        yield {
            "event": "metadata",
            "data": json.dumps({
                "trace_id": current_trace_id,
                "intent": "injection_refusal",
                "grounding_score": 1.0,
                "is_grounded": True,
                "fallback_triggered": True,
                "injection_detected": True,
                "retriever_used": "none",
                "channel": channel,
            }),
        }

        yield {
            "event": "done",
            "data": json.dumps({"status": "complete", "trace_id": current_trace_id}),
        }
        return

    # 4. Agent Graph Execution: passing already-masked query
    result = await run_agent_workflow(
        query=masked_query,
        channel=channel,
        tool_inputs=tool_inputs,
        trace_id=current_trace_id,
        timeout_seconds=settings.get_agent_config().get("timeout_seconds", 5.0),
        max_retries=settings.get_agent_config().get("max_retries", 2),
    )

    elapsed_ms = (time.time() - start_time) * 1000.0
    metrics_collector.record_latency(elapsed_ms)
    metrics_collector.record_intent(result.get("intent", "unknown"))

    response_text = result.get("response_text", "")

    # 5. Audit Logging: persistent record with trace_id and masked_query
    audit_logger.log_event(
        trace_id=current_trace_id,
        channel=channel,
        masked_query=masked_query,
        intent=result.get("intent"),
        retriever_used=result.get("retriever_used", "none"),
        grounding_score=result.get("grounding_score", 0.0),
        is_grounded=result.get("is_grounded", False),
        injection_detected=False,
        response_summary=response_text[:300],
        latency_ms=elapsed_ms,
    )

    # 6. Session state persistence: store assistant response
    if session_id:
        session_store.save_message(session_id, "assistant", response_text)

    # Event 2: Stream tokens incrementally
    tokens = response_text.split(" ")
    for idx, token in enumerate(tokens):
        chunk = token + (" " if idx < len(tokens) - 1 else "")
        yield {
            "event": "token",
            "data": json.dumps({"token": chunk, "trace_id": current_trace_id}),
        }
        await asyncio.sleep(0.01)

    # Event 3: Metadata (grounding, intent, retriever, channel)
    yield {
        "event": "metadata",
        "data": json.dumps({
            "trace_id": current_trace_id,
            "intent": result.get("intent"),
            "grounding_score": result.get("grounding_score", 0.0),
            "is_grounded": result.get("is_grounded", False),
            "fallback_triggered": result.get("fallback_triggered", False),
            "retriever_used": result.get("retriever_used", "none"),
            "channel": channel,
        }),
    }

    # Event 4: Completion event
    yield {
        "event": "done",
        "data": json.dumps({"status": "complete", "trace_id": current_trace_id}),
    }


@router.post("/chat/stream")
async def chat_stream_post(
    request: Request,
    body: ChatRequest,
    authorization: Optional[str] = Header(None),
) -> EventSourceResponse:
    """SSE streaming chat endpoint (POST). Enforces channel Bearer token auth."""
    # Enforce channel authorization
    is_authorized, error_msg = validate_channel_auth(
        channel=body.channel,
        authorization_header=authorization,
    )
    if not is_authorized:
        raise HTTPException(status_code=401, detail=error_msg)

    return EventSourceResponse(
        chat_event_generator(
            raw_message=body.message,
            channel=body.channel,
            session_id=body.session_id,
            tool_inputs=body.tool_inputs,
        )
    )


@router.get("/chat/stream")
async def chat_stream_get(
    request: Request,
    message: str = Query(..., description="User query text"),
    channel: str = Query("untrusted", description="Client channel"),
    session_id: Optional[str] = Query(None, description="Optional session identifier"),
    authorization: Optional[str] = Header(None),
) -> EventSourceResponse:
    """SSE streaming chat endpoint (GET fallback). Enforces channel Bearer token auth."""
    is_authorized, error_msg = validate_channel_auth(
        channel=channel,
        authorization_header=authorization,
    )
    if not is_authorized:
        raise HTTPException(status_code=401, detail=error_msg)

    return EventSourceResponse(
        chat_event_generator(
            raw_message=message,
            channel=channel,
            session_id=session_id,
        )
    )
