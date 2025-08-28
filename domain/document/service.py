import langdetect

from domain.embedding import (
    EmbeddingModel,
    Vector,
    VectorMetadata,
)
from domain.text_splitter import (
    TextSplitter,
    Chunk,
)
from domain.extraction import (
    extract as extract_from_document,
    Page,
    ExtractedInfo,
)
from domain.document.schemas import (
    File,
    DocumentStatus,
    DocumentDTO,
)
from domain.document.repositories import DocumentRepository
from domain.database.uow import UnitOfWork
from services import (
    RawStorage,
    VectorStore,
)
from config import logger


class DocumentService:
    """
    Сервис, управляющий полным циклом обработки загруженных документов.
    """

    def __init__(
        self,
        raw_storage: RawStorage,
        vector_store: VectorStore,
        embedding_model: EmbeddingModel,
        text_splitter: TextSplitter,
    ):
        """
        :param raw_storage: Экземпляр сервиса для сохранения сырых файлов.
        :type raw_storage: RawStorage
        :param vector_store: Экземпляр сервиса векторного хранилища.
        :type vector_store: VectorStore
        :param embedding_model: Модель для работы с эмбеддингами.
        :type embedding_model: SentenceTransformer
        :param text_splitter: Инструмент для разбиения текста на чанки.
        :type text_splitter: TextSplitter
        """

        self.raw_storage = raw_storage
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.text_splitter = text_splitter

    async def process(
        self,
        file: File,
        document_id: str,
        workspace_id: str,
        uow: UnitOfWork,
    ) -> None:
        """
        Выполняет полный цикл обработки загруженного документа.

        Метаданные документа сохраняются, если они присутствуют в результате извлечения.
        В случае любой ошибки на этапе обработки в поле метаданных будет записано
        ``status=DocumentStatus.failed`` и текст ошибки в ``error_message``.
        Метод гарантирует попытку сохранить метаданные в любом случае (успех/ошибка обработки).

        Пайплайн:
            1. Сохранение исходного файла в ``RawStorage``.
            2. Извлечение текста и метаданных с помощью ``TextExtractor``.
            3. Определение языка документа.
            4. Разбиение текста на чанки с помощью ``TextSplitter``.
            5. Генерация эмбеддингов для каждого чанка.
            6. Загрузка векторов в ``VectorStore``.
            7. Сохранение метаданных в репозиторий.

        :param file: Объект файла, содержащий байты и метаданные (:class:`File`).
        :type file: File
        :param document_id: Идентификатор документа (используется для ключей/путей хранения).
        :type document_id: str
        :param workspace_id: Идентификатор рабочего пространства (workspace).
        :type workspace_id: str
        :param uow: UnitOfWork - менеджер транзакции и фабрика репозиториев.
        :type uow: UnitOfWork
        """

        context_logger = logger.bind(document_id=document_id, workspace_id=workspace_id)

        document = DocumentDTO(
            id=document_id,
            workspace_id=workspace_id,
            name=file.name,
            media_type=file.type,
            raw_storage_path=f"{workspace_id}/{document_id}{file.extension}",
            size_bytes=file.size,
            status=DocumentStatus.success,
        )

        try:
            context_logger.info(
                "Сохранение необработанного документа",
                raw_storage_path=document.raw_storage_path,
            )
            self.raw_storage.save(file.content, document.raw_storage_path)

            context_logger.info(
                "Извлечение текста и метаданных из документа",
                media_type=document.media_type,
                file_size_bytes=file.size,
            )
            document_info: ExtractedInfo = extract_from_document(file)
            document.page_count = document_info.document_page_count
            document.author = document_info.author
            document.creation_date = document_info.creation_date

            context_logger.info("Определение основного языка документа")
            sample: str = self._get_text_sample(document_info.pages, min_chars=1000)
            document.detected_language = langdetect.detect(sample)

            context_logger.info("Разбиение текста на чанки")
            chunks: list[Chunk] = self.text_splitter.split_pages(document_info.pages)

            context_logger.info("Создание эмбеддингов для каждого чанка, векторизация")
            vectors: list[Vector] = await self.embedding_model.encode(
                sentences=[chunk.text for chunk in chunks],
                metadata=[
                    VectorMetadata(
                        document_id=document_id,
                        workspace_id=workspace_id,
                        document_name=file.name,
                        page_start=chunk.page_spans[0].page_num,
                        page_end=chunk.page_spans[-1].page_num,
                        text=chunk.text,
                    )
                    for chunk in chunks
                ]
            )

            context_logger.info("Сохранение векторов")
            self.vector_store.upsert(vectors)
        except Exception as e:
            error_message: str = str(e)
            context_logger.error(
                "Не удалось обработать документ",
                error_message=error_message,
            )
            document.status = DocumentStatus.failed
            document.error_message = error_message

        context_logger.info("Сохранение метаданных документа")
        document_repo = uow.get_repository(DocumentRepository)
        await document_repo.create(**document.model_dump())

    def _get_text_sample(self, pages: list[Page], min_chars: int = 1000) -> str:
        """
        Пытается получить кусочек текста из списка страниц ``pages`` заданного размера ``min_chars``.

        Полезно для случаев, когда первая страница документа не содержит текста.

        :param pages: Список страниц документа.
        :type pages: list[Page]
        :param min_chars: Минимальное количество символов, которое нужно попытаться извлечь. Если документ
            содержит меньше указанного количества символов, будут извлечены все символы.
        :type min_chars: int
        :return: Кусочек текста.
        :rtype str:
        """

        text: str = ""
        for page in pages:
            if page.text:
                text += f" {page.text}" if text else page.text
                if len(text) >= min_chars:
                    break
        return text
