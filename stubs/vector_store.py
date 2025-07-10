from domain.schemas import Vector
from services import VectorStore
from config import default_settings


class JSONVectorStore(VectorStore):
    def upsert(self, vectors: list[Vector]) -> None:
        with open(default_settings.index_path, "w", newline="\n") as file:
            for vector in vectors:
                file.write(vector.model_dump_json())
