.PHONY: up up-d down build logs ps restart test clean

# собрать и поднять весь стек: backend, затем frontend после его healthcheck
# (порядок задан в docker-compose.yml через depends_on: condition: service_healthy)
up:
	docker compose up --build

# то же самое в фоновом режиме
up-d:
	docker compose up --build -d

# остановить и удалить контейнеры
down:
	docker compose down

# пересобрать образы без запуска
build:
	docker compose build

# логи обоих сервисов
logs:
	docker compose logs -f

# статус контейнеров
ps:
	docker compose ps

# перезапустить стек
restart: down up-d

# все проверки, как в CI: база ответов и наборы фраз, pytest бэкенда, Vitest и сборка фронтенда
test:
	$(MAKE) -C data check
	$(MAKE) -C backend test
	$(MAKE) -C frontend test
	$(MAKE) -C frontend build

# остановить стек и удалить образы, созданные docker compose
clean:
	docker compose down --rmi local --volumes
