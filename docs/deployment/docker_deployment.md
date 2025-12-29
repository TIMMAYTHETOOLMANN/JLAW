# Docker Deployment

Deploy JLAW using Docker and Docker Compose for production environments.

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/TIMMAYTHETOOLMANN/JLAW.git
cd JLAW

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f jlaw
```

---

## Docker Compose Configuration

The provided `docker-compose.yml` includes:
- JLAW application container
- Neo4j graph database
- Redis cache
- TimescaleDB time-series database

### Services

#### JLAW Application
```yaml
services:
  jlaw:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./output:/app/output
      - ./.env:/app/.env
    depends_on:
      - neo4j
      - redis
      - timescaledb
```

#### Neo4j
```yaml
  neo4j:
    image: neo4j:5.15
    ports:
      - "7474:7474"  # Browser
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j_data:/data
```

#### Redis
```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

#### TimescaleDB
```yaml
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=jlaw_forensics
    volumes:
      - timescale_data:/var/lib/postgresql/data
```

---

## Volume Management

```bash
# Create named volumes
docker volume create jlaw_neo4j_data
docker volume create jlaw_redis_data
docker volume create jlaw_timescale_data
docker volume create jlaw_output

# List volumes
docker volume ls

# Inspect volume
docker volume inspect jlaw_neo4j_data

# Backup volume
docker run --rm -v jlaw_neo4j_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/neo4j_backup.tar.gz -C /data .
```

---

## Production Deployment

### Build Production Image

```dockerfile
# Dockerfile.prod
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create cache and log directories
RUN mkdir -p /app/.jlaw_cache /var/log/jlaw

# Run as non-root user
RUN useradd -m -u 1000 jlaw && \
    chown -R jlaw:jlaw /app
USER jlaw

ENTRYPOINT ["python", "jlaw_cli.py"]
```

Build:
```bash
docker build -f Dockerfile.prod -t jlaw:production .
```

---

## Next Steps

- **[Prerequisites](prerequisites.md)**: System requirements
- **[Configuration](configuration.md)**: Environment variables
- **[Troubleshooting](troubleshooting.md)**: Common issues
