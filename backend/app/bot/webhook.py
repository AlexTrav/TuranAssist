import hmac

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


# сюда Telegram присылает обновления. Подлинность проверяется секретом, который передан Telegram
# при регистрации webhook (заголовок X-Telegram-Bot-Api-Secret-Token): чужие POST-запросы отклоняются
@router.post("/telegram/webhook", include_in_schema=False)
async def telegram_webhook(request: Request) -> dict:
    bot, secret = request.app.state.bot, request.app.state.telegram_secret
    if bot is None:
        raise HTTPException(status_code=404)
    received = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not secret or not hmac.compare_digest(received, secret):
        raise HTTPException(status_code=403)
    await bot.handle(await request.json())
    return {"ok": True}
