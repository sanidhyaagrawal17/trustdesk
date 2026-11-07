"""Input injection and prompt override detection module for TrustDesk.
Runs on the already-masked input text to detect prompt overrides, delimiter attacks,
and jailbreak signatures before forwarding to tools or models.
Technical demonstration on synthetic data - not a regulated banking system.
"""

import re
from typing import Any, Dict

PROMPT_OVERRIDE_PATTERNS = [
    r"(?:ignore|disregard|forget)\s+(?:all\s+)?(?:previous|prior)?\s*(?:instructions|rules|commands|prompts|constraints)",
    r"override\s+(?:system|core|all)\s+(?:prompts?|instructions?|rules?)",
    r"system\s+override",
    r"system\s*prompt\s*:",
    r"new\s*instructions\s*:",
    r"forget\s+(?:everything|all\s+instructions|your\s+role)",
]

DELIMITER_ATTACK_PATTERNS = [
    r"<\s*system\s*>",
    r"<\s*/\s*system\s*>",
    r"\[\s*(?:SYSTEM|ADMIN|DEVELOPER)(?:_MODE)?\s*\]",
    r"\[\s*/\s*(?:SYSTEM|ADMIN|DEVELOPER)(?:_MODE)?\s*\]",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r'"""\s*(?:system|assistant|instruction)',
    r"'''\s*(?:system|assistant|instruction)",
    r"(?:\n\n|\b)(?:Human|Assistant|AI):\s*",
]

JAILBREAK_PATTERNS = [
    r"\bDAN\s+mode\b",
    r"\bjailbreak\b",
    r"\bdo\s+anything\s+now\b",
    r"\bunrestricted\s+(?:developer\s+mode|terminal|agent|assistant)\b",
    r"\b(?:admin|developer)\s+debug\s+mode\b",
    r"\bbypass\s+(?:all\s+)?(?:safety|guardrails|filters|rules|pii(?:\s+masking)?)\b",
    r"\bact\s+as\s+an\s+unfiltered\b",
]

INJECTION_REFUSAL_MESSAGE = (
    "Security Refusal: Input injection or prompt override signature detected. "
    "The synthetic assistant cannot fulfill this request."
)


def detect_injection(masked_text: str) -> Dict[str, Any]:
    """Scans already-masked input text for security injection vectors.

    Returns:
        Dict with is_injection (bool), risk_category (str), matched_pattern (str),
        and refusal_message (str).
    """
    # 1. Prompt override checks
    for pat in PROMPT_OVERRIDE_PATTERNS:
        match = re.search(pat, masked_text, re.IGNORECASE)
        if match:
            return {
                "is_injection": True,
                "risk_category": "prompt_override",
                "matched_pattern": match.group(0),
                "refusal_message": INJECTION_REFUSAL_MESSAGE,
            }

    # 2. Delimiter attack checks
    for pat in DELIMITER_ATTACK_PATTERNS:
        match = re.search(pat, masked_text, re.IGNORECASE)
        if match:
            return {
                "is_injection": True,
                "risk_category": "delimiter_attack",
                "matched_pattern": match.group(0),
                "refusal_message": INJECTION_REFUSAL_MESSAGE,
            }

    # 3. Jailbreak signature checks
    for pat in JAILBREAK_PATTERNS:
        match = re.search(pat, masked_text, re.IGNORECASE)
        if match:
            return {
                "is_injection": True,
                "risk_category": "jailbreak_signature",
                "matched_pattern": match.group(0),
                "refusal_message": INJECTION_REFUSAL_MESSAGE,
            }

    return {
        "is_injection": False,
        "risk_category": "none",
        "matched_pattern": "",
        "refusal_message": "",
    }
