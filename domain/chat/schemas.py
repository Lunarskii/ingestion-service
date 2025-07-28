from pydantic import BaseModel


class ChatRequest(BaseModel):
    """
    Схема запроса к ChatService.

    :param question: Текст вопроса пользователя.
    :type question: str
    :param workspace_id: Идентификатор рабочего пространства.
    :type workspace_id: str
    :param top_k: Количество релевантных отрывков (чанков) для поиска в RAG.
    :type top_k: int
    """

    question: str
    workspace_id: str
    top_k: int = 3


class Source(BaseModel):
    """
    Схема источника (чанка документа).

    :param document_id: Уникальный идентификатор документа.
    :type document_id: str
    :param chunk_id: Идентификатор чанка внутри документа.
    :type chunk_id: str
    :param snippet: Чанк.
    :type snippet: str
    """

    document_id: str
    chunk_id: str
    snippet: str


class ChatResponse(BaseModel):
    """
    Схема ответа от ChatService.

    :param answer: Сгенерированный ответ на вопрос.
    :type answer: str
    :param sources: Список источников (чанков), на которых основан ответ.
    :type sources: list[Source]
    """

    answer: str
    sources: list[Source]
