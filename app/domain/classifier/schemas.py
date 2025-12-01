from enum import Enum
import re

from app.schemas import (
    BaseSchema,
    BaseDTO,
    IDMixin,
    CreatedAtMixin,
)


class Topic(BaseSchema):
    """
    Схема темы.

    :ivar code: Короткий код темы, используемый как уникальный идентификатор.
    :ivar title: Отображаемое название темы для внешнего клиента.
    :ivar description: Дополнительное описание, если недостаточно названия.
    :ivar is_active: Активность темы. Если True, то тема активна, и ее можно использовать в подборке,
                     иначе нет.
    """

    code: str
    title: str
    description: str | None = None
    is_active: bool = True


class Rule(BaseSchema):
    """
    Схема правила.

    :ivar topic: Идентификатор темы, как поле ``code`` в классе ``Topic``.
    :ivar keywords: Набор ключевых слов, присущих данной теме.
    :ivar regex: Набор регулярных выражений, присущих данной теме.
    :ivar negative_keywords: Набор ключевых слов, при которых тема будет сразу отбрасываться для документа.
    :ivar weight: Вес правила. При итоговом подсчете является общим множителем.
    :ivar body_weight: Вес для совпадения в тексте.
    :ivar min_score: Минимальный счет, который должна преодолеть тема, чтобы попасть в предложенные темы.
    """

    topic: str
    keywords: list[str] = []
    regex: list[re.Pattern] = []
    negative_keywords: list[str] = []
    weight: float = 1.0
    body_weight: float = 1.0
    min_score: float = 1.0


class KeywordMatch(BaseSchema):
    """
    Совпадение по ключевому слову.

    :ivar keyword: Ключевое слово.
    :ivar count: Количество совпадений по этому ключевому слову.
    """

    keyword: str
    count: int


class RegexMatch(BaseSchema):
    """
    Совпадение по регулярному выражению.

    :ivar regex: Регулярное выражение.
    :ivar count: Количество совпадений по этому регулярному выражению.
    """

    regex: str
    count: int


class MatchDetail(BaseSchema):
    """
    Итоговые результаты всех совпадений.

    :ivar keyword_matches: Совпадения по ключевым словам.
    :ivar regex_matches: Совпадения по регулярным выражениям.
    """

    keyword_matches: list[KeywordMatch] = []
    regex_matches: list[RegexMatch] = []


class ClassificationResult(BaseSchema):
    """
    Результат классификации по теме.

    :ivar topic: Идентификатор темы, как поле ``code`` в классе ``Topic``.
    :ivar score: Набранный счет по теме.
    :ivar matches: Результаты всех совпадений по теме.
    """

    topic: str
    score: float
    matches: MatchDetail


class TopicSource(str, Enum):
    rules = "rules"
    ml = "ml"
    manual = "manual"


class TopicDTO(BaseDTO, IDMixin):
    """
    DTO (Data Transfer Object) для представления темы.

    :ivar id: Целочисленный идентификатор.
    :ivar code: Короткий код темы, используемый как уникальный идентификатор.
    :ivar title: Отображаемое название темы для внешнего клиента.
    :ivar description: Дополнительное описание, если недостаточно названия.
    :ivar is_active: Активность темы. Если True, то тема активна, и ее можно использовать в подборке,
                     иначе нет.
    """

    code: str
    title: str
    description: str | None = None
    is_active: bool = True


class DocumentTopicDTO(BaseDTO, IDMixin, CreatedAtMixin):
    """
    DTO (Data Transfer Object) для представления темы документа.

    :ivar id: Целочисленный идентификатор.
    :ivar document_id: Идентификатор документа.
    :ivar topic_id: Идентификатор темы.
    :ivar score: Счет совпадения темы с документом. Чем больше счет, тем большее совпадение документа с темой.
    :ivar created_at: Время определения темы.
    """

    document_id: str
    topic_id: int
    score: int
    source: TopicSource
