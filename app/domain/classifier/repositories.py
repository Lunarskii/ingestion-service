from sqlalchemy import select

from app.adapters.sqlalchemy_repository import AlchemyRepository
from app.domain.classifier.models import (
    TopicDAO,
    DocumentTopicDAO,
)
from app.domain.classifier.schemas import (
    TopicDTO,
    DocumentTopicDTO,
)
from app.domain.database.exceptions import EntityNotFoundError


class TopicRepository(AlchemyRepository[TopicDAO, TopicDTO]):
    """
    Репозиторий для работы с темами.
    """

    async def get_topic_by_code(self, code: str) -> TopicDTO:
        stmt = select(self.model_type).where(self.model_type.code == code)
        instance = await self.session.scalar(stmt)
        if instance is None:
            raise EntityNotFoundError()
        return self.schema_type.model_validate(instance)


class DocumentTopicRepository(AlchemyRepository[DocumentTopicDAO, DocumentTopicDTO]):
    """
    Репозиторий для работы с темами документов.
    """

    ...
