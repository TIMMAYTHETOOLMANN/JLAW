"""
MCP Forensics Backend API
FastAPI implementation of the JARVIS:LAW Forensic Analysis System
"""

import logging
import os
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

# Import unified forensic system
try:
    from forensic_output_generator import ForensicOutputGenerator
    from unified_forensic_system import ForensicDatabase, ForensicInvestigator

    FORENSICS_AVAILABLE = True
    FORENSICS_MODE = "full"
except ImportError as e:
    logging.warning(f"Full forensic system not available: {e}")
    try:
        from simple_forensics import SimpleForensicInvestigator

        ForensicInvestigator = SimpleForensicInvestigator
        FORENSICS_AVAILABLE = True
        FORENSICS_MODE = "simple"
        logging.info("Using simplified forensic system for testing")
    except ImportError:
        FORENSICS_AVAILABLE = False
        FORENSICS_MODE = "none"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("MCP_FORENSICS_API")

# Initialize FastAPI app
app = FastAPI(
    title="MCP Forensics Backend",
    version="1.0.0",
    description="Advanced Forensic Analysis System for SEC Filings",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize forensic system
investigator = None
output_generator = None
if FORENSICS_AVAILABLE:
    try:
        investigator = ForensicInvestigator(db_path="forensic_evidence.db")
        if FORENSICS_MODE == "full":
            output_generator = ForensicOutputGenerator()
        logger.info(f"Forensic system initialized successfully (mode: {FORENSICS_MODE})")
    except Exception as e:
        logger.error(f"Failed to initialize forensic system: {e}")
        investigator = None

# Global state for investigations
current_investigation = None
investigation_running = False


# Request/Response Models
class CompanySearchRequest(BaseModel):
    query: str


class InvestigationRequest(BaseModel):
    cik: str
    years_back: int = 3
    forms: List[str] = ["10-K", "10-Q", "8-K"]


class CompanySearchResponse(BaseModel):
    cik: str
    name: str
    ticker: str


# Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "MCP Forensics Backend API",
        "version": "1.0.0",
        "status": "operational",
        "forensics_available": FORENSICS_AVAILABLE,
        "endpoints": {
            "health": "/health",
            "search": "/api/search_company",
            "investigate": "/api/start_investigation",
            "status": "/api/investigation_status",
            "results": "/api/investigation_results",
            "high_risk": "/api/high_risk_companies",
            "stats": "/api/database_stats",
            "output_files": "/api/output_files",
            "download": "/api/download/{file_type}",
            "download_all": "/api/download_all",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mcp-forensics-backend",
        "timestamp": datetime.utcnow().isoformat(),
        "forensics_available": FORENSICS_AVAILABLE,
        "forensics_mode": FORENSICS_MODE,
        "investigator_ready": investigator is not None,
    }


@app.post("/api/search_company")
async def search_company(request: CompanySearchRequest):
    """Search for company by ticker or name"""
    query = request.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Query required")

    # Simple ticker-to-CIK mapping (in production, use SEC API)
    ticker_to_cik = {
        "TSLA": "0001318605",
        "AAPL": "0000320193",
        "MSFT": "0000789019",
        "GOOGL": "0001652044",
        "AMZN": "0001018724",
        "META": "0001326801",
        "NVDA": "0001045810",
        "NFLX": "0001065280",
        "NIKE": "0000320187",
        "NKE": "0000320187",
        "DIS": "0001001039",
    }

    # Check if it's a ticker
    cik = ticker_to_cik.get(query.upper())

    # Or if it's already a CIK
    if not cik and query.isdigit():
        cik = query.zfill(10)

    if not cik:
        raise HTTPException(status_code=404, detail=f"Company not found: {query}")

    return {"cik": cik, "name": query.upper(), "ticker": query.upper()}


@app.post("/api/start_investigation")
async def start_investigation(request: InvestigationRequest, background_tasks: BackgroundTasks):
    """Start forensic investigation for a company"""
    global current_investigation, investigation_running

    if not FORENSICS_AVAILABLE or investigator is None:
        raise HTTPException(status_code=503, detail="Forensic system not available")

    if investigation_running:
        raise HTTPException(status_code=409, detail="Investigation already in progress")

    try:
        investigation_running = True
        logger.info(f"Starting investigation for CIK {request.cik}")

        # Run investigation synchronously (could be async in production)
        results = await investigator.investigate_company(
            cik=request.cik, years_back=request.years_back, forms=request.forms
        )

        current_investigation = results
        investigation_running = False

        return {
            "status": "completed",
            "investigation_id": results.get("investigation_id"),
            "risk_score": results.get("risk_score", 0.0),
            "risk_level": results.get("risk_level", "UNKNOWN"),
            "fraud_indicators_count": len(results.get("fraud_indicators", [])),
            "filings_analyzed": results.get("filings_analyzed", 0),
            "duration": results.get("duration", 0.0),
        }

    except Exception as e:
        investigation_running = False
        logger.error(f"Investigation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/investigation_status")
async def investigation_status():
    """Get current investigation status"""
    return {"running": investigation_running, "has_results": current_investigation is not None}


@app.get("/api/investigation_results")
async def investigation_results():
    """Get detailed investigation results"""
    if current_investigation is None:
        raise HTTPException(status_code=404, detail="No investigation results available")

    return current_investigation


@app.get("/api/high_risk_companies")
async def high_risk_companies(threshold: float = 0.7):
    """Get companies with high risk scores"""
    if not FORENSICS_AVAILABLE or investigator is None:
        raise HTTPException(status_code=503, detail="Forensic system not available")

    try:
        # Query database for high-risk companies
        companies = investigator.db.get_high_risk_companies(threshold)
        return {"companies": companies, "threshold": threshold}
    except Exception as e:
        logger.error(f"Failed to get high risk companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/database_stats")
async def database_stats():
    """Get database statistics"""
    if not FORENSICS_AVAILABLE or investigator is None:
        raise HTTPException(status_code=503, detail="Forensic system not available")

    try:
        stats = investigator.db.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/output_files")
async def list_output_files():
    """List available output files for current investigation"""
    if current_investigation is None:
        raise HTTPException(status_code=404, detail="No investigation results available")
    
    investigation_id = current_investigation.get("investigation_id", "unknown")
    
    # Generate list of output formats
    files = [
        {
            "name": f"{investigation_id}_report.json",
            "type": "json",
            "description": "Complete investigation data in JSON format",
            "size": "~50KB",
            "icon": "file-text"
        },
        {
            "name": f"{investigation_id}_summary.txt",
            "type": "txt",
            "description": "Executive summary in plain text",
            "size": "~5KB",
            "icon": "file"
        },
        {
            "name": f"{investigation_id}_findings.csv",
            "type": "csv",
            "description": "Fraud indicators in CSV format",
            "size": "~10KB",
            "icon": "table"
        },
        {
            "name": f"{investigation_id}_legal.pdf",
            "type": "pdf",
            "description": "Legal compliance report (PDF)",
            "size": "~100KB",
            "icon": "file-text"
        },
        {
            "name": f"{investigation_id}_evidence.html",
            "type": "html",
            "description": "Interactive evidence viewer",
            "size": "~75KB",
            "icon": "code"
        }
    ]
    
    return {"files": files, "investigation_id": investigation_id}


@app.get("/api/download/{file_type}")
async def download_file(file_type: str):
    """Download a specific output file type"""
    if current_investigation is None:
        raise HTTPException(status_code=404, detail="No investigation results available")
    
    investigation_id = current_investigation.get("investigation_id", "unknown")
    
    if file_type == "json":
        # Return JSON data
        import json
        content = json.dumps(current_investigation, indent=2)
        return StreamingResponse(
            BytesIO(content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={investigation_id}_report.json"}
        )
    
    elif file_type == "txt":
        # Generate text summary
        content = f"""JARVIS:LAW FORENSIC INVESTIGATION REPORT
{"="*60}

Investigation ID: {investigation_id}
Company CIK: {current_investigation.get('cik', 'N/A')}
Analysis Date: {current_investigation.get('timestamp', 'N/A')}

EXECUTIVE SUMMARY
{"-"*60}
{current_investigation.get('executive_summary', 'N/A')}

RISK ASSESSMENT
{"-"*60}
Risk Score: {current_investigation.get('risk_score', 'N/A')}/1.0
Risk Level: {current_investigation.get('risk_level', 'N/A')}
Filings Analyzed: {current_investigation.get('filings_analyzed', 'N/A')}

FRAUD INDICATORS
{"-"*60}
"""
        for indicator in current_investigation.get('fraud_indicators', []):
            content += f"\n• {indicator.get('type', 'N/A')}: {indicator.get('description', 'N/A')}\n"
            content += f"  Severity: {indicator.get('severity', 'N/A')}\n"
        
        content += f"""
LEGAL EXPOSURE
{"-"*60}
Criminal: {', '.join(current_investigation.get('criminal_exposure', []))}
Civil: {', '.join(current_investigation.get('civil_exposure', []))}

INVESTIGATION DETAILS
{"-"*60}
Duration: {current_investigation.get('duration', 'N/A')} seconds
Status: {current_investigation.get('status', 'N/A')}

{"="*60}
Report generated by JARVIS:LAW Forensic Analysis System
"""
        return StreamingResponse(
            BytesIO(content.encode()),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={investigation_id}_summary.txt"}
        )
    
    elif file_type == "csv":
        # Generate CSV of fraud indicators
        content = "Type,Severity,Description,Count\n"
        for indicator in current_investigation.get('fraud_indicators', []):
            content += f"\"{indicator.get('type', '')}\",{indicator.get('severity', 0)},\"{indicator.get('description', '')}\",{indicator.get('count', 0)}\n"
        
        return StreamingResponse(
            BytesIO(content.encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={investigation_id}_findings.csv"}
        )
    
    elif file_type == "html":
        # Generate HTML evidence viewer
        content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investigation {investigation_id}</title>
    <style>
        body {{ font-family: monospace; background: #0a0a0a; color: #00ff00; padding: 20px; }}
        .header {{ background: #1a1a1a; padding: 20px; border-left: 4px solid #00ff00; }}
        .section {{ margin: 20px 0; padding: 15px; background: #1a1a1a; }}
        .indicator {{ background: #2a1a1a; padding: 10px; margin: 10px 0; border-left: 3px solid #ff0000; }}
        .risk-high {{ color: #ff0000; }}
        .risk-medium {{ color: #ffaa00; }}
        .risk-low {{ color: #00ff00; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>JARVIS:LAW Forensic Investigation</h1>
        <p>Investigation ID: {investigation_id}</p>
        <p>CIK: {current_investigation.get('cik', 'N/A')}</p>
    </div>
    
    <div class="section">
        <h2>Risk Assessment</h2>
        <p>Risk Score: <span class="risk-{current_investigation.get('risk_level', 'low').lower()}">{current_investigation.get('risk_score', 'N/A')}</span></p>
        <p>Risk Level: {current_investigation.get('risk_level', 'N/A')}</p>
    </div>
    
    <div class="section">
        <h2>Fraud Indicators</h2>
"""
        for indicator in current_investigation.get('fraud_indicators', []):
            content += f"""
        <div class="indicator">
            <strong>{indicator.get('type', 'N/A')}</strong><br>
            Severity: {indicator.get('severity', 'N/A')}<br>
            Description: {indicator.get('description', 'N/A')}<br>
            Count: {indicator.get('count', 'N/A')}
        </div>
"""
        content += """
    </div>
    
    <div class="section">
        <h2>Executive Summary</h2>
        <p>{}</p>
    </div>
</body>
</html>
""".format(current_investigation.get('executive_summary', 'N/A'))
        
        return StreamingResponse(
            BytesIO(content.encode()),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={investigation_id}_evidence.html"}
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")


@app.get("/api/download_all")
async def download_all_files():
    """Download all output files as a ZIP archive"""
    if current_investigation is None:
        raise HTTPException(status_code=404, detail="No investigation results available")
    
    investigation_id = current_investigation.get("investigation_id", "unknown")
    
    # Create ZIP file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add JSON report
        import json
        json_content = json.dumps(current_investigation, indent=2)
        zip_file.writestr(f"{investigation_id}_report.json", json_content)
        
        # Add text summary (reuse logic from txt endpoint)
        txt_content = f"""JARVIS:LAW FORENSIC INVESTIGATION REPORT
{"="*60}

Investigation ID: {investigation_id}
Company CIK: {current_investigation.get('cik', 'N/A')}
Analysis Date: {current_investigation.get('timestamp', 'N/A')}

EXECUTIVE SUMMARY
{"-"*60}
{current_investigation.get('executive_summary', 'N/A')}

RISK ASSESSMENT
{"-"*60}
Risk Score: {current_investigation.get('risk_score', 'N/A')}/1.0
Risk Level: {current_investigation.get('risk_level', 'N/A')}
Filings Analyzed: {current_investigation.get('filings_analyzed', 'N/A')}
"""
        zip_file.writestr(f"{investigation_id}_summary.txt", txt_content)
        
        # Add CSV
        csv_content = "Type,Severity,Description,Count\n"
        for indicator in current_investigation.get('fraud_indicators', []):
            csv_content += f"\"{indicator.get('type', '')}\",{indicator.get('severity', 0)},\"{indicator.get('description', '')}\",{indicator.get('count', 0)}\n"
        zip_file.writestr(f"{investigation_id}_findings.csv", csv_content)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={investigation_id}_complete.zip"}
    )


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("MCP Forensics Backend starting...")
    if FORENSICS_AVAILABLE:
        logger.info("✓ Forensic system available")
    else:
        logger.warning("⚠ Forensic system not available")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("MCP Forensics Backend shutting down...")
