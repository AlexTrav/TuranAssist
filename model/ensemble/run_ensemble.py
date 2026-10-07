import json
import urllib.request

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from model.baseline.train_baseline import CONFIGS, build_pipeline
from model.common import data, metrics

HF_BASE = "https://huggingface.co/AlexCode2003/turanassist-intent-e5/resolve/main/v2"
MODEL_DIR = data.REPO_ROOT / "model"
CACHE_DIR = MODEL_DIR / ".cache" / "v2"
REPORT_DIR = MODEL_DIR / "reports" / "ensemble"
ARTIFACT_DIR = MODEL_DIR / "artifacts" / "production"

SET_KEYS = ("train", "test", "ood_val", "ood_test", "external", "scenarios")
# варианты энкодера: fp32 – эталон (в 512 МБ Render не помещается), остальные – кандидаты в продакшн
ENCODERS = {
    "encoder_torch_fp32": {"deployable": False, "onnx": None},
    "encoder_int8_full": {"deployable": True, "onnx": "encoder_int8_full.onnx"},
    "encoder_int8_full_perchannel": {"deployable": True, "onnx": "encoder_int8_full_perchannel.onnx"},
    "encoder_int8_emb_only": {"deployable": True, "onnx": "encoder_int8_emb_only.onnx"},
}
C_GRID = [10, 100, 1000]
WEIGHTS = [round(w, 1) for w in np.arange(0.1, 1.0, 0.1)]


def fetch(name: str) -> bytes:
    path = CACHE_DIR / name
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f"{HF_BASE}/{name}", timeout=120) as resp:
            path.write_bytes(resp.read())
    return path.read_bytes()


def load_dump(variant: str) -> dict:
    fetch(f"dumps/{variant}.npz")
    with np.load(CACHE_DIR / "dumps" / f"{variant}.npz") as npz:
        return {k: npz[k] for k in SET_KEYS}


