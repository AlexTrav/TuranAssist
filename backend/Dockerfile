# образ бэкенда; контекст сборки – корень репозитория (нужны data/knowledge и model/artifacts)
FROM python:3.12-slim AS app

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend MODEL_CACHE_DIR=/app/model/.cache/production

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# энкодер e5 и токенизатор качаются с фиксированного коммита Hugging Face с проверкой SHA-256;
# отдельный слой до копирования кода – правки кода не вызывают повторную загрузку 130 МБ
COPY backend/app/__init__.py backend/app/config.py backend/app/
COPY backend/app/nlp/__init__.py backend/app/nlp/model_files.py backend/app/nlp/
RUN python -m app.nlp.model_files

COPY data/knowledge data/knowledge
COPY data/corpus/manifest.json data/corpus/manifest.json
# фразы тестового набора – для нагрузочного теста по кнопке (задержка, а не точность)
COPY data/phrases/test data/phrases/test
COPY model/artifacts/production model/artifacts/production
COPY model/artifacts/baseline/model.joblib model/artifacts/baseline/model.joblib
COPY model/reports/ensemble/metrics.json model/reports/ensemble/metrics.json
COPY backend/app backend/app

WORKDIR /app/backend
EXPOSE 8000
# Render передаёт порт в переменной PORT, локально – 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]


# образ для автотестов: тот же продакшн-образ плюс pytest
FROM app AS test
COPY backend/requirements-dev.txt /app/backend/requirements-dev.txt
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY backend/pytest.ini /app/backend/pytest.ini
COPY backend/tests /app/backend/tests
# вопросы для ручной проверки (data_test) – часть из них прогоняет автотест test_data_test.py
COPY data_test /app/data_test
CMD ["python", "-m", "pytest"]


# последняя стадия – продакшн: Render и docker build без --target собирают именно её
FROM app AS production
