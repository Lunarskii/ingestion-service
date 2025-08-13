from sqlalchemy import select

from domain.database.repositories import BaseAlchemyRepository
from domain.chat.models import (
    ChatSessionDAO,
    ChatMessageDAO,
)
from domain.chat.schemas import (
    ChatSessionDTO,
    ChatMessageDTO,
)


class ChatSessionRepository(BaseAlchemyRepository[ChatSessionDAO, ChatSessionDTO]):
    """
    Репозиторий для работы с чат-сессиями.

    Наследует :class:`BaseAlchemyRepository` и задаёт конкретные типы модели и схемы:

    :ivar model_type: ORM-модель для записей сессий чата.
    :vartype model_type: type[ChatSessionDAO]
    :ivar schema_type: Pydantic-схема для сериализации/валидации сессий.
    :vartype schema_type: type[ChatSessionDTO]
    """

    model_type = ChatSessionDAO
    schema_type = ChatSessionDTO


class ChatMessageRepository(BaseAlchemyRepository[ChatMessageDAO, ChatMessageDTO]):
    """
    Репозиторий для работы с сообщениями чата.

    Наследует :class:`BaseAlchemyRepository` и задаёт конкретные типы модели и схемы:

    :ivar model_type: ORM-модель для сообщений.
    :vartype model_type: type[ChatMessageDAO]
    :ivar schema_type: Pydantic-схема для сериализации/валидации сообщений.
    :vartype schema_type: type[ChatMessageDTO]
    """

    model_type = ChatMessageDAO
    schema_type = ChatMessageDTO

    async def fetch_recent_messages(
        self, session_id: str, n: int
    ) -> list[ChatMessageDTO]:
        """
        Возвращает последние ``n`` сообщений указанной чат-сессии в порядке от
        самых свежих к более ранним.

        Выполняет запрос к БД, сортируя по ``created_at`` в порядке убывания и
        применяя ограничение.

        :param session_id: Идентификатор чат-сессии.
        :type session_id: str
        :param n: Количество последних сообщений для получения.
        :type n: int
        :return: Список pydantic-схем соответствующих сообщений.
        :rtype: list[ChatMessageDTO]
        """

        stmt = (
            select(self.model_type)
            .where(self.model_type.session_id == session_id)
            .order_by(self.model_type.created_at.desc())
            .limit(n)
        )
        instances = await self.session.scalars(stmt)
        return list(map(self.schema_type.model_validate, instances))

    async def chat_history(self, session_id: str) -> list[ChatMessageDTO]:
        """
        Возвращает всю историю сообщений для указанной чат-сессии в хронологическом порядке.

        :param session_id: Идентификатор чат-сессии.
        :type session_id: str
        :return: Список pydantic-схем соответствующих сообщений, упорядоченных по возрастанию ``created_at``.
        :rtype: list[ChatMessageDTO]
        """

        stmt = (
            select(self.model_type)
            .where(self.model_type.session_id == session_id)
            .order_by(self.model_type.created_at)
        )
        instances = await self.session.scalars(stmt)
        return list(map(self.schema_type.model_validate, instances))
