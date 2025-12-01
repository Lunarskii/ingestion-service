from typing import Any
from io import BytesIO

import pytest

from app.domain.extraction import (
    DocumentExtractor,
    PdfExtractor,
    DocxExtractor,
    ExtractedInfo,
    ExtractionError,
)


class TestTextExtractor:
    @pytest.mark.parametrize(
        "extractor, file_extension",
        [
            (PdfExtractor(), ".pdf"),
            # (DocxExtractor(), ".docx"),
        ],
    )
    def test_extract_success(
        self,
        tmp_document: Any,
        extractor: DocumentExtractor,
        file_extension: str,
    ):
        file, *_ = tmp_document(doc_type=file_extension)
        extracted_info: ExtractedInfo = extractor.extract(BytesIO(file.content))
        assert extracted_info
        assert extracted_info.pages
        for i, page in enumerate(extracted_info.pages):
            assert i == page.num
        assert len(extracted_info.pages) == extracted_info.document_page_count

    @pytest.mark.parametrize(
        "extractor",
        [
            PdfExtractor(),
            DocxExtractor(),
        ],
    )
    def test_extract_invalid_file(
        self,
        extractor: DocumentExtractor,
    ):
        with pytest.raises(ExtractionError):
            extractor.extract(BytesIO(b"some bytes"))
