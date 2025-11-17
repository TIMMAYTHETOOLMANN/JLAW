"""
MCP Forensics Backend API
FastAPI implementation of the JARVIS:LAW Forensic Analysis System
"""

import logging
from datetime import datetime
from typing import List

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
