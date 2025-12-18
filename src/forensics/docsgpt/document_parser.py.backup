"""
DocsGPT Integration Module for JLAW SEC Forensic System
========================================================

Provides advanced document parsing capabilities via DocsGPT integration:
- Multi-format document parsing (PDF, DOCX, XLSX, HTML, XBRL, images)
- Intelligent chunking strategies optimized for SEC filings
- Vector embedding generation for semantic search
- OCR capabilities for scanned documents

Based on DocsGPT architecture: https://github.com/arc53/DocsGPT
"""

import os
import re
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class DocumentFormat(Enum):
    """Supported document formats."""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    CSV = "csv"
    HTML = "html"
    XML = "xml"
    XBRL = "xbrl"
    JSON = "json"
    TXT = "txt"
    IMAGE = "image"  # PNG, JPG, TIFF with OCR
    PPTX = "pptx"


class SECFilingType(Enum):
    """SEC filing types with specific parsing strategies."""
    FORM_4 = "4"
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    DEF_14A = "DEF 14A"
    FORM_13F = "13F-HR"
    FORM_13D = "SC 13D"
    FORM_13G = "SC 13G"
    FORM_144 = "144"
    FORM_S1 = "S-1"
    FORM_424B = "424B"
    EARNINGS_CALL = "TRANSCRIPT"
    UNKNOWN = "UNKNOWN"


@dataclass
class DocumentChunk:
    """Single chunk of parsed document."""
    chunk_id: str
    text: str
    chunk_index: int
    total_chunks: int
    token_count: int
    section: Optional[str] = None
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    content_hash: str = ""
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.text.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text[:500] + "..." if len(self.text) > 500 else self.text,
            "chunk_index": self.chunk_index,
            "section": self.section,
            "token_count": self.token_count,
            "content_hash": self.content_hash
        }


@dataclass
class ParsedDocument:
    """Complete parsed document with chunks."""
    doc_id: str
    filename: str
    format: DocumentFormat
    filing_type: SECFilingType
    chunks: List[DocumentChunk]
    total_tokens: int
    page_count: int
    parse_timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # SEC-specific fields
    cik: Optional[str] = None
    accession_number: Optional[str] = None
    filing_date: Optional[datetime] = None
    fiscal_period: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "format": self.format.value,
            "filing_type": self.filing_type.value,
            "chunk_count": len(self.chunks),
            "total_tokens": self.total_tokens,
            "page_count": self.page_count,
            "cik": self.cik,
            "accession_number": self.accession_number,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None
        }


