from sqlalchemy import select

from app.domain.database.repositories import AlchemyRepository
from app.domain.chat.models import (
    ChatSessionDAO,
    ChatMessageDAO,
    ChatMessageSourceDAO,
)
from app.domain.chat.schemas import (
    ChatSessionDTO,
    ChatMessageDTO,
    ChatMessageSourceDTO,
)


class ChatSessionRepository(AlchemyRepository[ChatSessionDAO, ChatSessionDTO]):
    """
    Репозиторий для работы с чат-сессиями.
    """

    ...


class ChatMessageRepository(AlchemyRepository[ChatMessageDAO, ChatMessageDTO]):
    """
    Репозиторий для работы с сообщениями чата.
    """

    async def get_recent_messages(
        self,
        session_id: str,
        limit: int,
    ) -> list[ChatMessageDTO]:
        """
        Возвращает последние ``n`` сообщений указанной чат-сессии в порядке от
        самых свежих к более ранним.

        Выполняет запрос к БД, сортируя по ``created_at`` в порядке убывания и
        применяя ограничение.

        :param session_id: Идентификатор чат-сессии.
        :type session_id: str
        :param limit: Количество последних сообщений для получения.
        :type limit: int
        :return: Список DTO-схем соответствующих сообщений.
        :rtype: list[ChatMessageDTO]
        """

        stmt = (
            select(self.model_type)
            .where(self.model_type.session_id == session_id)
            .order_by(self.model_type.created_at.desc())
            .limit(limit)
        )
        instances = await self.session.scalars(stmt)
        return list(map(self.schema_type.model_validate, instances))

    async def get_messages(self, session_id: str) -> list[ChatMessageDTO]:
        """
        Возвращает всю историю сообщений для указанной чат-сессии в хронологическом порядке.

        :param session_id: Идентификатор чат-сессии.
        :type session_id: str
        :return: Список DTO-схем соответствующих сообщений.
        :rtype: list[ChatMessageDTO]
        """

        stmt = (
            select(self.model_type)
            .where(self.model_type.session_id == session_id)
            .order_by(self.model_type.created_at)
        )
        instances = await self.session.scalars(stmt)
        return list(map(self.schema_type.model_validate, instances))


class ChatMessageSourceRepository(
    AlchemyRepository[ChatMessageSourceDAO, ChatMessageSourceDTO]
):
    """
    Репозиторий для работы с источниками сообщений.
    """

    ...
