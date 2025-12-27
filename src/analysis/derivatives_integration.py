"""
Derivatives Integration Module
================================

Integrates options flow data with earnings analysis and insider trading patterns
to detect suspicious pre-event positioning and information leakage.

Key Features:
1. Pre-earnings options activity analysis
2. Put/call ratio anomaly detection before announcements
3. Unusual options volume spike detection
4. Deep OTM options purchase flagging
5. Block trade detection before material events
6. Form 4 insider transaction correlation with options activity

Legal Framework:
- 17 CFR § 240.10b-5 (Securities fraud)
- 17 CFR § 240.10b5-1 (Insider trading - affirmative defense)
- Reg FD (17 CFR § 243.100) (Selective disclosure)
- Section 16(b) (Short-swing profits)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class OptionsAnomalyType(Enum):
    """Types of options trading anomalies."""
    PRE_EARNINGS_SPIKE = "PRE_EARNINGS_SPIKE"
    PUT_CALL_RATIO_ANOMALY = "PUT_CALL_RATIO_ANOMALY"
    UNUSUAL_VOLUME = "UNUSUAL_VOLUME"
    DEEP_OTM_PURCHASE = "DEEP_OTM_PURCHASE"
    BLOCK_TRADE = "BLOCK_TRADE"
    INSIDER_OPTIONS_CORRELATION = "INSIDER_OPTIONS_CORRELATION"


class AnomalySeverity(Enum):
    """Severity levels for derivatives anomalies."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class OptionsFlow:
    """Represents options trading flow data."""
    ticker: str
    trade_date: date
    contract_type: str  # 'CALL' or 'PUT'
    strike_price: float
    expiration_date: date
    volume: int
    open_interest: int
    premium: float
    is_block_trade: bool = False
    days_to_expiration: Optional[int] = None
    moneyness: Optional[float] = None  # (strike - spot) / spot
    
    def __post_init__(self):
        """Calculate derived fields."""
        if self.expiration_date and self.trade_date:
            self.days_to_expiration = (self.expiration_date - self.trade_date).days
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "trade_date": self.trade_date.isoformat() if isinstance(self.trade_date, date) else self.trade_date,
            "contract_type": self.contract_type,
            "strike_price": self.strike_price,
            "expiration_date": self.expiration_date.isoformat() if isinstance(self.expiration_date, date) else self.expiration_date,
            "volume": self.volume,
            "open_interest": self.open_interest,
            "premium": self.premium,
            "is_block_trade": self.is_block_trade,
            "days_to_expiration": self.days_to_expiration,
            "moneyness": round(self.moneyness, 4) if self.moneyness else None
        }


@dataclass
class DerivativesAnomaly:
    """Represents a detected derivatives trading anomaly."""
    anomaly_type: OptionsAnomalyType
    severity: AnomalySeverity
    confidence: float
    description: str
    evidence: Dict[str, Any]
    ticker: str
    detection_date: date
    options_involved: List[str]
    estimated_profit: Optional[float] = None
    regulatory_citations: List[str] = field(default_factory=list)
    recommended_agencies: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "confidence": round(self.confidence, 3),
            "description": self.description,
            "evidence": self.evidence,
            "ticker": self.ticker,
            "detection_date": self.detection_date.isoformat() if isinstance(self.detection_date, date) else self.detection_date,
            "options_involved": self.options_involved,
            "estimated_profit": round(self.estimated_profit, 2) if self.estimated_profit else None,
            "regulatory_citations": self.regulatory_citations,
            "recommended_agencies": self.recommended_agencies,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class DerivativesAnalysisResult:
    """Result from derivatives integration analysis."""
    analysis_date: datetime
    ticker: str
    company_name: str
    options_analyzed: int
    anomalies_found: int
    anomalies: List[DerivativesAnomaly]
    pre_earnings_flags: int
    insider_correlations: int
    total_suspicious_volume: int
    alerts: List[str]
    execution_time_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_date": self.analysis_date.isoformat(),
            "ticker": self.ticker,
            "company_name": self.company_name,
            "options_analyzed": self.options_analyzed,
            "anomalies_found": self.anomalies_found,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "pre_earnings_flags": self.pre_earnings_flags,
            "insider_correlations": self.insider_correlations,
            "total_suspicious_volume": self.total_suspicious_volume,
            "alerts": self.alerts,
            "execution_time_seconds": round(self.execution_time_seconds, 2)
        }


