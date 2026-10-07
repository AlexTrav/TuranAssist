import json
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer

from app.nlp.preprocess import preprocess_batch
from model.common import data, metrics

MODEL_DIR = data.REPO_ROOT / "model"
ARTIFACT_DIR = MODEL_DIR / "artifacts" / "baseline"
REPORT_DIR = MODEL_DIR / "reports" / "baseline"
C_GRID = [1, 10, 100]

# конфигурации: какие признаки и какая предобработка – сравниваем вклад каждого этапа из ТЗ
CONFIGS = {
    "bow_word_lemma": {"features": "bow", "lemmatize": True, "stopwords": None},
    "tfidf_word_raw": {"features": "word", "lemmatize": False, "stopwords": None},
    "tfidf_word_lemma": {"features": "word", "lemmatize": True, "stopwords": None},
    "tfidf_word_lemma_stop": {"features": "word", "lemmatize": True, "stopwords": "all"},
    "tfidf_word_lemma_stop_keepq": {"features": "word", "lemmatize": True, "stopwords": "no_questions"},
    "tfidf_char": {"features": "char", "lemmatize": False, "stopwords": None},
    "tfidf_word_char": {"features": "word+char", "lemmatize": True, "stopwords": None},
}


def _prep(lemmatize: bool, stopwords: str | None) -> FunctionTransformer:
    return FunctionTransformer(preprocess_batch, kw_args={"lemmatize": lemmatize, "stopwords": stopwords})


def _word_branch(cfg: dict, vectorizer_cls=TfidfVectorizer) -> Pipeline:
    kwargs = {"ngram_range": (1, 2), "token_pattern": r"\S+"}
    if vectorizer_cls is TfidfVectorizer:
        kwargs["sublinear_tf"] = True
    return Pipeline([("prep", _prep(cfg["lemmatize"], cfg["stopwords"])), ("vec", vectorizer_cls(**kwargs))])


def _char_branch() -> Pipeline:
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)
    return Pipeline([("prep", _prep(False, None)), ("vec", vec)])


def build_pipeline(cfg: dict) -> Pipeline:
    features = {
        "bow": lambda: _word_branch(cfg, CountVectorizer),
        "word": lambda: _word_branch(cfg),
        "char": _char_branch,
        "word+char": lambda: FeatureUnion([("word", _word_branch(cfg)), ("char", _char_branch())]),
    }[cfg["features"]]()
    return Pipeline([("features", features), ("clf", LogisticRegression(max_iter=5000))])


def predict(model: Pipeline, texts: list[str]) -> tuple[list[str], np.ndarray]:
    proba = model.predict_proba(texts)
    return list(model.classes_[proba.argmax(axis=1)]), proba.max(axis=1)


# обучает одну конфигурацию и оценивает её на всех наборах
def run_config(name: str, cfg: dict, sets: dict) -> tuple[dict, Pipeline]:
    train = sets["train"]
    x, y = [e.text for e in train], [e.labels[0] for e in train]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=data.SEED)

    start = time.perf_counter()
    search = GridSearchCV(build_pipeline(cfg), {"clf__C": C_GRID}, cv=cv, scoring="accuracy", n_jobs=1)
    search.fit(x, y)
    best_c = search.best_params_["clf__C"]

    # предсказания кросс-валидации: «свои» вопросы, которые модель не видела, – для подбора порога
    oof_model = build_pipeline(cfg).set_params(clf__C=best_c)
    oof_proba = cross_val_predict(oof_model, x, y, cv=cv, method="predict_proba")
    classes = np.array(sorted(set(y)))
    oof_correct = [classes[i] == t for i, t in zip(oof_proba.argmax(axis=1), y)]
    model = search.best_estimator_
    train_seconds = time.perf_counter() - start

    _, ood_val_conf = predict(model, [e.text for e in sets["ood_val"]])
    threshold, threshold_info = metrics.choose_threshold(oof_correct, oof_proba.max(axis=1), ood_val_conf)

    result = {"config": cfg, "C": best_c, "cv_accuracy": float(search.best_score_),
              "train_seconds": train_seconds, "threshold": threshold, "threshold_selection": threshold_info}

    test = sets["test"]
    test_pred, test_conf = predict(model, [e.text for e in test])
    test_true = [e.labels[0] for e in test]
    f1, per_intent = metrics.macro_f1(test_true, test_pred, sorted(set(y)))
    result["test"] = metrics.evaluate_set(test, test_pred, test_conf, threshold)
    result["test"]["macro_f1_no_threshold"] = f1
    result["test"]["per_intent"] = per_intent
    result["test"]["confusions"] = metrics.top_confusions(test_true, test_pred)

    for key in ("ood_test", "external", "scenarios"):
        pred, conf = predict(model, [e.text for e in sets[key]])
        result[key] = metrics.evaluate_set(sets[key], pred, conf, threshold)

    result["latency_ms"] = metrics.latency_ms(lambda t: predict(model, [t]), [e.text for e in test])
    return result, model


