import math
import time
from collections import Counter, defaultdict
from typing import Callable, Sequence

import numpy as np

from .data import OOD, Example

Z95 = 1.959964  # квантиль нормального распределения для 95% доверительного интервала


# доверительный интервал Уилсона для доли: точнее нормального приближения на малых выборках
# и при долях около 0 или 1
def wilson_ci(successes: int, n: int, z: float = Z95) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def proportion(successes: int, n: int) -> dict:
    low, high = wilson_ci(successes, n)
    return {"value": successes / n if n else 0.0, "ci95": [low, high], "n": n, "successes": successes}


def macro_f1(y_true: Sequence[str], y_pred: Sequence[str], labels: Sequence[str]) -> tuple[float, dict]:
    per_label = {}
    for label in labels:
        tp = sum(t == label and p == label for t, p in zip(y_true, y_pred))
        fp = sum(t != label and p == label for t, p in zip(y_true, y_pred))
        fn = sum(t == label and p != label for t, p in zip(y_true, y_pred))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_label[label] = {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}
    return float(np.mean([v["f1"] for v in per_label.values()])), per_label


# итоговое решение бота: интент, если уверенность не ниже порога, иначе «не понял» (ood)
def decide(intents: Sequence[str], confidences: Sequence[float], threshold: float) -> list[str]:
    return [i if c >= threshold else OOD for i, c in zip(intents, confidences)]


# порог подбирается так, чтобы одновременно принимать максимум своих вопросов с верным интентом
# и отклонять максимум чужих: максимизируем среднее этих двух долей (сбалансированная точность)
def choose_threshold(in_correct: Sequence[bool], in_conf: Sequence[float],
                     ood_conf: Sequence[float]) -> tuple[float, dict]:
    candidates = np.unique(np.concatenate([in_conf, ood_conf, [0.0, 1.0]]))
    best_t, best = 0.0, {"score": -1.0}
    for t in candidates:
        accepted_correct = float(np.mean([ok and c >= t for ok, c in zip(in_correct, in_conf)]))
        rejected_ood = float(np.mean([c < t for c in ood_conf]))
        score = (accepted_correct + rejected_ood) / 2
        if score > best["score"]:
            best_t, best = float(t), {"score": score, "accepted_correct": accepted_correct,
                                      "rejected_ood": rejected_ood}
    return best_t, best


# метрики на наборе с порогом: ответ верен, если интент среди допустимых или вопрос чужой и отклонён
def evaluate_set(examples: Sequence[Example], intents: Sequence[str], confidences: Sequence[float],
                 threshold: float) -> dict:
    decisions = decide(intents, confidences, threshold)
    ok = [d in ex.labels for ex, d in zip(examples, decisions)]
    in_domain = [i for i, ex in enumerate(examples) if OOD not in ex.labels]
    ood = [i for i, ex in enumerate(examples) if OOD in ex.labels]
    result = {"overall": proportion(sum(ok), len(ok))}
    if in_domain:
        result["in_domain_correct"] = proportion(sum(ok[i] for i in in_domain), len(in_domain))
        # без порога: модель всегда называет интент – так видно качество самой классификации
        raw_ok = sum(intents[i] in examples[i].labels for i in in_domain)
        result["in_domain_top1_no_threshold"] = proportion(raw_ok, len(in_domain))
    if ood:
        result["ood_rejected"] = proportion(sum(ok[i] for i in ood), len(ood))
    by_group = defaultdict(list)
    for ex, good in zip(examples, ok):
        by_group[ex.group or ex.lang].append(good)
    result["by_group"] = {g: proportion(sum(v), len(v)) for g, v in sorted(by_group.items())}
    by_lang = defaultdict(list)
    for ex, good in zip(examples, ok):
        by_lang[ex.lang].append(good)
    result["by_lang"] = {g: proportion(sum(v), len(v)) for g, v in sorted(by_lang.items())}
    return result


# самые частые ошибки классификации: (верный интент, предсказанный) -> сколько раз
def top_confusions(y_true: Sequence[str], y_pred: Sequence[str], k: int = 10) -> list[dict]:
    pairs = Counter((t, p) for t, p in zip(y_true, y_pred) if t != p)
    return [{"true": t, "pred": p, "count": c} for (t, p), c in pairs.most_common(k)]


# задержка ответа на одиночный запрос (как у живого пользователя), миллисекунды
def latency_ms(predict_one: Callable[[str], object], texts: Sequence[str], repeats: int = 3) -> dict:
    for text in texts[:20]:  # прогрев: кэши, ленивые загрузки
        predict_one(text)
    samples = []
    for _ in range(repeats):
        for text in texts:
            start = time.perf_counter()
            predict_one(text)
            samples.append((time.perf_counter() - start) * 1000)
    arr = np.array(samples)
    return {"p50": float(np.percentile(arr, 50)), "p95": float(np.percentile(arr, 95)),
            "p99": float(np.percentile(arr, 99)), "mean": float(arr.mean()), "n": len(samples)}
