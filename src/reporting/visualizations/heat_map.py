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

    MAX_ACTORS = 15
    MAX_ACTOR_NAME_LEN = 25

    def __init__(self):
        """Initialize the heatmap generator."""
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _parse_date(value):
        """Convert a date string or datetime to a datetime.date object."""
        from datetime import date as _date
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, _date):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value).date()
            except (ValueError, TypeError):
                pass
        return date.today()

    @staticmethod
    def _truncate_name(name: str, max_len: int = 25) -> str:
        """Truncate a name to *max_len* characters."""
        if len(name) > max_len:
            return name[:max_len - 1] + "\u2026"
        return name
    
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

        # Auto-switch metric when 'value' is requested but all values are 0
        if metric == 'value':
            all_vals = [abs(txn.get('value', 0)) for txn in transactions]
            if all(v == 0 for v in all_vals):
                self.logger.info(
                    "All transaction dollar values are 0 -- auto-switching heatmap metric to shares"
                )
                metric = 'shares'

        # Build actor x date matrix
        actor_date_data = defaultdict(lambda: defaultdict(float))
        actors = set()
        dates = set()

        for txn in transactions:
            actor = txn.get('actor', 'Unknown')
            txn_date = self._parse_date(txn.get('date'))

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

        # Limit to top-N actors to prevent overcrowding
        if len(sorted_actors) > self.MAX_ACTORS:
            self.logger.info(
                f"Limiting heatmap to top {self.MAX_ACTORS} actors (of {len(sorted_actors)})"
            )
            sorted_actors = sorted_actors[: self.MAX_ACTORS]

        # Truncate long actor names for display
        display_actors = [
            self._truncate_name(a, self.MAX_ACTOR_NAME_LEN) for a in sorted_actors
        ]

        # Sort dates
        sorted_dates = sorted(dates)

        # Build Z matrix
        z_matrix = []
        for actor in sorted_actors:
            row = [actor_date_data[actor].get(dt, 0) for dt in sorted_dates]
            z_matrix.append(row)

        # Choose hover template based on active metric
        if metric == 'shares':
            hover_tpl = '<b>%{y}</b><br>Date: %{x}<br>Shares: %{z:,.0f}<extra></extra>'
        elif metric == 'count':
            hover_tpl = '<b>%{y}</b><br>Date: %{x}<br>Count: %{z:,.0f}<extra></extra>'
        else:
            hover_tpl = '<b>%{y}</b><br>Date: %{x}<br>Value: $%{z:,.0f}<extra></extra>'

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=z_matrix,
            x=[str(dt) for dt in sorted_dates],
            y=display_actors,
            colorscale='Reds',
            hovertemplate=hover_tpl,
        ))

        # Add material event annotations
        if material_events:
            date_strings = [str(dt) for dt in sorted_dates]
            for evt in material_events:
                evt_date_str = str(self._parse_date(evt.get('date')))
                if evt_date_str in date_strings:
                    x_idx = date_strings.index(evt_date_str)
                    fig.add_vline(
                        x=x_idx,
                        line_dash="dash",
                        line_color="blue",
                        line_width=2,
                    )

        # Metric label for y-axis colorbar context
        metric_label = {"value": "Value ($)", "shares": "Shares", "count": "Count"}.get(
            metric, "Value ($)"
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
            height=max(400, len(display_actors) * 30),
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