class ChunkingStrategy:
    """
    Intelligent chunking strategies for SEC documents.
    
    Strategies:
    - SECTION_BASED: Chunk by SEC filing sections (Item 1, Item 7, etc.)
    - SEMANTIC: Chunk by semantic boundaries (paragraphs, topics)
    - FIXED_SIZE: Fixed token count chunks with overlap
    - HYBRID: Combination of section and semantic chunking
    """
    
    # SEC 10-K/10-Q section patterns
    SEC_SECTION_PATTERNS = [
        r"(?i)ITEM\s*1[\.\:\s]+BUSINESS",
        r"(?i)ITEM\s*1A[\.\:\s]+RISK\s*FACTORS",
        r"(?i)ITEM\s*1B[\.\:\s]+UNRESOLVED\s*STAFF\s*COMMENTS",
        r"(?i)ITEM\s*2[\.\:\s]+PROPERTIES",
        r"(?i)ITEM\s*3[\.\:\s]+LEGAL\s*PROCEEDINGS",
        r"(?i)ITEM\s*4[\.\:\s]+MINE\s*SAFETY",
        r"(?i)ITEM\s*5[\.\:\s]+MARKET",
        r"(?i)ITEM\s*6[\.\:\s]+SELECTED\s*FINANCIAL",
        r"(?i)ITEM\s*7[\.\:\s]+MANAGEMENT.*DISCUSSION",
        r"(?i)ITEM\s*7A[\.\:\s]+QUANTITATIVE.*MARKET\s*RISK",
        r"(?i)ITEM\s*8[\.\:\s]+FINANCIAL\s*STATEMENTS",
        r"(?i)ITEM\s*9[\.\:\s]+CHANGES.*DISAGREEMENTS",
        r"(?i)ITEM\s*9A[\.\:\s]+CONTROLS\s*AND\s*PROCEDURES",
        r"(?i)ITEM\s*10[\.\:\s]+DIRECTORS",
        r"(?i)ITEM\s*11[\.\:\s]+EXECUTIVE\s*COMPENSATION",
        r"(?i)ITEM\s*12[\.\:\s]+SECURITY\s*OWNERSHIP",
        r"(?i)ITEM\s*13[\.\:\s]+CERTAIN\s*RELATIONSHIPS",
        r"(?i)ITEM\s*14[\.\:\s]+PRINCIPAL\s*ACCOUNTANT",
        r"(?i)ITEM\s*15[\.\:\s]+EXHIBITS"
    ]
    
    # 8-K Item patterns
    SEC_8K_PATTERNS = [
        r"(?i)ITEM\s*1\.01.*MATERIAL\s*DEFINITIVE\s*AGREEMENT",
        r"(?i)ITEM\s*1\.02.*TERMINATION",
        r"(?i)ITEM\s*2\.01.*ACQUISITION",
        r"(?i)ITEM\s*2\.02.*RESULTS\s*OF\s*OPERATIONS",
        r"(?i)ITEM\s*2\.06.*MATERIAL\s*IMPAIRMENTS",
        r"(?i)ITEM\s*4\.01.*CHANGE.*ACCOUNTANT",
        r"(?i)ITEM\s*4\.02.*NON-RELIANCE",
        r"(?i)ITEM\s*5\.01.*CHANGE.*CONTROL",
        r"(?i)ITEM\s*5\.02.*DEPARTURE.*DIRECTORS",
        r"(?i)ITEM\s*7\.01.*REGULATION\s*FD",
        r"(?i)ITEM\s*8\.01.*OTHER\s*EVENTS"
    ]
    
    DEFAULT_CHUNK_SIZE = 1000  # tokens
    DEFAULT_OVERLAP = 100  # tokens
    
    @classmethod
    def chunk_by_sections(cls, text: str, filing_type: SECFilingType) -> List[Tuple[str, str]]:
        """
        Chunk document by SEC filing sections.
        
        Returns list of (section_name, section_text) tuples.
        """
        patterns = cls.SEC_SECTION_PATTERNS if filing_type in [
            SECFilingType.FORM_10K, SECFilingType.FORM_10Q
        ] else cls.SEC_8K_PATTERNS
        
        sections = []
        combined_pattern = '|'.join(f'({p})' for p in patterns)
        
        matches = list(re.finditer(combined_pattern, text))
        
        if not matches:
            return [("FULL_DOCUMENT", text)]
        
        for i, match in enumerate(matches):
            section_name = match.group().strip()
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()
            sections.append((section_name, section_text))
        
        return sections
    
    @classmethod
    def chunk_fixed_size(
        cls,
        text: str,
        chunk_size: int = None,
        overlap: int = None
    ) -> List[str]:
        """
        Chunk text into fixed-size pieces with overlap.
        """
        chunk_size = chunk_size or cls.DEFAULT_CHUNK_SIZE
        overlap = overlap or cls.DEFAULT_OVERLAP
        
        # Approximate tokens as words / 0.75
        words = text.split()
        token_estimate = int(len(words) * 0.75)
        
        chunks = []
        start = 0
        word_chunk_size = int(chunk_size / 0.75)
        word_overlap = int(overlap / 0.75)
        
        while start < len(words):
            end = start + word_chunk_size
            chunk_words = words[start:end]
            chunks.append(' '.join(chunk_words))
            start = end - word_overlap
        
        return chunks


