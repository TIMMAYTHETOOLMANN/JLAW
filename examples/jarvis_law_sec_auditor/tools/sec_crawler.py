"""
JARVIS:LAW Black Site Protocol - SEC Web Crawler Module
Live scraping of SEC.gov filings with cryptographic evidence chain
"""

import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import httpx
from bs4 import BeautifulSoup

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import Config
    SEC_BASE_URL = Config.SEC_BASE_URL
    REQUEST_DELAY = Config.SEC_REQUEST_DELAY_SECONDS
    SEC_HEADERS = Config.get_sec_headers()
except ImportError:
    # Fallback if config not available
    SEC_BASE_URL = "https://www.sec.gov"
    REQUEST_DELAY = 0.12
    SEC_HEADERS = {"User-Agent": "JarvisLAW/1.0 (forensics@domain.com)"}

from .utils import save_filing


SEC_BROWSE_URL = f"{SEC_BASE_URL}/cgi-bin/browse-edgar"
SEC_COMPANY_SEARCH_URL = f"{SEC_BASE_URL}/cgi-bin/browse-edgar"


def fetch_sec_filings_by_cik(
    cik: str,
    form_type: str,
    year_start: int,
    year_end: int,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch SEC filings from SEC.gov by CIK number and form type.
    
    Args:
        cik: Central Index Key (CIK) - company identifier
        form_type: SEC form type (e.g., "4", "10-K", "10-Q")
        year_start: Starting year for search
        year_end: Ending year for search
        limit: Maximum filings per year
        
    Returns:
        List of filing metadata dictionaries with:
            - title: Filing title
            - url: Direct URL to filing document
            - filing_date: ISO format date
            - year: Filing year
            - accession_number: SEC accession number
            - archived: Evidence chain metadata
    """
    filings = []
    
    for year in range(year_start, year_end + 1):
        print(f"[SEARCH] Scanning {form_type} filings for CIK {cik} - Year {year}...")
        
        params = {
            "action": "getcompany",
            "CIK": cik,
            "type": form_type,
            "dateb": f"{year}1231",
            "owner": "include",
            "count": str(limit),
            "output": "atom"
        }
        
        try:
            response = httpx.get(
                SEC_BROWSE_URL,
                params=params,
                headers=SEC_HEADERS,
                timeout=30.0,
                follow_redirects=True
            )
            response.raise_for_status()
            
            # Parse Atom feed
            soup = BeautifulSoup(response.text, 'xml')
            entries = soup.find_all('entry')
            
            print(f"  ?? Found {len(entries)} filings")
            
            for entry in entries:
                try:
                    title = entry.title.text.strip() if entry.title else "Unknown"
                    filing_url = entry.link['href'] if entry.link else None
                    filing_date = entry.updated.text[:10] if entry.updated else "Unknown"
                    
                    # Extract accession number from URL - try multiple patterns
                    accession_number = "Unknown"
                    if filing_url:
                        # Pattern 1: Standard format /0001234567-12-123456/
                        match = re.search(r'/(\d{10}-\d{2}-\d{6})/', filing_url)
                        if match:
                            accession_number = match.group(1)
                        else:
                            # Pattern 2: No hyphens /0001234567891234567/
                            match = re.search(r'/(\d{18,20})/', filing_url)
                            if match:
                                # Format as standard accession number
                                num = match.group(1)
                                accession_number = f"{num[:10]}-{num[10:12]}-{num[12:]}"
                            else:
                                # Pattern 3: Extract from filename in URL
                                match = re.search(r'/([^/]+)\.(htm|html|txt)$', filing_url)
                                if match:
                                    accession_number = match.group(1)
                    
                    if filing_url:
                        # Convert index page URL to full document URL
                        if "-index.htm" in filing_url:
                            # Fetch index page to find primary document
                            time.sleep(REQUEST_DELAY)
                            doc_url = extract_primary_document_url(filing_url, SEC_HEADERS)
                            filing_url = doc_url if doc_url else filing_url
                        
                        # Archive filing with evidence chain
                        # Determine file extension from URL
                        if filing_url.endswith('.xml'):
                            extension = '.xml'
                        elif filing_url.endswith('.htm') or filing_url.endswith('.html'):
                            extension = '.html'
                        else:
                            extension = '.txt'
                        
                        filename = f"{cik}_{form_type}_{filing_date}_{accession_number.replace('-', '')}{extension}"
                        
                        time.sleep(REQUEST_DELAY)  # Rate limiting
                        evidence = save_filing(filing_url, filename)
                        
                        filing_data = {
                            "title": title,
                            "url": filing_url,
                            "filing_date": filing_date,
                            "year": year,
                            "accession_number": accession_number,
                            "cik": cik,
                            "form_type": form_type,
                            "archived": evidence
                        }
                        
                        filings.append(filing_data)
                        print(f"  ?? [OK] {filing_date} | {accession_number}")
                        
                except Exception as e:
                    print(f"  ?? ? Error processing entry: {e}")
                    continue
            
        except Exception as e:
            print(f"  ?? ? Error fetching year {year}: {e}")
            continue
        
        time.sleep(REQUEST_DELAY)  # Rate limiting between years
    
    print(f"[OK] Total filings retrieved: {len(filings)}")
    return filings


def extract_primary_document_url(index_url: str, headers: Dict[str, str]) -> Optional[str]:
    """
    Extract primary document URL from SEC filing index page.
    For Form 4, returns XML source file, not HTML render.
    
    Args:
        index_url: URL to filing index page
        headers: HTTP headers
        
    Returns:
        URL to primary document (XML for Form 4) or None
    """
    try:
        response = httpx.get(index_url, headers=headers, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find primary document table
        table = soup.find('table', {'class': 'tableFile'})
        if table:
            # PRIORITY 1: Look for .xml file (Form 4 source)
            for row in table.find_all('tr')[1:]:  # Skip header
                cells = row.find_all('td')
                if len(cells) >= 3:
                    link = cells[2].find('a') if len(cells) > 2 else None
                    if link and 'href' in link.attrs:
                        doc_path = link['href']
                        # Prefer XML source for structured data
                        if doc_path.endswith('.xml'):
                            return f"{SEC_BASE_URL}{doc_path}" if not doc_path.startswith('http') else doc_path
            
            # FALLBACK: Get first non-exhibit document if no XML found
            for row in table.find_all('tr')[1:]:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    doc_type = cells[3].text.strip() if len(cells) > 3 else ""
                    if doc_type and not doc_type.startswith('EX-'):  # Skip exhibits
                        link = cells[2].find('a') if len(cells) > 2 else None
                        if link and 'href' in link.attrs:
                            doc_path = link['href']
                            return f"{SEC_BASE_URL}{doc_path}" if not doc_path.startswith('http') else doc_path
        
        return None
        
    except Exception as e:
        print(f"  ?? Warning: Could not extract primary doc: {e}")
        return None


def fetch_company_info_by_cik(cik: str) -> Dict[str, Any]:
    """
    Fetch company information by CIK.
    
    Args:
        cik: Central Index Key
        
    Returns:
        Company metadata dictionary
    """
    try:
        url = f"{SEC_BASE_URL}/cgi-bin/browse-edgar"
        params = {
            "action": "getcompany",
            "CIK": cik,
            "count": "1",
            "output": "atom"
        }
        
        response = httpx.get(url, params=params, headers=SEC_HEADERS, timeout=30.0)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'xml')
        company_info = soup.find('company-info')
        
        if company_info:
            return {
                "cik": cik,
                "company_name": company_info.find('conformed-name').text if company_info.find('conformed-name') else "Unknown",
                "sic": company_info.find('assigned-sic').text if company_info.find('assigned-sic') else "Unknown",
                "state": company_info.find('state').text if company_info.find('state') else "Unknown",
            }
        
        return {"cik": cik, "status": "not_found"}
        
    except Exception as e:
        return {"cik": cik, "error": str(e)}


def search_company_by_ticker(query: str) -> Optional[Dict[str, Any]]:
    """
    Search for company by ticker symbol, company name, or CIK.
    
    Args:
        query: Stock ticker (e.g., "NKE", "AAPL"), 
               company name (e.g., "Nike", "Apple Inc"),
               or CIK number (e.g., "0000320187")
        
    Returns:
        Dictionary with 'cik', 'name', and 'ticker' or None
    """
    try:
        # Clean input
        query = query.strip()
        
        # If query is already a CIK (all digits, possibly with leading zeros)
        if query.isdigit() or (query.startswith('0') and len(query) == 10):
            # Pad to 10 digits
            cik = query.zfill(10)
            company_info = fetch_company_info_by_cik(cik)
            if company_info.get('company_name'):
                return {
                    'cik': cik,
                    'name': company_info.get('company_name'),
                    'ticker': query
                }
        
        # Search by company name or ticker
        url = f"{SEC_BASE_URL}/cgi-bin/browse-edgar"
        params = {
            "company": query,
            "action": "getcompany",
            "count": "1",
            "output": "atom"
        }
        
        response = httpx.get(url, params=params, headers=SEC_HEADERS, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        
        # Parse XML response
        soup = BeautifulSoup(response.text, 'xml')
        
        # Look for company info in feed
        company_info = soup.find('company-info')
        if company_info:
            cik_elem = company_info.find('cik')
            name_elem = company_info.find('conformed-name')
            
            if cik_elem and name_elem:
                cik = cik_elem.text.strip().zfill(10)
                name = name_elem.text.strip()
                
                return {
                    'cik': cik,
                    'name': name,
                    'ticker': query.upper()
                }
        
        # Fallback: Try to extract from HTML response
        params['output'] = None  # Get HTML instead
        response = httpx.get(url, params=params, headers=SEC_HEADERS, timeout=30.0)
        response.raise_for_status()
        
        # Look for CIK in URL or page
        cik_match = re.search(r'CIK=(\d{10})', response.text)
        if cik_match:
            cik = cik_match.group(1)
            
            # Try to extract company name
            soup = BeautifulSoup(response.text, 'html.parser')
            company_elem = soup.find('span', {'class': 'companyName'})
            if company_elem:
                name_text = company_elem.text.strip()
                # Remove CIK from name if present
                name = re.sub(r'\s+CIK#.*$', '', name_text).strip()
            else:
                name = query
            
            return {
                'cik': cik,
                'name': name,
                'ticker': query.upper()
            }
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Search failed for '{query}': {e}")
        return None

