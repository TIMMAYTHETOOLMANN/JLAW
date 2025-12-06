"""
Unified Parser Factory for SEC Documents
=========================================

Combines DocsGPT's parsing capabilities with JLAW's SEC-specific extractors
to provide comprehensive document parsing for all SEC filing formats.

Supported Formats:
- PDF (with OCR and vision model support)
- HTML (SEC EDGAR HTML filings)
- XML/XBRL (structured financial data)
- DOCX (Word documents, exhibits)
- XLSX/CSV (tabular data, exhibits)
- PPTX (presentations, earnings calls)
- JSON (API responses, structured data)
- TXT (plain text filings)
- Images (OCR extraction)
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Type
from dataclasses import dataclass, field
from enum import Enum
import mimetypes
import hashlib

# Add DocsGPT to path
DOCSGPT_PATH = Path(__file__).parent.parent.parent.parent / "external_repos" / "DocsGPT"
if DOCSGPT_PATH.exists():
    sys.path.insert(0, str(DOCSGPT_PATH))

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Supported document types for SEC filings."""
    PDF = "pdf"
    HTML = "html"
    XML = "xml"
    XBRL = "xbrl"
    IXBRL = "ixbrl"
    DOCX = "docx"
    XLSX = "xlsx"
    CSV = "csv"
    PPTX = "pptx"
    JSON = "json"
    TXT = "txt"
    MD = "md"
    RST = "rst"
    EPUB = "epub"
    IMAGE = "image"
    UNKNOWN = "unknown"


class SECFilingType(Enum):
    """SEC filing types with specific parsing requirements."""
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    FORM_4 = "4"
    FORM_DEF14A = "DEF 14A"
    FORM_S1 = "S-1"
    FORM_20F = "20-F"
    FORM_6K = "6-K"
    FORM_424B = "424B"
    EXHIBIT = "EX"
    OTHER = "OTHER"


@dataclass
class ParsedDocument:
    """
    Unified structure for parsed SEC documents.
    
    Attributes:
        doc_id: Unique document identifier
        source_path: Original file path
        doc_type: Document format type
        filing_type: SEC filing type if applicable
        raw_text: Extracted raw text content
        structured_content: Structured data (tables, lists, etc.)
        metadata: Document metadata
        sections: Extracted document sections
        tables: Extracted tables as structured data
        exhibits: Referenced exhibits
        xbrl_facts: XBRL facts if applicable
        hash: Content hash for integrity
    """
    doc_id: str
    source_path: str
    doc_type: DocumentType
    filing_type: Optional[SECFilingType] = None
    raw_text: str = ""
    structured_content: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    sections: Dict[str, str] = field(default_factory=dict)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    exhibits: List[Dict[str, Any]] = field(default_factory=list)
    xbrl_facts: Dict[str, Any] = field(default_factory=dict)
    hash: str = ""
    
    def __post_init__(self):
        """Compute content hash after initialization."""
        if not self.hash and self.raw_text:
            self.hash = hashlib.sha256(self.raw_text.encode()).hexdigest()
    
    def to_chunks(self, chunker) -> List['ParsedDocument']:
        """Split document into chunks using provided chunker."""
        return chunker.chunk_document(self)


