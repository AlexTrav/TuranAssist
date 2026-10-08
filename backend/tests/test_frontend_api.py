from app.config import BENCHMARK_SIZE, HISTOGRAM_BUCKETS_MS, SLA_TARGET_MS
from app.metrics.collector import histogram, rss_mb


def chat(client, text, context=None):
    return client.post("/api/chat", json={"text": text, "context": context}).json()


def test_explain_shows_every_pipeline_stage(client):
    ex = chat(client, "Сколько стоит обучение на юристов?")["explain"]
    assert ex["language"] == "ru"
    tokens = {t["text"]: t for t in ex["tokens"]}
    assert tokens["юристов"]["lemma"] == "юрист"  # лемматизация pymorphy3
    assert tokens["на"]["stopword"] is True and tokens["сколько"]["stopword"] is False  # вопросительные слова остаются
    assert ex["subwords"] and ex["subwords_total"] >= len(ex["subwords"])
    top = ex["top"][0]
    assert top["intent"] == "tuition_bachelor"
    # вероятность ансамбля – взвешенная сумма вероятностей двух моделей
    assert abs(top["probability"] - (ex["weights"]["e5"] * top["e5"] + ex["weights"]["tfidf"] * top["tfidf"])) < 1e-6
    assert ex["rule"] == "model" and ex["programs"] == ["jurisprudence"]


def test_explain_does_not_lemmatize_kazakh(client):
    tokens = {t["text"]: t["lemma"] for t in chat(client, "Сессия қашан басталады?")["explain"]["tokens"]}
    assert tokens["басталады"] == "басталады"  # русский лемматизатор дал бы «басталада»


def test_explain_marks_tuition_sum_rule_and_context(client):
    first = chat(client, "ВТиПО сколько стоит")
    assert first["explain"]["rule"] == "tuition_sum"
    second = chat(client, "а в магистратуре?", first["context"])
    assert second["explain"]["context_used"] is True
    assert second["explain"]["classified_text"] == "ВТиПО сколько стоит а в магистратуре?"


def test_explain_for_unrecognized_question(client):
    data = chat(client, "фывапролдж йцукен")
    assert data["explain"]["rule"] == "fallback" and len(data["explain"]["top"]) == 5


def test_chat_returns_price_cards(client):
    prices = chat(client, "Сколько стоит международные отношения?")["prices"]
    assert prices[0]["program"] == "international_relations"
    row = prices[0]["rows"][0]
    assert row == {"plan": "bachelor_4y", "label": "очная, 4 года", "main": 1476600, "english": 1814700}
    assert chat(client, "Есть ли общежитие?")["prices"] == []


def test_tuition_catalog(client, knowledge):
    data = client.get("/api/tuition").json()
    assert len(data["programs"]) == len(knowledge.tuition.names)
    assert {p["level"] for p in data["plans"]} == {"bachelor", "postgrad"}
    ce = next(p for p in data["programs"] if p["id"] == "computer_engineering")
    assert set(ce["name"]) == {"ru", "kk", "en"} and ce["prices"]


def test_knowledge_lists_all_answers(client, classifier, knowledge):
    items = client.get("/api/knowledge", params={"lang": "kk"}).json()
    assert {i["id"] for i in items} == set(classifier.intents)
    dorm = next(i for i in items if i["id"] == "dormitory")
    assert dorm["answer"] == knowledge.answer("dormitory", "kk")
    assert client.get("/api/knowledge", params={"lang": "de"}).status_code == 400


def test_feedback_counts_in_metrics(client):
    before = client.get("/api/metrics").json()["feedback"]
    assert client.post("/api/feedback", json={"intent": "dormitory", "useful": True}).status_code == 200
    client.post("/api/feedback", json={"intent": None, "useful": False})
    after = client.get("/api/metrics").json()["feedback"]
    assert after["useful"] == before["useful"] + 1 and after["not_useful"] == before["not_useful"] + 1


def test_metrics_histogram_and_sla(client):
    chat(client, "Есть ли общежитие?")
    data = client.get("/api/metrics").json()
    assert [b["le"] for b in data["histogram"]] == [*HISTOGRAM_BUCKETS_MS, None]
    assert sum(b["count"] for b in data["histogram"]) == data["window"]
    assert data["sla"]["target_ms"] == SLA_TARGET_MS and 0 <= data["sla"]["share"] <= 1


def test_histogram_buckets():
    counts = [b["count"] for b in histogram([1, 5, 6, 499, 10_000], buckets=(5, 10, 500))]
    assert counts == [2, 1, 1, 1]


def test_benchmark_runs_and_does_not_touch_live_metrics(client):
    before = client.get("/api/metrics").json()["requests_total"]
    data = client.post("/api/benchmark").json()
    assert data["n"] == BENCHMARK_SIZE == len(data["series"])
    assert data["throughput_rps"] > 0 and data["latency_ms"]["p50"] > 0
    assert sum(b["count"] for b in data["histogram"]) == BENCHMARK_SIZE
    assert client.get("/api/metrics").json()["requests_total"] == before


def test_benchmark_rate_limit_and_busy(client):
    bench = client.app.state.benchmark
    bench._lock.acquire()  # имитируем тест, запущенный из другой вкладки
    try:
        resp = client.post("/api/benchmark")
        assert resp.status_code == 409 and resp.json()["detail"]["code"] == "benchmark_busy"
    finally:
        bench._lock.release()
    client.post("/api/benchmark")
    assert client.post("/api/benchmark").status_code == 429

def test_memory_from_cgroup_without_inactive_file_cache(tmp_path):
    (tmp_path / "memory.current").write_text(str(400 * 2**20))
    (tmp_path / "memory.stat").write_text("anon 1\ninactive_file 73400320\nactive_file 5\n")
    assert rss_mb(tmp_path) == 330
