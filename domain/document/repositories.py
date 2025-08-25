from domain.database.repositories import AlchemyRepository
from domain.document.models import DocumentDAO
from domain.document.schemas import DocumentDTO


class DocumentRepository(AlchemyRepository[DocumentDAO, DocumentDTO]):
    """
    Репозиторий для работы с документами.
    """
    ...
