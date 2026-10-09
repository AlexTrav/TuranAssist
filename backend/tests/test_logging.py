import logging

from app.main import HealthCheckFilter


def access_record(path: str, status: int) -> logging.LogRecord:
    # так uvicorn пишет строку журнала доступа: клиент, метод, путь, версия HTTP, код ответа
    return logging.LogRecord("uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d',
                             ("172.18.0.1:5000", "GET", path, "1.1", status), None)


def test_successful_healthcheck_is_not_logged():
    assert not HealthCheckFilter().filter(access_record("/api/health", 200))


def test_failed_healthcheck_and_other_requests_are_logged():
    f = HealthCheckFilter()
    assert f.filter(access_record("/api/health", 503))
    assert f.filter(access_record("/api/chat", 200))