# уверенность модели: максимальная вероятность или разрыв между первым и вторым интентом
def confidence(proba: np.ndarray, kind: str) -> np.ndarray:
    if kind == "maxprob":
        return proba.max(1)
    top2 = np.sort(proba, axis=1)[:, -2:]
    return top2[:, 1] - top2[:, 0]


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    ood_val, ood_test = data.load_ood()
    sets = {"train": data.load_train(), "test": data.load_test(), "ood_val": ood_val, "ood_test": ood_test,
            "external": data.load_external(), "scenarios": data.load_scenarios()}
    texts = {k: [e.text for e in v] for k, v in sets.items()}
    # эмбеддинги в Colab считались по тем же наборам – порядок фраз обязан совпадать
    assert json.loads(fetch("dumps/texts.json")) == texts, "наборы фраз изменились после прогона v2"
    quant = json.loads(fetch("metrics_v2.json"))["quantization"]
    baseline = json.loads((MODEL_DIR / "reports" / "baseline" / "metrics.json").read_text(encoding="utf-8"))

    y = [e.labels[0] for e in sets["train"]]
    intents = sorted(set(y))
    y_ids = np.array([intents.index(t) for t in y])
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=data.SEED)

    # TF-IDF char с тем же C, что выбрал baseline; вероятности кросс-валидации – для порога и весов ансамбля
    tfidf_c = baseline["results"]["tfidf_char"]["C"]
    tfidf_model = build_pipeline(CONFIGS["tfidf_char"]).set_params(clf__C=tfidf_c)
    oof = {"tfidf": cross_val_predict(tfidf_model, texts["train"], y, cv=cv, method="predict_proba")}
    tfidf_model.fit(texts["train"], y)
    probs = {"tfidf": {k: tfidf_model.predict_proba(texts[k]) for k in SET_KEYS}}
    latency = {"tfidf": baseline["results"]["tfidf_char"]["latency_ms"]["p50"]}

    heads = {}
    for variant in ENCODERS:
        emb = load_dump(variant)
        best = None
        for c in C_GRID:
            o = cross_val_predict(LogisticRegression(C=c, max_iter=5000), emb["train"], y_ids, cv=cv, method="predict_proba")
            acc = float(np.mean(o.argmax(1) == y_ids))
            if best is None or acc > best[1]:
                best = (c, acc, o)
        head = LogisticRegression(C=best[0], max_iter=5000).fit(emb["train"], y_ids)
        heads[variant] = (best[0], head)
        oof[variant] = best[2]
        probs[variant] = {k: head.predict_proba(emb[k]) for k in SET_KEYS}
        q = quant.get(variant.replace("encoder_", "encoder/"), {})
        latency[variant] = q.get("latency_ms", {}).get("p50")

        # ансамбль: взвешенное среднее вероятностей e5 и TF-IDF, вес – по точности кросс-валидации
        w = max(WEIGHTS, key=lambda w: np.mean((w * oof[variant] + (1 - w) * oof["tfidf"]).argmax(1) == y_ids))
        name = f"ensemble[{variant}]"
        oof[name] = w * oof[variant] + (1 - w) * oof["tfidf"]
        probs[name] = {k: w * probs[variant][k] + (1 - w) * probs["tfidf"][k] for k in SET_KEYS}
        latency[name] = latency[variant] + latency["tfidf"] if latency[variant] else None
        heads[name] = (w, None)
        print(f"{variant}: C={best[0]} cv={best[1]:.3f}; ансамбль w_e5={w} "
              f"cv={np.mean(oof[name].argmax(1) == y_ids):.3f}")

    results = {}
    for name in oof:
        for kind in ("maxprob", "margin"):
            correct = list(oof[name].argmax(1) == y_ids)
            thr, info = metrics.choose_threshold(correct, confidence(oof[name], kind),
                                                 confidence(probs[name]["ood_val"], kind))
            r = {"model": name, "confidence": kind, "cv_accuracy": float(np.mean(correct)), "threshold": thr,
                 "selection_score": info["score"], "threshold_selection": info, "latency_p50_ms": latency[name],
                 "deployable": name == "tfidf" or ENCODERS[name.split("[")[-1].rstrip("]")]["deployable"]}
            if name.startswith("ensemble"):
                r["weight_e5"] = heads[name][0]
            for key in ("test", "ood_test", "external", "scenarios"):
                pred = [intents[i] for i in probs[name][key].argmax(1)]
                r[key] = metrics.evaluate_set(sets[key], pred, confidence(probs[name][key], kind), thr)
            results[f"{name}|{kind}"] = r

    # продакшн выбирается без теста: лучший сбалансированный балл на кросс-валидации и OOD-валидации
    # среди вариантов, которые помещаются в 512 МБ бесплатного Render
    best_key = max((k for k, r in results.items() if r["deployable"]), key=lambda k: results[k]["selection_score"])
    best = results[best_key]
    print("выбрано для продакшна:", best_key)

    # кривая «порог → качество» для выбранной модели – для исследования (Задание 2), не для выбора
    name, kind = best["model"], best["confidence"]
    curve = []
    for t in np.round(np.arange(0.0, 1.0001, 0.05), 2):
        point = {"threshold": float(t)}
        for key in ("test", "ood_test", "external", "scenarios"):
            pred = [intents[i] for i in probs[name][key].argmax(1)]
            point[key] = metrics.evaluate_set(sets[key], pred, confidence(probs[name][key], kind), float(t))["overall"]["value"]
        curve.append(point)

    write_artifacts(best, heads, intents, tfidf_c)
    (REPORT_DIR / "metrics.json").write_text(json.dumps({"best": best_key, "results": results, "threshold_curve": curve},
                                                        ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    write_report(results, best_key, curve)


# параметры продакшн-модели: какой энкодер скачать с HF, голова логистической регрессии, вес ансамбля и порог
def write_artifacts(best: dict, heads: dict, intents: list[str], tfidf_c: float) -> None:
    name = best["model"]
    info = {"name": name, "confidence": best["confidence"], "threshold": best["threshold"], "intents": intents,
            "tfidf": {"artifact": "model/artifacts/baseline/model.joblib", "config": "tfidf_char", "C": tfidf_c}}
    variant = name.split("[")[-1].rstrip("]") if name != "tfidf" else None
    if variant:
        c, head = heads[variant]
        np.savez(ARTIFACT_DIR / "e5_head.npz", coef=head.coef_.astype(np.float32),
                 intercept=head.intercept_.astype(np.float32))
        info["e5"] = {"onnx_url": f"{HF_BASE}/{ENCODERS[variant]['onnx']}", "tokenizer_url": f"{HF_BASE}/tokenizer.json",
                      "head": "model/artifacts/production/e5_head.npz", "C": c, "query_prefix": "query: ",
                      "max_length": 64}
        info["weight_e5"] = best.get("weight_e5", 1.0)
    (ARTIFACT_DIR / "model_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")


def _fmt(p: dict) -> str:
    return f"{p['value']:.3f} [{p['ci95'][0]:.3f}; {p['ci95'][1]:.3f}]"


def write_report(results: dict, best_key: str, curve: list[dict]) -> None:
    lines = ["# Выбор модели для продакшна: e5, TF-IDF и их ансамбль", "",
             "Порог и вес ансамбля подбираются на кросс-валидации обучающей выборки и половине OOD-набора;",
             "продакшн-модель выбирается по сбалансированному баллу (доля принятых верных ответов и доля",
             "отклонённых чужих вопросов) среди вариантов, помещающихся в 512 МБ бесплатного Render.",
             "Тестовые наборы в выборе не участвуют. Значения – доля верных ответов, в скобках 95% ДИ Уилсона.", "",
             "| Модель | Уверенность | CV acc | Балл выбора | Порог | Test с порогом | OOD отклонено | Внешний тест | Сценарии | p50, мс |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for key, r in sorted(results.items(), key=lambda kv: -kv[1]["selection_score"]):
        mark = " **(выбрана)**" if key == best_key else ("" if r["deployable"] else " (не помещается в 512 МБ)")
        lat = f"{r['latency_p50_ms']:.1f}" if r["latency_p50_ms"] else "–"
        w = f", w_e5={r['weight_e5']}" if "weight_e5" in r else ""
        lines.append(f"| `{r['model']}`{w}{mark} | {r['confidence']} | {r['cv_accuracy']:.3f} | {r['selection_score']:.3f} "
                     f"| {r['threshold']:.3f} | {_fmt(r['test']['overall'])} | {_fmt(r['ood_test']['ood_rejected'])} "
                     f"| {_fmt(r['external']['overall'])} | {_fmt(r['scenarios']['overall'])} | {lat} |")
    b = results[best_key]
    lines += ["", f"## Выбранная модель: `{b['model']}`, уверенность `{b['confidence']}`, порог {b['threshold']:.3f}", "",
              "По стилям теста (с порогом):", ""]
    lines += [f"- {g}: {_fmt(p)}" for g, p in b["test"]["by_group"].items()]
    lines += ["", "По языкам (с порогом):", ""]
    lines += [f"- {g}: {_fmt(p)}" for g, p in b["test"]["by_lang"].items()]
    lines += ["", "Внешний тест: интенты с порогом " + _fmt(b["external"]["in_domain_correct"]) +
              ", вопросы вне базы отклонены " + _fmt(b["external"]["ood_rejected"]) + ".", "",
              "## Кривая «порог → доля верных ответов» (выбранная модель)", "",
              "| Порог | Тест | OOD-тест | Внешний | Сценарии |", "|---|---|---|---|---|"]
    lines += [f"| {p['threshold']:.2f} | {p['test']:.3f} | {p['ood_test']:.3f} | {p['external']:.3f} | {p['scenarios']:.3f} |"
              for p in curve]
    (REPORT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
