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
    raw_storage_dependency,
)
from api.v1.utils import build_content_disposition
from api.v1.exceptions import DocumentNotFoundError
from domain.document.dependencies import document_uow_dependency
from domain.document.repositories import DocumentRepository
from domain.document.service import DocumentService
from domain.document.schemas import (
    File,
    Document,
    DocumentDTO,
)
from domain.database.connection import get_async_scoped_session
from domain.database.uow import UnitOfWork
from services import RawStorage


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


async def _bg_process_file(
    service: DocumentService,
    file: File,
    document_id: str,
    workspace_id: str,
):
    session = get_async_scoped_session()
    async with UnitOfWork(session) as uow:
        uow.register_repository(DocumentRepository)
        await service.process(
            file=file,
            document_id=document_id,
            workspace_id=workspace_id,
            uow=uow,
        )


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_file(
    workspace_id: str,
    file: Annotated[File, Depends(validate_upload_file)],
    bg_tasks: BackgroundTasks,
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
    bg_tasks.add_task(
        _bg_process_file,
        service=service,
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
