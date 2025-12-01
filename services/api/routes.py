from fastapi import (
    APIRouter,
    Depends,
)

from services.api.routers.v1.admin.router import router as admin_router_v1
from services.api.routers.v1.auth.router import router as auth_router_v1
from services.api.routers.v1.chat.router import router as chat_router_v1
from services.api.routers.v1.documents.router import router as documents_router_v1
from services.api.routers.v1.ops.router import router as ops_router_v1
from services.api.routers.v1.workspaces.router import router as workspaces_router_v1
from app.domain.security.dependencies import require_api_key


router_v1 = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_api_key)],
)
router_v1.include_router(admin_router_v1)
router_v1.include_router(auth_router_v1)
router_v1.include_router(chat_router_v1)
router_v1.include_router(documents_router_v1)
router_v1.include_router(ops_router_v1)
router_v1.include_router(workspaces_router_v1)

__all__ = [
    "router_v1",
]
