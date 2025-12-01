from app.exceptions.base import ApplicationError
from app import status


class DatabaseError(ApplicationError):
    message = "Ошибка при работе с базой данных"
    error_code = "database_error"


class EntityNotFoundError(DatabaseError):
    message = "Записи в базе данных не существует"
    error_code = "database_entity_not_found"
    status_code = status.HTTP_404_NOT_FOUND


class DuplicateEntityError(DatabaseError):
    message = "Запись в базе данных уже существует"
    error_code = "database_unique_constraint_error"
    status_code = status.HTTP_409_CONFLICT


class ValidationError(DatabaseError):
    message = "Ошибка валидации данных"
    error_code = "database_validation_error"
    status_code = status.HTTP_400_BAD_REQUEST


class ConnectionError(DatabaseError):
    message = "Ошибка подключения к базе данных"
    error_code = "database_connection_error"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class TransactionError(DatabaseError):
    message = "Ошибка транзакции"
    error_code = "database_transaction_error"
