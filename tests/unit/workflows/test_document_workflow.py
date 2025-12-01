from typing import Any
from unittest.mock import (
    MagicMock,
    AsyncMock,
    create_autospec,
    call,
)
import json

import pytest
import langdetect

from tests.generators import (
    DocumentGenerator,
    ValueGenerator,
)
from tests.mock_utils import assert_called_once_with
from app.workflows.document import (
    extract_text_and_metadata,
    detect_language,
    split_pages_on_chunks,
    vectorize_chunks,
    classify_document_into_topics,
)
from app.domain.document.schemas import DocumentDTO
from app.types import Vector
from app.domain.text_splitter import Chunk
from app.domain.extraction import (
    extract as extract_from_document,
    Page,
    ExtractedInfo,
)
from app.domain.classifier.schemas import (
    ClassificationResult,
    MatchDetail,
    KeywordMatch,
    RegexMatch,
    TopicDTO,
)
from app.utils.datetime import reset_timezone


class TestDocumentWorkflow:
    @staticmethod
    def make_dummy_topic_repo(monkeypatch, **kwargs):
        calls = {
            "get_topic_by_code": [],
        }

        class DummyTopicRepository:
            def __init__(self, session): ...

            async def get_topic_by_code(self, code: str) -> TopicDTO:
                calls["get_topic_by_code"].append(code)
                if get_value := kwargs.get("get_topic_by_code"):
                    return get_value[code]

        monkeypatch.setattr(
            "app.workflows.document.TopicRepository",
            DummyTopicRepository,
        )

        return calls

    @staticmethod
    def make_dummy_document_topic_repo(monkeypatch, **kwargs):
        calls = {
            "create": [],
        }

        class DummyDocumentTopicRepository:
            def __init__(self, session): ...

            async def create(self, **kwargs):
                calls["create"].append(kwargs)

        monkeypatch.setattr(
            "app.workflows.document.DocumentTopicRepository",
            DummyDocumentTopicRepository,
        )

        return calls

    # @pytest.mark.asyncio
    # async def test_update_document_status(
    #     self,
    #     monkeypatch,
    #     document_id: str = ValueGenerator.uuid(),
    #     status: DocumentStatus = DocumentStatus.queued,
    # ):
    #     calls = self.make_dummy_document_repo(monkeypatch)
    #     await DocumentProcessor.update_document_status(document_id, status)
    #     assert calls["update"]
    #     assert calls["update"][0] == {
    #         "id": document_id,
    #         "status": status,
    #     }
    #
    # @pytest.mark.asyncio
    # async def test_get_pending_documents_ids(
    #     self,
    #     monkeypatch,
    # ):
    #     self.make_dummy_document_repo(monkeypatch)
    #     result = await DocumentProcessor.get_pending_documents_ids()
    #     assert result == self.get_document_ids()
    #
    # @pytest.mark.asyncio
    # async def test_get_document(
    #     self,
    #     monkeypatch,
    # ):
    #     document: DocumentDTO = TestDocumentProcessor.get_document()
    #     calls = self.make_dummy_document_repo(monkeypatch, get=document)
    #     result = await DocumentProcessor.get_document(document.id)
    #     assert result == document
    #     assert calls["get"]
    #     assert calls["get"][0] == document.id
    #
    # @pytest.mark.asyncio
    # async def test_update_document(
    #     self,
    #     monkeypatch,
    # ):
    #     document: DocumentDTO = TestDocumentProcessor.get_document()
    #     calls = self.make_dummy_document_repo(monkeypatch, get=document)
    #     await DocumentProcessor.update_document(
    #         document.id, **document.model_dump(exclude={"id"})
    #     )
    #     assert calls["update"]
    #     assert calls["update"][0] == {
    #         "id": document.id,
    #         **document.model_dump(exclude={"id"}),
    #     }

    @pytest.mark.asyncio
    async def test_extraction_success(
        self,
        monkeypatch,
        mock_document_repo: MagicMock,
        mock_raw_storage: MagicMock,
        mock_silver_storage: MagicMock,
        tmp_document: Any,
    ):
        document: DocumentDTO = DocumentGenerator.document_dto()
        mock_document_repo.get.return_value = document
        monkeypatch.setattr(
            "app.workflows.document.DocumentRepository",
            lambda session: mock_document_repo,
        )
        mock_document_event_repo = AsyncMock()
        monkeypatch.setattr(
            "app.workflows.document.DocumentEventRepository",
            lambda session: mock_document_event_repo,
        )

        file, _ = tmp_document()
        mock_raw_storage.get.return_value = file.content

        pages: list[Page] = ValueGenerator.page(10)
        extracted_info = ExtractedInfo(
            pages=pages,
            document_page_count=len(pages),
            author=ValueGenerator.text(),
            creation_date=ValueGenerator.datetime(),
        )
        mock_extract_func = create_autospec(
            extract_from_document,
            return_value=extracted_info,
            spec_set=True,
        )

        await extract_text_and_metadata(
            document_id=document.id,
            raw_storage=mock_raw_storage,
            silver_storage=mock_silver_storage,
            extractor=mock_extract_func,
        )

        mock_document_repo.get.assert_has_calls(
            [
                call(document.id),
                call(document.id),
            ],
        )

        assert_called_once_with(
            mock_raw_storage.get,
            path=document.raw_storage_path,
        )

        assert_called_once_with(
            mock_extract_func,
            file=file.content,
        )

        assert_called_once_with(
            mock_silver_storage.save,
            file_bytes=json.dumps([page.model_dump() for page in pages]).encode(),
            path=document.silver_storage_path,
        )

        assert_called_once_with(
            mock_document_repo.update,
            id=document.id,
            kwargs={
                "page_count": extracted_info.document_page_count,
                "author": extracted_info.author,
                "creation_date": reset_timezone(extracted_info.creation_date),
            },
        )

    @pytest.mark.asyncio
    async def test_detect_language_success(
        self,
        monkeypatch,
        mock_document_repo: MagicMock,
        mock_silver_storage: MagicMock,
    ):
        document: DocumentDTO = DocumentGenerator.document_dto()
        mock_document_repo.get.return_value = document
        monkeypatch.setattr(
            "app.workflows.document.DocumentRepository",
            lambda session: mock_document_repo,
        )
        mock_document_event_repo = AsyncMock()
        monkeypatch.setattr(
            "app.workflows.document.DocumentEventRepository",
            lambda session: mock_document_event_repo,
        )

        document_bytes: bytes = b'[{"num": 1, "text": "text"}]'
        mock_silver_storage.get.return_value = document_bytes

        mock_langdetect_func = create_autospec(
            langdetect.detect,
            return_value=document.detected_language,
            spec_set=True,
        )
        monkeypatch.setattr(
            "app.workflows.document.langdetect.detect",
            mock_langdetect_func,
        )

        await detect_language(
            document_id=document.id,
            silver_storage=mock_silver_storage,
        )

        mock_document_repo.get.assert_has_calls(
            [
                call(document.id),
                call(document.id),
            ],
        )

        assert_called_once_with(
            mock_silver_storage.get,
            path=document.silver_storage_path,
        )

        assert_called_once_with(
            mock_langdetect_func,
            text="text",
        )

        assert_called_once_with(
            mock_document_repo.update,
            id=document.id,
            kwargs={"detected_language": document.detected_language},
        )

    @pytest.mark.asyncio
    async def test_split_pages_success(
        self,
        monkeypatch,
        mock_document_repo: MagicMock,
        mock_silver_storage: MagicMock,
        mock_text_splitter: MagicMock,
    ):
        document: DocumentDTO = DocumentGenerator.document_dto()
        mock_document_repo.get.return_value = document
        monkeypatch.setattr(
            "app.workflows.document.DocumentRepository",
            lambda session: mock_document_repo,
        )
        mock_document_event_repo = AsyncMock()
        monkeypatch.setattr(
            "app.workflows.document.DocumentEventRepository",
            lambda session: mock_document_event_repo,
        )

        document_bytes: bytes = b'[{"num": 1, "text": "text"}]'
        mock_silver_storage.get.return_value = document_bytes

        chunks: list[Chunk] = ValueGenerator.chunk(10)
        mock_text_splitter.split_pages.return_value = chunks

        await split_pages_on_chunks(
            document_id=document.id,
            silver_storage=mock_silver_storage,
            text_splitter=mock_text_splitter,
        )

        mock_document_repo.get.assert_has_calls(
            [
                call(document.id),
                call(document.id),
            ],
        )

        assert_called_once_with(
            mock_silver_storage.get,
            path=document.silver_storage_path,
        )

        assert_called_once_with(
            mock_text_splitter.split_pages,
            pages=[Page(num=1, text="text")],
        )

    @pytest.mark.asyncio
    async def test_vectorize_chunks_success(
        self,
        monkeypatch,
        mock_document_repo: MagicMock,
        mock_vector_store: MagicMock,
        mock_embedding_model: MagicMock,
    ):
        document: DocumentDTO = DocumentGenerator.document_dto()
        mock_document_repo.get.return_value = document
        monkeypatch.setattr(
            "app.workflows.document.DocumentRepository",
            lambda session: mock_document_repo,
        )
        mock_document_event_repo = AsyncMock()
        monkeypatch.setattr(
            "app.workflows.document.DocumentEventRepository",
            lambda session: mock_document_event_repo,
        )

        chunks: list[Chunk] = ValueGenerator.chunk(10)
        vectors: list[Vector] = ValueGenerator.vector(
            chunks=chunks,
            document=document,
        )
        mock_embedding_model.encode.return_value = vectors

        await vectorize_chunks(
            document_id=document.id,
            chunks=chunks,
            vector_store=mock_vector_store,
            embedding_model=mock_embedding_model,
        )

        mock_document_repo.get.assert_has_calls(
            [
                call(document.id),
                call(document.id),
            ],
        )

        assert_called_once_with(
            mock_embedding_model.encode,
            sentences=[chunk.text for chunk in chunks],
            metadata=[vector.payload for vector in vectors],
        )

        assert_called_once_with(
            mock_vector_store.upsert,
            vectors=vectors,
        )

    @pytest.mark.asyncio
    async def test_classify_document_success(
        self,
        monkeypatch,
        mock_document_repo: MagicMock,
        mock_classifier: MagicMock,
        mock_silver_storage: MagicMock,
        document_id: str = ValueGenerator.uuid(),
    ):
        document: DocumentDTO = DocumentGenerator.document_dto()
        mock_document_repo.get.return_value = document
        monkeypatch.setattr(
            "app.workflows.document.DocumentRepository",
            lambda session: mock_document_repo,
        )
        mock_document_event_repo = AsyncMock()
        monkeypatch.setattr(
            "app.workflows.document.DocumentEventRepository",
            lambda session: mock_document_event_repo,
        )

        document_bytes: bytes = b'[{"num": 1, "text": "text"}]'
        mock_silver_storage.get.return_value = document_bytes

        classification_results: list[ClassificationResult] = [
            ClassificationResult(
                topic=ValueGenerator.uuid(),
                score=ValueGenerator.integer(),
                matches=MatchDetail(
                    keyword_matches=[
                        KeywordMatch(
                            keyword=ValueGenerator.word(),
                            count=ValueGenerator.integer(),
                        )
                        for _ in range(ValueGenerator.integer(2))
                    ],
                    regex_matches=[
                        RegexMatch(
                            regex=ValueGenerator.word(),
                            count=ValueGenerator.integer(),
                        )
                        for _ in range(ValueGenerator.integer(2))
                    ],
                ),
            )
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_classifier.classify_text.return_value = classification_results

        topics_mapping: dict[str, TopicDTO] = {
            result.topic: TopicDTO(
                code=result.topic,
                title=ValueGenerator.text(),
            )
            for result in classification_results
        }
        calls_topic_repo = self.make_dummy_topic_repo(
            monkeypatch,
            get_topic_by_code=topics_mapping,
        )

        calls_doc_topic_repo = self.make_dummy_document_topic_repo(monkeypatch)

        await classify_document_into_topics(
            document_id=document_id,
            classifier=mock_classifier,
            silver_storage=mock_silver_storage,
        )

        assert_called_once_with(
            mock_classifier.classify_text,
            text="text",
        )

        assert calls_topic_repo["get_topic_by_code"]
        for i, topic_code in enumerate(topics_mapping.keys()):
            assert calls_topic_repo["get_topic_by_code"][i] == topic_code

        assert calls_doc_topic_repo["create"]
        for i, result in enumerate(classification_results):
            assert calls_doc_topic_repo["create"][i] == {
                "document_id": document_id,
                "topic_id": topics_mapping.get(result.topic).id,
                "score": result.score,
                "source": "rules",
            }
