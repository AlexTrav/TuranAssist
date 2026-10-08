import pytest

from app.config import CHAT_RATE_LIMIT, MAX_TEXT_LENGTH
from app.knowledge import FALLBACK

LIMIT = int(CHAT_RATE_LIMIT.split("/")[0])


def ask(client, text, lang=None, ip=None):
    headers = {"X-Forwarded-For": ip} if ip else {}
    return client.post("/api/chat", json={"text": text, "lang": lang}, headers=headers)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


@pytest.mark.parametrize("text, intent, lang", [
    ("Сколько стоит обучение в бакалавриате?", "tuition_bachelor", "ru"),
    ("Есть ли общежитие?", "dormitory", "ru"),
    ("Как взять академический отпуск?", "academic_leave", "ru"),
    ("Телефон приёмной комиссии", "contacts", "ru"),
    ("Жатақхана бар ма?", "dormitory", "kk"),
    ("How do I apply for a master's program?", "master_admission", "en"),
])
def test_chat_answers_known_questions(client, knowledge, text, intent, lang):
    data = ask(client, text).json()
    assert data["recognized"] is True
    assert data["intent"] == intent
    assert data["lang"] == lang
    assert data["answer"] == knowledge.answer(intent, lang)
    assert data["title"] == knowledge.title(intent, lang)
    assert data["suggestions"] == []
    assert set(data["timing_ms"]) == {"tfidf", "e5", "model", "total"}


def test_chat_source_link_in_user_language(client):
    data = ask(client, "Сколько стоит обучение в бакалавриате?", lang="en").json()
    assert data["lang"] == "en"
    assert data["source_url"].startswith("https://turan.edu.kz/en/")


def test_chat_unknown_question_returns_fallback_with_suggestions(client):
    data = ask(client, "фывапролдж йцукен").json()
    assert data["recognized"] is False
    assert data["intent"] is None
    assert data["answer"] == FALLBACK["ru"]
    assert len(data["suggestions"]) == 3
    assert all(s["title"] for s in data["suggestions"])


@pytest.mark.parametrize("body, code", [
    ({"text": "   "}, "empty_text"),
    ({"text": "а" * (MAX_TEXT_LENGTH + 1)}, "text_too_long"),
    ({"text": "Есть ли общежитие?", "lang": "de"}, "unsupported_lang"),
])
def test_chat_validation(client, body, code):
    resp = client.post("/api/chat", json=body)
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == code


def test_chat_collapses_whitespace(client):
    assert ask(client, "Есть   ли\n\nобщежитие?").json()["intent"] == "dormitory"


def test_rate_limit_counts_invalid_requests_too(client):
    # невалидные запросы тоже расходуют лимит – валидация вызывается внутри эндпоинта, а не в Depends()
    for _ in range(LIMIT):
        assert client.post("/api/chat", json={"text": ""}).status_code == 400
    resp = ask(client, "Есть ли общежитие?")
    assert resp.status_code == 429
    assert resp.json()["detail"]["code"] == "rate_limited"


def test_rate_limit_is_per_client_ip(client):
    for _ in range(LIMIT):
        ask(client, "привет", ip="10.0.0.1")
    assert ask(client, "привет", ip="10.0.0.1").status_code == 429
    assert ask(client, "привет", ip="10.0.0.2").status_code == 200


def test_cors_allows_only_own_origins(client):
    def preflight(origin):
        return client.options("/api/chat", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
    assert preflight("https://alextrav.github.io").headers.get("access-control-allow-origin") == "https://alextrav.github.io"
    assert "access-control-allow-origin" not in preflight("https://evil.example").headers


def test_intents_lists_all_groups_and_titles(client, classifier):
    groups = client.get("/api/intents").json()
    intents = [i for g in groups for i in g["intents"]]
    assert len(groups) == 8
    assert {i["id"] for i in intents} == set(classifier.intents)
    assert all(set(i["title"]) == {"ru", "kk", "en"} for i in intents)


def test_model_info_compares_models(client):
    data = client.get("/api/model-info").json()
    assert set(data["comparison"]) == {"tfidf", "e5", "ensemble"}
    assert data["intents"] == 53
    assert 0 < data["threshold"] < 1


def test_metrics_reflect_requests(client):
    before = client.get("/api/metrics").json()["requests_total"]
    ask(client, "Есть ли общежитие?")
    data = client.get("/api/metrics").json()
    assert data["requests_total"] == before + 1
    assert data["model_load_seconds"] > 0
    assert data["latency_ms"]["total"]["p50"] > 0
    assert data["recent"][-1]["recognized"] is True


def test_answer_by_intent(client, knowledge):
    data = client.get("/api/answer/dormitory", params={"lang": "kk"}).json()
    assert data["answer"] == knowledge.answer("dormitory", "kk")
    assert data["source_url"].startswith("https://turan.edu.kz/")
    assert client.get("/api/answer/no_such_intent").status_code == 404
    assert client.get("/api/answer/dormitory", params={"lang": "de"}).status_code == 400
