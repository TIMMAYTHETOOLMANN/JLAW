# JLAW SEC Forensic Analysis System
# Python 3.11 slim-based container for production deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create output directories
RUN mkdir -p output forensic_storage

# Set proper permissions
RUN useradd -m -u 1000 jlaw && \
    chown -R jlaw:jlaw /app

# Switch to non-root user
USER jlaw

# Expose port (if needed for future API server)
EXPOSE 8000

# Default command - run the unified script
CMD ["python", "JLAW_UNIFIED.py"]
