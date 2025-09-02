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
    def __init__(
        self,
        *,
        name: str,
        scheme_name: str | None = None,
    ) -> None:
        self.name = name
        self.scheme_name = scheme_name or self.__class__.__name__

    @abc.abstractmethod
    def get(self, request: Request) -> str | None: ...

    @abc.abstractmethod
    def set(self, response: Response, value: str) -> Response: ...

    @abc.abstractmethod
    def delete(self, response: Response) -> Response: ...


class HeaderTransport(Transport):
    def __init__(
        self,
        *,
        name: str = "Authorization",
        scheme_name: str | None = "HeaderBearer",
    ):
        super().__init__(name=name, scheme_name=scheme_name)

    def get(self, request: Request) -> str | None:
        authorization = request.headers.get(self.name)
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            return None
        return param

    def set(self, response: Response, value: str) -> Response:
        response.headers[self.name] = f"Bearer {value}"
        return response

    def delete(self, response: Response) -> Response:
        del response.headers[self.name]
        return response


class CookieTransport(Transport):
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
        return request.cookies.get(self.name)

    def set(self, response: Response, value: str) -> Response:
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
        response.delete_cookie(
            key=self.name,
            path=self.path,
            domain=self.domain,
            secure=self.secure,
            httponly=self.httponly,
            samesite=self.samesite,
        )
        return response