def _model_size(model: Pipeline, path: Path) -> int:
    joblib.dump(model, path, compress=3)
    return path.stat().st_size


def _fmt(p: dict) -> str:
    return f"{p['value']:.3f} [{p['ci95'][0]:.3f}; {p['ci95'][1]:.3f}]"


# сводная таблица в markdown – для README, исследования (Задание 2) и записки (Задание 3)
def write_report(results: dict, best: str) -> None:
    lines = [
        "# Baseline: Bag-of-Words и TF-IDF + логистическая регрессия",
        "",
        "Значения – доля верных ответов, в скобках 95% доверительный интервал Уилсона.",
        "",
        "| Модель | CV acc | Test top-1 | Test macro-F1 | Порог | Test с порогом | OOD отклонено | Внешний тест | Сценарии | p50, мс | p95, мс | Размер, КБ |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, r in results.items():
        mark = " **(выбрана)**" if name == best else ""
        lines.append(
            f"| `{name}`{mark} | {r['cv_accuracy']:.3f} | {_fmt(r['test']['in_domain_top1_no_threshold'])} "
            f"| {r['test']['macro_f1_no_threshold']:.3f} | {r['threshold']:.3f} | {_fmt(r['test']['overall'])} "
            f"| {_fmt(r['ood_test']['ood_rejected'])} | {_fmt(r['external']['overall'])} "
            f"| {_fmt(r['scenarios']['overall'])} | {r['latency_ms']['p50']:.2f} | {r['latency_ms']['p95']:.2f} "
            f"| {r['model_bytes'] / 1024:.0f} |"
        )
    b = results[best]
    lines += ["", f"## Выбранная модель `{best}` (по точности кросс-валидации)", "",
              "Точность на стилистическом тесте по стилям (с порогом):", ""]
    lines += [f"- {g}: {_fmt(p)}" for g, p in b["test"]["by_group"].items()]
    lines += ["", "По языкам (с порогом):", ""]
    lines += [f"- {g}: {_fmt(p)}" for g, p in b["test"]["by_lang"].items()]
    lines += ["", "Внешний тест: интенты без порога "
              f"{_fmt(b['external']['in_domain_top1_no_threshold'])}, с порогом "
              f"{_fmt(b['external']['in_domain_correct'])}, вопросы вне базы отклонены "
              f"{_fmt(b['external']['ood_rejected'])}.", "",
              "Самые слабые интенты на тесте (F1):", ""]
    weakest = sorted(b["test"]["per_intent"].items(), key=lambda kv: kv[1]["f1"])[:8]
    lines += [f"- `{k}`: F1 {v['f1']:.2f} (precision {v['precision']:.2f}, recall {v['recall']:.2f})"
              for k, v in weakest]
    lines += ["", "Частые ошибки (верный → предсказанный):", ""]
    lines += [f"- `{c['true']}` → `{c['pred']}`: {c['count']}" for c in b["test"]["confusions"]]
    (REPORT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ood_val, ood_test = data.load_ood()
    sets = {"train": data.load_train(), "test": data.load_test(), "ood_val": ood_val, "ood_test": ood_test,
            "external": data.load_external(), "scenarios": data.load_scenarios()}
    print({k: len(v) for k, v in sets.items()})

    results, models = {}, {}
    for name, cfg in CONFIGS.items():
        result, model = run_config(name, cfg, sets)
        result["model_bytes"] = _model_size(model, ARTIFACT_DIR / f"_{name}.tmp")
        (ARTIFACT_DIR / f"_{name}.tmp").unlink()
        results[name], models[name] = result, model
        print(f"{name}: cv={result['cv_accuracy']:.3f} test={result['test']['in_domain_top1_no_threshold']['value']:.3f} "
              f"f1={result['test']['macro_f1_no_threshold']:.3f} thr={result['threshold']:.2f} "
              f"ood={result['ood_test']['ood_rejected']['value']:.3f} ext={result['external']['overall']['value']:.3f} "
              f"p50={result['latency_ms']['p50']:.2f}ms")

    # лучшая модель выбирается по кросс-валидации на обучающей выборке, а не по тесту – без утечки
    best = max(results, key=lambda n: results[n]["cv_accuracy"])
    joblib.dump(models[best], ARTIFACT_DIR / "model.joblib", compress=3)
    meta = {"name": best, "config": results[best]["config"], "C": results[best]["C"],
            "threshold": results[best]["threshold"], "intents": list(models[best].classes_)}
    (ARTIFACT_DIR / "model_info.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORT_DIR / "metrics.json").write_text(json.dumps({"best": best, "results": results}, ensure_ascii=False,
                                                        indent=2, default=float), encoding="utf-8")
    write_report(results, best)
    print("выбрана:", best)


if __name__ == "__main__":
    main()
