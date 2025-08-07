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
    model_type = ChatSessionDAO
    schema_type = ChatSessionDTO


class ChatMessageRepository(BaseAlchemyRepository[ChatMessageDAO, ChatMessageDTO]):
    model_type = ChatMessageDAO
    schema_type = ChatMessageDTO

    async def fetch_recent_messages(self, session_id: str, n: int) -> list[ChatMessageDTO]:
        stmt = (
            select(self.model_type)
            .where(self.model_type.session_id == session_id)
            .order_by(self.model_type.created_at.desc())
            .limit(n)
        )
        instances = await self.session.scalars(stmt)
        return list(map(self.schema_type.model_validate, instances))

    async def chat_history(self, session_id: str) -> list[ChatMessageDTO]:
        stmt = (
            select(self.model_type)
            .where(self.model_type.session_id == session_id)
            .order_by(self.model_type.created_at)
        )
        instances = await self.session.scalars(stmt)
        return list(map(self.schema_type.model_validate, instances))
