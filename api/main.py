from fastapi import FastAPI

from config import settings
from api.exc_handlers import setup_exception_handlers
from api.events import setup_event_handlers
from api.v1 import router as v1_router


app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    openapi_url=settings.api.openapi_url,
    openapi_prefix=settings.api.openapi_prefix,
    docs_url=settings.api.docs_url,
    redoc_url=settings.api.redoc_url,
    root_path=settings.api.root_path,
)

setup_exception_handlers(app)
setup_event_handlers(app)
app.include_router(v1_router)
