from pathlib import Path

# корень папки data: data/collect/config.py -> collect -> data
DATA_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = DATA_DIR / "raw"  # сырые JSON страниц и PDF – не попадают в git, воспроизводятся скриптом
CORPUS_DIR = DATA_DIR / "corpus"  # извлечённый текст – хранится в git, из него собирается база ответов

BASE_URL = "https://turan.edu.kz"

# префикс пути для каждого языка: казахская версия сайта открывается без префикса
LOCALE_PREFIX = {"kk": "", "ru": "/ru", "en": "/en"}

# вежливый сбор: представляемся и делаем паузу между запросами, чтобы не нагружать сайт
USER_AGENT = "TuranAssist-collector/1.0 (student project)"
REQUEST_DELAY_SEC = 1.0
TIMEOUT_SEC = 60

# страницы сайта по темам будущих интентов: короткий id (имя файла в корпусе) -> путь на сайте.
# id короткие намеренно – путь к проекту на Windows и так близок к лимиту в 260 символов
PAGES: dict[str, dict[str, str]] = {
    "admission": {
        "how-to-enroll": "how-to-enroll-in-turan",
        "bachelor": "academic-degree/baccalaureate",
        "master": "academic-degree/masters-degree",
        "phd": "academic-degree/phd",
        "foundation": "faculty/foundation",
        "continuing-education": "institute-of-continuing-education",
    },
    "finance": {
        "tuition-fee": "tuition-fee",
        "grants-discounts": "grants-and-discounts",
        "grant-application": "grant-education-application",
        "payment-details": "payment-details",
    },
    "study": {
        "educational-process": "educational-process",
        "student-guide": "educational-process/putevoditel-studenta",
        "calendar-bachelor": "educational-process/academic-calendar",
        "schedule-bachelor": "educational-process/schedule",
        "practice-bachelor": "educational-process/practice",
        "calendar-master": "educational-process/master-degree-academic-calendar",
        "schedule-master": "educational-process/master-degree-schedule",
        "practice-master": "educational-process/master-degree-practice-internship",
        "calendar-phd": "educational-process/phd-academic-calendar",
        "calendar-foundation": "educational-process/akademicheskiy-kalendar-found",
        "user-instructions": "educational-process/instruktsii-dlya-polzovatelya",
        "student-meetings": "educational-process/regulations-for-student-meetings-on-educational-process-matters",
        "transfers-leave": "educational-process/perevody-vosstanovleniya-akademicheskiy-otpusk",
        "reference-documents": "reference-documents",
    },
    "faculties": {
        "faculty-business": "faculty/faculty-of-business-administration",
        "faculty-digital-arts": "faculty/faculty-of-digital-technologies-and-arts",
        "faculty-economics": "faculty/faculty-of-economics",
        "faculty-humanities-law": "faculty/faculty-of-humanities-and-law",
    },
    "student_life": {
        "student-life": "student-life",
        "student-support-center": "student-support-center",
        "dormitory": "application-for-accommodation-in-a-student-house",
        "medical-center": "medical-center",
        "career-center": "career-and-leadership-center",
        "inclusive-education": "about/inclusive-education",
        "library": "library",
        "library-rules": "library/terms-of-the-library-use",
        "library-resources": "library/turan-library-resources",
    },
    "international": {
        "international": "international-cooperation",
        "international-faq": "international-cooperation/faq",
        "academic-mobility": "international-cooperation/academic-mobility-of-students",
        "erasmus": "international-cooperation/erasmus",
        "foreign-citizens": "international-cooperation/reception-of-foreign-citizens",
        "scholarships": "international-cooperation/scholarship-programs",
        "international-exams": "international-cooperation/international-exams",
    },
    "about": {
        "about": "about",
        "accreditation": "about/ratings-and-accreditations",
        "contacts": "contacts",
    },
}

# страницы, где все таблицы – списки людей (вакантные гранты: ФИО, GPA, статус заявки);
# таблицы на них отбрасываются целиком, текст положения о грантах остаётся
PAGES_WITHOUT_TABLES = {"grant-application"}

# PDF-документы на Google Drive: ссылку ищем на указанной странице сайта по началу её подписи
# (на каждом языке своя); если подходящих ссылок несколько, берётся первая – на сайте
# документы текущего учебного года идут первыми
DOCUMENTS: dict[str, dict] = {
    "academic-policy-2025-2026": {
        "page": "reference-documents",
        "match": {
            "ru": "Академическая политика 2025-2026",
            "kk": "2025-2026 оқу жылының академиялық саясаты",
            "en": "Academic policy of the 2025-2026",
        },
    },
    "assessment-regulation": {
        "page": "reference-documents",
        "match": {
            "ru": "Положение о порядке проведения текущего контроля",
            "kk": "Тұран университетінде білім алушылардың үлгеріміне",
            "en": "Regulation on the procedure for conducting current control",
        },
    },
    "student-code": {
        "page": "reference-documents",
        "match": {"ru": "Кодекс студента", "kk": "Студенттің кодексі", "en": "Student code"},
    },
    "admission-rules-2026-2027": {
        "page": "how-to-enroll-in-turan",
        "match": {
            "ru": "Правила приема на обучение в университет «Туран» на 2026-2027",
            "kk": "«Тұран» университетінде оқуға қабылдаудың 2026-2027",
            "en": "Admission Rules for Enrollment at Turan University for the 2026–2027",
        },
    },
    "academic-calendar-bachelor-2026-2027": {
        "page": "educational-process/academic-calendar",
        "match": {
            "ru": "Открыть академический календарь",
            "kk": "Академиялық күнтізбені ашу",
            "en": "Open the academic calendar",
        },
    },
    "academic-calendar-master-profile-2026-2027": {
        "page": "educational-process/master-degree-academic-calendar",
        "match": {
            "ru": "Академический календарь профильной магистратуры Университета «Туран» на 2026",
            "kk": "«Тұран» университеті бейіндік магистратурасының 2026",
            "en": "Academic Calendar of the Professional Master's Program at Turan University for the 2026",
        },
    },
    "academic-calendar-master-research-2026-2027": {
        "page": "educational-process/master-degree-academic-calendar",
        "match": {
            "ru": "Академический календарь научно-педагогической магистратуры Университета «Туран» на 2026",
            "kk": "«Тұран» университеті ғылыми-педагогикалық магистратурасының 2026",
            "en": "Academic Calendar of the Research and Pedagogical Master's Program at Turan University for the 2026",
        },
    },
}
# не собираются: «Политика использования ИИ» – владелец запретил скачивание файла на Google Drive
# (ссылка на неё остаётся в корпусе вместе со страницей «Нормативные документы»), протокол
# конкурсной комиссии по грантам – содержит персональные данные претендентов
