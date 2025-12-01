import abc
from abc import ABC
from datetime import datetime
from typing import Literal

from fastapi import (
    Response,
    Request,
)
from fastapi.security.utils import get_authorization_scheme_param


class Transport(ABC):
    """
    Базовый абстрактный класс для транспорта токенов.
    """

    def __init__(
        self,
        *,
        name: str,
        scheme_name: str | None = None,
    ) -> None:
        self.name = name
        self.scheme_name = scheme_name or self.__class__.__name__

    @abc.abstractmethod
    def get(self, request: Request) -> str | None:
        """
        Извлекает токен из запроса.

        :param request: FastAPI Request.

        :return: Строка токена или None, если токен отсутствует или невалиден для данного транспорта
        """

        ...

    @abc.abstractmethod
    def set(self, response: Response, value: str) -> Response:
        """
        Помещает токен в ответ, например заголовок или куки.

        :param response: FastAPI Response.
        :param value: Строковое значение токена.

        :return: Модифицированный Response.
        """

        ...

    @abc.abstractmethod
    def delete(self, response: Response) -> Response:
        """
        Удаляет токен из ответа, например заголовок или куки.

        :param response: FastAPI Response.

        :return: Модифицированный Response.
        """

        ...


class HeaderTransport(Transport):
    """
    Транспорт, хранящий/читающий токен в HTTP-заголовке Authorization в формате "Bearer <token>".
    """

    def __init__(
        self,
        *,
        name: str = "Authorization",
        scheme_name: str | None = "HeaderBearer",
    ):
        super().__init__(name=name, scheme_name=scheme_name)

    def get(self, request: Request) -> str | None:
        """
        Читает токен из HTTP-заголовка "Authorization".

        :return: Токен, если заголовок присутствует и начинается с "Bearer", иначе None.
        """

        authorization = request.headers.get(self.name)
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            return None
        return param

    def set(self, response: Response, value: str) -> Response:
        """
        Устанавливает заголовок Authorization в формате "Bearer <value>"

        :return: Модифицированный Response.
        """

        response.headers[self.name] = f"Bearer {value}"
        return response

    def delete(self, response: Response) -> Response:
        """
        Удаляет заголовок Authorization, если такой присутствует.

        :return: Модифицированный Response.
        """

        if self.name in response.headers:
            del response.headers[self.name]
        return response


class CookieTransport(Transport):
    """
    Транспорт, который использует куки для хранения и чтения токена.
    """

    def __init__(
        self,
        *,
        name: str = "access_token",
        scheme_name: str | None = "CookieBearer",
        max_age: int | None = None,
        expires: datetime | str | int | None = None,
        path: str | None = "/",
        domain: str | None = None,
        secure: bool = False,
        httponly: bool = True,
        samesite: Literal["lax", "strict", "none"] | None = "lax",
    ):
        self.max_age = max_age
        self.expires = expires
        self.path = path
        self.domain = domain
        self.secure = secure
        self.httponly = httponly
        self.samesite = samesite
        super().__init__(
            name=name,
            scheme_name=scheme_name,
        )

    def get(self, request: Request) -> str | None:
        """
        Читает токен из куки access_token

        :return: Токен, если куки присутствует, иначе None.
        """

        return request.cookies.get(self.name)

    def set(self, response: Response, value: str) -> Response:
        """
        Устанавливает токен в куки.

        :return: Модифицированный Response.
        """

        response.set_cookie(
            key=self.name,
            value=value,
            max_age=self.max_age,
            expires=self.expires,
            path=self.path,
            domain=self.domain,
            secure=self.secure,
            httponly=self.httponly,
            samesite=self.samesite,
        )
        return response

    def delete(self, response: Response) -> Response:
        """
        Удаляет токен из куки.

        :return: Модифицированный Response.
        """

        response.delete_cookie(
            key=self.name,
            path=self.path,
            domain=self.domain,
            secure=self.secure,
            httponly=self.httponly,
            samesite=self.samesite,
        )
        return response
