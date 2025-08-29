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
import numpy

from domain.embedding.schemas import (
    Vector,
    VectorMetadata,
)


class EmbeddingModel:
    """
    Обертка над SentenceTransformer с ограничением параллелизма.

    Основные возможности
    -------------------
    * Инициализация SentenceTransformer с проксированием аргументов конструктора.
    * Управление максимумом одновременных вызовов ``encode`` через ``asyncio.BoundedSemaphore``.
    * Асинхронный метод ``encode`` выполняет реальную работу в пуле потоков
      (``asyncio.to_thread``), так как ``SentenceTransformer.encode`` - синхронная функция.
    """

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
        """
        :param model_name_or_path: Имя/путь к модели для SentenceTransformer.
        :type model_name_or_path: str
        :param modules: Дополнительные torch-модули для сборки модели (передаются в SentenceTransformer).
        :type modules: Iterable[torch.nn.Module] | None
        :param device: Устройство для выполнения (например, "cpu" или "cuda:0").
        :type device: str | None
        :param prompts: Словарь предопределённых подсказок (prompt templates).
        :type prompts: dict[str, str] | None
        :param default_prompt_name: Имя подсказки по-умолчанию.
        :type default_prompt_name: str | None
        :param similarity_fn_name: Название функции похожести или объект SimilarityFunction.
        :type similarity_fn_name: str | SimilarityFunction | None
        :param cache_folder: Папка для кэша модели.
        :type cache_folder: str | None
        :param trust_remote_code: Разрешить загрузку произвольного кода из удалённых репозиториев.
        :type trust_remote_code: bool
        :param revision: Ревизия модели (git, tag и т.п.).
        :type revision: str | None
        :param local_files_only: Использовать только локальные файлы (не тянуть из сети).
        :type local_files_only: bool
        :param token: Токен доступа.
        :type token: bool | str | None
        :param truncate_dim: Усечение размерности.
        :type truncate_dim: int | None
        :param model_kwargs: Дополнительные keyword-аргументы для модели.
        :type model_kwargs: dict[str, Any] | None
        :param tokenizer_kwargs: Дополнительные keyword-аргументы для токенизатора.
        :type tokenizer_kwargs: dict[str, Any] | None
        :param config_kwargs: Дополнительные keyword-аргументы для конфигурации.
        :type config_kwargs: dict[str, Any] | None
        :param model_card_data: Метаданные модели (Model card).
        :type model_card_data: SentenceTransformerModelCardData | None
        :param backend: Бэкенд выполнения ('torch', 'onnx', 'openvino').
        :type backend: Literal["torch", "onnx", "openvino"]
        :param max_concurrency: Максимальное число одновременных вызовов ``encode``.
        :type max_concurrency: int
        :param acquire_timeout: Таймаут на ожидание семафора при попытке получить слот.
                                Если None - ждать бесконечно.
        :type acquire_timeout: float | None
        """

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
        """
        Асинхронный контекстный менеджер для контроля конкуренции.

        Блокирует вход, ожидая освобождения семафора. Если при создании объекта был
        передан ``acquire_timeout``, применяется ``asyncio.wait_for`` с указанным таймаутом.

        :raises asyncio.TimeoutError: Если не удалось захватить семафор в отведённый таймаут.
        """

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
        output_value: Literal["sentence_embedding", "token_embeddings"]
        | None = "sentence_embedding",
        precision: Literal["float32", "int8", "uint8", "binary", "ubinary"] = "float32",
        convert_to_numpy: bool = True,
        convert_to_tensor: bool = False,
        device: str | list[str | torch.device] | None = None,
        normalize_embeddings: bool = False,
        truncate_dim: int | None = None,
        pool: dict[Literal["input", "output", "processes"], Any] | None = None,
        chunk_size: int | None = None,
        **kwargs,
    ) -> list[float] | numpy.ndarray | list[Vector]:
        """
        Асинхронно получает эмбеддинги для строки или списка строк.

        Аргументы
        ---------
        :param sentences: Входная строка или список строк для кодирования.
        :type sentences: str | list[str]
        :param metadata: Необязательный список метаданных для каждого входного предложения.
        :type metadata: list[VectorMetadata] | None
        :param prompt_name: Имя промпта (если модель его поддерживает).
        :type prompt_name: str | None
        :param prompt: Явный текст промпта.
        :type prompt: str | None
        :param batch_size: Размер батча при кодировании.
        :type batch_size: int
        :param show_progress_bar: Показывать прогресс-бар (если поддерживается).
        :type show_progress_bar: bool
        :param output_value: Что возвращать - эмбеддинги предложений или токенов.
        :type output_value: Literal["sentence_embedding", "token_embeddings"] | None
        :param precision: Тип точности (влияет на формат возвращаемых данных).
        :type precision: Literal["float32", "int8", "uint8", "binary", "ubinary"]
        :param convert_to_numpy: Преобразовывать ли результат в numpy.ndarray.
        :type convert_to_numpy: bool
        :param convert_to_tensor: Возвращать ли результаты в виде тензоров (torch).
        :type convert_to_tensor: bool
        :param device: Устройство(а) для вычислений (переопределяет устройство модели).
        :type device: str | list[str | torch.device] | None
        :param normalize_embeddings: Нормализовать ли эмбеддинги.
        :type normalize_embeddings: bool
        :param truncate_dim: Усечь размерность эмбеддинга.
        :type truncate_dim: int | None
        :param pool: Параметры пула процессов/входа/выхода для encode.
        :type pool: dict[Literal["input", "output", "processes"], Any] | None
        :param chunk_size: Размер чанка при больших входах.
        :type chunk_size: int | None
        :param kwargs: Дополнительные аргументы, передающиеся в ``SentenceTransformer.encode``.
        :type kwargs: Any

        :return: В зависимости от входных данных:
                 - если ``sentences`` - str: ``list[float]`` (embedding для строки);
                 - иначе, если ``metadata`` не указан: результат ``self.model.encode`` (обычно ``numpy.ndarray`` или ``list[list[float]]``);
                 - иначе список :class:`Vector`.
        :rtype: list[float] | numpy.ndarray | list[Vector]

        :raises asyncio.TimeoutError: при невозможности получить слот семафора в заданный ``acquire_timeout``.
        :raises Exception: любые исключения, проброшенные из ``SentenceTransformer.encode``.
        """

        async with self._concurrency_guard():
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
