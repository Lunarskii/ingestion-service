# Архитектура Ingestion Service

## Архитектурные слои

### Описание слоев

1. **`api/` (Слой API)**
    - Отвечает за прием HTTP-запросов, их валидацию и отправку ответа.
    - Использует `FastAPI`.
    - Не содержит бизнес-логики.

2. **`config/` (Настройки приложения)**
    - Отвечает за управление конфигурацией приложения из переменных окружения.
    - Использует `pydantic_settings.BaseSettings`

3. **`domain/` (Ядро приложения)**
    - Содержит пакеты `chat` и `fhandler` с бизнес-логикой и основные модели данных `schemas.py`.
    - Этот слой полностью изолирован от деталей инфраструктуры.

4. **`domain/fhandler/` (Обработка документов)**
    - Содержит бизнес-логику `service.py` для обработки документов и модели данных `schemas.py`.
    - Является центральным компонентом для конвейера приёма и обработки документов.
    - Спроектирован для работы с абстрактными интерфейсами хранилищ.

5. **`domain/chat/` (RAG-логика)**
    - Содержит бизнес-логику `service.py` для "общения" с документами и модели данных `schemas.py`.
    - Является ядром вопросно-ответной системы, реализует пайплайн RAG (Retrieval-Augmented Generation).
    - Зависит от абстрактного интерфейса `VectorStore`, что позволяет легко заменять реализацию векторной базы данных.

6. **`exceptions/` (Исключения)**
    - Содержит базовые исключения для всего приложения в `base.py` и базовые исключения хранилищ в `storage.py`.

7. **`services/` (Абстракции / Интерфейсы)**
    - "Контракты", которые определяют, какие методы должны быть у сервисов хранения.
    - Используется `typing.Protocol` для статической типизации без необходимости наследования от базовых классов.
    - **`RawStorage`**: контракт для хранения "сырых" файлов.
    - **`VectorStore`**: контракт для индексации векторов.
    - **`MetadataRepository`**: контракт для хранения метаданных о документах.

8. **`stubs/` ("Заглушки")**
    - Простые реализации интерфейсов для локальной разработки и тестирования.
    - `FileRawStorage`: сохраняет файлы в локальную папку.
    - `JSONVectorStore`: сохраняет векторы в JSON-файлы.
    - `SQLiteMetadataRepository`: использует локальную базу данных SQLite.

## Как добавить "продуктивные" реализации

**Пример: Добавление поддержки S3 для `RawStorage`**

1. **Создать новую реализацию:**
    - Создать файл, например, `./implementations/s3_storage.py`.
    - В этом файле создать класс `S3RawStorage`, который реализует протокол `RawStorage` (т.е. имеет метод `save`).

    ```python
    from services.interfaces import RawStorage

    class S3RawStorage(RawStorage):
        def __init__(self, bucket_name: str):
            self.s3_client = ...
            self.bucket_name = bucket_name

        def save(self, file_bytes: bytes, path: str) -> None:
            self.s3_client.put(
                bucket=self.bucket_name, 
                key=path, 
                data=file_bytes,
            )
    ```

2. **Обновить конфигурацию:**
    - Добавить в `config/storage.py` переменные, необходимые для новой реализации (например, `s3_bucket`).

    ```python
    class StorageSettings(BaseSettings):
        raw_storage_path: Annotated[str, Field(alias="RAW_STORAGE_PATH")] = ...
        # ...
        s3_bucket: Annotated[str | None, Field(alias="S3_BUCKET")] = None
    ```

3. **Обновить `api/fhandler/dependencies.py`:**
    - Добавить логику в `get_raw_storage()`, чтобы она возвращала `S3RawStorage`, если `storage_settings.s3_storage` установлен.

    ```python
    from config import stub_settings
    from stubs.storage import FileRawStorage
    from implementations.s3_storage import S3RawStorage # Импортируем новый класс

    def get_raw_storage() -> RawStorage:
        if s3_bucket := stub_settings.s3_bucket:
            return S3RawStorage(bucket_name=s3_bucket)
        
        if stub_settings.raw_storage_path:
            return FileRawStorage()
            
        raise ValueError(...)
    ```

Теперь, просто изменив переменную окружения `S3_BUCKET=bucket_name`, все приложение начнет использовать S3 вместо локального хранилища, без единого изменения в `domain/` или `api/` слоях, за исключением самих зависимостей в `api/dependencies.py`.

**Пример: Добавление поддержки новых документов для `TextExtractor`**

1. **Создать новую реализацию:**
    - Создать новый класс в `domain/fhandler/extractor.py`, например, `XlsxExtractor`. Этот класс будет использовать библиотеку `openpyxl` для взаимодействия с XLSX документами.
    - В этом классе реализовать метод `_extract(...)`

    ```python
    class XlsxExtractor(TextExtractor):
        def _extract(self, document: IO[bytes]) -> ExtractedInfo:
            document = openpyxl.load_workbook(document)
            metadata = document.properties
            text: str = "\n".join(
                " ".join(str(cell) for cell in row if cell is not None)
                for sheet in document.worksheets
                for row in sheet.iter_rows(values_only=True)
            )
   
            return ExtractedInfo(
                text=text,
                author=metadata.creator,
                creation_date=metadata.created,
            )
    ```
   
2. **Обновить фабрику экстракторов `domain/fhandler/factory.py`:**
    - Добавить в `ExtractorFactory._map` новый экстрактор, необходимый для обработки документов данного типа, чтобы функция `ExtractorFactory.get_extractor(...)` возвращала его, когда потребуется.

    ```python
    from domain.handlers import XlsxExtractor
   
    class ExtractorFactory:
        _map: dict[str, type[TextExtractor]] = {
            "pdf": PdfExtractor,
            ...,
            "xlsx": XlsxExtractor,
        }
    ```
   
Теперь из документов типа XLSX тоже можно будет извлечь текст и необходимые метаданные.
