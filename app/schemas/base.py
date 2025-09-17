from pydantic import (
    BaseModel,
    ConfigDict,
)


class BaseSchema(BaseModel):
    """
    Базовая схема Pydantic.

    Используется как точка расширения для создания общих схем проекта.
    """

    ...


class BaseDTO(BaseModel):
    """
    Базовый класс для всех DTO (Data Transfer Objects).
    Содержит общие настройки конфигурации.

    Конфигурация (``model_config``):
        - ``from_attributes=True`` - позволяет инициализировать DTO напрямую из ORM-моделей через атрибуты объектов.
        - ``populate_by_name=True`` - разрешает инициализацию модели с использованием алиасов полей.
        - ``extra="ignore"`` - игнорирует лишние поля, отсутствующие в модели.
        - ``frozen=False`` - объекты не являются иммутабельными, их можно изменять.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="ignore",
        frozen=False,
    )
