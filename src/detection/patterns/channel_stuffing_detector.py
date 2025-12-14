"""
Channel Stuffing Detector
=========================

Implements revenue manipulation detection through channel stuffing patterns.

Channel stuffing involves artificially inflating revenue by pushing excess
inventory to distributors/retailers near quarter end, often with favorable
terms or side agreements.

Detection Capabilities:
- Quarter-end revenue concentration exceeding 40% (hockey stick pattern)
- Days Sales Outstanding (DSO) acceleration vs prior periods
- Accounts receivable growth significantly exceeding revenue growth
- Customer concentration shifts in segment disclosures
- Return rate spikes in subsequent quarters (1-2 quarters post-stuffing)
- Credit term extensions near quarter end
- Bill-and-hold arrangement indicators

Thresholds:
- Quarter-end concentration: 40% of quarterly revenue in final month
- DSO change: greater than 15% increase quarter-over-quarter
- AR/Revenue divergence: AR growth exceeds Revenue growth by more than 10%
- Return rate spike: greater than 2x normal return rate

Integration: Connects with Node 3 (10-Q) for quarterly financial data
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import hashlib
import logging
import math

logger = logging.getLogger(__name__)


class StuffingSeverity(Enum):
    """Severity level for channel stuffing detection."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class QuarterlyMetrics:
    """Financial metrics for a single quarter."""
    quarter: str  # e.g., "Q1 2023"
    year: int
    quarter_num: int
    
    # Revenue metrics
    total_revenue: float
    last_month_revenue: float
    quarter_end_concentration: float  # Percentage
    
    # Receivables metrics
    accounts_receivable: float
    days_sales_outstanding: float
    dso_change_pct: Optional[float]  # vs prior quarter
    
    # Growth metrics
    revenue_growth_pct: float  # vs prior quarter
    ar_growth_pct: float  # vs prior quarter
    ar_revenue_divergence: float  # AR growth - Revenue growth
    
    # Quality indicators
    return_rate: Optional[float]  # Product return rate
    allowance_for_doubtful_accounts: Optional[float]
    credit_terms_days: Optional[int]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "quarter": self.quarter,
            "year": self.year,
            "quarter_num": self.quarter_num,
            "revenue": {
                "total": round(self.total_revenue, 2),
                "last_month": round(self.last_month_revenue, 2),
                "end_concentration_pct": round(self.quarter_end_concentration, 2)
            },
            "receivables": {
                "accounts_receivable": round(self.accounts_receivable, 2),
                "dso": round(self.days_sales_outstanding, 2),
                "dso_change_pct": round(self.dso_change_pct, 2) if self.dso_change_pct else None
            },
            "growth": {
                "revenue_growth_pct": round(self.revenue_growth_pct, 2),
                "ar_growth_pct": round(self.ar_growth_pct, 2),
                "divergence": round(self.ar_revenue_divergence, 2)
            },
            "quality": {
                "return_rate": round(self.return_rate, 4) if self.return_rate else None,
                "credit_terms_days": self.credit_terms_days
            }
        }


@dataclass
class StuffingIndicator:
    """Individual channel stuffing indicator."""
    indicator_name: str
    detected: bool
    severity: str
    value: float
    threshold: float
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.indicator_name,
            "detected": self.detected,
            "severity": self.severity,
            "value": round(self.value, 4),
            "threshold": round(self.threshold, 4),
            "description": self.description
        }


