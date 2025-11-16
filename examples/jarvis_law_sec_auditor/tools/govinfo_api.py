"""
JARVIS:LAW Black Site Protocol - GovInfo API Integration
JSON-level metadata scraping for enhanced precision
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

import httpx

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import Config
    GOVINFO_API_KEY = Config.GOVINFO_API_KEY
except ImportError:
    import os
    GOVINFO_API_KEY = os.getenv("GOVINFO_API_KEY", "")

GOVINFO_BASE_URL = "https://api.govinfo.gov"


def get_filing_metadata(doc_id: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve filing metadata from GovInfo API.
    
    Args:
        doc_id: GovInfo document package ID
        api_key: GovInfo API key (defaults to GOVINFO_API_KEY from config)
        
    Returns:
        Filing metadata dictionary
        
    Example:
        >>> metadata = get_filing_metadata("CRPT-117hrpt169")
    """
    key = api_key or GOVINFO_API_KEY
    
    if not key:
        return {
            "error": "GOVINFO_API_KEY not set",
            "doc_id": doc_id,
            "status": "unauthorized"
        }
    
    headers = {"X-Api-Key": key}
    url = f"{GOVINFO_BASE_URL}/packages/{doc_id}/summary"
    
    try:
        response = httpx.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()
        
    except httpx.HTTPStatusError as e:
        return {
            "error": str(e),
            "doc_id": doc_id,
            "status": "failed",
            "status_code": e.response.status_code
        }
    except Exception as e:
        return {
            "error": str(e),
            "doc_id": doc_id,
            "status": "failed"
        }


def search_govinfo_documents(
    query: str,
    collection: str = "CRPT",
    page_size: int = 100,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search GovInfo documents.
    
    Args:
        query: Search query string
        collection: Document collection code (e.g., "CRPT" for Congressional Reports)
        page_size: Number of results per page
        api_key: GovInfo API key
        
    Returns:
        Search results dictionary
    """
    key = api_key or GOVINFO_API_KEY
    
    if not key:
        return {
            "error": "GOVINFO_API_KEY not set",
            "status": "unauthorized"
        }
    
    headers = {"X-Api-Key": key}
    url = f"{GOVINFO_BASE_URL}/search"
    params = {
        "query": query,
        "collection": collection,
        "pageSize": page_size
    }
    
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }


def get_document_download_url(doc_id: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Get direct download URL for a GovInfo document.
    
    Args:
        doc_id: GovInfo document package ID
        api_key: GovInfo API key
        
    Returns:
        Download URL or None
    """
    metadata = get_filing_metadata(doc_id, api_key)
    
    if "download" in metadata:
        return metadata["download"].get("txtLink") or metadata["download"].get("pdfLink")
    
    return None

