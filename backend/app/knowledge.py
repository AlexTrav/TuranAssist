import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from .config import KNOWLEDGE_DIR, MANIFEST_PATH
from .tuition import Tuition

# ответ, когда уверенность модели ниже порога: честно говорим «не понял» и предлагаем темы
FALLBACK = {
    "ru": "Я не уверен, что правильно понял вопрос. Возможно, вы имели в виду одну из тем ниже – "
          "или переформулируйте вопрос. Точную информацию можно уточнить в приёмной комиссии: +7 (727) 260 40 00.",
    "kk": "Сұрағыңызды дұрыс түсінгеніме сенімді емеспін. Мүмкін, төмендегі тақырыптардың бірін меңзеген "
          "шығарсыз – немесе сұрақты басқаша қойыңыз. Нақты ақпаратты қабылдау комиссиясынан білуге болады: "
          "+7 (727) 260 40 00.",
    "en": "I am not sure I understood your question. Perhaps you meant one of the topics below – "
          "or try rephrasing. You can also contact the admissions office: +7 (727) 260 40 00.",
}


@dataclass
class Intent:
    id: str
    group: str
    title: dict[str, str]
    answer: dict[str, str]
    sources: list[str]


# база ответов (data/knowledge) и ссылки на первоисточники из манифеста корпуса
class Knowledge:
    def __init__(self, knowledge_dir: Path = KNOWLEDGE_DIR, manifest_path: Path = MANIFEST_PATH):
        groups = yaml.safe_load((knowledge_dir / "groups.yaml").read_text(encoding="utf-8"))["groups"]
        self.groups = [{"id": g["id"], "title": g["title"]} for g in groups]
        self.intents: dict[str, Intent] = {}
        for path in sorted((knowledge_dir / "intents").glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            for item in data["intents"]:
                self.intents[item["id"]] = Intent(
                    id=item["id"], group=data["group"], title=item["title"],
                    answer={lang: text.strip() for lang, text in item["answer"].items()},
                    sources=item.get("sources", []))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self._urls = {(r["id"], r["locale"]): r["url"] for r in manifest if "file" in r}
        self.tuition = Tuition()

    def title(self, intent: str, lang: str) -> str:
        return self.intents[intent].title[lang]

    def answer(self, intent: str, lang: str) -> str:
        return self.intents[intent].answer[lang]

    # ссылка «Подробнее»: первый источник интента на языке пользователя, если его нет – русская версия
    def source_url(self, intent: str, lang: str) -> str | None:
        for source in self.intents[intent].sources:
            url = self._urls.get((source, lang)) or self._urls.get((source, "ru"))
            if url:
                return url
        return None
