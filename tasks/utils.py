from importlib import import_module
from types import ModuleType
from typing import Any


def import_attribute(module: str, qualname: str) -> Any:
    """
    Собирает путь, разделенный точками, к модулю и полному имени элемента модуля,
    импортирует модуль и возвращает именованный элемент.
    """

    module_: ModuleType = import_module(module)
    obj: ModuleType | type = module_

    for attribute in qualname.split("."):
        obj = getattr(obj, attribute)
    return obj
