import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security.rate_limit import limiter


# один клиент на все тесты: модель грузится при старте приложения, повторять это для каждого теста долго
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


# счётчики rate limit общие для процесса – сбрасываем, чтобы тесты не влияли друг на друга
@pytest.fixture(autouse=True)
def reset_rate_limits():
    limiter.reset()
    yield


@pytest.fixture(scope="session")
def classifier(client):
    return client.app.state.classifier


@pytest.fixture(scope="session")
def knowledge(client):
    return client.app.state.knowledge
