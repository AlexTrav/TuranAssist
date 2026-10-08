import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import onnxruntime as ort

from ..config import ENCODER_FILE, ONNX_THREADS, PRODUCTION_INFO_PATH, ROOT, TOKENIZER_FILE
from .model_files import local_path
from .tokenizer import XlmrTokenizer


@dataclass
class Prediction:
    intent: str
    confidence: float
    recognized: bool  # уверенность не ниже порога – можно отвечать из базы
    top: list[tuple[str, float]]  # интенты по убыванию вероятности – для подсказок «возможно, вы имели в виду»
    timing_ms: dict = field(default_factory=dict)


def _softmax(logits: np.ndarray) -> np.ndarray:
    exp = np.exp(logits - logits.max())
    return exp / exp.sum()


# ансамбль классификаторов интентов: TF-IDF по символьным n-граммам и эмбеддинги multilingual-e5-small
# (ONNX int8) с головой логистической регрессии; итоговые вероятности – взвешенное среднее
class IntentClassifier:
    def __init__(self, info_path: Path = PRODUCTION_INFO_PATH):
        start = time.perf_counter()
        info = json.loads(info_path.read_text(encoding="utf-8"))
        self.name = info["name"]
        self.intents: list[str] = info["intents"]
        self.threshold = float(info["threshold"])
        self.weight_e5 = float(info.get("weight_e5", 1.0))

        self.tfidf = joblib.load(ROOT / info["tfidf"]["artifact"])
        if list(self.tfidf.classes_) != self.intents:
            raise RuntimeError("порядок интентов TF-IDF не совпадает с model_info.json")

        e5 = info["e5"]
        self.query_prefix = e5["query_prefix"]
        self.tokenizer = XlmrTokenizer(local_path(TOKENIZER_FILE), max_length=e5["max_length"])
        options = ort.SessionOptions()
        options.intra_op_num_threads = ONNX_THREADS
        options.inter_op_num_threads = ONNX_THREADS
        self.session = ort.InferenceSession(str(local_path(ENCODER_FILE)), options,
                                            providers=["CPUExecutionProvider"])
        head = np.load(ROOT / e5["head"])
        self.coef, self.intercept = head["coef"], head["intercept"]
        if self.coef.shape[0] != len(self.intents):
            raise RuntimeError("голова e5 не совпадает по числу интентов")

        self.load_seconds = time.perf_counter() - start
        # первый вызов инициализирует внутренние буферы ONNX Runtime – делаем его до первого пользователя
        warm = time.perf_counter()
        self.predict("здравствуйте")
        self.warmup_ms = (time.perf_counter() - warm) * 1000

    def _e5_proba(self, text: str) -> np.ndarray:
        ids = np.array([self.tokenizer.encode(self.query_prefix + text)], dtype=np.int64)
        mask = np.ones_like(ids)  # один вопрос без паддинга – все токены значимые
        embedding = self.session.run(None, {"input_ids": ids, "attention_mask": mask})[0][0]
        return _softmax(self.coef @ embedding + self.intercept)

    def predict(self, text: str) -> Prediction:
        t0 = time.perf_counter()
        p_tfidf = self.tfidf.predict_proba([text])[0]
        t1 = time.perf_counter()
        p_e5 = self._e5_proba(text)
        t2 = time.perf_counter()
        proba = self.weight_e5 * p_e5 + (1 - self.weight_e5) * p_tfidf
        order = np.argsort(-proba)
        best = int(order[0])
        return Prediction(
            intent=self.intents[best],
            confidence=float(proba[best]),
            recognized=bool(proba[best] >= self.threshold),
            top=[(self.intents[i], float(proba[i])) for i in order[:5]],
            timing_ms={"tfidf": (t1 - t0) * 1000, "e5": (t2 - t1) * 1000, "model": (t2 - t0) * 1000},
        )
