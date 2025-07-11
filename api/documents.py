import uuid

from fastapi import (
    APIRouter,
    UploadFile,
    BackgroundTasks,
    status as http_status,
)

from domain.process import process_file


router = APIRouter(prefix="/documents")


@router.post("/upload", status_code=http_status.HTTP_202_ACCEPTED)
async def upload_file(
    file: UploadFile,
    bg_tasks: BackgroundTasks,
    *,
    workspace_id: str | None = None,
):
    content: bytes = await file.read()
    filename: str = file.filename
    document_id = str(uuid.uuid4())
    bg_tasks.add_task(process_file, content, filename, document_id=document_id)
    return {"document_id": document_id}
