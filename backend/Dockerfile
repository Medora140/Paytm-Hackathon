# =====================================================================
# Production Dockerfile for Render Web Service (FastAPI + PyMuPDF + Tesseract)
# =====================================================================

FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HF_HUB_ENABLE_HF_TRANSFER=0

WORKDIR /app

# Install system dependencies for OCR (Tesseract), PDF processing (Poppler), and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-cache local SentenceTransformer embedding model into the container image
# This eliminates startup download latency and Hugging Face network dependencies at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application source code
COPY . .

# Expose default port (overridden dynamically by Render via $PORT)
EXPOSE 8000

# Container healthcheck against the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start uvicorn server binding to 0.0.0.0 and dynamic $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
