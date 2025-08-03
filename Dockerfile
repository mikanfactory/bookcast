FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    poppler-utils \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache --no-dev

COPY .env ./.env
RUN mkdir downloads
COPY resources/ ./resources/
COPY src/bookcast ./src/bookcast

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["fastapi", "run", "src/bookcast/main.py"]
