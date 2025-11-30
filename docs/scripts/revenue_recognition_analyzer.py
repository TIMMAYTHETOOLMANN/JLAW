"""
Revenue Recognition Anomaly Analyzer
=====================================

Advanced detection of aggressive or fraudulent revenue recognition
practices through multi-factor analysis of financial metrics.

Detection Capabilities:
- Channel stuffing indicators
- Bill-and-hold arrangement detection
- Quarter-end revenue spikes (hockey stick patterns)
- Days Sales Outstanding (DSO) anomalies
- Deferred revenue irregularities
- Accounts receivable aging anomalies
- Revenue-cash flow divergence
- Industry benchmark deviations

Usage:
    analyzer = RevenueRecognitionAnalyzer()
    result = analyzer.analyze(
        financial_data=quarterly_financials,
        industry_benchmarks=tech_benchmarks
    )
    if result.overall_risk_score > 0.7:
        print("HIGH RISK: Revenue recognition anomalies detected")
"""

import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from enum import Enum
import json
from collections import defaultdict


class AnomalyType(Enum):
    """Types of revenue recognition anomalies."""
    DSO_DIVERGENCE = "dso_divergence"
    QUARTER_END_SPIKE = "quarter_end_spike"
    DEFERRED_REVENUE_DECLINE = "deferred_revenue_decline"
    AR_AGING_DETERIORATION = "ar_aging_deterioration"
    CASH_FLOW_DIVERGENCE = "cash_flow_divergence"
    CHANNEL_STUFFING = "channel_stuffing"
    BILL_AND_HOLD = "bill_and_hold"
    GROSS_MARGIN_VOLATILITY = "gross_margin_volatility"
    REVENUE_REVERSAL_RISK = "revenue_reversal_risk"
    ROUND_TRIPPING = "round_tripping"


