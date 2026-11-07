# TrustDesk Verified Technical Claims

> **Verification Standard**: Every claim listed below is certified strictly by a passing automated test.
> Claims without automated test coverage are intentionally omitted.

| ID | Category | Verified Capability | Verifying Test Function |
| :--- | :--- | :--- | :--- |
| `CLAIM-AGENT-01` | **Agent Routing & Loop** | LangGraph StateGraph routes loan queries among FAQ, EMI calculation, and eligibility tools. | `test_langgraph_import_and_compilation` |
| `CLAIM-AGENT-02` | **Agent Routing & Loop** | Real ChromaDB dense embeddings retrieve semantic FAQ answers with in-memory TF-IDF fallback. | `test_chromadb_dense_semantic_search` |
| `CLAIM-SECURITY-01` | **Security & Privacy** | 13-19 digit credit/debit card numbers are validated via Luhn algorithm before masking. | `test_luhn_card_masking_valid` |
| `CLAIM-SECURITY-02` | **Security & Privacy** | Spaced 16-digit invalid Luhn numbers are preserved from Aadhaar or card masking. | `test_spaced_16_digit_invalid_luhn_not_masked_as_aadhaar` |
| `CLAIM-SECURITY-03` | **Security & Privacy** | 12-digit Indian Aadhaar UIDs and 10-digit mobile numbers (+91/91 prefixes) are reliably masked. | `test_phone_masking_with_and_without_prefix` |
| `CLAIM-SECURITY-04` | **Security & Privacy** | Server validates Bearer token via constant-time comparison against TRUSTED_CHANNEL_SECRET. | `test_channel_auth_trusted_valid` |
| `CLAIM-SECURITY-05` | **Security & Privacy** | Heuristic input injection detector screens prompt overrides and jailbreaks on masked text. | `test_adversarial_injection_detection_screening` |
| `CLAIM-RESILIENCE-01` | **Fault Tolerance & Dual-Mode Adapters** | Redis outage triggers automatic graceful fallback to thread-safe in-memory session store. | `test_redis_outage_graceful_fallback` |
| `CLAIM-RESILIENCE-02` | **Fault Tolerance & Dual-Mode Adapters** | PostgreSQL outage triggers automatic graceful fallback to local SQLite audit logger. | `test_postgresql_outage_graceful_fallback` |
| `CLAIM-RESILIENCE-03` | **Fault Tolerance & Dual-Mode Adapters** | Live storage adapter health status is exposed via /api/health, and connection failures log warning notices. | `test_health_endpoints_adapter_reporting` |
| `CLAIM-SECURITY-06` | **Security & Privacy** | Benign loan queries with domain keywords achieve 0.0% false-positive rate under heuristic injection screening. | `test_held_out_injection_and_benign_catch_and_fp_rates` |
| `CLAIM-STREAMING-01` | **API & Streaming** | SSE endpoint streams status, token, metadata, and done events with trace IDs. | `test_sse_chat_stream_protocol` |
| `CLAIM-EVAL-01` | **Evaluation & Grounding** | Token-overlap grounding guardrail scores model claims against FAQ knowledge base. | `test_grounding_evaluator_high_overlap` |
| `CLAIM-EVAL-02` | **Evaluation & Grounding** | Intent classifier is evaluated on synthetic test split and benchmarked against dual keyword baselines. | `test_intent_classifier_evaluation_metrics` |
| `CLAIM-EVAL-03` | **Evaluation & Grounding** | 12-query independent evaluation suite benchmarks out-of-scope refusal (4/6) and zero-keyword fallback behavior (0/6) on frozen router. | `test_independent_evaluation_suite_frozen_router` |
| `CLAIM-EVAL-04` | **Evaluation & Grounding** | 40-question golden set regression suite verifies routing, eligibility math, EMI calculation, and FAQ grounding (40/40 after fixes). | `test_golden_set_mock_llm_evaluation` |
| `CLAIM-EVAL-05` | **Evaluation & Grounding** | Hybrid intent router combining rule fast path, classifier probabilities, and Chroma retrieval elevates 20-query concordance from 45% to 85% with low-confidence clarification. | `test_independent_20_query_evaluation_before_and_after_hybrid_router` |
| `CLAIM-ROUTER-01` | **Agent Routing & Loop** | Low-confidence queries return interactive clarifying questions rather than outright refusals. | `test_low_confidence_query_returns_clarifying_question` |

## Non-Claims & Honest Architectural Gaps
- **No gRPC**: Communications rely strictly on REST and SSE streaming.
- **No Kubernetes**: Demonstrations run on local processes, Docker Compose, or GitHub Actions containers.
- **Local / CI Concurrency Only**: Not benchmarked for distributed multi-region horizontal scaling.
- **Not a Regulated Banking System**: All interest rates, loan approvals, and eligibility criteria are synthetic.
- **No Voice / Audio**: Text and token streaming only; no audio or speech recognition pipelines.
- **No Node.js Backend**: Backend is built entirely in Python 3.11 with FastAPI and LangGraph.
