# MCP Forensics System - Quick Deploy Guide

## Start System

### Backend
```bash
cd mcp_forensics_backend
uv run uvicorn app:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd mcp_forensics_frontend
python serve.py
```

Access: http://localhost:3000

## Test
1. Enter "NKE" 
2. Click search
3. Run analysis
4. View results

## Status
✅ All systems operational
