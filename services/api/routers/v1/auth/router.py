from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)
from fastapi.responses import RedirectResponse

from app.domain.security.dependencies import keycloak_dependency
from app.domain.security.service import KeycloakClient
from app.domain.security.schemas import OIDCToken


router = APIRouter(prefix="/auth")


@router.get("/login")
async def login(
    keycloak: Annotated[KeycloakClient, Depends(keycloak_dependency)],
) -> RedirectResponse:
    """
    Перенаправляет пользователя на страницу аутентификации.

    В данный момент возвращает именно RedirectResponse, пока этим не займется UI.
    """

    return RedirectResponse(keycloak.login_uri)


@router.get("/callback")
async def callback(
    session_state: str,
    code: str,
    keycloak: Annotated[KeycloakClient, Depends(keycloak_dependency)],
) -> RedirectResponse:
    """
    Принимает callback с кодом авторизации от сервера аутентификации/авторизации.

    В данный момент устанавливает токены в куки, пока этим не займется UI.
    """

    token: OIDCToken = keycloak.login_with_authorization_code(
        session_state=session_state,
        code=code,
    )
    response = RedirectResponse(url="/")
    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=3600,
    )
    response.set_cookie(
        key="refresh_token",
        value=token.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=2592000,
    )
    response.set_cookie(
        key="id_token",
        value=token.id_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=3600,
    )
    return response


@router.get("/logout")
async def logout(
    keycloak: Annotated[KeycloakClient, Depends(keycloak_dependency)],
) -> RedirectResponse:
    """
    Перенаправляет пользователя на страницу выхода из аккаунта.

    В данный момент удаляет токены из куки, пока этим не займется UI.
    """

    response = RedirectResponse(keycloak.logout_uri)
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    response.delete_cookie(
        key="id_token",
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return response
