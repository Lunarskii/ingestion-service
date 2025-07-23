from typing import Annotated

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class EmbeddingSettings(BaseSettings):
    """
    Настройки Embedding модели.
    """

    model_name: Annotated[str, Field(alias="EMBEDDING_MODEL_NAME")] = "sentence-transformers/all-MiniLM-L6-v2"
    device: Annotated[str | None, Field(alias="EMBEDDING_MODEL_DEVICE")] = None
    cache_folder: Annotated[str | None, Field(alias="EMBEDDING_MODEL_CACHE_FOLDER")] = None
    token: Annotated[bool | str | None, Field(alias="EMBEDDING_MODEL_TOKEN")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_parse_none_str="None",
        extra="ignore",
    )
