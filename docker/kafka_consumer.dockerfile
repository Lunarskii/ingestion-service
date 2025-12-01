FROM python:3.12-bookworm AS builder

RUN apt-get update && \
    apt-get install --no-install-recommends -y build-essential curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

#RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.8.2 python3 -
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --no-cache-dir "poetry==1.8.2" && \
    ln -s /usr/local/bin/poetry /root/.local/bin/poetry || true

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root --only=kafka-consumer --no-interaction --no-ansi





FROM python:3.12-slim-bookworm AS production

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
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

WORKDIR /app

COPY app ./app
COPY services ./services
COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 9093

CMD ["gunicorn", "services.kafka_consumer.main.app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:9093"]
