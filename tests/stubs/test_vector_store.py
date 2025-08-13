import os
import json

import pytest

from tests.conftest import ValueGenerator
from stubs import JSONVectorStore
from domain.schemas import (
    VectorMetadata,
    Vector,
)


class TestJSONVectorStore:
    @pytest.mark.parametrize(
        "directory",
        [
            f"{ValueGenerator.path()}{ValueGenerator.uuid()}",
            f"{ValueGenerator.path(1)}{ValueGenerator.uuid()}",
            ValueGenerator.uuid(),
        ],
    )
    def test_init_raises_for_non_directory_path(self, tmp_path, directory):
        directory: str = f"{tmp_path}/{directory}"
        with pytest.raises(ValueError):
            JSONVectorStore(directory=directory)

    @pytest.mark.parametrize(
        "directory, vectors",
        [
            (f"{ValueGenerator.path()}", [ValueGenerator.vector()]),
            (f"{ValueGenerator.path(1)}", [ValueGenerator.vector()]),
            (f"{ValueGenerator.path()}", ValueGenerator.vectors()),
        ],
    )
    def test_upsert_creates_json_file_with_correct_content(
        self,
        tmp_path,
        directory: str,
        vectors: list[Vector],
    ):
        directory = f"{tmp_path}/{directory}"
        document_id: str = vectors[0].metadata.document_id
        workspace_id: str = vectors[0].metadata.workspace_id

        vector_store = JSONVectorStore(directory=directory)
        vector_store.upsert(vectors)

        with open(
            os.path.join(directory, f"{workspace_id}/{document_id}.json")
        ) as file:
            content: list = json.load(file)
            for v1, v2 in zip(content, vectors):
                assert v1["id"] == v2.id
                assert v1["values"] == v2.values
                assert v1["metadata"] == v2.metadata.model_dump()

    def test_search_returns_correct_vectors(self, tmp_path):
        directory: str = f"{tmp_path}/{ValueGenerator.path()}"
        workspace_id: str = ValueGenerator.uuid()

        vector_store = JSONVectorStore(directory=directory)

        document_id: str = ValueGenerator.uuid()
        vector_metadata = VectorMetadata(
            document_id=document_id,
            workspace_id=workspace_id,
            document_name=ValueGenerator.text(),
            document_page=ValueGenerator.integer(),
            text=ValueGenerator.text(),
        )
        vectors1: list[Vector] = [
            Vector(values=[0.1, 0.2, 0.3], metadata=vector_metadata.model_copy()),
            Vector(values=[0.4, 0.5, 0.6], metadata=vector_metadata.model_copy()),
        ]
        vector_store.upsert(vectors1)

        document_id = ValueGenerator.uuid()
        vector_metadata.document_id = document_id
        vectors2: list[Vector] = [
            Vector(values=[0.7, 0.8, 0.9], metadata=vector_metadata.model_copy()),
            Vector(values=[0.9, 0.8, 0.7], metadata=vector_metadata.model_copy()),
            Vector(values=[0.0, 0.0, 0.0], metadata=vector_metadata.model_copy()),
        ]
        vector_store.upsert(vectors2)

        top_k: int = 2
        expected_vectors: list[Vector] = list(vectors1)
        retrieved_vectors: list[Vector] = vector_store.search(
            [0.1, 0.3, 0.6], top_k, workspace_id
        )
        assert retrieved_vectors == expected_vectors

    def test_search_empty_directory(self, tmp_path):
        directory: str = f"{tmp_path}/{ValueGenerator.path()}"

        vector_store = JSONVectorStore(directory=directory)

        assert vector_store.search([0.1, 0.2, 0.3], 999, ValueGenerator.uuid()) == []

    def test_delete_vector_from_correct_location(self, tmp_path):
        vectors: list[Vector] = ValueGenerator.vectors()
        document_id: str = vectors[0].metadata.document_id
        workspace_id: str = vectors[0].metadata.workspace_id
        directory: str = f"{tmp_path}/{ValueGenerator.path()}"
        path: str = f"{workspace_id}/{document_id}.json"
        full_path: str = os.path.join(directory, path)

        vector_store = JSONVectorStore(directory=directory)
        vector_store.upsert(vectors)

        with open(full_path, "r") as file:
            assert json.load(file)

        vector_store.delete(workspace_id=workspace_id, document_id=document_id)

        with pytest.raises(FileNotFoundError):
            open(full_path, "r")

    def test_delete_vectors_directory_from_correct_location(self, tmp_path):
        vectors: list[Vector] = ValueGenerator.vectors()
        document_id: str = vectors[0].metadata.document_id
        workspace_id: str = vectors[0].metadata.workspace_id
        directory: str = f"{tmp_path}/{ValueGenerator.path()}"
        path: str = f"{workspace_id}/{document_id}.json"
        full_path: str = os.path.join(directory, path)

        vector_store = JSONVectorStore(directory=directory)
        vector_store.upsert(vectors)

        with open(full_path, "r") as file:
            assert json.load(file)

        vector_store.delete(workspace_id=workspace_id)

        with pytest.raises(FileNotFoundError):
            open(full_path, "r")