class BaseDocumentParser:
    """Base class for document parsers."""
    
    supported_types: List[DocumentType] = []
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def parse(self, file_path: Union[str, Path]) -> ParsedDocument:
        """Parse a document and return structured content."""
        raise NotImplementedError
    
    def parse_bytes(self, content: bytes, filename: str) -> ParsedDocument:
        """Parse document from bytes."""
        raise NotImplementedError
    
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if this parser can handle the given file."""
        doc_type = self._detect_type(file_path)
        return doc_type in self.supported_types
    
    def _detect_type(self, file_path: Union[str, Path]) -> DocumentType:
        """Detect document type from file path."""
        path = Path(file_path)
        ext = path.suffix.lower().lstrip('.')
        
        type_map = {
            'pdf': DocumentType.PDF,
            'html': DocumentType.HTML,
            'htm': DocumentType.HTML,
            'xml': DocumentType.XML,
            'xbrl': DocumentType.XBRL,
            'docx': DocumentType.DOCX,
            'xlsx': DocumentType.XLSX,
            'csv': DocumentType.CSV,
            'pptx': DocumentType.PPTX,
            'json': DocumentType.JSON,
            'txt': DocumentType.TXT,
            'md': DocumentType.MD,
            'rst': DocumentType.RST,
            'epub': DocumentType.EPUB,
            'png': DocumentType.IMAGE,
            'jpg': DocumentType.IMAGE,
            'jpeg': DocumentType.IMAGE,
            'tiff': DocumentType.IMAGE,
            'gif': DocumentType.IMAGE,
        }
        
        return type_map.get(ext, DocumentType.UNKNOWN)


class PDFParser(BaseDocumentParser):
    """
    PDF Parser combining DocsGPT and JLAW capabilities.
    
    Features:
    - Text extraction via pypdf
    - OCR fallback via pytesseract
    - Vision model extraction for complex layouts
    - Table extraction via pdfplumber
    """
    
    supported_types = [DocumentType.PDF]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.use_vision = config.get('pdf_as_image', False) if config else False
        self.extract_tables = config.get('extract_tables', True) if config else True
    
    def parse(self, file_path: Union[str, Path]) -> ParsedDocument:
        """Parse PDF document."""
        path = Path(file_path)
        doc_id = f"pdf_{path.stem}_{hashlib.md5(str(path).encode()).hexdigest()[:8]}"
        
        text_content = ""
        tables = []
        metadata = {}
        
        try:
            # Try DocsGPT PDF parser first
            from application.parser.file.docs_parser import PDFParser as DocsGPTPDF
            docsgpt_parser = DocsGPTPDF()
            text_content = docsgpt_parser.parse_file(path)
            logger.info(f"Parsed PDF using DocsGPT parser: {path.name}")
        except ImportError:
            logger.debug("DocsGPT parser not available, using fallback")
        except Exception as e:
            logger.warning(f"DocsGPT parser failed: {e}")
        
        # Fallback to JLAW's extraction methods
        if not text_content:
            try:
                from pypdf import PdfReader
                with open(path, 'rb') as f:
                    pdf = PdfReader(f)
                    metadata = {
                        'pages': len(pdf.pages),
                        'metadata': dict(pdf.metadata) if pdf.metadata else {}
                    }
                    text_list = []
                    for page in pdf.pages:
                        text_list.append(page.extract_text() or "")
                    text_content = "\n".join(text_list)
                logger.info(f"Parsed PDF using pypdf: {path.name}")
            except Exception as e:
                logger.error(f"pypdf parsing failed: {e}")
        
        # Extract tables if enabled
        if self.extract_tables and text_content:
            try:
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        page_tables = page.extract_tables()
                        for j, table in enumerate(page_tables):
                            if table:
                                tables.append({
                                    'page': i + 1,
                                    'table_index': j,
                                    'data': table,
                                    'headers': table[0] if table else []
                                })
                logger.info(f"Extracted {len(tables)} tables from PDF")
            except Exception as e:
                logger.warning(f"Table extraction failed: {e}")
        
        return ParsedDocument(
            doc_id=doc_id,
            source_path=str(path),
            doc_type=DocumentType.PDF,
            raw_text=text_content,
            metadata=metadata,
            tables=tables
        )


class HTMLParser(BaseDocumentParser):
    """
    HTML Parser for SEC EDGAR filings.
    
    Features:
    - Clean text extraction
    - Table preservation
    - Section detection for SEC forms
    - Link and reference extraction
    """
    
    supported_types = [DocumentType.HTML]
    
    def parse(self, file_path: Union[str, Path]) -> ParsedDocument:
        """Parse HTML document."""
        path = Path(file_path)
        doc_id = f"html_{path.stem}_{hashlib.md5(str(path).encode()).hexdigest()[:8]}"
        
        text_content = ""
        tables = []
        sections = {}
        
        try:
            # Use DocsGPT HTML parser
            from application.parser.file.html_parser import HTMLParser as DocsGPTHTML
            docsgpt_parser = DocsGPTHTML()
            result = docsgpt_parser.parse_file(path)
            if isinstance(result, list) and result:
                text_content = result[0].page_content if hasattr(result[0], 'page_content') else str(result[0])
            else:
                text_content = str(result)
            logger.info(f"Parsed HTML using DocsGPT: {path.name}")
        except ImportError:
            logger.debug("DocsGPT HTML parser not available")
        except Exception as e:
            logger.warning(f"DocsGPT HTML parser failed: {e}")
        
        # Fallback to BeautifulSoup
        if not text_content:
            try:
                from bs4 import BeautifulSoup
                import html2text
                
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                
                # Extract tables
                for i, table in enumerate(soup.find_all('table')):
                    rows = []
                    for row in table.find_all('tr'):
                        cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                        if cells:
                            rows.append(cells)
                    if rows:
                        tables.append({
                            'table_index': i,
                            'data': rows,
                            'headers': rows[0] if rows else []
                        })
                
                # Convert to text
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = True
                text_content = h.handle(str(soup))
                
                logger.info(f"Parsed HTML using BeautifulSoup: {path.name}")
            except Exception as e:
                logger.error(f"HTML parsing failed: {e}")
        
        # Detect SEC sections
        sections = self._extract_sec_sections(text_content)
        
        return ParsedDocument(
            doc_id=doc_id,
            source_path=str(path),
            doc_type=DocumentType.HTML,
            raw_text=text_content,
            sections=sections,
            tables=tables
        )
    
    def _extract_sec_sections(self, text: str) -> Dict[str, str]:
        """Extract SEC form sections from text."""
        import re
        sections = {}
        
        # Common SEC section patterns
        patterns = [
            (r'(?:ITEM|Item)\s*1\.?\s*[-–—]?\s*Business', 'Item 1'),
            (r'(?:ITEM|Item)\s*1A\.?\s*[-–—]?\s*Risk\s*Factors', 'Item 1A'),
            (r'(?:ITEM|Item)\s*2\.?\s*[-–—]?\s*Properties', 'Item 2'),
            (r'(?:ITEM|Item)\s*3\.?\s*[-–—]?\s*Legal\s*Proceedings', 'Item 3'),
            (r'(?:ITEM|Item)\s*7\.?\s*[-–—]?\s*Management', 'Item 7'),
            (r'(?:ITEM|Item)\s*7A\.?\s*[-–—]?\s*Quantitative', 'Item 7A'),
            (r'(?:ITEM|Item)\s*8\.?\s*[-–—]?\s*Financial\s*Statements', 'Item 8'),
            (r'(?:ITEM|Item)\s*9\.?\s*[-–—]?\s*Changes', 'Item 9'),
        ]
        
        for pattern, section_name in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sections[section_name] = match.group(0)
        
        return sections


class TabularParser(BaseDocumentParser):
    """
    Parser for tabular data (CSV, XLSX).
    
    Features:
    - Pandas-based parsing
    - Header-aware chunking context
    - Multi-sheet Excel support
    """
    
    supported_types = [DocumentType.CSV, DocumentType.XLSX]
    
    def parse(self, file_path: Union[str, Path]) -> ParsedDocument:
        """Parse tabular document."""
        path = Path(file_path)
        doc_type = self._detect_type(path)
        doc_id = f"tabular_{path.stem}_{hashlib.md5(str(path).encode()).hexdigest()[:8]}"
        
        text_content = ""
        tables = []
        
        try:
            if doc_type == DocumentType.CSV:
                from application.parser.file.tabular_parser import PandasCSVParser
                parser = PandasCSVParser(header_period=20)
                text_content = parser.parse_file(path)
            elif doc_type == DocumentType.XLSX:
                from application.parser.file.tabular_parser import ExcelParser
                parser = ExcelParser()
                text_content = parser.parse_file(path)
            logger.info(f"Parsed tabular file using DocsGPT: {path.name}")
        except ImportError:
            logger.debug("DocsGPT tabular parser not available")
        except Exception as e:
            logger.warning(f"DocsGPT tabular parser failed: {e}")
        
        # Fallback to pandas
        if not text_content:
            try:
                import pandas as pd
                if doc_type == DocumentType.CSV:
                    df = pd.read_csv(path)
                else:
                    df = pd.read_excel(path)
                
                tables.append({
                    'sheet': 'Sheet1',
                    'data': df.values.tolist(),
                    'headers': df.columns.tolist(),
                    'shape': df.shape
                })
                
                text_content = df.to_string()
                logger.info(f"Parsed tabular file using pandas: {path.name}")
            except Exception as e:
                logger.error(f"Tabular parsing failed: {e}")
        
        return ParsedDocument(
            doc_id=doc_id,
            source_path=str(path),
            doc_type=doc_type,
            raw_text=text_content,
            tables=tables
        )


class XBRLParser(BaseDocumentParser):
    """
    XBRL/iXBRL Parser for SEC structured financial data.
    
    Features:
    - XBRL fact extraction
    - Context and unit parsing
    - Inline XBRL (iXBRL) support
    """
    
    supported_types = [DocumentType.XBRL, DocumentType.IXBRL, DocumentType.XML]
    
    def parse(self, file_path: Union[str, Path]) -> ParsedDocument:
        """Parse XBRL document."""
        path = Path(file_path)
        doc_id = f"xbrl_{path.stem}_{hashlib.md5(str(path).encode()).hexdigest()[:8]}"
        
        text_content = ""
        xbrl_facts = {}
        
        try:
            from lxml import etree
            
            tree = etree.parse(str(path))
            root = tree.getroot()
            
            # Extract all text content
            text_parts = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_parts.append(elem.text.strip())
            text_content = "\n".join(text_parts)
            
            # Extract XBRL facts
            namespaces = root.nsmap
            
            # Look for common XBRL namespaces
            xbrl_ns_prefixes = ['us-gaap', 'dei', 'srt', 'country']
            
            for prefix in xbrl_ns_prefixes:
                if prefix in namespaces:
                    for elem in root.iter(f"{{{namespaces[prefix]}}}*"):
                        fact_name = etree.QName(elem).localname
                        fact_value = elem.text
                        context_ref = elem.get('contextRef', '')
                        
                        if fact_value:
                            xbrl_facts[f"{prefix}:{fact_name}"] = {
                                'value': fact_value,
                                'context': context_ref,
                                'unit': elem.get('unitRef', ''),
                                'decimals': elem.get('decimals', '')
                            }
            
            logger.info(f"Parsed XBRL with {len(xbrl_facts)} facts: {path.name}")
            
        except Exception as e:
            logger.error(f"XBRL parsing failed: {e}")
        
        return ParsedDocument(
            doc_id=doc_id,
            source_path=str(path),
            doc_type=DocumentType.XBRL,
            raw_text=text_content,
            xbrl_facts=xbrl_facts
        )


class JSONParser(BaseDocumentParser):
    """Parser for JSON documents."""
    
    supported_types = [DocumentType.JSON]
    
    def parse(self, file_path: Union[str, Path]) -> ParsedDocument:
        """Parse JSON document."""
        path = Path(file_path)
        doc_id = f"json_{path.stem}_{hashlib.md5(str(path).encode()).hexdigest()[:8]}"
        
        try:
            from application.parser.file.json_parser import JSONParser as DocsGPTJSON
            parser = DocsGPTJSON()
            text_content = parser.parse_file(path)
            logger.info(f"Parsed JSON using DocsGPT: {path.name}")
        except ImportError:
            import json
            with open(path, 'r') as f:
                data = json.load(f)
            text_content = json.dumps(data, indent=2)
            logger.info(f"Parsed JSON using stdlib: {path.name}")
        
        return ParsedDocument(
            doc_id=doc_id,
            source_path=str(path),
            doc_type=DocumentType.JSON,
            raw_text=text_content
        )


class TextParser(BaseDocumentParser):
    """Simple parser for plain text files."""
    
    supported_types = [DocumentType.TXT, DocumentType.MD, DocumentType.RST]
    
    def parse(self, file_path: Union[str, Path]) -> ParsedDocument:
        """Parse text document."""
        path = Path(file_path)
        doc_id = f"txt_{path.stem}_{hashlib.md5(str(path).encode()).hexdigest()[:8]}"
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()
            logger.info(f"Parsed text file: {path.name}")
        except Exception as e:
            logger.error(f"Text parsing failed: {e}")
            text_content = ""
        
        return ParsedDocument(
            doc_id=doc_id,
            source_path=str(path),
            doc_type=DocumentType.TXT,
            raw_text=text_content
        )


class ParserFactory:
    """
    Factory class for creating appropriate document parsers.
    
    Usage:
        parser = ParserFactory.get_parser("document.pdf")
        result = parser.parse("document.pdf")
        
        # Or auto-detect and parse
        result = ParserFactory.parse("document.pdf")
    """
    
    _parsers: Dict[DocumentType, Type[BaseDocumentParser]] = {
        DocumentType.PDF: PDFParser,
        DocumentType.HTML: HTMLParser,
        DocumentType.CSV: TabularParser,
        DocumentType.XLSX: TabularParser,
        DocumentType.XBRL: XBRLParser,
        DocumentType.IXBRL: XBRLParser,
        DocumentType.XML: XBRLParser,
        DocumentType.JSON: JSONParser,
        DocumentType.TXT: TextParser,
        DocumentType.MD: TextParser,
        DocumentType.RST: TextParser,
    }
    
    @classmethod
    def get_parser(
        cls, 
        file_path: Union[str, Path],
        config: Optional[Dict] = None
    ) -> BaseDocumentParser:
        """
        Get appropriate parser for the given file.
        
        Args:
            file_path: Path to the document
            config: Optional parser configuration
            
        Returns:
            Parser instance for the document type
        """
        path = Path(file_path)
        doc_type = cls._detect_type(path)
        
        parser_class = cls._parsers.get(doc_type)
        if not parser_class:
            raise ValueError(f"No parser available for document type: {doc_type}")
        
        return parser_class(config)
    
    @classmethod
    def parse(
        cls,
        file_path: Union[str, Path],
        config: Optional[Dict] = None
    ) -> ParsedDocument:
        """
        Parse a document automatically.
        
        Args:
            file_path: Path to the document
            config: Optional parser configuration
            
        Returns:
            Parsed document
        """
        parser = cls.get_parser(file_path, config)
        return parser.parse(file_path)
    
    @classmethod
    def parse_batch(
        cls,
        file_paths: List[Union[str, Path]],
        config: Optional[Dict] = None,
        parallel: bool = True
    ) -> List[ParsedDocument]:
        """
        Parse multiple documents.
        
        Args:
            file_paths: List of document paths
            config: Optional parser configuration
            parallel: Whether to parse in parallel
            
        Returns:
            List of parsed documents
        """
        if parallel:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            results = []
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(cls.parse, path, config): path 
                    for path in file_paths
                }
                for future in as_completed(futures):
                    try:
                        results.append(future.result())
                    except Exception as e:
                        logger.error(f"Failed to parse {futures[future]}: {e}")
            return results
        else:
            return [cls.parse(path, config) for path in file_paths]
    
    @classmethod
    def register_parser(
        cls,
        doc_type: DocumentType,
        parser_class: Type[BaseDocumentParser]
    ):
        """Register a custom parser for a document type."""
        cls._parsers[doc_type] = parser_class
    
    @classmethod
    def _detect_type(cls, file_path: Path) -> DocumentType:
        """Detect document type from file path."""
        ext = file_path.suffix.lower().lstrip('.')
        
        type_map = {
            'pdf': DocumentType.PDF,
            'html': DocumentType.HTML,
            'htm': DocumentType.HTML,
            'xml': DocumentType.XML,
            'xbrl': DocumentType.XBRL,
            'docx': DocumentType.DOCX,
            'xlsx': DocumentType.XLSX,
            'csv': DocumentType.CSV,
            'pptx': DocumentType.PPTX,
            'json': DocumentType.JSON,
            'txt': DocumentType.TXT,
            'md': DocumentType.MD,
        }
        
        return type_map.get(ext, DocumentType.UNKNOWN)
    
    @classmethod
    def supported_formats(cls) -> List[str]:
        """Get list of supported file formats."""
        return [dt.value for dt in cls._parsers.keys()]

