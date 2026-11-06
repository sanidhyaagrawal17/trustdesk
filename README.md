# TrustDesk

TrustDesk is a loan-FAQ conversational assistant built on synthetic data, designed to demonstrate streaming APIs, session state, auditability, PII masking, grounding, fallbacks, and honest evaluation. It is a technical demonstration on synthetic data, not a bank or credit system.

## Architectural Overview

- **Agent Routing**: Built using the real LangGraph library (`StateGraph`, `END`) with intent routing, retries, timeout handling, and deterministic fallbacks.
- **FAQ Retrieval**: Real ChromaDB collection utilizing dense semantic embeddings over 35 synthetic loan entries, with an in-memory TF-IDF fallback explicitly labelled as `test_tfidf_fallback`.
- **Channel Security**:
  - The trusted channel strictly mandates a server-validated Bearer token (`Authorization: Bearer <token>`) validated with `hmac.compare_digest` against `TRUSTED_CHANNEL_SECRET`.
  - Unauthenticated requests, spoofed headers, and requests when the secret is unset in the environment are rejected with HTTP 401.
  - The untrusted channel receives restricted tool access and stricter masking.
- **PII Masking Pipeline**:
  - Executes in strict precedence order:
    1. 13–19 digit card masking with Luhn mod-10 checksum validation (preserving invalid card numbers and loan amounts).
    2. 12-digit Indian Aadhaar UIDs.
    3. 10-digit Indian mobile numbers (`+91` and `91` prefixes included).
    4. PAN format (case-insensitive).
    5. Email addresses.
  - **Timing Invariant**: Masking executes BEFORE session storage, BEFORE audit logging, and BEFORE any model/LLM calls.
- **Input Injection Detector (Heuristic Screening)**:
  - Runs on the already-masked text before forwarding to tools or models.
  - Screens for prompt overrides, delimiter attacks, and jailbreak signatures.
  - *Heuristic Screening Notice*: The injection detector intentionally screens out queries probing internal system prompt directives. Inquisitive or testing queries asking for system prompt disclosures are intentionally refused to prioritize safety over permissive interpretation.
- **Dual-Mode Adapters**:
  - Redis session store with an in-memory dictionary fallback.
  - PostgreSQL audit logger with SQLite fallback (`audit.db`, gitignored).
  - Note: Dual-mode adapters are active in standalone environments. Redis and PostgreSQL are claimed as active systems only when live service containers pass integration tests.
- **Evaluation & Benchmarking**:
  - Intent classification on 120 synthetic queries (4 balanced classes) using scikit-learn (`TfidfVectorizer` + `LogisticRegression`).
  - Dynamically computes $N_{\text{test}}$ from the test split and benchmarks against a keyword baseline without arbitrary assertions on minimum F1.
  - 40-question golden set evaluation with split reporting: `[Eval - Mock LLM]` and `[Eval - Live LLM]`.

## Invented Synthetic Thresholds

All applicant eligibility thresholds are synthetic and invented for demonstration purposes:
- Applicant age range: 21 to 60 years.
- Minimum monthly salary: INR 25,000.
- Fixed Obligation to Income Ratio (FOIR) cutoff: 50%.

## Live Model Evaluation Guide (Ollama / Gemini)

To evaluate the golden set against a live model instead of the default zero-key `MockLLMClient`:

1. Configure environment variables (no default secrets exist in code):
   ```bash
   # For Google Gemini:
   export LIVE_LLM_PROVIDER="gemini"
   export LIVE_LLM_API_KEY="your-api-key"

   # For local Ollama:
   export LIVE_LLM_PROVIDER="ollama"
   export LIVE_LLM_API_KEY="ollama-local"
   ```
2. Execute the evaluation script:
   ```bash
   python -c "import asyncio; from backend.eval.golden_set import run_full_golden_set_evaluation; import pprint; pprint.pprint(asyncio.run(run_full_golden_set_evaluation()))"
   ```
3. Record evaluation metadata:
   - `model_runtime`: Active model provider and model version tag.
   - `timestamp`: Execution timestamp in UTC.
   - Settings: Temperature 0.0 for deterministic audit evaluation.

## Regulatory Scope & Gaps

TrustDesk is strictly **not a regulated banking system**. All financial calculations and approvals are synthetic demonstrations.

### Honest Architectural Gaps
- **gRPC**: Inter-service communication relies on REST and SSE streaming rather than high-throughput binary gRPC.
- **Kubernetes**: Container orchestration configs and Helm charts are omitted in favor of simple Docker Compose and GitHub Actions service containers.
- **Real-world Scale and Concurrency**: Tested in local and CI runtimes; not benchmarked for distributed multi-region concurrency.
- **Not a Regulated Banking System**: Does not hold banking charters, credit bureau integrations, or statutory lending authorities.
- **Voice / Multimodal**: Text and SSE token streaming only; no audio or speech recognition pipelines.
- **Node.js**: Backend is entirely implemented in Python 3.11 with FastAPI and LangGraph.
