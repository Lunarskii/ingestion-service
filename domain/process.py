from io import BytesIO
import uuid

from langdetect import detect
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from domain.schemas import (
    Vector,
    DocumentMeta,
)
from domain.handlers import (
    TextExtractor,
    ExtractorFactory,
    ExtractedInfo,
)
from domain.utils import (
    get_mime_type,
    get_file_extension,
)
from services.interfaces import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)


class DocumentProcessor:
    """
    Управляет всем процессом обработки документов.

    :ivar raw_storage: Сервис для сохранения сырых файлов.
    :type raw_storage: RawStorage
    :ivar vector_store: Сервис для индексации векторов.
    :type vector_store: VectorStore
    :ivar metadata_repository: Сервис для хранения метаданных.
    :type metadata_repository: MetadataRepository
    """

    def __init__(
        self,
        raw_storage: RawStorage,
        vector_store: VectorStore,
        metadata_repository: MetadataRepository,
    ):
        self.raw_storage = raw_storage
        self.vector_store = vector_store
        self.metadata_repository = metadata_repository
        self.sentence_transformer = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )  # TODO вынести в настройки
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50
        )  # TODO вынести в настройки

    def process(
        self,
        content: bytes,
        document_id: str = str(uuid.uuid4()),
        workspace_id: str | None = None,
    ) -> None:
        """
        Выполняет полный цикл обработки загруженного файла:
            1. Сохраняет исходный файл.
            2. Извлекает текст в зависимости от типа файла.
            3. Определяет язык.
            4. Разбивает текст на фрагменты.
            5. Создает эмбеддинги для каждого чанка.
            6. Загружает векторы в хранилище векторов.
            7. Сохраняет метаданные документа.

        :param content: Документ в байтах.
        :type content: bytes
        :param document_id: ID документа. По умолчанию генерируется новый UUID4.
        :type document_id: str
        :param workspace_id: ...
        :type workspace_id: str
        """

        file_extension: str = get_file_extension(content)
        raw_storage_path: str = f"{document_id}{file_extension}"
        if workspace_id:
            raw_storage_path = f"{workspace_id}/{raw_storage_path}"
        self.raw_storage.save(content, raw_storage_path)

        file = BytesIO(content)
        extractor: TextExtractor = ExtractorFactory().get_extractor(file_extension)
        document_info: ExtractedInfo = extractor.extract(file)

        if not document_info.text:
            return

        language: str = detect(document_info.text)
        chunks: list[str] = self.text_splitter.split_text(document_info.text)
        vectors: list[Vector] = self._vectorize_chunks(document_id, chunks)
        self.vector_store.upsert(vectors)

        metadata = DocumentMeta(
            document_id=document_id,
            document_type=file_extension.lstrip(".").upper(),
            detected_language=language,
            document_page_count=document_info.document_page_count,
            author=document_info.author,
            creation_date=document_info.creation_date,
            raw_storage_path=raw_storage_path,
            file_size_bytes=len(content),
        )
        self.metadata_repository.save(metadata)

    def _vectorize_chunks(self, document_id: str, chunks: list[str]) -> list[Vector]:
        embeddings = self.sentence_transformer.encode(chunks)
        return [
            Vector(
                document_id=document_id,
                embedding=embedding.tolist()
                if hasattr(embedding, "tolist")
                else embedding,  # TODO посмотреть почему
                metadata={"chunk": i},
            )
            for i, embedding in enumerate(embeddings)
        ]
