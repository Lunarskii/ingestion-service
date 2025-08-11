from typing import (
    Annotated,
    Any,
)
import uuid
from io import BytesIO

from fastapi import (
    APIRouter,
    BackgroundTasks,
    status,
    Depends,
)
from fastapi.responses import StreamingResponse

from api.v1.dependencies import (
    validate_upload_file,
    document_service_dependency,
    metadata_repository_dependency,
    raw_storage_dependency,
)
from api.v1.utils import build_content_disposition
from api.v1.exc import DocumentNotFoundError
from domain.document.service import DocumentService
from domain.document.schemas import File, DocumentMeta
from services import (
    MetadataRepository,
    RawStorage,
)


router = APIRouter(prefix="/documents")


@router.get("", status_code=status.HTTP_200_OK)
async def documents(
    metadata_repository: Annotated[
        MetadataRepository,
        Depends(metadata_repository_dependency),
    ],
    workspace_id: str,
) -> list[DocumentMeta]:
    """
    Возвращает список метаданных документов в заданном пространстве.
    """

    return metadata_repository.get(workspace_id=workspace_id)


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_file(
    file: Annotated[File, Depends(validate_upload_file)],
    bg_tasks: BackgroundTasks,
    service: Annotated[
        DocumentService,
        Depends(document_service_dependency),
    ],
    workspace_id: str,
) -> dict[str, Any]:
    """
    Принимает документ для обработки, немедленно возвращает ID документа и выполняет обработку в фоновом режиме.
    """

    document_id = str(uuid.uuid4())
    bg_tasks.add_task(
        service.process,
        file=file,
        document_id=document_id,
        workspace_id=workspace_id,
    )
    return {"document_id": document_id}


@router.get("/{document_id}/download", status_code=status.HTTP_200_OK)
async def download_file(
    document_id: str,
    metadata_repository: Annotated[
        MetadataRepository,
        Depends(metadata_repository_dependency),
    ],
    raw_storage: Annotated[RawStorage, Depends(raw_storage_dependency)],
) -> StreamingResponse:
    metadata: list[DocumentMeta] = metadata_repository.get(document_id=document_id)
    if not metadata:
        raise DocumentNotFoundError()

    metadata0: DocumentMeta = metadata[0]
    file_bytes: bytes = raw_storage.get(metadata0.raw_storage_path)
    headers: dict[str, str] = {
        "Content-Disposition": build_content_disposition(metadata0.document_name),
        "Content-Length": str(len(file_bytes)),
    }

    return StreamingResponse(
        BytesIO(file_bytes),
        media_type=metadata0.media_type,
        headers=headers,
    )
