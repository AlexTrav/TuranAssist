from pydantic import BaseModel


# тело запроса без ограничений pydantic: длину и язык проверяем вручную внутри эндпоинта,
# иначе невалидные запросы отклонялись бы до slowapi и не попадали в счётчик rate limit
class ChatRequest(BaseModel):
    text: str
    lang: str | None = None  # язык ответа; не задан – определяется по тексту вопроса


class Suggestion(BaseModel):
    intent: str
    title: str
    confidence: float


class ChatResponse(BaseModel):
    recognized: bool
    intent: str | None  # None, если уверенность ниже порога
    title: str | None
    confidence: float
    answer: str
    source_url: str | None
    suggestions: list[Suggestion]
    lang: str
    timing_ms: dict[str, float]


class IntentInfo(BaseModel):
    id: str
    group: str
    title: dict[str, str]


class GroupInfo(BaseModel):
    id: str
    title: dict[str, str]
    intents: list[IntentInfo]
