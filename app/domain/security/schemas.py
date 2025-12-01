from pydantic import ConfigDict

from app.domain.security.exceptions import KeycloakError
from app.schemas import (
    BaseSchema,
    BaseDTO,
    IDMixin,
    CreatedAtMixin,
)
from app import status


class OIDCUser(BaseSchema):
    """
    Схема представления OIDC-пользователя.

    :ivar jti: JWT Идентификатор.
    :ivar kid: Идентификатор ключа.
    :ivar iss: Издатель токена.
    :ivar sub: Субъект, которому выдан токен.
    :ivar typ: Тип токена. По умолчанию для JWT всегда равно "JWT". Некоторые приложения могут
               игнорировать это поле, но рекомендуется оставить поле для обратной совместимости.
    :ivar azp: Авторизованная сторона - сторона, которой был выдан идентификационный токен.
    :ivar aud: Аудитория токена.
    :ivar email: Предпочитаемый адрес электронной почты.
    :ivar preferred_username: Предпочитаемое имя пользователя. Может быть любым - почта, телефонный номер и др.
    :ivar name: Имя пользователя.
    :ivar given_name: Имя пользователя.
    :ivar family_name: Фамилия пользователя.
    :ivar scope: Доступ к каким ресурсам имеет пользователь.
    :ivar email_verified: True, если адрес электронной почты был подтвержден, иначе False.

    :ivar exp: Время истечения срока действия.
    :ivar nbf: Время, до наступления которого токен не может быть принят к обработке.
    :ivar iat: Время создания токена.

    :ivar realm_access: Содержит роли, назначенные пользователю на уровне реалма.
    :ivar resource_access: Содержит роли, назначенные пользователю на уровне ресурса.
    """

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
                message="В предоставленном токене доступа отсутствуют роли",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        roles = []
        if self.realm_access:
            roles.extend(self.realm_access.get("roles", []))
        if self.azp and self.resource_access and self.azp in self.resource_access:
            roles.extend(self.resource_access[self.azp].get("roles", []))
        if not roles:
            raise KeycloakError(
                message="В предоставленном токене доступа отсутствуют роли",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return roles


class OIDCToken(BaseSchema):
    """
    Схема представления OIDC-токена.

    :ivar access_token: Токен доступа.
    :ivar refresh_token: Токен обновления.
    :ivar id_token: Токен безопасности.
    """

    access_token: str
    refresh_token: str | None = None
    id_token: str | None = None


class APIKeysDTO(BaseDTO, IDMixin, CreatedAtMixin):
    """
    DTO (Data Transfer Object) для представления API-ключа.

    :ivar id: Идентификатор API-ключа.
    :ivar key_hash: Хэш API-ключа.
    :ivar label: Название API-ключа.
    :ivar is_active: Флаг валидности API-ключа. Если False, то не валиден.
    :ivar created_at: Время создания API-ключа.
    """

    key_hash: str
    label: str
    is_active: bool
