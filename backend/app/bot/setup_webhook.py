import asyncio
import sys

from ..config import PUBLIC_BASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET
from .telegram_api import TelegramClient
from .texts import COMMANDS


# регистрирует webhook и меню команд бота; запускается один раз после деплоя бэкенда
async def main() -> None:
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET and PUBLIC_BASE_URL):
        sys.exit("Нужны TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET и PUBLIC_BASE_URL")
    client = TelegramClient(TELEGRAM_BOT_TOKEN)
    try:
        url = PUBLIC_BASE_URL.rstrip("/") + "/telegram/webhook"
        await client.call("setWebhook", url=url, secret_token=TELEGRAM_WEBHOOK_SECRET,
                          allowed_updates=["message", "callback_query"], drop_pending_updates=True)
        for lang, commands in COMMANDS.items():
            payload = [{"command": c, "description": d} for c, d in commands]
            # русское меню – по умолчанию для всех, казахское и английское – по языку Telegram пользователя
            await client.call("setMyCommands", commands=payload, language_code=None if lang == "ru" else lang)
        info = await client.call("getWebhookInfo")
        print(f"webhook: {info['url']}, ожидают обработки: {info.get('pending_update_count', 0)}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
