from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """
    Настройки API (FastAPI).
    """

    title: Annotated[str, Field(alias="API_TITLE")] = "Ingestion Service"
    description: Annotated[str, Field(alias="API_DESCRIPTION")] = ""
    version: Annotated[str, Field(alias="API_VERSION")] = "0.1.0"
    openapi_url: Annotated[str, Field(alias="OPENAPI_URL")] = "/openapi.json"
    openapi_prefix: Annotated[str, Field(alias="API_PREFIX")] = ""
    docs_url: Annotated[str, Field(alias="DOCS_URL")] = "/docs"
    redoc_url: Annotated[str, Field(alias="REDOC_URL")] = "/redoc"
    root_path: Annotated[str, Field(alias="ROOT_PATH")] = ""
