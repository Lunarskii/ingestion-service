from typing import Any
from datetime import datetime

from aiokafka.structs import ConsumerRecord

from app.domain.document.service import DocumentService
from app.domain.document.schemas import (
    DocumentStatus,
    DocumentDTO,
)
from app.domain.document.exceptions import DuplicateDocumentError
from app.core import logger
from app.metrics.kafka import metrics


async def save_document_meta(msg: ConsumerRecord) -> None:
    msg_json: dict[str, Any] = msg.value

    if not msg_json:
        logger.warning(
            "Сообщение пустое, невозможно сохранить метаданные документа",
            topic=msg.topic,
            partition=msg.partition,
            offset=msg.offset,
        )
        return

    # TODO ENV AUTO_PROVISION_WORKSPACE или иначе. Сделать авто-создание пространства, если его не существует
    service = DocumentService()
    try:
        await service.save_document_metadata(
            DocumentDTO(
                id=msg_json.get("doc_id"),
                workspace_id=msg_json.get("workspace_id"), # TODO сменить на workspace_code
                source_id=msg_json.get("source_id"),
                run_id=msg_json.get("run_id"),
                sha256=msg_json.get("sha256"),
                raw_url=msg_json.get("raw_url"),
                title=msg_json.get("title"),
                media_type=msg_json.get("mime"),
                raw_storage_path=msg_json.get("stored_path", "").lstrip("s3://"),
                size_bytes=msg_json.get("size_bytes"),
                fetched_at=datetime.fromisoformat(msg_json.get("fetched_at")),
                stored_at=datetime.fromisoformat(msg_json.get("stored_at")),
                status=DocumentStatus.pending,
            ),
        )
    except DuplicateDocumentError:
        metrics.duplicates_total.labels(msg.topic, "some_client_id").inc()
        # TODO отправить в DLQ, если будет
