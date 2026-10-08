"""Оценка работающего сервиса для исследования (Задание 2): качество по наборам, ошибки, контекст, задержки.

Запускается в образе бэкенда – той же моделью и тем же кодом, что отвечают пользователям:
    make -C research collect
Результат – research/results/service_eval.json.
"""
import csv
import json
import logging
import math
import sys
import time
from collections import Counter
from pathlib import Path

import yaml

from app.knowledge import Knowledge
from app.metrics.benchmark import Benchmark
from app.metrics.collector import MetricsCollector, histogram, percentiles, rss_mb
from app.nlp.classifier import IntentClassifier
from app.nlp.context import is_follow_up
from app.service import answer_question

logging.disable(logging.INFO)  # в логах сервиса – по строке на вопрос, здесь они не нужны

PHRASES = Path("/app/data/phrases")
OUT = Path("/research/results")


def wilson(successes: int, n: int, z: float = 1.96) -> dict:
    if n == 0:
        return {"value": None, "ci95": [None, None], "n": 0, "successes": 0}
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return {"value": p, "ci95": [max(0.0, centre - half), min(1.0, centre + half)], "n": n, "successes": successes}


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


classifier = IntentClassifier()
knowledge = Knowledge()
metrics = MetricsCollector()


def ask(text: str, context=None):
    return answer_question(classifier, knowledge, metrics, text, None, "research", context)


def evaluate(rows: list[dict], key: str) -> tuple[list[dict], dict]:
    """Каждый вопрос – через сервис; верно = тема из ожидаемых и бот ответил (или «не понял» для ood)."""
    records = []
    for r in rows:
        gold = r.get("intent", "ood") or "ood"
        golds = gold.split("|")
        a = ask(r["text"])
        top1 = a.prediction.intent
        ok = (not a.recognized) if golds == ["ood"] else (a.recognized and a.intent in golds)
        records.append({"text": r["text"], "gold": golds, "lang": r.get("lang"), "group": r.get(key),
                        "intent": a.intent, "top1": top1, "confidence": a.confidence, "recognized": a.recognized,
                        "rule": a.rule, "ok": ok, "top1_ok": golds != ["ood"] and top1 in golds})
    summary = {"overall": wilson(sum(x["ok"] for x in records), len(records))}
    in_domain = [x for x in records if x["gold"] != ["ood"]]
    if in_domain:
        summary["top1_no_threshold"] = wilson(sum(x["top1_ok"] for x in in_domain), len(in_domain))
    for field in ("lang", "group"):
        values = sorted({x[field] for x in records if x[field]})
        summary[f"by_{field}"] = {v: wilson(sum(x["ok"] for x in records if x[field] == v),
                                            sum(1 for x in records if x[field] == v)) for v in values}
    summary["rules"] = dict(Counter(x["rule"] for x in records))
    return records, summary


def confusions(records: list[dict], top: int = 12) -> list[dict]:
    pairs = Counter((x["gold"][0], x["top1"]) for x in records if x["gold"] != ["ood"] and not x["top1_ok"])
    return [{"gold": g, "pred": p, "count": c, "gold_title": knowledge.title(g, "ru"),
             "pred_title": knowledge.title(p, "ru")} for (g, p), c in pairs.most_common(top)]


# ---------- контекст диалога: итоговое правило сервиса и отвергнутые простые правила ----------

group_of = {i: x.group for i, x in knowledge.intents.items()}


def rule_decision(rule: str, prev: tuple[str, str] | None, text: str):
    """(интент, распознан) для реплики по одному из правил; prev – (текст, интент) прошлого ответа."""
    alone = classifier.predict(text)
    if prev is None or rule == "none":
        return alone.intent, alone.recognized
    joint = classifier.predict(f"{prev[0]} {text}")
    marker = is_follow_up(text)
    same_group = group_of[joint.intent] == group_of[prev[1]]
    use = {
        "unrecognized": not alone.recognized,
        "marker": marker or not alone.recognized,
        "more_confident": joint.confidence > alone.confidence,
        "marker_same_group": marker and (not alone.recognized or same_group),
    }[rule] and joint.recognized
    return (joint.intent, joint.recognized) if use else (alone.intent, alone.recognized)


def correct(intent, recognized, expect) -> bool:
    expect = expect if isinstance(expect, list) else [expect]
    return (not recognized) if expect == ["ood"] else (recognized and intent in expect)


