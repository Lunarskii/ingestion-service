from fastapi import APIRouter

from app.api.v1.auth.router import router as auth_router
from app.api.v1.chat.router import router as chat_router
from app.api.v1.documents.router import router as documents_router
from app.api.v1.ops.router import router as ops_router
from app.api.v1.workspaces.router import router as workspaces_router


router = APIRouter(prefix="/v1")
router.include_router(auth_router)
router.include_router(chat_router)
router.include_router(documents_router)
router.include_router(ops_router)
router.include_router(workspaces_router)

__all__ = [
    "router",
]
