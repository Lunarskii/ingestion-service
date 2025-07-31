from sentence_transformers import SentenceTransformer

from domain.chat.schemas import (
    ChatRequest,
    ChatResponse,
    Source,
)
from domain.schemas import Vector
from stubs import llm_stub
from services import VectorStore
from services.exc import VectorStoreDocumentsNotFound
from config import logger


class ChatService:
    """
    Управляет RAG-логикой для ответов на вопросы.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: SentenceTransformer,
    ):
        self.vector_store = vector_store
        self.embedding_model = embedding_model

    def ask(self, request: ChatRequest) -> ChatResponse:
        """
        Обрабатывает запрос в чат с помощью RAG-логики.
            1. Векторизует вопрос.
            2. Запрашивает в хранилище векторов соответствующие вектора с фильтром по 'workspace_id'.
            3. Формирует контекст для LLM.
            4. Генерирует ответ, используя LLM.
            5. Формирует ответ.
        """

        context_logger = logger.bind(workspace_id=request.workspace_id)

        try:
            context_logger.info("Векторизация вопроса")
            question_vector: list[float] = self.embedding_model.encode(
                request.question
            ).tolist()

            context_logger.info("Поиск top_k чанков в VectorStore", top_k=request.top_k)
            retrieved_vectors: list[Vector] = self.vector_store.search(
                vector=Vector(values=question_vector),
                top_k=request.top_k,
                workspace_id=request.workspace_id,
            )

            sources: list[Source] = [
                Source(
                    document_id=vector.metadata.get("document_id", ""),
                    chunk_id=vector.id,
                    snippet=vector.metadata.get("text", ""),
                )
                for vector in retrieved_vectors
            ]
            prompt: str = "\n".join(
                [
                    "Основываясь на следующем контексте, ответь на вопрос.",
                    "---",
                    "Контекст:",
                    "\n".join([source.snippet for source in sources]),
                    "---",
                    f"Вопрос: {request.question}",
                ],
            )

            context_logger.info("Получение ответа от LLM")
            answer: str = llm_stub.generate(prompt)
        except VectorStoreDocumentsNotFound as e:
            context_logger.error(
                "Не удалось обработать запрос к чату", error_message=e.message
            )
            raise VectorStoreDocumentsNotFound(e.message)
        except Exception as e:
            context_logger.error(
                "Не удалось обработать запрос к чату", error_message=str(e)
            )
        else:
            return ChatResponse(
                answer=answer,
                sources=sources,
            )
