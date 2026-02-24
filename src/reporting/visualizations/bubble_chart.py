"""
Bubble Chart Generator - Phase 4 Enhanced Visualization
=======================================================

Generates bubble chart visualizations showing:
- Transaction value (bubble size) by actor and date
- Risk level color coding
- Filing type categorization
- Profit/loss quantification per benefiting party

Uses plotly for interactive bubble charts.
"""

import logging
from datetime import date, datetime
from typing import List, Dict, Any
from pathlib import Path

import plotly.graph_objects as go

logger = logging.getLogger(__name__)


class BubbleChartGenerator:
    """
    Generates bubble chart visualizations for financial forensic analysis.

    Usage:
        generator = BubbleChartGenerator()
        fig = generator.generate_transaction_bubbles(
            transactions=[...],
            title="NIKE 2019 Transaction Bubble Chart"
        )
        fig.show()
    """

    RISK_COLORS = {
        "CRITICAL": "#DC143C",
        "HIGH": "#FF6347",
        "MEDIUM": "#FFD700",
        "LOW": "#32CD32",
    }

    TRANSACTION_SYMBOLS = {
        "SALE": "circle",
        "PURCHASE": "diamond",
        "GRANT": "square",
        "EXERCISE": "triangle-up",
        "GIFT": "star",
        "OTHER": "circle",
    }

    def __init__(self):
        """Initialize the bubble chart generator."""
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

    def generate_transaction_bubbles(
        self,
        transactions: List[Dict[str, Any]],
        title: str = "Transaction Bubble Chart",
        size_metric: str = "value",
        color_by: str = "risk_level",
    ) -> go.Figure:
        """
        Generate a bubble chart of transactions.

        Args:
            transactions: List of transaction dicts with keys:
                - date: Transaction date
                - actor: Actor name
                - value: Transaction value ($)
                - shares: Number of shares
                - risk_level: Risk level (CRITICAL, HIGH, MEDIUM, LOW)
                - transaction_type: Type (SALE, PURCHASE, GRANT, etc.)
                - profit: Estimated profit/benefit ($)
            title: Chart title
            size_metric: Metric for bubble size ('value', 'shares', 'profit')
            color_by: Metric for bubble color ('risk_level', 'transaction_type')

        Returns:
            Plotly figure object
        """
        self.logger.info(f"Generating bubble chart with {len(transactions)} transactions")

        if not transactions:
            return self._empty_figure(title)

        # Auto-fallback: when size_metric is 'value' but all values are 0, use shares
        if size_metric == "value":
            all_vals = [abs(txn.get("value", 0)) for txn in transactions]
            if all(v == 0 for v in all_vals):
                self.logger.info(
                    "All transaction dollar values are 0 -- falling back to shares for bubble size"
                )
                size_metric = "shares"

        fig = go.Figure()

        # Group by the color metric
        if color_by == "risk_level":
            groups = {}
            for txn in transactions:
                key = txn.get("risk_level", "LOW")
                groups.setdefault(key, []).append(txn)

            for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                if level not in groups:
                    continue
                self._add_bubble_trace(
                    fig, groups[level], level, self.RISK_COLORS.get(level, "#888"),
                    size_metric,
                )
        else:
            groups = {}
            for txn in transactions:
                key = txn.get("transaction_type", "OTHER")
                groups.setdefault(key, []).append(txn)

            palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
            for i, (txn_type, txns) in enumerate(groups.items()):
                self._add_bubble_trace(
                    fig, txns, txn_type, palette[i % len(palette)], size_metric,
                )

        fig.update_layout(
            title={
                "text": title,
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": "Arial, sans-serif"},
            },
            xaxis_title="Date",
            yaxis_title="Actor",
            hovermode="closest",
            showlegend=True,
            legend={"title": "Category", "orientation": "v", "yanchor": "top", "y": 1, "x": 1.02},
            template="plotly_white",
            height=700,
            width=1200,
        )

        self.logger.info("Bubble chart generation complete")
        return fig

    def generate_beneficiary_profit_bubbles(
        self,
        beneficiaries: List[Dict[str, Any]],
        title: str = "Financial Beneficiary Analysis",
    ) -> go.Figure:
        """
        Generate a bubble chart showing benefiting parties and their profits.

        Args:
            beneficiaries: List of beneficiary dicts with keys:
                - name: Beneficiary name
                - role: Role (CEO, CFO, Director, etc.)
                - total_profit: Total estimated profit ($)
                - transaction_count: Number of transactions
                - risk_score: Risk score (0-100)
                - violations: Number of associated violations
            title: Chart title

        Returns:
            Plotly figure object
        """
        self.logger.info(
            f"Generating beneficiary profit bubbles for {len(beneficiaries)} beneficiaries"
        )

        if not beneficiaries:
            return self._empty_figure(title)

        names = [b.get("name", "Unknown") for b in beneficiaries]
        profits = [b.get("total_profit", 0) for b in beneficiaries]
        txn_counts = [b.get("transaction_count", 1) for b in beneficiaries]
        risk_scores = [b.get("risk_score", 0) for b in beneficiaries]
        violations = [b.get("violations", 0) for b in beneficiaries]
        roles = [b.get("role", "Unknown") for b in beneficiaries]

        # Scale bubble size
        max_profit = max(profits) if max(profits) > 0 else 1
        bubble_sizes = [max(10, (p / max_profit) * 80) for p in profits]

        hover_text = [
            f"<b>{name}</b><br>"
            f"Role: {role}<br>"
            f"Total Profit: ${profit:,.0f}<br>"
            f"Transactions: {txn}<br>"
            f"Risk Score: {risk:.1f}<br>"
            f"Violations: {viol}"
            for name, role, profit, txn, risk, viol in zip(
                names, roles, profits, txn_counts, risk_scores, violations
            )
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=txn_counts,
                y=profits,
                mode="markers+text",
                marker={
                    "size": bubble_sizes,
                    "color": risk_scores,
                    "colorscale": "RdYlGn_r",
                    "colorbar": {"title": "Risk Score"},
                    "line": {"width": 2, "color": "white"},
                    "opacity": 0.85,
                },
                text=names,
                textposition="top center",
                textfont={"size": 10},
                hovertext=hover_text,
                hoverinfo="text",
            )
        )

        fig.update_layout(
            title={
                "text": title,
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": "Arial, sans-serif"},
            },
            xaxis_title="Transaction Count",
            yaxis_title="Total Estimated Profit ($)",
            yaxis={"tickformat": "$,.0f"},
            hovermode="closest",
            template="plotly_white",
            height=700,
            width=1200,
        )

        self.logger.info("Beneficiary profit bubble chart complete")
        return fig

    def _add_bubble_trace(
        self,
        fig: go.Figure,
        transactions: List[Dict[str, Any]],
        name: str,
        color: str,
        size_metric: str,
    ):
        """Add a bubble trace for a group of transactions."""
        dates = [self._parse_date(txn.get("date", date.today())) for txn in transactions]
        actors = [txn.get("actor", "Unknown") for txn in transactions]
        values = [abs(txn.get("value", 0)) for txn in transactions]
        shares = [abs(txn.get("shares", 0)) for txn in transactions]
        profits = [abs(txn.get("profit", 0)) for txn in transactions]

        if size_metric == "shares":
            sizes_raw = shares
        elif size_metric == "profit":
            sizes_raw = profits
        else:
            sizes_raw = values

        max_val = max(sizes_raw) if sizes_raw and max(sizes_raw) > 0 else 1
        # Ensure a minimum bubble size so zero-value entries still appear
        sizes = [max(8, (v / max_val) * 50) for v in sizes_raw]

        hover_text = [
            f"<b>{actor}</b><br>"
            f"Date: {dt}<br>"
            f"Value: ${val:,.0f}<br>"
            f"Shares: {sh:,}<br>"
            f"Profit: ${pr:,.0f}"
            for actor, dt, val, sh, pr in zip(actors, dates, values, shares, profits)
        ]

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=actors,
                mode="markers",
                name=name,
                marker={
                    "size": sizes,
                    "color": color,
                    "line": {"width": 1.5, "color": "white"},
                    "opacity": 0.8,
                },
                text=hover_text,
                hoverinfo="text",
            )
        )

    def _empty_figure(self, title: str) -> go.Figure:
        """Return an empty figure with a message."""
        fig = go.Figure()
        fig.add_annotation(
            text="No data available", xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font={"size": 20},
        )
        fig.update_layout(title=title, template="plotly_white", height=400, width=800)
        return fig

    def save_chart(
        self, fig: go.Figure, output_path: Path, format: str = "html",
    ) -> Path:
        """Save bubble chart figure to file."""
        if format == "html":
            fig.write_html(str(output_path))
        elif format == "png":
            fig.write_image(str(output_path))
        elif format == "svg":
            fig.write_image(str(output_path), format="svg")
        else:
            raise ValueError(f"Unsupported format: {format}")

        self.logger.info(f"Bubble chart saved to {output_path}")
        return output_path