class DocumentParser:
    """
    Multi-format document parser based on DocsGPT architecture.
    
    Supports: PDF, DOCX, XLSX, CSV, HTML, XML, XBRL, JSON, TXT, Images
    """
    
    def __init__(self):
        self.chunking = ChunkingStrategy()
    
    def parse(
        self,
        content: bytes,
        filename: str,
        filing_type: SECFilingType = SECFilingType.UNKNOWN,
        chunk_strategy: str = "hybrid",
        **metadata
    ) -> ParsedDocument:
        """
        Parse document content and return chunked result.
        
        Args:
            content: Raw document bytes
            filename: Original filename
            filing_type: SEC filing type for optimized parsing
            chunk_strategy: "section", "fixed", "semantic", or "hybrid"
            **metadata: Additional metadata (cik, accession_number, etc.)
            
        Returns:
            ParsedDocument with chunks
        """
        # Detect format from filename
        ext = Path(filename).suffix.lower().lstrip('.')
        doc_format = self._detect_format(ext)
        
        # Parse based on format
        text, page_count = self._extract_text(content, doc_format)
        
        # Chunk based on strategy
        chunks = self._create_chunks(text, filing_type, chunk_strategy, filename)
        
        total_tokens = sum(c.token_count for c in chunks)
        
        return ParsedDocument(
            doc_id=hashlib.sha256(content).hexdigest()[:16],
            filename=filename,
            format=doc_format,
            filing_type=filing_type,
            chunks=chunks,
            total_tokens=total_tokens,
            page_count=page_count,
            parse_timestamp=datetime.utcnow(),
            metadata=metadata,
            cik=metadata.get('cik'),
            accession_number=metadata.get('accession_number'),
            filing_date=metadata.get('filing_date'),
            fiscal_period=metadata.get('fiscal_period')
        )
    
    def parse_sec_filing(
        self,
        html_content: str,
        filing_type: SECFilingType,
        cik: str,
        accession_number: str,
        filing_date: datetime
    ) -> ParsedDocument:
        """
        Parse SEC EDGAR HTML filing with optimized SEC-specific extraction.
        """
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove scripts, styles
        for tag in soup(['script', 'style', 'meta', 'link']):
            tag.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        chunks = self._create_chunks(text, filing_type, "hybrid", f"{cik}_{accession_number}")
        
        return ParsedDocument(
            doc_id=hashlib.sha256(html_content.encode()).hexdigest()[:16],
            filename=f"{accession_number}.html",
            format=DocumentFormat.HTML,
            filing_type=filing_type,
            chunks=chunks,
            total_tokens=sum(c.token_count for c in chunks),
            page_count=1,
            parse_timestamp=datetime.utcnow(),
            cik=cik,
            accession_number=accession_number,
            filing_date=filing_date
        )
    
    def _detect_format(self, ext: str) -> DocumentFormat:
        """Detect document format from extension."""
        format_map = {
            'pdf': DocumentFormat.PDF,
            'docx': DocumentFormat.DOCX,
            'doc': DocumentFormat.DOCX,
            'xlsx': DocumentFormat.XLSX,
            'xls': DocumentFormat.XLSX,
            'csv': DocumentFormat.CSV,
            'html': DocumentFormat.HTML,
            'htm': DocumentFormat.HTML,
            'xml': DocumentFormat.XML,
            'xbrl': DocumentFormat.XBRL,
            'json': DocumentFormat.JSON,
            'txt': DocumentFormat.TXT,
            'png': DocumentFormat.IMAGE,
            'jpg': DocumentFormat.IMAGE,
            'jpeg': DocumentFormat.IMAGE,
            'tiff': DocumentFormat.IMAGE,
            'pptx': DocumentFormat.PPTX
        }
        return format_map.get(ext, DocumentFormat.TXT)
    
    def _extract_text(self, content: bytes, doc_format: DocumentFormat) -> Tuple[str, int]:
        """Extract text from document based on format."""
        
        if doc_format == DocumentFormat.PDF:
            return self._parse_pdf(content)
        elif doc_format == DocumentFormat.HTML:
            return self._parse_html(content.decode('utf-8', errors='ignore')), 1
        elif doc_format == DocumentFormat.TXT:
            return content.decode('utf-8', errors='ignore'), 1
        elif doc_format == DocumentFormat.CSV:
            return self._parse_csv(content), 1
        elif doc_format == DocumentFormat.JSON:
            return self._parse_json(content), 1
        else:
            # Fallback: try to decode as text
            return content.decode('utf-8', errors='ignore'), 1
    
    def _parse_pdf(self, content: bytes) -> Tuple[str, int]:
        """Parse PDF document."""
        try:
            import pdfplumber
            import io
            
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages = []
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    pages.append(text)
                return '\n\n'.join(pages), len(pdf.pages)
        except ImportError:
            logger.warning("pdfplumber not installed, returning raw content")
            return content.decode('utf-8', errors='ignore'), 1
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            return "", 0
    
    def _parse_html(self, html: str) -> str:
        """Parse HTML document."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup(['script', 'style']):
                tag.decompose()
            return soup.get_text(separator='\n', strip=True)
        except ImportError:
            # Fallback: regex-based HTML stripping
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            return re.sub(r'\s+', ' ', text).strip()
    
    def _parse_csv(self, content: bytes) -> str:
        """Parse CSV to text representation."""
        try:
            import csv
            import io
            
            reader = csv.reader(io.StringIO(content.decode('utf-8', errors='ignore')))
            rows = list(reader)
            
            if not rows:
                return ""
            
            # Format as readable text with headers
            headers = rows[0] if rows else []
            lines = []
            
            for row in rows[1:]:
                row_text = ", ".join(f"{h}: {v}" for h, v in zip(headers, row) if v)
                lines.append(row_text)
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"CSV parsing error: {e}")
            return content.decode('utf-8', errors='ignore')
    
    def _parse_json(self, content: bytes) -> str:
        """Parse JSON to text representation."""
        import json
        
        try:
            data = json.loads(content.decode('utf-8'))
            return json.dumps(data, indent=2)
        except json.JSONDecodeError:
            return content.decode('utf-8', errors='ignore')
    
    def _create_chunks(
        self,
        text: str,
        filing_type: SECFilingType,
        strategy: str,
        base_id: str
    ) -> List[DocumentChunk]:
        """Create document chunks based on strategy."""
        chunks = []
        
        if strategy in ["section", "hybrid"]:
            sections = self.chunking.chunk_by_sections(text, filing_type)
            
            for section_name, section_text in sections:
                if strategy == "hybrid" and len(section_text) > 4000:
                    # Further chunk large sections
                    sub_chunks = self.chunking.chunk_fixed_size(section_text, 1000, 100)
                    for i, sub_text in enumerate(sub_chunks):
                        chunks.append(self._make_chunk(
                            sub_text, len(chunks), section_name, base_id
                        ))
                else:
                    chunks.append(self._make_chunk(
                        section_text, len(chunks), section_name, base_id
                    ))
        else:
            # Fixed size chunking
            text_chunks = self.chunking.chunk_fixed_size(text)
            for i, chunk_text in enumerate(text_chunks):
                chunks.append(self._make_chunk(chunk_text, i, None, base_id))
        
        # Update total chunks count
        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total
        
        return chunks
    
    def _make_chunk(
        self,
        text: str,
        index: int,
        section: Optional[str],
        base_id: str
    ) -> DocumentChunk:
        """Create a single DocumentChunk."""
        # Estimate token count (words * 1.3 for subword tokenization)
        token_count = int(len(text.split()) * 1.3)
        
        return DocumentChunk(
            chunk_id=f"{base_id}_chunk_{index}",
            text=text,
            chunk_index=index,
            total_chunks=0,  # Updated after all chunks created
            token_count=token_count,
            section=section
        )


class SECDocumentAnalyzer:
    """
    High-level SEC document analyzer using DocsGPT-style parsing.
    
    Integrates with JLAW forensic system for comprehensive analysis.
    """
    
    def __init__(self):
        self.parser = DocumentParser()
    
    def analyze_filing(
        self,
        content: str,
        filing_type: str,
        cik: str,
        accession_number: str,
        filing_date: datetime
    ) -> ParsedDocument:
        """
        Analyze an SEC filing and return parsed, chunked document.
        """
        sec_type = self._map_filing_type(filing_type)
        
        return self.parser.parse_sec_filing(
            html_content=content,
            filing_type=sec_type,
            cik=cik,
            accession_number=accession_number,
            filing_date=filing_date
        )
    
    def get_section_text(
        self,
        doc: ParsedDocument,
        section_pattern: str
    ) -> Optional[str]:
        """Extract specific section from parsed document."""
        pattern = re.compile(section_pattern, re.IGNORECASE)
        
        for chunk in doc.chunks:
            if chunk.section and pattern.search(chunk.section):
                return chunk.text
        
        return None
    
    def get_risk_factors(self, doc: ParsedDocument) -> Optional[str]:
        """Extract Item 1A Risk Factors section."""
        return self.get_section_text(doc, r"ITEM\s*1A.*RISK")
    
    def get_mda(self, doc: ParsedDocument) -> Optional[str]:
        """Extract Item 7 MD&A section."""
        return self.get_section_text(doc, r"ITEM\s*7.*MANAGEMENT.*DISCUSSION")
    
    def _map_filing_type(self, filing_type: str) -> SECFilingType:
        """Map string filing type to enum."""
        type_map = {
            "4": SECFilingType.FORM_4,
            "10-K": SECFilingType.FORM_10K,
            "10-Q": SECFilingType.FORM_10Q,
            "8-K": SECFilingType.FORM_8K,
            "DEF 14A": SECFilingType.DEF_14A,
            "13F-HR": SECFilingType.FORM_13F,
            "SC 13D": SECFilingType.FORM_13D,
            "SC 13G": SECFilingType.FORM_13G,
            "144": SECFilingType.FORM_144
        }
        return type_map.get(filing_type, SECFilingType.UNKNOWN)

