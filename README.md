# Ingestion Service
Этот сервис предоставляет API для загрузки, обработки и индексации документов (PDF, DOCX, ...), 
и API для "общения" с ними. 

## Дымовой сценарий

1. Создать рабочее пространство (workspace) -> получить workspace_id.
2. Загрузить документ (PDF, DOCX и др.) в сервис (POST /v1/documents/upload {document}) -> получить document_id.
3. Убедиться, что в реестре/базе данных появилась запись по этому document_id.
4. Задать вопрос в чат (POST /v1/chat/ask {question, workspace_id, top_k, session_id?}) -> получить answer (ответ) и sources (источники)
   - Скачать исходный документ из источника.
   - Задать вопрос снова

## Функционал

### 1. Documents API

#### `GET /v1/documents`:
- **Описание**: Возвращает список метаданных документов в заданном рабочем пространстве.
- **Параметры**: `workspace_id` (query).
- **Ответ**: `200 OK` - список объектов `DocumentMeta` (JSON)
- **Формат ответа**: `application/json`.
- **Пример ответа**:
```json
[
  {
    "document_id": "f47ac10b-...",
    "workspace_id": "workspace-1",
    "document_name": "invoice.pdf",
    "media_type": "application/pdf",
    "document_page_count": 5,
    "author": "Alice",
    "creation_date": "2023-05-01T12:00:00",
    "raw_storage_path": "workspace-1/f47ac10b-invoice.pdf",
    "file_size_bytes": 12345,
    "ingested_at": "2024-08-13T10:00:00",
    "status": "success"
  }
]
```

#### `POST /v1/documents/upload`:
- **Описание**: Загружает документ; запускает полную обработку (сохранение, извлечение текста, векторизация, запись метаданных) в фоне.
- **Прием файлов**: `multipart/form-data` (файл/документ).
- **Параметры**: `workspace_id` (query).
- **Ответ**: `202 Accepted` немедленный ответ с `document_id`.
- **Фоновая обработка**: Разбор документа и индексирование выполняются в фоновых задачах.
- **Пример ответа**:
```json
{ "document_id": "d290f1ee-..." }
```
- **Возможные ошибки**:
  - `415 Unsupported Media Type` - формат файла не поддерживается.
  - `413 Request Entity Too Large` - файл больше разрешенного размера.

#### `GET /v1/documents/{document_id}/download`:
- **Описание**: Скачивает исходный файл (streaming).
- **Параметры**: `document_id` (path).
- **Ответ**: `200 OK` - потоковый ответ (`StreamingResponse`) с заголовками `Content-Disposition` и `Content-Length`.
- **Формат ответа**: бинарный поток (например, `application/pdf`).
- **Возможные ошибки**:
  - `404 Not Found` - документ с таким `document_id` не найден.

### 2. Chat API

#### `GET /v1/chat`:
- **Описание**: Возвращает список всех чат-сессий в рабочем пространстве.
- **Параметры**: `workspace_id` (query).
- **Ответ**: `200 OK` - список ChatSessionDTO (JSON).
- **Формат ответа**: `application/json`.
- **Пример ответа**:
```json
[
  {
    "id": "f47ac10b-...",
    "workspace_id": "qa98bc3p-...",
    "created_at": "2024-08-13T10:00:00"
  }
]
```

#### `POST /v1/chat/ask`:
- **Описание**: Принимает запрос пользователя, ищет релевантные фрагменты в векторном индексе и генерирует ответ (RAG — retrieval augmented generation).
- **Пример тела запроса (JSON)**:
```json
{
  "workspace_id": "qa98bc3p-...",
  "question": "Как оплатить счёт?",
  "top_k": 3,        // опционально, по умолчанию 3
  "session_id": null // опционально — если не указан, создаётся новая сессия
}
```
- **Особенности**:
  - Если `session_id` не задан - создается новая чат-сессия и ее `id` возвращается в `ChatResponse` как `session_id`.
  - После генерации ответ и исходный вопрос сохраняются в БД (user + assistant сообщения).
