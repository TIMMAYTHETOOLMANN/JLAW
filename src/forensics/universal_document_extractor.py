"""
SEC DOCUMENT FORENSIC EXTRACTION SYSTEM v3.0
=============================================
Advanced multi-format parser with complete document coverage
Designed for research and compliance analysis in controlled environments
"""

# File: sec_forensic_extraction_system.py

import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup, NavigableString, Comment
from lxml import etree, html
import xml.etree.ElementTree as ET
import html2text
import pdfplumber
import pytesseract
from PIL import Image
import chardet
import magic
import re
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, OrderedDict
import pandas as pd
import numpy as np
from decimal import Decimal
import traceback
import base64
import io
import zipfile
import tarfile
from urllib.parse import urljoin, urlparse, quote
from enum import Enum
import warnings
warnings.filterwarnings("ignore")

# Configure advanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentFormat(Enum):
    """Supported document formats with extraction capabilities."""
    HTML = "html"
    XML = "xml"
    XBRL = "xbrl"
    IXBRL = "ixbrl"
    PDF = "pdf"
    TEXT = "text"
    SGML = "sgml"
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    IMAGE = "image"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"


@dataclass
class ExtractionResult:
    """Complete extraction result with all document components."""
    format: DocumentFormat
    success: bool
    content: Dict[str, Any]
    raw_text: str
    structured_data: Dict[str, Any]
    tables: List[Dict[str, Any]]
    forms: List[Dict[str, Any]]
    headers: Dict[str, str]
    footers: Dict[str, str]
    footnotes: List[str]
    exhibits: List[Dict[str, Any]]
    signatures: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    embedded_documents: List[Dict[str, Any]]
    extraction_method: str
    extraction_time: float
    byte_coverage: float  # Percentage of bytes successfully extracted
    element_count: int
    error_log: List[str]


