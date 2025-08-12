# Ingestion Service
Этот сервис предоставляет API для загрузки, обработки и индексации документов (PDF, DOCX, ...), 
и API для "общения" с ними. 

## Функционал

### 1. Endpoint: `POST /v1/documents/upload`
- **Прием файлов**: `multipart/form-data` (файл/документ).
- **Параметры**: `workspace_id`.
- **Ответ**: Немедленный `202 Accepted` с `document_id`.
- **Фоновая обработка**: Все "тяжелые" операции выполняются в фоновом режиме.

**Пайплайн обработки**:
1. **Сохранение**: Исходный файл сохраняется в "сыром" виде.
2. **Извлечение текста**: Из PDF (`pypdf`) и DOCX (`python-docx`).
3. **Определение языка**: С помощью `langdetect`.
4. **Разбиение на чанки**: Используется `RecursiveCharacterTextSplitter` из LangChain.
5. **Векторизация**: Чанки преобразуются в эмбеддинги моделью `all-MiniLM-L6-v2`.
6. **Индексация**: Векторы сохраняются в векторное хранилище.
7. **Сохранение метаданных**: Информация о документе сохраняется в репозиторий.

### 2. Endpoint: `GET /v1/documents`
- **Параметры**: `workspace_id`.
- **Ответ**: `200 OK` со списком всех метаданных документов в формате JSON, хранящихся в указанном `workspace_id`.

Данные извлекаются из репозитория метаданных.

### 3. Endpoint: `POST /v1/chat/ask`
- **Тело запроса**: JSON `{"question": "...", "workspace_id": "...", "top_k": 3}` (top_k —
  опционально, по умолчанию 3).
- **Ответ**: `200 OK` с `{"answer": "...", "sources": [{"document_id": "...", "chunk_id": "...", "snippet": "..."}]}`.
- **Ответ**: `404 Not Found`, если в заданном `workspace_id` нет документов.

**Пайплайн обработки**:
1. **Векторизация**: Вопрос преобразуется в эмбеддинг моделью `all-MiniLM-L6-v2`.
2. **Поиск векторов**: Вектора с фильтром по `workspace_id` запрашиваются из векторного хранилища.
3. **Формирование вопроса**: Формируется вопрос для LLM из `question` и контекста.
4. **Ответ от LLM**: Генерируется ответ от LLM.
5. **Ответ**: Формируется ответ из ответа LLM и источников контекста.

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

### 3. Настройка переменных окружения (.env)
Скопируйте файл .env.example в .env, если планируете использовать иные настройки приложения.
```bash
cp .env.example .env
```
По умолчанию сервис использует локальные "заглушки", которые сохраняют данные в папку `./local_storage/`.
Никаких дополнительных настроек не требуется.

### 4. Запуск сервиса (отдельно backend и frontend)

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

### 5. Запуск сервиса (целиком, `docker compose`)
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
poetry run pytest --cov=api --cov=config --cov=domain --cov=exceptions --cov=infrastructure --cov=services --cov=stubs --cov-report=term-missing

# Проверка качества кода с Ruff
poetry run ruff check .
```
