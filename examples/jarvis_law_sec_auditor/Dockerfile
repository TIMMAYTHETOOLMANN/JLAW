# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install core dependencies in stages (prevents timeout)
# Stage 1: Web framework
RUN pip install --no-cache-dir \
    flask==2.3.3 \
    flask-cors==4.0.0 \
    waitress==2.1.2

# Stage 2: OpenAI and HTTP clients
RUN pip install --no-cache-dir \
    openai==1.12.0 \
    httpx==0.25.2 \
    beautifulsoup4==4.12.2 \
    lxml==4.9.3 \
    requests==2.31.0

# Stage 3: Configuration and utilities
RUN pip install --no-cache-dir \
    python-dotenv==1.0.0 \
    litellm==1.17.0

# Stage 4: Data science core
RUN pip install --no-cache-dir \
    numpy==1.24.4 \
    pandas==2.0.3 \
    scipy==1.11.4

# Stage 5: Machine learning
RUN pip install --no-cache-dir \
    scikit-learn==1.3.2 \
    matplotlib==3.7.5 \
    seaborn==0.12.2

# Stage 6: Network and text analysis
RUN pip install --no-cache-dir \
    networkx==3.2.1 \
    textstat==0.7.3

# Stage 7: Deep learning (continue on failure for large packages)
RUN pip install --no-cache-dir \
    torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu || true

# Stage 8: NLP packages (optional, continue on failure)
RUN pip install --no-cache-dir \
    transformers==4.36.2 \
    sentence-transformers==2.2.2 \
    spacy==3.7.2 || true

# Copy application code
COPY . .

# Create directories for outputs
RUN mkdir -p forensic_exports web_frontend

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# Run the application
CMD ["python", "production_waitress.py"]
