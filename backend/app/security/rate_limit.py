from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


# в проде мы за прокси Render – реальный IP клиента лежит в X-Forwarded-For,
# а request.client.host был бы адресом прокси, одним на всех, и лимит бы не работал
def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# in-memory хранилища лимитов достаточно: на бесплатном тарифе всегда один инстанс
limiter = Limiter(key_func=client_ip)
