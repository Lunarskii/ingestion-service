from enum import (
    StrEnum,
    auto,
)
from typing import (
    Annotated,
    Iterable,
)

from fastapi.security import (
    OAuth2PasswordBearer as BaseOAuth2PasswordBearer,
    OAuth2PasswordRequestForm as BaseOAuth2PasswordRequestForm,
)
from fastapi import (
    Request,
    Form,
)
from pydantic import BaseModel

from domain.security.exceptions import NoTokenProvidedError
from domain.security.transports import Transport


class OAuth2Grant(StrEnum):
    """
    Гранты - это методы, с помощью которых клиент может получить access токен.

    :cvar authorization_code: Клиент направляет владельца ресурса на сервер авторизации.
                              Владелец ресурса выполняет проверку подлинности и авторизует клиента.
                              Сервер авторизации перенаправляет владельца ресурса обратно клиенту
                              с помощью кода авторизации. Клиент запрашивает access токен у endpoint-а token
                              сервера авторизации, включая код авторизации, полученный на предыдущем шаге.
    :cvar password: Владелец ресурса предоставляет клиенту свое имя пользователя и пароль.
                    Клиент запрашивает access токен у endpoint-а token сервера авторизации,
                    включая учетные данные, полученные от владельца ресурса.
                    Этот тип гранта следует использовать только при наличии высокой степени
                    доверия между владельцем ресурса и клиентом.
    :cvar pkce: Клиент направляет владельца ресурса на сервер авторизации. Владелец ресурса
                выполняет проверку подлинности и авторизует клиента. Сервер авторизации
                перенаправляет владельца ресурса обратно клиенту с помощью кода авторизации.
                Клиент запрашивает access токен у endpoint-а token сервера авторизации, включая
                код авторизации, полученный на предыдущем шаге, и средство проверки кода (code verifier).
    :cvar refresh_token: Клиент запрашивает access токен у endpoint-а token сервера авторизации,
                         включая refresh токен.
    """

    authorization_code = auto()
    password = auto()
    pkce = auto()
    refresh_token = auto()


class OAuth2ConsentRequest(BaseModel):
    """
    Consent Request is sent by the client to the authorization server.
    Authorization server asks the resource owner to grant permissions to the client.
    """

    response_type: str | None = None
    """
    The response type is used to specify the desired authorization processing flow.
    """

    client_id: str | None = None
    """
    The client ID is a public identifier for the client.
    """

    redirect_uri: str | None = None
    """
    The redirect URI is used to redirect the user-agent back to the client.
    """

    scope: str | None = None
    """
    The scope is used to specify what access rights an access token has.
    """

    state: str | None = None
    """
    The state is used to prevent CSRF attacks.
    """

    code_challenge: str | None = None
    """
    The code challenge is used to verify the authorization code.
    """

    code_challenge_method: str | None = None
    """
    The code challenge method is used to verify the authorization code.
    """

    @property
    def scopes(self) -> Iterable[str]:
        if self.scope is None:
            return []
        return self.scope.split(" ")


class OAuth2PasswordBearer(BaseOAuth2PasswordBearer):
    def __init__(
        self,
        token_url: str,
        scheme_name: str | None = None,
        scopes: dict[str, str] | None = None,
        description: str | None = None,
        auto_error: bool = True,
        transports: list[Transport] | None = None,
    ):
        self.transports = transports
        super().__init__(
            tokenUrl=token_url,
            scheme_name=scheme_name,
            scopes=scopes,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> str | None:
        if self.transports:
            for transport in self.transports:
                if token := transport.get(request):
                    return token
        if self.auto_error:
            raise NoTokenProvidedError()


class OAuth2PasswordRequestForm(BaseOAuth2PasswordRequestForm):
    def __init__(
        self,
        *,
        grant_type: Annotated[OAuth2Grant, Form()],
        username: Annotated[str | None, Form(examples=["user@example.com"])] = None,
        password: Annotated[str | None, Form(examples=["password"])] = None,
        refresh_token: Annotated[str | None, Form()] = None,
        scope: Annotated[str, Form()] = "",
        client_id: Annotated[str | None, Form()] = "",
        client_secret: Annotated[str | None, Form()] = "",
    ):
        """
        :param grant_type: В спецификации OAuth2 указано, что это обязательная строка, которая
                           должна быть фиксированной ``password``. Тем не менее этот класс
                           зависимостей является разрешающим и позволяет не передавать его.
                           Если вы хотите применить это, используйте вместо этого зависимость
                           ``OAuth2PasswordRequestFormStrict``.
        :param username: Строка ``username``. Спецификация OAuth2 требует точного указания имени поля
                         ``username``.
        :param password: Строка ``password``. Спецификация OAuth2 требует точного указания имени поля
                         ``password``.
        :param refresh_token:
        :param scope: Одна строка, на самом деле имеющая несколько областей действия,
                      разделенных пробелами. Каждая область видимости также является строкой.
                      Например, одна строка с: "read:items write:items read:users profile openid"
                      будет представлять собой области применения: "read:items", "write:items",
                      "read:users", "profile", "openid".
        :param client_id: Если есть ``client_id``, он может быть отправлен как часть полей формы.
                          Но спецификация OAuth2 рекомендует отправлять ``client_id`` и
                          ``client_secret`` (если есть) с использованием HTTP Basic auth.
        :param client_secret: Если есть ``client_password`` (и ``client_id``), они могут быть
                              отправлены как часть полей формы. Но спецификация OAuth2 рекомендует
                              отправлять ``client_id`` и ``client_secret`` (если есть)
                              с использованием HTTP Basic auth.
        """

        self.refresh_token = refresh_token
        super().__init__(
            grant_type=grant_type,
            username=username,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
        )


class OAuth2PasswordRequestFormStrict(OAuth2PasswordRequestForm):
    ...
