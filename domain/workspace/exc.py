from exceptions.base import (
    ApplicationError,
    status,
)


class WorkspaceAlreadyExistsError(ApplicationError):
    message = "Пространство с таким названием уже существует"
    error_code = "workspace_already_exists"
    status_code = status.HTTP_409_CONFLICT