class AnomalySeverity(Enum):
    """Severity levels for detected anomalies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QuarterlyFinancials:
    """Financial data for a single quarter."""
    period: str  # e.g., "Q1 2024" or "2024-Q1"
    period_end_date: str
    
    # Revenue metrics
    total_revenue: float
    product_revenue: Optional[float] = None
    service_revenue: Optional[float] = None
    subscription_revenue: Optional[float] = None
    
    # Cost and margin
    cost_of_revenue: float = 0
    gross_profit: float = 0
    gross_margin: float = 0
    
    # Balance sheet items
    accounts_receivable: float = 0
    allowance_for_doubtful_accounts: float = 0
    deferred_revenue: float = 0
    unbilled_revenue: float = 0
    inventory: float = 0
    
    # Cash flow
    cash_from_operations: float = 0
    cash_collected_from_customers: Optional[float] = None
    
    # Calculated metrics (will be computed)
    days_sales_outstanding: float = 0
    revenue_growth_yoy: Optional[float] = None
    revenue_growth_qoq: Optional[float] = None
    
    # Monthly breakdown if available
    monthly_revenue: Optional[List[float]] = None  # [month1, month2, month3]
    
    def __post_init__(self):
        """Calculate derived metrics."""
        if self.total_revenue > 0 and self.cost_of_revenue > 0:
            self.gross_profit = self.total_revenue - self.cost_of_revenue
            self.gross_margin = self.gross_profit / self.total_revenue
        
        if self.total_revenue > 0 and self.accounts_receivable > 0:
            # Approximate DSO using quarter-end AR
            daily_revenue = self.total_revenue / 90  # Approximate days in quarter
            self.days_sales_outstanding = self.accounts_receivable / daily_revenue


@dataclass 
class IndustryBenchmarks:
    """Industry benchmark data for comparison."""
    industry: str
    median_dso: float
    median_gross_margin: float
    median_revenue_growth: float
    
    # Percentile ranges
    dso_p25: float = 0
    dso_p75: float = 0
    gross_margin_p25: float = 0
    gross_margin_p75: float = 0
    
    # Typical seasonal patterns
    quarterly_seasonality: Optional[Dict[str, float]] = None  # {"Q1": 0.22, "Q2": 0.24, ...}


@dataclass
class RevenueAnomaly:
    """A detected revenue recognition anomaly."""
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    period: str
    description: str
    
    # Evidence
    observed_value: float
    expected_value: float
    deviation_pct: float
    
    # Supporting data
    supporting_metrics: Dict[str, float]
    trend_data: Optional[List[Tuple[str, float]]] = None
    
    # Forensic indicators
    fraud_indicators: List[str] = field(default_factory=list)
    investigation_recommendations: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.fraud_indicators:
            self.fraud_indicators = []
        if not self.investigation_recommendations:
            self.investigation_recommendations = []


@dataclass
class QuarterlyPattern:
    """Analysis of quarter-end patterns."""
    period: str
    month1_pct: float
    month2_pct: float
    month3_pct: float
    hockey_stick_score: float  # 0-1, higher = more concentrated at quarter end
    is_anomalous: bool
    prior_period_comparison: Optional[float] = None


@dataclass
class DSOAnalysis:
    """Days Sales Outstanding trend analysis."""
    current_dso: float
    prior_quarter_dso: float
    prior_year_dso: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    vs_industry_median: float  # Percentage deviation from industry
    vs_revenue_growth: float  # DSO growth vs revenue growth ratio
    anomaly_score: float  # 0-1


@dataclass
class DeferredRevenueAnalysis:
    """Deferred revenue analysis."""
    current_deferred: float
    prior_quarter_deferred: float
    change_pct: float
    vs_new_bookings: Optional[float] = None
    coverage_ratio: float = 0  # Deferred revenue / quarterly revenue
    trend_periods: int = 0  # Consecutive periods of decline
    anomaly_score: float = 0


@dataclass
class RevenueRecognitionAnalysis:
    """Complete revenue recognition analysis result."""
    analysis_id: str
    analysis_timestamp: str
    periods_analyzed: int
    
    # Individual analyses
    anomalies: List[RevenueAnomaly]
    dso_analysis: DSOAnalysis
    deferred_revenue_analysis: DeferredRevenueAnalysis
    quarterly_patterns: List[QuarterlyPattern]
    
    # Aggregate scores
    overall_risk_score: float  # 0-1
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    
    # Key findings
    key_findings: List[str]
    investigation_priorities: List[str]
    
    # Comparison data
    vs_industry_summary: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "analysis_id": self.analysis_id,
            "analysis_timestamp": self.analysis_timestamp,
            "periods_analyzed": self.periods_analyzed,
            "overall_risk_score": self.overall_risk_score,
            "risk_level": self.risk_level,
            "anomaly_count": len(self.anomalies),
            "key_findings": self.key_findings,
            "investigation_priorities": self.investigation_priorities
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class RevenueRecognitionAnalyzer:
    """
    Analyzes financial data for revenue recognition anomalies
    that may indicate aggressive accounting or fraud.
    """
    
    # Thresholds for anomaly detection
    DSO_GROWTH_THRESHOLD = 0.15  # 15% DSO increase is concerning
    HOCKEY_STICK_THRESHOLD = 0.45  # >45% in final month is suspicious
    DEFERRED_DECLINE_THRESHOLD = -0.10  # 10% decline is notable
    CASH_FLOW_DIVERGENCE_THRESHOLD = 0.20  # 20% divergence from revenue
    
    def __init__(
        self,
        dso_sensitivity: float = 1.0,
        pattern_sensitivity: float = 1.0,
        cash_flow_sensitivity: float = 1.0
    ):
        """
        Initialize the analyzer.
        
        Args:
            dso_sensitivity: Multiplier for DSO anomaly detection (0.5-2.0)
            pattern_sensitivity: Multiplier for pattern detection
            cash_flow_sensitivity: Multiplier for cash flow analysis
        """
        self.dso_sensitivity = max(0.5, min(2.0, dso_sensitivity))
        self.pattern_sensitivity = max(0.5, min(2.0, pattern_sensitivity))
        self.cash_flow_sensitivity = max(0.5, min(2.0, cash_flow_sensitivity))
    
    def analyze(
        self,
        financial_data: List[QuarterlyFinancials],
        industry_benchmarks: Optional[IndustryBenchmarks] = None,
        peer_data: Optional[List[Dict[str, float]]] = None
    ) -> RevenueRecognitionAnalysis:
        """
        Perform comprehensive revenue recognition analysis.
        
        Args:
            financial_data: List of quarterly financial data (chronological order)
            industry_benchmarks: Optional industry comparison data
            peer_data: Optional peer company comparison data
            
        Returns:
            RevenueRecognitionAnalysis with findings
        """
        import hashlib
        
        analysis_id = hashlib.sha256(
            f"{datetime.utcnow().isoformat()}|{len(financial_data)}".encode()
        ).hexdigest()[:16]
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        if len(financial_data) < 2:
            return RevenueRecognitionAnalysis(
                analysis_id=analysis_id,
                analysis_timestamp=timestamp,
                periods_analyzed=len(financial_data),
                anomalies=[],
                dso_analysis=DSOAnalysis(0, 0, 0, "stable", 0, 0, 0),
                deferred_revenue_analysis=DeferredRevenueAnalysis(0, 0, 0),
                quarterly_patterns=[],
                overall_risk_score=0,
                risk_level="LOW",
                key_findings=["Insufficient data for analysis"],
                investigation_priorities=[],
                vs_industry_summary={}
            )
        
        # Sort by period (chronological)
        sorted_data = sorted(financial_data, key=lambda x: x.period_end_date)
        
        anomalies = []
        
        # 1. DSO Analysis
        dso_analysis = self._analyze_dso(sorted_data, industry_benchmarks)
        if dso_analysis.anomaly_score > 0.5:
            anomalies.append(self._create_dso_anomaly(dso_analysis, sorted_data[-1]))
        
        # 2. Deferred Revenue Analysis
        deferred_analysis = self._analyze_deferred_revenue(sorted_data)
        if deferred_analysis.anomaly_score > 0.5:
            anomalies.append(self._create_deferred_anomaly(deferred_analysis, sorted_data[-1]))
        
        # 3. Quarterly Pattern Analysis (hockey stick detection)
        quarterly_patterns = self._analyze_quarterly_patterns(sorted_data)
        for pattern in quarterly_patterns:
            if pattern.is_anomalous:
                anomalies.append(self._create_pattern_anomaly(pattern))
        
        # 4. Cash Flow Divergence Analysis
        cash_anomalies = self._analyze_cash_flow_divergence(sorted_data)
        anomalies.extend(cash_anomalies)
        
        # 5. Gross Margin Volatility
        margin_anomalies = self._analyze_gross_margin(sorted_data, industry_benchmarks)
        anomalies.extend(margin_anomalies)
        
        # 6. AR Aging Analysis (if data available)
        ar_anomalies = self._analyze_ar_aging(sorted_data)
        anomalies.extend(ar_anomalies)
        
        # Calculate overall risk score
        overall_risk_score = self._calculate_overall_risk(anomalies, dso_analysis, deferred_analysis)
        risk_level = self._determine_risk_level(overall_risk_score)
        
        # Generate key findings
        key_findings = self._generate_key_findings(anomalies, dso_analysis, deferred_analysis)
        
        # Generate investigation priorities
        investigation_priorities = self._generate_investigation_priorities(anomalies)
        
        # Industry comparison summary
        vs_industry = {}
        if industry_benchmarks:
            vs_industry = self._compare_to_industry(sorted_data[-1], industry_benchmarks)
        
        return RevenueRecognitionAnalysis(
            analysis_id=analysis_id,
            analysis_timestamp=timestamp,
            periods_analyzed=len(sorted_data),
            anomalies=anomalies,
            dso_analysis=dso_analysis,
            deferred_revenue_analysis=deferred_analysis,
            quarterly_patterns=quarterly_patterns,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            key_findings=key_findings,
            investigation_priorities=investigation_priorities,
            vs_industry_summary=vs_industry
        )
    
    def _analyze_dso(
        self,
        data: List[QuarterlyFinancials],
        benchmarks: Optional[IndustryBenchmarks]
    ) -> DSOAnalysis:
        """Analyze Days Sales Outstanding trends."""
        current = data[-1]
        prior_quarter = data[-2] if len(data) >= 2 else None
        prior_year = data[-4] if len(data) >= 4 else None
        
        current_dso = current.days_sales_outstanding
        prior_q_dso = prior_quarter.days_sales_outstanding if prior_quarter else current_dso
        prior_y_dso = prior_year.days_sales_outstanding if prior_year else current_dso
        
        # Determine trend
        if current_dso > prior_q_dso * 1.05:
            trend = "increasing"
        elif current_dso < prior_q_dso * 0.95:
            trend = "decreasing"
        else:
            trend = "stable"
        
        # Compare to industry
        vs_industry = 0.0
        if benchmarks and benchmarks.median_dso > 0:
            vs_industry = (current_dso - benchmarks.median_dso) / benchmarks.median_dso
        
        # Compare DSO growth to revenue growth
        vs_revenue = 0.0
        if prior_q_dso > 0 and prior_quarter:
            dso_growth = (current_dso - prior_q_dso) / prior_q_dso
            revenue_growth = current.revenue_growth_qoq or 0
            if revenue_growth != 0:
                vs_revenue = dso_growth - revenue_growth
        
        # Calculate anomaly score
        anomaly_score = 0.0
        
        # DSO increasing faster than revenue is concerning
        if vs_revenue > self.DSO_GROWTH_THRESHOLD * self.dso_sensitivity:
            anomaly_score += 0.4
        
        # DSO significantly above industry median
        if vs_industry > 0.3:
            anomaly_score += 0.3
        
        # Sustained DSO increase
        if trend == "increasing" and prior_year:
            yoy_increase = (current_dso - prior_y_dso) / prior_y_dso if prior_y_dso > 0 else 0
            if yoy_increase > 0.2:
                anomaly_score += 0.3
        
        return DSOAnalysis(
            current_dso=current_dso,
            prior_quarter_dso=prior_q_dso,
            prior_year_dso=prior_y_dso,
            trend_direction=trend,
            vs_industry_median=vs_industry,
            vs_revenue_growth=vs_revenue,
            anomaly_score=min(1.0, anomaly_score)
        )
    
    def _analyze_deferred_revenue(
        self,
        data: List[QuarterlyFinancials]
    ) -> DeferredRevenueAnalysis:
        """Analyze deferred revenue trends."""
        current = data[-1]
        prior = data[-2] if len(data) >= 2 else None
        
        current_deferred = current.deferred_revenue
        prior_deferred = prior.deferred_revenue if prior else current_deferred
        
        change_pct = 0.0
        if prior_deferred > 0:
            change_pct = (current_deferred - prior_deferred) / prior_deferred
        
        # Coverage ratio
        coverage = current_deferred / current.total_revenue if current.total_revenue > 0 else 0
        
        # Count consecutive decline periods
        decline_periods = 0
        for i in range(len(data) - 1, 0, -1):
            if data[i].deferred_revenue < data[i-1].deferred_revenue:
                decline_periods += 1
            else:
                break
        
        # Calculate anomaly score
        anomaly_score = 0.0
        
        # Declining deferred revenue while revenue growing is suspicious
        if change_pct < self.DEFERRED_DECLINE_THRESHOLD:
            if current.revenue_growth_qoq and current.revenue_growth_qoq > 0:
                anomaly_score += 0.5
            else:
                anomaly_score += 0.3
        
        # Multiple consecutive decline periods
        if decline_periods >= 3:
            anomaly_score += 0.3
        
        # Very low coverage ratio
        if coverage < 0.1:
            anomaly_score += 0.2
        
        return DeferredRevenueAnalysis(
            current_deferred=current_deferred,
            prior_quarter_deferred=prior_deferred,
            change_pct=change_pct,
            coverage_ratio=coverage,
            trend_periods=decline_periods,
            anomaly_score=min(1.0, anomaly_score)
        )
    
    def _analyze_quarterly_patterns(
        self,
        data: List[QuarterlyFinancials]
    ) -> List[QuarterlyPattern]:
        """Analyze quarter-end revenue concentration (hockey stick patterns)."""
        patterns = []
        
        for quarter in data:
            if quarter.monthly_revenue and len(quarter.monthly_revenue) == 3:
                total = sum(quarter.monthly_revenue)
                if total > 0:
                    m1_pct = quarter.monthly_revenue[0] / total
                    m2_pct = quarter.monthly_revenue[1] / total
                    m3_pct = quarter.monthly_revenue[2] / total
                    
                    # Hockey stick score: how concentrated is month 3?
                    # Expected even distribution: 33% each
                    hockey_score = max(0, m3_pct - 0.33) / 0.67  # Normalize to 0-1
                    
                    is_anomalous = m3_pct > (self.HOCKEY_STICK_THRESHOLD * self.pattern_sensitivity)
                    
                    patterns.append(QuarterlyPattern(
                        period=quarter.period,
                        month1_pct=m1_pct,
                        month2_pct=m2_pct,
                        month3_pct=m3_pct,
                        hockey_stick_score=hockey_score,
                        is_anomalous=is_anomalous
                    ))
        
        return patterns
    
    def _analyze_cash_flow_divergence(
        self,
        data: List[QuarterlyFinancials]
    ) -> List[RevenueAnomaly]:
        """Analyze divergence between revenue and cash flow."""
        anomalies = []
        
        for quarter in data:
            if quarter.total_revenue > 0 and quarter.cash_from_operations != 0:
                # Calculate cash conversion ratio
                cash_ratio = quarter.cash_from_operations / quarter.total_revenue
                
                # Significant negative divergence is suspicious
                if cash_ratio < (1 - self.CASH_FLOW_DIVERGENCE_THRESHOLD * self.cash_flow_sensitivity):
                    severity = AnomalySeverity.HIGH if cash_ratio < 0.5 else AnomalySeverity.MEDIUM
                    
                    anomalies.append(RevenueAnomaly(
                        anomaly_type=AnomalyType.CASH_FLOW_DIVERGENCE,
                        severity=severity,
                        period=quarter.period,
                        description=f"Cash flow significantly below revenue ({cash_ratio:.1%} of revenue)",
                        observed_value=quarter.cash_from_operations,
                        expected_value=quarter.total_revenue * 0.8,
                        deviation_pct=(cash_ratio - 0.8) / 0.8,
                        supporting_metrics={
                            "revenue": quarter.total_revenue,
                            "cash_from_operations": quarter.cash_from_operations,
                            "cash_conversion_ratio": cash_ratio
                        },
                        fraud_indicators=[
                            "Revenue may not be supported by cash collection",
                            "Possible aggressive revenue recognition"
                        ],
                        investigation_recommendations=[
                            "Review customer payment terms and collection",
                            "Analyze AR aging detail",
                            "Compare cash receipts to billings"
                        ]
                    ))
        
        return anomalies
    
    def _analyze_gross_margin(
        self,
        data: List[QuarterlyFinancials],
        benchmarks: Optional[IndustryBenchmarks]
    ) -> List[RevenueAnomaly]:
        """Analyze gross margin trends and volatility."""
        anomalies = []
        
        if len(data) < 3:
            return anomalies
        
        margins = [q.gross_margin for q in data if q.gross_margin > 0]
        
        if len(margins) < 3:
            return anomalies
        
        # Calculate margin volatility
        mean_margin = sum(margins) / len(margins)
        variance = sum((m - mean_margin) ** 2 for m in margins) / len(margins)
        std_dev = math.sqrt(variance)
        
        # High volatility is suspicious
        coefficient_of_variation = std_dev / mean_margin if mean_margin > 0 else 0
        
        if coefficient_of_variation > 0.15:  # >15% CV is notable
            severity = AnomalySeverity.HIGH if coefficient_of_variation > 0.25 else AnomalySeverity.MEDIUM
            
            anomalies.append(RevenueAnomaly(
                anomaly_type=AnomalyType.GROSS_MARGIN_VOLATILITY,
                severity=severity,
                period=data[-1].period,
                description=f"High gross margin volatility (CV: {coefficient_of_variation:.1%})",
                observed_value=coefficient_of_variation,
                expected_value=0.10,
                deviation_pct=(coefficient_of_variation - 0.10) / 0.10,
                supporting_metrics={
                    "mean_margin": mean_margin,
                    "std_dev": std_dev,
                    "current_margin": margins[-1]
                },
                fraud_indicators=[
                    "Inconsistent revenue/cost recognition",
                    "Possible earnings management"
                ],
                investigation_recommendations=[
                    "Review cost allocation methodology",
                    "Analyze product mix changes",
                    "Check for one-time adjustments"
                ]
            ))
        
        return anomalies
    
    def _analyze_ar_aging(
        self,
        data: List[QuarterlyFinancials]
    ) -> List[RevenueAnomaly]:
        """Analyze accounts receivable quality indicators."""
        anomalies = []
        
        for i, quarter in enumerate(data):
            if quarter.accounts_receivable > 0 and quarter.allowance_for_doubtful_accounts > 0:
                # Allowance as % of AR
                allowance_pct = quarter.allowance_for_doubtful_accounts / quarter.accounts_receivable
                
                # Check for significant allowance increase
                if i > 0:
                    prior = data[i-1]
                    if prior.allowance_for_doubtful_accounts > 0:
                        prior_pct = prior.allowance_for_doubtful_accounts / prior.accounts_receivable if prior.accounts_receivable > 0 else 0
                        
                        if allowance_pct > prior_pct * 1.5:  # 50%+ increase
                            anomalies.append(RevenueAnomaly(
                                anomaly_type=AnomalyType.AR_AGING_DETERIORATION,
                                severity=AnomalySeverity.HIGH,
                                period=quarter.period,
                                description=f"Significant increase in bad debt allowance ({prior_pct:.1%} → {allowance_pct:.1%})",
                                observed_value=allowance_pct,
                                expected_value=prior_pct,
                                deviation_pct=(allowance_pct - prior_pct) / prior_pct if prior_pct > 0 else 0,
                                supporting_metrics={
                                    "allowance": quarter.allowance_for_doubtful_accounts,
                                    "accounts_receivable": quarter.accounts_receivable,
                                    "allowance_pct": allowance_pct
                                },
                                fraud_indicators=[
                                    "Prior revenue may have been uncollectible",
                                    "Possible channel stuffing reversals"
                                ],
                                investigation_recommendations=[
                                    "Review specific customer write-offs",
                                    "Analyze aging bucket changes",
                                    "Check for related party transactions"
                                ]
                            ))
        
        return anomalies
    
    def _create_dso_anomaly(
        self,
        analysis: DSOAnalysis,
        current: QuarterlyFinancials
    ) -> RevenueAnomaly:
        """Create anomaly record for DSO issues."""
        return RevenueAnomaly(
            anomaly_type=AnomalyType.DSO_DIVERGENCE,
            severity=AnomalySeverity.HIGH if analysis.anomaly_score > 0.7 else AnomalySeverity.MEDIUM,
            period=current.period,
            description=f"DSO growth exceeds revenue growth by {analysis.vs_revenue_growth:.1%}",
            observed_value=analysis.current_dso,
            expected_value=analysis.prior_quarter_dso,
            deviation_pct=(analysis.current_dso - analysis.prior_quarter_dso) / analysis.prior_quarter_dso if analysis.prior_quarter_dso > 0 else 0,
            supporting_metrics={
                "current_dso": analysis.current_dso,
                "prior_dso": analysis.prior_quarter_dso,
                "trend": analysis.trend_direction,
                "vs_industry": analysis.vs_industry_median
            },
            fraud_indicators=[
                "Collection issues may indicate revenue quality problems",
                "Possible premature revenue recognition"
            ],
            investigation_recommendations=[
                "Review AR aging detail by customer",
                "Analyze collection patterns vs historical",
                "Check for unusual revenue transactions near quarter-end"
            ]
        )
    
    def _create_deferred_anomaly(
        self,
        analysis: DeferredRevenueAnalysis,
        current: QuarterlyFinancials
    ) -> RevenueAnomaly:
        """Create anomaly record for deferred revenue issues."""
        return RevenueAnomaly(
            anomaly_type=AnomalyType.DEFERRED_REVENUE_DECLINE,
            severity=AnomalySeverity.HIGH if analysis.anomaly_score > 0.7 else AnomalySeverity.MEDIUM,
            period=current.period,
            description=f"Deferred revenue declined {abs(analysis.change_pct):.1%} while revenue grew",
            observed_value=analysis.current_deferred,
            expected_value=analysis.prior_quarter_deferred,
            deviation_pct=analysis.change_pct,
            supporting_metrics={
                "current_deferred": analysis.current_deferred,
                "prior_deferred": analysis.prior_quarter_deferred,
                "coverage_ratio": analysis.coverage_ratio,
                "decline_periods": analysis.trend_periods
            },
            fraud_indicators=[
                "May indicate pull-forward of revenue",
                "Backlog may be declining",
                "Future revenue at risk"
            ],
            investigation_recommendations=[
                "Analyze new bookings vs revenue recognized",
                "Review contract terms for acceleration clauses",
                "Compare to guidance and forward outlook"
            ]
        )
    
    def _create_pattern_anomaly(self, pattern: QuarterlyPattern) -> RevenueAnomaly:
        """Create anomaly record for quarter-end patterns."""
        return RevenueAnomaly(
            anomaly_type=AnomalyType.QUARTER_END_SPIKE,
            severity=AnomalySeverity.HIGH if pattern.month3_pct > 0.50 else AnomalySeverity.MEDIUM,
            period=pattern.period,
            description=f"Revenue heavily concentrated in final month ({pattern.month3_pct:.1%})",
            observed_value=pattern.month3_pct,
            expected_value=0.33,
            deviation_pct=(pattern.month3_pct - 0.33) / 0.33,
            supporting_metrics={
                "month1_pct": pattern.month1_pct,
                "month2_pct": pattern.month2_pct,
                "month3_pct": pattern.month3_pct,
                "hockey_stick_score": pattern.hockey_stick_score
            },
            fraud_indicators=[
                "Classic channel stuffing indicator",
                "May indicate quarter-end deals with unusual terms",
                "Side agreements possible"
            ],
            investigation_recommendations=[
                "Review largest deals in final month",
                "Check for unusual payment terms",
                "Analyze returns/credits in following quarter",
                "Interview sales personnel about quota pressure"
            ]
        )
    
    def _calculate_overall_risk(
        self,
        anomalies: List[RevenueAnomaly],
        dso: DSOAnalysis,
        deferred: DeferredRevenueAnalysis
    ) -> float:
        """Calculate overall risk score from all analyses."""
        score = 0.0
        
        # Base score from anomaly count and severity
        for anomaly in anomalies:
            if anomaly.severity == AnomalySeverity.CRITICAL:
                score += 0.25
            elif anomaly.severity == AnomalySeverity.HIGH:
                score += 0.15
            elif anomaly.severity == AnomalySeverity.MEDIUM:
                score += 0.08
            else:
                score += 0.03
        
        # Add DSO and deferred scores
        score += dso.anomaly_score * 0.2
        score += deferred.anomaly_score * 0.2
        
        return min(1.0, score)
    
    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level from score."""
        if score >= 0.7:
            return "CRITICAL"
        elif score >= 0.5:
            return "HIGH"
        elif score >= 0.3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_key_findings(
        self,
        anomalies: List[RevenueAnomaly],
        dso: DSOAnalysis,
        deferred: DeferredRevenueAnalysis
    ) -> List[str]:
        """Generate key findings summary."""
        findings = []
        
        if dso.trend_direction == "increasing" and dso.anomaly_score > 0.3:
            findings.append(f"DSO increasing trend (currently {dso.current_dso:.0f} days)")
        
        if deferred.trend_periods >= 2:
            findings.append(f"Deferred revenue declining for {deferred.trend_periods} consecutive quarters")
        
        critical_anomalies = [a for a in anomalies if a.severity == AnomalySeverity.CRITICAL]
        if critical_anomalies:
            findings.append(f"{len(critical_anomalies)} critical anomalies detected requiring immediate review")
        
        hockey_anomalies = [a for a in anomalies if a.anomaly_type == AnomalyType.QUARTER_END_SPIKE]
        if hockey_anomalies:
            findings.append("Quarter-end revenue concentration pattern detected")
        
        cash_anomalies = [a for a in anomalies if a.anomaly_type == AnomalyType.CASH_FLOW_DIVERGENCE]
        if cash_anomalies:
            findings.append("Cash flow divergence from revenue indicates collection issues")
        
        if not findings:
            findings.append("No significant revenue recognition anomalies detected")
        
        return findings
    
    def _generate_investigation_priorities(
        self,
        anomalies: List[RevenueAnomaly]
    ) -> List[str]:
        """Generate prioritized investigation recommendations."""
        priorities = []
        
        # Collect all unique recommendations
        all_recs = []
        for anomaly in sorted(anomalies, key=lambda a: a.severity.value, reverse=True):
            all_recs.extend(anomaly.investigation_recommendations)
        
        # Deduplicate while preserving order
        seen = set()
        for rec in all_recs:
            if rec not in seen:
                priorities.append(rec)
                seen.add(rec)
                if len(priorities) >= 5:
                    break
        
        return priorities
    
    def _compare_to_industry(
        self,
        current: QuarterlyFinancials,
        benchmarks: IndustryBenchmarks
    ) -> Dict[str, float]:
        """Compare current metrics to industry benchmarks."""
        return {
            "dso_vs_median": (current.days_sales_outstanding - benchmarks.median_dso) / benchmarks.median_dso if benchmarks.median_dso > 0 else 0,
            "gross_margin_vs_median": (current.gross_margin - benchmarks.median_gross_margin) / benchmarks.median_gross_margin if benchmarks.median_gross_margin > 0 else 0,
            "industry": benchmarks.industry
        }


# Module exports
__all__ = [
    "RevenueRecognitionAnalyzer",
    "RevenueRecognitionAnalysis",
    "QuarterlyFinancials",
    "IndustryBenchmarks",
    "RevenueAnomaly",
    "AnomalyType",
    "AnomalySeverity",
    "DSOAnalysis",
    "DeferredRevenueAnalysis",
    "QuarterlyPattern"
]
