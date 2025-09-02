from exceptions.base import (
    ApplicationError,
    status,
)


class UnauthorizedError(ApplicationError):
    message = 'Unauthorized'
    error_code = "unauthorized"
    status_code = status.HTTP_401_UNAUTHORIZED
    headers = {"WWW-Authenticate": "Bearer"}


class InvalidTokenError(UnauthorizedError):
    message = "Invalid token"
    error_code = "invalid_token"


class InvalidTokenTypeError(UnauthorizedError):
    message = "Invalid token type"
    error_code = "invalid_token_type"


class NoTokenProvidedError(UnauthorizedError):
    message = "No access token provided"
    error_code = "no_token_provided"


class TokenExpiredError(UnauthorizedError):
    message = "Token expired"
    error_code = "token_expired"
