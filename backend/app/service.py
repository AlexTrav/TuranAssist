import logging
import time
from dataclasses import dataclass, field

from .config import MAX_TEXT_LENGTH, SUGGESTIONS_COUNT
from .knowledge import FALLBACK, Knowledge
from .metrics.collector import MetricsCollector
from .nlp.classifier import IntentClassifier, Prediction
from .nlp.context import Context, is_follow_up, use_context
from .nlp.language import detect_language

logger = logging.getLogger("turanassist")

NO_CONTEXT_GROUPS = {"service"}  # после «привет» и «спасибо» уточнять нечего


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
    programs: list[str] = field(default_factory=list)  # программы, найденные в вопросе о стоимости
    context_used: bool = False  # вопрос понят как уточнение предыдущего
    context: Context | None = None  # контекст для следующего вопроса: клиент присылает его обратно
    prices: list[dict] = field(default_factory=list)  # цены найденных программ структурой – для таблицы в веб-чате
    # для панели «Как бот понял»: итоговое предсказание, классифицированный текст и сработавшее правило
    prediction: Prediction | None = None
    classified_text: str = ""
    rule: str = "fallback"


# общая логика веб-чата и Telegram-бота: вопрос -> интент -> ответ из базы или «не понял» с подсказками
def answer_question(classifier: IntentClassifier, knowledge: Knowledge, metrics: MetricsCollector,
                    text: str, lang: str | None = None, channel: str = "web",
                    context: Context | None = None) -> Answer:
    start = time.perf_counter()

    # решение по одному варианту вопроса: порог модели, а для вопроса с программой – сумма двух
    # интентов стоимости (см. Tuition.resolve_intent)
    def decide(p: Prediction, question: str) -> tuple[str, float, bool, str]:
        if p.recognized:
            return p.intent, p.confidence, True, "model"
        resolved = knowledge.tuition.resolve_intent(question, p.top, classifier.threshold)
        return (*resolved, True, "tuition_sum") if resolved else (p.intent, p.confidence, False, "fallback")

    pred = classifier.predict(text)
    timing = dict(pred.timing_ms)
    decision, used_text, context_used = decide(pred, text), text, False
    follow_up = context is not None and context.intent in knowledge.intents and is_follow_up(text)
    if follow_up:
        joint_text = f"{context.text} {text}"
        joint = classifier.predict(joint_text)
        timing = {k: v + joint.timing_ms.get(k, 0.0) for k, v in timing.items()}
        joint_decision = decide(joint, joint_text)
        same_group = knowledge.intents[joint_decision[0]].group == knowledge.intents[context.intent].group
        if use_context(text, decision[2], joint_decision[2], same_group):
            pred, decision, used_text, context_used = joint, joint_decision, joint_text, True
    # язык уточнения – по всему диалогу: в «а PhD?» латиницы больше, но спрашивают по-русски,
    # а в «ал магистратурада?» нет казахских букв
    lang = lang or detect_language(f"{context.text} {text}" if follow_up else text)

    intent, confidence, recognized, rule = decision
    if recognized:
        answer = Answer(True, intent, knowledge.title(intent, lang), confidence,
                        knowledge.answer(intent, lang), knowledge.source_url(intent, lang), lang)
        # вопрос о стоимости с названием программы («Сколько стоит ВТиПО?») – цена именно этой программы;
        # в уточнении «а в магистратуре?» программа берётся из предыдущего вопроса
        specific = knowledge.tuition.answer(intent, text, lang, context_text=used_text)
        if specific:
            answer.text, answer.programs = specific
            answer.prices = knowledge.tuition.cards(intent, answer.programs, lang)
        if knowledge.intents[intent].group not in NO_CONTEXT_GROUPS:
            answer.context = Context(used_text[-MAX_TEXT_LENGTH:], intent)
    else:
        suggestions = [(i, knowledge.title(i, lang), c) for i, c in pred.top[:SUGGESTIONS_COUNT]]
        answer = Answer(False, None, None, confidence, FALLBACK[lang], None, lang, suggestions)
    answer.context_used = context_used
    answer.prediction, answer.classified_text, answer.rule = pred, used_text, rule
    total_ms = (time.perf_counter() - start) * 1000
    answer.timing_ms = {**timing, "total": total_ms}
    metrics.record(total_ms, timing, recognized)
    # текст вопроса в лог не пишем: в нём могут быть персональные данные пользователя
    logger.info("%s: lang=%s intent=%s programs=%s context=%s conf=%.3f recognized=%s total=%.1fms", channel,
                lang, intent, ",".join(answer.programs) or "-", context_used, confidence, recognized, total_ms)
    return answer
