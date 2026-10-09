"""Эксперимент с короткими запросами (Задание 2, раздел 4.11): правила и умный поиск.

    make -C research collect-short   ->  research/results/short_queries.json

Три конфигурации сервиса на одних и тех же вопросах:
  A – модель с порогом и правилами из основного исследования (сумма тем стоимости);
  B – A + правило «программа и слова о цене» + уточнение многозначного короткого запроса;
  C – B + умный поиск по названиям тем.
Конфигурация A получается из B: правила B срабатывают только там, где A отвечает «не понял».
Плюс перебор порога отрыва умного поиска: сколько верных ответов он добавляет и сколько ложных даёт.
"""
import csv
import json
import logging
import sys
import time
from collections import Counter
from pathlib import Path

from app.config import SEARCH_MAX_WORDS, SEARCH_MIN_MARGIN, SEARCH_MIN_SCORE
from app.knowledge import Knowledge
from app.metrics.collector import MetricsCollector
from app.nlp.classifier import IntentClassifier
from app.nlp.preprocess import tokenize
from app.nlp.search import TopicSearch
from app.service import answer_question

logging.disable(logging.INFO)
PHRASES = Path("/app/data/phrases")
OUT = Path("/research/results")
NEW_RULES = {"program", "clarify"}  # правила конфигурации B
MARGINS = [0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.05, 0.06]
SCORES = [0.88, 0.90, 0.92]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


classifier, knowledge, metrics = IntentClassifier(), Knowledge(), MetricsCollector()
search = TopicSearch(classifier, knowledge)


# исход ответа: для своих вопросов – верный ответ, ошибка, уточнение с верной темой среди кнопок или без неё,
# «не понял»; для вопросов вне базы – ложный ответ, уточнение или верный отказ
def outcome(answer, gold: list[str]) -> str:
    suggested = {i for i, _, _ in answer.suggestions}
    if gold == ["ood"]:
        return "false_answer" if answer.recognized else ("clarify" if answer.rule == "clarify" else "refused")
    if answer.recognized:
        return "correct" if answer.intent in gold else "wrong"
    if answer.rule == "clarify":
        return "clarify_hit" if gold and suggested & set(gold) else "clarify_miss"
    return "fallback"


def as_config_a(kind: str, rule: str, gold: list[str]) -> str:
    if rule in NEW_RULES:
        return "refused" if gold == ["ood"] else "fallback"
    return kind


def main() -> None:
    test = [r for p in sorted((PHRASES / "test").glob("*.csv")) for r in read_csv(p)]
    sets = {"short": read_csv(PHRASES / "short.csv"), "test": test,
            "external": read_csv(PHRASES / "external.csv"), "ood": read_csv(PHRASES / "ood.csv")}
    result, details, candidates, search_ms = {}, [], [], []
    for name, rows in sets.items():
        counts = {"A": Counter(), "B": Counter(), "C": Counter()}
        for r in rows:
            gold = (r.get("intent") or "ood").split("|")
            b = answer_question(classifier, knowledge, metrics, r["text"], None, "research")
            c = answer_question(classifier, knowledge, metrics, r["text"], None, "research", search=search)
            kb, kc = outcome(b, gold), outcome(c, gold)
            counts["A"][as_config_a(kb, b.rule, gold)] += 1
            counts["B"][kb] += 1
            counts["C"][kc] += 1
            if name == "short":
                details.append({"text": r["text"], "kind": r["kind"], "gold": gold, "A": as_config_a(kb, b.rule, gold),
                                "B": kb, "C": kc, "rule": c.rule, "intent": c.intent})
            # кандидаты для перебора порога: вопросы, на которые без поиска бот не ответил
            if not b.recognized and len(tokenize(r["text"])) <= SEARCH_MAX_WORDS:
                pred = classifier.predict(r["text"])
                t0 = time.perf_counter()
                hit = search.best(r["text"], pred.embedding)
                search_ms.append((time.perf_counter() - t0) * 1000)
                usable = hit.intent in {i for i, _ in pred.top} and bool(hit.shared)
                candidates.append({"set": name, "gold": gold, "intent": hit.intent, "score": hit.score,
                                   "margin": hit.margin, "usable": usable})
        result[name] = {cfg: dict(cnt) for cfg, cnt in counts.items()}
        result[name]["n"] = len(rows)
        print(name, {cfg: dict(cnt) for cfg, cnt in counts.items()})

    # перебор порогов: при каждом пороге – верные и ошибочные ответы поиска на своих вопросах и ложные на чужих
    sweep = []
    for min_score in SCORES:
        for margin in MARGINS:
            row = {"min_score": min_score, "min_margin": margin, "correct": 0, "wrong": 0, "false_answer": 0}
            for x in candidates:
                if not (x["usable"] and x["score"] >= min_score and x["margin"] >= margin):
                    continue
                if x["gold"] == ["ood"]:
                    row["false_answer"] += 1
                else:
                    row["correct" if x["intent"] in x["gold"] else "wrong"] += 1
            sweep.append(row)
    chosen = next(s for s in sweep if s["min_score"] == SEARCH_MIN_SCORE and s["min_margin"] == SEARCH_MIN_MARGIN)
    print("выбранные пороги", chosen)

    report = {"sets": result, "short_details": details, "sweep": sweep,
              "chosen": {"min_score": SEARCH_MIN_SCORE, "min_margin": SEARCH_MIN_MARGIN, "max_words": SEARCH_MAX_WORDS},
              "search_ms_mean": sum(search_ms) / max(len(search_ms), 1)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "short_queries.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("поиск, мс на вопрос:", round(report["search_ms_mean"], 3))


if __name__ == "__main__":
    sys.exit(main())
