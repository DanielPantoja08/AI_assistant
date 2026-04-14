# Stage 1: install dependencies with uv
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy only dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (not the project itself)
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install the project
COPY src/ ./src/
RUN uv sync --frozen --no-dev


# Stage 2: minimal runtime image
FROM python:3.14-slim AS runtime

WORKDIR /app

# System libraries required by OpenCV (cv2) / docling
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment and source from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src ./src
COPY --from=builder /app/pyproject.toml ./pyproject.toml

# Copy Alembic migration files
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini

# Copy entrypoint and strip Windows CRLF line endings
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/src"

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
