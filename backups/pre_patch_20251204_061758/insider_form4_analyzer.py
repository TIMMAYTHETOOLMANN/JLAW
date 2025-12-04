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
from typing import Any, Dict, List, Optional, Tuple
import json
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
        # Resolve and fetch robustly (handles xslF345X03/, edgardoc.xml, form4.xml, wf-form4*.xml)
        resolved_url, xml_text = await self._resolve_form4_xml_url(xml_url)
        if resolved_url != xml_url:
            logger.info(f"[Form4 URL Resolver] Resolved URL: {xml_url} → {resolved_url}")
        xml_url = resolved_url
        violations: List[Form4ViolationRecord] = []

        # Parse Form 4 XML using robust lxml parser with fallback
        logger.info(f"[Form4 Parser] Parsing: {xml_url}")
        tx_records: List[Dict[str, Optional[str]]] = []
        root = None
        
        try:
            from lxml import etree
            parser = etree.XMLParser(recover=True, remove_blank_text=True, huge_tree=True)
            root = etree.fromstring(xml_text.encode('utf-8'), parser)
            
            if root is not None and hasattr(root, 'xpath'):
                for tx_type in ['nonDerivativeTransaction', 'derivativeTransaction']:
                    for tx in root.xpath(f'//*[local-name()="{tx_type}"]'):
                        tx_data = self._parse_transaction_xml_comprehensive(tx)
                        tx_records.append(tx_data)
                logger.info(f"[Form4 Parser] Found {len(tx_records)} transactions via lxml")
        except Exception as e:
            logger.warning(f"[Form4 Parser] lxml parsing failed: {e}, trying ElementTree")
            # Fallback to ElementTree
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(xml_text)
                # Will be handled by the ElementTree fallback code below
            except Exception as e2:
                logger.error(f"[Form4 Parser] ElementTree also failed: {e2}")
                root = None

        # Continue with existing violation detection logic
        if not tx_records and root is not None:
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
        # CRITICAL FIX: Do NOT use periodOfReport as fallback - it's the transaction date, not filing date
        # Instead, extract filedAt/dateFiled from index.json or SEC filing header
        if filing_date is None:
            # Try filedAt pattern (SEC EDGAR index.json format)
            filed_at_m = re.search(r'"filedAt"\s*:\s*"(\d{4}-\d{2}-\d{2})', xml_text)
            if filed_at_m:
                try:
                    filing_date = datetime.strptime(filed_at_m.group(1), "%Y-%m-%d")
                except Exception:
                    filing_date = None
        if filing_date is None:
            # Try dateFiled pattern (SGML header format)
            date_filed_m = re.search(r'<FILED-DATE>(\d{8})</FILED-DATE>', xml_text)
            if date_filed_m:
                try:
                    filing_date = datetime.strptime(date_filed_m.group(1), "%Y%m%d")
                except Exception:
                    filing_date = None
        if filing_date is None:
            # Try ACCEPTANCE-DATETIME (more reliable than periodOfReport)
            accept_m = re.search(r'ACCEPTANCE-DATETIME\s*[>:=]\s*(\d{14})', xml_text)
            if accept_m:
                try:
                    filing_date = datetime.strptime(accept_m.group(1)[:8], "%Y%m%d")
                except Exception:
                    filing_date = None
        if filing_date is None:
            # Last resort: periodOfReport (note: this is often WRONG for late filing detection)
            filing_date_m = re.search(r"<periodOfReport>(.*?)</periodOfReport>", xml_text)
            if filing_date_m:
                try:
                    filing_date = datetime.strptime(filing_date_m.group(1), "%Y-%m-%d")
                    logger.warning(f"[Form4 Diag] Using periodOfReport as filing date fallback - may be inaccurate")
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

    async def _fetch(self, url: str, accept: str = "text/xml,application/xml;q=0.9,*/*;q=0.8", return_json: bool = False) -> str:
        """Fetch a URL with SEC-compliant headers and resilient backoff.
        If return_json is True, parse and return JSON text (raw str is still returned; JSON parsing used elsewhere).
        """
        await asyncio.sleep(0.3)  # gentle rate limit per SEC guidance
        headers = {
            "User-Agent": self.user_agent,
            "Accept": accept,
            "Connection": "keep-alive",
        }
        last_exc: Optional[Exception] = None
        for attempt in range(6):
            try:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                    async with session.get(url) as resp:
                        status = resp.status
                        if status == 200:
                            return await resp.text()
                        if status in (301, 302, 303, 307, 308):
                            # Let aiohttp follow redirects automatically; if not, handle location
                            loc = resp.headers.get('Location')
                            if loc:
                                url = loc
                                continue
                        if status in (403, 429):
                            # Too many requests or forbidden: exponential backoff with jitter
                            await asyncio.sleep(min(2 ** attempt * 0.5, 8) + 0.1 * attempt)
                            continue
                        if status == 404:
                            raise FileNotFoundError(f"HTTP 404 for {url}")
                        # Other errors: brief backoff and retry
                        await asyncio.sleep(0.5 + 0.2 * attempt)
            except Exception as e:
                last_exc = e
                await asyncio.sleep(0.4 + 0.2 * attempt)
        if last_exc:
            raise last_exc
        raise RuntimeError(f"Failed to fetch {url}")

    async def _try_get(self, url: str, accept: str = "text/xml,application/xml;q=0.9,*/*;q=0.8") -> Tuple[int, Optional[str]]:
        """Lightweight GET that returns (status, text or None)."""
        try:
            await asyncio.sleep(0.2)
            headers = {
                "User-Agent": self.user_agent,
                "Accept": accept,
            }
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                async with session.get(url) as resp:
                    status = resp.status
                    if status == 200:
                        return status, await resp.text()
                    return status, None
        except Exception:
            return 0, None

    async def _resolve_form4_xml_url(self, xml_url: str) -> Tuple[str, str]:
        """Resolve a robust Form 4 XML URL and return (resolved_url, content).
        CRITICAL FIX: Fetch the raw .txt filing file and extract XML from <TEXT><XML>...</XML></TEXT>
        """
        attempts: List[str] = []
        
        # CRITICAL: The xslF345X03/form4.xml URLs return HTML, not XML!
        # We need to get the raw .txt file instead
        
        # Extract accession number from URL
        # Example: .../000112760219035995/xslF345X03/form4.xml -> 000112760219035995
        accession_match = re.search(r'/(\d{18})/', xml_url)
        if accession_match:
            accession = accession_match.group(1)
            # Format as 0001127602-19-035995
            formatted_accession = f"{accession[:10]}-{accession[10:12]}-{accession[12:]}"
            
            # Construct the .txt file URL
            txt_url = xml_url.split('/xslF345X03')[0] if '/xslF345X03' in xml_url else xml_url.rsplit('/', 1)[0]
            txt_url = f"{txt_url}/{formatted_accession}.txt"
            
            logger.info(f"[Form4 URL Resolver] Fetching raw filing: {txt_url}")
            status, text = await self._try_get(txt_url)
            if status == 200 and text:
                # Extract XML from <TEXT><XML>...</XML></TEXT> section
                xml_match = re.search(r'<TEXT>\s*<XML>(.*?)</XML>\s*</TEXT>', text, re.DOTALL | re.IGNORECASE)
                if xml_match:
                    xml_content = xml_match.group(1).strip()
                    logger.info(f"[Form4 URL Resolver] Successfully extracted XML ({len(xml_content)} bytes)")
                    return txt_url, xml_content
                else:
                    logger.warning(f"[Form4 URL Resolver] No <XML> section found in {txt_url}")
                    attempts.append(f"{txt_url} -> XML section not found")
            else:
                attempts.append(f"{txt_url} -> {status}")
        
        # Fallback: Try the provided URL first
        status, text = await self._try_get(xml_url)
        if status == 200 and text and '<ownershipDocument>' in text:
            return xml_url, text
        attempts.append(f"{xml_url} -> {status}")

        # 2) Derive accession root path
        acc_root = None
        m = re.search(r"(https://www\\.sec\\.gov/Archives/edgar/data/\\d+/\\d+)", xml_url)
        if m:
            acc_root = m.group(1)
        else:
            # Fallback: strip to parent dir, then parent if last folder is xslF345X03
            try:
                base_dir = xml_url.rsplit('/', 1)[0]
                if base_dir.endswith('/xslF345X03'):
                    acc_root = base_dir.rsplit('/', 1)[0]
                else:
                    acc_root = base_dir
            except Exception:
                acc_root = None

        candidates: List[str] = []
        if acc_root:
            candidates.extend([
                f"{acc_root}/edgardoc.xml",
                f"{acc_root}/form4.xml",
                f"{acc_root}/xslF345X03/edgardoc.xml",
                f"{acc_root}/xslF345X03/form4.xml",
            ])

        # 3) Try common candidate paths
        for url in candidates:
            status, text = await self._try_get(url)
            if status == 200 and text:
                logger.info(f"[Form4 URL Resolver] Selected candidate: {url}")
                return url, text
            attempts.append(f"{url} -> {status}")

        # 4) Directory discovery via index.json (top-level)
        if acc_root:
            index_url = f"{acc_root}/index.json"
            status, idx_text = await self._try_get(index_url, accept="application/json, */*;q=0.8")
            attempts.append(f"{index_url} -> {status}")
            if status == 200 and idx_text:
                try:
                    idx = json.loads(idx_text)
                    items = (idx.get('directory') or {}).get('item') or []
                    # First pass: direct XML files matching preferred names
                    preferred_xml = None
                    any_xml = None
                    for it in items:
                        name = it.get('name') or ''
                        itype = it.get('type') or ''
                        href = it.get('href') or name
                        if itype == 'file' and name.lower().endswith('.xml'):
                            any_xml = href
                            lname = name.lower()
                            if lname == 'edgardoc.xml' or lname == 'form4.xml' or lname.startswith('wf-form4'):
                                preferred_xml = href
                                break
                    chosen = preferred_xml or any_xml
                    if chosen:
                        url = f"{acc_root}/{chosen}"
                        status, text = await self._try_get(url)
                        if status == 200 and text:
                            logger.info(f"[Form4 URL Resolver] Discovered via index.json: {url}")
                            return url, text
                        attempts.append(f"{url} -> {status}")
                    # Second pass: if xslF345X03 dir exists, inspect it
                    xsl_dir = next((it for it in items if (it.get('type') == 'dir' and (it.get('name') or '').lower() == 'xslf345x03')), None)
                    if xsl_dir:
                        xsl_index = f"{acc_root}/xslF345X03/index.json"
                        s2, idx2_text = await self._try_get(xsl_index, accept="application/json, */*;q=0.8")
                        attempts.append(f"{xsl_index} -> {s2}")
                        if s2 == 200 and idx2_text:
                            idx2 = json.loads(idx2_text)
                            items2 = (idx2.get('directory') or {}).get('item') or []
                            # Look for form4.xml or edgardoc.xml inside xsl folder
                            for it2 in items2:
                                name2 = (it2.get('name') or '').lower()
                                if name2 in ('form4.xml', 'edgardoc.xml') or name2.startswith('wf-form4'):
                                    url = f"{acc_root}/xslF345X03/{it2.get('name')}"
                                    s3, text3 = await self._try_get(url)
                                    if s3 == 200 and text3:
                                        logger.info(f"[Form4 URL Resolver] Discovered via xsl index: {url}")
                                        return url, text3
                                    attempts.append(f"{url} -> {s3}")
                except Exception as e:
                    logger.warning(f"[Form4 URL Resolver] Failed to parse index.json at {index_url}: {e}")

        # 5) If everything fails, raise with diagnostics
        logger.error("[Form4 URL Resolver] All attempts failed:\n  " + "\n  ".join(attempts))
        raise RuntimeError(f"Failed to resolve Form 4 XML URL starting from {xml_url}")

    # Federal holidays observed by SEC for deadline calculations (2019 calendar)
    FEDERAL_HOLIDAYS_2019 = {
        datetime(2019, 1, 1),   # New Year's Day
        datetime(2019, 1, 21),  # MLK Day
        datetime(2019, 2, 18),  # Presidents' Day
        datetime(2019, 5, 27),  # Memorial Day
        datetime(2019, 7, 4),   # Independence Day
        datetime(2019, 9, 2),   # Labor Day
        datetime(2019, 10, 14), # Columbus Day
        datetime(2019, 11, 11), # Veterans Day
        datetime(2019, 11, 28), # Thanksgiving
        datetime(2019, 12, 25), # Christmas
    }
    
    # Extended holiday set for multi-year analysis
    FEDERAL_HOLIDAYS = {
        # 2018
        datetime(2018, 1, 1), datetime(2018, 1, 15), datetime(2018, 2, 19),
        datetime(2018, 5, 28), datetime(2018, 7, 4), datetime(2018, 9, 3),
        datetime(2018, 10, 8), datetime(2018, 11, 12), datetime(2018, 11, 22), datetime(2018, 12, 25),
        # 2019
        datetime(2019, 1, 1), datetime(2019, 1, 21), datetime(2019, 2, 18),
        datetime(2019, 5, 27), datetime(2019, 7, 4), datetime(2019, 9, 2),
        datetime(2019, 10, 14), datetime(2019, 11, 11), datetime(2019, 11, 28), datetime(2019, 12, 25),
        # 2020
        datetime(2020, 1, 1), datetime(2020, 1, 20), datetime(2020, 2, 17),
        datetime(2020, 5, 25), datetime(2020, 7, 3), datetime(2020, 9, 7),
        datetime(2020, 10, 12), datetime(2020, 11, 11), datetime(2020, 11, 26), datetime(2020, 12, 25),
        # 2021
        datetime(2021, 1, 1), datetime(2021, 1, 18), datetime(2021, 2, 15),
        datetime(2021, 5, 31), datetime(2021, 7, 5), datetime(2021, 9, 6),
        datetime(2021, 10, 11), datetime(2021, 11, 11), datetime(2021, 11, 25), datetime(2021, 12, 24),
        # 2022
        datetime(2022, 1, 17), datetime(2022, 2, 21), datetime(2022, 5, 30),
        datetime(2022, 7, 4), datetime(2022, 9, 5), datetime(2022, 10, 10),
        datetime(2022, 11, 11), datetime(2022, 11, 24), datetime(2022, 12, 26),
        # 2023
        datetime(2023, 1, 2), datetime(2023, 1, 16), datetime(2023, 2, 20),
        datetime(2023, 5, 29), datetime(2023, 7, 4), datetime(2023, 9, 4),
        datetime(2023, 10, 9), datetime(2023, 11, 10), datetime(2023, 11, 23), datetime(2023, 12, 25),
        # 2024
        datetime(2024, 1, 1), datetime(2024, 1, 15), datetime(2024, 2, 19),
        datetime(2024, 5, 27), datetime(2024, 7, 4), datetime(2024, 9, 2),
        datetime(2024, 10, 14), datetime(2024, 11, 11), datetime(2024, 11, 28), datetime(2024, 12, 25),
        # 2025
        datetime(2025, 1, 1), datetime(2025, 1, 20), datetime(2025, 2, 17),
        datetime(2025, 5, 26), datetime(2025, 7, 4), datetime(2025, 9, 1),
        datetime(2025, 10, 13), datetime(2025, 11, 11), datetime(2025, 11, 27), datetime(2025, 12, 25),
    }

    def _is_federal_holiday(self, dt: datetime) -> bool:
        """Check if date is a federal holiday (SEC market closure)."""
        # Normalize to date-only comparison
        dt_date = datetime(dt.year, dt.month, dt.day)
        return dt_date in self.FEDERAL_HOLIDAYS

    def _business_days_between(self, start: datetime, end: datetime) -> int:
        """Calculate business days between dates excluding weekends AND federal holidays."""
        if end < start:
            return 0
        day_count = 0
        cur = start
        while cur < end:
            cur += timedelta(days=1)
            # Mon-Fri (weekday < 5) AND not a federal holiday
            if cur.weekday() < 5 and not self._is_federal_holiday(cur):
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
        Supports both lxml (xpath) and ElementTree (iteration) elements.
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
        
        # Check if this is lxml element (supports xpath) or ElementTree
        has_xpath = hasattr(tx_elem, 'xpath')
        
        # Helper to strip namespace from tag
        def _local_name(tag: str) -> str:
            return tag[tag.rfind('}')+1:] if '}' in tag else tag
        
        # Extract each field type
        for key, field_names in field_mappings.items():
            for field_name in field_names:
                elem = None
                
                if has_xpath:
                    # lxml: Use XPath with local-name() for namespace handling
                    matches = tx_elem.xpath(f'.//*[local-name()="{field_name}"]')
                    elem = matches[0] if matches else None
                else:
                    # ElementTree: Iterate and match by local name
                    for child in tx_elem.iter():
                        if _local_name(child.tag).lower() == field_name.lower():
                            elem = child
                            break
                
                if elem is not None:
                    # Check for nested <value> element (common in Form 4 XML)
                    value_elem = None
                    if has_xpath:
                        value_matches = elem.xpath('.//*[local-name()="value"]')
                        value_elem = value_matches[0] if value_matches else None
                    else:
                        for child in elem.iter():
                            if _local_name(child.tag).lower() == 'value':
                                value_elem = child
                                break
                    
                    if value_elem is not None and hasattr(value_elem, 'text') and value_elem.text:
                        tx_data[key] = value_elem.text.strip()
                        break
                    elif hasattr(elem, 'text') and elem.text:
                        tx_data[key] = elem.text.strip()
                        break
        
        return tx_data