- **Ответ**: `200 OK` - ChatResponse (JSON).
- **Пример ответа**:
```json
{
  "answer": "Вот как вы можете оплатить...",
  "sources": [
    {
      "source_id": "f47ac10b-...",
      "document_name": "invoice.pdf",
      "document_page": 2,
      "snippet": "оплатить можно через банк..."
    }
  ],
  "session_id": "qa98bc3p-..."
}
```
- **Возможные ошибки**:
  - Ошибки валидации запроса (4xx).

#### `GET /v1/chat/{session_id/messages`:
- **Описание**: Возвращает все сообщения указанной чат-сессии в хронологическом порядке.
- **Параметры**: `session_id` (path).
- **Ответ**: `200 OK` - список ChatMessageDTO (JSON).
- **Пример ответа**:
```json
[
  {
    "id": "f47ac10b-...",
    "session_id": "qa98bc3p-...",
    "role": "user",
    "content": "Как оплатить счёт?",
    "created_at": "2024-08-13T10:00:00"
  },
  {
    "id": "q47bd19a-...",
    "session_id": "qa98bc3p-...",
    "role": "assistant",
    "content": "Вот как вы можете оплатить...",
    "created_at": "2024-08-13T10:00:00"
  }
]
```

### 3. Workspaces API

#### `GET /v1/workspaces`:
- **Описание**: Возвращает список всех рабочих пространств.
- **Ответ**: `200 OK` - список `WorkspaceDTO` (JSON).
- **Пример ответа**:
```json
[
  {
    "id": "qa98bc3p-...",
    "name": "default",
    "created_at": "2024-08-13T10:00:00"
  }
]
```

#### `POST /v1/workspaces`:
- **Описание**: Создаёт новое рабочее пространство.
- **Параметры**: `name` (query/body - строка).
- **Ответ**: `201 Created` - `WorkspaceDTO` (JSON).
- **Пример ответа**:
```json
{
  "id": "qa98bc3p-...",
  "name": "default",
  "created_at": "2024-08-13T10:00:00"
}
```
- **Возможные ошибки**:
  - `409 Conflict` - пространство с таким именем уже существует.

#### `DELETE /v1/workspaces/{workspace_id}`:
- **Описание**: Удаляет workspace и все связанные с ним данные (сырые файлы, векторы, метаданные, сессии, сообщения).
- **Параметры**: `workspace_id` (path).
- **Ответ**: `204 No Content` - задача удаления запускается в фоновом режиме.
- **Примечание**: при удалении могут быть удалены большие объёмы данных — убедитесь, что вы создаёте бэкапы при необходимости.

### 4. Адаптеры
Приложение поддерживает несколько реализаций (адаптеров) для внешних сервисов:
- Репозиторий (`Repository`) - хранение метаданных.
  - `AlchemyRepository` - может быть и stub, и prod, реализован как репозиторий для общения с БД.
- Сырое хранилище (`RawStorage`) - хранение сырых файлов PDF, DOCX и др.
  - `FileRawStorage`: stub, реализован как локальное файловое хранилище.
  - `MinIORawStorage`: MinIO, S3-совместимое файловое хранилище.
- Векторное хранилище (`VectorStore`) - хранение векторов, поиск.
  - `JSONVectorStore`: stub, реализован как локальное векторное хранилище в формате JSON.
  - `QdrantVectorStore`: Qdrant, векторное хранилище.

Как приложение выбирает, какой адаптер использовать? Выбор осуществляется во время старта приложения по наличию соответствующих переменных окружения (прочитанных из .env):
- Если задан `DATABASE_URL` - используется выбранная БД, иначе - локальная `SQLite`.
- Если задан `MINIO_ENDPOINT` - используется `MinIORawStorage`, иначе - `FileRawStorage`.
- Если задан `QDRANT_URL` - используется `QdrantVectorStore`, иначе - `JSONVectorStore`.
  - Также можно использовать связку `QDRANT_HOST` + `QDRANT_PORT`. `QDRANT_PORT` по умолчанию уже задан как 6333.

## Переменные окружения + частые форматы

### Конфигурация базы данных

```text
DATABASE_URL=dialect+driver://username:password@host:port/dbname

# например для PostgreSQL
DATABASE_URL=postgres+asyncpg://username:password@host:5432/dbname
```

### Конфигурация MinIO

