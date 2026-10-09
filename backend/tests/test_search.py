import numpy as np

from app.nlp.search import TopicSearch, stems


def test_index_is_cached_and_rebuilt_when_titles_change(classifier, knowledge, tmp_path):
    first = TopicSearch(classifier, knowledge, tmp_path)
    assert first.matrix.shape == (3, len(first.intents), first.matrix.shape[2])
    assert "greeting" not in first.intents  # служебные темы в поиск не входят
    # норма каждого вектора – 1: близость считается скалярным произведением
    assert np.allclose(np.linalg.norm(first.matrix, axis=2), 1, atol=1e-4)
    cached = TopicSearch(classifier, knowledge, tmp_path)
    assert np.array_equal(first.matrix, cached.matrix)
    knowledge.intents["dormitory"].title["ru"] = "Общежитие для студентов"
    try:
        changed = TopicSearch(classifier, knowledge, tmp_path)
        assert changed._fingerprint() != first._fingerprint()
    finally:
        knowledge.intents["dormitory"].title["ru"] = "Общежитие"


def test_stems_match_word_forms():
    assert stems("Поступление в магистратуру") == stems("магистратура поступление")
    assert stems("Оқу ақысы") & stems("оқу ақысы қанша")


# запрос из ключевых слов: модель делит вероятность между соседними темами, поиск находит тему по названию
def test_keyword_query_is_answered_by_search(client):
    data = client.post("/api/chat", json={"text": "Магистратура поступление"}).json()
    assert data["recognized"] is True and data["intent"] == "master_admission"
    search = data["explain"]["search"]
    assert data["explain"]["rule"] == "search" and search["intent"] == "master_admission"
    assert search["score"] >= 0.9 and search["margin"] >= 0.025
    assert set(search["shared"]) == {"магистратура", "поступление"}


def test_search_does_not_answer_nonsense_or_long_questions(client):
    for text in ["бла бла бла", "Что такое биткоин?", "Подскажите, пожалуйста, как у вас с поступлением в магистратуру"]:
        data = client.post("/api/chat", json={"text": text}).json()
        assert data["explain"]["rule"] != "search", text


def test_search_endpoint_for_knowledge_base(client):
    assert client.get("/api/search", params={"q": "общага"}).json()[0]["id"] == "dormitory"
    assert client.get("/api/search", params={"q": "армия"}).json()[0]["id"] == "military"
    assert client.get("/api/search", params={"q": "бла бла"}).json() == []  # ниже порога ранга – ничего
    assert client.get("/api/search", params={"q": "  "}).status_code == 400
