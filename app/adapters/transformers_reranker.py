from typing import (
    TYPE_CHECKING,
    Callable,
    Literal,
    Optional,
)

from app.interfaces import Reranker


if TYPE_CHECKING:
    from sentence_transformers import CrossEncoderModelCardData


class CrossEncoderReranker(Reranker):
    def __init__(
        self,
        model_name_or_path: str,
        num_labels: int | None = None,
        max_length: int | None = None,
        activation_fn: Callable | None = None,
        device: str | None = None,
        cache_folder: str | None = None,
        trust_remote_code: bool = False,
        revision: str | None = None,
        local_files_only: bool = False,
        token: bool | str | None = None,
        model_kwargs: dict | None = None,
        tokenizer_kwargs: dict | None = None,
        config_kwargs: dict | None = None,
        model_card_data: Optional["CrossEncoderModelCardData"] = None,
        backend: Literal["torch", "onnx", "openvino"] = "torch",
        batch_size: int = 32,
    ):
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(
            model_name_or_path=model_name_or_path,
            num_labels=num_labels,
            max_length=max_length,
            activation_fn=activation_fn,
            device=device,
            cache_folder=cache_folder,
            trust_remote_code=trust_remote_code,
            revision=revision,
            local_files_only=local_files_only,
            token=token,
            model_kwargs=model_kwargs,
            tokenizer_kwargs=tokenizer_kwargs,
            config_kwargs=config_kwargs,
            model_card_data=model_card_data,
            backend=backend,
        )
        self.batch_size = batch_size

    def predict(
        self,
        pairs: list[tuple[str, str]],
        batch_size: int | None = None,
    ) -> list[float]:
        return self.model.predict(
            sentences=pairs,
            batch_size=batch_size or self.batch_size or 32,
            show_progress_bar=False,
            convert_to_numpy=True,
        ).tolist()
