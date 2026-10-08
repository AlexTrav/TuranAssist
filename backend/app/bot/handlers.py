import logging
import time
from collections import OrderedDict, deque

from starlette.concurrency import run_in_threadpool

from ..config import BOT_RATE_LIMIT_PER_MINUTE, MAX_TEXT_LENGTH, SUPPORTED_LANGS
from ..knowledge import Knowledge
from ..metrics.collector import MetricsCollector
from ..nlp.context import Context
from ..nlp.classifier import IntentClassifier
from ..service import answer_question
from . import texts
from .telegram_api import TelegramClient, TelegramError

logger = logging.getLogger("turanassist.bot")

MAX_CHATS = 10_000  # сколько чатов помнить (язык, лимит) – защита памяти от бесконечного роста
CONTEXT_TTL_SEC = 600  # уточнение «а в магистратуре?» через 10 минут после вопроса – уже новый разговор


# обработчик обновлений Telegram – общий для webhook (продакшн) и long polling (локальная разработка)
class BotHandler:
    def __init__(self, client: TelegramClient, classifier: IntentClassifier, knowledge: Knowledge,
                 metrics: MetricsCollector):
        self.client, self.classifier, self.knowledge, self.metrics = client, classifier, knowledge, metrics
        # выбранный через /lang язык и время последних сообщений чата; хранятся в памяти до перезапуска
        self.langs: OrderedDict[int, str] = OrderedDict()
        self.recent: OrderedDict[int, deque] = OrderedDict()
        self.warned: set[int] = set()
        # тема последнего ответа для уточнений: (контекст, время) – только в памяти, в лог не пишется
        self.contexts: OrderedDict[int, tuple[Context, float]] = OrderedDict()

    @staticmethod
    def _remember(store: OrderedDict, key: int, value) -> None:
        store[key] = value
        store.move_to_end(key)
        if len(store) > MAX_CHATS:
            store.popitem(last=False)

    # язык интерфейса: выбранный через /lang, иначе язык Telegram пользователя, иначе русский
    def _ui_lang(self, chat_id: int, user: dict | None) -> str:
        if chat_id in self.langs:
            return self.langs[chat_id]
        code = ((user or {}).get("language_code") or "")[:2]
        return code if code in SUPPORTED_LANGS else "ru"

    # не больше BOT_RATE_LIMIT_PER_MINUTE сообщений в минуту на чат: Telegram присылает запросы со своих IP,
    # поэтому лимит по IP (slowapi) здесь не работает – считаем по идентификатору чата
    def _rate_limited(self, chat_id: int) -> bool:
        now = time.monotonic()
        window = self.recent.get(chat_id) or deque()
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= BOT_RATE_LIMIT_PER_MINUTE:
            return True
        window.append(now)
        self._remember(self.recent, chat_id, window)
        self.warned.discard(chat_id)
        return False

    def _context(self, chat_id: int) -> Context | None:
        context, at = self.contexts.get(chat_id, (None, 0.0))
        return context if context and time.monotonic() - at <= CONTEXT_TTL_SEC else None

    def _set_context(self, chat_id: int, context: Context | None) -> None:
        if context:
            self._remember(self.contexts, chat_id, (context, time.monotonic()))
        else:
            self.contexts.pop(chat_id, None)

    def _topics_buttons(self, lang: str) -> list[list[tuple[str, str]]]:
        return [[(g["title"][lang], f"group:{g['id']}")] for g in self.knowledge.groups if g["id"] != "service"]

    def _with_link(self, text: str, url: str | None, lang: str) -> str:
        return f"{text}\n\n{texts.MORE[lang]}: {url}" if url else text

    async def handle(self, update: dict) -> None:
        try:
            if "callback_query" in update:
                await self._on_callback(update["callback_query"])
            elif "message" in update:
                await self._on_message(update["message"])
        except TelegramError as exc:  # например, пользователь заблокировал бота – не повод падать
            logger.warning("telegram: %s", exc)

    async def _on_message(self, msg: dict) -> None:
        chat_id = msg["chat"]["id"]
        lang = self._ui_lang(chat_id, msg.get("from"))
        if self._rate_limited(chat_id):
            if chat_id not in self.warned:  # предупреждаем один раз, дальше молча игнорируем
                self.warned.add(chat_id)
                await self.client.send_message(chat_id, texts.RATE_LIMITED[lang])
            return
        text = msg.get("text")
        if text is None:
            await self.client.send_message(chat_id, texts.NOT_TEXT[lang])
        elif text.startswith("/"):
            await self._on_command(chat_id, text.split()[0].split("@")[0][1:].lower(), lang)
        else:
            await self._on_question(chat_id, text)

    async def _on_command(self, chat_id: int, command: str, lang: str) -> None:
        if command == "start":
            await self.client.send_message(chat_id, texts.START[lang])
        elif command == "lang":
            # по умолчанию бот отвечает на языке вопроса; язык можно и закрепить явно
            buttons = [[(texts.AUTO_BUTTON[lang], "lang:auto")],
                       [(name, f"lang:{code}") for code, name in texts.LANG_BUTTONS]]
            await self.client.send_message(chat_id, texts.CHOOSE_LANG[lang], buttons)
        elif command == "topics":
            await self.client.send_message(chat_id, texts.TOPICS[lang], self._topics_buttons(lang))
        else:  # /help и неизвестные команды
            await self.client.send_message(chat_id, texts.HELP[lang])

    async def _on_question(self, chat_id: int, text: str) -> None:
        text = " ".join(text.split())
        pref = self.langs.get(chat_id)
        if len(text) > MAX_TEXT_LENGTH:
            await self.client.send_message(chat_id, texts.TOO_LONG[pref or "ru"])
            return
        # расчёт модели – в пуле потоков, чтобы не блокировать цикл событий
        a = await run_in_threadpool(answer_question, self.classifier, self.knowledge, self.metrics, text, pref,
                                    "telegram", self._context(chat_id))
        self._set_context(chat_id, a.context)
        if a.recognized:
            await self.client.send_message(chat_id, self._with_link(a.text, a.source_url, a.lang))
        else:
            buttons = [[(title, f"intent:{intent}")] for intent, title, _ in a.suggestions]
            await self.client.send_message(chat_id, a.text, buttons)

    async def _on_callback(self, cq: dict) -> None:
        await self.client.answer_callback(cq["id"])  # убирает «часики» на нажатой кнопке
        chat_id = cq["message"]["chat"]["id"]
        kind, _, value = (cq.get("data") or "").partition(":")
        if kind == "lang" and value in SUPPORTED_LANGS:
            self._remember(self.langs, chat_id, value)
            await self.client.send_message(chat_id, texts.LANG_SET[value])
            return
        if kind == "lang" and value == "auto":
            self.langs.pop(chat_id, None)
            await self.client.send_message(chat_id, texts.LANG_AUTO[self._ui_lang(chat_id, cq.get("from"))])
            return
        lang = self._ui_lang(chat_id, cq.get("from"))
        if kind == "topics":
            await self.client.send_message(chat_id, texts.TOPICS[lang], self._topics_buttons(lang))
        elif kind == "group" and any(g["id"] == value for g in self.knowledge.groups):
            buttons = [[(i.title[lang], f"intent:{i.id}")] for i in self.knowledge.intents.values() if i.group == value]
            buttons.append([(texts.BACK[lang], "topics:")])
            group_title = next(g["title"][lang] for g in self.knowledge.groups if g["id"] == value)
            await self.client.send_message(chat_id, group_title, buttons)
        elif kind == "intent" and value in self.knowledge.intents:
            # выбранная кнопкой тема – тоже контекст: после «Стоимость бакалавриата» можно спросить «а ВТиПО?»
            self._set_context(chat_id, Context(self.knowledge.title(value, lang), value))
            answer = self._with_link(self.knowledge.answer(value, lang), self.knowledge.source_url(value, lang), lang)
            await self.client.send_message(chat_id, answer)
