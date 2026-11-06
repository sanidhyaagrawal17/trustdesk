"""Token-overlap grounding guardrail for TrustDesk.
Checks whether synthesized claims are grounded in retrieved synthetic FAQ sources.
Technical demonstration on synthetic data - not a regulated banking system.
"""

import re
from typing import Any, Dict, List, Set

STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "did", "do", "does", "doing", "don", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
    "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same", "she", "should",
    "so", "some", "such", "t", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "you", "your", "yours", "yourself", "yourselves", "based", "synthetic"
}


def tokenize(text: str) -> Set[str]:
    """Tokenize and filter stopwords to extract key semantic tokens."""
    tokens = re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text.lower())
    return {t for t in tokens if t not in STOPWORDS}


def calculate_grounding_score(response_text: str, source_texts: List[str]) -> float:
    """Calculates token-overlap grounding score between response and retrieved source texts.
    Returns a score between 0.0 and 1.0.
    """
    if not source_texts:
        return 0.0

    response_tokens = tokenize(response_text)
    if not response_tokens:
        return 1.0  # Trivial or empty response

    combined_source_tokens: Set[str] = set()
    for src in source_texts:
        combined_source_tokens.update(tokenize(src))

    if not combined_source_tokens:
        return 0.0

    overlap = response_tokens.intersection(combined_source_tokens)
    return len(overlap) / len(response_tokens)


def verify_grounding(
    response_text: str,
    source_texts: List[str],
    threshold: float = 0.35,
) -> Dict[str, Any]:
    """Evaluates grounding and returns verification metadata."""
    score = calculate_grounding_score(response_text, source_texts)
    is_grounded = score >= threshold

    disclaimer = ""
    if not is_grounded:
        disclaimer = (
            "\n\n[Grounding Advisory]: This response could not be verified against "
            "synthetic reference documentation (grounding score: " f"{score:.2f} < {threshold:.2f})."
        )

    return {
        "grounding_score": round(score, 4),
        "is_grounded": is_grounded,
        "threshold": threshold,
        "advisory": disclaimer,
        "verified_text": response_text + disclaimer if not is_grounded else response_text,
    }
