from fastapi import (
    APIRouter,
    UploadFile,
)


router = APIRouter(prefix="/documents")


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    *,
    workspace_id: str | None = None,
): ...
