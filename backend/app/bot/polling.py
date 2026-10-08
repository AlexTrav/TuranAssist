import asyncio
import logging
import sys

from ..config import TELEGRAM_BOT_TOKEN
from ..knowledge import Knowledge
from ..metrics.collector import MetricsCollector
from ..nlp.classifier import IntentClassifier
from .handlers import BotHandler
from .telegram_api import TelegramClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("turanassist.bot")
# httpx на уровне INFO пишет полный URL запроса, а в URL Bot API – токен бота: такие логи отключаем
logging.getLogger("httpx").setLevel(logging.WARNING)


# локальная разработка: бот сам опрашивает Telegram (long polling), публичный адрес не нужен.
# webhook при этом снимается – одновременно Telegram отдаёт обновления только одним способом
async def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        sys.exit("Не задан TELEGRAM_BOT_TOKEN (backend/.env)")
    client = TelegramClient(TELEGRAM_BOT_TOKEN, timeout=40)
    handler = BotHandler(client, IntentClassifier(), Knowledge(), MetricsCollector())
    await client.call("deleteWebhook")
    me = await client.call("getMe")
    logger.info("бот @%s слушает сообщения (long polling), Ctrl+C – остановить", me["username"])
    offset = None
    try:
        while True:
            updates = await client.call("getUpdates", offset=offset, timeout=30,
                                        allowed_updates=["message", "callback_query"])
            for update in updates:
                offset = update["update_id"] + 1
                await handler.handle(update)
    finally:
        await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
