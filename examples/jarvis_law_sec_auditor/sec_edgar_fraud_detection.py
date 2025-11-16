"""
SEC EDGAR API Integration with Fraud Detection Patterns
Handles 10 req/s limits, XBRL parsing, and multi-document correlation
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from lxml import etree
import pandas as pd
import numpy as np
from scipy import stats
from dataclasses import dataclass
import json

from forensic_core_architecture import (
    ForensicAPIClient, BlockchainAuditTrail, ChainOfCustody,
    ViolationType, HardFailureException, logger
)

@dataclass
class FilingMetadata:
    """SEC filing metadata with fraud indicators"""
    cik: str
    form_type: str
    filing_date: datetime
    period_end: datetime
    accession_number: str
    file_number: Optional[str]
    amendments: int = 0
    late_filing: bool = False
    restatement: bool = False
    going_concern: bool = False
    material_weakness: bool = False
    
    @property
    def filing_delay_days(self) -> int:
        """Calculate delay between period end and filing"""
        return (self.filing_date - self.period_end).days
    
    @property
    def deadline_days(self) -> int:
        """Get filing deadline based on filer status"""
        deadlines = {
            "10-K": {"large": 60, "accelerated": 75, "non-accelerated": 90},
            "10-Q": {"large": 40, "accelerated": 40, "non-accelerated": 45}
        }
        form_base = self.form_type.replace("/A", "")
        if form_base in deadlines:
            # Default to non-accelerated (conservative)
            return deadlines[form_base]["non-accelerated"]
        return 0
    
    @property
    def is_late(self) -> bool:
        """Determine if filing is late without NT filing"""
        return self.filing_delay_days > self.deadline_days

class XBRLValidator:
    """XBRL validation with DQC rules and fraud detection"""
    
    DQC_RULES = {
        "DQC_0015": "Negative values for typically positive items",
        "DQC_0001": "Axis member combinations invalid",
        "DQC_0004": "Element values inconsistent with element name",
        "DQC_0005": "ContextDateForNonTimePeriod",
        "DQC_0006": "DEI and block tag date contexts",
        "DQC_0008": "Reversed calculation",
        "DQC_0009": "Element A must be less than or equal to Element B",
        "DQC_0013": "Negative values with dependence",
        "DQC_0033": "Document period end date context",
        "DQC_0036": "Document period end date context/fact value check"
    }
    
    def __init__(self):
        self.namespaces = {
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'us-gaap': 'http://fasb.org/us-gaap/2023',
            'dei': 'http://xbrl.sec.gov/dei/2023'
        }
        self.violations = []
    
    def validate(self, xbrl_content: bytes) -> List[Dict]:
        """Validate XBRL against DQC rules"""
        try:
            tree = etree.fromstring(xbrl_content)
            
            # DQC_0015: Check for negative values
            self._check_negative_values(tree)
            
            # DQC_0001: Invalid axis-member combinations
            self._check_axis_members(tree)
            
            # DQC_0008: Reversed calculations
            self._check_calculations(tree)
            
            # Custom fraud indicators
            self._check_revenue_recognition(tree)
            self._check_quarter_end_activity(tree)
            
            return self.violations
            
        except Exception as e:
            logger.error(f"XBRL validation failed: {e}")
            return [{"rule": "PARSE_ERROR", "message": str(e)}]
    
    def _check_negative_values(self, tree: etree.Element):
        """DQC_0015: Negative values for typically positive items"""
        positive_elements = [
            'Assets', 'CurrentAssets', 'Revenue', 'Revenues',
            'CashAndCashEquivalentsAtCarryingValue', 'CommonStockSharesOutstanding'
        ]
        
        for element in positive_elements:
            nodes = tree.xpath(f"//us-gaap:{element}", namespaces=self.namespaces)
            for node in nodes:
                try:
                    value = float(node.text)
                    if value < 0:
                        self.violations.append({
                            "rule": "DQC_0015",
                            "element": element,
                            "value": value,
                            "context": node.get("contextRef"),
                            "severity": "HIGH"
                        })
                except (ValueError, TypeError):
                    pass
    
    def _check_axis_members(self, tree: etree.Element):
        """DQC_0001: Invalid axis-member combinations"""
        # Implementation would check specific business rules
        # This is a simplified version
        contexts = tree.xpath("//xbrli:context", namespaces=self.namespaces)
        for context in contexts:
            dimensions = context.xpath(".//xbrldi:explicitMember",
                                      namespaces={'xbrldi': 'http://xbrl.org/2006/xbrldi'})
            # Validate dimension combinations
    
    def _check_calculations(self, tree: etree.Element):
        """DQC_0008: Reversed calculation relationships"""
        # Assets = Liabilities + Equity
        assets = self._get_fact_value(tree, "Assets")
        liabilities = self._get_fact_value(tree, "Liabilities")
        equity = self._get_fact_value(tree, "StockholdersEquity")
        
        if all([assets, liabilities, equity]):
            calculated = liabilities + equity
            if abs(assets - calculated) > 0.01:  # Allow small rounding
                self.violations.append({
                    "rule": "DQC_0008",
                    "message": f"Assets ({assets}) != Liabilities ({liabilities}) + Equity ({equity})",
                    "severity": "CRITICAL"
                })
    
    def _check_revenue_recognition(self, tree: etree.Element):
        """Detect revenue recognition manipulation patterns"""
        revenue = self._get_fact_value(tree, "Revenues")
        receivables = self._get_fact_value(tree, "AccountsReceivableNetCurrent")
        cash_ops = self._get_fact_value(tree, "NetCashProvidedByUsedInOperatingActivities")
        
        if revenue and receivables:
            # Days Sales Outstanding
            dso = (receivables / revenue) * 365
            if dso > 90:  # Industry-specific threshold
                self.violations.append({
                    "rule": "REVENUE_TIMING",
                    "indicator": "HIGH_DSO",
                    "value": dso,
                    "severity": "MEDIUM"
                })
        
        if revenue and cash_ops:
            # Cash flow divergence from revenue
            if cash_ops < revenue * 0.5:  # Less than 50% cash conversion
                self.violations.append({
                    "rule": "REVENUE_QUALITY",
                    "indicator": "LOW_CASH_CONVERSION",
                    "revenue": revenue,
                    "cash_ops": cash_ops,
                    "severity": "HIGH"
                })
    
    def _check_quarter_end_activity(self, tree: etree.Element):
        """Detect quarter-end manipulation patterns"""
        # Would analyze daily/weekly data if available
        # This is a placeholder for the pattern
        pass
    
    def _get_fact_value(self, tree: etree.Element, element: str) -> Optional[float]:
        """Extract numeric value from XBRL element"""
        try:
            node = tree.xpath(f"//us-gaap:{element}[1]", namespaces=self.namespaces)[0]
            return float(node.text)
        except (IndexError, ValueError, TypeError):
            return None

class SECEdgarClient:
    """SEC EDGAR client with fraud detection capabilities"""
    
    BASE_URL = "https://data.sec.gov"
    ARCHIVE_URL = "https://www.sec.gov/Archives/edgar"
    
    def __init__(self, api_client: ForensicAPIClient, audit_trail: BlockchainAuditTrail):
        self.client = api_client
        self.audit = audit_trail
        self.xbrl_validator = XBRLValidator()
    
    async def get_company_filings(self, cik: str, form_types: List[str] = None) -> List[FilingMetadata]:
        """Retrieve company filings with metadata"""
        # Normalize CIK to 10 digits
        cik = cik.zfill(10)
        
        url = f"{self.BASE_URL}/submissions/CIK{cik}.json"
        response = await self.client.fetch_with_retry(url, "sec")
        data = json.loads(response["content"])
        
        filings = []
        recent = data.get("filings", {}).get("recent", {})
        
        for i in range(len(recent.get("form", []))):
            form = recent["form"][i]
            
            if form_types and form not in form_types:
                continue
            
            filing = FilingMetadata(
                cik=cik,
                form_type=form,
                filing_date=datetime.strptime(recent["filingDate"][i], "%Y-%m-%d"),
                period_end=datetime.strptime(recent["reportDate"][i], "%Y-%m-%d")
                    if recent["reportDate"][i] else datetime.min,
                accession_number=recent["accessionNumber"][i],
                file_number=recent.get("fileNumber", [None])[i]
            )
            
            # Check for amendments
            if "/A" in form:
                filing.amendments += 1
            
            # Check if late
            filing.late_filing = filing.is_late
            
            filings.append(filing)
        
        # Log to audit trail
        self.audit.add_entry("SEC_FILINGS_RETRIEVED", {
            "cik": cik,
            "count": len(filings),
            "forms": list(set(f.form_type for f in filings))
        })
        
        return filings
    
    async def analyze_filing_delays(self, filings: List[FilingMetadata]) -> Dict:
        """Analyze filing delay patterns for fraud indicators"""
        delays = [f.filing_delay_days for f in filings if f.filing_delay_days > 0]
        
        if not delays:
            return {}
        
        analysis = {
            "mean_delay": np.mean(delays),
            "median_delay": np.median(delays),
            "std_delay": np.std(delays),
            "max_delay": max(delays),
            "trend": None,
            "red_flags": []
        }
        
        # Trend analysis
        if len(delays) >= 4:
            x = np.arange(len(delays))
            slope, _, r_value, p_value, _ = stats.linregress(x, delays)
            
            if p_value < 0.05 and slope > 0:
                analysis["trend"] = "INCREASING"
                analysis["red_flags"].append({
                    "type": "INCREASING_DELAYS",
                    "severity": "HIGH",
                    "slope": slope,
                    "p_value": p_value
                })
        
        # Check for late filings without NT
        late_without_nt = [f for f in filings if f.late_filing and "NT" not in f.form_type]
        if late_without_nt:
            analysis["red_flags"].append({
                "type": "LATE_WITHOUT_NOTIFICATION",
                "severity": "CRITICAL",
                "count": len(late_without_nt),
                "violations": [ViolationType.CFR_17_240_12b25.value]
            })
        
        return analysis
    
    async def download_filing(self, accession_number: str, primary_doc: str = None) -> Tuple[bytes, ChainOfCustody]:
        """Download filing document with integrity verification"""
        # Remove hyphens from accession number
        acc_no_dashes = accession_number.replace("-", "")
        
        if primary_doc:
            url = f"{self.ARCHIVE_URL}/data/{acc_no_dashes}/{primary_doc}"
        else:
            url = f"{self.ARCHIVE_URL}/data/{acc_no_dashes}/{accession_number}.txt"
        
        response = await self.client.fetch_with_retry(url, "sec")
        content = response["content"]
        
        # Create chain of custody
        custody = ChainOfCustody(
            case_id=f"SEC-{accession_number}",
            collected_by={
                "system": "SECEdgarClient",
                "timestamp": datetime.utcnow().isoformat(),
                "method": "HTTPS",
                "url": url
            },
            initial_hash=response["content_hash"]
        )
        
        # Log download to audit trail
        self.audit.add_entry("FILING_DOWNLOADED", {
            "accession_number": accession_number,
            "size": len(content),
            "hash": response["content_hash"],
            "custody_id": custody.evidence_id
        })
        
        return content, custody
    
    async def validate_xbrl(self, accession_number: str) -> List[Dict]:
        """Validate XBRL filing for DQC violations and fraud indicators"""
        # Download XBRL instance document
        xbrl_content, custody = await self.download_filing(
            accession_number, 
            f"{accession_number}-instance.xml"
        )
        
        violations = self.xbrl_validator.validate(xbrl_content)
        
        # Determine if critical violations exist
        critical_violations = [v for v in violations if v.get("severity") in ["HIGH", "CRITICAL"]]
        
        if critical_violations:
            self.audit.add_entry("XBRL_VIOLATIONS_DETECTED", {
                "accession_number": accession_number,
                "total_violations": len(violations),
                "critical_count": len(critical_violations),
                "rules": list(set(v.get("rule") for v in critical_violations))
            })
        
        return violations

class MultiDocumentCorrelator:
    """Cross-document fraud detection through correlation analysis"""
    
    def __init__(self, edgar_client: SECEdgarClient):
        self.edgar = edgar_client
        self.correlation_patterns = {
            "REVENUE_MANIPULATION": self._detect_revenue_manipulation,
            "CHANNEL_STUFFING": self._detect_channel_stuffing,
            "EARNINGS_MANAGEMENT": self._detect_earnings_management,
            "DISCLOSURE_INCONSISTENCY": self._detect_disclosure_inconsistency
        }
    
    async def analyze_company(self, cik: str, years: int = 3) -> Dict:
        """Comprehensive multi-year analysis for fraud patterns"""
        # Fetch filings
        forms = ["10-K", "10-Q", "8-K", "DEF 14A", "NT 10-K", "NT 10-Q"]
        filings = await self.edgar.get_company_filings(cik, forms)
        
        # Filter to analysis period
        cutoff = datetime.now() - timedelta(days=years * 365)
        recent_filings = [f for f in filings if f.filing_date >= cutoff]
        
        # Group by form type
        grouped = {}
        for filing in recent_filings:
            form_base = filing.form_type.replace("/A", "")
            if form_base not in grouped:
                grouped[form_base] = []
            grouped[form_base].append(filing)
        
        # Run correlation analysis
        results = {
            "cik": cik,
            "period": f"{years} years",
            "filings_analyzed": len(recent_filings),
            "patterns": {},
            "risk_score": 0.0
        }
        
        for pattern_name, detector in self.correlation_patterns.items():
            pattern_result = await detector(grouped)
            results["patterns"][pattern_name] = pattern_result
            
            # Update risk score
            if pattern_result.get("detected"):
                results["risk_score"] += pattern_result.get("confidence", 0.5)
        
        # Normalize risk score to 0-1
        results["risk_score"] = min(1.0, results["risk_score"] / len(self.correlation_patterns))
        
        return results
    
    async def _detect_revenue_manipulation(self, filings: Dict[str, List[FilingMetadata]]) -> Dict:
        """Detect revenue recognition timing manipulation"""
        quarters = filings.get("10-Q", [])
        
        if len(quarters) < 4:
            return {"detected": False, "reason": "Insufficient quarterly data"}
        
        # Sort by period end
        quarters.sort(key=lambda x: x.period_end)
        
        indicators = []
        
        # Check for increasing delays
        delays = [q.filing_delay_days for q in quarters[-4:]]
        if all(delays[i] <= delays[i+1] for i in range(3)):
            indicators.append("INCREASING_FILING_DELAYS")
        
        # Check for amendments
        amendments = sum(1 for q in quarters if "/A" in q.form_type)
        if amendments > 2:
            indicators.append("MULTIPLE_AMENDMENTS")
        
        # Check for restatements (would need to parse filing content)
        restatements = sum(1 for q in quarters if q.restatement)
        if restatements > 0:
            indicators.append("RESTATEMENTS_PRESENT")
        
        detected = len(indicators) >= 2
        
        return {
            "detected": detected,
            "indicators": indicators,
            "confidence": min(1.0, len(indicators) * 0.3),
            "recommendation": "Deep dive into quarter-end transactions" if detected else None
        }
    
    async def _detect_channel_stuffing(self, filings: Dict[str, List[FilingMetadata]]) -> Dict:
        """Detect channel stuffing patterns"""
        # Would need to parse MD&A sections for specific language
        # This is a simplified detection
        
        quarterly = filings.get("10-Q", [])
        eight_ks = filings.get("8-K", [])
        
        indicators = []
        
        # Check for earnings warnings in 8-Ks
        if len(eight_ks) > 5:  # Unusual number of 8-Ks
            indicators.append("EXCESSIVE_8K_FILINGS")
        
        # Check for late filings followed by restatements
        late_quarters = [q for q in quarterly if q.late_filing]
        if late_quarters:
            indicators.append("LATE_QUARTERLY_FILINGS")
        
        return {
            "detected": len(indicators) > 0,
            "indicators": indicators,
            "confidence": min(1.0, len(indicators) * 0.4),
            "recommendation": "Analyze distributor agreements and return policies" if indicators else None
        }
    
    async def _detect_earnings_management(self, filings: Dict[str, List[FilingMetadata]]) -> Dict:
        """Detect earnings management through filing patterns"""
        annuals = filings.get("10-K", [])
        
        if len(annuals) < 2:
            return {"detected": False, "reason": "Insufficient annual data"}
        
        indicators = []
        
        # Check for pattern of just meeting earnings
        # Would need actual earnings data parsing
        
        # Check for auditor changes (in 8-K Item 4.01)
        # This would require parsing 8-K content
        
        # Check for material weaknesses
        material_weaknesses = sum(1 for a in annuals if a.material_weakness)
        if material_weaknesses > 0:
            indicators.append("MATERIAL_WEAKNESSES")
        
        return {
            "detected": len(indicators) > 0,
            "indicators": indicators,
            "confidence": min(1.0, len(indicators) * 0.5),
            "violations": [ViolationType.USC_15_78m.value] if indicators else []
        }
    
    async def _detect_disclosure_inconsistency(self, filings: Dict[str, List[FilingMetadata]]) -> Dict:
        """Detect inconsistencies across document types"""
        # Would compare proxy statements to 10-K executive comp
        # Compare 8-K guidance to actual results
        # This requires deep content analysis
        
        proxy = filings.get("DEF 14A", [])
        annual = filings.get("10-K", [])
        
        if not (proxy and annual):
            return {"detected": False, "reason": "Missing proxy or annual filings"}
        
        # Simplified check for timing consistency
        latest_proxy = max(proxy, key=lambda x: x.filing_date)
        latest_annual = max(annual, key=lambda x: x.filing_date)
        
        indicators = []
        
        # Check if proxy filed significantly after 10-K
        days_diff = (latest_proxy.filing_date - latest_annual.filing_date).days
        if days_diff > 120:  # Proxy should be filed within 120 days
            indicators.append("DELAYED_PROXY_FILING")
        
        return {
            "detected": len(indicators) > 0,
            "indicators": indicators,
            "confidence": min(1.0, len(indicators) * 0.3)
        }