@dataclass
class ChannelStuffingAlert:
    """Alert for detected channel stuffing pattern."""
    alert_id: str
    company_cik: str
    company_name: str
    detection_date: datetime
    severity: StuffingSeverity
    
    # Analysis period
    quarters_analyzed: List[QuarterlyMetrics]
    suspicious_quarters: List[str]
    
    # Detected indicators
    indicators: List[StuffingIndicator]
    red_flags_count: int
    
    # Risk assessment
    manipulation_probability: float
    
    # Evidence and recommendations
    evidence_summary: str
    regulatory_implications: List[str]
    recommended_actions: List[str]
    evidence_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "company": {
                "cik": self.company_cik,
                "name": self.company_name
            },
            "detection_date": self.detection_date.isoformat(),
            "severity": self.severity.value,
            "analysis": {
                "quarters_analyzed": len(self.quarters_analyzed),
                "suspicious_quarters": self.suspicious_quarters,
                "red_flags_count": self.red_flags_count
            },
            "indicators": [i.to_dict() for i in self.indicators],
            "manipulation_probability": round(self.manipulation_probability, 3),
            "evidence_summary": self.evidence_summary,
            "regulatory_implications": self.regulatory_implications,
            "recommended_actions": self.recommended_actions,
            "evidence_hash": self.evidence_hash
        }


