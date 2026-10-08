"""Замер задержек развёрнутого сервиса на Render (0,1 CPU, 512 МБ) для исследования.

Нагрузочный тест сервера (/api/benchmark, 100 фраз) трижды с паузой под rate limit (2 в минуту)
и полное время ответа /api/chat, как его видит пользователь (сеть + сервер):
    make -C research render
Результат – research/results/render_latency.json.
"""
import json
import statistics
import time
import urllib.request
from pathlib import Path

BASE = "https://turanassist-backend.onrender.com"
OUT = Path("/research/results/render_latency.json")
QUESTIONS = [
    "Сколько стоит обучение?", "Есть ли общежитие?", "Как поступить в магистратуру?", "Когда зимняя сессия?",
    "Какие документы нужны для поступления?", "Жатақхана бар ма?", "How much is the tuition?", "Есть ли гранты?",
    "Как взять академический отпуск?", "Телефон приёмной комиссии", "Сколько стоит ВТиПО?", "Оқу ақысы қанша?",
    "Is there a dormitory?", "Какой проходной балл?", "получил FX, что делать", "Где находится университет?",
    "Какие скидки по ЕНТ?", "Можно ли перевестись из другого вуза?", "Есть ли военная кафедра?", "Как оплатить обучение?",
]


def call(path: str, body: dict | None = None, timeout: int = 120) -> tuple[dict, float]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"},
                                 method="POST" if body is not None else "GET")
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.load(resp)
    return payload, (time.perf_counter() - t0) * 1000


def main() -> None:
    _, wake_ms = call("/api/health")  # сервис мог спать – первый запрос будит его (холодный старт)
    print(f"health {wake_ms:.0f} ms")
    benchmarks = []
    for i in range(3):
        if i:
            time.sleep(31)
        result, _ = call("/api/benchmark", {})
        benchmarks.append(result)
        print("benchmark", {k: round(v, 1) for k, v in result["latency_ms"].items()}, round(result["throughput_rps"], 1))
    time.sleep(61)  # окно rate limit чата освобождается
    rtt, server = [], []
    for q in QUESTIONS:
        payload, ms = call("/api/chat", {"text": q})
        rtt.append(ms)
        server.append(payload["timing_ms"]["total"])
    metrics, _ = call("/api/metrics")
    result = {"wake_ms": wake_ms, "benchmarks": benchmarks,
              "chat_rtt_ms": rtt, "chat_server_ms": server,
              "chat_rtt_median": statistics.median(rtt), "chat_server_median": statistics.median(server),
              "memory_mb": metrics["memory_rss_mb"], "model_load_seconds": metrics["model_load_seconds"]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print("chat rtt median", round(result["chat_rtt_median"]), "server", round(result["chat_server_median"], 1),
          "memory", result["memory_mb"])


if __name__ == "__main__":
    main()
