from fastapi import APIRouter

from api.v1.documents import router as documents_router
from api.v1.chat import router as chat_router
from api.v1.workspaces import router as workspaces_router


router = APIRouter(prefix="/v1")
router.include_router(documents_router)
router.include_router(chat_router)
router.include_router(workspaces_router)

__all__ = [
    "router",
]
