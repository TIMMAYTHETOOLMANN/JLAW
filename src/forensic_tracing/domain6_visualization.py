"""
Domain 6: Courtroom-Grade Visualization Specifications
========================================================

Specifications for charts that survive courtroom scrutiny, including:
  - Okabe-Ito colorblind-safe palette (WCAG AA compliant)
  - ReportLab Platypus layout architecture (no text/image overlap)
  - Standard sizing for letter paper with 1-inch margins
  - FRE 902(13)/(14) compliant evidence labeling
  - Data source attribution on every chart

Chart container: single-cell ReportLab Table with full border control
  - 468pt wide x 288pt tall (6.5" x 4") for full-width charts
  - 0.75pt borders in dark gray (#333333)
  - 12pt internal padding, 18pt external spacing

Key anti-overlap flowables:
  - KeepTogether: chart title + chart drawing + source note on same page
  - CondPageBreak: trigger page break if insufficient vertical space
  - Spacer: explicit vertical gaps between chart containers

References:
  - Okabe & Ito (2008) Color Universal Design palette
  - WCAG 2.1 AA: 4.5:1 contrast minimum for text, 3:1 for graphics
  - ISO 19005 (PDF/A archival compliance)
  - FRE 902(13), 902(14) (self-authentication for electronic evidence)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ============================================================================
# OKABE-ITO COLORBLIND-SAFE PALETTE
# ============================================================================
# These colors provide distinct luminance values that remain distinguishable
# in grayscale. Meets WCAG AA (4.5:1 contrast minimum for normal text,
# 3:1 for graphics). Recommended by Nature Methods for scientific publication.
# ============================================================================

OKABE_ITO_PALETTE = {
    'primary': '#0072B2',        # Blue — primary data series
    'highlight': '#E69F00',      # Orange — highlighted comparison
    'positive': '#009E73',       # Bluish green — positive/gains
    'alert': '#D55E00',          # Vermillion — alert/losses
    'secondary': '#56B4E9',      # Sky blue — secondary series
    'tertiary': '#CC79A7',       # Reddish purple — tertiary category
    'baseline': '#999999',       # Gray — baselines/gridlines
    'black': '#000000',          # Black — text, axes
}

# Severity color mapping using Okabe-Ito-derived values
SEVERITY_COLORS = {
    'critical': '#D55E00',       # Vermillion (alert)
    'high': '#E69F00',           # Orange (highlight)
    'medium': '#F0E442',         # Yellow
    'low': '#009E73',            # Bluish green (positive)
}


@dataclass
class ChartSpec:
    """Specification for a single courtroom-grade chart."""
    chart_id: str
    title: str  # Format: "Figure [N]: [Descriptive Title]"
    chart_type: str  # bar, line, scatter, network, treemap, timeline
    width_pt: float = 468  # 6.5 inches at 72 dpi
    height_pt: float = 288  # 4 inches at 72 dpi
    border_width_pt: float = 0.75
    border_color: str = '#333333'
    internal_padding_pt: float = 12
    external_spacing_pt: float = 18

    # Typography
    title_font: str = 'Times-Bold'
    title_size_pt: float = 12
    axis_label_font: str = 'Helvetica'
    axis_label_size_pt: float = 9
    data_label_font: str = 'Helvetica'
    data_label_size_pt: float = 8

    # Data source attribution (required on every chart)
    source_text: str = ''  # e.g., "Source: NIKE Form 4 filings, FY2019"
    source_font: str = 'Helvetica-Oblique'
    source_size_pt: float = 8

    # Color palette
    colors: Dict[str, str] = field(default_factory=lambda: dict(OKABE_ITO_PALETTE))

    # Y-axis configuration
    y_axis_label: str = ''
    y_axis_format: str = ''  # e.g., '$XXM', '$XXK', '%'

    # Render settings
    dpi: int = 300
    font_type: int = 42  # TrueType for editability
    transparent_bg: bool = False
    remove_top_spine: bool = True
    remove_right_spine: bool = True

    def to_dict(self) -> dict:
        return {
            'chart_id': self.chart_id,
            'title': self.title,
            'chart_type': self.chart_type,
            'dimensions': f'{self.width_pt}pt x {self.height_pt}pt',
            'source_text': self.source_text,
            'y_axis_label': self.y_axis_label,
            'y_axis_format': self.y_axis_format,
            'dpi': self.dpi,
        }


class CourtroomVisualizationSpec:
    """
    Complete visualization specifications for the forensic dossier PDF.

    Replaces the current charts that have deficiencies:
      - DEF-008: Transaction timeline Y-axis flat at 1.0
      - DEF-011: Beneficiary chart shows $0 profit
      - DEF-018: Network graph has no edge weights
      - DEF-019: Pie chart shows "100% Insider" (useless)
    """

    @classmethod
    def get_all_chart_specs(cls) -> List[ChartSpec]:
        """Return specifications for all charts in the enhanced dossier."""
        return [
            cls.transaction_timeline_spec(),
            cls.beneficiary_economic_spec(),
            cls.filing_party_network_spec(),
            cls.role_distribution_spec(),
            cls.temporal_cluster_spec(),
            cls.penalty_breakdown_spec(),
        ]

    @classmethod
    def transaction_timeline_spec(cls) -> ChartSpec:
        """
        DEF-008 fix: Transaction timeline with ECONOMIC_BENEFIT on Y-axis.
        Replaces the flat Y-axis at 1.0 with actual dollar valuations.
        """
        return ChartSpec(
            chart_id='CHART-001',
            title='Figure 1: Insider Transaction Timeline by Economic Value',
            chart_type='scatter',
            y_axis_label='Transaction Value ($)',
            y_axis_format='$XXM',
            source_text='Source: NIKE Form 4 filings, FY2019. Values computed from NKE closing prices.',
        )

    @classmethod
    def beneficiary_economic_spec(cls) -> ChartSpec:
        """
        DEF-011 fix: Beneficiary analysis with TOTAL_ECONOMIC_BENEFIT.
        Replaces the $0 profit table with actual dollar-value bars.
        """
        return ChartSpec(
            chart_id='CHART-002',
            title='Figure 2: Top Beneficiaries by Economic Value',
            chart_type='bar',
            y_axis_label='Economic Benefit ($)',
            y_axis_format='$XXM',
            source_text='Source: NIKE Form 4 filings, FY2019. Stacked by: option spread | grant FMV | gift | transfer.',
        )

    @classmethod
    def filing_party_network_spec(cls) -> ChartSpec:
        """
        DEF-018 fix: Network graph with edge weights and relationship labels.
        """
        return ChartSpec(
            chart_id='CHART-003',
            title='Figure 3: Filing Party Relationship Network',
            chart_type='network',
            source_text='Source: NIKE Form 4 filings, FY2019. Edge weights = shared transaction count.',
        )

    @classmethod
    def role_distribution_spec(cls) -> ChartSpec:
        """
        DEF-019 fix: Treemap replacing useless 100% pie chart.
        Each insider as proportional rectangle by economic benefit.
        """
        return ChartSpec(
            chart_id='CHART-004',
            title='Figure 4: Economic Benefit Distribution by Insider',
            chart_type='treemap',
            source_text='Source: NIKE Form 4 filings, FY2019. Area proportional to total economic benefit.',
        )

    @classmethod
    def temporal_cluster_spec(cls) -> ChartSpec:
        """New chart: Transaction cluster analysis."""
        return ChartSpec(
            chart_id='CHART-005',
            title='Figure 5: Transaction Cluster Analysis',
            chart_type='timeline',
            y_axis_label='Cluster Size (insiders)',
            source_text='Source: NIKE Form 4 filings, FY2019. Clusters = 3+ transactions within 3 business days.',
        )

    @classmethod
    def penalty_breakdown_spec(cls) -> ChartSpec:
        """New chart: Comprehensive penalty exposure breakdown."""
        return ChartSpec(
            chart_id='CHART-006',
            title='Figure 6: Estimated Penalty Exposure Breakdown',
            chart_type='bar',
            y_axis_label='Penalty Amount ($)',
            y_axis_format='$XXB',
            source_text='Source: Statutory penalty calculations. Civil + criminal + disgorgement + treble damages.',
        )

    @classmethod
    def get_reportlab_container_style(cls) -> dict:
        """
        ReportLab TableStyle for chart containers.

        Prevents text/image overlap by wrapping each chart in a
        single-cell Table with explicit padding and borders.
        """
        return {
            'box_border': ('BOX', (0, 0), (-1, -1), 0.75, '#333333'),
            'top_padding': ('TOPPADDING', (0, 0), (-1, -1), 12),
            'bottom_padding': ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            'left_padding': ('LEFTPADDING', (0, 0), (-1, -1), 12),
            'right_padding': ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            'alignment': ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        }

    @classmethod
    def get_matplotlib_config(cls) -> dict:
        """
        Matplotlib rcParams for courtroom-grade output.

        All charts use these settings for consistency and
        PDF/A archival compliance.
        """
        return {
            'figure.dpi': 300,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'pdf.fonttype': 42,          # TrueType fonts for editability
            'ps.fonttype': 42,
            'font.family': 'sans-serif',
            'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
            'axes.spines.top': False,    # Remove top spine
            'axes.spines.right': False,  # Remove right spine
            'axes.labelsize': 9,
            'axes.titlesize': 12,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
            'legend.fontsize': 8,
            'figure.figsize': (6.5, 4.0),
        }

    @classmethod
    def get_cover_page_spec(cls) -> dict:
        """
        Cover page field specifications fixing DEF-002 severity counts.
        All values must come from unified severity aggregation.
        """
        return {
            'total_violations': 'FROM severity_summary.total',
            'critical_alerts': 'FROM severity_summary.critical',
            'high_alerts': 'FROM severity_summary.high',
            'max_civil_exposure': 'FROM penalty_exposure.civil_penalty_range.maximum',
            'disgorgement': 'FROM penalty_exposure.estimated_disgorgement.amount',
            'total_economic_value': 'FROM economic_valuations.total_aggregate_benefit',
            'whistleblower_bounty_range': (
                'FROM penalty_exposure.whistleblower_bounty.bounty_floor '
                'TO penalty_exposure.whistleblower_bounty.bounty_ceiling'
            ),
        }

    @classmethod
    def get_new_sections(cls) -> List[dict]:
        """Specifications for new PDF sections to add."""
        return [
            {
                'title': 'PROSECUTORIAL PATTERN ANALYSIS',
                'content_source': 'executive_summary.executive_summary',
                'position': 'After Executive Summary, before Key Metrics',
            },
            {
                'title': 'TRANSACTION CLUSTER ANALYSIS',
                'content_source': 'temporal_analysis.transaction_clusters',
                'position': 'After Transaction Timeline',
            },
            {
                'title': 'ECONOMIC BENEFIT VALUATION METHODOLOGY',
                'content_source': 'Explain how $0 transactions were valued with formulas',
                'position': 'Before Evidence Chain',
            },
            {
                'title': 'WHISTLEBLOWER BOUNTY ESTIMATION',
                'content_source': 'penalty_exposure.whistleblower_bounty',
                'position': 'After Estimated Penalties',
            },
        ]
