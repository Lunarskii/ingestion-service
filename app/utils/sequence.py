from typing import Iterable
from itertools import islice


def chunked(iterable: Iterable, size: int):
    """
    Разбивает итерируемый объект на подряд идущие чанки (списки) фиксированного размера.

    :param iterable: Любой итерируемый объект (например, list, tuple, generator).
    :param size: Положительное целое число - максимальный размер каждого чанка. Должно быть > 0.

    :raises ValueError: Если size <= 0.
    """

    if size <= 0:
        raise ValueError("Размер чанка должен быть > 0")

    iterator = iter(iterable)
    while True:
        chunk = list(islice(iterator, size))
        if not chunk:
            break
        yield chunk
