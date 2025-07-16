# Ingestion Service
Этот сервис предоставляет API для загрузки, обработки и индексации документов (PDF, DOCX, ...). 

## Функционал

- **Endpoint**: `POST /v1/documents/upload`.
- **Прием файлов**: `multipart/form-data` (файл/документ).
- **Параметры**: `workspace_id` (опционально).
- **Ответ**: Немедленный `202 Accepted` с `document_id`.
- **Фоновая обработка**: Все "тяжелые" операции выполняются в фоновом режиме.

### Пайплайн обработки

1.  **Сохранение**: Исходный файл сохраняется в "сыром" виде.
2.  **Извлечение текста**: Из PDF (`pypdf`) и DOCX (`python-docx`).
3.  **Определение языка**: С помощью `langdetect`.
4.  **Разбиение на чанки**: Используется `RecursiveCharacterTextSplitter` из LangChain.
5.  **Векторизация**: Чанки преобразуются в эмбеддинги моделью `all-MiniLM-L6-v2`.
6.  **Индексация**: Векторы сохраняются в векторное хранилище.
7.  **Сохранение метаданных**: Информация о документе сохраняется в репозиторий.

## Установка и запуск

### 1. Требования

- Python 3.12+
- Poetry

### 2. Установка зависимостей

**Если Poetry не установлен**
```bash
pip install poetry
```

**Если Poetry установлен**
```bash
# Установка всех зависимостей
poetry install

# Без dev-зависимостей (pytest, pytest-mock, requests)
poetry install --only=main
```

**Установка дополнительных библиотек для python-magic**
```bash
# Debian/Ubuntu
sudo apt-get install libmagic1

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
По умолчанию сервис использует локальные "заглушки", которые сохраняют данные в папку `./local_storage/`. Никаких дополнительных настроек не требуется.

### 4. Запуск сервиса
Используйте uvicorn для запуска FastAPI-приложения:
```bash
uvicorn api.main:app
```
Сервис будет доступен по адресу http://127.0.0.1:8000.
Интерактивная документация API (Swagger UI) находится по адресу http://127.0.0.1:8000/docs.

Или используйте gunicorn для запуска с несколькими рабочими процессами.
```bash
# <pr_num> нужно изменить на необходимое количество рабочих процессов 
gunicorn api.main:app --workers <pr_num> --worker-class uvicorn.workers.UvicornWorker
```
Рекомендуемое количество процессов - (2 * количество_ядер_CPU + 1)

## Запуск тестов и проверок качества кода
```bash
# Запуск тестов Pytest
pytest

# Проверка качества кода с Ruff
ruff check .
```
