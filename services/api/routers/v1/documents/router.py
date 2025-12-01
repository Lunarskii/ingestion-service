from typing import (
    Annotated,
    Any,
)

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.routers.v1.documents.utils import build_content_disposition
from app.domain.document.exceptions import DocumentNotFoundError
from app.domain.document.repositories import DocumentRepository
from app.domain.document.service import DocumentService
from app.domain.document.schemas import (
    File,
    Document,
    DocumentDTO,
)
from app.domain.document.dependencies import document_service_dependency
from app.domain.database.dependencies import async_scoped_session_dependency
from app import status


router = APIRouter(prefix="/documents")


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[Document],
)
async def documents(
    workspace_id: str,
    service: Annotated[
        DocumentService,
        Depends(document_service_dependency),
    ],
) -> list[Document]:
    """
    Возвращает список документов в заданном рабочем пространстве.
    """

    return await service.get_documents(workspace_id)


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_file(
    workspace_id: str,
    file: UploadFile,
    service: Annotated[
        DocumentService,
        Depends(document_service_dependency),
    ],
) -> dict[str, Any]:
    """
    Принимает файл для обработки и сохраняет его в сырое хранилище.
    После сохранения возвращает сгенерированный идентификатор документа.
    """

    document: Document = await service.save_document(
        file=File(
            content=await file.read(),
            name=file.filename,
        ),
        workspace_id=workspace_id,
    )
    return {"document_id": document.id}


@router.get("/{document_id}/download", status_code=status.HTTP_200_OK)
async def download_file(
    document_id: str,
    service: Annotated[
        DocumentService,
        Depends(document_service_dependency),
    ],
) -> StreamingResponse:
    """
    Возвращает бинарный файл для скачивания по идентификатору документа в виде потоковой передачи.
    """

    file: File = await service.get_document_file(document_id)
    return StreamingResponse(
        file.file,
        media_type=file.type,
        headers={
            "Content-Disposition": build_content_disposition(file.name),
            "Content-Length": str(len(file.content)),
        },
    )


@router.get("/{document_id}/status", status_code=status.HTTP_200_OK)
async def document_status(
    document_id: str,
    session: Annotated[AsyncSession, Depends(async_scoped_session_dependency)],
):
    """
    Возвращает статус обработки документа, например PENDING, RUNNING, EXTRACTING и др.
    """

    document_repo = DocumentRepository(session)
    try:
        document: DocumentDTO = await document_repo.get(document_id)
    except Exception:
        raise DocumentNotFoundError()
    return {"document_status": document.status}
