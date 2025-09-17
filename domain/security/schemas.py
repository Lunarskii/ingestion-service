from pydantic import ConfigDict

from domain.security.exceptions import (
    status,
    KeycloakError,
)
from schemas import (
    BaseSchema,
    BaseDTO,
    IDMixin,
    CreatedAtMixin,
)


class OIDCUser(BaseSchema):
    model_config = ConfigDict(extra="allow")

    jti: str | None = None
    kid: str | None = None
    iss: str | None = None
    sub: str
    typ: str | None = None
    azp: str | None = None
    aud: str | None = None
    email: str | None = None
    preferred_username: str | None = None
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    scope: str | None = None
    email_verified: bool

    exp: int
    nbf: int | None = None
    iat: int

    realm_access: dict | None = None
    resource_access: dict | None = None

    @property
    def roles(self) -> list[str]:
        """
        Возвращает роли пользователя.
        """
        if not self.realm_access and not self.resource_access:
            raise KeycloakError(
                message="В предоставленном access токене отсутствуют поля 'realm_access' и 'resource_access'",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        roles = []
        if self.realm_access:
            roles.extend(self.realm_access.get("roles", []))
        if self.azp and self.resource_access and self.azp in self.resource_access:
            roles.extend(self.resource_access[self.azp].get("roles", []))
        if not roles:
            raise KeycloakError(
                message="В предоставленном access токене 'realm_access' и 'resource_access' не содержат 'roles'",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return roles


class OIDCToken(BaseSchema):
    access_token: str
    refresh_token: str | None = None
    id_token: str | None = None


class APIKeysDTO(BaseDTO, IDMixin, CreatedAtMixin):
    key_hash: bytes
    label: str
    is_active: bool
