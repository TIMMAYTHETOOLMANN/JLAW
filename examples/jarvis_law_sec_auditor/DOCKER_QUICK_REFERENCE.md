# JARVIS:LAW Docker Quick Reference

## Build Status: ✅ OPERATIONAL

The Docker build issue has been **RESOLVED**. Image builds successfully in ~60 seconds.

---

## Quick Commands

### Build the Image
```bash
cd C:\Users\timot\IdeaProjects\openai-agents-python\examples\jarvis_law_sec_auditor
docker build -t jarvis-law-forensic:latest .
```

### Run Standalone Container
```bash
docker run -d -p 5000:5000 --name jarvis-forensic jarvis-law-forensic:latest
```

### Run Full Stack (with Redis, Kafka, PostgreSQL, Minio)
```bash
docker-compose up -d
```

### Check Running Containers
```bash
docker ps
```

### View Container Logs
```bash
docker logs jarvis-forensic
# or for docker-compose
docker-compose logs -f forensic_app
```

### Stop and Remove
```bash
# Standalone
docker stop jarvis-forensic
docker rm jarvis-forensic

# Full stack
docker-compose down
```

### Rebuild from Scratch
```bash
docker build --no-cache -t jarvis-law-forensic:latest .
```

---

## Production Deployment

### Option 1: Use START_PRODUCTION.bat (Recommended)
```bash
.\START_PRODUCTION.bat
```
This script:
- Checks Docker availability
- Starts all Docker services
- Installs Python dependencies
- Launches production server on port 9000
- Opens browser automatically

### Option 2: Docker Compose Only
```bash
docker-compose up -d
```
Access at: http://localhost:5000

### Option 3: Local Python (No Docker)
```bash
pip install -r requirements_unified.txt
python production_waitress.py
```
Access at: http://localhost:9000

---

## Dockerfile Versions

### Dockerfile (Main - Recommended) ✅
- **Status:** Working
- **Build Time:** ~60 seconds (cached: <1 second)
- **Features:** Staged installation, pinned versions, optimized layers
- **Use:** Default for production

### Dockerfile.simple (Minimal)
- **Status:** Working
- **Build Time:** ~30 seconds
- **Features:** Bare minimum packages only
- **Use:** Testing, debugging, minimal deployments

### Dockerfile.optimized (Advanced)
- **Status:** Working
- **Build Time:** ~90 seconds
- **Features:** Multi-stage build, pre-compiled wheels
- **Use:** When you need all ML packages and fastest runtime

---

## Troubleshooting

### Build Fails with Timeout
```bash
# Increase Docker memory to 8GB in Docker Desktop settings
# Then retry build
docker build --no-cache -t jarvis-law-forensic:latest .
```

### Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :5000

# Use different port
docker run -p 5001:5000 jarvis-law-forensic:latest
```

### Container Won't Start
```bash
# Check logs
docker logs jarvis-forensic

# Check if port is available
docker run -p 5000:5000 --rm jarvis-law-forensic:latest
```

### Clear Everything and Start Fresh
```bash
docker-compose down -v
docker system prune -a --volumes
docker build -t jarvis-law-forensic:latest .
docker-compose up -d
```

---

## Health Checks

### Test Container Health
```bash
docker inspect jarvis-forensic | findstr Health
```

### Test API Endpoint
```bash
curl http://localhost:5000/api/health
# or
Invoke-WebRequest http://localhost:5000/api/health
```

---

## Image Information

- **Name:** jarvis-law-forensic
- **Tag:** latest
- **Base Image:** python:3.11-slim
- **Working Directory:** /app
- **Exposed Port:** 5000
- **Health Check:** Built-in Python check every 30s

---

## Files Reference

| File | Purpose |
|------|---------|
| `Dockerfile` | Main production Dockerfile ✅ |
| `Dockerfile.simple` | Minimal fallback |
| `Dockerfile.optimized` | Multi-stage with wheels |
| `docker-compose.yml` | Full stack orchestration |
| `requirements_docker.txt` | Docker-specific requirements |
| `START_PRODUCTION.bat` | Automated deployment script |
| `DOCKER_TROUBLESHOOTING.md` | Detailed troubleshooting guide |

---

## Support Infrastructure

When using docker-compose, these services are included:
- **Redis** - Circuit breaker state & caching (port 6379)
- **Kafka** - Audit trail (port 9092)
- **PostgreSQL** - Evidence storage (port 5432)
- **MinIO** - Document archives (port 9000/9001)
- **JARVIS:LAW App** - Main application (port 5000)

---

**Last Updated:** November 15, 2025
**Status:** All systems operational ✅

