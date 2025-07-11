from io import BytesIO
import uuid

from langdetect import detect
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from domain.schemas import (
    Vector,
    DocumentMeta,
)
from services.interfaces import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from stubs.raw_storage import FileRawStorage
from stubs.vector_store import JSONVectorStore
from stubs.metadata_repository import SQLiteMetadataRepository
from domain.handlers import (
    TextExtractor,
    ExtractorFactory,
    ExtractedInfo,
)
from config import storage_settings


_transformer = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


# TODO посмотреть как лучше всего у UploadFile узнать какой тип файла. Потому что возможно такое,
#  что у файла после точки (или точка отсутствует) нет расширения, хотя файл является PDF или DOCX
async def process_file(
    content: bytes,
    filename: str,
    *,
    document_id: str = str(uuid.uuid4()),
    raw_storage: RawStorage | None = None,
    vector_store: VectorStore | None = None,
    metadata_repository: MetadataRepository | None = None,
) -> None:
    file_extension: str = filename.split(".")[-1].lower()
    filename = f"{document_id}.{file_extension}"
    file = BytesIO(content)

    raw_storage = raw_storage or FileRawStorage(f"{storage_settings.raw_storage_path}{filename}")
    vector_store = vector_store or JSONVectorStore(f"{storage_settings.index_path}{filename}")
    metadata_repository = metadata_repository or SQLiteMetadataRepository(storage_settings.sqlite_url)

    raw_storage.save(content, filename)

    extractor: TextExtractor = ExtractorFactory().get_extractor(file_extension)
    document_info: ExtractedInfo = extractor.extract(file)

    if not document_info.text:
        return

    language: str = detect(document_info.text)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks: list[str] = text_splitter.split_text(document_info.text)

    # embeddings = _transformer.encode(chunks)
    # vectors = [
    #     Vector(
    #         document_id=document_id,
    #         embedding=embedding.tolist() if hasattr(embedding, "tolist") else embedding,
    #         metadata={"chunk": i},
    #     )
    #     for i, embedding in enumerate(embeddings)
    # ]
    # vector_store.upsert(vectors)

    metadata = DocumentMeta(
        document_id=document_id,
        document_type="",
        detected_language=language,
        document_page_count=document_info.document_page_count,
        author=document_info.author,
        creation_date=document_info.creation_date,
    )
    metadata_repository.save(metadata)
