# JLAW SEC Forensic Financial Analysis System
# Multi-stage build for optimized production image
FROM python:3.10-slim AS base

# Security & Metadata Labels
LABEL maintainer="JLAW Development Team"
LABEL description="JLAW SEC Forensic Financial Analysis System - 15-Node Recursive Prosecutorial Engine"
LABEL version="4.1.0"
LABEL org.opencontainers.image.title="JLAW Forensics"
LABEL org.opencontainers.image.description="DOJ-grade SEC filing forensic analysis platform"
LABEL org.opencontainers.image.vendor="JLAW Development Team"
LABEL org.opencontainers.image.version="4.1.0"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/TIMMAYTHETOOLMANN/JLAW"
LABEL security.scan="trivy"
LABEL compliance.fre="902(13)/902(14)"
LABEL compliance.soc2="type-ii-preparation"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies (no version pinning for system packages due to distro variations)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

FROM base AS dependencies

# Copy dependency files
COPY requirements.txt pyproject.toml ./

# Install Python dependencies (upgrade pip without pinning to avoid SSL issues in build environments)
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

FROM dependencies AS production

# Copy application code (layer optimization - most stable to most volatile)
COPY config/ ./config/
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY JLAW_UNIFIED.py ./

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 jlaw && \
    chown -R jlaw:jlaw /app && \
    mkdir -p /app/evidence /app/reports /app/.jlaw_cache && \
    chown -R jlaw:jlaw /app/evidence /app/reports /app/.jlaw_cache

USER jlaw

# Health check using dedicated script
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python scripts/health_check.py || exit 1

CMD ["python", "JLAW_UNIFIED.py"]
