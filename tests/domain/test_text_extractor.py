from typing import Any
from io import BytesIO

import pytest

from domain.extraction import (
    TextExtractor,
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
        extractor: TextExtractor,
        file_extension: str,
    ):
        file_bytes, *_ = tmp_document(doc_type=file_extension)
        extracted_info: ExtractedInfo = extractor.extract(BytesIO(file_bytes))
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
        extractor: TextExtractor,
    ):
        with pytest.raises(ExtractionError):
            extractor.extract(BytesIO(b"some bytes"))
