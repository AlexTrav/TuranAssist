# образ для обучения и оценки baseline-моделей; контекст сборки – корень репозитория,
# потому что нужна предобработка из backend/app/nlp (та же, что в продакшне)
FROM python:3.12-slim

WORKDIR /work

COPY model/requirements.txt model/requirements.txt
RUN pip install --no-cache-dir -r model/requirements.txt

COPY backend/app/__init__.py backend/app/__init__.py
COPY backend/app/nlp backend/app/nlp
COPY model/__init__.py model/__init__.py
COPY model/common model/common
COPY model/baseline model/baseline
COPY model/ensemble model/ensemble

ENV PYTHONPATH=/work/backend:/work PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-m", "model.baseline.train_baseline"]
