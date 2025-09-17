from typing import (
    Annotated,
    Any,
)
import uuid
from io import BytesIO

from fastapi import (
    APIRouter,
    status,
    Depends,
)
from fastapi.responses import StreamingResponse

from app.api.v1.documents.dependencies import document_service_dependency
from app.api.v1.dependencies import raw_storage_dependency
from app.api.v1.documents.dependencies import validate_upload_file
from app.api.v1.documents.utils import build_content_disposition
from app.api.v1.documents.exceptions import DocumentNotFoundError
from app.domain.document.dependencies import document_uow_dependency
from app.domain.document.repositories import DocumentRepository
from app.domain.document.service import DocumentService
from app.domain.document.schemas import (
    File,
    Document,
    DocumentDTO,
)
from app.domain.database.uow import UnitOfWork
from app.services import RawStorage
from tasks.main import app as celery_app


router = APIRouter(prefix="/documents")


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[Document],
)
async def documents(
    workspace_id: str,
    uow: Annotated[UnitOfWork, Depends(document_uow_dependency)],
) -> list[Document]:
    """
    Возвращает список метаданных документов в заданном рабочем пространстве.
    """

    document_repo = uow.get_repository(DocumentRepository)
    return [
        Document(**document.model_dump())
        for document in await document_repo.get_n(workspace_id=workspace_id)
    ]


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_file(
    workspace_id: str,
    file: Annotated[File, Depends(validate_upload_file)],
    service: Annotated[
        DocumentService,
        Depends(document_service_dependency),
    ],
) -> dict[str, Any]:
    """
    Принимает файл для обработки и запускает обработку в фоновом режиме.
    Немедленно возвращает сгенерированный идентификатор документа.
    """

    document_id = str(uuid.uuid4())
    await service.process(
        file=file,
        document_id=document_id,
        workspace_id=workspace_id,
    )
    return {"document_id": document_id}


@router.get("/{document_id}/download", status_code=status.HTTP_200_OK)
async def download_file(
    document_id: str,
    uow: Annotated[UnitOfWork, Depends(document_uow_dependency)],
    raw_storage: Annotated[RawStorage, Depends(raw_storage_dependency)],
) -> StreamingResponse:
    """
    Возвращает бинарный файл для скачивания по идентификатору документа в виде потоковой передачи.
    """

    document_repo = uow.get_repository(DocumentRepository)
    try:
        document: DocumentDTO = await document_repo.get(document_id)
    except Exception:
        raise DocumentNotFoundError()

    file_bytes: bytes = raw_storage.get(document.raw_storage_path)

    return StreamingResponse(
        BytesIO(file_bytes),
        media_type=document.media_type,
        headers={
            "Content-Disposition": build_content_disposition(document.name),
            "Content-Length": str(len(file_bytes)),
        },
    )


@router.get("/{document_id}/status", status_code=status.HTTP_200_OK)
async def file_status(
    document_id: str,
):
    ...
