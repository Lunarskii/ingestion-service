from typing import (
    Callable,
    Iterable,
)
from abc import (
    ABC,
    abstractmethod,
)
from app.domain.document.exceptions import (
    ValidationError,
    UnsupportedMediaTypeError,
    FileTooLargeError,
)
from app.utils.file import get_file_extension


DocumentType = str | bytes


class Validator(ABC):
    """
    Абстрактный интерфейс валидатора.

    Валидатор реализует единый контракт: быть вызываемым объектом, принимающим
    один аргумент `document` (тип `DocumentType`), и, либо успешно завершать
    выполнение (ничего не возвращая), либо выбрасывать исключение-наследник
    `ValidationError` в случае ошибки валидации.
    """

    @abstractmethod
    def __call__(self, document: DocumentType) -> None:
        """
        Выполняет проверку документа.

        :param document: Проверяемый документ.

        :raises ValidationError: Если документ не проходит валидацию.
        """

        ...


class FunctionalValidator(Validator):
    """
    Валидатор-обёртка для произвольной функции.
    """
    
    def __init__(
        self,
        func: Callable[[DocumentType], bool | tuple[bool, str]],
    ):
        """
        :param func: Функция, принимающая `DocumentType` и возвращающая либо
               `bool`, либо кортеж `(bool, str)` где `bool` - результат
               проверки, а `str` - сообщение об ошибке.
               Если `func(document)` вернёт `(False, "msg")`, будет брошено
               `ValidationError("msg")`. Если вернёт `False` - будет брошено
               `ValidationError` с сообщением по умолчанию.
        """
        
        super().__init__()
        self.func = func

    def __call__(self, document: DocumentType) -> None:
        """
        Вызывает функцию и обрабатывает результат.

        :param document: Проверяемый документ.

        :raises ValidationError: Если `func` вернула ложный результат.
        """

        result = self.func(document)
        if isinstance(result, tuple):
            ok, msg = result
        else:
            ok, msg = bool(result), None

        if not ok:
            raise ValidationError(msg or ValidationError.message)


class ExtensionValidator(Validator):
    """
    Проверяет расширение документа.
    """

    def __init__(self, allowed_extensions: set[str]):
        """
        :param allowed_extensions: Набор допустимых расширений (с точкой).
        """

        super().__init__()
        self.allowed_extensions = allowed_extensions

    def __call__(self, document: DocumentType) -> None:
        """
        Проверяет расширение документа.
        Для извлечения расширения используется функция `get_file_extension`.

        :param document: Проверяемый документ.

        :raises UnsupportedMediaTypeError: Если расширение документа не входит в allowed_extensions.
        """

        ext: str = get_file_extension(document)
        if ext not in self.allowed_extensions:
            raise UnsupportedMediaTypeError(
                f"Неподдерживаемый формат {ext!r}. Поддерживаются: {self.allowed_extensions}",
            )


class SizeValidator(Validator):
    """
    Проверяет размер документа.
    """

    def __init__(self, max_size_bytes: int):
        """
        :param max_size_bytes: Максимально допустимый размер в байтах.
        """

        super().__init__()
        self.max_size_bytes = max_size_bytes

    def __call__(self, document: DocumentType) -> None:
        """
        Проверяет длину документа.
        Использует `len(document)`, поэтому для корректности передавайте либо
        байтовый объект, либо объект, у которого len() даёт длину в байтах.

        :param document: Проверяемый документ.

        :raises FileTooLargeError: Если размер превышает max_size_bytes.
        """

        size: int = len(document)
        if size > self.max_size_bytes:
            raise FileTooLargeError(
                f"Размер файла превышает максимально допустимый размер {self.max_size_bytes}MB",
            )


class ChainValidator(Validator):
    """
    Комбинирует несколько валидаторов и выполняет их последовательно.
    """

    def __init__(
        self,
        validators: Iterable[Validator] | None = None,
        *,
        stop_on_first_error: bool = True,
    ):
        """
        :param validators: Итерируемая коллекция валидаторов, которые будут вызваны
                           в указанном порядке.
        :param stop_on_first_error: Если True - при первом выброшенном
                                    `ValidationError` вызов цепочки будет остановлен и
                                    исключение проброшено дальше; если False - все валидаторы
                                    будут вызваны, соберутся все `ValidationError` и
                                    в конце вернётся кортеж `(ok, errors)`.
        """

        super().__init__()
        self._validators: list[Validator] = list(validators or [])
        self.stop_on_first_error = stop_on_first_error

    def add(self, validator: Validator) -> None:
        """
        Добавляет валидатор в конец цепочки.
        """

        self._validators.append(validator)

    def extend(self, validators: Iterable[Validator]) -> None:
        """
        Добавляет несколько валидаторов в конец цепочки.
        """

        self._validators.extend(validators)

    def __call__(self, document: DocumentType) -> tuple[bool, list[ValidationError]]:
        """
        Выполняет все валидаторы в цепочке.

        :param document: Проверяемый документ.
        
        :return: Кортеж `(ok, errors)`, где `ok` - True при отсутствии ошибок,
                 `errors` - список пойманных `ValidationError`.
                 (Если `stop_on_first_error` == True, то в случае ошибки метод
                 выбросит исключение и не вернёт значение.)
        """
        
        errors: list[ValidationError] = []
        for validator in self._validators:
            try:
                validator(document)
            except ValidationError as e:
                if self.stop_on_first_error:
                    raise
                errors.append(e)
        return len(errors) == 0, errors
