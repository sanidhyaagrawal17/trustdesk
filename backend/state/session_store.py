"""Dual-mode session state store for TrustDesk.
Connects to live Redis if available; gracefully falls back to an in-memory dictionary.
Timing Invariant: Stores already-masked text only.
Technical demonstration on synthetic data - not a regulated banking system.
"""

import json
import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("trustdesk.session_store")


class InMemorySessionStore:
    """Thread-safe in-memory session store fallback for standalone execution."""

    def __init__(self) -> None:
        self._store: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def save_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = []
            self._store[session_id].append(
                {
                    "role": role,
                    "content": content,
                    "timestamp": time.time(),
                }
            )

    def get_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            history = self._store.get(session_id, [])
            return list(history[-limit:])

    def clear(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._store:
                del self._store[session_id]

    @property
    def is_live(self) -> bool:
        return False


class RedisSessionStore:
    """Live Redis session store for distributed containerized execution."""

    def __init__(self, redis_url: str) -> None:
        import redis

        self.client = redis.from_url(redis_url, decode_responses=True, socket_timeout=2.0)
        # Test connection immediately
        self.client.ping()

    def _key(self, session_id: str) -> str:
        return f"trustdesk:session:{session_id}"

    def save_message(self, session_id: str, role: str, content: str, ttl_seconds: int = 86400) -> None:
        payload = json.dumps(
            {
                "role": role,
                "content": content,
                "timestamp": time.time(),
            }
        )
        key = self._key(session_id)
        self.client.rpush(key, payload)
        self.client.expire(key, ttl_seconds)

    def get_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        key = self._key(session_id)
        raw_items = self.client.lrange(key, -limit, -1)
        return [json.loads(item) for item in raw_items]

    def clear(self, session_id: str) -> None:
        self.client.delete(self._key(session_id))

    @property
    def is_live(self) -> bool:
        return True


class DualModeSessionStore:
    """Manages session history, adapting between Redis and in-memory store."""

    def __init__(self, redis_url: Optional[str] = None) -> None:
        url = redis_url or os.getenv("REDIS_URL")
        self._backend_type = "in_memory"
        self._adapter: InMemorySessionStore | RedisSessionStore

        if url:
            try:
                self._adapter = RedisSessionStore(url)
                self._backend_type = "redis"
            except Exception as exc:
                if os.getenv("REQUIRE_INTEGRATION") == "1":
                    raise exc
                logger.warning("Redis connection failed (%s); falling back to in-memory session store.", exc)
                self._adapter = InMemorySessionStore()
                self._backend_type = "in_memory"
        else:
            self._adapter = InMemorySessionStore()
            self._backend_type = "in_memory"

    @property
    def backend_type(self) -> str:
        return self._backend_type

    def save_message(self, session_id: str, role: str, masked_content: str) -> None:
        """Saves message to session store. Content must already be PII-masked."""
        self._adapter.save_message(session_id, role, masked_content)

    def get_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        return self._adapter.get_history(session_id, limit=limit)

    def clear(self, session_id: str) -> None:
        self._adapter.clear(session_id)


# Global default session store instance
session_store = DualModeSessionStore()
