from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from fastapi import status

from exceptions.base import ApplicationError


class DatabaseError(ApplicationError):
    message = "Ошибка при работе с базой данных"
    error_code = "database_error"
    
    def __init__(
        self, 
        message: str | None = None,
        original_error: Exception | None = None,
        **kwargs,
    ):
        super().__init__(message=message, **kwargs)
        self.original_error = original_error


class EntityNotFoundError(DatabaseError):
    error_code = "entity_not_found"
    status_code = status.HTTP_404_NOT_FOUND
    
    def __init__(
        self, 
        entity_type: str, 
        entity_id: Any, 
        original_error: Exception | None = None,
        **kwargs,
    ):
        super().__init__(
            message=f"Запись в {entity_type} с ID {entity_id} не найдена",
            original_error=original_error,
            **kwargs,
        )
        self.entity_type = entity_type
        self.entity_id = entity_id


class DuplicateEntityError(DatabaseError):
    message = "Такая запись в базе данных уже существует"
    error_code = "duplicate_entity"
    status_code = status.HTTP_409_CONFLICT
    
    def __init__(
        self, 
        entity_type: str, 
        duplicate_field: str, 
        duplicate_value: Any, 
        original_error: Exception | None = None,
        **kwargs,
    ):
        message = f"Запись в {entity_type} с {duplicate_field}={duplicate_value} уже существует"
        super().__init__(message=message, original_error=original_error, **kwargs)
        self.entity_type = entity_type
        self.duplicate_field = duplicate_field
        self.duplicate_value = duplicate_value


class ValidationError(DatabaseError):
    message = "Ошибка валидации данных"
    error_code = "validation_error"
    status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(
        self, 
        field: str, 
        value: Any, 
        constraint: str, 
        original_error: Exception | None = None,
        **kwargs,
    ):
        message = f"Поле {field} со значением {value} не соответствует ограничению: {constraint}"
        super().__init__(message=message, original_error=original_error, **kwargs)
        self.field = field
        self.value = value
        self.constraint = constraint


class ConnectionError(DatabaseError):
    message = "Ошибка подключения к базе данных"
    error_code = "connection_error"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    def __init__(
        self,
        original_error: Exception | None = None,
        **kwargs,
    ):
        super().__init__(original_error=original_error, **kwargs)


class TransactionError(DatabaseError):
    message = "Ошибка транзакции"
    error_code = "transaction_error"
    
    def __init__(
        self,
        original_error: Exception | None = None,
        **kwargs,
    ):
        super().__init__(original_error=original_error, **kwargs)


def handle_sqlalchemy_error(
    error: SQLAlchemyError,
    entity_type: str = "Unknown",
) -> DatabaseError:
    """
    Преобразует SQLAlchemy исключения в наши доменные исключения, сохраняя детали оригинальной ошибки.
    
    Это позволяет:
        1. Сохранить детали SQLAlchemy ошибки для отладки.
        2. Предоставить понятные сообщения в API.
        3. Правильно обработать разные типы ошибок.
        4. Интегрироваться с существующей системой ApplicationError.
    """
    
    from sqlalchemy.exc import (
        IntegrityError,
        OperationalError,
        NoResultFound,
        MultipleResultsFound,
        DataError,
        ProgrammingError,
    )
    
    if isinstance(error, IntegrityError):
        error_str = str(error).lower()
        
        if "duplicate key" in error_str or "unique constraint" in error_str:
            return DuplicateEntityError(
                entity_type=entity_type,
                duplicate_field="Unknown",
                duplicate_value="Unknown",
                original_error=error
            )
        else:
            return ValidationError(
                field="Unknown",
                value="Unknown",
                constraint="Integrity constraint",
                original_error=error
            )
    
    elif isinstance(error, OperationalError):
        if "connection" in str(error).lower():
            return ConnectionError(original_error=error)
        else:
            return DatabaseError(
                message="Операционная ошибка базы данных",
                original_error=error
            )
    
    elif isinstance(error, NoResultFound):
        return EntityNotFoundError("Unknown", "Unknown", original_error=error)
    
    elif isinstance(error, MultipleResultsFound):
        return DatabaseError(
            message="Найдено несколько результатов вместо одного",
            original_error=error
        )
    
    elif isinstance(error, DataError):
        return ValidationError(
            field="Unknown",
            value="Unknown", 
            constraint="Data type constraint",
            original_error=error
        )
    
    elif isinstance(error, ProgrammingError):
        return DatabaseError(
            message="Ошибка программирования SQL",
            original_error=error
        )
    
    else:
        return DatabaseError(
            message="Неизвестная ошибка базы данных",
            original_error=error
        )
