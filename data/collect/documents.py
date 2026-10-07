import re
import time
from datetime import date
from functools import cache

import pymupdf
import requests

from .config import CORPUS_DIR, DOCUMENTS, LOCALE_PREFIX, RAW_DIR, REQUEST_DELAY_SEC, TIMEOUT_SEC
from .extract import clean_pdf_text, group_words_into_lines, props_to_markdown
from .site import fetch_props, session

DRIVE_ID_RE = re.compile(r"/d/([\w-]+)")
# ссылка на документ в корпусе: «подпись (https://drive.google.com/...)» или «подпись (https://docs.google.com/...)»
DOC_LINK_RE = re.compile(r"^(?:- )?(.+?) \((https://(?:drive|docs)\.google\.com/[^)\s]+)\)$", re.M)
DRIVE_DOWNLOAD_URL = "https://drive.google.com/uc?export=download&id={file_id}"
# документ Google Docs (в том числе загруженный .docx) отдаётся сразу простым текстом
DOCS_TXT_URL = "https://docs.google.com/document/d/{file_id}/export?format=txt"


# все ссылки на Google Drive и Google Docs со страницы сайта: пары (подпись, ссылка) в порядке на странице
@cache
def list_doc_links(slug: str, locale: str) -> tuple[tuple[str, str], ...]:
    markdown = props_to_markdown(fetch_props(slug, locale))
    return tuple(DOC_LINK_RE.findall(markdown))


# текст страницы PDF построчно: стандартный get_text() читает таблицы по столбцам
# и отрывает даты календаря от событий, поэтому собираем строки из слов по координатам
def page_to_lines(page: pymupdf.Page) -> str:
    words = [(w[0], w[1], w[2], w[3], w[4]) for w in page.get_text("words")]
    return "\n".join(group_words_into_lines(words))


def _get(url: str) -> requests.Response:
    response = session.get(url, timeout=TIMEOUT_SEC)
    response.raise_for_status()
    time.sleep(REQUEST_DELAY_SEC)
    return response


# скачивает PDF с Google Drive по ссылке вида .../file/d/<id>/view
def download_pdf(view_url: str) -> bytes:
    content = _get(DRIVE_DOWNLOAD_URL.format(file_id=DRIVE_ID_RE.search(view_url).group(1))).content
    if not content.startswith(b"%PDF"):
        raise ValueError("Google Drive вернул не PDF (файл закрыт или требует подтверждения)")
    return content


# скачивает документ Google Docs простым текстом по ссылке вида .../document/d/<id>/edit
def download_doc_text(view_url: str) -> str:
    response = _get(DOCS_TXT_URL.format(file_id=DRIVE_ID_RE.search(view_url).group(1)))
    if not response.headers.get("content-type", "").startswith("text/plain"):
        raise ValueError("Google Docs не отдал текст (документ закрыт)")
    return response.content.decode("utf-8-sig")


# скачивает документ, сохраняет оригинал в raw/ и возвращает (число страниц или None, текст)
def fetch_document(url: str, raw_base) -> tuple[int | None, str]:
    if "docs.google.com/document" in url:
        text = download_doc_text(url)
        raw_base.with_suffix(".txt").write_text(text, encoding="utf-8")
        return None, clean_pdf_text(text)
    pdf_bytes = download_pdf(url)
    raw_base.with_suffix(".pdf").write_bytes(pdf_bytes)
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
        return pdf.page_count, clean_pdf_text("\n".join(page_to_lines(page) for page in pdf))


# скачивает документы из DOCUMENTS на всех языках и извлекает из них текст
def collect_documents() -> list[dict]:
    today = date.today().isoformat()
    records = []
    for doc_id, spec in DOCUMENTS.items():
        for locale in LOCALE_PREFIX:
            base = {"type": "document", "id": doc_id, "locale": locale}
            prefix = spec["match"][locale]
            try:
                links = list_doc_links(spec["page"], locale)
            except (requests.RequestException, ValueError) as exc:
                print(f"  ! {locale} {doc_id}: страница {spec['page']} недоступна: {exc}")
                records.append({**base, "error": f"страница {spec['page']} недоступна"})
                continue

            found = next(((t, u) for t, u in links if t.startswith(prefix)), None)
            if found is None:
                print(f"  ! {locale} {doc_id}: ссылка не найдена на странице {spec['page']}")
                records.append({**base, "error": f"ссылка не найдена на странице {spec['page']}"})
                continue

            title, url = found
            raw_base = RAW_DIR / "docs" / locale / doc_id
            raw_base.parent.mkdir(parents=True, exist_ok=True)
            try:
                pages, body = fetch_document(url, raw_base)
            except (requests.RequestException, ValueError) as exc:
                print(f"  ! {locale} {doc_id}: {exc}")
                records.append({**base, "url": url, "error": str(exc)})
                continue

            md_path = CORPUS_DIR / "docs" / locale / f"{doc_id}.md"
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(f"# {title}\n\nИсточник: {url}\nДата сбора: {today}\n\n{body}\n",
                               encoding="utf-8")

            # PDF-скан без текстового слоя даст почти пустой текст – такой документ стоит проверить вручную
            warn = "  (мало текста – возможно, скан)" if pages and len(body) < 200 * pages else ""
            size = f"{pages} стр., " if pages else ""
            print(f"  {locale} {doc_id}: {size}{len(body)} симв.{warn}")
            records.append({**base, "title": title, "url": url, "pages": pages, "chars": len(body),
                            "file": md_path.relative_to(CORPUS_DIR).as_posix(), "fetched_at": today})
    return records
