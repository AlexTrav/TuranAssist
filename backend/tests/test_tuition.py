import pytest

from app.nlp.entities import EntityExtractor, normalize
from app.tuition import Tuition, format_price


@pytest.fixture(scope="module")
def tuition():
    return Tuition()


def test_every_program_has_prices(tuition):
    # полноту таблицы относительно сайта проверяет make check в data/, здесь – что бэкенд видит все цены
    assert set(tuition.prices) == set(tuition.names)
    assert all(tuition.prices[p] for p in tuition.names)
    assert {r["plan"] for rows in tuition.prices.values() for r in rows} == set(tuition.plans)


@pytest.mark.parametrize("text, programs", [
    ("Сколько стоит ВТиПО?", ["computer_engineering"]),
    ("сколько стоит учиться на вт и по", ["computer_engineering"]),
    ("Цена обучения на программиста", ["software_engineering"]),
    ("стоимость ИС", ["information_systems"]),
    ("Сколько стоит история?", []),  # «ис» – только целым словом
    ("Сколько стоит международное право?", ["international_law"]),  # не «право» и не «международные отношения»
    ("Клиническая психология цена", ["clinical_psychology"]),
    ("менеджмент инноваций туризма и гостеприимства", ["tourism_innovation"]),
    ("юрист и экономист сколько стоит", ["jurisprudence", "economics"]),
    ("Учёт и аудит", ["accounting"]),
    ("Есептеу техникасы қанша тұрады?", ["computer_engineering"]),
    ("How much is software engineering?", ["software_engineering"]),
    ("Сколько стоит обучение?", []),
])
def test_program_extraction(tuition, text, programs):
    assert tuition.programs_in(text) == programs


def test_extractor_prefers_longest_match():
    extractor = EntityExtractor({"a": ["психолог"], "b": ["клиническ психолог"]})
    assert extractor.extract("Клиническую психологию") == ["b"]
    assert normalize("ВТ-и-ПО, Ёлка!") == "вт и по елка"


def test_program_answer_uses_level_of_intent(tuition):
    text, programs = tuition.answer("tuition_bachelor", "Сколько стоит ВТиПО?", "ru")
    assert programs == ["computer_engineering"]
    assert "«Вычислительная техника и программное обеспечение»" in text
    assert "- очная, 4 года: 1 476 600 тенге;" in text
    assert "после колледжа, 2 года: 1 925 100 тенге" in text
    assert "магистратура" not in text

    text, _ = tuition.answer("tuition_postgrad", "магистратура ВТиПО", "ru")
    assert "научно-педагогическая магистратура, 2 года: 1 483 500 тенге." in text


def test_program_answer_english_department_and_languages(tuition):
    text, _ = tuition.answer("tuition_bachelor", "международные отношения", "en")
    assert "“International relations”" in text
    assert "full-time, 4 years: 1,476,600 tenge (English department – 1,814,700);" in text
    text, _ = tuition.answer("tuition_bachelor", "Актерлік өнер", "kk")
    assert "күндізгі, 4 жыл: 1 587 000 теңге." in text


def test_falls_back_to_other_level(tuition):
    # клиническая психология есть только в магистратуре – показываем её цены, а не пустой ответ
    text, _ = tuition.answer("tuition_bachelor", "клиническая психология", "ru")
    assert "профильная магистратура, 1 год: 1 573 200 тенге" in text


def test_no_specific_answer_for_other_intents(tuition):
    assert tuition.answer("dormitory", "ВТиПО", "ru") is None
    assert tuition.answer("tuition_bachelor", "Сколько стоит обучение?", "ru") is None


def test_resolve_intent_sums_tuition_probabilities(tuition):
    top = [("tuition_bachelor", 0.49), ("tuition_postgrad", 0.26), ("stipend", 0.05)]
    assert tuition.resolve_intent("ВТиПО сколько стоит", top, 0.58) == ("tuition_bachelor", pytest.approx(0.75))
    assert tuition.resolve_intent("сколько стоит", top, 0.58) is None  # без программы правило не работает
    assert tuition.resolve_intent("ВТиПО сколько стоит", top, 0.8) is None
    assert tuition.resolve_intent("ВТиПО", [("greeting", 0.27), ("academic_mobility", 0.17)], 0.58) is None


def test_format_price():
    assert format_price(1476600, "ru") == "1 476 600"
    assert format_price(1476600, "en") == "1,476,600"


def test_chat_returns_program_price(client):
    data = client.post("/api/chat", json={"text": "Сколько стоит обучение на ВТиПО?"}).json()
    assert data["intent"] == "tuition_bachelor"
    assert data["programs"] == ["computer_engineering"]
    assert "1 476 600 тенге" in data["answer"]


def test_chat_general_tuition_without_program(client, knowledge):
    data = client.post("/api/chat", json={"text": "Сколько стоит обучение в бакалавриате?"}).json()
    assert data["programs"] == []
    assert data["answer"] == knowledge.answer("tuition_bachelor", "ru")


def test_chat_program_question_with_uncertain_model(client):
    # модель делит вероятность между двумя интентами стоимости – программа в вопросе решает в пользу темы
    data = client.post("/api/chat", json={"text": "ВТиПО сколько стоит"}).json()
    assert data["recognized"] is True
    assert data["intent"] == "tuition_bachelor"
    assert data["programs"] == ["computer_engineering"]


@pytest.mark.parametrize("text, intent", [
    ("ВТиПО", "tuition_bachelor"),
    ("ВТиПО цена", "tuition_bachelor"),
    ("цена за год ВТиПО", "tuition_bachelor"),
    ("психология магистратура цена", "tuition_postgrad"),
    ("Есептеу техникасы бағасы", "tuition_bachelor"),
    ("software engineering price", "tuition_bachelor"),
    ("ВТиПО общежитие", None),  # другое слово – решает модель, а не правило цены
    ("Цена", None),  # без программы правило не работает
])
def test_program_query(tuition, text, intent):
    assert tuition.program_query(text) == intent


def test_extractor_rest_drops_entities():
    extractor = EntityExtractor({"ce": ["втипо", "вт и по"]})
    assert extractor.rest("ВТ и ПО, цена?") == ["цена"]
    assert extractor.rest("ВТиПО") == []


def test_chat_program_only_shows_its_price(client):
    # «ВТиПО цена»: модель не уверена ни в одной теме, но программа названа явно – показываем её стоимость
    data = client.post("/api/chat", json={"text": "ВТиПО цена"}).json()
    assert data["recognized"] is True and data["intent"] == "tuition_bachelor"
    assert data["programs"] == ["computer_engineering"]
    assert data["prices"] and data["explain"]["rule"] == "program"
