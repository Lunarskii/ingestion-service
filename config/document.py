from typing import Annotated

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class DocumentRestrictionSettings(BaseSettings):
    """
    Настройки (ограничения) документа.
    """

    max_upload_mb: Annotated[int, Field(alias="DR_MAX_UPLOAD_MB")] = 25
    allowed_extensions: Annotated[set[str], Field(alias="DR_ALLOWED_EXTENSIONS")] = {
        ".pdf",
        ".docx",
    }

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
