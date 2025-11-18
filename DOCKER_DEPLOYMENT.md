# JLAW Forensic System - Docker Deployment Guide

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### 1. Build the Image

```bash
# Build Docker image
docker build -t jlaw-forensics:latest .

# Verify build
docker images | grep jlaw-forensics
```

### 2. Run with Docker

```bash
# Run help
docker run --rm jlaw-forensics:latest --help

# Run verification
docker run --rm jlaw-forensics:latest verify

# Run investigation
docker run --rm \
    -e GOVINFO_API_KEY="your_key" \
    -v $(pwd)/results:/app/results \
    jlaw-forensics:latest investigate \
    --cik 0001318605 \
    --name "Tesla Inc" \
    --output /app/results/tesla.json
```

### 3. Run with Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f jlaw-forensics

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Storage
STORAGE_PROVIDER=LOCAL  # AWS, AZURE, or LOCAL
RETENTION_DAYS=2555

# API Keys
GOVINFO_API_KEY=your_api_key_here
SEC_USER_AGENT=YourCompany contact@email.com

# AWS (if using)
AWS_REGION=us-east-1
FORENSIC_S3_BUCKET=your-forensic-bucket
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Azure (if using)
AZURE_STORAGE_CONNECTION=your_connection_string

# Security
AUDIT_SIGNING_KEY=your_secret_signing_key
```

### Docker Compose Configuration

Edit `docker-compose.yml` for custom settings:

```yaml
services:
  jlaw-forensics:
    command: ["investigate", "--cik", "0001318605", "--name", "Tesla Inc"]
    environment:
      - STORAGE_PROVIDER=AWS
      # ... other vars
```

---

## Deployment Scenarios

### Scenario 1: Local Development

```bash
# Build and run locally
docker build -t jlaw-forensics:latest .

# Run interactive shell
docker run -it --rm \
    -v $(pwd)/data:/var/forensic/worm \
    -v $(pwd)/logs:/app/logs \
    jlaw-forensics:latest /bin/bash

# Inside container
python jlaw_forensics.py verify
python jlaw_forensics.py investigate --cik 0001318605 --name "Tesla Inc"
```

### Scenario 2: Single Investigation

```bash
# Run one-off investigation
docker run --rm \
    -e GOVINFO_API_KEY="${GOVINFO_API_KEY}" \
    -v $(pwd)/results:/app/results \
    jlaw-forensics:latest investigate \
    --cik 0001318605 \
    --name "Tesla Inc" \
    --years 3 \
    --output /app/results/tesla_investigation.json

# Check results
cat results/tesla_investigation.json | jq '.summary'
```

### Scenario 3: Continuous Monitoring

```bash
# Start monitoring service
docker-compose up -d jlaw-monitor

# Check logs
docker-compose logs -f jlaw-monitor

# Logs will show:
# INFO - Monitoring iteration 1
# INFO - System integrity: VALID - Next check in 1 hour
```

### Scenario 4: Production Deployment

```bash
# Create production compose file
cat > docker-compose.prod.yml << EOF
version: '3.8'

