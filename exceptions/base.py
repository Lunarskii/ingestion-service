from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ApplicationError(Exception):
    """
    Общий базовый класс для всех исключений.
    """

    message: str = "Internal server error"
    error_code: str = "unknown_error"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    headers: dict[str, str] | None = None

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code: str | None = None,
        status_code: int | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.status_code = status_code or self.status_code
        self.headers = headers or self.headers
        super().__init__(
            self.message,
            self.error_code,
            self.status_code,
            self.headers,
        )

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f'{class_name}(message="{self.message}", error_code={self.error_code}, status_code={self.status_code})'


class ErrorResponse(BaseModel):
    msg: str
    code: str


class UnexpectedErrorResponse(JSONResponse):
    """
    Класс для всех непредвиденных, неизвестных ошибок.
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                msg="Internal Server Error",
                code="unexpected_error",
            ).model_dump(mode="json"),
        )
