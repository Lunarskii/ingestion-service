from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Iterable,
    Union,
    Optional,
    overload,
)

from app.interfaces import EmbeddingModel
from app.types import Vector


if TYPE_CHECKING:
    import torch
    import numpy
    from sentence_transformers import (
        SentenceTransformerModelCardData,
        SimilarityFunction,
    )

    from app.types import VectorPayload


class TransformersEmbeddingModel(EmbeddingModel):
    def __init__(
        self,
        model_name_or_path: str,
        modules: Iterable["torch.nn.Module"] | None = None,
        device: str | None = None,
        prompts: dict[str, str] | None = None,
        default_prompt_name: str | None = None,
        similarity_fn_name: Union[str, "SimilarityFunction", None] = None,
        cache_folder: str | None = None,
        trust_remote_code: bool = False,
        revision: str | None = None,
        local_files_only: bool = False,
        token: bool | str | None = None,
        truncate_dim: int | None = None,
        model_kwargs: dict[str, Any] | None = None,
        tokenizer_kwargs: dict[str, Any] | None = None,
        config_kwargs: dict[str, Any] | None = None,
        model_card_data: Optional["SentenceTransformerModelCardData"] = None,
        backend: Literal["torch", "onnx", "openvino"] = "torch",
        batch_size: int = 32,
    ):
        """
        :param model_name_or_path: Имя/путь к модели для SentenceTransformer.
        :param modules: Дополнительные torch-модули для сборки модели (передаются в SentenceTransformer).
        :param device: Устройство для выполнения (например, "cpu" или "cuda:0").
        :param prompts: Словарь предопределённых подсказок (prompt templates).
        :param default_prompt_name: Имя подсказки по-умолчанию.
        :param similarity_fn_name: Название функции похожести или объект SimilarityFunction.
        :param cache_folder: Папка для кэша модели.
        :param trust_remote_code: Разрешить загрузку произвольного кода из удалённых репозиториев.
        :param revision: Ревизия модели (git, tag и т.п.).
        :param local_files_only: Использовать только локальные файлы (не тянуть из сети).
        :param token: Токен доступа.
        :param truncate_dim: Усечение размерности.
        :param model_kwargs: Дополнительные keyword-аргументы для модели.
        :param tokenizer_kwargs: Дополнительные keyword-аргументы для токенизатора.
        :param config_kwargs: Дополнительные keyword-аргументы для конфигурации.
        :param model_card_data: Метаданные модели (Model card).
        :param backend: Бэкенд выполнения ('torch', 'onnx', 'openvino').
        :param batch_size: Количество элементов данных, обрабатываемых за один шаг.
        """

        from sentence_transformers import SentenceTransformer

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
        self.batch_size: int = batch_size

    @overload
    def encode(
        self,
        sentences: str,
        prompt_name: str | None = None,
        prompt: str | None = None,
        batch_size: int | None = None,
        show_progress_bar: bool = False,
        output_value: Literal["sentence_embedding", "token_embeddings"] | None = "sentence_embedding",
        precision: Literal["float32", "int8", "uint8", "binary", "ubinary"] = "float32",
        convert_to_numpy: bool = True,
        convert_to_tensor: bool = False,
        device: str | list[Union[str, "torch.device"]] | None = None,
        normalize_embeddings: bool = False,
        truncate_dim: int | None = None,
        pool: dict[Literal["input", "output", "processes"], Any] | None = None,
        chunk_size: int | None = None,
        **kwargs,
    ) -> list[float]: ...

    @overload
    def encode(
        self,
        sentences: list[str],
        prompt_name: str | None = None,
        prompt: str | None = None,
        batch_size: int | None = None,
        show_progress_bar: bool = False,
        output_value: Literal["sentence_embedding", "token_embeddings"] | None = "sentence_embedding",
        precision: Literal["float32", "int8", "uint8", "binary", "ubinary"] = "float32",
        convert_to_numpy: bool = True,
        convert_to_tensor: bool = False,
        device: str | list[Union[str, "torch.device"]] | None = None,
        normalize_embeddings: bool = False,
        truncate_dim: int | None = None,
        pool: dict[Literal["input", "output", "processes"], Any] | None = None,
        chunk_size: int | None = None,
        **kwargs,
    ) -> list[list[float]]: ...

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
        """
        Получает эмбеддинги для строки или списка строк.

        :param sentences: Входная строка или список строк для кодирования.
        :param prompt_name: Имя промпта (если модель его поддерживает).
        :param prompt: Явный текст промпта.
        :param batch_size: Количество элементов данных, обрабатываемых за один шаг.
        :param show_progress_bar: Показывать прогресс-бар (если поддерживается).
        :param output_value: Что возвращать - эмбеддинги предложений или токенов.
        :param precision: Тип точности (влияет на формат возвращаемых данных).
        :param device: Устройство(а) для вычислений (переопределяет устройство модели).
        :param normalize_embeddings: Нормализовать ли эмбеддинги.
        :param truncate_dim: Усечь размерность эмбеддинга.
        :param pool: Параметры пула процессов/входа/выхода для encode.
        :param chunk_size: Размер чанка при больших входах.

        :return: В зависимости от входных данных:
                 - если ``sentences`` - str: ``list[float]`` (эмбеддинг);
                 - если ``sentences`` - list[str] и ``payload`` - None: ``list[list[float]]`` (список эмбеддингов);

        :raises Exception: любые исключения, проброшенные из ``SentenceTransformer.encode``.
        """

        embeddings: numpy.ndarray = self.model.encode(
            sentences=sentences,
            prompt_name=prompt_name,
            prompt=prompt,
            batch_size=batch_size or self.batch_size or 32,
            show_progress_bar=show_progress_bar,
            output_value=output_value,
            precision=precision,
            convert_to_numpy=True,
            device=device,
            normalize_embeddings=normalize_embeddings,
            truncate_dim=truncate_dim,
            pool=pool,
            chunk_size=chunk_size,
        )

        if isinstance(sentences, str):
            return embeddings.tolist()
        return [embedding.tolist() for embedding in embeddings]

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
    ) -> list[Vector]:
        """
        Получает эмбеддинги для списка строк и соединяет их с полезной нагрузкой векторов.

        :param sentences: Входная строка или список строк для кодирования.
        :param payload: Полезная нагрузка вектора.
        :param prompt_name: Имя промпта (если модель его поддерживает).
        :param prompt: Явный текст промпта.
        :param batch_size: Количество элементов данных, обрабатываемых за один шаг.
        :param show_progress_bar: Показывать прогресс-бар (если поддерживается).
        :param output_value: Что возвращать - эмбеддинги предложений или токенов.
        :param precision: Тип точности (влияет на формат возвращаемых данных).
        :param device: Устройство(а) для вычислений (переопределяет устройство модели).
        :param normalize_embeddings: Нормализовать ли эмбеддинги.
        :param truncate_dim: Усечь размерность эмбеддинга.
        :param pool: Параметры пула процессов/входа/выхода для encode.
        :param chunk_size: Размер чанка при больших входах.

        :return: Список векторов.

        :raises Exception: любые исключения, проброшенные из ``SentenceTransformer.encode``.
        """

        embeddings: list[list[float]] = self.encode(
            sentences=sentences,
            prompt_name=prompt_name,
            prompt=prompt,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            output_value=output_value,
            precision=precision,
            device=device,
            normalize_embeddings=normalize_embeddings,
            truncate_dim=truncate_dim,
            pool=pool,
            chunk_size=chunk_size,
        )
        return [
            Vector(
                values=embedding,
                payload=_payload,
            )
            for _payload, embedding in zip(payload, embeddings)
        ]
