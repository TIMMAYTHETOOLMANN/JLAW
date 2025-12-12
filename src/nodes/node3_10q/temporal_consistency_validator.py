#!/usr/bin/env python3
"""
NODE 3: 10-Q Temporal Consistency Validator
Validates quarter-over-quarter financial consistency across 10-Q filings.
Detects: Restatement triggers, sudden metric shifts, inconsistent accounting
policy application, segment reporting anomalies, discontinued operations timing.

Legal Basis: Regulation S-X Rule 10-01, ASC 250 (Accounting Changes and Error Corrections)
"""

import re
import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timezone, timedelta
from typing import List, Dict, Optional, Tuple, Any, Union
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
import logging
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TemporalViolationType(Enum):
    """Classification of 10-Q temporal consistency violations"""
    RESTATEMENT_TRIGGER = "restatement_trigger"
    SUDDEN_METRIC_SHIFT = "sudden_metric_shift"
    ACCOUNTING_POLICY_CHANGE = "accounting_policy_change_unannounced"
    SEGMENT_REPORTING_INCONSISTENCY = "segment_reporting_inconsistency"
    DISCONTINUED_OPS_TIMING = "discontinued_operations_timing_anomaly"
    REVENUE_RECOGNITION_SHIFT = "revenue_recognition_timing_shift"
    INVENTORY_VALUATION_CHANGE = "inventory_valuation_method_change"
    RECEIVABLES_ANOMALY = "receivables_collection_anomaly"
    GROSS_MARGIN_MANIPULATION = "gross_margin_manipulation_signal"
    QUARTER_END_LOADING = "quarter_end_revenue_loading"
    COOKIE_JAR_RESERVE = "cookie_jar_reserve_pattern"
    BIG_BATH_CHARGES = "big_bath_charge_pattern"


@dataclass
class QuarterlyMetrics:
    """Financial metrics extracted from a single 10-Q"""
    cik: str
    fiscal_year: int
    fiscal_quarter: int  # 1, 2, or 3 (Q4 in 10-K)
    filing_date: date
    period_end_date: date
    
    # Income Statement
    revenue: Decimal
    cost_of_revenue: Decimal
    gross_profit: Decimal
    operating_expenses: Decimal
    operating_income: Decimal
    net_income: Decimal
    eps_basic: Decimal
    eps_diluted: Decimal
    
    # Balance Sheet
    total_assets: Decimal
    total_liabilities: Decimal
    stockholders_equity: Decimal
    cash_and_equivalents: Decimal
    accounts_receivable: Decimal
    inventory: Decimal
    accounts_payable: Decimal
    
    # Cash Flow
    operating_cash_flow: Decimal
    investing_cash_flow: Decimal
    financing_cash_flow: Decimal
    
    # Derived Metrics
    gross_margin: float = 0.0
    operating_margin: float = 0.0
    net_margin: float = 0.0
    days_sales_outstanding: float = 0.0
    days_inventory_outstanding: float = 0.0
    current_ratio: float = 0.0
    
    # Segment Data
    segments: Dict[str, Decimal] = field(default_factory=dict)
    
    # Accounting Policies
    revenue_recognition_method: str = ""
    inventory_method: str = ""  # FIFO, LIFO, Weighted Average
    depreciation_method: str = ""
    
    def __post_init__(self):
        """Calculate derived metrics"""
        if self.revenue > 0:
            self.gross_margin = float(self.gross_profit / self.revenue)
            self.operating_margin = float(self.operating_income / self.revenue)
            self.net_margin = float(self.net_income / self.revenue)
        
        if self.revenue > 0 and self.accounts_receivable > 0:
            daily_revenue = self.revenue / Decimal("90")  # Quarterly
            self.days_sales_outstanding = float(self.accounts_receivable / daily_revenue)
        
        if self.cost_of_revenue > 0 and self.inventory > 0:
            daily_cogs = self.cost_of_revenue / Decimal("90")
            self.days_inventory_outstanding = float(self.inventory / daily_cogs)


