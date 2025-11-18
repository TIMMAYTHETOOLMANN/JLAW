FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY jlaw_forensics.py .

# Create necessary directories
RUN mkdir -p /var/forensic/worm \
    && mkdir -p /app/models \
    && mkdir -p /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV STORAGE_PROVIDER=LOCAL
ENV FORENSIC_S3_BUCKET=jlaw-forensic-evidence
ENV RETENTION_DAYS=2555
ENV GOVINFO_API_KEY=DEMO_KEY
ENV SEC_USER_AGENT="JLAW forensics@jlaw.com"
ENV AUDIT_SIGNING_KEY=default_signing_key

# Run as non-root user
RUN useradd -m -u 1000 forensic && chown -R forensic:forensic /app /var/forensic
USER forensic

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.forensics import ForensicOrchestrator; print('OK')" || exit 1

# Entry point
ENTRYPOINT ["python", "jlaw_forensics.py"]
CMD ["--help"]

