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
    poetry install --no-root --only=celery-worker --no-interaction --no-ansi





FROM python:3.12-slim-bookworm AS production

RUN apt-get update && apt-get install --no-install-recommends -y \
    libmagic1 \
    libmagic-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    libpangocairo-1.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY app ./app
COPY tasks ./tasks
COPY --from=builder /app/.venv .venv

ENV PATH=".venv/bin:$PATH"

CMD ["celery", "-A", "tasks.main.app", "worker", "--concurrency", "4"]