def context_study() -> dict:
    scenarios = yaml.safe_load((PHRASES / "scenarios.yaml").read_text(encoding="utf-8"))["scenarios"]
    pairs = yaml.safe_load((PHRASES / "followups.yaml").read_text(encoding="utf-8"))["pairs"]
    result = {}
    for rule in ("none", "unrecognized", "marker", "more_confident", "marker_same_group"):
        good = total = 0
        for s in scenarios:
            prev = None
            for turn in s["turns"]:
                intent, rec = rule_decision(rule, prev, turn["text"])
                good += correct(intent, rec, turn["intent"])
                total += 1
                prev = (turn["text"], intent) if rec and group_of[intent] != "service" else None
        pair_good = 0
        for p in pairs:
            first = classifier.predict(p["first"])
            prev = (p["first"], first.intent) if first.recognized else None
            pair_good += correct(*rule_decision(rule, prev, p["followup"]), p["expect"])
        result[rule] = {"scenarios": wilson(good, total), "followups": wilson(pair_good, len(pairs))}
    # итоговое правило – как в сервисе: контекст из ответа, правило суммы тем стоимости, извлечение программ
    good = total = 0
    for s in scenarios:
        ctx = None
        for turn in s["turns"]:
            a = ask(turn["text"], ctx)
            ctx = a.context
            good += correct(a.intent, a.recognized, turn["intent"])
            total += 1
    pair_good = 0
    for p in pairs:
        a = ask(p["followup"], ask(p["first"]).context)
        pair_good += correct(a.intent, a.recognized, p["expect"])
    result["service"] = {"scenarios": wilson(good, total), "followups": wilson(pair_good, len(pairs))}
    return result


# ---------- задержки и память ----------

def latency_study(texts: list[str]) -> dict:
    model_ms, total_ms = [], []
    for t in texts:
        t0 = time.perf_counter()
        classifier.predict(t)
        model_ms.append((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        ask(t)
        total_ms.append((time.perf_counter() - t0) * 1000)
    bench = [Benchmark(classifier).run() for _ in range(3)]
    return {"model": {"percentiles": percentiles(model_ms), "histogram": histogram(model_ms), "series": model_ms},
            "service": {"percentiles": percentiles(total_ms), "histogram": histogram(total_ms)},
            "benchmark": [{k: b[k] for k in ("n", "seconds", "throughput_rps", "latency_ms", "sla")} for b in bench],
            "memory_mb": rss_mb(), "model_load_seconds": classifier.load_seconds}


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "full"
    test = [r for p in sorted((PHRASES / "test").glob("*.csv")) for r in read_csv(p)]
    OUT.mkdir(parents=True, exist_ok=True)
    if label != "full":  # только задержки при заданных ограничениях CPU: make collect-latency
        result = latency_study([r["text"] for r in test])
        (OUT / f"latency_{label}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print(label, result["model"]["percentiles"], "rps", [round(b["throughput_rps"]) for b in result["benchmark"]])
        return
    sets = {"test": (test, "style"), "external": (read_csv(PHRASES / "external.csv"), "university"),
            "ood": (read_csv(PHRASES / "ood.csv"), "kind")}
    report, all_records = {}, []
    for name, (rows, key) in sets.items():
        records, summary = evaluate(rows, key)
        report[name] = summary
        all_records += records if name != "ood" else []
        print(name, round(summary["overall"]["value"], 3), summary["rules"])
    report["confusions"] = confusions(all_records)
    report["confidence"] = {
        "in_domain_correct": [x["confidence"] for x in all_records if x["top1_ok"]],
        "in_domain_wrong": [x["confidence"] for x in all_records if x["gold"] != ["ood"] and not x["top1_ok"]],
        "ood": [x["confidence"] for x in evaluate(sets["ood"][0], "kind")[0]],
        "threshold": classifier.threshold,
    }
    report["context"] = context_study()
    print("context", {k: (v["scenarios"]["successes"], v["followups"]["successes"]) for k, v in report["context"].items()})
    report["latency"] = latency_study([r["text"] for r in test])
    (OUT / "service_eval.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("latency p50/p95", report["latency"]["model"]["percentiles"], "memory", report["latency"]["memory_mb"])


if __name__ == "__main__":
    main()
