FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .

CMD ["uv", "run", "granian", "--interface", "asgi", "--host", "0.0.0.0", "--port", "9000", "--reload", "src.main:app"]
