"""
Temporal Forensic Reconciliation - Final Enhancement Module
Implements AICPA Forensic and Valuation Services and ACFE standards.
Performs inter-period reconciliation, restatement analysis, and ratio manipulation detection.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging
import statistics
import numpy as np

from src.forensics.core.integrity_manager import (
    ForensicHashChain, IntegrityLevel
)

logger = logging.getLogger(__name__)


class ReconciliationSeverity(Enum):
    """Reconciliation failure severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class RestatementType(Enum):
    """Types of financial restatements."""
    BIG_R_RESTATEMENT = "BIG_R_RESTATEMENT"  # Material, filed as 8-K
    LITTLE_R_RESTATEMENT = "LITTLE_R_RESTATEMENT"  # Revision in subsequent filing
    OUT_OF_PERIOD_ADJUSTMENT = "OUT_OF_PERIOD_ADJUSTMENT"
    ERROR_CORRECTION = "ERROR_CORRECTION"
    ACCOUNTING_CHANGE = "ACCOUNTING_CHANGE"


class RatioAnomalyType(Enum):
    """Types of ratio anomalies."""
    BENFORD_VIOLATION = "BENFORD_VIOLATION"
    STATISTICAL_OUTLIER = "STATISTICAL_OUTLIER"
    TREND_BREAK = "TREND_BREAK"
    PEER_DEVIATION = "PEER_DEVIATION"
    IMPLAUSIBLE_VALUE = "IMPLAUSIBLE_VALUE"


@dataclass
class AccountDiscrepancy:
    """Individual account balance discrepancy."""
    account_name: str
    prior_ending_balance: float
    current_beginning_balance: float
    variance: float
    variance_percentage: float
    materiality_threshold: float
    is_material: bool
    statute_implication: str
    recommended_action: str


@dataclass
class ReconciliationTest:
    """Individual reconciliation test result."""
    test_name: str
    test_type: str
    period_transition: str
    discrepancies: List[AccountDiscrepancy]
    severity: ReconciliationSeverity
    total_variance: float
    accounts_affected: int
    explanation: str
    forensic_significance: str


@dataclass
class RestatementEvent:
    """Financial restatement event."""
    restatement_type: RestatementType
    announcement_date: datetime
    periods_affected: List[str]
    accounts_restated: List[str]
    financial_impact: Dict[str, float]
    reason_stated: str
    materiality_assessment: str
    fraud_indicators: List[str]
    regulatory_consequences: List[str]
    market_reaction: Optional[float]


@dataclass
class RatioAnomaly:
    """Financial ratio anomaly detection."""
    ratio_name: str
    anomaly_type: RatioAnomalyType
    period: str
    calculated_value: float
    expected_range: Tuple[float, float]
    z_score: float
    percentile: float
    peer_comparison: Optional[float]
    benford_p_value: Optional[float]
    forensic_interpretation: str


@dataclass
class TemporalForensicAnalysis:
    """Complete temporal forensic analysis result."""
    analysis_timestamp: str
    company_cik: str
    company_name: str
    periods_analyzed: int
    date_range: Tuple[str, str]
    
    # Reconciliation results
    reconciliation_failures: List[ReconciliationTest]
    total_discrepancies: int
    material_discrepancies: int
    critical_failures: int
    
    # Restatement analysis
    restatements_identified: List[RestatementEvent]
    restatement_frequency: float
    restatement_risk_score: float
    
    # Ratio forensics
    ratio_anomalies: List[RatioAnomaly]
    benford_violations: int
    statistical_outliers: int
    trend_breaks: int
    
    # Overall assessment
    temporal_integrity_score: float  # 0-1 (1 = perfect)
    forensic_risk_level: str
    red_flags: List[str]
    recommended_investigations: List[str]
    
    # Evidence
    evidence_chain_hash: str


