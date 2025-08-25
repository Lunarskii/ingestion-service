from contextlib import asynccontextmanager
from typing import (
    Any,
    Literal,
    Iterable,
)
import asyncio

from sentence_transformers import (
    SentenceTransformer,
    SentenceTransformerModelCardData,
    SimilarityFunction,
)
import torch

from domain.embedding.schemas import (
    Vector,
    VectorMetadata,
)


class EmbeddingModel:
    def __init__(
        self,
        model_name_or_path: str,
        modules: Iterable[torch.nn.Module] | None = None,
        device: str | None = None,
        prompts: dict[str, str] | None = None,
        default_prompt_name: str | None = None,
        similarity_fn_name: str | SimilarityFunction | None = None,
        cache_folder: str | None = None,
        trust_remote_code: bool = False,
        revision: str | None = None,
        local_files_only: bool = False,
        token: bool | str | None = None,
        truncate_dim: int | None = None,
        model_kwargs: dict[str, Any] | None = None,
        tokenizer_kwargs: dict[str, Any] | None = None,
        config_kwargs: dict[str, Any] | None = None,
        model_card_data: SentenceTransformerModelCardData | None = None,
        backend: Literal["torch", "onnx", "openvino"] = "torch",
        max_concurrency: int = 1,
        acquire_timeout: float | None = None,
    ):
        self.model = SentenceTransformer(
            model_name_or_path=model_name_or_path,
            modules=modules,
            device=device,
            prompts=prompts,
            default_prompt_name=default_prompt_name,
            similarity_fn_name=similarity_fn_name,
            cache_folder=cache_folder,
            trust_remote_code=trust_remote_code,
            revision=revision,
            local_files_only=local_files_only,
            token=token,
            truncate_dim=truncate_dim,
            model_kwargs=model_kwargs,
            tokenizer_kwargs=tokenizer_kwargs,
            config_kwargs=config_kwargs,
            model_card_data=model_card_data,
            backend=backend,
        )
        self._semaphore = asyncio.BoundedSemaphore(max_concurrency)
        self._acquire_timeout = acquire_timeout

    @asynccontextmanager
    async def _concurrency_guard(self) -> None:
        if self._acquire_timeout:
            await asyncio.wait_for(self._semaphore.acquire(), self._acquire_timeout)
        else:
            await self._semaphore.acquire()
        try:
            yield
        finally:
            self._semaphore.release()

    async def encode(
        self,
        sentences: str | list[str],
        metadata: list[VectorMetadata] | None = None,
        prompt_name: str | None = None,
        prompt: str | None = None,
        batch_size: int = 32,
        show_progress_bar: bool = False,
        output_value: Literal["sentence_embedding", "token_embeddings"] | None = "sentence_embedding",
        precision: Literal["float32", "int8", "uint8", "binary", "ubinary"] = "float32",
        convert_to_numpy: bool = True,
        convert_to_tensor: bool = False,
        device: str | list[str | torch.device] | None = None,
        normalize_embeddings: bool = False,
        truncate_dim: int | None = None,
        pool: dict[Literal["input", "output", "processes"], Any] | None = None,
        chunk_size: int | None = None,
        **kwargs,
    ) -> list[float] | list[torch.Tensor] | list[Vector]:
        async with self._concurrency_guard:
            embeddings = await asyncio.to_thread(
                self.model.encode,
                sentences=sentences,
                prompt_name=prompt_name,
                prompt=prompt,
                batch_size=batch_size,
                show_progress_bar=show_progress_bar,
                output_value=output_value,
                precision=precision,
                convert_to_numpy=convert_to_numpy,
                convert_to_tensor=convert_to_tensor,
                device=device,
                normalize_embeddings=normalize_embeddings,
                truncate_dim=truncate_dim,
                pool=pool,
                chunk_size=chunk_size,
                **kwargs,
            )

        if isinstance(sentences, str):
            return embeddings.tolist()

        if metadata is None:
            return embeddings

        return [
            Vector(
                values=embedding.tolist(),
                metadata=_metadata,
            )
            for _metadata, embedding in zip(metadata, embeddings)
        ]
