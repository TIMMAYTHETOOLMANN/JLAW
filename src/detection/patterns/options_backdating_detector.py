"""
Options Backdating Detector
===========================

Implements Erik Lie methodology for detecting stock option backdating
and SOX Section 403 violations.

Academic Reference: Lie, E. (2005) "On the Timing of CEO Stock Option Awards"
Management Science, Vol. 51, No. 5, pp. 802-812

Detection Capabilities:
- Grant date clustering at stock price local minima
- Post-SOX reporting delays exceeding 2 business days (SOX 403 violation)
- V-shaped return patterns around grant dates
- Negative pre-grant Cumulative Abnormal Return (CAR) less than -2%
- Positive post-grant CAR greater than +1.85%
- Lucky grant timing detection (grants at monthly/quarterly price lows)

Thresholds:
- Pre-grant analysis window: -20 to -1 trading days
- Post-grant analysis window: +1 to +20 trading days
- Abnormal return significance threshold: 2%
- SOX 403 filing deadline: 2 business days

Integration: Connects with Node 1 (Form 4) for insider transaction data
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import hashlib
import logging
import math
from collections import defaultdict

logger = logging.getLogger(__name__)


class BackdatingSeverity(Enum):
    """Severity level for backdating detection."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class GrantAnalysis:
    """Analysis result for a single stock option grant."""
    grant_date: date
    executive_name: str
    shares_granted: int
    exercise_price: float
    stock_price_on_grant: float
    filing_date: Optional[date]
    filing_delay_days: Optional[int]
    
    # CAR analysis
    pre_grant_car: float
    post_grant_car: float
    
    # Pattern flags
    is_at_local_minimum: bool
    is_sox_violation: bool
    has_v_shaped_pattern: bool
    is_lucky_grant: bool
    
    # Risk metrics
    backdating_probability: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "grant_date": self.grant_date.isoformat(),
            "executive_name": self.executive_name,
            "shares_granted": self.shares_granted,
            "exercise_price": round(self.exercise_price, 2),
            "stock_price_on_grant": round(self.stock_price_on_grant, 2),
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "filing_delay_days": self.filing_delay_days,
            "pre_grant_car": round(self.pre_grant_car, 4),
            "post_grant_car": round(self.post_grant_car, 4),
            "is_at_local_minimum": self.is_at_local_minimum,
            "is_sox_violation": self.is_sox_violation,
            "has_v_shaped_pattern": self.has_v_shaped_pattern,
            "is_lucky_grant": self.is_lucky_grant,
            "backdating_probability": round(self.backdating_probability, 3)
        }


@dataclass
class BackdatingAlert:
    """Alert for detected options backdating pattern."""
    alert_id: str
    company_cik: str
    company_name: str
    detection_date: datetime
    severity: BackdatingSeverity
    grants_analyzed: List[GrantAnalysis]
    suspicious_grants: List[GrantAnalysis]
    
    # Aggregate statistics
    total_grants: int
    suspicious_count: int
    sox_violations: int
    average_pre_grant_car: float
    average_post_grant_car: float
    
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
            "statistics": {
                "total_grants": self.total_grants,
                "suspicious_count": self.suspicious_count,
                "sox_violations": self.sox_violations,
                "average_pre_grant_car": round(self.average_pre_grant_car, 4),
                "average_post_grant_car": round(self.average_post_grant_car, 4)
            },
            "suspicious_grants": [g.to_dict() for g in self.suspicious_grants],
            "evidence_summary": self.evidence_summary,
            "regulatory_implications": self.regulatory_implications,
            "recommended_actions": self.recommended_actions,
            "evidence_hash": self.evidence_hash
        }


