from typing import Any

from tests.generators import ValueGenerator
from app.utils.file import (
    get_mime_type,
    get_file_extension,
)


class TestMimeType:
    def test_mime_type_for_pdf_determined_correctly(
        self,
        tmp_document: Any,
    ):
        file, _ = tmp_document(doc_type=".pdf")
        assert get_mime_type(file.content) == "application/pdf"

    def test_mime_type_for_docx_determined_correctly(
        self,
        tmp_document: Any,
    ):
        file, _ = tmp_document(doc_type=".docx")
        assert get_mime_type(file.content) == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class TestFileExtension:
    def test_extension_for_pdf_determined_correctly(
        self,
        tmp_document: Any,
    ):
        file, _ = tmp_document(doc_type=".pdf")
        assert get_file_extension(file.content) == ".pdf"

    def test_extension_for_docx_determined_correctly(
        self,
        tmp_document: Any,
    ):
        file, _ = tmp_document(doc_type=".docx")
        assert get_file_extension(file.content) == ".docx"

    def test_empty_bytes(self):
        file_bytes: bytes = b""
        assert get_file_extension(file_bytes) == ""