```text
MINIO_ENDPOINT=host[:port] (пишется без протокола http или https)

# например
MINIO_ENDPOINT=localhost:9000

# дополнительно могут потребоваться ключи доступа
MINIO_ACCESS_KEY=access_key
MINIO_SECRET_KEY=secret_key

# имена бакетов в MinIO
MINIO_BUCKET_RAW=my-raw-bucket
MINIO_BUCKET_SILVER=my-silver-bucket
```

### Конфигурация Qdrant

```text
QDRANT_URL=[http/https]://host:port

# например
QDRANT_URL=http://localhost:6333

# или отдельно QDRANT_HOST и QDRANT_PORT
QDRANT_HOST=localhost
QDRANT_PORT=6333

# дополнительно может потребоваться ключ доступа
QDRANT_API_KEY=api_key

# имя коллекции в Qdrant
QDRANT_COLLECTION=my_collection_name

# конфигурация Qdrant коллекции
QDRANT_VECTOR_SIZE=384
QDRANT_DISTANCE=Cosine
```

## Установка и запуск

### 1. Требования

- Python 3.12+
- Poetry (Если не планируете использовать Poetry, то замените везде вызовы 'poetry run' на 'python -m')

### 2. Установка зависимостей

**Если Poetry не установлен**
```bash
# Через pip
pip install poetry

# С помощью официального установщика (требуется curl)
export POETRY_VERSION=1.8.2
curl -sSL https://install.python-poetry.org | python3 -
```

**Если Poetry установлен**
```bash
# Установка всех зависимостей
poetry install

# Без dev-зависимостей (ruff, pytest, pytest-mock, ...)
poetry install --without=dev
```

**Установка дополнительных библиотек для `python-magic`**
```bash
# Debian/Ubuntu
apt-get install libmagic1

# Windows
pip install python-magic-bin или poetry add python-magic-bin

# MacOS
Homebrew: brew install libmagic
macports: port install file
```

### 3. Миграции БД
Если миграции ещё не применены к базе данных.
```bash
poetry run alembic upgrade head
```

### 4. Настройка переменных окружения (.env)
Скопируйте файл .env.example в .env, если планируете использовать иные настройки приложения.
```bash
cp .env.example .env
```
По умолчанию сервис использует локальные "заглушки", которые сохраняют данные в папку `./local_storage/`.
Никаких дополнительных настроек не требуется.

### 5. Запуск сервиса (отдельно backend и frontend)

#### 1. Запуск API
Используйте uvicorn для запуска FastAPI-приложения:
```bash
poetry run uvicorn api.main:app
```
API будет доступен по адресу http://127.0.0.1:8000.
Интерактивная документация API (Swagger UI) находится по адресу http://127.0.0.1:8000/docs.

Или используйте gunicorn для запуска с несколькими рабочими процессами.
```bash
# <pr_num> требуется изменить на необходимое количество рабочих процессов 
poetry run gunicorn api.main:app --workers <pr_num> --worker-class uvicorn.workers.UvicornWorker
```
Рекомендуемое количество процессов - (2 * количество_ядер_CPU + 1)

#### 2. Запуск UI
```bash
poetry run streamlit run ui/main.py
# Или если ваш backend имеет отличный адрес от http://127.0.0.1:8000, вы можете задать переменную окружения BACKEND_URL,
# где вместо <backend_url> установить адрес вашего backend
BACKEND_URL=<backend_url> poetry run streamlit run ui/main.py
```
UI будет доступен по адресу http://127.0.0.1:8501

### 6. Запуск сервиса (целиком, `docker compose`)
```bash
# Требуется установленный Docker Engine и docker compose
docker-compose up
# Или если compose установлен нативно
docker compose up
```
API будет доступен по адресу http://0.0.0.0:8000, UI по адресу http://0.0.0.0:8501

## Запуск тестов и проверок качества кода
```bash
# Запуск тестов Pytest
poetry run pytest

# Покрытие кода
poetry run pytest --cov=api --cov=config --cov=domain --cov=exceptions --cov=infrastructure --cov=schemas --cov=services --cov=stubs --cov=utils --cov-report=term-missing

# Проверка качества кода с Ruff
poetry run ruff check .
```
