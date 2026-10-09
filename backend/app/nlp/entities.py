import re
from dataclasses import dataclass

# слова до 3 букв («ис», «рэт», «pr», «и», «по») совпадают только целиком – иначе «ис» найдётся в «история»
SHORT_WORD = 3


@dataclass(frozen=True)
class Entity:
    id: str
    start: int
    end: int


def normalize(text: str) -> str:
    text = text.lower().replace("ё", "е")
    return " ".join(re.findall(r"\w+", text))


def alias_pattern(alias: str) -> re.Pattern:
    words = normalize(alias).split()
    parts = [re.escape(w) + (r"\b" if len(w) <= SHORT_WORD else r"\w*") for w in words]
    return re.compile(r"\b" + r" ".join(parts))


# второй NLP-компонент после классификатора интентов: извлечение сущностей по словарю псевдонимов.
# модель отвечает «о чём» вопрос (стоимость обучения), словарь – «про что именно» (ВТиПО, психология)
class EntityExtractor:
    def __init__(self, aliases: dict[str, list[str]]):
        self.patterns = [(entity_id, alias_pattern(a)) for entity_id, items in aliases.items() for a in items]

    # совпадения в нормализованном тексте по порядку; из пересекающихся побеждает самое длинное
    def spans(self, text: str) -> list[Entity]:
        norm = normalize(text)
        found = [Entity(entity_id, m.start(), m.end())
                 for entity_id, pattern in self.patterns for m in pattern.finditer(norm)]
        chosen: list[Entity] = []
        for e in sorted(found, key=lambda e: e.end - e.start, reverse=True):
            if all(e.end <= c.start or e.start >= c.end for c in chosen):
                chosen.append(e)
        return sorted(chosen, key=lambda e: e.start)

    # все найденные сущности в порядке упоминания
    def extract(self, text: str) -> list[str]:
        ids: list[str] = []
        for e in self.spans(text):
            if e.id not in ids:
                ids.append(e.id)
        return ids

    # слова вопроса вне найденных сущностей: в «ВТиПО цена» это «цена»
    def rest(self, text: str) -> list[str]:
        norm = normalize(text)
        for e in reversed(self.spans(text)):
            norm = norm[:e.start] + " " + norm[e.end:]
        return norm.split()
