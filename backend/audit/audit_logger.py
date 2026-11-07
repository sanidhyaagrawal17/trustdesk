"""Dual-mode audit logger for TrustDesk.
Connects to live PostgreSQL if configured; gracefully falls back to SQLite (audit.db).
Timing Invariant: Logs already-masked text only.
Technical demonstration on synthetic data - not a regulated banking system.
"""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    select,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_SQLITE_URL = f"sqlite:///{BASE_DIR / 'audit.db'}"

metadata = MetaData()

audit_table = Table(
    "audit_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("trace_id", String(64), index=True, nullable=False),
    Column("timestamp", Float, nullable=False),
    Column("channel", String(32), nullable=False),
    Column("masked_query", Text, nullable=False),
    Column("intent", String(64), nullable=True),
    Column("retriever_used", String(64), nullable=True),
    Column("grounding_score", Float, default=0.0),
    Column("is_grounded", Boolean, default=False),
    Column("injection_detected", Boolean, default=False),
    Column("response_summary", Text, nullable=True),
    Column("latency_ms", Float, default=0.0),
)


class DualModeAuditLogger:
    """Audit logger implementing dual-mode persistence (PostgreSQL with SQLite fallback)."""

    def __init__(self, db_url: Optional[str] = None) -> None:
        url = db_url or os.getenv("DATABASE_URL")
        self._backend_type = "sqlite"

        if url and ("postgres" in url or "postgresql" in url):
            try:
                self.engine = create_engine(url, pool_pre_ping=True)
                with self.engine.connect() as conn:
                    metadata.create_all(self.engine)
                self._backend_type = "postgresql"
            except Exception as exc:
                if os.getenv("REQUIRE_INTEGRATION") == "1":
                    raise exc
                self.engine = create_engine(DEFAULT_SQLITE_URL, connect_args={"check_same_thread": False})
                metadata.create_all(self.engine)
                self._backend_type = "sqlite"
        else:
            self.engine = create_engine(DEFAULT_SQLITE_URL, connect_args={"check_same_thread": False})
            metadata.create_all(self.engine)
            self._backend_type = "sqlite"

    @property
    def backend_type(self) -> str:
        return self._backend_type

    def log_event(
        self,
        trace_id: str,
        channel: str,
        masked_query: str,
        intent: Optional[str] = None,
        retriever_used: Optional[str] = None,
        grounding_score: float = 0.0,
        is_grounded: bool = False,
        injection_detected: bool = False,
        response_summary: Optional[str] = None,
        latency_ms: float = 0.0,
    ) -> None:
        """Persists audit record. Query MUST already be PII-masked."""
        with self.engine.begin() as conn:
            stmt = audit_table.insert().values(
                trace_id=trace_id,
                timestamp=time.time(),
                channel=channel,
                masked_query=masked_query,
                intent=intent or "unknown",
                retriever_used=retriever_used or "none",
                grounding_score=round(grounding_score, 4),
                is_grounded=is_grounded,
                injection_detected=injection_detected,
                response_summary=response_summary or "",
                latency_ms=round(latency_ms, 2),
            )
            conn.execute(stmt)

    def get_log_by_trace_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        with self.engine.connect() as conn:
            stmt = select(audit_table).where(audit_table.c.trace_id == trace_id)
            row = conn.execute(stmt).fetchone()
            if not row:
                return None
            return dict(row._mapping)

    def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            stmt = select(audit_table).order_by(audit_table.c.id.desc()).limit(limit)
            rows = conn.execute(stmt).fetchall()
            return [dict(r._mapping) for r in rows]


# Global default audit logger
audit_logger = DualModeAuditLogger()
