"""
NODE 13: Altman Z-Score Bankruptcy Predictor
============================================

Implements Altman's Z-Score model variants for bankruptcy prediction:
- Z-Score: Original for public manufacturing companies
- Z'-Score: Modified for private companies  
- Z''-Score: Modified for non-manufacturing companies

Academic Reference: Altman, E.I. (1968) "Financial Ratios, Discriminant Analysis 
and the Prediction of Corporate Bankruptcy"

Classification Thresholds (Original Z-Score):
- Z > 2.99: Safe Zone
- 1.81 < Z < 2.99: Gray Zone
- Z < 1.81: Distress Zone (bankruptcy likely within 2 years)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import hashlib
import logging
import warnings

warnings.warn(
    f"{__name__} (V1) is deprecated and will be removed in a future release. "
    f"Use {__name__}_v2 instead.",
    DeprecationWarning,
    stacklevel=2
)

logger = logging.getLogger(__name__)


class ZScoreVariant(Enum):
    Z = "Z (Public Manufacturing)"
    Z_PRIME = "Z' (Private Companies)"
    Z_DOUBLE_PRIME = "Z'' (Non-Manufacturing)"


class ZoneClassification(Enum):
    SAFE = "Safe Zone"
    GRAY = "Gray Zone"
    DISTRESS = "Distress Zone"


class BankruptcyAlertType(Enum):
    DISTRESS_ZONE = "Entered Distress Zone"
    GRAY_ZONE_ENTRY = "Entered Gray Zone"
    RAPID_DETERIORATION = "Rapid Deterioration"
    BANKRUPTCY_IMMINENT = "Bankruptcy Imminent"


@dataclass
class FinancialInputs:
    """Financial inputs for Z-Score calculation."""
    # Balance Sheet
    current_assets: float
    current_liabilities: float
    total_assets: float
    total_liabilities: float
    retained_earnings: float
    
    # Income Statement
    ebit: float  # Earnings Before Interest and Taxes
    sales: float
    
    # Market Data (for Z-Score)
    market_cap: Optional[float] = None
    book_value_equity: Optional[float] = None
    
    # Metadata
    fiscal_period: str = ""
    company_type: str = "PUBLIC_MANUFACTURING"


@dataclass
class ZScoreComponents:
    """Individual Z-Score component ratios."""
    x1_working_capital_ratio: float  # Working Capital / Total Assets
    x2_retained_earnings_ratio: float  # Retained Earnings / Total Assets
    x3_ebit_ratio: float  # EBIT / Total Assets
    x4_equity_debt_ratio: float  # Market/Book Value of Equity / Total Liabilities
    x5_sales_ratio: float  # Sales / Total Assets
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "X1 (Working Capital/Assets)": round(self.x1_working_capital_ratio, 4),
            "X2 (Retained Earnings/Assets)": round(self.x2_retained_earnings_ratio, 4),
            "X3 (EBIT/Assets)": round(self.x3_ebit_ratio, 4),
            "X4 (Equity/Liabilities)": round(self.x4_equity_debt_ratio, 4),
            "X5 (Sales/Assets)": round(self.x5_sales_ratio, 4)
        }


@dataclass
class ZScoreResult:
    """Complete Z-Score calculation result."""
    score: float
    variant: ZScoreVariant
    classification: ZoneClassification
    components: ZScoreComponents
    interpretation: str
    bankruptcy_probability: str
    evidence_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "z_score": round(self.score, 4),
            "variant": self.variant.value,
            "classification": self.classification.value,
            "components": self.components.to_dict(),
            "interpretation": self.interpretation,
            "bankruptcy_probability": self.bankruptcy_probability
        }


@dataclass
class BankruptcyAlert:
    """Alert for bankruptcy risk detection."""
    alert_type: BankruptcyAlertType
    company_id: str
    company_name: str
    current_z_score: float
    previous_z_score: Optional[float]
    z_score_change: Optional[float]
    classification: ZoneClassification
    risk_indicators: List[str]
    time_horizon: str
    evidence_hash: str
    severity: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "company": self.company_name,
            "current_z_score": round(self.current_z_score, 4),
            "previous_z_score": round(self.previous_z_score, 4) if self.previous_z_score else None,
            "z_score_change": round(self.z_score_change, 4) if self.z_score_change else None,
            "classification": self.classification.value,
            "risk_indicators": self.risk_indicators,
            "time_horizon": self.time_horizon,
            "severity": self.severity
        }


@dataclass
class Node13Output:
    """Output from Node 13 analysis."""
    companies_analyzed: int
    distress_zone_count: int
    gray_zone_count: int
    alerts: List[BankruptcyAlert]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "companies_analyzed": self.companies_analyzed,
                "distress_zone": self.distress_zone_count,
                "gray_zone": self.gray_zone_count,
                "safe_zone": self.companies_analyzed - self.distress_zone_count - self.gray_zone_count
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class BankruptcyPredictor:
    """
    Altman Z-Score Bankruptcy Predictor.
    
    Implements three variants:
    1. Z-Score (Original): For public manufacturing companies
    2. Z'-Score (Model A): For private companies
    3. Z''-Score (Model B): For non-manufacturing companies
    
    Formula (Original Z-Score):
    Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 0.999*X5
    """
    
    # Coefficients for each variant
    COEFFICIENTS = {
        ZScoreVariant.Z: {'x1': 1.2, 'x2': 1.4, 'x3': 3.3, 'x4': 0.6, 'x5': 0.999},
        ZScoreVariant.Z_PRIME: {'x1': 0.717, 'x2': 0.847, 'x3': 3.107, 'x4': 0.420, 'x5': 0.998},
        ZScoreVariant.Z_DOUBLE_PRIME: {'x1': 6.56, 'x2': 3.26, 'x3': 6.72, 'x4': 1.05, 'x5': 0}
    }
    
    # Thresholds for each variant
    THRESHOLDS = {
        ZScoreVariant.Z: {'safe': 2.99, 'distress': 1.81},
        ZScoreVariant.Z_PRIME: {'safe': 2.90, 'distress': 1.23},
        ZScoreVariant.Z_DOUBLE_PRIME: {'safe': 2.60, 'distress': 1.10}
    }
    
    def __init__(self):
        pass
    
    def calculate_z_score(self, inputs: FinancialInputs) -> ZScoreResult:
        """
        Calculate Z-Score based on company type.
        
        Args:
            inputs: FinancialInputs with all required metrics
            
        Returns:
            ZScoreResult with score, classification, and interpretation
        """
        # Determine variant based on company type
        if inputs.company_type == 'PUBLIC_MANUFACTURING' and inputs.market_cap:
            variant = ZScoreVariant.Z
        elif inputs.company_type == 'NON_MANUFACTURING':
            variant = ZScoreVariant.Z_DOUBLE_PRIME
        else:
            variant = ZScoreVariant.Z_PRIME
        
        # Calculate component ratios
        working_capital = inputs.current_assets - inputs.current_liabilities
        x1 = working_capital / inputs.total_assets if inputs.total_assets else 0
        x2 = inputs.retained_earnings / inputs.total_assets if inputs.total_assets else 0
        x3 = inputs.ebit / inputs.total_assets if inputs.total_assets else 0
        x5 = inputs.sales / inputs.total_assets if inputs.total_assets else 0
        
        # X4 depends on variant
        if variant == ZScoreVariant.Z and inputs.market_cap:
            x4 = inputs.market_cap / inputs.total_liabilities if inputs.total_liabilities else 0
        else:
            book_equity = inputs.book_value_equity or (inputs.total_assets - inputs.total_liabilities)
            x4 = book_equity / inputs.total_liabilities if inputs.total_liabilities else 0
        
        components = ZScoreComponents(
            x1_working_capital_ratio=x1,
            x2_retained_earnings_ratio=x2,
            x3_ebit_ratio=x3,
            x4_equity_debt_ratio=x4,
            x5_sales_ratio=x5
        )
        
        # Calculate Z-Score
        coef = self.COEFFICIENTS[variant]
        score = (
            coef['x1'] * x1 +
            coef['x2'] * x2 +
            coef['x3'] * x3 +
            coef['x4'] * x4 +
            coef['x5'] * x5
        )
        
        # Classify
        thresholds = self.THRESHOLDS[variant]
        if score > thresholds['safe']:
            classification = ZoneClassification.SAFE
            interpretation = 'Company is financially healthy with low bankruptcy risk'
            probability = '<5% within 2 years'
        elif score < thresholds['distress']:
            classification = ZoneClassification.DISTRESS
            interpretation = 'High probability of bankruptcy within 2 years'
            probability = '>80% within 2 years'
        else:
            classification = ZoneClassification.GRAY
            interpretation = 'Elevated risk - requires close monitoring'
            probability = '35-50% within 2 years'
        
        return ZScoreResult(
            score=score,
            variant=variant,
            classification=classification,
            components=components,
            interpretation=interpretation,
            bankruptcy_probability=probability,
            evidence_hash=self._generate_hash({'inputs': str(inputs), 'score': score})
        )
    
    def monitor_trends(
        self,
        historical_scores: List[Dict[str, Any]],
        company_id: str,
        company_name: str
    ) -> List[BankruptcyAlert]:
        """
        Monitor Z-Score trends over time and generate alerts.
        
        Args:
            historical_scores: List of {'period': str, 'result': ZScoreResult}
            company_id: Company CIK or identifier
            company_name: Company name
            
        Returns:
            List of BankruptcyAlert objects
        """
        alerts = []
        
        if len(historical_scores) < 2:
            return alerts
        
        # Sort by period
        sorted_scores = sorted(historical_scores, key=lambda x: x['period'])
        
        latest = sorted_scores[-1]['result']
        previous = sorted_scores[-2]['result']
        score_change = latest.score - previous.score
        
        # Alert: Entered distress zone
        if latest.classification == ZoneClassification.DISTRESS and previous.classification != ZoneClassification.DISTRESS:
            alerts.append(BankruptcyAlert(
                alert_type=BankruptcyAlertType.DISTRESS_ZONE,
                company_id=company_id,
                company_name=company_name,
                current_z_score=latest.score,
                previous_z_score=previous.score,
                z_score_change=score_change,
                classification=ZoneClassification.DISTRESS,
                risk_indicators=[
                    f'Z-Score dropped from {previous.score:.2f} to {latest.score:.2f}',
                    f'Now below distress threshold of {self.THRESHOLDS[latest.variant]["distress"]}',
                    latest.interpretation,
                    f'Bankruptcy probability: {latest.bankruptcy_probability}'
                ],
                time_horizon='12-24 months',
                evidence_hash=self._generate_hash({'latest': latest.score, 'previous': previous.score}),
                severity='CRITICAL'
            ))
        
        # Alert: Entered gray zone from safe
        if latest.classification == ZoneClassification.GRAY and previous.classification == ZoneClassification.SAFE:
            alerts.append(BankruptcyAlert(
                alert_type=BankruptcyAlertType.GRAY_ZONE_ENTRY,
                company_id=company_id,
                company_name=company_name,
                current_z_score=latest.score,
                previous_z_score=previous.score,
                z_score_change=score_change,
                classification=ZoneClassification.GRAY,
                risk_indicators=[
                    f'Z-Score declined from {previous.score:.2f} to {latest.score:.2f}',
                    'Company moved from "Safe" to "Gray Zone" classification',
                    'Elevated monitoring required'
                ],
                time_horizon='24-36 months',
                evidence_hash=self._generate_hash({'latest': latest.score, 'previous': previous.score}),
                severity='HIGH'
            ))
        
        # Alert: Rapid deterioration (>20% decline)
        if previous.score > 0 and score_change / previous.score < -0.2:
            drivers = self._identify_drivers(latest.components, previous.components)
            alerts.append(BankruptcyAlert(
                alert_type=BankruptcyAlertType.RAPID_DETERIORATION,
                company_id=company_id,
                company_name=company_name,
                current_z_score=latest.score,
                previous_z_score=previous.score,
                z_score_change=score_change,
                classification=latest.classification,
                risk_indicators=[
                    f'Z-Score declined {abs(score_change / previous.score * 100):.1f}% in one period',
                    'Rapid financial deterioration detected',
                    f'Key drivers: {drivers}'
                ],
                time_horizon='Immediate investigation required',
                evidence_hash=self._generate_hash({'latest': latest.score, 'previous': previous.score}),
                severity='CRITICAL' if latest.classification == ZoneClassification.DISTRESS else 'HIGH'
            ))
        
        # Alert: Extremely low Z-Score
        if latest.score < 0.5:
            alerts.append(BankruptcyAlert(
                alert_type=BankruptcyAlertType.BANKRUPTCY_IMMINENT,
                company_id=company_id,
                company_name=company_name,
                current_z_score=latest.score,
                previous_z_score=None,
                z_score_change=None,
                classification=ZoneClassification.DISTRESS,
                risk_indicators=[
                    f'Z-Score of {latest.score:.2f} indicates severe financial distress',
                    'Bankruptcy or restructuring likely within 6-12 months',
                    'Recommend immediate portfolio risk assessment'
                ],
                time_horizon='6-12 months',
                evidence_hash=self._generate_hash({'score': latest.score}),
                severity='CRITICAL'
            ))
        
        return alerts
    
    def _identify_drivers(
        self,
        current: ZScoreComponents,
        previous: ZScoreComponents
    ) -> str:
        """Identify which components drove the Z-Score change."""
        changes = [
            ('Working Capital', current.x1_working_capital_ratio - previous.x1_working_capital_ratio),
            ('Retained Earnings', current.x2_retained_earnings_ratio - previous.x2_retained_earnings_ratio),
            ('EBIT/Assets', current.x3_ebit_ratio - previous.x3_ebit_ratio),
            ('Equity/Debt', current.x4_equity_debt_ratio - previous.x4_equity_debt_ratio),
            ('Sales/Assets', current.x5_sales_ratio - previous.x5_sales_ratio)
        ]
        
        # Sort by absolute change
        changes.sort(key=lambda x: abs(x[1]), reverse=True)
        
        return ', '.join(
            f'{name} {"+" if change > 0 else ""}{change * 100:.1f}%'
            for name, change in changes[:2]
        )
    
    def _generate_hash(self, data: Any) -> str:
        """Generate SHA-256 evidence hash."""
        return hashlib.sha256(str(data).encode()).hexdigest()

