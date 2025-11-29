# JLAW Production Container
# Multi-stage build for smaller image size

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app \
    METRICS_PORT=8000

WORKDIR ${APP_HOME}

# System dependencies commonly needed by parsing/ocr libs (kept minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       tesseract-ocr \
       poppler-utils \
       libgl1 \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first for better caching
COPY requirements.txt requirements.txt

# Install Python dependencies
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

# Copy source code
COPY . ${APP_HOME}

# Create non-root user
RUN useradd -ms /bin/bash jlaw \
    && chown -R jlaw:jlaw ${APP_HOME}

USER jlaw

EXPOSE ${METRICS_PORT}

# Healthcheck attempts to pull Prometheus metrics endpoint if running
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD \
  python -c "import urllib.request,os; \
  u=f'http://127.0.0.1:{os.getenv("METRICS_PORT","8000")}/metrics'; \
  urllib.request.urlopen(u).read(10); print('OK')" || exit 1

# Default command executes the production deployment
CMD ["python", "production_deployment.py"]
