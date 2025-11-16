"""
JARVIS:LAW Black Site Protocol - Complete Document Parser
100% visibility into SEC filings - all formats, all content, all metadata
ENHANCED: XML parsing for structured data extraction
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup, Tag
import sys

# Import XML and HTML parsers for Form 4
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from form4_xml_parser import Form4XMLParser
    XML_PARSER_AVAILABLE = True
except ImportError:
    XML_PARSER_AVAILABLE = False

try:
    from form4_html_parser import Form4HTMLParser
    HTML_PARSER_AVAILABLE = True
except ImportError:
    HTML_PARSER_AVAILABLE = False


class DocumentParser:
    """Complete document ingestion and extraction system - HTML & XML compatible"""
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.content = ""
        self.soup = None
        self.xml_soup = None
        self.is_html_format = False
        self.is_xml_format = False
        self.xml_data = None
        self.extracted_data = {}
        
        if self.filepath.exists():
            with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
                self.content = f.read()
            
            # Check if XML file - try XML parser first
            if self.filepath.suffix == '.xml' and XML_PARSER_AVAILABLE:
                self.is_xml_format = True
                try:
                    parser = Form4XMLParser(str(self.filepath))
                    self.xml_data = parser.extract_all()
                    print(f"[OK] XML parsing successful")
                except Exception as e:
                    print(f"[INFO] XML parsing failed, trying surgical HTML parser...")
                    self.is_xml_format = False
            
            # Try surgical HTML parser if XML failed or not XML file
            if not self.is_xml_format and HTML_PARSER_AVAILABLE:
                try:
                    html_parser = Form4HTMLParser(str(self.filepath))
                    self.xml_data = html_parser.extract_all()
                    self.is_xml_format = True  # Mark as structured data available
                    print(f"[OK] Surgical HTML parsing successful")
                except Exception as e:
                    print(f"[WARNING] Surgical HTML parsing failed: {e}")
            
            # Fall back to basic HTML parsing if both failed
            if not self.is_xml_format:
                self.soup = BeautifulSoup(self.content, 'html.parser')
            
            # Determine format type
            if '<ownershipDocument>' in self.content or '<XML>' in self.content:
                # Extract embedded XML
                xml_match = re.search(r'<XML>(.*?)</XML>', self.content, re.DOTALL | re.IGNORECASE)
                if xml_match:
                    xml_content = xml_match.group(1).strip()
                    self.xml_soup = BeautifulSoup(xml_content, 'xml')
                else:
                    self.xml_soup = BeautifulSoup(self.content, 'xml')
                self.is_html_format = False
            elif 'SEC FORM' in self.content[:1000] and '<table' in self.content:
                # HTML-rendered SEC form
                self.is_html_format = True
                self.xml_soup = None
            else:
                self.xml_soup = self.soup
                self.is_html_format = False
    
    def extract_complete_profile(self) -> Dict[str, Any]:
        """
        Extract EVERYTHING from the document.
        Leaves no stone unturned.
        Uses surgical parser data when available.
        """
        # If we have structured data from surgical parser, use it
        if self.xml_data:
            profile = {
                "file_metadata": self._extract_file_metadata(),
                "document_structure": self._extract_document_structure(),
                "reporting_owner": self.xml_data.get('reporting_owner', {}),
                "issuer_info": self.xml_data.get('issuer', {}),
                "transactions": self.xml_data.get('transactions', []),
                "holdings": [],  # Not in surgical parser yet
                "signatures": [],
                "footnotes": {'footnotes': self.xml_data.get('footnotes', []), 'total_count': len(self.xml_data.get('footnotes', []))},
                "dollar_amounts": self._extract_dollar_amounts(),
                "dates": self._extract_all_dates(),
                "names": self._extract_all_names(),
                "addresses": self._extract_addresses(),
                "stock_classes": self._extract_stock_classes(),
                "derivative_securities": self._extract_derivative_securities(),
                "ownership_nature": self._extract_ownership_nature(),
                "raw_text_segments": self._extract_text_segments(),
                "embedded_tables": self._extract_tables(),
                "xml_structure": self._extract_xml_elements(),
            }
        else:
            # Fall back to basic extraction
            profile = {
                "file_metadata": self._extract_file_metadata(),
                "document_structure": self._extract_document_structure(),
                "reporting_owner": self._extract_reporting_owner(),
                "issuer_info": self._extract_issuer_info(),
                "transactions": self._extract_all_transactions(),
            "holdings": self._extract_holdings(),
            "signatures": self._extract_signatures(),
            "footnotes": self._extract_footnotes(),
            "dollar_amounts": self._extract_dollar_amounts(),
            "dates": self._extract_all_dates(),
            "names": self._extract_all_names(),
            "addresses": self._extract_addresses(),
            "stock_classes": self._extract_stock_classes(),
            "derivative_securities": self._extract_derivative_securities(),
            "ownership_nature": self._extract_ownership_nature(),
            "raw_text_segments": self._extract_text_segments(),
            "embedded_tables": self._extract_tables(),
            "xml_structure": self._extract_xml_elements(),
        }
        
        self.extracted_data = profile
        return profile
    
    def _extract_file_metadata(self) -> Dict[str, Any]:
        """Extract file-level metadata"""
        return {
            "filename": self.filepath.name,
            "file_size": self.filepath.stat().st_size,
            "file_extension": self.filepath.suffix,
            "content_length": len(self.content),
            "line_count": self.content.count('\n'),
            "modified_time": datetime.fromtimestamp(self.filepath.stat().st_mtime).isoformat(),
        }
    
    def _extract_document_structure(self) -> Dict[str, Any]:
        """Analyze document structure"""
        return {
            "has_xml": '<?xml' in self.content,
            "has_html": '<html' in self.content.lower(),
            "has_sec_header": 'SEC' in self.content[:500],
            "total_tags": len(self.soup.find_all()) if self.soup else 0,
            "encoding": 'utf-8',
            "format_type": self._detect_format_type(),
        }
    
    def _detect_format_type(self) -> str:
        """Detect the primary format of the filing"""
        if '<ownershipDocument>' in self.content:
            return "XML_FORM_4"
        elif '<edgarSubmission>' in self.content:
            return "XML_EDGAR_SUBMISSION"
        elif '<?xml' in self.content:
            return "XML_GENERIC"
        elif '<html' in self.content.lower():
            return "HTML"
        else:
            return "UNKNOWN"
    
    def _extract_reporting_owner(self) -> Dict[str, Any]:
        """Extract complete reporting owner information"""
        owner_data = {}
        
        if self.is_html_format:
            # HTML table-based extraction
            # Look for "Name and Address of Reporting Person" section
            name_text = self._extract_text_after_pattern(r'1\.\s*Name and Address of Reporting Person')
            if name_text:
                # Extract name from link or text
                name_link = self.soup.find('a', href=re.compile(r'browse-edgar'))
                if name_link and 'Reporting Person' in self._get_section_text(name_link):
                    owner_data['name'] = name_link.get_text(strip=True)
                else:
                    # Try to extract from structured text
                    lines = name_text.split('\n')
                    if lines:
                        owner_data['name'] = lines[0].strip()
            
            # Extract address
            street_match = re.search(r'<span class="FormData">([^<]+)</span>', self.content)
            if street_match:
                owner_data['address'] = {
                    'street1': street_match.group(1).strip() if street_match else None
                }
            
            # Extract relationship checkboxes
            # Look for relationship section
            relationship_section = self._find_section_by_number('5')
            if relationship_section:
                owner_data['relationship'] = {
                    'is_director': 'Director' in relationship_section,
                    'is_officer': 'Officer' in relationship_section,
                    'is_ten_percent_owner': '10%' in relationship_section or 'Ten Percent' in relationship_section,
                    'is_other': 'Other' in relationship_section,
                }
                # Extract officer title
                title_match = re.search(r'Officer.*?title[^>]*>([^<]+)<', relationship_section, re.IGNORECASE | re.DOTALL)
                if title_match:
                    owner_data['relationship']['officer_title'] = title_match.group(1).strip()
        
        elif self.xml_soup:
            # XML-based extraction
            owner = self.xml_soup.find('reportingOwner')
            if owner:
                owner_data = {
                    "name": self._get_text(owner, 'rptOwnerName'),
                    "cik": self._get_text(owner, 'rptOwnerCik'),
                    "address": {
                        "street1": self._get_text(owner, 'rptOwnerStreet1'),
                        "street2": self._get_text(owner, 'rptOwnerStreet2'),
                        "city": self._get_text(owner, 'rptOwnerCity'),
                        "state": self._get_text(owner, 'rptOwnerState'),
                        "zipcode": self._get_text(owner, 'rptOwnerZipCode'),
                    },
                    "relationship": {
                        "is_director": self._get_text(owner, 'isDirector') == '1',
                        "is_officer": self._get_text(owner, 'isOfficer') == '1',
                        "is_ten_percent_owner": self._get_text(owner, 'isTenPercentOwner') == '1',
                        "is_other": self._get_text(owner, 'isOther') == '1',
                        "officer_title": self._get_text(owner, 'officerTitle'),
                        "other_text": self._get_text(owner, 'otherText'),
                    }
                }
        
        return owner_data
    
    def _extract_issuer_info(self) -> Dict[str, Any]:
        """Extract issuer/company information"""
        issuer_data = {}
        
        if self.is_html_format:
            # HTML table-based extraction
            # Look for "Issuer Name and Ticker"
            issuer_section = self._find_section_by_number('2')
            if issuer_section:
                # Extract company name from link
                issuer_link = re.search(r'<a[^>]*>([^<]+)</a>', issuer_section)
                if issuer_link:
                    issuer_data['name'] = issuer_link.group(1).strip()
                
                # Extract ticker symbol
                ticker_match = re.search(r'\[\s*<span class="FormData">([^<]+)</span>\s*\]', issuer_section)
                if ticker_match:
                    issuer_data['trading_symbol'] = ticker_match.group(1).strip()
        
        elif self.xml_soup:
            issuer = self.xml_soup.find('issuer')
            if issuer:
                issuer_data = {
                    "name": self._get_text(issuer, 'issuerName'),
                    "cik": self._get_text(issuer, 'issuerCik'),
                    "trading_symbol": self._get_text(issuer, 'issuerTradingSymbol'),
                }
        
        return issuer_data
    
    def _extract_all_transactions(self) -> List[Dict[str, Any]]:
        """Extract ALL transaction details - non-derivative and derivative"""
        transactions = []
        
        if self.is_html_format:
            # HTML table-based extraction
            # Find all transaction tables (look for "Table I" and "Table II")
            tables = self.soup.find_all('table')
            
            for table in tables:
                table_text = table.get_text()
                
                # Check if this is a transaction table
                if any(keyword in table_text for keyword in ['Transaction', 'Securities Acquired', 'Disposed', 'Price']):
                    rows = table.find_all('tr')
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            # Extract data from cells
                            cell_texts = [cell.get_text(strip=True) for cell in cells]
                            
                            # Skip header rows
                            if any(h in ' '.join(cell_texts) for h in ['Title', 'Date', 'Code']):
                                continue
                            
                            # Try to identify transaction data
                            if any(cell_texts):  # Has data
                                trans_data = {
                                    'type': 'html_extracted',
                                    'raw_data': cell_texts,
                                }
                                
                                # Try to identify specific fields
                                for idx, text in enumerate(cell_texts):
                                    if re.match(r'\d{4}-\d{2}-\d{2}', text):
                                        trans_data['transaction_date'] = text
                                    elif re.match(r'[A-Z]', text) and len(text) == 1:
                                        trans_data['transaction_code'] = text
                                    elif '$' in text:
                                        trans_data['price_per_share'] = text
                                    elif re.match(r'[\d,]+$', text):
                                        trans_data['shares'] = text
                                
                                if len(trans_data) > 2:  # Has more than just type and raw_data
                                    transactions.append(trans_data)
        
        elif self.xml_soup:
            # Non-derivative transactions
            for trans in self.xml_soup.find_all('nonDerivativeTransaction'):
                transactions.append({
                    "type": "non_derivative",
                    "security_title": self._get_text(trans, 'securityTitle'),
                    "transaction_date": self._get_text(trans, 'transactionDate'),
                    "transaction_code": self._get_text(trans, 'transactionCode'),
                    "shares": self._get_text(trans, 'transactionShares'),
                    "price_per_share": self._get_text(trans, 'transactionPricePerShare'),
                    "acquired_disposed": self._get_text(trans, 'transactionAcquiredDisposedCode'),
                    "shares_owned_following": self._get_text(trans, 'sharesOwnedFollowingTransaction'),
                    "ownership_form": self._get_text(trans, 'directOrIndirectOwnership'),
                    "nature_of_ownership": self._get_text(trans, 'natureOfOwnership'),
                })
            
            # Derivative transactions
            for trans in self.xml_soup.find_all('derivativeTransaction'):
                transactions.append({
                    "type": "derivative",
                    "security_title": self._get_text(trans, 'securityTitle'),
                    "transaction_date": self._get_text(trans, 'transactionDate'),
                    "transaction_code": self._get_text(trans, 'transactionCode'),
                    "shares": self._get_text(trans, 'transactionShares'),
                    "price_per_share": self._get_text(trans, 'transactionPricePerShare'),
                    "acquired_disposed": self._get_text(trans, 'transactionAcquiredDisposedCode'),
                    "exercise_date": self._get_text(trans, 'exerciseDate'),
                    "expiration_date": self._get_text(trans, 'expirationDate'),
                    "underlying_security_title": self._get_text(trans, 'underlyingSecurityTitle'),
                    "underlying_security_shares": self._get_text(trans, 'underlyingSecurityShares'),
                    "shares_owned_following": self._get_text(trans, 'sharesOwnedFollowingTransaction'),
                    "ownership_form": self._get_text(trans, 'directOrIndirectOwnership'),
                })
        
        return transactions
    
    def _extract_holdings(self) -> List[Dict[str, Any]]:
        """Extract current holdings (non-transaction)"""
        holdings = []
        
        if self.xml_soup:
            # Non-derivative holdings
            for holding in self.xml_soup.find_all('nonDerivativeHolding'):
                holdings.append({
                    "type": "non_derivative",
                    "security_title": self._get_text(holding, 'securityTitle'),
                    "shares_owned": self._get_text(holding, 'sharesOwnedFollowingTransaction'),
                    "ownership_form": self._get_text(holding, 'directOrIndirectOwnership'),
                    "nature_of_ownership": self._get_text(holding, 'natureOfOwnership'),
                })
            
            # Derivative holdings
            for holding in self.xml_soup.find_all('derivativeHolding'):
                holdings.append({
                    "type": "derivative",
                    "security_title": self._get_text(holding, 'securityTitle'),
                    "exercise_date": self._get_text(holding, 'exerciseDate'),
                    "expiration_date": self._get_text(holding, 'expirationDate'),
                    "underlying_security_title": self._get_text(holding, 'underlyingSecurityTitle'),
                    "underlying_security_shares": self._get_text(holding, 'underlyingSecurityShares'),
                    "shares_owned": self._get_text(holding, 'sharesOwnedFollowingTransaction'),
                    "ownership_form": self._get_text(holding, 'directOrIndirectOwnership'),
                })
        
        return holdings
    
    def _extract_signatures(self) -> List[Dict[str, Any]]:
        """Extract signature information"""
        signatures = []
        
        if self.xml_soup:
            for sig in self.xml_soup.find_all('ownerSignature'):
                signatures.append({
                    "signature_name": self._get_text(sig, 'signatureName'),
                    "signature_date": self._get_text(sig, 'signatureDate'),
                })
        
        return signatures
    
    def _extract_footnotes(self) -> Dict[str, Any]:
        """Extract ALL footnotes with IDs and text"""
        footnotes = []
        
        if self.is_html_format:
            # Extract from HTML - look for FootnoteData class and footnote sections
            footnote_elements = self.soup.find_all('span', class_='FootnoteData')
            for fn in footnote_elements:
                text = fn.get_text(strip=True)
                if text:
                    footnotes.append({
                        'id': f'html_footnote_{len(footnotes)+1}',
                        'text': text
                    })
            
            # Also look for explicit footnote sections
            footnote_section = re.findall(r'<sup>\d+</sup>([^<]+)', self.content)
            for idx, text in enumerate(footnote_section, len(footnotes)+1):
                if text.strip():
                    footnotes.append({
                        'id': f'html_sup_{idx}',
                        'text': text.strip()
                    })
        
        elif self.xml_soup:
            for footnote in self.xml_soup.find_all('footnote'):
                footnotes.append({
                    "id": footnote.get('id', ''),
                    "text": footnote.get_text(strip=True),
                })
        
        # Also check for footnote references
        footnote_refs = re.findall(r'<footnoteId[^>]*>([^<]+)</footnoteId>', self.content)
        
        return {
            "footnotes": footnotes,
            "total_count": len(footnotes),
            "referenced_ids": list(set(footnote_refs)),
        }
    
    def _extract_dollar_amounts(self) -> Dict[str, Any]:
        """Extract ALL dollar amounts from document"""
        # Multiple patterns for dollar amounts
        patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
            r'\$\s*(\d+(?:\.\d{2})?)',  # $123.45
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars|USD)',  # 1,234.56 dollars
        ]
        
        all_amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, self.content, re.IGNORECASE)
            all_amounts.extend(matches)
        
        # Clean and convert
        cleaned_amounts = []
        for amount in all_amounts:
            clean = amount.replace(',', '').strip()
            try:
                cleaned_amounts.append(float(clean))
            except:
                pass
        
        return {
            "all_amounts": cleaned_amounts,
            "count": len(cleaned_amounts),
            "min": min(cleaned_amounts) if cleaned_amounts else 0,
            "max": max(cleaned_amounts) if cleaned_amounts else 0,
            "total": sum(cleaned_amounts) if cleaned_amounts else 0,
            "zero_dollar_count": cleaned_amounts.count(0.0),
        }
    
    def _extract_all_dates(self) -> Dict[str, Any]:
        """Extract ALL dates from document"""
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2019-12-31
            r'\d{2}/\d{2}/\d{4}',  # 12/31/2019
            r'\d{8}',  # 20191231
        ]
        
        all_dates = []
        for pattern in date_patterns:
            all_dates.extend(re.findall(pattern, self.content))
        
        return {
            "all_dates": list(set(all_dates)),
            "count": len(set(all_dates)),
        }
    
    def _extract_all_names(self) -> Dict[str, Any]:
        """Extract all person/entity names"""
        names = []
        
        if self.xml_soup:
            # Names from specific tags
            name_tags = ['rptOwnerName', 'signatureName', 'issuerName']
            for tag in name_tags:
                for element in self.xml_soup.find_all(tag):
                    names.append(element.get_text(strip=True))
        
        return {
            "names": list(set(names)),
            "count": len(set(names)),
        }
    
    def _extract_addresses(self) -> List[Dict[str, Any]]:
        """Extract all addresses"""
        addresses = []
        
        if self.xml_soup:
            for addr in self.xml_soup.find_all(['reportingOwner', 'issuer']):
                address = {
                    "street1": self._get_text(addr, 'rptOwnerStreet1') or self._get_text(addr, 'issuerStreet1'),
                    "street2": self._get_text(addr, 'rptOwnerStreet2') or self._get_text(addr, 'issuerStreet2'),
                    "city": self._get_text(addr, 'rptOwnerCity') or self._get_text(addr, 'issuerCity'),
                    "state": self._get_text(addr, 'rptOwnerState') or self._get_text(addr, 'issuerState'),
                    "zipcode": self._get_text(addr, 'rptOwnerZipCode') or self._get_text(addr, 'issuerZipCode'),
                }
                if any(address.values()):
                    addresses.append(address)
        
        return addresses
    
    def _extract_stock_classes(self) -> Dict[str, Any]:
        """Extract all mentions of stock classes"""
        class_a_count = len(re.findall(r'\bclass\s+a\b', self.content, re.IGNORECASE))
        class_b_count = len(re.findall(r'\bclass\s+b\b', self.content, re.IGNORECASE))
        class_c_count = len(re.findall(r'\bclass\s+c\b', self.content, re.IGNORECASE))
        
        return {
            "class_a_mentions": class_a_count,
            "class_b_mentions": class_b_count,
            "class_c_mentions": class_c_count,
            "total_class_mentions": class_a_count + class_b_count + class_c_count,
        }
    
    def _extract_derivative_securities(self) -> Dict[str, Any]:
        """Extract derivative security information"""
        stock_option_count = len(re.findall(r'\bstock\s+option', self.content, re.IGNORECASE))
        warrant_count = len(re.findall(r'\bwarrant', self.content, re.IGNORECASE))
        
        return {
            "stock_options": stock_option_count,
            "warrants": warrant_count,
            "derivative_transaction_count": len(self.xml_soup.find_all('derivativeTransaction')) if self.xml_soup else 0,
            "derivative_holding_count": len(self.xml_soup.find_all('derivativeHolding')) if self.xml_soup else 0,
        }
    
    def _extract_ownership_nature(self) -> List[str]:
        """Extract nature of ownership descriptions"""
        natures = []
        
        if self.xml_soup:
            for element in self.xml_soup.find_all('natureOfOwnership'):
                text = element.get_text(strip=True)
                if text:
                    natures.append(text)
        
        return list(set(natures))
    
    def _extract_text_segments(self) -> Dict[str, Any]:
        """Extract major text segments for analysis"""
        return {
            "first_1000_chars": self.content[:1000],
            "last_1000_chars": self.content[-1000:],
            "full_text_preview": self.content[:5000] + "..." if len(self.content) > 5000 else self.content,
        }
    
    def _extract_tables(self) -> List[Dict[str, Any]]:
        """Extract all table structures"""
        tables = []
        
        if self.soup:
            for i, table in enumerate(self.soup.find_all('table'), 1):
                rows = table.find_all('tr')
                tables.append({
                    "table_number": i,
                    "row_count": len(rows),
                    "cell_count": len(table.find_all(['td', 'th'])),
                })
        
        return tables
    
    def _extract_xml_elements(self) -> Dict[str, Any]:
        """Count all XML element types"""
        element_counts = {}
        
        if self.soup:
            for tag in self.soup.find_all():
                tag_name = tag.name
                element_counts[tag_name] = element_counts.get(tag_name, 0) + 1
        
        return {
            "unique_elements": len(element_counts),
            "element_breakdown": element_counts,
        }
    
    def _get_text(self, parent, tag_name: str) -> Optional[str]:
        """Helper to safely extract text from XML element"""
        if parent:
            element = parent.find(tag_name)
            if element:
                return element.get_text(strip=True)
        return None
    
    def _find_section_by_number(self, section_num: str) -> Optional[str]:
        """Find HTML section by number (e.g., '1.', '2.')"""
        pattern = rf'{section_num}\.\s*[^<]+'
        match = re.search(pattern, self.content, re.DOTALL)
        if match:
            # Get surrounding context (next 500 chars)
            start = match.start()
            return self.content[start:start+1000]
        return None
    
    def _extract_text_after_pattern(self, pattern: str) -> Optional[str]:
        """Extract text after a regex pattern"""
        match = re.search(pattern, self.content, re.IGNORECASE)
        if match:
            # Get next 200 chars
            start = match.end()
            return self.content[start:start+200]
        return None
    
    def _get_section_text(self, element: Tag) -> str:
        """Get text from element and surrounding context"""
        if element.parent:
            return element.parent.get_text()
        return element.get_text()
    
    def generate_report(self) -> str:
        """Generate human-readable comprehensive report"""
        if not self.extracted_data:
            self.extract_complete_profile()
        
        report = []
        report.append("="*80)
        report.append("JARVIS:LAW COMPLETE DOCUMENT INGESTION REPORT")
        report.append("="*80)
        report.append(f"\nFile: {self.extracted_data['file_metadata']['filename']}")
        report.append(f"Size: {self.extracted_data['file_metadata']['file_size']:,} bytes")
        report.append(f"Format: {self.extracted_data['document_structure']['format_type']}")
        
        # Reporting Owner
        owner = self.extracted_data['reporting_owner']
        if owner:
            report.append(f"\n{'='*80}")
            report.append("REPORTING OWNER")
            report.append(f"{'='*80}")
            report.append(f"Name: {owner.get('name', 'N/A')}")
            report.append(f"CIK: {owner.get('cik', 'N/A')}")
            if owner.get('relationship'):
                rel = owner['relationship']
                report.append(f"Relationship:")
                report.append(f"  - Director: {rel.get('is_director', False)}")
                report.append(f"  - Officer: {rel.get('is_officer', False)} {f'({rel.get('officer_title')})' if rel.get('officer_title') else ''}")
                report.append(f"  - 10% Owner: {rel.get('is_ten_percent_owner', False)}")
        
        # Issuer
        issuer = self.extracted_data['issuer_info']
        if issuer:
            report.append(f"\n{'='*80}")
            report.append("ISSUER INFORMATION")
            report.append(f"{'='*80}")
            report.append(f"Company: {issuer.get('name', 'N/A')}")
            report.append(f"CIK: {issuer.get('cik', 'N/A')}")
            report.append(f"Trading Symbol: {issuer.get('trading_symbol', 'N/A')}")
        
        # Transactions
        trans = self.extracted_data['transactions']
        if trans:
            report.append(f"\n{'='*80}")
            report.append(f"TRANSACTIONS ({len(trans)} total)")
            report.append(f"{'='*80}")
            for i, t in enumerate(trans, 1):
                report.append(f"\nTransaction #{i} ({t['type']})")
                report.append(f"  Security: {t.get('security_title', 'N/A')}")
                report.append(f"  Date: {t.get('transaction_date', 'N/A')}")
                report.append(f"  Code: {t.get('transaction_code', 'N/A')}")
                report.append(f"  Shares: {t.get('shares', 'N/A')}")
                report.append(f"  Price: ${t.get('price_per_share', 'N/A')}")
                report.append(f"  Acquired/Disposed: {t.get('acquired_disposed', 'N/A')}")
                report.append(f"  Shares Owned After: {t.get('shares_owned_following', 'N/A')}")
        
        # Holdings
        holdings = self.extracted_data['holdings']
        if holdings:
            report.append(f"\n{'='*80}")
            report.append(f"CURRENT HOLDINGS ({len(holdings)} total)")
            report.append(f"{'='*80}")
            for i, h in enumerate(holdings, 1):
                report.append(f"\nHolding #{i} ({h['type']})")
                report.append(f"  Security: {h.get('security_title', 'N/A')}")
                report.append(f"  Shares Owned: {h.get('shares_owned', 'N/A')}")
                report.append(f"  Ownership: {h.get('ownership_form', 'N/A')}")
        
        # Dollar amounts
        dollars = self.extracted_data['dollar_amounts']
        report.append(f"\n{'='*80}")
        report.append("FINANCIAL FIGURES")
        report.append(f"{'='*80}")
        report.append(f"Dollar amounts found: {dollars['count']}")
        if dollars['count'] > 0:
            report.append(f"  Range: ${dollars['min']:,.2f} - ${dollars['max']:,.2f}")
            report.append(f"  Total: ${dollars['total']:,.2f}")
            report.append(f"  Zero-dollar transactions: {dollars['zero_dollar_count']}")
        
        # Stock classes
        classes = self.extracted_data['stock_classes']
        report.append(f"\n{'='*80}")
        report.append("STOCK CLASSES")
        report.append(f"{'='*80}")
        report.append(f"Class A mentions: {classes['class_a_mentions']}")
        report.append(f"Class B mentions: {classes['class_b_mentions']}")
        report.append(f"Class C mentions: {classes['class_c_mentions']}")
        report.append(f"Total: {classes['total_class_mentions']}")
        
        # Footnotes
        footnotes = self.extracted_data['footnotes']
        report.append(f"\n{'='*80}")
        report.append(f"FOOTNOTES ({footnotes['total_count']} total)")
        report.append(f"{'='*80}")
        for i, fn in enumerate(footnotes['footnotes'], 1):
            report.append(f"\nFootnote #{i} (ID: {fn['id']})")
            report.append(f"  {fn['text'][:200]}{'...' if len(fn['text']) > 200 else ''}")
        
        report.append(f"\n{'='*80}")
        report.append("END OF REPORT")
        report.append(f"{'='*80}\n")
        
        return '\n'.join(report)

