import re
import sys

import yaml

from .config import CORPUS_DIR, DATA_DIR

KNOWLEDGE_DIR = DATA_DIR / "knowledge"
TABLE_PATH = CORPUS_DIR / "site" / "ru" / "tuition-fee.md"  # русская версия – эталон: в английской есть опечатки
PROGRAMS_PATH = KNOWLEDGE_DIR / "programs.yaml"
TUITION_PATH = KNOWLEDGE_DIR / "tuition.yaml"

HEADER = ("# сгенерировано из corpus/site/ru/tuition-fee.md: python -m collect.tuition (make tuition)\n"
          "# руками не править – после пересбора корпуса запустить генерацию заново\n")

# формы обучения: заголовок раздела таблицы на сайте -> id, уровень и подпись строки ответа на трёх языках.
# разделы MBA и DBA не разбираются – их цены одни на программу и уже есть в общем ответе
PLANS = [
    ("Очная (4 года обучения)", "bachelor_4y", "bachelor",
     {"ru": "очная, 4 года", "kk": "күндізгі, 4 жыл", "en": "full-time, 4 years"}),
    ("Очная, после среднего общего образования (3 года обучения)", "bachelor_school_3y", "bachelor",
     {"ru": "очная после школы, 3 года", "kk": "мектептен кейін күндізгі, 3 жыл",
      "en": "full-time after school, 3 years"}),
    ("Очная сокращенная после колледжа (3 года обучения)", "bachelor_college_3y", "bachelor",
     {"ru": "после колледжа, 3 года", "kk": "колледжден кейін, 3 жыл", "en": "after college, 3 years"}),
    ("Очная сокращенная после колледжа (2 года обучения)", "bachelor_college_2y", "bachelor",
     {"ru": "после колледжа, 2 года", "kk": "колледжден кейін, 2 жыл", "en": "after college, 2 years"}),
    ("Очная форма с сокращенным сроком обучения (с применением дистанционного обучения) после колледжа (3 г.о.)",
     "bachelor_distance_college_3y", "bachelor",
     {"ru": "с дистанционными технологиями после колледжа, 3 года",
      "kk": "колледжден кейін қашықтан оқыту технологияларымен, 3 жыл",
      "en": "with distance technologies after college, 3 years"}),
    ("Очная форма с сокращенным сроком обучения (с применением дистанционного обучения) после колледжа (2 г.о.)",
     "bachelor_distance_college_2y", "bachelor",
     {"ru": "с дистанционными технологиями после колледжа, 2 года",
      "kk": "колледжден кейін қашықтан оқыту технологияларымен, 2 жыл",
      "en": "with distance technologies after college, 2 years"}),
    ("Очная форма с сокращенным сроком обучения (с применением дистанционного обучения) после ВУЗа (2 г.о. / 3 г.о.)",
     "bachelor_distance_university", "bachelor",
     {"ru": "с дистанционными технологиями после вуза", "kk": "ЖОО-дан кейін қашықтан оқыту технологияларымен",
      "en": "with distance technologies after a university degree"}),
    ("Научно-педагогическое направление (2 года)", "master_research_2y", "postgrad",
     {"ru": "научно-педагогическая магистратура, 2 года", "kk": "ғылыми-педагогикалық магистратура, 2 жыл",
      "en": "research and teaching master's, 2 years"}),
    ("Профильное направление (1 год)", "master_professional_1y", "postgrad",
     {"ru": "профильная магистратура, 1 год", "kk": "бейіндік магистратура, 1 жыл",
      "en": "professional master's, 1 year"}),
    ("Докторантура", "phd", "postgrad", {"ru": "докторантура PhD", "kk": "PhD докторантурасы", "en": "PhD"}),
]


def parse_price(cell: str) -> int | None:
    digits = re.sub(r"\D", "", cell)
    return int(digits) if digits else None


# таблица сайта + справочник программ -> цены по программам и формам обучения; ошибки – вместо молчаливых пропусков
def build_tuition(table_md: str, programs: list[dict]) -> tuple[dict, list[str]]:
    errors: list[str] = []
    by_name = {name: p["id"] for p in programs for name in [p["name"]["ru"], *p.get("table_names", [])]}
    plan_by_heading = {heading: plan_id for heading, plan_id, _, _ in PLANS}
    prices: dict[str, list[dict]] = {p["id"]: [] for p in programs}
    seen_plans: set[str] = set()
    plan = None
    for line in table_md.splitlines():
        if line.startswith("### "):
            plan = plan_by_heading.get(line[4:].strip())
        elif plan and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            main, english = (parse_price(c) for c in (cells[1:] + [""])[:2])
            if main is None and english is None:  # строка заголовка или программы нет в этой форме обучения
                continue
            if cells[0] not in by_name:
                errors.append(f"программа «{cells[0]}» из таблицы не описана в programs.yaml")
                continue
            if main is None:  # бэкенд считает основной ценой казахское/русское отделение
                errors.append(f"программа «{cells[0]}»: есть только цена английского отделения")
                continue
            row = {"plan": plan, "main": main}
            if english is not None:
                row["english"] = english
            prices[by_name[cells[0]]].append(row)
            seen_plans.add(plan)
    errors += [f"раздел «{heading}» не найден в таблице" for heading, plan_id, _, _ in PLANS
               if plan_id not in seen_plans]
    errors += [f"у программы {pid} нет ни одной цены" for pid, rows in prices.items() if not rows]
    collected = re.search(r"Дата сбора: (\S+)", table_md)
    data = {
        "source": {"page": "tuition-fee", "collected": collected.group(1) if collected else None},
        "plans": [{"id": plan_id, "level": level, "label": label} for _, plan_id, level, label in PLANS],
        "prices": prices,
    }
    return data, errors


def render() -> tuple[str, list[str]]:
    programs = yaml.safe_load(PROGRAMS_PATH.read_text(encoding="utf-8"))["programs"]
    data, errors = build_tuition(TABLE_PATH.read_text(encoding="utf-8"), programs)
    body = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=None, width=200)
    return HEADER + body, errors


if __name__ == "__main__":
    text, problems = render()
    for p in problems:
        print("  !", p)
    if problems:
        sys.exit(1)
    TUITION_PATH.write_text(text, encoding="utf-8")
    print(f"записано: {TUITION_PATH.relative_to(DATA_DIR)}")