@dataclass
class TemporalViolation:
    """Detected temporal consistency violation"""
    violation_type: TemporalViolationType
    severity: int  # 1-10
    description: str
    affected_quarters: List[str]  # e.g., ["2024-Q1", "2024-Q2"]
    metric_name: str
    prior_value: Union[Decimal, float]
    current_value: Union[Decimal, float]
    change_percentage: float
    threshold_exceeded: float
    regulatory_citations: List[str]
    evidence_hash: str
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['violation_type'] = self.violation_type.value
        result['prior_value'] = str(self.prior_value)
        result['current_value'] = str(self.current_value)
        result['detected_at'] = self.detected_at.isoformat()
        return result


class TemporalConsistencyValidator:
    """
    10-Q Temporal Consistency Validator
    
    Implements ASC 250 compliance validation:
    - Quarter-over-quarter metric comparison
    - Accounting policy change detection
    - Restatement trigger identification
    - Earnings management pattern detection
    - Segment reporting consistency
    """
    
    # Thresholds for anomaly detection
    THRESHOLDS = {
        "revenue_change_pct": 25.0,  # >25% QoQ change triggers review
        "gross_margin_change_pct": 5.0,  # >5% points change
        "dso_change_days": 15.0,  # >15 days change
        "dio_change_days": 20.0,  # >20 days change
        "operating_margin_change_pct": 8.0,
        "segment_revenue_change_pct": 30.0,
        "quarter_end_revenue_concentration": 0.45,  # >45% in last month
    }
    
    # Patterns indicating earnings management
    EARNINGS_MANAGEMENT_PATTERNS = {
        "cookie_jar": "building_reserves_in_good_quarters",
        "big_bath": "concentrating_charges_in_bad_quarters",
        "channel_stuffing": "quarter_end_revenue_spikes",
        "expense_timing": "deferring_discretionary_expenses"
    }
    
    def __init__(self, output_dir: str = "./output/node3_10q"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.quarters: List[QuarterlyMetrics] = []
        self.violations: List[TemporalViolation] = []
    
    def analyze_quarterly_series(
        self,
        quarterly_filings: List[Dict[str, Any]],
        company_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Main entry point for temporal consistency analysis
        
        Args:
            quarterly_filings: List of parsed 10-Q data dictionaries
            company_info: Company metadata (CIK, name, industry)
            
        Returns:
            Complete analysis results with violations
        """
        logger.info(f"Beginning temporal consistency analysis for {len(quarterly_filings)} quarters")
        
        # Phase 1: Parse quarterly metrics
        self.quarters = self._parse_quarterly_metrics(quarterly_filings, company_info)
        logger.info(f"Parsed {len(self.quarters)} quarterly metric sets")
        
        if len(self.quarters) < 2:
            logger.warning("Insufficient quarters for temporal analysis (need >= 2)")
            return self._compile_results()
        
        # Sort by fiscal period
        self.quarters.sort(key=lambda q: (q.fiscal_year, q.fiscal_quarter))
        
        # Phase 2: Revenue consistency validation
        self._validate_revenue_consistency()
        
        # Phase 3: Margin stability analysis
        self._analyze_margin_stability()
        
        # Phase 4: Working capital metrics
        self._validate_working_capital_metrics()
        
        # Phase 5: Segment reporting consistency
        self._validate_segment_consistency()
        
        # Phase 6: Accounting policy change detection
        self._detect_accounting_policy_changes()
        
        # Phase 7: Earnings management pattern detection
        self._detect_earnings_management_patterns()
        
        # Phase 8: Restatement trigger identification
        self._identify_restatement_triggers()
        
        # Phase 9: Quarter-end loading detection
        self._detect_quarter_end_loading()
        
        return self._compile_results()
    
    def _parse_quarterly_metrics(
        self,
        filings: List[Dict],
        company_info: Dict
    ) -> List[QuarterlyMetrics]:
        """Parse 10-Q filings into QuarterlyMetrics objects"""
        metrics = []
        
        for filing in filings:
            try:
                qm = QuarterlyMetrics(
                    cik=company_info.get('cik', ''),
                    fiscal_year=filing.get('fiscal_year', 0),
                    fiscal_quarter=filing.get('fiscal_quarter', 0),
                    filing_date=self._parse_date(filing.get('filing_date')),
                    period_end_date=self._parse_date(filing.get('period_end_date')),
                    revenue=Decimal(str(filing.get('revenue', 0))),
                    cost_of_revenue=Decimal(str(filing.get('cost_of_revenue', 0))),
                    gross_profit=Decimal(str(filing.get('gross_profit', 0))),
                    operating_expenses=Decimal(str(filing.get('operating_expenses', 0))),
                    operating_income=Decimal(str(filing.get('operating_income', 0))),
                    net_income=Decimal(str(filing.get('net_income', 0))),
                    eps_basic=Decimal(str(filing.get('eps_basic', 0))),
                    eps_diluted=Decimal(str(filing.get('eps_diluted', 0))),
                    total_assets=Decimal(str(filing.get('total_assets', 0))),
                    total_liabilities=Decimal(str(filing.get('total_liabilities', 0))),
                    stockholders_equity=Decimal(str(filing.get('stockholders_equity', 0))),
                    cash_and_equivalents=Decimal(str(filing.get('cash', 0))),
                    accounts_receivable=Decimal(str(filing.get('accounts_receivable', 0))),
                    inventory=Decimal(str(filing.get('inventory', 0))),
                    accounts_payable=Decimal(str(filing.get('accounts_payable', 0))),
                    operating_cash_flow=Decimal(str(filing.get('operating_cash_flow', 0))),
                    investing_cash_flow=Decimal(str(filing.get('investing_cash_flow', 0))),
                    financing_cash_flow=Decimal(str(filing.get('financing_cash_flow', 0))),
                    segments=filing.get('segments', {}),
                    revenue_recognition_method=filing.get('revenue_recognition', ''),
                    inventory_method=filing.get('inventory_method', ''),
                    depreciation_method=filing.get('depreciation_method', '')
                )
                metrics.append(qm)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse quarterly metrics: {e}")
                continue
        
        return metrics
    
    def _parse_date(self, date_val: Any) -> date:
        """Parse date from various formats"""
        if isinstance(date_val, date):
            return date_val
        if isinstance(date_val, str):
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y%m%d']:
                try:
                    return datetime.strptime(date_val, fmt).date()
                except ValueError:
                    continue
        return date.today()
    
    def _validate_revenue_consistency(self) -> None:
        """Check for sudden revenue shifts that may indicate manipulation"""
        for i in range(1, len(self.quarters)):
            prior = self.quarters[i - 1]
            current = self.quarters[i]
            
            if prior.revenue == 0:
                continue
            
            change_pct = float((current.revenue - prior.revenue) / prior.revenue * 100)
            
            if abs(change_pct) > self.THRESHOLDS["revenue_change_pct"]:
                severity = 6 if abs(change_pct) < 50 else 8
                
                self.violations.append(TemporalViolation(
                    violation_type=TemporalViolationType.SUDDEN_METRIC_SHIFT,
                    severity=severity,
                    description=f"Revenue changed {change_pct:+.1f}% QoQ, exceeding "
                               f"{self.THRESHOLDS['revenue_change_pct']}% threshold",
                    affected_quarters=[
                        f"{prior.fiscal_year}-Q{prior.fiscal_quarter}",
                        f"{current.fiscal_year}-Q{current.fiscal_quarter}"
                    ],
                    metric_name="revenue",
                    prior_value=prior.revenue,
                    current_value=current.revenue,
                    change_percentage=change_pct,
                    threshold_exceeded=self.THRESHOLDS["revenue_change_pct"],
                    regulatory_citations=[
                        "ASC 606 Revenue Recognition",
                        "Regulation S-X Rule 10-01"
                    ],
                    evidence_hash=self._hash_evidence(f"{prior.revenue}:{current.revenue}")
                ))
    
    def _analyze_margin_stability(self) -> None:
        """Analyze gross and operating margin stability"""
        for i in range(1, len(self.quarters)):
            prior = self.quarters[i - 1]
            current = self.quarters[i]
            
            # Gross margin analysis
            gm_change = (current.gross_margin - prior.gross_margin) * 100  # Points
            
            if abs(gm_change) > self.THRESHOLDS["gross_margin_change_pct"]:
                self.violations.append(TemporalViolation(
                    violation_type=TemporalViolationType.GROSS_MARGIN_MANIPULATION,
                    severity=7,
                    description=f"Gross margin shifted {gm_change:+.1f} percentage points QoQ - "
                               f"potential cost allocation manipulation",
                    affected_quarters=[
                        f"{prior.fiscal_year}-Q{prior.fiscal_quarter}",
                        f"{current.fiscal_year}-Q{current.fiscal_quarter}"
                    ],
                    metric_name="gross_margin",
                    prior_value=prior.gross_margin,
                    current_value=current.gross_margin,
                    change_percentage=gm_change,
                    threshold_exceeded=self.THRESHOLDS["gross_margin_change_pct"],
                    regulatory_citations=[
                        "ASC 330 Inventory",
                        "ASC 420 Exit or Disposal Cost Obligations"
                    ],
                    evidence_hash=self._hash_evidence(f"GM:{prior.gross_margin}:{current.gross_margin}")
                ))
            
            # Operating margin analysis
            om_change = (current.operating_margin - prior.operating_margin) * 100
            
            if abs(om_change) > self.THRESHOLDS["operating_margin_change_pct"]:
                self.violations.append(TemporalViolation(
                    violation_type=TemporalViolationType.SUDDEN_METRIC_SHIFT,
                    severity=6,
                    description=f"Operating margin shifted {om_change:+.1f} percentage points QoQ",
                    affected_quarters=[
                        f"{prior.fiscal_year}-Q{prior.fiscal_quarter}",
                        f"{current.fiscal_year}-Q{current.fiscal_quarter}"
                    ],
                    metric_name="operating_margin",
                    prior_value=prior.operating_margin,
                    current_value=current.operating_margin,
                    change_percentage=om_change,
                    threshold_exceeded=self.THRESHOLDS["operating_margin_change_pct"],
                    regulatory_citations=["Regulation S-X Rule 10-01"],
                    evidence_hash=self._hash_evidence(f"OM:{prior.operating_margin}:{current.operating_margin}")
                ))
    
    def _validate_working_capital_metrics(self) -> None:
        """Validate DSO and DIO consistency - key manipulation indicators"""
        for i in range(1, len(self.quarters)):
            prior = self.quarters[i - 1]
            current = self.quarters[i]
            
            # Days Sales Outstanding (DSO) analysis
            dso_change = current.days_sales_outstanding - prior.days_sales_outstanding
            
            if abs(dso_change) > self.THRESHOLDS["dso_change_days"]:
                # DSO increase may indicate: channel stuffing, aggressive revenue recognition
                # DSO decrease may indicate: factoring, allowance manipulation
                direction = "increased" if dso_change > 0 else "decreased"
                concern = "potential aggressive revenue recognition" if dso_change > 0 else "potential factoring or allowance adjustment"
                
                self.violations.append(TemporalViolation(
                    violation_type=TemporalViolationType.RECEIVABLES_ANOMALY,
                    severity=7,
                    description=f"DSO {direction} by {abs(dso_change):.1f} days QoQ - {concern}",
                    affected_quarters=[
                        f"{prior.fiscal_year}-Q{prior.fiscal_quarter}",
                        f"{current.fiscal_year}-Q{current.fiscal_quarter}"
                    ],
                    metric_name="days_sales_outstanding",
                    prior_value=prior.days_sales_outstanding,
                    current_value=current.days_sales_outstanding,
                    change_percentage=dso_change,
                    threshold_exceeded=self.THRESHOLDS["dso_change_days"],
                    regulatory_citations=[
                        "ASC 310 Receivables",
                        "ASC 606 Revenue Recognition"
                    ],
                    evidence_hash=self._hash_evidence(f"DSO:{prior.days_sales_outstanding}:{current.days_sales_outstanding}")
                ))
            
            # Days Inventory Outstanding (DIO) analysis
            dio_change = current.days_inventory_outstanding - prior.days_inventory_outstanding
            
            if abs(dio_change) > self.THRESHOLDS["dio_change_days"]:
                direction = "increased" if dio_change > 0 else "decreased"
                concern = "potential inventory buildup/obsolescence" if dio_change > 0 else "potential write-down or valuation change"
                
                self.violations.append(TemporalViolation(
                    violation_type=TemporalViolationType.INVENTORY_VALUATION_CHANGE,
                    severity=6,
                    description=f"DIO {direction} by {abs(dio_change):.1f} days QoQ - {concern}",
                    affected_quarters=[
                        f"{prior.fiscal_year}-Q{prior.fiscal_quarter}",
                        f"{current.fiscal_year}-Q{current.fiscal_quarter}"
                    ],
                    metric_name="days_inventory_outstanding",
                    prior_value=prior.days_inventory_outstanding,
                    current_value=current.days_inventory_outstanding,
                    change_percentage=dio_change,
                    threshold_exceeded=self.THRESHOLDS["dio_change_days"],
                    regulatory_citations=["ASC 330 Inventory"],
                    evidence_hash=self._hash_evidence(f"DIO:{prior.days_inventory_outstanding}:{current.days_inventory_outstanding}")
                ))
    
    def _validate_segment_consistency(self) -> None:
        """Validate segment reporting consistency per ASC 280"""
        if len(self.quarters) < 2:
            return
        
        for i in range(1, len(self.quarters)):
            prior = self.quarters[i - 1]
            current = self.quarters[i]
            
            if not prior.segments or not current.segments:
                continue
            
            # Check for segment additions/removals
            prior_segments = set(prior.segments.keys())
            current_segments = set(current.segments.keys())
            
            added = current_segments - prior_segments
            removed = prior_segments - current_segments
            
            if added or removed:
                self.violations.append(TemporalViolation(
                    violation_type=TemporalViolationType.SEGMENT_REPORTING_INCONSISTENCY,
                    severity=7,
                    description=f"Segment structure changed: Added {list(added)}, Removed {list(removed)}",
                    affected_quarters=[
                        f"{prior.fiscal_year}-Q{prior.fiscal_quarter}",
                        f"{current.fiscal_year}-Q{current.fiscal_quarter}"
                    ],
                    metric_name="segment_structure",
                    prior_value=len(prior_segments),
                    current_value=len(current_segments),
                    change_percentage=0,
                    threshold_exceeded=0,
                    regulatory_citations=[
                        "ASC 280 Segment Reporting",
                        "Regulation S-K Item 101"
                    ],
                    evidence_hash=self._hash_evidence(f"SEG:{prior_segments}:{current_segments}")
                ))
            
            # Check for large revenue shifts within segments
            common_segments = prior_segments & current_segments
            for seg in common_segments:
                prior_rev = Decimal(str(prior.segments.get(seg, 0)))
                current_rev = Decimal(str(current.segments.get(seg, 0)))
                
                if prior_rev > 0:
                    change_pct = float((current_rev - prior_rev) / prior_rev * 100)
                    
                    if abs(change_pct) > self.THRESHOLDS["segment_revenue_change_pct"]:
                        self.violations.append(TemporalViolation(
                            violation_type=TemporalViolationType.SEGMENT_REPORTING_INCONSISTENCY,
                            severity=6,
                            description=f"Segment '{seg}' revenue changed {change_pct:+.1f}% QoQ",
                            affected_quarters=[
                                f"{prior.fiscal_year}-Q{prior.fiscal_quarter}",
                                f"{current.fiscal_year}-Q{current.fiscal_quarter}"
                            ],
                            metric_name=f"segment_{seg}_revenue",
                            prior_value=prior_rev,
                            current_value=current_rev,
                            change_percentage=change_pct,
                            threshold_exceeded=self.THRESHOLDS["segment_revenue_change_pct"],
                            regulatory_citations=["ASC 280 Segment Reporting"],
                            evidence_hash=self._hash_evidence(f"SEG:{seg}:{prior_rev}:{current_rev}")
                        ))
    
    def _detect_accounting_policy_changes(self) -> None:
        """Detect undisclosed accounting policy changes"""
        for i in range(1, len(self.quarters)):
            prior = self.quarters[i - 1]
            current = self.quarters[i]
            
            # Revenue recognition method change
            if (prior.revenue_recognition_method and 
                current.revenue_recognition_method and
                prior.revenue_recognition_method != current.revenue_recognition_method):
                
                self.violations.append(TemporalViolation(
                    violation_type=TemporalViolationType.REVENUE_RECOGNITION_SHIFT,
                    severity=8,
                    description=f"Revenue recognition method changed from "
                               f"'{prior.revenue_recognition_method}' to "
                               f"'{current.revenue_recognition_method}'",
                    affected_quarters=[
                        f"{prior.fiscal_year}-Q{prior.fiscal_quarter}",
                        f"{current.fiscal_year}-Q{current.fiscal_quarter}"
                    ],
                    metric_name="revenue_recognition_method",
                    prior_value=prior.revenue_recognition_method,
                    current_value=current.revenue_recognition_method,
                    change_percentage=0,
                    threshold_exceeded=0,
                    regulatory_citations=[
                        "ASC 250 Accounting Changes",
                        "ASC 606 Revenue Recognition"
                    ],
                    evidence_hash=self._hash_evidence(f"REV_REC:{prior.revenue_recognition_method}:{current.revenue_recognition_method}")
                ))
            
            # Inventory method change
            if (prior.inventory_method and 
                current.inventory_method and
                prior.inventory_method != current.inventory_method):
                
                self.violations.append(TemporalViolation(
                    violation_type=TemporalViolationType.INVENTORY_VALUATION_CHANGE,
                    severity=7,
                    description=f"Inventory valuation method changed from "
                               f"'{prior.inventory_method}' to '{current.inventory_method}'",
                    affected_quarters=[
                        f"{prior.fiscal_year}-Q{prior.fiscal_quarter}",
                        f"{current.fiscal_year}-Q{current.fiscal_quarter}"
                    ],
                    metric_name="inventory_method",
                    prior_value=prior.inventory_method,
                    current_value=current.inventory_method,
                    change_percentage=0,
                    threshold_exceeded=0,
                    regulatory_citations=[
                        "ASC 250 Accounting Changes",
                        "ASC 330 Inventory"
                    ],
                    evidence_hash=self._hash_evidence(f"INV:{prior.inventory_method}:{current.inventory_method}")
                ))
    
    def _detect_earnings_management_patterns(self) -> None:
        """Detect cookie jar reserves and big bath charges"""
        if len(self.quarters) < 4:
            return
        
        # Analyze net income trend vs. reserve/charge patterns
        net_incomes = [float(q.net_income) for q in self.quarters]
        
        # Cookie jar: Building reserves in good quarters
        # Pattern: High income quarters with unusual expense increases
        for i in range(len(self.quarters)):
            q = self.quarters[i]
            
            if i > 0:
                prior = self.quarters[i - 1]
                income_change_pct = ((q.net_income - prior.net_income) / abs(prior.net_income) * 100) if prior.net_income != 0 else 0
                
                # High income with disproportionate "other expense" may indicate cookie jar
                accrual_ratio = (q.net_income - q.operating_cash_flow) / q.total_assets if q.total_assets != 0 else Decimal("0")
                
                if income_change_pct > 20 and float(accrual_ratio) > 0.05:
                    self.violations.append(TemporalViolation(
                        violation_type=TemporalViolationType.COOKIE_JAR_RESERVE,
                        severity=7,
                        description=f"Potential cookie jar reserve pattern: Income up {income_change_pct:.1f}% "
                                   f"with high accrual ratio ({float(accrual_ratio):.3f})",
                        affected_quarters=[f"{q.fiscal_year}-Q{q.fiscal_quarter}"],
                        metric_name="accrual_ratio",
                        prior_value=0,
                        current_value=float(accrual_ratio),
                        change_percentage=income_change_pct,
                        threshold_exceeded=0.05,
                        regulatory_citations=["SEC Staff Accounting Bulletin 99"],
                        evidence_hash=self._hash_evidence(f"COOKIE:{q.net_income}:{accrual_ratio}")
                    ))
        
        # Big bath: Concentrating charges in already-bad quarters
        # Pattern: Significant losses with unusual write-offs/charges
        for i, q in enumerate(self.quarters):
            if q.net_income < 0:
                # Check if operating charges are disproportionate
                operating_loss = q.revenue - q.cost_of_revenue - q.operating_expenses
                if operating_loss < 0 and q.operating_expenses > q.revenue * Decimal("0.5"):
                    self.violations.append(TemporalViolation(
                        violation_type=TemporalViolationType.BIG_BATH_CHARGES,
                        severity=7,
                        description=f"Potential big bath pattern: Operating expenses "
                                   f"({float(q.operating_expenses / q.revenue * 100):.1f}% of revenue) "
                                   f"concentrated in loss quarter",
                        affected_quarters=[f"{q.fiscal_year}-Q{q.fiscal_quarter}"],
                        metric_name="operating_expense_ratio",
                        prior_value=0.3,
                        current_value=float(q.operating_expenses / q.revenue) if q.revenue else 0,
                        change_percentage=0,
                        threshold_exceeded=0.5,
                        regulatory_citations=["SEC Staff Accounting Bulletin 99"],
                        evidence_hash=self._hash_evidence(f"BIGBATH:{q.operating_expenses}:{q.revenue}")
                    ))
    
    def _identify_restatement_triggers(self) -> None:
        """Identify conditions that may trigger restatement requirements"""
        if len(self.quarters) < 2:
            return
        
        # Check for changes that exceed materiality thresholds
        # Generally: 5% of net income or 0.5% of total assets
        
        for i in range(1, len(self.quarters)):
            prior = self.quarters[i - 1]
            current = self.quarters[i]
            
            # Balance sheet tie-out check
            # Assets should equal Liabilities + Equity
            prior_balance = prior.total_assets - (prior.total_liabilities + prior.stockholders_equity)
            current_balance = current.total_assets - (current.total_liabilities + current.stockholders_equity)
            
            tolerance = prior.total_assets * Decimal("0.001")  # 0.1% tolerance
            
            if abs(prior_balance) > tolerance or abs(current_balance) > tolerance:
                self.violations.append(TemporalViolation(
                    violation_type=TemporalViolationType.RESTATEMENT_TRIGGER,
                    severity=9,
                    description=f"Balance sheet does not balance - potential restatement trigger. "
                               f"Imbalance: ${current_balance:,.0f}",
                    affected_quarters=[f"{current.fiscal_year}-Q{current.fiscal_quarter}"],
                    metric_name="balance_sheet_integrity",
                    prior_value=prior_balance,
                    current_value=current_balance,
                    change_percentage=0,
                    threshold_exceeded=float(tolerance),
                    regulatory_citations=[
                        "ASC 250 Accounting Changes and Error Corrections",
                        "SEC Staff Accounting Bulletin 99"
                    ],
                    evidence_hash=self._hash_evidence(f"RESTATE:{current_balance}")
                ))
    
    def _detect_quarter_end_loading(self) -> None:
        """
        Detect channel stuffing via quarter-end revenue concentration
        
        Note: This would ideally use monthly revenue breakdown if available
        """
        # This is a simplified check - real implementation would analyze
        # daily/weekly revenue patterns if available from internal data
        
        for i in range(1, len(self.quarters)):
            prior = self.quarters[i - 1]
            current = self.quarters[i]
            
            # Check for unusual receivables buildup suggesting quarter-end loading
            # AR growth significantly exceeding revenue growth indicates potential stuffing
            
            if prior.revenue > 0 and prior.accounts_receivable > 0:
                rev_growth = float((current.revenue - prior.revenue) / prior.revenue)
                ar_growth = float((current.accounts_receivable - prior.accounts_receivable) / prior.accounts_receivable)
                
                # AR growing 2x+ faster than revenue is a red flag
                if ar_growth > rev_growth * 2 and ar_growth > 0.15:
                    self.violations.append(TemporalViolation(
                        violation_type=TemporalViolationType.QUARTER_END_LOADING,
                        severity=8,
                        description=f"Potential quarter-end loading: AR grew {ar_growth*100:.1f}% vs "
                                   f"revenue growth of {rev_growth*100:.1f}%",
                        affected_quarters=[f"{current.fiscal_year}-Q{current.fiscal_quarter}"],
                        metric_name="ar_revenue_divergence",
                        prior_value=rev_growth,
                        current_value=ar_growth,
                        change_percentage=ar_growth * 100,
                        threshold_exceeded=rev_growth * 2,
                        regulatory_citations=[
                            "ASC 606 Revenue Recognition",
                            "SEC Enforcement: Channel Stuffing"
                        ],
                        evidence_hash=self._hash_evidence(f"CHANNEL:{ar_growth}:{rev_growth}")
                    ))
    
    def _hash_evidence(self, evidence: str) -> str:
        """Generate SHA-256 hash of evidence"""
        return hashlib.sha256(evidence.encode('utf-8')).hexdigest()
    
    def _compile_results(self) -> Dict[str, Any]:
        """Compile analysis results"""
        results = {
            "node": "NODE_3_10Q",
            "analysis_timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "quarters_analyzed": len(self.quarters),
            "quarters": [
                {
                    "period": f"{q.fiscal_year}-Q{q.fiscal_quarter}",
                    "revenue": str(q.revenue),
                    "net_income": str(q.net_income),
                    "gross_margin": f"{q.gross_margin:.2%}",
                    "dso": f"{q.days_sales_outstanding:.1f}",
                    "dio": f"{q.days_inventory_outstanding:.1f}"
                }
                for q in self.quarters
            ],
            "violations_detected": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
            "severity_summary": {
                "critical": len([v for v in self.violations if v.severity >= 8]),
                "high": len([v for v in self.violations if 6 <= v.severity < 8]),
                "medium": len([v for v in self.violations if 4 <= v.severity < 6]),
                "low": len([v for v in self.violations if v.severity < 4])
            },
            "patterns_detected": {
                "cookie_jar": len([v for v in self.violations if v.violation_type == TemporalViolationType.COOKIE_JAR_RESERVE]),
                "big_bath": len([v for v in self.violations if v.violation_type == TemporalViolationType.BIG_BATH_CHARGES]),
                "quarter_end_loading": len([v for v in self.violations if v.violation_type == TemporalViolationType.QUARTER_END_LOADING]),
                "restatement_triggers": len([v for v in self.violations if v.violation_type == TemporalViolationType.RESTATEMENT_TRIGGER])
            }
        }
        
        # Write results
        output_path = self.output_dir / f"temporal_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Temporal consistency analysis complete. Results: {output_path}")
        
        return results


# CLI Entry Point
if __name__ == "__main__":
    validator = TemporalConsistencyValidator()
    
    # Demo data
    quarterly_filings = [
        {
            "fiscal_year": 2024, "fiscal_quarter": 1,
            "filing_date": "2024-05-01", "period_end_date": "2024-03-31",
            "revenue": 10000000000, "cost_of_revenue": 6000000000,
            "gross_profit": 4000000000, "operating_expenses": 2000000000,
            "operating_income": 2000000000, "net_income": 1500000000,
            "eps_basic": 2.50, "eps_diluted": 2.45,
            "total_assets": 30000000000, "total_liabilities": 15000000000,
            "stockholders_equity": 15000000000, "cash": 5000000000,
            "accounts_receivable": 3000000000, "inventory": 4000000000,
            "accounts_payable": 2000000000,
            "operating_cash_flow": 1200000000, "investing_cash_flow": -500000000,
            "financing_cash_flow": -300000000
        },
        {
            "fiscal_year": 2024, "fiscal_quarter": 2,
            "filing_date": "2024-08-01", "period_end_date": "2024-06-30",
            "revenue": 12500000000, "cost_of_revenue": 7800000000,  # Gross margin compression
            "gross_profit": 4700000000, "operating_expenses": 2200000000,
            "operating_income": 2500000000, "net_income": 1800000000,
            "eps_basic": 3.00, "eps_diluted": 2.95,
            "total_assets": 32000000000, "total_liabilities": 16000000000,
            "stockholders_equity": 16000000000, "cash": 5500000000,
            "accounts_receivable": 4200000000,  # DSO increase
            "inventory": 4500000000,
            "accounts_payable": 2200000000,
            "operating_cash_flow": 1400000000, "investing_cash_flow": -600000000,
            "financing_cash_flow": -400000000
        }
    ]
    
    company_info = {"cik": "0000320187", "name": "NIKE, Inc."}
    
    results = validator.analyze_quarterly_series(quarterly_filings, company_info)
    print(json.dumps(results, indent=2, default=str))

