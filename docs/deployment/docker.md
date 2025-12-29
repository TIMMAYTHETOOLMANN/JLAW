# JLAW Docker Deployment Guide

This guide covers deploying JLAW SEC Forensic Analysis Platform using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- Docker Compose v2.0+
- 8GB+ RAM
- 50GB+ disk space
- Internet connection (for SEC EDGAR API)

## Quick Start with Docker Compose

### 1. Clone Repository

```bash
git clone https://github.com/TIMMAYTHETOOLMANN/JLAW.git
cd JLAW
```

### 2. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
# Edit .env with your configuration
```

**Required Environment Variables:**

```bash
# SEC EDGAR Configuration
SEC_USER_AGENT="YourCompany contact@example.com"
SEC_RATE_LIMIT=6.0

# External API Keys
POLYGON_API_KEY=your_polygon_api_key

# Database Passwords
NEO4J_PASSWORD=secure_neo4j_password
TIMESCALE_PASSWORD=secure_timescale_password

# Optional: AI Validation
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f jlaw

# Check status
docker-compose ps
```

### 4. Verify Deployment

```bash
# Health check
docker-compose exec jlaw python scripts/health_check.py

# Test SEC EDGAR connection
docker-compose exec jlaw python -c "
from src.integrations.sec_edgar.edgar_client import SECEdgarClient
import asyncio

async def test():
    async with SECEdgarClient(user_agent='Test') as client:
        print('SEC EDGAR connection: OK')

asyncio.run(test())
"
```

## Single Container Deployment

### Build Image

```bash
docker build -t jlaw:latest .
```

### Run Container

```bash
docker run -d \
  --name jlaw-forensics \
  -e SEC_USER_AGENT="YourCompany contact@example.com" \
  -e SEC_RATE_LIMIT=6.0 \
  -e POLYGON_API_KEY=your_key \
  -v $(pwd)/evidence:/app/evidence \
  -v $(pwd)/reports:/app/reports \
  -v jlaw_cache:/app/.jlaw_cache \
  --restart unless-stopped \
  jlaw:latest
```

### View Logs

```bash
docker logs -f jlaw-forensics
```

### Execute Health Check

```bash
docker exec jlaw-forensics python scripts/health_check.py
```

## Docker Architecture

### Multi-Stage Build

The Dockerfile uses a three-stage build for optimization:

1. **base**: Python 3.10-slim with system dependencies
2. **dependencies**: Python package installation
3. **production**: Application code with non-root user

### Image Layers (Optimized)

```
├── Python 3.10-slim base (~150MB)
├── System dependencies (~50MB)
├── Python packages (~500MB)
└── Application code (~100MB)
────────────────────────────────
Total: ~800MB
```

### Health Check

The container includes a comprehensive health check that validates:
- Core engine availability (RecursiveProsecutorialEngine)
- Evidence chain components (HashService, MerkleTree)
- All 15 analysis nodes
- Detection pattern algorithms

Health check runs every 30 seconds with 10s timeout.

## Docker Compose Services

### JLAW Forensics Engine

```yaml
jlaw:
  - Python 3.10 application
  - Non-root user (UID 1000)
  - Resource limits: 2-4GB RAM, 1-2 CPU cores
  - Auto-restart on failure
```

### Neo4j Graph Database

```yaml
neo4j:
  - Version: 5.15-community
  - Ports: 7474 (HTTP), 7687 (Bolt)
  - Memory: 512MB-2GB heap
  - APOC plugin enabled
```

### TimescaleDB

```yaml
timescaledb:
  - PostgreSQL 15 with TimescaleDB extension
  - Port: 5432
  - Optimized for time-series data
  - 2GB shared buffers
```

### Redis Cache

```yaml
redis:
  - Version: 7-alpine
  - Port: 6379
  - Persistence: AOF enabled
  - MaxMemory: 1GB with LRU eviction
```

## Volume Management

### Persistent Volumes

```bash
# List volumes
docker volume ls | grep jlaw

# Inspect volume
docker volume inspect jlaw_neo4j_data

# Backup volume
docker run --rm -v jlaw_neo4j_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/neo4j-backup.tar.gz -C /data .

# Restore volume
docker run --rm -v jlaw_neo4j_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/neo4j-backup.tar.gz -C /data
```

### Host Bind Mounts

Evidence and reports are stored in host directories:

```bash
./evidence/  # SEC filings and raw data
./reports/   # Generated forensic dossiers
```

## Resource Configuration

### CPU Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'      # Maximum 2 cores
    reservations:
      cpus: '1.0'      # Guaranteed 1 core
```

### Memory Limits

