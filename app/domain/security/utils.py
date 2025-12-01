from datetime import timedelta
from json import JSONEncoder
from typing import (
    Any,
    Iterable,
)
import hashlib

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import (
    VerifyMismatchError,
    VerificationError,
)

from app.domain.security.schemas import OIDCUser
from app.utils.datetime import universal_time


def encode_jwt(
    claims: OIDCUser,
    private_key: str,
    *,
    algorithm: str | None = "RS256",
    headers: dict[str, Any] | None = None,
    json_encoder: JSONEncoder | None = None,
    expires_in: timedelta | None = None,
    sort_headers: bool = True,
) -> str:
    """
    Генерирует JWT, используя переданные требования, алгоритм и др.

    :param claims: Требования.
    :param private_key: Приватный ключ/секрет для подписи (PEM-строка).
    :param algorithm: Алгоритм подписи.
    :param headers: Дополнительные заголовки JWT.
    :param json_encoder: Индивидуальный JSONEncoder для шифрования полей.
    :param expires_in: Опционально добавить поля iat/nbf/exp; если передан, они будут установлены.
    :param sort_headers: Сортировать ли заголовки ``headers``.

    :return: JWT.
    :raises PyJWTError: Ошибки из библиотеки ``jwt`` при проблемах с сериализацией/подписью.
    """

    payload = claims.model_dump(exclude_none=True)
    if expires_in:
        current_time = universal_time()
        payload["iat"] = claims.iat or current_time
        payload["nbf"] = claims.nbf or current_time
        payload["exp"] = claims.exp or (current_time + expires_in)
    encoded = jwt.encode(
        payload=payload,
        key=private_key,
        algorithm=algorithm,
        headers=headers,
        json_encoder=json_encoder,
        sort_headers=sort_headers,
    )
    return encoded


def decode_jwt(
    public_key: str,
    token: str | bytes,
    *,
    algorithms: list[str] = ["RS256"],
    options: dict[str, Any] | None = None,
    detached_payload: bytes | None = None,
    audience: str | Iterable[str] | None = None,
    issuer: str | list[str] | None = None,
    leeway: float | timedelta = 0,
    **kwargs: Any,
) -> OIDCUser:
    """
    Проверяет подлинность JWT и возвращает JWT как OIDCUser схему.

    :param public_key: Публичный ключ для проверки подписи (PEM-строка).
    :param token: JWT.
    :param algorithms: Список допустимых алгоритмов.
    :param options: Дополнительные опции для расшифровки JWT (по умолчанию включает проверку signature/exp/aud).
    :param detached_payload: Поддержка detached payload.
    :param audience: Ожидаемое поле audience (aud) - если указано, включается проверка aud.
    :param issuer: Ожидаемый issuer (iss).
    :param leeway: Допустимый leeway (в секундах или timedelta) при проверке времени.
    :param kwargs: Дополнительные параметры для jwt.decode.

    :return: OIDCUser.
    :raises PyJWTError (например ExpiredSignatureError, InvalidAudienceError и т.п.) при неудаче.
    """

    options = options or {
        "verify_signature": True,
        "verify_aud": audience is not None,
        "verify_exp": True,
    }
    decoded = jwt.decode(
        jwt=token,
        key=public_key,
        algorithms=algorithms,
        options=options,
        detached_payload=detached_payload,
        audience=audience,
        issuer=issuer,
        leeway=leeway,
        **kwargs,
    )
    return OIDCUser.model_validate(decoded)


# TODO возможно стоит вынести все настройки в конфиг для более глубокой настройки
password_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=2**16,
    parallelism=2,
)


def hash_token(token: str) -> str:
    """
    Возвращает argon2-хеш для переданного токена.

    :param token: Токен.

    :return: Хэшированный токен (argon2).
    :raises argon2.exceptions.*: Возможны исключения при внутренней ошибке хеширования.
    """

    return password_hasher.hash(token)


def validate_token(
    plain_token: str,
    hashed_token: str,
) -> bool:
    """
    Проверяет подлинность plain_token и соответствие plain_token с сохраненным hashed_token.

    :param plain_token: Открытый (переданный клиентом) токен
    :param hashed_token: Ранее сохраненное значение, хэшированное через hash_token()

    :return: True, если токены совпали и верификация успешна, иначе False.
    """

    try:
        return password_hasher.verify(
            password=plain_token,
            hash=hashed_token,
        )
    except (VerifyMismatchError, VerificationError):
        return False


def hash_sha256(value: bytes) -> str:
    """
    Возвращает хэш байтов в виде строки.
    """

    return hashlib.sha256(value).hexdigest()
