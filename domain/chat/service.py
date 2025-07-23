from sentence_transformers import SentenceTransformer

from domain.chat.schemas import (
    ChatRequest,
    ChatResponse,
    Source,
)
from domain.schemas import Vector
from stubs import llm_stub
from services import VectorStore


class ChatService:
    """
    Управляет RAG-логикой для ответов на вопросы.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: SentenceTransformer | None = None,
    ):
        self.vector_store = vector_store
        self.embedding_model = embedding_model or SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def ask(self, request: ChatRequest) -> ChatResponse:
        """
        Обрабатывает запрос в чат с помощью RAG-логики.
            1. Векторизует вопрос.
            2. Запрашивает в хранилище векторов соответствующие чанки.
            3. Генерирует ответ, используя LLM.
            4. Формирует ответ.
        """

        question_vector: list[float] = self.embedding_model.encode(request.question).tolist()
        retrieved_vectors: list[Vector] = self.vector_store.search(
            vector=Vector(values=question_vector),
            top_k=request.top_k,
            workspace_id=request.workspace_id,
        )
        sources: list[Source] = [
            Source(
                document_id=vector.metadata.get("document_id", "unknown"),
                chunk_id=vector.id,
                snippet=vector.metadata.get("text", ""),
            )
            for vector in retrieved_vectors
        ]

        return ChatResponse(
            answer=llm_stub.generate([source.snippet for source in sources]),
            sources=sources,
        )
