.PHONY: build collect collect-pages collect-docs clean

IMAGE := turanassist-data

# Git Bash на Windows иначе превращает пути контейнера (/data/raw) в пути Windows
export MSYS_NO_PATHCONV=1

# сырые данные и корпус монтируются с хоста – результат сбора остаётся в папке data/
RUN := docker run --rm -v "$(CURDIR)/raw:/data/raw" -v "$(CURDIR)/corpus:/data/corpus" $(IMAGE)

# собрать образ со скриптами сбора
build:
	docker build -t $(IMAGE) .

# собрать весь корпус: страницы сайта и нормативные документы на ru/kk/en
collect: build
	$(RUN)

# собрать только страницы сайта
collect-pages: build
	$(RUN) --only pages

# собрать только нормативные документы (PDF)
collect-docs: build
	$(RUN) --only docs

# удалить сырые данные и образ (корпус в corpus/ остаётся)
clean:
	rm -rf raw
	docker rmi -f $(IMAGE)
