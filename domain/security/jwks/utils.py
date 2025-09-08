import base64

from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPublicKey,
    RSAPublicNumbers,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
)
from cryptography.hazmat.backends import default_backend

from domain.security.jwks.schemas import JWK


def _b64url_to_bytes(val: str) -> bytes:
    """Decode base64url string without padding to bytes."""
    if val is None:
        raise ValueError("Base64url value is None")
    s = val
    rem = len(s) % 4
    if rem:
        s += "=" * (4 - rem)
    return base64.urlsafe_b64decode(s.encode("ascii"))


def _b64url_to_int(val: str) -> int:
    return int.from_bytes(_b64url_to_bytes(val), "big")


def jwk_to_rsa_public_key(jwk: JWK) -> RSAPublicKey:
    """
    Конвертирует RSA JWK (n,e) в объект публичного ключа cryptography.
    Возвращает объект public_key (cryptography.hazmat.backends).
    """

    if jwk.kty != "RSA":
        raise ValueError("JWK is not RSA")
    numbers = RSAPublicNumbers(
        e=_b64url_to_int(jwk.e),
        n=_b64url_to_int(jwk.n),
    )
    return numbers.public_key(default_backend())


def jwk_to_public_pem(jwk: JWK) -> bytes:
    """
    Возвращает PEM bytes публичного ключа (SubjectPublicKeyInfo).
    """

    if jwk.kty == "RSA":
        public_key: RSAPublicKey = jwk_to_rsa_public_key(jwk)
        return public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    elif jwk.kty == "EC":
        # Для EC: нужен выбор кривой по crv - не реализовано здесь.
        raise NotImplementedError("EC -> public key conversion not implemented in helper")
    else:
        raise NotImplementedError(f"Conversion for key type {jwk.kty} is not implemented")
