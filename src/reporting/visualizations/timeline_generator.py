"""
Timeline Generator - Phase 4 Visualization
==========================================

Generates transaction timeline visualizations with material events overlaid.

Features:
- Chronological transaction display
- Material event markers (earnings calls, 8-K filings)
- Risk level color coding
- Interactive plotly charts
- Export to PNG/SVG
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from io import BytesIO

import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


class TimelineGenerator:
    """
    Generates timeline visualizations of transactions and material events.

    Usage:
        generator = TimelineGenerator()
        fig = generator.generate_timeline(
            transactions=[...],
            material_events=[...],
            title="NIKE 2019 Insider Trading Timeline"
        )
        fig.show()  # Interactive
        fig.write_image("timeline.png")  # Static
    """

    MAX_ACTOR_NAME_LEN = 25

    def __init__(self):
        """Initialize the timeline generator."""
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _parse_date(value) -> date:
        """Convert a date string or datetime to a datetime.date object."""
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
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
    
    def generate_timeline(
        self,
        transactions: List[Dict[str, Any]],
        material_events: List[Dict[str, Any]] = None,
        title: str = "Transaction Timeline",
        show_actor_labels: bool = True,
    ) -> go.Figure:
        """
        Generate an interactive timeline visualization.
        
        Args:
            transactions: List of transaction dicts with keys:
                - date: Transaction date
                - actor: Actor name
                - value: Transaction value
                - shares: Number of shares
                - risk_level: Risk level (CRITICAL, HIGH, MEDIUM, LOW)
                - transaction_type: Type (SALE, PURCHASE, GRANT, etc.)
            material_events: List of material event dicts with keys:
                - date: Event date
                - event_type: Type (EARNINGS_CALL, 8K_FILING, etc.)
                - description: Event description
            title: Chart title
            show_actor_labels: Whether to show actor names on hover
            
        Returns:
            Plotly figure object
        """
        self.logger.info(f"Generating timeline with {len(transactions)} transactions")

        if material_events is None:
            material_events = []

        # Create figure
        fig = go.Figure()

        # Sort transactions by date (parse strings to real dates for proper axis)
        transactions_sorted = sorted(
            transactions,
            key=lambda x: self._parse_date(x.get('date', date.today())),
        )

        # Detect whether dollar values are all zero; if so fall back to shares
        all_values = [abs(txn.get('value', 0)) for txn in transactions_sorted]
        use_shares = all(v == 0 for v in all_values)
        if use_shares:
            self.logger.info(
                "All transaction dollar values are 0 -- falling back to shares as y-axis metric"
            )
        y_label = "Shares" if use_shares else "Transaction Value ($)"

        # Color mapping for risk levels
        risk_colors = {
            'CRITICAL': 'red',
            'HIGH': 'orange',
            'MEDIUM': 'yellow',
            'LOW': 'green',
        }

        # Group transactions by risk level for legend
        transactions_by_risk: Dict[str, List[Dict[str, Any]]] = {}
        for txn in transactions_sorted:
            risk = txn.get('risk_level', 'LOW')
            if risk not in transactions_by_risk:
                transactions_by_risk[risk] = []
            transactions_by_risk[risk].append(txn)

        # Add transaction scatter plots by risk level
        for risk_level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if risk_level not in transactions_by_risk:
                continue

            txns = transactions_by_risk[risk_level]
            dates = [self._parse_date(txn.get('date')) for txn in txns]
            values = [abs(txn.get('value', 0)) for txn in txns]
            shares = [abs(txn.get('shares', 0)) for txn in txns]
            actors = [
                self._truncate_name(txn.get('actor', 'Unknown'), self.MAX_ACTOR_NAME_LEN)
                for txn in txns
            ]

            # Choose the y-axis metric
            y_values = shares if use_shares else values

            # Compute relative marker sizing based on the chosen metric
            max_metric = max(y_values) if y_values and max(y_values) > 0 else 1
            marker_sizes = [max(8, (v / max_metric) * 30) for v in y_values]

            hover_text = [
                f"<b>{actor}</b><br>"
                f"Date: {dt}<br>"
                f"Value: ${val:,.0f}<br>"
                f"Shares: {sh:,}<br>"
                f"Risk: {risk_level}"
                for actor, dt, val, sh in zip(actors, dates, values, shares)
            ]

            fig.add_trace(go.Scatter(
                x=dates,
                y=y_values,
                mode='markers',
                name=risk_level,
                marker=dict(
                    size=marker_sizes,
                    color=risk_colors[risk_level],
                    line=dict(width=2, color='white'),
                ),
                text=hover_text,
                hoverinfo='text',
            ))

        # Add material event markers
        if material_events:
            event_dates = [self._parse_date(evt.get('date')) for evt in material_events]
            event_descriptions = [evt.get('description', '') for evt in material_events]

            for evt_date, evt_desc in zip(event_dates, event_descriptions):
                fig.add_vline(
                    x=evt_date,
                    line_dash="dash",
                    line_color="purple",
                    annotation_text=evt_desc,
                    annotation_position="top",
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
            yaxis_title=y_label,
            hovermode='closest',
            showlegend=True,
            legend=dict(
                title="Risk Level",
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            template="plotly_white",
            height=600,
            width=1200,
            xaxis=dict(tickangle=45),
        )

        self.logger.info("Timeline generation complete")
        return fig
    
    def save_timeline(
        self,
        fig: go.Figure,
        output_path: Path,
        format: str = 'png',
    ) -> Path:
        """
        Save timeline figure to file.
        
        Args:
            fig: Plotly figure
            output_path: Output file path
            format: Output format ('png', 'svg', 'html')
            
        Returns:
            Path to saved file
        """
        if format == 'html':
            fig.write_html(str(output_path))
        elif format == 'png':
            fig.write_image(str(output_path))
        elif format == 'svg':
            fig.write_image(str(output_path), format='svg')
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        self.logger.info(f"Timeline saved to {output_path}")
        return output_path
    
    def generate_timeline_bytes(
        self,
        transactions: List[Dict[str, Any]],
        material_events: List[Dict[str, Any]] = None,
        title: str = "Transaction Timeline",
        format: str = 'png',
    ) -> bytes:
        """
        Generate timeline as bytes for embedding in PDF.
        
        Args:
            transactions: List of transactions
            material_events: List of material events
            title: Chart title
            format: Output format ('png', 'svg')
            
        Returns:
            Bytes of the generated image
        """
        fig = self.generate_timeline(transactions, material_events, title)
        
        if format == 'png':
            img_bytes = fig.to_image(format='png')
        elif format == 'svg':
            img_bytes = fig.to_image(format='svg')
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return img_bytes
