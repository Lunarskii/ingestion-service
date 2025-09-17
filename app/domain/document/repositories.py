from app.domain.database.repositories import AlchemyRepository
from app.domain.document.models import DocumentDAO
from app.domain.document.schemas import DocumentDTO


class DocumentRepository(AlchemyRepository[DocumentDAO, DocumentDTO]):
    """
    Репозиторий для работы с документами.
    """

    ...
