import html
import json
import re

# служебные props Inertia: меню, подвал, переводы интерфейса – одинаковы на всех страницах, не контент
LAYOUT_PROPS = {
    "errors", "locale", "browserSiteTitle", "ui", "name", "quote", "auth", "sidebarOpen",
    "headerMenu", "headerMenuPromo", "corporationBar", "siteFooter", "mourningMode",
    "offerForm", "breadcrumbs", "sidebarItems", "facultySidebar", "metaTitle",
    "metaDescription", "breadcrumbParent", "breadcrumbCurrent",
}

# ключи, значения которых – заголовки блоков
HEADING_KEYS = {
    "title", "label", "blockTitle", "section_heading", "slider_title", "pageTitle",
    "pageTitleFixed", "contactsTitle", "emails_section_label", "introTitle", "cardsTitle", "heroTitle",
}

# ключи, значения которых – текст (часто с HTML-разметкой)
TEXT_KEYS = {
    "text", "body", "content", "introHtml", "intro", "description", "value", "address",
    "name", "position", "link_text", "question", "answer", "bio", "html", "introDescription",
}

# ссылки на документы оставляем в тексте – по ним бот сможет отправить пользователя к первоисточнику
DOC_LINK_RE = re.compile(r"drive\.google\.com|docs\.google\.com|\.pdf\b|\.docx?\b", re.IGNORECASE)


# извлекает JSON страницы, который Inertia.js кладёт в атрибут data-page корневого элемента
def parse_inertia_page(page_html: str) -> dict:
    match = re.search(r'data-page="([^"]*)"', page_html)
    if match is None:
        raise ValueError("на странице нет атрибута data-page")
    return json.loads(html.unescape(match.group(1)))


# невидимые символы-заполнители, которыми на сайте «раздвигают» пустые блоки
INVISIBLE_RE = re.compile("[\u3164\u200b\u200c\u200d\u2060\ufeff]")


# заголовки столбцов с ФИО: такие таблицы (списки претендентов на гранты с GPA) не собираем –
# это персональные данные, даже если сайт публикует их открыто
PERSONAL_DATA_RE = re.compile(r"Ф\.?\s*И\.?\s*О|аты-жөні|full\s*name", re.IGNORECASE)


# строка таблицы целиком в одну строку «| ячейка | ячейка |» – иначе цена отрывается от программы
def _table_to_lines(match: re.Match) -> str:
    table = match.group(0)
    if PERSONAL_DATA_RE.search(re.sub(r"<[^>]+>", "", table)):
        return "\n"
    rows = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", table, flags=re.S | re.I):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S | re.I)
        cells = [html_to_text(cell).replace("\n", " ") for cell in cells]
        if any(cells):
            rows.append("| " + " | ".join(cells) + " |")
    return "\n" + "\n".join(rows) + "\n"


