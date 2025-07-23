from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

from exceptions.base import (
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
    return UnexpectedErrorResponse()


def setup_exception_handlers(app: "FastAPI") -> None:
    app.add_exception_handler(ApplicationError, application_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
