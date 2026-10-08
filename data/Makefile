.PHONY: build collect collect-pages collect-docs tuition check clean

IMAGE := turanassist-data

# Git Bash на Windows иначе превращает пути контейнера (/data/raw) в пути Windows
export MSYS_NO_PATHCONV=1

# сырые данные и корпус монтируются с хоста – результат сбора остаётся в папке data/
RUN := docker run --rm -v "$(CURDIR)/raw:/data/raw" -v "$(CURDIR)/corpus:/data/corpus" $(IMAGE)

# собрать образ со скриптами сбора
build:
	docker build -t $(IMAGE) .

# собрать весь корпус: страницы сайта и нормативные документы на ru/kk/en, затем таблицу цен
collect: build
	$(RUN)
	"$(MAKE)" tuition

# собрать только страницы сайта
collect-pages: build
	$(RUN) --only pages
	"$(MAKE)" tuition

# собрать только нормативные документы (PDF)
collect-docs: build
	$(RUN) --only docs

# цены по программам из страницы «Стоимость обучения» -> knowledge/tuition.yaml (для ответа «Сколько стоит ВТиПО?»)
tuition: build
	docker run --rm -v "$(CURDIR)/corpus:/data/corpus:ro" -v "$(CURDIR)/knowledge:/data/knowledge" \
		--entrypoint python $(IMAGE) -m collect.tuition

# проверить базу ответов и наборы фраз: переводы, источники в корпусе, дубли и пересечения выборок
check: build
	docker run --rm -v "$(CURDIR)/corpus:/data/corpus:ro" -v "$(CURDIR)/knowledge:/data/knowledge:ro" \
		-v "$(CURDIR)/phrases:/data/phrases:ro" --entrypoint sh $(IMAGE) \
		-c "python -m collect.check_knowledge && python -m collect.check_phrases"

# удалить сырые данные и образ (корпус в corpus/ остаётся)
clean:
	rm -rf raw
	docker rmi -f $(IMAGE)
