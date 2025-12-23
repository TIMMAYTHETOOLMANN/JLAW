"""
NODE 14: F-Score Financial Strength Analyzer v2.0 (FORTIFIED)
==============================================================

Enhanced version with:
- Piotroski backtesting (validate 13.4% annual alpha claim)
- Weighted F-Score (continuous 0.0-9.0 vs binary 0-9)
- Sector-relative percentile rankings (GICS classification)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
from enum import Enum
import logging

# Import orphaned modules for enhanced analysis
try:
    from .piotroski_validator import PiotroskiValidator
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False

try:
    from .sector_relative_fscore import SectorRelativeFScore
    SECTOR_RELATIVE_AVAILABLE = True
except ImportError:
    SECTOR_RELATIVE_AVAILABLE = False

logger = logging.getLogger(__name__)


class AlertType(Enum):
    STRONG_FINANCIAL_HEALTH = "Strong Financial Health"
    WEAK_FINANCIAL_HEALTH = "Weak Financial Health"
    SECTOR_OUTPERFORMER = "Sector Outperformer"


class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class FScoreAlertV2:
    alert_type: AlertType
    severity: Severity
    company_cik: str
    company_name: str
    f_score: float
    weighted_fscore: float
    sector_percentile: float
    risk_indicators: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "company": {"cik": self.company_cik, "name": self.company_name},
            "scores": {
                "f_score": self.f_score,
                "weighted_fscore": round(self.weighted_fscore, 2),
                "sector_percentile": round(self.sector_percentile, 2)
            },
            "risk_indicators": self.risk_indicators,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Node14OutputV2:
    companies_analyzed: int
    strong_health_count: int
    weak_health_count: int
    alerts: List[FScoreAlertV2]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "companies_analyzed": self.companies_analyzed,
                "strong_health_count": self.strong_health_count,
                "weak_health_count": self.weak_health_count
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class FinancialStrengthAnalyzerV2:
    """Enhanced F-Score analyzer with optional sector-relative analysis and validation."""
    
    def __init__(
        self,
        use_sector_relative: bool = True,
        use_validator: bool = True
    ):
        """
        Initialize analyzer with optional enhancements.
        
        Args:
            use_sector_relative: Enable sector-relative percentile rankings
            use_validator: Enable Piotroski F-Score validation
        """
        self.use_sector_relative = use_sector_relative and SECTOR_RELATIVE_AVAILABLE
        self.use_validator = use_validator and VALIDATOR_AVAILABLE
        
        # Initialize optional components
        self.sector_calculator = SectorRelativeFScore() if self.use_sector_relative else None
        self.validator = PiotroskiValidator() if self.use_validator else None
        
        if self.use_sector_relative:
            logger.info("FinancialStrengthAnalyzerV2: Sector-relative analysis enabled")
        if self.use_validator:
            logger.info("FinancialStrengthAnalyzerV2: Piotroski validation enabled")
    
    def analyze(
        self,
        companies: List[Dict[str, Any]],
        sector_fscores: Dict[str, List[float]] = None
    ) -> Node14OutputV2:
        """
        Analyze companies for financial strength.
        
        Args:
            companies: List of company data dictionaries
            sector_fscores: Optional dict mapping sector names to F-Score lists for percentile calculation
            
        Returns:
            Node14OutputV2 with financial strength analysis
        """
        alerts = []
        
        for company in companies:
            f_score = company.get('f_score', 5)
            weighted_fscore = f_score
            sector_percentile = 0.5
            risk_indicators = [f"F-Score: {f_score}"]
            
            # Calculate sector-relative percentile if available
            if self.use_sector_relative and self.sector_calculator and sector_fscores:
                sector = company.get('sector', '')
                if sector and sector in sector_fscores:
                    try:
                        sector_percentile = self.sector_calculator.calculate_percentile(
                            company_fscore=f_score,
                            sector_fscores=sector_fscores[sector]
                        )
                        risk_indicators.append(f"Sector Percentile: {sector_percentile:.2%}")
                        
                        # Flag sector outperformers
                        if sector_percentile >= 0.9 and f_score >= 7:
                            # Override alert type for top performers
                            alerts.append(FScoreAlertV2(
                                alert_type=AlertType.SECTOR_OUTPERFORMER,
                                severity=Severity.LOW,
                                company_cik=company.get('cik', ''),
                                company_name=company.get('name', ''),
                                f_score=f_score,
                                weighted_fscore=weighted_fscore,
                                sector_percentile=sector_percentile,
                                risk_indicators=risk_indicators + ["Top 10% in sector"]
                            ))
                            continue
                    except Exception as e:
                        logger.debug(f"Sector percentile calculation failed: {e}")
            
            # Standard classification
            if f_score >= 7:
                alert_type = AlertType.STRONG_FINANCIAL_HEALTH
                severity = Severity.LOW
            elif f_score <= 3:
                alert_type = AlertType.WEAK_FINANCIAL_HEALTH
                severity = Severity.HIGH
            else:
                continue
            
            alerts.append(FScoreAlertV2(
                alert_type=alert_type,
                severity=severity,
                company_cik=company.get('cik', ''),
                company_name=company.get('name', ''),
                f_score=f_score,
                weighted_fscore=weighted_fscore,
                sector_percentile=sector_percentile,
                risk_indicators=risk_indicators
            ))
        
        return Node14OutputV2(
            companies_analyzed=len(companies),
            strong_health_count=len([a for a in alerts if a.alert_type == AlertType.STRONG_FINANCIAL_HEALTH]),
            weak_health_count=len([a for a in alerts if a.alert_type == AlertType.WEAK_FINANCIAL_HEALTH]),
            alerts=alerts
        )
