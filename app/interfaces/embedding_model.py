from typing import (
    TYPE_CHECKING,
    Protocol,
    Any,
    Union,
    Literal,
)


if TYPE_CHECKING:
    import torch

    from app.types import (
        Vector,
        VectorPayload,
    )


class EmbeddingModel(Protocol):
    def encode(
        self,
        sentences: str | list[str],
        prompt_name: str | None = None,
        prompt: str | None = None,
        batch_size: int | None = None,
        show_progress_bar: bool = False,
        output_value: Literal["sentence_embedding", "token_embeddings"] | None = "sentence_embedding",
        precision: Literal["float32", "int8", "uint8", "binary", "ubinary"] = "float32",
        device: str | list[Union[str, "torch.device"]] | None = None,
        normalize_embeddings: bool = False,
        truncate_dim: int | None = None,
        pool: dict[Literal["input", "output", "processes"], Any] | None = None,
        chunk_size: int | None = None,
    ) -> list[float] | list[list[float]]:
        ...

    def encode_with_payload(
        self,
        sentences: list[str],
        payload: list["VectorPayload"],
        prompt_name: str | None = None,
        prompt: str | None = None,
        batch_size: int | None = None,
        show_progress_bar: bool = False,
        output_value: Literal["sentence_embedding", "token_embeddings"] | None = "sentence_embedding",
        precision: Literal["float32", "int8", "uint8", "binary", "ubinary"] = "float32",
        device: str | list[Union[str, "torch.device"]] | None = None,
        normalize_embeddings: bool = False,
        truncate_dim: int | None = None,
        pool: dict[Literal["input", "output", "processes"], Any] | None = None,
        chunk_size: int | None = None,
    ) -> list["Vector"]:
        ...
