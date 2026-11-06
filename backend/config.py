"""Configuration manager for TrustDesk.
Technical demonstration on synthetic data - not a regulated banking system.
"""

import os
from pathlib import Path
from typing import Any, Dict
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "features.yaml"


def load_feature_flags() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {
        "agent": {
            "max_retries": 2,
            "timeout_seconds": 5.0,
            "deterministic_fallback": True,
            "grounding_threshold": 0.35,
        },
        "tools": {
            "enable_chromadb_faq": True,
            "enable_emi_calculator": True,
            "enable_eligibility_checker": True,
            "enable_tfidf_fallback": False,
        },
        "security": {
            "strict_channel_auth": True,
            "input_injection_check": True,
            "pii_masking_enabled": True,
        },
        "synthetic_eval": {
            "default_mock_llm": True,
            "log_trace_ids": True,
        },
    }


class Settings:
    """Runtime settings loaded from environment variables and features.yaml.
    Note: No secret or token has a default value in code.
    """

    def __init__(self) -> None:
        self.features: Dict[str, Any] = load_feature_flags()
        # Explicitly no default string for secrets:
        self.trusted_channel_secret: str | None = os.getenv("TRUSTED_CHANNEL_SECRET")
        self.live_llm_provider: str | None = os.getenv("LIVE_LLM_PROVIDER")
        self.live_llm_api_key: str | None = os.getenv("LIVE_LLM_API_KEY")
        self.redis_url: str | None = os.getenv("REDIS_URL")
        self.database_url: str | None = os.getenv("DATABASE_URL")

    def get_agent_config(self) -> Dict[str, Any]:
        return self.features.get("agent", {})

    def get_tool_config(self) -> Dict[str, Any]:
        return self.features.get("tools", {})


settings = Settings()
