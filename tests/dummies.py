class DummyEmbeddingModel:
    def __init__(self, vector: list[float]):
        self._vector = vector

    def encode(self, sentences, **kwargs):
        class _Vector:
            def __init__(self, values):
                self._values = values

            def tolist(self) -> list:
                return self._values

        if isinstance(sentences, str):
            return _Vector(self._vector)
        if isinstance(sentences, list):
            return [_Vector(self._vector)]


class DummyTextSplitter:
    def __init__(self, chunks: list[str]):
        self.chunks = chunks

    def split_text(self, text: str):
        return self.chunks