class DerivativesIntegrationEngine:
    """
    Derivatives Integration Engine
    
    Analyzes options flow data in conjunction with:
    - Earnings call dates (Node 12)
    - Material events (8-K filings)
    - Insider Form 4 transactions
    - Market price movements (Node 15)
    """
    
    # Thresholds for anomaly detection
    VOLUME_SPIKE_THRESHOLD = 3.0  # 3x average volume
    PUT_CALL_RATIO_THRESHOLD = 2.5  # Unusual put/call ratio
    DEEP_OTM_THRESHOLD = 0.15  # 15% out of the money
    BLOCK_TRADE_VOLUME = 10000  # Contracts threshold for block trades
    PRE_EVENT_WINDOW_DAYS = 7  # Days before earnings/material events
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def analyze(
        self,
        ticker: str,
        company_name: str,
        options_flow: List[OptionsFlow],
        earnings_dates: List[date],
        material_event_dates: Optional[List[date]] = None,
        insider_transactions: Optional[List[Dict[str, Any]]] = None,
        spot_prices: Optional[Dict[date, float]] = None
    ) -> DerivativesAnalysisResult:
        """
        Execute derivatives integration analysis.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Company name
            options_flow: List of options trading data
            earnings_dates: List of earnings announcement dates
            material_event_dates: List of material event dates (from 8-K)
            insider_transactions: List of Form 4 insider transactions
            spot_prices: Historical spot prices for moneyness calculation
        
        Returns:
            DerivativesAnalysisResult with detected anomalies
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"=== Derivatives Integration Analysis for {ticker} ===")
        self.logger.info(f"Analyzing {len(options_flow)} options contracts...")
        
        anomalies: List[DerivativesAnomaly] = []
        alerts: List[str] = []
        
        # Calculate moneyness if spot prices provided
        if spot_prices:
            for option in options_flow:
                if option.trade_date in spot_prices:
                    spot = spot_prices[option.trade_date]
                    option.moneyness = (option.strike_price - spot) / spot
        
        try:
            # Analysis 1: Pre-earnings options activity
            pre_earnings_anomalies = self._analyze_pre_earnings_activity(
                options_flow, earnings_dates
            )
            anomalies.extend(pre_earnings_anomalies)
            if pre_earnings_anomalies:
                alerts.append(f"Detected {len(pre_earnings_anomalies)} pre-earnings anomalies")
            
            # Analysis 2: Put/call ratio anomalies
            putcall_anomalies = self._detect_putcall_ratio_anomalies(
                options_flow, earnings_dates, material_event_dates
            )
            anomalies.extend(putcall_anomalies)
            if putcall_anomalies:
                alerts.append(f"Detected {len(putcall_anomalies)} put/call ratio anomalies")
            
            # Analysis 3: Unusual volume spikes
            volume_anomalies = self._detect_volume_spikes(options_flow)
            anomalies.extend(volume_anomalies)
            if volume_anomalies:
                alerts.append(f"Detected {len(volume_anomalies)} unusual volume spikes")
            
            # Analysis 4: Deep OTM options purchases
            otm_anomalies = self._detect_deep_otm_purchases(options_flow, spot_prices)
            anomalies.extend(otm_anomalies)
            if otm_anomalies:
                alerts.append(f"Detected {len(otm_anomalies)} deep OTM purchases")
            
            # Analysis 5: Block trades before material events
            block_anomalies = self._detect_block_trades(
                options_flow, earnings_dates, material_event_dates
            )
            anomalies.extend(block_anomalies)
            if block_anomalies:
                alerts.append(f"Detected {len(block_anomalies)} suspicious block trades")
            
            # Analysis 6: Insider-options correlation
            if insider_transactions:
                insider_anomalies = self._correlate_insider_options(
                    options_flow, insider_transactions
                )
                anomalies.extend(insider_anomalies)
                if insider_anomalies:
                    alerts.append(f"CRITICAL: {len(insider_anomalies)} insider-options correlations")
            
        except Exception as e:
            self.logger.error(f"Error during derivatives analysis: {e}", exc_info=True)
            alerts.append(f"Analysis error: {str(e)}")
        
        # Calculate aggregate metrics
        pre_earnings_flags = len([a for a in anomalies if a.anomaly_type == OptionsAnomalyType.PRE_EARNINGS_SPIKE])
        insider_correlations = len([a for a in anomalies if a.anomaly_type == OptionsAnomalyType.INSIDER_OPTIONS_CORRELATION])
        total_suspicious_volume = sum(
            a.evidence.get('volume', 0) for a in anomalies
            if 'volume' in a.evidence
        )
        
        execution_time = time.time() - start_time
        
        result = DerivativesAnalysisResult(
            analysis_date=datetime.utcnow(),
            ticker=ticker,
            company_name=company_name,
            options_analyzed=len(options_flow),
            anomalies_found=len(anomalies),
            anomalies=anomalies,
            pre_earnings_flags=pre_earnings_flags,
            insider_correlations=insider_correlations,
            total_suspicious_volume=total_suspicious_volume,
            alerts=alerts,
            execution_time_seconds=execution_time
        )
        
        self.logger.info(f"✓ Derivatives analysis complete: {len(anomalies)} anomalies detected in {execution_time:.2f}s")
        return result
    
    def _analyze_pre_earnings_activity(
        self,
        options_flow: List[OptionsFlow],
        earnings_dates: List[date]
    ) -> List[DerivativesAnomaly]:
        """Detect unusual options activity before earnings announcements."""
        anomalies = []
        
        for earnings_date in earnings_dates:
            # Look for options activity in the week before earnings
            pre_earnings_window_start = earnings_date - timedelta(days=self.PRE_EVENT_WINDOW_DAYS)
            pre_earnings_window_end = earnings_date - timedelta(days=1)
            
            pre_earnings_options = [
                opt for opt in options_flow
                if pre_earnings_window_start <= opt.trade_date <= pre_earnings_window_end
            ]
            
            if not pre_earnings_options:
                continue
            
            # Calculate total volume and premium in pre-earnings window
            total_volume = sum(opt.volume for opt in pre_earnings_options)
            total_premium = sum(opt.premium * opt.volume for opt in pre_earnings_options)
            
            # Compare to baseline (options NOT in pre-earnings windows)
            baseline_options = [
                opt for opt in options_flow
                if not any(
                    ed - timedelta(days=self.PRE_EVENT_WINDOW_DAYS) <= opt.trade_date <= ed - timedelta(days=1)
                    for ed in earnings_dates
                )
            ]
            
            if baseline_options:
                baseline_avg_volume = sum(opt.volume for opt in baseline_options) / len(baseline_options)
                pre_earnings_avg_volume = total_volume / len(pre_earnings_options) if pre_earnings_options else 0
                
                # Flag if pre-earnings volume is significantly elevated
                if pre_earnings_avg_volume > baseline_avg_volume * self.VOLUME_SPIKE_THRESHOLD:
                    volume_ratio = pre_earnings_avg_volume / baseline_avg_volume if baseline_avg_volume > 0 else 0
                    
                    anomaly = DerivativesAnomaly(
                        anomaly_type=OptionsAnomalyType.PRE_EARNINGS_SPIKE,
                        severity=AnomalySeverity.HIGH,
                        confidence=0.80,
                        description=f"Options volume {volume_ratio:.1f}x baseline in {self.PRE_EVENT_WINDOW_DAYS} days before earnings on {earnings_date}",
                        evidence={
                            "earnings_date": earnings_date.isoformat(),
                            "pre_earnings_volume": total_volume,
                            "baseline_avg_volume": baseline_avg_volume,
                            "pre_earnings_avg_volume": pre_earnings_avg_volume,
                            "volume_ratio": volume_ratio,
                            "total_premium": total_premium,
                            "contracts_count": len(pre_earnings_options)
                        },
                        ticker=options_flow[0].ticker if options_flow else "UNKNOWN",
                        detection_date=earnings_date,
                        options_involved=[f"{opt.trade_date}:{opt.contract_type}:{opt.strike_price}" for opt in pre_earnings_options[:10]],
                        estimated_profit=total_premium * 0.50,  # Assume 50% profit on informed trades
                        regulatory_citations=[
                            "17 CFR § 240.10b-5 (Securities fraud)",
                            "17 CFR § 243.100 (Reg FD - selective disclosure)"
                        ],
                        recommended_agencies=["SEC", "DOJ"]
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_putcall_ratio_anomalies(
        self,
        options_flow: List[OptionsFlow],
        earnings_dates: List[date],
        material_event_dates: Optional[List[date]]
    ) -> List[DerivativesAnomaly]:
        """Detect unusual put/call ratios before announcements."""
        anomalies = []
        
        # Combine all event dates
        event_dates = earnings_dates.copy()
        if material_event_dates:
            event_dates.extend(material_event_dates)
        
        for event_date in event_dates:
            # Pre-event window
            window_start = event_date - timedelta(days=self.PRE_EVENT_WINDOW_DAYS)
            window_end = event_date - timedelta(days=1)
            
            window_options = [
                opt for opt in options_flow
                if window_start <= opt.trade_date <= window_end
            ]
            
            if not window_options:
                continue
            
            # Calculate put/call ratio by volume
            put_volume = sum(opt.volume for opt in window_options if opt.contract_type.upper() == 'PUT')
            call_volume = sum(opt.volume for opt in window_options if opt.contract_type.upper() == 'CALL')
            
            if call_volume == 0:
                continue
            
            put_call_ratio = put_volume / call_volume
            
            # Flag unusual put/call ratios (very high indicates bearish positioning)
            if put_call_ratio > self.PUT_CALL_RATIO_THRESHOLD:
                anomaly = DerivativesAnomaly(
                    anomaly_type=OptionsAnomalyType.PUT_CALL_RATIO_ANOMALY,
                    severity=AnomalySeverity.HIGH,
                    confidence=0.75,
                    description=f"Unusual put/call ratio {put_call_ratio:.2f} before event on {event_date} (threshold: {self.PUT_CALL_RATIO_THRESHOLD})",
                    evidence={
                        "event_date": event_date.isoformat(),
                        "put_volume": put_volume,
                        "call_volume": call_volume,
                        "put_call_ratio": put_call_ratio,
                        "window_days": self.PRE_EVENT_WINDOW_DAYS
                    },
                    ticker=options_flow[0].ticker if options_flow else "UNKNOWN",
                    detection_date=event_date,
                    options_involved=[f"{opt.trade_date}:PUT:{opt.strike_price}" for opt in window_options if opt.contract_type.upper() == 'PUT'][:10],
                    regulatory_citations=[
                        "17 CFR § 240.10b-5 (Securities fraud)",
                        "17 CFR § 240.10b5-1 (Insider trading)"
                    ],
                    recommended_agencies=["SEC", "DOJ"]
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_volume_spikes(
        self,
        options_flow: List[OptionsFlow]
    ) -> List[DerivativesAnomaly]:
        """Detect unusual volume spikes."""
        anomalies = []
        
        if len(options_flow) < 10:
            return anomalies
        
        # Calculate average volume
        avg_volume = sum(opt.volume for opt in options_flow) / len(options_flow)
        
        # Flag options with volume significantly above average
        for option in options_flow:
            if option.volume > avg_volume * self.VOLUME_SPIKE_THRESHOLD:
                volume_ratio = option.volume / avg_volume if avg_volume > 0 else 0
                
                anomaly = DerivativesAnomaly(
                    anomaly_type=OptionsAnomalyType.UNUSUAL_VOLUME,
                    severity=AnomalySeverity.MEDIUM,
                    confidence=0.70,
                    description=f"Unusual volume spike: {option.volume:,} contracts ({volume_ratio:.1f}x average) on {option.trade_date}",
                    evidence={
                        "trade_date": option.trade_date.isoformat(),
                        "volume": option.volume,
                        "average_volume": avg_volume,
                        "volume_ratio": volume_ratio,
                        "contract_type": option.contract_type,
                        "strike": option.strike_price,
                        "premium": option.premium
                    },
                    ticker=option.ticker,
                    detection_date=option.trade_date,
                    options_involved=[f"{option.trade_date}:{option.contract_type}:{option.strike_price}"],
                    regulatory_citations=[
                        "17 CFR § 240.10b-5 (Securities fraud)"
                    ],
                    recommended_agencies=["SEC"]
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_deep_otm_purchases(
        self,
        options_flow: List[OptionsFlow],
        spot_prices: Optional[Dict[date, float]]
    ) -> List[DerivativesAnomaly]:
        """Detect deep out-of-the-money options purchases (lottery ticket behavior)."""
        anomalies = []
        
        if not spot_prices:
            self.logger.debug("No spot prices provided, skipping deep OTM detection")
            return anomalies
        
        for option in options_flow:
            if option.trade_date not in spot_prices:
                continue
            
            # Check if option is deep OTM
            if option.moneyness and abs(option.moneyness) > self.DEEP_OTM_THRESHOLD:
                # For calls: moneyness > 0.15 (strike 15% above spot)
                # For puts: moneyness < -0.15 (strike 15% below spot)
                is_deep_otm_call = option.contract_type.upper() == 'CALL' and option.moneyness > self.DEEP_OTM_THRESHOLD
                is_deep_otm_put = option.contract_type.upper() == 'PUT' and option.moneyness < -self.DEEP_OTM_THRESHOLD
                
                if (is_deep_otm_call or is_deep_otm_put) and option.volume > 1000:
                    anomaly = DerivativesAnomaly(
                        anomaly_type=OptionsAnomalyType.DEEP_OTM_PURCHASE,
                        severity=AnomalySeverity.MEDIUM,
                        confidence=0.68,
                        description=f"Large deep OTM {option.contract_type} purchase: {option.volume:,} contracts, {abs(option.moneyness)*100:.1f}% OTM",
                        evidence={
                            "trade_date": option.trade_date.isoformat(),
                            "contract_type": option.contract_type,
                            "strike": option.strike_price,
                            "spot_price": spot_prices[option.trade_date],
                            "moneyness": option.moneyness,
                            "volume": option.volume,
                            "premium": option.premium
                        },
                        ticker=option.ticker,
                        detection_date=option.trade_date,
                        options_involved=[f"{option.trade_date}:{option.contract_type}:{option.strike_price}"],
                        regulatory_citations=[
                            "17 CFR § 240.10b-5 (Securities fraud)"
                        ],
                        recommended_agencies=["SEC"]
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_block_trades(
        self,
        options_flow: List[OptionsFlow],
        earnings_dates: List[date],
        material_event_dates: Optional[List[date]]
    ) -> List[DerivativesAnomaly]:
        """Detect block trades before material events."""
        anomalies = []
        
        # Combine all event dates
        event_dates = earnings_dates.copy()
        if material_event_dates:
            event_dates.extend(material_event_dates)
        
        # Find block trades
        block_trades = [opt for opt in options_flow if opt.volume >= self.BLOCK_TRADE_VOLUME]
        
        for block_trade in block_trades:
            # Check if block trade occurred before any material event
            for event_date in event_dates:
                days_before_event = (event_date - block_trade.trade_date).days
                
                if 0 < days_before_event <= self.PRE_EVENT_WINDOW_DAYS:
                    anomaly = DerivativesAnomaly(
                        anomaly_type=OptionsAnomalyType.BLOCK_TRADE,
                        severity=AnomalySeverity.HIGH,
                        confidence=0.78,
                        description=f"Block trade {days_before_event} days before event: {block_trade.volume:,} {block_trade.contract_type} contracts",
                        evidence={
                            "trade_date": block_trade.trade_date.isoformat(),
                            "event_date": event_date.isoformat(),
                            "days_before_event": days_before_event,
                            "contract_type": block_trade.contract_type,
                            "volume": block_trade.volume,
                            "strike": block_trade.strike_price,
                            "premium": block_trade.premium,
                            "total_value": block_trade.premium * block_trade.volume
                        },
                        ticker=block_trade.ticker,
                        detection_date=block_trade.trade_date,
                        options_involved=[f"{block_trade.trade_date}:{block_trade.contract_type}:{block_trade.strike_price}"],
                        estimated_profit=block_trade.premium * block_trade.volume * 0.50,
                        regulatory_citations=[
                            "17 CFR § 240.10b-5 (Securities fraud)",
                            "17 CFR § 240.10b5-1 (Insider trading)"
                        ],
                        recommended_agencies=["SEC", "DOJ"]
                    )
                    anomalies.append(anomaly)
                    break  # Only flag once per block trade
        
        return anomalies
    
    def _correlate_insider_options(
        self,
        options_flow: List[OptionsFlow],
        insider_transactions: List[Dict[str, Any]]
    ) -> List[DerivativesAnomaly]:
        """Correlate Form 4 insider transactions with options activity."""
        anomalies = []
        
        for insider_txn in insider_transactions:
            txn_date = insider_txn.get('transaction_date')
            if not txn_date:
                continue
            
            # Convert to date object if needed
            if isinstance(txn_date, str):
                try:
                    txn_date = datetime.strptime(txn_date, '%Y-%m-%d').date()
                except ValueError:
                    continue
            
            # Look for unusual options activity around insider transaction date
            window_start = txn_date - timedelta(days=3)
            window_end = txn_date + timedelta(days=3)
            
            related_options = [
                opt for opt in options_flow
                if window_start <= opt.trade_date <= window_end
                and opt.volume >= 1000  # Significant volume
            ]
            
            if related_options:
                total_volume = sum(opt.volume for opt in related_options)
                total_premium = sum(opt.premium * opt.volume for opt in related_options)
                
                anomaly = DerivativesAnomaly(
                    anomaly_type=OptionsAnomalyType.INSIDER_OPTIONS_CORRELATION,
                    severity=AnomalySeverity.CRITICAL,
                    confidence=0.85,
                    description=f"Options activity correlated with insider transaction: {total_volume:,} contracts around {txn_date}",
                    evidence={
                        "insider_transaction_date": txn_date.isoformat(),
                        "insider_name": insider_txn.get('reporter_name', 'Unknown'),
                        "insider_transaction_type": insider_txn.get('transaction_type', 'Unknown'),
                        "insider_shares": insider_txn.get('shares', 0),
                        "options_volume": total_volume,
                        "options_premium": total_premium,
                        "contracts_count": len(related_options)
                    },
                    ticker=options_flow[0].ticker if options_flow else "UNKNOWN",
                    detection_date=txn_date,
                    options_involved=[f"{opt.trade_date}:{opt.contract_type}:{opt.strike_price}" for opt in related_options[:10]],
                    estimated_profit=total_premium * 0.75,  # Assume 75% profit on insider-correlated trades
                    regulatory_citations=[
                        "17 CFR § 240.10b-5 (Securities fraud)",
                        "17 CFR § 240.10b5-1 (Insider trading)",
                        "Section 16(b) (Short-swing profits)"
                    ],
                    recommended_agencies=["SEC", "DOJ"]
                )
                anomalies.append(anomaly)
        
        return anomalies
