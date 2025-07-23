from typing import (
    Annotated,
    Any,
)
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    status as http_status,
    Depends,
)

from api.v1.dependencies import (
    document_processor_dependency,
    validate_upload_file,
)
from domain.fhandler.service import DocumentProcessor


router = APIRouter(prefix="/documents")


@router.post("/upload", status_code=http_status.HTTP_202_ACCEPTED)
async def upload_file(
    file_bytes: Annotated[bytes, Depends(validate_upload_file)],
    bg_tasks: BackgroundTasks,
    document_processor: Annotated[DocumentProcessor, Depends(document_processor_dependency)],
    workspace_id: str,
) -> dict[str, Any]:
    """
    Принимает документ для обработки, немедленно возвращает document_id и выполняет обработку в фоновом режиме.
    """

    document_id = str(uuid.uuid4())
    bg_tasks.add_task(
        document_processor.process,
        file_bytes=file_bytes,
        document_id=document_id,
        workspace_id=workspace_id,
    )
    return {"document_id": document_id}
