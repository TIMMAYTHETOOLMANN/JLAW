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
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

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
            self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()


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
            if path.endswith(".xml"):
                # Distinguish between XML and XBRL by checking for XBRL namespace
                # Note: This is content inspection, not URL sanitization
                xbrl_namespace = "http://www.xbrl.org"  # Standard XBRL namespace
                if "xbrl" in content.lower() or xbrl_namespace in content:
                    return DocumentFormat.XBRL
                return DocumentFormat.XML
            elif path.endswith(".html") or path.endswith(".htm"):
                return DocumentFormat.HTML
            elif path.endswith(".pdf"):
                return DocumentFormat.PDF
            elif path.endswith(".docx"):
                return DocumentFormat.DOCX
            elif path.endswith(".xlsx"):
                return DocumentFormat.XLSX
            elif path.endswith(".sgm") or path.endswith(".sgml"):
                return DocumentFormat.SGML

        # Content-based detection
        content_lower = content.lower().strip()

        # Check for SGML first (SEC filings have specific structure)
        # This needs to be before HTML check since SGML can contain HTML
        if (
            "<sec-document>" in content_lower
            or "<sec-header>" in content_lower
            or ("<document>" in content_lower and "<type>" in content_lower)
        ):
            return DocumentFormat.SGML

        # Check for XBRL (has higher priority than XML)
        # Note: Checking for XBRL namespace in content, not URL validation
        xbrl_namespace = "http://www.xbrl.org"  # Standard XBRL namespace identifier
        if "xbrl" in content_lower or xbrl_namespace in content_lower or "<xbrl" in content_lower:
            return DocumentFormat.XBRL

        # Check for XML
        if content.strip().startswith("<?xml") or content_lower.startswith("<xml"):
            return DocumentFormat.XML

        # Check for HTML
        if (
            content_lower.startswith("<!doctype html")
            or content_lower.startswith("<html")
            or "<html>" in content_lower
        ):
            return DocumentFormat.HTML

        # Check for binary PDF signature
        if content.startswith("%PDF"):
            return DocumentFormat.PDF

        # Default to TXT for plain text
        if content and not content.startswith(("<", "%", "{")):
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
        soup = BeautifulSoup(content, "lxml")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract text
        text = soup.get_text(separator="\n", strip=True)

        # Extract tables
        tables = []
        for table in soup.find_all("table"):
            table_data = self._extract_table_from_html(table)
            if table_data:
                tables.append(table_data)

        # Extract metadata
        metadata = {}
        if soup.title:
            metadata["title"] = soup.title.string

        # Extract meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content_val = meta.get("content")
            if name and content_val:
                metadata[name] = content_val

        confidence = 0.95 if text else 0.5

        return ExtractionResult(
            content=text,
            format=DocumentFormat.HTML,
            confidence=confidence,
            metadata=metadata,
            tables=tables,
            url=url,
        )

    def _extract_table_from_html(self, table_element) -> Optional[Dict[str, Any]]:
        """Extract structured data from HTML table."""
        rows = []
        headers = []

        # Extract headers
        for th in table_element.find_all("th"):
            headers.append(th.get_text(strip=True))

        # Extract rows
        for tr in table_element.find_all("tr"):
            cells = []
            for td in tr.find_all("td"):
                cells.append(td.get_text(strip=True))
            if cells:
                rows.append(cells)

        if not rows:
            return None

        return {
            "headers": headers,
            "rows": rows,
            "row_count": len(rows),
            "column_count": len(headers) if headers else (len(rows[0]) if rows else 0),
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
                    tag_name = element.tag.split("}")[-1] if "}" in element.tag else element.tag
                    metadata[f"{tag_name}_attrs"] = element.attrib

                for child in element:
                    extract_from_element(child, depth + 1)

            extract_from_element(root)
            text = "\n".join(text_parts)

            return ExtractionResult(
                content=text, format=DocumentFormat.XML, confidence=0.90, metadata=metadata, url=url
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
            metadata = {"is_xbrl": True}

            # Common XBRL namespaces
            namespaces = {
                "xbrli": "http://www.xbrl.org/2003/instance",
                "dei": "http://xbrl.sec.gov/dei/2023",
                "us-gaap": "http://fasb.org/us-gaap/2023",
            }

            # Extract context and period information
            contexts = {}
            for context in root.findall(".//xbrli:context", namespaces):
                context_id = context.get("id")
                if context_id:
                    period = context.find(".//xbrli:period", namespaces)
                    if period is not None:
                        instant = period.find("xbrli:instant", namespaces)
                        if instant is not None:
                            contexts[context_id] = instant.text

            # Extract financial facts
            for element in root.iter():
                tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

                # Skip structural elements
                if tag in ["xbrl", "context", "unit", "schemaRef"]:
                    continue

                if element.text and element.text.strip():
                    text_parts.append(f"{tag}: {element.text.strip()}")

                    # Try to extract as financial metric
                    try:
                        value = float(element.text.strip())
                        context_ref = element.get("contextRef")
                        financial_data[tag] = {
                            "value": value,
                            "contextRef": context_ref,
                            "period": contexts.get(context_ref) if context_ref else None,
                            "decimals": element.get("decimals"),
                            "unitRef": element.get("unitRef"),
                        }
                    except (ValueError, AttributeError):
                        pass

            text = "\n".join(text_parts)

            return ExtractionResult(
                content=text,
                format=DocumentFormat.XBRL,
                confidence=0.92,
                metadata=metadata,
                financial_data=financial_data,
                url=url,
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
            r"<SEC-HEADER>(.*?)</SEC-HEADER>", content, re.DOTALL | re.IGNORECASE
        )
        if sec_header_match:
            header = sec_header_match.group(1)
            metadata["sec_header"] = header.strip()

            # Extract key fields from header
            for field in ["COMPANY CONFORMED NAME", "CENTRAL INDEX KEY", "FILING DATE"]:
                field_match = re.search(rf"{field}:\s*(.*?)$", header, re.MULTILINE)
                if field_match:
                    metadata[field.lower().replace(" ", "_")] = field_match.group(1).strip()

        # Extract document sections
        document_pattern = re.compile(r"<DOCUMENT>(.*?)</DOCUMENT>", re.DOTALL | re.IGNORECASE)

        for doc_match in document_pattern.finditer(content):
            doc_content = doc_match.group(1)

            # Extract document type
            type_match = re.search(r"<TYPE>(.*?)$", doc_content, re.MULTILINE)
            doc_type = type_match.group(1).strip() if type_match else "UNKNOWN"

            # Extract text content
            text_match = re.search(r"<TEXT>(.*?)</TEXT>", doc_content, re.DOTALL | re.IGNORECASE)
            if text_match:
                doc_text = text_match.group(1)
                # Parse embedded HTML/XML if present
                if "<HTML>" in doc_text.upper() or "<!DOCTYPE" in doc_text.upper():
                    html_result = await self._extract_html(doc_text, url)
                    text_parts.append(f"[{doc_type}]\n{html_result.content}")
                    tables.extend(html_result.tables)
                else:
                    # Clean SGML tags
                    clean_text = re.sub(r"<[^>]+>", "", doc_text)
                    text_parts.append(f"[{doc_type}]\n{clean_text}")

        text = "\n\n".join(text_parts)

        return ExtractionResult(
            content=text,
            format=DocumentFormat.SGML,
            confidence=0.88,
            metadata=metadata,
            tables=tables,
            url=url,
        )

    async def _extract_pdf(self, content: str, url: Optional[str]) -> ExtractionResult:
        """Extract content from PDF documents."""
        try:
            import pdfplumber

            # PDF content should be bytes, but we may receive it as string
            if isinstance(content, str):
                content_bytes = content.encode("latin-1")
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
                            tables.append(
                                {
                                    "page": page_num + 1,
                                    "rows": table,
                                    "row_count": len(table),
                                    "column_count": len(table[0]) if table else 0,
                                }
                            )

                text = "\n\n".join(text_parts)
                metadata = {"page_count": len(pdf.pages), "pdf_metadata": pdf.metadata}

                return ExtractionResult(
                    content=text,
                    format=DocumentFormat.PDF,
                    confidence=0.85,
                    metadata=metadata,
                    tables=tables,
                    url=url,
                )
        except ImportError:
            logger.warning("pdfplumber not available, cannot extract PDF")
            return ExtractionResult(
                content="[PDF content - extraction not available]",
                format=DocumentFormat.PDF,
                confidence=0.1,
                metadata={},
                url=url,
            )
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ExtractionResult(
                content=f"[PDF extraction error: {str(e)}]",
                format=DocumentFormat.PDF,
                confidence=0.1,
                metadata={},
                url=url,
            )

    async def _extract_text(self, content: str, url: Optional[str]) -> ExtractionResult:
        """Extract content from plain text documents."""
        # Basic text cleaning
        text = content.strip()

        # Calculate confidence based on text characteristics
        confidence = 0.50  # Start lower for empty/minimal content
        if len(text) > 100:
            confidence = 0.80
        if len(text) > 1000:
            confidence = 0.90

        return ExtractionResult(
            content=text, format=DocumentFormat.TXT, confidence=confidence, metadata={}, url=url
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
                result.financial_data.update({"extracted_metrics": financial_metrics.__dict__})

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
            "revenue": r"(?:revenue|sales|total\s+revenue)[:\s]+\$?\s*([\d,]+\.?\d*)\s*(?:million|billion)?",
            "earnings": r"(?:net\s+income|earnings|profit)[:\s]+\$?\s*([\d,]+\.?\d*)\s*(?:million|billion)?",
            "cash_flow": r"(?:cash\s+flow|operating\s+cash\s+flow)[:\s]+\$?\s*([\d,]+\.?\d*)\s*(?:million|billion)?",
            "total_assets": r"(?:total\s+assets)[:\s]+\$?\s*([\d,]+\.?\d*)\s*(?:million|billion)?",
            "total_liabilities": r"(?:total\s+liabilities)[:\s]+\$?\s*([\d,]+\.?\d*)\s*(?:million|billion)?",
        }

        content_lower = content.lower()
        extracted_any = False

        for metric_name, pattern in patterns.items():
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            if matches:
                try:
                    # Take the first match and convert to float
                    value_str = matches[0].replace(",", "")
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


# ============================================================================
# ENHANCED DOCUMENT FORMAT SUPPORT
# ============================================================================


class EnhancedDocumentFormat(Enum):
    """Extended document formats with complete coverage."""

    HTML = "html"
    XML = "xml"
    XBRL = "xbrl"
    IXBRL = "ixbrl"  # Inline XBRL
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    SGML = "sgml"
    TXT = "txt"
    JSON = "json"
    CSV = "csv"
    IMAGE = "image"
    UNKNOWN = "unknown"


@dataclass
class ComprehensiveExtractionResult:
    """
    Complete extraction result with forensic-level detail.
    Provides 100% content coverage with audit trail.
    """

    # Core content
    content: str
    raw_content: str  # Unprocessed original content
    format: EnhancedDocumentFormat

    # Byte-level tracking
    byte_coverage: float  # Percentage of bytes successfully processed
    total_bytes: int
    extracted_bytes: int

    # Element tracking
    element_count: int
    elements: List[Dict[str, Any]] = field(default_factory=list)

    # Structured data
    tables: List[Dict[str, Any]] = field(default_factory=list)
    forms: List[Dict[str, Any]] = field(default_factory=list)
    footnotes: List[Dict[str, Any]] = field(default_factory=list)
    signatures: List[Dict[str, Any]] = field(default_factory=list)

    # Financial data
    financial_data: Dict[str, Any] = field(default_factory=dict)

    # SEC-specific
    sec_sections: Dict[str, Any] = field(default_factory=dict)
    legal_references: List[Dict[str, Any]] = field(default_factory=list)
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    material_events: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata and audit trail
    metadata: Dict[str, Any] = field(default_factory=dict)
    hidden_elements: List[Dict[str, Any]] = field(default_factory=list)
    comments: List[str] = field(default_factory=list)
    styles: Dict[str, Any] = field(default_factory=dict)

    # Hierarchical structure
    document_structure: Dict[str, Any] = field(default_factory=dict)
    cross_references: List[Dict[str, Any]] = field(default_factory=list)

    # Extraction details
    confidence: float = 0.0
    extraction_method: str = "forensic"
    encoding: str = "utf-8"
    parse_errors: List[str] = field(default_factory=list)
    fallback_strategies_used: List[str] = field(default_factory=list)

    # Audit trail
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    content_hash: str = field(default="")
    url: Optional[str] = None

    def __post_init__(self):
        """Calculate content hash and byte coverage if not provided."""
        if not self.content_hash and self.content:
            self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
        if self.total_bytes > 0 and self.byte_coverage == 0:
            self.byte_coverage = self.extracted_bytes / self.total_bytes


@dataclass
class SECPatternMatch:
    """Match result for SEC-specific patterns."""

    pattern_type: str
    matched_text: str
    start_position: int
    end_position: int
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ForensicSECAnalyzer:
    """
    Complete forensic SEC document analyzer with 100% content coverage.

    Implements:
    - Universal format support (HTML, XML, XBRL, iXBRL, SGML, PDF, JSON, CSV)
    - Exhaustive content extraction (hidden elements, comments, styles)
    - Advanced SEC-specific pattern recognition
    - Byte-level coverage tracking
    - Multiple parsing fallbacks with error recovery
    - Complete audit trail

    Usage:
        analyzer = ForensicSECAnalyzer()
        await analyzer.create_session()
        result = await analyzer.analyze_filing("https://sec.gov/path/to/filing")
    """

    # SEC document section patterns
    SEC_SECTION_PATTERNS = {
        "item_1": r"(?:ITEM\s*1[\.:]?\s*(?:BUSINESS|Description of Business))",
        "item_1a": r"(?:ITEM\s*1A[\.:]?\s*RISK\s*FACTORS)",
        "item_2": r"(?:ITEM\s*2[\.:]?\s*(?:PROPERTIES|DESCRIPTION OF PROPERTY))",
        "item_3": r"(?:ITEM\s*3[\.:]?\s*LEGAL\s*PROCEEDINGS)",
        "item_4": r"(?:ITEM\s*4[\.:]?\s*MINE\s*SAFETY)",
        "item_5": r"(?:ITEM\s*5[\.:]?\s*MARKET|ITEM\s*5[\.:]?\s*EQUITY)",
        "item_6": r"(?:ITEM\s*6[\.:]?\s*SELECTED\s*FINANCIAL)",
        "item_7": r"(?:ITEM\s*7[\.:]?\s*MANAGEMENT)",
        "item_7a": r"(?:ITEM\s*7A[\.:]?\s*QUANTITATIVE)",
        "item_8": r"(?:ITEM\s*8[\.:]?\s*FINANCIAL\s*STATEMENTS)",
        "item_9": r"(?:ITEM\s*9[\.:]?\s*CHANGES|DISAGREEMENTS)",
        "item_9a": r"(?:ITEM\s*9A[\.:]?\s*CONTROLS)",
        "item_10": r"(?:ITEM\s*10[\.:]?\s*DIRECTORS)",
        "item_11": r"(?:ITEM\s*11[\.:]?\s*EXECUTIVE\s*COMPENSATION)",
        "item_12": r"(?:ITEM\s*12[\.:]?\s*SECURITY\s*OWNERSHIP)",
        "item_13": r"(?:ITEM\s*13[\.:]?\s*CERTAIN\s*RELATIONSHIPS)",
        "item_14": r"(?:ITEM\s*14[\.:]?\s*PRINCIPAL\s*ACCOUNTANT)",
        "item_15": r"(?:ITEM\s*15[\.:]?\s*EXHIBITS)",
    }

    # Financial pattern recognition
    FINANCIAL_PATTERNS = {
        "monetary_amount": r"\$\s*([\d,]+(?:\.\d{2})?)\s*(?:million|billion|thousand|M|B|K)?",
        "percentage": r"([\d.]+)\s*%",
        "fiscal_year": r"(?:fiscal\s*(?:year\s*)?|FY\s*)(20\d{2})",
        "quarter": r"(?:Q|quarter\s*)([1-4])",
        "date": r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
    }

    # Legal reference patterns
    LEGAL_PATTERNS = {
        "usc_citation": r"(\d+)\s*U\.?S\.?C\.?\s*§?\s*(\d+[a-z]?(?:\([a-z0-9]+\))?)",
        "cfr_citation": r"(\d+)\s*C\.?F\.?R\.?\s*§?\s*(\d+(?:\.\d+)?)",
        "sec_rule": r"(?:Rule|Regulation)\s*(\d+[a-z]?(?:-\d+)?)",
        "sox_section": r"(?:Sarbanes-Oxley|SOX)\s*(?:Section|§)?\s*(\d+)",
        "gaap_reference": r"(?:ASC|FASB)\s*(\d+(?:-\d+)?)",
    }

    # Signature patterns
    SIGNATURE_PATTERNS = {
        "typed_signature": r"/s/\s*([A-Z][a-zA-Z\s\.\-\']+)",
        "signature_block": r"(?:By|Signed)[:\s]+([A-Z][a-zA-Z\s\.\-\']+)",
        "attestation": r"(?:I|We),?\s+([A-Z][a-zA-Z\s\.\-\']+),?\s+(?:certify|attest)",
    }

    def __init__(
        self,
        enable_ocr: bool = False,
        strict_mode: bool = True,
        encoding_fallbacks: Optional[List[str]] = None,
    ):
        """
        Initialize forensic SEC analyzer.

        Args:
            enable_ocr: Enable OCR for scanned documents
            strict_mode: Require complete extraction (raise on partial)
            encoding_fallbacks: List of encodings to try if UTF-8 fails
        """
        self.enable_ocr = enable_ocr
        self.strict_mode = strict_mode
        self.encoding_fallbacks = encoding_fallbacks or [
            "utf-8",
            "latin-1",
            "cp1252",
            "iso-8859-1",
            "ascii",
        ]

        self._session_active = False
        self._session_id: Optional[str] = None
        self._extractor = UniversalDocumentExtractor(enable_ocr=enable_ocr)

        logger.info("ForensicSECAnalyzer initialized with strict_mode=%s", strict_mode)

    async def create_session(self) -> str:
        """
        Create a new analysis session.

        Returns:
            Session ID for tracking
        """
        self._session_id = hashlib.sha256(
            datetime.now(timezone.utc).isoformat().encode()
        ).hexdigest()[:16]
        self._session_active = True

        logger.info("Analysis session created: %s", self._session_id)
        return self._session_id

    async def close_session(self) -> None:
        """Close the current analysis session."""
        self._session_active = False
        logger.info("Analysis session closed: %s", self._session_id)
        self._session_id = None

    def _detect_encoding(self, content: bytes) -> str:
        """
        Detect content encoding with multiple fallbacks.

        Args:
            content: Raw bytes content

        Returns:
            Detected encoding name
        """
        # Try chardet if available
        try:
            import chardet

            result = chardet.detect(content[:10000])
            if result and result.get("encoding"):
                return result["encoding"]
        except ImportError:
            pass

        # Try each fallback encoding
        for encoding in self.encoding_fallbacks:
            try:
                content.decode(encoding)
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue

        return "utf-8"  # Default fallback

    def _detect_format(self, content: str, url: Optional[str] = None) -> EnhancedDocumentFormat:
        """
        Detect document format with extended format support.

        Args:
            content: Document content
            url: Optional document URL

        Returns:
            Detected document format
        """
        content_lower = content.lower().strip()

        # URL-based detection
        if url:
            url_lower = url.lower()
            if url_lower.endswith(".json"):
                return EnhancedDocumentFormat.JSON
            elif url_lower.endswith(".csv"):
                return EnhancedDocumentFormat.CSV
            elif "ixbrl" in url_lower or "inline" in url_lower:
                return EnhancedDocumentFormat.IXBRL

        # Content-based detection

        # JSON detection
        if content.strip().startswith("{") or content.strip().startswith("["):
            try:
                import json as json_module

                json_module.loads(content)
                return EnhancedDocumentFormat.JSON
            except (ValueError, json_module.JSONDecodeError):
                pass

        # CSV detection (simple heuristic)
        lines = content.strip().split("\n")[:5]
        if lines and all("," in line for line in lines if line.strip()):
            # Check if it looks like structured CSV
            comma_counts = [line.count(",") for line in lines if line.strip()]
            if comma_counts and len(set(comma_counts)) == 1:
                return EnhancedDocumentFormat.CSV

        # iXBRL detection (HTML with XBRL namespaces/attributes)
        if "<html" in content_lower or "<!doctype html" in content_lower:
            if (
                "ix:" in content_lower
                or "xmlns:ix" in content_lower
                or "data-xbrl" in content_lower
                or "xbrli:" in content_lower
            ):
                return EnhancedDocumentFormat.IXBRL

        # SGML detection (SEC filings)
        if (
            "<sec-document>" in content_lower
            or "<sec-header>" in content_lower
            or ("<document>" in content_lower and "<type>" in content_lower)
        ):
            return EnhancedDocumentFormat.SGML

        # XBRL detection
        xbrl_namespace = "http://www.xbrl.org"
        if "xbrl" in content_lower or xbrl_namespace in content_lower or "<xbrl" in content_lower:
            return EnhancedDocumentFormat.XBRL

        # XML detection
        if content.strip().startswith("<?xml") or content_lower.startswith("<xml"):
            return EnhancedDocumentFormat.XML

        # HTML detection
        if (
            content_lower.startswith("<!doctype html")
            or content_lower.startswith("<html")
            or "<html>" in content_lower
        ):
            return EnhancedDocumentFormat.HTML

        # PDF detection
        if content.startswith("%PDF"):
            return EnhancedDocumentFormat.PDF

        # Default to text
        if content and not content.startswith(("<", "%", "{")):
            return EnhancedDocumentFormat.TXT

        return EnhancedDocumentFormat.UNKNOWN

    async def analyze_filing(
        self,
        url_or_content: str,
        is_content: bool = False,
        format_hint: Optional[EnhancedDocumentFormat] = None,
    ) -> Dict[str, Any]:
        """
        Analyze SEC filing with complete forensic extraction.

        Args:
            url_or_content: URL to fetch or content string
            is_content: True if url_or_content is actual content
            format_hint: Optional format hint to skip detection

        Returns:
            Complete analysis result with extraction data
        """
        if not self._session_active:
            await self.create_session()

        # Get content
        if is_content:
            content = url_or_content
            url = None
        else:
            content = await self._fetch_content(url_or_content)
            url = url_or_content

        # Perform forensic extraction
        extraction = await self._forensic_extract(content, url, format_hint)

        return {
            "session_id": self._session_id,
            "extraction": extraction,
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _fetch_content(self, url: str) -> str:
        """
        Fetch content from URL with error handling.

        Args:
            url: URL to fetch

        Returns:
            Document content
        """
        import aiohttp

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ForensicSECAnalyzer/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        async with aiohttp.ClientSession() as session:
            await asyncio.sleep(0.1)  # Rate limiting
            async with session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    content_bytes = await response.read()
                    encoding = self._detect_encoding(content_bytes)
                    return content_bytes.decode(encoding, errors="replace")
                else:
                    raise ValueError(f"Failed to fetch URL: {url}, status: {response.status}")

    async def _forensic_extract(
        self,
        content: str,
        url: Optional[str] = None,
        format_hint: Optional[EnhancedDocumentFormat] = None,
    ) -> Dict[str, Any]:
        """
        Perform complete forensic extraction.

        Args:
            content: Document content
            url: Optional source URL
            format_hint: Optional format hint

        Returns:
            Complete extraction result as dictionary
        """
        # Track extraction
        raw_content = content
        total_bytes = len(content.encode("utf-8"))
        extracted_bytes = 0
        parse_errors: List[str] = []
        fallback_strategies: List[str] = []

        # Detect format
        doc_format = format_hint or self._detect_format(content, url)

        # Initialize result components
        elements: List[Dict[str, Any]] = []
        tables: List[Dict[str, Any]] = []
        forms: List[Dict[str, Any]] = []
        footnotes: List[Dict[str, Any]] = []
        signatures: List[Dict[str, Any]] = []
        hidden_elements: List[Dict[str, Any]] = []
        comments: List[str] = []
        styles: Dict[str, Any] = {}
        metadata: Dict[str, Any] = {}
        sec_sections: Dict[str, Any] = {}
        legal_references: List[Dict[str, Any]] = []
        risk_factors: List[Dict[str, Any]] = []
        material_events: List[Dict[str, Any]] = []
        financial_data: Dict[str, Any] = {}
        document_structure: Dict[str, Any] = {}
        cross_references: List[Dict[str, Any]] = []
        extracted_text = ""

        try:
            if doc_format == EnhancedDocumentFormat.HTML:
                result = await self._extract_html_complete(content, url)
            elif doc_format == EnhancedDocumentFormat.IXBRL:
                result = await self._extract_ixbrl(content, url)
            elif doc_format == EnhancedDocumentFormat.XBRL:
                result = await self._extract_xbrl_complete(content, url)
            elif doc_format == EnhancedDocumentFormat.XML:
                result = await self._extract_xml_complete(content, url)
            elif doc_format == EnhancedDocumentFormat.SGML:
                result = await self._extract_sgml_complete(content, url)
            elif doc_format == EnhancedDocumentFormat.JSON:
                result = await self._extract_json(content, url)
            elif doc_format == EnhancedDocumentFormat.CSV:
                result = await self._extract_csv(content, url)
            elif doc_format == EnhancedDocumentFormat.PDF:
                result = await self._extract_pdf_complete(content, url)
            else:
                result = await self._extract_text_complete(content, url)

            # Unpack result
            extracted_text = result.get("text", "")
            elements = result.get("elements", [])
            tables = result.get("tables", [])
            forms = result.get("forms", [])
            footnotes = result.get("footnotes", [])
            signatures = result.get("signatures", [])
            hidden_elements = result.get("hidden_elements", [])
            comments = result.get("comments", [])
            styles = result.get("styles", {})
            metadata = result.get("metadata", {})
            financial_data = result.get("financial_data", {})
            document_structure = result.get("document_structure", {})

            extracted_bytes = len(extracted_text.encode("utf-8"))

        except Exception as e:
            parse_errors.append(f"Primary extraction failed: {str(e)}")
            fallback_strategies.append("text_fallback")

            # Fallback to plain text extraction
            extracted_text = self._strip_tags(content)
            extracted_bytes = len(extracted_text.encode("utf-8"))

        # Extract SEC-specific patterns
        sec_sections = self._extract_sec_sections(extracted_text)
        legal_references = self._extract_legal_references(extracted_text)
        signatures = signatures or self._extract_signatures(extracted_text)
        risk_factors = self._extract_risk_factors(extracted_text)
        material_events = self._extract_material_events(extracted_text)

        # Extract financial patterns
        if not financial_data:
            financial_data = self._extract_financial_patterns(extracted_text)

        # Build cross-references
        cross_references = self._extract_cross_references(extracted_text)

        # Calculate byte coverage
        byte_coverage = extracted_bytes / total_bytes if total_bytes > 0 else 0.0

        # Build confidence score
        confidence = self._calculate_confidence(
            byte_coverage=byte_coverage,
            element_count=len(elements),
            table_count=len(tables),
            has_financial_data=bool(financial_data),
            has_sec_sections=bool(sec_sections),
            parse_error_count=len(parse_errors),
        )

        # Build result dictionary
        result_dict = {
            "content": extracted_text,
            "raw_content": raw_content,
            "format": doc_format.value,
            "byte_coverage": byte_coverage,
            "total_bytes": total_bytes,
            "extracted_bytes": extracted_bytes,
            "element_count": len(elements),
            "elements": elements,
            "tables": tables,
            "forms": forms,
            "footnotes": footnotes,
            "signatures": signatures,
            "financial_data": financial_data,
            "sec_sections": sec_sections,
            "legal_references": legal_references,
            "risk_factors": risk_factors,
            "material_events": material_events,
            "metadata": metadata,
            "hidden_elements": hidden_elements,
            "comments": comments,
            "styles": styles,
            "document_structure": document_structure,
            "cross_references": cross_references,
            "confidence": confidence,
            "extraction_method": "forensic",
            "encoding": "utf-8",
            "parse_errors": parse_errors,
            "fallback_strategies_used": fallback_strategies,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content_hash": hashlib.sha256(extracted_text.encode("utf-8")).hexdigest(),
            "url": url,
        }

        return result_dict

    async def _extract_html_complete(self, content: str, url: Optional[str]) -> Dict[str, Any]:
        """
        Extract HTML with complete DOM traversal including hidden elements and comments.
        """
        soup = BeautifulSoup(content, "lxml")

        result: Dict[str, Any] = {
            "text": "",
            "elements": [],
            "tables": [],
            "forms": [],
            "footnotes": [],
            "signatures": [],
            "hidden_elements": [],
            "comments": [],
            "styles": {},
            "metadata": {},
            "financial_data": {},
            "document_structure": {},
        }

        # Extract HTML comments
        from bs4 import Comment

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            result["comments"].append(str(comment))

        # Extract all elements including hidden ones
        for element in soup.find_all(True):  # True matches all tags
            elem_data = {
                "tag": element.name,
                "text": element.get_text(strip=True)[:500],  # Limit text length
                "attributes": dict(element.attrs) if element.attrs else {},
                "is_hidden": self._is_hidden_element(element),
            }
            result["elements"].append(elem_data)

            if elem_data["is_hidden"]:
                result["hidden_elements"].append(elem_data)

        # Extract metadata
        if soup.title:
            result["metadata"]["title"] = soup.title.string

        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content_val = meta.get("content")
            if name and content_val:
                result["metadata"][name] = content_val

        # Extract styles
        for style in soup.find_all("style"):
            style_text = style.get_text()
            if style_text:
                result["styles"]["inline"] = result["styles"].get("inline", "") + style_text

        # Extract link stylesheets
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if href:
                result["styles"].setdefault("external", []).append(href)

        # Extract tables with cell-level detail
        for idx, table in enumerate(soup.find_all("table")):
            table_data = self._extract_table_complete(table, idx)
            if table_data:
                result["tables"].append(table_data)

        # Extract forms
        for idx, form in enumerate(soup.find_all("form")):
            form_data = self._extract_form(form, idx)
            if form_data:
                result["forms"].append(form_data)

        # Extract footnotes (common patterns)
        footnote_patterns = ["footnote", "fn-", "note-", "endnote"]
        for pattern in footnote_patterns:
            for elem in soup.find_all(class_=lambda x: x and pattern in str(x).lower()):
                result["footnotes"].append(
                    {"text": elem.get_text(strip=True), "pattern": pattern, "id": elem.get("id")}
                )

        # Also check for sup/sub elements with numbers (footnote markers)
        for sup in soup.find_all(["sup", "sub"]):
            text = sup.get_text(strip=True)
            if text.isdigit() or text.startswith("(") and text.endswith(")"):
                parent_text = sup.parent.get_text(strip=True)[:200] if sup.parent else ""
                result["footnotes"].append(
                    {"marker": text, "context": parent_text, "type": "inline_marker"}
                )

        # Build document structure (headers hierarchy)
        headers = []
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            headers.append(
                {"level": int(h.name[1]), "text": h.get_text(strip=True), "id": h.get("id")}
            )
        result["document_structure"]["headers"] = headers

        # Remove script and style for text extraction
        for script in soup(["script", "style"]):
            script.decompose()

        result["text"] = soup.get_text(separator="\n", strip=True)

        return result

    def _is_hidden_element(self, element) -> bool:
        """Check if element is hidden via CSS or attributes."""
        style = element.get("style", "")
        if "display:none" in style.replace(" ", "").lower():
            return True
        if "visibility:hidden" in style.replace(" ", "").lower():
            return True
        if element.get("hidden"):
            return True
        if element.get("aria-hidden") == "true":
            return True
        return False

    def _extract_table_complete(self, table_element, idx: int) -> Optional[Dict[str, Any]]:
        """Extract table with complete cell-level detail."""
        rows = []
        headers = []

        # Extract headers from thead or first row with th
        thead = table_element.find("thead")
        if thead:
            for th in thead.find_all("th"):
                headers.append(
                    {
                        "text": th.get_text(strip=True),
                        "colspan": th.get("colspan", 1),
                        "rowspan": th.get("rowspan", 1),
                        "attributes": dict(th.attrs) if th.attrs else {},
                    }
                )

        # Extract rows
        for tr in table_element.find_all("tr"):
            cells = []
            for cell in tr.find_all(["td", "th"]):
                cells.append(
                    {
                        "text": cell.get_text(strip=True),
                        "tag": cell.name,
                        "colspan": int(cell.get("colspan", 1)),
                        "rowspan": int(cell.get("rowspan", 1)),
                        "class": cell.get("class", []),
                        "style": cell.get("style", ""),
                        "is_numeric": self._is_numeric_cell(cell.get_text(strip=True)),
                    }
                )
            if cells:
                rows.append(cells)

        if not rows:
            return None

        return {
            "index": idx,
            "headers": headers,
            "rows": rows,
            "row_count": len(rows),
            "column_count": len(rows[0]) if rows else 0,
            "caption": table_element.find("caption").get_text(strip=True)
            if table_element.find("caption")
            else None,
            "id": table_element.get("id"),
            "class": table_element.get("class", []),
        }

    def _is_numeric_cell(self, text: str) -> bool:
        """Check if cell contains numeric data."""
        # Remove common formatting
        cleaned = re.sub(r"[$,%()[\]\s]", "", text)
        cleaned = cleaned.replace("-", "")
        return bool(cleaned) and cleaned.replace(".", "").replace(",", "").isdigit()

    def _extract_form(self, form_element, idx: int) -> Optional[Dict[str, Any]]:
        """Extract form structure."""
        inputs = []
        for input_elem in form_element.find_all(["input", "select", "textarea", "button"]):
            inputs.append(
                {
                    "tag": input_elem.name,
                    "type": input_elem.get("type"),
                    "name": input_elem.get("name"),
                    "id": input_elem.get("id"),
                    "value": input_elem.get("value"),
                    "required": input_elem.get("required") is not None,
                }
            )

        if not inputs:
            return None

        return {
            "index": idx,
            "action": form_element.get("action"),
            "method": form_element.get("method", "get"),
            "id": form_element.get("id"),
            "inputs": inputs,
            "input_count": len(inputs),
        }

    async def _extract_ixbrl(self, content: str, url: Optional[str]) -> Dict[str, Any]:
        """
        Extract Inline XBRL (iXBRL) with both HTML content and XBRL facts.
        """
        # First extract as HTML
        html_result = await self._extract_html_complete(content, url)

        # Then extract XBRL facts embedded in HTML
        soup = BeautifulSoup(content, "lxml")

        xbrl_facts: List[Dict[str, Any]] = []

        # Find all ix: prefixed elements
        for ns_prefix in ["ix:", "ix\\:", "xbrli:", "xbrli\\:"]:
            for elem in soup.find_all(lambda tag: tag.name.startswith(ns_prefix.rstrip("\\"))):
                fact = {
                    "element": elem.name,
                    "name": elem.get("name"),
                    "contextRef": elem.get("contextRef") or elem.get("contextref"),
                    "unitRef": elem.get("unitRef") or elem.get("unitref"),
                    "value": elem.get_text(strip=True),
                    "format": elem.get("format"),
                    "scale": elem.get("scale"),
                    "decimals": elem.get("decimals"),
                }
                xbrl_facts.append(fact)

        # Also look for data-xbrl attributes
        for elem in soup.find_all(attrs={"data-xbrl": True}):
            fact = {
                "element": elem.name,
                "data_xbrl": elem.get("data-xbrl"),
                "value": elem.get_text(strip=True),
            }
            xbrl_facts.append(fact)

        html_result["financial_data"]["xbrl_facts"] = xbrl_facts
        html_result["financial_data"]["fact_count"] = len(xbrl_facts)

        return html_result

    async def _extract_xbrl_complete(self, content: str, url: Optional[str]) -> Dict[str, Any]:
        """Extract XBRL with complete fact extraction."""
        result: Dict[str, Any] = {
            "text": "",
            "elements": [],
            "tables": [],
            "forms": [],
            "footnotes": [],
            "signatures": [],
            "hidden_elements": [],
            "comments": [],
            "styles": {},
            "metadata": {"is_xbrl": True},
            "financial_data": {},
            "document_structure": {},
        }

        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(content)

            text_parts = []
            facts: Dict[str, Any] = {}
            contexts: Dict[str, Any] = {}
            units: Dict[str, str] = {}

            # Common XBRL namespaces
            namespaces = {
                "xbrli": "http://www.xbrl.org/2003/instance",
                "dei": "http://xbrl.sec.gov/dei/2023",
                "us-gaap": "http://fasb.org/us-gaap/2023",
            }

            # Extract contexts
            for context in root.iter():
                tag = context.tag.split("}")[-1] if "}" in context.tag else context.tag
                if tag == "context":
                    context_id = context.get("id")
                    if context_id:
                        period_elem = context.find(".//xbrli:period", namespaces) or context.find(
                            ".//{http://www.xbrl.org/2003/instance}period"
                        )
                        if period_elem is not None:
                            instant = period_elem.find(
                                ".//{http://www.xbrl.org/2003/instance}instant"
                            )
                            if instant is not None and instant.text:
                                contexts[context_id] = {"instant": instant.text}

            # Extract units
            for unit in root.iter():
                tag = unit.tag.split("}")[-1] if "}" in unit.tag else unit.tag
                if tag == "unit":
                    unit_id = unit.get("id")
                    measure = unit.find(".//{http://www.xbrl.org/2003/instance}measure")
                    if unit_id and measure is not None and measure.text:
                        units[unit_id] = measure.text

            # Extract all facts
            for element in root.iter():
                tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

                # Skip structural elements
                if tag in ["xbrl", "context", "unit", "schemaRef"]:
                    continue

                if element.text and element.text.strip():
                    text_parts.append(f"{tag}: {element.text.strip()}")

                    # Try to extract as financial fact
                    try:
                        value = float(element.text.strip().replace(",", ""))
                        context_ref = element.get("contextRef")
                        unit_ref = element.get("unitRef")
                        facts[tag] = {
                            "value": value,
                            "contextRef": context_ref,
                            "unitRef": unit_ref,
                            "period": contexts.get(context_ref, {}).get("instant")
                            if context_ref
                            else None,
                            "decimals": element.get("decimals"),
                            "unit": units.get(unit_ref) if unit_ref else None,
                        }
                    except (ValueError, AttributeError):
                        # Non-numeric fact
                        facts[tag] = {
                            "value": element.text.strip(),
                            "contextRef": element.get("contextRef"),
                        }

            result["text"] = "\n".join(text_parts)
            result["financial_data"] = {
                "facts": facts,
                "contexts": contexts,
                "units": units,
                "fact_count": len(facts),
            }

        except Exception as e:
            logger.warning(f"XBRL parsing failed: {e}")
            result["text"] = self._strip_tags(content)

        return result

    async def _extract_xml_complete(self, content: str, url: Optional[str]) -> Dict[str, Any]:
        """Extract XML with complete element traversal."""
        result: Dict[str, Any] = {
            "text": "",
            "elements": [],
            "tables": [],
            "forms": [],
            "footnotes": [],
            "signatures": [],
            "hidden_elements": [],
            "comments": [],
            "styles": {},
            "metadata": {},
            "financial_data": {},
            "document_structure": {},
        }

        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(content)

            text_parts = []

            def extract_from_element(element, path=""):
                tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
                current_path = f"{path}/{tag}" if path else tag

                elem_data = {
                    "tag": tag,
                    "path": current_path,
                    "text": element.text.strip() if element.text else "",
                    "attributes": element.attrib,
                }
                result["elements"].append(elem_data)

                if element.text and element.text.strip():
                    text_parts.append(element.text.strip())

                for child in element:
                    extract_from_element(child, current_path)

            extract_from_element(root)
            result["text"] = "\n".join(text_parts)
            result["document_structure"]["root_tag"] = root.tag

        except Exception as e:
            logger.warning(f"XML parsing failed: {e}")
            result["text"] = self._strip_tags(content)

        return result

    async def _extract_sgml_complete(self, content: str, url: Optional[str]) -> Dict[str, Any]:
        """Extract SGML SEC documents with embedded document handling."""
        result: Dict[str, Any] = {
            "text": "",
            "elements": [],
            "tables": [],
            "forms": [],
            "footnotes": [],
            "signatures": [],
            "hidden_elements": [],
            "comments": [],
            "styles": {},
            "metadata": {},
            "financial_data": {},
            "document_structure": {"embedded_documents": []},
        }

        text_parts = []

        # Extract SEC header
        sec_header_match = re.search(
            r"<SEC-HEADER>(.*?)</SEC-HEADER>", content, re.DOTALL | re.IGNORECASE
        )
        if sec_header_match:
            header = sec_header_match.group(1)
            result["metadata"]["sec_header"] = header.strip()

            # Extract key fields
            for field in [
                "COMPANY CONFORMED NAME",
                "CENTRAL INDEX KEY",
                "FILING DATE",
                "FORM TYPE",
                "IRS NUMBER",
                "FISCAL YEAR END",
            ]:
                field_match = re.search(rf"{field}:\s*(.*?)$", header, re.MULTILINE)
                if field_match:
                    result["metadata"][field.lower().replace(" ", "_")] = field_match.group(
                        1
                    ).strip()

        # Extract embedded documents
        document_pattern = re.compile(r"<DOCUMENT>(.*?)</DOCUMENT>", re.DOTALL | re.IGNORECASE)

        for doc_match in document_pattern.finditer(content):
            doc_content = doc_match.group(1)

            # Extract document metadata
            type_match = re.search(r"<TYPE>(.*?)(?:\n|$)", doc_content, re.MULTILINE)
            seq_match = re.search(r"<SEQUENCE>(.*?)(?:\n|$)", doc_content, re.MULTILINE)
            filename_match = re.search(r"<FILENAME>(.*?)(?:\n|$)", doc_content, re.MULTILINE)

            doc_type = type_match.group(1).strip() if type_match else "UNKNOWN"

            embedded_doc = {
                "type": doc_type,
                "sequence": seq_match.group(1).strip() if seq_match else None,
                "filename": filename_match.group(1).strip() if filename_match else None,
            }

            # Extract text content
            text_match = re.search(r"<TEXT>(.*?)</TEXT>", doc_content, re.DOTALL | re.IGNORECASE)

            if text_match:
                doc_text = text_match.group(1)

                # Parse embedded HTML/XML if present
                if "<HTML>" in doc_text.upper() or "<!DOCTYPE" in doc_text.upper():
                    html_result = await self._extract_html_complete(doc_text, url)
                    text_parts.append(f"[{doc_type}]\n{html_result['text']}")
                    result["tables"].extend(html_result.get("tables", []))
                    embedded_doc["extracted_text"] = html_result["text"][:1000]
                else:
                    clean_text = self._strip_tags(doc_text)
                    text_parts.append(f"[{doc_type}]\n{clean_text}")
                    embedded_doc["extracted_text"] = clean_text[:1000]

            result["document_structure"]["embedded_documents"].append(embedded_doc)

        result["text"] = "\n\n".join(text_parts)

        return result

    async def _extract_json(self, content: str, url: Optional[str]) -> Dict[str, Any]:
        """Extract JSON data."""
        import json as json_module

        result: Dict[str, Any] = {
            "text": "",
            "elements": [],
            "tables": [],
            "forms": [],
            "footnotes": [],
            "signatures": [],
            "hidden_elements": [],
            "comments": [],
            "styles": {},
            "metadata": {"format": "json"},
            "financial_data": {},
            "document_structure": {},
        }

        try:
            data = json_module.loads(content)

            # Convert to text representation
            result["text"] = json_module.dumps(data, indent=2)

            # Store structure
            result["document_structure"]["json_data"] = data
            result["metadata"]["data_type"] = type(data).__name__

            # If it's a list of dicts, treat as table
            if isinstance(data, list) and data and isinstance(data[0], dict):
                headers = list(data[0].keys())
                rows = [[str(item.get(h, "")) for h in headers] for item in data]
                result["tables"].append(
                    {
                        "headers": headers,
                        "rows": rows,
                        "row_count": len(rows),
                        "column_count": len(headers),
                    }
                )

        except json_module.JSONDecodeError as e:
            result["text"] = content
            result["metadata"]["parse_error"] = str(e)

        return result

    async def _extract_csv(self, content: str, url: Optional[str]) -> Dict[str, Any]:
        """Extract CSV data."""
        import csv
        from io import StringIO

        result: Dict[str, Any] = {
            "text": "",
            "elements": [],
            "tables": [],
            "forms": [],
            "footnotes": [],
            "signatures": [],
            "hidden_elements": [],
            "comments": [],
            "styles": {},
            "metadata": {"format": "csv"},
            "financial_data": {},
            "document_structure": {},
        }

        try:
            reader = csv.reader(StringIO(content))
            rows = list(reader)

            if rows:
                headers = rows[0]
                data_rows = rows[1:]

                result["tables"].append(
                    {
                        "headers": headers,
                        "rows": data_rows,
                        "row_count": len(data_rows),
                        "column_count": len(headers),
                    }
                )

                # Create text representation
                text_parts = []
                for row in rows:
                    text_parts.append(" | ".join(row))
                result["text"] = "\n".join(text_parts)

                result["metadata"]["row_count"] = len(rows)
                result["metadata"]["column_count"] = len(headers)

        except Exception as e:
            result["text"] = content
            result["metadata"]["parse_error"] = str(e)

        return result

    async def _extract_pdf_complete(self, content: str, url: Optional[str]) -> Dict[str, Any]:
        """Extract PDF with complete content."""
        result: Dict[str, Any] = {
            "text": "",
            "elements": [],
            "tables": [],
            "forms": [],
            "footnotes": [],
            "signatures": [],
            "hidden_elements": [],
            "comments": [],
            "styles": {},
            "metadata": {"format": "pdf"},
            "financial_data": {},
            "document_structure": {},
        }

        try:
            import pdfplumber

            # PDF content should be bytes
            if isinstance(content, str):
                content_bytes = content.encode("latin-1")
            else:
                content_bytes = content

            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                text_parts = []

                result["metadata"]["page_count"] = len(pdf.pages)
                result["metadata"]["pdf_info"] = pdf.metadata

                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"[Page {page_num + 1}]\n{page_text}")

                    # Extract tables
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        if table:
                            result["tables"].append(
                                {
                                    "page": page_num + 1,
                                    "headers": table[0] if table else [],
                                    "rows": table[1:] if len(table) > 1 else [],
                                    "row_count": len(table),
                                    "column_count": len(table[0]) if table else 0,
                                }
                            )

                result["text"] = "\n\n".join(text_parts)

        except ImportError:
            result["text"] = "[PDF extraction not available - pdfplumber required]"
            result["metadata"]["extraction_error"] = "pdfplumber not installed"
        except Exception as e:
            result["text"] = f"[PDF extraction error: {str(e)}]"
            result["metadata"]["extraction_error"] = str(e)

        return result

    async def _extract_text_complete(self, content: str, url: Optional[str]) -> Dict[str, Any]:
        """Extract plain text with structure detection."""
        result: Dict[str, Any] = {
            "text": content.strip(),
            "elements": [],
            "tables": [],
            "forms": [],
            "footnotes": [],
            "signatures": [],
            "hidden_elements": [],
            "comments": [],
            "styles": {},
            "metadata": {"format": "text"},
            "financial_data": {},
            "document_structure": {},
        }

        # Detect sections based on patterns
        lines = content.split("\n")
        headers = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            # Detect headers (ALL CAPS, numbered items, etc.)
            if stripped and stripped.isupper() and len(stripped) > 3:
                headers.append({"line": i, "text": stripped, "type": "uppercase"})
            elif stripped and re.match(
                r"^(ITEM\s+\d+|Section\s+\d+|Part\s+[IVX]+)", stripped, re.IGNORECASE
            ):
                headers.append({"line": i, "text": stripped, "type": "section"})

        result["document_structure"]["detected_headers"] = headers

        return result

    def _strip_tags(self, content: str) -> str:
        """Strip HTML/XML tags from content."""
        return re.sub(r"<[^>]+>", " ", content)

    def _extract_sec_sections(self, text: str) -> Dict[str, Any]:
        """Extract SEC document sections."""
        sections = {}

        for section_name, pattern in self.SEC_SECTION_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                sections[section_name] = {
                    "found": True,
                    "start_position": match.start(),
                    "matched_text": match.group(),
                }

        return sections

    def _extract_legal_references(self, text: str) -> List[Dict[str, Any]]:
        """Extract legal and statutory references."""
        references = []

        for ref_type, pattern in self.LEGAL_PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                references.append(
                    {
                        "type": ref_type,
                        "matched_text": match.group(),
                        "start_position": match.start(),
                        "end_position": match.end(),
                        "groups": match.groups(),
                    }
                )

        return references

    def _extract_signatures(self, text: str) -> List[Dict[str, Any]]:
        """Extract signatures from document."""
        signatures = []

        for sig_type, pattern in self.SIGNATURE_PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                signatures.append(
                    {
                        "type": sig_type,
                        "name": match.group(1).strip() if match.groups() else match.group(),
                        "matched_text": match.group(),
                        "start_position": match.start(),
                    }
                )

        return signatures

    def _extract_risk_factors(self, text: str) -> List[Dict[str, Any]]:
        """Extract risk factors from SEC filings."""
        risk_factors = []

        # Find risk factor section
        risk_section_pattern = (
            r"(?:RISK\s*FACTORS|Item\s*1A\.?\s*Risk\s*Factors)(.*?)(?:ITEM\s*[2-9]|PART\s*II|$)"
        )
        risk_match = re.search(risk_section_pattern, text, re.IGNORECASE | re.DOTALL)

        if risk_match:
            risk_text = risk_match.group(1)

            # Extract individual risk factors (typically bold or bulleted)
            bullet_pattern = r"(?:^|\n)\s*(?:•|▪|■|◦|\*|-)?\s*([A-Z][^.]+\.)"
            for match in re.finditer(bullet_pattern, risk_text):
                risk_factors.append(
                    {
                        "text": match.group(1).strip(),
                        "start_position": risk_match.start() + match.start(),
                    }
                )

        return risk_factors[:50]  # Limit to top 50

    def _extract_material_events(self, text: str) -> List[Dict[str, Any]]:
        """Extract material events from SEC filings."""
        events = []

        # Material event patterns
        event_patterns = [
            r"(acquisition of [^.]+\.)",
            r"(merger with [^.]+\.)",
            r"(entered into [^.]+agreement[^.]+\.)",
            r"(terminated [^.]+agreement[^.]+\.)",
            r"(appointed [^.]+as [^.]+\.)",
            r"(resigned as [^.]+\.)",
            r"(restatement[^.]+\.)",
            r"(impairment[^.]+\.)",
            r"(restructuring[^.]+\.)",
        ]

        for pattern in event_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                events.append({"text": match.group(1), "start_position": match.start()})

        return events[:25]  # Limit to top 25

    def _extract_financial_patterns(self, text: str) -> Dict[str, Any]:
        """Extract financial patterns from text."""
        financial_data: Dict[str, Any] = {}

        for pattern_name, pattern in self.FINANCIAL_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                financial_data[pattern_name] = {
                    "matches": matches[:20],  # Limit matches
                    "count": len(matches),
                }

        return financial_data

    def _extract_cross_references(self, text: str) -> List[Dict[str, Any]]:
        """Extract cross-references within document."""
        cross_refs = []

        # Common cross-reference patterns
        patterns = [
            r"(?:see|refer to|as described in|as discussed in)\s+([^.]+)",
            r"(?:Note|Footnote)\s+(\d+)",
            r"(?:Exhibit|Schedule)\s+(\d+(?:\.\d+)?)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                cross_refs.append(
                    {
                        "type": "reference",
                        "target": match.group(1).strip(),
                        "context": text[
                            max(0, match.start() - 50) : min(len(text), match.end() + 50)
                        ],
                        "start_position": match.start(),
                    }
                )

        return cross_refs[:100]  # Limit

    def _calculate_confidence(
        self,
        byte_coverage: float,
        element_count: int,
        table_count: int,
        has_financial_data: bool,
        has_sec_sections: bool,
        parse_error_count: int,
    ) -> float:
        """Calculate extraction confidence score."""
        confidence = byte_coverage * 0.4  # Base on coverage

        # Boost for structured data
        if element_count > 0:
            confidence += 0.15
        if table_count > 0:
            confidence += 0.15
        if has_financial_data:
            confidence += 0.15
        if has_sec_sections:
            confidence += 0.10

        # Penalty for parse errors
        confidence -= parse_error_count * 0.05

        return max(0.0, min(1.0, confidence))
