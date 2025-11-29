﻿"""
Forensic Table Extractor - Phase 1
==================================
Advanced table extraction with cell relationships and data validation
"""
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from dataclasses import dataclass, field
logger = logging.getLogger(__name__)
@dataclass
class ExtractedTable:
    """Enhanced table structure with forensic metadata"""
    data: List[List[Any]]
    headers: List[str]
    row_count: int
    col_count: int
    confidence: float
    table_type: str = "generic"
    financial_indicators: List[str] = field(default_factory=list)
    def to_dataframe(self) -> pd.DataFrame:
        """Convert table to pandas DataFrame"""
        try:
            return pd.DataFrame(self.data, columns=self.headers)
        except Exception as e:
            logger.warning(f"Failed to convert to DataFrame: {e}")
            return pd.DataFrame(self.data)
class ForensicTableExtractor:
    """Advanced table extraction with multiple strategies"""
    def __init__(self):
        self.financial_indicators = [
            'revenue', 'income', 'earnings', 'assets', 'liabilities',
            'cash flow', 'ebitda', 'eps', 'dividends', 'equity'
        ]
        logger.info("✅ Forensic Table Extractor initialized")
    async def extract_tables_with_context(
        self,
        content: str,
        format_hint: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> List[ExtractedTable]:
        """Extract tables using multiple strategies
        
        Strategies:
        1. HTML table tags (highest accuracy for HTML)
        2. ML-based PDF table extraction (Camelot)
        3. Structured text parsing
        4. Financial indicator detection
        """
        tables = []
        
        # Strategy 1: HTML tables
        try:
            html_tables = await self._extract_via_html_table(content)
            tables.extend(html_tables)
        except Exception as e:
            logger.debug(f"HTML extraction failed: {e}")
        
        # Strategy 2: ML-based PDF extraction (if file path provided)
        if file_path and file_path.lower().endswith('.pdf'):
            try:
                pdf_tables = await self._extract_via_camelot(file_path)
                tables.extend(pdf_tables)
            except Exception as e:
                logger.debug(f"Camelot PDF extraction failed: {e}")
        
        # Strategy 3: Structured text
        try:
            text_tables = await self._extract_via_structured_text(content)
            tables.extend(text_tables)
        except Exception as e:
            logger.debug(f"Text extraction failed: {e}")
        
        # Enhance tables with financial indicator detection
        for table in tables:
            table.financial_indicators = self._detect_financial_indicators(table)
        
        # Deduplicate and validate
        tables = self._merge_and_validate_tables(tables)
        
        logger.info(f"📊 Extracted {len(tables)} tables with context")
        return tables
    
    async def _extract_via_camelot(self, pdf_path: str) -> List[ExtractedTable]:
        """Extract tables from PDF using Camelot ML-based detection"""
        tables = []
        try:
            import camelot
            
            # Try lattice mode first (for tables with lines)
            try:
                camelot_tables = camelot.read_pdf(pdf_path, flavor='lattice', pages='all')
            except Exception:
                # Fallback to stream mode (for tables without lines)
                camelot_tables = camelot.read_pdf(pdf_path, flavor='stream', pages='all')
            
            for camelot_table in camelot_tables:
                df = camelot_table.df
                
                # Convert to ExtractedTable format
                headers = df.iloc[0].tolist() if len(df) > 0 else []
                data = df.iloc[1:].values.tolist() if len(df) > 1 else []
                
                # Clean headers and data
                headers = [str(h).strip() for h in headers]
                data = [[str(cell).strip() for cell in row] for row in data]
                
                table = ExtractedTable(
                    data=data,
                    headers=headers,
                    row_count=len(data),
                    col_count=len(headers),
                    confidence=float(camelot_table.accuracy) / 100.0,
                    table_type='pdf_ml'
                )
                tables.append(table)
            
            logger.info(f"🤖 Camelot extracted {len(tables)} tables from PDF")
        except ImportError:
            logger.debug("Camelot not available - install with: pip install camelot-py[cv]")
        except Exception as e:
            logger.debug(f"Camelot extraction error: {e}")
        
        return tables
    
    def _detect_financial_indicators(self, table: ExtractedTable) -> List[str]:
        """Detect financial indicators in table content
        
        Returns list of detected indicator types
        """
        indicators = []
        
        # Combine headers and data for analysis
        text_content = ' '.join(table.headers).lower()
        for row in table.data[:5]:  # Check first 5 rows
            text_content += ' ' + ' '.join(str(cell) for cell in row).lower()
        
        # Check for each indicator type
        indicator_patterns = {
            'revenue': ['revenue', 'sales', 'turnover'],
            'income': ['income', 'earnings', 'profit', 'loss'],
            'assets': ['assets', 'property', 'equipment'],
            'liabilities': ['liabilities', 'debt', 'payable'],
            'cash_flow': ['cash flow', 'operating activities', 'financing activities'],
            'equity': ['equity', 'shareholders', 'stockholders'],
            'ebitda': ['ebitda', 'operating income'],
            'eps': ['eps', 'earnings per share', 'per share'],
            'dividends': ['dividend', 'distribution']
        }
        
        for indicator, keywords in indicator_patterns.items():
            if any(keyword in text_content for keyword in keywords):
                indicators.append(indicator)
        
        return indicators
    async def _extract_via_html_table(self, content: str) -> List[ExtractedTable]:
        """Extract tables from HTML table tags"""
        from bs4 import BeautifulSoup
        tables = []
        soup = BeautifulSoup(content, 'html.parser')
        html_tables = soup.find_all('table')
        for html_table in html_tables:
            try:
                headers = [th.get_text(strip=True) for th in html_table.find_all('th')]
                rows = html_table.find_all('tr')
                data = []
                for row in rows[1:] if headers else rows:
                    cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                    if cells:
                        data.append(cells)
                if data:
                    table = ExtractedTable(
                        data=data,
                        headers=headers or [f"Col{i}" for i in range(len(data[0]))],
                        row_count=len(data),
                        col_count=len(data[0]) if data else 0,
                        confidence=0.95,
                        table_type='html'
                    )
                    tables.append(table)
            except Exception as e:
                logger.debug(f"Failed to parse HTML table: {e}")
                continue
        return tables
    async def _extract_via_structured_text(self, content: str) -> List[ExtractedTable]:
        """Extract tables from structured text with delimiters"""
        tables = []
        lines = content.split('\n')
        current_table = []
        for line in lines:
            delimiter_count = line.count('\t') + line.count('|')
            if delimiter_count >= 2:
                cells = re.split(r'[\t|]+', line.strip())
                current_table.append([cell.strip() for cell in cells if cell.strip()])
            elif current_table and len(current_table) > 2:
                table = self._create_table_from_rows(current_table)
                if table:
                    tables.append(table)
                current_table = []
        if current_table and len(current_table) > 2:
            table = self._create_table_from_rows(current_table)
            if table:
                tables.append(table)
        return tables
    def _create_table_from_rows(self, rows: List[List[str]]) -> Optional[ExtractedTable]:
        """Create ExtractedTable from list of rows"""
        if not rows or len(rows) < 2:
            return None
        try:
            headers = rows[0]
            data = rows[1:]
            max_cols = max(len(row) for row in data)
            normalized_data = []
            for row in data:
                if len(row) < max_cols:
                    row.extend([''] * (max_cols - len(row)))
                normalized_data.append(row[:max_cols])
            if len(headers) < max_cols:
                headers.extend([f'Col{i}' for i in range(len(headers), max_cols)])
            headers = headers[:max_cols]
            return ExtractedTable(
                data=normalized_data,
                headers=headers,
                row_count=len(normalized_data),
                col_count=max_cols,
                confidence=0.75,
                table_type='text_structured'
            )
        except Exception as e:
            logger.debug(f"Failed to create table from rows: {e}")
            return None
    def _merge_and_validate_tables(self, tables: List[ExtractedTable]) -> List[ExtractedTable]:
        """Deduplicate and validate extracted tables"""
        if not tables:
            return []
        unique_tables = []
        seen_hashes = set()
        for table in tables:
            table_hash = self._hash_table(table)
            if table_hash not in seen_hashes:
                seen_hashes.add(table_hash)
                unique_tables.append(table)
        unique_tables.sort(key=lambda t: t.confidence, reverse=True)
        return unique_tables
    def _hash_table(self, table: ExtractedTable) -> str:
        """Generate hash for table deduplication"""
        import hashlib
        data_sample = str(table.row_count) + str(table.col_count)
        if table.data and len(table.data) > 0:
            data_sample += str(table.data[0][:3])
        return hashlib.md5(data_sample.encode()).hexdigest()
