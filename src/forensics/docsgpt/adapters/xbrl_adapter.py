"""
SEC XBRL Adapter
=================

Enhanced XBRL/iXBRL parsing for SEC structured financial data.
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)


class SECXBRLAdapter:
    """
    Adapter for parsing SEC XBRL/iXBRL filings.
    
    Extracts structured financial facts, contexts, and units from
    XBRL-tagged SEC filings.
    """

    # Common XBRL namespaces
    NAMESPACES = {
        'xbrl': 'http://www.xbrl.org/2003/instance',
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink',
        'us-gaap': 'http://fasb.org/us-gaap/2023',
        'dei': 'http://xbrl.sec.gov/dei/2023',
        'srt': 'http://fasb.org/srt/2023',
        'country': 'http://xbrl.sec.gov/country/2023',
    }

    # Key financial concepts to extract
    KEY_CONCEPTS = [
        # Income Statement
        'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax',
        'CostOfGoodsAndServicesSold', 'GrossProfit',
        'OperatingIncomeLoss', 'NetIncomeLoss',
        'EarningsPerShareBasic', 'EarningsPerShareDiluted',

        # Balance Sheet
        'Assets', 'AssetsCurrent', 'CashAndCashEquivalentsAtCarryingValue',
        'Liabilities', 'LiabilitiesCurrent', 'LongTermDebt',
        'StockholdersEquity', 'RetainedEarningsAccumulatedDeficit',

        # Cash Flow
        'NetCashProvidedByUsedInOperatingActivities',
        'NetCashProvidedByUsedInInvestingActivities',
        'NetCashProvidedByUsedInFinancingActivities',

        # DEI
        'EntityRegistrantName', 'EntityCentralIndexKey',
        'DocumentType', 'DocumentPeriodEndDate',
        'EntityCurrentReportingStatus', 'EntityFilerCategory',
    ]

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.extract_all_facts = config.get('extract_all_facts', False) if config else False

    def parse(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse an XBRL/iXBRL filing.
        
        Args:
            file_path: Path to the XBRL file
            
        Returns:
            Parsed document with facts, contexts, and metadata
        """
        path = Path(file_path)

        result = {
            'doc_id': f"xbrl_{path.stem}_{hashlib.md5(str(path).encode()).hexdigest()[:8]}",
            'source_path': str(path),
            'format': 'xbrl',
            'facts': {},
            'contexts': {},
            'units': {},
            'metadata': {},
            'text': ''
        }

        # Determine if inline XBRL
        is_ixbrl = self._is_inline_xbrl(path)
        result['metadata']['is_inline'] = is_ixbrl

        if is_ixbrl:
            result.update(self._parse_ixbrl(path))
        else:
            result.update(self._parse_xbrl(path))

        # Extract key financial metrics
        result['key_metrics'] = self._extract_key_metrics(result['facts'])

        # Generate text representation
        result['text'] = self._generate_text_representation(result)

        return result

    def _is_inline_xbrl(self, path: Path) -> bool:
        """Check if file is inline XBRL (HTML with embedded XBRL)."""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                header = f.read(5000)
                return 'xmlns:ix=' in header or '<ix:' in header
        except Exception:
            return False

    def _parse_xbrl(self, path: Path) -> Dict[str, Any]:
        """Parse traditional XBRL instance document."""
        result = {'facts': {}, 'contexts': {}, 'units': {}}

        try:
            from lxml import etree

            tree = etree.parse(str(path))
            root = tree.getroot()
            nsmap = root.nsmap

            # Extract contexts
            for context in root.findall('.//{http://www.xbrl.org/2003/instance}context'):
                ctx_id = context.get('id', '')
                result['contexts'][ctx_id] = self._parse_context(context)

            # Extract units
            for unit in root.findall('.//{http://www.xbrl.org/2003/instance}unit'):
                unit_id = unit.get('id', '')
                result['units'][unit_id] = self._parse_unit(unit)

            # Extract facts
            for ns_prefix in ['us-gaap', 'dei', 'srt']:
                ns_uri = nsmap.get(ns_prefix)
                if ns_uri:
                    for elem in root.iter(f'{{{ns_uri}}}*'):
                        fact = self._parse_fact(elem)
                        if fact:
                            concept = fact['concept']
                            if concept not in result['facts']:
                                result['facts'][concept] = []
                            result['facts'][concept].append(fact)

            logger.info(f"Parsed XBRL with {len(result['facts'])} concepts")

        except Exception as e:
            logger.error(f"XBRL parsing failed: {e}")

        return result

    def _parse_ixbrl(self, path: Path) -> Dict[str, Any]:
        """Parse inline XBRL document."""
        result = {'facts': {}, 'contexts': {}, 'units': {}}

        try:
            from lxml import etree
            from bs4 import BeautifulSoup

            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            soup = BeautifulSoup(content, 'lxml')

            # Extract hidden XBRL header
            hidden = soup.find('ix:header') or soup.find('div', {'style': 'display:none'})

            # Extract contexts from ix:resources
            for ctx in soup.find_all(['ix:context', 'xbrli:context']):
                ctx_id = ctx.get('id', '')
                result['contexts'][ctx_id] = {
                    'id': ctx_id,
                    'raw': str(ctx)
                }

            # Extract facts from ix:nonfraction, ix:nonnumeric, etc.
            for tag in ['ix:nonfraction', 'ix:nonnumeric', 'ix:fraction']:
                for elem in soup.find_all(tag.split(':')[1] if ':' in tag else tag):
                    name = elem.get('name', '')
                    if ':' in name:
                        ns, concept = name.split(':', 1)
                    else:
                        concept = name

                    fact = {
                        'concept': concept,
                        'value': elem.get_text(strip=True),
                        'context_ref': elem.get('contextref', ''),
                        'unit_ref': elem.get('unitref', ''),
                        'decimals': elem.get('decimals', ''),
                        'format': elem.get('format', ''),
                        'scale': elem.get('scale', '')
                    }

                    if concept not in result['facts']:
                        result['facts'][concept] = []
                    result['facts'][concept].append(fact)

            logger.info(f"Parsed iXBRL with {len(result['facts'])} concepts")

        except Exception as e:
            logger.error(f"iXBRL parsing failed: {e}")

        return result

    def _parse_context(self, context) -> Dict[str, Any]:
        """Parse XBRL context element."""
        result = {'id': context.get('id', '')}

        # Entity identifier
        entity = context.find('.//{http://www.xbrl.org/2003/instance}identifier')
        if entity is not None:
            result['entity'] = entity.text

        # Period
        instant = context.find('.//{http://www.xbrl.org/2003/instance}instant')
        if instant is not None:
            result['instant'] = instant.text
        else:
            start = context.find('.//{http://www.xbrl.org/2003/instance}startDate')
            end = context.find('.//{http://www.xbrl.org/2003/instance}endDate')
            if start is not None and end is not None:
                result['start_date'] = start.text
                result['end_date'] = end.text

        return result

    def _parse_unit(self, unit) -> Dict[str, Any]:
        """Parse XBRL unit element."""
        result = {'id': unit.get('id', '')}

        measure = unit.find('.//{http://www.xbrl.org/2003/instance}measure')
        if measure is not None:
            result['measure'] = measure.text

        return result

    def _parse_fact(self, elem) -> Optional[Dict[str, Any]]:
        """Parse XBRL fact element."""
        from lxml.etree import QName

        value = elem.text
        if value is None:
            return None

        return {
            'concept': QName(elem).localname,
            'namespace': QName(elem).namespace,
            'value': value.strip(),
            'context_ref': elem.get('contextRef', ''),
            'unit_ref': elem.get('unitRef', ''),
            'decimals': elem.get('decimals', ''),
            'id': elem.get('id', '')
        }

    def _extract_key_metrics(self, facts: Dict[str, List]) -> Dict[str, Any]:
        """Extract key financial metrics from facts."""
        metrics = {}

        for concept in self.KEY_CONCEPTS:
            if concept in facts:
                fact_list = facts[concept]
                if fact_list:
                    # Get most recent value
                    latest = fact_list[-1]
                    metrics[concept] = {
                        'value': latest['value'],
                        'context': latest.get('context_ref', ''),
                        'unit': latest.get('unit_ref', '')
                    }

        return metrics

    def _generate_text_representation(self, result: Dict[str, Any]) -> str:
        """Generate human-readable text from XBRL data."""
        lines = []

        # Add key metrics
        if 'key_metrics' in result:
            lines.append("=== KEY FINANCIAL METRICS ===\n")
            for concept, data in result['key_metrics'].items():
                # Make concept readable
                readable = re.sub(r'([A-Z])', r' \1', concept).strip()
                lines.append(f"{readable}: {data['value']}")

        # Add context info
        if result.get('contexts'):
            lines.append("\n=== REPORTING PERIODS ===\n")
            for ctx_id, ctx in list(result['contexts'].items())[:5]:
                if 'instant' in ctx:
                    lines.append(f"{ctx_id}: {ctx['instant']}")
                elif 'start_date' in ctx:
                    lines.append(f"{ctx_id}: {ctx['start_date']} to {ctx['end_date']}")

        return '\n'.join(lines)

    def get_financial_statement(
            self,
            result: Dict[str, Any],
            statement_type: str = 'income'
    ) -> Dict[str, Any]:
        """
        Extract a specific financial statement.
        
        Args:
            result: Parsed XBRL result
            statement_type: Type of statement (income, balance, cashflow)
            
        Returns:
            Structured financial statement data
        """
        concepts_map = {
            'income': [
                'Revenues', 'CostOfGoodsAndServicesSold', 'GrossProfit',
                'OperatingIncomeLoss', 'NetIncomeLoss'
            ],
            'balance': [
                'Assets', 'AssetsCurrent', 'Liabilities', 'LiabilitiesCurrent',
                'StockholdersEquity'
            ],
            'cashflow': [
                'NetCashProvidedByUsedInOperatingActivities',
                'NetCashProvidedByUsedInInvestingActivities',
                'NetCashProvidedByUsedInFinancingActivities'
            ]
        }

        concepts = concepts_map.get(statement_type, [])
        statement = {}

        for concept in concepts:
            if concept in result.get('key_metrics', {}):
                statement[concept] = result['key_metrics'][concept]

        return {
            'statement_type': statement_type,
            'line_items': statement
        }