# переводит HTML-фрагмент в простой текст, сохраняя абзацы, пункты списков, таблицы и ссылки на документы
def html_to_text(fragment: str, drop_tables: bool = False) -> str:
    # адрес оставляем у документов и внешних ресурсов (регистрация на экзамен, порталы);
    # внутренние ссылки на страницы turan.edu.kz – навигация, они не нужны
    def keep_doc_link(m: re.Match) -> str:
        href, label = m.group(1), m.group(2)
        external = href.startswith("http") and "://turan.edu.kz" not in href
        return f"{label} ({href})" if DOC_LINK_RE.search(href) or external else label

    table_repl = (lambda m: "\n") if drop_tables else _table_to_lines
    text = re.sub(r"<table[^>]*>.*?</table>", table_repl, fragment, flags=re.S | re.I)
    text = re.sub(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', keep_doc_link, text, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<li[^>]*>", "\n- ", text, flags=re.I)
    text = re.sub(r"</(p|div|h[1-6]|li|ul|ol)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = normalize_dashes(INVISIBLE_RE.sub("", html.unescape(text).replace("\xa0", " ")))
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    # убираем пустые пункты списка, оставшиеся от вложенных <li><p>
    lines = [line for line in lines if line and line != "-"]
    return "\n".join(lines)


# строки-идентификаторы (ссылки, пути, css-классы) – не текст для пользователя
def _is_noise(value: str) -> bool:
    v = value.strip()
    return (
        not v
        or v.startswith(("http://", "https://", "/", "#", "mailto:", "tel:"))
        or not re.search(r"[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]", v)
    )


# обходит props страницы по порядку и собирает markdown: заголовки блоков, текст, ссылки на документы;
# drop_tables выбрасывает все таблицы страницы (для страниц, где таблицы – списки людей)
def props_to_markdown(props: dict, drop_tables: bool = False) -> str:
    lines: list[str] = []

    def emit(line: str) -> None:
        # соседние дубли появляются, когда заголовок вкладки повторяется заголовком блока
        if line and (not lines or lines[-1] != line):
            lines.append(line)

    def walk(node, key: str | None = None) -> None:
        if isinstance(node, dict):
            # элемент списка документов: название и ссылка на файл
            text, url = node.get("text"), node.get("url")
            if isinstance(text, str) and isinstance(url, str) and DOC_LINK_RE.search(url):
                label = html_to_text(text)
                if label:
                    emit(f"- {label} ({url})")
                return
            # явная ссылка из блока ссылок (онлайн-заявка, правила проживания, регистрация на экзамен) –
            # оставляем вместе с адресом; ссылки навигации по сайту (url_mode: page) не нужны
            link_label = node.get("title") or node.get("text") or node.get("label")
            leaf = not any(isinstance(v, (dict, list)) for v in node.values())
            if (leaf and node.get("url_mode") == "custom" and isinstance(link_label, str)
                    and isinstance(url, str) and url.startswith("http")):
                label = html_to_text(link_label)
                if label:
                    emit(f"- {label} ({url})")
                return
            # пара «подпись: значение» (телефоны в контактах) – одной строкой, иначе номер
            # без букв отсеется как служебная строка и отделится от подписи
            label, value = node.get("label"), node.get("value")
            if isinstance(label, str) and isinstance(value, str) and value.strip():
                emit(f"{html_to_text(label)} {html_to_text(value)}")
                return
            for k, v in node.items():
                walk(v, k)
        elif isinstance(node, list):
            for item in node:
                walk(item, key)
        elif isinstance(node, str) and not _is_noise(node):
            if key in HEADING_KEYS:
                emit(f"### {html_to_text(node)}")
            elif key in TEXT_KEYS:
                for line in html_to_text(node, drop_tables).split("\n"):
                    emit(line)

    for prop_key, value in props.items():
        if prop_key not in LAYOUT_PROPS:
            walk(value, prop_key)
    return "\n".join(lines)


# заголовок страницы: в разных компонентах сайта он лежит под разными ключами
def page_title(props: dict) -> str:
    page = props.get("page") if isinstance(props.get("page"), dict) else {}
    for value in (page.get("title"), props.get("title"), props.get("pageTitle"),
                  props.get("pageTitleFixed"), props.get("metaTitle")):
        if isinstance(value, str) and value.strip():
            return html_to_text(value)
    return ""


# собирает слова PDF (x0, y0, x1, y1, текст) в строки: слова с близкой вертикальной серединой
# считаются одной строкой, а широкий горизонтальный разрыв – границей ячейки таблицы
def group_words_into_lines(words: list[tuple], y_tolerance: float = 3.0, cell_gap: float = 25.0) -> list[str]:
    rows: list[list[tuple]] = []
    for word in sorted(words, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
        middle = (word[1] + word[3]) / 2
        if rows and abs(middle - rows[-1][0]) <= y_tolerance:
            rows[-1][1].append(word)
        else:
            rows.append([middle, [word]])
    lines = []
    for _, row in rows:
        row.sort(key=lambda w: w[0])
        parts = [row[0][4]]
        for prev, word in zip(row, row[1:]):
            parts.append((" | " if word[0] - prev[2] > cell_gap else " ") + word[4])
        lines.append("".join(parts))
    return lines


# склеивает текст PDF: переносы по слогам, номера страниц, лишние пробелы
def clean_pdf_text(raw: str) -> str:
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", normalize_dashes(raw))
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.split("\n")]
    lines = [line for line in lines if line and not re.fullmatch(r"\d{1,3}", line)]
    return "\n".join(lines)


# длинное тире в первоисточниках заменяем средним – единое оформление текстов проекта
def normalize_dashes(text: str) -> str:
    return text.replace("\u2014", "\u2013")
