import argparse
import json
from collections import defaultdict

from .config import CORPUS_DIR
from .documents import collect_documents
from .site import collect_pages

MANIFEST_PATH = CORPUS_DIR / "manifest.json"


# сводка по корпусу: сколько страниц/документов и символов текста на каждую тему и язык
def print_summary(records: list[dict]) -> None:
    stats: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    errors = missing = 0
    for r in records:
        if "error" in r:
            errors += 1
            continue
        if "missing" in r:
            missing += 1
            continue
        group = r.get("topic", "documents")
        stats[(group, r["locale"])][0] += 1
        stats[(group, r["locale"])][1] += r["chars"]
    print("\nтема            язык  файлов  символов")
    for (group, locale), (count, chars) in sorted(stats.items()):
        print(f"{group:15} {locale:5} {count:6} {chars:9}")
    print(f"нет языковой версии: {missing}, ошибок: {errors}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Сбор корпуса текстов с сайта turan.edu.kz")
    parser.add_argument("--only", choices=["pages", "docs"], help="собрать только страницы или только документы")
    args = parser.parse_args()

    # при частичном сборе сохраняем записи другой части из прошлого манифеста
    old = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else []
    records: list[dict] = []
    if args.only != "docs":
        print("страницы сайта:")
        records += collect_pages()
    else:
        records += [r for r in old if r["type"] == "page"]
    if args.only != "pages":
        print("нормативные документы:")
        records += collect_documents()
    else:
        records += [r for r in old if r["type"] == "document"]

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print_summary(records)


if __name__ == "__main__":
    main()
