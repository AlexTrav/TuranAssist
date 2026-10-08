from .classifier import IntentClassifier, Prediction
from .preprocess import STOPWORDS_NO_QUESTIONS, lemma, normalize, tokenize

MAX_PIECES = 48  # длинный вопрос – показываем начало разбора, интерфейсу хватает


# разбор вопроса для панели «Как бот понял вопрос» в веб-чате: что сделала каждая ступень конвейера.
# считается после ответа и в его время не входит
def explain(classifier: IntentClassifier, pred: Prediction, text: str, classified_text: str,
            lang: str, rule: str, programs: list[str], context_used: bool) -> dict:
    tokens = tokenize(text)
    pieces = classifier.tokenizer.pieces(classified_text)
    return {
        "language": lang,
        "normalized": normalize(text),
        # предобработка, как у словесных baseline-моделей: токены, леммы pymorphy3, стоп-слова
        "tokens": [{"text": t, "lemma": lemma(t), "stopword": t in STOPWORDS_NO_QUESTIONS} for t in tokens],
        # подслова SentencePiece, которые получает трансформер (без служебного префикса «query: »)
        "subwords": pieces[:MAX_PIECES],
        "subwords_total": len(pieces),
        "classified_text": classified_text,
        "context_used": context_used,
        "top": [{"intent": intent, "probability": p, "e5": e5, "tfidf": tfidf}
                for (intent, p), (_, e5, tfidf) in zip(pred.top, pred.components)],
        "weights": {"e5": classifier.weight_e5, "tfidf": round(1 - classifier.weight_e5, 4)},
        "threshold": classifier.threshold,
        "rule": rule,  # model – порог модели, tuition_sum – сумма интентов стоимости, fallback – «не понял»
        "programs": programs,
    }
