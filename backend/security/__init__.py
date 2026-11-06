"""Security package for TrustDesk.
Includes PII masking, input injection detection, and channel authentication.
Technical demonstration on synthetic data - not a regulated banking system.
"""

from backend.security.auth import validate_channel_auth
from backend.security.injection_detector import detect_injection
from backend.security.pii_masker import is_luhn_valid, mask_pii

__all__ = ["validate_channel_auth", "detect_injection", "mask_pii", "is_luhn_valid"]
