import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse

from .bot.handlers import BotHandler
from .bot.telegram_api import TelegramClient
from .bot.webhook import router as telegram_router
from .config import (BENCHMARK_RATE_LIMIT, CHAT_RATE_LIMIT, CORS_ORIGINS, ENSEMBLE_METRICS_PATH, FEEDBACK_RATE_LIMIT,
                     SUPPORTED_LANGS, TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET)
from .knowledge import Knowledge
from .metrics.benchmark import Benchmark
from .metrics.collector import MetricsCollector
from .nlp.classifier import IntentClassifier
from .nlp.explain import explain
from .schemas import (ChatContext, ChatRequest, ChatResponse, FeedbackRequest, GroupInfo, IntentAnswer, IntentInfo,
                      KnowledgeItem, Suggestion)
from .security.rate_limit import limiter
from .security.validation import validated_context, validated_text
from .service import answer_question

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("turanassist")
# httpx на уровне INFO пишет полный URL запроса, а в URL Bot API – токен бота: такие логи отключаем
logging.getLogger("httpx").setLevel(logging.WARNING)


# healthcheck docker-compose и Render дёргает /api/health каждые несколько секунд – успешные проверки
# не пишем в журнал доступа, иначе они забивают логи; ошибки проверки остаются видны
class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if isinstance(args, tuple) and len(args) >= 5:
            path, status = args[2], args[4]
            return not (str(path).startswith("/api/health") and status == 200)
        return True


logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())


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
    app.state.benchmark = Benchmark(classifier)
    logger.info("модель %s загружена за %.1f с, прогрев %.0f мс", classifier.name,
                classifier.load_seconds, classifier.warmup_ms)

    # Telegram-бот включается, только если задан токен; без него веб-API работает как обычно
    client = TelegramClient(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None
    app.state.bot = BotHandler(client, classifier, knowledge, metrics) if client else None
    app.state.telegram_secret = TELEGRAM_WEBHOOK_SECRET
    logger.info("Telegram-бот: %s", "включён (webhook)" if client else "выключен – нет TELEGRAM_BOT_TOKEN")
    yield
    if client:
        await client.close()


app = FastAPI(title="TuranAssist API", lifespan=lifespan)

# запросы разрешены только с dev-сервера Vite, контейнера фронтенда и GitHub Pages
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type"])

# ограничение частоты запросов по IP – защита модели на 0,1 CPU от перегрузки
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.include_router(telegram_router)


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
    text = validated_text(body)
    context = validated_context(body)
    state = request.app.state
    a = answer_question(state.classifier, state.knowledge, state.metrics, text, body.lang, "web", context)
    return ChatResponse(
        recognized=a.recognized, intent=a.intent, title=a.title, confidence=round(a.confidence, 4),
        answer=a.text, source_url=a.source_url, lang=a.lang,
        suggestions=[Suggestion(intent=i, title=t, confidence=round(c, 4)) for i, t, c in a.suggestions],
        timing_ms={k: round(v, 2) for k, v in a.timing_ms.items()}, programs=a.programs,
        context_used=a.context_used,
        context=ChatContext(text=a.context.text, intent=a.context.intent) if a.context else None,
        prices=a.prices,
        explain=explain(state.classifier, a.prediction, text, a.classified_text, a.lang, a.rule, a.programs,
                        a.context_used))


# темы, на которые отвечает бот, по группам – для страницы «О проекте» и стартовых подсказок в чате
@app.get("/api/intents", response_model=list[GroupInfo])
def intents(request: Request) -> list[GroupInfo]:
    kb = request.app.state.knowledge
    return [GroupInfo(id=g["id"], title=g["title"],
                      intents=[IntentInfo(id=i.id, group=i.group, title=i.title)
                               for i in kb.intents.values() if i.group == g["id"]])
            for g in kb.groups]


def check_lang(lang: str) -> None:
    if lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=400, detail={"code": "unsupported_lang",
                                                     "message": f"Язык должен быть одним из: {', '.join(SUPPORTED_LANGS)}"})


# вся база ответов на одном языке – для страницы «База знаний» с поиском по темам и ответам
@app.get("/api/knowledge", response_model=list[KnowledgeItem])
def knowledge_items(request: Request, lang: str = "ru") -> list[KnowledgeItem]:
    check_lang(lang)
    kb = request.app.state.knowledge
    return [KnowledgeItem(id=i.id, group=i.group, title=kb.title(i.id, lang), answer=kb.answer(i.id, lang),
                          source_url=kb.source_url(i.id, lang)) for i in kb.intents.values()]


# справочник цен для калькулятора стоимости: программы, формы обучения, цены (из страницы сайта)
@app.get("/api/tuition")
def tuition(request: Request) -> dict:
    return request.app.state.knowledge.tuition.catalog()


# оценка ответа 👍/👎 из веб-чата: только счётчики, текст вопроса не передаётся и не хранится
@app.post("/api/feedback")
@limiter.limit(FEEDBACK_RATE_LIMIT)
def feedback(request: Request, body: FeedbackRequest) -> dict:
    request.app.state.metrics.record_feedback(body.useful)
    return {"status": "ok"}


# последний нагрузочный тест: живой с его возрастом или сохранённый замер на Render (после пробуждения)
@app.get("/api/benchmark")
def last_benchmark(request: Request) -> dict | None:
    return request.app.state.benchmark.last()


# нагрузочный тест по кнопке: 100 фраз тестового набора подряд через модель. Защита сервера на 0,1 CPU:
# не чаще 2 запросов в минуту с IP, один тест одновременно и общий кулдаун 5 минут на весь сервер –
# во время кулдауна возвращается последний результат (cached), модель не нагружается
@app.post("/api/benchmark")
@limiter.limit(BENCHMARK_RATE_LIMIT)
def benchmark(request: Request) -> dict:
    result = request.app.state.benchmark.run()
    if result is None:
        raise HTTPException(status_code=409, detail={"code": "benchmark_busy", "message": "Тест уже идёт"})
    return result


# ответ по конкретной теме – для кнопок-подсказок «возможно, вы имели в виду» в веб-чате
@app.get("/api/answer/{intent}", response_model=IntentAnswer)
def intent_answer(request: Request, intent: str, lang: str = "ru") -> IntentAnswer:
    kb = request.app.state.knowledge
    if intent not in kb.intents:
        raise HTTPException(status_code=404, detail={"code": "unknown_intent", "message": "Такой темы нет"})
    check_lang(lang)
    title = kb.title(intent, lang)
    # тему выбрали кнопкой, ответ – без классификации; для панели «Как бот понял» модель разбирает название темы
    # (в живые метрики это не попадает – вопроса пользователя не было)
    classifier = request.app.state.classifier
    pred = classifier.predict(title)
    return IntentAnswer(intent=intent, title=title, answer=kb.answer(intent, lang),
                        source_url=kb.source_url(intent, lang), lang=lang,
                        explain=explain(classifier, pred, title, title, lang, "chosen", [], False))


@app.get("/api/model-info")
def model_info(request: Request) -> dict:
    return request.app.state.model_summary


# живые метрики для страницы «Производительность»: задержки p50/p95/p99, нагрузка, память, холодный старт
@app.get("/api/metrics")
def live_metrics(request: Request) -> dict:
    return request.app.state.metrics.snapshot()
