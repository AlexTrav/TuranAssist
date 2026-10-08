import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import numpy as np

from ..config import HISTOGRAM_BUCKETS_MS, LATENCY_WINDOW, SLA_TARGET_MS


@dataclass
class Sample:
    ts: float
    total_ms: float
    model_ms: float
    tfidf_ms: float
    e5_ms: float
    recognized: bool


CGROUP_DIR = Path("/sys/fs/cgroup")


# память контейнера так, как её считает лимит (и docker stats): использование cgroup без неактивного
# файлового кэша. VmRSS процесса завышен: в него входят отображённые в память файлы библиотек
def rss_mb(cgroup_dir: Path = CGROUP_DIR) -> float | None:
    current, stat = cgroup_dir / "memory.current", cgroup_dir / "memory.stat"
    if current.exists() and stat.exists():
        inactive = next((int(line.split()[1]) for line in stat.read_text().splitlines()
                         if line.startswith("inactive_file ")), 0)
        return (int(current.read_text()) - inactive) / 2**20
    # вне контейнера с cgroup v2 – резидентная память процесса из /proc; вне Linux – None
    status = Path("/proc/self/status")
    if not status.exists():
        return None
    for line in status.read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) / 1024
    return None


# гистограмма задержек по фиксированным корзинам: le – верхняя граница корзины, None – всё, что дольше
def histogram(values: list[float], buckets: tuple = HISTOGRAM_BUCKETS_MS) -> list[dict]:
    counts = [0] * (len(buckets) + 1)
    for v in values:
        counts[next((i for i, b in enumerate(buckets) if v <= b), len(buckets))] += 1
    return [{"le": b, "count": n} for b, n in zip([*buckets, None], counts)]


def percentiles(values: list[float]) -> dict | None:
    if not values:
        return None
    arr = np.array(values)
    return {"p50": float(np.percentile(arr, 50)), "p95": float(np.percentile(arr, 95)),
            "p99": float(np.percentile(arr, 99)), "max": float(arr.max())}


# метрики «реального времени» в памяти процесса: задержки последних запросов и счётчики.
# хранятся до перезапуска – на бесплатном Render это честный компромисс вместо Prometheus
class MetricsCollector:
    def __init__(self, window: int = LATENCY_WINDOW):
        self.started_at = time.time()
        self.samples: deque[Sample] = deque(maxlen=window)
        self.requests_total = 0
        self.recognized_total = 0
        self.rate_limited_total = 0
        self.feedback = {"useful": 0, "not_useful": 0}  # оценки ответов 👍/👎 из веб-чата, без текста вопросов
        self.model_load_seconds: float | None = None
        self.warmup_ms: float | None = None
        self._lock = Lock()

    def record(self, total_ms: float, timing: dict, recognized: bool) -> None:
        with self._lock:
            self.samples.append(Sample(time.time(), total_ms, timing["model"], timing["tfidf"], timing["e5"], recognized))
            self.requests_total += 1
            self.recognized_total += int(recognized)

    def record_feedback(self, useful: bool) -> None:
        with self._lock:
            self.feedback["useful" if useful else "not_useful"] += 1

    def record_rate_limited(self) -> None:
        with self._lock:
            self.rate_limited_total += 1


    def snapshot(self, recent: int = 100) -> dict:
        with self._lock:
            samples = list(self.samples)
            requests, recognized, limited = self.requests_total, self.recognized_total, self.rate_limited_total
            feedback = dict(self.feedback)
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
                "total": percentiles([s.total_ms for s in samples]),
                "model": percentiles([s.model_ms for s in samples]),
                "tfidf": percentiles([s.tfidf_ms for s in samples]),
                "e5": percentiles([s.e5_ms for s in samples]),
            },
            "histogram": histogram([s.total_ms for s in samples]),
            # доля ответов быстрее цели по задержке – «укладываемся ли в реальное время»
            "sla": {"target_ms": SLA_TARGET_MS,
                    "share": sum(s.total_ms <= SLA_TARGET_MS for s in samples) / len(samples) if samples else None},
            "feedback": feedback,
            # последние запросы для живого графика на странице «Производительность»
            "recent": [{"ts": s.ts, "total_ms": round(s.total_ms, 2), "model_ms": round(s.model_ms, 2),
                        "recognized": s.recognized} for s in samples[-recent:]],
        }