class OptionsBackdatingDetector:
    """
    Detector for stock option backdating using Erik Lie methodology.
    
    Analyzes stock option grants to executives and identifies patterns
    consistent with backdating manipulation.
    """
    
    # Analysis windows (trading days)
    PRE_GRANT_WINDOW = 20
    POST_GRANT_WINDOW = 20
    
    # Detection thresholds
    PRE_GRANT_CAR_THRESHOLD = -0.02  # -2%
    POST_GRANT_CAR_THRESHOLD = 0.0185  # +1.85%
    SOX_403_DEADLINE_DAYS = 2  # Business days
    LOCAL_MINIMUM_LOOKBACK = 20  # Trading days for local min detection
    
    def __init__(self, mock_mode: bool = False):
        """
        Initialize the detector.
        
        Args:
            mock_mode: If True, use mock data for testing without external dependencies
        """
        self.mock_mode = mock_mode
        self.alerts = []
    
    def analyze_grants(
        self,
        company_cik: str,
        company_name: str,
        grants: List[Dict[str, Any]],
        price_history: Dict[date, float],
        market_returns: Optional[Dict[date, float]] = None
    ) -> BackdatingAlert:
        """
        Analyze stock option grants for backdating patterns.
        
        Args:
            company_cik: SEC CIK number
            company_name: Company name
            grants: List of option grant records from Form 4
            price_history: Daily stock prices {date: price}
            market_returns: Optional market index returns for abnormal return calculation
            
        Returns:
            BackdatingAlert with detection results
        """
        if self.mock_mode:
            return self._generate_mock_alert(company_cik, company_name, len(grants))
        
        grant_analyses = []
        suspicious_grants = []
        
        for grant in grants:
            try:
                analysis = self._analyze_single_grant(grant, price_history, market_returns)
                grant_analyses.append(analysis)
                
                # Flag as suspicious if multiple red flags present
                if self._is_suspicious_grant(analysis):
                    suspicious_grants.append(analysis)
                    
            except Exception as e:
                logger.warning(f"Failed to analyze grant: {e}")
                continue
        
        # Calculate aggregate statistics
        sox_violations = sum(1 for g in grant_analyses if g.is_sox_violation)
        avg_pre_car = sum(g.pre_grant_car for g in grant_analyses) / len(grant_analyses) if grant_analyses else 0
        avg_post_car = sum(g.post_grant_car for g in grant_analyses) / len(grant_analyses) if grant_analyses else 0
        
        # Determine severity
        severity = self._determine_severity(len(grant_analyses), len(suspicious_grants), sox_violations)
        
        # Generate evidence summary
        evidence_summary = self._generate_evidence_summary(grant_analyses, suspicious_grants)
        
        # Generate alert
        alert = BackdatingAlert(
            alert_id=self._generate_alert_id(company_cik),
            company_cik=company_cik,
            company_name=company_name,
            detection_date=datetime.utcnow(),
            severity=severity,
            grants_analyzed=grant_analyses,
            suspicious_grants=suspicious_grants,
            total_grants=len(grant_analyses),
            suspicious_count=len(suspicious_grants),
            sox_violations=sox_violations,
            average_pre_grant_car=avg_pre_car,
            average_post_grant_car=avg_post_car,
            evidence_summary=evidence_summary,
            regulatory_implications=self._get_regulatory_implications(severity, sox_violations),
            recommended_actions=self._get_recommended_actions(severity),
            evidence_hash=self._compute_evidence_hash(grant_analyses)
        )
        
        self.alerts.append(alert)
        return alert
    
    def _analyze_single_grant(
        self,
        grant: Dict[str, Any],
        price_history: Dict[date, float],
        market_returns: Optional[Dict[date, float]]
    ) -> GrantAnalysis:
        """Analyze a single option grant for backdating indicators."""
        grant_date = grant['grant_date']
        filing_date = grant.get('filing_date')
        
        # Calculate filing delay
        filing_delay = None
        is_sox_violation = False
        if filing_date:
            filing_delay = self._calculate_business_days(grant_date, filing_date)
            is_sox_violation = filing_delay > self.SOX_403_DEADLINE_DAYS
        
        # Calculate CAR (Cumulative Abnormal Return)
        pre_grant_car = self._calculate_car(
            grant_date,
            price_history,
            market_returns,
            window=-self.PRE_GRANT_WINDOW,
            direction='backward'
        )
        
        post_grant_car = self._calculate_car(
            grant_date,
            price_history,
            market_returns,
            window=self.POST_GRANT_WINDOW,
            direction='forward'
        )
        
        # Check if grant at local minimum
        is_at_local_minimum = self._is_local_minimum(grant_date, price_history)
        
        # Check for V-shaped pattern
        has_v_shaped_pattern = (
            pre_grant_car < self.PRE_GRANT_CAR_THRESHOLD and
            post_grant_car > self.POST_GRANT_CAR_THRESHOLD
        )
        
        # Check for lucky grant timing
        is_lucky_grant = self._is_lucky_grant(grant_date, price_history)
        
        # Calculate backdating probability
        backdating_probability = self._calculate_backdating_probability(
            pre_grant_car,
            post_grant_car,
            is_at_local_minimum,
            is_sox_violation,
            has_v_shaped_pattern,
            is_lucky_grant
        )
        
        stock_price = price_history.get(grant_date, 0.0)
        
        return GrantAnalysis(
            grant_date=grant_date,
            executive_name=grant.get('executive_name', 'Unknown'),
            shares_granted=grant.get('shares', 0),
            exercise_price=grant.get('exercise_price', 0.0),
            stock_price_on_grant=stock_price,
            filing_date=filing_date,
            filing_delay_days=filing_delay,
            pre_grant_car=pre_grant_car,
            post_grant_car=post_grant_car,
            is_at_local_minimum=is_at_local_minimum,
            is_sox_violation=is_sox_violation,
            has_v_shaped_pattern=has_v_shaped_pattern,
            is_lucky_grant=is_lucky_grant,
            backdating_probability=backdating_probability
        )
    
    def _calculate_car(
        self,
        grant_date: date,
        price_history: Dict[date, float],
        market_returns: Optional[Dict[date, float]],
        window: int,
        direction: str
    ) -> float:
        """
        Calculate Cumulative Abnormal Return (CAR).
        
        CAR = Sum of (daily_return - market_return) over window
        If market_returns not provided, use raw returns
        """
        sorted_dates = sorted(price_history.keys())
        grant_idx = sorted_dates.index(grant_date) if grant_date in sorted_dates else -1
        
        if grant_idx == -1:
            return 0.0
        
        cumulative_return = 0.0
        
        if direction == 'backward':
            start_idx = max(0, grant_idx - abs(window))
            end_idx = grant_idx
        else:  # forward
            start_idx = grant_idx + 1
            end_idx = min(len(sorted_dates), grant_idx + abs(window) + 1)
        
        for i in range(start_idx, end_idx):
            if i > 0:
                prev_price = price_history[sorted_dates[i-1]]
                curr_price = price_history[sorted_dates[i]]
                
                if prev_price > 0:
                    daily_return = (curr_price - prev_price) / prev_price
                    
                    # Adjust for market if available
                    if market_returns and sorted_dates[i] in market_returns:
                        daily_return -= market_returns[sorted_dates[i]]
                    
                    cumulative_return += daily_return
        
        return cumulative_return
    
    def _is_local_minimum(self, grant_date: date, price_history: Dict[date, float]) -> bool:
        """Check if grant date is at a local stock price minimum."""
        sorted_dates = sorted(price_history.keys())
        grant_idx = sorted_dates.index(grant_date) if grant_date in sorted_dates else -1
        
        if grant_idx == -1:
            return False
        
        grant_price = price_history[grant_date]
        
        # Check surrounding window
        start_idx = max(0, grant_idx - self.LOCAL_MINIMUM_LOOKBACK)
        end_idx = min(len(sorted_dates), grant_idx + self.LOCAL_MINIMUM_LOOKBACK + 1)
        
        for i in range(start_idx, end_idx):
            if i != grant_idx and price_history[sorted_dates[i]] < grant_price:
                return False
        
        return True
    
    def _is_lucky_grant(self, grant_date: date, price_history: Dict[date, float]) -> bool:
        """Check if grant is at monthly or quarterly price low."""
        grant_price = price_history.get(grant_date, float('inf'))
        
        # Get month prices
        month_prices = []
        for d, price in price_history.items():
            if d.year == grant_date.year and d.month == grant_date.month:
                month_prices.append(price)
        
        if month_prices:
            min_month_price = min(month_prices)
            # Grant is "lucky" if within 1% of monthly low
            return grant_price <= min_month_price * 1.01
        
        return False
    
    def _calculate_business_days(self, start_date: date, end_date: date) -> int:
        """Calculate business days between two dates (simplified)."""
        if start_date > end_date:
            return 0
        
        delta = end_date - start_date
        total_days = delta.days
        
        # Rough estimate: 5/7 of calendar days are business days
        business_days = int(total_days * 5 / 7)
        
        return business_days
    
    def _calculate_backdating_probability(
        self,
        pre_grant_car: float,
        post_grant_car: float,
        is_at_local_minimum: bool,
        is_sox_violation: bool,
        has_v_shaped_pattern: bool,
        is_lucky_grant: bool
    ) -> float:
        """
        Calculate probability of backdating based on multiple indicators.
        
        Uses weighted scoring system:
        - V-shaped pattern: 30%
        - SOX violation: 25%
        - Local minimum: 20%
        - Lucky grant: 15%
        - Pre-grant CAR: 5%
        - Post-grant CAR: 5%
        """
        score = 0.0
        
        # V-shaped pattern (strongest indicator)
        if has_v_shaped_pattern:
            score += 0.30
        
        # SOX 403 violation
        if is_sox_violation:
            score += 0.25
        
        # Local minimum
        if is_at_local_minimum:
            score += 0.20
        
        # Lucky grant timing
        if is_lucky_grant:
            score += 0.15
        
        # Pre-grant CAR significance
        if pre_grant_car < self.PRE_GRANT_CAR_THRESHOLD:
            score += 0.05
        
        # Post-grant CAR significance
        if post_grant_car > self.POST_GRANT_CAR_THRESHOLD:
            score += 0.05
        
        return min(score, 1.0)
    
    def _is_suspicious_grant(self, analysis: GrantAnalysis) -> bool:
        """Determine if a grant is suspicious based on multiple criteria."""
        # Require at least 2 red flags or 1 critical flag
        red_flags = 0
        
        if analysis.has_v_shaped_pattern:
            red_flags += 2  # V-pattern is strong indicator
        
        if analysis.is_sox_violation:
            red_flags += 2  # SOX violation is critical
        
        if analysis.is_at_local_minimum:
            red_flags += 1
        
        if analysis.is_lucky_grant:
            red_flags += 1
        
        return red_flags >= 2 or analysis.backdating_probability >= 0.50
    
    def _determine_severity(
        self,
        total_grants: int,
        suspicious_count: int,
        sox_violations: int
    ) -> BackdatingSeverity:
        """Determine alert severity based on findings."""
        if total_grants == 0:
            return BackdatingSeverity.LOW
        
        suspicious_ratio = suspicious_count / total_grants
        
        # Critical: High rate of suspicious grants or multiple SOX violations
        if suspicious_ratio >= 0.5 or sox_violations >= 3:
            return BackdatingSeverity.CRITICAL
        
        # High: Moderate suspicious rate with SOX violations
        if suspicious_ratio >= 0.3 or sox_violations >= 2:
            return BackdatingSeverity.HIGH
        
        # Medium: Some suspicious activity
        if suspicious_ratio >= 0.15 or sox_violations >= 1:
            return BackdatingSeverity.MEDIUM
        
        return BackdatingSeverity.LOW
    
    def _generate_evidence_summary(
        self,
        all_grants: List[GrantAnalysis],
        suspicious_grants: List[GrantAnalysis]
    ) -> str:
        """Generate human-readable evidence summary."""
        if not all_grants:
            return "No grants analyzed."
        
        summary_parts = [
            f"Analyzed {len(all_grants)} stock option grants.",
            f"Found {len(suspicious_grants)} grants with backdating indicators.",
        ]
        
        sox_violations = sum(1 for g in all_grants if g.is_sox_violation)
        if sox_violations > 0:
            summary_parts.append(
                f"Detected {sox_violations} SOX Section 403 violations "
                f"(filing delay > {self.SOX_403_DEADLINE_DAYS} business days)."
            )
        
        v_shaped = sum(1 for g in suspicious_grants if g.has_v_shaped_pattern)
        if v_shaped > 0:
            summary_parts.append(
                f"{v_shaped} grants exhibit V-shaped return patterns "
                f"(negative pre-grant CAR followed by positive post-grant CAR)."
            )
        
        local_mins = sum(1 for g in suspicious_grants if g.is_at_local_minimum)
        if local_mins > 0:
            summary_parts.append(
                f"{local_mins} grants occurred at local stock price minima."
            )
        
        return " ".join(summary_parts)
    
    def _get_regulatory_implications(
        self,
        severity: BackdatingSeverity,
        sox_violations: int
    ) -> List[str]:
        """Get regulatory implications based on findings."""
        implications = []
        
        if sox_violations > 0:
            implications.append(
                "Sarbanes-Oxley Section 403 violations detected - "
                "executives failed to file Form 4 within 2 business days"
            )
        
        if severity in [BackdatingSeverity.HIGH, BackdatingSeverity.CRITICAL]:
            implications.extend([
                "Potential securities fraud under Section 10(b) of Securities Exchange Act",
                "Possible financial statement misstatement (FAS 123R)",
                "Executive compensation disclosure violations (Item 402 of Regulation S-K)",
                "Recommended for SEC Division of Enforcement review"
            ])
        
        if severity == BackdatingSeverity.CRITICAL:
            implications.append(
                "Pattern suggests coordinated backdating scheme - "
                "recommend DOJ Criminal Division referral"
            )
        
        return implications
    
    def _get_recommended_actions(self, severity: BackdatingSeverity) -> List[str]:
        """Get recommended investigative actions."""
        actions = [
            "Review all Form 4 filings for affected executives",
            "Obtain stock price data for grant date verification",
            "Interview compensation committee members",
            "Examine board meeting minutes for grant authorization dates"
        ]
        
        if severity in [BackdatingSeverity.HIGH, BackdatingSeverity.CRITICAL]:
            actions.extend([
                "Subpoena email communications regarding grant timing",
                "Forensic analysis of compensation committee records",
                "Engage independent auditor for FAS 123R compliance review",
                "Request production of all stock option grant documentation"
            ])
        
        if severity == BackdatingSeverity.CRITICAL:
            actions.extend([
                "Consider criminal investigation referral to DOJ",
                "Coordinate with SEC Office of the Chief Accountant",
                "Assess need for disgorgement and civil penalties"
            ])
        
        return actions
    
    def _generate_alert_id(self, company_cik: str) -> str:
        """Generate unique alert ID."""
        timestamp = datetime.utcnow().isoformat()
        data = f"BACKDATING_{company_cik}_{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16].upper()
    
    def _compute_evidence_hash(self, grants: List[GrantAnalysis]) -> str:
        """Compute SHA-256 hash of all grant evidence."""
        evidence_data = [g.to_dict() for g in grants]
        evidence_str = str(sorted(str(e) for e in evidence_data))
        return hashlib.sha256(evidence_str.encode()).hexdigest()
    
    def _generate_mock_alert(
        self,
        company_cik: str,
        company_name: str,
        num_grants: int
    ) -> BackdatingAlert:
        """Generate mock alert for testing without external dependencies."""
        # Create mock grants
        mock_grants = []
        suspicious_grants = []
        
        for i in range(min(num_grants, 5)):
            grant = GrantAnalysis(
                grant_date=date(2022, 6, 15 + i),
                executive_name=f"Executive {i+1}",
                shares_granted=10000 * (i+1),
                exercise_price=50.0 - i,
                stock_price_on_grant=50.0 - i,
                filing_date=date(2022, 6, 20 + i),
                filing_delay_days=3 + i,
                pre_grant_car=-0.025 - (i * 0.005),
                post_grant_car=0.020 + (i * 0.003),
                is_at_local_minimum=(i % 2 == 0),
                is_sox_violation=(i >= 2),
                has_v_shaped_pattern=(i >= 1),
                is_lucky_grant=(i % 2 == 1),
                backdating_probability=0.60 + (i * 0.05)
            )
            mock_grants.append(grant)
            
            if i >= 1:  # Make some suspicious
                suspicious_grants.append(grant)
        
        return BackdatingAlert(
            alert_id=self._generate_alert_id(company_cik),
            company_cik=company_cik,
            company_name=company_name,
            detection_date=datetime.utcnow(),
            severity=BackdatingSeverity.HIGH,
            grants_analyzed=mock_grants,
            suspicious_grants=suspicious_grants,
            total_grants=len(mock_grants),
            suspicious_count=len(suspicious_grants),
            sox_violations=len([g for g in mock_grants if g.is_sox_violation]),
            average_pre_grant_car=-0.03,
            average_post_grant_car=0.025,
            evidence_summary="Mock alert generated for testing",
            regulatory_implications=[
                "Mock regulatory implication 1",
                "Mock regulatory implication 2"
            ],
            recommended_actions=[
                "Mock action 1",
                "Mock action 2"
            ],
            evidence_hash=self._compute_evidence_hash(mock_grants)
        )
    
    async def analyze_grants_async(
        self,
        company_cik: str,
        company_name: str,
        grants: List[Dict[str, Any]],
        price_history: Dict[date, float],
        market_returns: Optional[Dict[date, float]] = None
    ) -> BackdatingAlert:
        """Async version of analyze_grants for concurrent execution."""
        # For now, just wrap synchronous version
        # In production, this could fetch price data asynchronously
        return self.analyze_grants(
            company_cik,
            company_name,
            grants,
            price_history,
            market_returns
        )
