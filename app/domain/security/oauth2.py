from fastapi.security import OAuth2PasswordBearer as BaseOAuth2PasswordBearer
from fastapi import Request

from app.domain.security.exceptions import NoTokenProvidedError
from app.domain.security.transports import Transport


class OAuth2PasswordBearer(BaseOAuth2PasswordBearer):
    """
    Поток OAuth2 для аутентификации с использованием Bearer токена, полученного с помощью пароля.
    Экземпляр этого класса может использоваться как FastAPI зависимость.
    """

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
