from exceptions.base import (
    ApplicationError,
    status,
)


class WorkspaceError(ApplicationError):
    message = "Ошибка при работе с пространствами"
    error_code = "workspace_error"


class WorkspaceAlreadyExistsError(WorkspaceError):
    message = "Пространство с таким названием уже существует"
    error_code = "workspace_already_exists"
    status_code = status.HTTP_409_CONFLICT


class WorkspaceCreationError(WorkspaceError):
    message = "Не удалось создать новое пространство"
    error_code = "workspace_creation_error"


class WorkspaceRetrievalError(WorkspaceError):
    message = "Не удалось получить пространство"
    error_code = "workspace_retrieval_error"


class WorkspaceDeletionError(WorkspaceError):
    message = "Не удалось удалить пространство"
    error_code = "workspace_deletion_error"
