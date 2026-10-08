import asyncio

import pytest

from app.bot import texts
from app.bot.handlers import BotHandler
from app.config import BOT_RATE_LIMIT_PER_MINUTE
from app.knowledge import FALLBACK


# подменяет Telegram Bot API: запоминает отправленные сообщения вместо сетевых запросов
class FakeTelegram:
    def __init__(self):
        self.sent, self.callbacks = [], []

    async def send_message(self, chat_id, text, buttons=None):
        self.sent.append({"chat_id": chat_id, "text": text, "buttons": buttons or []})

    async def answer_callback(self, callback_id):
        self.callbacks.append(callback_id)


@pytest.fixture
def bot(client, classifier, knowledge):
    return BotHandler(FakeTelegram(), classifier, knowledge, client.app.state.metrics)


def message(text, chat=1, lang="ru"):
    return {"update_id": 1, "message": {"chat": {"id": chat}, "from": {"language_code": lang}, "text": text}}


def callback(data, chat=1):
    return {"update_id": 2, "callback_query": {"id": "cb-1", "data": data, "message": {"chat": {"id": chat}},
                                               "from": {"language_code": "ru"}}}


def handle(bot, *updates):
    for u in updates:
        asyncio.run(bot.handle(u))
    return bot.client.sent


def test_start_uses_telegram_language_without_forcing_answer_language(bot):
    sent = handle(bot, message("/start", lang="kk"))
    assert sent[-1]["text"] == texts.START["kk"] and sent[-1]["buttons"] == []


def test_lang_menu_offers_auto_and_three_languages(bot):
    buttons = handle(bot, message("/lang"))[-1]["buttons"]
    assert [d for row in buttons for _, d in row] == ["lang:auto", "lang:ru", "lang:kk", "lang:en"]


def test_auto_language_returns_to_question_language(bot, knowledge):
    handle(bot, callback("lang:ru"), callback("lang:auto"))
    assert bot.client.sent[-1]["text"] == texts.LANG_AUTO["ru"]
    text = handle(bot, message("Жатақхана бар ма?"))[-1]["text"]
    assert text.startswith(knowledge.answer("dormitory", "kk"))


def test_question_answer_has_source_link(bot, knowledge):
    text = handle(bot, message("Есть ли общежитие?"))[-1]["text"]
    assert text.startswith(knowledge.answer("dormitory", "ru"))
    assert "Подробнее: https://turan.edu.kz/ru/" in text


def test_kazakh_question_gets_kazakh_answer(bot, knowledge):
    text = handle(bot, message("Жатақхана бар ма?"))[-1]["text"]
    assert text.startswith(knowledge.answer("dormitory", "kk"))


def test_unknown_question_offers_topic_buttons(bot):
    sent = handle(bot, message("фывапролдж йцукен"))[-1]
    assert sent["text"] == FALLBACK["ru"]
    assert len(sent["buttons"]) == 3 and all(d.startswith("intent:") for row in sent["buttons"] for _, d in row)


def test_suggestion_button_returns_answer(bot, knowledge):
    sent = handle(bot, callback("intent:dormitory"))
    assert bot.client.callbacks == ["cb-1"]
    assert sent[-1]["text"].startswith(knowledge.answer("dormitory", "ru"))


def test_language_choice_overrides_question_language(bot, knowledge):
    handle(bot, callback("lang:en"))
    assert bot.client.sent[-1]["text"] == texts.LANG_SET["en"]
    text = handle(bot, message("Есть ли общежитие?"))[-1]["text"]
    assert text.startswith(knowledge.answer("dormitory", "en"))


def test_topics_menu_leads_to_intents(bot):
    groups = handle(bot, message("/topics"))[-1]["buttons"]
    assert len(groups) == 7  # все группы, кроме служебной «Общение»
    intents = handle(bot, callback("group:payment"))[-1]["buttons"]
    assert [d for row in intents for _, d in row] == ["intent:tuition_bachelor", "intent:tuition_postgrad",
                                                      "intent:payment_details", "topics:"]


def test_non_text_message(bot):
    update = {"update_id": 3, "message": {"chat": {"id": 1}, "from": {"language_code": "en"}, "sticker": {}}}
    assert handle(bot, update)[-1]["text"] == texts.NOT_TEXT["en"]


def test_rate_limit_per_chat_warns_once(bot):
    handle(bot, *[message("привет", chat=7)] * BOT_RATE_LIMIT_PER_MINUTE)
    before = len(bot.client.sent)
    handle(bot, message("привет", chat=7), message("привет", chat=7))
    assert [m["text"] for m in bot.client.sent[before:]] == [texts.RATE_LIMITED["ru"]]
    assert handle(bot, message("привет", chat=8))[-1]["chat_id"] == 8  # другой чат не затронут


def test_webhook_checks_secret(client, bot, monkeypatch):
    monkeypatch.setattr(client.app.state, "bot", bot)
    monkeypatch.setattr(client.app.state, "telegram_secret", "test-secret")
    update = message("Есть ли общежитие?")
    assert client.post("/telegram/webhook", json=update).status_code == 403
    assert client.post("/telegram/webhook", json=update,
                       headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"}).status_code == 403
    resp = client.post("/telegram/webhook", json=update, headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"})
    assert resp.status_code == 200 and len(bot.client.sent) == 1


def test_webhook_disabled_without_token(client, monkeypatch):
    monkeypatch.setattr(client.app.state, "bot", None)
    assert client.post("/telegram/webhook", json={}).status_code == 404


def test_token_does_not_leak_into_logs(client):
    # httpx логирует полный URL запроса, а в URL Bot API зашит токен – его логи должны быть выключены
    import logging
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
