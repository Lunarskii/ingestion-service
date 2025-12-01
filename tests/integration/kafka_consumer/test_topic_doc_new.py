from typing import (
    Callable,
    AsyncContextManager,
)
from datetime import datetime
import asyncio
import json

import pytest
from aiokafka import AIOKafkaProducer
from sqlalchemy.ext.asyncio import AsyncSession

from tests.generators import ValueGenerator
from app.domain.workspace.service import WorkspaceService
from app.domain.workspace.schemas import Workspace
from app.domain.document.repositories import DocumentRepository
from app.domain.document.schemas import (
    DocumentDTO,
    DocumentStatus,
)
from app.domain.database.dependencies import async_scoped_session_ctx
from app.core import settings


class TestTopicDocNew:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_processes_10_messages(
        self,
        kafka,
        session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    ):
        await kafka.start()

        producer = AIOKafkaProducer(
            bootstrap_servers=kafka.bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode(),
        )
        await producer.start()

        ws_service = WorkspaceService()
        ws_name: str = ValueGenerator.uuid()
        workspace: Workspace = await ws_service.create_workspace(ws_name)

        try:
            messages: list[dict] = [
                {
                    "doc_id": ValueGenerator.uuid(),
                    "workspace_id": workspace.id,
                    "source_id": ValueGenerator.text(),
                    "run_id": ValueGenerator.uuid(),
                    "sha256": ValueGenerator.text(),
                    "raw_url": ValueGenerator.text(),
                    "title": ValueGenerator.text(),
                    "mime": "application/pdf",
                    "stored_path": ValueGenerator.text(),
                    "size_bytes": ValueGenerator.integer(5),
                    "fetched_at": datetime.isoformat(ValueGenerator.datetime()),
                    "stored_at": datetime.isoformat(ValueGenerator.datetime()),
                }
                for _ in range(10)
            ]
            for msg in messages:
                await producer.send_and_wait(settings.kafka.topic_doc_new, msg)
        finally:
            await producer.stop()

        await asyncio.sleep(5)
        await kafka.stop()

        async with session_ctx() as session:
            repo = DocumentRepository(session)
            documents: list[DocumentDTO] = await repo.get_n(workspace_id=workspace.id)
            assert len(documents) == len(messages)

            for msg in messages:
                document: DocumentDTO = await repo.get(msg.get("doc_id"))
                assert document.workspace_id == msg.get("workspace_id")
                assert document.source_id == msg.get("source_id")
                assert document.run_id == msg.get("run_id")
                assert document.sha256 == msg.get("sha256")
                assert document.raw_url == msg.get("raw_url")
                assert document.title == msg.get("title")
                assert document.media_type == msg.get("mime")
                assert document.raw_storage_path == msg.get("stored_path")
                assert document.size_bytes == msg.get("size_bytes")
                assert document.fetched_at == datetime.fromisoformat(msg.get("fetched_at"))
                assert document.stored_at == datetime.fromisoformat(msg.get("stored_at"))
                assert document.status == DocumentStatus.pending

        await ws_service.delete_workspace(workspace.id)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_duplicates_not_saved(
        self,
        kafka,
        session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    ):
        await kafka.start()

        producer = AIOKafkaProducer(
            bootstrap_servers=kafka.bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode(),
        )
        await producer.start()

        ws_service = WorkspaceService()
        ws_name: str = ValueGenerator.uuid()
        workspace: Workspace = await ws_service.create_workspace(ws_name)

        try:
            messages: list[dict] = [
                {
                    "doc_id": ValueGenerator.uuid(),
                    "workspace_id": workspace.id,
                    "source_id": ValueGenerator.text(),
                    "run_id": ValueGenerator.uuid(),
                    "sha256": ValueGenerator.text(),
                    "raw_url": ValueGenerator.text(),
                    "title": ValueGenerator.text(),
                    "mime": "application/pdf",
                    "stored_path": ValueGenerator.text(),
                    "size_bytes": ValueGenerator.integer(5),
                    "fetched_at": datetime.isoformat(ValueGenerator.datetime()),
                    "stored_at": datetime.isoformat(ValueGenerator.datetime()),
                }
                for _ in range(10)
            ]
            for msg in messages:
                await producer.send_and_wait(settings.kafka.topic_doc_new, msg)
                await producer.send_and_wait(settings.kafka.topic_doc_new, msg)
        finally:
            await producer.stop()

        await asyncio.sleep(5)
        await kafka.stop()

        async with session_ctx() as session:
            repo = DocumentRepository(session)
            documents: list[DocumentDTO] = await repo.get_n(workspace_id=workspace.id)
            assert len(documents) == len(messages)

            for msg in messages:
                document: DocumentDTO = await repo.get(msg.get("doc_id"))
                assert document.workspace_id == msg.get("workspace_id")
                assert document.source_id == msg.get("source_id")
                assert document.run_id == msg.get("run_id")
                assert document.sha256 == msg.get("sha256")
                assert document.raw_url == msg.get("raw_url")
                assert document.title == msg.get("title")
                assert document.media_type == msg.get("mime")
                assert document.raw_storage_path == msg.get("stored_path")
                assert document.size_bytes == msg.get("size_bytes")
                assert document.fetched_at == datetime.fromisoformat(msg.get("fetched_at"))
                assert document.stored_at == datetime.fromisoformat(msg.get("stored_at"))
                assert document.status == DocumentStatus.pending

        await ws_service.delete_workspace(workspace.id)
