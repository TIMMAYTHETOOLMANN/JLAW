"""
SEC EDGAR forensic analysis with advanced fraud detection.
Implements multi-document correlation and revenue manipulation detection.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
import re
import json
from urllib.parse import urljoin
import numpy as np
from collections import defaultdict
import pandas as pd
from scipy import stats
import hashlib

from src.forensics.core.integrity_manager import (
    ForensicHashChain, IntegrityLevel, ChainOfCustody, IntegrityError
)

@dataclass
class FilingAnalysis:
    """Forensic analysis results for SEC filing."""
    cik: str
    filing_type: str
    filing_date: datetime
    period_end_date: datetime
    delay_days: int
    amendments: List[str]
    red_flags: List[Dict[str, Any]]
    fraud_indicators: Dict[str, float]
    cross_reference_issues: List[Dict[str, Any]]
    revenue_anomalies: List[Dict[str, Any]]
    benford_analysis: Dict[str, Any]
    narrative_consistency: float
    integrity_hash: str

class SECForensicAnalyzer:
    """
    Advanced SEC filing forensic analyzer with fraud detection.
    Implements TimeTrail methodology and multi-document correlation.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://data.sec.gov"
        self.user_agent = "ForensicAnalyzer contact@forensics.com"  # Required format
        self.rate_limit = 7  # Effective rate for medium-volume operations
        self.session = None
        self.hash_chain = ForensicHashChain("sec_forensics")
        self.filing_cache: Dict[str, Any] = {}
        self.fraud_patterns = self._load_fraud_patterns()
    
    def _load_fraud_patterns(self) -> Dict[str, Any]:
        """Load known fraud patterns from historical cases."""
        return {
            "revenue_manipulation": {
                "pull_forward": {
                    "indicators": ["quarter_end_spike", "subsequent_reversal", "channel_stuffing"],
                    "threshold": 0.16,  # Marvell Technology case: 16% of quarterly revenue
                    "detection_lag_years": 4.1  # Average fraud duration
                },
                "channel_stuffing": {
                    "indicators": ["distributor_inventory_growth", "high_returns", "dso_expansion"],
                    "bristol_myers_amount": 1500000000,  # $1.5B oversold to wholesalers
                    "detection_method": "whistleblower"  # 60% of cases
                },
                "cut_off_manipulation": {
                    "indicators": ["shipment_timing", "return_rights", "side_agreements"],
                    "detection_rate": 0.33  # 33% of XBRL errors are axis-member combinations
                }
            },
            "expense_capitalization": {
                "worldcom_pattern": {
                    "amount": 3800000000,  # $3.8B operating expenses as assets
                    "income_growth": 5.0,  # 500% income growth
                    "revenue_growth": 0.05,  # 5% revenue growth
                    "impossible_ratio": 100.0  # Income/revenue growth ratio
                }
            },
            "executive_fraud": {
                "missing_cfo": {
                    "theranos_years": 12,  # No CFO for 12 years
                    "red_flag_level": "CRITICAL"
                },
                "certification_fraud": {
                    "section_1350_penalty_years": 20,  # Willful false certification
                    "fine": 5000000  # $5M fine
                }
            }
        }
    
    async def analyze_filing(
        self,
        cik: str,
        accession_number: str,
        filing_type: str = "10-K"
    ) -> FilingAnalysis:
        """
        Comprehensive forensic analysis of SEC filing.
        
        Args:
            cik: Central Index Key
            accession_number: SEC accession number
            filing_type: Type of filing (10-K, 10-Q, 8-K, etc.)
        
        Returns:
            FilingAnalysis with fraud indicators and red flags
        """
        # Initialize session
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent}
            )
        
        # Fetch filing data
        filing_data = await self._fetch_filing(cik, accession_number)
        
        # Parse key dates
        filing_date = datetime.fromisoformat(filing_data["filingDate"])
        period_end = datetime.fromisoformat(filing_data["periodOfReport"])
        
        # Calculate delay
        expected_deadline = self._calculate_deadline(period_end, filing_type, cik)
        delay_days = (filing_date - expected_deadline).days
        
        # Initialize analysis
        analysis = FilingAnalysis(
            cik=cik,
            filing_type=filing_type,
            filing_date=filing_date,
            period_end_date=period_end,
            delay_days=delay_days,
            amendments=[],
            red_flags=[],
            fraud_indicators={},
            cross_reference_issues=[],
            revenue_anomalies=[],
            benford_analysis={},
            narrative_consistency=0.0,
            integrity_hash=""
        )
        
        # Run forensic checks
        await self._check_filing_delays(analysis)
        await self._analyze_amendments(analysis, cik, accession_number)
        await self._detect_revenue_manipulation(analysis, filing_data)
        await self._perform_benford_analysis(analysis, filing_data)
        await self._check_cross_document_consistency(analysis, cik, period_end)
        await self._analyze_narrative_consistency(analysis, filing_data)
        await self._detect_accounting_fraud_patterns(analysis, filing_data)
        
        # Calculate overall fraud probability
        analysis.fraud_indicators["overall_risk"] = self._calculate_fraud_risk(analysis)
        
        # Generate integrity hash
        analysis.integrity_hash = self._generate_analysis_hash(analysis)
        
        # Add to forensic chain
        await self.hash_chain.add_evidence(
            {
                "type": "filing_analysis",
                "cik": cik,
                "accession": accession_number,
                "fraud_risk": analysis.fraud_indicators["overall_risk"],
                "red_flags": len(analysis.red_flags),
                "hash": analysis.integrity_hash
            },
            IntegrityLevel.CRITICAL
        )
        
        return analysis
    
    async def _fetch_filing(self, cik: str, accession: str) -> Dict[str, Any]:
        """Fetch filing with rate limiting and retry logic."""
        url = f"{self.base_url}/submissions/CIK{cik.zfill(10)}/{accession}.json"
        
        for attempt in range(3):
            try:
                # Rate limiting
                await asyncio.sleep(1.0 / self.rate_limit)
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 503:
                        # GovInfo-style retry
                        retry_after = int(response.headers.get("Retry-After", 30))
                        await asyncio.sleep(retry_after)
                    elif response.status == 429:
                        # Rate limit hit - exponential backoff
                        await asyncio.sleep(2 ** attempt * 5)
            except Exception as e:
                if attempt == 2:
                    raise IntegrityError(f"Failed to fetch filing: {e}")
        
        raise IntegrityError("Maximum retries exceeded")
    
    async def _check_filing_delays(self, analysis: FilingAnalysis):
        """Detect suspicious filing delays indicating problems."""
        # Based on research: accounting delays average 41 days
        if analysis.delay_days > 0:
            severity = "LOW"
            if analysis.delay_days > 41:
                severity = "HIGH"
                analysis.red_flags.append({
                    "type": "excessive_delay",
                    "severity": severity,
                    "delay_days": analysis.delay_days,
                    "expected_issue": "accounting_problems",
                    "stock_impact": -0.03 if analysis.filing_type == "10-Q" else -0.02
                })
            
            if analysis.delay_days > 15 and "NT" not in analysis.filing_type:
                analysis.red_flags.append({
                    "type": "missing_nt_filing",
                    "severity": "CRITICAL",
                    "description": "Late filing without Form 12b-25 notification",
                    "penalty_range": "$25,000-$225,000"
                })
    
    async def _analyze_amendments(self, analysis: FilingAnalysis, cik: str, accession: str):
        """Check for suspicious amendment patterns."""
        # Fetch amendment history
        amendments = await self._fetch_amendments(cik, accession)
        
        analysis.amendments = amendments
        
        if len(amendments) > 2:
            analysis.red_flags.append({
                "type": "excessive_amendments",
                "severity": "HIGH",
                "count": len(amendments),
                "description": "Multiple amendments suggest material errors"
            })
        
        # Check for amendments filed shortly after extensions
        for amendment in amendments:
            if (amendment["filing_date"] - analysis.filing_date).days < 30:
                analysis.red_flags.append({
                    "type": "rapid_amendment",
                    "severity": "HIGH",
                    "days_after_original": (amendment["filing_date"] - analysis.filing_date).days,
                    "description": "Amendment filed shortly after original"
                })
    
    async def _detect_revenue_manipulation(self, analysis: FilingAnalysis, filing_data: Dict):
        """Detect revenue recognition manipulation patterns."""
        financial_data = filing_data.get("financials", {})
        
        if not financial_data:
            return
        
        # Extract revenue data
        revenues = financial_data.get("revenues", [])
        if not revenues:
            return
        
        # Check for quarter-end spikes (pull-forward schemes)
        monthly_revenues = self._extract_monthly_revenues(revenues)
        if monthly_revenues:
            quarter_ends = [2, 5, 8, 11]  # March, June, September, December
            
            for month_idx in quarter_ends:
                if month_idx < len(monthly_revenues):
                    month_revenue = monthly_revenues[month_idx]
                    avg_revenue = np.mean(monthly_revenues)
                    
                    if month_revenue > avg_revenue * 1.16:  # Marvell threshold
                        analysis.revenue_anomalies.append({
                            "type": "quarter_end_spike",
                            "month": month_idx + 1,
                            "revenue": month_revenue,
                            "deviation": (month_revenue / avg_revenue) - 1,
                            "marvell_threshold_exceeded": True,
                            "severity": "CRITICAL"
                        })
                        
                        analysis.red_flags.append({
                            "type": "revenue_pull_forward",
                            "severity": "CRITICAL",
                            "pattern": "marvell_technology",
                            "deviation": (month_revenue / avg_revenue) - 1
                        })
        
        # Check DSO expansion (Days Sales Outstanding)
        dso = self._calculate_dso(financial_data)
        if dso:
            historical_dso = self._get_historical_dso(analysis.cik)
            if historical_dso and dso > historical_dso * 1.3:
                analysis.revenue_anomalies.append({
                    "type": "dso_expansion",
                    "current_dso": dso,
                    "historical_dso": historical_dso,
                    "increase": (dso / historical_dso) - 1,
                    "channel_stuffing_indicator": True
                })
        
        # Check for impossible growth ratios (WorldCom pattern)
        income_growth = financial_data.get("income_growth", 0)
        revenue_growth = financial_data.get("revenue_growth", 0)
        
        if revenue_growth > 0 and income_growth / revenue_growth > 10:
            analysis.red_flags.append({
                "type": "impossible_growth_ratio",
                "severity": "CRITICAL",
                "pattern": "worldcom",
                "income_growth": income_growth,
                "revenue_growth": revenue_growth,
                "ratio": income_growth / revenue_growth
            })
    
    async def _perform_benford_analysis(self, analysis: FilingAnalysis, filing_data: Dict):
        """Apply Benford's Law to detect fabricated numbers."""
        numbers = self._extract_all_numbers(filing_data)
        
        if len(numbers) < 100:
            return
        
        # Get first digits
        first_digits = [int(str(abs(n))[0]) for n in numbers if n != 0]
        
        # Expected Benford distribution
        benford_expected = {
            1: 0.301, 2: 0.176, 3: 0.125, 4: 0.097,
            5: 0.079, 6: 0.067, 7: 0.058, 8: 0.051, 9: 0.046
        }
        
        # Calculate actual distribution
        digit_counts = defaultdict(int)
        for digit in first_digits:
            digit_counts[digit] += 1
        
        total = len(first_digits)
        actual_dist = {d: count/total for d, count in digit_counts.items()}
        
        # Chi-square test
        chi_square = sum(
            ((actual_dist.get(d, 0) - expected) ** 2) / expected
            for d, expected in benford_expected.items()
        )
        
        # Critical value at 0.01 significance level with 8 degrees of freedom
        critical_value = 20.09
        
        analysis.benford_analysis = {
            "chi_square": chi_square,
            "critical_value": critical_value,
            "suspicious": chi_square > critical_value,
            "actual_distribution": actual_dist,
            "expected_distribution": benford_expected
        }
        
        if chi_square > critical_value:
            analysis.red_flags.append({
                "type": "benford_violation",
                "severity": "HIGH",
                "chi_square": chi_square,
                "description": "Number distribution suggests possible fabrication"
            })
    
    async def _check_cross_document_consistency(
        self,
        analysis: FilingAnalysis,
        cik: str,
        period_end: datetime
    ):
        """Verify consistency across related filings."""
        # Fetch related filings (10-Q, 8-K, proxy)
        related_filings = await self._fetch_related_filings(cik, period_end)
        
        for filing in related_filings:
            filing_data = await self._fetch_filing(cik, filing["accession"])
            
            # Check revenue consistency
            if filing["type"] == "10-Q":
                quarterly_revenue = filing_data.get("financials", {}).get("revenue", 0)
                annual_revenue = analysis.filing_data.get("financials", {}).get("revenue", 0)
                
                # Q4 10-Q should approximately match annual difference
                expected_q4 = annual_revenue - sum(
                    f.get("revenue", 0) for f in related_filings 
                    if f["type"] == "10-Q" and f != filing
                )
                
                if abs(quarterly_revenue - expected_q4) > expected_q4 * 0.05:
                    analysis.cross_reference_issues.append({
                        "type": "revenue_inconsistency",
                        "filing1": analysis.filing_type,
                        "filing2": filing["type"],
                        "discrepancy": abs(quarterly_revenue - expected_q4),
                        "severity": "HIGH"
                    })
            
            # Check 8-K consistency
            if filing["type"] == "8-K":
                events = filing_data.get("events", [])
                for event in events:
                    if event["type"] == "material_event" and not self._event_disclosed_in_10k(
                        event, analysis.filing_data
                    ):
                        analysis.cross_reference_issues.append({
                            "type": "undisclosed_material_event",
                            "event": event["description"],
                            "8k_date": filing["filing_date"],
                            "severity": "CRITICAL"
                        })
    
    async def _analyze_narrative_consistency(self, analysis: FilingAnalysis, filing_data: Dict):
        """Analyze MD&A narrative for consistency and red flags."""
        mda_text = filing_data.get("mda", "")
        
        if not mda_text:
            analysis.red_flags.append({
                "type": "missing_mda",
                "severity": "CRITICAL",
                "description": "Management Discussion & Analysis section missing"
            })
            return
        
        # Check for required disclosures
        required_topics = [
            "liquidity", "capital resources", "results of operations",
            "critical accounting", "market risk"
        ]
        
        missing_topics = []
        for topic in required_topics:
            if topic.lower() not in mda_text.lower():
                missing_topics.append(topic)
        
        if missing_topics:
            analysis.red_flags.append({
                "type": "incomplete_mda",
                "severity": "HIGH",
                "missing_topics": missing_topics,
                "regulation": "Item 303"
            })
        
        # Sentiment analysis (fraudulent MD&As show negative tone with complexity)
        sentiment_score = self._calculate_sentiment(mda_text)
        complexity_score = self._calculate_complexity(mda_text)
        
        # Japanese research: fraudulent AUC 0.907
        if sentiment_score < -0.3 and complexity_score > 0.7:
            analysis.red_flags.append({
                "type": "suspicious_mda_pattern",
                "severity": "HIGH",
                "sentiment": sentiment_score,
                "complexity": complexity_score,
                "pattern": "negative_complex"
            })
        
        # Check for missing uncertainty language
        uncertainty_terms = ["may", "might", "could", "uncertain", "risk", "potential"]
        uncertainty_count = sum(
            1 for term in uncertainty_terms 
            if term in mda_text.lower()
        )
        
        if uncertainty_count < 5 and analysis.delay_days > 0:
            analysis.red_flags.append({
                "type": "missing_uncertainty_language",
                "severity": "MEDIUM",
                "description": "Lack of cautionary language despite filing delays"
            })
        
        analysis.narrative_consistency = 1.0 - (len(missing_topics) / len(required_topics))
    
    async def _detect_accounting_fraud_patterns(self, analysis: FilingAnalysis, filing_data: Dict):
        """Detect known accounting fraud patterns."""
        # This is a placeholder for the method that was called but not defined
        # It would contain additional fraud detection logic
        pass
    
    def _calculate_deadline(
        self,
        period_end: datetime,
        filing_type: str,
        cik: str
    ) -> datetime:
        """Calculate SEC filing deadline based on filer status."""
        # Determine filer status (simplified - would need actual lookup)
        # Large accelerated: $700M+ float
        # Accelerated: $75M-$700M float
        # Non-accelerated: <$75M float
        
        if filing_type == "10-K":
            # Assuming accelerated filer for this example
            deadline_days = 75
        elif filing_type == "10-Q":
            deadline_days = 40
        elif filing_type == "8-K":
            deadline_days = 4
        else:
            deadline_days = 30
        
        return period_end + timedelta(days=deadline_days)
    
    def _calculate_fraud_risk(self, analysis: FilingAnalysis) -> float:
        """Calculate overall fraud risk score (0-1)."""
        risk_score = 0.0
        
        # Weight different factors
        weights = {
            "CRITICAL": 0.3,
            "HIGH": 0.2,
            "MEDIUM": 0.1,
            "LOW": 0.05
        }
        
        for red_flag in analysis.red_flags:
            severity = red_flag.get("severity", "LOW")
            risk_score += weights.get(severity, 0.05)
        
        # Add specific pattern bonuses
        if any(rf["type"] == "impossible_growth_ratio" for rf in analysis.red_flags):
            risk_score += 0.4  # WorldCom pattern
        
        if any(rf["type"] == "revenue_pull_forward" for rf in analysis.red_flags):
            risk_score += 0.3  # Marvell pattern
        
        if analysis.benford_analysis.get("suspicious", False):
            risk_score += 0.2
        
        # Normalize to 0-1
        return min(1.0, risk_score)
    
    def _generate_analysis_hash(self, analysis: FilingAnalysis) -> str:
        """Generate cryptographic hash of analysis for integrity."""
        analysis_dict = {
            "cik": analysis.cik,
            "filing_type": analysis.filing_type,
            "filing_date": analysis.filing_date.isoformat(),
            "red_flags": len(analysis.red_flags),
            "fraud_risk": analysis.fraud_indicators.get("overall_risk", 0),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        canonical = json.dumps(analysis_dict, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    # Helper methods
    def _extract_monthly_revenues(self, revenues: List) -> List[float]:
        """Extract monthly revenue data from filing."""
        # Implementation would parse XBRL or structured data
        return []
    
    def _calculate_dso(self, financial_data: Dict) -> Optional[float]:
        """Calculate Days Sales Outstanding."""
        ar = financial_data.get("accounts_receivable", 0)
        revenue = financial_data.get("revenue", 0)
        
        if revenue > 0:
            return (ar / revenue) * 365
        return None
    
    def _get_historical_dso(self, cik: str) -> Optional[float]:
        """Get historical DSO for comparison."""
        # Would fetch from database
        return None
    
    def _extract_all_numbers(self, data: Dict) -> List[float]:
        """Extract all numerical values from filing data."""
        numbers = []
        
        def extract_recursive(obj):
            if isinstance(obj, (int, float)):
                numbers.append(obj)
            elif isinstance(obj, dict):
                for value in obj.values():
                    extract_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)
        
        extract_recursive(data)
        return numbers
    
    async def _fetch_amendments(self, cik: str, accession: str) -> List[Dict]:
        """Fetch amendment history for filing."""
        # Implementation would query SEC API
        return []
    
    async def _fetch_related_filings(
        self,
        cik: str,
        period_end: datetime
    ) -> List[Dict]:
        """Fetch related filings for cross-reference."""
        # Implementation would query SEC API
        return []
    
    def _event_disclosed_in_10k(self, event: Dict, filing_data: Dict) -> bool:
        """Check if 8-K event is disclosed in 10-K."""
        # Implementation would search filing text
        return False
    
    def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score for text."""
        # Implementation would use NLP model
        return 0.0
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate complexity score for text."""
        # Fog index or similar readability metric
        return 0.0

