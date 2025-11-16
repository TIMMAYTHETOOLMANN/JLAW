"""
JARVIS:LAW Black Site Protocol - Utility Functions
Cryptographic evidence chain, archival, and logging
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import httpx

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import Config
    EVIDENCE_DIR = Config.EVIDENCE_CHAIN_DIR
    FILINGS_DIR = Config.SEC_FILINGS_ARCHIVE_DIR
    SEC_HEADERS = Config.get_sec_headers()
except ImportError:
    # Fallback if config not available
    EVIDENCE_DIR = Path("./memory/evidence_chain")
    FILINGS_DIR = Path("./memory/sec_filings_archive")
    SEC_HEADERS = {"User-Agent": "JarvisLAW/1.0 (forensics@domain.com)"}

# Ensure directories exist
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
FILINGS_DIR.mkdir(parents=True, exist_ok=True)

VIOLATIONS_LOG = EVIDENCE_DIR / "violations.jsonl"


def sha256_url(url: str) -> str:
    """
    Generate SHA-256 hash of source URL for cryptographic evidence integrity.
    
    Args:
        url: Source URL to hash
        
    Returns:
        SHA-256 hexdigest
    """
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


def sha256_content(content: str) -> str:
    """
    Generate SHA-256 hash of document content.
    
    Args:
        content: Document content to hash
        
    Returns:
        SHA-256 hexdigest (full 64 chars)
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def save_filing(url: str, filename: str) -> Dict[str, Any]:
    """
    Archive SEC filing locally with cryptographic hash.
    
    Args:
        url: Source URL of the filing
        filename: Target filename (e.g., "0000320187_4_2023-05-12.html")
        
    Returns:
        Evidence metadata dictionary
    """
    try:
        response = httpx.get(url, headers=SEC_HEADERS, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        content = response.text
        
        # Generate evidence chain metadata
        url_hash = sha256_url(url)
        content_hash = sha256_content(content)
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Save filing to archive
        filepath = FILINGS_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Generate evidence metadata
        evidence = {
            "url": url,
            "url_hash": url_hash,
            "content_hash": content_hash,
            "archived_path": str(filepath),
            "filename": filename,
            "timestamp_utc": timestamp,
            "size_bytes": len(content),
            "status": "archived"
        }
        
        # Save metadata
        metadata_path = EVIDENCE_DIR / f"{filename}.meta.json"
        with open(metadata_path, 'w') as f:
            json.dump(evidence, f, indent=2)
        
        return evidence
        
    except Exception as e:
        return {
            "url": url,
            "filename": filename,
            "status": "failed",
            "error": str(e),
            "timestamp_utc": datetime.utcnow().isoformat() + "Z"
        }


def log_violation(violation_data: Dict[str, Any]) -> str:
    """
    Log detected violation to evidence chain with append-only JSONL format.
    
    Args:
        violation_data: Violation details including:
            - violation_detected: bool
            - hash: URL hash
            - source_url: Original filing URL
            - filing_meta: Filing metadata
            - evidence: Extracted evidence
            
    Returns:
        Log entry ID
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    log_entry = {
        "id": hashlib.sha256(f"{timestamp}:{violation_data.get('source_url', '')}".encode()).hexdigest()[:16],
        "timestamp_utc": timestamp,
        **violation_data
    }
    
    # Append to violations log (JSONL format)
    with open(VIOLATIONS_LOG, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    return log_entry["id"]


def get_violations_log() -> list[Dict[str, Any]]:
    """
    Retrieve all logged violations.
    
    Returns:
        List of violation entries
    """
    if not VIOLATIONS_LOG.exists():
        return []
    
    violations = []
    with open(VIOLATIONS_LOG, 'r') as f:
        for line in f:
            if line.strip():
                violations.append(json.loads(line))
    
    return violations


def export_evidence_chain(output_path: str = "evidence_chain_export.json") -> str:
    """
    Export complete evidence chain for legal/forensic review.
    
    Args:
        output_path: Output file path
        
    Returns:
        Path to exported file
    """
    violations = get_violations_log()
    
    export_data = {
        "export_timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "total_violations": len(violations),
        "violations": violations,
        "integrity": {
            "method": "SHA-256",
            "chain_hash": hashlib.sha256(json.dumps(violations, sort_keys=True).encode()).hexdigest()
        }
    }
    
    export_file = EVIDENCE_DIR / output_path
    with open(export_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    return str(export_file)

