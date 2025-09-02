from datetime import timedelta
from json import JSONEncoder
from typing import (
    Any,
    Iterable,
)

import bcrypt
import jwt

from domain.security.schemas import JWTClaims
from utils.datetime import universal_time


def encode_jwt(
    claims: JWTClaims,
    private_key: str,
    *,
    algorithm: str | None = "HS256",
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
    algorithms: list[str] | None = list["HS256"],
    options: dict[str, Any] | None = None,
    verify: bool | None = None,
    detached_payload: bytes | None = None,
    audience: str | Iterable[str] | None = None,
    issuer: str | list[str] | None = None,
    leeway: float | timedelta = 0,
    **kwargs: Any,
) -> JWTClaims:
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
    return JWTClaims.model_validate(decoded)


def hash_password(password: str) -> bytes:
    salt: bytes = bcrypt.gensalt()
    pwd_bytes: bytes = password.encode()
    return bcrypt.hashpw(pwd_bytes, salt)


def validate_password(
    plain_password: str,
    hashed_password: bytes,
) -> bool:
    return bcrypt.checkpw(
        password=plain_password.encode(),
        hashed_password=hashed_password,
    )
