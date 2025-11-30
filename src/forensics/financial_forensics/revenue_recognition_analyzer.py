"""
Revenue Recognition Analyzer - Accounting Fraud Detection System
=================================================================

Advanced revenue recognition analysis for detecting accounting fraud patterns
including DSO manipulation, hockey stick patterns, deferred revenue issues,
and cash flow divergence.

Features:
- Days Sales Outstanding (DSO) trend analysis
- Quarter-end revenue concentration (hockey stick) detection
- Deferred revenue decline tracking
- Cash flow vs revenue divergence
- Gross margin volatility analysis
- AR aging deterioration detection
- Industry benchmark comparison

Usage:
    analyzer = RevenueRecognitionAnalyzer()
    
    quarterly_data = [
        QuarterlyFinancials(
            quarter="Q1 2024",
            revenue=1000000,
            accounts_receivable=150000,
            deferred_revenue=50000,
            operating_cash_flow=120000,
            cogs=600000,
        ),
        # ... more quarters
    ]
    
    result = analyzer.analyze(quarterly_data)
    if result.overall_risk_score > 0.7:
        print("HIGH RISK:", result.key_findings)
"""

import logging
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Type of revenue recognition anomaly."""
    DSO_SPIKE = "dso_spike"
    DSO_TREND_UP = "dso_trend_up"
    HOCKEY_STICK = "hockey_stick"
    DEFERRED_REVENUE_DECLINE = "deferred_revenue_decline"
    CASH_REVENUE_DIVERGENCE = "cash_revenue_divergence"
    GROSS_MARGIN_VOLATILITY = "gross_margin_volatility"
    AR_AGING_DETERIORATION = "ar_aging_deterioration"
    REVENUE_RESERVE_IMBALANCE = "revenue_reserve_imbalance"
    CHANNEL_STUFFING = "channel_stuffing"
    BILL_AND_HOLD = "bill_and_hold"


class RiskLevel(Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QuarterlyFinancials:
    """Quarterly financial data for analysis."""
    quarter: str
    revenue: float
    accounts_receivable: float
    deferred_revenue: float = 0.0
    operating_cash_flow: float = 0.0
    cogs: float = 0.0  # Cost of goods sold
    inventory: float = 0.0
    bad_debt_expense: float = 0.0
    allowance_for_doubtful_accounts: float = 0.0
    revenue_by_month: Optional[List[float]] = None  # For hockey stick detection
    ar_aging_buckets: Optional[Dict[str, float]] = None  # e.g., {'0-30': 50000, '31-60': 30000}
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def gross_profit(self) -> float:
        """Calculate gross profit."""
        return self.revenue - self.cogs
    
    @property
    def gross_margin(self) -> float:
        """Calculate gross margin percentage."""
        if self.revenue == 0:
            return 0.0
        return (self.revenue - self.cogs) / self.revenue


@dataclass
class RevenueAnomaly:
    """Detected revenue recognition anomaly."""
    anomaly_type: AnomalyType
    quarter: str
    severity: float  # 0.0-1.0
    description: str
    evidence: List[str]
    risk_level: RiskLevel
    recommendation: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IndustryBenchmark:
    """Industry benchmark data for comparison."""
    industry: str
    avg_dso: float
    dso_std_dev: float
    avg_gross_margin: float
    gross_margin_std_dev: float
    avg_deferred_revenue_ratio: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class RevenueAnalysisResult:
    """Result of revenue recognition analysis."""
    quarters_analyzed: int
    anomalies: List[RevenueAnomaly]
    dso_trend: List[float]
    gross_margin_trend: List[float]
    cash_conversion_trend: List[float]
    overall_risk_score: float
    risk_level: RiskLevel
    key_findings: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


# Default industry benchmarks
DEFAULT_BENCHMARKS = {
    'technology': IndustryBenchmark(
        industry='technology',
        avg_dso=45.0,
        dso_std_dev=15.0,
        avg_gross_margin=0.65,
        gross_margin_std_dev=0.1,
        avg_deferred_revenue_ratio=0.15,
    ),
    'retail': IndustryBenchmark(
        industry='retail',
        avg_dso=25.0,
        dso_std_dev=10.0,
        avg_gross_margin=0.35,
        gross_margin_std_dev=0.08,
        avg_deferred_revenue_ratio=0.05,
    ),
    'manufacturing': IndustryBenchmark(
        industry='manufacturing',
        avg_dso=55.0,
        dso_std_dev=20.0,
        avg_gross_margin=0.25,
        gross_margin_std_dev=0.07,
        avg_deferred_revenue_ratio=0.08,
    ),
    'services': IndustryBenchmark(
        industry='services',
        avg_dso=40.0,
        dso_std_dev=12.0,
        avg_gross_margin=0.45,
        gross_margin_std_dev=0.12,
        avg_deferred_revenue_ratio=0.20,
    ),
    'default': IndustryBenchmark(
        industry='default',
        avg_dso=45.0,
        dso_std_dev=15.0,
        avg_gross_margin=0.40,
        gross_margin_std_dev=0.10,
        avg_deferred_revenue_ratio=0.10,
    ),
}


class RevenueRecognitionAnalyzer:
    """
    Revenue recognition fraud detection system.
    
    Analyzes quarterly financial data for patterns indicative of
    revenue manipulation, channel stuffing, and other accounting fraud.
    
    Example:
        analyzer = RevenueRecognitionAnalyzer()
        
        quarterly_data = [
            QuarterlyFinancials(quarter="Q1", revenue=1000000, ...),
            QuarterlyFinancials(quarter="Q2", revenue=1100000, ...),
        ]
        
        result = analyzer.analyze(quarterly_data)
    """
    
    # Days in quarter for DSO calculation
    DAYS_IN_QUARTER = 91
    
    # Thresholds
    DSO_SPIKE_THRESHOLD = 0.3  # 30% increase
    DSO_TREND_THRESHOLD = 0.15  # 15% quarterly increase over 3+ quarters
    HOCKEY_STICK_THRESHOLD = 0.4  # 40%+ of quarterly revenue in last month
    CASH_DIVERGENCE_THRESHOLD = 0.25  # 25% divergence
    MARGIN_VOLATILITY_THRESHOLD = 0.2  # 20% change in gross margin
    AR_AGING_THRESHOLD = 0.5  # 50%+ in aged buckets
    
    def __init__(
        self,
        industry: str = 'default',
        custom_benchmark: Optional[IndustryBenchmark] = None,
        dso_spike_threshold: float = 0.3,
        hockey_stick_threshold: float = 0.4,
        cash_divergence_threshold: float = 0.25,
    ):
        """
        Initialize the revenue recognition analyzer.
        
        Args:
            industry: Industry for benchmark comparison
            custom_benchmark: Custom benchmark data
            dso_spike_threshold: Threshold for DSO spike detection
            hockey_stick_threshold: Threshold for hockey stick detection
            cash_divergence_threshold: Threshold for cash/revenue divergence
        """
        self.benchmark = custom_benchmark or DEFAULT_BENCHMARKS.get(
            industry, DEFAULT_BENCHMARKS['default']
        )
        self.dso_spike_threshold = dso_spike_threshold
        self.hockey_stick_threshold = hockey_stick_threshold
        self.cash_divergence_threshold = cash_divergence_threshold
        
        logger.info(f"RevenueRecognitionAnalyzer initialized for industry: {self.benchmark.industry}")
    
    def analyze(
        self, 
        quarterly_data: List[QuarterlyFinancials]
    ) -> RevenueAnalysisResult:
        """
        Analyze quarterly financial data for revenue recognition issues.
        
        Args:
            quarterly_data: List of quarterly financials (chronological order)
            
        Returns:
            RevenueAnalysisResult with detected anomalies and risk assessment
        """
        if not quarterly_data:
            return RevenueAnalysisResult(
                quarters_analyzed=0,
                anomalies=[],
                dso_trend=[],
                gross_margin_trend=[],
                cash_conversion_trend=[],
                overall_risk_score=0.0,
                risk_level=RiskLevel.LOW,
                key_findings=[],
                recommendations=[],
            )
        
        logger.info(f"Analyzing {len(quarterly_data)} quarters of financial data")
        
        # Calculate trends
        dso_trend = self._calculate_dso_trend(quarterly_data)
        gross_margin_trend = [q.gross_margin for q in quarterly_data]
        cash_conversion_trend = self._calculate_cash_conversion_trend(quarterly_data)
        
        # Detect anomalies
        anomalies = []
        
        # 1. DSO Analysis
        dso_anomalies = self._analyze_dso(quarterly_data, dso_trend)
        anomalies.extend(dso_anomalies)
        
        # 2. Hockey Stick Detection
        hockey_stick_anomalies = self._detect_hockey_stick(quarterly_data)
        anomalies.extend(hockey_stick_anomalies)
        
        # 3. Deferred Revenue Analysis
        deferred_anomalies = self._analyze_deferred_revenue(quarterly_data)
        anomalies.extend(deferred_anomalies)
        
        # 4. Cash Flow Divergence
        cash_anomalies = self._analyze_cash_divergence(quarterly_data)
        anomalies.extend(cash_anomalies)
        
        # 5. Gross Margin Volatility
        margin_anomalies = self._analyze_gross_margin(quarterly_data, gross_margin_trend)
        anomalies.extend(margin_anomalies)
        
        # 6. AR Aging Deterioration
        ar_anomalies = self._analyze_ar_aging(quarterly_data)
        anomalies.extend(ar_anomalies)
        
        # Calculate overall risk
        overall_risk_score = self._calculate_risk_score(anomalies)
        risk_level = self._determine_risk_level(overall_risk_score)
        
        # Generate findings and recommendations
        key_findings = self._generate_findings(anomalies, dso_trend, gross_margin_trend)
        recommendations = self._generate_recommendations(anomalies, risk_level)
        
        return RevenueAnalysisResult(
            quarters_analyzed=len(quarterly_data),
            anomalies=anomalies,
            dso_trend=dso_trend,
            gross_margin_trend=gross_margin_trend,
            cash_conversion_trend=cash_conversion_trend,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            key_findings=key_findings,
            recommendations=recommendations,
        )
    
    def _calculate_dso(self, quarter: QuarterlyFinancials) -> float:
        """Calculate Days Sales Outstanding."""
        if quarter.revenue == 0:
            return 0.0
        
        daily_revenue = quarter.revenue / self.DAYS_IN_QUARTER
        if daily_revenue == 0:
            return 0.0
        
        return quarter.accounts_receivable / daily_revenue
    
    def _calculate_dso_trend(self, quarters: List[QuarterlyFinancials]) -> List[float]:
        """Calculate DSO trend across quarters."""
        return [self._calculate_dso(q) for q in quarters]
    
    def _calculate_cash_conversion_trend(
        self, 
        quarters: List[QuarterlyFinancials]
    ) -> List[float]:
        """Calculate cash conversion ratio trend."""
        ratios = []
        for q in quarters:
            if q.revenue == 0:
                ratios.append(0.0)
            else:
                ratios.append(q.operating_cash_flow / q.revenue)
        return ratios
    
    def _analyze_dso(
        self, 
        quarters: List[QuarterlyFinancials],
        dso_trend: List[float],
    ) -> List[RevenueAnomaly]:
        """Analyze DSO for spikes and concerning trends."""
        anomalies = []
        
        if len(dso_trend) < 2:
            return anomalies
        
        # Check for DSO spikes
        for i in range(1, len(dso_trend)):
            if dso_trend[i-1] == 0:
                continue
            
            change = (dso_trend[i] - dso_trend[i-1]) / dso_trend[i-1]
            
            if change > self.dso_spike_threshold:
                anomalies.append(RevenueAnomaly(
                    anomaly_type=AnomalyType.DSO_SPIKE,
                    quarter=quarters[i].quarter,
                    severity=min(change, 1.0),
                    description=f"DSO increased {change*100:.1f}% from prior quarter",
                    evidence=[
                        f"DSO previous: {dso_trend[i-1]:.1f} days",
                        f"DSO current: {dso_trend[i]:.1f} days",
                        f"Industry average: {self.benchmark.avg_dso:.1f} days",
                    ],
                    risk_level=RiskLevel.HIGH if change > 0.5 else RiskLevel.MEDIUM,
                    recommendation="Investigate reasons for AR buildup; may indicate revenue timing issues",
                ))
        
        # Check for upward DSO trend
        if len(dso_trend) >= 3:
            consecutive_increases = 0
            for i in range(1, len(dso_trend)):
                if dso_trend[i] > dso_trend[i-1]:
                    consecutive_increases += 1
                else:
                    consecutive_increases = 0
                
                if consecutive_increases >= 3:
                    avg_increase = (dso_trend[i] - dso_trend[i-3]) / max(dso_trend[i-3], 1) / 3
                    if avg_increase > self.DSO_TREND_THRESHOLD / 3:
                        anomalies.append(RevenueAnomaly(
                            anomaly_type=AnomalyType.DSO_TREND_UP,
                            quarter=quarters[i].quarter,
                            severity=min(avg_increase * 3, 1.0),
                            description=f"DSO has increased for {consecutive_increases} consecutive quarters",
                            evidence=[
                                f"Starting DSO: {dso_trend[i-consecutive_increases]:.1f} days",
                                f"Current DSO: {dso_trend[i]:.1f} days",
                                f"Average quarterly increase: {avg_increase*100:.1f}%",
                            ],
                            risk_level=RiskLevel.HIGH,
                            recommendation="Review collection practices and revenue recognition policies",
                        ))
                        break
        
        # Compare to industry benchmark
        for i, dso in enumerate(dso_trend):
            z_score = (dso - self.benchmark.avg_dso) / max(self.benchmark.dso_std_dev, 1)
            if z_score > 2.0:
                anomalies.append(RevenueAnomaly(
                    anomaly_type=AnomalyType.DSO_SPIKE,
                    quarter=quarters[i].quarter,
                    severity=min(z_score / 4, 1.0),
                    description=f"DSO significantly above industry average",
                    evidence=[
                        f"Company DSO: {dso:.1f} days",
                        f"Industry average: {self.benchmark.avg_dso:.1f} days",
                        f"Z-score: {z_score:.2f}",
                    ],
                    risk_level=RiskLevel.MEDIUM,
                    recommendation="Benchmark against peers; investigate if structural or concerning",
                ))
        
        return anomalies
    
    def _detect_hockey_stick(
        self, 
        quarters: List[QuarterlyFinancials]
    ) -> List[RevenueAnomaly]:
        """Detect hockey stick revenue patterns (end of quarter loading)."""
        anomalies = []
        
        for q in quarters:
            if q.revenue_by_month is None or len(q.revenue_by_month) != 3:
                continue
            
            total_revenue = sum(q.revenue_by_month)
            if total_revenue == 0:
                continue
            
            # Calculate percentage of revenue in last month
            last_month_pct = q.revenue_by_month[2] / total_revenue
            
            if last_month_pct > self.hockey_stick_threshold:
                anomalies.append(RevenueAnomaly(
                    anomaly_type=AnomalyType.HOCKEY_STICK,
                    quarter=q.quarter,
                    severity=min((last_month_pct - 0.33) * 3, 1.0),
                    description=f"{last_month_pct*100:.1f}% of quarterly revenue recognized in final month",
                    evidence=[
                        f"Month 1: ${q.revenue_by_month[0]:,.0f} ({q.revenue_by_month[0]/total_revenue*100:.1f}%)",
                        f"Month 2: ${q.revenue_by_month[1]:,.0f} ({q.revenue_by_month[1]/total_revenue*100:.1f}%)",
                        f"Month 3: ${q.revenue_by_month[2]:,.0f} ({q.revenue_by_month[2]/total_revenue*100:.1f}%)",
                    ],
                    risk_level=RiskLevel.HIGH if last_month_pct > 0.5 else RiskLevel.MEDIUM,
                    recommendation="May indicate channel stuffing or aggressive revenue recognition; review deal terms",
                ))
        
        return anomalies
    
    def _analyze_deferred_revenue(
        self, 
        quarters: List[QuarterlyFinancials]
    ) -> List[RevenueAnomaly]:
        """Analyze deferred revenue trends."""
        anomalies = []
        
        if len(quarters) < 2:
            return anomalies
        
        # Calculate deferred revenue as percentage of revenue
        deferred_ratios = []
        for q in quarters:
            if q.revenue > 0:
                deferred_ratios.append(q.deferred_revenue / q.revenue)
            else:
                deferred_ratios.append(0.0)
        
        # Check for declining deferred revenue
        consecutive_declines = 0
        for i in range(1, len(deferred_ratios)):
            if deferred_ratios[i] < deferred_ratios[i-1]:
                consecutive_declines += 1
            else:
                consecutive_declines = 0
            
            if consecutive_declines >= 2:
                decline_pct = (deferred_ratios[i-2] - deferred_ratios[i]) / max(deferred_ratios[i-2], 0.01)
                if decline_pct > 0.2:  # 20%+ decline
                    anomalies.append(RevenueAnomaly(
                        anomaly_type=AnomalyType.DEFERRED_REVENUE_DECLINE,
                        quarter=quarters[i].quarter,
                        severity=min(decline_pct, 1.0),
                        description="Deferred revenue declining relative to revenue",
                        evidence=[
                            f"Deferred revenue ratio declined from {deferred_ratios[i-2]*100:.1f}% to {deferred_ratios[i]*100:.1f}%",
                            f"This may indicate pulling forward future revenue",
                        ],
                        risk_level=RiskLevel.MEDIUM,
                        recommendation="Verify subscription/contract renewal rates; may indicate future revenue concerns",
                    ))
        
        return anomalies
    
    def _analyze_cash_divergence(
        self, 
        quarters: List[QuarterlyFinancials]
    ) -> List[RevenueAnomaly]:
        """Analyze divergence between cash flow and revenue."""
        anomalies = []
        
        for q in quarters:
            if q.revenue == 0:
                continue
            
            cash_ratio = q.operating_cash_flow / q.revenue
            
            # Check for significant divergence (revenue growing faster than cash)
            if cash_ratio < (1 - self.cash_divergence_threshold):
                anomalies.append(RevenueAnomaly(
                    anomaly_type=AnomalyType.CASH_REVENUE_DIVERGENCE,
                    quarter=q.quarter,
                    severity=min((1 - cash_ratio), 1.0),
                    description=f"Operating cash flow significantly below revenue",
                    evidence=[
                        f"Revenue: ${q.revenue:,.0f}",
                        f"Operating Cash Flow: ${q.operating_cash_flow:,.0f}",
                        f"Cash/Revenue Ratio: {cash_ratio*100:.1f}%",
                    ],
                    risk_level=RiskLevel.HIGH if cash_ratio < 0.5 else RiskLevel.MEDIUM,
                    recommendation="High-quality earnings convert to cash; investigate collection issues",
                ))
        
        # Check for trend divergence
        if len(quarters) >= 3:
            revenues = [q.revenue for q in quarters]
            cash_flows = [q.operating_cash_flow for q in quarters]
            
            # Simple trend comparison
            revenue_growth = (revenues[-1] - revenues[0]) / max(revenues[0], 1)
            cash_growth = (cash_flows[-1] - cash_flows[0]) / max(abs(cash_flows[0]), 1)
            
            if revenue_growth > 0.2 and cash_growth < 0:
                anomalies.append(RevenueAnomaly(
                    anomaly_type=AnomalyType.CASH_REVENUE_DIVERGENCE,
                    quarter=quarters[-1].quarter,
                    severity=0.7,
                    description="Revenue growing while cash flow declining",
                    evidence=[
                        f"Revenue growth: {revenue_growth*100:.1f}%",
                        f"Cash flow growth: {cash_growth*100:.1f}%",
                    ],
                    risk_level=RiskLevel.HIGH,
                    recommendation="Earnings quality concern; verify revenue is being collected",
                ))
        
        return anomalies
    
    def _analyze_gross_margin(
        self, 
        quarters: List[QuarterlyFinancials],
        margin_trend: List[float],
    ) -> List[RevenueAnomaly]:
        """Analyze gross margin volatility."""
        anomalies = []
        
        if len(margin_trend) < 2:
            return anomalies
        
        # Check for significant margin changes
        for i in range(1, len(margin_trend)):
            if margin_trend[i-1] == 0:
                continue
            
            change = abs(margin_trend[i] - margin_trend[i-1])
            
            if change > self.MARGIN_VOLATILITY_THRESHOLD:
                anomalies.append(RevenueAnomaly(
                    anomaly_type=AnomalyType.GROSS_MARGIN_VOLATILITY,
                    quarter=quarters[i].quarter,
                    severity=min(change * 2, 1.0),
                    description=f"Gross margin changed by {change*100:.1f} percentage points",
                    evidence=[
                        f"Previous margin: {margin_trend[i-1]*100:.1f}%",
                        f"Current margin: {margin_trend[i]*100:.1f}%",
                        f"Industry average: {self.benchmark.avg_gross_margin*100:.1f}%",
                    ],
                    risk_level=RiskLevel.MEDIUM,
                    recommendation="Large margin swings may indicate inventory manipulation or cost allocation issues",
                ))
        
        # Calculate margin volatility (standard deviation)
        if len(margin_trend) >= 3:
            margin_std = statistics.stdev(margin_trend)
            if margin_std > self.benchmark.gross_margin_std_dev * 2:
                anomalies.append(RevenueAnomaly(
                    anomaly_type=AnomalyType.GROSS_MARGIN_VOLATILITY,
                    quarter=quarters[-1].quarter,
                    severity=min(margin_std / self.benchmark.gross_margin_std_dev / 4, 1.0),
                    description="Gross margin more volatile than industry norms",
                    evidence=[
                        f"Company margin std dev: {margin_std*100:.2f}%",
                        f"Industry norm: {self.benchmark.gross_margin_std_dev*100:.2f}%",
                    ],
                    risk_level=RiskLevel.MEDIUM,
                    recommendation="Investigate causes of margin instability",
                ))
        
        return anomalies
    
    def _analyze_ar_aging(
        self, 
        quarters: List[QuarterlyFinancials]
    ) -> List[RevenueAnomaly]:
        """Analyze accounts receivable aging deterioration."""
        anomalies = []
        
        for q in quarters:
            if q.ar_aging_buckets is None:
                continue
            
            total_ar = sum(q.ar_aging_buckets.values())
            if total_ar == 0:
                continue
            
            # Calculate percentage in aged buckets (over 60 days)
            aged_ar = sum(
                value for bucket, value in q.ar_aging_buckets.items()
                if any(key in bucket for key in ['61', '90', '120', '>'])
            )
            
            aged_pct = aged_ar / total_ar
            
            if aged_pct > self.AR_AGING_THRESHOLD:
                anomalies.append(RevenueAnomaly(
                    anomaly_type=AnomalyType.AR_AGING_DETERIORATION,
                    quarter=q.quarter,
                    severity=min(aged_pct, 1.0),
                    description=f"{aged_pct*100:.1f}% of AR aged over 60 days",
                    evidence=[
                        f"Total AR: ${total_ar:,.0f}",
                        f"Aged AR (60+ days): ${aged_ar:,.0f}",
                    ],
                    risk_level=RiskLevel.HIGH,
                    recommendation="Review bad debt reserves; may need to write off uncollectible receivables",
                ))
            
            # Check allowance for doubtful accounts
            if q.allowance_for_doubtful_accounts > 0:
                allowance_ratio = q.allowance_for_doubtful_accounts / q.accounts_receivable
                if allowance_ratio < 0.02 and aged_pct > 0.2:  # Low allowance with aged AR
                    anomalies.append(RevenueAnomaly(
                        anomaly_type=AnomalyType.AR_AGING_DETERIORATION,
                        quarter=q.quarter,
                        severity=0.6,
                        description="Allowance for doubtful accounts appears low given AR aging",
                        evidence=[
                            f"Allowance ratio: {allowance_ratio*100:.2f}%",
                            f"Aged AR: {aged_pct*100:.1f}%",
                        ],
                        risk_level=RiskLevel.MEDIUM,
                        recommendation="Reserve may be inadequate; potential earnings overstatement",
                    ))
        
        return anomalies
    
    def _calculate_risk_score(self, anomalies: List[RevenueAnomaly]) -> float:
        """Calculate overall risk score from anomalies."""
        if not anomalies:
            return 0.0
        
        # Weighted scoring based on anomaly type severity
        type_weights = {
            AnomalyType.CHANNEL_STUFFING: 1.0,
            AnomalyType.HOCKEY_STICK: 0.9,
            AnomalyType.CASH_REVENUE_DIVERGENCE: 0.85,
            AnomalyType.DSO_SPIKE: 0.7,
            AnomalyType.DSO_TREND_UP: 0.75,
            AnomalyType.DEFERRED_REVENUE_DECLINE: 0.6,
            AnomalyType.GROSS_MARGIN_VOLATILITY: 0.5,
            AnomalyType.AR_AGING_DETERIORATION: 0.65,
        }
        
        weighted_sum = sum(
            a.severity * type_weights.get(a.anomaly_type, 0.5)
            for a in anomalies
        )
        
        # Normalize by number of anomalies with diminishing returns
        count_factor = len(anomalies) ** 0.5
        raw_score = weighted_sum / count_factor if count_factor > 0 else 0
        
        # Scale to 0-1
        return min(raw_score, 1.0)
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score."""
        if score >= 0.8:
            return RiskLevel.CRITICAL
        elif score >= 0.6:
            return RiskLevel.HIGH
        elif score >= 0.3:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
    
    def _generate_findings(
        self,
        anomalies: List[RevenueAnomaly],
        dso_trend: List[float],
        margin_trend: List[float],
    ) -> List[str]:
        """Generate key findings from analysis."""
        findings = []
        
        # Summarize by anomaly type
        type_counts: Dict[AnomalyType, int] = {}
        for a in anomalies:
            type_counts[a.anomaly_type] = type_counts.get(a.anomaly_type, 0) + 1
        
        for atype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            findings.append(f"{atype.value}: {count} occurrence(s) detected")
        
        # DSO trend summary
        if len(dso_trend) >= 2:
            overall_change = dso_trend[-1] - dso_trend[0]
            if overall_change > 10:
                findings.append(f"DSO increased by {overall_change:.1f} days over analysis period")
            elif overall_change < -10:
                findings.append(f"DSO improved by {abs(overall_change):.1f} days over analysis period")
        
        # Margin trend summary
        if len(margin_trend) >= 2:
            margin_change = margin_trend[-1] - margin_trend[0]
            if abs(margin_change) > 0.05:
                direction = "improved" if margin_change > 0 else "declined"
                findings.append(f"Gross margin {direction} by {abs(margin_change)*100:.1f} percentage points")
        
        return findings
    
    def _generate_recommendations(
        self,
        anomalies: List[RevenueAnomaly],
        risk_level: RiskLevel,
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("CRITICAL: Immediate forensic audit recommended")
            recommendations.append("Consider engaging external forensic accountants")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("HIGH PRIORITY: Detailed review of revenue recognition required")
            recommendations.append("Compare management representations to underlying data")
        
        # Deduplicate recommendations from anomalies
        seen_recommendations = set()
        for a in anomalies:
            if a.recommendation not in seen_recommendations:
                recommendations.append(a.recommendation)
                seen_recommendations.add(a.recommendation)
        
        if not recommendations:
            recommendations.append("Continue monitoring; no significant issues detected")
        
        return recommendations[:10]  # Limit to top 10
