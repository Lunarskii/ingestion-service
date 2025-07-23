from fastapi import FastAPI

from config import api_settings
from api.exc_handlers import setup_exception_handlers
from api.v1 import router as v1_router


app = FastAPI(
    title=api_settings.title,
    description=api_settings.description,
    version=api_settings.version,
    openapi_url=api_settings.openapi_url,
    openapi_prefix=api_settings.openapi_prefix,
    docs_url=api_settings.docs_url,
    redoc_url=api_settings.redoc_url,
    root_path=api_settings.root_path,
)

setup_exception_handlers(app)
app.include_router(v1_router)
