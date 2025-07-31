from typing import Annotated

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class DatabaseSettings(BaseSettings):
    """
    Настройки базы данных
    """

    dialect: Annotated[str, Field(alias="DATABASE_DIALECT")]
    driver: Annotated[str, Field(alias="DATABASE_DRIVER")] = "asyncpg"
    username: Annotated[str, Field(alias="DATABASE_USERNAME")]
    password: Annotated[str, Field(alias="DATABASE_PASSWORD")]
    host: Annotated[str, Field(alias="DATABASE_HOST")]
    port: Annotated[int, Field(alias="DATABASE_PORT")]
    name: Annotated[str, Field(alias="DATABASE_NAME")]
    echo: Annotated[bool, Field(alias="DATABASE_ECHO")] = False
    echo_pool: Annotated[bool, Field(alias="DATABASE_ECHO_POOL")] = False
    pool_pre_ping: Annotated[bool, Field(alias="DATABASE_POOL_PRE_PING")] = True
    auto_flush: Annotated[bool, Field(alias="DATABASE_AUTO_FLUSH")] = False
    auto_commit: Annotated[bool, Field(alias="DATABASE_AUTO_COMMIT")] = False
    expire_on_commit: Annotated[bool, Field(alias="DATABASE_EXPIRE_ON_COMMIT")] = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def url(self) -> str:
        return f"{self.dialect}+{self.driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"
