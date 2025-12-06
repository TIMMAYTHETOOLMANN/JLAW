"""
SEC PDF Adapter
================

Enhanced PDF parsing for SEC filings with DocsGPT integration.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import hashlib

logger = logging.getLogger(__name__)


class SECPDFAdapter:
    """
    Adapter for parsing SEC PDF filings.
    
    Combines DocsGPT's PDF parsing with SEC-specific extraction logic.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.use_ocr = config.get('use_ocr', True) if config else True
        self.extract_tables = config.get('extract_tables', True) if config else True
    
    def parse(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse a PDF filing.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Parsed document with text, tables, and metadata
        """
        path = Path(file_path)
        
        result = {
            'doc_id': f"pdf_{path.stem}_{hashlib.md5(str(path).encode()).hexdigest()[:8]}",
            'source_path': str(path),
            'format': 'pdf',
            'text': '',
            'tables': [],
            'metadata': {},
            'pages': []
        }
        
        # Try primary parsing method
        text = self._parse_with_pypdf(path)
        if text:
            result['text'] = text
        
        # Extract tables if enabled
        if self.extract_tables:
            result['tables'] = self._extract_tables(path)
        
        # If no text extracted and OCR enabled, try OCR
        if not result['text'] and self.use_ocr:
            result['text'] = self._parse_with_ocr(path)
            result['metadata']['ocr_used'] = True
        
        # Extract SEC-specific metadata
        result['metadata'].update(self._extract_sec_metadata(result['text']))
        
        return result
    
    def _parse_with_pypdf(self, path: Path) -> str:
        """Parse PDF using pypdf."""
        try:
            from pypdf import PdfReader
            
            with open(path, 'rb') as f:
                pdf = PdfReader(f)
                text_parts = []
                
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                
                return '\n'.join(text_parts)
        except Exception as e:
            logger.warning(f"pypdf parsing failed: {e}")
            return ''
    
    def _parse_with_ocr(self, path: Path) -> str:
        """Parse PDF using OCR."""
        try:
            import pdfplumber
            import pytesseract
            
            text_parts = []
            
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text and len(text.strip()) > 50:
                        text_parts.append(text)
                    else:
                        img = page.to_image(resolution=300)
                        pil_img = img.original
                        ocr_text = pytesseract.image_to_string(pil_img)
                        text_parts.append(ocr_text)
            
            return '\n'.join(text_parts)
        except Exception as e:
            logger.warning(f"OCR parsing failed: {e}")
            return ''
    
    def _extract_tables(self, path: Path) -> List[Dict[str, Any]]:
        """Extract tables from PDF."""
        tables = []
        
        try:
            import pdfplumber
            
            with pdfplumber.open(path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(page_tables):
                        if table and len(table) > 1:
                            tables.append({
                                'page': page_num + 1,
                                'index': table_idx,
                                'rows': len(table),
                                'cols': len(table[0]) if table else 0,
                                'headers': table[0] if table else [],
                                'data': table[1:] if len(table) > 1 else []
                            })
            
            logger.info(f"Extracted {len(tables)} tables from PDF")
        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")
        
        return tables
    
    def _extract_sec_metadata(self, text: str) -> Dict[str, Any]:
        """Extract SEC-specific metadata from text."""
        import re
        
        metadata = {}
        
        # CIK
        cik_match = re.search(r'CIK[:\s]+(\d{10})', text, re.IGNORECASE)
        if cik_match:
            metadata['cik'] = cik_match.group(1)
        
        # Company name
        company_match = re.search(r'(?:Registrant|Company)[:\s]+([A-Z][^\n]{5,50})', text)
        if company_match:
            metadata['company_name'] = company_match.group(1).strip()
        
        # Filing type
        for filing_type in ['10-K', '10-Q', '8-K', 'DEF 14A', 'S-1', '20-F']:
            if filing_type in text[:5000]:
                metadata['filing_type'] = filing_type
                break
        
        # Filing date
        date_match = re.search(
            r'(?:filed|dated)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
            text[:5000],
            re.IGNORECASE
        )
        if date_match:
            metadata['filing_date'] = date_match.group(1)
        
        return metadata

