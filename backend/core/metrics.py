"""Runtime metrics collector for TrustDesk.
Provides counters for total requests, channels, intents, injection attempts, and PII masking.
Technical demonstration on synthetic data - not a regulated banking system.
"""

import threading
from typing import Any, Dict, List


class MetricsCollector:
    """Thread-safe runtime performance and security metrics collector."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.total_requests = 0
        self.requests_by_channel = {"trusted": 0, "untrusted": 0}
        self.intents_classified: Dict[str, int] = {}
        self.injection_attempts = 0
        self.pii_masked_count = {
            "card": 0,
            "aadhaar": 0,
            "phone": 0,
            "pan": 0,
            "email": 0,
        }
        self.latencies_ms: List[float] = []

    def record_request(self, channel: str) -> None:
        with self._lock:
            self.total_requests += 1
            if channel in self.requests_by_channel:
                self.requests_by_channel[channel] += 1
            else:
                self.requests_by_channel[channel] = 1

    def record_intent(self, intent: str) -> None:
        with self._lock:
            self.intents_classified[intent] = self.intents_classified.get(intent, 0) + 1

    def record_injection(self) -> None:
        with self._lock:
            self.injection_attempts += 1

    def record_pii_stats(self, stats: Dict[str, int]) -> None:
        with self._lock:
            for k, count in stats.items():
                if k in self.pii_masked_count:
                    self.pii_masked_count[k] += count
                else:
                    self.pii_masked_count[k] = count

    def record_latency(self, latency_ms: float) -> None:
        with self._lock:
            self.latencies_ms.append(latency_ms)
            if len(self.latencies_ms) > 1000:
                self.latencies_ms = self.latencies_ms[-1000:]

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            avg_latency = (
                sum(self.latencies_ms) / len(self.latencies_ms)
                if self.latencies_ms
                else 0.0
            )
            return {
                "total_requests": self.total_requests,
                "requests_by_channel": dict(self.requests_by_channel),
                "intents_classified": dict(self.intents_classified),
                "injection_attempts": self.injection_attempts,
                "pii_masked_count": dict(self.pii_masked_count),
                "average_latency_ms": round(avg_latency, 2),
            }

    def reset(self) -> None:
        with self._lock:
            self.total_requests = 0
            self.requests_by_channel = {"trusted": 0, "untrusted": 0}
            self.intents_classified = {}
            self.injection_attempts = 0
            self.pii_masked_count = {
                "card": 0,
                "aadhaar": 0,
                "phone": 0,
                "pan": 0,
                "email": 0,
            }
            self.latencies_ms = []


metrics_collector = MetricsCollector()
