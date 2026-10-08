"""Рисунки исследования (Задание 2) по сохранённым метрикам: model/reports и research/results.

    make -C research figures FIGURES=/путь/к/папке
Имена файлов – «Рисунок N – Название.png», как в отчёте.
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

REPO = Path("/repo")
OUT = Path("/figures")
REPORTS = REPO / "model" / "reports"
RESULTS = REPO / "research" / "results"

# шрифт отчёта – Times New Roman из Windows (папка Fonts подключена только для чтения)
for name in ("times.ttf", "timesbd.ttf", "timesi.ttf"):
    path = Path("/winfonts") / name
    if path.exists():
        font_manager.fontManager.addfont(str(path))
plt.rcParams.update({
    "font.family": "Times New Roman", "font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e3e3e3",
    "grid.linewidth": 0.8, "axes.axisbelow": True, "legend.frameon": True, "legend.framealpha": 0.95,
    "legend.edgecolor": "#dddddd", "savefig.dpi": 200, "savefig.bbox": "tight",
})

# цвета «Турана»: голубой, стальной, золотой; оранжевый – для контраста, как в образце
BLUE, STEEL, GOLD, ORANGE, INK, GREY = "#0082C9", "#84ADCA", "#E0A100", "#E8673A", "#0F172A", "#9aa3ad"
COMMA = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
PCT = FuncFormatter(lambda v, _: f"{v * 100:.0f}%")


def num(v: float, digits: int = 3) -> str:
    return f"{v:.{digits}f}".replace(".", ",")


def save(fig, n: int, title: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"Рисунок {n} – {title}.png")
    plt.close(fig)
    print("saved", n, title)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


baseline = load(REPORTS / "baseline" / "metrics.json")["results"]
ensemble = load(REPORTS / "ensemble" / "metrics.json")
service = load(RESULTS / "service_eval.json")
MODELS = {"TF-IDF (символы)": ensemble["results"]["tfidf|maxprob"],
          "e5 int8": ensemble["results"]["encoder_int8_full|maxprob"],
          "Ансамбль": ensemble["results"][ensemble["best"]]}
MODEL_COLORS = [STEEL, ORANGE, BLUE]


# ---------- 1. архитектура ----------
def fig_architecture():
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 56)
    ax.axis("off")

    def box(x, y, w, h, title, body, accent=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.6",
                                    fc="#f6f6f4", ec=BLUE if accent else "#555555", lw=2))
        ax.text(x + w / 2, y + h - 3.2, title, ha="center", va="center", fontsize=14, weight="bold", color=INK)
        ax.text(x + w / 2, y + (h - 5) / 2, body, ha="center", va="center", fontsize=11.5, color="#444444",
                linespacing=1.35)

    def arrow(x1, y1, x2, y2, label="", dashed=False, lx=0, ly=1.4):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", lw=2, color="#555555", ls="--" if dashed else "-",
                                    mutation_scale=16))
        if label:
            ax.text((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label, ha="center", fontsize=9.5, color="#555555")

    box(1, 30, 19, 15, "Пользователь", "браузер ПК\nили смартфон,\nTelegram")
    box(28, 37, 21, 15, "Фронтенд", "Vue 3, TypeScript,\nTailwind CSS,\nGitHub Pages", accent=True)
    box(28, 18, 21, 13, "Telegram", "Bot API,\nwebhook с секретом")
    box(58, 23, 26, 29, "Бэкенд", "FastAPI, Docker, Render\n(0,1 CPU, 512 МБ)\n\nпредобработка →\ne5 int8 + TF-IDF →\nпорог «не понял» →\nсущности и контекст", accent=True)
    box(88, 37, 16, 15, "База ответов", "53 темы,\nru / kk / en,\nисточники")
    box(88, 18, 16, 15, "Метрики", "p50 / p95 / p99,\nпамять,\nнагрузочный тест")
    box(28, 1, 21, 13, "Данные", "turan.edu.kz,\nдокументы вуза,\nнаборы фраз")
    box(58, 1, 26, 13, "Обучение", "Docker (TF-IDF), Colab (e5),\nHugging Face Hub")

    arrow(20, 41, 28, 44, "HTTPS", lx=-1.5, ly=2.6)
    arrow(20, 34, 28, 26, "сообщения", lx=-6, ly=-3.6)
    arrow(49, 44, 58, 44, "REST API", ly=2.4)
    arrow(49, 25, 58, 29, "update", ly=-3.4)
    arrow(84, 44, 88, 44)
    arrow(84, 27, 88, 27)
    arrow(49, 7.5, 58, 7.5, "фразы")
    arrow(71, 14, 71, 23, "модель", lx=5.2, ly=0)
    save(fig, 1, "Архитектура и конвейер обработки вопроса TuranAssist")


# ---------- 2. состав обучающей выборки ----------
GROUP_RU = {"service": "Общение", "admission": "Поступление", "postgrad": "Магистратура и PhD",
            "payment": "Стоимость и оплата", "grants": "Гранты и скидки", "study": "Учебный процесс",
            "student_life": "Студенческая жизнь", "about": "Об университете"}


def fig_data():
    counts = defaultdict(Counter)
    for path in sorted((REPO / "data" / "phrases" / "train").glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                counts[path.stem][row["lang"]] += 1
    groups = sorted(counts, key=lambda g: sum(counts[g].values()))
    fig, ax = plt.subplots(figsize=(9, 4.6))
    left = [0] * len(groups)
    for lang, color, label in (("ru", BLUE, "русский"), ("kk", GOLD, "казахский"), ("en", STEEL, "английский")):
        vals = [counts[g][lang] for g in groups]
        ax.barh([GROUP_RU[g] for g in groups], vals, left=left, color=color, label=label, height=0.62)
        left = [a + b for a, b in zip(left, vals)]
    for i, total in enumerate(left):
        ax.text(total + 3, i, str(total), va="center", fontsize=11)
    ax.set_xlabel("Число обучающих фраз")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right")
    ax.set_xlim(0, max(left) * 1.12)
    save(fig, 2, "Обучающие фразы по группам тем и языкам")


# ---------- 3. варианты предобработки baseline ----------
BASE_LABELS = {
    "bow_word_lemma": "BoW, леммы", "tfidf_word_raw": "TF-IDF, слова без лемм",
    "tfidf_word_lemma": "TF-IDF, леммы", "tfidf_word_lemma_stop": "TF-IDF, леммы, стоп-слова",
    "tfidf_word_lemma_stop_keepq": "TF-IDF, леммы, стоп-слова\nбез вопросительных",
    "tfidf_char": "TF-IDF, символьные n-граммы", "tfidf_word_char": "TF-IDF, слова + символы",
}


def fig_baseline():
    keys = list(BASE_LABELS)
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    y = range(len(keys))
    h = 0.27
    series = [("Тест без порога (top-1)", lambda r: r["test"]["in_domain_top1_no_threshold"]["value"], BLUE),
              ("Тест с порогом «не понял»", lambda r: r["test"]["overall"]["value"], STEEL),
              ("Вопросы из FAQ других вузов", lambda r: r["external"]["overall"]["value"], GOLD)]
    for i, (label, get, color) in enumerate(series):
        vals = [get(baseline[k]) for k in keys]
        ax.barh([v + (1 - i) * h for v in y], vals, height=h, color=color, label=label)
        for yy, v in zip(y, vals):
            ax.text(v + 0.006, yy + (1 - i) * h, num(v), va="center", fontsize=9.5)
    ax.set_yticks(list(y), [BASE_LABELS[k] for k in keys])
    ax.invert_yaxis()
    ax.set_xlim(0.4, 0.9)
    ax.xaxis.set_major_formatter(COMMA)
    ax.set_xlabel("Доля верных ответов")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.4, -0.13), ncols=3, fontsize=10.5)
    save(fig, 3, "Сравнение вариантов предобработки baseline-моделей")


# ---------- 4. сравнение моделей с доверительными интервалами ----------
def fig_models():
    metrics = [("Тест разными\nстилями (n = 318)", lambda r: r["test"]["overall"]),
               ("FAQ других вузов\n(n = 209)", lambda r: r["external"]["overall"]),
               ("Сценарии диалогов\n(n = 65)", lambda r: r["scenarios"]["overall"]),
               ("Отклонено вопросов\nне по теме (n = 78)", lambda r: r["ood_test"]["ood_rejected"])]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    w = 0.26
    for i, ((name, r), color) in enumerate(zip(MODELS.items(), MODEL_COLORS)):
        xs = [m + (i - 1) * w for m in range(len(metrics))]
        props = [get(r) for _, get in metrics]
        vals = [p["value"] for p in props]
        err = [[v - p["ci95"][0] for v, p in zip(vals, props)], [p["ci95"][1] - v for v, p in zip(vals, props)]]
        ax.bar(xs, vals, w * 0.92, color=color, label=name, yerr=err, capsize=3,
               error_kw=dict(lw=1, ecolor="#333333"))
        for x, v in zip(xs, vals):
            ax.text(x, 0.03, num(v), ha="center", va="bottom", fontsize=9.5, rotation=90, color="white" if color != STEEL else INK)
    ax.set_xticks(range(len(metrics)), [m for m, _ in metrics])
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(COMMA)
    ax.set_ylabel("Доля верных ответов")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", ncols=3, fontsize=10.5)
    save(fig, 4, "Сравнение моделей с 95% доверительными интервалами Уилсона")


# ---------- 5. стили вопросов и языки ----------
STYLE_RU = [("typo", "опечатки"), ("slang", "разговорный"), ("long", "длинные"), ("translit", "транслит"),
            ("plain", "обычные\nkk / en")]


def fig_styles():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [5, 3]})
    w = 0.26
    for i, ((name, r), color) in enumerate(zip(MODELS.items(), MODEL_COLORS)):
        vals = [r["test"]["by_group"][k]["value"] for k, _ in STYLE_RU]
        ax1.bar([x + (i - 1) * w for x in range(len(STYLE_RU))], vals, w * 0.92, color=color, label=name)
        langs = [r["test"]["by_lang"][k]["value"] for k in ("ru", "kk", "en")]
        ax2.bar([x + (i - 1) * w for x in range(3)], langs, w * 0.92, color=color, label=name)
    ax1.set_xticks(range(len(STYLE_RU)), [f"{ru}\n(n = {MODELS['Ансамбль']['test']['by_group'][k]['n']})" for k, ru in STYLE_RU])
    ax2.set_xticks(range(3), ["русский\n(n = 212)", "казахский\n(n = 53)", "английский\n(n = 53)"])
    for ax, title in ((ax1, "а) по стилю вопроса"), (ax2, "б) по языку")):
        ax.set_ylim(0, 1.05)
        ax.yaxis.set_major_formatter(COMMA)
        ax.grid(axis="x", visible=False)
        ax.set_title(title, loc="left", fontsize=12)
    ax1.set_ylabel("Доля верных ответов с порогом")
    fig.legend(*ax1.get_legend_handles_labels(), loc="upper center", bbox_to_anchor=(0.5, 1.07), ncols=3, fontsize=11)
    save(fig, 5, "Качество моделей по стилям вопросов и языкам")


# ---------- 6. кривая порога ----------
def fig_threshold():
    curve = ensemble["threshold_curve"]
    th = [c["threshold"] for c in curve]
    chosen = ensemble["results"][ensemble["best"]]["threshold"]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot(th, [c["test"] for c in curve], color=BLUE, lw=2.2, marker="o", ms=3.5, label="Тест: верные ответы")
    ax.plot(th, [c["scenarios"] for c in curve], color=STEEL, lw=2, marker="o", ms=3, label="Сценарии: верные ответы")
    ax.plot(th, [c["ood_test"] for c in curve], color=ORANGE, lw=2.2, marker="o", ms=3.5, label="Отклонено вопросов не по теме")
    ax.axvline(chosen, color=GOLD, lw=2, ls="--")
    ax.text(chosen + 0.012, 0.06, f"выбранный порог {num(chosen)}", fontsize=11, color="#7a5800")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.xaxis.set_major_formatter(COMMA)
    ax.yaxis.set_major_formatter(COMMA)
    ax.set_xlabel("Порог уверенности ансамбля")
    ax.set_ylabel("Доля")
    ax.legend(loc="center left", fontsize=10.5)
    save(fig, 6, "Влияние порога уверенности на ответы и отсев вопросов не по теме")


# ---------- 7. распределение уверенности ----------
def fig_confidence():
    c = service["confidence"]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    bins = [i / 20 for i in range(21)]
    for data, color, label in ((c["in_domain_correct"], BLUE, f"тема угадана (n = {len(c['in_domain_correct'])})"),
                               (c["in_domain_wrong"], ORANGE, f"тема не угадана (n = {len(c['in_domain_wrong'])})"),
                               (c["ood"], GOLD, f"вопрос не по теме (n = {len(c['ood'])})")):
        ax.hist(data, bins=bins, color=color, label=label, density=True, histtype="step", lw=2.4)
    ax.axvline(c["threshold"], color=INK, lw=1.8, ls="--")
    ax.text(c["threshold"] + 0.012, ax.get_ylim()[1] * 0.9, f"порог {num(c['threshold'])}", fontsize=11)
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(COMMA)
    ax.yaxis.set_major_formatter(COMMA)
    ax.set_xlabel("Уверенность ансамбля (максимальная вероятность темы)")
    ax.set_ylabel("Плотность")
    ax.legend(loc="upper left", fontsize=10.5)
    save(fig, 7, "Распределение уверенности для верных, ошибочных и посторонних вопросов")


# ---------- 8. задержки при разных ресурсах ----------
def fig_latency():
    runs = [("1 CPU,\nлокально", load(RESULTS / "latency_cpu1.json")["model"]["series"], BLUE),
            ("0,5 CPU,\nлокально", load(RESULTS / "latency_cpu05.json")["model"]["series"], STEEL),
            ("0,1 CPU,\nлокально", load(RESULTS / "latency_cpu01.json")["model"]["series"], GOLD)]
    render = load(RESULTS / "render_latency.json")
    runs.append(("0,1 CPU,\nRender", [v for b in render["benchmarks"] for v in b["series"]], ORANGE))
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    bp = ax.boxplot([r[1] for r in runs], tick_labels=[r[0] for r in runs], patch_artist=True, widths=0.5,
                    whis=(1, 99), showfliers=True, flierprops=dict(marker=".", ms=3, alpha=0.4))
    for patch, (_, _, color) in zip(bp["boxes"], runs):
        patch.set(facecolor=color, alpha=0.75, edgecolor="#333333")
    for med in bp["medians"]:
        med.set(color=INK, lw=1.6)
    ax.set_yscale("log")
    ax.set_yticks([2, 5, 10, 20, 50, 100, 200], ["2", "5", "10", "20", "50", "100", "200"])
    ax.axhline(100, color=INK, lw=1.2, ls="--")
    ax.text(0.55, 108, "цель 100 мс", fontsize=10.5)
    for i, (_, series, _) in enumerate(runs, start=1):
        s = sorted(series)
        ax.text(i, 2.4, f"p50 = {num(s[len(s) // 2], 1)} мс", fontsize=10.5, ha="center")
    ax.set_ylabel("Время классификации одного вопроса, мс (лог. шкала)")
    ax.grid(axis="x", visible=False)
    save(fig, 8, "Задержка модели при разных ограничениях процессора")


# ---------- 9. правила контекста ----------
def fig_context():
    labels = {"none": "без контекста", "unrecognized": "склеивать,\nесли не понял", "marker": "склеивать,\nесли «а …»",
              "more_confident": "склеенный\nувереннее", "marker_same_group": "«а …» + та же\nгруппа тем",
              "service": "итоговое правило\n(+ длина, сущности)"}
    ctx = service["context"]
    keys = list(labels)
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    w = 0.38
    for i, (field, color, name) in enumerate((("scenarios", BLUE, "сценарии диалогов (65 реплик)"),
                                              ("followups", GOLD, "пары с уточнением (17)"))):
        vals = [ctx[k][field]["value"] for k in keys]
        xs = [x + (i - 0.5) * w for x in range(len(keys))]
        ax.bar(xs, vals, w * 0.92, color=color, label=name)
        for x, k in zip(xs, keys):
            p = ctx[k][field]
            ax.text(x, p["value"] + 0.015, f"{p['successes']}/{p['n']}", ha="center", fontsize=9.5)
    ax.set_xticks(range(len(keys)), [labels[k] for k in keys], fontsize=10.5)
    ax.set_ylim(0, 1.08)
    ax.yaxis.set_major_formatter(COMMA)
    ax.set_ylabel("Доля верных ответов")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", fontsize=10.5)
    save(fig, 11, "Сравнение правил учёта контекста диалога")


for fn in (fig_architecture, fig_data, fig_baseline, fig_models, fig_styles, fig_threshold, fig_confidence,
           fig_latency, fig_context):
    fn()
