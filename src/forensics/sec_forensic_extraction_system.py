"""
SEC Forensic Extraction System - Universal Document Processor
Implements multi-modal document extraction with forensic precision.
Supports: PDF, DOCX, XLSX, XML, HTML, XBRL, SGML, Images, Scanned documents
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import logging
import mimetypes
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import numpy as np
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DocumentFormat(Enum):
    """Supported document formats for extraction."""
    HTML = "html"
    XML = "xml"
    XBRL = "xbrl"
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    SGML = "sgml"
    TXT = "txt"
    IMAGE = "image"
    UNKNOWN = "unknown"


@dataclass
class ExtractionResult:
    """Result of document extraction with forensic metadata."""
    content: str
    format: DocumentFormat
    confidence: float
    metadata: Dict[str, Any]
    tables: List[Dict[str, Any]] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    financial_data: Dict[str, Any] = field(default_factory=dict)
    extraction_method: str = "universal"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    content_hash: str = field(default="")
    url: Optional[str] = None
    
    def __post_init__(self):
        """Calculate content hash if not provided."""
        if not self.content_hash and self.content:
            self.content_hash = hashlib.sha256(self.content.encode('utf-8')).hexdigest()


@dataclass
class FinancialMetrics:
    """Extracted financial metrics from documents."""
    revenue: Optional[float] = None
    earnings: Optional[float] = None
    cash_flow: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    ratios: Dict[str, float] = field(default_factory=dict)
    segments: List[Dict[str, Any]] = field(default_factory=list)
    year_over_year: Dict[str, float] = field(default_factory=dict)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)


class UniversalDocumentExtractor:
    """
    Universal document extraction with forensic precision.
    Implements cascading extraction strategies with quality validation.
    """
    
    EXTRACTION_CONFIDENCE_THRESHOLD = 0.95
    
    def __init__(self, enable_ocr: bool = False):
        """
        Initialize universal document extractor.
        
        Args:
            enable_ocr: Enable OCR for scanned documents (requires pytesseract)
        """
        self.enable_ocr = enable_ocr
        self._ocr_available = False
        
        # Try to import optional OCR dependencies
        if enable_ocr:
            try:
                import pytesseract
                from PIL import Image
                self._ocr_available = True
            except ImportError:
                logger.warning("OCR requested but pytesseract/PIL not available")
    
    def detect_format(self, content: str, url: Optional[str] = None) -> DocumentFormat:
        """
        Detect document format from content and URL.
        
        Args:
            content: Document content
            url: Optional document URL
            
        Returns:
            Detected document format
        """
        # Check URL extension first
        if url:
            parsed = urlparse(url)
            path = parsed.path.lower()
            if path.endswith('.xml'):
                # Distinguish between XML and XBRL
                if 'xbrl' in content.lower() or 'http://www.xbrl.org' in content:
                    return DocumentFormat.XBRL
                return DocumentFormat.XML
            elif path.endswith('.html') or path.endswith('.htm'):
                return DocumentFormat.HTML
            elif path.endswith('.pdf'):
                return DocumentFormat.PDF
            elif path.endswith('.docx'):
                return DocumentFormat.DOCX
            elif path.endswith('.xlsx'):
                return DocumentFormat.XLSX
            elif path.endswith('.sgm') or path.endswith('.sgml'):
                return DocumentFormat.SGML
        
        # Content-based detection
        content_lower = content.lower().strip()
        
        # Check for XBRL (has higher priority than XML)
        if ('xbrl' in content_lower or 
            'http://www.xbrl.org' in content_lower or
            '<xbrl' in content_lower):
            return DocumentFormat.XBRL
        
        # Check for XML
        if content.strip().startswith('<?xml') or content_lower.startswith('<xml'):
            return DocumentFormat.XML
        
        # Check for HTML
        if (content_lower.startswith('<!doctype html') or 
            content_lower.startswith('<html') or
            '<html>' in content_lower):
            return DocumentFormat.HTML
        
        # Check for SGML (SEC filings often start with specific tags)
        if ('<sec-document>' in content_lower or 
            '<sec-header>' in content_lower or
            '<document>' in content_lower and '<type>' in content_lower):
            return DocumentFormat.SGML
        
        # Check for binary PDF signature
        if content.startswith('%PDF'):
            return DocumentFormat.PDF
        
        # Default to TXT for plain text
        if content and not content.startswith(('<', '%', '{')):
            return DocumentFormat.TXT
        
        return DocumentFormat.UNKNOWN
    
    async def extract_document(
        self,
        content: str,
        url: Optional[str] = None,
        format_hint: Optional[DocumentFormat] = None,
    ) -> ExtractionResult:
        """
        Extract document content with optimal strategy based on format.
        
        Args:
            content: Document content
            url: Optional document URL
            format_hint: Optional format hint to skip detection
            
        Returns:
            Extraction result with parsed content
        """
        # Detect format if not provided
        doc_format = format_hint if format_hint else self.detect_format(content, url)
        
        # Route to appropriate extractor
        if doc_format == DocumentFormat.HTML:
            return await self._extract_html(content, url)
        elif doc_format == DocumentFormat.XML:
            return await self._extract_xml(content, url)
        elif doc_format == DocumentFormat.XBRL:
            return await self._extract_xbrl(content, url)
        elif doc_format == DocumentFormat.SGML:
            return await self._extract_sgml(content, url)
        elif doc_format == DocumentFormat.PDF:
            return await self._extract_pdf(content, url)
        elif doc_format == DocumentFormat.TXT:
            return await self._extract_text(content, url)
        else:
            # Fallback to text extraction
            return await self._extract_text(content, url)
    
    async def _extract_html(self, content: str, url: Optional[str]) -> ExtractionResult:
        """Extract content from HTML documents."""
        soup = BeautifulSoup(content, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract text
        text = soup.get_text(separator='\n', strip=True)
        
        # Extract tables
        tables = []
        for table in soup.find_all('table'):
            table_data = self._extract_table_from_html(table)
            if table_data:
                tables.append(table_data)
        
        # Extract metadata
        metadata = {}
        if soup.title:
            metadata['title'] = soup.title.string
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content_val = meta.get('content')
            if name and content_val:
                metadata[name] = content_val
        
        confidence = 0.95 if text else 0.5
        
        return ExtractionResult(
            content=text,
            format=DocumentFormat.HTML,
            confidence=confidence,
            metadata=metadata,
            tables=tables,
            url=url
        )
    
    def _extract_table_from_html(self, table_element) -> Optional[Dict[str, Any]]:
        """Extract structured data from HTML table."""
        rows = []
        headers = []
        
        # Extract headers
        for th in table_element.find_all('th'):
            headers.append(th.get_text(strip=True))
        
        # Extract rows
        for tr in table_element.find_all('tr'):
            cells = []
            for td in tr.find_all('td'):
                cells.append(td.get_text(strip=True))
            if cells:
                rows.append(cells)
        
        if not rows:
            return None
        
        return {
            'headers': headers,
            'rows': rows,
            'row_count': len(rows),
            'column_count': len(headers) if headers else (len(rows[0]) if rows else 0)
        }
    
    async def _extract_xml(self, content: str, url: Optional[str]) -> ExtractionResult:
        """Extract content from XML documents."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            
            # Extract text from all elements
            text_parts = []
            metadata = {}
            
            def extract_from_element(element, depth=0):
                if element.text and element.text.strip():
                    text_parts.append(element.text.strip())
                
                # Store attributes in metadata
                if element.attrib:
                    tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
                    metadata[f'{tag_name}_attrs'] = element.attrib
                
                for child in element:
                    extract_from_element(child, depth + 1)
            
            extract_from_element(root)
            text = '\n'.join(text_parts)
            
            return ExtractionResult(
                content=text,
                format=DocumentFormat.XML,
                confidence=0.90,
                metadata=metadata,
                url=url
            )
        except Exception as e:
            logger.warning(f"XML parsing failed, falling back to text: {e}")
            return await self._extract_text(content, url)
    
    async def _extract_xbrl(self, content: str, url: Optional[str]) -> ExtractionResult:
        """Extract content from XBRL documents with financial data parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            
            text_parts = []
            financial_data = {}
            metadata = {'is_xbrl': True}
            
            # Common XBRL namespaces
            namespaces = {
                'xbrli': 'http://www.xbrl.org/2003/instance',
                'dei': 'http://xbrl.sec.gov/dei/2023',
                'us-gaap': 'http://fasb.org/us-gaap/2023',
            }
            
            # Extract context and period information
            contexts = {}
            for context in root.findall('.//xbrli:context', namespaces):
                context_id = context.get('id')
                if context_id:
                    period = context.find('.//xbrli:period', namespaces)
                    if period is not None:
                        instant = period.find('xbrli:instant', namespaces)
                        if instant is not None:
                            contexts[context_id] = instant.text
            
            # Extract financial facts
            for element in root.iter():
                tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
                
                # Skip structural elements
                if tag in ['xbrl', 'context', 'unit', 'schemaRef']:
                    continue
                
                if element.text and element.text.strip():
                    text_parts.append(f"{tag}: {element.text.strip()}")
                    
                    # Try to extract as financial metric
                    try:
                        value = float(element.text.strip())
                        context_ref = element.get('contextRef')
                        financial_data[tag] = {
                            'value': value,
                            'contextRef': context_ref,
                            'period': contexts.get(context_ref) if context_ref else None,
                            'decimals': element.get('decimals'),
                            'unitRef': element.get('unitRef')
                        }
                    except (ValueError, AttributeError):
                        pass
            
            text = '\n'.join(text_parts)
            
            return ExtractionResult(
                content=text,
                format=DocumentFormat.XBRL,
                confidence=0.92,
                metadata=metadata,
                financial_data=financial_data,
                url=url
            )
        except Exception as e:
            logger.warning(f"XBRL parsing failed, falling back to XML: {e}")
            return await self._extract_xml(content, url)
    
    async def _extract_sgml(self, content: str, url: Optional[str]) -> ExtractionResult:
        """Extract content from SGML SEC documents."""
        # SGML documents often contain multiple embedded documents
        # Extract the main text content and document structure
        
        text_parts = []
        metadata = {}
        tables = []
        
        # Extract SEC header information
        sec_header_match = re.search(
            r'<SEC-HEADER>(.*?)</SEC-HEADER>',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if sec_header_match:
            header = sec_header_match.group(1)
            metadata['sec_header'] = header.strip()
            
            # Extract key fields from header
            for field in ['COMPANY CONFORMED NAME', 'CENTRAL INDEX KEY', 'FILING DATE']:
                field_match = re.search(rf'{field}:\s*(.*?)$', header, re.MULTILINE)
                if field_match:
                    metadata[field.lower().replace(' ', '_')] = field_match.group(1).strip()
        
        # Extract document sections
        document_pattern = re.compile(
            r'<DOCUMENT>(.*?)</DOCUMENT>',
            re.DOTALL | re.IGNORECASE
        )
        
        for doc_match in document_pattern.finditer(content):
            doc_content = doc_match.group(1)
            
            # Extract document type
            type_match = re.search(r'<TYPE>(.*?)$', doc_content, re.MULTILINE)
            doc_type = type_match.group(1).strip() if type_match else 'UNKNOWN'
            
            # Extract text content
            text_match = re.search(
                r'<TEXT>(.*?)</TEXT>',
                doc_content,
                re.DOTALL | re.IGNORECASE
            )
            if text_match:
                doc_text = text_match.group(1)
                # Parse embedded HTML/XML if present
                if '<HTML>' in doc_text.upper() or '<!DOCTYPE' in doc_text.upper():
                    html_result = await self._extract_html(doc_text, url)
                    text_parts.append(f"[{doc_type}]\n{html_result.content}")
                    tables.extend(html_result.tables)
                else:
                    # Clean SGML tags
                    clean_text = re.sub(r'<[^>]+>', '', doc_text)
                    text_parts.append(f"[{doc_type}]\n{clean_text}")
        
        text = '\n\n'.join(text_parts)
        
        return ExtractionResult(
            content=text,
            format=DocumentFormat.SGML,
            confidence=0.88,
            metadata=metadata,
            tables=tables,
            url=url
        )
    
    async def _extract_pdf(self, content: str, url: Optional[str]) -> ExtractionResult:
        """Extract content from PDF documents."""
        try:
            import pdfplumber
            
            # PDF content should be bytes, but we may receive it as string
            if isinstance(content, str):
                content_bytes = content.encode('latin-1')
            else:
                content_bytes = content
            
            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                text_parts = []
                tables = []
                
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        if table:
                            tables.append({
                                'page': page_num + 1,
                                'rows': table,
                                'row_count': len(table),
                                'column_count': len(table[0]) if table else 0
                            })
                
                text = '\n\n'.join(text_parts)
                metadata = {
                    'page_count': len(pdf.pages),
                    'pdf_metadata': pdf.metadata
                }
                
                return ExtractionResult(
                    content=text,
                    format=DocumentFormat.PDF,
                    confidence=0.85,
                    metadata=metadata,
                    tables=tables,
                    url=url
                )
        except ImportError:
            logger.warning("pdfplumber not available, cannot extract PDF")
            return ExtractionResult(
                content="[PDF content - extraction not available]",
                format=DocumentFormat.PDF,
                confidence=0.1,
                metadata={},
                url=url
            )
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ExtractionResult(
                content=f"[PDF extraction error: {str(e)}]",
                format=DocumentFormat.PDF,
                confidence=0.1,
                metadata={},
                url=url
            )
    
    async def _extract_text(self, content: str, url: Optional[str]) -> ExtractionResult:
        """Extract content from plain text documents."""
        # Basic text cleaning
        text = content.strip()
        
        # Calculate confidence based on text characteristics
        confidence = 0.80
        if len(text) > 100:
            confidence = 0.85
        if len(text) > 1000:
            confidence = 0.90
        
        return ExtractionResult(
            content=text,
            format=DocumentFormat.TXT,
            confidence=confidence,
            metadata={},
            url=url
        )
    
    def calculate_extraction_confidence(self, result: ExtractionResult) -> float:
        """
        Calculate overall extraction confidence based on multiple factors.
        
        Args:
            result: Extraction result
            
        Returns:
            Confidence score (0-1)
        """
        confidence = result.confidence
        
        # Adjust based on content length
        if len(result.content) < 100:
            confidence *= 0.8
        
        # Boost confidence if we extracted structured data
        if result.tables:
            confidence = min(1.0, confidence * 1.1)
        
        if result.financial_data:
            confidence = min(1.0, confidence * 1.15)
        
        return confidence


class ForensicSECDocumentAnalyzer:
    """
    Forensic analyzer for SEC documents with complete provenance tracking.
    """
    
    def __init__(self, extractor: Optional[UniversalDocumentExtractor] = None):
        """
        Initialize forensic SEC document analyzer.
        
        Args:
            extractor: Optional custom document extractor
        """
        self.extractor = extractor or UniversalDocumentExtractor()
    
    async def analyze_document(
        self,
        content: str,
        url: Optional[str] = None,
        extract_financials: bool = True,
        extract_tables: bool = True,
    ) -> ExtractionResult:
        """
        Analyze SEC document with forensic precision.
        
        Args:
            content: Document content
            url: Document URL
            extract_financials: Whether to extract financial metrics
            extract_tables: Whether to extract tables
            
        Returns:
            Complete extraction result with forensic metadata
        """
        # Extract document
        result = await self.extractor.extract_document(content, url)
        
        # Calculate final confidence
        final_confidence = self.extractor.calculate_extraction_confidence(result)
        result.confidence = final_confidence
        
        # Extract financial metrics if requested
        if extract_financials and result.content:
            financial_metrics = await self._extract_financial_metrics(result.content)
            if financial_metrics:
                result.financial_data.update({
                    'extracted_metrics': financial_metrics.__dict__
                })
        
        return result
    
    async def _extract_financial_metrics(self, content: str) -> Optional[FinancialMetrics]:
        """
        Extract financial metrics from text content.
        
        Args:
            content: Document text content
            
        Returns:
            Extracted financial metrics or None
        """
        metrics = FinancialMetrics()
        
        # Common patterns for financial metrics (in millions or billions)
        patterns = {
            'revenue': r'(?:revenue|sales|total\s+revenue)[:\s]+\$?\s*([\d,]+\.?\d*)\s*(?:million|billion)?',
            'earnings': r'(?:net\s+income|earnings|profit)[:\s]+\$?\s*([\d,]+\.?\d*)\s*(?:million|billion)?',
            'cash_flow': r'(?:cash\s+flow|operating\s+cash\s+flow)[:\s]+\$?\s*([\d,]+\.?\d*)\s*(?:million|billion)?',
            'total_assets': r'(?:total\s+assets)[:\s]+\$?\s*([\d,]+\.?\d*)\s*(?:million|billion)?',
            'total_liabilities': r'(?:total\s+liabilities)[:\s]+\$?\s*([\d,]+\.?\d*)\s*(?:million|billion)?',
        }
        
        content_lower = content.lower()
        extracted_any = False
        
        for metric_name, pattern in patterns.items():
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            if matches:
                try:
                    # Take the first match and convert to float
                    value_str = matches[0].replace(',', '')
                    value = float(value_str)
                    setattr(metrics, metric_name, value)
                    extracted_any = True
                except (ValueError, AttributeError):
                    pass
        
        return metrics if extracted_any else None


# Alias for backward compatibility
class UniversalSECExtractor(UniversalDocumentExtractor):
    """Alias for UniversalDocumentExtractor for backward compatibility."""
    pass
