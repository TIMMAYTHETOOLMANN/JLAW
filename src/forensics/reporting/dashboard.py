"""
Interactive Dashboard Generator
================================

Generates web-based interactive dashboards for forensic investigations.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class DashboardWidget:
    """A dashboard widget configuration."""
    widget_id: str
    widget_type: str  # chart, table, metric, timeline
    title: str
    data: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=dict)  # row, col, width, height


@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    title: str
    theme: str = "light"
    refresh_interval: int = 0  # 0 = no auto-refresh
    layout: str = "grid"  # grid, flow
    columns: int = 12


@dataclass
class Dashboard:
    """Complete dashboard definition."""
    dashboard_id: str
    case_id: str
    config: DashboardConfig
    widgets: List[DashboardWidget] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class InteractiveDashboard:
    """
    Interactive Dashboard Generator
    
    Creates web-based dashboards for forensic investigation visualization.
    
    Features:
    - Multiple widget types
    - Responsive layout
    - Interactive charts
    - Real-time updates
    
    Example:
        dashboard = InteractiveDashboard()
        
        # Create dashboard
        db = dashboard.create_dashboard("CASE-001", "Investigation Overview")
        
        # Add widgets
        dashboard.add_metric_widget(db.dashboard_id, "Total Findings", 42)
        dashboard.add_chart_widget(db.dashboard_id, "Violations by Type", {...})
        
        # Generate HTML
        html = dashboard.generate_html(db.dashboard_id)
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the dashboard generator."""
        self.output_dir = output_dir or Path("./dashboards")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._dashboards: Dict[str, Dashboard] = {}
        self._widget_counter = 0
        
        logger.info("InteractiveDashboard initialized")
    
    def create_dashboard(
        self,
        case_id: str,
        title: str,
        config: Optional[DashboardConfig] = None
    ) -> Dashboard:
        """
        Create a new dashboard.
        
        Args:
            case_id: Case identifier
            title: Dashboard title
            config: Dashboard configuration
            
        Returns:
            Created dashboard
        """
        dashboard_id = f"DASH-{case_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        dashboard = Dashboard(
            dashboard_id=dashboard_id,
            case_id=case_id,
            config=config or DashboardConfig(title=title)
        )
        
        self._dashboards[dashboard_id] = dashboard
        
        logger.info(f"Created dashboard: {dashboard_id}")
        return dashboard
    
    def _next_widget_id(self) -> str:
        """Generate next widget ID."""
        self._widget_counter += 1
        return f"widget-{self._widget_counter:04d}"
    
    def add_metric_widget(
        self,
        dashboard_id: str,
        title: str,
        value: Any,
        subtitle: str = "",
        trend: Optional[float] = None,
        position: Optional[Dict[str, int]] = None
    ) -> Optional[DashboardWidget]:
        """Add a metric widget to the dashboard."""
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return None
        
        widget = DashboardWidget(
            widget_id=self._next_widget_id(),
            widget_type="metric",
            title=title,
            data={
                "value": value,
                "subtitle": subtitle,
                "trend": trend
            },
            position=position or {"row": 0, "col": 0, "width": 3, "height": 1}
        )
        
        dashboard.widgets.append(widget)
        dashboard.updated_at = datetime.now()
        
        return widget
    
    def add_chart_widget(
        self,
        dashboard_id: str,
        title: str,
        chart_type: str,  # bar, line, pie, scatter
        data: Dict[str, Any],
        position: Optional[Dict[str, int]] = None
    ) -> Optional[DashboardWidget]:
        """Add a chart widget to the dashboard."""
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return None
        
        widget = DashboardWidget(
            widget_id=self._next_widget_id(),
            widget_type="chart",
            title=title,
            data=data,
            config={"chart_type": chart_type},
            position=position or {"row": 0, "col": 0, "width": 6, "height": 2}
        )
        
        dashboard.widgets.append(widget)
        dashboard.updated_at = datetime.now()
        
        return widget
    
    def add_table_widget(
        self,
        dashboard_id: str,
        title: str,
        columns: List[str],
        rows: List[List[Any]],
        position: Optional[Dict[str, int]] = None
    ) -> Optional[DashboardWidget]:
        """Add a table widget to the dashboard."""
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return None
        
        widget = DashboardWidget(
            widget_id=self._next_widget_id(),
            widget_type="table",
            title=title,
            data={"columns": columns, "rows": rows},
            position=position or {"row": 0, "col": 0, "width": 12, "height": 3}
        )
        
        dashboard.widgets.append(widget)
        dashboard.updated_at = datetime.now()
        
        return widget
    
    def add_timeline_widget(
        self,
        dashboard_id: str,
        title: str,
        events: List[Dict[str, Any]],
        position: Optional[Dict[str, int]] = None
    ) -> Optional[DashboardWidget]:
        """Add a timeline widget to the dashboard."""
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return None
        
        widget = DashboardWidget(
            widget_id=self._next_widget_id(),
            widget_type="timeline",
            title=title,
            data={"events": events},
            position=position or {"row": 0, "col": 0, "width": 12, "height": 2}
        )
        
        dashboard.widgets.append(widget)
        dashboard.updated_at = datetime.now()
        
        return widget
    
    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get a dashboard by ID."""
        return self._dashboards.get(dashboard_id)
    
    def generate_html(self, dashboard_id: str) -> str:
        """
        Generate HTML for the dashboard.
        
        Args:
            dashboard_id: Dashboard identifier
            
        Returns:
            HTML string
        """
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return ""
        
        html = self._generate_html_template(dashboard)
        return html
    
    def _generate_html_template(self, dashboard: Dashboard) -> str:
        """Generate HTML template for dashboard."""
        widgets_html = self._generate_widgets_html(dashboard.widgets)
        widgets_json = json.dumps([
            {
                "id": w.widget_id,
                "type": w.widget_type,
                "title": w.title,
                "data": w.data,
                "config": w.config
            }
            for w in dashboard.widgets
        ])
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dashboard.config.title}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }}
        .dashboard {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1a1a2e; color: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .meta {{ font-size: 14px; opacity: 0.8; }}
        .widgets {{ display: grid; grid-template-columns: repeat(12, 1fr); gap: 16px; }}
        .widget {{ background: white; border-radius: 8px; padding: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .widget-header {{ font-size: 14px; font-weight: 600; color: #333; margin-bottom: 12px; }}
        .metric {{ }}
        .metric .value {{ font-size: 36px; font-weight: 700; color: #1a1a2e; }}
        .metric .subtitle {{ font-size: 12px; color: #666; margin-top: 4px; }}
        .metric .trend {{ font-size: 14px; margin-top: 8px; }}
        .trend.positive {{ color: #10b981; }}
        .trend.negative {{ color: #ef4444; }}
        .table-widget table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        .table-widget th {{ text-align: left; padding: 10px; background: #f8f9fa; border-bottom: 2px solid #e5e7eb; }}
        .table-widget td {{ padding: 10px; border-bottom: 1px solid #e5e7eb; }}
        .timeline {{ position: relative; padding-left: 30px; }}
        .timeline-event {{ position: relative; padding-bottom: 16px; }}
        .timeline-event::before {{ content: ''; position: absolute; left: -24px; top: 4px; width: 12px; height: 12px; background: #3b82f6; border-radius: 50%; }}
        .timeline-event::after {{ content: ''; position: absolute; left: -19px; top: 16px; width: 2px; height: calc(100% - 8px); background: #e5e7eb; }}
        .timeline-event:last-child::after {{ display: none; }}
        .timeline-date {{ font-size: 12px; color: #666; }}
        .timeline-title {{ font-weight: 600; margin-top: 4px; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>{dashboard.config.title}</h1>
            <div class="meta">Case: {dashboard.case_id} | Generated: {dashboard.created_at.strftime("%Y-%m-%d %H:%M")}</div>
        </div>
        <div class="widgets">
            {widgets_html}
        </div>
    </div>
    <script>
        const widgets = {widgets_json};
        widgets.forEach(w => {{
            if (w.type === 'chart') {{
                const el = document.getElementById(w.id + '-chart');
                if (el && w.data.labels && w.data.values) {{
                    const trace = {{
                        x: w.data.labels,
                        y: w.data.values,
                        type: w.config.chart_type || 'bar'
                    }};
                    Plotly.newPlot(el, [trace], {{margin: {{t: 20, r: 20, b: 40, l: 40}}}});
                }}
            }}
        }});
    </script>
</body>
</html>'''
    
    def _generate_widgets_html(self, widgets: List[DashboardWidget]) -> str:
        """Generate HTML for all widgets."""
        html_parts = []
        
        for widget in widgets:
            pos = widget.position
            style = f"grid-column: span {pos.get('width', 3)}; grid-row: span {pos.get('height', 1)};"
            
            if widget.widget_type == "metric":
                value = widget.data.get("value", 0)
                subtitle = widget.data.get("subtitle", "")
                trend = widget.data.get("trend")
                trend_html = ""
                if trend is not None:
                    trend_class = "positive" if trend >= 0 else "negative"
                    trend_symbol = "↑" if trend >= 0 else "↓"
                    trend_html = f'<div class="trend {trend_class}">{trend_symbol} {abs(trend)}%</div>'
                
                html_parts.append(f'''
                <div class="widget metric" style="{style}">
                    <div class="widget-header">{widget.title}</div>
                    <div class="value">{value}</div>
                    <div class="subtitle">{subtitle}</div>
                    {trend_html}
                </div>''')
            
            elif widget.widget_type == "chart":
                html_parts.append(f'''
                <div class="widget chart-widget" style="{style}">
                    <div class="widget-header">{widget.title}</div>
                    <div id="{widget.widget_id}-chart" style="width:100%;height:200px;"></div>
                </div>''')
            
            elif widget.widget_type == "table":
                columns = widget.data.get("columns", [])
                rows = widget.data.get("rows", [])
                
                header_html = "".join(f"<th>{col}</th>" for col in columns)
                rows_html = ""
                for row in rows[:20]:  # Limit to 20 rows
                    cells = "".join(f"<td>{cell}</td>" for cell in row)
                    rows_html += f"<tr>{cells}</tr>"
                
                html_parts.append(f'''
                <div class="widget table-widget" style="{style}">
                    <div class="widget-header">{widget.title}</div>
                    <table>
                        <thead><tr>{header_html}</tr></thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                </div>''')
            
            elif widget.widget_type == "timeline":
                events = widget.data.get("events", [])
                events_html = ""
                for event in events[:10]:  # Limit to 10 events
                    date = event.get("date", "")
                    title = event.get("title", "")
                    events_html += f'''
                    <div class="timeline-event">
                        <div class="timeline-date">{date}</div>
                        <div class="timeline-title">{title}</div>
                    </div>'''
                
                html_parts.append(f'''
                <div class="widget" style="{style}">
                    <div class="widget-header">{widget.title}</div>
                    <div class="timeline">{events_html}</div>
                </div>''')
        
        return "\n".join(html_parts)
    
    def save_dashboard(self, dashboard_id: str, filename: Optional[str] = None) -> Optional[Path]:
        """Save dashboard to HTML file."""
        html = self.generate_html(dashboard_id)
        if not html:
            return None
        
        dashboard = self._dashboards[dashboard_id]
        filename = filename or f"dashboard_{dashboard.case_id}.html"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            f.write(html)
        
        logger.info(f"Saved dashboard to: {output_path}")
        return output_path