class ChannelStuffingDetector:
    """
    Detector for channel stuffing revenue manipulation.
    
    Analyzes quarterly financial data to identify patterns consistent
    with artificially inflating revenue through channel stuffing.
    """
    
    # Detection thresholds
    QUARTER_END_CONCENTRATION_THRESHOLD = 0.40  # 40% of revenue in last month
    DSO_INCREASE_THRESHOLD = 0.15  # 15% increase QoQ
    AR_REVENUE_DIVERGENCE_THRESHOLD = 0.10  # 10 percentage points
    RETURN_RATE_SPIKE_MULTIPLIER = 2.0  # 2x normal rate
    
    def __init__(self, mock_mode: bool = False):
        """
        Initialize the detector.
        
        Args:
            mock_mode: If True, use mock data for testing without external dependencies
        """
        self.mock_mode = mock_mode
        self.alerts = []
    
    def analyze_quarters(
        self,
        company_cik: str,
        company_name: str,
        quarterly_data: List[Dict[str, Any]]
    ) -> ChannelStuffingAlert:
        """
        Analyze quarterly financial data for channel stuffing patterns.
        
        Args:
            company_cik: SEC CIK number
            company_name: Company name
            quarterly_data: List of quarterly financial records from 10-Q filings
            
        Returns:
            ChannelStuffingAlert with detection results
        """
        if self.mock_mode:
            return self._generate_mock_alert(company_cik, company_name, len(quarterly_data))
        
        # Parse and compute metrics for each quarter
        quarterly_metrics = []
        for i, quarter_data in enumerate(quarterly_data):
            try:
                metrics = self._compute_quarterly_metrics(quarter_data, quarterly_data[i-1] if i > 0 else None)
                quarterly_metrics.append(metrics)
            except Exception as e:
                logger.warning(f"Failed to compute metrics for quarter: {e}")
                continue
        
        # Detect stuffing indicators for each quarter
        all_indicators = []
        suspicious_quarters = []
        
        for metrics in quarterly_metrics:
            indicators = self._detect_indicators(metrics, quarterly_metrics)
            all_indicators.extend(indicators)
            
            # Flag quarter as suspicious if multiple indicators present
            quarter_red_flags = sum(1 for ind in indicators if ind.detected)
            if quarter_red_flags >= 2:
                suspicious_quarters.append(metrics.quarter)
        
        # Count total red flags
        red_flags_count = sum(1 for ind in all_indicators if ind.detected)
        
        # Calculate manipulation probability
        manipulation_probability = self._calculate_manipulation_probability(
            all_indicators,
            len(suspicious_quarters),
            len(quarterly_metrics)
        )
        
        # Determine severity
        severity = self._determine_severity(red_flags_count, len(suspicious_quarters), len(quarterly_metrics))
        
        # Generate evidence summary
        evidence_summary = self._generate_evidence_summary(quarterly_metrics, all_indicators, suspicious_quarters)
        
        # Generate alert
        alert = ChannelStuffingAlert(
            alert_id=self._generate_alert_id(company_cik),
            company_cik=company_cik,
            company_name=company_name,
            detection_date=datetime.utcnow(),
            severity=severity,
            quarters_analyzed=quarterly_metrics,
            suspicious_quarters=suspicious_quarters,
            indicators=all_indicators,
            red_flags_count=red_flags_count,
            manipulation_probability=manipulation_probability,
            evidence_summary=evidence_summary,
            regulatory_implications=self._get_regulatory_implications(severity),
            recommended_actions=self._get_recommended_actions(severity),
            evidence_hash=self._compute_evidence_hash(quarterly_metrics)
        )
        
        self.alerts.append(alert)
        return alert
    
    def _compute_quarterly_metrics(
        self,
        quarter_data: Dict[str, Any],
        prior_quarter_data: Optional[Dict[str, Any]]
    ) -> QuarterlyMetrics:
        """Compute financial metrics for a single quarter."""
        # Extract basic info
        quarter = quarter_data['quarter']
        year = quarter_data['year']
        quarter_num = quarter_data['quarter_num']
        
        # Revenue metrics
        total_revenue = quarter_data['revenue']
        last_month_revenue = quarter_data.get('last_month_revenue', total_revenue / 3)
        quarter_end_concentration = (last_month_revenue / total_revenue) if total_revenue > 0 else 0
        
        # Receivables metrics
        accounts_receivable = quarter_data['accounts_receivable']
        
        # Calculate DSO: (AR / Revenue) * 90 days
        days_sales_outstanding = (accounts_receivable / total_revenue * 90) if total_revenue > 0 else 0
        
        # Calculate changes vs prior quarter
        dso_change_pct = None
        revenue_growth_pct = 0.0
        ar_growth_pct = 0.0
        
        if prior_quarter_data:
            prior_revenue = prior_quarter_data['revenue']
            prior_ar = prior_quarter_data['accounts_receivable']
            prior_dso = (prior_ar / prior_revenue * 90) if prior_revenue > 0 else 0
            
            if prior_dso > 0:
                dso_change_pct = (days_sales_outstanding - prior_dso) / prior_dso
            
            if prior_revenue > 0:
                revenue_growth_pct = (total_revenue - prior_revenue) / prior_revenue
            
            if prior_ar > 0:
                ar_growth_pct = (accounts_receivable - prior_ar) / prior_ar
        
        ar_revenue_divergence = ar_growth_pct - revenue_growth_pct
        
        # Quality indicators
        return_rate = quarter_data.get('return_rate')
        allowance_for_doubtful_accounts = quarter_data.get('allowance_doubtful')
        credit_terms_days = quarter_data.get('credit_terms_days')
        
        return QuarterlyMetrics(
            quarter=quarter,
            year=year,
            quarter_num=quarter_num,
            total_revenue=total_revenue,
            last_month_revenue=last_month_revenue,
            quarter_end_concentration=quarter_end_concentration,
            accounts_receivable=accounts_receivable,
            days_sales_outstanding=days_sales_outstanding,
            dso_change_pct=dso_change_pct,
            revenue_growth_pct=revenue_growth_pct,
            ar_growth_pct=ar_growth_pct,
            ar_revenue_divergence=ar_revenue_divergence,
            return_rate=return_rate,
            allowance_for_doubtful_accounts=allowance_for_doubtful_accounts,
            credit_terms_days=credit_terms_days
        )
    
    def _detect_indicators(
        self,
        metrics: QuarterlyMetrics,
        all_quarters: List[QuarterlyMetrics]
    ) -> List[StuffingIndicator]:
        """Detect channel stuffing indicators for a quarter."""
        indicators = []
        
        # Indicator 1: Quarter-end revenue concentration (hockey stick)
        hockey_stick_detected = metrics.quarter_end_concentration > self.QUARTER_END_CONCENTRATION_THRESHOLD
        indicators.append(StuffingIndicator(
            indicator_name="Quarter-End Revenue Concentration",
            detected=hockey_stick_detected,
            severity="HIGH" if hockey_stick_detected else "LOW",
            value=metrics.quarter_end_concentration,
            threshold=self.QUARTER_END_CONCENTRATION_THRESHOLD,
            description=f"{metrics.quarter_end_concentration*100:.1f}% of quarterly revenue "
                       f"recognized in final month (threshold: {self.QUARTER_END_CONCENTRATION_THRESHOLD*100:.0f}%)"
        ))
        
        # Indicator 2: DSO acceleration
        if metrics.dso_change_pct is not None:
            dso_spike_detected = metrics.dso_change_pct > self.DSO_INCREASE_THRESHOLD
            indicators.append(StuffingIndicator(
                indicator_name="DSO Acceleration",
                detected=dso_spike_detected,
                severity="HIGH" if dso_spike_detected else "LOW",
                value=metrics.dso_change_pct,
                threshold=self.DSO_INCREASE_THRESHOLD,
                description=f"Days Sales Outstanding increased {metrics.dso_change_pct*100:.1f}% QoQ "
                           f"(threshold: {self.DSO_INCREASE_THRESHOLD*100:.0f}%)"
            ))
        
        # Indicator 3: AR/Revenue divergence
        divergence_detected = metrics.ar_revenue_divergence > self.AR_REVENUE_DIVERGENCE_THRESHOLD
        indicators.append(StuffingIndicator(
            indicator_name="AR/Revenue Growth Divergence",
            detected=divergence_detected,
            severity="CRITICAL" if divergence_detected else "LOW",
            value=metrics.ar_revenue_divergence,
            threshold=self.AR_REVENUE_DIVERGENCE_THRESHOLD,
            description=f"Accounts Receivable growing {metrics.ar_revenue_divergence*100:.1f} percentage points "
                       f"faster than Revenue (threshold: {self.AR_REVENUE_DIVERGENCE_THRESHOLD*100:.0f} pp)"
        ))
        
        # Indicator 4: Return rate spike (check subsequent quarters)
        if metrics.return_rate is not None:
            # Find this quarter's index
            quarter_idx = next((i for i, q in enumerate(all_quarters) if q.quarter == metrics.quarter), -1)
            
            if quarter_idx >= 0 and quarter_idx < len(all_quarters) - 2:
                # Check if return rate spiked in next 1-2 quarters
                baseline_return_rate = metrics.return_rate
                future_quarters = all_quarters[quarter_idx+1:quarter_idx+3]
                
                max_future_return_rate = max(
                    (q.return_rate for q in future_quarters if q.return_rate is not None),
                    default=0
                )
                
                return_spike_detected = (
                    baseline_return_rate > 0 and
                    max_future_return_rate > baseline_return_rate * self.RETURN_RATE_SPIKE_MULTIPLIER
                )
                
                indicators.append(StuffingIndicator(
                    indicator_name="Subsequent Return Rate Spike",
                    detected=return_spike_detected,
                    severity="CRITICAL" if return_spike_detected else "LOW",
                    value=max_future_return_rate / baseline_return_rate if baseline_return_rate > 0 else 0,
                    threshold=self.RETURN_RATE_SPIKE_MULTIPLIER,
                    description=f"Product return rate increased {max_future_return_rate/baseline_return_rate:.1f}x "
                               f"in subsequent quarters (threshold: {self.RETURN_RATE_SPIKE_MULTIPLIER:.1f}x)"
                ))
        
        return indicators
    
    def _calculate_manipulation_probability(
        self,
        indicators: List[StuffingIndicator],
        suspicious_quarters_count: int,
        total_quarters: int
    ) -> float:
        """Calculate probability of channel stuffing manipulation."""
        if not indicators:
            return 0.0
        
        # Weight critical indicators more heavily
        critical_count = sum(1 for ind in indicators if ind.detected and ind.severity == "CRITICAL")
        high_count = sum(1 for ind in indicators if ind.detected and ind.severity == "HIGH")
        
        # Base score from indicator detections
        indicator_score = (critical_count * 0.30 + high_count * 0.15)
        
        # Adjust for pattern persistence across quarters
        if total_quarters > 0:
            persistence_score = (suspicious_quarters_count / total_quarters) * 0.25
        else:
            persistence_score = 0
        
        total_score = indicator_score + persistence_score
        
        return min(total_score, 1.0)
    
    def _determine_severity(
        self,
        red_flags_count: int,
        suspicious_quarters: int,
        total_quarters: int
    ) -> StuffingSeverity:
        """Determine alert severity based on findings."""
        if total_quarters == 0:
            return StuffingSeverity.LOW
        
        # Calculate suspicious quarter ratio
        suspicious_ratio = suspicious_quarters / total_quarters
        
        # Critical: Many red flags or persistent pattern
        if red_flags_count >= 6 or suspicious_ratio >= 0.75:
            return StuffingSeverity.CRITICAL
        
        # High: Multiple red flags or frequent pattern
        if red_flags_count >= 4 or suspicious_ratio >= 0.50:
            return StuffingSeverity.HIGH
        
        # Medium: Some red flags
        if red_flags_count >= 2 or suspicious_ratio >= 0.25:
            return StuffingSeverity.MEDIUM
        
        return StuffingSeverity.LOW
    
    def _generate_evidence_summary(
        self,
        quarters: List[QuarterlyMetrics],
        indicators: List[StuffingIndicator],
        suspicious_quarters: List[str]
    ) -> str:
        """Generate human-readable evidence summary."""
        if not quarters:
            return "No quarterly data analyzed."
        
        summary_parts = [
            f"Analyzed {len(quarters)} quarters of financial data.",
            f"Identified {len(suspicious_quarters)} quarters with channel stuffing indicators.",
        ]
        
        # Summarize detected indicators
        detected = [ind for ind in indicators if ind.detected]
        if detected:
            summary_parts.append(f"Detected {len(detected)} red flags:")
            
            # Group by type
            indicator_types = {}
            for ind in detected:
                if ind.indicator_name not in indicator_types:
                    indicator_types[ind.indicator_name] = 0
                indicator_types[ind.indicator_name] += 1
            
            for name, count in indicator_types.items():
                summary_parts.append(f"  - {name}: {count} occurrence(s)")
        
        if suspicious_quarters:
            summary_parts.append(f"Suspicious quarters: {', '.join(suspicious_quarters)}")
        
        return " ".join(summary_parts)
    
    def _get_regulatory_implications(self, severity: StuffingSeverity) -> List[str]:
        """Get regulatory implications based on findings."""
        implications = []
        
        if severity in [StuffingSeverity.MEDIUM, StuffingSeverity.HIGH, StuffingSeverity.CRITICAL]:
            implications.extend([
                "Potential revenue recognition violations under ASC 606",
                "Possible securities fraud under Section 10(b) of Securities Exchange Act",
                "Financial statement misstatement concerns"
            ])
        
        if severity in [StuffingSeverity.HIGH, StuffingSeverity.CRITICAL]:
            implications.extend([
                "Recommended for SEC Division of Enforcement review",
                "Potential violations of SOX Section 302 (CEO/CFO certifications)",
                "Audit committee investigation recommended"
            ])
        
        if severity == StuffingSeverity.CRITICAL:
            implications.extend([
                "Pattern suggests coordinated revenue manipulation scheme",
                "Consider criminal investigation referral to DOJ",
                "Potential auditor liability under PCAOB standards"
            ])
        
        return implications
    
    def _get_recommended_actions(self, severity: StuffingSeverity) -> List[str]:
        """Get recommended investigative actions."""
        actions = [
            "Review all quarterly 10-Q filings for revenue recognition policies",
            "Analyze monthly revenue patterns within each quarter",
            "Examine accounts receivable aging schedules",
            "Review credit term modifications and side agreements"
        ]
        
        if severity in [StuffingSeverity.HIGH, StuffingSeverity.CRITICAL]:
            actions.extend([
                "Interview sales personnel regarding quarter-end pressure",
                "Subpoena distributor/retailer inventory records",
                "Forensic analysis of return authorization documents",
                "Examine email communications regarding revenue targets",
                "Review sales compensation incentive structures",
                "Engage independent auditor for revenue recognition review"
            ])
        
        if severity == StuffingSeverity.CRITICAL:
            actions.extend([
                "Coordinate with SEC Office of the Chief Accountant",
                "Consider restatement of prior period financial statements",
                "Assess need for disgorgement and civil penalties",
                "Evaluate potential criminal securities fraud charges"
            ])
        
        return actions
    
    def _generate_alert_id(self, company_cik: str) -> str:
        """Generate unique alert ID."""
        timestamp = datetime.utcnow().isoformat()
        data = f"CHANNEL_STUFFING_{company_cik}_{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16].upper()
    
    def _compute_evidence_hash(self, quarters: List[QuarterlyMetrics]) -> str:
        """Compute SHA-256 hash of all quarterly evidence."""
        evidence_data = [q.to_dict() for q in quarters]
        evidence_str = str(sorted(str(e) for e in evidence_data))
        return hashlib.sha256(evidence_str.encode()).hexdigest()
    
    def _generate_mock_alert(
        self,
        company_cik: str,
        company_name: str,
        num_quarters: int
    ) -> ChannelStuffingAlert:
        """Generate mock alert for testing without external dependencies."""
        # Create mock quarters
        mock_quarters = []
        for i in range(min(num_quarters, 4)):
            quarter = QuarterlyMetrics(
                quarter=f"Q{i+1} 2023",
                year=2023,
                quarter_num=i+1,
                total_revenue=1000000 * (i+1),
                last_month_revenue=450000 * (i+1),  # 45% concentration
                quarter_end_concentration=0.45,
                accounts_receivable=300000 * (i+1),
                days_sales_outstanding=81.0 + (i * 5),
                dso_change_pct=0.06 + (i * 0.05) if i > 0 else None,
                revenue_growth_pct=0.10,
                ar_growth_pct=0.25,
                ar_revenue_divergence=0.15,
                return_rate=0.02 + (i * 0.01),
                allowance_for_doubtful_accounts=5000 * (i+1),
                credit_terms_days=30
            )
            mock_quarters.append(quarter)
        
        # Create mock indicators
        mock_indicators = [
            StuffingIndicator(
                indicator_name="Quarter-End Revenue Concentration",
                detected=True,
                severity="HIGH",
                value=0.45,
                threshold=0.40,
                description="45% of revenue in final month"
            ),
            StuffingIndicator(
                indicator_name="AR/Revenue Growth Divergence",
                detected=True,
                severity="CRITICAL",
                value=0.15,
                threshold=0.10,
                description="AR growing 15pp faster than revenue"
            )
        ]
        
        return ChannelStuffingAlert(
            alert_id=self._generate_alert_id(company_cik),
            company_cik=company_cik,
            company_name=company_name,
            detection_date=datetime.utcnow(),
            severity=StuffingSeverity.HIGH,
            quarters_analyzed=mock_quarters,
            suspicious_quarters=["Q1 2023", "Q2 2023"],
            indicators=mock_indicators,
            red_flags_count=2,
            manipulation_probability=0.65,
            evidence_summary="Mock alert generated for testing",
            regulatory_implications=["Mock implication 1", "Mock implication 2"],
            recommended_actions=["Mock action 1", "Mock action 2"],
            evidence_hash=self._compute_evidence_hash(mock_quarters)
        )
    
    async def analyze_quarters_async(
        self,
        company_cik: str,
        company_name: str,
        quarterly_data: List[Dict[str, Any]]
    ) -> ChannelStuffingAlert:
        """Async version of analyze_quarters for concurrent execution."""
        # For now, just wrap synchronous version
        # In production, this could fetch 10-Q data asynchronously
        return self.analyze_quarters(company_cik, company_name, quarterly_data)
