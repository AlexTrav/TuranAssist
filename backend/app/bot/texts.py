# тексты интерфейса Telegram-бота на трёх языках; ответы на вопросы берутся из базы знаний
START = {
    "ru": "Здравствуйте! Я TuranAssist – помощник абитуриентов и студентов Университета «Туран».\n\n"
          "Задайте вопрос своими словами: о поступлении, стоимости, грантах, учёбе, общежитии или контактах. "
          "Отвечаю на языке вопроса – русском, казахском или английском.\n\n"
          "/topics – темы, /lang – язык ответов, /help – справка.",
    "kk": "Сәлеметсіз бе! Мен TuranAssist – «Тұран» университетінің талапкерлері мен студенттеріне арналған көмекшімін.\n\n"
          "Сұрағыңызды өз сөзіңізбен қойыңыз: түсу, оқу ақысы, гранттар, оқу, жатақхана немесе байланыстар туралы. "
          "Сұрақ тілінде – қазақ, орыс немесе ағылшын тілінде жауап беремін.\n\n"
          "/topics – тақырыптар, /lang – жауап тілі, /help – анықтама.",
    "en": "Hello! I am TuranAssist, an assistant for applicants and students of Turan University.\n\n"
          "Ask your question in your own words: admission, tuition, grants, studies, dormitory or contacts. "
          "I answer in the language of your question – Kazakh, Russian or English.\n\n"
          "/topics – topics, /lang – answer language, /help – help.",
}
HELP = {
    "ru": "Как пользоваться:\n"
          "- просто напишите вопрос, например «Сколько стоит обучение?» или «Есть ли общежитие?»;\n"
          "- /topics – выбрать тему кнопками;\n"
          "- /lang – язык ответов (по умолчанию – язык вашего вопроса).\n\n"
          "Ответы основаны на официальном сайте turan.edu.kz и документах университета. "
          "Если я не уверен, что понял вопрос, предложу похожие темы.",
    "kk": "Қалай пайдалану керек:\n"
          "- сұрағыңызды жазыңыз, мысалы «Оқу ақысы қанша?» немесе «Жатақхана бар ма?»;\n"
          "- /topics – тақырыпты батырмалармен таңдау;\n"
          "- /lang – жауап тілі (әдепкі бойынша – сұрағыңыздың тілі).\n\n"
          "Жауаптар turan.edu.kz ресми сайты мен университет құжаттарына негізделген. "
          "Сұрақты түсінгеніме сенімді болмасам, ұқсас тақырыптарды ұсынамын.",
    "en": "How to use:\n"
          "- just type a question, for example \"How much is the tuition?\" or \"Is there a dormitory?\";\n"
          "- /topics – choose a topic with buttons;\n"
          "- /lang – answer language (by default, the language of your question).\n\n"
          "Answers are based on the official website turan.edu.kz and university documents. "
          "If I am not sure I understood you, I will suggest related topics.",
}
CHOOSE_LANG = {"ru": "Выберите язык ответов:", "kk": "Жауап тілін таңдаңыз:", "en": "Choose the answer language:"}
LANG_SET = {"ru": "Готово, отвечаю на русском.", "kk": "Дайын, қазақ тілінде жауап беремін.",
            "en": "Done, I will answer in English."}
# режим по умолчанию: ответ на языке вопроса
LANG_AUTO = {"ru": "Готово, отвечаю на языке вашего вопроса.", "kk": "Дайын, сұрағыңыздың тілінде жауап беремін.",
             "en": "Done, I will answer in the language of your question."}
AUTO_BUTTON = {"ru": "Как в вопросе", "kk": "Сұрақ тілінде", "en": "Same as question"}
TOPICS = {"ru": "Выберите тему:", "kk": "Тақырыпты таңдаңыз:", "en": "Choose a topic:"}
MORE = {"ru": "Подробнее", "kk": "Толығырақ", "en": "More"}
BACK = {"ru": "« Темы", "kk": "« Тақырыптар", "en": "« Topics"}
RATE_LIMITED = {"ru": "Слишком много сообщений. Подождите минуту, пожалуйста.",
                "kk": "Хабарлама тым көп. Бір минут күте тұрыңыз.",
                "en": "Too many messages. Please wait a minute."}
NOT_TEXT = {"ru": "Я понимаю только текстовые вопросы.", "kk": "Мен тек мәтіндік сұрақтарды түсінемін.",
            "en": "I can only understand text questions."}
TOO_LONG = {"ru": "Вопрос слишком длинный – сформулируйте его короче.",
            "kk": "Сұрақ тым ұзын – қысқарақ қойыңыз.", "en": "The question is too long – please make it shorter."}
LANG_BUTTONS = [("ru", "Русский"), ("kk", "Қазақша"), ("en", "English")]
# описания команд в меню Telegram для каждого языка интерфейса пользователя
COMMANDS = {
    "ru": [("start", "Начать"), ("topics", "Темы"), ("lang", "Язык ответов"), ("help", "Справка")],
    "kk": [("start", "Бастау"), ("topics", "Тақырыптар"), ("lang", "Жауап тілі"), ("help", "Анықтама")],
    "en": [("start", "Start"), ("topics", "Topics"), ("lang", "Answer language"), ("help", "Help")],
}
