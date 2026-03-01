FROM python:3.9-slim AS base

WORKDIR /app

# Install uv for fast dependency installation
RUN pip install --no-cache-dir uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (includes torch, sentence-transformers, hdbscan)
RUN uv pip install --system .

# Copy application code
COPY newsroom_director/ newsroom_director/

# Pre-download the embedding model into the image so
# it doesn't need to be fetched at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

CMD ["python", "-m", "newsroom_director.main"]
