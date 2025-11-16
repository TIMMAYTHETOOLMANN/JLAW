"""
JARVIS:LAW Black Site Protocol - Visual Analytics Engine
Timeline graphs, heat maps, correlation bubbles for forensic pattern visualization
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Circle
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from pathlib import Path
import json


class VisualAnalyticsEngine:
    """Generate visual representations of forensic findings"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set professional style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
    
    def generate_transaction_timeline(self, filings: List[Dict], output_name: str = "timeline.png") -> Path:
        """
        Generate timeline showing ALL transactions with date correlation
        This is the money shot - shows if patterns are clustered vs sporadic
        """
        
        # Extract all transactions with dates
        timeline_data = []
        
        for filing in filings:
            filing_date_str = filing.get('filing_date', '')
            accession = filing.get('accession_number', 'Unknown')
            
            try:
                filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d')
            except:
                continue
            
            transactions = filing.get('transactions', [])
            
            for trans in transactions:
                # Try to extract transaction date from raw data
                trans_date = filing_date  # Fallback to filing date
                
                # Try to parse from transaction data
                if trans.get('transaction_date'):
                    try:
                        trans_date = datetime.strptime(trans['transaction_date'], '%Y-%m-%d')
                    except:
                        pass
                
                timeline_data.append({
                    'date': trans_date,
                    'filing': accession,
                    'code': trans.get('transaction_code', 'Unknown'),
                    'shares': self._parse_shares(trans.get('shares', '0')),
                    'price': self._parse_price(trans.get('price_per_share', '$0'))
                })
        
        if not timeline_data:
            return None
        
        # Create DataFrame
        df = pd.DataFrame(timeline_data)
        df = df.sort_values('date')
        
        # Create figure
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Plot transactions as scatter
        # Size represents share volume, color represents transaction code
        code_colors = {
            'D': 'red',      # Disposition
            'A': 'green',    # Award
            'P': 'blue',     # Purchase
            'S': 'orange',   # Sale
            'X': 'purple',   # Exercise
            'M': 'brown',    # Option Exercise
            'F': 'pink',     # Tax
            'I': 'cyan',     # Indirect
            'G': 'yellow'    # Gift
        }
        
        for code in df['code'].unique():
            if code == 'Unknown':
                continue
            
            code_data = df[df['code'] == code]
            
            # Scale share sizes for visibility
            sizes = np.sqrt(code_data['shares']) * 2
            sizes = sizes.fillna(50)  # Default size for unknown
            
            ax.scatter(
                code_data['date'],
                [1] * len(code_data),  # All on same line
                s=sizes,
                c=code_colors.get(code, 'gray'),
                alpha=0.6,
                label=f'Code {code}',
                edgecolors='black',
                linewidth=1
            )
        
        # Highlight clusters (transactions within 5 days of each other)
        cluster_threshold = timedelta(days=5)
        clusters = []
        current_cluster = []
        
        for i, row in df.iterrows():
            if not current_cluster:
                current_cluster.append(row['date'])
            else:
                if row['date'] - current_cluster[-1] <= cluster_threshold:
                    current_cluster.append(row['date'])
                else:
                    if len(current_cluster) >= 3:  # 3+ transactions = cluster
                        clusters.append((min(current_cluster), max(current_cluster)))
                    current_cluster = [row['date']]
        
        # Add last cluster
        if len(current_cluster) >= 3:
            clusters.append((min(current_cluster), max(current_cluster)))
        
        # Draw cluster regions
        for start, end in clusters:
            ax.axvspan(start, end, alpha=0.2, color='red', label='Suspicious Cluster')
        
        # Format
        ax.set_yticks([])
        ax.set_xlabel('Date', fontsize=14, fontweight='bold')
        ax.set_title('TRANSACTION TIMELINE - Pattern Correlation Analysis', 
                     fontsize=16, fontweight='bold', pad=20)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.xticks(rotation=45, ha='right')
        
        # Legend
        handles, labels = ax.get_legend_handles_labels()
        # Remove duplicate labels
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), 
                 loc='upper left', fontsize=10, framealpha=0.9)
        
        # Add statistics box
        stats_text = f"Total Transactions: {len(df)}\n"
        stats_text += f"Date Range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}\n"
        stats_text += f"Suspicious Clusters: {len(clusters)}"
        
        ax.text(0.02, 0.98, stats_text,
               transform=ax.transAxes,
               fontsize=10,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Grid
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        output_path = self.output_dir / output_name
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_filing_delay_heatmap(self, filings: List[Dict], output_name: str = "delay_heatmap.png") -> Path:
        """
        Generate heat map showing filing delays over time
        Red zones indicate late filings - pattern of redness = systematic issues
        """
        
        # Extract filing delay data
        delay_data = []
        
        for filing in filings:
            try:
                filing_date = datetime.strptime(filing.get('filing_date', ''), '%Y-%m-%d')
                # Would need period_end from actual data
                # For now, estimate based on form type
                form_type = filing.get('form_type', '')
                
                # Simplified delay calculation
                delay_data.append({
                    'date': filing_date,
                    'form': form_type,
                    'delay': filing.get('filing_delay_days', 0),
                    'late': filing.get('late_filing', False)
                })
            except:
                continue
        
        if not delay_data:
            return None
        
        df = pd.DataFrame(delay_data)
        df['year_month'] = df['date'].dt.to_period('M')
        
        # Aggregate by month
        monthly = df.groupby('year_month').agg({
            'delay': 'mean',
            'late': 'sum'
        }).reset_index()
        
        # Create heatmap
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
        
        # Delay magnitude
        ax1.bar(range(len(monthly)), monthly['delay'], 
               color=['red' if d > 30 else 'yellow' if d > 15 else 'green' 
                      for d in monthly['delay']])
        ax1.set_title('Average Filing Delay by Month', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Days', fontsize=12)
        ax1.axhline(y=30, color='red', linestyle='--', label='Critical Threshold')
        ax1.axhline(y=15, color='orange', linestyle='--', label='Warning Threshold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Late filing count
        ax2.bar(range(len(monthly)), monthly['late'], color='red', alpha=0.7)
        ax2.set_title('Late Filings by Month', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Count', fontsize=12)
        ax2.set_xlabel('Month', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Set x-axis labels
        labels = [str(m) for m in monthly['year_month']]
        for ax in [ax1, ax2]:
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha='right')
        
        plt.tight_layout()
        
        output_path = self.output_dir / output_name
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_risk_bubble_chart(self, filings: List[Dict], output_name: str = "risk_bubbles.png") -> Path:
        """
        Generate bubble chart showing risk concentration
        Bubble size = transaction volume, color = violation severity
        """
        
        # Extract risk data
        risk_data = []
        
        for i, filing in enumerate(filings):
            try:
                filing_date = datetime.strptime(filing.get('filing_date', ''), '%Y-%m-%d')
            except:
                filing_date = datetime.now()
            
            violations = filing.get('violations', [])
            transaction_count = len(filing.get('transactions', []))
            
            # Calculate risk score
            risk_score = len(violations) * 0.3
            if filing.get('late_filing'):
                risk_score += 0.2
            if filing.get('amendments', 0) > 0:
                risk_score += 0.1
            
            risk_score = min(1.0, risk_score)
            
            risk_data.append({
                'date': filing_date,
                'risk': risk_score,
                'transactions': transaction_count,
                'violations': len(violations),
                'accession': filing.get('accession_number', 'Unknown')[:15]
            })
        
        if not risk_data:
            return None
        
        df = pd.DataFrame(risk_data)
        
        # Create bubble chart
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Scatter with bubble sizes
        scatter = ax.scatter(
            df['date'],
            df['risk'],
            s=df['transactions'] * 100 + 100,  # Scale for visibility
            c=df['violations'],
            cmap='YlOrRd',
            alpha=0.6,
            edgecolors='black',
            linewidth=1
        )
        
        # Colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Violation Count', fontsize=12, fontweight='bold')
        
        # Format
        ax.set_xlabel('Filing Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Risk Score', fontsize=12, fontweight='bold')
        ax.set_title('RISK CONCENTRATION BUBBLE MAP', fontsize=14, fontweight='bold', pad=20)
        
        # Risk zones
        ax.axhspan(0.7, 1.0, alpha=0.1, color='red', label='Critical Risk')
        ax.axhspan(0.4, 0.7, alpha=0.1, color='orange', label='High Risk')
        ax.axhspan(0.0, 0.4, alpha=0.1, color='green', label='Low Risk')
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.xticks(rotation=45, ha='right')
        
        ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        # Annotate high-risk bubbles
        high_risk = df[df['risk'] > 0.7]
        for _, row in high_risk.iterrows():
            ax.annotate(
                row['accession'],
                xy=(row['date'], row['risk']),
                xytext=(10, 10),
                textcoords='offset points',
                fontsize=8,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
            )
        
        plt.tight_layout()
        
        output_path = self.output_dir / output_name
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_violation_breakdown(self, statute_refs: List[Dict], output_name: str = "violation_breakdown.png") -> Path:
        """Generate pie chart and bar chart of violation types"""
        
        if not statute_refs:
            return None
        
        # Count violations by statute
        violation_counts = {}
        for statute in statute_refs:
            vtype = statute.get('violation', 'Unknown')
            violation_counts[vtype] = violation_counts.get(vtype, 0) + 1
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Pie chart
        labels = list(violation_counts.keys())
        sizes = list(violation_counts.values())
        
        # Shorten labels for pie
        short_labels = [l[:30] + '...' if len(l) > 30 else l for l in labels]
        
        colors = plt.cm.Set3(range(len(labels)))
        
        ax1.pie(sizes, labels=short_labels, colors=colors, autopct='%1.1f%%',
               startangle=90)
        ax1.set_title('Violation Distribution', fontsize=14, fontweight='bold')
        
        # Bar chart with full labels
        ax2.barh(range(len(labels)), sizes, color=colors)
        ax2.set_yticks(range(len(labels)))
        ax2.set_yticklabels(labels, fontsize=9)
        ax2.set_xlabel('Count', fontsize=12, fontweight='bold')
        ax2.set_title('Violation Counts', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        
        output_path = self.output_dir / output_name
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_all_analytics(self, analysis_data: Dict) -> Dict[str, Path]:
        """Generate complete visual analytics suite"""
        
        filings = analysis_data.get('filings_analyzed', [])
        statute_refs = analysis_data.get('statute_references', [])
        
        outputs = {}
        
        # Timeline
        timeline_path = self.generate_transaction_timeline(filings)
        if timeline_path:
            outputs['timeline'] = timeline_path
        
        # Heat map
        heatmap_path = self.generate_filing_delay_heatmap(filings)
        if heatmap_path:
            outputs['heatmap'] = heatmap_path
        
        # Bubble chart
        bubble_path = self.generate_risk_bubble_chart(filings)
        if bubble_path:
            outputs['bubbles'] = bubble_path
        
        # Violation breakdown
        violation_path = self.generate_violation_breakdown(statute_refs)
        if violation_path:
            outputs['violations'] = violation_path
        
        return outputs
    
    # Helper methods
    
    def _parse_shares(self, shares_str: str) -> int:
        """Parse share count from string"""
        try:
            clean = str(shares_str).replace(',', '').strip()
            return int(float(clean))
        except:
            return 0
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price from string"""
        try:
            clean = str(price_str).replace('$', '').replace(',', '').strip()
            return float(clean)
        except:
            return 0.0


# Export
__all__ = ['VisualAnalyticsEngine']

