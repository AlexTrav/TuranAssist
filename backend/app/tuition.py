from pathlib import Path

import yaml

from .config import PROGRAMS_PATH, TUITION_PATH
from .nlp.entities import EntityExtractor

MAX_PROGRAMS = 3  # больше трёх программ в одном ответе – уже не ответ, а таблица

# интент -> уровень, цены которого показываем; если по уровню цен нет – показываем другой
TUITION_INTENTS = {"tuition_bachelor": "bachelor", "tuition_postgrad": "postgrad"}

TEXTS = {
    "header": {
        "ru": "Стоимость обучения по программе «{name}» на 2026–2027 учебный год (первый курс, за год):",
        "kk": "«{name}» бағдарламасының 2026–2027 оқу жылына оқу ақысы (бірінші курс, бір жылға):",
        "en": "Tuition for the “{name}” program for the 2026–2027 academic year (first year, per year):",
    },
    "currency": {"ru": "тенге", "kk": "теңге", "en": "tenge"},
    "english": {"ru": "английское отделение", "kk": "ағылшын бөлімі", "en": "English department"},
    "footer": {
        "ru": "Полная таблица – на странице «Стоимость обучения», о скидках – в разделе «Гранты и скидки».",
        "kk": "Толық кесте – «Оқу ақысы» бетінде, жеңілдіктер туралы – «Гранттар мен жеңілдіктер» бөлімінде.",
        "en": "The full table is on the Tuition fee page; discounts are described in the Grants and discounts section.",
    },
}


def format_price(value: int, lang: str) -> str:
    return f"{value:,}".replace(",", "," if lang == "en" else " ")


# цена по конкретной программе: программа извлекается из вопроса, цены – из tuition.yaml,
# который генерируется из страницы сайта «Стоимость обучения» (data/collect/tuition.py)
class Tuition:
    def __init__(self, programs_path: Path = PROGRAMS_PATH, tuition_path: Path = TUITION_PATH):
        programs = yaml.safe_load(programs_path.read_text(encoding="utf-8"))["programs"]
        table = yaml.safe_load(tuition_path.read_text(encoding="utf-8"))
        self.names = {p["id"]: p["name"] for p in programs}
        self.extractor = EntityExtractor({p["id"]: p["aliases"] for p in programs})
        self.plans = {p["id"]: p for p in table["plans"]}
        self.prices: dict[str, list[dict]] = table["prices"]

    def programs_in(self, text: str) -> list[str]:
        return [p for p in self.extractor.extract(text) if self.prices.get(p)][:MAX_PROGRAMS]

    def rows(self, program: str, level: str) -> list[dict]:
        rows = [r for r in self.prices[program] if self.plans[r["plan"]]["level"] == level]
        return rows or self.prices[program]

    def program_answer(self, program: str, level: str, lang: str) -> str:
        currency, lines = TEXTS["currency"][lang], [TEXTS["header"][lang].format(name=self.names[program][lang])]
        for r in self.rows(program, level):
            price = f"{format_price(r['main'], lang)} {currency}"
            if "english" in r:
                price += f" ({TEXTS['english'][lang]} – {format_price(r['english'], lang)})"
            lines.append(f"- {self.plans[r['plan']]['label'][lang]}: {price};")
        lines[-1] = lines[-1][:-1] + "."
        return "\n".join(lines)

    # «ВТиПО сколько стоит»: модель не уверена, потому что делит вероятность между похожими интентами
    # «стоимость бакалавриата» и «стоимость магистратуры». если в вопросе есть программа, с порогом модели
    # сравнивается суммарная вероятность темы «стоимость»; ответ – по более вероятному из двух интентов
    def resolve_intent(self, text: str, top: list[tuple[str, float]], threshold: float) -> tuple[str, float] | None:
        tuition = [(intent, conf) for intent, conf in top if intent in TUITION_INTENTS]
        mass = sum(conf for _, conf in tuition)
        if not tuition or mass < threshold or not self.programs_in(text):
            return None
        return tuition[0][0], mass

    # ответ на вопрос о стоимости с конкретными программами или None, если программ в вопросе нет
    def answer(self, intent: str, text: str, lang: str) -> tuple[str, list[str]] | None:
        level = TUITION_INTENTS.get(intent)
        programs = self.programs_in(text) if level else []
        if not programs:
            return None
        blocks = [self.program_answer(p, level, lang) for p in programs]
        return "\n\n".join(blocks + [TEXTS["footer"][lang]]), programs
