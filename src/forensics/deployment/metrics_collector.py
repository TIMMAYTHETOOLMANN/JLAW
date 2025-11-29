"""Lightweight Prometheus metrics collector for JLAW.

Provides a minimal interface to expose process-level metrics and
custom counters/gauges for production deployments. Designed to start
an HTTP metrics server on a configurable port (default 8000).
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server

logger = logging.getLogger(__name__)


class Metrics:
    """Container for application metrics."""

    def __init__(self):
        # Core lifecycle counters
        self.app_starts = Counter("jlaw_app_starts_total", "Number of application starts")
        self.investigations_total = Counter(
            "jlaw_investigations_total", "Number of investigations executed"
        )
        self.filings_collected_total = Counter(
            "jlaw_filings_collected_total", "Number of filings collected"
        )
        self.filings_analyzed_total = Counter(
            "jlaw_filings_analyzed_total", "Number of filings analyzed"
        )
        self.violations_detected_total = Counter(
            "jlaw_violations_detected_total", "Number of violations detected"
        )

        # Gauges for current run
        self.current_filings_collected = Gauge(
            "jlaw_current_filings_collected", "Filings collected in current run"
        )
        self.current_filings_analyzed = Gauge(
            "jlaw_current_filings_analyzed", "Filings analyzed in current run"
        )
        self.current_violations_detected = Gauge(
            "jlaw_current_violations_detected", "Violations detected in current run"
        )

        # Performance metrics
        self.filing_analysis_seconds = Histogram(
            "jlaw_filing_analysis_seconds",
            "Time spent analyzing a single filing",
            buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5, 10, 30, 60, 120, 300),
        )
        self.run_duration_seconds = Summary(
            "jlaw_run_duration_seconds", "Total execution time of production run"
        )


_metrics_instance: Optional[Metrics] = None
_server_started = False


def get_metrics() -> Metrics:
    """Return a singleton Metrics instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = Metrics()
    return _metrics_instance


def start_metrics_server(port: int = 8000) -> None:
    """Start Prometheus metrics HTTP server on given port if not already running."""
    global _server_started
    if _server_started:
        return

    def _run():
        try:
            start_http_server(port)
            logger.info(f"📈 Prometheus metrics server started on port {port}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to start metrics server on port {port}: {e}")

    # Start server in a daemon thread so it doesn't block shutdown
    thread = threading.Thread(target=_run, name="metrics-server", daemon=True)
    thread.start()
    _server_started = True

    # Increment app start counter on first start
    try:
        get_metrics().app_starts.inc()
    except Exception:  # pragma: no cover - defensive
        pass
