# MCP Forensics System - Deployment Guide

## Quick Start

### Local Development

#### Start Backend
```bash
cd mcp_forensics_backend
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

#### Start Frontend
```bash
cd mcp_forensics_frontend
python serve.py
```

### Docker Deployment
```bash
docker-compose up -d
```

### Access
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Testing

1. Open http://localhost:3000
2. Search company (e.g., "NKE")
3. Run forensic analysis
4. Review results
