import csv
import json
import random
import time
from pathlib import Path
from threading import Lock

from ..config import (BENCHMARK_COOLDOWN_SECONDS, BENCHMARK_PHRASES_DIR, BENCHMARK_REFERENCE_PATH, BENCHMARK_SIZE,
                      SLA_TARGET_MS)
from ..nlp.classifier import IntentClassifier
from .collector import histogram, percentiles


# нагрузочный тест по кнопке со страницы «Производительность»: модель подряд обрабатывает фразы
# тестового набора (опечатки, сленг, транслит, длинные вопросы), меряется задержка каждого вызова.
# в живые метрики чата не попадает. Защита сервера на 0,1 CPU:
#  - одновременно идёт не больше одного теста;
#  - общий кулдаун на весь сервер – не чаще одного теста в 5 минут (~6 с CPU, около 2% времени);
#    в остальное время возвращается последний результат с его возрастом
class Benchmark:
    def __init__(self, classifier: IntentClassifier, phrases_dir: Path = BENCHMARK_PHRASES_DIR,
                 size: int = BENCHMARK_SIZE, cooldown: float = BENCHMARK_COOLDOWN_SECONDS,
                 reference_path: Path = BENCHMARK_REFERENCE_PATH):
        phrases: list[str] = []
        for path in sorted(phrases_dir.glob("*.csv")):
            with path.open(encoding="utf-8", newline="") as f:
                phrases += [row["text"] for row in csv.DictReader(f)]
        if not phrases:
            raise RuntimeError(f"нет фраз для нагрузочного теста в {phrases_dir}")
        random.Random(42).shuffle(phrases)  # один и тот же набор при каждом запуске – результаты сравнимы
        self.phrases = phrases[:size]
        self.classifier = classifier
        self.cooldown = cooldown
        self._lock = Lock()
        self._last: dict | None = None
        self._last_at: float | None = None  # monotonic-время последнего живого теста
        # после пробуждения сервера память пуста – показываем сохранённый замер на Render (research/results)
        self._reference = self._load_reference(reference_path)

    @staticmethod
    def _load_reference(path: Path) -> dict | None:
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        first = data["benchmarks"][0]
        return {**first, "source": "reference", "measured_at": data.get("measured_at")}

    def next_run_in(self) -> float:
        if self._last_at is None:
            return 0.0
        return max(0.0, self.cooldown - (time.monotonic() - self._last_at))

    # последний результат: живой тест с его возрастом или сохранённый замер; None – нет ни того, ни другого
    def last(self) -> dict | None:
        result = self._last or self._reference
        if result is None:
            return None
        age = time.monotonic() - self._last_at if self._last else None
        return {**result, "age_seconds": age, "next_run_in": self.next_run_in(), "cooldown_seconds": self.cooldown}

    # None – тест уже идёт; во время кулдауна – последний результат с cached = True, без нагрузки на CPU
    def run(self) -> dict | None:
        if not self._lock.acquire(blocking=False):
            return None
        try:
            if self.next_run_in() > 0:
                return {**self.last(), "cached": True}
            latencies = []
            start = time.perf_counter()
            for text in self.phrases:
                t0 = time.perf_counter()
                self.classifier.predict(text)
                latencies.append((time.perf_counter() - t0) * 1000)
            seconds = time.perf_counter() - start
            self._last = {
                "n": len(latencies),
                "seconds": seconds,
                "throughput_rps": len(latencies) / seconds if seconds else None,
                "latency_ms": percentiles(latencies),
                "histogram": histogram(latencies),
                "sla": {"target_ms": SLA_TARGET_MS,
                        "share": sum(v <= SLA_TARGET_MS for v in latencies) / len(latencies)},
                "series": [round(v, 2) for v in latencies],  # для «проигрывания» теста на графике
                "source": "live",
                "measured_at": None,
            }
            self._last_at = time.monotonic()
        finally:
            self._lock.release()
        return {**self.last(), "cached": False}
