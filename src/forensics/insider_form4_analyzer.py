"""
Insider Form 4 Analyzer - HOLY GRAIL INTEGRATION
- Parses Form 4 XML filings using Universal SEC Extractor
- Detects late filings (Section 16(a) - 2 business day rule)
- Detects zero-dollar transactions (potential gifts/RSU vesting)
- Produces prosecution-ready violation records with quotes and URLs
- 100% extraction coverage with comprehensive transaction parsing
"""

from __future__ import annotations

import aiohttp
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import re
import xml.etree.ElementTree as ET
import logging

from .statute_mapper import StatuteViolation
from .universal_sec_extractor import UniversalDocumentExtractor, DocumentFormat

logger = logging.getLogger(__name__)


@dataclass
class Form4ViolationRecord:
    type: str  # late_form4 | zero_dollar_transaction
    severity: str  # HIGH | MEDIUM | CRITICAL
    statute_title: int  # 15
    statute_section: str  # 78p(a)
    description: str
    exact_quote: Optional[str]
    document_url: str
    viewer_url: Optional[str]
    document_section: Optional[str]
    prosecutorial_merit: str  # WEAK | MODERATE | STRONG
    estimated_damages: Optional[int]
    evidence_refs: List[str]


class InsiderForm4Analyzer:
    """Analyzer for SEC Form 4 insider trading filings."""

    def __init__(self, user_agent: str = "NITS Recon Unit contact@nits-secops.org"):
        # Use SEC-compliant UA across all HTTP requests
        self.user_agent = user_agent

    async def analyze_form4(
        self,
        xml_url: str,
        viewer_url: Optional[str] = None,
        filing_date_str: Optional[str] = None
    ) -> List[Form4ViolationRecord]:
        """Analyze a single Form 4 XML using HOLY GRAIL Universal Extractor."""
        xml_text = await self._fetch(xml_url)
        violations: List[Form4ViolationRecord] = []

        # HOLY GRAIL INTEGRATION: Use Universal SEC Extractor for 100% coverage
        logger.info(f"[Form4 Holy Grail] Extracting: {xml_url}")
        extractor = UniversalDocumentExtractor()
        
        try:
            extraction_result = await extractor.extract_document(
                content=xml_text,
                url=xml_url,
                force_format=DocumentFormat.XML
            )
            
            logger.info(f"[Form4 Holy Grail] Coverage: {extraction_result.byte_coverage:.1%}, Elements: {extraction_result.element_count}")
            
            # Extract transactions from structured data
            tx_records: List[Dict[str, Optional[str]]] = []
            
            if 'transactions' in extraction_result.structured_data:
                transactions = extraction_result.structured_data['transactions']
                logger.info(f"[Form4 Holy Grail] Found {len(transactions)} transactions")
                
                for tx in transactions:
                    # Normalize field names to match our detection logic
                    tx_record = {
                        'date': tx.get('transactionDate'),
                        'price': tx.get('transactionPricePerShare'),
                        'shares': tx.get('transactionShares'),
                        'code': tx.get('transactionCode'),
                        'acq_disp': tx.get('transactionAcquiredDisposedCode')
                    }
                    tx_records.append(tx_record)
                    logger.info(f"[Form4 Holy Grail] Transaction: {tx_record}")
            else:
                logger.warning(f"[Form4 Holy Grail] No transactions found in structured_data")
                # Fallback to regex extraction
                tx_records = []
        
        except Exception as e:
            logger.error(f"[Form4 Holy Grail] Extraction failed: {e}, falling back to legacy parsing")
            # Fallback to legacy XML parsing
            try:
                from lxml import etree
                parser = etree.XMLParser(recover=True, remove_blank_text=True, huge_tree=True)
                root = etree.fromstring(xml_text.encode('utf-8'), parser)
                tx_records = []
                
                if root is not None and hasattr(root, 'xpath'):
                    for tx_type in ['nonDerivativeTransaction', 'derivativeTransaction']:
                        for tx in root.xpath(f'//*[local-name()="{tx_type}"]'):
                            tx_data = self._parse_transaction_xml_comprehensive(tx)
                            tx_records.append(tx_data)
            except Exception as e2:
                logger.error(f"[Form4] Fallback also failed: {e2}")
                tx_records = []
        
        # Continue with existing violation detection logic
        if not tx_records:
            # Fallback for ElementTree (no XPath)
            def _ln(tag: str) -> str:
                return tag[tag.rfind('}')+1:] if '}' in tag else tag

            def _first_text(node) -> Optional[str]:
                if node is None:
                    return None
                if hasattr(node, 'text') and node.text and node.text.strip():
                    return node.text.strip()
                # Some values are inside <value>
                for ch in node:
                    if _ln(ch.tag).lower() == 'value' and hasattr(ch, 'text') and ch.text and ch.text.strip():
                        return ch.text.strip()
                return None

            # Traverse all elements
            for el in root.iter():
                name = _ln(el.tag).lower()
                if name in ('nonderivativetransaction', 'derivativetransaction'):
                    tdate = None
                    price = None
                    shares = None
                    code = None
                    acqd = None
                    for sub in el.iter():
                        sname = _ln(sub.tag).lower()
                        if sname == 'transactiondate' and tdate is None:
                            t = _first_text(sub)
                            if t:
                                tdate = t
                        elif sname in ('transactionpricepershare', 'pricepershare', 'price') and price is None:
                            p = _first_text(sub)
                            if p is not None:
                                price = p
                        elif sname in ('transactionshares', 'shares') and shares is None:
                            sh = _first_text(sub)
                            if sh is not None:
                                shares = sh
                        elif sname == 'transactioncode' and code is None:
                            c = _first_text(sub)
                            if c:
                                code = c
                        elif sname == 'transactionacquireddisposedcode' and acqd is None:
                            ad = _first_text(sub)
                            if ad:
                                acqd = ad
                    tx_records.append({'date': tdate, 'price': price, 'shares': shares, 'code': code, 'acq_disp': acqd})

        # Extract key fields via regex (fallback; robust to namespace variations)
        ns_val = r"(?:edgar:)?"
        # transactionDate
        tx_dates = re.findall(rf"<{ns_val}transactionDate>\s*<{ns_val}value>(.*?)</{ns_val}value>\s*</{ns_val}transactionDate>", xml_text, flags=re.IGNORECASE)
        # price per share (multiple fallbacks across issuers/templates)
        prices = re.findall(
            rf"<{ns_val}transactionPricePerShare>\s*<{ns_val}value>(.*?)</{ns_val}value>\s*</{ns_val}transactionPricePerShare>",
            xml_text,
            flags=re.IGNORECASE,
        )
        # some variants use pricePerShare or price
        if not prices:
            prices = re.findall(rf"<{ns_val}pricePerShare>\s*<{ns_val}value>(.*?)</{ns_val}value>\s*</{ns_val}pricePerShare>", xml_text, flags=re.IGNORECASE)
        if not prices:
            prices = re.findall(rf"<{ns_val}price>\s*<{ns_val}value>(.*?)</{ns_val}value>\s*</{ns_val}price>", xml_text, flags=re.IGNORECASE)
        # shares amount
        share_amounts = re.findall(rf"<{ns_val}transactionShares>\s*<{ns_val}value>(.*?)</{ns_val}value>\s*</{ns_val}transactionShares>", xml_text, flags=re.IGNORECASE)
        # transaction codes
        codes = re.findall(rf"<{ns_val}transactionCode>(.*?)</{ns_val}transactionCode>", xml_text, flags=re.IGNORECASE)
        # acquired/disposed codes (A/D) can indicate awards or disposals
        acq_disp = re.findall(rf"<{ns_val}transactionAcquiredDisposedCode>\s*<{ns_val}value>(.*?)</{ns_val}value>\s*</{ns_val}transactionAcquiredDisposedCode>", xml_text, flags=re.IGNORECASE)
        # period of report (filing date)
        filing_date = None
        # Prefer provided filing date from metadata (accurate filing date), fallback to periodOfReport
        if filing_date_str:
            try:
                filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
            except Exception:
                filing_date = None
        if filing_date is None:
            filing_date_m = re.search(r"<periodOfReport>(.*?)</periodOfReport>", xml_text)
            if filing_date_m:
                try:
                    filing_date = datetime.strptime(filing_date_m.group(1), "%Y-%m-%d")
                except Exception:
                    filing_date = None

        # Build a unified list of transaction dates for lateness check
        tx_date_list: List[str] = []
        if tx_records:
            for r in tx_records:
                if r.get('date'):
                    tx_date_list.append(r['date'])
        else:
            tx_date_list = tx_dates

        # DIAGNOSTIC LOGGING
        logger.info(f"[Form4 Diag] URL: {xml_url}")
        logger.info(f"[Form4 Diag] Filing date provided: {filing_date_str}")
        logger.info(f"[Form4 Diag] Filing date parsed: {filing_date}")
        logger.info(f"[Form4 Diag] Transaction dates found: {tx_date_list}")
        logger.info(f"[Form4 Diag] Transaction records: {len(tx_records)}")
        
        # 1) Late Form 4 detection: (filing date - txn date) > 2 business days
        if filing_date is not None and tx_date_list:
            for td in tx_date_list:
                try:
                    tdate = datetime.strptime(td.strip(), "%Y-%m-%d")
                except Exception as e:
                    logger.warning(f"[Form4 Diag] Failed to parse transaction date '{td}': {e}")
                    continue
                business_days = self._business_days_between(tdate, filing_date)
                logger.info(f"[Form4 Diag] Transaction {tdate.date()} → Filing {filing_date.date()} = {business_days} business days")
                if business_days > 2:
                    quote = f"Transaction date {tdate.date()} filed on {filing_date.date()} (>2 business days)"
                    penalty = self._late_form4_penalty(business_days)
                    violations.append(Form4ViolationRecord(
                        type="late_form4",
                        severity="HIGH",
                        statute_title=15,
                        statute_section="78p(a)",
                        description=f"Late Form 4 filing by {business_days} business days",
                        exact_quote=quote,
                        document_url=xml_url,
                        viewer_url=viewer_url,
                        document_section="Cover/Timing",
                        prosecutorial_merit="STRONG" if business_days >= 3 else "MODERATE",
                        estimated_damages=penalty,
                        evidence_refs=[xml_url]
                    ))

        # 2) Zero-dollar transactions (price 0.00) and vesting/gift code signals
        any_zero_flagged = False
        logger.info(f"[Form4 Diag] Checking zero-dollar transactions in {len(tx_records)} records")
        if tx_records:
            for r in tx_records:
                price_s = (r.get('price') or '').replace(',', '').strip()
                code_s = (r.get('code') or '').strip().upper()
                shares_s = (r.get('shares') or '').replace(',', '').strip()
                p = None
                try:
                    p = float(price_s) if price_s != '' else None
                except Exception:
                    p = None
                shares_val = None
                try:
                    shares_val = float(shares_s) if shares_s != '' else None
                except Exception:
                    shares_val = None
                
                logger.info(f"[Form4 Diag] Transaction: price={price_s} ({p}), code={code_s}, shares={shares_s} ({shares_val})")
                
                if p == 0.0:
                    quote = f"Transaction code {code_s or '?'} at $0.00 per share for {int(shares_val) if shares_val is not None else 'N/A'} shares"
                    violations.append(Form4ViolationRecord(
                        type="zero_dollar_transaction",
                        severity="HIGH",
                        statute_title=15,
                        statute_section="78p(a)",
                        description="Zero-dollar transaction (potential gift/RSU vesting)",
                        exact_quote=quote,
                        document_url=xml_url,
                        viewer_url=viewer_url,
                        document_section="Non-derivative Transactions",
                        prosecutorial_merit="MODERATE",
                        estimated_damages=None,
                        evidence_refs=[xml_url]
                    ))
                    any_zero_flagged = True
        else:
            for i, price in enumerate(prices or []):
                try:
                    p = float((price or '').replace(',', '').strip())
                except Exception:
                    continue
                code = (codes[i] if i < len(codes) else '').strip().upper()
                shares = None
                if i < len(share_amounts):
                    try:
                        shares = float(share_amounts[i].replace(',', '').strip())
                    except Exception:
                        shares = None
                if p == 0.0:
                    quote = f"Transaction code {code or '?'} at $0.00 per share for {int(shares) if shares is not None else 'N/A'} shares"
                    violations.append(Form4ViolationRecord(
                        type="zero_dollar_transaction",
                        severity="HIGH",
                        statute_title=15,
                        statute_section="78p(a)",
                        description="Zero-dollar transaction (potential gift/RSU vesting)",
                        exact_quote=quote,
                        document_url=xml_url,
                        viewer_url=viewer_url,
                        document_section="Non-derivative Transactions",
                        prosecutorial_merit="MODERATE",
                        estimated_damages=None,
                        evidence_refs=[xml_url]
                    ))
                    any_zero_flagged = True

        # Heuristic: if no explicit $0.00 found, interpret vesting/gift codes with missing/blank price as zero-dollar
        if not any_zero_flagged:
            # If any transactionCode is V (vesting) or G (gift) and there is no parseable price or blank/None values, flag
            code_set = {c.strip().upper() for c in (codes or []) if c}
            has_vesting_or_gift = any(c in {"V", "G"} for c in code_set)
            # Consider acquired (A) with no price also as possible award/RSU vesting depending on filer practices
            has_award = any((ad or '').strip().upper() == 'A' for ad in (acq_disp or []))
            # Treat missing or empty prices as zero indicators when codes suggest non-cash award
            missing_prices = len(prices) == 0 or all(((p or '').strip() == '') for p in prices)
            if (has_vesting_or_gift or has_award) and missing_prices:
                quote = "Transaction with vesting/gift/award code and no price disclosed (interpreted as $0.00)"
                violations.append(Form4ViolationRecord(
                    type="zero_dollar_transaction",
                    severity="HIGH",
                    statute_title=15,
                    statute_section="78p(a)",
                    description="Zero-dollar transaction inferred from code (V/G/A) with no price disclosed",
                    exact_quote=quote,
                    document_url=xml_url,
                    viewer_url=viewer_url,
                    document_section="Non-derivative Transactions",
                    prosecutorial_merit="MODERATE",
                    estimated_damages=None,
                    evidence_refs=[xml_url]
                ))

        # DIAGNOSTIC SUMMARY
        logger.info(f"[Form4 Diag] SUMMARY: {len(violations)} violations detected")
        if violations:
            for v in violations:
                logger.info(f"[Form4 Diag]   - {v.type}: {v.description}")
        else:
            logger.warning(f"[Form4 Diag] NO VIOLATIONS detected despite:")
            logger.warning(f"[Form4 Diag]   Filing date: {filing_date}")
            logger.warning(f"[Form4 Diag]   Transaction dates: {len(tx_date_list)}")
            logger.warning(f"[Form4 Diag]   Transaction records: {len(tx_records)}")
            logger.warning(f"[Form4 Diag]   Prices parsed: {len(prices)}")
            logger.warning(f"[Form4 Diag]   Codes parsed: {len(codes)}")
        
        return violations

    async def _fetch(self, url: str) -> str:
        # Rate limit
        await asyncio.sleep(0.6)
        
        for attempt in range(4):
            try:
                async with aiohttp.ClientSession(headers={"User-Agent": self.user_agent}) as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            return await resp.text()
                        # backoff with jitter
                        await asyncio.sleep(1 + attempt * 0.5 + (0.2 * attempt))
            except Exception:
                if attempt == 3:
                    raise
        raise RuntimeError(f"Failed to fetch {url}")

    def _business_days_between(self, start: datetime, end: datetime) -> int:
        if end < start:
            return 0
        day_count = 0
        cur = start
        while cur < end:
            cur += timedelta(days=1)
            if cur.weekday() < 5:  # Mon-Fri
                day_count += 1
        return day_count

    def _late_form4_penalty(self, business_days: int) -> int:
        # Benchmark tiers: 3–10: $25k, 11–30: $50k, 30+: $100k
        if business_days >= 30:
            return 100_000
        if business_days >= 11:
            return 50_000
        if business_days >= 3:
            return 25_000
        return 0

    def _parse_transaction_xml_comprehensive(self, tx_elem) -> Dict[str, Optional[str]]:
        """
        HOLY GRAIL: Parse transaction element with comprehensive field extraction.
        Handles nested <value> elements and multiple field name variations.
        """
        tx_data = {}
        
        # Define all possible transaction fields from Holy Grail
        field_mappings = {
            'date': ['transactionDate', 'deemedExecutionDate'],
            'code': ['transactionCode'],
            'shares': ['transactionShares', 'shares', 'amountOfShares'],
            'price': ['transactionPricePerShare', 'pricePerShare', 'price', 'conversionOrExercisePrice'],
            'acq_disp': ['transactionAcquiredDisposedCode', 'acquiredDisposedCode'],
            'shares_owned': ['sharesOwnedFollowingTransaction', 'postTransactionAmounts'],
            'ownership': ['directOrIndirectOwnership', 'ownershipNature']
        }
        
        # Extract each field type
        for key, field_names in field_mappings.items():
            for field_name in field_names:
                # Use XPath with local-name() for namespace handling
                elem = tx_elem.find(f'.//*[local-name()="{field_name}"]')
                if elem is not None:
                    # Check for nested <value> element (common in Form 4 XML)
                    value_elem = elem.find('.//*[local-name()="value"]')
                    if value_elem is not None and hasattr(value_elem, 'text') and value_elem.text:
                        tx_data[key] = value_elem.text.strip()
                        break
                    elif hasattr(elem, 'text') and elem.text:
                        tx_data[key] = elem.text.strip()
                        break
        
        return tx_data

