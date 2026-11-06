"""LLM client interface supporting configurable mock execution and live providers.
Technical demonstration on synthetic data - not a regulated banking system.
Zero external API keys required for default operation.
"""

import os
import time
from typing import Any, AsyncGenerator, Dict, List, Optional


class MockLLMClient:
    """Configurable mock LLM client for zero-key testing and deterministic evaluation."""

    def __init__(
        self,
        default_response: Optional[str] = None,
        latency_seconds: float = 0.0,
        should_timeout: bool = False,
        should_fail: bool = False,
    ) -> None:
        self.default_response = default_response
        self.latency_seconds = latency_seconds
        self.should_timeout = should_timeout
        self.should_fail = should_fail
        self.call_history: List[Dict[str, Any]] = []

    def generate(self, prompt: str, context: Optional[str] = None) -> str:
        self.call_history.append({"prompt": prompt, "context": context})

        if self.should_fail:
            raise RuntimeError("Simulated MockLLMClient failure")

        if self.should_timeout:
            time.sleep(self.latency_seconds if self.latency_seconds > 0 else 0.5)
            raise TimeoutError("Simulated MockLLMClient timeout")

        if self.latency_seconds > 0:
            time.sleep(self.latency_seconds)

        if self.default_response is not None:
            return self.default_response

        # Context-grounded synthesis fallback
        if context:
            return f"Based on synthetic loan documentation: {context.strip()}"
        return "Synthetic response for query: " + prompt.strip()

    async def astream(
        self, prompt: str, context: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        full_text = self.generate(prompt, context)
        words = full_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")


class LiveLLMClient:
    """Live LLM client (Gemini / Ollama / OpenAI) active only if configured via environment.
    Note: No hardcoded API keys or default secret tokens.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        self.provider = provider or os.getenv("LIVE_LLM_PROVIDER", "mock")
        self.api_key = api_key or os.getenv("LIVE_LLM_API_KEY")
        self.model_name = model_name or "gemini-2.5-flash"

    def generate(self, prompt: str, context: Optional[str] = None) -> str:
        if self.provider == "mock" or not self.api_key:
            return MockLLMClient().generate(prompt, context)
        # Placeholder for external live provider integration
        return f"[Live LLM: {self.provider}] Synthetic grounded response to: {prompt}"


_default_mock_client = MockLLMClient()


def get_llm_client(force_mock: bool = True, fresh: bool = False) -> MockLLMClient | LiveLLMClient:
    """Factory function for acquiring the configured LLM client."""
    provider = os.getenv("LIVE_LLM_PROVIDER")
    if force_mock or not provider or provider.lower() == "mock":
        if fresh:
            return MockLLMClient()
        return _default_mock_client
    return LiveLLMClient(provider=provider, api_key=os.getenv("LIVE_LLM_API_KEY"))
