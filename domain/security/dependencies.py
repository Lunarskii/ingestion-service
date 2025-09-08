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

from domain.security.service import KeycloakClient
from domain.security.oauth2 import OAuth2PasswordBearer
from domain.security.transports import (
    Transport,
    HeaderTransport,
    CookieTransport,
)
from domain.security.schemas import OIDCUser
from domain.security.exceptions import UnauthorizedError


transports: list[Transport] = [
    HeaderTransport(),
    CookieTransport(),
]


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
                raise UnauthorizedError()
        return user
    return wrapper
