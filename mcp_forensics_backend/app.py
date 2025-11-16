from fastapi import FastAPI

app = FastAPI(title="MCP Forensics Backend", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "mcp-forensics-backend"}

@app.get("/")
async def root():
    return {"message": "MCP Forensics Backend API", "version": "1.0.0"}
