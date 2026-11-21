"""
Prometheus-compatible In-Memory Metrics Registry & System Telemetry Collector.
Tracks latency distributions, counter rates, queue depth, and hardware acceleration stats.
"""
from collections import defaultdict
import threading
import time
from typing import Any, Dict, List, Tuple


class Counter:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.values: Dict[Tuple[Tuple[str, str], ...], float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0, **labels):
        key = tuple(sorted(labels.items()))
        with self._lock:
            self.values[key] += amount


class Gauge:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.values: Dict[Tuple[Tuple[str, str], ...], float] = defaultdict(float)
        self._lock = threading.Lock()

    def set(self, value: float, **labels):
        key = tuple(sorted(labels.items()))
        with self._lock:
            self.values[key] = float(value)

    def inc(self, amount: float = 1.0, **labels):
        key = tuple(sorted(labels.items()))
        with self._lock:
            self.values[key] += amount

    def dec(self, amount: float = 1.0, **labels):
        key = tuple(sorted(labels.items()))
        with self._lock:
            self.values[key] -= amount


class Histogram:
    """Latency histogram tracking count, sum, and average."""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.counts: Dict[Tuple[Tuple[str, str], ...], int] = defaultdict(int)
        self.sums: Dict[Tuple[Tuple[str, str], ...], float] = defaultdict(float)
        self._lock = threading.Lock()

    def observe(self, value: float, **labels):
        key = tuple(sorted(labels.items()))
        with self._lock:
            self.counts[key] += 1
            self.sums[key] += float(value)


class MetricsRegistry:
    """Central metrics collector delivering Prometheus format and structured JSON."""
    def __init__(self):
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
        self._init_standard_metrics()

    def _init_standard_metrics(self):
        # HTTP Metrics
        self.http_requests_total = self.register_counter(
            "studio_http_requests_total", "Total incoming HTTP requests handled by the API gateway"
        )
        self.http_request_duration_seconds = self.register_histogram(
            "studio_http_request_duration_seconds", "HTTP request processing latency in seconds"
        )
        # Job Queue Metrics
        self.job_queue_depth = self.register_gauge(
            "studio_job_queue_depth", "Current count of pending jobs in queue"
        )
        self.job_execution_duration_seconds = self.register_histogram(
            "studio_job_execution_duration_seconds", "Background job execution duration in seconds"
        )
        self.job_failures_total = self.register_counter(
            "studio_job_failures_total", "Total background job failures across departments"
        )
        # Hardware & Video Metrics
        self.active_transcode_sessions = self.register_gauge(
            "studio_active_transcode_sessions", "Currently executing VideoToolbox / FFmpeg encode sessions"
        )
        self.qc_defects_detected_total = self.register_counter(
            "studio_qc_defects_detected_total", "Total quality control defects identified"
        )
        self.generation_cost_usd_total = self.register_counter(
            "studio_generation_cost_usd_total", "Cumulative estimated cost of generative AI provider calls"
        )

    def register_counter(self, name: str, desc: str) -> Counter:
        c = Counter(name, desc)
        self.counters[name] = c
        return c

    def register_gauge(self, name: str, desc: str) -> Gauge:
        g = Gauge(name, desc)
        self.gauges[name] = g
        return g

    def register_histogram(self, name: str, desc: str) -> Histogram:
        h = Histogram(name, desc)
        self.histograms[name] = h
        return h

    def export_prometheus(self) -> str:
        lines: List[str] = []
        for name, c in self.counters.items():
            lines.append(f"# HELP {name} {c.description}")
            lines.append(f"# TYPE {name} counter")
            for labels, val in c.values.items():
                lbl_str = ",".join(f'{k}="{v}"' for k, v in labels)
                suffix = f"{{{lbl_str}}}" if lbl_str else ""
                lines.append(f"{name}{suffix} {val}")

        for name, g in self.gauges.items():
            lines.append(f"# HELP {name} {g.description}")
            lines.append(f"# TYPE {name} gauge")
            for labels, val in g.values.items():
                lbl_str = ",".join(f'{k}="{v}"' for k, v in labels)
                suffix = f"{{{lbl_str}}}" if lbl_str else ""
                lines.append(f"{name}{suffix} {val}")

        for name, h in self.histograms.items():
            lines.append(f"# HELP {name} {h.description}")
            lines.append(f"# TYPE {name} histogram")
            for labels, count in h.counts.items():
                total_sum = h.sums[labels]
                lbl_str = ",".join(f'{k}="{v}"' for k, v in labels)
                prefix = f"{{{lbl_str}}}" if lbl_str else ""
                lines.append(f"{name}_count{prefix} {count}")
                lines.append(f"{name}_sum{prefix} {total_sum}")

        return "\n".join(lines) + "\n"

    def export_json(self) -> Dict[str, Any]:
        return {
            "counters": {k: {str(lbl): v for lbl, v in c.values.items()} for k, c in self.counters.items()},
            "gauges": {k: {str(lbl): v for lbl, v in g.values.items()} for k, g in self.gauges.items()},
            "histograms": {
                k: {
                    str(lbl): {
                        "count": h.counts[lbl],
                        "sum": h.sums[lbl],
                        "avg": round(h.sums[lbl] / max(1, h.counts[lbl]), 4)
                    }
                    for lbl in h.counts.keys()
                }
                for k, h in self.histograms.items()
            }
        }


metrics = MetricsRegistry()

