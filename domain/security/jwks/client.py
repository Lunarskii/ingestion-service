import asyncio
import time
from functools import lru_cache

import httpx
import jwt
import jwt.algorithms
from jwt.exceptions import (
    PyJWKError,
    PyJWKClientError,
    PyJWKClientConnectionError,
)

from domain.security.jwks.schemas import (
    JWK,
    JWKSet,
)
from config import settings


class JWKSFetchError(RuntimeError):
    pass


class JWKSetCache:
    def __init__(self, lifespan: int):
        if lifespan <= 0:
            raise PyJWKError(f"'lifespan' должен быть больше 0, получено '{lifespan}'")
        self.lifespan: int = lifespan
        self.jwks: JWKSet | None = None
        self.timestamp = time.monotonic()

    def put(self, jwks: JWKSet | None) -> None:
        self.jwks = jwks

    def get(self) -> JWKSet | None:
        if not self.jwks or self.is_expired():
            return None
        return self.jwks

    def is_expired(self) -> bool:
        return (
            self.jwks
            and time.monotonic() > self.timestamp + self.lifespan
        )


class JWKSetClient:
    def __init__(
        self,
        uri: str | None = None,
        cache_signing_keys: bool = False,
        max_cached_keys: int = 16,
        cache_jwk_set: bool = True,
        lifespan: int = 3600,
        timeout: float = 5.0,
    ):
        self.uri: str | None = uri
        self.lifespan: int = lifespan
        self.timeout: float = timeout
        self._lock = asyncio.Lock()

        if cache_jwk_set:
            self.jwks_cache = JWKSetCache(lifespan)
        else:
            self.jwks_cache = None

        if cache_signing_keys:
            self.get_signing_key = lru_cache(maxsize=max_cached_keys)(
                self.get_signing_key,
            )

    async def fetch_jwk_set(self) -> JWKSet:
        url: str = self.uri or await self._discover_jwk_set_uri()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response: httpx.Response = await client.get(url)
                response.raise_for_status()
                jwks = JWKSet(
                    keys=[
                        JWK(
                            kid=key.get("kid"),
                            kty=key.get("kty"),
                            use=key.get("use"),
                            alg=key.get("alg"),
                            crv=key.get("crv"),
                            exp=key.get("exp"),
                            n=key.get("n"),
                            e=key.get("e"),
                            x=key.get("x"),
                            y=key.get("y"),
                            k=key.get("k"),
                        )
                        for key in response.json().get("keys", [])
                    ]
                )
        except httpx.HTTPStatusError as e:
            raise PyJWKClientConnectionError(f"Не удалось извлечь данные по URL, ошибка: '{e}'")
        else:
            return jwks
        finally:
            if self.jwks_cache:
                self.jwks_cache.put(jwks)

    async def _discover_jwk_set_uri(self) -> str:
        discover: str = f"{settings.keycloak.issuer.rstrip('/')}/.well-known/openid-configuration"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response: httpx.Response = await client.get(discover)
            response.raise_for_status()
            data: dict = response.json()
            if "jwks_uri" not in data:
                raise JWKSFetchError(f"'jwks_uri' не найден в {discover}")
            return data["jwks_uri"]

    async def get_jwk_set(self, refresh: bool = False) -> JWKSet:
        jwks: JWKSet | None = None

        if self.jwks_cache and not refresh:
            jwks = self.jwks_cache.get()
        if jwks is None:
            jwks = await self.fetch_jwk_set()

        if jwks is None:
            raise PyJWKClientError("JWKS endpoint не вернул JSON объект")

        return jwks

    async def get_signing_keys(self, refresh: bool = False) -> list[JWK]:
        jwks: JWKSet = await self.get_jwk_set(refresh)
        signing_keys: list[JWK] = [jwk for jwk in jwks.keys if jwk.use in ("sig", None)]

        if not signing_keys:
            raise PyJWKClientError("JWKS endpoint не содержит ключей для подписи")

        return signing_keys

    async def get_signing_key(self, kid: str) -> JWK:
        signing_keys: list[JWK] = await self.get_signing_keys()
        signing_key: JWK = self.match_kid(signing_keys, kid)

        if not signing_key:
            signing_keys = await self.get_signing_keys(refresh=True)
            signing_key = self.match_kid(signing_keys, kid)

            if not signing_key:
                raise PyJWKClientError(f"Не удалось найти ключ для подписи с kid={kid}")

        return signing_key

    @staticmethod
    def match_kid(signing_keys: list[JWK], kid: str) -> JWK | None:
        for key in signing_keys:
            if key.kid == kid:
                return key

    async def get_signing_key_from_jwt(self, token: str) -> JWK:
        header = jwt.get_unverified_header(token)
        return await self.get_signing_key(header.get("kid"))


