import csv
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

from .check_knowledge import EM_DASH, KNOWLEDGE_DIR
from .config import DATA_DIR

PHRASES_DIR = DATA_DIR / "phrases"
MIN_TRAIN_PER_INTENT = 15
MIN_TEST_PER_INTENT = 4


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_dir(name: str) -> list[dict]:
    return [row for path in sorted((PHRASES_DIR / name).glob("*.csv")) for row in read_csv(path)]


# сравниваем фразы без регистра, пунктуации и лишних пробелов – так ловятся почти-дубли
def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()


def known_intents() -> set[str]:
    ids = set()
    for path in (KNOWLEDGE_DIR / "intents").glob("*.yaml"):
        ids |= {i["id"] for i in yaml.safe_load(path.read_text(encoding="utf-8"))["intents"]}
    return ids


# проверяет наборы фраз: интенты из базы, отсутствие дублей и пересечений между выборками
def check() -> list[str]:
    errors: list[str] = []
    intents = known_intents()
    train, test = read_dir("train"), read_dir("test")
    ood = read_csv(PHRASES_DIR / "ood.csv")
    scenarios = yaml.safe_load((PHRASES_DIR / "scenarios.yaml").read_text(encoding="utf-8"))["scenarios"]

    for path in PHRASES_DIR.rglob("*.*"):
        if EM_DASH in path.read_text(encoding="utf-8"):
            errors.append(f"{path.name}: длинное тире")

    for name, rows in (("train", train), ("test", test)):
        for row in rows:
            if row["intent"] not in intents:
                errors.append(f"{name}: неизвестный интент {row['intent']} – {row['text']}")
            if row["lang"] not in ("ru", "kk", "en"):
                errors.append(f"{name}: неизвестный язык {row['lang']} – {row['text']}")

    train_norm = Counter(normalize(r["text"]) for r in train)
    errors += [f"train: дубль «{t}»" for t, c in train_norm.items() if c > 1]
    errors += [f"test пересекается с train: «{r['text']}»" for r in test if normalize(r["text"]) in train_norm]
    errors += [f"ood пересекается с train: «{r['text']}»" for r in ood if normalize(r["text"]) in train_norm]

    train_counts, test_counts = Counter(r["intent"] for r in train), Counter(r["intent"] for r in test)
    for intent in sorted(intents):
        if train_counts[intent] < MIN_TRAIN_PER_INTENT:
            errors.append(f"{intent}: в train {train_counts[intent]} фраз (нужно от {MIN_TRAIN_PER_INTENT})")
        if test_counts[intent] < MIN_TEST_PER_INTENT:
            errors.append(f"{intent}: в test {test_counts[intent]} фраз (нужно от {MIN_TEST_PER_INTENT})")

    # во внешнем тесте у двусмысленного вопроса допустимые интенты перечислены через «|»
    external = read_csv(PHRASES_DIR / "external.csv")
    for row in external:
        for intent in row["intent"].split("|"):
            if intent != "ood" and intent not in intents:
                errors.append(f"external: неизвестный интент {intent} – {row['text']}")
    external_ood = sum(r["intent"] == "ood" for r in external)

    turns = 0
    for sc in scenarios:
        for turn in sc["turns"]:
            turns += 1
            expected = turn["intent"] if isinstance(turn["intent"], list) else [turn["intent"]]
            for intent in expected:
                if intent != "ood" and intent not in intents:
                    errors.append(f"сценарий {sc['id']}: неизвестный интент {intent}")

    print(f"train: {len(train)} фраз, по языкам {dict(Counter(r['lang'] for r in train))}")
    print(f"test: {len(test)} фраз, по стилям {dict(Counter(r['style'] for r in test))}")
    print(f"ood: {len(ood)} фраз, по видам {dict(Counter(r['kind'] for r in ood))}")
    print(f"external: {len(external)} вопросов из {len({r['university'] for r in external})} вузов, "
          f"вне базы {external_ood}, по языкам {dict(Counter(r['lang'] for r in external))}")
    print(f"сценарии: {len(scenarios)} диалогов, {turns} реплик")
    print(f"фраз на интент в train: от {min(train_counts.values())} до {max(train_counts.values())}")
    return errors


if __name__ == "__main__":
    problems = check()
    for p in problems:
        print("  !", p)
    print("ошибок:", len(problems))
    sys.exit(1 if problems else 0)
