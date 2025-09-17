from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ApplicationError(Exception):
    """
    Базовый класс исключений для всех ошибок бизнес-логики приложения.

    Содержит поля:
      - message: читаемое сообщение об ошибке.
      - error_code: машинно-ориентированный код ошибки.
      - status_code: HTTP-статус для ответа.
      - headers: дополнительные HTTP-заголовки.

    При инициализации можно переопределить любое поле.
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
        """
        Инициализирует исключение с возможностью перегрузки параметров.

        :param message: Текст сообщения ошибки.
        :param error_code: Машинно-ориентированный код ошибки.
        :param status_code: HTTP-статус для ответа.
        :param headers: Дополнительные HTTP-заголовки.
        """

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
    """
    Структура JSON-ответа для ошибок.

    :ivar msg: Человеко-читаемое сообщение.
    :vartype msg: str
    :ivar code: Машинный код ошибки.
    :vartype code: str
    """

    msg: str
    code: str


class UnexpectedErrorResponse(JSONResponse):
    """
    Ответ при непредвиденной ошибке, не относящейся к ApplicationError.

    Возвращает:
      - HTTP 500 Internal Server Error
      - JSON: {msg: "Internal Server Error", code: "unexpected_error"}
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                msg="Internal Server Error",
                code="unexpected_error",
            ).model_dump(mode="json"),
        )
