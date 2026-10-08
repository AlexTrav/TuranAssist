# TuranAssist

[![CI](https://github.com/AlexTrav/TuranAssist/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexTrav/TuranAssist/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Рубежное задание по курсу «Технологии разработки программного обеспечения для систем
реального времени»: чат-бот с NLP – ассистент студента и абитуриента Университета «Туран».
Отвечает на вопросы о поступлении, стоимости обучения, грантах, учебном процессе,
общежитии и документах на русском, казахском и английском языках – в веб-чате и в Telegram.

Автор: **Алексей Нерезов**.

Условие задания: [ТЗ.md](ТЗ.md).

> Проект в разработке.

## Структура проекта

```
TuranAssist/
  data/      – сбор данных с сайта и из нормативных документов, база ответов, наборы фраз
  model/     – baseline (BoW, TF-IDF), Colab-ноутбук с трансформером, артефакты и метрики
  backend/   – FastAPI: NLP-конвейер, REST API, Telegram-бот (webhook), метрики задержек
  frontend/  – Vue 3 + TypeScript + Tailwind CSS: чат, производительность, о проекте
```

## Запуск

Всё запускается в Docker, локальные Python и Node не нужны (на Windows – из Git Bash):

```bash
make up      # бэкенд и фронтенд: http://localhost:8080 (API – http://localhost:8000)
make down    # остановить
make test    # все проверки, как в CI: данные, pytest бэкенда, Vitest и сборка фронтенда
```

Бэкенд в compose ограничен 512 МБ и 0,5 CPU, фронтенд стартует после healthcheck бэкенда.
Telegram-бот локально – `cd backend && make bot-dev` (токен в `backend/.env`).

## Деплой

- **Бэкенд** – Render, Docker, бесплатный тариф: описание сервиса в [render.yaml](render.yaml).
- **Фронтенд** – GitHub Pages: [deploy-pages.yml](.github/workflows/deploy-pages.yml) собирает
  статику с адресом бэкенда на Render при каждом push, затрагивающем `frontend/`.
- **CI** – [ci.yml](.github/workflows/ci.yml): проверка базы ответов и наборов фраз, pytest, Vitest,
  проверка типов и сборка – теми же `make`-командами и в тех же образах, что локально.

## Лицензия

[MIT](LICENSE)
