from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    workspace_id: str
    top_k: int = 3


class Source(BaseModel):
    document_id: str
    chunk_id: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
