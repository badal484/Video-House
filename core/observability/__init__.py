"""
Observability package for Universal AI Video Production Studio.
Structured JSON logging, correlation IDs, OpenTelemetry hooks, and metrics registry.
"""
from .logger import StudioLogger, get_logger, correlation_context, get_correlation_id
from .metrics import MetricsRegistry, metrics

__all__ = [
    "StudioLogger",
    "get_logger",
    "correlation_context",
    "get_correlation_id",
    "MetricsRegistry",
    "metrics",
]
