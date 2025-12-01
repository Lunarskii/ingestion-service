from uuid import UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
import sqlalchemy as sa

from app.domain.classifier.schemas import TopicSource
from app.domain.database.models import BaseDAO
from app.domain.database.mixins import (
    IDMixin,
    CreatedAtMixin,
)


class TopicDAO(BaseDAO, IDMixin):
    """
    DAO (ORM) модель, представляющая тему.

    :ivar id: Целочисленный идентификатор.
    :ivar code: Короткий код темы, используемый как уникальный идентификатор.
    :ivar title: Отображаемое название темы для внешнего клиента.
    :ivar description: Дополнительное описание, если недостаточно названия.
    :ivar is_active: Активность темы. Если True, то тема активна, и ее можно использовать в подборке,
                     иначе нет.
    """

    __tablename__ = "topics"

    code: Mapped[str] = mapped_column(unique=True)
    title: Mapped[str]
    description: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool]


class DocumentTopicDAO(BaseDAO, IDMixin, CreatedAtMixin):
    """
    DAO (ORM) модель, представляющая набор тем для каждого документа.

    :ivar id: Целочисленный идентификатор.
    :ivar document_id: Идентификатор документа.
    :ivar topic_id: Идентификатор темы.
    :ivar score: Счет совпадения темы с документом. Чем больше счет, тем большее совпадение документа с темой.
    :ivar created_at: Время определения темы.
    """

    __tablename__ = "document_topics"

    document_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("documents.id", ondelete="CASCADE"),
    )
    topic_id: Mapped[int] = mapped_column(
        sa.ForeignKey("topics.id", ondelete="CASCADE"),
    )
    score: Mapped[int]
    source: Mapped[TopicSource] = mapped_column(
        sa.Enum(
            TopicSource,
            name="topic_source",
            native_enum=False,
        ),
    )
