"""Structured JSON logging configuration for TrustDesk.
Outputs JSON logs with trace_id, timestamps, and contextual metadata.
Technical demonstration on synthetic data - not a regulated banking system.
"""

import json
import logging
import time
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Custom formatter emitting structured JSON records."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include custom extra fields if provided
        for key, val in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                "message", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName"
            ):
                log_payload[key] = val

        return json.dumps(log_payload)


def configure_structured_logging(level: int = logging.INFO) -> logging.Logger:
    """Configures root or app logger with structured JSON handler."""
    logger = logging.getLogger("trustdesk")
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger


structured_logger = configure_structured_logging()
