from typing import Annotated

from fastapi import (
    APIRouter,
    UploadFile,
    Depends,
    BackgroundTasks,
)

from services import RawStorage
from api.dependencies import raw_storage_dependency


router = APIRouter(prefix="/documents")


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    raw_storage: Annotated[RawStorage, Depends(raw_storage_dependency)],
    bg_tasks: BackgroundTasks,
    *,
    workspace_id: str | None = None,
):
    bg_tasks.add_task(raw_storage.save, await file.read(), "./local_storage/raw/")

