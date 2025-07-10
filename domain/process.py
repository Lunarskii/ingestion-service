import uuid
from fastapi import UploadFile
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

from langdetect import detect
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from domain.handlers import (
    TextExtractor,
    ExtractorFactory,
    ExtractedInfo,
)


_default_raw_storage = FileRawStorage()
_default_vector_store = JSONVectorStore()
_default_metadata_repository = SQLiteMetadataRepository()
_transformer = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


# TODO посмотреть как лучше всего у UploadFile узнать какой тип файла. Потому что возможно такое,
#  что у файла после точки (или точка отсутствует) нет расширения, хотя файл является PDF или DOCX
async def process_file(
    file: UploadFile,
    *,
    raw_storage: RawStorage = _default_raw_storage,
    vector_store: VectorStore = _default_vector_store,
    metadata_repository: MetadataRepository = _default_metadata_repository,
):
    document_id = str(uuid.uuid4())
    content = await file.read()
    raw_storage.save(content, f"{document_id}/{file.filename}")

    filename: str = file.filename.lower()
    extractor: TextExtractor = ExtractorFactory().get_extractor(filename.split(".")[-1])
    document_info: ExtractedInfo = extractor.extract(file.file)

    # TODO текста может не быть, нужно исправить это
    language: str = detect(document_info.text)

    # splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    # chunks = splitter.split_text(text)

    # embeddings = _transformer.encode(chunks, convert_to_tensor=False)
    # vectors = [
    #     Vector(id=f"{doc_id}_{i}", embedding=emb.tolist() if hasattr(emb, "tolist") else emb, metadata={"chunk": i})
    #     for i, emb in enumerate(embeddings)
    # ]

    # vector_store.upsert(vectors)

    metadata = DocumentMeta(
        id=document_id,
        type="",
        detected_language=language,
        document_page_count=None,
        author="",
        creation_date=None,
    )
    metadata_repository.save(metadata)
