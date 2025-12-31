"""
Heat Map Generator - Phase 4 Visualization
==========================================

Generates trading intensity heatmaps showing:
- Trading patterns by actor and date
- Earnings call proximity analysis
- Material event correlation

Uses plotly for interactive heatmaps.
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import defaultdict

import plotly.graph_objects as go
import numpy as np

logger = logging.getLogger(__name__)


class HeatMapGenerator:
    """
    Generates trading intensity heatmaps.
    
    Usage:
        generator = HeatMapGenerator()
        fig = generator.generate_heatmap(
            transactions=[...],
            material_events=[...],
            title="NIKE 2019 Trading Intensity"
        )
        fig.show()
    """
    
    def __init__(self):
        """Initialize the heatmap generator."""
        self.logger = logging.getLogger(__name__)
    
    def generate_heatmap(
        self,
        transactions: List[Dict[str, Any]],
        material_events: List[Dict[str, Any]] = None,
        title: str = "Trading Intensity Heatmap",
        metric: str = 'value',  # 'value', 'shares', 'count'
    ) -> go.Figure:
        """
        Generate a trading intensity heatmap.
        
        Args:
            transactions: List of transaction dicts with keys:
                - date: Transaction date
                - actor: Actor name
                - value: Transaction value
                - shares: Number of shares
            material_events: List of material events for annotation
            title: Chart title
            metric: Metric to visualize ('value', 'shares', 'count')
            
        Returns:
            Plotly figure object
        """
        self.logger.info(f"Generating heatmap with {len(transactions)} transactions")
        
        if material_events is None:
            material_events = []
        
        # Build actor x date matrix
        actor_date_data = defaultdict(lambda: defaultdict(float))
        actors = set()
        dates = set()
        
        for txn in transactions:
            actor = txn.get('actor', 'Unknown')
            txn_date = txn.get('date')
            
            if metric == 'value':
                value = abs(txn.get('value', 0))
            elif metric == 'shares':
                value = abs(txn.get('shares', 0))
            elif metric == 'count':
                value = 1
            else:
                value = abs(txn.get('value', 0))
            
            actor_date_data[actor][txn_date] += value
            actors.add(actor)
            dates.add(txn_date)
        
        # Sort actors by total activity
        actor_totals = {
            actor: sum(actor_date_data[actor].values())
            for actor in actors
        }
        sorted_actors = sorted(actors, key=lambda x: actor_totals[x], reverse=True)
        
        # Sort dates
        sorted_dates = sorted(dates)
        
        # Build Z matrix
        z_matrix = []
        for actor in sorted_actors:
            row = [actor_date_data[actor].get(dt, 0) for dt in sorted_dates]
            z_matrix.append(row)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=z_matrix,
            x=[str(dt) for dt in sorted_dates],
            y=sorted_actors,
            colorscale='Reds',
            hovertemplate='<b>%{y}</b><br>Date: %{x}<br>Value: $%{z:,.0f}<extra></extra>',
        ))
        
        # Add material event annotations
        if material_events:
            event_dates = [str(evt.get('date')) for evt in material_events]
            for evt_date in event_dates:
                if evt_date in [str(dt) for dt in sorted_dates]:
                    x_idx = [str(dt) for dt in sorted_dates].index(evt_date)
                    fig.add_vline(
                        x=x_idx,
                        line_dash="dash",
                        line_color="blue",
                        line_width=2,
                    )
        
        # Update layout
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'family': 'Arial, sans-serif'}
            },
            xaxis_title="Date",
            yaxis_title="Actor",
            template="plotly_white",
            height=max(400, len(sorted_actors) * 30),
            width=1200,
        )
        
        self.logger.info("Heatmap generation complete")
        return fig
    
    def save_heatmap(
        self,
        fig: go.Figure,
        output_path: Path,
        format: str = 'png',
    ) -> Path:
        """Save heatmap figure to file."""
        if format == 'html':
            fig.write_html(str(output_path))
        elif format == 'png':
            fig.write_image(str(output_path))
        elif format == 'svg':
            fig.write_image(str(output_path), format='svg')
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        self.logger.info(f"Heatmap saved to {output_path}")
        return output_path
