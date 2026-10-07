.PHONY: build baseline ensemble clean

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

# выбрать продакшн-модель: эмбеддинги e5 из прогона v2 (скачиваются с HF в .cache), TF-IDF и ансамбль
ensemble: build
	docker run --rm -v "$(CURDIR)/../data:/work/data:ro" -v "$(CURDIR)/.cache:/work/model/.cache" \
		-v "$(CURDIR)/artifacts:/work/model/artifacts" -v "$(CURDIR)/reports:/work/model/reports" \
		--entrypoint python $(IMAGE) -m model.ensemble.run_ensemble

# удалить образ
clean:
	docker rmi -f $(IMAGE)
