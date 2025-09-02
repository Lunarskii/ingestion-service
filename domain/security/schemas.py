import uuid
from datetime import datetime
from typing import Annotated

from pydantic import (
    ConfigDict,
    Field,
    EmailStr,
    field_serializer,
)

from schemas.base import BaseSchema


class JWTClaims(BaseSchema):
    model_config = ConfigDict(extra="allow")

    jti: Annotated[str | None, Field(default_factory=lambda: str(uuid.uuid4()))]  # type: ignore
    iss: str | None = None
    aud: str | None = None
    typ: str | None = None
    sub: str | None = None
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    iat: datetime | None = None
    nbf: datetime | None = None
    exp: datetime | None = None

    scope: list[str] | None = None
    email_verified: bool | None = None
    nickname: str | None = None
    user_id: str | None = None

    @field_serializer("iat", "exp", "nbf", mode="plain")
    def datetime_to_timestamp(
        self,
        value: datetime | None,
    ) -> int | None:
        if value is None:
            return value
        return int(value.timestamp())
