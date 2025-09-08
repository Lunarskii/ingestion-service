from pydantic import ConfigDict

from schemas.base import BaseSchema


class KeycloakError(Exception):
    """Thrown if any response of keycloak does not match our expectation

    Attributes:
        status_code (int): The status code of the response received
        reason (str): The reason why the requests did fail
    """

    def __init__(self, status_code: int, reason: str):
        self.status_code = status_code
        self.reason = reason
        super().__init__(f"HTTP {status_code}: {reason}")


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

        Returns:
            List[str]: If the realm access dict contains roles
        """
        if not self.realm_access and not self.resource_access:
            raise KeycloakError(
                status_code=404,
                reason="The 'realm_access' and 'resource_access' sections of the provided access token are missing.",
            )
        roles = []
        if self.realm_access:
            roles.extend(self.realm_access.get("roles", []))
        if self.azp and self.resource_access and self.azp in self.resource_access:
            roles.extend(self.resource_access[self.azp].get("roles", []))
        if not roles:
            raise KeycloakError(
                status_code=404,
                reason="The 'realm_access' and 'resource_access' sections of the provided access token did not "
                       "contain any 'roles'",
            )
        return roles

class OIDCToken(BaseSchema):
    """Keycloak representation of a token object

    Attributes:
        access_token (str): An access token
        refresh_token (str): An a refresh token, default None
        id_token (str): An issued by the Authorization Server token id, default None
    """

    access_token: str
    refresh_token: str | None = None
    id_token: str | None = None
