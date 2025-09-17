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

from domain.security.service import KeycloakClient
from domain.security.oauth2 import OAuth2PasswordBearer
from domain.security.transports import (
    Transport,
    HeaderTransport,
    CookieTransport,
)
from domain.security.schemas import (
    OIDCUser,
    APIKeysDTO,
)
from domain.security.repositories import APIKeysRepository
from domain.security.utils import (
    hash_value,
    validate_value,
)
from domain.security.exceptions import (
    UnauthorizedError,
    InvalidKeyError,
)
from domain.database.dependencies import async_scoped_session_dependency
from domain.database.uow import (
    UnitOfWork,
    UnitOfWorkFactory,
)


transports: list[Transport] = [
    HeaderTransport(),
    CookieTransport(),
]
api_key_header_scheme = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def keycloak_dependency(request: Request) -> KeycloakClient:
    return request.app.state.keycloak


async def oauth2_scheme(
    keycloak: Annotated[KeycloakClient, Depends(keycloak_dependency)],
    request: Request,
):
    _oauth2_scheme = OAuth2PasswordBearer(
        token_url=keycloak.token_uri,
        transports=transports,
    )
    return await _oauth2_scheme(request)


def required_roles(*roles: str) -> Callable[[KeycloakClient, str], Coroutine[Any, Any, OIDCUser]]:
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


async def api_keys_uow_dependency(
    session: Annotated[AsyncSession, Depends(async_scoped_session_dependency)],
) -> UnitOfWork:
    """
    Возвращает UnitOfWork с предзарегистрированными репозиториями:
        * ``APIKeysRepository``
    """

    async with UnitOfWorkFactory.get_uow(
        session,
        APIKeysRepository,
    ) as uow:
        yield uow


async def require_api_key(
    api_key_header: Annotated[str | None, Depends(api_key_header_scheme)],
    uow: Annotated[UnitOfWork, Depends(api_keys_uow_dependency)],
) -> None:
    if not api_key_header:
        raise UnauthorizedError("Не предоставлен API-ключ авторизации")

    api_keys_repo = uow.get_repository(APIKeysRepository)
    api_keys: list[APIKeysDTO] = await api_keys_repo.get_n(
        key_hash=hash_value(api_key_header),
    )

    if len(api_keys) == 0:
        raise InvalidKeyError("Предоставлен недействительный API-ключ")

    for api_key in api_keys:
        if validate_value(api_key_header, api_key.key_hash):
            return

    raise InvalidKeyError("Предоставлен недействительный API-ключ")
