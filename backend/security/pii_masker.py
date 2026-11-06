"""PII Masking Pipeline for TrustDesk.
Executes strict precedence:
  Step 1: 13-19 digit card masking using the Luhn algorithm (preserving invalid numbers and loan amounts).
  Step 2: 12-digit Indian Aadhaar UIDs.
  Step 3: Indian 10-digit mobile numbers.
  Step 4: PAN (5 letters, 4 digits, 1 letter).
  Step 5: Email addresses.
Timing Invariant: Must execute BEFORE session storage, BEFORE audit logging, and BEFORE any model/LLM calls.
Technical demonstration on synthetic data - not a regulated banking system.
"""

import re
from typing import Dict, Tuple


def is_luhn_valid(number_str: str) -> bool:
    """Validates whether a digit sequence satisfies the Luhn mod-10 checksum."""
    digits = [int(c) for c in number_str if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False

    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += (doubled - 9) if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0


def mask_cards_luhn(text: str) -> Tuple[str, int]:
    """Step 1: Finds 13-19 digit sequences and masks strictly if Luhn checksum is valid."""
    # Matches digit sequences with optional space or hyphen delimiters
    pattern = re.compile(r"\b(?:\d[ -]?){13,19}\b")
    count = 0

    def replace_if_luhn(match: re.Match) -> str:
        nonlocal count
        raw = match.group(0)
        digits_only = re.sub(r"[^\d]", "", raw)
        if 13 <= len(digits_only) <= 19 and is_luhn_valid(digits_only):
            count += 1
            return "[CARD_MASKED]"
        return raw

    masked_text = pattern.sub(replace_if_luhn, text)
    return masked_text, count


def mask_aadhaar(text: str) -> Tuple[str, int]:
    """Step 2: Masks 12-digit Indian Aadhaar UIDs.
    Ensures 16-digit spaced sequences (such as invalid cards) are NOT partially matched.
    """
    pattern = re.compile(
        r"(?<!\d{4}[\s\-])(?<!\d)\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b(?![\s\-]?\d{4})(?![\s\-]?\d)"
    )
    matches = list(pattern.finditer(text))
    count = len(matches)
    masked_text = pattern.sub("[AADHAAR_MASKED]", text)
    return masked_text, count


def mask_phone_numbers(text: str) -> Tuple[str, int]:
    """Step 3: Masks Indian 10-digit mobile numbers with optional +91 or 91 prefix.
    Ensures no prefix digits or trailing digits are left exposed.
    """
    pattern = re.compile(r"(?:\+?91[\-\s]?)?[6-9]\d{9}\b")
    matches = list(pattern.finditer(text))
    count = len(matches)
    masked_text = pattern.sub("[PHONE_MASKED]", text)
    return masked_text, count


def mask_pan(text: str) -> Tuple[str, int]:
    """Step 4: Masks Indian PAN (5 letters, 4 digits, 1 letter) in both uppercase and lowercase."""
    pattern = re.compile(r"\b[A-Za-z]{5}[0-9]{4}[A-Za-z]\b")
    matches = list(pattern.finditer(text))
    count = len(matches)
    masked_text = pattern.sub("[PAN_MASKED]", text)
    return masked_text, count


def mask_emails(text: str) -> Tuple[str, int]:
    """Step 5: Masks email addresses."""
    pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    matches = list(pattern.finditer(text))
    count = len(matches)
    masked_text = pattern.sub("[EMAIL_MASKED]", text)
    return masked_text, count


def mask_pii(text: str, channel: str = "untrusted") -> Tuple[str, Dict[str, int]]:
    """Runs the full 5-step PII masking pipeline in strict precedence order.

    Timing Invariant: Executed BEFORE session storage, BEFORE audit logging,
    and BEFORE any model/LLM calls.
    """
    stats: Dict[str, int] = {
        "card": 0,
        "aadhaar": 0,
        "phone": 0,
        "pan": 0,
        "email": 0,
    }

    # Step 1: Luhn Card Masking
    current_text, stats["card"] = mask_cards_luhn(text)

    # Step 2: Aadhaar 12-digit UIDs
    current_text, stats["aadhaar"] = mask_aadhaar(current_text)

    # Step 3: Indian Phone numbers
    current_text, stats["phone"] = mask_phone_numbers(current_text)

    # Step 4: PAN Card
    current_text, stats["pan"] = mask_pan(current_text)

    # Step 5: Email addresses
    current_text, stats["email"] = mask_emails(current_text)

    return current_text, stats
