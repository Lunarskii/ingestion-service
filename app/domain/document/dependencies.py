from app.domain.document.service import DocumentService


async def document_service_dependency() -> DocumentService:
    return DocumentService()
