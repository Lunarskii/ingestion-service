from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from fastapi.responses import RedirectResponse

from domain.security.dependencies import keycloak_dependency
from domain.security.service import KeycloakClient
from domain.security.schemas import OIDCToken


router = APIRouter(prefix="/auth")


@router.get("/login")
async def login(
    keycloak: Annotated[KeycloakClient, Depends(keycloak_dependency)],
) -> RedirectResponse:
    return RedirectResponse(keycloak.login_uri)


@router.get("/callback")
async def callback(
    session_state: str,
    code: str,
    keycloak: Annotated[KeycloakClient, Depends(keycloak_dependency)],
) -> RedirectResponse:
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
