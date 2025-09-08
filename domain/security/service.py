from typing import Any
import functools

import requests
from fastapi import FastAPI
from jwt.exceptions import PyJWTError
from urllib.parse import urlencode

from domain.security.schemas import (
    OIDCUser,
    OIDCToken,
)
from domain.security.utils import decode_jwt


class KeycloakClient:
    def __init__(
        self,
        url: str,
        client_id: str,
        client_secret: str,
        realm: str,
        redirect_uri: str | None = None,
        scope: str = "openid profile email",
        timeout: int = 10,
        ssl_verification: bool = True,
    ):
        self.url: str = url
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.realm: str = realm
        self.redirect_uri: str = redirect_uri
        self.scope: str = scope
        self.timeout: int = timeout
        self.ssl_verification: bool = ssl_verification

    @functools.cached_property
    def realm_uri(self) -> str:
        return f"{self.url}/realms/{self.realm}"

    @functools.cached_property
    def openid_configuration(self) -> dict:
        response: requests.Response = requests.get(
            url=f"{self.realm_uri}/.well-known/openid-configuration",
            timeout=self.timeout,
            verify=self.ssl_verification,
        )
        return response.json()

    @functools.cached_property
    def authorization_uri(self) -> str | None:
        return self.openid_configuration.get("authorization_endpoint")

    @functools.cached_property
    def token_uri(self) -> str | None:
        return self.openid_configuration.get("token_endpoint")

    @functools.cached_property
    def login_uri(self) -> str:
        params: dict[str, Any] = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope,
        }
        return f"{self.authorization_uri}?{urlencode(params)}"

    @functools.cached_property
    def logout_uri(self) -> str | None:
        return self.openid_configuration.get("end_session_endpoint")

    @functools.cached_property
    def public_key(self) -> str:
        response: requests.Response = requests.get(
            url=self.realm_uri,
            timeout=self.timeout,
            verify=self.ssl_verification,
        )
        public_key = response.json()["public_key"]
        return f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"

    def get_user(self, token: str):
        try:
            user: OIDCUser = decode_jwt(
                public_key=self.public_key,
                token=token,
                audience="account",
            )
        except PyJWTError as e:
            raise
        else:
            return user

    def login_with_authorization_code(
        self,
        session_state: str,
        code: str,
    ) -> OIDCToken:
        response: requests.Response = requests.post(
            url=self.token_uri,
            data={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "session_state": session_state,
                "redirect_uri": self.redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return OIDCToken.model_validate(response.json())

    def add_swagger_config(self, app: FastAPI):
        app.swagger_ui_init_oauth = {
            "usePkceWithAuthorizationCodeGrant": True,
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
        }
