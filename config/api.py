from typing import Annotated

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class APISettings(BaseSettings):
    """
    Настройки API (FastAPI).
    """

    title: Annotated[str, Field(alias="API_TITLE")] = "Ingestion Service"
    description: Annotated[str, Field(alias="API_DESCRIPTION")] = ""
    version: Annotated[str, Field(alias="API_VERSION")] = "0.1.0"
    openapi_url: Annotated[str | None, Field(alias="OPENAPI_URL")] = "/openapi.json"
    openapi_prefix: Annotated[str, Field(alias="API_PREFIX")] = ""
    docs_url: Annotated[str | None, Field(alias="DOCS_URL")] = "/docs"
    redoc_url: Annotated[str | None, Field(alias="REDOC_URL")] = "/redoc"
    root_path: Annotated[str, Field(alias="ROOT_PATH")] = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_parse_none_str="None",
        extra="ignore",
    )
