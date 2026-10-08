import json
import sys

import yaml

from .config import CORPUS_DIR, DATA_DIR
from .tuition import PROGRAMS_PATH, TUITION_PATH
from .tuition import render as render_tuition

KNOWLEDGE_DIR = DATA_DIR / "knowledge"
LOCALES = ("ru", "kk", "en")
EM_DASH = "\u2014"


# проверяет базу ответов: структуру, полноту переводов и ссылки на источники в корпусе
def check() -> list[str]:
    errors: list[str] = []
    manifest = json.loads((CORPUS_DIR / "manifest.json").read_text(encoding="utf-8"))
    known_sources = {r["id"] for r in manifest if "file" in r}

    groups = yaml.safe_load((KNOWLEDGE_DIR / "groups.yaml").read_text(encoding="utf-8"))["groups"]
    group_ids = {g["id"] for g in groups}
    for g in groups:
        if set(g["title"]) != set(LOCALES):
            errors.append(f"группа {g['id']}: нет названия на всех языках")

    seen: set[str] = set()
    for path in sorted((KNOWLEDGE_DIR / "intents").glob("*.yaml")):
        raw = path.read_text(encoding="utf-8")
        if EM_DASH in raw:
            errors.append(f"{path.name}: длинное тире")
        data = yaml.safe_load(raw)
        if data["group"] not in group_ids:
            errors.append(f"{path.name}: неизвестная группа {data['group']}")
        for intent in data["intents"]:
            iid = intent["id"]
            if iid in seen:
                errors.append(f"{iid}: повторяющийся id")
            seen.add(iid)
            # ключи – ровно ru/kk/en, значения – непустые строки: запятая в YAML-словаре в одну строку
            # без кавычек незаметно разбивает значение на лишние ключи
            for field in ("title", "answer"):
                value = intent.get(field) or {}
                if set(value) != set(LOCALES):
                    errors.append(f"{iid}: в {field} ключи {sorted(value)} вместо {list(LOCALES)}")
                for locale in LOCALES:
                    if not isinstance(value.get(locale), str) or not value[locale].strip():
                        errors.append(f"{iid}: нет {field}.{locale}")
            for source in intent.get("sources", []):
                if source not in known_sources:
                    errors.append(f"{iid}: источник {source} не найден в корпусе")
    print(f"групп: {len(groups)}, интентов: {len(seen)}")
    return errors + check_programs()


# справочник программ для цены по программе и сгенерированная из сайта таблица цен
def check_programs() -> list[str]:
    errors: list[str] = []
    raw = PROGRAMS_PATH.read_text(encoding="utf-8")
    if EM_DASH in raw:
        errors.append("programs.yaml: длинное тире")
    programs = yaml.safe_load(raw)["programs"]
    ids = [p["id"] for p in programs]
    errors += [f"программа {pid}: повторяющийся id" for pid in {i for i in ids if ids.count(i) > 1}]
    for p in programs:
        if set(p["name"]) != set(LOCALES) or not all(isinstance(v, str) and v for v in p["name"].values()):
            errors.append(f"программа {p['id']}: название не на всех языках")
        if not p.get("aliases"):
            errors.append(f"программа {p['id']}: нет псевдонимов")
    expected, problems = render_tuition()
    errors += problems
    if not TUITION_PATH.exists() or TUITION_PATH.read_text(encoding="utf-8") != expected:
        errors.append("tuition.yaml устарел – запустить make tuition")
    print(f"программ: {len(programs)}")
    return errors


if __name__ == "__main__":
    problems = check()
    for p in problems:
        print("  !", p)
    print("ошибок:", len(problems))
    sys.exit(1 if problems else 0)
