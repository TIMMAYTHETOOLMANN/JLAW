"""
Pre-Announcement Trading Detection Module
==========================================

Implements event study methodology to detect suspicious insider trading
before material announcements (earnings, M&A, guidance changes, etc.).

Key Features:
- Cumulative Abnormal Returns (CAR) calculation
- Market Model for expected returns: E[R] = α + β×R_m
- Estimation window: [-250, -30] days
- Event window: [-5, -1] days (before announcement)
- Volume spike detection (>200% of ADV)
- Statistical significance testing

Reference: Fama-French event study methodology
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import logging
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PreAnnouncementSignal:
    """Pre-announcement trading signal with statistical analysis."""
    insider_name: str
    transaction_date: datetime
    announcement_date: datetime
    car_value: float  # Cumulative Abnormal Return
    volume_ratio: float  # Volume / ADV
    statistical_significance: float  # p-value
    is_suspicious: bool
    transaction_details: Optional[Dict[str, Any]] = None
    market_model_alpha: Optional[float] = None
    market_model_beta: Optional[float] = None
    abnormal_returns: List[float] = field(default_factory=list)
    event_window: Tuple[int, int] = (-5, -1)
    confidence_level: str = 'MEDIUM'  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'


@dataclass
class MarketModelEstimate:
    """Market model regression results."""
    alpha: float  # Intercept
    beta: float  # Market sensitivity
    r_squared: float
    estimation_period_days: int
    market_index: str = 'SP500'


class PreAnnouncementDetector:
    """
    Detect suspicious pre-announcement insider trading using event study methodology.
    
    Market Model: R_i,t = α + β×R_m,t + ε_i,t
    Abnormal Return: AR_i,t = R_i,t - (α̂ + β̂×R_m,t)
    Cumulative Abnormal Return: CAR = Σ AR_i,t over event window
    """
    
    # Default parameters
    ESTIMATION_WINDOW_START = -250  # Days before announcement
    ESTIMATION_WINDOW_END = -30
    EVENT_WINDOW_START = -5  # Days before announcement
    EVENT_WINDOW_END = -1
    
    CAR_THRESHOLD_CRITICAL = 0.05  # 5% CAR is highly suspicious
    CAR_THRESHOLD_HIGH = 0.03  # 3% CAR is suspicious
    CAR_THRESHOLD_MEDIUM = 0.02  # 2% CAR is notable
    
    VOLUME_SPIKE_THRESHOLD = 2.0  # 200% of average daily volume
    
    def __init__(self, market_index: str = 'SP500'):
        """
        Initialize pre-announcement detector.
        
        Args:
            market_index: Market index for market model (default: S&P 500)
        """
        self.logger = logging.getLogger("PreAnnouncementDetector")
        self.market_index = market_index
    
    def detect_pre_announcement_trading(
        self,
        insider_transactions: List[Dict[str, Any]],
        stock_prices: Dict[datetime, float],
        market_returns: Dict[datetime, float],
        volume_data: Dict[datetime, float],
        announcements: List[Dict[str, Any]]
    ) -> List[PreAnnouncementSignal]:
        """
        Detect suspicious pre-announcement trading patterns.
        
        Args:
            insider_transactions: List of insider transaction records
            stock_prices: Historical stock prices {date: price}
            market_returns: Market index returns {date: return}
            volume_data: Trading volumes {date: volume}
            announcements: Material announcements {date, type, description}
        
        Returns:
            List of suspicious pre-announcement signals
        """
        signals = []
        
        for announcement in announcements:
            announcement_date = announcement.get('date')
            if not isinstance(announcement_date, datetime):
                try:
                    announcement_date = datetime.fromisoformat(str(announcement_date))
                except Exception:
                    continue
            
            # Find insider transactions before this announcement
            pre_announcement_transactions = self._find_transactions_before_announcement(
                insider_transactions,
                announcement_date
            )
            
            if not pre_announcement_transactions:
                continue
            
            # Calculate market model for this stock
            market_model = self._estimate_market_model(
                stock_prices,
                market_returns,
                announcement_date
            )
            
            if market_model is None:
                self.logger.warning(f"Could not estimate market model for {announcement_date}")
                continue
            
            # Calculate CAR for event window
            car = self._calculate_car(
                stock_prices,
                market_returns,
                market_model,
                announcement_date,
                self.EVENT_WINDOW_START,
                self.EVENT_WINDOW_END
            )
            
            if car is None:
                continue
            
            # Calculate volume spike
            volume_ratio = self._calculate_volume_spike(
                volume_data,
                announcement_date,
                self.EVENT_WINDOW_START,
                self.EVENT_WINDOW_END
            )
            
            # Calculate statistical significance
            p_value = self._calculate_significance(
                stock_prices,
                market_returns,
                market_model,
                announcement_date
            )
            
            # Determine if suspicious
            is_suspicious = (
                (car >= self.CAR_THRESHOLD_MEDIUM) and
                (volume_ratio >= self.VOLUME_SPIKE_THRESHOLD or car >= self.CAR_THRESHOLD_HIGH)
            )
            
            # Classify confidence level
            confidence = self._classify_confidence(car, volume_ratio, p_value)
            
            # Create signal for each transaction
            for tx in pre_announcement_transactions:
                tx_date = tx.get('date')
                if not isinstance(tx_date, datetime):
                    try:
                        tx_date = datetime.fromisoformat(str(tx_date))
                    except Exception:
                        continue
                
                signal = PreAnnouncementSignal(
                    insider_name=tx.get('insider_name', 'Unknown'),
                    transaction_date=tx_date,
                    announcement_date=announcement_date,
                    car_value=car,
                    volume_ratio=volume_ratio,
                    statistical_significance=p_value,
                    is_suspicious=is_suspicious,
                    transaction_details=tx,
                    market_model_alpha=market_model.alpha,
                    market_model_beta=market_model.beta,
                    confidence_level=confidence
                )
                
                signals.append(signal)
        
        self.logger.info(f"Detected {len([s for s in signals if s.is_suspicious])} suspicious signals")
        
        return signals
    
    def _find_transactions_before_announcement(
        self,
        transactions: List[Dict[str, Any]],
        announcement_date: datetime
    ) -> List[Dict[str, Any]]:
        """Find transactions in event window before announcement."""
        event_start = announcement_date + timedelta(days=self.EVENT_WINDOW_START)
        event_end = announcement_date + timedelta(days=self.EVENT_WINDOW_END)
        
        pre_announcement = []
        
        for tx in transactions:
            tx_date = tx.get('date')
            if not isinstance(tx_date, datetime):
                try:
                    tx_date = datetime.fromisoformat(str(tx_date))
                except Exception:
                    continue
            
            if event_start <= tx_date <= event_end:
                pre_announcement.append(tx)
        
        return pre_announcement
    
    def _estimate_market_model(
        self,
        stock_prices: Dict[datetime, float],
        market_returns: Dict[datetime, float],
        announcement_date: datetime
    ) -> Optional[MarketModelEstimate]:
        """
        Estimate market model using OLS regression.
        
        R_i,t = α + β×R_m,t + ε_i,t
        
        Estimation window: [-250, -30] days before announcement
        """
        # Define estimation window
        est_start = announcement_date + timedelta(days=self.ESTIMATION_WINDOW_START)
        est_end = announcement_date + timedelta(days=self.ESTIMATION_WINDOW_END)
        
        # Collect returns in estimation window
        stock_returns = []
        market_returns_list = []
        
        sorted_dates = sorted(stock_prices.keys())
        
        for i in range(1, len(sorted_dates)):
            date = sorted_dates[i]
            prev_date = sorted_dates[i-1]
            
            if est_start <= date <= est_end:
                if date in market_returns:
                    # Calculate stock return
                    stock_ret = (stock_prices[date] - stock_prices[prev_date]) / stock_prices[prev_date]
                    market_ret = market_returns[date]
                    
                    stock_returns.append(stock_ret)
                    market_returns_list.append(market_ret)
        
        if len(stock_returns) < 50:  # Need minimum data points
            return None
        
        # OLS regression
        try:
            # Convert to numpy arrays
            X = np.array(market_returns_list).reshape(-1, 1)
            y = np.array(stock_returns)
            
            # Add intercept
            X_with_intercept = np.column_stack([np.ones(len(X)), X])
            
            # Solve: (X'X)^-1 X'y
            coefficients = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
            
            alpha = coefficients[0]
            beta = coefficients[1]
            
            # Calculate R-squared
            y_pred = X_with_intercept @ coefficients
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            return MarketModelEstimate(
                alpha=alpha,
                beta=beta,
                r_squared=r_squared,
                estimation_period_days=len(stock_returns),
                market_index=self.market_index
            )
        
        except Exception as e:
            self.logger.error(f"Market model estimation failed: {e}")
            return None
    
    def _calculate_car(
        self,
        stock_prices: Dict[datetime, float],
        market_returns: Dict[datetime, float],
        market_model: MarketModelEstimate,
        announcement_date: datetime,
        window_start: int,
        window_end: int
    ) -> Optional[float]:
        """
        Calculate Cumulative Abnormal Return (CAR) over event window.
        
        AR_t = R_i,t - (α̂ + β̂×R_m,t)
        CAR = Σ AR_t
        """
        event_start = announcement_date + timedelta(days=window_start)
        event_end = announcement_date + timedelta(days=window_end)
        
        abnormal_returns = []
        
        sorted_dates = sorted(stock_prices.keys())
        
        for i in range(1, len(sorted_dates)):
            date = sorted_dates[i]
            prev_date = sorted_dates[i-1]
            
            if event_start <= date <= event_end:
                if date in market_returns:
                    # Actual stock return
                    actual_return = (stock_prices[date] - stock_prices[prev_date]) / stock_prices[prev_date]
                    
                    # Expected return from market model
                    expected_return = market_model.alpha + market_model.beta * market_returns[date]
                    
                    # Abnormal return
                    ar = actual_return - expected_return
                    abnormal_returns.append(ar)
        
        if not abnormal_returns:
            return None
        
        # Cumulative abnormal return
        car = sum(abnormal_returns)
        
        return car
    
    def _calculate_volume_spike(
        self,
        volume_data: Dict[datetime, float],
        announcement_date: datetime,
        window_start: int,
        window_end: int
    ) -> float:
        """
        Calculate volume spike ratio.
        
        Returns: (Event window avg volume) / (Average daily volume)
        """
        # Calculate average daily volume (ADV) over estimation window
        est_start = announcement_date + timedelta(days=self.ESTIMATION_WINDOW_START)
        est_end = announcement_date + timedelta(days=self.ESTIMATION_WINDOW_END)
        
        estimation_volumes = [
            vol for date, vol in volume_data.items()
            if est_start <= date <= est_end
        ]
        
        if not estimation_volumes:
            return 0.0
        
        adv = sum(estimation_volumes) / len(estimation_volumes)
        
        # Calculate average volume in event window
        event_start = announcement_date + timedelta(days=window_start)
        event_end = announcement_date + timedelta(days=window_end)
        
        event_volumes = [
            vol for date, vol in volume_data.items()
            if event_start <= date <= event_end
        ]
        
        if not event_volumes or adv == 0:
            return 0.0
        
        event_avg_volume = sum(event_volumes) / len(event_volumes)
        
        return event_avg_volume / adv
    
    def _calculate_significance(
        self,
        stock_prices: Dict[datetime, float],
        market_returns: Dict[datetime, float],
        market_model: MarketModelEstimate,
        announcement_date: datetime
    ) -> float:
        """
        Calculate statistical significance (p-value) of CAR.
        
        Uses t-test on standardized CAR.
        """
        # Calculate variance of abnormal returns in estimation window
        est_start = announcement_date + timedelta(days=self.ESTIMATION_WINDOW_START)
        est_end = announcement_date + timedelta(days=self.ESTIMATION_WINDOW_END)
        
        abnormal_returns = []
        
        sorted_dates = sorted(stock_prices.keys())
        
        for i in range(1, len(sorted_dates)):
            date = sorted_dates[i]
            prev_date = sorted_dates[i-1]
            
            if est_start <= date <= est_end:
                if date in market_returns:
                    actual_return = (stock_prices[date] - stock_prices[prev_date]) / stock_prices[prev_date]
                    expected_return = market_model.alpha + market_model.beta * market_returns[date]
                    ar = actual_return - expected_return
                    abnormal_returns.append(ar)
        
        if len(abnormal_returns) < 2:
            return 1.0  # Not significant
        
        # Standard deviation of abnormal returns
        ar_std = np.std(abnormal_returns)
        
        if ar_std == 0:
            return 1.0
        
        # Calculate CAR
        car = self._calculate_car(
            stock_prices,
            market_returns,
            market_model,
            announcement_date,
            self.EVENT_WINDOW_START,
            self.EVENT_WINDOW_END
        )
        
        if car is None:
            return 1.0
        
        # Event window length
        event_length = abs(self.EVENT_WINDOW_END - self.EVENT_WINDOW_START) + 1
        
        # Standardized CAR
        car_std = car / (ar_std * np.sqrt(event_length))
        
        # Two-tailed t-test (approximate with normal distribution)
        try:
            from scipy import stats
            p_value = 2 * (1 - stats.norm.cdf(abs(car_std)))
        except ImportError:
            # Fallback: use approximate normal CDF without scipy
            # For large samples, use standard normal approximation
            # P(|Z| > z) ≈ 2 * (1 - Φ(|z|))
            # Approximate Φ(z) using error function
            from math import erf, sqrt
            p_value = 2 * (1 - (0.5 * (1 + erf(abs(car_std) / sqrt(2)))))
        
        return p_value
    
    def _classify_confidence(
        self,
        car: float,
        volume_ratio: float,
        p_value: float
    ) -> str:
        """
        Classify confidence level of suspicious signal.
        
        Returns: 'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW'
        """
        if car >= self.CAR_THRESHOLD_CRITICAL and p_value < 0.01:
            return 'CRITICAL'
        elif car >= self.CAR_THRESHOLD_HIGH and volume_ratio >= self.VOLUME_SPIKE_THRESHOLD and p_value < 0.05:
            return 'HIGH'
        elif car >= self.CAR_THRESHOLD_MEDIUM and p_value < 0.1:
            return 'MEDIUM'
        else:
            return 'LOW'


def detect_pre_announcement_signals(
    insider_transactions: List[Dict[str, Any]],
    stock_data: Dict[str, Any],
    announcements: List[Dict[str, Any]]
) -> List[PreAnnouncementSignal]:
    """
    Convenience function for pre-announcement trading detection.
    
    Args:
        insider_transactions: List of insider transaction records
        stock_data: Dictionary with 'prices', 'volumes', 'market_returns'
        announcements: List of material announcement records
    
    Returns:
        List of pre-announcement signals
    """
    detector = PreAnnouncementDetector()
    
    return detector.detect_pre_announcement_trading(
        insider_transactions=insider_transactions,
        stock_prices=stock_data.get('prices', {}),
        market_returns=stock_data.get('market_returns', {}),
        volume_data=stock_data.get('volumes', {}),
        announcements=announcements
    )
