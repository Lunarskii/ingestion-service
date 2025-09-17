from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

from app.exceptions.base import (
    ApplicationError,
    ErrorResponse,
    UnexpectedErrorResponse,
)


if TYPE_CHECKING:
    from fastapi import (
        FastAPI,
        Request,
    )


async def application_exception_handler(
    request: "Request",
    ex: ApplicationError,
) -> JSONResponse:
    """
    Обработчик ошибок бизнес-логики приложения.

    Перехватывает все исключения, унаследованные от `ApplicationError`,
    и возвращает структурированный JSON-ответ с кодом и сообщением ошибки.

    :param request: Объект запроса FastAPI, во время обработки которого произошло исключение.
    :type request: Request
    :param ex: Экземпляр `ApplicationError`, содержащий информацию об ошибке.
    :type ex: ApplicationError

    :return: JSONResponse с полями: {"msg": текст сообщения об ошибке, "code": код ошибки},
             а также установленным HTTP-статус кодом и заголовками из `ex.headers`.
    :rtype: JSONResponse
    """

    return JSONResponse(
        status_code=ex.status_code,
        content=ErrorResponse(
            msg=ex.message,
            code=ex.error_code,
        ).model_dump(mode="json"),
        headers=ex.headers,
    )


async def unhandled_exception_handler(
    request: "Request",
    ex: Exception,
) -> JSONResponse:
    """
    Обработчик непредвиденных исключений.

    Перехватывает все необработанные исключения, не унаследованные от `ApplicationError`,
    и возвращает ответ `UnexpectedErrorResponse`.

    :param request: Объект запроса FastAPI, во время обработки которого произошло исключение.
    :type request: Request
    :param ex: Экземпляр `Exception`, не являющийся `ApplicationError`.
    :type ex: Exception

    :return: `UnexpectedErrorResponse` с кодом 500 и общим сообщением о внутренней ошибке.
    :rtype: JSONResponse
    """

    return UnexpectedErrorResponse()


def setup_exception_handlers(app: "FastAPI") -> None:
    """
    Регистрирует обработчики исключений в приложении FastAPI.

    Добавляет в `app` следующие обработчики:

    - `application_exception_handler` для `ApplicationError`.
    - `unhandled_exception_handler` для всех остальных `Exception`.

    :param app: Экземпляр приложения FastAPI, куда надо добавить обработчики.
    :type app: FastAPI
    """

    app.add_exception_handler(ApplicationError, application_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
