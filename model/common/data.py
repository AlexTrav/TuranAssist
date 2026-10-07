import csv
import os
import random
from dataclasses import dataclass
from pathlib import Path

import yaml

# корень репозитория: model/common/data.py -> common -> model -> корень; в Docker переопределяется через DATA_DIR
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("DATA_DIR", REPO_ROOT / "data"))
PHRASES_DIR = DATA_DIR / "phrases"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"

OOD = "ood"
SEED = 42


@dataclass
class Example:
    text: str
    labels: tuple[str, ...]  # допустимые интенты; ("ood",) – вопрос вне базы
    lang: str = ""
    group: str = ""  # стиль, вид OOD, вуз или сценарий – для разбивки метрик


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _read_dir(name: str) -> list[dict]:
    return [row for path in sorted((PHRASES_DIR / name).glob("*.csv")) for row in _read_csv(path)]


def intent_ids() -> list[str]:
    ids = []
    for path in sorted((KNOWLEDGE_DIR / "intents").glob("*.yaml")):
        ids += [i["id"] for i in yaml.safe_load(path.read_text(encoding="utf-8"))["intents"]]
    return ids


def load_train() -> list[Example]:
    return [Example(r["text"], (r["intent"],), r["lang"]) for r in _read_dir("train")]


def load_test() -> list[Example]:
    return [Example(r["text"], (r["intent"],), r["lang"], r["style"]) for r in _read_dir("test")]


def load_external() -> list[Example]:
    rows = _read_csv(PHRASES_DIR / "external.csv")
    return [Example(r["text"], tuple(r["intent"].split("|")), r["lang"], r["university"]) for r in rows]


# OOD-набор делится пополам с фиксированным seed: первая половина – подбор порога, вторая – проверка;
# деление стратифицировано по виду вопроса, чтобы в обеих половинах были все виды
def load_ood() -> tuple[list[Example], list[Example]]:
    rows = _read_csv(PHRASES_DIR / "ood.csv")
    rng = random.Random(SEED)
    val, test = [], []
    for kind in sorted({r["kind"] for r in rows}):
        group = [r for r in rows if r["kind"] == kind]
        rng.shuffle(group)
        half = len(group) // 2
        val += [Example(r["text"], (OOD,), r["lang"], kind) for r in group[:half]]
        test += [Example(r["text"], (OOD,), r["lang"], kind) for r in group[half:]]
    return val, test


def load_scenarios() -> list[Example]:
    data = yaml.safe_load((PHRASES_DIR / "scenarios.yaml").read_text(encoding="utf-8"))
    examples = []
    for sc in data["scenarios"]:
        for turn in sc["turns"]:
            labels = turn["intent"] if isinstance(turn["intent"], list) else [turn["intent"]]
            examples.append(Example(turn["text"], tuple(labels), sc["lang"], sc["id"]))
    return examples
