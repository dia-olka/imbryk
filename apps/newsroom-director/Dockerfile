FROM python:3.12-slim AS base

WORKDIR /app

# Install build tools required for packages like hdbscan
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency installation
RUN pip install --no-cache-dir uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock README.md ./

# Install dependencies (includes torch, sentence-transformers, hdbscan)
RUN uv pip install --system .

# Copy application code (includes pre-generated _generated_data.py)
COPY newsroom_director/ newsroom_director/

# Pre-download the embedding model into the image so
# it doesn't need to be fetched at runtime
ENV HF_HOME=/app/.hf_cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

CMD ["python", "-m", "newsroom_director"]
