# Docker Build Troubleshooting Guide - JARVIS:LAW

## Issue: pip install failed during Docker build

### Root Cause
The error "process '/bin/sh -c pip install --no-cache-dir -r requirements.txt' did not complete successfully: exit code: 1" typically occurs due to:

1. **Conflicting package versions** - Multiple requirements files with incompatible versions
2. **Missing system dependencies** - Some Python packages need C/C++ compilers
3. **Network/timeout issues** - PyPI downloads timing out
4. **Memory constraints** - Docker build running out of memory

### Solutions Applied

#### 1. Consolidated Requirements File
Created `requirements_docker.txt` - a single, conflict-free requirements file specifically for Docker builds.

#### 2. Enhanced Dockerfile
Updated Dockerfile with:
- Proper system dependencies (gcc, g++, build-essential)
- Upgraded pip/setuptools/wheel before installing packages
- Environment variables to optimize pip behavior
- Staged installation (core packages first, then extras)

#### 3. Simplified Alternative
Created `Dockerfile.simple` for minimal, reliable builds.

### Quick Fix Commands

#### Option 1: Use the fixed Dockerfile (recommended)
```bash
cd C:\Users\timot\IdeaProjects\openai-agents-python\examples\jarvis_law_sec_auditor
docker build -t jarvis-law-forensic:latest -f Dockerfile .
```

#### Option 2: Use the simplified Dockerfile
```bash
cd C:\Users\timot\IdeaProjects\openai-agents-python\examples\jarvis_law_sec_auditor
docker build -t jarvis-law-forensic:latest -f Dockerfile.simple .
```

#### Option 3: Build with docker-compose
```bash
cd C:\Users\timot\IdeaProjects\openai-agents-python\examples\jarvis_law_sec_auditor
docker-compose build --no-cache forensic_app
docker-compose up -d
```

### If Build Still Fails

#### Increase Docker Memory
1. Open Docker Desktop
2. Settings → Resources → Memory
3. Increase to at least 4GB (8GB recommended)
4. Apply & Restart

#### Clear Docker Cache
```bash
docker system prune -a --volumes
docker builder prune -a
```

#### Build with Verbose Output
```bash
docker build --progress=plain --no-cache -t jarvis-law-forensic:latest .
```

### Alternative: Run Without Docker

If Docker continues to have issues, run the application directly:

```bash
cd C:\Users\timot\IdeaProjects\openai-agents-python\examples\jarvis_law_sec_auditor

# Install requirements locally
pip install -r requirements_unified.txt
pip install waitress

# Run production server
python production_waitress.py
```

The START_PRODUCTION.bat script already does this automatically if you run it.

### Files Modified
- ✅ `Dockerfile` - Enhanced with better dependency management
- ✅ `requirements_docker.txt` - Consolidated requirements file
- ✅ `Dockerfile.simple` - Minimal fallback option
- ✅ `DOCKER_TROUBLESHOOTING.md` - This guide

### Next Steps
1. Try building with the fixed Dockerfile
2. If that fails, use Dockerfile.simple
3. If still issues, run locally without Docker (START_PRODUCTION.bat handles this)

### Status: RESOLVED ✓
The Docker build issue has been successfully fixed!

**Build completed successfully on:** November 15, 2025

**Solution Applied:**
- Simplified Dockerfile with staged package installation
- Pinned specific package versions to avoid conflicts
- Installed packages in logical groups to prevent timeout
- Used `--no-install-recommends` for system packages to reduce image size

**Build Output:**
```
[+] Building 0.8s (16/16) FINISHED
 => [11/11] RUN mkdir -p forensic_exports web_frontend
 => exporting to image
 => naming to docker.io/library/jarvis-law-forensic:latest
```

**Image Details:**
- Name: `jarvis-law-forensic:latest`
- Base: `python:3.11-slim`
- Status: ✅ Built successfully

**Next Steps:**
1. Start the full stack: `docker-compose up -d`
2. Or run just the app: `docker run -p 5000:5000 jarvis-law-forensic:latest`
3. Or use the production script: `START_PRODUCTION.bat`

