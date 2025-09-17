from exceptions.base import (
    ApplicationError,
    status,
)


class UnauthorizedError(ApplicationError):
    message = 'Не авторизован'
    error_code = "unauthorized"
    status_code = status.HTTP_401_UNAUTHORIZED


class InvalidKeyError(UnauthorizedError):
    message = "Недействительный ключ авторизации"
    error_code = "invalid_key"
    status_code = status.HTTP_403_FORBIDDEN


class InvalidTokenTypeError(UnauthorizedError):
    message = "Invalid token type"
    error_code = "invalid_token_type"


class NoTokenProvidedError(UnauthorizedError):
    message = "No access token provided"
    error_code = "no_token_provided"


class TokenExpiredError(UnauthorizedError):
    message = "Token expired"
    error_code = "token_expired"


class SignatureHasExpired(UnauthorizedError):
    ...


class KeycloakError(ApplicationError):
    message = "Ошибка при работе с Keycloak"
    error_code = "keycloak_error"
