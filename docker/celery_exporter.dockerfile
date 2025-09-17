FROM python:3.12-bookworm AS builder

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root --only=celery-exporter --no-interaction --no-ansi





FROM python:3.12-slim-bookworm AS production

COPY app ./app
COPY tasks ./tasks
COPY celery_exporter ./celery_exporter
COPY --from=builder /app/.venv .venv

ENV PATH=".venv/bin:$PATH"

CMD ["python", "-m", "celery_exporter.main"]
