import numpy as np
import pytest

from app.knowledge import FALLBACK
from app.nlp.language import detect_language
from app.nlp.preprocess import preprocess, tokenize


@pytest.mark.parametrize("text, lang", [
    ("Сколько стоит обучение?", "ru"),
    ("Жатақхана бар ма?", "kk"),
    ("Оқу ақысы қанша?", "kk"),
    ("How much is the tuition?", "en"),
    ("skolko stoit obuchenie", "en"),  # транслит отвечаем по-английски – латиница без кириллицы
    ("Есть ли IELTS центр?", "ru"),
])
def test_detect_language(text, lang):
    assert detect_language(text) == lang


def test_tokenize_normalizes_case_yo_and_decimals():
    assert tokenize("Ёлка IELTS 6.5, Тұран!") == ["елка", "ielts", "6.5", "тұран"]


def test_stopwords_keep_question_words():
    # вопросительные слова определяют интент («где» против «когда») – облегчённый список их не удаляет
    assert preprocess("где и когда сессия", lemmatize=False, stopwords="no_questions") == "где когда сессия"
    assert preprocess("где и когда сессия", lemmatize=False, stopwords="all") == "сессия"


def test_classifier_returns_probability_distribution(classifier):
    pred = classifier.predict("Сколько стоит обучение?")
    probs = [p for _, p in pred.top]
    assert probs == sorted(probs, reverse=True)
    assert pred.confidence == pytest.approx(probs[0])
    assert 0 < pred.confidence <= 1
    assert pred.recognized == (pred.confidence >= classifier.threshold)


def test_classifier_ensemble_matches_components(classifier):
    # итог ансамбля – взвешенная сумма распределений e5 и TF-IDF, каждое суммируется в 1
    text = "Есть ли общежитие?"
    p_tfidf = classifier.tfidf.predict_proba([text])[0]
    p_e5 = classifier._e5_proba(text)
    assert p_tfidf.sum() == pytest.approx(1) and p_e5.sum() == pytest.approx(1, abs=1e-5)
    expected = classifier.weight_e5 * p_e5 + (1 - classifier.weight_e5) * p_tfidf
    assert classifier.predict(text).confidence == pytest.approx(float(np.max(expected)), abs=1e-6)


def test_knowledge_is_complete(knowledge, classifier):
    assert set(knowledge.intents) == set(classifier.intents)
    for intent in knowledge.intents.values():
        for lang in ("ru", "kk", "en"):
            assert intent.answer[lang] and intent.title[lang]
            if intent.sources:
                assert knowledge.source_url(intent.id, lang).startswith("https://")
    assert set(FALLBACK) == {"ru", "kk", "en"}


# эталонные id взяты из tokenizer.json модели e5 (библиотека tokenizers): наша реализация на SentencePiece
# обязана выдавать ровно их – иначе эмбеддинги разойдутся с теми, на которых обучалась голова
@pytest.mark.parametrize("text, ids", [
    ("Есть ли общежитие?", [0, 41, 1294, 12, 54722, 1656, 59156, 52166, 103, 32, 2]),
    ("Жатақхана бар ма?", [0, 41, 1294, 12, 18465, 222, 7439, 81266, 2406, 4562, 32, 2]),
    ("How much is the tuition?", [0, 41, 1294, 12, 11249, 5045, 83, 70, 74278, 1363, 32, 2]),
])
def test_tokenizer_matches_reference_ids(classifier, text, ids):
    assert classifier.tokenizer.encode("query: " + text) == ids


def test_tokenizer_truncates_to_max_length(classifier):
    ids = classifier.tokenizer.encode("query: " + "слово " * 200)
    assert len(ids) == classifier.tokenizer.max_length
    assert ids[0] == 0 and ids[-1] == 2
