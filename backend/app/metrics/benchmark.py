import csv
import random
import time
from pathlib import Path
from threading import Lock

from ..config import BENCHMARK_PHRASES_DIR, BENCHMARK_SIZE, SLA_TARGET_MS
from ..nlp.classifier import IntentClassifier
from .collector import histogram, percentiles


# нагрузочный тест по кнопке со страницы «Производительность»: модель подряд обрабатывает фразы
# тестового набора (опечатки, сленг, транслит, длинные вопросы), меряется задержка каждого вызова.
# в живые метрики чата не попадает; одновременно идёт не больше одного теста – сервер на 0,1 CPU
class Benchmark:
    def __init__(self, classifier: IntentClassifier, phrases_dir: Path = BENCHMARK_PHRASES_DIR,
                 size: int = BENCHMARK_SIZE):
        phrases: list[str] = []
        for path in sorted(phrases_dir.glob("*.csv")):
            with path.open(encoding="utf-8", newline="") as f:
                phrases += [row["text"] for row in csv.DictReader(f)]
        if not phrases:
            raise RuntimeError(f"нет фраз для нагрузочного теста в {phrases_dir}")
        random.Random(42).shuffle(phrases)  # один и тот же набор при каждом запуске – результаты сравнимы
        self.phrases = phrases[:size]
        self.classifier = classifier
        self._lock = Lock()

    # None – тест уже идёт (запущен из другой вкладки или другим пользователем)
    def run(self) -> dict | None:
        if not self._lock.acquire(blocking=False):
            return None
        try:
            latencies = []
            start = time.perf_counter()
            for text in self.phrases:
                t0 = time.perf_counter()
                self.classifier.predict(text)
                latencies.append((time.perf_counter() - t0) * 1000)
            seconds = time.perf_counter() - start
        finally:
            self._lock.release()
        return {
            "n": len(latencies),
            "seconds": seconds,
            "throughput_rps": len(latencies) / seconds if seconds else None,
            "latency_ms": percentiles(latencies),
            "histogram": histogram(latencies),
            "sla": {"target_ms": SLA_TARGET_MS, "share": sum(v <= SLA_TARGET_MS for v in latencies) / len(latencies)},
            "series": [round(v, 2) for v in latencies],  # для «проигрывания» теста на графике
        }
