import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import numpy as np

from ..config import LATENCY_WINDOW


@dataclass
class Sample:
    ts: float
    total_ms: float
    model_ms: float
    tfidf_ms: float
    e5_ms: float
    recognized: bool


# память процесса из /proc (Linux, в Docker и на Render); вне Linux – None
def rss_mb() -> float | None:
    status = Path("/proc/self/status")
    if not status.exists():
        return None
    for line in status.read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) / 1024
    return None


# метрики «реального времени» в памяти процесса: задержки последних запросов и счётчики.
# хранятся до перезапуска – на бесплатном Render это честный компромисс вместо Prometheus
class MetricsCollector:
    def __init__(self, window: int = LATENCY_WINDOW):
        self.started_at = time.time()
        self.samples: deque[Sample] = deque(maxlen=window)
        self.requests_total = 0
        self.recognized_total = 0
        self.rate_limited_total = 0
        self.model_load_seconds: float | None = None
        self.warmup_ms: float | None = None
        self._lock = Lock()

    def record(self, total_ms: float, timing: dict, recognized: bool) -> None:
        with self._lock:
            self.samples.append(Sample(time.time(), total_ms, timing["model"], timing["tfidf"], timing["e5"], recognized))
            self.requests_total += 1
            self.recognized_total += int(recognized)

    def record_rate_limited(self) -> None:
        with self._lock:
            self.rate_limited_total += 1

    @staticmethod
    def _percentiles(values: list[float]) -> dict | None:
        if not values:
            return None
        arr = np.array(values)
        return {"p50": float(np.percentile(arr, 50)), "p95": float(np.percentile(arr, 95)),
                "p99": float(np.percentile(arr, 99)), "max": float(arr.max())}

    def snapshot(self, recent: int = 100) -> dict:
        with self._lock:
            samples = list(self.samples)
            requests, recognized, limited = self.requests_total, self.recognized_total, self.rate_limited_total
        now = time.time()
        return {
            "uptime_seconds": now - self.started_at,
            "model_load_seconds": self.model_load_seconds,
            "warmup_ms": self.warmup_ms,
            "memory_rss_mb": rss_mb(),
            "requests_total": requests,
            "recognized_share": recognized / requests if requests else None,
            "rate_limited_total": limited,
            "requests_last_minute": sum(1 for s in samples if now - s.ts <= 60),
            "window": len(samples),
            "latency_ms": {
                "total": self._percentiles([s.total_ms for s in samples]),
                "model": self._percentiles([s.model_ms for s in samples]),
                "tfidf": self._percentiles([s.tfidf_ms for s in samples]),
                "e5": self._percentiles([s.e5_ms for s in samples]),
            },
            # последние запросы для живого графика на странице «Производительность»
            "recent": [{"ts": s.ts, "total_ms": round(s.total_ms, 2), "model_ms": round(s.model_ms, 2),
                        "recognized": s.recognized} for s in samples[-recent:]],
        }
