import os
from pathlib import Path

# корень репозитория: backend/app/config.py -> app -> backend -> корень (в Docker это /app)
ROOT = Path(os.environ.get("APP_ROOT", Path(__file__).resolve().parents[2]))

KNOWLEDGE_DIR = ROOT / "data" / "knowledge"
MANIFEST_PATH = ROOT / "data" / "corpus" / "manifest.json"
# справочник программ и цены по ним (генерируются из страницы сайта) – для ответа «Сколько стоит ВТиПО?»
PROGRAMS_PATH = KNOWLEDGE_DIR / "programs.yaml"
TUITION_PATH = KNOWLEDGE_DIR / "tuition.yaml"
PRODUCTION_INFO_PATH = ROOT / "model" / "artifacts" / "production" / "model_info.json"
ENSEMBLE_METRICS_PATH = ROOT / "model" / "reports" / "ensemble" / "metrics.json"

# энкодер e5 и модель токенизатора скачиваются с Hugging Face при сборке образа – в git они не помещаются.
# коммиты зафиксированы: образ воспроизводим, даже если модели на HF обновят; SHA-256 проверяется
MODEL_CACHE_DIR = Path(os.environ.get("MODEL_CACHE_DIR", ROOT / "model" / ".cache" / "production"))
ENCODER_FILE = "encoder_int8_full.onnx"
# токенизатор – исходная модель SentencePiece от e5: в памяти ~20 МБ против ~280 МБ у tokenizer.json
TOKENIZER_FILE = "sentencepiece.bpe.model"
MODEL_FILES = {
    ENCODER_FILE: {
        "repo": "AlexCode2003/turanassist-intent-e5", "revision": "00d4d9e0dc62bdfea5b3c8f97add0a0c20c16565",
        "path": "v2/encoder_int8_full.onnx",
        "sha256": "7a0e292f503a41525ecc675f40f0cd597c272fd6f98d8dc10a932ab21a92ce27",
    },
    TOKENIZER_FILE: {
        "repo": "intfloat/multilingual-e5-small", "revision": "614241f622f53c4eeff9890bdc4f31cfecc418b3",
        "path": "sentencepiece.bpe.model",
        "sha256": "cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865",
    },
}

# бесплатный Render даёт 0,1 CPU – больше одного потока ONNX Runtime только мешает
ONNX_THREADS = int(os.environ.get("ONNX_THREADS", "1"))

MAX_TEXT_LENGTH = 500  # вопрос длиннее – почти наверняка не вопрос, а вставленный текст
SUPPORTED_LANGS = ("ru", "kk", "en")
SUGGESTIONS_COUNT = 3
LATENCY_WINDOW = 1000  # сколько последних запросов учитывать в p50/p95/p99
# цель по задержке (SLA) для чата: на 0,1 CPU бесплатного Render ответ модели – десятки миллисекунд
SLA_TARGET_MS = 100
# границы корзин гистограммы задержек, мс (последняя корзина – всё, что дольше)
HISTOGRAM_BUCKETS_MS = (5, 10, 15, 20, 30, 50, 75, 100, 150, 250, 500)

# нагрузочный тест по кнопке: модель прогоняет фразы тестового набора подряд, вне живых метрик
BENCHMARK_PHRASES_DIR = ROOT / "data" / "phrases" / "test"
BENCHMARK_SIZE = 100
BENCHMARK_RATE_LIMIT = "2/minute"
# общий кулдаун на весь сервер: тест (~6 с на 0,1 CPU) не чаще раза в 5 минут – около 2% процессорного времени
BENCHMARK_COOLDOWN_SECONDS = 300
# сохранённый замер на Render – показывается, пока после пробуждения сервера живого теста ещё не было
BENCHMARK_REFERENCE_PATH = ROOT / "research" / "results" / "render_latency.json"
FEEDBACK_RATE_LIMIT = "30/minute"

CHAT_RATE_LIMIT = "30/minute"
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "https://alextrav.github.io",
]

# Telegram-бот: токен и секрет webhook – только из переменных окружения (локально .env, на Render – секреты);
# без токена бот выключен, веб-API работает как обычно
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "")  # адрес бэкенда для регистрации webhook
BOT_RATE_LIMIT_PER_MINUTE = 20  # сообщений в минуту на один чат
