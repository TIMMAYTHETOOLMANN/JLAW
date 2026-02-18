"""
Beneficiary Profit Chart - Phase 4 Enhanced Visualization
=========================================================

Generates visualizations for financial beneficiary analysis:
- Profit waterfall charts per benefiting party
- Role-based profit distribution pie/donut charts
- Dollar amount quantification with color-coded severity

Uses plotly for interactive charts.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


class BeneficiaryProfitChart:
    """
    Generates financial beneficiary visualizations.

    Usage:
        generator = BeneficiaryProfitChart()
        fig = generator.generate_profit_waterfall(
            beneficiaries=[...],
            title="NIKE 2019 Beneficiary Profit Analysis"
        )
        fig.show()
    """

    ROLE_COLORS = {
        "CEO": "#DC143C",
        "CFO": "#FF6347",
        "COO": "#FF8C00",
        "Director": "#4169E1",
        "VP": "#9370DB",
        "Officer": "#20B2AA",
        "10% Owner": "#CD853F",
        "Other": "#778899",
    }

    def __init__(self):
        """Initialize the beneficiary profit chart generator."""
        self.logger = logging.getLogger(__name__)

    def generate_profit_waterfall(
        self,
        beneficiaries: List[Dict[str, Any]],
        title: str = "Beneficiary Profit Waterfall",
    ) -> go.Figure:
        """
        Generate a waterfall chart showing profit per beneficiary.

        Args:
            beneficiaries: List of beneficiary dicts with keys:
                - name: Beneficiary name
                - role: Role (CEO, CFO, etc.)
                - total_profit: Total estimated profit ($)
                - risk_score: Risk score (0-100)
            title: Chart title

        Returns:
            Plotly figure object
        """
        self.logger.info(
            f"Generating profit waterfall for {len(beneficiaries)} beneficiaries"
        )

        if not beneficiaries:
            return self._empty_figure(title)

        # Sort by profit descending
        sorted_bens = sorted(
            beneficiaries, key=lambda x: x.get("total_profit", 0), reverse=True
        )

        names = [f"{b['name']}\n({b.get('role', 'Unknown')})" for b in sorted_bens]
        profits = [b.get("total_profit", 0) for b in sorted_bens]
        risk_scores = [b.get("risk_score", 0) for b in sorted_bens]

        # Color by risk score
        colors = []
        for rs in risk_scores:
            if rs >= 80:
                colors.append("#DC143C")
            elif rs >= 60:
                colors.append("#FF6347")
            elif rs >= 40:
                colors.append("#FFD700")
            else:
                colors.append("#32CD32")

        fig = go.Figure(
            go.Waterfall(
                name="Profit",
                orientation="v",
                measure=["relative"] * len(names) + ["total"],
                x=names + ["TOTAL"],
                y=profits + [0],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                decreasing={"marker": {"color": "#FF6347"}},
                increasing={"marker": {"color": "#2ECC40"}},
                totals={"marker": {"color": "#0074D9"}},
                textposition="outside",
                text=[f"${p:,.0f}" for p in profits] + [""],
                textfont=dict(size=10),
            )
        )

        fig.update_layout(
            title={
                "text": title,
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": "Arial, sans-serif"},
            },
            yaxis_title="Profit ($)",
            yaxis=dict(tickformat="$,.0f"),
            showlegend=False,
            template="plotly_white",
            height=600,
            width=max(900, len(names) * 120),
        )

        self.logger.info("Profit waterfall generation complete")
        return fig

    def generate_role_distribution(
        self,
        beneficiaries: List[Dict[str, Any]],
        title: str = "Profit Distribution by Role",
    ) -> go.Figure:
        """
        Generate a donut chart showing profit distribution by role.

        Args:
            beneficiaries: List of beneficiary dicts with 'role' and 'total_profit'
            title: Chart title

        Returns:
            Plotly figure object
        """
        if not beneficiaries:
            return self._empty_figure(title)

        # Aggregate by role
        role_profits: Dict[str, float] = {}
        for b in beneficiaries:
            role = b.get("role", "Other")
            role_profits[role] = role_profits.get(role, 0) + b.get("total_profit", 0)

        roles = list(role_profits.keys())
        profits = list(role_profits.values())
        colors = [self.ROLE_COLORS.get(r, "#778899") for r in roles]

        fig = go.Figure(
            go.Pie(
                labels=roles,
                values=profits,
                hole=0.4,
                marker=dict(colors=colors, line=dict(color="white", width=2)),
                textinfo="label+percent+value",
                texttemplate="%{label}<br>%{percent}<br>$%{value:,.0f}",
                hovertemplate="<b>%{label}</b><br>Profit: $%{value:,.0f}<br>"
                "Share: %{percent}<extra></extra>",
            )
        )

        fig.update_layout(
            title={
                "text": title,
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": "Arial, sans-serif"},
            },
            template="plotly_white",
            height=600,
            width=800,
        )

        self.logger.info("Role distribution chart generation complete")
        return fig

    def generate_profit_risk_dashboard(
        self,
        beneficiaries: List[Dict[str, Any]],
        title: str = "Beneficiary Profit & Risk Dashboard",
    ) -> go.Figure:
        """
        Generate a 2x2 dashboard with profit and risk metrics.

        Args:
            beneficiaries: List of beneficiary dicts with keys:
                - name, role, total_profit, transaction_count, risk_score, violations
            title: Chart title

        Returns:
            Plotly figure with subplots
        """
        if not beneficiaries:
            return self._empty_figure(title)

        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Top Beneficiaries by Profit",
                "Profit by Role",
                "Risk Score vs Profit",
                "Violation Count by Beneficiary",
            ),
            specs=[
                [{"type": "bar"}, {"type": "pie"}],
                [{"type": "scatter"}, {"type": "bar"}],
            ],
        )

        sorted_bens = sorted(
            beneficiaries, key=lambda x: x.get("total_profit", 0), reverse=True
        )[:10]

        # 1. Top beneficiaries bar chart
        names = [b.get("name", "Unknown") for b in sorted_bens]
        profits = [b.get("total_profit", 0) for b in sorted_bens]
        risk_scores = [b.get("risk_score", 0) for b in sorted_bens]

        bar_colors = []
        for rs in risk_scores:
            if rs >= 80:
                bar_colors.append("#DC143C")
            elif rs >= 60:
                bar_colors.append("#FF6347")
            elif rs >= 40:
                bar_colors.append("#FFD700")
            else:
                bar_colors.append("#32CD32")

        fig.add_trace(
            go.Bar(
                x=names,
                y=profits,
                marker_color=bar_colors,
                name="Profit",
                showlegend=False,
            ),
            row=1,
            col=1,
        )

        # 2. Profit by role donut
        role_profits: Dict[str, float] = {}
        for b in beneficiaries:
            role = b.get("role", "Other")
            role_profits[role] = role_profits.get(role, 0) + b.get("total_profit", 0)

        fig.add_trace(
            go.Pie(
                labels=list(role_profits.keys()),
                values=list(role_profits.values()),
                hole=0.4,
                marker=dict(
                    colors=[
                        self.ROLE_COLORS.get(r, "#778899")
                        for r in role_profits.keys()
                    ]
                ),
                showlegend=False,
            ),
            row=1,
            col=2,
        )

        # 3. Risk vs profit scatter
        all_names = [b.get("name", "Unknown") for b in beneficiaries]
        all_profits = [b.get("total_profit", 0) for b in beneficiaries]
        all_risks = [b.get("risk_score", 0) for b in beneficiaries]
        all_viols = [b.get("violations", 0) for b in beneficiaries]

        fig.add_trace(
            go.Scatter(
                x=all_risks,
                y=all_profits,
                mode="markers+text",
                text=all_names,
                textposition="top center",
                textfont=dict(size=8),
                marker=dict(
                    size=[max(8, v * 5 + 8) for v in all_viols],
                    color=all_risks,
                    colorscale="RdYlGn_r",
                    line=dict(width=1, color="white"),
                ),
                showlegend=False,
            ),
            row=2,
            col=1,
        )

        # 4. Violations bar chart
        sorted_by_viols = sorted(
            beneficiaries, key=lambda x: x.get("violations", 0), reverse=True
        )[:10]

        fig.add_trace(
            go.Bar(
                x=[b.get("name", "Unknown") for b in sorted_by_viols],
                y=[b.get("violations", 0) for b in sorted_by_viols],
                marker_color="#FF4136",
                name="Violations",
                showlegend=False,
            ),
            row=2,
            col=2,
        )

        fig.update_layout(
            title={
                "text": title,
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18, "family": "Arial, sans-serif"},
            },
            template="plotly_white",
            height=900,
            width=1200,
        )

        # Format axes
        fig.update_yaxes(tickformat="$,.0f", row=1, col=1)
        fig.update_yaxes(tickformat="$,.0f", row=2, col=1)
        fig.update_xaxes(title_text="Risk Score", row=2, col=1)
        fig.update_yaxes(title_text="Profit ($)", row=2, col=1)

        self.logger.info("Profit risk dashboard generation complete")
        return fig

    def _empty_figure(self, title: str) -> go.Figure:
        """Return an empty figure with a message."""
        fig = go.Figure()
        fig.add_annotation(
            text="No beneficiary data available", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(size=20),
        )
        fig.update_layout(title=title, template="plotly_white", height=400, width=800)
        return fig

    def save_chart(
        self, fig: go.Figure, output_path: Path, format: str = "html",
    ) -> Path:
        """Save chart figure to file."""
        if format == "html":
            fig.write_html(str(output_path))
        elif format == "png":
            fig.write_image(str(output_path))
        elif format == "svg":
            fig.write_image(str(output_path), format="svg")
        else:
            raise ValueError(f"Unsupported format: {format}")

        self.logger.info(f"Beneficiary chart saved to {output_path}")
        return output_path
