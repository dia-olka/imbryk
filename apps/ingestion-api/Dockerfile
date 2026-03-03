FROM python:3.12-slim AS base

WORKDIR /app

# Install uv for fast dependency installation
RUN pip install --no-cache-dir uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv pip install --system .

# Copy application code
COPY ingestion_api/ ingestion_api/
COPY alembic/ alembic/
COPY alembic.ini .

EXPOSE 8080

CMD ["uvicorn", "ingestion_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
