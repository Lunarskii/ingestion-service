from typing import (
    Annotated,
    Callable,
    Any,
    Coroutine,
)

from fastapi import (
    Request,
    Depends,
)
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.security.service import KeycloakClient
from app.domain.security.oauth2 import OAuth2PasswordBearer
from app.domain.security.transports import (
    Transport,
    HeaderTransport,
    CookieTransport,
)
from app.domain.security.schemas import (
    OIDCUser,
    APIKeysDTO,
)
from app.domain.security.repositories import APIKeysRepository
from app.domain.security.utils import (
    hash_token,
    validate_token,
)
from app.domain.security.exceptions import (
    UnauthorizedError,
    InvalidKeyError,
)
from app.domain.database.dependencies import async_scoped_session_dependency


transports: list[Transport] = [
    HeaderTransport(),
    CookieTransport(),
]
api_key_header_scheme = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def keycloak_dependency(request: Request) -> KeycloakClient:
    """
    Возвращает настроенный Keycloak клиент из состояния приложения.
    """

    return request.app.state.keycloak_client


async def oauth2_scheme(
    keycloak: Annotated[KeycloakClient, Depends(keycloak_dependency)],
    request: Request,
) -> str | None:
    """
    Зависимость для получения access токена пользователя из заголовков или куки.

    :param keycloak: зависимость от клиента Keycloak.
    :param request: FastAPI Request - прокидывается в сам _oauth2_scheme.

    :return: Bearer токен - аналогично тому, как возвращает FastAPI.OAuth2PasswordBearer.
    :raises NoTokenProvidedError: если токен отсутствует или невалиден.
    """

    _oauth2_scheme = OAuth2PasswordBearer(
        token_url=keycloak.token_uri,
        transports=transports,
    )
    return await _oauth2_scheme(request)


def required_roles(
    *roles: str,
) -> Callable[[KeycloakClient, str], Coroutine[Any, Any, OIDCUser]]:
    """
    Зависимость для проверки наличия набора ролей у текущего пользователя.

    Возвращаемая зависимость может быть использована в endpoint'ах FastAPI как:
        user: OIDCUser = Depends(required_roles("admin", "editor"))
    или как:
        @router.get("/admin")
        async def admin_area(user: OIDCUser = Depends(required_roles("admin"))):
            return {"msg": "ok"}

    :param roles: набор ролей, которые требуются для доступа к ресурсу.

    :return: асинхронная dependency-функция, возвращающая OIDCUser при успешной проверке.
    :raises UnauthorizedError: если пользователя нет или у пользователя отсутствует требуемая роль.
    """

    async def wrapper(
        keycloak: Annotated[KeycloakClient, Depends(keycloak_dependency)],
        token: Annotated[str, Depends(oauth2_scheme)],
    ) -> OIDCUser:
        user: OIDCUser = keycloak.get_user(token)
        user_roles: list[str] = user.roles
        for role in roles:
            if role not in user_roles:
                raise UnauthorizedError(
                    headers={"WWW-Authenticate": "Bearer"},
                )
        return user

    return wrapper


async def require_api_key(
    api_key_header: Annotated[str | None, Depends(api_key_header_scheme)],
    session: Annotated[AsyncSession, Depends(async_scoped_session_dependency)],
) -> None:
    """
    Зависимость для проверки наличия заголовка ``X-API-Key`` (или другого заголовка) - валидирует ключ в БД.

    Возвращаемая зависимость может быть использована в endpoint'ах FastAPI как:
        @router.post("/download")
        async def download(data: Payload, _ = Depends(require_api_key)):
            ...

    :param api_key_header: Значение заголовка API-ключа (None, если заголовок не передан).
    :param session: Асинхронная БД сессия.

    :raises UnauthorizedError: Если заголовок отсутствует.
    :raises InvalidKeyError: Если ключ передан, но не найден/не валиден.
    """

    if not api_key_header:
        raise UnauthorizedError("Не предоставлен API-ключ авторизации")

    api_keys_repo = APIKeysRepository(session)
    api_keys: list[APIKeysDTO] = await api_keys_repo.get_n(
        key_hash=hash_token(api_key_header),
    )

    if len(api_keys) == 0:
        raise InvalidKeyError("Предоставлен недействительный API-ключ")

    for api_key in api_keys:
        if validate_token(api_key_header, api_key.key_hash):
            return

    raise InvalidKeyError("Предоставлен недействительный API-ключ")
