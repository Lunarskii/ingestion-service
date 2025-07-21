from typing import Annotated

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class StorageSettings(BaseSettings):
    """
    Настройки хранилищ для локальной разработки.
    """

    raw_storage_path: Annotated[str, Field(alias="RAW_STORAGE_PATH")] = (
        "./local_storage/raw/"
    )
    index_path: Annotated[str, Field(alias="INDEX_PATH")] = "./local_storage/index/"
    sqlite_url: Annotated[str, Field(alias="SQLITE_URL")] = "./local_storage/sqlite.db"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
