from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.adapters.sqlalchemy_repository import AlchemyRepository
from app.domain.database.exceptions import (
    ValidationError,
    DatabaseError,
)
from app.domain.document.models import (
    DocumentDAO,
    DocumentEventDAO,
)
from app.domain.document.schemas import (
    DocumentDTO,
    DocumentEventDTO,
    DocumentStage,
    DocumentStatus,
)
from app.core import logger


class DocumentRepository(AlchemyRepository[DocumentDAO, DocumentDTO]):
    """
    Репозиторий для работы с документами.
    """

    async def get_pending_documents_ids(self) -> list[str]:
        stmt = select(self.model_type.id).where(
            self.model_type.status == DocumentStatus.pending
        )
        instances = await self.session.scalars(stmt)
        return instances.all()


class DocumentEventRepository(AlchemyRepository[DocumentEventDAO, DocumentEventDTO]):
    """
    Репозиторий для работы с событиями документов.
    """

    async def update_document_event(
        self,
        document_id: str,
        stage: DocumentStage,
        **kwargs,
    ) -> DocumentEventDTO:
        stmt = select(self.model_type).where(
            self.model_type.document_id == document_id,
            self.model_type.stage == stage,
        )

        try:
            instance = await self.session.scalar(stmt)

            for key, value in kwargs.items():
                if not hasattr(instance, key):
                    self._logger.error(
                        ValidationError.message,
                        field=key,
                    )
                    raise ValidationError()
                setattr(instance, key, value)

            await self.session.flush()
            return self.schema_type.model_validate(instance)
        except SQLAlchemyError as e:
            logger.error(
                DatabaseError.message,
                error_message=str(e),
            )
            raise DatabaseError()
