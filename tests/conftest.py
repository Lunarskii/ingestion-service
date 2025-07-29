from unittest.mock import MagicMock
from typing import Any
import random
import uuid
import string
import io

import pytest
import docx
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4

from domain.fhandler.service import DocumentProcessor
from domain.chat.service import ChatService
from services import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from domain.schemas import Vector


class ValueGenerator:
    @classmethod
    def generate_float_list(
        cls,
        float_range: tuple[int, int],
        n: int | None = None,
        exclude: set[float] | None = None,
    ) -> list[float]:
        if exclude is None:
            exclude = {}
        n = n or 10
        floats: list[float] = []

        def random_float():
            return (
                random.randrange(float_range[0], float_range[1] + 1) * random.random()
            )

        for _ in range(n):
            while (value := random_float()) in exclude:
                pass
            floats.append(value)

        return floats

    @classmethod
    def word(cls, n: int = 10):
        return "".join(random.choices(string.ascii_letters, k=n))

    @classmethod
    def text(cls, n: int = 10):
        return "".join(
            random.choices(
                string.ascii_letters + string.digits + string.punctuation + " ", k=n
            )
        )

    @classmethod
    def integer(cls, n: int = 10) -> int:
        return int("".join(random.choices(string.digits, k=n)))

    @classmethod
    def uuid(cls, length: int | None = None) -> str:
        if length:
            return str(uuid.uuid4())[:length]
        return str(uuid.uuid4())

    @classmethod
    def path(cls, sub_directories: int = 0):
        return f"{'/'.join([cls.word() for _ in range(sub_directories + 1)])}/"

    @classmethod
    def vector(
        cls,
        n_values: int = 384,
        document_id: bool = True,
        workspace_id: bool = True,
        chunk_index: bool = True,
    ) -> Vector:
        metadata: dict[str, Any] = {}
        if document_id:
            metadata["document_id"] = cls.uuid()
        if workspace_id:
            metadata["workspace_id"] = cls.uuid()
        if chunk_index:
            metadata["chunk_index"] = cls.integer()
        return Vector(
            values=cls.generate_float_list((-1, 1), n_values, {0}),
            metadata=metadata,
        )

    @classmethod
    def vectors(cls, n_vectors: int = 10, n_values: int = 384):
        return [cls.vector(n_values) for _ in range(n_vectors)]

    @classmethod
    def pdf(
        cls,
        path: str,
        target_bytes: int = 1_000_000,
        min_pages: int = 1,
        max_pages: int = 1000,
        min_page_text_num: int = 500,
        max_page_text_num: int = 5000,
        min_line_len: int = 20,
        max_line_len: int = 100,
    ) -> None:
        buffer = io.BytesIO()
        document = Canvas(buffer, pagesize=A4)
        num_pages = random.randint(min_pages, max_pages)

        for _ in range(num_pages):
            text: str = cls.text(random.randint(min_page_text_num, max_page_text_num))
            text_obj = document.beginText(40, 800)

            start: int = 0
            end: int = len(text)
            while start < end:
                line_len = random.randint(min_line_len, max_line_len)
                text_obj.textLine(text[start : start + line_len])
                start += line_len

            document.drawText(text_obj)
            document.showPage()

        document.save()
        data = buffer.getvalue()

        if len(data) < target_bytes:
            data += b"\n" * (target_bytes - len(data))

        with open(path, "wb") as f:
            f.write(data)

    @classmethod
    def docx(
        cls,
        path: str,
        target_bytes: int,
    ) -> None:
        buffer = io.BytesIO()
        document = docx.Document()
        num_pages: int = int(target_bytes / 1_000_000)
        page_text_num: int = int(target_bytes / num_pages)

        for page_num in range(num_pages):
            text: str = cls.text(page_text_num)
            document.add_paragraph(text)
            if page_num < num_pages - 1:
                document.add_page_break()

        document.save(buffer)
        data = buffer.getvalue()

        for _ in range(int((target_bytes - len(data)) / page_text_num)):
            text: str = cls.text(page_text_num)
            document.add_paragraph(text)

        document.save(path)


@pytest.fixture
def tmp_document(tmp_path):
    _map: dict[int, tuple] = {
        0: (ValueGenerator.pdf, ".pdf"),
        1: (ValueGenerator.docx, ".docx"),
    }

    def _make(target_bytes: int = 1_000_000) -> tuple:
        path = tmp_path / f"document_{target_bytes}.document"
        func, file_extension = _map[random.randint(0, len(_map) - 1)]
        func(path, target_bytes)
        return path, file_extension

    return _make


def assert_any_exception(exctype, excinfo):
    assert excinfo.type is exctype
    assert excinfo.value.message == exctype.message
    assert excinfo.value.error_code == exctype.error_code
    assert excinfo.value.status_code == exctype.status_code


@pytest.fixture
def random_document_id() -> str:
    return ValueGenerator.uuid()


@pytest.fixture
def random_workspace_id() -> str:
    return ValueGenerator.uuid()


@pytest.fixture
def mock_raw_storage(mocker):
    return mocker.MagicMock(spec=RawStorage)


@pytest.fixture
def mock_vector_store(mocker):
    return mocker.MagicMock(spec=VectorStore)


@pytest.fixture
def mock_metadata_repository(mocker):
    return mocker.MagicMock(spec=MetadataRepository)


@pytest.fixture
def mock_embedding_model(mocker):
    return mocker.MagicMock(spec=SentenceTransformer)


@pytest.fixture
def mock_text_splitter(mocker):
    return mocker.MagicMock(spec=RecursiveCharacterTextSplitter)


@pytest.fixture
def document_processor(
    mock_raw_storage: MagicMock,
    mock_vector_store: MagicMock,
    mock_metadata_repository: MagicMock,
    mock_embedding_model: MagicMock,
    mock_text_splitter: MagicMock,
) -> DocumentProcessor:
    return DocumentProcessor(
        raw_storage=mock_raw_storage,  # noqa
        vector_store=mock_vector_store,  # noqa
        metadata_repository=mock_metadata_repository,  # noqa
        embedding_model=mock_embedding_model,  # noqa
        text_splitter=mock_text_splitter,  # noqa
    )


@pytest.fixture
def chat_service(
    mock_vector_store: MagicMock,
    mock_embedding_model: MagicMock,
) -> ChatService:
    return ChatService(
        vector_store=mock_vector_store,  # noqa
        embedding_model=mock_embedding_model,  # noqa
    )
