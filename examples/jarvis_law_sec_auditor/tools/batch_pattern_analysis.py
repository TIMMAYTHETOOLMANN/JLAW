"""
JARVIS:LAW - Batch Pattern Intelligence (BPI) Module
=====================================================

Module: batch_pattern_analysis.py
Purpose: Cross-filing forensic pattern detection and correlation
Classification: Forensic Grade - Batch Intelligence Layer

CAPABILITIES:
- Multi-filing timeline correlation
- Insider clustering and collusion detection
- Cross-filing risk aggregation
- Recurring trader pattern analysis
- Earnings season behavior mapping
- Batch-level forensic reporting

PowerShell Compatible: YES (No Unicode, emojis, or special characters)
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
import os

# Optional imports with graceful fallback
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("[WARNING] numpy not available - statistical features limited")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("[WARNING] pandas not available - batch processing limited")

try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[WARNING] scikit-learn not available - clustering disabled")


class BatchPatternIntelligence:
    """
    Batch-level forensic analysis engine for cross-filing pattern detection.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Batch Pattern Intelligence module.
        
        Args:
            config: Configuration dictionary for thresholds and parameters
        """
        self.config = config or self._default_config()
        self.analysis_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for batch analysis."""
        return {
            "volume_spike_threshold": 2.5,  # 2.5x average = spike
            "sync_window_days": 7,           # 7-day window for coordinated activity
            "clustering_eps": 0.3,           # DBSCAN epsilon
            "clustering_min_samples": 2,     # Minimum cluster size
            "earnings_window_days": 14,      # 14 days pre/post earnings
            "high_risk_threshold": 0.7,      # 0.7+ = high risk composite
            "medium_risk_threshold": 0.4,    # 0.4-0.69 = medium risk
        }
    
    def detect_trendline_anomalies(self, filings_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes transaction timelines across multiple filings to detect anomalies.
        
        Detects:
        - Volume spikes (transactions significantly above average)
        - Synchronized insider activity (multiple insiders trading within narrow window)
        - Repeat behavior patterns (same insiders, same patterns, different times)
        
        Args:
            filings_batch: List of parsed filing dictionaries
            
        Returns:
            Dictionary containing anomaly detection results
        """
        print("[BPI] Analyzing trendline anomalies across {} filings...".format(len(filings_batch)))
        
        # Build timeline
        timeline = []
        for filing in filings_batch:
            for tx in filing.get('transactions', []):
                timeline.append({
                    'date': tx.get('transaction_date'),
                    'insider': filing.get('reporting_owner', {}).get('name', 'UNKNOWN'),
                    'cik': filing.get('issuer', {}).get('cik', 'UNKNOWN'),
                    'shares': tx.get('shares_traded', 0),
                    'transaction_type': tx.get('transaction_code', 'UNKNOWN'),
                    'price': tx.get('price_per_share', 0.0)
                })
        
        # Sort by date
        timeline.sort(key=lambda x: x['date'] if x['date'] else '')
        
        # Calculate statistics
        total_transactions = len(timeline)
        if total_transactions == 0:
            return {
                'status': 'NO_DATA',
                'anomalies': [],
                'statistics': {}
            }
        
        # Volume analysis
        share_volumes = [tx['shares'] for tx in timeline if tx['shares'] > 0]
        avg_volume = sum(share_volumes) / len(share_volumes) if share_volumes else 0
        max_volume = max(share_volumes) if share_volumes else 0
        
        # Detect volume spikes
        volume_spikes = []
        spike_threshold = avg_volume * self.config['volume_spike_threshold']
        for tx in timeline:
            if tx['shares'] > spike_threshold and tx['shares'] > 0:
                volume_spikes.append({
                    'date': tx['date'],
                    'insider': tx['insider'],
                    'shares': tx['shares'],
                    'average': avg_volume,
                    'multiplier': round(tx['shares'] / avg_volume, 2) if avg_volume > 0 else 0
                })
        
        # Detect synchronized activity (multiple insiders trading within sync window)
        sync_clusters = self._detect_synchronized_activity(timeline)
        
        # Detect repeat patterns
        repeat_patterns = self._detect_repeat_patterns(timeline)
        
        return {
            'status': 'ANALYZED',
            'total_transactions': total_transactions,
            'timeline_span': {
                'earliest': timeline[0]['date'] if timeline else None,
                'latest': timeline[-1]['date'] if timeline else None
            },
            'statistics': {
                'average_share_volume': round(avg_volume, 2),
                'max_share_volume': max_volume,
                'unique_insiders': len(set(tx['insider'] for tx in timeline))
            },
            'volume_spikes': volume_spikes,
            'synchronized_clusters': sync_clusters,
            'repeat_patterns': repeat_patterns,
            'anomaly_count': len(volume_spikes) + len(sync_clusters) + len(repeat_patterns)
        }
    
    def _detect_synchronized_activity(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect multiple insiders trading within a narrow time window."""
        sync_window = timedelta(days=self.config['sync_window_days'])
        clusters = []
        
        for i, tx1 in enumerate(timeline):
            cluster_insiders = [tx1['insider']]
            cluster_dates = [tx1['date']]
            
            try:
                date1 = datetime.strptime(tx1['date'], '%Y-%m-%d')
            except:
                continue
            
            for tx2 in timeline[i+1:]:
                try:
                    date2 = datetime.strptime(tx2['date'], '%Y-%m-%d')
                    if abs((date2 - date1).days) <= sync_window.days:
                        if tx2['insider'] not in cluster_insiders:
                            cluster_insiders.append(tx2['insider'])
                            cluster_dates.append(tx2['date'])
                except:
                    continue
            
            if len(cluster_insiders) >= 2:
                clusters.append({
                    'window_start': tx1['date'],
                    'insider_count': len(cluster_insiders),
                    'insiders': cluster_insiders,
                    'dates': cluster_dates
                })
        
        # Deduplicate clusters
        unique_clusters = []
        seen = set()
        for cluster in clusters:
            key = tuple(sorted(cluster['insiders']))
            if key not in seen:
                seen.add(key)
                unique_clusters.append(cluster)
        
        return unique_clusters
    
    def _detect_repeat_patterns(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect insiders with recurring transaction patterns."""
        insider_transactions = defaultdict(list)
        
        for tx in timeline:
            insider_transactions[tx['insider']].append(tx)
        
        repeat_patterns = []
        for insider, txs in insider_transactions.items():
            if len(txs) >= 3:  # At least 3 transactions to establish pattern
                # Analyze transaction codes
                codes = [tx['transaction_type'] for tx in txs]
                code_frequency = Counter(codes)
                
                # Check for repeated behavior
                most_common_code, frequency = code_frequency.most_common(1)[0]
                if frequency >= 3:
                    repeat_patterns.append({
                        'insider': insider,
                        'pattern_type': 'REPEATED_CODE',
                        'transaction_code': most_common_code,
                        'frequency': frequency,
                        'total_transactions': len(txs)
                    })
        
        return repeat_patterns
    
    def cluster_insider_activity(self, filings_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Clusters similar trading behavior across insiders.
        
        Uses DBSCAN clustering on transaction features:
        - Share volume (normalized)
        - Transaction timing (day of quarter)
        - Price range
        
        Args:
            filings_batch: List of parsed filing dictionaries
            
        Returns:
            Dictionary containing clustering results and potential collusion flags
        """
        print("[BPI] Clustering insider activity patterns...")
        
        if not SKLEARN_AVAILABLE or not NUMPY_AVAILABLE:
            return {
                'status': 'UNAVAILABLE',
                'message': 'Clustering requires numpy and scikit-learn',
                'clusters': []
            }
        
        # Extract features for clustering
        features = []
        insider_metadata = []
        
        for filing in filings_batch:
            for tx in filing.get('transactions', []):
                try:
                    tx_date = datetime.strptime(tx.get('transaction_date', ''), '%Y-%m-%d')
                    day_of_quarter = (tx_date.timetuple().tm_yday % 90)  # Rough quarter day
                    
                    features.append([
                        float(tx.get('shares_traded', 0)),
                        float(day_of_quarter),
                        float(tx.get('price_per_share', 0))
                    ])
                    
                    insider_metadata.append({
                        'insider': filing.get('reporting_owner', {}).get('name', 'UNKNOWN'),
                        'date': tx.get('transaction_date'),
                        'shares': tx.get('shares_traded', 0),
                        'code': tx.get('transaction_code')
                    })
                except:
                    continue
        
        if len(features) < 2:
            return {
                'status': 'INSUFFICIENT_DATA',
                'clusters': []
            }
        
        # Normalize features
        scaler = StandardScaler()
        features_normalized = scaler.fit_transform(features)
        
        # DBSCAN clustering
        clustering = DBSCAN(
            eps=self.config['clustering_eps'],
            min_samples=self.config['clustering_min_samples']
        ).fit(features_normalized)
        
        labels = clustering.labels_
        
        # Analyze clusters
        clusters = defaultdict(list)
        for idx, label in enumerate(labels):
            if label != -1:  # -1 is noise
                clusters[label].append(insider_metadata[idx])
        
        # Format results
        cluster_results = []
        for cluster_id, members in clusters.items():
            unique_insiders = set(m['insider'] for m in members)
            
            cluster_results.append({
                'cluster_id': int(cluster_id),
                'member_count': len(members),
                'unique_insiders': len(unique_insiders),
                'insiders': list(unique_insiders),
                'transactions': members,
                'collusion_risk': 'HIGH' if len(unique_insiders) >= 3 else 'MEDIUM'
            })
        
        return {
            'status': 'CLUSTERED',
            'total_clusters': len(cluster_results),
            'noise_points': sum(1 for l in labels if l == -1),
            'clusters': cluster_results
        }
    
    def score_cross_filing_risk(self, filings_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates composite risk score across all filings in batch.
        
        Aggregates:
        - Individual filing risk scores
        - Cross-filing correlation penalties
        - Coordinated activity multipliers
        
        Args:
            filings_batch: List of parsed filing dictionaries
            
        Returns:
            Dictionary containing composite risk assessment
        """
        print("[BPI] Scoring cross-filing risk patterns...")
        
        if not filings_batch:
            return {
                'status': 'NO_DATA',
                'composite_risk': 0.0
            }
        
        # Extract individual risk scores
        individual_risks = []
        for filing in filings_batch:
            risk = filing.get('risk_score', 0.0)
            if isinstance(risk, (int, float)):
                individual_risks.append(risk)
        
        if not individual_risks:
            avg_risk = 0.0
        else:
            avg_risk = sum(individual_risks) / len(individual_risks)
        
        # Calculate correlation penalties
        correlation_penalty = self._calculate_correlation_penalty(filings_batch)
        
        # Calculate coordination multiplier
        coordination_multiplier = self._calculate_coordination_multiplier(filings_batch)
        
        # Composite score
        composite_risk = min(1.0, (avg_risk + correlation_penalty) * coordination_multiplier)
        
        # Risk classification
        if composite_risk >= self.config['high_risk_threshold']:
            risk_level = 'HIGH'
        elif composite_risk >= self.config['medium_risk_threshold']:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'status': 'SCORED',
            'composite_risk': round(composite_risk, 3),
            'risk_level': risk_level,
            'components': {
                'average_individual_risk': round(avg_risk, 3),
                'correlation_penalty': round(correlation_penalty, 3),
                'coordination_multiplier': round(coordination_multiplier, 2)
            },
            'filing_count': len(filings_batch),
            'high_risk_filings': sum(1 for r in individual_risks if r >= 0.7)
        }
    
    def _calculate_correlation_penalty(self, filings_batch: List[Dict[str, Any]]) -> float:
        """Calculate penalty for correlated suspicious activity."""
        # Count filings with high-risk patterns
        suspicious_count = 0
        for filing in filings_batch:
            risk = filing.get('risk_score', 0.0)
            if isinstance(risk, (int, float)) and risk >= 0.6:
                suspicious_count += 1
        
        # Penalty scales with proportion of suspicious filings
        if len(filings_batch) > 0:
            proportion = suspicious_count / len(filings_batch)
            return proportion * 0.2  # Max 0.2 penalty
        return 0.0
    
    def _calculate_coordination_multiplier(self, filings_batch: List[Dict[str, Any]]) -> float:
        """Calculate multiplier for coordinated activity."""
        # Look for same-day or near-same-day transactions
        transaction_dates = []
        for filing in filings_batch:
            for tx in filing.get('transactions', []):
                tx_date = tx.get('transaction_date')
                if tx_date:
                    transaction_dates.append(tx_date)
        
        # Count date frequency
        date_counts = Counter(transaction_dates)
        max_same_day = max(date_counts.values()) if date_counts else 1
        
        # Multiplier: 1.0 baseline, +0.1 per each additional same-day transaction
        multiplier = 1.0 + (max_same_day - 1) * 0.1
        return min(2.0, multiplier)  # Cap at 2.0x
    
    def detect_recurring_traders(self, filings_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identifies insiders appearing across multiple filings.
        
        Tracks:
        - Frequency of appearances
        - Behavioral changes over time
        - Volume escalation patterns
        
        Args:
            filings_batch: List of parsed filing dictionaries
            
        Returns:
            Dictionary containing recurring trader analysis
        """
        print("[BPI] Detecting recurring traders across filings...")
        
        insider_tracker = defaultdict(lambda: {
            'appearances': 0,
            'total_shares_traded': 0,
            'transactions': [],
            'dates': [],
            'companies': set()
        })
        
        for filing in filings_batch:
            insider_name = filing.get('reporting_owner', {}).get('name', 'UNKNOWN')
            company = filing.get('issuer', {}).get('name', 'UNKNOWN')
            
            for tx in filing.get('transactions', []):
                insider_tracker[insider_name]['appearances'] += 1
                insider_tracker[insider_name]['total_shares_traded'] += tx.get('shares_traded', 0)
                insider_tracker[insider_name]['transactions'].append(tx)
                insider_tracker[insider_name]['dates'].append(tx.get('transaction_date'))
                insider_tracker[insider_name]['companies'].add(company)
        
        # Filter for recurring traders (2+ appearances)
        recurring_traders = []
        for insider, data in insider_tracker.items():
            if data['appearances'] >= 2:
                # Analyze behavioral changes
                behavior_analysis = self._analyze_behavior_changes(data['transactions'])
                
                recurring_traders.append({
                    'insider': insider,
                    'appearances': data['appearances'],
                    'total_shares_traded': data['total_shares_traded'],
                    'companies': list(data['companies']),
                    'company_count': len(data['companies']),
                    'date_range': {
                        'earliest': min(data['dates']) if data['dates'] else None,
                        'latest': max(data['dates']) if data['dates'] else None
                    },
                    'behavior_analysis': behavior_analysis
                })
        
        # Sort by appearances (descending)
        recurring_traders.sort(key=lambda x: x['appearances'], reverse=True)
        
        return {
            'status': 'ANALYZED',
            'recurring_trader_count': len(recurring_traders),
            'total_unique_insiders': len(insider_tracker),
            'recurring_traders': recurring_traders
        }
    
    def _analyze_behavior_changes(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze changes in trading behavior over time."""
        if len(transactions) < 2:
            return {'status': 'INSUFFICIENT_DATA'}
        
        # Sort by date
        sorted_txs = sorted(transactions, key=lambda x: x.get('transaction_date', ''))
        
        # Compare first half vs second half
        midpoint = len(sorted_txs) // 2
        first_half = sorted_txs[:midpoint]
        second_half = sorted_txs[midpoint:]
        
        first_avg = sum(tx.get('shares_traded', 0) for tx in first_half) / len(first_half)
        second_avg = sum(tx.get('shares_traded', 0) for tx in second_half) / len(second_half)
        
        if first_avg > 0:
            volume_change = ((second_avg - first_avg) / first_avg) * 100
        else:
            volume_change = 0.0
        
        return {
            'status': 'ANALYZED',
            'volume_trend': 'INCREASING' if volume_change > 20 else 'DECREASING' if volume_change < -20 else 'STABLE',
            'volume_change_percent': round(volume_change, 2),
            'first_period_avg_shares': round(first_avg, 2),
            'second_period_avg_shares': round(second_avg, 2)
        }
    
    def analyze_earnings_season_patterns(self, filings_batch: List[Dict[str, Any]], 
                                        earnings_calendar: Dict[str, List[str]] = None) -> Dict[str, Any]:
        """
        Maps trades to earnings release windows and detects systemic patterns.
        
        Args:
            filings_batch: List of parsed filing dictionaries
            earnings_calendar: Dict mapping CIK -> list of earnings dates
            
        Returns:
            Dictionary containing earnings correlation analysis
        """
        print("[BPI] Analyzing earnings season trading patterns...")
        
        if not earnings_calendar:
            # Attempt to load from data directory
            try:
                data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'earnings_calendar.json')
                with open(data_path, 'r') as f:
                    earnings_calendar = json.load(f)
            except:
                return {
                    'status': 'NO_EARNINGS_DATA',
                    'message': 'Earnings calendar not provided and not found in data directory'
                }
        
        earnings_window_days = self.config['earnings_window_days']
        
        # Track transactions relative to earnings
        pre_earnings_trades = []
        post_earnings_trades = []
        outside_window_trades = []
        
        for filing in filings_batch:
            cik = filing.get('issuer', {}).get('cik', '')
            earnings_dates = earnings_calendar.get(cik, [])
            
            for tx in filing.get('transactions', []):
                tx_date_str = tx.get('transaction_date')
                if not tx_date_str:
                    continue
                
                try:
                    tx_date = datetime.strptime(tx_date_str, '%Y-%m-%d')
                except:
                    continue
                
                # Check against earnings dates
                within_window = False
                for earnings_date_str in earnings_dates:
                    try:
                        earnings_date = datetime.strptime(earnings_date_str, '%Y-%m-%d')
                        days_diff = (tx_date - earnings_date).days
                        
                        if -earnings_window_days <= days_diff <= 0:
                            # Pre-earnings
                            pre_earnings_trades.append({
                                'insider': filing.get('reporting_owner', {}).get('name'),
                                'date': tx_date_str,
                                'days_before_earnings': abs(days_diff),
                                'shares': tx.get('shares_traded', 0)
                            })
                            within_window = True
                            break
                        elif 0 < days_diff <= earnings_window_days:
                            # Post-earnings
                            post_earnings_trades.append({
                                'insider': filing.get('reporting_owner', {}).get('name'),
                                'date': tx_date_str,
                                'days_after_earnings': days_diff,
                                'shares': tx.get('shares_traded', 0)
                            })
                            within_window = True
                            break
                    except:
                        continue
                
                if not within_window:
                    outside_window_trades.append(tx_date_str)
        
        total_trades = len(pre_earnings_trades) + len(post_earnings_trades) + len(outside_window_trades)
        
        return {
            'status': 'ANALYZED',
            'total_transactions': total_trades,
            'pre_earnings_count': len(pre_earnings_trades),
            'post_earnings_count': len(post_earnings_trades),
            'outside_window_count': len(outside_window_trades),
            'pre_earnings_percentage': round((len(pre_earnings_trades) / total_trades * 100), 2) if total_trades > 0 else 0,
            'post_earnings_percentage': round((len(post_earnings_trades) / total_trades * 100), 2) if total_trades > 0 else 0,
            'pre_earnings_trades': pre_earnings_trades[:10],  # Top 10 for brevity
            'post_earnings_trades': post_earnings_trades[:10],
            'risk_assessment': 'HIGH' if len(pre_earnings_trades) > len(post_earnings_trades) else 'MEDIUM' if len(pre_earnings_trades) > 0 else 'LOW'
        }
    
    def generate_batch_forensic_summary(self, filings_batch: List[Dict[str, Any]], 
                                       output_dir: str = None) -> Dict[str, Any]:
        """
        Generates comprehensive batch-level intelligence report.
        
        Combines all BPI module outputs into master forensic summary.
        
        Args:
            filings_batch: List of parsed filing dictionaries
            output_dir: Directory to write output files (optional)
            
        Returns:
            Dictionary containing complete batch analysis
        """
        print("[BPI] Generating batch forensic summary for {} filings...".format(len(filings_batch)))
        
        # Run all analysis modules
        trendline = self.detect_trendline_anomalies(filings_batch)
        clustering = self.cluster_insider_activity(filings_batch)
        cross_filing = self.score_cross_filing_risk(filings_batch)
        recurring = self.detect_recurring_traders(filings_batch)
        earnings = self.analyze_earnings_season_patterns(filings_batch)
        
        # Compile master summary
        summary = {
            'metadata': {
                'analysis_timestamp': self.analysis_timestamp,
                'filing_count': len(filings_batch),
                'module_version': 'BPI-1.0',
                'powershell_compatible': True
            },
            'trendline_anomalies': trendline,
            'insider_clustering': clustering,
            'cross_filing_risk': cross_filing,
            'recurring_traders': recurring,
            'earnings_correlation': earnings,
            'master_assessment': self._generate_master_assessment(
                trendline, clustering, cross_filing, recurring, earnings
            )
        }
        
        # Write to files if output directory provided
        if output_dir:
            self._write_batch_outputs(summary, output_dir)
        
        return summary
    
    def _generate_master_assessment(self, trendline: Dict, clustering: Dict, 
                                    cross_filing: Dict, recurring: Dict, 
                                    earnings: Dict) -> Dict[str, Any]:
        """Generate overall risk assessment from all modules."""
        
        # Aggregate risk signals
        risk_signals = []
        
        if trendline.get('anomaly_count', 0) > 5:
            risk_signals.append('HIGH_ANOMALY_COUNT')
        
        if clustering.get('total_clusters', 0) > 0:
            risk_signals.append('CLUSTERING_DETECTED')
        
        composite_risk = cross_filing.get('composite_risk', 0.0)
        if composite_risk >= 0.7:
            risk_signals.append('HIGH_COMPOSITE_RISK')
        
        if recurring.get('recurring_trader_count', 0) > 3:
            risk_signals.append('MULTIPLE_RECURRING_TRADERS')
        
        if earnings.get('pre_earnings_percentage', 0) > 30:
            risk_signals.append('HIGH_PRE_EARNINGS_ACTIVITY')
        
        # Overall risk determination
        if len(risk_signals) >= 3:
            overall_risk = 'CRITICAL'
        elif len(risk_signals) >= 2:
            overall_risk = 'HIGH'
        elif len(risk_signals) >= 1:
            overall_risk = 'MEDIUM'
        else:
            overall_risk = 'LOW'
        
        return {
            'overall_risk_level': overall_risk,
            'risk_signal_count': len(risk_signals),
            'risk_signals': risk_signals,
            'composite_risk_score': composite_risk,
            'recommendation': self._generate_recommendation(overall_risk, risk_signals)
        }
    
    def _generate_recommendation(self, risk_level: str, signals: List[str]) -> str:
        """Generate human-readable recommendation based on risk assessment."""
        if risk_level == 'CRITICAL':
            return "IMMEDIATE FORENSIC REVIEW REQUIRED - Multiple high-risk patterns detected across batch"
        elif risk_level == 'HIGH':
            return "PRIORITY INVESTIGATION RECOMMENDED - Significant suspicious patterns identified"
        elif risk_level == 'MEDIUM':
            return "ROUTINE MONITORING ADVISED - Some patterns warrant follow-up"
        else:
            return "NO IMMEDIATE ACTION REQUIRED - Normal trading patterns observed"
    
    def _write_batch_outputs(self, summary: Dict[str, Any], output_dir: str):
        """Write batch analysis outputs to files."""
        os.makedirs(output_dir, exist_ok=True)
        
        # JSON output
        json_path = os.path.join(output_dir, 
                                'BATCH_FORENSIC_REPORT_{}.json'.format(self.analysis_timestamp))
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print("[BPI] JSON report written to: {}".format(json_path))
        
        # Human-readable summary
        txt_path = os.path.join(output_dir, 
                               'BATCH_SUMMARY_{}.txt'.format(self.analysis_timestamp))
        with open(txt_path, 'w') as f:
            f.write(self._format_human_readable_summary(summary))
        print("[BPI] Human-readable summary written to: {}".format(txt_path))
    
    def _format_human_readable_summary(self, summary: Dict[str, Any]) -> str:
        """Format summary as human-readable intelligence brief."""
        lines = []
        lines.append("=" * 80)
        lines.append("JARVIS:LAW - BATCH PATTERN INTELLIGENCE REPORT")
        lines.append("=" * 80)
        lines.append("")
        lines.append("Analysis Timestamp: {}".format(summary['metadata']['analysis_timestamp']))
        lines.append("Filing Count: {}".format(summary['metadata']['filing_count']))
        lines.append("Module Version: {}".format(summary['metadata']['module_version']))
        lines.append("")
        lines.append("-" * 80)
        lines.append("MASTER ASSESSMENT")
        lines.append("-" * 80)
        
        master = summary.get('master_assessment', {})
        lines.append("Overall Risk Level: {}".format(master.get('overall_risk_level', 'UNKNOWN')))
        lines.append("Risk Signal Count: {}".format(master.get('risk_signal_count', 0)))
        lines.append("Composite Risk Score: {}".format(master.get('composite_risk_score', 0)))
        lines.append("")
        lines.append("Risk Signals Detected:")
        for signal in master.get('risk_signals', []):
            lines.append("  - {}".format(signal))
        lines.append("")
        lines.append("Recommendation: {}".format(master.get('recommendation', 'N/A')))
        lines.append("")
        
        lines.append("-" * 80)
        lines.append("TRENDLINE ANOMALIES")
        lines.append("-" * 80)
        trendline = summary.get('trendline_anomalies', {})
        lines.append("Total Anomalies: {}".format(trendline.get('anomaly_count', 0)))
        lines.append("Volume Spikes: {}".format(len(trendline.get('volume_spikes', []))))
        lines.append("Synchronized Clusters: {}".format(len(trendline.get('synchronized_clusters', []))))
        lines.append("")
        
        lines.append("-" * 80)
        lines.append("CROSS-FILING RISK")
        lines.append("-" * 80)
        cross = summary.get('cross_filing_risk', {})
        lines.append("Composite Risk: {}".format(cross.get('composite_risk', 0)))
        lines.append("Risk Level: {}".format(cross.get('risk_level', 'UNKNOWN')))
        lines.append("High-Risk Filings: {}".format(cross.get('high_risk_filings', 0)))
        lines.append("")
        
        lines.append("-" * 80)
        lines.append("RECURRING TRADERS")
        lines.append("-" * 80)
        recurring = summary.get('recurring_traders', {})
        lines.append("Recurring Trader Count: {}".format(recurring.get('recurring_trader_count', 0)))
        lines.append("Total Unique Insiders: {}".format(recurring.get('total_unique_insiders', 0)))
        lines.append("")
        
        lines.append("-" * 80)
        lines.append("EARNINGS CORRELATION")
        lines.append("-" * 80)
        earnings = summary.get('earnings_correlation', {})
        lines.append("Pre-Earnings Trades: {} ({}%)".format(
            earnings.get('pre_earnings_count', 0),
            earnings.get('pre_earnings_percentage', 0)
        ))
        lines.append("Post-Earnings Trades: {} ({}%)".format(
            earnings.get('post_earnings_count', 0),
            earnings.get('post_earnings_percentage', 0)
        ))
        lines.append("Risk Assessment: {}".format(earnings.get('risk_assessment', 'UNKNOWN')))
        lines.append("")
        
        lines.append("=" * 80)
        lines.append("END OF BATCH INTELLIGENCE REPORT")
        lines.append("=" * 80)
        
        return "\n".join(lines)


# Module-level convenience functions
def analyze_batch(filings_batch: List[Dict[str, Any]], 
                 output_dir: str = None,
                 config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to run complete batch analysis.
    
    Args:
        filings_batch: List of parsed filing dictionaries
        output_dir: Directory to write outputs (optional)
        config: Custom configuration (optional)
        
    Returns:
        Complete batch analysis results
    """
    bpi = BatchPatternIntelligence(config)
    return bpi.generate_batch_forensic_summary(filings_batch, output_dir)


def quick_risk_assessment(filings_batch: List[Dict[str, Any]]) -> str:
    """
    Quick risk assessment without full analysis.
    
    Args:
        filings_batch: List of parsed filing dictionaries
        
    Returns:
        Risk level string (LOW, MEDIUM, HIGH, CRITICAL)
    """
    bpi = BatchPatternIntelligence()
    cross_filing = bpi.score_cross_filing_risk(filings_batch)
    return cross_filing.get('risk_level', 'UNKNOWN')


if __name__ == "__main__":
    print("[BPI] Batch Pattern Intelligence Module - PowerShell Compatible")
    print("[BPI] Version: 1.0")
    print("[BPI] Status: OPERATIONAL")
    print("[BPI] Dependencies:")
    print("  - numpy: {}".format("AVAILABLE" if NUMPY_AVAILABLE else "NOT AVAILABLE"))
    print("  - pandas: {}".format("AVAILABLE" if PANDAS_AVAILABLE else "NOT AVAILABLE"))
    print("  - scikit-learn: {}".format("AVAILABLE" if SKLEARN_AVAILABLE else "NOT AVAILABLE"))

