import asyncio
import json
import sys
from pathlib import Path

from ..config import TELEGRAM_BOT_TOKEN
from .telegram_api import TelegramClient
from .texts import COMMANDS

NAME = "TuranAssist"
# короткое описание – в профиле и при пересылке ссылки на бота (до 120 символов)
SHORT_DESCRIPTION = {
    "ru": "Неофициальный помощник по Университету «Туран»: поступление, стоимость, гранты, учёба. Ru, kk, en.",
    "kk": "«Тұран» университеті бойынша бейресми көмекші: түсу, оқу ақысы, гранттар, оқу. Kk, ru, en.",
    "en": "Unofficial assistant for Turan University: admission, tuition, grants, studies. En, ru, kk.",
}
# описание – в пустом чате до первого сообщения (до 512 символов)
DESCRIPTION = {
    "ru": "Я TuranAssist – чат-бот, который отвечает на вопросы абитуриентов и студентов Университета «Туран».\n\n"
          "Спросите своими словами: как поступить, сколько стоит обучение, какие есть гранты и скидки, когда сессия, "
          "как получить общежитие или справку. Понимаю русский, казахский и английский.\n\n"
          "Ответы основаны на сайте turan.edu.kz и документах университета. Это учебный проект, а не официальный "
          "сервис университета – важные детали уточняйте в приёмной комиссии.",
    "kk": "Мен TuranAssist – «Тұран» университетінің талапкерлері мен студенттерінің сұрақтарына жауап беретін чат-ботпын.\n\n"
          "Өз сөзіңізбен сұраңыз: қалай түсуге болады, оқу ақысы қанша, қандай гранттар мен жеңілдіктер бар, сессия қашан, "
          "жатақхана немесе анықтама қалай алынады. Қазақ, орыс және ағылшын тілдерін түсінемін.\n\n"
          "Жауаптар turan.edu.kz сайты мен университет құжаттарына негізделген. Бұл университеттің ресми қызметі емес, "
          "оқу жобасы – маңызды мәліметтерді қабылдау комиссиясынан нақтылаңыз.",
    "en": "I am TuranAssist, a chatbot that answers questions from applicants and students of Turan University.\n\n"
          "Ask in your own words: how to apply, how much tuition costs, what grants and discounts exist, when exams are, "
          "how to get a dormitory place or a certificate. I understand Kazakh, Russian and English.\n\n"
          "Answers are based on turan.edu.kz and university documents. This is a student project, not an official "
          "university service – please confirm important details with the admissions office.",
}


# меню команд: русское – по умолчанию для всех, казахское и английское – по языку Telegram пользователя
async def apply_commands(client: TelegramClient) -> None:
    for lang, commands in COMMANDS.items():
        payload = [{"command": c, "description": d} for c, d in commands]
        await client.call("setMyCommands", commands=payload, language_code=None if lang == "ru" else lang)


# оформление профиля бота: имя, описания и меню на трёх языках, аватар (JPG)
async def main(photo: Path | None) -> None:
    if not TELEGRAM_BOT_TOKEN:
        sys.exit("Не задан TELEGRAM_BOT_TOKEN (backend/.env)")
    for lang in DESCRIPTION:
        assert len(SHORT_DESCRIPTION[lang]) <= 120, f"короткое описание {lang} длиннее 120 символов"
        assert len(DESCRIPTION[lang]) <= 512, f"описание {lang} длиннее 512 символов"
    client = TelegramClient(TELEGRAM_BOT_TOKEN)
    try:
        for lang in DESCRIPTION:
            code = None if lang == "ru" else lang
            await client.call("setMyName", name=NAME, language_code=code)
            await client.call("setMyShortDescription", short_description=SHORT_DESCRIPTION[lang], language_code=code)
            await client.call("setMyDescription", description=DESCRIPTION[lang], language_code=code)
        await apply_commands(client)
        if photo:
            await client.set_profile_photo(photo)
        me = await client.call("getMe")
        print(f"профиль @{me['username']} оформлен: имя, описания и команды (ru/kk/en)"
              + (", аватар" if photo else ""))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]) if len(sys.argv) > 1 else None))
