"""
FINRA Electronic Form 144 XML Parser
====================================

Parses FINRA's electronic Form 144 XML filings.

FINRA requires electronic filing of Form 144 in XML format.
This parser extracts structured data from these filings.

Reference: FINRA Rule 4510, SEC Rule 144
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)


@dataclass
class FINRAForm144Data:
    """Structured data from FINRA Form 144 XML filing."""
    
    # Filing metadata
    filing_id: str
    filing_date: date
    submission_date: datetime
    
    # Filer information
    filer_cik: str
    filer_name: str
    
    # Issuer information
    issuer_cik: str
    issuer_name: str
    
    # Optional fields
    filer_address: Optional[str] = None
    issuer_symbol: Optional[str] = None
    
    # Relationship
    is_officer: bool = False
    is_director: bool = False
    is_ten_percent_owner: bool = False
    is_other: bool = False
    other_relationship: Optional[str] = None
    
    # Security details
    security_class: str = ""
    cusip: Optional[str] = None
    
    # Proposed sale
    proposed_sale_date: Optional[date] = None
    proposed_sale_shares: int = 0
    proposed_sale_value: float = 0.0
    
    # Acquisition details
    date_acquired: Optional[date] = None
    acquisition_method: Optional[str] = None
    
    # Broker information
    broker_name: Optional[str] = None
    broker_address: Optional[str] = None
    
    # Remarks
    remarks: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "filing_metadata": {
                "filing_id": self.filing_id,
                "filing_date": self.filing_date.isoformat() if self.filing_date else None,
                "submission_date": self.submission_date.isoformat() if self.submission_date else None
            },
            "filer": {
                "cik": self.filer_cik,
                "name": self.filer_name,
                "address": self.filer_address
            },
            "issuer": {
                "cik": self.issuer_cik,
                "name": self.issuer_name,
                "symbol": self.issuer_symbol
            },
            "relationship": {
                "officer": self.is_officer,
                "director": self.is_director,
                "ten_percent_owner": self.is_ten_percent_owner,
                "other": self.is_other,
                "other_description": self.other_relationship
            },
            "security": {
                "class": self.security_class,
                "cusip": self.cusip
            },
            "proposed_sale": {
                "date": self.proposed_sale_date.isoformat() if self.proposed_sale_date else None,
                "shares": self.proposed_sale_shares,
                "value": self.proposed_sale_value
            },
            "acquisition": {
                "date": self.date_acquired.isoformat() if self.date_acquired else None,
                "method": self.acquisition_method
            },
            "broker": {
                "name": self.broker_name,
                "address": self.broker_address
            },
            "remarks": self.remarks
        }


class FINRAForm144Parser:
    """
    Parser for FINRA electronic Form 144 XML filings.
    
    Handles the XML structure used by FINRA for electronic Form 144 submissions.
    """
    
    def __init__(self):
        self.logger = logger
    
    def parse_xml(self, xml_content: str) -> Optional[FINRAForm144Data]:
        """
        Parse FINRA Form 144 XML content.
        
        Args:
            xml_content: XML string content
        
        Returns:
            FINRAForm144Data object or None if parsing fails
        """
        try:
            root = ET.fromstring(xml_content)
            return self._extract_data_from_xml(root)
        except ET.ParseError as e:
            self.logger.error(f"XML parsing error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing Form 144 XML: {e}")
            return None
    
    def parse_xml_file(self, file_path: str) -> Optional[FINRAForm144Data]:
        """
        Parse FINRA Form 144 XML from a file.
        
        Args:
            file_path: Path to XML file
        
        Returns:
            FINRAForm144Data object or None if parsing fails
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return self._extract_data_from_xml(root)
        except Exception as e:
            self.logger.error(f"Error parsing Form 144 XML file: {e}")
            return None
    
    def _extract_data_from_xml(self, root: ET.Element) -> FINRAForm144Data:
        """
        Extract structured data from XML root element.
        
        Note: This is a simplified parser. The actual FINRA XML schema
        may vary and would need to be adapted based on the specific format.
        """
        # Initialize with default values
        data = FINRAForm144Data(
            filing_id="",
            filing_date=date.today(),
            submission_date=datetime.now(),
            filer_cik="",
            filer_name="",
            issuer_cik="",
            issuer_name=""
        )
        
        # Extract filing metadata
        filing_id_elem = root.find(".//FilingID")
        if filing_id_elem is not None:
            data.filing_id = filing_id_elem.text or ""
        
        filing_date_elem = root.find(".//FilingDate")
        if filing_date_elem is not None:
            data.filing_date = self._parse_date(filing_date_elem.text)
        
        submission_date_elem = root.find(".//SubmissionDate")
        if submission_date_elem is not None:
            data.submission_date = self._parse_datetime(submission_date_elem.text)
        
        # Extract filer information
        filer_cik_elem = root.find(".//Filer/CIK")
        if filer_cik_elem is not None:
            data.filer_cik = filer_cik_elem.text or ""
        
        filer_name_elem = root.find(".//Filer/Name")
        if filer_name_elem is not None:
            data.filer_name = filer_name_elem.text or ""
        
        filer_address_elem = root.find(".//Filer/Address")
        if filer_address_elem is not None:
            data.filer_address = self._extract_address(filer_address_elem)
        
        # Extract issuer information
        issuer_cik_elem = root.find(".//Issuer/CIK")
        if issuer_cik_elem is not None:
            data.issuer_cik = issuer_cik_elem.text or ""
        
        issuer_name_elem = root.find(".//Issuer/Name")
        if issuer_name_elem is not None:
            data.issuer_name = issuer_name_elem.text or ""
        
        issuer_symbol_elem = root.find(".//Issuer/Symbol")
        if issuer_symbol_elem is not None:
            data.issuer_symbol = issuer_symbol_elem.text
        
        # Extract relationship
        relationship_elem = root.find(".//Relationship")
        if relationship_elem is not None:
            data.is_officer = self._get_bool_value(relationship_elem.find("Officer"))
            data.is_director = self._get_bool_value(relationship_elem.find("Director"))
            data.is_ten_percent_owner = self._get_bool_value(relationship_elem.find("TenPercentOwner"))
            data.is_other = self._get_bool_value(relationship_elem.find("Other"))
            
            other_desc_elem = relationship_elem.find("OtherDescription")
            if other_desc_elem is not None:
                data.other_relationship = other_desc_elem.text
        
        # Extract security details
        security_elem = root.find(".//Security")
        if security_elem is not None:
            class_elem = security_elem.find("Class")
            if class_elem is not None:
                data.security_class = class_elem.text or ""
            
            cusip_elem = security_elem.find("CUSIP")
            if cusip_elem is not None:
                data.cusip = cusip_elem.text
        
        # Extract proposed sale
        proposed_sale_elem = root.find(".//ProposedSale")
        if proposed_sale_elem is not None:
            sale_date_elem = proposed_sale_elem.find("SaleDate")
            if sale_date_elem is not None:
                data.proposed_sale_date = self._parse_date(sale_date_elem.text)
            
            shares_elem = proposed_sale_elem.find("Shares")
            if shares_elem is not None:
                data.proposed_sale_shares = self._parse_int(shares_elem.text)
            
            value_elem = proposed_sale_elem.find("Value")
            if value_elem is not None:
                data.proposed_sale_value = self._parse_float(value_elem.text)
        
        # Extract acquisition details
        acquisition_elem = root.find(".//Acquisition")
        if acquisition_elem is not None:
            acq_date_elem = acquisition_elem.find("Date")
            if acq_date_elem is not None:
                data.date_acquired = self._parse_date(acq_date_elem.text)
            
            method_elem = acquisition_elem.find("Method")
            if method_elem is not None:
                data.acquisition_method = method_elem.text
        
        # Extract broker information
        broker_elem = root.find(".//Broker")
        if broker_elem is not None:
            name_elem = broker_elem.find("Name")
            if name_elem is not None:
                data.broker_name = name_elem.text
            
            address_elem = broker_elem.find("Address")
            if address_elem is not None:
                data.broker_address = self._extract_address(address_elem)
        
        # Extract remarks
        remarks_elem = root.find(".//Remarks")
        if remarks_elem is not None:
            data.remarks = remarks_elem.text
        
        return data
    
    def _extract_address(self, address_elem: ET.Element) -> str:
        """Extract and format address from XML element."""
        parts = []
        
        street1 = address_elem.find("Street1")
        if street1 is not None and street1.text:
            parts.append(street1.text)
        
        street2 = address_elem.find("Street2")
        if street2 is not None and street2.text:
            parts.append(street2.text)
        
        city = address_elem.find("City")
        state = address_elem.find("State")
        zip_code = address_elem.find("Zip")
        
        city_state_zip = []
        if city is not None and city.text:
            city_state_zip.append(city.text)
        if state is not None and state.text:
            city_state_zip.append(state.text)
        if zip_code is not None and zip_code.text:
            city_state_zip.append(zip_code.text)
        
        if city_state_zip:
            parts.append(", ".join(city_state_zip))
        
        return ", ".join(parts)
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.split('T')[0]).date()
        except ValueError:
            try:
                # Try common US format
                return datetime.strptime(date_str, "%m/%d/%Y").date()
            except ValueError:
                self.logger.warning(f"Could not parse date: {date_str}")
                return None
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not datetime_str:
            return None
        
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except ValueError:
            self.logger.warning(f"Could not parse datetime: {datetime_str}")
            return None
    
    def _parse_int(self, value_str: Optional[str]) -> int:
        """Parse integer value."""
        if not value_str:
            return 0
        
        try:
            # Remove commas and convert
            return int(value_str.replace(',', ''))
        except ValueError:
            self.logger.warning(f"Could not parse int: {value_str}")
            return 0
    
    def _parse_float(self, value_str: Optional[str]) -> float:
        """Parse float value."""
        if not value_str:
            return 0.0
        
        try:
            # Remove commas and dollar signs
            cleaned = value_str.replace(',', '').replace('$', '')
            return float(cleaned)
        except ValueError:
            self.logger.warning(f"Could not parse float: {value_str}")
            return 0.0
    
    def _get_bool_value(self, elem: Optional[ET.Element]) -> bool:
        """Get boolean value from element."""
        if elem is None:
            return False
        
        text = (elem.text or "").strip().lower()
        return text in ("true", "1", "yes", "y")
    
    def batch_parse(self, xml_contents: List[str]) -> List[FINRAForm144Data]:
        """
        Parse multiple Form 144 XML filings.
        
        Args:
            xml_contents: List of XML strings
        
        Returns:
            List of successfully parsed FINRAForm144Data objects
        """
        results = []
        
        for i, xml_content in enumerate(xml_contents):
            try:
                data = self.parse_xml(xml_content)
                if data:
                    results.append(data)
            except Exception as e:
                self.logger.error(f"Error parsing XML at index {i}: {e}")
                continue
        
        return results
