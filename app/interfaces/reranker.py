from typing import Protocol


class Reranker(Protocol):
    def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        ...