```yaml
deploy:
  resources:
    limits:
      memory: 4G       # Maximum 4GB
    reservations:
      memory: 2G       # Guaranteed 2GB
```

### Adjust Resources

Edit `docker-compose.yml` and restart:

```bash
docker-compose down
docker-compose up -d
```

## Monitoring

### Container Stats

```bash
# Real-time stats
docker stats

# Specific container
docker stats jlaw-forensics
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f jlaw

# Last 100 lines
docker-compose logs --tail=100 jlaw

# Since timestamp
docker-compose logs --since 2024-01-01T00:00:00 jlaw
```

### Database Connections

```bash
# Neo4j browser
open http://localhost:7474

# TimescaleDB
docker-compose exec timescaledb psql -U jlaw -d jlaw_forensics

# Redis CLI
docker-compose exec redis redis-cli
```

## Security

### Non-Root User

JLAW runs as user `jlaw` (UID 1000) inside the container:

```dockerfile
USER jlaw
```

### Read-Only Root Filesystem (Optional)

For enhanced security, enable read-only root:

```yaml
services:
  jlaw:
    read_only: true
    tmpfs:
      - /tmp
      - /app/.jlaw_cache
```

### Network Isolation

```yaml
networks:
  jlaw-network:
    driver: bridge
    internal: false  # Set to true for no external access
```

### Secrets Management

Use Docker secrets instead of environment variables:

```bash
# Create secrets
echo "your_api_key" | docker secret create polygon_api_key -

# Use in compose
services:
  jlaw:
    secrets:
      - polygon_api_key
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs jlaw

# Inspect container
docker inspect jlaw-forensics

# Check resources
docker stats --no-stream
```

### Health Check Failing

```bash
# Manual health check
docker-compose exec jlaw python scripts/health_check.py

# Check dependencies
docker-compose exec jlaw pip list
```

### Database Connection Issues

```bash
# Check Neo4j health
docker-compose exec neo4j neo4j status

# Check TimescaleDB
docker-compose exec timescaledb pg_isready -U jlaw

# Check Redis
docker-compose exec redis redis-cli ping
```

### Storage Full

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a --volumes

# Remove old images
docker image prune -a --filter "until=24h"
```

## Updating JLAW

### Pull Latest Code

```bash
git pull origin main
```

### Rebuild Image

```bash
docker-compose build --no-cache jlaw
docker-compose up -d jlaw
```

### Zero-Downtime Update

```bash
# Scale up
docker-compose up -d --scale jlaw=2

# Update image
docker-compose pull jlaw

# Rolling restart
docker-compose up -d --no-deps jlaw

# Scale back down
docker-compose up -d --scale jlaw=1
```

## Production Best Practices

### 1. Use Docker Swarm or Kubernetes

For production deployments, use orchestration:
- Docker Swarm: Built-in clustering
- Kubernetes: See `docs/deployment/kubernetes.md`

### 2. External Databases

For production, use managed databases:
- AWS DocumentDB (Neo4j alternative)
- AWS RDS for PostgreSQL + TimescaleDB
- AWS ElastiCache for Redis

### 3. Backup Strategy

```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)

# Backup evidence
docker-compose exec jlaw tar czf /tmp/evidence-$DATE.tar.gz /app/evidence

# Backup Neo4j
docker-compose exec neo4j neo4j-admin dump --to=/tmp/neo4j-$DATE.dump

# Backup TimescaleDB
docker-compose exec timescaledb pg_dump -U jlaw jlaw_forensics > timescale-$DATE.sql
```

### 4. Monitoring & Alerting

- Prometheus + Grafana for metrics
- ELK Stack for log aggregation
- Sentry for error tracking

### 5. Resource Monitoring

```bash
# Set resource limits
ulimit -n 65536  # File descriptors
sysctl -w vm.max_map_count=262144  # For Neo4j
```

## Performance Tuning

### Neo4j Optimization

```yaml
environment:
  - NEO4J_dbms_memory_heap_max__size=4G
  - NEO4J_dbms_memory_pagecache_size=2G
```

### TimescaleDB Optimization

```yaml
command:
  - "-c"
  - "shared_buffers=4GB"
  - "-c"
  - "effective_cache_size=12GB"
```

### Redis Optimization

```yaml
command:
  - redis-server
  - --maxmemory 2gb
  - --maxmemory-policy allkeys-lru
  - --appendonly yes
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/TIMMAYTHETOOLMANN/JLAW/issues
- Documentation: https://github.com/TIMMAYTHETOOLMANN/JLAW/docs
- Docker Hub: https://hub.docker.com/r/timmaythetoolmann/jlaw
