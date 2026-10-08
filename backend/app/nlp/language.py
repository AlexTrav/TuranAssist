import re

KAZAKH_LETTERS_RE = re.compile(r"[әғқңөұүһі]", re.IGNORECASE)
CYRILLIC_RE = re.compile(r"[а-яё]", re.IGNORECASE)
LATIN_RE = re.compile(r"[a-z]", re.IGNORECASE)


# язык ответа по тексту вопроса: казахские буквы – kk, латиница без кириллицы – en, иначе ru.
# транслит («skolko stoit») распознаётся как en – ответ всё равно понятен, а в вебе язык задаёт интерфейс
def detect_language(text: str) -> str:
    if KAZAKH_LETTERS_RE.search(text):
        return "kk"
    latin, cyrillic = len(LATIN_RE.findall(text)), len(CYRILLIC_RE.findall(text))
    if latin > cyrillic:
        return "en"
    return "ru"
