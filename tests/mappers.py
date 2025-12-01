from app.domain.document.schemas import (
    Document,
    DocumentDTO,
)


def document_dto_to_scheme(documents: DocumentDTO | list[DocumentDTO]) -> Document | list[Document]:
    def _dto_to_scheme(document: DocumentDTO) -> Document:
        return Document(
            id=document.id,
            workspace_id=document.workspace_id,
            source_id=document.source_id,
            run_id=document.run_id,
            trace_id=document.trace_id,
            sha256=document.sha256,
            raw_url=document.raw_url,
            title=document.title,
            media_type=document.media_type,
            detected_language=document.detected_language,
            page_count=document.page_count,
            author=document.author,
            creation_date=document.creation_date,
            raw_storage_path=document.raw_storage_path,
            silver_storage_path=document.silver_storage_path,
            size_bytes=document.size_bytes,
            fetched_at=document.fetched_at,
            stored_at=document.stored_at,
            ingested_at=document.ingested_at,
            status=document.status,
            error_message=document.error_message,
        )

    if isinstance(documents, DocumentDTO):
        return _dto_to_scheme(documents)
    if isinstance(documents, list):
        return list(map(_dto_to_scheme, documents))
    raise NotImplementedError()
