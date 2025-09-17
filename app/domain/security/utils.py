from datetime import timedelta
from json import JSONEncoder
from typing import (
    Any,
    Iterable,
)

import jwt
import bcrypt

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
    verify: bool | None = None,
    detached_payload: bytes | None = None,
    audience: str | Iterable[str] | None = None,
    issuer: str | list[str] | None = None,
    leeway: float | timedelta = 0,
    **kwargs: Any,
) -> OIDCUser:
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
        verify=verify,
        detached_payload=detached_payload,
        audience=audience,
        issuer=issuer,
        leeway=leeway,
        **kwargs,
    )
    return OIDCUser.model_validate(decoded)


def hash_value(value: str) -> bytes:
    """
    Примечание: Ограничение 72 байта. Если значение больше, то будет обрезано.
    """

    salt: bytes = bcrypt.gensalt()
    value_bytes: bytes = value.encode()
    return bcrypt.hashpw(value_bytes, salt)


def validate_value(
    plain_value: str,
    hashed_value: bytes,
) -> bool:
    return bcrypt.checkpw(plain_value.encode(), hashed_value)
