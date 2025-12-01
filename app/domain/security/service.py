from typing import (
    TYPE_CHECKING,
    Any,
)
from functools import cached_property

import requests
from jwt.exceptions import PyJWTError
from urllib.parse import urlencode

from app.domain.security.schemas import (
    OIDCUser,
    OIDCToken,
)
from app.domain.security.utils import decode_jwt


if TYPE_CHECKING:
    from fastapi import FastAPI


class KeycloakClient:
    """
    Лёгкий клиент для взаимодействия с Keycloak/OpenID Connect провайдером.
    """

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
        """
        :param url: Базовый URL Keycloak (например, "https://auth.example.com/auth").
        :param client_id: client_id зарегистрированного клиента в Keycloak.
        :param client_secret: client_secret (если используется confidential client).
        :param realm: Имя реалма в Keycloak.
        :param redirect_uri: URI перенаправления, указываемый при авторизации.
        :param scope: scope для запроса авторизации (по умолчанию "openid profile email").
        :param timeout: Таймаут HTTP-запросов в секундах.
        :param ssl_verification: Проверять ли TLS-сертификат
                                 (Использовать False только в тестах/при локальной разработке).
        """

        self.url: str = url
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.realm: str = realm
        self.redirect_uri: str = redirect_uri
        self.scope: str = scope
        self.timeout: int = timeout
        self.ssl_verification: bool = ssl_verification

    @cached_property
    def realm_uri(self) -> str:
        """
        Базовый URI для реалма: "{url}/realms/{realm}".

        :return: URI реалма. Пример: "https://auth.example.com/auth/realms/myrealm".
        """

        return f"{self.url}/realms/{self.realm}"

    @cached_property
    def openid_configuration(self) -> dict:
        """
        Загружает и возвращает OpenID Connect discovery документ:
        "{realm_uri}/.well-known/openid-configuration".

        :return: Словарь JSON, как его отдаёт Keycloak.
        """

        response: requests.Response = requests.get(
            url=f"{self.realm_uri}/.well-known/openid-configuration",
            timeout=self.timeout,
            verify=self.ssl_verification,
        )
        return response.json()

    @cached_property
    def authorization_uri(self) -> str | None:
        """
        URL endpoint-а авторизации (authorization_endpoint из openid-configuration).

        :return: URL, если был найден, иначе None.
        """

        return self.openid_configuration.get("authorization_endpoint")

    @cached_property
    def token_uri(self) -> str | None:
        """
        URL token endpoint-а (token_endpoint из openid-configuration).

        :return: URL, если был найден, иначе None.
        """

        return self.openid_configuration.get("token_endpoint")

    @cached_property
    def login_uri(self) -> str:
        """
        Сформированный URI для инициирования Authorization Code flow (URI для перенаправления пользователя).

        :return: URL для перенаправления пользователя на страницу аутентификации.
                 Пример: https://auth.example.com/auth/realms/myrealm/protocol/openid-connect/auth?client_id=...
        """

        params: dict[str, Any] = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope,
        }
        return f"{self.authorization_uri}?{urlencode(params)}"

    @cached_property
    def logout_uri(self) -> str | None:
        """
        URL endpoint-а завершения сессии (end_session_endpoint из openid-configuration).

        :return: URL, если был найден, иначе None.
        """

        return self.openid_configuration.get("end_session_endpoint")

    @cached_property
    def public_key(self) -> str:
        """
        :return: Публичный RSA ключ реалма в PEM-формате.
        """

        response: requests.Response = requests.get(
            url=self.realm_uri,
            timeout=self.timeout,
            verify=self.ssl_verification,
        )
        public_key = response.json()["public_key"]
        return f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"

    def get_user(self, token: str):
        """
        Декодирует и валидирует переданный JWT (id_token, access_token) с использованием публичного ключа.

        :param token: JWT (строка Bearer token).

        :return: OIDCUser - модель с данными пользователя (claims).
        :raises PyJWTError: при ошибке декодирования/валидации токена.
        """

        try:
            user: OIDCUser = decode_jwt(
                public_key=self.public_key,
                token=token,
                audience="account",
            )
        except PyJWTError:
            raise
        else:
            return user

    def login_with_authorization_code(
        self,
        session_state: str,
        code: str,
    ) -> OIDCToken:
        """
        Обменивает код авторизации на набор токенов (access_token, refresh_token, id_token).

        :param session_state: session_state, пришедший в callback.
        :param code: Код авторизации, полученный от Keycloak после перенаправления.

        :return: Pydantic-схема ``OIDCToken``.
        :raises ValueError / ValidationError: если возвращённый JSON не соответствует OIDCToken.
        """

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

    def add_swagger_config(self, app: "FastAPI"):
        """
        Добавляет настройки OAuth2 в Swagger UI (FastAPI) для удобного логина через Keycloak.

        Этот метод меняет атрибут `app.swagger_ui_init_oauth`, который используется Swagger UI
        на стороне клиента, чтобы инициализировать PKCE + client credentials в UI.

        :param app: экземпляр FastAPI, в котором нужно включить конфигурацию.

        :note: хранение client_secret в swagger UI - потенциальный риск безопасности для prod.
               Используйте осторожно (в dev/test окружениях такая конфигурация удобна).
        """

        app.swagger_ui_init_oauth = {
            "usePkceWithAuthorizationCodeGrant": True,
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
        }
