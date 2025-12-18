# JLAW SEC Forensic Financial Analysis System
FROM python:3.11-slim AS base

LABEL maintainer="JLAW Development Team"
LABEL description="JLAW SEC Forensic Financial Analysis System - 15-Node Recursive Prosecutorial Engine"
LABEL version="4.0.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

FROM base AS dependencies
COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip && pip install -r requirements.txt

FROM dependencies AS production
COPY src/ ./src/
COPY config/ ./config/

RUN useradd --create-home --shell /bin/bash jlaw && \
    chown -R jlaw:jlaw /app && \
    mkdir -p /app/evidence /app/reports /app/.jlaw_cache && \
    chown -R jlaw:jlaw /app/evidence /app/reports /app/.jlaw_cache

USER jlaw

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.core import recursive_engine; print('OK')" || exit 1

CMD ["python", "-m", "src.core.recursive_engine"]
