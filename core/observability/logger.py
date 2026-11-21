"""
Structured JSON Logger with Correlation ID Tracking and Sensitive Data Scrubbing.
Outputs high-performance JSON lines suitable for stdout, file rotation, and log collectors (Loki/Elasticsearch).
"""
import contextvars
from datetime import datetime, timezone
import json
import logging
import os
import sys
from typing import Any, Dict, Optional
from uuid import uuid4

from core.security import SecretScrubber

_correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")
_project_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("project_id", default="")

def get_correlation_id() -> str:
    val = _correlation_id_ctx.get()
    if not val:
        val = str(uuid4())
        _correlation_id_ctx.set(val)
    return val

def set_correlation_id(cid: str) -> None:
    _correlation_id_ctx.set(cid)

def set_project_id(pid: str) -> None:
    _project_id_ctx.set(pid)

class correlation_context:
    """Context manager for scoping correlation and project IDs across async tasks."""
    def __init__(self, correlation_id: Optional[str] = None, project_id: Optional[str] = None):
        self.cid = correlation_id or str(uuid4())
        self.pid = project_id or ""
        self.token_cid = None
        self.token_pid = None

    def __enter__(self):
        self.token_cid = _correlation_id_ctx.set(self.cid)
        if self.pid:
            self.token_pid = _project_id_ctx.set(self.pid)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token_cid:
            _correlation_id_ctx.reset(self.token_cid)
        if self.token_pid:
            _project_id_ctx.reset(self.token_pid)


class JSONFormatter(logging.Formatter):
    """Formats standard python logging records into scrubbed JSON lines."""
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": SecretScrubber.scrub_text(record.getMessage()),
            "correlation_id": _correlation_id_ctx.get() or "none",
        }

        pid = _project_id_ctx.get()
        if pid:
            log_entry["project_id"] = pid

        if hasattr(record, "department"):
            log_entry["department"] = getattr(record, "department")

        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = getattr(record, "duration_ms")

        if hasattr(record, "extra_metrics") and isinstance(record.extra_metrics, dict):
            log_entry["metrics"] = SecretScrubber.scrub_dict(record.extra_metrics)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class StudioLogger:
    """Wrapper providing structured logging methods with performance metrics."""
    def __init__(self, name: str, department: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.department = department

    def info(self, msg: str, duration_ms: Optional[float] = None, **kwargs):
        self._log(logging.INFO, msg, duration_ms, kwargs)

    def warning(self, msg: str, duration_ms: Optional[float] = None, **kwargs):
        self._log(logging.WARNING, msg, duration_ms, kwargs)

    def error(self, msg: str, duration_ms: Optional[float] = None, exc_info: bool = False, **kwargs):
        self._log(logging.ERROR, msg, duration_ms, kwargs, exc_info=exc_info)

    def debug(self, msg: str, duration_ms: Optional[float] = None, **kwargs):
        self._log(logging.DEBUG, msg, duration_ms, kwargs)

    def _log(self, level: int, msg: str, duration_ms: Optional[float], extra_metrics: dict, exc_info: bool = False):
        extra = {}
        if self.department:
            extra["department"] = self.department
        if duration_ms is not None:
            extra["duration_ms"] = round(duration_ms, 2)
        if extra_metrics:
            extra["extra_metrics"] = extra_metrics
        self.logger.log(level, msg, extra=extra, exc_info=exc_info)


def setup_observability_logging(log_level: int = logging.INFO, log_file: Optional[str] = "logs/studio.jsonl") -> None:
    root = logging.getLogger()
    root.setLevel(log_level)

    # Avoid duplicate handlers on re-setup
    for h in list(root.handlers):
        root.removeHandler(h)

    formatter = JSONFormatter()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # File Handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


def get_logger(name: str, department: Optional[str] = None) -> StudioLogger:
    return StudioLogger(name, department=department)