services:
  jlaw-forensics:
    image: jlaw-forensics:latest
    environment:
      - STORAGE_PROVIDER=AWS
      - FORENSIC_S3_BUCKET=prod-forensic-evidence
      - GOVINFO_API_KEY=\${GOVINFO_API_KEY}
      - AWS_ACCESS_KEY_ID=\${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=\${AWS_SECRET_ACCESS_KEY}
    volumes:
      - /mnt/forensic-data:/var/forensic/worm
      - /var/log/forensic:/app/logs
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
EOF

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Scenario 5: Batch Processing

```bash
# Batch investigation script
cat > batch_investigate.sh << 'EOF'
#!/bin/bash

COMPANIES=(
    "0001318605:Tesla Inc"
    "0000320193:Apple Inc"
    "0001652044:Alphabet Inc"
)

for entry in "${COMPANIES[@]}"; do
    IFS=':' read -r cik name <<< "$entry"
    
    echo "Investigating: $name (CIK: $cik)"
    
    docker run --rm \
        -e GOVINFO_API_KEY="${GOVINFO_API_KEY}" \
        -v $(pwd)/results:/app/results \
        jlaw-forensics:latest investigate \
        --cik "$cik" \
        --name "$name" \
        --output "/app/results/${cik}_report.json"
    
    sleep 10  # Rate limiting
done
EOF

chmod +x batch_investigate.sh
./batch_investigate.sh
```

---

## Volume Management

### Persistent Data

```bash
# Create named volumes
docker volume create forensic-data
docker volume create forensic-logs
docker volume create forensic-models

# Inspect volume
docker volume inspect forensic-data

# Backup volume
docker run --rm \
    -v forensic-data:/data \
    -v $(pwd)/backup:/backup \
    alpine tar czf /backup/forensic-data-$(date +%Y%m%d).tar.gz -C /data .

# Restore volume
docker run --rm \
    -v forensic-data:/data \
    -v $(pwd)/backup:/backup \
    alpine tar xzf /backup/forensic-data-YYYYMMDD.tar.gz -C /data
```

### Bind Mounts

```bash
# Use local directories
docker run --rm \
    -v $(pwd)/data:/var/forensic/worm \
    -v $(pwd)/logs:/app/logs \
    -v $(pwd)/models:/app/models \
    jlaw-forensics:latest verify
```

---

## Networking

### Port Exposure (if adding web server)

```yaml
services:
  jlaw-forensics:
    ports:
      - "8000:8000"  # Web API
      - "9000:9000"  # Metrics
```

### Multi-Container Communication

```yaml
services:
  jlaw-forensics:
    networks:
      - forensic-network
      - external-network

  jlaw-database:
    networks:
      - forensic-network

networks:
  forensic-network:
    internal: true
  external-network:
    driver: bridge
```

---

## Security

### Run as Non-Root

Already configured in Dockerfile:
```dockerfile
USER forensic  # UID 1000
```

### Secrets Management

```bash
# Use Docker secrets
echo "your_api_key" | docker secret create govinfo_api_key -

# In compose file
services:
  jlaw-forensics:
    secrets:
      - govinfo_api_key
    environment:
      - GOVINFO_API_KEY_FILE=/run/secrets/govinfo_api_key

secrets:
  govinfo_api_key:
    external: true
```

### Read-Only Filesystem

```yaml
services:
  jlaw-forensics:
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs
```

---

## Monitoring

### Health Checks

```bash
# Check container health
docker ps --filter name=jlaw-forensics

# View health status
docker inspect jlaw-forensics | jq '.[0].State.Health'

# Health endpoint
docker exec jlaw-forensics python -c "from src.forensics import ForensicOrchestrator; print('OK')"
```

### Logs

```bash
# View logs
docker logs jlaw-forensics

# Follow logs
docker logs -f jlaw-forensics

# Last 100 lines
docker logs --tail 100 jlaw-forensics

# Export logs
docker logs jlaw-forensics > forensic.log
```

### Resource Usage

```bash
# Monitor resources
docker stats jlaw-forensics

# Resource limits in compose
services:
  jlaw-forensics:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/docker-build.yml
name: Build and Push Docker Image

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build image
        run: docker build -t jlaw-forensics:${{ github.sha }} .
      
      - name: Test image
        run: docker run --rm jlaw-forensics:${{ github.sha }} verify
      
      - name: Push to registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker tag jlaw-forensics:${{ github.sha }} your-registry/jlaw-forensics:latest
          docker push your-registry/jlaw-forensics:latest
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - docker build -t jlaw-forensics:$CI_COMMIT_SHA .
    - docker push jlaw-forensics:$CI_COMMIT_SHA

test:
  stage: test
  script:
    - docker run --rm jlaw-forensics:$CI_COMMIT_SHA verify

deploy:
  stage: deploy
  script:
    - docker-compose -f docker-compose.prod.yml up -d
  only:
    - main
```

---

## Troubleshooting

### Build Issues

**Problem:** Package installation fails
```bash
# Check network connectivity
docker run --rm python:3.11-slim ping -c 3 pypi.org

# Use cache from previous build
docker build --cache-from jlaw-forensics:latest -t jlaw-forensics:latest .
```

**Problem:** Out of disk space
```bash
# Clean up
docker system prune -a --volumes

# Check disk usage
docker system df
```

### Runtime Issues

**Problem:** Import errors
```bash
# Check Python path
docker run --rm jlaw-forensics:latest python -c "import sys; print(sys.path)"

# Verify installation
docker run --rm jlaw-forensics:latest pip list | grep forensics
```

**Problem:** Permission errors
```bash
# Check file permissions
docker run --rm -it jlaw-forensics:latest ls -la /var/forensic/worm

# Fix permissions
docker run --rm -it --user root jlaw-forensics:latest chown -R forensic:forensic /var/forensic
```

**Problem:** Memory issues
```bash
# Increase memory limit
docker run --rm --memory=4g jlaw-forensics:latest investigate ...

# Or in compose
services:
  jlaw-forensics:
    mem_limit: 4g
```

---

## Performance Optimization

### Multi-Stage Build

```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY src/ ./src/
ENV PATH=/root/.local/bin:$PATH
```

### Layer Caching

```dockerfile
# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then copy code (changes more frequently)
COPY src/ ./src/
COPY jlaw_forensics.py .
```

### Build Args

```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

ARG ENABLE_GPU=false
RUN if [ "$ENABLE_GPU" = "true" ]; then \
    pip install torch --index-url https://download.pytorch.org/whl/cu118; \
    fi
```

```bash
# Build with GPU support
docker build --build-arg ENABLE_GPU=true -t jlaw-forensics:gpu .
```

---

## Production Checklist

### Pre-Deployment
- [ ] Set proper environment variables
- [ ] Configure storage backend (AWS/Azure)
- [ ] Set up secrets management
- [ ] Configure volume mounts
- [ ] Set resource limits
- [ ] Enable health checks
- [ ] Configure logging

### Deployment
- [ ] Build image: `docker build -t jlaw-forensics:latest .`
- [ ] Test locally: `docker run --rm jlaw-forensics:latest verify`
- [ ] Push to registry
- [ ] Deploy to production
- [ ] Verify health: `docker ps --filter health=healthy`
- [ ] Check logs: `docker logs jlaw-forensics`

### Post-Deployment
- [ ] Monitor resource usage
- [ ] Check integrity: Run `verify` command
- [ ] Set up backup procedures
- [ ] Configure alerting
- [ ] Document deployment

---

## Commands Reference

```bash
# Build
docker build -t jlaw-forensics:latest .

# Run
docker run --rm jlaw-forensics:latest [command] [options]

# Compose
docker-compose up -d          # Start services
docker-compose down           # Stop services
docker-compose logs -f        # View logs
docker-compose ps             # List services
docker-compose restart        # Restart services

# Maintenance
docker system prune -a        # Clean up
docker volume ls              # List volumes
docker network ls             # List networks
docker exec -it [container] /bin/bash  # Shell access
```

---

## Support

### Documentation
- Dockerfile: Production-ready container definition
- docker-compose.yml: Multi-service orchestration
- requirements.txt: Python dependencies
- JLAW_CLI_README.md: CLI usage guide
- FORENSIC_SYSTEM_FINAL.md: Complete system overview

### Logs
- Container logs: `docker logs jlaw-forensics`
- Application logs: `/app/logs/forensic_YYYYMMDD.log`
- Compose logs: `docker-compose logs`

### Debugging
```bash
# Interactive shell
docker run -it --rm jlaw-forensics:latest /bin/bash

# Check imports
docker run --rm jlaw-forensics:latest python -c "from src.forensics import *"

# Run verification
docker run --rm jlaw-forensics:latest verify
```

---

## File Locations

- `Dockerfile` - Container definition
- `docker-compose.yml` - Multi-service orchestration
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (create this)
- `DOCKER_DEPLOYMENT.md` - This guide

## Status
✅ **PRODUCTION READY**

## Last Updated
November 18, 2025

