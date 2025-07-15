from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class StorageSettings(BaseSettings):
    """
    Настройки хранилищ для локальной разработки.
    """

    raw_storage_path: Annotated[str, Field(alias="DEFAULT_RAW_STORAGE_PATH")] = (
        "./local_storage/raw/"
    )
    index_path: Annotated[str, Field(alias="DEFAULT_INDEX_PATH")] = (
        "./local_storage/index/"
    )
    sqlite_url: Annotated[str, Field(alias="DEFAULT_SQLITE_URL")] = (
        "./local_storage/sqlite.db"
    )
