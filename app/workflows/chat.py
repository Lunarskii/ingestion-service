from typing import (
    Literal,
    Callable,
    AsyncContextManager,
)
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chat.schemas import (
    RetrievalSource,
    RetrievalChunk,
)
from app.domain.document.repositories import DocumentRepository
from app.domain.document.schemas import DocumentDTO
from app.domain.database.dependencies import async_scoped_session_ctx
from app.types import (
    ScoredVector,
    Document,
)
from app.interfaces import (
    FileStorage,
    VectorStorage,
    Reranker,
)
from app.defaults import defaults


# TODO сделать так, что бы search_sources просто возвращал полученные источники, а реранк отделить в отдельную функцию в этом же Workflow
async def search_sources(
    question: str,
    embedding: list[float],
    workspace_id: str,
    *,
    top_k: int | Literal["all"] = 10,
    score_threshold: float = 0.35,
    vector_storage: VectorStorage = defaults.vector_storage,
    silver_storage: FileStorage = defaults.silver_storage,
    session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
) -> list[RetrievalSource]:
    """

    """

    scored_vectors: list[ScoredVector] = vector_storage.search(
        embedding=embedding,
        top_k=top_k,
        workspace_id=workspace_id,
        score_threshold=score_threshold,
    )

    async def get_documents(documents_ids: list[str]) -> list[DocumentDTO]:
        async with session_ctx() as session:
            repo = DocumentRepository(session)
            return await repo.get_n(id=documents_ids)

    document_chunks_ids: dict[str, list[str]] = defaultdict(list)
    scores: dict[str, float] = defaultdict(float)

    for scored_vector in scored_vectors:
        payload = scored_vector.payload
        if payload:
            document_chunks_ids[payload.document_id].append(payload.chunk_id)
            scores[payload.chunk_id] = scored_vector.score

    documents: list[DocumentDTO] = await get_documents(list(document_chunks_ids.keys()))
    retrieval_sources: list[RetrievalSource] = []

    for document_dto in documents:
        if not document_dto.silver_storage_chunks_path:
            continue

        silver_document: bytes = silver_storage.get(document_dto.silver_storage_chunks_path)
        document = Document.model_validate_json(silver_document)

        if not document.chunks:
            continue

        retrieval_sources.append(
            RetrievalSource(
                source_id=document_dto.id,
                title=document_dto.title,
                chunks=[
                    RetrievalChunk(
                        chunk_id=chunk.id,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        retrieval_score=scores[chunk.id],
                        text=chunk.text,
                    )
                    for chunk in document.chunks
                    if chunk.id in document_chunks_ids[document_dto.id]
                ],
            ),
        )

    return retrieval_sources


def rerank(
    question: str,
    sources: list[RetrievalSource],
    *,
    top_k: int | None = 10,
    absolute_threshold: float | None = None,
    relative_threshold_frac: float | None = 0.5,
    reranker: Reranker = defaults.reranker,
) -> list[RetrievalSource]:
    alpha: float = 0.35
    beta: float = 0.7

    max_combined_score: float = 0.0

    for source in sources:
        pairs: list[tuple[str, str]] = [
            (question, chunk.text)
            for chunk in source.chunks
            if chunk.text is not None
        ]

        reranked_scores: list[float] = reranker.predict(pairs)

        min_score: float = min(reranked_scores)
        max_score: float = max(reranked_scores)
        denom = (max_score - min_score) if (max_score - min_score) > 1e-12 else 1.0
        normed = [(score - min_score) / denom for score in reranked_scores]

        for chunk, reranked_score, nr in zip(source.chunks, reranked_scores, normed):
            chunk.reranked_score = reranked_score
            chunk.combined_score = alpha * chunk.retrieval_score + beta * nr
            max_combined_score = max(max_combined_score, chunk.combined_score)

    reranked_sources: list[RetrievalSource] = []
    chunks_count: int = 0

    for source in sources:
        reranked_chunks: list[RetrievalChunk] = []

        for chunk in source.chunks:
            keep = True
            if absolute_threshold and chunk.combined_score:
                keep = chunk.combined_score >= absolute_threshold
            elif relative_threshold_frac and chunk.combined_score:
                keep = chunk.combined_score >= (relative_threshold_frac * max_combined_score)
            if keep:
                reranked_chunks.append(chunk)
                chunks_count += 1
            if top_k and chunks_count >= top_k:
                break

        reranked_sources.append(
            RetrievalSource(
                source_id=source.source_id,
                title=source.title,
                chunks=reranked_chunks,
            ),
        )

    return reranked_sources
