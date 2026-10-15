FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and install Python packages
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi>=0.115.0 \
    uvicorn[standard]>=0.32.0 \
    pydantic>=2.9.0 \
    pydantic-settings>=2.5.0 \
    sqlalchemy>=2.0.35 \
    aiosqlite>=0.20.0 \
    greenlet>=3.1.0 \
    pymupdf>=1.24.0 \
    sentence-transformers>=3.0.0 \
    faiss-cpu>=1.8.0 \
    rank-bm25>=0.2.2 \
    groq>=0.11.0 \
    python-multipart>=0.0.12 \
    httpx>=0.27.0 \
    numpy>=1.26.0

# Copy application source code
COPY app/ ./app/

# Environment variables
ENV PYTHONPATH=/app
ENV OMP_NUM_THREADS=1
ENV KMP_DUPLICATE_LIB_OK=TRUE

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
