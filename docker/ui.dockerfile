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
    poetry install --no-root --only=ui --no-interaction --no-ansi





FROM python:3.12-slim-bookworm AS production

WORKDIR /app

COPY services ./services
COPY --from=builder /app/.venv .venv

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "services/ui/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
