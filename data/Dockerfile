# образ для скриптов сбора корпуса; результаты пишутся на хост через volume, а не внутрь образа
FROM python:3.12-slim

WORKDIR /data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY collect ./collect

ENTRYPOINT ["python", "-m", "collect"]
