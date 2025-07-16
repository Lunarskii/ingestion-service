# Архитектура Ingestion Service

## Архитектурные слои

### Описание слоев

1. **`api/` (Слой API)**
    - Отвечает за прием HTTP-запросов, их валидацию и отправку ответа.
    - Использует `FastAPI`.
    - Не содержит бизнес-логики. Его задача — запустить фоновую задачу и немедленно вернуть ответ.

2. **`config/` (Настройки приложения)**
    - Отвечает за управление конфигурацией приложения из переменных окружения.
    - Использует `pydantic_settings.BaseSettings`

3. **`domain/` (Ядро приложения)**
    - Содержит основную бизнес-логику (`process.py`) и модели данных (`schemas.py`).
    - Этот слой полностью изолирован от деталей инфраструктуры. Он не знает, где хранятся файлы или векторы. Он просто вызывает методы у объектов, которые соответствуют нужным интерфейсам.

4. **`services/` (Абстракции / Интерфейсы)**
    - "Контракты", которые определяют, какие методы должны быть у сервисов хранения.
    - Используются `typing.Protocol` для статической типизации без необходимости наследования от базовых классов.
    - **`RawStorage`**: контракт для хранения "сырых" файлов.
    - **`VectorStore`**: контракт для индексации векторов.
    - **`MetadataRepository`**: контракт для хранения метаданных о документах.

5. **`stubs/` ("Заглушки")**
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

3. **Обновить `api/dependencies.py`:**
    - Добавить логику в `raw_storage_dependency()`, чтобы она возвращала `S3RawStorage`, если `storage_settings.s3_storage` установлен.

    ```python
    from config import storage_settings
    from stubs.storage import FileRawStorage
    from implementations.s3_storage import S3RawStorage # Импортируем новый класс

    def raw_storage_dependency() -> RawStorage:
        if s3_bucket := storage_settings.s3_bucket:
            return S3RawStorage(bucket_name=s3_bucket)
        
        if storage_settings.raw_storage_path:
            return FileRawStorage()
            
        raise ValueError(...)
    ```

Теперь, просто изменив переменную окружения `S3_BUCKET=bucket_name`, все приложение начнет использовать S3 вместо локального хранилища, без единого изменения в `domain/` или `api/` слоях, за исключением самих зависимостей в `api/dependencies.py`.

**Пример: Добавление поддержки новых документов для `TextExtractor`**

1. **Создать новую реализацию:**
    - Создать новый класс в `domain/handlers/extractor.py`, например, `XlsxExtractor`. Этот класс будет использовать библиотеку `openpyxl` для взаимодействия с XLSX документами.
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
   
2. **Обновить фабрику экстракторов `domain/handlers/factory.py`:**
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
