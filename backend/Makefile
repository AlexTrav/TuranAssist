.PHONY: build run test stop clean

IMAGE := turanassist-backend
CONTAINER := turanassist-backend

# Git Bash на Windows иначе превращает пути контейнера в пути Windows
export MSYS_NO_PATHCONV=1

# собрать продакшн-образ; контекст – корень репозитория
build:
	docker build -f Dockerfile --target app -t $(IMAGE) ..

# запустить бэкенд с ограничением памяти как на бесплатном Render (512 МБ)
run: build
	docker run --rm -p 8000:8000 --memory=512m --name $(CONTAINER) $(IMAGE)

# прогнать автотесты pytest внутри образа
test:
	docker build -f Dockerfile --target test -t $(IMAGE)-test ..
	docker run --rm $(IMAGE)-test

# остановить запущенный контейнер
stop:
	docker stop $(CONTAINER)

# удалить образы
clean:
	docker rmi -f $(IMAGE) $(IMAGE)-test
