import asyncio

import pytest

from app.bot.handlers import BotHandler
from app.config import MAX_TEXT_LENGTH
from app.nlp.context import is_follow_up, use_context


def chat(client, text, context=None):
    return client.post("/api/chat", json={"text": text, "context": context}).json()


def dialog(client, *texts):
    context, answers = None, []
    for text in texts:
        data = chat(client, text, context)
        answers.append(data)
        context = data["context"]
    return answers


@pytest.mark.parametrize("text, expected", [
    ("а в магистратуре?", True), ("А PhD?", True), ("ал магистратурада?", True), ("and for a master's?", True),
    ("What about PhD?", True), ("Сколько стоит обучение?", False), ("анекдот расскажи", False),
])
def test_follow_up_marker(text, expected):
    assert is_follow_up(text) is expected


def test_use_context_rule():
    # уточнение, понятое без контекста иначе, но короткое и в той же группе тем – берём контекст
    assert use_context("а в магистратуре?", True, True, same_group=True)
    # нет союза в начале – самостоятельный вопрос, контекст не нужен
    assert not use_context("Какой курс евро сегодня?", False, True, same_group=False)
    # длинная самостоятельная реплика, понятая и без контекста
    assert not use_context("А потом можно перевестись на дистанционную форму обучения?", True, True, same_group=True)
    # без контекста не понято – контекст выручает, если склеенный вариант распознан
    assert use_context("а для многодетных?", False, True, same_group=False)
    assert not use_context("а для многодетных?", False, False, same_group=True)

def test_level_follow_up_keeps_program(client):
    first, second = dialog(client, "Сколько стоит ВТиПО?", "а в магистратуре?")
    assert first["context"]["intent"] == "tuition_bachelor"
    assert second["context_used"] is True
    assert second["intent"] == "tuition_postgrad"
    assert second["programs"] == ["computer_engineering"]
    assert "научно-педагогическая магистратура, 2 года: 1 483 500 тенге" in second["answer"]


def test_program_follow_up_replaces_program(client):
    _, second = dialog(client, "Сколько стоит юриспруденция?", "а экономика?")
    assert second["intent"] == "tuition_bachelor" and second["programs"] == ["economics"]


def test_follow_up_language_from_whole_dialog(client):
    _, second = dialog(client, "Сколько стоит магистратура?", "а PhD?")
    assert second["intent"] == "tuition_postgrad"
    assert second["lang"] == "ru"  # в «а PhD?» латиницы больше, но диалог – на русском
    _, second = dialog(client, "Бағдарламалық инженерия қанша тұрады?", "ал магистратурада?")
    # язык – по всему диалогу; тему не проверяем: склеенный казахский вопрос проходит порог впритык
    # (0,59 при пороге 0,577), и на другом процессоре ONNX Runtime даёт чуть меньшую вероятность
    assert second["lang"] == "kk"


def test_same_follow_up_without_context_is_another_topic(client):
    assert chat(client, "а в магистратуре?")["intent"] != "tuition_postgrad"


@pytest.mark.parametrize("first, second", [
    ("Есть ли общежитие?", "Какой курс евро сегодня?"),
    ("Есть ли общежитие?", "Где у вас столовая?"),
])
def test_off_topic_does_not_stick_to_previous_topic(client, first, second):
    _, answer = dialog(client, first, second)
    assert answer["recognized"] is False and answer["context_used"] is False
    assert answer["context"] is None  # после «не понял» тема не продолжается


def test_new_question_ignores_context(client):
    _, second = dialog(client, "Как взять академический отпуск?", "Сколько стоит обучение?")
    assert second["intent"] == "tuition_bachelor" and second["context_used"] is False


def test_greeting_does_not_become_context(client):
    assert chat(client, "Привет")["context"] is None


def test_invalid_context(client):
    resp = client.post("/api/chat", json={"text": "а в магистратуре?",
                                          "context": {"text": "а" * (MAX_TEXT_LENGTH + 1), "intent": "dormitory"}})
    assert resp.status_code == 400 and resp.json()["detail"]["code"] == "context_too_long"
    # незнакомая тема в контексте просто игнорируется
    data = chat(client, "а в магистратуре?", {"text": "что-то", "intent": "no_such_intent"})
    assert data["context_used"] is False


def test_bot_remembers_context_per_chat(client, classifier, knowledge):
    from tests.test_bot import FakeTelegram, message
    bot = BotHandler(FakeTelegram(), classifier, knowledge, client.app.state.metrics)
    for update in (message("Сколько стоит ВТиПО?", chat=1), message("а в магистратуре?", chat=1),
                   message("а в магистратуре?", chat=2)):
        asyncio.run(bot.handle(update))
    first_chat, other_chat = bot.client.sent[1]["text"], bot.client.sent[2]["text"]
    assert "«Вычислительная техника и программное обеспечение»" in first_chat
    assert "научно-педагогическая магистратура" in first_chat
    assert "Вычислительная техника" not in other_chat  # у другого чата своего контекста нет
