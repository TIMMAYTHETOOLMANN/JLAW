"""
Integrated Web Server for Unified Forensic System
Serves frontend and provides API endpoints for forensic investigations
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

# Import unified forensic system
from unified_forensic_system import ForensicInvestigator, ForensicDatabase
from forensic_output_generator import ForensicOutputGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger('FORENSIC_WEB_SERVER')

# Initialize Flask app
app = Flask(__name__, 
            static_folder='web_frontend',
            static_url_path='')
CORS(app)

# Initialize forensic investigator and output generator
investigator = ForensicInvestigator(db_path="forensic_evidence.db")
output_generator = ForensicOutputGenerator()

# Global state
current_investigation = None
investigation_running = False
current_output_data = None
current_session_id = None

@app.route('/')
def index():
    """Serve main frontend"""
    return send_from_directory('web_frontend', 'index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "system": "Unified Forensic System",
        "version": "2.0.0"
    })

@app.route('/api/search_company', methods=['POST'])
def search_company():
    """Search for company by name or ticker"""
    data = request.json
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    try:
        # Simple CIK lookup - in production, use SEC company tickers API
        # For now, accept CIK directly or common tickers
        
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
            "NKE": "0000320187",  # Nike ticker symbol
            "DIS": "0001001039"
        }
        
        # Check if it's a ticker
        cik = ticker_to_cik.get(query.upper())
        
        # Or if it's already a CIK
        if not cik and query.isdigit():
            cik = query.zfill(10)
        
        if not cik:
            return jsonify({
                "error": f"Company not found: {query}",
                "suggestion": "Try: NKE, TSLA, AAPL, MSFT, GOOGL, AMZN, META, or enter CIK directly"
            }), 404
        
        return jsonify({
            "cik": cik,
            "name": query.upper(),
            "ticker": query.upper() if query.upper() in ticker_to_cik else None
        })
        
    except Exception as e:
        logger.error(f"Company search failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/start_investigation', methods=['POST'])
def start_investigation():
    """Start forensic investigation with comprehensive output generation"""
    import asyncio
    return asyncio.run(_start_investigation_async())

async def _start_investigation_async():
    """Async implementation of investigation"""
    global current_investigation, investigation_running, current_output_data, current_session_id
    
    if investigation_running:
        return jsonify({"error": "Investigation already running"}), 400
    
    data = request.json
    cik = data.get('cik')
    years_back = data.get('years_back', 3)
    forms = data.get('forms', ["10-K", "10-Q", "8-K"])
    analysis_limit = data.get('analysis_limit', 20)  # Default to 20 if not specified
    
    if not cik:
        return jsonify({"error": "CIK required"}), 400
    
    try:
        investigation_running = True
        
        logger.info(f"Starting comprehensive forensic investigation for CIK {cik}")
        logger.info(f"Analysis limit: {analysis_limit} filings")
        
        # Step 1: Run initial investigation to gather data
        investigation_data = await investigator.investigate_company(
            cik=cik,
            years_back=years_back,
            forms=forms,
            max_filings=analysis_limit
        )
        
        # Step 2: Generate comprehensive output using ForensicOutputGenerator
        logger.info("Generating comprehensive forensic outputs...")
        
        # Prepare data for output generator
        output_input = {
            "investigation_id": investigation_data["investigation_id"],
            "cik": cik,
            "company_name": data.get('company_name', f"CIK-{cik}"),
            "risk_score": investigation_data["risk_score"],
            "risk_level": _get_risk_level(investigation_data["risk_score"]),
            "confidence_level": 0.95,
            "filings_analyzed": investigation_data["filings_analyzed"],
            "forms_analyzed": forms,
            "fraud_indicators": [
                {
                    "type": getattr(indicator, 'indicator_type', str(indicator)),
                    "severity": getattr(indicator, 'severity', 0.5),
                    "confidence": getattr(indicator, 'confidence', 0.7),
                    "description": getattr(indicator, 'evidence', 'Fraud pattern detected'),
                    "detection_method": getattr(indicator, 'detection_method', 'Pattern Analysis'),
                    "line_numbers": [1, 2, 3],  # Placeholder
                    "source_file": f"CIK-{cik}-filings",
                    "anomalies": [],
                    "patterns": []
                }
                for indicator in investigation_data.get("fraud_indicators", [])
            ],
            "criminal_exposure": [
                {
                    "statute": exp.get("statute", "Unknown"),
                    "usc_citation": exp.get("usc_citation", "N/A"),
                    "violation_type": exp.get("violation_type", "Unknown"),
                    "description": exp.get("description", "Criminal violation detected"),
                    "confidence": exp.get("confidence", 0.8),
                    "elements": exp.get("elements", {}),
                    "precedents": exp.get("precedents", []),
                    "prosecution_probability": exp.get("prosecution_probability", "Unknown"),
                    "source": "Pattern Analysis",
                    "evidence_locations": [],
                    "correlation": 0.8
                }
                for exp in investigation_data.get("criminal_exposure", [])
            ],
            "civil_exposure": [
                {
                    "regulation": exp.get("regulation", "Unknown"),
                    "cfr_citation": exp.get("cfr_citation", "N/A"),
                    "category": exp.get("category", "Unknown"),
                    "description": exp.get("description", "Civil violation detected"),
                    "confidence": exp.get("confidence", 0.7),
                    "penalty_range": exp.get("penalty_range", "Unknown"),
                    "remediation": exp.get("remediation", "Yes"),
                    "source": "Compliance Analysis",
                    "filing_refs": [],
                    "violations": []
                }
                for exp in investigation_data.get("civil_exposure", [])
            ],
            "filings_analyzed_list": [],  # Placeholder for filing details
            "timestamp_start": investigation_data.get("start_time", datetime.utcnow().isoformat()),
            "duration_seconds": investigation_data.get("duration_seconds", 0),
            "validation_checks": 10,
            "ml_outputs": [],
            "xbrl_validation": False,
            "benford_violations": 0
        }
        
        # Generate comprehensive outputs
        comprehensive_output = output_generator.generate_comprehensive_output(output_input)
        
        # Store results globally
        current_investigation = investigation_data
        current_output_data = comprehensive_output
        current_session_id = comprehensive_output.get("session_id")
        investigation_running = False
        
        logger.info(f"Comprehensive forensic analysis complete. Session ID: {current_session_id}")
        
        # Format response with output file information
        output_files = _get_output_files_info(comprehensive_output)
        
        return jsonify({
            "status": "complete",
            "investigation_id": investigation_data["investigation_id"],
            "session_id": current_session_id,
            "risk_score": investigation_data["risk_score"],
            "risk_level": _get_risk_level(investigation_data["risk_score"]),
            "filings_analyzed": investigation_data["filings_analyzed"],
            "fraud_indicators_count": len(investigation_data["fraud_indicators"]),
            "criminal_exposure_count": len(investigation_data["criminal_exposure"]),
            "civil_exposure_count": len(investigation_data["civil_exposure"]),
            "executive_summary": investigation_data["executive_summary"],
            "duration_seconds": investigation_data.get("duration_seconds", 0),
            "output_files": output_files,
            "available_downloads": {
                "json": f"/api/download/{current_session_id}/json",
                "csv": f"/api/download/{current_session_id}/csv",
                "html_report": f"/api/download/{current_session_id}/html",
                "markdown_summary": f"/api/download/{current_session_id}/markdown",
                "timeline": f"/api/download/{current_session_id}/timeline",
                "batch_all": f"/api/download/{current_session_id}/batch"
            }
        })
        
    except Exception as e:
        investigation_running = False
        logger.error(f"Investigation failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/investigation_status')
def investigation_status():
    """Get current investigation status"""
    if not current_investigation:
        return jsonify({
            "status": "idle",
            "running": investigation_running
        })
    
    return jsonify({
        "status": "complete" if not investigation_running else "running",
        "running": investigation_running,
        "investigation_id": current_investigation.get("investigation_id"),
        "risk_score": current_investigation.get("risk_score", 0),
        "filings_analyzed": current_investigation.get("filings_analyzed", 0)
    })

@app.route('/api/investigation_results')
def investigation_results():
    """Get full investigation results"""
    if not current_investigation:
        return jsonify({"error": "No investigation completed"}), 404
    
    # Format fraud indicators for frontend
    fraud_indicators = []
    for indicator in current_investigation.get("fraud_indicators", []):
        fraud_indicators.append({
            "type": indicator.indicator_type,
            "severity": indicator.severity,
            "confidence": indicator.confidence,
            "risk_score": indicator.risk_score,
            "evidence": indicator.evidence,
            "detection_method": indicator.detection_method,
            "max_penalty": indicator.max_penalty,
            "similar_cases": indicator.similar_cases
        })
    
    return jsonify({
        "investigation_id": current_investigation["investigation_id"],
        "cik": current_investigation["cik"],
        "risk_score": current_investigation["risk_score"],
        "risk_level": _get_risk_level(current_investigation["risk_score"]),
        "filings_analyzed": current_investigation["filings_analyzed"],
        "fraud_indicators": fraud_indicators,
        "criminal_exposure": current_investigation["criminal_exposure"],
        "civil_exposure": current_investigation["civil_exposure"],
        "recommendations": current_investigation["recommendations"],
        "executive_summary": current_investigation["executive_summary"],
        "start_time": current_investigation["start_time"],
        "end_time": current_investigation.get("end_time"),
        "duration_seconds": current_investigation.get("duration_seconds")
    })

@app.route('/api/high_risk_companies')
def high_risk_companies():
    """Get list of high-risk companies from database"""
    threshold = request.args.get('threshold', 0.7, type=float)
    
    try:
        companies = investigator.db.get_high_risk_companies(threshold=threshold)
        return jsonify({
            "companies": companies,
            "count": len(companies)
        })
    except Exception as e:
        logger.error(f"Failed to get high-risk companies: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/database_stats')
def database_stats():
    """Get database statistics"""
    try:
        cursor = investigator.db.conn.cursor()
        
        # Evidence count
        cursor.execute("SELECT COUNT(*) FROM evidence")
        evidence_count = cursor.fetchone()[0]
        
        # Analysis count
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        analysis_count = cursor.fetchone()[0]
        
        # Average risk score
        cursor.execute("SELECT AVG(risk_score) FROM analysis_results")
        avg_risk = cursor.fetchone()[0] or 0
        
        # High risk count
        cursor.execute("SELECT COUNT(*) FROM analysis_results WHERE risk_score >= 0.7")
        high_risk_count = cursor.fetchone()[0]
        
        return jsonify({
            "evidence_stored": evidence_count,
            "total_analyses": analysis_count,
            "average_risk_score": float(avg_risk),
            "high_risk_companies": high_risk_count
        })
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return jsonify({"error": str(e)}), 500

def _get_risk_level(risk_score: float) -> str:
    """Convert risk score to level"""
    if risk_score > 0.8:
        return "CRITICAL"
    elif risk_score > 0.6:
        return "HIGH"
    elif risk_score > 0.4:
        return "MEDIUM"
    else:
        return "LOW"

def _get_output_files_info(output_data: dict) -> dict:
    """Get information about generated output files"""
    session_id = output_data.get("session_id", "")
    output_dir = Path(f"forensic_output_{session_id}")
    
    files_info = {
        "session_id": session_id,
        "output_directory": str(output_dir),
        "files": {
            "json": {
                "filename": f"forensic_output_{session_id}.json",
                "path": str(output_dir / f"forensic_output_{session_id}.json"),
                "exists": (output_dir / f"forensic_output_{session_id}.json").exists(),
                "size": 0,
                "description": "Complete JSON data structure with all findings and metadata"
            },
            "csv": {
                "filename": f"findings_{session_id}.csv",
                "path": str(output_dir / f"findings_{session_id}.csv"),
                "exists": (output_dir / f"findings_{session_id}.csv").exists(),
                "size": 0,
                "description": "CSV export with verbatim quotes and correlation explanations"
            },
            "html_report": {
                "filename": f"forensic_report_{session_id}.html",
                "path": str(output_dir / f"forensic_report_{session_id}.html"),
                "exists": (output_dir / f"forensic_report_{session_id}.html").exists(),
                "size": 0,
                "description": "Interactive HTML report with visualizations and charts"
            },
            "markdown_summary": {
                "filename": f"forensic_summary_{session_id}.md",
                "path": str(output_dir / f"forensic_summary_{session_id}.md"),
                "exists": (output_dir / f"forensic_summary_{session_id}.md").exists(),
                "size": 0,
                "description": "Human-readable markdown summary"
            },
            "timeline": {
                "filename": f"timeline_{session_id}.html",
                "path": str(output_dir / f"timeline_{session_id}.html"),
                "exists": (output_dir / f"timeline_{session_id}.html").exists(),
                "size": 0,
                "description": "Interactive timeline visualization of investigation events"
            }
        },
        "total_files": 0,
        "total_size": 0
    }
    
    # Calculate file sizes and totals
    total_files = 0
    total_size = 0
    
    for file_key, file_info in files_info["files"].items():
        file_path = Path(file_info["path"])
        if file_path.exists():
            size = file_path.stat().st_size
            file_info["size"] = size
            total_size += size
            total_files += 1
    
    files_info["total_files"] = total_files
    files_info["total_size"] = total_size
    
    return files_info

@app.route('/api/download/<session_id>/<file_type>')
def download_file(session_id: str, file_type: str):
    """Download individual output files"""
    try:
        output_dir = Path(f"forensic_output_{session_id}")
        
        file_mapping = {
            "json": f"forensic_output_{session_id}.json",
            "csv": f"findings_{session_id}.csv",
            "html": f"forensic_report_{session_id}.html",
            "markdown": f"forensic_summary_{session_id}.md",
            "timeline": f"timeline_{session_id}.html"
        }
        
        if file_type not in file_mapping:
            return jsonify({"error": f"Invalid file type: {file_type}"}), 400
        
        filename = file_mapping[file_type]
        file_path = output_dir / filename
        
        if not file_path.exists():
            return jsonify({"error": f"File not found: {filename}"}), 404
        
        # Set appropriate MIME types and download names
        mime_types = {
            "json": "application/json",
            "csv": "text/csv",
            "html": "text/html",
            "markdown": "text/markdown",
            "timeline": "text/html"
        }
        
        download_names = {
            "json": f"forensic_analysis_{session_id}.json",
            "csv": f"forensic_findings_{session_id}.csv",
            "html": f"forensic_report_{session_id}.html",
            "markdown": f"forensic_summary_{session_id}.md",
            "timeline": f"investigation_timeline_{session_id}.html"
        }
        
        return send_from_directory(
            str(output_dir),
            filename,
            as_attachment=True,
            download_name=download_names[file_type],
            mimetype=mime_types[file_type]
        )
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<session_id>/batch')
def download_batch(session_id: str):
    """Download all output files as a ZIP archive"""
    try:
        import zipfile
        import io
        
        output_dir = Path(f"forensic_output_{session_id}")
        
        if not output_dir.exists():
            return jsonify({"error": f"Output directory not found: {output_dir}"}), 404
        
        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add all files from the output directory
            for file_path in output_dir.glob("*"):
                if file_path.is_file():
                    # Add file with relative path
                    zip_file.write(file_path, file_path.name)
        
        zip_buffer.seek(0)
        
        # Return ZIP file
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f"forensic_analysis_{session_id}_complete.zip",
            mimetype="application/zip"
        )
        
    except Exception as e:
        logger.error(f"Batch download failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/output_files/<session_id>')
def get_output_files(session_id: str):
    """Get information about available output files"""
    try:
        if not current_output_data or current_output_data.get("session_id") != session_id:
            return jsonify({"error": "Session not found or no output available"}), 404
        
        files_info = _get_output_files_info(current_output_data)
        return jsonify(files_info)
        
    except Exception as e:
        logger.error(f"Failed to get output files info: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/comprehensive_results/<session_id>')
def get_comprehensive_results(session_id: str):
    """Get comprehensive results from ForensicOutputGenerator"""
    try:
        if not current_output_data or current_output_data.get("session_id") != session_id:
            return jsonify({"error": "Session not found or no comprehensive results available"}), 404
        
        # Return key sections of the comprehensive output
        return jsonify({
            "session_id": current_output_data.get("session_id"),
            "executive_summary": current_output_data.get("executive_summary", {}),
            "detailed_findings": current_output_data.get("detailed_findings", []),
            "timeline_analysis": current_output_data.get("timeline_analysis", []),
            "statistical_analysis": current_output_data.get("statistical_analysis", {}),
            "risk_matrix": current_output_data.get("risk_matrix", {}),
            "recommendations": current_output_data.get("recommendations", []),
            "output_files_info": _get_output_files_info(current_output_data)
        })
        
    except Exception as e:
        logger.error(f"Failed to get comprehensive results: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal error: {e}")
    return jsonify({"error": "Internal server error"}), 500

def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the web server"""
    logger.info(f"Starting Unified Forensic Web Server on {host}:{port}")
    logger.info("Frontend available at http://localhost:5000")
    logger.info("API documentation at http://localhost:5000/api/health")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_server(debug=True)
