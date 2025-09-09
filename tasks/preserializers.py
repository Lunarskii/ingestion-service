from typing import (
    Any,
    Protocol,
    Literal,
    TypedDict,
)

from kombu.utils.json import register_type
from pydantic import BaseModel

from tasks.utils import import_attribute


class Preserializer(Protocol):
    """
    Предварительный сериализатор можно использовать для `pack` (упаковки) несериализуемого объекта в
    сериализуемый, а затем для `unpack` (распаковки) его снова.
    """

    @classmethod
    def compatible_with(cls, type_: type) -> Literal[True]:
        """
        Если данный тип совместим с этой стратегией, возвращается значение `True`.
        Если нет, возбуждается исключение, объясняющее, почему это не так.
        """
        ...

    @classmethod
    def pack(cls, obj: Any) -> Any:
        """
        Запаковывает полученный объект в JSON-сериализуемый объект.
        """
        ...

    @classmethod
    def unpack(cls, data: Any) -> object:
        """
        Распаковывает сериализуемый объект обратно в экземпляр оригинального типа.
        """
        ...


class PackedModel(TypedDict):
    module: str
    qualname: str
    dump: dict[str, Any]


class PydanticPreserializer(Preserializer):
    @classmethod
    def compatible_with(cls, type_: type) -> Literal[True]:
        if not issubclass(type_, BaseModel):
            raise TypeError(
                f"{cls.__class__.__name__} "
                f"требует тип данных, наследованный от BaseModel"
            )
        return True

    @classmethod
    def pack(cls, obj: BaseModel) -> PackedModel:
        return {
            "module": obj.__class__.__module__,
            "qualname": obj.__class__.__qualname__,
            "dump": obj.model_dump(),
        }

    @classmethod
    def unpack(cls, data: PackedModel) -> BaseModel:
        schema_type = import_attribute(data["module"], data["qualname"])
        if not issubclass(schema_type, BaseModel):
            raise TypeError(
                f"Нельзя распаковать {schema_type}: не Pydantic модель"
            )
        return schema_type(**data["dump"])


def register_preserializer(preserializer: Preserializer, type_: type[object]) -> type[object]:
    """
    Регистрирует предварительный сериализатор для декорированного типа
    в реестре типов Kombu JSON.
    """

    if "<locals>" in type_.__qualname__ or "__main__" in type_.__module__:
        raise TypeError(
            "Вы не можете зарегистрировать предварительные сериализаторы для объектов, "
            "которые не доступны напрямую во время импорта"
        )

    try:
        preserializer.compatible_with(type_)
    except Exception as e:
        raise TypeError(
            f"{type_} не совместим с {preserializer}: {e}"
        ) from e

    register_type(
        type_,
        f"{type_.__module__}.{type_.__qualname__}",
        encoder=preserializer.pack,
        decoder=preserializer.unpack,
    )
    return type_
