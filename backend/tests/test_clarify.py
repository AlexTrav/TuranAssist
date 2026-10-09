from app.nlp.classifier import Prediction
from app.service import clarify_topics


def prediction(top: list[tuple[str, float]]) -> Prediction:
    return Prediction(intent=top[0][0], confidence=top[0][1], recognized=False, top=top, components=[], timing_ms={})


# короткий запрос на несколько тем: бот не гадает, а просит выбрать тему
def test_short_query_asks_to_clarify(client):
    data = client.post("/api/chat", json={"text": "Гранты"}).json()
    assert data["recognized"] is False and data["clarify"] is True
    assert {"state_grant", "vacant_grant"} <= {s["intent"] for s in data["suggestions"]}
    assert data["answer"].startswith("Уточните")
    assert data["explain"]["rule"] == "clarify"
    assert data["explain"]["decisive"] >= data["explain"]["threshold"]


def test_long_or_unclear_queries_are_not_clarified(client):
    for text in ["Что такое биткоин?", "Расскажи анекдот про студентов и сессию"]:
        data = client.post("/api/chat", json={"text": text}).json()
        assert data["clarify"] is False, text


def test_clarify_rules(knowledge):
    thr = 0.577
    grants = [("state_grant", 0.46), ("vacant_grant", 0.35), ("ent_discounts", 0.05), ("thanks", 0.04)]
    assert [i for i, _ in clarify_topics(prediction(grants), knowledge, "Гранты", thr)] == \
        ["state_grant", "vacant_grant", "ent_discounts"]
    # длиннее трёх слов – это уже вопрос, а не запрос-слово
    assert clarify_topics(prediction(grants), knowledge, "а какие гранты у вас есть", thr) == []
    # служебные темы («спасибо», «пока») в уточнение не попадают и порог не добирают
    weak = [("tuition_bachelor", 0.29), ("goodbye", 0.19), ("thanks", 0.14), ("greeting", 0.1)]
    assert clarify_topics(prediction(weak), knowledge, "Price", thr) == []
    # темы из трёх групп – вопрос непонятен, а не двусмыслен
    scattered = [("payment_details", 0.3), ("library", 0.2), ("retake_fx", 0.2)]
    assert clarify_topics(prediction(scattered), knowledge, "биткоин", thr) == []
