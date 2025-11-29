"""
. Now. 
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
        """Extract comprehensive financial metrics from content
        
        Supports:
        - Text-based extraction with regex patterns
        - XBRL parsing (if XML content detected)
        - Multiple financial indicators
        - Ratio calculation
        - Anomaly detection
        """
        metrics = FinancialMetrics()
        
        # Check if content is XBRL/XML
        if '<' in content and ('xbrl' in content.lower() or '<?xml' in content.lower()):
            metrics = await self._extract_from_xbrl(content)
        else:
            # Text-based extraction
            metrics = await self._extract_from_text(content)
        
        # Calculate ratios
        metrics.ratios = self._calculate_ratios(metrics)
        
        # Calculate year-over-year changes
        metrics.year_over_year = self._calculate_yoy_changes(metrics)
        
        # Detect anomalies
        metrics.anomalies = self._detect_anomalies(metrics)
        
        logger.info(
            f"💰 Extracted: Revenue={len(metrics.revenue)}, "
            f"Earnings={len(metrics.earnings)}, "
            f"Assets={len(metrics.assets)}, "
            f"Ratios={len(metrics.ratios)}"
        )
        return metrics
    
    async def _extract_from_text(self, content: str) -> FinancialMetrics:
        """Extract financial metrics from text content using regex patterns"""
        metrics = FinancialMetrics()
        
        # Define comprehensive extraction patterns
        patterns = {
            'revenue': [
                r'(?:total\s+)?(?:revenue|sales|turnover)\s*[:\-]?\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?',
                r'revenues?\s+(?:of|was|were|:)\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?'
            ],
            'earnings': [
                r'(?:net\s+)?(?:income|earnings|profit)\s*[:\-]?\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?',
                r'(?:net\s+)?(?:income|earnings)\s+(?:of|was|were|:)\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?'
            ],
            'assets': [
                r'(?:total\s+)?assets?\s*[:\-]?\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?',
                r'assets?\s+(?:of|was|were|:)\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?'
            ],
            'liabilities': [
                r'(?:total\s+)?liabilities?\s*[:\-]?\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?',
            ],
            'equity': [
                r'(?:shareholders?|stockholders?)\s+equity\s*[:\-]?\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?',
            ],
            'cash_flow': [
                r'(?:operating\s+)?cash\s+flow\s*[:\-]?\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?',
                r'cash\s+(?:from|provided\s+by)\s+operations?\s*[:\-]?\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?'
            ]
        }
        
        # Extract each metric type
        for metric_type, pattern_list in patterns.items():
            for pattern_str in pattern_list:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                
                for match in pattern.finditer(content):
                    try:
                        value = float(match.group(1).replace(',', ''))
                        if match.group(2):
                            value *= self.multipliers.get(match.group(2).lower(), 1)
                        
                        metric_entry = {
                            'value': value,
                            'formatted': f"${value:,.0f}",
                            'text': match.group(0)
                        }
                        
                        # Add to appropriate list
                        getattr(metrics, metric_type).append(metric_entry)
                    except (ValueError, AttributeError, IndexError):
                        continue
        
        return metrics
    
    async def _extract_from_xbrl(self, content: str) -> FinancialMetrics:
        """Extract financial metrics from XBRL/XML content
        
        Note: This is a basic implementation. Full XBRL parsing requires
        specialized libraries like python-xbrl or arelle.
        """
        metrics = FinancialMetrics()
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'xml')
            
            # Common XBRL tags for financial metrics
            xbrl_mappings = {
                'revenue': ['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax'],
                'earnings': ['NetIncomeLoss', 'ProfitLoss', 'NetIncome'],
                'assets': ['Assets', 'AssetsCurrent', 'AssetsTotal'],
                'liabilities': ['Liabilities', 'LiabilitiesCurrent', 'LiabilitiesTotal'],
                'equity': ['StockholdersEquity', 'Equity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],
                'cash_flow': ['NetCashProvidedByUsedInOperatingActivities', 'CashFlowOperatingActivities']
            }
            
            for metric_type, tags in xbrl_mappings.items():
                for tag in tags:
                    elements = soup.find_all(tag)
                    for elem in elements:
                        try:
                            value = float(elem.get_text().strip())
                            
                            metric_entry = {
                                'value': value,
                                'formatted': f"${value:,.0f}",
                                'text': f"{tag}: {value}",
                                'source': 'xbrl'
                            }
                            
                            getattr(metrics, metric_type).append(metric_entry)
                        except (ValueError, AttributeError):
                            continue
            
            logger.debug("📊 XBRL extraction completed")
        except Exception as e:
            logger.warning(f"XBRL extraction failed: {e} - falling back to text extraction")
            # Fallback to text extraction
            metrics = await self._extract_from_text(content)
        
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

    def _calculate_yoy_changes(self, metrics: FinancialMetrics) -> Dict[str, float]:
        """Calculate year-over-year changes for financial metrics
        
        Compares current period to prior period values where available
        """
        yoy_changes = {}
        
        try:
            # Calculate revenue YoY if we have multiple periods
            if len(metrics.revenue) >= 2:
                current_rev = metrics.revenue[0]['value']
                prior_rev = metrics.revenue[1]['value']
                if prior_rev > 0:
                    yoy_changes['revenue_yoy'] = ((current_rev - prior_rev) / prior_rev) * 100
            
            # Calculate earnings YoY if we have multiple periods
            if len(metrics.earnings) >= 2:
                current_earn = metrics.earnings[0]['value']
                prior_earn = metrics.earnings[1]['value']
                if prior_earn != 0:
                    yoy_changes['earnings_yoy'] = ((current_earn - prior_earn) / abs(prior_earn)) * 100
            
            # Calculate assets YoY if we have multiple periods
            if len(metrics.assets) >= 2:
                current_assets = metrics.assets[0]['value']
                prior_assets = metrics.assets[1]['value']
                if prior_assets > 0:
                    yoy_changes['assets_yoy'] = ((current_assets - prior_assets) / prior_assets) * 100
            
            # Calculate cash flow YoY if we have multiple periods
            if len(metrics.cash_flow) >= 2:
                current_cf = metrics.cash_flow[0]['value']
                prior_cf = metrics.cash_flow[1]['value']
                if prior_cf != 0:
                    yoy_changes['cash_flow_yoy'] = ((current_cf - prior_cf) / abs(prior_cf)) * 100
                    
        except (IndexError, ZeroDivisionError, KeyError, TypeError) as e:
            logger.debug(f"YoY calculation error: {e}")
        
        return yoy_changes

    def _detect_anomalies(self, metrics: FinancialMetrics) -> List[Dict[str, Any]]:
        """Detect anomalies in financial data
        
        Anomaly detection methods:
        - Negative margins
        - Extreme ratio values
        - Unusual YoY changes
        - Benford's Law violations (digit distribution)
        """
        anomalies = []
        
        # Negative profit margin
        if 'profit_margin' in metrics.ratios and metrics.ratios['profit_margin'] < 0:
            anomalies.append({
                'type': 'negative_profit_margin',
                'severity': 'high',
                'description': f"Negative profit margin: {metrics.ratios['profit_margin']:.2f}%"
            })
        
        # Extremely high profit margin (>50% - potential manipulation)
        if 'profit_margin' in metrics.ratios and metrics.ratios['profit_margin'] > 50:
            anomalies.append({
                'type': 'unusually_high_margin',
                'severity': 'medium',
                'description': f"Unusually high profit margin: {metrics.ratios['profit_margin']:.2f}%"
            })
        
        # High debt-to-equity ratio (>3.0 - financial distress indicator)
        if 'debt_to_equity' in metrics.ratios and metrics.ratios['debt_to_equity'] > 3.0:
            anomalies.append({
                'type': 'high_leverage',
                'severity': 'high',
                'description': f"High debt-to-equity ratio: {metrics.ratios['debt_to_equity']:.2f}"
            })
        
        # Extreme YoY changes (>100% or <-50%)
        if 'revenue_yoy' in metrics.year_over_year:
            yoy = metrics.year_over_year['revenue_yoy']
            if yoy > 100:
                anomalies.append({
                    'type': 'extreme_revenue_growth',
                    'severity': 'medium',
                    'description': f"Extreme revenue growth: {yoy:.1f}% YoY"
                })
            elif yoy < -50:
                anomalies.append({
                    'type': 'extreme_revenue_decline',
                    'severity': 'high',
                    'description': f"Extreme revenue decline: {yoy:.1f}% YoY"
                })
        
        # Benford's Law analysis (first digit distribution)
        benford_result = self._benfords_law_test(metrics)
        if benford_result and benford_result['anomaly']:
            anomalies.append({
                'type': 'benfords_law_violation',
                'severity': 'high',
                'description': f"Benford's Law violation detected (χ²={benford_result['chi_squared']:.2f})",
                'details': benford_result
            })
        
        logger.debug(f"⚠️ Detected {len(anomalies)} anomalies")
        return anomalies
    
    def _benfords_law_test(self, metrics: FinancialMetrics) -> Optional[Dict[str, Any]]:
        """Apply Benford's Law test to detect digit manipulation
        
        Benford's Law states that in many naturally occurring collections
        of numbers, the leading digit is likely to be small. First digit
        distribution should follow: P(d) = log10(1 + 1/d)
        """
        try:
            import numpy as np
            from collections import Counter
            
            # Collect all numerical values
            numbers = []
            for metric_list in [metrics.revenue, metrics.earnings, metrics.assets, 
                              metrics.liabilities, metrics.equity, metrics.cash_flow]:
                for item in metric_list:
                    if 'value' in item and item['value'] != 0:
                        numbers.append(abs(item['value']))
            
            if len(numbers) < 10:  # Need sufficient sample size
                return None
            
            # Extract first digits
            first_digits = [int(str(int(n))[0]) for n in numbers if n > 0]
            
            if not first_digits:
                return None
            
            # Expected distribution according to Benford's Law
            expected = {d: np.log10(1 + 1/d) for d in range(1, 10)}
            
            # Observed distribution
            observed_counts = Counter(first_digits)
            total = len(first_digits)
            observed = {d: observed_counts.get(d, 0) / total for d in range(1, 10)}
            
            # Chi-square test
            chi_squared = 0
            for d in range(1, 10):
                expected_count = expected[d] * total
                observed_count = observed_counts.get(d, 0)
                if expected_count > 0:
                    chi_squared += ((observed_count - expected_count) ** 2) / expected_count
            
            # Chi-square critical value at p<0.05 with 8 degrees of freedom is 15.51
            is_anomaly = chi_squared > 15.51
            
            return {
                'chi_squared': round(chi_squared, 2),
                'anomaly': is_anomaly,
                'sample_size': len(first_digits),
                'observed_distribution': {str(d): round(observed[d], 3) for d in range(1, 10)},
                'expected_distribution': {str(d): round(expected[d], 3) for d in range(1, 10)}
            }
        except Exception as e:
            logger.debug(f"Benford's Law test failed: {e}")
            return None
