import os
import json
import uuid

from domain.schemas import Vector
from services import VectorStore


class JSONVectorStore(VectorStore):
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def upsert(self, vectors: list[Vector]) -> None:
        data = [vector.model_dump() for vector in vectors]
        full_path = os.path.join(self.path, str(uuid.uuid4()))
        with open(full_path, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
