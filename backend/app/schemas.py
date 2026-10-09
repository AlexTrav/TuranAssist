from pydantic import BaseModel


# тело запроса без ограничений pydantic: длину и язык проверяем вручную внутри эндпоинта,
# иначе невалидные запросы отклонялись бы до slowapi и не попадали в счётчик rate limit
class ChatContext(BaseModel):
    text: str
    intent: str


class ChatRequest(BaseModel):
    text: str
    lang: str | None = None  # язык ответа; не задан – определяется по тексту вопроса
    # контекст из предыдущего ответа сервера – клиент возвращает его как есть; сервер ничего не хранит
    context: ChatContext | None = None


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
    programs: list[str] = []  # образовательные программы, извлечённые из вопроса о стоимости
    context_used: bool = False  # вопрос понят как уточнение предыдущего
    clarify: bool = False  # короткий запрос на несколько тем: бот просит выбрать тему из suggestions
    context: ChatContext | None = None  # прислать в следующем запросе; None – тема не продолжается
    prices: list[dict] = []  # цены найденных программ по формам обучения – таблица в веб-чате
    explain: dict | None = None  # разбор вопроса по ступеням конвейера – панель «Как бот понял»


class IntentInfo(BaseModel):
    id: str
    group: str
    title: dict[str, str]


class GroupInfo(BaseModel):
    id: str
    title: dict[str, str]
    intents: list[IntentInfo]


class IntentAnswer(BaseModel):
    intent: str
    title: str
    answer: str
    source_url: str | None
    lang: str
    explain: dict | None = None  # разбор названия темы для панели «Как бот понял» (rule = chosen)


class FeedbackRequest(BaseModel):
    intent: str | None = None  # тема оценённого ответа (None – ответ «не понял»)
    useful: bool


class KnowledgeItem(BaseModel):
    id: str
    group: str
    title: str
    answer: str
    source_url: str | None
