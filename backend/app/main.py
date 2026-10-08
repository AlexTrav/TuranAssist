import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse

from .config import CHAT_RATE_LIMIT, CORS_ORIGINS, ENSEMBLE_METRICS_PATH, SUGGESTIONS_COUNT
from .knowledge import FALLBACK, Knowledge
from .metrics.collector import MetricsCollector
from .nlp.classifier import IntentClassifier
from .nlp.language import detect_language
from .schemas import ChatRequest, ChatResponse, GroupInfo, IntentInfo, Suggestion
from .security.rate_limit import limiter
from .security.validation import validated_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("turanassist")


# сводка качества моделей для страницы «О проекте»: TF-IDF, e5 и выбранный ансамбль (с порогом)
def model_summary(classifier: IntentClassifier) -> dict:
    report = json.loads(ENSEMBLE_METRICS_PATH.read_text(encoding="utf-8"))
    rows = {"tfidf": "tfidf|maxprob", "e5": "encoder_int8_full|maxprob", "ensemble": report["best"]}
    comparison = {}
    for label, key in rows.items():
        r = report["results"][key]
        comparison[label] = {
            "cv_accuracy": r["cv_accuracy"], "threshold": r["threshold"], "latency_p50_ms": r["latency_p50_ms"],
            "test": r["test"]["overall"], "ood_rejected": r["ood_test"]["ood_rejected"],
            "external": r["external"]["overall"], "scenarios": r["scenarios"]["overall"],
        }
    return {"name": classifier.name, "threshold": classifier.threshold, "weight_e5": classifier.weight_e5,
            "intents": len(classifier.intents), "encoder": "intfloat/multilingual-e5-small (ONNX int8)",
            "comparison": comparison}


# модели и база ответов грузятся один раз при старте – первый пользователь не ждёт загрузки
@asynccontextmanager
async def lifespan(app: FastAPI):
    metrics = MetricsCollector()
    knowledge = Knowledge()
    classifier = IntentClassifier()
    if set(classifier.intents) != set(knowledge.intents):
        raise RuntimeError("интенты модели и базы ответов не совпадают")
    metrics.model_load_seconds, metrics.warmup_ms = classifier.load_seconds, classifier.warmup_ms
    app.state.metrics, app.state.knowledge, app.state.classifier = metrics, knowledge, classifier
    app.state.model_summary = model_summary(classifier)
    logger.info("модель %s загружена за %.1f с, прогрев %.0f мс", classifier.name,
                classifier.load_seconds, classifier.warmup_ms)
    yield


app = FastAPI(title="TuranAssist API", lifespan=lifespan)

# запросы разрешены только с dev-сервера Vite, контейнера фронтенда и GitHub Pages
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type"])

# ограничение частоты запросов по IP – защита модели на 0,1 CPU от перегрузки
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    request.app.state.metrics.record_rate_limited()
    logger.warning("rate limit: %s %s", request.url.path, exc.detail)
    return JSONResponse(status_code=429, content={"detail": {
        "code": "rate_limited", "message": "Слишком много запросов, попробуйте через минуту"}})


# используется healthcheck-ом docker-compose и для «пробуждения» сервиса на Render
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# основной эндпоинт: вопрос -> интент -> ответ из базы или «не понял» с подсказками.
# обычная def: FastAPI выполняет её в пуле потоков, и расчёт модели не блокирует цикл событий
@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit(CHAT_RATE_LIMIT)
def chat(request: Request, body: ChatRequest) -> ChatResponse:
    start = time.perf_counter()
    text = validated_text(body)
    lang = body.lang or detect_language(text)
    state = request.app.state
    pred = state.classifier.predict(text)
    kb = state.knowledge

    if pred.recognized:
        intent, answer = pred.intent, kb.answer(pred.intent, lang)
        title, source_url, suggestions = kb.title(intent, lang), kb.source_url(intent, lang), []
    else:
        intent, title, source_url, answer = None, None, None, FALLBACK[lang]
        suggestions = [Suggestion(intent=i, title=kb.title(i, lang), confidence=round(c, 4))
                       for i, c in pred.top[:SUGGESTIONS_COUNT]]

    total_ms = (time.perf_counter() - start) * 1000
    state.metrics.record(total_ms, pred.timing_ms, pred.recognized)
    # текст вопроса в лог не пишем: в нём могут быть персональные данные пользователя
    logger.info("chat: lang=%s intent=%s conf=%.3f recognized=%s total=%.1fms", lang, pred.intent,
                pred.confidence, pred.recognized, total_ms)
    return ChatResponse(recognized=pred.recognized, intent=intent, title=title, confidence=round(pred.confidence, 4),
                        answer=answer, source_url=source_url, suggestions=suggestions, lang=lang,
                        timing_ms={**{k: round(v, 2) for k, v in pred.timing_ms.items()}, "total": round(total_ms, 2)})


# темы, на которые отвечает бот, по группам – для страницы «О проекте» и стартовых подсказок в чате
@app.get("/api/intents", response_model=list[GroupInfo])
def intents(request: Request) -> list[GroupInfo]:
    kb = request.app.state.knowledge
    return [GroupInfo(id=g["id"], title=g["title"],
                      intents=[IntentInfo(id=i.id, group=i.group, title=i.title)
                               for i in kb.intents.values() if i.group == g["id"]])
            for g in kb.groups]


@app.get("/api/model-info")
def model_info(request: Request) -> dict:
    return request.app.state.model_summary


# живые метрики для страницы «Производительность»: задержки p50/p95/p99, нагрузка, память, холодный старт
@app.get("/api/metrics")
def live_metrics(request: Request) -> dict:
    return request.app.state.metrics.snapshot()
