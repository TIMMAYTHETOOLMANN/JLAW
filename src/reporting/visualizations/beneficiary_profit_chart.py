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
from typing import List, Dict, Any
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

        # Detect all-zero profits and fall back to shares or transaction count
        all_profits = [b.get("total_profit", 0) for b in beneficiaries]
        use_profit = not all(p == 0 for p in all_profits)

        if use_profit:
            metric_key = "total_profit"
            metric_label = "Profit ($)"
            tick_fmt = "$,.0f"
            fmt_fn = lambda v: f"${v:,.0f}"
        else:
            # Try total_shares first, then transaction_count
            all_shares = [b.get("total_shares", 0) for b in beneficiaries]
            if any(s != 0 for s in all_shares):
                metric_key = "total_shares"
                metric_label = "Total Shares"
                tick_fmt = ",.0f"
                fmt_fn = lambda v: f"{v:,.0f}"
                self.logger.info(
                    "All total_profit values are 0 -- falling back to total_shares"
                )
            else:
                metric_key = "transaction_count"
                metric_label = "Transaction Count"
                tick_fmt = ",.0f"
                fmt_fn = lambda v: f"{v:,.0f}"
                self.logger.info(
                    "All total_profit values are 0 -- falling back to transaction_count"
                )

        # Sort by the chosen metric descending; filter out zero-value entries
        sorted_bens = sorted(
            beneficiaries, key=lambda x: x.get(metric_key, 0), reverse=True
        )
        sorted_bens = [b for b in sorted_bens if b.get(metric_key, 0) != 0]

        if not sorted_bens:
            return self._empty_figure(title)

        names = [f"{b['name']}\n({b.get('role', 'Unknown')})" for b in sorted_bens]
        metric_values = [b.get(metric_key, 0) for b in sorted_bens]
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
                name=metric_label,
                orientation="v",
                measure=["relative"] * len(names) + ["total"],
                x=names + ["TOTAL"],
                y=metric_values + [0],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                decreasing={"marker": {"color": "#FF6347"}},
                increasing={"marker": {"color": "#2ECC40"}},
                totals={"marker": {"color": "#0074D9"}},
                textposition="outside",
                text=[fmt_fn(v) for v in metric_values] + [""],
                textfont={"size": 10},
            )
        )

        fig.update_layout(
            title={
                "text": title,
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": "Arial, sans-serif"},
            },
            yaxis_title=metric_label,
            yaxis={"tickformat": tick_fmt},
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

        When all ``total_profit`` values are 0 the chart automatically falls
        back to ``total_shares`` (then ``violations``, then ``transaction_count``)
        so that the pie chart is still meaningful for Form 4 data where dollar
        values are unavailable.

        Args:
            beneficiaries: List of beneficiary dicts with 'role' and 'total_profit'
            title: Chart title

        Returns:
            Plotly figure object
        """
        if not beneficiaries:
            return self._empty_figure(title)

        # Determine which metric to use -----------------------------------------
        all_profits = [b.get("total_profit", 0) for b in beneficiaries]
        if any(p != 0 for p in all_profits):
            metric_key = "total_profit"
            metric_label = "Profit"
            val_tpl = "$%{value:,.0f}"
            hover_tpl = (
                "<b>%{label}</b><br>Profit: $%{value:,.0f}<br>"
                "Share: %{percent}<extra></extra>"
            )
        else:
            # Try total_shares, then violations, then transaction_count
            all_shares = [b.get("total_shares", 0) for b in beneficiaries]
            all_viols = [b.get("violations", 0) for b in beneficiaries]
            all_txns = [b.get("transaction_count", 0) for b in beneficiaries]
            if any(s != 0 for s in all_shares):
                metric_key = "total_shares"
                metric_label = "Shares"
                val_tpl = "%{value:,.0f}"
                hover_tpl = (
                    "<b>%{label}</b><br>Shares: %{value:,.0f}<br>"
                    "Share: %{percent}<extra></extra>"
                )
                self.logger.info(
                    "All total_profit values are 0 -- role distribution falling back to total_shares"
                )
            elif any(v != 0 for v in all_viols):
                metric_key = "violations"
                metric_label = "Violations"
                val_tpl = "%{value:,.0f}"
                hover_tpl = (
                    "<b>%{label}</b><br>Violations: %{value:,.0f}<br>"
                    "Share: %{percent}<extra></extra>"
                )
                self.logger.info(
                    "All total_profit values are 0 -- role distribution falling back to violations"
                )
            else:
                metric_key = "transaction_count"
                metric_label = "Transactions"
                val_tpl = "%{value:,.0f}"
                hover_tpl = (
                    "<b>%{label}</b><br>Transactions: %{value:,.0f}<br>"
                    "Share: %{percent}<extra></extra>"
                )
                self.logger.info(
                    "All total_profit values are 0 -- role distribution falling back to transaction_count"
                )

        # Aggregate by role using the chosen metric -----------------------------
        role_values: Dict[str, float] = {}
        for b in beneficiaries:
            role = b.get("role", "Other")
            role_values[role] = role_values.get(role, 0) + b.get(metric_key, 0)

        # Filter out zero-value roles to avoid empty slices
        role_values = {r: v for r, v in role_values.items() if v != 0}
        if not role_values:
            return self._empty_figure(title)

        roles = list(role_values.keys())
        values = list(role_values.values())
        colors = [self.ROLE_COLORS.get(r, "#778899") for r in roles]

        fig = go.Figure(
            go.Pie(
                labels=roles,
                values=values,
                hole=0.4,
                marker={"colors": colors, "line": {"color": "white", "width": 2}},
                textinfo="label+percent+value",
                texttemplate=f"%{{label}}<br>%{{percent}}<br>{val_tpl}",
                hovertemplate=hover_tpl,
            )
        )

        chart_title = title
        if metric_key != "total_profit":
            chart_title = title.replace("Profit", metric_label) if "Profit" in title else title

        fig.update_layout(
            title={
                "text": chart_title,
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
                marker={
                    "colors": [
                        self.ROLE_COLORS.get(r, "#778899")
                        for r in role_profits.keys()
                    ]
                },
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
                textfont={"size": 8},
                marker={
                    "size": [max(8, v * 5 + 8) for v in all_viols],
                    "color": all_risks,
                    "colorscale": "RdYlGn_r",
                    "line": {"width": 1, "color": "white"},
                },
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
            x=0.5, y=0.5, showarrow=False, font={"size": 20},
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
