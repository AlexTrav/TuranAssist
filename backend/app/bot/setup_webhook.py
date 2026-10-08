import asyncio
import sys

from ..config import PUBLIC_BASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET
from .setup_profile import apply_commands
from .telegram_api import TelegramClient


# регистрирует webhook и меню команд бота; запускается один раз после деплоя бэкенда
async def main() -> None:
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET and PUBLIC_BASE_URL):
        sys.exit("Нужны TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET и PUBLIC_BASE_URL")
    client = TelegramClient(TELEGRAM_BOT_TOKEN)
    try:
        url = PUBLIC_BASE_URL.rstrip("/") + "/telegram/webhook"
        await client.call("setWebhook", url=url, secret_token=TELEGRAM_WEBHOOK_SECRET,
                          allowed_updates=["message", "callback_query"], drop_pending_updates=True)
        await apply_commands(client)
        info = await client.call("getWebhookInfo")
        print(f"webhook: {info['url']}, ожидают обработки: {info.get('pending_update_count', 0)}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
