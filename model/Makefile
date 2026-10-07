.PHONY: build baseline clean

IMAGE := turanassist-model

# Git Bash на Windows иначе превращает пути контейнера (/work/data) в пути Windows
export MSYS_NO_PATHCONV=1

# собрать образ; контекст – корень репозитория (нужен backend/app/nlp)
build:
	docker build -f Dockerfile -t $(IMAGE) ..

# обучить и оценить baseline-модели: данные только для чтения, артефакты и отчёты – на хост
baseline: build
	docker run --rm -v "$(CURDIR)/../data:/work/data:ro" \
		-v "$(CURDIR)/artifacts:/work/model/artifacts" -v "$(CURDIR)/reports:/work/model/reports" $(IMAGE)

# удалить образ
clean:
	docker rmi -f $(IMAGE)
