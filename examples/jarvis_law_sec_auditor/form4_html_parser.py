"""
JARVIS:LAW - Surgical HTML Form 4 Parser
Extracts REAL data from HTML-rendered SEC Form 4 files with surgical precision
NO N/A. NO True/False. ONLY REAL DATA.
"""

from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
from pathlib import Path


class Form4HTMLParser:
    """Surgical HTML parser for SEC Form 4 - extracts REAL data from HTML tables"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content = ""
        self.soup = None
        self._load_html()
    
    def _load_html(self):
        """Load and parse HTML file"""
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.content = f.read()
            self.soup = BeautifulSoup(self.content, 'html.parser')
        except Exception as e:
            raise Exception(f"Failed to load HTML: {e}")
    
    def _extract_text_clean(self, element) -> Optional[str]:
        """Extract clean text from element, removing HTML garbage"""
        if element is None:
            return None
        
        text = element.get_text(strip=True)
        
        # Remove common garbage patterns
        if '<' in text or '>' in text:
            return None
        
        return text if text else None
    
    def extract_reporting_owner(self) -> Dict:
        """Extract reporting owner with surgical precision - NO N/A, NO True/False"""
        owner = {}
        
        # Find section 1: Name and Address of Reporting Person
        section1_start = self.content.find('1. Name and Address of Reporting Person')
        if section1_start == -1:
            raise Exception("ERROR: Section 1 not found - cannot extract reporting owner")
        
        # Extract section 1 content (next 1000 chars)
        section1_text = self.content[section1_start:section1_start+1000]
        
        # Find the CIK link for reporting person
        cik_match = re.search(r'CIK=(\d+)["\']>([^<]+)<', section1_text)
        if cik_match:
            owner['cik'] = cik_match.group(1)
            owner['name'] = cik_match.group(2).strip()
        else:
            raise Exception("ERROR: Could not extract reporting person name and CIK")
        
        # Extract address from FormData spans in section 1
        section1_soup = BeautifulSoup(section1_text, 'html.parser')
        address_spans = section1_soup.find_all('span', class_='FormData')
        
        if len(address_spans) >= 3:
            # Address structure: street, city, state, zip
            address_texts = [span.get_text(strip=True) for span in address_spans if span.get_text(strip=True)]
            if len(address_texts) >= 3:
                owner['address'] = {
                    'street': address_texts[0],
                    'city': address_texts[1] if len(address_texts) > 1 else None,
                    'state': address_texts[2] if len(address_texts) > 2 else None,
                    'zipcode': address_texts[3] if len(address_texts) > 3 else None
                }
        
        # Extract relationship - look for section 5 with SURGICAL PRECISION
        section5_start = self.content.find('5. Relationship of Reporting Person')
        if section5_start == -1:
            raise Exception("ERROR: Section 5 not found - cannot extract relationship")
        
        section5_text = self.content[section5_start:section5_start+800]
        relationship = {}
        
        # Parse HTML structure to find checked boxes
        section5_soup = BeautifulSoup(section5_text, 'html.parser')
        
        # Find all table rows in section 5
        rows = section5_soup.find_all('tr')
        
        for row in rows:
            row_text = row.get_text()
            cells = row.find_all('td')
            
            if 'Director' in row_text:
                # Check if first cell has 'X'
                if len(cells) >= 2:
                    checkbox = cells[0].get_text(strip=True)
                    if checkbox == 'X':
                        relationship['is_director'] = 'Yes'
            
            if 'Officer' in row_text and 'give title below' in row_text:
                if len(cells) >= 2:
                    checkbox = cells[0].get_text(strip=True)
                    if checkbox == 'X':
                        relationship['is_officer'] = 'Yes'
                        # Extract officer title from next row
                        title_cell = None
                        for cell in cells:
                            if 'color: blue' in str(cell):
                                title_text = cell.get_text(strip=True)
                                if title_text:
                                    relationship['officer_title'] = title_text
            
            if '10% Owner' in row_text:
                if len(cells) >= 4:
                    checkbox = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                    if checkbox == 'X':
                        relationship['is_ten_percent_owner'] = 'Yes'
        
        # If no checkboxes found using structured approach, try simpler text search
        if not relationship:
            # Fallback: look for X marks in the section text
            if 'X' in section5_text:
                lines_after_x = section5_text.split('X')
                for line in lines_after_x[1:]:  # Skip first split (before first X)
                    if 'Director' in line[:50]:
                        relationship['is_director'] = 'Yes'
                    elif 'Officer' in line[:50]:
                        relationship['is_officer'] = 'Yes'
                    elif '10%' in line[:50]:
                        relationship['is_ten_percent_owner'] = 'Yes'
        
        # If still nothing, set as unknown but don't fail
        if not relationship:
            relationship['role'] = 'Unable to extract - check source document'
        
        owner['relationship'] = relationship
        
        return owner
    
    def extract_issuer(self) -> Dict:
        """Extract issuer (company) information with surgical precision"""
        issuer = {}
        
        # Find section 2: Issuer Name and Ticker
        section2_start = self.content.find('2. Issuer Name')
        if section2_start == -1:
            raise Exception("ERROR: Section 2 not found - cannot extract issuer")
        
        section2_text = self.content[section2_start:section2_start+600]
        
        # Extract CIK and name from link
        cik_match = re.search(r'CIK=(\d+)["\']>([^<]+)</a>', section2_text)
        if cik_match:
            issuer['cik'] = cik_match.group(1)
            issuer['name'] = cik_match.group(2).strip()
        else:
            raise Exception("ERROR: Could not extract issuer name and CIK")
        
        # Extract ticker symbol
        ticker_match = re.search(r'\[\s*<span class="FormData">([^<]+)</span>\s*\]', section2_text)
        if ticker_match:
            issuer['trading_symbol'] = ticker_match.group(1).strip()
        else:
            raise Exception("ERROR: Could not extract trading symbol")
        
        return issuer
    
    def extract_transactions(self) -> List[Dict]:
        """
        Surgically extract ALL transaction data from HTML tables
        This is the money shot - Table I (non-derivative) and Table II (derivative)
        """
        transactions = []
        
        # Find all tables
        tables = self.soup.find_all('table')
        
        for table in tables:
            table_text = table.get_text()
            
            # Check if this is a transaction table (Table I or Table II)
            is_table_1 = 'Non-Derivative Securities' in table_text or 'Table I' in table_text
            is_table_2 = 'Derivative Securities' in table_text or 'Table II' in table_text
            
            if not (is_table_1 or is_table_2):
                continue
            
            # Get all rows
            rows = table.find_all('tr')
            
            # Find header row to map columns
            header_row = None
            for row in rows:
                row_text = row.get_text()
                if 'Transaction' in row_text and 'Date' in row_text:
                    header_row = row
                    break
            
            if not header_row:
                continue
            
            # Map column indices
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            # Process data rows
            for row in rows:
                # Skip header rows
                if row == header_row:
                    continue
                
                cells = row.find_all(['td', 'th'])
                
                # Skip rows with too few cells or header-like content
                if len(cells) < 3:
                    continue
                
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                # Skip header rows - check if first cell contains header-like text
                first_cell = cell_texts[0] if cell_texts else ''
                if 'Transaction' in first_cell or 'Title' in first_cell or len(cells) < 8:
                    continue
                
                # Parse row based on table type
                if is_table_1:
                    transaction = self._parse_table1_row(cells)
                else:
                    transaction = self._parse_table2_row(cells)
                
                # Only add if we got meaningful data
                if transaction and len(transaction) > 2:
                    transactions.append(transaction)
        
        # Additional parsing: Look for embedded XML data
        xml_match = re.search(r'<XML>(.*?)</XML>', self.content, re.DOTALL | re.IGNORECASE)
        if xml_match:
            xml_content = xml_match.group(1)
            # Parse embedded XML for structured data
            try:
                from lxml import etree
                xml_soup = BeautifulSoup(xml_content, 'xml')
                
                # Extract non-derivative transactions
                for trans_elem in xml_soup.find_all('nonDerivativeTransaction'):
                    transaction = {
                        'type': 'non_derivative',
                        'source': 'embedded_xml',
                        'security_title': self._get_xml_text(trans_elem, 'securityTitle value'),
                        'transaction_date': self._get_xml_text(trans_elem, 'transactionDate value'),
                        'transaction_code': self._get_xml_text(trans_elem, 'transactionCode'),
                        'shares': self._get_xml_text(trans_elem, 'transactionShares value'),
                        'price_per_share': self._get_xml_text(trans_elem, 'transactionPricePerShare value'),
                        'acquired_disposed': self._get_xml_text(trans_elem, 'transactionAcquiredDisposedCode value'),
                        'shares_owned_after': self._get_xml_text(trans_elem, 'sharesOwnedFollowingTransaction value'),
                        'direct_indirect': self._get_xml_text(trans_elem, 'directOrIndirectOwnership value')
                    }
                    
                    # Only add if has required fields
                    if transaction['transaction_date'] and transaction['shares']:
                        transactions.append(transaction)
                
                # Extract derivative transactions
                for trans_elem in xml_soup.find_all('derivativeTransaction'):
                    transaction = {
                        'type': 'derivative',
                        'source': 'embedded_xml',
                        'security_title': self._get_xml_text(trans_elem, 'securityTitle value'),
                        'transaction_date': self._get_xml_text(trans_elem, 'transactionDate value'),
                        'transaction_code': self._get_xml_text(trans_elem, 'transactionCode'),
                        'shares': self._get_xml_text(trans_elem, 'transactionShares value'),
                        'price_per_share': self._get_xml_text(trans_elem, 'transactionPricePerShare value'),
                        'acquired_disposed': self._get_xml_text(trans_elem, 'transactionAcquiredDisposedCode value'),
                        'shares_owned_after': self._get_xml_text(trans_elem, 'sharesOwnedFollowingTransaction value'),
                        'exercise_price': self._get_xml_text(trans_elem, 'conversionOrExercisePrice value'),
                        'underlying_security_title': self._get_xml_text(trans_elem, 'underlyingSecurityTitle value'),
                        'underlying_security_shares': self._get_xml_text(trans_elem, 'underlyingSecurityShares value')
                    }
                    
                    if transaction['transaction_date'] and transaction['shares']:
                        transactions.append(transaction)
                
            except Exception as e:
                # XML parsing failed, continue with HTML-only extraction
                pass
        
        return transactions
    
    def _get_xml_text(self, element, tag_path: str) -> Optional[str]:
        """Extract text from XML element using tag path"""
        try:
            # Split tag path for nested elements
            tags = tag_path.split()
            current = element
            
            for tag in tags:
                if current:
                    current = current.find(tag)
            
            if current:
                return current.get_text(strip=True)
        except:
            pass
        
        return None
    
    def _parse_table1_row(self, cells) -> Optional[Dict]:
        """
        Parse Table I (Non-Derivative) row with SURGICAL PRECISION
        Table I columns:
        0: Security Title
        1: Transaction Date
        2: Deemed Execution Date
        3: Transaction Code
        4: V (if any)
        5: Amount (shares)
        6: A/D
        7: Price
        8: Shares Owned After
        9: D/I (Direct/Indirect)
        10: Nature of Indirect Ownership
        """
        if len(cells) < 8:
            return None
        
        # Extract all cell texts
        cell_texts = []
        for cell in cells:
            text = cell.get_text(strip=True)
            # Clean up footnote markers
            text = re.sub(r'\(\d+\)$', '', text).strip()
            cell_texts.append(text)
        
        # CRITICAL: Skip holdings-only rows (no transaction date or code)
        # These are rows that just show current holdings, not actual transactions
        has_date = cell_texts[1] and re.search(r'\d{1,2}/\d{1,2}/\d{4}', cell_texts[1])
        has_code = len(cell_texts) > 3 and cell_texts[3] and re.match(r'^[PSADXMFIGJ]$', cell_texts[3])
        
        if not (has_date or has_code):
            # This is just a holdings row, not a transaction
            return None
        
        transaction = {
            'type': 'non_derivative',
            'source': 'html_table'
        }
        
        # Column 0: Security Title
        if cell_texts[0]:
            transaction['security_title'] = cell_texts[0]
        
        # Column 1: Transaction Date (MM/DD/YYYY format)
        if has_date:
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', cell_texts[1])
            if date_match:
                month, day, year = date_match.groups()
                transaction['transaction_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Column 3: Transaction Code
        if has_code:
            transaction['transaction_code'] = cell_texts[3]
        
        # Column 5: Shares (Amount)
        if len(cell_texts) > 5 and cell_texts[5]:
            shares_clean = cell_texts[5].replace(',', '')
            if re.match(r'^[\d.]+$', shares_clean):
                transaction['shares'] = shares_clean
        
        # Column 6: A/D (Acquired/Disposed)
        if len(cell_texts) > 6 and cell_texts[6] in ['A', 'D']:
            transaction['acquired_disposed'] = 'Acquired' if cell_texts[6] == 'A' else 'Disposed'
        
        # Column 7: Price per Share
        if len(cell_texts) > 7 and cell_texts[7]:
            price_clean = re.sub(r'[^\d.]', '', cell_texts[7])
            if price_clean and re.match(r'^\d+\.?\d*$', price_clean):
                transaction['price_per_share'] = price_clean
        
        # Column 8: Shares Owned After Transaction
        if len(cell_texts) > 8 and cell_texts[8]:
            shares_after_clean = cell_texts[8].replace(',', '')
            if re.match(r'^[\d.]+$', shares_after_clean):
                transaction['shares_owned_after'] = shares_after_clean
        
        # Column 9: Direct/Indirect Ownership
        if len(cell_texts) > 9 and cell_texts[9] in ['D', 'I']:
            transaction['direct_indirect'] = 'Direct' if cell_texts[9] == 'D' else 'Indirect'
        
        # Column 10: Nature of Indirect Ownership
        if len(cell_texts) > 10 and cell_texts[10]:
            transaction['nature_of_indirect'] = cell_texts[10]
        
        # Only return if we have minimum required fields
        if 'security_title' in transaction or 'transaction_date' in transaction:
            return transaction
        
        return None
    
    def _parse_table2_row(self, cells) -> Optional[Dict]:
        """
        Parse Table II (Derivative) row with SURGICAL PRECISION
        Table II columns:
        0: Derivative Security Title
        1: Conversion/Exercise Price
        2: Transaction Date
        3: Deemed Execution Date
        4: Transaction Code
        5: V (if any)
        6: Number Acquired (A)
        7: Number Disposed (D)
        8: Date Exercisable
        9: Expiration Date
        10: Underlying Security Title
        11: Underlying Security Shares
        12: Price of Derivative
        13: Number Owned After
        14: D/I
        15: Nature of Indirect
        """
        if len(cells) < 10:
            return None
        
        # Extract all cell texts
        cell_texts = []
        for cell in cells:
            text = cell.get_text(strip=True)
            # Clean up footnote markers
            text = re.sub(r'\(\d+\)$', '', text).strip()
            cell_texts.append(text)
        
        # CRITICAL: Skip holdings-only rows - must have transaction date or code
        has_date = len(cell_texts) > 2 and cell_texts[2] and re.search(r'\d{1,2}/\d{1,2}/\d{4}', cell_texts[2])
        has_code = len(cell_texts) > 4 and cell_texts[4] and re.match(r'^[PSADXMFIGJ]$', cell_texts[4])
        
        if not (has_date or has_code):
            # This is just a holdings row, not a transaction
            return None
        
        transaction = {
            'type': 'derivative',
            'source': 'html_table'
        }
        
        # Column 0: Derivative Security Title
        if cell_texts[0]:
            transaction['security_title'] = cell_texts[0]
        
        # Column 1: Exercise/Conversion Price
        if len(cell_texts) > 1 and cell_texts[1]:
            exercise_price = re.sub(r'[^\d.]', '', cell_texts[1])
            if exercise_price and re.match(r'^\d+\.?\d*$', exercise_price):
                transaction['exercise_price'] = exercise_price
        
        # Column 2: Transaction Date
        if len(cell_texts) > 2 and cell_texts[2]:
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', cell_texts[2])
            if date_match:
                month, day, year = date_match.groups()
                transaction['transaction_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Column 4: Transaction Code
        if len(cell_texts) > 4 and cell_texts[4] and re.match(r'^[PSADXMFIGJ]$', cell_texts[4]):
            transaction['transaction_code'] = cell_texts[4]
        
        # Columns 6 & 7: Number Acquired/Disposed
        shares_acquired = None
        shares_disposed = None
        if len(cell_texts) > 6 and cell_texts[6]:
            shares_clean = cell_texts[6].replace(',', '')
            if re.match(r'^[\d.]+$', shares_clean):
                shares_acquired = shares_clean
        if len(cell_texts) > 7 and cell_texts[7]:
            shares_clean = cell_texts[7].replace(',', '')
            if re.match(r'^[\d.]+$', shares_clean):
                shares_disposed = shares_clean
        
        # Determine which is populated
        if shares_acquired:
            transaction['shares'] = shares_acquired
            transaction['acquired_disposed'] = 'Acquired'
        elif shares_disposed:
            transaction['shares'] = shares_disposed
            transaction['acquired_disposed'] = 'Disposed'
        
        # Column 8: Date Exercisable
        if len(cell_texts) > 8 and cell_texts[8]:
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', cell_texts[8])
            if date_match:
                month, day, year = date_match.groups()
                transaction['date_exercisable'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Column 9: Expiration Date
        if len(cell_texts) > 9 and cell_texts[9]:
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', cell_texts[9])
            if date_match:
                month, day, year = date_match.groups()
                transaction['expiration_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Column 10: Underlying Security Title
        if len(cell_texts) > 10 and cell_texts[10]:
            transaction['underlying_security_title'] = cell_texts[10]
        
        # Column 11: Underlying Security Shares
        if len(cell_texts) > 11 and cell_texts[11]:
            shares_clean = cell_texts[11].replace(',', '')
            if re.match(r'^[\d.]+$', shares_clean):
                transaction['underlying_security_shares'] = shares_clean
        
        # Column 12: Price of Derivative
        if len(cell_texts) > 12 and cell_texts[12]:
            price_clean = re.sub(r'[^\d.]', '', cell_texts[12])
            if price_clean and re.match(r'^\d+\.?\d*$', price_clean):
                transaction['price_per_share'] = price_clean
        
        # Column 13: Number Owned After Transaction
        if len(cell_texts) > 13 and cell_texts[13]:
            shares_after_clean = cell_texts[13].replace(',', '')
            if re.match(r'^[\d.]+$', shares_after_clean):
                transaction['shares_owned_after'] = shares_after_clean
        
        # Column 14: Direct/Indirect
        if len(cell_texts) > 14 and cell_texts[14] in ['D', 'I']:
            transaction['direct_indirect'] = 'Direct' if cell_texts[14] == 'D' else 'Indirect'
        
        # Only return if we have minimum required fields
        if 'security_title' in transaction or 'transaction_date' in transaction:
            return transaction
        
        return None
    
    def extract_footnotes(self) -> List[Dict]:
        """Extract footnotes from document"""
        footnotes = []
        
        # Look for FootnoteData class spans
        for span in self.soup.find_all('span', class_='FootnoteData'):
            text = span.get_text(strip=True)
            if text and len(text) > 2:
                footnotes.append({
                    'id': f'footnote_{len(footnotes)+1}',
                    'text': text
                })
        
        # Also check embedded XML for footnotes
        xml_match = re.search(r'<XML>(.*?)</XML>', self.content, re.DOTALL | re.IGNORECASE)
        if xml_match:
            try:
                xml_soup = BeautifulSoup(xml_match.group(1), 'xml')
                for fn in xml_soup.find_all('footnote'):
                    footnotes.append({
                        'id': fn.get('id', f'xml_footnote_{len(footnotes)+1}'),
                        'text': fn.get_text(strip=True)
                    })
            except:
                pass
        
        return footnotes
    
    def extract_all(self) -> Dict:
        """Extract ALL data from Form 4 HTML with surgical precision"""
        reporting_owner = self.extract_reporting_owner()
        issuer = self.extract_issuer()
        transactions = self.extract_transactions()
        footnotes = self.extract_footnotes()
        
        # Combine derivative and non-derivative into single list
        all_transactions = transactions
        
        return {
            'reporting_owner': reporting_owner,
            'issuer': issuer,
            'transactions': all_transactions,
            'footnotes': footnotes
        }


# Export
__all__ = ['Form4HTMLParser']

