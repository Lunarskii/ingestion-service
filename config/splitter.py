from typing import Annotated

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class TextSplitterSettings(BaseSettings):
    """
    Настройки для разделителя текста.
    """

    chunk_size: Annotated[int, Field(alias="TEXT_SPLITTER_CHUNK_SIZE")] = 500
    chunk_overlap: Annotated[int, Field(alias="TEXT_SPLITTER_CHUNK_OVERLAP")] = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