class TemporalForensicReconciliation:
    """
    Advanced temporal forensic reconciliation system.
    
    Implements:
    - AICPA Forensic and Valuation Services Section
    - ACFE Fraud Examiners Manual §4.601-4.650
    - PCAOB AS 2401 - Consideration of Fraud
    - AU-C Section 240 - Fraud Detection
    """
    
    def __init__(self):
        """Initialize temporal forensic reconciliation."""
        self.hash_chain = ForensicHashChain("temporal_forensic_reconciliation")
        
        # Materiality thresholds (PCAOB standards)
        self.materiality_thresholds = {
            'quantitative': 0.05,  # 5% of relevant benchmark
            'absolute': 0.01,      # $0.01 for balance reconciliation
            'accumulated': 0.03    # 3% accumulated over periods
        }
        
        # Financial ratios for analysis
        self.financial_ratios = self._initialize_ratio_definitions()
        
        # Benford's Law expected frequencies (first digit)
        self.benford_first_digit = {
            1: 0.301, 2: 0.176, 3: 0.125, 4: 0.097, 5: 0.079,
            6: 0.067, 7: 0.058, 8: 0.051, 9: 0.046
        }
        
        logger.info("TemporalForensicReconciliation initialized")
    
    def _initialize_ratio_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize financial ratio calculation definitions."""
        return {
            'current_ratio': {
                'formula': lambda d: d.get('current_assets', 0) / d.get('current_liabilities', 1),
                'normal_range': (1.0, 3.0),
                'category': 'liquidity'
            },
            'quick_ratio': {
                'formula': lambda d: (d.get('current_assets', 0) - d.get('inventory', 0)) / d.get('current_liabilities', 1),
                'normal_range': (0.5, 2.0),
                'category': 'liquidity'
            },
            'debt_to_equity': {
                'formula': lambda d: d.get('total_liabilities', 0) / d.get('total_equity', 1),
                'normal_range': (0.3, 2.0),
                'category': 'leverage'
            },
            'gross_margin': {
                'formula': lambda d: (d.get('revenue', 0) - d.get('cogs', 0)) / d.get('revenue', 1),
                'normal_range': (0.20, 0.60),
                'category': 'profitability'
            },
            'operating_margin': {
                'formula': lambda d: d.get('operating_income', 0) / d.get('revenue', 1),
                'normal_range': (0.05, 0.30),
                'category': 'profitability'
            },
            'net_margin': {
                'formula': lambda d: d.get('net_income', 0) / d.get('revenue', 1),
                'normal_range': (0.03, 0.25),
                'category': 'profitability'
            },
            'roa': {
                'formula': lambda d: d.get('net_income', 0) / d.get('total_assets', 1),
                'normal_range': (0.03, 0.20),
                'category': 'profitability'
            },
            'roe': {
                'formula': lambda d: d.get('net_income', 0) / d.get('total_equity', 1),
                'normal_range': (0.08, 0.30),
                'category': 'profitability'
            },
            'asset_turnover': {
                'formula': lambda d: d.get('revenue', 0) / d.get('total_assets', 1),
                'normal_range': (0.5, 3.0),
                'category': 'efficiency'
            },
            'inventory_turnover': {
                'formula': lambda d: d.get('cogs', 0) / d.get('inventory', 1),
                'normal_range': (2.0, 12.0),
                'category': 'efficiency'
            },
            'receivables_turnover': {
                'formula': lambda d: d.get('revenue', 0) / d.get('receivables', 1),
                'normal_range': (4.0, 15.0),
                'category': 'efficiency'
            },
            'days_sales_outstanding': {
                'formula': lambda d: (d.get('receivables', 0) / d.get('revenue', 1)) * 365,
                'normal_range': (25, 90),
                'category': 'efficiency'
            },
            'cash_conversion_cycle': {
                'formula': lambda d: ((d.get('receivables', 0) / d.get('revenue', 1)) * 365 + 
                                     (d.get('inventory', 0) / d.get('cogs', 1)) * 365 - 
                                     (d.get('payables', 0) / d.get('cogs', 1)) * 365),
                'normal_range': (30, 120),
                'category': 'efficiency'
            }
        }
    
    async def reconcile_interperiod_statements(
        self,
        periods: List[Dict[str, Any]],
        company_metadata: Optional[Dict[str, Any]] = None
    ) -> TemporalForensicAnalysis:
        """
        Comprehensive inter-period reconciliation analysis.
        
        Args:
            periods: List of period data with balances and financials
            company_metadata: Optional company information
            
        Returns:
            Complete temporal forensic analysis
        """
        logger.info(f"Starting temporal forensic reconciliation for {len(periods)} periods...")
        
        if len(periods) < 2:
            raise ValueError("Minimum 2 periods required for reconciliation")
        
        metadata = company_metadata or {}
        company_cik = metadata.get('cik', 'UNKNOWN')
        company_name = metadata.get('company_name', 'UNKNOWN')
        
        # Sort periods chronologically
        periods_sorted = sorted(periods, key=lambda x: x.get('period_date', datetime.min))
        
        # Test 1: Beginning Balance Consistency
        logger.info("Test 1: Beginning Balance Consistency...")
        reconciliation_tests = await self._test_beginning_balance_consistency(periods_sorted)
        
        # Test 2: Restatement Pattern Analysis
        logger.info("Test 2: Restatement Pattern Analysis...")
        restatement_analysis = await self._analyze_restatement_patterns(periods_sorted)
        
        # Test 3: Ratio Stability Analysis
        logger.info("Test 3: Ratio Manipulation Detection...")
        ratio_anomalies = await self._detect_ratio_manipulation(periods_sorted)
        
        # Test 4: Benford's Law Analysis
        logger.info("Test 4: Benford's Law Conformance...")
        benford_results = await self._apply_benfords_law(periods_sorted)
        
        # Test 5: Trend Break Detection
        logger.info("Test 5: Trend Break Analysis...")
        trend_breaks = await self._detect_trend_breaks(periods_sorted)
        
        # Combine all anomalies
        all_anomalies = ratio_anomalies + benford_results + trend_breaks
        
        # Calculate aggregate metrics
        total_discrepancies = sum(len(test.discrepancies) for test in reconciliation_tests)
        material_discrepancies = sum(
            len([d for d in test.discrepancies if d.is_material])
            for test in reconciliation_tests
        )
        critical_failures = sum(
            1 for test in reconciliation_tests 
            if test.severity == ReconciliationSeverity.CRITICAL
        )
        
        # Restatement metrics
        restatement_frequency = len(restatement_analysis) / len(periods) if periods else 0
        restatement_risk = self._calculate_restatement_risk(restatement_analysis)
        
        # Anomaly counts
        benford_violations = sum(
            1 for a in all_anomalies 
            if a.anomaly_type == RatioAnomalyType.BENFORD_VIOLATION
        )
        statistical_outliers = sum(
            1 for a in all_anomalies 
            if a.anomaly_type == RatioAnomalyType.STATISTICAL_OUTLIER
        )
        trend_break_count = sum(
            1 for a in all_anomalies 
            if a.anomaly_type == RatioAnomalyType.TREND_BREAK
        )
        
        # Calculate temporal integrity score
        integrity_score = self._calculate_temporal_integrity(
            total_discrepancies,
            material_discrepancies,
            len(restatement_analysis),
            len(all_anomalies)
        )
        
        # Determine forensic risk level
        risk_level = self._determine_risk_level(
            integrity_score,
            critical_failures,
            restatement_frequency
        )
        
        # Identify red flags
        red_flags = self._identify_red_flags(
            reconciliation_tests,
            restatement_analysis,
            all_anomalies
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            reconciliation_tests,
            restatement_analysis,
            all_anomalies,
            risk_level
        )
        
        # Date range
        date_range = (
            periods_sorted[0].get('period', 'UNKNOWN'),
            periods_sorted[-1].get('period', 'UNKNOWN')
        )
        
        # Create analysis result
        analysis = TemporalForensicAnalysis(
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            company_cik=company_cik,
            company_name=company_name,
            periods_analyzed=len(periods),
            date_range=date_range,
            reconciliation_failures=reconciliation_tests,
            total_discrepancies=total_discrepancies,
            material_discrepancies=material_discrepancies,
            critical_failures=critical_failures,
            restatements_identified=restatement_analysis,
            restatement_frequency=restatement_frequency,
            restatement_risk_score=restatement_risk,
            ratio_anomalies=all_anomalies,
            benford_violations=benford_violations,
            statistical_outliers=statistical_outliers,
            trend_breaks=trend_break_count,
            temporal_integrity_score=integrity_score,
            forensic_risk_level=risk_level,
            red_flags=red_flags,
            recommended_investigations=recommendations,
            evidence_chain_hash=self.hash_chain.blocks[-1].current_hash if self.hash_chain.blocks else ""
        )
        
        # Log to hash chain
        await self.hash_chain.add_evidence(
            data={
                "action": "reconcile_interperiod_statements",
                "company_cik": company_cik,
                "periods_analyzed": len(periods),
                "discrepancies_found": total_discrepancies,
                "restatements_found": len(restatement_analysis),
                "anomalies_detected": len(all_anomalies),
                "integrity_score": integrity_score,
                "risk_level": risk_level,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            integrity_level=IntegrityLevel.CRITICAL
        )
        
        logger.info(
            f"Temporal reconciliation complete: {total_discrepancies} discrepancies, "
            f"{len(restatement_analysis)} restatements, {len(all_anomalies)} anomalies, "
            f"integrity: {integrity_score:.2%}, risk: {risk_level}"
        )
        
        return analysis
    
    async def _test_beginning_balance_consistency(
        self,
        periods: List[Dict[str, Any]]
    ) -> List[ReconciliationTest]:
        """
        Test beginning balance consistency across periods.
        ACFE §4.601 - Inter-period Reconciliation
        """
        reconciliation_tests = []
        
        for i in range(1, len(periods)):
            prior_period = periods[i-1]
            current_period = periods[i]
            
            prior_ending = prior_period.get('ending_balances', {})
            current_beginning = current_period.get('beginning_balances', {})
            
            discrepancies = []
            total_variance = 0.0
            
            # Check each account
            for account in prior_ending:
                if account in current_beginning:
                    prior_bal = prior_ending[account]
                    current_bal = current_beginning[account]
                    diff = abs(prior_bal - current_bal)
                    
                    # Calculate variance percentage
                    if prior_bal != 0:
                        variance_pct = (diff / abs(prior_bal)) * 100
                    else:
                        variance_pct = 100.0 if diff > 0 else 0.0
                    
                    # Check materiality
                    is_material = diff > self.materiality_thresholds['absolute']
                    
                    if diff > self.materiality_thresholds['absolute']:
                        total_variance += diff
                        
                        discrepancy = AccountDiscrepancy(
                            account_name=account,
                            prior_ending_balance=prior_bal,
                            current_beginning_balance=current_bal,
                            variance=diff,
                            variance_percentage=variance_pct,
                            materiality_threshold=self.materiality_thresholds['absolute'],
                            is_material=is_material,
                            statute_implication='15 USC § 78m(b)(2)(B) - Internal Accounting Controls',
                            recommended_action='Investigate period transition and journal entries'
                        )
                        
                        discrepancies.append(discrepancy)
            
            # Create test result if discrepancies found
            if discrepancies:
                # Determine severity
                if len(discrepancies) >= 5 or total_variance > 1000000:
                    severity = ReconciliationSeverity.CRITICAL
                elif len(discrepancies) >= 3 or total_variance > 100000:
                    severity = ReconciliationSeverity.HIGH
                elif total_variance > 10000:
                    severity = ReconciliationSeverity.MEDIUM
                else:
                    severity = ReconciliationSeverity.LOW
                
                test = ReconciliationTest(
                    test_name='Beginning Balance Consistency',
                    test_type='INTER_PERIOD_RECONCILIATION',
                    period_transition=f"{prior_period.get('period', 'UNKNOWN')} -> {current_period.get('period', 'UNKNOWN')}",
                    discrepancies=discrepancies,
                    severity=severity,
                    total_variance=total_variance,
                    accounts_affected=len(discrepancies),
                    explanation=(
                        f"Beginning balances do not match prior period ending balances. "
                        f"{len(discrepancies)} accounts show variances totaling ${total_variance:,.2f}"
                    ),
                    forensic_significance=(
                        "Discrepancies between period-end and period-start balances may indicate "
                        "unauthorized adjustments, posting errors, or deliberate manipulation. "
                        "PCAOB AS 2401 requires investigation of unexplained differences."
                    )
                )
                
                reconciliation_tests.append(test)
        
        return reconciliation_tests
    
    async def _analyze_restatement_patterns(
        self,
        periods: List[Dict[str, Any]]
    ) -> List[RestatementEvent]:
        """
        Analyze restatement patterns and frequency.
        ACFE §4.610 - Restatement Analysis
        """
        restatements = []
        
        for i, period in enumerate(periods):
            # Check for restatement indicators
            is_restated = period.get('is_restated', False)
            restatement_data = period.get('restatement_data', {})
            
            if is_restated and restatement_data:
                # Determine restatement type
                if restatement_data.get('filed_8k', False):
                    restat_type = RestatementType.BIG_R_RESTATEMENT
                elif restatement_data.get('prior_period_adjustment', False):
                    restat_type = RestatementType.OUT_OF_PERIOD_ADJUSTMENT
                elif restatement_data.get('accounting_change', False):
                    restat_type = RestatementType.ACCOUNTING_CHANGE
                elif restatement_data.get('error_correction', False):
                    restat_type = RestatementType.ERROR_CORRECTION
                else:
                    restat_type = RestatementType.LITTLE_R_RESTATEMENT
                
                # Extract restated accounts
                accounts_restated = restatement_data.get('accounts_affected', [])
                
                # Calculate financial impact
                financial_impact = {}
                for account in accounts_restated:
                    original = restatement_data.get(f'{account}_original', 0)
                    restated = restatement_data.get(f'{account}_restated', 0)
                    financial_impact[account] = restated - original
                
                # Identify fraud indicators
                fraud_indicators = []
                
                if restat_type == RestatementType.BIG_R_RESTATEMENT:
                    fraud_indicators.append("Material restatement requiring 8-K filing")
                
                if 'revenue' in accounts_restated:
                    fraud_indicators.append("Revenue restatement - high fraud risk")
                
                if len(accounts_restated) > 3:
                    fraud_indicators.append("Multiple accounts restated - systematic issue")
                
                total_impact = sum(abs(v) for v in financial_impact.values())
                if total_impact > 10000000:  # $10M threshold
                    fraud_indicators.append(f"Material financial impact: ${total_impact:,.0f}")
                
                # Regulatory consequences
                consequences = []
                if restat_type == RestatementType.BIG_R_RESTATEMENT:
                    consequences.append("SEC investigation likely")
                    consequences.append("Potential SOX 404 control deficiency")
                
                if 'revenue' in accounts_restated or 'net_income' in accounts_restated:
                    consequences.append("Possible violation of 15 USC § 78m(a)")
                
                # Create restatement event
                restatement = RestatementEvent(
                    restatement_type=restat_type,
                    announcement_date=period.get('restatement_date', datetime.now(timezone.utc)),
                    periods_affected=[period.get('period', 'UNKNOWN')],
                    accounts_restated=accounts_restated,
                    financial_impact=financial_impact,
                    reason_stated=restatement_data.get('reason', 'Not disclosed'),
                    materiality_assessment=self._assess_materiality(financial_impact, period),
                    fraud_indicators=fraud_indicators,
                    regulatory_consequences=consequences,
                    market_reaction=restatement_data.get('stock_price_impact')
                )
                
                restatements.append(restatement)
        
        return restatements
    
    def _assess_materiality(
        self,
        financial_impact: Dict[str, float],
        period: Dict[str, Any]
    ) -> str:
        """Assess materiality of restatement."""
        total_impact = sum(abs(v) for v in financial_impact.values())
        revenue = period.get('revenue', 1)
        net_income = period.get('net_income', 1)
        total_assets = period.get('total_assets', 1)
        
        # SEC SAB 99 materiality guidance
        if total_impact / revenue > 0.05:
            return "MATERIAL - Exceeds 5% of revenue (SAB 99)"
        elif total_impact / abs(net_income) > 0.10 if net_income != 0 else False:
            return "MATERIAL - Exceeds 10% of net income (SAB 99)"
        elif total_impact / total_assets > 0.01:
            return "MATERIAL - Exceeds 1% of total assets"
        else:
            return "IMMATERIAL - Below quantitative thresholds"
    
    async def _detect_ratio_manipulation(
        self,
        periods: List[Dict[str, Any]]
    ) -> List[RatioAnomaly]:
        """
        Detect financial ratio manipulation and anomalies.
        ACFE §4.620 - Ratio Analysis
        """
        anomalies = []
        
        # Calculate ratios for each period
        period_ratios = []
        for period in periods:
            ratios = {}
            for ratio_name, ratio_def in self.financial_ratios.items():
                try:
                    ratios[ratio_name] = ratio_def['formula'](period)
                except (ZeroDivisionError, KeyError):
                    ratios[ratio_name] = None
            
            period_ratios.append({
                'period': period.get('period', 'UNKNOWN'),
                'ratios': ratios
            })
        
        # Analyze each ratio across time
        for ratio_name in self.financial_ratios.keys():
            ratio_values = [
                pr['ratios'][ratio_name] 
                for pr in period_ratios 
                if pr['ratios'][ratio_name] is not None
            ]
            
            if len(ratio_values) < 2:
                continue
            
            # Calculate statistics
            mean_val = statistics.mean(ratio_values)
            if len(ratio_values) > 1:
                stdev_val = statistics.stdev(ratio_values)
            else:
                stdev_val = 0
            
            # Check each period
            for i, period_ratio in enumerate(period_ratios):
                value = period_ratio['ratios'][ratio_name]
                
                if value is None:
                    continue
                
                period_name = period_ratio['period']
                normal_range = self.financial_ratios[ratio_name]['normal_range']
                
                # Calculate Z-score
                if stdev_val > 0:
                    z_score = (value - mean_val) / stdev_val
                else:
                    z_score = 0
                
                # Check for anomalies
                is_outlier = abs(z_score) > 2.5  # 2.5 standard deviations
                outside_normal = value < normal_range[0] or value > normal_range[1]
                
                if is_outlier or outside_normal:
                    # Determine anomaly type
                    if is_outlier:
                        anomaly_type = RatioAnomalyType.STATISTICAL_OUTLIER
                    elif outside_normal:
                        anomaly_type = RatioAnomalyType.IMPLAUSIBLE_VALUE
                    else:
                        anomaly_type = RatioAnomalyType.PEER_DEVIATION
                    
                    # Forensic interpretation
                    interpretation = self._interpret_ratio_anomaly(
                        ratio_name,
                        value,
                        normal_range,
                        z_score
                    )
                    
                    anomaly = RatioAnomaly(
                        ratio_name=ratio_name,
                        anomaly_type=anomaly_type,
                        period=period_name,
                        calculated_value=value,
                        expected_range=normal_range,
                        z_score=z_score,
                        percentile=self._calculate_percentile(value, ratio_values),
                        peer_comparison=None,  # Would compare to industry in production
                        benford_p_value=None,
                        forensic_interpretation=interpretation
                    )
                    
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _interpret_ratio_anomaly(
        self,
        ratio_name: str,
        value: float,
        normal_range: Tuple[float, float],
        z_score: float
    ) -> str:
        """Generate forensic interpretation of ratio anomaly."""
        if ratio_name in ['gross_margin', 'operating_margin', 'net_margin']:
            if value > normal_range[1]:
                return f"Abnormally high {ratio_name} ({value:.2%}) may indicate revenue overstatement or expense understatement"
            else:
                return f"Abnormally low {ratio_name} ({value:.2%}) may indicate expense manipulation or revenue quality issues"
        
        elif ratio_name == 'days_sales_outstanding':
            if value > normal_range[1]:
                return f"Excessive DSO ({value:.1f} days) suggests receivables overstatement or channel stuffing"
            else:
                return f"Unusually low DSO ({value:.1f} days) may indicate aggressive cash collection or timing manipulation"
        
        elif ratio_name in ['current_ratio', 'quick_ratio']:
            if value < normal_range[0]:
                return f"Low {ratio_name} ({value:.2f}) indicates liquidity stress or liability understatement"
            else:
                return f"High {ratio_name} ({value:.2f}) may indicate asset overvaluation"
        
        else:
            return f"{ratio_name} value {value:.3f} is {abs(z_score):.1f} standard deviations from mean"
    
    def _calculate_percentile(self, value: float, all_values: List[float]) -> float:
        """Calculate percentile rank of value in distribution."""
        if not all_values:
            return 50.0
        
        sorted_vals = sorted(all_values)
        position = sum(1 for v in sorted_vals if v < value)
        
        return (position / len(sorted_vals)) * 100
    
    async def _apply_benfords_law(
        self,
        periods: List[Dict[str, Any]]
    ) -> List[RatioAnomaly]:
        """
        Apply Benford's Law to detect number manipulation.
        ACFE §4.625 - Digital Analysis
        """
        anomalies = []
        
        # Extract financial figures (revenue, expenses, assets, etc.)
        financial_figures = []
        for period in periods:
            figures = [
                period.get('revenue', 0),
                period.get('cogs', 0),
                period.get('operating_expenses', 0),
                period.get('net_income', 0),
                period.get('total_assets', 0),
                period.get('total_liabilities', 0),
                period.get('cash', 0),
                period.get('receivables', 0),
                period.get('inventory', 0)
            ]
            financial_figures.extend([f for f in figures if f > 0])
        
        if len(financial_figures) < 30:  # Benford needs sufficient sample
            return anomalies
        
        # Count first digit frequencies
        first_digit_counts = {i: 0 for i in range(1, 10)}
        
        for figure in financial_figures:
            first_digit = int(str(abs(int(figure)))[0])
            if first_digit in first_digit_counts:
                first_digit_counts[first_digit] += 1
        
        # Calculate observed frequencies
        total_numbers = sum(first_digit_counts.values())
        observed_freq = {
            d: count / total_numbers 
            for d, count in first_digit_counts.items()
        }
        
        # Chi-square test for Benford conformance
        chi_square = 0
        for digit in range(1, 10):
            expected = self.benford_first_digit[digit] * total_numbers
            observed = first_digit_counts[digit]
            chi_square += ((observed - expected) ** 2) / expected
        
        # Critical value for chi-square (8 df, α=0.05) is 15.507
        p_value = 1.0 / (1.0 + chi_square / 15.507)  # Simplified p-value approximation
        
        # Check for significant deviation
        if chi_square > 15.507:  # p < 0.05
            anomaly = RatioAnomaly(
                ratio_name='benford_law_conformance',
                anomaly_type=RatioAnomalyType.BENFORD_VIOLATION,
                period='ALL_PERIODS',
                calculated_value=chi_square,
                expected_range=(0, 15.507),
                z_score=0,
                percentile=0,
                peer_comparison=None,
                benford_p_value=p_value,
                forensic_interpretation=(
                    f"Financial figures deviate significantly from Benford's Law "
                    f"(χ²={chi_square:.2f}, p={p_value:.3f}). This may indicate "
                    f"number manipulation, fabrication, or selective rounding. "
                    f"Most non-conformant digits: " + 
                    ", ".join([
                        f"{d}({observed_freq[d]:.1%} vs {self.benford_first_digit[d]:.1%})" 
                        for d in sorted(range(1, 10), 
                                      key=lambda x: abs(observed_freq[x] - self.benford_first_digit[x]), 
                                      reverse=True)[:3]
                    ])
                )
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_trend_breaks(
        self,
        periods: List[Dict[str, Any]]
    ) -> List[RatioAnomaly]:
        """
        Detect sudden trend breaks in financial metrics.
        ACFE §4.630 - Trend Analysis
        """
        anomalies = []
        
        # Metrics to analyze for trends
        trend_metrics = [
            'revenue', 'gross_profit', 'operating_income', 'net_income',
            'total_assets', 'receivables', 'inventory', 'cash'
        ]
        
        for metric in trend_metrics:
            values = [p.get(metric, 0) for p in periods if p.get(metric) is not None]
            
            if len(values) < 4:  # Need at least 4 periods
                continue
            
            # Calculate period-over-period growth rates
            growth_rates = []
            for i in range(1, len(values)):
                if values[i-1] != 0:
                    growth = (values[i] - values[i-1]) / abs(values[i-1])
                    growth_rates.append(growth)
            
            if len(growth_rates) < 3:
                continue
            
            # Detect trend breaks (sudden changes in growth rate)
            for i in range(1, len(growth_rates)):
                prior_growth = growth_rates[i-1]
                current_growth = growth_rates[i]
                
                # Check for significant change
                if abs(prior_growth) > 0.01:  # Avoid division by near-zero
                    growth_change = abs((current_growth - prior_growth) / prior_growth)
                else:
                    growth_change = abs(current_growth - prior_growth)
                
                # Trend break threshold: >100% change in growth rate
                if growth_change > 1.0:
                    period_idx = i + 1  # Adjust for indexing
                    
                    anomaly = RatioAnomaly(
                        ratio_name=f'{metric}_growth_trend',
                        anomaly_type=RatioAnomalyType.TREND_BREAK,
                        period=periods[period_idx].get('period', 'UNKNOWN'),
                        calculated_value=current_growth,
                        expected_range=(prior_growth * 0.5, prior_growth * 1.5),
                        z_score=0,
                        percentile=0,
                        peer_comparison=None,
                        benford_p_value=None,
                        forensic_interpretation=(
                            f"Significant trend break in {metric} growth. "
                            f"Prior growth: {prior_growth:.1%}, Current growth: {current_growth:.1%}. "
                            f"Change of {growth_change:.0%} may indicate accounting manipulation, "
                            f"one-time events, or business model changes requiring investigation."
                        )
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _calculate_temporal_integrity(
        self,
        total_discrepancies: int,
        material_discrepancies: int,
        restatement_count: int,
        anomaly_count: int
    ) -> float:
        """
        Calculate overall temporal integrity score.
        Score ranges from 0 (poor) to 1 (perfect).
        """
        # Base score starts at 1.0
        score = 1.0
        
        # Deduct for discrepancies
        score -= min(total_discrepancies * 0.02, 0.30)
        score -= min(material_discrepancies * 0.05, 0.25)
        
        # Deduct for restatements
        score -= min(restatement_count * 0.10, 0.30)
        
        # Deduct for anomalies
        score -= min(anomaly_count * 0.01, 0.15)
        
        return max(0.0, score)
    
    def _calculate_restatement_risk(
        self,
        restatements: List[RestatementEvent]
    ) -> float:
        """Calculate restatement risk score (0-1)."""
        if not restatements:
            return 0.0
        
        risk = 0.0
        
        for restatement in restatements:
            # Big R restatements are highest risk
            if restatement.restatement_type == RestatementType.BIG_R_RESTATEMENT:
                risk += 0.40
            elif restatement.restatement_type == RestatementType.ERROR_CORRECTION:
                risk += 0.20
            else:
                risk += 0.10
            
            # Revenue restatements add risk
            if 'revenue' in restatement.accounts_restated:
                risk += 0.15
            
            # Multiple accounts add risk
            if len(restatement.accounts_restated) > 3:
                risk += 0.10
        
        return min(risk, 1.0)
    
    def _determine_risk_level(
        self,
        integrity_score: float,
        critical_failures: int,
        restatement_frequency: float
    ) -> str:
        """Determine overall forensic risk level."""
        if integrity_score < 0.50 or critical_failures >= 3 or restatement_frequency > 0.30:
            return "CRITICAL"
        elif integrity_score < 0.70 or critical_failures >= 2 or restatement_frequency > 0.20:
            return "HIGH"
        elif integrity_score < 0.85 or critical_failures >= 1 or restatement_frequency > 0.10:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _identify_red_flags(
        self,
        reconciliation_tests: List[ReconciliationTest],
        restatements: List[RestatementEvent],
        anomalies: List[RatioAnomaly]
    ) -> List[str]:
        """Identify red flags from analysis."""
        red_flags = []
        
        # Reconciliation red flags
        critical_tests = [t for t in reconciliation_tests if t.severity == ReconciliationSeverity.CRITICAL]
        if critical_tests:
            red_flags.append(
                f"🚨 {len(critical_tests)} CRITICAL reconciliation failures - systematic control deficiency"
            )
        
        # Restatement red flags
        big_r_restatements = [
            r for r in restatements 
            if r.restatement_type == RestatementType.BIG_R_RESTATEMENT
        ]
        if big_r_restatements:
            red_flags.append(
                f"🚨 {len(big_r_restatements)} material restatements (Big R) - potential fraud indicator"
            )
        
        revenue_restatements = [
            r for r in restatements 
            if 'revenue' in r.accounts_restated
        ]
        if revenue_restatements:
            red_flags.append(
                f"🚨 Revenue restated in {len(revenue_restatements)} periods - high fraud risk"
            )
        
        # Anomaly red flags
        benford_violations = [
            a for a in anomalies 
            if a.anomaly_type == RatioAnomalyType.BENFORD_VIOLATION
        ]
        if benford_violations:
            red_flags.append(
                "🚨 Benford's Law violation - possible number manipulation or fabrication"
            )
        
        trend_breaks = [
            a for a in anomalies 
            if a.anomaly_type == RatioAnomalyType.TREND_BREAK
        ]
        if len(trend_breaks) >= 3:
            red_flags.append(
                f"⚠️ {len(trend_breaks)} significant trend breaks - investigate business changes"
            )
        
        statistical_outliers = [
            a for a in anomalies 
            if a.anomaly_type == RatioAnomalyType.STATISTICAL_OUTLIER
        ]
        if len(statistical_outliers) >= 5:
            red_flags.append(
                f"⚠️ {len(statistical_outliers)} statistical outliers - ratio manipulation possible"
            )
        
        return red_flags
    
    def _generate_recommendations(
        self,
        reconciliation_tests: List[ReconciliationTest],
        restatements: List[RestatementEvent],
        anomalies: List[RatioAnomaly],
        risk_level: str
    ) -> List[str]:
        """Generate investigation recommendations."""
        recommendations = []
        
        if risk_level == "CRITICAL":
            recommendations.append(
                "IMMEDIATE: Engage forensic accounting firm for comprehensive investigation"
            )
            recommendations.append(
                "REQUIRED: Notify audit committee and independent auditors"
            )
        elif risk_level == "HIGH":
            recommendations.append(
                "HIGH PRIORITY: Conduct detailed review of accounting policies and controls"
            )
        
        # Specific recommendations based on findings
        if reconciliation_tests:
            recommendations.append(
                "ACTION: Review general ledger and journal entries for period transitions"
            )
        
        if restatements:
            recommendations.append(
                "ACTION: Analyze root cause of restatements and implement corrective controls"
            )
            recommendations.append(
                "ACTION: Assess SOX 404 control deficiencies and remediation plan"
            )
        
        benford_violations = [
            a for a in anomalies 
            if a.anomaly_type == RatioAnomalyType.BENFORD_VIOLATION
        ]
        if benford_violations:
            recommendations.append(
                "ACTION: Detailed testing of transaction populations for authenticity"
            )
        
        trend_breaks = [
            a for a in anomalies 
            if a.anomaly_type == RatioAnomalyType.TREND_BREAK
        ]
        if trend_breaks:
            recommendations.append(
                "ACTION: Investigate business events and accounting policy changes"
            )
        
        recommendations.append(
            "ONGOING: Implement continuous monitoring of reconciliation processes"
        )
        
        return recommendations
    
    async def verify_integrity(self) -> bool:
        """Verify hash chain integrity."""
        is_valid = await self.hash_chain.verify_chain()
        
        if not is_valid:
            logger.critical("Temporal forensic reconciliation hash chain integrity violation!")
        
        return is_valid


# Backward compatibility exports
__all__ = [
    'TemporalForensicReconciliation',
    'ReconciliationSeverity',
    'RestatementType',
    'RatioAnomalyType',
    'AccountDiscrepancy',
    'ReconciliationTest',
    'RestatementEvent',
    'RatioAnomaly',
    'TemporalForensicAnalysis'
]

