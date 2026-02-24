"""
Filing Deadline Compliance Chart - Phase 4 Enhanced Visualization
================================================================

Generates visualizations showing:
- Filing dates vs regulatory deadlines
- Compliance/late filing indicators
- Annual report timeline markers
- Color-coded compliance status

Uses plotly for interactive timeline charts.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    go = None
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)


# SEC filing deadline rules (calendar days after trigger)
FILING_DEADLINES = {
    "Form 4": 2,          # 2 business days after transaction
    "10-K": 60,           # 60 days after fiscal year end (large accelerated)
    "10-Q": 40,           # 40 days after fiscal quarter end (large accelerated)
    "8-K": 4,             # 4 business days after triggering event
    "DEF 14A": 120,       # No fixed deadline, typically 120 days before annual meeting
    "SC 13D": 10,         # 10 days after crossing 5% ownership
    "SC 13G": 45,         # 45 days after calendar year end
    "Form 144": 0,        # Concurrent with or before sale
    "13F-HR": 45,         # 45 days after calendar quarter end
}


class FilingDeadlineChart:
    """
    Generates filing deadline compliance visualizations.

    Usage:
        generator = FilingDeadlineChart()
        fig = generator.generate_deadline_chart(
            filings=[...],
            title="NIKE 2019 Filing Compliance Timeline"
        )
        fig.show()
    """

    STATUS_COLORS = {
        "ON_TIME": "#2ECC40",
        "LATE": "#FF4136",
        "AMENDED": "#FF851B",
        "UNKNOWN": "#AAAAAA",
    }

    def __init__(self):
        """Initialize the filing deadline chart generator."""
        self.logger = logging.getLogger(__name__)

    def generate_deadline_chart(
        self,
        filings: List[Dict[str, Any]],
        annual_events: List[Dict[str, Any]] = None,
        title: str = "Filing Deadline Compliance",
    ):
        """
        Generate a filing deadline compliance chart.

        Args:
            filings: List of filing dicts with keys:
                - filing_type: Type of filing (Form 4, 10-K, etc.)
                - filing_date: Date the filing was submitted
                - trigger_date: Date of triggering event/period end
                - deadline_date: Regulatory deadline (optional, calculated if missing)
                - filer: Name of the filing party
                - status: ON_TIME, LATE, AMENDED (optional, calculated if missing)
                - days_margin: Days before/after deadline (optional)
            annual_events: List of annual event dicts with keys:
                - date: Event date
                - event_type: FISCAL_YEAR_END, ANNUAL_MEETING, EARNINGS, etc.
                - description: Event description
            title: Chart title

        Returns:
            Plotly figure object, or None if plotly is not installed
        """
        if not HAS_PLOTLY:
            self.logger.warning("plotly is not installed -- skipping deadline chart generation")
            return None

        self.logger.info(f"Generating deadline chart with {len(filings)} filings")

        if annual_events is None:
            annual_events = []

        if not filings:
            return self._empty_figure(title)

        fig = go.Figure()

        # Calculate compliance status for each filing
        filings_enriched = self._enrich_filings(filings)

        # Group filings by status
        for status in ["LATE", "AMENDED", "ON_TIME", "UNKNOWN"]:
            group = [f for f in filings_enriched if f.get("status") == status]
            if not group:
                continue

            filing_dates = [f["filing_date"] for f in group]
            filing_types = [f["filing_type"] for f in group]
            filers = [f.get("filer", "Unknown") for f in group]
            margins = [f.get("days_margin", 0) for f in group]

            hover_text = [
                f"<b>{filer}</b><br>"
                f"Filing: {ftype}<br>"
                f"Filed: {fdate}<br>"
                f"Deadline: {f.get('deadline_date', 'N/A')}<br>"
                f"Margin: {margin:+d} days<br>"
                f"Status: {status}"
                for filer, ftype, fdate, margin, f in zip(
                    filers, filing_types, filing_dates, margins, group
                )
            ]

            marker_size = [max(8, min(25, abs(m) + 8)) for m in margins]

            fig.add_trace(
                go.Scatter(
                    x=filing_dates,
                    y=filing_types,
                    mode="markers",
                    name=status.replace("_", " ").title(),
                    marker={
                        "size": marker_size,
                        "color": self.STATUS_COLORS.get(status, "#888"),
                        "line": {"width": 1.5, "color": "white"},
                        "symbol": "circle" if status != "LATE" else "x",
                        "opacity": 0.85,
                    },
                    text=hover_text,
                    hoverinfo="text",
                )
            )

        # Add annual event markers
        if annual_events:
            for evt in annual_events:
                fig.add_vline(
                    x=evt.get("date"),
                    line_dash="dash",
                    line_color="#7FDBFF",
                    line_width=2,
                    annotation_text=evt.get("description", evt.get("event_type", "")),
                    annotation_position="top",
                    annotation_font={"size": 9, "color": "#0074D9"},
                )

        fig.update_layout(
            title={
                "text": title,
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": "Arial, sans-serif"},
            },
            xaxis_title="Date",
            yaxis_title="Filing Type",
            hovermode="closest",
            showlegend=True,
            legend={
                "title": "Compliance Status",
                "orientation": "v",
                "yanchor": "top",
                "y": 1,
                "x": 1.02,
            },
            template="plotly_white",
            height=600,
            width=1200,
        )

        self.logger.info("Filing deadline chart generation complete")
        return fig

    def generate_compliance_summary(
        self,
        filings: List[Dict[str, Any]],
        title: str = "Filing Compliance Summary",
    ):
        """
        Generate a compliance summary bar chart.

        Args:
            filings: List of filings (same format as generate_deadline_chart)
            title: Chart title

        Returns:
            Plotly figure with stacked bar chart of compliance by filing type,
            or None if plotly is not installed
        """
        if not HAS_PLOTLY:
            self.logger.warning("plotly is not installed -- skipping compliance summary generation")
            return None

        if not filings:
            return self._empty_figure(title)

        filings_enriched = self._enrich_filings(filings)

        # Count statuses by filing type
        from collections import Counter

        type_status_counts: Dict[str, Counter] = {}
        for f in filings_enriched:
            ftype = f["filing_type"]
            status = f.get("status", "UNKNOWN")
            type_status_counts.setdefault(ftype, Counter())[status] += 1

        filing_types = sorted(type_status_counts.keys())
        fig = go.Figure()

        for status in ["ON_TIME", "LATE", "AMENDED", "UNKNOWN"]:
            counts = [type_status_counts[ft].get(status, 0) for ft in filing_types]
            if sum(counts) == 0:
                continue
            fig.add_trace(
                go.Bar(
                    name=status.replace("_", " ").title(),
                    x=filing_types,
                    y=counts,
                    marker_color=self.STATUS_COLORS.get(status, "#888"),
                )
            )

        fig.update_layout(
            title={
                "text": title,
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": "Arial, sans-serif"},
            },
            barmode="stack",
            xaxis_title="Filing Type",
            yaxis_title="Count",
            template="plotly_white",
            height=500,
            width=900,
        )

        return fig

    def _enrich_filings(self, filings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich filings with computed deadline and status info."""
        enriched = []
        for f in filings:
            enriched_f = dict(f)

            # Compute deadline if not provided
            if "deadline_date" not in enriched_f and "trigger_date" in enriched_f:
                trigger = enriched_f["trigger_date"]
                ftype = enriched_f.get("filing_type", "")
                days = FILING_DEADLINES.get(ftype, 30)
                if isinstance(trigger, str):
                    trigger = datetime.strptime(trigger, "%Y-%m-%d").date()
                enriched_f["deadline_date"] = trigger + timedelta(days=days)

            # Compute status if not provided
            if "status" not in enriched_f:
                filing_date = enriched_f.get("filing_date")
                deadline_date = enriched_f.get("deadline_date")
                if filing_date and deadline_date:
                    if isinstance(filing_date, str):
                        filing_date = datetime.strptime(filing_date, "%Y-%m-%d").date()
                    if isinstance(deadline_date, str):
                        deadline_date = datetime.strptime(deadline_date, "%Y-%m-%d").date()
                    diff = (deadline_date - filing_date).days
                    enriched_f["days_margin"] = diff
                    enriched_f["status"] = "ON_TIME" if diff >= 0 else "LATE"
                else:
                    enriched_f["status"] = "UNKNOWN"
                    enriched_f["days_margin"] = 0

            enriched.append(enriched_f)
        return enriched

    def _empty_figure(self, title: str):
        """Return an empty figure with a message, or None if plotly is unavailable."""
        if not HAS_PLOTLY:
            return None
        fig = go.Figure()
        fig.add_annotation(
            text="No filing data available", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font={"size": 20},
        )
        fig.update_layout(title=title, template="plotly_white", height=400, width=800)
        return fig

    def save_chart(
        self, fig, output_path: Path, format: str = "html",
    ):
        """Save chart figure to file. Returns None if plotly is unavailable."""
        if not HAS_PLOTLY or fig is None:
            self.logger.warning("plotly is not installed or figure is None -- cannot save chart")
            return None

        if format == "html":
            fig.write_html(str(output_path))
        elif format == "png":
            fig.write_image(str(output_path))
        elif format == "svg":
            fig.write_image(str(output_path), format="svg")
        else:
            raise ValueError(f"Unsupported format: {format}")

        self.logger.info(f"Filing deadline chart saved to {output_path}")
        return output_path
