"""
Form 4 XML Parser for SEC EDGAR Filings
Handles parsing of Form 4 insider trading filings from XML format
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

class Form4XMLParser:
    """Parser for SEC Form 4 XML filings"""

    def __init__(self):
        self.namespaces = {
            'edgar': 'http://www.sec.gov/edgar',
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'xbrldi': 'http://xbrl.org/2006/xbrldi',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }

    def parse_form4_xml(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse Form 4 XML content and extract insider trading information

        Args:
            xml_content: Raw XML content from SEC filing

        Returns:
            Dictionary containing parsed Form 4 data
        """
        try:
            root = ET.fromstring(xml_content)

            # Extract basic filing information
            filing_info = self._extract_filing_info(root)

            # Extract reporting owner information
            reporting_owner = self._extract_reporting_owner(root)

            # Extract non-derivative transactions
            non_derivative_transactions = self._extract_non_derivative_transactions(root)

            # Extract derivative transactions
            derivative_transactions = self._extract_derivative_transactions(root)

            # Extract footnotes
            footnotes = self._extract_footnotes(root)

            return {
                'filing_info': filing_info,
                'reporting_owner': reporting_owner,
                'non_derivative_transactions': non_derivative_transactions,
                'derivative_transactions': derivative_transactions,
                'footnotes': footnotes,
                'parsed_at': datetime.utcnow().isoformat(),
                'parser_version': '1.0.0'
            }

        except ET.ParseError as e:
            return {
                'error': f'XML parsing error: {str(e)}',
                'parsed_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'error': f'Unexpected error: {str(e)}',
                'parsed_at': datetime.utcnow().isoformat()
            }

    def _extract_filing_info(self, root: ET.Element) -> Dict[str, Any]:
        """Extract basic filing information"""
        filing_info = {}

        # Try to find schema version
        schema_version = root.find('.//edgar:schemaVersion', self.namespaces)
        if schema_version is not None:
            filing_info['schema_version'] = schema_version.text

        # Try to find document type
        document_type = root.find('.//edgar:documentType', self.namespaces)
        if document_type is not None:
            filing_info['document_type'] = document_type.text

        # Try to find period of report
        period_of_report = root.find('.//edgar:periodOfReport', self.namespaces)
        if period_of_report is not None:
            filing_info['period_of_report'] = period_of_report.text

        # Try to find date of original submission
        date_of_original = root.find('.//edgar:dateOfOriginalSubmission', self.namespaces)
        if date_of_original is not None:
            filing_info['date_of_original_submission'] = date_of_original.text

        return filing_info

    def _extract_reporting_owner(self, root: ET.Element) -> Dict[str, Any]:
        """Extract reporting owner information"""
        owner_info = {}

        # Try to find reporting owner details
        owner_name = root.find('.//edgar:rptOwnerName', self.namespaces)
        if owner_name is not None:
            owner_info['name'] = owner_name.text

        owner_cik = root.find('.//edgar:rptOwnerCik', self.namespaces)
        if owner_cik is not None:
            owner_info['cik'] = owner_cik.text

        owner_title = root.find('.//edgar:rptOwnerTitle', self.namespaces)
        if owner_title is not None:
            owner_info['title'] = owner_title.text

        owner_street1 = root.find('.//edgar:rptOwnerStreet1', self.namespaces)
        if owner_street1 is not None:
            owner_info['street1'] = owner_street1.text

        owner_city = root.find('.//edgar:rptOwnerCity', self.namespaces)
        if owner_city is not None:
            owner_info['city'] = owner_city.text

        owner_state = root.find('.//edgar:rptOwnerState', self.namespaces)
        if owner_state is not None:
            owner_info['state'] = owner_state.text

        owner_zip = root.find('.//edgar:rptOwnerZipCode', self.namespaces)
        if owner_zip is not None:
            owner_info['zip_code'] = owner_zip.text

        return owner_info

    def _extract_non_derivative_transactions(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract non-derivative transactions"""
        transactions = []

        # Find all non-derivative transaction elements
        transaction_elements = root.findall('.//edgar:nonDerivativeTransaction', self.namespaces)

        for transaction in transaction_elements:
            transaction_data = {}

            # Security title
            security_title = transaction.find('.//edgar:securityTitle', self.namespaces)
            if security_title is not None:
                transaction_data['security_title'] = security_title.text

            # Transaction date
            transaction_date = transaction.find('.//edgar:transactionDate', self.namespaces)
            if transaction_date is not None:
                transaction_data['transaction_date'] = transaction_date.text

            # Transaction code
            transaction_code = transaction.find('.//edgar:transactionCode', self.namespaces)
            if transaction_code is not None:
                transaction_data['transaction_code'] = transaction_code.text

            # Transaction amount
            transaction_amount = transaction.find('.//edgar:transactionAmount', self.namespaces)
            if transaction_amount is not None:
                transaction_data['transaction_amount'] = transaction_amount.text

            # Transaction price per share
            transaction_price = transaction.find('.//edgar:transactionPricePerShare', self.namespaces)
            if transaction_price is not None:
                transaction_data['transaction_price_per_share'] = transaction_price.text

            # Transaction acquired disposed code
            acquired_disposed = transaction.find('.//edgar:transactionAcquiredDisposedCode', self.namespaces)
            if acquired_disposed is not None:
                transaction_data['acquired_disposed_code'] = acquired_disposed.text

            # Shares owned following transaction
            shares_owned = transaction.find('.//edgar:sharesOwnedFollowingTransaction', self.namespaces)
            if shares_owned is not None:
                transaction_data['shares_owned_following'] = shares_owned.text

            # Direct or indirect ownership
            direct_indirect = transaction.find('.//edgar:directOrIndirectOwnership', self.namespaces)
            if direct_indirect is not None:
                transaction_data['direct_or_indirect'] = direct_indirect.text

            if transaction_data:
                transactions.append(transaction_data)

        return transactions

    def _extract_derivative_transactions(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract derivative transactions"""
        transactions = []

        # Find all derivative transaction elements
        transaction_elements = root.findall('.//edgar:derivativeTransaction', self.namespaces)

        for transaction in transaction_elements:
            transaction_data = {}

            # Security title
            security_title = transaction.find('.//edgar:securityTitle', self.namespaces)
            if security_title is not None:
                transaction_data['security_title'] = security_title.text

            # Transaction date
            transaction_date = transaction.find('.//edgar:transactionDate', self.namespaces)
            if transaction_date is not None:
                transaction_data['transaction_date'] = transaction_date.text

            # Transaction code
            transaction_code = transaction.find('.//edgar:transactionCode', self.namespaces)
            if transaction_code is not None:
                transaction_data['transaction_code'] = transaction_code.text

            # Transaction amount
            transaction_amount = transaction.find('.//edgar:transactionAmount', self.namespaces)
            if transaction_amount is not None:
                transaction_data['transaction_amount'] = transaction_amount.text

            # Transaction price per share
            transaction_price = transaction.find('.//edgar:transactionPricePerShare', self.namespaces)
            if transaction_price is not None:
                transaction_data['transaction_price_per_share'] = transaction_price.text

            # Transaction acquired disposed code
            acquired_disposed = transaction.find('.//edgar:transactionAcquiredDisposedCode', self.namespaces)
            if acquired_disposed is not None:
                transaction_data['acquired_disposed_code'] = acquired_disposed.text

            # Shares owned following transaction
            shares_owned = transaction.find('.//edgar:sharesOwnedFollowingTransaction', self.namespaces)
            if shares_owned is not None:
                transaction_data['shares_owned_following'] = shares_owned.text

            # Direct or indirect ownership
            direct_indirect = transaction.find('.//edgar:directOrIndirectOwnership', self.namespaces)
            if direct_indirect is not None:
                transaction_data['direct_or_indirect'] = direct_indirect.text

            # Exercise date (for options)
            exercise_date = transaction.find('.//edgar:exerciseDate', self.namespaces)
            if exercise_date is not None:
                transaction_data['exercise_date'] = exercise_date.text

            # Expiration date (for options)
            expiration_date = transaction.find('.//edgar:expirationDate', self.namespaces)
            if expiration_date is not None:
                transaction_data['expiration_date'] = expiration_date.text

            if transaction_data:
                transactions.append(transaction_data)

        return transactions

    def _extract_footnotes(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract footnotes"""
        footnotes = []

        # Find all footnote elements
        footnote_elements = root.findall('.//edgar:footnote', self.namespaces)

        for footnote in footnote_elements:
            footnote_data = {}

            footnote_id = footnote.find('.//edgar:footnoteId', self.namespaces)
            if footnote_id is not None:
                footnote_data['id'] = footnote_id.text

            footnote_text = footnote.find('.//edgar:footnoteText', self.namespaces)
            if footnote_text is not None:
                footnote_data['text'] = footnote_text.text

            if footnote_data:
                footnotes.append(footnote_data)

        return footnotes

# Create global parser instance
parser = Form4XMLParser()

def parse_form4_xml(xml_content: str) -> Dict[str, Any]:
    """
    Parse Form 4 XML content - convenience function

    Args:
        xml_content: Raw XML content from SEC filing

    Returns:
        Dictionary containing parsed Form 4 data
    """
    return parser.parse_form4_xml(xml_content)