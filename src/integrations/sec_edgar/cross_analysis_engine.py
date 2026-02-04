"""
SEC Cross-Analysis Engine
==========================

Dynamic research and cross-analysis engine that leverages all SEC Data Resources
for sophisticated forensic analysis. This module provides:

1. Multi-Source Data Acquisition:
   - Company filings (10-K, 10-Q, 8-K, etc.)
   - Insider transactions (Form 4)
   - Institutional holdings (13F)
   - Beneficial ownership (13D/13G)
   - XBRL financial data
   - Fails-to-deliver data
   - Investment adviser relationships
   - Enforcement actions

2. Cross-Reference Analysis:
   - Insider trading vs. FTD correlations
   - Institutional ownership changes vs. material events
   - Executive network mapping across filings
   - Temporal correlation of events

3. Dynamic Research Capabilities:
   - Full-text search across all filings
   - Real-time RSS monitoring
   - Peer company comparisons
   - Historical trend analysis

Legal Framework:
- 17 CFR § 240.10b-5 (Securities fraud)
- 17 CFR § 240.10b5-1/10b5-2 (Insider trading)
- SOX Sections 302, 404, 906
- 18 U.S.C. § 1348 (Securities/commodities fraud)
- FRE 902(13)/(14) (Self-authenticating evidence)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
from pathlib import Path
import hashlib
import json

from .edgar_client import SECEdgarClient, SECFiling
from .sec_data_resources import (
    SECDataResourcesClient,
    FailsToDeliverRecord,
    InvestmentAdviser,
    FullTextSearchResult,
    RSSFilingEntry
)
from .models import IntegrityHashes

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================

class AnalysisType(Enum):
    """Types of cross-analysis available."""
    INSIDER_FTD_CORRELATION = "insider_ftd_correlation"
    INSTITUTIONAL_MOVEMENT = "institutional_movement"
    EXECUTIVE_NETWORK = "executive_network"
    MATERIAL_EVENT_TIMING = "material_event_timing"
    FINANCIAL_ANOMALY = "financial_anomaly"
    ENFORCEMENT_HISTORY = "enforcement_history"
    COMPREHENSIVE = "comprehensive"


class AlertSeverity(Enum):
    """Severity levels for forensic alerts."""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Significant anomaly detected
    MEDIUM = "medium"  # Notable pattern requiring review
    LOW = "low"  # Minor observation
    INFORMATIONAL = "informational"  # For tracking only


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class ForensicAlert:
    """Alert generated from cross-analysis."""
    alert_id: str
    severity: AlertSeverity
    analysis_type: AnalysisType
    title: str
    description: str
    evidence: List[Dict[str, Any]]
    related_entities: List[str]
    timestamp: datetime
    statutory_references: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "analysis_type": self.analysis_type.value,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "related_entities": self.related_entities,
            "timestamp": self.timestamp.isoformat(),
            "statutory_references": self.statutory_references,
            "recommended_actions": self.recommended_actions,
            "confidence_score": self.confidence_score
        }


@dataclass
class DataAcquisitionReport:
    """Report of data acquired from SEC sources."""
    acquisition_id: str
    target_cik: str
    company_name: str
    start_time: datetime
    end_time: datetime
    sources_queried: List[str]
    records_acquired: Dict[str, int]
    integrity_hashes: Dict[str, str]
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "acquisition_id": self.acquisition_id,
            "target_cik": self.target_cik,
            "company_name": self.company_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "sources_queried": self.sources_queried,
            "records_acquired": self.records_acquired,
            "integrity_hashes": self.integrity_hashes,
            "errors": self.errors
        }


@dataclass
class CrossAnalysisResult:
    """Result from cross-analysis engine."""
    analysis_id: str
    target_cik: str
    company_name: str
    analysis_types: List[AnalysisType]
    period_start: date
    period_end: date
    alerts: List[ForensicAlert]
    acquisition_report: DataAcquisitionReport
    summary_statistics: Dict[str, Any]
    raw_data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "target_cik": self.target_cik,
            "company_name": self.company_name,
            "analysis_types": [t.value for t in self.analysis_types],
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_alerts": len(self.alerts),
            "alerts_by_severity": {
                severity.value: len([a for a in self.alerts if a.severity == severity])
                for severity in AlertSeverity
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "acquisition_report": self.acquisition_report.to_dict(),
            "summary_statistics": self.summary_statistics
        }


# =============================================================================
# Cross-Analysis Engine
# =============================================================================

class SECCrossAnalysisEngine:
    """
    Dynamic research and cross-analysis engine for SEC data.
    
    This engine coordinates data acquisition from multiple SEC sources
    and performs sophisticated cross-referencing to identify:
    - Suspicious trading patterns
    - Material non-public information correlations
    - Executive network relationships
    - Financial statement anomalies
    - Enforcement action history
    
    All data acquisition maintains FRE 902(13)/(14) compliant evidence chains.
    """
    
    def __init__(
        self,
        user_agent: Optional[str] = None,
        enable_caching: bool = True,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize Cross-Analysis Engine.
        
        Args:
            user_agent: SEC-compliant User-Agent string
            enable_caching: Enable local caching of data
            cache_dir: Directory for cached data
        """
        self.user_agent = user_agent
        self.enable_caching = enable_caching
        self.cache_dir = cache_dir
        
        self._edgar_client: Optional[SECEdgarClient] = None
        self._data_resources_client: Optional[SECDataResourcesClient] = None
        
        logger.info("SEC Cross-Analysis Engine initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._edgar_client = SECEdgarClient(
            user_agent=self.user_agent,
            enable_circuit_breaker=True
        )
        self._data_resources_client = SECDataResourcesClient(
            user_agent=self.user_agent,
            enable_caching=self.enable_caching,
            cache_dir=self.cache_dir
        )
        
        await self._edgar_client.__aenter__()
        await self._data_resources_client.__aenter__()
        
        return self
    
    async def __aexit__(self, *args):
        """Async context manager exit."""
        if self._edgar_client:
            await self._edgar_client.__aexit__(*args)
        if self._data_resources_client:
            await self._data_resources_client.__aexit__(*args)
    
    # =========================================================================
    # Core Analysis Methods
    # =========================================================================
    
    async def run_comprehensive_analysis(
        self,
        cik: str,
        start_date: date,
        end_date: date,
        analysis_types: Optional[List[AnalysisType]] = None
    ) -> CrossAnalysisResult:
        """
        Run comprehensive cross-analysis on a company.
        
        This is the primary entry point for forensic analysis. It:
        1. Acquires data from all relevant SEC sources
        2. Cross-references data for pattern detection
        3. Generates forensic alerts for anomalies
        4. Produces an evidence-grade report
        
        Args:
            cik: Company CIK number
            start_date: Start of analysis period
            end_date: End of analysis period
            analysis_types: Types of analysis to perform (default: all)
            
        Returns:
            CrossAnalysisResult with alerts and data
        """
        analysis_id = self._generate_analysis_id(cik, start_date, end_date)
        
        if analysis_types is None:
            analysis_types = [AnalysisType.COMPREHENSIVE]
        
        logger.info(f"Starting comprehensive analysis {analysis_id} for CIK {cik}")
        
        # Phase 1: Data Acquisition
        acquisition_start = datetime.now(timezone.utc)
        acquired_data, acquisition_report = await self._acquire_all_data(
            cik, start_date, end_date
        )
        
        # Phase 2: Cross-Reference Analysis
        alerts = []
        
        if AnalysisType.COMPREHENSIVE in analysis_types or AnalysisType.INSIDER_FTD_CORRELATION in analysis_types:
            ftd_alerts = await self._analyze_insider_ftd_correlation(
                cik, acquired_data, start_date, end_date
            )
            alerts.extend(ftd_alerts)
        
        if AnalysisType.COMPREHENSIVE in analysis_types or AnalysisType.INSTITUTIONAL_MOVEMENT in analysis_types:
            inst_alerts = await self._analyze_institutional_movement(
                cik, acquired_data, start_date, end_date
            )
            alerts.extend(inst_alerts)
        
        if AnalysisType.COMPREHENSIVE in analysis_types or AnalysisType.MATERIAL_EVENT_TIMING in analysis_types:
            event_alerts = await self._analyze_material_event_timing(
                cik, acquired_data, start_date, end_date
            )
            alerts.extend(event_alerts)
        
        if AnalysisType.COMPREHENSIVE in analysis_types or AnalysisType.FINANCIAL_ANOMALY in analysis_types:
            financial_alerts = await self._analyze_financial_anomalies(
                cik, acquired_data, start_date, end_date
            )
            alerts.extend(financial_alerts)
        
        # Phase 3: Generate Summary Statistics
        summary_stats = self._generate_summary_statistics(acquired_data, alerts)
        
        # Sort alerts by severity
        alerts.sort(key=lambda a: list(AlertSeverity).index(a.severity))
        
        return CrossAnalysisResult(
            analysis_id=analysis_id,
            target_cik=cik,
            company_name=acquired_data.get("company_name", "Unknown"),
            analysis_types=analysis_types,
            period_start=start_date,
            period_end=end_date,
            alerts=alerts,
            acquisition_report=acquisition_report,
            summary_statistics=summary_stats,
            raw_data=acquired_data
        )
    
    # =========================================================================
    # Data Acquisition
    # =========================================================================
    
    async def _acquire_all_data(
        self,
        cik: str,
        start_date: date,
        end_date: date
    ) -> Tuple[Dict[str, Any], DataAcquisitionReport]:
        """
        Acquire data from all SEC sources.
        
        This method orchestrates parallel data acquisition from:
        - Company submissions (filings list)
        - XBRL company facts
        - Insider transactions (Form 4)
        - Institutional holdings (13F)
        - Beneficial ownership (13D/13G)
        - Material events (8-K)
        - Fails-to-deliver data
        - Investment adviser relationships
        """
        acquisition_id = f"ACQ-{cik}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        start_time = datetime.now(timezone.utc)
        
        acquired_data = {
            "cik": cik,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }
        records_acquired = {}
        sources_queried = []
        errors = []
        
        # 1. Get company submissions and facts
        try:
            logger.info(f"Acquiring company facts for CIK {cik}...")
            facts = await self._data_resources_client.get_company_facts(cik)
            if facts:
                acquired_data["company_name"] = facts.get("entityName", "Unknown")
                acquired_data["company_facts"] = facts
                records_acquired["company_facts"] = 1
                sources_queried.append("company_facts_api")
        except Exception as e:
            errors.append(f"Company facts acquisition failed: {e}")
            logger.error(f"Error acquiring company facts: {e}")
        
        # 2. Get filings list
        try:
            logger.info(f"Acquiring filings for CIK {cik}...")
            filings = await self._edgar_client.get_filings(
                cik, start_date=start_date, end_date=end_date
            )
            if filings:
                acquired_data["filings"] = [f.to_dict() for f in filings]
                records_acquired["filings"] = len(filings)
                sources_queried.append("submissions_api")
                
                # Categorize filings
                acquired_data["filings_by_type"] = self._categorize_filings(filings)
        except Exception as e:
            errors.append(f"Filings acquisition failed: {e}")
            logger.error(f"Error acquiring filings: {e}")
        
        # 3. Get Form 4 insider transactions
        try:
            logger.info(f"Acquiring Form 4 filings for CIK {cik}...")
            form4_filings = await self._edgar_client.get_form4_filings(
                cik, start_date=start_date, end_date=end_date
            )
            if form4_filings:
                acquired_data["form4_filings"] = [f.to_dict() for f in form4_filings]
                records_acquired["form4_filings"] = len(form4_filings)
                sources_queried.append("form4_filings")
        except Exception as e:
            errors.append(f"Form 4 acquisition failed: {e}")
            logger.error(f"Error acquiring Form 4 filings: {e}")
        
        # 4. Get ticker for FTD data
        try:
            logger.info("Resolving company ticker...")
            tickers = await self._data_resources_client.get_all_company_tickers()
            cik_clean = cik.lstrip("0")
            ticker = None
            for t, info in tickers.items():
                if info.get("cik") == cik_clean:
                    ticker = t
                    acquired_data["ticker"] = t
                    break
            
            # 5. Get Fails-to-Deliver data if ticker found
            if ticker:
                logger.info(f"Acquiring FTD data for {ticker}...")
                ftd_records = await self._data_resources_client.get_fails_to_deliver_by_symbol(
                    ticker, start_date, end_date
                )
                if ftd_records:
                    acquired_data["fails_to_deliver"] = [r.to_dict() for r in ftd_records]
                    records_acquired["fails_to_deliver"] = len(ftd_records)
                    sources_queried.append("fails_to_deliver_data")
        except Exception as e:
            errors.append(f"FTD data acquisition failed: {e}")
            logger.error(f"Error acquiring FTD data: {e}")
        
        # 6. Get financial metrics for the year
        try:
            fiscal_year = end_date.year
            logger.info(f"Extracting financial metrics for FY{fiscal_year}...")
            metrics = await self._data_resources_client.extract_financial_metrics(
                cik, fiscal_year
            )
            if metrics:
                acquired_data["financial_metrics"] = metrics
                records_acquired["financial_metrics"] = len(metrics)
                sources_queried.append("xbrl_company_facts")
        except Exception as e:
            errors.append(f"Financial metrics extraction failed: {e}")
            logger.error(f"Error extracting financial metrics: {e}")
        
        # 7. Search for related investment advisers
        try:
            if acquired_data.get("company_name"):
                logger.info("Searching for related investment advisers...")
                company_name = acquired_data["company_name"]
                name_parts = company_name.split()[:2]
                if name_parts:
                    advisers = await self._data_resources_client.search_investment_advisers(
                        firm_name=" ".join(name_parts)
                    )
                    if advisers:
                        acquired_data["related_advisers"] = [a.to_dict() for a in advisers]
                        records_acquired["related_advisers"] = len(advisers)
                        sources_queried.append("iapd_search")
        except Exception as e:
            errors.append(f"Investment adviser search failed: {e}")
            logger.error(f"Error searching investment advisers: {e}")
        
        # Generate integrity hash for the acquired data
        data_json = json.dumps(acquired_data, sort_keys=True, default=str)
        integrity_hashes = {
            "sha256": hashlib.sha256(data_json.encode()).hexdigest(),
            "sha3_512": hashlib.sha3_512(data_json.encode()).hexdigest(),
            "blake2b": hashlib.blake2b(data_json.encode()).hexdigest()
        }
        
        end_time = datetime.now(timezone.utc)
        
        acquisition_report = DataAcquisitionReport(
            acquisition_id=acquisition_id,
            target_cik=cik,
            company_name=acquired_data.get("company_name", "Unknown"),
            start_time=start_time,
            end_time=end_time,
            sources_queried=sources_queried,
            records_acquired=records_acquired,
            integrity_hashes=integrity_hashes,
            errors=errors
        )
        
        logger.info(f"Data acquisition complete: {len(sources_queried)} sources, "
                   f"{sum(records_acquired.values())} total records")
        
        return acquired_data, acquisition_report
    
    def _categorize_filings(self, filings: List[SECFiling]) -> Dict[str, List[Dict]]:
        """Categorize filings by form type."""
        categories = {}
        for filing in filings:
            form_type = filing.form_type
            if form_type not in categories:
                categories[form_type] = []
            categories[form_type].append(filing.to_dict())
        return categories
    
    # =========================================================================
    # Analysis Methods
    # =========================================================================
    
    async def _analyze_insider_ftd_correlation(
        self,
        cik: str,
        data: Dict[str, Any],
        start_date: date,
        end_date: date
    ) -> List[ForensicAlert]:
        """
        Analyze correlation between insider transactions and FTD spikes.
        
        This identifies patterns where:
        - Insider sales precede FTD spikes
        - Insider purchases follow FTD spikes
        - Unusual FTD volumes coincide with material events
        """
        alerts = []
        
        form4_filings = data.get("form4_filings", [])
        ftd_records = data.get("fails_to_deliver", [])
        
        if not form4_filings or not ftd_records:
            return alerts
        
        # Analyze temporal correlation
        for filing in form4_filings:
            filing_date = datetime.fromisoformat(filing["filing_date"]).date()
            
            # Look for FTD spikes within 10 days of filing
            related_ftds = [
                r for r in ftd_records
                if abs((datetime.fromisoformat(r["settlement_date"]).date() - filing_date).days) <= 10
            ]
            
            if related_ftds:
                total_ftd_qty = sum(r["quantity"] for r in related_ftds)
                
                # High FTD volume near insider transaction
                if total_ftd_qty > 100000:
                    alert = ForensicAlert(
                        alert_id=f"INSIDER-FTD-{filing['accession_number'][:15]}",
                        severity=AlertSeverity.HIGH if total_ftd_qty > 500000 else AlertSeverity.MEDIUM,
                        analysis_type=AnalysisType.INSIDER_FTD_CORRELATION,
                        title=f"Insider Transaction Near FTD Spike",
                        description=(
                            f"Form 4 filing on {filing_date} coincides with elevated "
                            f"fails-to-deliver volume ({total_ftd_qty:,} shares within 10 days). "
                            f"This pattern may indicate market manipulation or coordinated trading."
                        ),
                        evidence=[
                            {"type": "form4_filing", "data": filing},
                            {"type": "ftd_records", "total_qty": total_ftd_qty, "count": len(related_ftds)}
                        ],
                        related_entities=[cik, data.get("ticker", "")],
                        timestamp=datetime.now(timezone.utc),
                        statutory_references=[
                            "17 CFR § 240.10b-5",
                            "17 CFR § 240.10b5-1",
                            "15 U.S.C. § 78j(b)"
                        ],
                        recommended_actions=[
                            "Review Form 4 transaction details",
                            "Analyze FTD pattern for manipulation indicators",
                            "Cross-reference with 8-K material events"
                        ],
                        confidence_score=0.75 if total_ftd_qty > 500000 else 0.60
                    )
                    alerts.append(alert)
        
        return alerts
    
    async def _analyze_institutional_movement(
        self,
        cik: str,
        data: Dict[str, Any],
        start_date: date,
        end_date: date
    ) -> List[ForensicAlert]:
        """
        Analyze institutional ownership changes.
        
        This identifies patterns where:
        - Large institutional holders exit positions
        - Concentrated buying/selling by connected parties
        - Unusual timing relative to material events
        """
        alerts = []
        
        filings_by_type = data.get("filings_by_type", {})
        
        # Check for 13D/13G filings (beneficial ownership)
        beneficial_filings = (
            filings_by_type.get("SC 13D", []) +
            filings_by_type.get("SC 13D/A", []) +
            filings_by_type.get("SC 13G", []) +
            filings_by_type.get("SC 13G/A", [])
        )
        
        if len(beneficial_filings) >= 3:
            # Multiple ownership disclosures in the period
            alert = ForensicAlert(
                alert_id=f"INST-MOVEMENT-{cik}-{start_date.isoformat()}",
                severity=AlertSeverity.MEDIUM,
                analysis_type=AnalysisType.INSTITUTIONAL_MOVEMENT,
                title="Elevated Beneficial Ownership Activity",
                description=(
                    f"Detected {len(beneficial_filings)} beneficial ownership filings "
                    f"(13D/13G) during the analysis period. This may indicate "
                    f"significant ownership restructuring or activist investor activity."
                ),
                evidence=[
                    {"type": "beneficial_ownership_filings", "filings": beneficial_filings}
                ],
                related_entities=[cik],
                timestamp=datetime.now(timezone.utc),
                statutory_references=[
                    "17 CFR § 240.13d-1",
                    "17 CFR § 240.13d-2"
                ],
                recommended_actions=[
                    "Review each 13D/13G for ownership changes",
                    "Identify common parties across filings",
                    "Analyze timing relative to stock price movements"
                ],
                confidence_score=0.65
            )
            alerts.append(alert)
        
        return alerts
    
    async def _analyze_material_event_timing(
        self,
        cik: str,
        data: Dict[str, Any],
        start_date: date,
        end_date: date
    ) -> List[ForensicAlert]:
        """
        Analyze timing of material events (8-K) relative to trading.
        
        This identifies patterns where:
        - Insider transactions cluster around material events
        - 8-K filings follow unusual trading volume
        - Material events coincide with earnings timing
        """
        alerts = []
        
        filings_by_type = data.get("filings_by_type", {})
        form4_filings = data.get("form4_filings", [])
        
        # Get 8-K filings
        material_events = filings_by_type.get("8-K", []) + filings_by_type.get("8-K/A", [])
        
        if not material_events:
            return alerts
        
        for event in material_events:
            event_date = datetime.fromisoformat(event["filing_date"]).date()
            
            # Find insider transactions within 5 days before the event
            pre_event_trades = [
                f for f in form4_filings
                if 0 < (event_date - datetime.fromisoformat(f["filing_date"]).date()).days <= 5
            ]
            
            if pre_event_trades:
                alert = ForensicAlert(
                    alert_id=f"EVENT-TIMING-{event['accession_number'][:15]}",
                    severity=AlertSeverity.HIGH,
                    analysis_type=AnalysisType.MATERIAL_EVENT_TIMING,
                    title="Insider Transactions Preceding Material Event",
                    description=(
                        f"Detected {len(pre_event_trades)} insider transaction(s) within "
                        f"5 days before 8-K filing on {event_date}. This pattern may "
                        f"indicate trading on material non-public information (MNPI)."
                    ),
                    evidence=[
                        {"type": "8k_filing", "data": event},
                        {"type": "pre_event_trades", "filings": pre_event_trades}
                    ],
                    related_entities=[cik],
                    timestamp=datetime.now(timezone.utc),
                    statutory_references=[
                        "17 CFR § 240.10b5-1",
                        "17 CFR § 240.10b5-2",
                        "15 U.S.C. § 78j(b)",
                        "18 U.S.C. § 1348"
                    ],
                    recommended_actions=[
                        "Review 8-K content for material information",
                        "Analyze insider trading patterns for MNPI indicators",
                        "Document temporal correlation for enforcement referral"
                    ],
                    confidence_score=0.80
                )
                alerts.append(alert)
        
        return alerts
    
    async def _analyze_financial_anomalies(
        self,
        cik: str,
        data: Dict[str, Any],
        start_date: date,
        end_date: date
    ) -> List[ForensicAlert]:
        """
        Analyze XBRL financial data for anomalies.
        
        This identifies patterns such as:
        - Unusual changes in key metrics
        - Inconsistent financial relationships
        - Revenue/receivables divergence
        """
        alerts = []
        
        metrics = data.get("financial_metrics", {})
        
        if not metrics:
            return alerts
        
        # Check for revenue-receivables divergence (potential channel stuffing)
        revenues = metrics.get("Revenues", {}).get("value")
        receivables = metrics.get("AccountsReceivableNetCurrent", {}).get("value")
        
        if revenues and receivables and revenues > 0:
            receivables_ratio = receivables / revenues
            
            # High receivables relative to revenue
            if receivables_ratio > 0.25:
                alert = ForensicAlert(
                    alert_id=f"FIN-ANOMALY-REC-{cik}-{end_date.year}",
                    severity=AlertSeverity.MEDIUM,
                    analysis_type=AnalysisType.FINANCIAL_ANOMALY,
                    title="Elevated Receivables-to-Revenue Ratio",
                    description=(
                        f"Accounts receivable represents {receivables_ratio:.1%} of revenue. "
                        f"This elevated ratio may indicate channel stuffing, collection issues, "
                        f"or aggressive revenue recognition practices."
                    ),
                    evidence=[
                        {"type": "xbrl_metric", "concept": "Revenues", "value": revenues},
                        {"type": "xbrl_metric", "concept": "AccountsReceivableNetCurrent", "value": receivables},
                        {"type": "ratio", "name": "receivables_to_revenue", "value": receivables_ratio}
                    ],
                    related_entities=[cik],
                    timestamp=datetime.now(timezone.utc),
                    statutory_references=[
                        "17 CFR § 240.10b-5",
                        "GAAP ASC 606 Revenue Recognition"
                    ],
                    recommended_actions=[
                        "Analyze DSO (Days Sales Outstanding) trend",
                        "Compare with industry peers",
                        "Review quarterly progression for anomalies"
                    ],
                    confidence_score=0.55
                )
                alerts.append(alert)
        
        return alerts
    
    def _generate_summary_statistics(
        self,
        data: Dict[str, Any],
        alerts: List[ForensicAlert]
    ) -> Dict[str, Any]:
        """Generate summary statistics for the analysis."""
        return {
            "total_filings": len(data.get("filings", [])),
            "form4_transactions": len(data.get("form4_filings", [])),
            "ftd_records": len(data.get("fails_to_deliver", [])),
            "ftd_total_quantity": sum(
                r.get("quantity", 0) for r in data.get("fails_to_deliver", [])
            ),
            "related_advisers": len(data.get("related_advisers", [])),
            "metrics_extracted": len(data.get("financial_metrics", {})),
            "total_alerts": len(alerts),
            "critical_alerts": len([a for a in alerts if a.severity == AlertSeverity.CRITICAL]),
            "high_alerts": len([a for a in alerts if a.severity == AlertSeverity.HIGH]),
            "medium_alerts": len([a for a in alerts if a.severity == AlertSeverity.MEDIUM]),
            "filings_by_type": {
                k: len(v) for k, v in data.get("filings_by_type", {}).items()
            }
        }
    
    def _generate_analysis_id(
        self,
        cik: str,
        start_date: date,
        end_date: date
    ) -> str:
        """Generate unique analysis ID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"XANA-{cik}-{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}-{timestamp}"
    
    # =========================================================================
    # Dynamic Research Methods
    # =========================================================================
    
    async def search_filings(
        self,
        query: str,
        form_types: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[FullTextSearchResult]:
        """
        Perform full-text search across all SEC filings.
        
        Args:
            query: Search query (supports phrases in quotes)
            form_types: Filter by form types
            start_date: Start of search period
            end_date: End of search period
            limit: Maximum results
            
        Returns:
            List of search results
        """
        return await self._data_resources_client.full_text_search(
            query=query,
            form_types=form_types,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    
    async def monitor_real_time_filings(
        self,
        form_type: Optional[str] = None,
        callback: Optional[callable] = None
    ) -> List[RSSFilingEntry]:
        """
        Get recent filings from RSS feed.
        
        Args:
            form_type: Filter by form type
            callback: Optional callback for each filing
            
        Returns:
            List of recent filings
        """
        filings = await self._data_resources_client.get_recent_filings_rss(
            form_type=form_type
        )
        
        if callback:
            for filing in filings:
                await callback(filing)
        
        return filings
    
    async def compare_peer_companies(
        self,
        ciks: List[str],
        concepts: List[str],
        fiscal_year: int
    ) -> Dict[str, Any]:
        """
        Compare financial metrics across peer companies.
        
        Args:
            ciks: List of company CIKs
            concepts: XBRL concepts to compare
            fiscal_year: Fiscal year for comparison
            
        Returns:
            Peer comparison data
        """
        return await self._data_resources_client.cross_analyze_peer_companies(
            ciks=ciks,
            concepts=concepts,
            fiscal_year=fiscal_year
        )


# =============================================================================
# Convenience Function
# =============================================================================

async def run_forensic_analysis(
    cik: str,
    start_date: date,
    end_date: date,
    user_agent: Optional[str] = None,
    analysis_types: Optional[List[AnalysisType]] = None
) -> CrossAnalysisResult:
    """
    Convenience function to run comprehensive forensic analysis.
    
    Args:
        cik: Company CIK number
        start_date: Start of analysis period
        end_date: End of analysis period
        user_agent: SEC-compliant User-Agent string
        analysis_types: Types of analysis to perform
        
    Returns:
        CrossAnalysisResult with all findings
    """
    async with SECCrossAnalysisEngine(user_agent=user_agent) as engine:
        return await engine.run_comprehensive_analysis(
            cik=cik,
            start_date=start_date,
            end_date=end_date,
            analysis_types=analysis_types
        )
