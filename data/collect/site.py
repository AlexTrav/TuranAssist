import json
import time
from datetime import date

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from .config import (BASE_URL, CORPUS_DIR, LOCALE_PREFIX, PAGES, PAGES_WITHOUT_TABLES, RAW_DIR, REQUEST_DELAY_SEC,
                     TIMEOUT_SEC, USER_AGENT)
from .extract import page_title, parse_inertia_page, props_to_markdown

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT
# сайт иногда обрывает соединение – повторяем запрос с нарастающей паузой (2, 4, 8 с)
_retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
session.mount("https://", HTTPAdapter(max_retries=_retry))
# страница без версии на нужном языке зацикливает редиректы – обрываем цикл быстро
session.max_redirects = 5


def page_url(slug: str, locale: str) -> str:
    return f"{BASE_URL}{LOCALE_PREFIX[locale]}/{slug}"


# скачивает страницу и возвращает props Inertia (весь контент страницы в виде JSON)
def fetch_props(slug: str, locale: str) -> dict:
    response = session.get(page_url(slug, locale), timeout=TIMEOUT_SEC)
    response.raise_for_status()
    time.sleep(REQUEST_DELAY_SEC)
    return parse_inertia_page(response.text)["props"]


# собирает все страницы из PAGES на всех языках: сырой JSON в raw/, markdown в corpus/
def collect_pages() -> list[dict]:
    today = date.today().isoformat()
    records = []
    for topic, pages in PAGES.items():
        for page_id, slug in pages.items():
            for locale in LOCALE_PREFIX:
                url = page_url(slug, locale)
                base = {"type": "page", "topic": topic, "id": page_id, "slug": slug, "locale": locale, "url": url}
                try:
                    props = fetch_props(slug, locale)
                except requests.TooManyRedirects:
                    print(f"  - {locale} {page_id}: нет версии на этом языке")
                    records.append({**base, "missing": "нет версии на этом языке"})
                    continue
                except (requests.RequestException, ValueError) as exc:
                    print(f"  ! {locale} {page_id}: {exc}")
                    records.append({**base, "error": str(exc)})
                    continue

                raw_path = RAW_DIR / "site" / locale / f"{page_id}.json"
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")

                title = page_title(props)
                body = props_to_markdown(props, drop_tables=page_id in PAGES_WITHOUT_TABLES)
                md_path = CORPUS_DIR / "site" / locale / f"{page_id}.md"
                md_path.parent.mkdir(parents=True, exist_ok=True)
                md_path.write_text(f"# {title}\n\nИсточник: {url}\nДата сбора: {today}\n\n{body}\n",
                                   encoding="utf-8")

                print(f"  {locale} {page_id}: {len(body)} симв.")
                records.append({**base, "title": title, "chars": len(body),
                                "file": md_path.relative_to(CORPUS_DIR).as_posix(), "fetched_at": today})
    return records
