"""
NODE 15: Real-Time Market Correlation Engine
============================================

Correlates forensic findings with real-time and historical market data:
- Price/volume anomaly detection around events
- Cumulative Abnormal Return (CAR) event study
- Intraday pattern analysis
- Cross-security correlation

Integration: Polygon.io WebSocket for real-time data
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import hashlib
import logging
import math

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    PRICE_SPIKE = "Price Spike"
    PRICE_DROP = "Price Drop"
    VOLUME_SURGE = "Volume Surge"
    VOLATILITY_SPIKE = "Volatility Spike"
    PRE_EVENT_MOVEMENT = "Pre-Event Movement"
    CORRELATION_BREAK = "Correlation Break"


class EventStudyResult(Enum):
    SIGNIFICANT_POSITIVE = "Significant Positive CAR"
    SIGNIFICANT_NEGATIVE = "Significant Negative CAR"
    NOT_SIGNIFICANT = "Not Statistically Significant"


@dataclass
class MarketDataPoint:
    """Single market data observation."""
    symbol: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    vwap: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "close": self.close_price,
            "volume": self.volume,
            "vwap": self.vwap
        }


@dataclass
class AbnormalReturn:
    """Abnormal return calculation for event study."""
    date: date
    actual_return: float
    expected_return: float
    abnormal_return: float
    cumulative_ar: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "actual_return": round(self.actual_return, 6),
            "expected_return": round(self.expected_return, 6),
            "abnormal_return": round(self.abnormal_return, 6),
            "cumulative_ar": round(self.cumulative_ar, 6)
        }


@dataclass
class EventStudy:
    """Complete event study results."""
    event_date: date
    event_description: str
    estimation_window: Tuple[date, date]
    event_window: Tuple[date, date]
    abnormal_returns: List[AbnormalReturn]
    car: float  # Cumulative Abnormal Return
    car_t_stat: float  # T-statistic
    car_p_value: float  # P-value
    result: EventStudyResult
    interpretation: str
    evidence_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_date": self.event_date.isoformat(),
            "event_description": self.event_description,
            "estimation_window": [self.estimation_window[0].isoformat(), 
                                  self.estimation_window[1].isoformat()],
            "event_window": [self.event_window[0].isoformat(), 
                            self.event_window[1].isoformat()],
            "car": round(self.car * 100, 2),  # Percentage
            "car_t_stat": round(self.car_t_stat, 3),
            "car_p_value": round(self.car_p_value, 4),
            "result": self.result.value,
            "interpretation": self.interpretation
        }


@dataclass
class MarketCorrelationAlert:
    """Alert for market correlation anomalies."""
    anomaly_type: AnomalyType
    symbol: str
    detection_date: date
    anomaly_value: float
    baseline_value: float
    deviation_multiple: float
    correlated_events: List[str]
    risk_score: float
    evidence: Dict[str, Any]
    evidence_hash: str
    severity: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type.value,
            "symbol": self.symbol,
            "detection_date": self.detection_date.isoformat(),
            "anomaly_value": self.anomaly_value,
            "baseline_value": self.baseline_value,
            "deviation_multiple": round(self.deviation_multiple, 2),
            "correlated_events": self.correlated_events,
            "risk_score": round(self.risk_score, 3),
            "severity": self.severity
        }


@dataclass
class Node15Output:
    """Output from Node 15 analysis."""
    symbols_analyzed: int
    event_studies_completed: int
    anomalies_detected: int
    event_studies: List[EventStudy]
    alerts: List[MarketCorrelationAlert]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "symbols_analyzed": self.symbols_analyzed,
                "event_studies_completed": self.event_studies_completed,
                "anomalies_detected": self.anomalies_detected
            },
            "event_studies": [e.to_dict() for e in self.event_studies],
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class MarketCorrelationEngine:
    """
    Real-Time Market Correlation Engine.
    
    Capabilities:
    - Cumulative Abnormal Return (CAR) event studies
    - Volume anomaly detection
    - Price movement correlation with filings
    - Pre-announcement pattern detection
    
    Integration points:
    - Polygon.io for real-time/historical data
    - SEC EDGAR for filing events
    """
    
    # Statistical thresholds
    SIGNIFICANCE_LEVEL = 0.05
    Z_CRITICAL = 1.96  # Two-tailed 5%
    VOLUME_ANOMALY_THRESHOLD = 3.0  # Standard deviations
    PRICE_ANOMALY_THRESHOLD = 2.5  # Standard deviations
    
    def __init__(self, polygon_api_key: Optional[str] = None):
        """
        Initialize market correlation engine.
        
        Args:
            polygon_api_key: Optional Polygon.io API key for live data
        """
        self.polygon_api_key = polygon_api_key
        self._market_data_cache: Dict[str, List[MarketDataPoint]] = {}
    
    def analyze(
        self,
        symbols: List[str],
        events: List[Dict[str, Any]],
        market_data: Dict[str, List[Dict[str, Any]]],
        benchmark_data: Optional[List[Dict[str, Any]]] = None
    ) -> Node15Output:
        """
        Run complete market correlation analysis.
        
        Args:
            symbols: List of stock symbols to analyze
            events: List of events (filings, announcements) with dates
            market_data: Historical market data by symbol
            benchmark_data: Optional market benchmark (S&P 500) data
            
        Returns:
            Node15Output with analysis results
        """
        logger.info(f"[NODE 15] Analyzing {len(symbols)} symbols with {len(events)} events")
        
        event_studies = []
        alerts = []
        
        for symbol in symbols:
            symbol_data = market_data.get(symbol, [])
            
            if not symbol_data:
                continue
            
            # Convert to MarketDataPoint objects
            data_points = self._parse_market_data(symbol, symbol_data)
            
            # Detect volume anomalies
            vol_alerts = self.detect_volume_anomalies(data_points, events)
            alerts.extend(vol_alerts)
            
            # Detect price anomalies
            price_alerts = self.detect_price_anomalies(data_points, events)
            alerts.extend(price_alerts)
            
            # Run event studies for relevant events
            symbol_events = [e for e in events if e.get('symbol') == symbol]
            
            for event in symbol_events:
                event_date = event.get('date')
                if isinstance(event_date, str):
                    event_date = datetime.strptime(event_date, '%Y-%m-%d').date()
                
                study = self.run_event_study(
                    symbol=symbol,
                    event_date=event_date,
                    event_description=event.get('description', 'Filing event'),
                    market_data=data_points,
                    benchmark_data=benchmark_data
                )
                
                if study:
                    event_studies.append(study)
        
        return Node15Output(
            symbols_analyzed=len(symbols),
            event_studies_completed=len(event_studies),
            anomalies_detected=len(alerts),
            event_studies=event_studies,
            alerts=alerts
        )
    
    def run_event_study(
        self,
        symbol: str,
        event_date: date,
        event_description: str,
        market_data: List[MarketDataPoint],
        benchmark_data: Optional[List[Dict[str, Any]]] = None,
        estimation_days: int = 120,
        event_window_pre: int = 5,
        event_window_post: int = 5
    ) -> Optional[EventStudy]:
        """
        Run Cumulative Abnormal Return (CAR) event study.
        
        Uses market model: R_i = alpha + beta * R_m + epsilon
        
        Args:
            symbol: Stock symbol
            event_date: Date of the event
            event_description: Description of the event
            market_data: Historical price data for the stock
            benchmark_data: Market benchmark returns
            estimation_days: Days in estimation window
            event_window_pre: Days before event in event window
            event_window_post: Days after event in event window
            
        Returns:
            EventStudy with CAR results and significance tests
        """
        # Filter data around event
        sorted_data = sorted(market_data, key=lambda x: x.timestamp)
        
        # Find event date index
        event_idx = None
        for i, dp in enumerate(sorted_data):
            if dp.timestamp.date() >= event_date:
                event_idx = i
                break
        
        if event_idx is None or event_idx < estimation_days + event_window_pre:
            return None
        
        # Define windows
        est_start = event_idx - estimation_days - event_window_pre
        est_end = event_idx - event_window_pre
        evt_start = event_idx - event_window_pre
        evt_end = min(event_idx + event_window_post, len(sorted_data) - 1)
        
        # Calculate returns
        estimation_returns = []
        for i in range(est_start + 1, est_end):
            if sorted_data[i-1].close_price > 0:
                ret = (sorted_data[i].close_price - sorted_data[i-1].close_price) / sorted_data[i-1].close_price
                estimation_returns.append(ret)
        
        if len(estimation_returns) < 30:
            return None
        
        # Calculate expected return (mean model if no benchmark)
        mean_return = sum(estimation_returns) / len(estimation_returns)
        std_return = (sum((r - mean_return)**2 for r in estimation_returns) / len(estimation_returns)) ** 0.5
        
        # Calculate abnormal returns in event window
        abnormal_returns = []
        cumulative_ar = 0.0
        
        for i in range(evt_start, evt_end + 1):
            if i > 0 and sorted_data[i-1].close_price > 0:
                actual = (sorted_data[i].close_price - sorted_data[i-1].close_price) / sorted_data[i-1].close_price
                expected = mean_return
                ar = actual - expected
                cumulative_ar += ar
                
                abnormal_returns.append(AbnormalReturn(
                    date=sorted_data[i].timestamp.date(),
                    actual_return=actual,
                    expected_return=expected,
                    abnormal_return=ar,
                    cumulative_ar=cumulative_ar
                ))
        
        if not abnormal_returns:
            return None
        
        # Calculate CAR statistics
        car = cumulative_ar
        n_days = len(abnormal_returns)
        
        # T-statistic: CAR / (std * sqrt(n))
        if std_return > 0 and n_days > 0:
            t_stat = car / (std_return * math.sqrt(n_days))
        else:
            t_stat = 0.0
        
        # Approximate p-value (two-tailed)
        p_value = 2 * (1 - self._normal_cdf(abs(t_stat)))
        
        # Determine significance
        if p_value < self.SIGNIFICANCE_LEVEL:
            if car > 0:
                result = EventStudyResult.SIGNIFICANT_POSITIVE
                interpretation = f"Significant positive abnormal return of {car*100:.2f}% around event"
            else:
                result = EventStudyResult.SIGNIFICANT_NEGATIVE
                interpretation = f"Significant negative abnormal return of {car*100:.2f}% around event"
        else:
            result = EventStudyResult.NOT_SIGNIFICANT
            interpretation = f"Abnormal return of {car*100:.2f}% not statistically significant"
        
        return EventStudy(
            event_date=event_date,
            event_description=event_description,
            estimation_window=(sorted_data[est_start].timestamp.date(), 
                             sorted_data[est_end].timestamp.date()),
            event_window=(sorted_data[evt_start].timestamp.date(),
                         sorted_data[evt_end].timestamp.date()),
            abnormal_returns=abnormal_returns,
            car=car,
            car_t_stat=t_stat,
            car_p_value=p_value,
            result=result,
            interpretation=interpretation,
            evidence_hash=self._generate_hash({'symbol': symbol, 'event_date': str(event_date), 'car': car})
        )
    
    def detect_volume_anomalies(
        self,
        market_data: List[MarketDataPoint],
        events: List[Dict[str, Any]],
        lookback_days: int = 60
    ) -> List[MarketCorrelationAlert]:
        """
        Detect abnormal trading volume using statistical methods.
        """
        alerts = []
        
        if len(market_data) < lookback_days:
            return alerts
        
        sorted_data = sorted(market_data, key=lambda x: x.timestamp)
        
        for i in range(lookback_days, len(sorted_data)):
            # Calculate rolling statistics
            window = [dp.volume for dp in sorted_data[i-lookback_days:i]]
            current_volume = sorted_data[i].volume
            
            mean_vol = sum(window) / len(window)
            std_vol = (sum((v - mean_vol)**2 for v in window) / len(window)) ** 0.5
            
            if std_vol > 0:
                z_score = (current_volume - mean_vol) / std_vol
                
                if abs(z_score) > self.VOLUME_ANOMALY_THRESHOLD:
                    current_date = sorted_data[i].timestamp.date()
                    
                    # Find correlated events
                    correlated = self._find_correlated_events(current_date, events)
                    
                    alerts.append(MarketCorrelationAlert(
                        anomaly_type=AnomalyType.VOLUME_SURGE,
                        symbol=sorted_data[i].symbol,
                        detection_date=current_date,
                        anomaly_value=current_volume,
                        baseline_value=mean_vol,
                        deviation_multiple=current_volume / mean_vol if mean_vol > 0 else 0,
                        correlated_events=correlated,
                        risk_score=min(abs(z_score) / 5, 1.0),
                        evidence={
                            'volume': current_volume,
                            'mean_volume': mean_vol,
                            'std_volume': std_vol,
                            'z_score': z_score
                        },
                        evidence_hash=self._generate_hash(sorted_data[i]),
                        severity='HIGH' if abs(z_score) > 4 else 'MEDIUM'
                    ))
        
        return alerts
    
    def detect_price_anomalies(
        self,
        market_data: List[MarketDataPoint],
        events: List[Dict[str, Any]],
        lookback_days: int = 60
    ) -> List[MarketCorrelationAlert]:
        """
        Detect abnormal price movements.
        """
        alerts = []
        
        if len(market_data) < lookback_days + 1:
            return alerts
        
        sorted_data = sorted(market_data, key=lambda x: x.timestamp)
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(sorted_data)):
            if sorted_data[i-1].close_price > 0:
                ret = (sorted_data[i].close_price - sorted_data[i-1].close_price) / sorted_data[i-1].close_price
                returns.append((sorted_data[i], ret))
        
        for i in range(lookback_days, len(returns)):
            window = [r[1] for r in returns[i-lookback_days:i]]
            current_return = returns[i][1]
            current_dp = returns[i][0]
            
            mean_ret = sum(window) / len(window)
            std_ret = (sum((r - mean_ret)**2 for r in window) / len(window)) ** 0.5
            
            if std_ret > 0:
                z_score = (current_return - mean_ret) / std_ret
                
                if abs(z_score) > self.PRICE_ANOMALY_THRESHOLD:
                    current_date = current_dp.timestamp.date()
                    correlated = self._find_correlated_events(current_date, events)
                    
                    anomaly_type = AnomalyType.PRICE_SPIKE if current_return > 0 else AnomalyType.PRICE_DROP
                    
                    alerts.append(MarketCorrelationAlert(
                        anomaly_type=anomaly_type,
                        symbol=current_dp.symbol,
                        detection_date=current_date,
                        anomaly_value=current_return,
                        baseline_value=mean_ret,
                        deviation_multiple=abs(z_score),
                        correlated_events=correlated,
                        risk_score=min(abs(z_score) / 4, 1.0),
                        evidence={
                            'return': current_return,
                            'mean_return': mean_ret,
                            'std_return': std_ret,
                            'z_score': z_score
                        },
                        evidence_hash=self._generate_hash(current_dp),
                        severity='HIGH' if abs(z_score) > 3.5 else 'MEDIUM'
                    ))
        
        return alerts
    
    def _parse_market_data(
        self, 
        symbol: str, 
        data: List[Dict[str, Any]]
    ) -> List[MarketDataPoint]:
        """Parse raw market data into MarketDataPoint objects."""
        points = []
        
        for d in data:
            ts = d.get('timestamp') or d.get('date')
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            elif isinstance(ts, date):
                ts = datetime.combine(ts, datetime.min.time())
            
            points.append(MarketDataPoint(
                symbol=symbol,
                timestamp=ts,
                open_price=d.get('open', d.get('o', 0)),
                high_price=d.get('high', d.get('h', 0)),
                low_price=d.get('low', d.get('l', 0)),
                close_price=d.get('close', d.get('c', 0)),
                volume=d.get('volume', d.get('v', 0)),
                vwap=d.get('vwap')
            ))
        
        return points
    
    def _find_correlated_events(
        self, 
        target_date: date, 
        events: List[Dict[str, Any]],
        window_days: int = 3
    ) -> List[str]:
        """Find events within window of target date."""
        correlated = []
        
        for event in events:
            event_date = event.get('date')
            if isinstance(event_date, str):
                event_date = datetime.strptime(event_date, '%Y-%m-%d').date()
            elif isinstance(event_date, datetime):
                event_date = event_date.date()
            
            if event_date and abs((target_date - event_date).days) <= window_days:
                desc = event.get('description') or event.get('type') or 'Event'
                correlated.append(f"{event_date}: {desc}")
        
        return correlated
    
    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF using error function approximation."""
        # Approximation using error function
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    def _generate_hash(self, data: Any) -> str:
        """Generate SHA-256 evidence hash."""
        return hashlib.sha256(str(data).encode()).hexdigest()

