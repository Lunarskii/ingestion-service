from fastapi import FastAPI

from services.api.exc_handlers import setup_exception_handlers
from services.api.events import setup_event_handlers
from services.api.routes import router_v1
from app.domain.security.dependencies import (
    require_api_key,
    required_roles,
)
from app.core import (
    settings,
    logger,
)


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
app.include_router(router_v1)

if not settings.api.api_key_required:
    app.dependency_overrides[require_api_key] = lambda: None
    logger.warning("X-API-Key заголовок отключен - только для разработки!")
if not settings.api.api_auth_required:
    app.dependency_overrides[required_roles] = lambda: None
    logger.warning("API Auth отключен - только для разработки!")
