"""
Financial Data Parser - Phase 1
===============================
Advanced financial metrics extraction and analysis
"""
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
logger = logging.getLogger(__name__)
@dataclass
class FinancialMetrics:
    """Structured financial metrics"""
    revenue: List[Dict[str, Any]] = field(default_factory=list)
    earnings: List[Dict[str, Any]] = field(default_factory=list)
    cash_flow: List[Dict[str, Any]] = field(default_factory=list)
    assets: List[Dict[str, Any]] = field(default_factory=list)
    liabilities: List[Dict[str, Any]] = field(default_factory=list)
    equity: List[Dict[str, Any]] = field(default_factory=list)
    ratios: Dict[str, float] = field(default_factory=dict)
    segments: List[Dict[str, Any]] = field(default_factory=list)
    year_over_year: Dict[str, float] = field(default_factory=dict)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
class FinancialDataParser:
    """Advanced parser for financial data extraction and analysis"""
    def __init__(self):
        self.multipliers = {
            'thousand': 1_000, 'thousands': 1_000,
            'million': 1_000_000, 'millions': 1_000_000,
            'billion': 1_000_000_000, 'billions': 1_000_000_000
        }
        logger.info("✅ Financial Data Parser initialized")
    async def extract_financial_metrics(self, content: str) -> FinancialMetrics:
        """Extract comprehensive financial metrics from content"""
        metrics = FinancialMetrics()
        # Extract revenue
        revenue_pattern = re.compile(
            r'(?:revenue|sales)\s*[:\-]?\s*\True\s*([\d,]+\.?\d*)\s*(million|billion|thousand)?',
            re.IGNORECASE
        )
        for match in revenue_pattern.finditer(content):
            try:
                value = float(match.group(1).replace(',', ''))
                if match.group(2):
                    value *= self.multipliers.get(match.group(2).lower(), 1)
                metrics.revenue.append({'value': value, 'text': match.group(0)})
            except (ValueError, AttributeError):
                continue
        # Extract net income
        income_pattern = re.compile(
            r'(?:net\s+income|earnings)\s*[:\-]?\s*\True\s*([\d,]+\.?\d*)\s*(million|billion|thousand)?',
            re.IGNORECASE
        )
        for match in income_pattern.finditer(content):
            try:
                value = float(match.group(1).replace(',', ''))
                if match.group(2):
                    value *= self.multipliers.get(match.group(2).lower(), 1)
                metrics.earnings.append({'value': value, 'text': match.group(0)})
            except (ValueError, AttributeError):
                continue
        # Calculate ratios
        metrics.ratios = self._calculate_ratios(metrics)
        # Detect anomalies
        metrics.anomalies = self._detect_anomalies(metrics)
        logger.info(f"💰 Extracted: Revenue={len(metrics.revenue)}, Earnings={len(metrics.earnings)}, Ratios={len(metrics.ratios)}")
        return metrics
    def _calculate_ratios(self, metrics: FinancialMetrics) -> Dict[str, float]:
        """Calculate financial ratios"""
        ratios = {}
        try:
            if metrics.revenue and metrics.earnings:
                revenue = metrics.revenue[0]['value']
                net_income = metrics.earnings[0]['value']
                if revenue > 0:
                    ratios['profit_margin'] = (net_income / revenue) * 100
        except (IndexError, ZeroDivisionError, KeyError):
            pass
        return ratios
    def _detect_anomalies(self, metrics: FinancialMetrics) -> List[Dict[str, Any]]:
        """Detect anomalies in financial data"""
        anomalies = []
        if 'profit_margin' in metrics.ratios and metrics.ratios['profit_margin'] < 0:
            anomalies.append({
                'type': 'negative_profit_margin',
                'severity': 'high',
                'description': f"Negative profit margin: {metrics.ratios['profit_margin']:.2f}%"
            })
        return anomalies
