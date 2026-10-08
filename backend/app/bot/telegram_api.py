import httpx

API_URL = "https://api.telegram.org/bot{token}/{method}"


class TelegramError(RuntimeError):
    pass


# тонкий асинхронный клиент Telegram Bot API: только нужные боту методы, без тяжёлых фреймворков.
# токен живёт только в URL запросов и нигде не логируется
class TelegramClient:
    def __init__(self, token: str, timeout: float = 30):
        self._token = token
        self._http = httpx.AsyncClient(timeout=timeout)

    async def call(self, method: str, **params) -> dict | list | bool:
        resp = await self._http.post(API_URL.format(token=self._token, method=method),
                                     json={k: v for k, v in params.items() if v is not None})
        data = resp.json()
        if not data.get("ok"):
            # описание ошибки от Telegram без URL запроса – в URL токен
            raise TelegramError(f"{method}: {data.get('error_code')} {data.get('description')}")
        return data["result"]

    async def send_message(self, chat_id: int, text: str, buttons: list[list[tuple[str, str]]] | None = None) -> None:
        markup = None
        if buttons:
            markup = {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in row] for row in buttons]}
        await self.call("sendMessage", chat_id=chat_id, text=text, reply_markup=markup,
                        link_preview_options={"is_disabled": True})

    async def answer_callback(self, callback_id: str) -> None:
        await self.call("answerCallbackQuery", callback_query_id=callback_id)

    async def close(self) -> None:
        await self._http.aclose()
