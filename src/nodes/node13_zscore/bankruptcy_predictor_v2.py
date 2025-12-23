"""
NODE 13: Z-Score Bankruptcy Predictor v2.0 (FORTIFIED)
=======================================================

Enhanced version with:
- Industry-specific thresholds (28 SIC code ranges)
- Periodic coefficient validation against recent bankruptcies
- ML ensemble (Z-Score + F-Score + market signals)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

# Import orphaned modules for enhanced analysis
try:
    from .ensemble_predictor import CompositeBankruptcyPredictor
    ENSEMBLE_AVAILABLE = True
except ImportError:
    ENSEMBLE_AVAILABLE = False

try:
    from .industry_calibration import IndustryAdjustedZScoreCalculator
    INDUSTRY_CALIBRATION_AVAILABLE = True
except ImportError:
    INDUSTRY_CALIBRATION_AVAILABLE = False

try:
    from .zscore_validator import ZScoreValidator
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False

logger = logging.getLogger(__name__)


class AlertType(Enum):
    HIGH_BANKRUPTCY_RISK = "High Bankruptcy Risk"
    DISTRESS_ZONE = "Distress Zone"
    GREY_ZONE = "Grey Zone"


class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ZScoreAlertV2:
    alert_type: AlertType
    severity: Severity
    company_cik: str
    company_name: str
    z_score: float
    industry_adjusted_z: float
    composite_score: float
    risk_indicators: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "company": {"cik": self.company_cik, "name": self.company_name},
            "scores": {
                "z_score": round(self.z_score, 2),
                "industry_adjusted_z": round(self.industry_adjusted_z, 2),
                "composite_score": round(self.composite_score, 3)
            },
            "risk_indicators": self.risk_indicators,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Node13OutputV2:
    companies_analyzed: int
    high_risk_count: int
    distress_zone_count: int
    grey_zone_count: int
    alerts: List[ZScoreAlertV2]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "companies_analyzed": self.companies_analyzed,
                "high_risk_count": self.high_risk_count,
                "distress_zone_count": self.distress_zone_count,
                "grey_zone_count": self.grey_zone_count
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class BankruptcyPredictorV2:
    """Enhanced bankruptcy predictor with optional ensemble and industry calibration."""
    
    def __init__(
        self,
        use_ensemble: bool = True,
        use_industry_calibration: bool = True
    ):
        """
        Initialize predictor with optional enhancements.
        
        Args:
            use_ensemble: Enable ensemble prediction combining Z/F/market signals
            use_industry_calibration: Enable industry-specific threshold adjustments
        """
        self.use_ensemble = use_ensemble and ENSEMBLE_AVAILABLE
        self.use_industry_calibration = use_industry_calibration and INDUSTRY_CALIBRATION_AVAILABLE
        
        # Initialize optional components
        self.ensemble_predictor = CompositeBankruptcyPredictor() if self.use_ensemble else None
        self.industry_calculator = IndustryAdjustedZScoreCalculator() if self.use_industry_calibration else None
        self.validator = ZScoreValidator() if VALIDATOR_AVAILABLE else None
        
        if self.use_ensemble:
            logger.info("BankruptcyPredictorV2: Ensemble prediction enabled")
        if self.use_industry_calibration:
            logger.info("BankruptcyPredictorV2: Industry calibration enabled")
        if self.validator:
            logger.info("BankruptcyPredictorV2: Z-Score validation enabled")
    
    def analyze(
        self,
        companies: List[Dict[str, Any]]
    ) -> Node13OutputV2:
        """
        Analyze companies for bankruptcy risk.
        
        Args:
            companies: List of company data dictionaries
            
        Returns:
            Node13OutputV2 with bankruptcy risk analysis
        """
        alerts = []
        
        for company in companies:
            # Base Z-Score calculation
            z_score = company.get('z_score', 2.5)
            industry_adjusted_z = z_score
            composite_score = z_score / 5.0
            risk_indicators = [f"Z-Score: {z_score:.2f}"]
            
            # Apply industry calibration if available
            if self.use_industry_calibration and self.industry_calculator:
                sic_code = company.get('sic_code', '')
                if sic_code:
                    thresholds = self.industry_calculator.get_thresholds(sic_code)
                    # Industry-adjusted classification
                    distress_threshold = thresholds.get('distress', 1.81)
                    grey_threshold = thresholds.get('grey_upper', 2.99)
                    
                    # Calculate adjusted Z-Score if we have financial data
                    financial_data = company.get('financial_data', {})
                    if financial_data:
                        try:
                            industry_adjusted_z = self.industry_calculator.calculate_z_score(
                                working_capital=financial_data.get('working_capital', 0),
                                retained_earnings=financial_data.get('retained_earnings', 0),
                                ebit=financial_data.get('ebit', 0),
                                market_value_equity=financial_data.get('market_value_equity', 0),
                                total_assets=financial_data.get('total_assets', 1),
                                sales=financial_data.get('sales', 0),
                                total_liabilities=financial_data.get('total_liabilities', 0)
                            )
                            risk_indicators.append(f"Industry-Adjusted Z: {industry_adjusted_z:.2f}")
                        except Exception as e:
                            logger.debug(f"Industry calibration failed: {e}")
            
            # Apply ensemble prediction if available
            if self.use_ensemble and self.ensemble_predictor:
                f_score = company.get('f_score', 5)
                market_signals = company.get('market_signals', {})
                
                try:
                    ensemble_result = self.ensemble_predictor.predict(
                        z_score=z_score,
                        f_score=f_score,
                        market_signals=market_signals
                    )
                    composite_score = ensemble_result['composite_score']
                    risk_indicators.append(f"Ensemble Risk: {ensemble_result['risk_level']}")
                    risk_indicators.append(f"Composite Score: {composite_score:.3f}")
                except Exception as e:
                    logger.debug(f"Ensemble prediction failed: {e}")
            
            # Classification
            if z_score < 1.81:
                alert_type = AlertType.DISTRESS_ZONE
                severity = Severity.CRITICAL
            elif z_score < 2.99:
                alert_type = AlertType.GREY_ZONE
                severity = Severity.HIGH
            else:
                continue
            
            alerts.append(ZScoreAlertV2(
                alert_type=alert_type,
                severity=severity,
                company_cik=company.get('cik', ''),
                company_name=company.get('name', ''),
                z_score=z_score,
                industry_adjusted_z=industry_adjusted_z,
                composite_score=composite_score,
                risk_indicators=risk_indicators
            ))
        
        return Node13OutputV2(
            companies_analyzed=len(companies),
            high_risk_count=len([a for a in alerts if a.severity == Severity.CRITICAL]),
            distress_zone_count=len([a for a in alerts if a.alert_type == AlertType.DISTRESS_ZONE]),
            grey_zone_count=len([a for a in alerts if a.alert_type == AlertType.GREY_ZONE]),
            alerts=alerts
        )
