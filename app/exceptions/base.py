from app import status


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
    debug_message: str | None = None
    error_code: str = "unknown_error"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    headers: dict[str, str] | None = None

    def __init__(
        self,
        message: str | None = None,
        *,
        debug_message: str | None = None,
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
        self.debug_message = debug_message or self.debug_message
        self.error_code = error_code or self.error_code
        self.status_code = status_code or self.status_code
        self.headers = headers or self.headers
        super().__init__(
            self.message,
            self.debug_message,
            self.error_code,
            self.status_code,
            self.headers,
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(message='{self.message}', "
            f"debug_message='{self.debug_message}', "
            f"error_code='{self.error_code}', "
            f"status_code='{self.status_code}', "
            f"headers='{self.headers}')"
        )


class UnexpectedError(ApplicationError):
    """
    Ответ при непредвиденной ошибке, не относящейся к ошибкам, наследованных от ApplicationError.
    """

    message = "Internal Server Error"
    error_code = "unexpected_error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    headers = None
