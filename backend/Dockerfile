FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache --no-dev

FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY .env ./.env
RUN mkdir downloads
COPY resources/ ./resources/
COPY src/bookcast ./src/bookcast

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080
CMD ["fastapi", "run", "src/bookcast/main.py", "--port", "8080"]
