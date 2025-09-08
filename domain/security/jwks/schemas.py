from typing import (
    Literal,
    Self,
)

from pydantic import model_validator
from jwt.exceptions import InvalidKeyError

from schemas.base import BaseSchema


class JWK(BaseSchema):
    kid: str
    kty: Literal[
        "EC",
        "oct",
        "RSA",
        "OKP",
    ] = "RSA"
    use: (
        Literal[
            "sig",
            "enc",
        ]
        | None
    ) = None
    alg: (
        Literal[
            "ES256",
            "ES384",
            "ES512",
            "ES256K",
            "RS256",
            "HS256",
            "EdDSA",
        ]
        | None
    ) = None
    crv: (
        Literal[
            "P-256",
            "P-384",
            "P-521",
            "secp256k1",
            "Ed25519",
        ]
        | None
    ) = None
    exp: int

    n: str | None = None  # base64url модуль (для RSA)
    e: str | None = None  # base64url экспонента (для RSA)
    x: str | None = None  # для EC/OKP
    y: str | None = None
    k: str | None = None  # симметричное ключевое значение (для oct)

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if not self.alg:
            if self.kty == "EC":
                if self.crv == "P-256" or not self.crv:
                    self.alg = "ES256"
                elif self.crv == "P-384":
                    self.alg = "ES384"
                elif self.crv == "P-521":
                    self.alg = "ES512"
                elif self.crv == "secp256k1":
                    self.alg = "ES256K"
                else:
                    raise InvalidKeyError(f"Неподдерживаемый crv: {self.crv}")
            elif self.kty == "RSA":
                self.alg = "RS256"
            elif self.kty == "oct":
                self.alg = "HS256"
            elif self.kty == "OKP":
                if not self.crv:
                    raise InvalidKeyError(f"Неподдерживаемый crv: {self.crv}")
                if self.crv == "Ed25519":
                    self.alg = "EdDSA"

        if self.kty == "EC":
            if not self.x or not self.y:
                raise InvalidKeyError("EC JWK должен содержать 'x' и 'y' поля")
        elif self.kty == "RSA":
            if not self.n or not self.e:
                raise InvalidKeyError(f"RSA JWK должен содержать 'n' и 'e' поля")

        return self


class JWKSet(BaseSchema):
    keys: list[JWK] = []
