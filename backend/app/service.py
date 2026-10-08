import logging
import time
from dataclasses import dataclass, field

from .config import SUGGESTIONS_COUNT
from .knowledge import FALLBACK, Knowledge
from .metrics.collector import MetricsCollector
from .nlp.classifier import IntentClassifier
from .nlp.language import detect_language

logger = logging.getLogger("turanassist")


@dataclass
class Answer:
    recognized: bool
    intent: str | None
    title: str | None
    confidence: float
    text: str
    source_url: str | None
    lang: str
    suggestions: list[tuple[str, str, float]] = field(default_factory=list)  # (интент, название, уверенность)
    timing_ms: dict = field(default_factory=dict)


# общая логика веб-чата и Telegram-бота: вопрос -> интент -> ответ из базы или «не понял» с подсказками
def answer_question(classifier: IntentClassifier, knowledge: Knowledge, metrics: MetricsCollector,
                    text: str, lang: str | None = None, channel: str = "web") -> Answer:
    start = time.perf_counter()
    lang = lang or detect_language(text)
    pred = classifier.predict(text)
    if pred.recognized:
        answer = Answer(True, pred.intent, knowledge.title(pred.intent, lang), pred.confidence,
                        knowledge.answer(pred.intent, lang), knowledge.source_url(pred.intent, lang), lang)
    else:
        suggestions = [(i, knowledge.title(i, lang), c) for i, c in pred.top[:SUGGESTIONS_COUNT]]
        answer = Answer(False, None, None, pred.confidence, FALLBACK[lang], None, lang, suggestions)
    total_ms = (time.perf_counter() - start) * 1000
    answer.timing_ms = {**pred.timing_ms, "total": total_ms}
    metrics.record(total_ms, pred.timing_ms, pred.recognized)
    # текст вопроса в лог не пишем: в нём могут быть персональные данные пользователя
    logger.info("%s: lang=%s intent=%s conf=%.3f recognized=%s total=%.1fms", channel, lang, pred.intent,
                pred.confidence, pred.recognized, total_ms)
    return answer
