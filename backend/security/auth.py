"""Channel security and Bearer token authentication for TrustDesk.
Enforces constant-time HMAC validation against TRUSTED_CHANNEL_SECRET for the trusted channel.
Zero default secrets in code.
Technical demonstration on synthetic data - not a regulated banking system.
"""

import hmac
import os
from typing import Optional, Tuple


def validate_channel_auth(
    channel: str,
    authorization_header: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Validates channel authorization.

    Rules:
      - Untrusted channel is permitted without authentication (subject to restricted capabilities).
      - Trusted channel strictly mandates Authorization: Bearer <token>.
      - Token is validated using hmac.compare_digest against TRUSTED_CHANNEL_SECRET.
      - Automatically rejects if TRUSTED_CHANNEL_SECRET is unset, empty, or token is invalid.
      - No secret or token has a default value in code.

    Returns:
        (is_authorized: bool, error_detail: Optional[str])
    """
    if channel != "trusted":
        return True, None

    if not authorization_header:
        return False, "Missing Authorization header for trusted channel access."

    parts = authorization_header.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False, "Malformed Authorization header. Format must be 'Bearer <token>'."

    provided_token = parts[1].strip()
    if not provided_token:
        return False, "Bearer token is empty."

    # Fetch server secret from environment without any fallback defaults
    trusted_secret = os.getenv("TRUSTED_CHANNEL_SECRET")
    if not trusted_secret or not trusted_secret.strip():
        return False, "Trusted channel secret is not configured on server."

    # Constant-time comparison to prevent timing side-channel attacks
    is_valid = hmac.compare_digest(
        provided_token.encode("utf-8"),
        trusted_secret.strip().encode("utf-8"),
    )

    if not is_valid:
        return False, "Unauthorized: Invalid Bearer token for trusted channel."

    return True, None
