import csv

import pytest

from app.config import ROOT

# вопросы для ручной проверки из data_test – здесь проверяются те, что помечены check = yes
# (уверенность далеко от порога); остальные – пограничные и известные ограничения, см. data_test/README.md
with (ROOT / "data_test" / "questions.csv").open(encoding="utf-8", newline="") as f:
    ROWS = [r for r in csv.DictReader(f) if r["check"] == "yes"]


@pytest.mark.parametrize("row", ROWS, ids=[r["text"] for r in ROWS])
def test_data_test_question(client, row):
    data = client.post("/api/chat", json={"text": row["text"]}).json()
    if row["expect"] == "ood":
        assert data["recognized"] is False, f"ожидался «не понял», получено {data['intent']}"
    elif row["expect"].startswith("clarify:"):
        # короткий запрос на несколько тем: бот просит уточнить и предлагает эти темы кнопками
        expected = set(row["expect"].removeprefix("clarify:").split("|"))
        assert data["clarify"] is True, data["intent"]
        assert expected <= {s["intent"] for s in data["suggestions"]}, data["suggestions"]
    else:
        assert data["recognized"] is True and data["intent"] == row["expect"], data["suggestions"]
    if row["program"]:
        assert data["programs"] == [row["program"]]
