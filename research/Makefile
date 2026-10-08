.PHONY: collect collect-latency render figures all

# Git Bash на Windows иначе превращает пути контейнера в пути Windows
export MSYS_NO_PATHCONV=1

ROOT := $(CURDIR)/..
# рисунки – в папку отчёта, если передана: make figures FIGURES=/путь/к/Рисункам
FIGURES ?= $(CURDIR)/figures
# образ бэкенда с наборами фраз и папкой research: та же модель и тот же код, что отвечают пользователям
MOUNTS := -v "$(ROOT)/data/phrases:/app/data/phrases:ro" -v "$(CURDIR):/research" -e PYTHONPATH=/app/backend
BACKEND := turanassist-backend

# оценка сервиса: наборы, ошибки, контекст, задержки (0,5 CPU и 512 МБ, как в docker-compose)
collect:
	"$(MAKE)" -C ../backend build
	docker run --rm --cpus=0.5 --memory=512m $(MOUNTS) $(BACKEND) python /research/collect.py

# задержки при разных ограничениях CPU: 1 ядро, 0,5 и 0,1 – как на бесплатном Render
collect-latency:
	"$(MAKE)" -C ../backend build
	docker run --rm --cpus=1 $(MOUNTS) $(BACKEND) python /research/collect.py cpu1
	docker run --rm --cpus=0.5 $(MOUNTS) $(BACKEND) python /research/collect.py cpu05
	docker run --rm --cpus=0.1 $(MOUNTS) $(BACKEND) python /research/collect.py cpu01

# задержки развёрнутого сервиса на Render (около 3 минут из-за rate limit)
render:
	docker run --rm -v "$(CURDIR):/research" python:3.12-slim python /research/render_latency.py

# рисунки по сохранённым метрикам (model/reports и research/results); шрифт Times New Roman – из Windows
figures:
	docker run --rm -v "$(ROOT):/repo:ro" -v "$(FIGURES):/figures" -v "C:/Windows/Fonts:/winfonts:ro" \
		python:3.12-slim sh -c "pip install -q matplotlib==3.10.7 2>/dev/null && python /repo/research/figures.py"

all: collect collect-latency render figures
