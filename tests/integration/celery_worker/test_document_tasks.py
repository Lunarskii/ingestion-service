# import asyncio
# from unittest.mock import (
#     MagicMock,
#     create_autospec,
# )
#
# import pytest
#
# from tests.mock_utils import assert_called_once_with
# import services.celery_worker.tasks.document_processing as tasks_module
# from services.celery_worker.tasks.document_processing import AsyncTask
# import app.workflows.document as document_workflow_module
#
#
# class TestDocumentTasks:
#     @pytest.fixture(autouse=True)
#     def patch_async_run(self, monkeypatch):
#         async_run = staticmethod(lambda coro: asyncio.run(coro))
#         monkeypatch.setattr(AsyncTask, "async_run", async_run)
#         yield
#
#     @staticmethod
#     def make_dummy_document_service(
#         monkeypatch,
#         *,
#         pending_ids=None,
#     ):
#         calls = {
#             "get_pending_documents_ids": [],
#             "update_document_status": [],
#             "extract": [],
#             "detect_language": [],
#             "split_pages_on_chunks": [],
#             "vectorize_chunks": [],
#             "classify": [],
#         }
#
#         class DummyService:
#             @staticmethod
#             async def get_pending_documents_ids():
#                 calls["get_pending_documents_ids"].append(True)
#                 return pending_ids or []
#
#             @staticmethod
#             async def update_document_status(document_id, status):
#                 calls["update_document_status"].append((document_id, status))
#                 return None
#
#         monkeypatch.setattr(
#             "app.domain.document.service.DocumentProcessor",
#             DummyService,
#             raising=False,
#         )
#
#         return calls
#
#     def test_start_processing_documents_awaiting_processing(self, monkeypatch):
#         calls = self.make_dummy_document_service(
#             monkeypatch,
#             pending_ids=["doc-1", "doc-2"],
#         )
#
#         delayed = []
#
#         def fake_delay(document_id):
#             delayed.append(document_id)
#
#         monkeypatch.setattr(
#             tasks_module.process_document,
#             "delay",
#             fake_delay,
#             raising=False,
#         )
#
#         tasks_module.start_processing_documents_awaiting_processing.run()
#
#         assert calls["get_pending_documents_ids"], (
#             "DocumentService.get_pending_documents_ids не вызывался"
#         )
#         assert len(calls["update_document_status"]) == 2
#         assert delayed == ["doc-1", "doc-2"]
#
#     def test_document_pipeline(self, monkeypatch):
#         self.make_dummy_document_service(monkeypatch, pending_ids=["doc-42"])
#
#         called_canvas = []
#
#         def fake_chain(*args, **kwargs):
#             def _call():
#                 called_canvas.append(("chain", args))
#                 return None
#
#             return _call
#
#         monkeypatch.setattr(
#             tasks_module,
#             "chain",
#             fake_chain,
#             raising=False,
#         )
#
#         tasks_module.process_document.run("doc-42")
#
#         assert called_canvas, "chain не был вызван из process_document"
#
#     def test_split_pages_on_chunks_returns_chunks(self, monkeypatch):
#         mock_func = create_autospec(
#             document_workflow_module.split_pages_on_chunks,
#             return_value=["chunk1", "chunk2"],
#             spec_set=True,
#         )
#         monkeypatch.setattr(
#             document_workflow_module,
#             "split_pages_on_chunks",
#             lambda document_id, _logger: mock_func,
#         )
#
#         result = tasks_module.split_pages_on_chunks.run("doc-x")
#         assert result == ["chunk1", "chunk2"]
#         #
#         # assert_called_once_with(
#         #     mock_func,
#         #     document_id="doc-x",
#         # )
#
#     # def test_vectorize_chunks_calls_service(self, monkeypatch):
#     #     calls = self.make_dummy_document_service(monkeypatch)
#     #     chunks = ["c1", "c2"]
#     #
#     #     tasks_module.vectorize_chunks.run(chunks, "doc-y")
#     #     assert calls["vectorize_chunks"] == [("doc-y", chunks)]
#     #
#     # def test_extract_and_classify_helpers(self, monkeypatch):
#     #     calls = self.make_dummy_document_service(monkeypatch)
#     #
#     #     tasks_module.extract_text_and_metadata_from_document.run("doc-E")
#     #     tasks_module.detect_language.run("doc-E")
#     #     tasks_module.classify_document_into_topics.run("doc-E")
#     #
#     #     assert calls["extract"] == ["doc-E"]
#     #     assert calls["detect_language"] == ["doc-E"]
#     #     assert calls["classify"] == ["doc-E"]