# jwks_client = JWKSetClient(settings.openid.jwks_uri)
#
#
# # Mapping roles from token to application permission strings
# # Example mapping: provider role -> app permission
# DEFAULT_ROLE_TO_PERMISSION = {
#     "admin": {"documents:create", "documents:read", "users:manage"},
#     "editor": {"documents:create", "documents:read", "documents:update"},
#     "viewer": {"documents:read"},
# }
#
#
# def map_provider_roles_to_permissions(provider_roles: List[str]) -> Set[str]:
#     perms: Set[str] = set()
#     for r in provider_roles:
#         perms.update(DEFAULT_ROLE_TO_PERMISSION.get(r, set()))
#     return perms
#
#
# async def validate_jwt_token(
#     token: str,
#     audience: Optional[str] = None,
#     issuer: Optional[str] = None,
# ) -> Dict[str, Any]:
#     """
#     Валидация JWT (access_token или id_token) по JWKS и базовым claims.
#     Возвращает payload (claims) при успешной проверке, иначе возбуждает исключение.
#     """
#     # Decode header to read kid
#     try:
#         header = jwt.get_unverified_header(token)
#     except JoseError as e:
#         raise ValueError("Invalid JWT header") from e
#
#     kid = header.get("kid")
#     if not kid:
#         raise ValueError("JWT missing 'kid' header")
#
#     jwk_dict = await jwks_client.get_key_for_kid(kid)
#     jwk_set = {"keys": [jwk_dict]}
#     key = JsonWebKey.import_key_set(jwk_set)
#
#     claims_options = {
#         "exp": {"essential": True},
#         "nbf": {"essential": False},
#         "iat": {"essential": False},
#     }
#
#     # issuer / audience defaults
#     issuer = issuer or settings.OIDC_ISSUER
#     # prepare required claims checkers
#     # Authlib's jwt.decode will raise when verification fails
#     try:
#         claims = jwt.decode(token, key)
#     except JoseError as e:
#         # try to give helpful message
#         raise ValueError(f"JWT verification failed: {e}") from e
#
#     # optional checks
#     if (
#         issuer
#         and claims.get("iss") != issuer
#         and not (claims.get("iss") and issuer.endswith("/") and claims.get("iss") == issuer.rstrip("/"))
#     ):
#         raise ValueError("Invalid token issuer")
#
#     if audience:
#         aud = claims.get("aud")
#         # aud can be a list or string
#         if isinstance(aud, list):
#             if audience not in aud:
#                 raise ValueError("Invalid token audience")
#         elif aud != audience:
#             raise ValueError("Invalid token audience")
#
#     # expiry handled by jwt.decode above (authlib checks exp by default)
#
#     return claims
#
#
# # Helper to extract provider roles from standard places commonly used by Keycloak etc.
# def extract_roles_from_claims(claims: Dict[str, Any]) -> List[str]:
#     # try a few common locations:
#     roles: Set[str] = set()
#
#     # 1) realm_access.roles (Keycloak default)
#     realm_access = claims.get("realm_access") or {}
#     if isinstance(realm_access, dict):
#         r = realm_access.get("roles")
#         if isinstance(r, list):
#             roles.update(r)
#
#     # 2) resource_access.{client}.roles
#     resource_access = claims.get("resource_access") or {}
#     if isinstance(resource_access, dict):
#         for client, info in resource_access.items():
#             if isinstance(info, dict):
#                 rr = info.get("roles")
#                 if isinstance(rr, list):
#                     roles.update(rr)
#
#     # 3) custom claim "roles" (array)
#     custom_roles = claims.get("roles")
#     if isinstance(custom_roles, list):
#         roles.update(custom_roles)
#
#     return list(roles)