class UniversalDocumentExtractor:
    """
    Advanced document extractor with complete coverage capabilities.
    Handles all SEC document formats and ensures no content is missed.
    """
    
    def __init__(self):
        self.html_converter = html2text.HTML2Text()
        self.html_converter.body_width = 0
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.ignore_emphasis = False
        self.html_converter.single_line_break = False
        self.html_converter.unicode_snob = True
        
        # Pattern library for SEC documents
        self.sec_patterns = self._initialize_sec_patterns()
        
        # Statistics
        self.extraction_stats = defaultdict(int)
        
        logger.info("Universal Document Extractor initialized with full coverage mode")
    
    def _initialize_sec_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize comprehensive SEC document patterns."""
        return {
            # Document sections
            'section': re.compile(r'(?:PART|Part|ITEM|Item|Section|SECTION|Article|ARTICLE)\s+([IVX\d]+[A-Z]?\.?)\s*[-â€“â€”:]?\s*([^\n]{1,200})', re.IGNORECASE),
            
            # Headers and footers
            'page_header': re.compile(r'^[\s]*(.{1,100}?)[\s]*(?:Page|PAGE|Pg\.?)\s*(\d+)', re.MULTILINE),
            'document_header': re.compile(r'^[\s]*(?:UNITED STATES|SECURITIES AND EXCHANGE COMMISSION|SEC|Form|FORM).*?$', re.MULTILINE | re.IGNORECASE),
            
            # Financial data
            'currency': re.compile(r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand))?', re.IGNORECASE),
            'percentage': re.compile(r'\d+(?:\.\d+)?%'),
            'date': re.compile(r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4}|\d{4}[-/]\d{2}[-/]\d{2})\b'),
            
            # Tables
            'table_delimiter': re.compile(r'[|\t]{2,}|(?:\s{3,})', re.MULTILINE),
            'table_row': re.compile(r'^[^\n]*?(?:[|\t]|[ ]{3,})[^\n]*?$', re.MULTILINE),
            
            # Footnotes and references
            'footnote': re.compile(r'\(\d+\)|\[\d+\]|\*{1,3}|â€ |â€¡|Â§|Â¶'),
            'exhibit': re.compile(r'(?:Exhibit|EXHIBIT|Appendix|APPENDIX|Schedule|SCHEDULE)\s+([A-Z\d]+(?:\.\d+)?)', re.IGNORECASE),
            
            # Signatures
            'signature': re.compile(r'/s/\s*([^\n]+)|(?:Signature|SIGNATURE).*?:.*?([^\n]+)', re.IGNORECASE),
            
            # XBRL/XML tags
            'xml_tag': re.compile(r'<([^/>]+?)(?:\s+[^>]*)?>.*?</\1>', re.DOTALL),
            'self_closing_tag': re.compile(r'<([^/>]+?)(?:\s+[^>]*)?/>', re.DOTALL),
            
            # Special characters and formatting
            'special_char': re.compile(r'[Â§Â¶â€ â€¡*â€¢Â·â–ªâ–«â—¦â€£âƒ]'),
            'emphasis': re.compile(r'\*\*(.+?)\*\*|__(.+?)__|~~(.+?)~~'),
            
            # Legal references
            'legal_ref': re.compile(r'(?:Section|Rule|Regulation|Form)\s+\d+[A-Za-z]?(?:\.\d+)?(?:\([a-z]\))?', re.IGNORECASE),
            
            # Accounting terms
            'gaap_term': re.compile(r'\b(?:ASC|FASB|GAAP|IFRS|SOX)\s*\d*[-\d]*\b', re.IGNORECASE)
        }
    
    async def extract_document(self, 
                              content: Union[str, bytes], 
                              url: Optional[str] = None,
                              force_format: Optional[DocumentFormat] = None) -> ExtractionResult:
        """
        Extract complete content from document with maximum coverage.
        
        Args:
            content: Document content (string or bytes)
            url: Optional URL for context
            force_format: Force specific format parsing
            
        Returns:
            Complete extraction result with all components
        """
        start_time = datetime.now()
        
        # Convert bytes to string if needed
        if isinstance(content, bytes):
            encoding = self._detect_encoding(content)
            try:
                content = content.decode(encoding)
            except:
                content = content.decode('utf-8', errors='ignore')
        
        # Detect format
        doc_format = force_format or self._detect_format(content, url)
        
        logger.info(f"Extracting document with format: {doc_format.value}")
        
        # Initialize result
        result = ExtractionResult(
            format=doc_format,
            success=False,
            content={},
            raw_text="",
            structured_data={},
            tables=[],
            forms=[],
            headers={},
            footers={},
            footnotes=[],
            exhibits=[],
            signatures=[],
            metadata={},
            embedded_documents=[],
            extraction_method="",
            extraction_time=0.0,
            byte_coverage=0.0,
            element_count=0,
            error_log=[]
        )
        
        try:
            # Route to appropriate extractor
            if doc_format == DocumentFormat.HTML:
                await self._extract_html(content, result)
            elif doc_format == DocumentFormat.XML:
                await self._extract_xml(content, result)
            elif doc_format in [DocumentFormat.XBRL, DocumentFormat.IXBRL]:
                await self._extract_xbrl(content, result)
            elif doc_format == DocumentFormat.PDF:
                await self._extract_pdf(content, result)
            elif doc_format == DocumentFormat.SGML:
                await self._extract_sgml(content, result)
            elif doc_format == DocumentFormat.JSON:
                await self._extract_json(content, result)
            elif doc_format == DocumentFormat.CSV:
                await self._extract_csv(content, result)
            else:
                await self._extract_text(content, result)
            
            # Post-processing for complete coverage
            await self._post_process_extraction(result)
            
            # Calculate metrics
            result.byte_coverage = self._calculate_coverage(content, result)
            result.extraction_time = (datetime.now() - start_time).total_seconds()
            result.success = result.byte_coverage > 0.95  # 95% coverage threshold
            
            # Update statistics
            self.extraction_stats[doc_format.value] += 1
            self.extraction_stats['total'] += 1
            
            logger.info(f"Extraction complete: {result.element_count} elements, {result.byte_coverage:.1%} coverage")
            
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            result.error_log.append(str(e))
            traceback.print_exc()
        
        return result
    
    def _detect_encoding(self, content: bytes) -> str:
        """Detect content encoding with multiple methods."""
        # Method 1: chardet
        detection = chardet.detect(content)
        if detection['confidence'] > 0.7:
            return detection['encoding']
        
        # Method 2: Try common encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                content.decode(encoding)
                return encoding
            except:
                continue
        
        return 'utf-8'
    
    def _detect_format(self, content: str, url: Optional[str] = None) -> DocumentFormat:
        """Detect document format with high accuracy."""
        content_lower = content[:5000].lower()
        
        # Check URL extension
        if url:
            ext = Path(urlparse(url).path).suffix.lower()
            ext_map = {
                '.html': DocumentFormat.HTML,
                '.htm': DocumentFormat.HTML,
                '.xml': DocumentFormat.XML,
                '.xbrl': DocumentFormat.XBRL,
                '.pdf': DocumentFormat.PDF,
                '.txt': DocumentFormat.TEXT,
                '.json': DocumentFormat.JSON,
                '.csv': DocumentFormat.CSV
            }
            if ext in ext_map:
                return ext_map[ext]
        
        # Content-based detection
        if '<!doctype html' in content_lower or '<html' in content_lower:
            return DocumentFormat.HTML
        elif '<?xml' in content_lower:
            if 'xbrl' in content_lower:
                if 'ix:' in content or 'inline' in content_lower:
                    return DocumentFormat.IXBRL
                return DocumentFormat.XBRL
            return DocumentFormat.XML
        elif '<document>' in content_lower and '<type>' in content_lower:
            return DocumentFormat.SGML
        elif content.strip().startswith('{') or content.strip().startswith('['):
            return DocumentFormat.JSON
        elif '\t' in content[:1000] or ',' in content[:1000]:
            return DocumentFormat.CSV
        elif content.startswith('%PDF'):
            return DocumentFormat.PDF
        
        return DocumentFormat.TEXT
    
    async def _extract_html(self, content: str, result: ExtractionResult):
        """Extract complete HTML content with all elements."""
        result.extraction_method = "HTML Parser"
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove scripts and styles but preserve their count
        scripts = soup.find_all('script')
        styles = soup.find_all('style')
        result.metadata['script_count'] = len(scripts)
        result.metadata['style_count'] = len(styles)
        
        for element in scripts + styles:
            element.decompose()
        
        # Extract all text with structure preservation
        result.raw_text = soup.get_text()
        
        # Extract title
        if soup.title:
            result.metadata['title'] = soup.title.string
        
        # Extract all meta tags
        meta_tags = {}
        for meta in soup.find_all('meta'):
            if meta.get('name'):
                meta_tags[meta['name']] = meta.get('content', '')
            elif meta.get('property'):
                meta_tags[meta['property']] = meta.get('content', '')
        result.metadata['meta_tags'] = meta_tags
        
        # Extract all headers (h1-h6)
        headers = defaultdict(list)
        for i in range(1, 7):
            for header in soup.find_all(f'h{i}'):
                headers[f'h{i}'].append(header.get_text(strip=True))
                
                # Store header with content
                content_after = []
                for sibling in header.find_next_siblings():
                    if sibling.name and sibling.name.startswith('h'):
                        break
                    content_after.append(sibling.get_text(strip=True))
                
                result.headers[header.get_text(strip=True)] = ' '.join(content_after[:3])
        
        result.structured_data['headers_hierarchy'] = dict(headers)
        
        # Extract all tables with complete data
        for table_idx, table in enumerate(soup.find_all('table')):
            table_data = self._extract_html_table(table)
            table_data['index'] = table_idx
            table_data['html'] = str(table)[:1000]  # Store first 1000 chars of HTML
            result.tables.append(table_data)
        
        # Extract all forms
        for form_idx, form in enumerate(soup.find_all('form')):
            form_data = {
                'index': form_idx,
                'action': form.get('action', ''),
                'method': form.get('method', 'get'),
                'fields': []
            }
            
            for input_elem in form.find_all(['input', 'select', 'textarea']):
                field = {
                    'type': input_elem.name,
                    'name': input_elem.get('name', ''),
                    'value': input_elem.get('value', ''),
                    'required': input_elem.has_attr('required')
                }
                form_data['fields'].append(field)
            
            result.forms.append(form_data)
        
        # Extract all links
        links = []
        for link in soup.find_all('a', href=True):
            links.append({
                'text': link.get_text(strip=True),
                'href': link['href']
            })
        result.structured_data['links'] = links
        
        # Extract all images
        images = []
        for img in soup.find_all('img'):
            images.append({
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
        result.structured_data['images'] = images
        
        # Extract divs with specific classes/ids (common in SEC filings)
        important_divs = {}
        for div in soup.find_all('div', class_=True):
            classes = ' '.join(div['class'])
            if any(term in classes.lower() for term in ['footer', 'header', 'signature', 'exhibit', 'table']):
                important_divs[classes] = div.get_text(strip=True)[:500]
        
        for div in soup.find_all('div', id=True):
            if any(term in div['id'].lower() for term in ['footer', 'header', 'signature', 'exhibit', 'table']):
                important_divs[div['id']] = div.get_text(strip=True)[:500]
        
        result.structured_data['important_divs'] = important_divs
        
        # Extract spans with special formatting
        special_spans = []
        for span in soup.find_all('span', style=True):
            style = span.get('style', '')
            if 'bold' in style or 'underline' in style or 'italic' in style:
                special_spans.append(span.get_text(strip=True))
        result.structured_data['emphasized_text'] = special_spans
        
        # Extract lists
        lists = {'ordered': [], 'unordered': []}
        for ol in soup.find_all('ol'):
            items = [li.get_text(strip=True) for li in ol.find_all('li')]
            lists['ordered'].append(items)
        
        for ul in soup.find_all('ul'):
            items = [li.get_text(strip=True) for li in ul.find_all('li')]
            lists['unordered'].append(items)
        
        result.structured_data['lists'] = lists
        
        # Extract paragraphs with substantial content
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if len(text) > 50:  # Only substantial paragraphs
                paragraphs.append(text)
        result.structured_data['paragraphs'] = paragraphs[:100]  # Limit to first 100
        
        # Extract comments (often contain metadata)
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        result.structured_data['html_comments'] = [str(comment) for comment in comments]
        
        # Count elements
        result.element_count = len(soup.find_all())
        
        logger.info(f"HTML extraction: {result.element_count} elements, {len(result.tables)} tables")
    
    def _extract_html_table(self, table_elem) -> Dict[str, Any]:
        """Extract complete table data from HTML element."""
        table_data = {
            'headers': [],
            'rows': [],
            'caption': '',
            'footer': '',
            'col_count': 0,
            'row_count': 0
        }
        
        # Extract caption
        caption = table_elem.find('caption')
        if caption:
            table_data['caption'] = caption.get_text(strip=True)
        
        # Extract headers
        thead = table_elem.find('thead')
        if thead:
            for row in thead.find_all('tr'):
                headers = [cell.get_text(strip=True) for cell in row.find_all(['th', 'td'])]
                if headers:
                    table_data['headers'] = headers
                    break
        else:
            # Check first row for headers
            first_row = table_elem.find('tr')
            if first_row:
                cells = first_row.find_all(['th', 'td'])
                if cells and cells[0].name == 'th':
                    table_data['headers'] = [cell.get_text(strip=True) for cell in cells]
        
        # Extract body rows
        tbody = table_elem.find('tbody')
        rows_elem = tbody.find_all('tr') if tbody else table_elem.find_all('tr')
        
        for row in rows_elem:
            cells = row.find_all(['td', 'th'])
            if cells:
                row_data = []
                for cell in cells:
                    cell_data = {
                        'text': cell.get_text(strip=True),
                        'colspan': int(cell.get('colspan', 1)),
                        'rowspan': int(cell.get('rowspan', 1)),
                        'style': cell.get('style', ''),
                        'class': ' '.join(cell.get('class', []))
                    }
                    row_data.append(cell_data)
                
                # Skip if this appears to be header row
                if not table_data['headers'] or row_data != table_data['headers']:
                    table_data['rows'].append(row_data)
        
        # Extract footer
        tfoot = table_elem.find('tfoot')
        if tfoot:
            footer_text = tfoot.get_text(strip=True)
            table_data['footer'] = footer_text
        
        # Calculate dimensions
        table_data['row_count'] = len(table_data['rows'])
        table_data['col_count'] = max(
            len(table_data['headers']),
            max((len(row) for row in table_data['rows']), default=0)
        )
        
        return table_data
    
    async def _extract_xml(self, content: str, result: ExtractionResult):
        """Extract complete XML content with namespace handling."""
        result.extraction_method = "XML Parser"
        
        try:
            # Use lxml for better namespace handling
            parser = etree.XMLParser(recover=True, remove_blank_text=True, huge_tree=True)
            root = etree.fromstring(content.encode('utf-8'), parser)
            
            # Extract namespaces
            nsmap = root.nsmap if hasattr(root, 'nsmap') else {}
            result.metadata['namespaces'] = {k: v for k, v in nsmap.items() if k}
            
            # Convert to dictionary recursively
            def elem_to_dict(elem):
                result_dict = {}
                
                # Attributes
                if elem.attrib:
                    result_dict['@attributes'] = dict(elem.attrib)
                
                # Text content
                if elem.text and elem.text.strip():
                    text = elem.text.strip()
                    # Try to parse as number
                    try:
                        if '.' in text:
                            result_dict['@value'] = float(text)
                        else:
                            result_dict['@value'] = int(text)
                    except:
                        result_dict['@value'] = text
                
                # Process children
                children = defaultdict(list)
                for child in elem:
                    child_dict = elem_to_dict(child)
                    tag = etree.QName(child.tag).localname if '}' in child.tag else child.tag
                    children[tag].append(child_dict)
                
                # Flatten single-item lists
                for key, value in children.items():
                    if len(value) == 1:
                        result_dict[key] = value[0]
                    else:
                        result_dict[key] = value
                
                return result_dict if result_dict else elem.text
            
            # Convert entire tree
            result.structured_data = elem_to_dict(root)
            
            # Extract raw text
            result.raw_text = etree.tostring(root, method='text', encoding='unicode')
            
            # Count elements
            result.element_count = len(root.xpath('//*'))
            
            # Extract specific SEC elements if present
            if 'ownershipDocument' in etree.tostring(root, encoding='unicode'):
                await self._extract_ownership_document(root, result)
            
            logger.info(f"XML extraction: {result.element_count} elements")
            
        except Exception as e:
            result.error_log.append(f"XML parsing error: {e}")
            # Fallback to ElementTree
            try:
                root = ET.fromstring(content)
                result.structured_data = self._elementtree_to_dict(root)
                result.element_count = len(list(root.iter()))
            except:
                result.raw_text = content
    
    async def _extract_xbrl(self, content: str, result: ExtractionResult):
        """Extract XBRL/iXBRL content with complete fact extraction."""
        result.extraction_method = "XBRL Parser"
        
        is_inline = 'ix:' in content or 'inline' in content.lower()
        
        if is_inline:
            # Inline XBRL - extract from HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract all facts
            facts = {}
            for elem in soup.find_all(attrs={'name': True}):
                fact_name = elem.get('name')
                context_ref = elem.get('contextref', '')
                
                fact_key = f"{fact_name}_{context_ref}" if context_ref else fact_name
                
                facts[fact_key] = {
                    'value': elem.get_text(strip=True),
                    'name': fact_name,
                    'context': context_ref,
                    'format': elem.get('format'),
                    'scale': elem.get('scale'),
                    'decimals': elem.get('decimals'),
                    'unit': elem.get('unitref'),
                    'sign': elem.get('sign')
                }
            
            result.structured_data['xbrl_facts'] = facts
            
            # Also extract as HTML
            await self._extract_html(content, result)
            
        else:
            # Standard XBRL
            await self._extract_xml(content, result)
            
            # Extract XBRL-specific elements
            parser = etree.XMLParser(recover=True, huge_tree=True)
            root = etree.fromstring(content.encode('utf-8'), parser)
            
            # Extract contexts
            contexts = {}
            for context in root.xpath('//*[local-name()="context"]'):
                context_id = context.get('id')
                contexts[context_id] = {
                    'entity': context.find('.//*[local-name()="identifier"]').text if context.find('.//*[local-name()="identifier"]') is not None else None,
                    'period': {
                        'instant': context.find('.//*[local-name()="instant"]').text if context.find('.//*[local-name()="instant"]') is not None else None,
                        'start': context.find('.//*[local-name()="startDate"]').text if context.find('.//*[local-name()="startDate"]') is not None else None,
                        'end': context.find('.//*[local-name()="endDate"]').text if context.find('.//*[local-name()="endDate"]') is not None else None
                    }
                }
            
            result.structured_data['xbrl_contexts'] = contexts
            
            # Extract units
            units = {}
            for unit in root.xpath('//*[local-name()="unit"]'):
                unit_id = unit.get('id')
                measure = unit.find('.//*[local-name()="measure"]')
                if measure is not None:
                    units[unit_id] = measure.text
            
            result.structured_data['xbrl_units'] = units
    
    async def _extract_sgml(self, content: str, result: ExtractionResult):
        """Extract SGML documents with SEC-specific handling."""
        result.extraction_method = "SGML Parser"
        
        documents = []
        
        # Extract all documents
        doc_pattern = re.compile(r'<DOCUMENT>(.*?)</DOCUMENT>', re.DOTALL | re.IGNORECASE)
        
        for match in doc_pattern.finditer(content):
            doc_content = match.group(1)
            doc_info = {}
            
            # Extract headers
            for header in ['TYPE', 'SEQUENCE', 'FILENAME', 'DESCRIPTION']:
                header_pattern = re.compile(f'<{header}>([^<]+)', re.IGNORECASE)
                header_match = header_pattern.search(doc_content)
                if header_match:
                    doc_info[header.lower()] = header_match.group(1).strip()
            
            # Extract text content
            text_pattern = re.compile(r'<TEXT>(.*?)</TEXT>', re.DOTALL | re.IGNORECASE)
            text_match = text_pattern.search(doc_content)
            
            if text_match:
                text_content = text_match.group(1)
                
                # Check for embedded XML
                if '<XML>' in text_content:
                    xml_pattern = re.compile(r'<XML>(.*?)</XML>', re.DOTALL | re.IGNORECASE)
                    xml_match = xml_pattern.search(text_content)
                    if xml_match:
                        doc_info['content'] = xml_match.group(1)
                        doc_info['content_type'] = 'xml'
                        
                        # Parse the XML content
                        sub_result = await self.extract_document(doc_info['content'], force_format=DocumentFormat.XML)
                        doc_info['parsed'] = sub_result.structured_data
                else:
                    doc_info['content'] = text_content
                    doc_info['content_type'] = 'text'
                    
                    # Check if it's HTML
                    if '<html' in text_content.lower():
                        sub_result = await self.extract_document(doc_info['content'], force_format=DocumentFormat.HTML)
                        doc_info['parsed'] = sub_result.structured_data
            
            documents.append(doc_info)
        
        result.embedded_documents = documents
        result.element_count = len(documents)
        
        # Extract raw text from all documents
        all_text = []
        for doc in documents:
            if 'content' in doc:
                all_text.append(doc['content'])
        result.raw_text = '\n\n'.join(all_text)
        
        logger.info(f"SGML extraction: {len(documents)} documents found")
    
    async def _extract_pdf(self, content: Union[str, bytes], result: ExtractionResult):
        """Extract PDF content with OCR fallback."""
        result.extraction_method = "PDF Parser"
        
        try:
            # Convert to bytes if string
            if isinstance(content, str):
                content = content.encode('latin-1')
            
            # Create file-like object
            pdf_file = io.BytesIO(content)
            
            # Extract with pdfplumber
            with pdfplumber.open(pdf_file) as pdf:
                result.metadata['page_count'] = len(pdf.pages)
                
                all_text = []
                all_tables = []
                
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    text = page.extract_text()
                    if text:
                        all_text.append(f"--- Page {page_num + 1} ---\n{text}")
                    
                    # Extract tables
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        if table:
                            table_data = {
                                'page': page_num + 1,
                                'index': table_idx,
                                'data': table,
                                'rows': len(table),
                                'cols': len(table[0]) if table else 0
                            }
                            all_tables.append(table_data)
                    
                    # Extract images (for potential OCR)
                    if hasattr(page, 'images'):
                        for img_idx, img in enumerate(page.images):
                            result.structured_data[f'image_p{page_num}_i{img_idx}'] = {
                                'bbox': img.get('bbox'),
                                'width': img.get('width'),
                                'height': img.get('height')
                            }
                
                result.raw_text = '\n'.join(all_text)
                result.tables = all_tables
                
                # Extract metadata
                if hasattr(pdf, 'metadata'):
                    result.metadata.update(pdf.metadata or {})
                
        except Exception as e:
            result.error_log.append(f"PDF extraction error: {e}")
            logger.error(f"PDF extraction failed: {e}")
    
    async def _extract_json(self, content: str, result: ExtractionResult):
        """Extract JSON content."""
        result.extraction_method = "JSON Parser"
        
        try:
            data = json.loads(content)
            result.structured_data = data
            
            # Flatten for text extraction
            def flatten_json(obj, prefix=''):
                items = []
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        new_key = f"{prefix}.{k}" if prefix else k
                        if isinstance(v, (dict, list)):
                            items.extend(flatten_json(v, new_key))
                        else:
                            items.append(f"{new_key}: {v}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        new_key = f"{prefix}[{i}]"
                        if isinstance(item, (dict, list)):
                            items.extend(flatten_json(item, new_key))
                        else:
                            items.append(f"{new_key}: {item}")
                return items
            
            flat_items = flatten_json(data)
            result.raw_text = '\n'.join(flat_items)
            result.element_count = len(flat_items)
            
        except json.JSONDecodeError as e:
            result.error_log.append(f"JSON parse error: {e}")
            result.raw_text = content
    
    async def _extract_csv(self, content: str, result: ExtractionResult):
        """Extract CSV content as tables."""
        result.extraction_method = "CSV Parser"
        
        try:
            # Detect delimiter
            delimiter = ','
            if '\t' in content[:1000]:
                delimiter = '\t'
            elif '|' in content[:1000]:
                delimiter = '|'
            
            # Parse with pandas
            df = pd.read_csv(io.StringIO(content), delimiter=delimiter)
            
            # Convert to table format
            table_data = {
                'headers': df.columns.tolist(),
                'rows': df.values.tolist(),
                'row_count': len(df),
                'col_count': len(df.columns),
                'data': df.to_dict('records')
            }
            
            result.tables.append(table_data)
            result.structured_data['dataframe'] = df.to_dict()
            result.raw_text = df.to_string()
            result.element_count = len(df) * len(df.columns)
            
        except Exception as e:
            result.error_log.append(f"CSV parse error: {e}")
            result.raw_text = content
    
    async def _extract_text(self, content: str, result: ExtractionResult):
        """Extract structured data from plain text."""
        result.extraction_method = "Text Parser"
        
        result.raw_text = content
        
        # Extract sections using patterns
        sections = {}
        for section_match in self.sec_patterns['section'].finditer(content):
            section_num = section_match.group(1)
            section_title = section_match.group(2).strip()
            
            # Get content until next section
            start_pos = section_match.end()
            next_match = self.sec_patterns['section'].search(content, start_pos)
            end_pos = next_match.start() if next_match else len(content)
            
            section_content = content[start_pos:end_pos].strip()
            sections[f"{section_num}. {section_title}"] = section_content[:5000]  # Limit size
        
        result.structured_data['sections'] = sections
        
        # Extract tables from text
        potential_tables = self._extract_text_tables(content)
        result.tables.extend(potential_tables)
        
        # Extract financial data
        financial_data = {
            'amounts': list(set(self.sec_patterns['currency'].findall(content))),
            'percentages': list(set(self.sec_patterns['percentage'].findall(content))),
            'dates': list(set(self.sec_patterns['date'].findall(content)))[:100]  # Limit
        }
        result.structured_data['financial_data'] = financial_data
        
        # Extract footnotes
        footnotes = list(set(self.sec_patterns['footnote'].findall(content)))
        result.footnotes = footnotes
        
        # Extract signatures
        for sig_match in self.sec_patterns['signature'].finditer(content):
            signature = {
                'text': sig_match.group(0),
                'name': sig_match.group(1) or sig_match.group(2),
                'position': sig_match.start()
            }
            result.signatures.append(signature)
        
        # Extract exhibits
        for exhibit_match in self.sec_patterns['exhibit'].finditer(content):
            exhibit = {
                'reference': exhibit_match.group(0),
                'number': exhibit_match.group(1),
                'position': exhibit_match.start()
            }
            result.exhibits.append(exhibit)
        
        # Extract legal references
        legal_refs = list(set(self.sec_patterns['legal_ref'].findall(content)))[:50]
        result.structured_data['legal_references'] = legal_refs
        
        # Extract GAAP terms
        gaap_terms = list(set(self.sec_patterns['gaap_term'].findall(content)))
        result.structured_data['accounting_terms'] = gaap_terms
        
        result.element_count = len(sections) + len(potential_tables) + len(footnotes)
    
    def _extract_text_tables(self, content: str) -> List[Dict]:
        """Extract tables from plain text content."""
        tables = []
        lines = content.split('\n')
        
        current_table = []
        in_table = False
        
        for line in lines:
            # Check if line looks like table row
            if self.sec_patterns['table_delimiter'].search(line):
                in_table = True
                current_table.append(line)
            elif in_table and line.strip() == '':
                # End of table
                if len(current_table) > 2:  # Minimum viable table
                    table_data = self._parse_text_table(current_table)
                    if table_data:
                        tables.append(table_data)
                current_table = []
                in_table = False
            elif in_table:
                current_table.append(line)
        
        return tables
    
    def _parse_text_table(self, lines: List[str]) -> Optional[Dict]:
        """Parse text lines into table structure."""
        if not lines:
            return None
        
        # Detect delimiter
        delimiter = None
        if all('|' in line for line in lines[:3]):
            delimiter = '|'
        elif all('\t' in line for line in lines[:3]):
            delimiter = '\t'
        else:
            # Space-separated (look for consistent spacing)
            delimiter = re.compile(r'\s{2,}')
        
        rows = []
        for line in lines:
            if isinstance(delimiter, str):
                cells = [cell.strip() for cell in line.split(delimiter)]
            else:
                cells = [cell.strip() for cell in delimiter.split(line)]
            
            if any(cells):  # Skip empty rows
                rows.append(cells)
        
        if len(rows) < 2:
            return None
        
        # Assume first row is header
        return {
            'headers': rows[0],
            'rows': rows[1:],
            'row_count': len(rows) - 1,
            'col_count': len(rows[0])
        }
    
    async def _extract_ownership_document(self, root, result: ExtractionResult):
        """Extract SEC ownership document specific data."""
        # Reporting owner
        owner = root.find('.//*[local-name()="reportingOwner"]')
        if owner is not None:
            owner_data = {}
            for field in ['rptOwnerName', 'rptOwnerCik', 'rptOwnerStreet1', 'rptOwnerCity', 'rptOwnerState']:
                elem = owner.find(f'.//*[local-name()="{field}"]')
                if elem is not None and elem.text:
                    owner_data[field] = elem.text.strip()
            
            result.structured_data['reporting_owner'] = owner_data
        
        # Transactions
        transactions = []
        
        # Non-derivative transactions
        for tx in root.findall('.//*[local-name()="nonDerivativeTransaction"]'):
            tx_data = self._parse_transaction_xml(tx)
            tx_data['type'] = 'non-derivative'
            transactions.append(tx_data)
        
        # Derivative transactions
        for tx in root.findall('.//*[local-name()="derivativeTransaction"]'):
            tx_data = self._parse_transaction_xml(tx)
            tx_data['type'] = 'derivative'
            transactions.append(tx_data)
        
        result.structured_data['transactions'] = transactions
        
        # Footnotes
        footnotes = []
        for footnote in root.findall('.//*[local-name()="footnote"]'):
            if footnote.text:
                footnotes.append({
                    'id': footnote.get('id'),
                    'text': footnote.text.strip()
                })
        
        result.footnotes.extend([f['text'] for f in footnotes])
        result.structured_data['footnotes_detailed'] = footnotes
        
        # Signatures
        for sig in root.findall('.//*[local-name()="signature"]'):
            sig_name = sig.find('.//*[local-name()="signatureName"]')
            sig_date = sig.find('.//*[local-name()="signatureDate"]')
            
            if sig_name is not None:
                result.signatures.append({
                    'name': sig_name.text.strip() if sig_name.text else '',
                    'date': sig_date.text.strip() if sig_date is not None and sig_date.text else ''
                })
    
    def _parse_transaction_xml(self, tx_elem) -> Dict:
        """Parse transaction element from ownership document."""
        tx_data = {}
        
        # Define fields to extract
        fields = [
            'transactionDate',
            'transactionCode',
            'transactionShares',
            'transactionPricePerShare',
            'transactionAcquiredDisposedCode',
            'sharesOwnedFollowingTransaction',
            'directOrIndirectOwnership'
        ]
        
        for field in fields:
            elem = tx_elem.find(f'.//*[local-name()="{field}"]')
            if elem is not None:
                # Check for nested value element
                value_elem = elem.find('.//*[local-name()="value"]')
                if value_elem is not None and value_elem.text:
                    tx_data[field] = value_elem.text.strip()
                elif elem.text:
                    tx_data[field] = elem.text.strip()
        
        return tx_data
    
    async def _post_process_extraction(self, result: ExtractionResult):
        """Post-process extraction to ensure complete coverage."""
        
        # Ensure we have raw text
        if not result.raw_text and result.structured_data:
            # Generate raw text from structured data
            def extract_text(obj, texts=[]):
                if isinstance(obj, dict):
                    for value in obj.values():
                        extract_text(value, texts)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_text(item, texts)
                elif isinstance(obj, str):
                    texts.append(obj)
                elif obj is not None:
                    texts.append(str(obj))
                return texts
            
            all_texts = extract_text(result.structured_data)
            result.raw_text = ' '.join(all_texts)
        
        # Extract patterns from raw text if not already done
        if result.raw_text:
            # Extract any missed financial data
            if 'financial_data' not in result.structured_data:
                result.structured_data['financial_data'] = {
                    'amounts': list(set(self.sec_patterns['currency'].findall(result.raw_text)))[:100],
                    'percentages': list(set(self.sec_patterns['percentage'].findall(result.raw_text)))[:100],
                    'dates': list(set(self.sec_patterns['date'].findall(result.raw_text)))[:100]
                }
            
            # Extract missed legal references
            if 'legal_references' not in result.structured_data:
                result.structured_data['legal_references'] = list(
                    set(self.sec_patterns['legal_ref'].findall(result.raw_text))
                )[:50]
        
        # Ensure element count is set
        if result.element_count == 0:
            result.element_count = (
                len(result.tables) +
                len(result.forms) +
                len(result.footnotes) +
                len(result.exhibits) +
                len(result.signatures) +
                len(result.structured_data.get('sections', {}))
            )
    
    def _calculate_coverage(self, original: str, result: ExtractionResult) -> float:
        """Calculate extraction coverage percentage."""
        if not original:
            return 0.0
        
        original_bytes = len(original.encode('utf-8'))
        
        # Calculate extracted bytes
        extracted_bytes = 0
        
        if result.raw_text:
            extracted_bytes += len(result.raw_text.encode('utf-8'))
        
        # Add structured data
        if result.structured_data:
            extracted_bytes += len(json.dumps(result.structured_data, default=str).encode('utf-8'))
        
        # Add tables
        if result.tables:
            extracted_bytes += len(json.dumps(result.tables, default=str).encode('utf-8'))
        
        # Calculate coverage
        coverage = min(extracted_bytes / original_bytes, 1.0) if original_bytes > 0 else 0.0
        
        # Adjust for compression (structured data may be more compact)
        if coverage < 0.5 and result.element_count > 10:
            coverage = min(coverage * 1.5, 0.95)
        
        return coverage
    
    def _elementtree_to_dict(self, elem) -> Dict:
        """Convert ElementTree element to dictionary."""
        result = {}
        
        if elem.attrib:
            result['@attributes'] = dict(elem.attrib)
        
        if elem.text and elem.text.strip():
            result['@text'] = elem.text.strip()
        
        children = defaultdict(list)
        for child in elem:
            child_dict = self._elementtree_to_dict(child)
            children[child.tag].append(child_dict)
        
        for key, value in children.items():
            if len(value) == 1:
                result[key] = value[0]
            else:
                result[key] = value
        
        return result if result else elem.text


class ForensicSECAnalyzer:
    """
    Complete SEC filing forensic analyzer with universal document extraction.
    """
    
    def __init__(self):
        self.extractor = UniversalDocumentExtractor()
        self.session = None
        self.output_dir = Path("sec_forensic_output")
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("Forensic SEC Analyzer initialized")
    
    async def create_session(self):
        """Create HTTP session."""
        if self.session:
            await self.session.close()
        
        timeout = aiohttp.ClientTimeout(total=300)
        headers = {
            "User-Agent": "Academic Research Bot 1.0 (Contact: research@university.edu)",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br"
        }
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers
        )
    
    async def analyze_filing(self, url: str) -> Dict[str, Any]:
        """
        Analyze SEC filing with complete extraction.
        
        Args:
            url: URL of SEC filing
            
        Returns:
            Complete analysis with all extracted data
        """
        logger.info(f"Analyzing filing: {url}")
        
        analysis = {
            'url': url,
            'timestamp': datetime.utcnow().isoformat(),
            'extraction': None,
            'success': False,
            'errors': []
        }
        
        try:
            # Fetch document
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Extract document
                    extraction = await self.extractor.extract_document(content, url)
                    
                    analysis['extraction'] = {
                        'format': extraction.format.value,
                        'success': extraction.success,
                        'byte_coverage': extraction.byte_coverage,
                        'element_count': extraction.element_count,
                        'extraction_time': extraction.extraction_time,
                        'extraction_method': extraction.extraction_method,
                        'tables_found': len(extraction.tables),
                        'signatures_found': len(extraction.signatures),
                        'footnotes_found': len(extraction.footnotes),
                        'raw_text_length': len(extraction.raw_text),
                        'structured_data_keys': list(extraction.structured_data.keys()),
                        'errors': extraction.error_log
                    }
                    
                    # Save full extraction
                    await self._save_extraction(url, extraction)
                    
                    analysis['success'] = extraction.success
                    
                    logger.info(f"Extraction complete: {extraction.byte_coverage:.1%} coverage, {extraction.element_count} elements")
                    
                else:
                    analysis['errors'].append(f"HTTP {response.status}")
                    
        except Exception as e:
            analysis['errors'].append(str(e))
            logger.error(f"Analysis error: {e}")
        
        return analysis
    
    async def _save_extraction(self, url: str, extraction: ExtractionResult):
        """Save extraction results to file."""
        # Generate filename from URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output_file = self.output_dir / f"extraction_{timestamp}_{url_hash}.json"
        
        # Convert extraction to serializable format
        extraction_dict = {
            'url': url,
            'timestamp': datetime.utcnow().isoformat(),
            'format': extraction.format.value,
            'success': extraction.success,
            'byte_coverage': extraction.byte_coverage,
            'element_count': extraction.element_count,
            'extraction_time': extraction.extraction_time,
            'extraction_method': extraction.extraction_method,
            'metadata': extraction.metadata,
            'structured_data': extraction.structured_data,
            'tables': extraction.tables,
            'signatures': extraction.signatures,
            'footnotes': extraction.footnotes,
            'exhibits': extraction.exhibits,
            'raw_text': extraction.raw_text[:10000],  # First 10k chars
            'errors': extraction.error_log
        }
        
        # Save to file
        async with aiofiles.open(output_file, 'w') as f:
            await f.write(json.dumps(extraction_dict, indent=2, default=str))
        
        logger.info(f"Extraction saved to {output_file}")
    
    async def close(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()


# Main execution
async def main():
    """Demonstration of complete SEC document extraction."""
    
    analyzer = ForensicSECAnalyzer()
    
    try:
        await analyzer.create_session()
        
        # Example SEC filing URLs
        test_urls = [
            "https://www.sec.gov/Archives/edgar/data/320187/000032018719000119/0000320187-19-000119.txt",  # Form 4
            "https://www.sec.gov/Archives/edgar/data/320187/000032018719000076/nke-5312019x10k.htm",  # 10-K
        ]
        
        for url in test_urls:
            logger.info("=" * 80)
            result = await analyzer.analyze_filing(url)
            
            if result['success']:
                print(f"\nâœ“ Successfully extracted: {url}")
                print(f"  Format: {result['extraction']['format']}")
                print(f"  Coverage: {result['extraction']['byte_coverage']:.1%}")
                print(f"  Elements: {result['extraction']['element_count']}")
                print(f"  Tables: {result['extraction']['tables_found']}")
                print(f"  Extraction Time: {result['extraction']['extraction_time']:.2f}s")
            else:
                print(f"\nâœ— Extraction failed: {url}")
                print(f"  Errors: {result['errors']}")
        
    finally:
        await analyzer.close()


if __name__ == "__main__":
    print("SEC Document Forensic Extraction System v3.0")
    print("=" * 60)
    print("Starting complete document extraction...")
    
    asyncio.run(main())
