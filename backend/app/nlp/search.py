import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..config import (ENCODER_FILE, MODEL_CACHE_DIR, MODEL_FILES, SEARCH_INDEX_FILE, SEARCH_MAX_WORDS,
                      SEARCH_MIN_MARGIN, SEARCH_MIN_RANK, SEARCH_MIN_SCORE)
from .classifier import IntentClassifier, Prediction
from .preprocess import STOPWORDS, lemma, tokenize

logger = logging.getLogger("turanassist")

LANGS = ("ru", "kk", "en")
EXCLUDED_GROUPS = {"service"}  # «привет» и «спасибо» – не темы для поиска
STEM_LENGTH = 5  # слова сравниваются по началу: «магистратуру» и «магистратура», «ақысы» и «ақы»


def stem(token: str) -> str:
    return lemma(token)[:STEM_LENGTH]


def stems(text: str) -> set[str]:
    return {stem(t) for t in tokenize(text) if t not in STOPWORDS and len(t) > 1}


@dataclass
class SearchHit:
    intent: str
    score: float  # косинусная близость вопроса к названию темы (лучшая из трёх языков)
    margin: float  # отрыв от следующей по близости темы
    shared: list[str] = field(default_factory=list)  # слова вопроса, которые есть в названии темы


# третий NLP-компонент – умный поиск по темам базы. Классификатор обучен на полных вопросах
# («Как поступить в магистратуру?»), а запрос из ключевых слов («Магистратура поступление») для него
# непривычен: вероятность расходится по соседним темам. Поиск сравнивает эмбеддинг e5 вопроса с эмбеддингами
# названий тем на трёх языках – тем же энкодером, поэтому лишнего прогона модели нет.
# Векторы названий считаются один раз при сборке Docker-образа и лежат рядом с моделью
class TopicSearch:
    def __init__(self, classifier: IntentClassifier, knowledge, cache_dir: Path = MODEL_CACHE_DIR):
        self.classifier = classifier
        self.intents = [i for i, x in knowledge.intents.items() if x.group not in EXCLUDED_GROUPS]
        self.titles = {i: [knowledge.title(i, lang) for lang in LANGS] for i in self.intents}
        self.title_stems = {i: set().union(*(stems(t) for t in titles)) for i, titles in self.titles.items()}
        self.matrix = self._load_or_build(cache_dir / SEARCH_INDEX_FILE)  # (язык, тема, размерность)

    # отпечаток индекса: названия тем, версия энкодера и префикс – изменилось что-то одно, индекс пересчитывается
    def _fingerprint(self) -> str:
        payload = json.dumps([self.titles, MODEL_FILES[ENCODER_FILE]["sha256"], self.classifier.query_prefix],
                             ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _load_or_build(self, path: Path) -> np.ndarray:
        fingerprint = self._fingerprint()
        if path.exists():
            data = np.load(path)
            if str(data["fingerprint"]) == fingerprint:
                return data["matrix"]
        start = time.perf_counter()
        vectors = [[self._unit(self.classifier.embed(self.titles[i][k])) for i in self.intents]
                   for k in range(len(LANGS))]
        matrix = np.array(vectors, dtype=np.float32)
        try:
            np.savez(path, matrix=matrix, fingerprint=fingerprint)
        except OSError:
            pass  # кеш только ускоряет запуск – без него индекс просто считается заново
        logger.info("индекс поиска: %d тем × %d языка за %.1f с", len(self.intents), len(LANGS),
                    time.perf_counter() - start)
        return matrix

    @staticmethod
    def _unit(vector: np.ndarray) -> np.ndarray:
        return vector / np.linalg.norm(vector)

    # близость вопроса к каждой теме: максимум по трём языкам названий
    def scores(self, embedding: np.ndarray) -> np.ndarray:
        return (self.matrix @ embedding).max(axis=0)

    def best(self, text: str, embedding: np.ndarray) -> SearchHit:
        scores = self.scores(embedding)
        first, second = np.argsort(-scores)[:2]
        intent = self.intents[int(first)]
        words = [t for t in tokenize(text)
                 if t not in STOPWORDS and len(t) > 1 and stem(t) in self.title_stems[intent]]
        return SearchHit(intent, float(scores[first]), float(scores[first] - scores[second]), words)

    # тема для короткого запроса, в которой модель не уверена, или None. Поиск отвечает, только если:
    # запрос не длиннее SEARCH_MAX_WORDS слов, тема заметно ближе остальных (близость и отрыв не ниже порогов),
    # модель держит её в своей пятёрке и хотя бы одно слово запроса есть в названии темы. Пороги подобраны
    # так, чтобы на вопросах не по теме (data/phrases/ood.csv) поиск не дал ни одного ответа
    def match(self, text: str, pred: Prediction) -> SearchHit | None:
        if pred.embedding is None or len(tokenize(text)) > SEARCH_MAX_WORDS:
            return None
        hit = self.best(text, pred.embedding)
        if hit.score < SEARCH_MIN_SCORE or hit.margin < SEARCH_MIN_MARGIN:
            return None
        if hit.intent not in {i for i, _ in pred.top} or not hit.shared:
            return None
        return hit

    # темы по смыслу для страницы «База знаний». Ранг – вероятность темы у модели плюс близость к названию:
    # модель знает сленг и перефразировки («общага» -> общежитие), близость к названию – ключевые слова
    # («магистратура поступление»). Один прогон модели на запрос
    def search(self, query: str, limit: int) -> list[tuple[str, float]]:
        pred = self.classifier.predict(query)
        proba = dict(zip(self.classifier.intents, pred.proba))
        scores = self.scores(pred.embedding) + np.array([proba[i] for i in self.intents])
        order = np.argsort(-scores)[:limit]
        return [(self.intents[int(i)], float(scores[i])) for i in order if scores[i] >= SEARCH_MIN_RANK]


# python -m app.nlp.search – посчитать индекс заранее (при сборке Docker-образа)
if __name__ == "__main__":
    from ..knowledge import Knowledge

    logging.basicConfig(level=logging.INFO)
    TopicSearch(IntentClassifier(), Knowledge())
