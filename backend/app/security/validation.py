from fastapi import HTTPException

from ..config import MAX_TEXT_LENGTH, SUPPORTED_LANGS
from ..nlp.context import Context
from ..schemas import ChatRequest


def _error(code: str, message: str) -> HTTPException:
    return HTTPException(status_code=400, detail={"code": code, "message": message})


# проверка вопроса. ВАЖНО: вызывается вручную внутри тела эндпоинта, а не через Depends() –
# slowapi считает лимит на вызове функции-эндпоинта, и запрос, отклонённый в Depends(), в счётчик
# не попал бы: перебором невалидных запросов можно было бы обойти rate limit
def validated_text(body: ChatRequest) -> str:
    text = " ".join(body.text.split())  # схлопываем переводы строк и повторяющиеся пробелы
    if not text:
        raise _error("empty_text", "Вопрос пустой")
    if len(text) > MAX_TEXT_LENGTH:
        raise _error("text_too_long", f"Вопрос слишком длинный (максимум {MAX_TEXT_LENGTH} символов)")
    if body.lang is not None and body.lang not in SUPPORTED_LANGS:
        raise _error("unsupported_lang", f"Язык должен быть одним из: {', '.join(SUPPORTED_LANGS)}")
    return text

# контекст приходит от клиента: тот же лимит длины, что и у вопроса; пустой – как будто его нет.
# незнакомый интент отбросит сервис – подделать можно только контекст собственного диалога
def validated_context(body: ChatRequest) -> Context | None:
    if body.context is None:
        return None
    text = " ".join(body.context.text.split())
    if len(text) > MAX_TEXT_LENGTH:
        raise _error("context_too_long", f"Контекст слишком длинный (максимум {MAX_TEXT_LENGTH} символов)")
    return Context(text, body.context.intent) if text else None
