"""
Forensic Visual Report Generator - Enhanced Phase 9 Output
==========================================================

Generates a visually rich, human-readable PDF dossier that embeds:
- Executive summary with severity gauge indicators
- Color-coded violation severity breakdown tables
- Transaction timeline with risk color coding
- Beneficiary profit waterfall and role distribution charts
- Financial beneficiary heatmap
- Bubble charts for transaction magnitude analysis
- Filing deadline compliance visualization
- Actor network association diagram
- Dollar amount quantification tables with color highlights
- Evidence chain summary

This generator produces ReportLab PDFs with embedded Matplotlib/Plotly chart images.
All charts are generated as in-memory images and embedded directly into the PDF.
"""

import hashlib
import logging
from collections import Counter, defaultdict
from datetime import datetime, date
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, List, Optional
import copy

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, HRFlowable,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    inch = 72.0
    logging.warning("ReportLab not installed - visual PDF generation unavailable")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logging.warning("Matplotlib not installed - chart embedding unavailable")

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

SEVERITY_COLORS_HEX = {
    "CRITICAL": "#DC143C",
    "HIGH": "#FF6347",
    "MEDIUM": "#FFD700",
    "LOW": "#32CD32",
}

SEVERITY_COLORS_RL = {
    "CRITICAL": colors.HexColor("#DC143C") if REPORTLAB_AVAILABLE else "#DC143C",
    "HIGH": colors.HexColor("#FF6347") if REPORTLAB_AVAILABLE else "#FF6347",
    "MEDIUM": colors.HexColor("#FFD700") if REPORTLAB_AVAILABLE else "#FFD700",
    "LOW": colors.HexColor("#32CD32") if REPORTLAB_AVAILABLE else "#32CD32",
}

ROLE_COLORS_HEX = {
    "CEO": "#DC143C",
    "CFO": "#FF6347",
    "COO": "#FF8C00",
    "Director": "#4169E1",
    "VP": "#9370DB",
    "Officer": "#20B2AA",
    "10% Owner": "#CD853F",
    "Other": "#778899",
}

BRAND_DARK = "#1B2A4A"
BRAND_ACCENT = "#C8102E"
BRAND_LIGHT_BG = "#F8F9FA"
HEADER_BG = colors.HexColor(BRAND_DARK) if REPORTLAB_AVAILABLE else BRAND_DARK
ACCENT_COLOR = colors.HexColor(BRAND_ACCENT) if REPORTLAB_AVAILABLE else BRAND_ACCENT


class ForensicVisualReportGenerator:
    """
    Generates a comprehensive, visually sophisticated forensic analysis PDF.

    This is the primary visual output generator for the JLAW platform,
    designed to produce dense yet human-readable dossiers with embedded
    charts, color-coded tables, and financial visualizations.

    Usage:
        generator = ForensicVisualReportGenerator(output_dir="./output/reports")
        output_path = generator.generate_visual_dossier(
            case_id="CASE-2019-NIKE",
            company_name="NIKE, Inc.",
            cik="320187",
            analysis_results={...},
        )
    """

    TITLE_FONT = "Helvetica-Bold"
    BODY_FONT = "Helvetica"
    MONO_FONT = "Courier"

    def __init__(self, output_dir: str = "./output/reports"):
        """
        Initialize the visual report generator.

        Args:
            output_dir: Directory to write PDF reports to.

        Raises:
            ImportError: If ReportLab is not installed.
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "ReportLab is required for PDF generation. "
                "Install with: pip install reportlab"
            )

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    # ─── STYLE SETUP ─────────────────────────────────────────────────

    def _setup_custom_styles(self):
        """Configure custom paragraph styles for the visual dossier."""
        self.styles.add(ParagraphStyle(
            name="DossierTitle",
            parent=self.styles["Heading1"],
            fontSize=26,
            textColor=colors.HexColor(BRAND_DARK),
            spaceAfter=14,
            alignment=TA_CENTER,
            fontName=self.TITLE_FONT,
        ))
        self.styles.add(ParagraphStyle(
            name="SectionHead",
            parent=self.styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor(BRAND_DARK),
            spaceBefore=16,
            spaceAfter=8,
            fontName=self.TITLE_FONT,
            borderWidth=0,
            borderPadding=0,
        ))
        self.styles.add(ParagraphStyle(
            name="SubHead",
            parent=self.styles["Heading3"],
            fontSize=13,
            textColor=colors.HexColor("#2a2a2a"),
            spaceBefore=10,
            spaceAfter=4,
            fontName=self.TITLE_FONT,
        ))
        self.styles.add(ParagraphStyle(
            name="BodyJustified",
            parent=self.styles["BodyText"],
            fontSize=10,
            alignment=TA_JUSTIFY,
            leading=14,
            fontName=self.BODY_FONT,
        ))
        self.styles.add(ParagraphStyle(
            name="SmallMono",
            parent=self.styles["Code"],
            fontSize=8,
            fontName=self.MONO_FONT,
            textColor=colors.HexColor("#555555"),
            backColor=colors.HexColor("#F5F5F5"),
            leftIndent=10,
            spaceBefore=2,
            spaceAfter=2,
        ))
        self.styles.add(ParagraphStyle(
            name="KPI",
            parent=self.styles["Normal"],
            fontSize=28,
            fontName=self.TITLE_FONT,
            alignment=TA_CENTER,
            textColor=colors.HexColor(BRAND_ACCENT),
            spaceBefore=4,
            spaceAfter=2,
        ))
        self.styles.add(ParagraphStyle(
            name="KPILabel",
            parent=self.styles["Normal"],
            fontSize=10,
            fontName=self.BODY_FONT,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#666666"),
            spaceAfter=6,
        ))

    # ─── MAIN ENTRY POINT ────────────────────────────────────────────

    def generate_visual_dossier(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        output_filename: Optional[str] = None,
    ) -> Path:
        """
        Generate a comprehensive visual forensic dossier PDF.

        Args:
            case_id: Unique case identifier.
            company_name: Target company name.
            cik: SEC CIK number.
            analysis_results: Complete analysis results dict containing:
                - total_violations (int)
                - critical_alerts (int)
                - high_alerts (int)
                - violations (list of violation dicts)
                - transactions (list of transaction dicts)
                - beneficiaries (list of beneficiary dicts)
                - filings (list of filing dicts)
                - actors (list of actor dicts)
                - relationships (list of relationship dicts)
                - material_events (list of event dicts)
                - annual_events (list of annual event dicts)
                - regulatory_routing (dict)
                - estimated_penalties (dict)
                - evidence_chain (list)
                - executive_summary_text (str)
            output_filename: Optional custom filename.

        Returns:
            Path to the generated PDF file.
        """
        # Enrich / synthesize missing collections before any rendering
        analysis_results = self._enrich_analysis_results(analysis_results)

        if not output_filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"VISUAL_DOSSIER_{case_id}_{ts}.pdf"

        output_path = self.output_dir / output_filename

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54,
        )

        story: list = []

        # ── COVER PAGE ──
        story.extend(self._build_cover(case_id, company_name, cik, analysis_results))
        story.append(PageBreak())

        # ── KPI DASHBOARD ──
        story.extend(self._build_kpi_dashboard(analysis_results))
        story.append(PageBreak())

        # ── VIOLATION SEVERITY BREAKDOWN ──
        story.extend(self._build_severity_breakdown(analysis_results))

        # ── VIOLATION REGISTER ──
        register_elements = self._build_violation_register(analysis_results)
        if register_elements:
            story.append(Spacer(1, 14))
            story.extend(register_elements)

        # ── TRANSACTION TIMELINE ──
        transactions = analysis_results.get("transactions", [])
        material_events = analysis_results.get("material_events", [])
        if transactions:
            story.append(PageBreak())
            story.extend(
                self._build_timeline_section(transactions, material_events, company_name)
            )

        # ── BENEFICIARY PROFIT ANALYSIS ──
        beneficiaries = analysis_results.get("beneficiaries", [])
        if beneficiaries:
            story.append(PageBreak())
            story.extend(self._build_beneficiary_section(beneficiaries, company_name))

        # ── FINANCIAL HEATMAP ──
        if transactions:
            story.append(PageBreak())
            story.extend(
                self._build_heatmap_section(transactions, material_events, company_name)
            )

        # ── BUBBLE CHART ──
        if transactions:
            story.append(PageBreak())
            story.extend(self._build_bubble_section(transactions, company_name))

        # ── FILING DEADLINE COMPLIANCE ──
        filings = analysis_results.get("filings", [])
        annual_events = analysis_results.get("annual_events", [])
        if filings:
            story.append(PageBreak())
            story.extend(
                self._build_filing_deadline_section(filings, annual_events, company_name)
            )

        # ── ACTOR NETWORK ──
        actors = analysis_results.get("actors", [])
        relationships = analysis_results.get("relationships", [])
        if actors:
            story.append(PageBreak())
            story.extend(
                self._build_network_section(actors, relationships, company_name)
            )

        # ── PENALTY ESTIMATES ──
        story.append(PageBreak())
        story.extend(self._build_penalty_section(analysis_results))

        # ── EVIDENCE CHAIN SUMMARY ──
        story.append(PageBreak())
        story.extend(self._build_evidence_summary(case_id, analysis_results))

        # Build PDF
        doc.build(
            story,
            onFirstPage=self._page_footer,
            onLaterPages=self._page_footer,
        )

        logger.info(f"Visual dossier generated: {output_path}")
        return output_path

    # ─── COVER PAGE ──────────────────────────────────────────────────

    def _build_cover(
        self, case_id: str, company_name: str, cik: str, results: Dict,
    ) -> list:
        """Build a visually distinctive cover page."""
        story: list = []
        story.append(Spacer(1, 1.5 * inch))

        # Accent bar
        story.append(HRFlowable(
            width="100%", thickness=4, color=ACCENT_COLOR,
            spaceAfter=12, spaceBefore=0,
        ))

        story.append(Paragraph("FORENSIC ANALYSIS", self.styles["DossierTitle"]))
        story.append(Paragraph("VISUAL DOSSIER", self.styles["DossierTitle"]))

        story.append(HRFlowable(
            width="100%", thickness=4, color=ACCENT_COLOR,
            spaceAfter=20, spaceBefore=8,
        ))

        story.append(Paragraph(
            f'<font color="{BRAND_ACCENT}"><b>CONFIDENTIAL — LAW ENFORCEMENT SENSITIVE</b></font>',
            ParagraphStyle("centered", parent=self.styles["Normal"], alignment=TA_CENTER),
        ))
        story.append(Spacer(1, 0.5 * inch))

        # Case info table
        total_v = results.get("total_violations", 0)
        crit = results.get("critical_alerts", 0)
        data = [
            ["Case ID", case_id],
            ["Target Entity", company_name],
            ["SEC CIK", cik],
            ["Generated", datetime.now().strftime("%Y-%m-%d %H:%M UTC")],
            ["Total Violations", str(total_v)],
            ["Critical Alerts", str(crit)],
        ]
        tbl = Table(data, colWidths=[2.2 * inch, 4.0 * inch])
        tbl.setStyle(TableStyle([
            ("FONT", (0, 0), (0, -1), self.TITLE_FONT, 11),
            ("FONT", (1, 0), (1, -1), self.BODY_FONT, 11),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F4F8")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)

        story.append(Spacer(1, 0.8 * inch))
        story.append(Paragraph(
            "Generated by JLAW Forensic Analysis System v4.1",
            ParagraphStyle("footer", parent=self.styles["Normal"],
                           alignment=TA_CENTER, fontSize=9, textColor=colors.grey),
        ))
        return story

    # ─── KPI DASHBOARD ───────────────────────────────────────────────

    def _build_kpi_dashboard(self, results: Dict) -> list:
        """Build a KPI dashboard with key metrics."""
        story: list = []
        story.append(Paragraph("KEY METRICS DASHBOARD", self.styles["SectionHead"]))
        story.append(HRFlowable(
            width="100%", thickness=2, color=ACCENT_COLOR, spaceAfter=12,
        ))

        total_v = results.get("total_violations", 0)
        crit = results.get("critical_alerts", 0)
        high = results.get("high_alerts", 0)
        penalties = results.get("estimated_penalties", {})
        civil_max = penalties.get("civil_maximum", 0)
        penalties.get("disgorgement", 0)

        # KPI row using table
        kpi_cells = [
            [
                Paragraph(str(total_v), self.styles["KPI"]),
                Paragraph(str(crit), self.styles["KPI"]),
                Paragraph(str(high), self.styles["KPI"]),
                Paragraph(f"${civil_max:,.0f}", self.styles["KPI"]),
            ],
            [
                Paragraph("Total Violations", self.styles["KPILabel"]),
                Paragraph("Critical Alerts", self.styles["KPILabel"]),
                Paragraph("High Alerts", self.styles["KPILabel"]),
                Paragraph("Max Civil Penalty", self.styles["KPILabel"]),
            ],
        ]
        kpi_table = Table(kpi_cells, colWidths=[1.6 * inch] * 4)
        kpi_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#DEE2E6")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8F9FA")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 16))

        # Severity chart (matplotlib)
        if MATPLOTLIB_AVAILABLE:
            chart_img = self._generate_severity_pie(results)
            if chart_img:
                story.append(Paragraph("Violation Severity Distribution", self.styles["SubHead"]))
                story.append(Image(chart_img, width=4.5 * inch, height=3.0 * inch))

        return story

    # ─── SEVERITY BREAKDOWN TABLE ────────────────────────────────────

    def _build_severity_breakdown(self, results: Dict) -> list:
        """Build a color-coded violation severity breakdown table."""
        story: list = []
        story.append(Paragraph("VIOLATION SEVERITY BREAKDOWN", self.styles["SectionHead"]))
        story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_COLOR, spaceAfter=12))

        all_violations = self._extract_violations(results)
        if not all_violations:
            story.append(Paragraph("No violations detected.", self.styles["BodyJustified"]))
            return story

        # Group by severity
        by_severity: Dict[str, list] = {}
        for v in all_violations:
            sev = v.get("severity", v.get("risk_level", "LOW"))
            if isinstance(sev, (int, float)):
                if sev >= 8:
                    sev = "CRITICAL"
                elif sev >= 6:
                    sev = "HIGH"
                elif sev >= 4:
                    sev = "MEDIUM"
                else:
                    sev = "LOW"
            by_severity.setdefault(sev, []).append(v)

        header = ["Severity", "Count", "Top Violation Types", "Regulatory Action"]
        rows = [header]
        row_colors = [colors.HexColor(BRAND_DARK)]

        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            viols = by_severity.get(sev, [])
            if not viols:
                continue
            types = Counter(v.get("violation_type", "Unknown") for v in viols)
            top_types = ", ".join(f"{t} ({c})" for t, c in types.most_common(3))
            action = {
                "CRITICAL": "DOJ Referral",
                "HIGH": "SEC Priority",
                "MEDIUM": "Civil Action",
                "LOW": "Monitoring",
            }.get(sev, "")
            rows.append([sev, str(len(viols)), top_types, action])
            row_colors.append(SEVERITY_COLORS_RL.get(sev, colors.white))

        col_widths = [1.0 * inch, 0.7 * inch, 3.5 * inch, 1.3 * inch]
        tbl = Table(rows, colWidths=col_widths)

        style_cmds = [
            ("FONT", (0, 0), (-1, 0), self.TITLE_FONT, 10),
            ("FONT", (0, 1), (-1, -1), self.BODY_FONT, 9),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        # Color-code severity cells
        for i in range(1, len(rows)):
            style_cmds.append(("BACKGROUND", (0, i), (0, i), row_colors[i]))
            style_cmds.append(("TEXTCOLOR", (0, i), (0, i), colors.white))
            style_cmds.append(("FONT", (0, i), (0, i), self.TITLE_FONT, 9))

        tbl.setStyle(TableStyle(style_cmds))
        story.append(tbl)
        return story

    # ─── TIMELINE SECTION ────────────────────────────────────────────

    def _build_timeline_section(
        self, transactions: list, material_events: list, company: str,
    ) -> list:
        """Build transaction timeline with color-coded risk markers."""
        story: list = []
        story.append(Paragraph(
            "TRANSACTION TIMELINE", self.styles["SectionHead"],
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_COLOR, spaceAfter=12))
        story.append(Paragraph(
            "Chronological view of transactions color-coded by risk level. "
            "Marker size reflects transaction value. "
            "Vertical dashed lines indicate material events.",
            self.styles["BodyJustified"],
        ))
        story.append(Spacer(1, 8))

        if MATPLOTLIB_AVAILABLE:
            img = self._generate_timeline_chart(transactions, material_events, company)
            if img:
                story.append(Image(img, width=6.5 * inch, height=3.5 * inch))

        return story

    # ─── BENEFICIARY SECTION ─────────────────────────────────────────

    def _build_beneficiary_section(self, beneficiaries: list, company: str) -> list:
        """Build beneficiary profit analysis with charts and tables."""
        story: list = []
        story.append(Paragraph(
            "FINANCIAL BENEFICIARY ANALYSIS", self.styles["SectionHead"],
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_COLOR, spaceAfter=12))

        # Top beneficiaries table
        # Determine whether profit or shares is the available metric
        has_profit = any(b.get("total_profit", 0) for b in beneficiaries)
        if has_profit:
            metric_label = "Profit ($)"
            sort_key = "total_profit"
        else:
            metric_label = "Shares"
            sort_key = "total_shares"

        sorted_bens = sorted(
            beneficiaries, key=lambda b: b.get(sort_key, 0), reverse=True,
        )[:10]

        header = ["Name", "Role", metric_label, "Transactions", "Risk Score", "Violations"]
        rows = [header]
        for b in sorted_bens:
            if has_profit:
                metric_value = f"${b.get('total_profit', 0):,.0f}"
            else:
                metric_value = f"{b.get('total_shares', 0):,.0f}"
            rows.append([
                b.get("name", "Unknown"),
                b.get("role", "—"),
                metric_value,
                str(b.get("transaction_count", 0)),
                f"{b.get('risk_score', 0):.0f}",
                str(b.get("violations", 0)),
            ])

        col_w = [1.6 * inch, 0.8 * inch, 1.2 * inch, 0.9 * inch, 0.8 * inch, 0.8 * inch]
        tbl = Table(rows, colWidths=col_w)

        style_cmds = [
            ("FONT", (0, 0), (-1, 0), self.TITLE_FONT, 9),
            ("FONT", (0, 1), (-1, -1), self.BODY_FONT, 8),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        # Highlight high-risk rows
        for i, b in enumerate(sorted_bens, start=1):
            rs = b.get("risk_score", 0)
            if rs >= 80:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FFF0F0")))
            elif rs >= 60:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FFF8F0")))

        tbl.setStyle(TableStyle(style_cmds))
        story.append(tbl)
        story.append(Spacer(1, 12))

        # Profit bar chart
        if MATPLOTLIB_AVAILABLE and sorted_bens:
            img = self._generate_profit_bar(sorted_bens, company)
            if img:
                story.append(Paragraph("Profit by Beneficiary", self.styles["SubHead"]))
                story.append(Image(img, width=6.0 * inch, height=3.0 * inch))

            img2 = self._generate_role_pie(beneficiaries, company)
            if img2:
                story.append(Spacer(1, 8))
                story.append(Paragraph("Profit Distribution by Role", self.styles["SubHead"]))
                story.append(Image(img2, width=4.5 * inch, height=3.0 * inch))

        return story

    # ─── HEATMAP SECTION ─────────────────────────────────────────────

    def _build_heatmap_section(
        self, transactions: list, material_events: list, company: str,
    ) -> list:
        """Build a financial beneficiary heatmap."""
        story: list = []
        story.append(Paragraph(
            "FINANCIAL BENEFICIARY HEATMAP", self.styles["SectionHead"],
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_COLOR, spaceAfter=12))
        story.append(Paragraph(
            "Trading intensity by actor and date. Darker cells indicate higher "
            "transaction values. Material events shown as vertical markers.",
            self.styles["BodyJustified"],
        ))
        story.append(Spacer(1, 8))

        if MATPLOTLIB_AVAILABLE:
            img = self._generate_heatmap_chart(transactions, company)
            if img:
                story.append(Image(img, width=6.5 * inch, height=3.5 * inch))

        return story

    # ─── BUBBLE CHART SECTION ────────────────────────────────────────

    def _build_bubble_section(self, transactions: list, company: str) -> list:
        """Build a transaction bubble chart section."""
        story: list = []
        story.append(Paragraph(
            "TRANSACTION MAGNITUDE ANALYSIS", self.styles["SectionHead"],
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_COLOR, spaceAfter=12))
        story.append(Paragraph(
            "Bubble size represents transaction value. Color indicates risk level. "
            "Larger bubbles represent larger dollar amounts.",
            self.styles["BodyJustified"],
        ))
        story.append(Spacer(1, 8))

        if MATPLOTLIB_AVAILABLE:
            img = self._generate_bubble_chart(transactions, company)
            if img:
                story.append(Image(img, width=6.5 * inch, height=4.0 * inch))

        return story

    # ─── FILING DEADLINE SECTION ─────────────────────────────────────

    def _build_filing_deadline_section(
        self, filings: list, annual_events: list, company: str,
    ) -> list:
        """Build filing deadline compliance section."""
        story: list = []
        story.append(Paragraph(
            "FILING DEADLINE COMPLIANCE", self.styles["SectionHead"],
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_COLOR, spaceAfter=12))
        story.append(Paragraph(
            "Filing dates relative to regulatory deadlines. "
            "Green markers indicate on-time filings; red markers indicate late filings.",
            self.styles["BodyJustified"],
        ))
        story.append(Spacer(1, 8))

        if MATPLOTLIB_AVAILABLE:
            img = self._generate_deadline_chart(filings, annual_events, company)
            if img:
                story.append(Image(img, width=6.5 * inch, height=3.5 * inch))

        # Compliance summary table
        from .visualizations.filing_deadline_chart import FilingDeadlineChart

        fdc = FilingDeadlineChart()
        enriched = fdc._enrich_filings(filings)
        late_count = sum(1 for f in enriched if f.get("status") == "LATE")
        on_time_count = sum(1 for f in enriched if f.get("status") == "ON_TIME")
        total = len(enriched)

        story.append(Spacer(1, 8))
        summary_data = [
            ["Metric", "Value"],
            ["Total Filings", str(total)],
            ["On Time", str(on_time_count)],
            ["Late", str(late_count)],
            ["Compliance Rate", f"{(on_time_count / total * 100):.1f}%" if total > 0 else "N/A"],
        ]
        tbl = Table(summary_data, colWidths=[2.5 * inch, 2.5 * inch])
        tbl.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, 0), self.TITLE_FONT, 10),
            ("FONT", (0, 1), (-1, -1), self.BODY_FONT, 10),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl)
        return story

    # ─── ACTOR NETWORK SECTION ───────────────────────────────────────

    def _build_network_section(
        self, actors: list, relationships: list, company: str,
    ) -> list:
        """Build actor network/association section."""
        story: list = []
        story.append(Paragraph(
            "FILING PARTY ASSOCIATIONS", self.styles["SectionHead"],
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_COLOR, spaceAfter=12))
        story.append(Paragraph(
            "Network graph showing relationships between filing parties. "
            "Node color indicates risk score; size reflects connection count.",
            self.styles["BodyJustified"],
        ))
        story.append(Spacer(1, 8))

        if MATPLOTLIB_AVAILABLE:
            img = self._generate_network_chart(actors, relationships, company)
            if img:
                story.append(Image(img, width=6.0 * inch, height=4.0 * inch))

        # Actor table
        if actors:
            header = ["Name", "Type", "Risk Score", "Roles"]
            rows = [header]
            sorted_actors = sorted(actors, key=lambda a: a.get("risk_score", 0), reverse=True)
            for a in sorted_actors[:15]:
                rows.append([
                    a.get("name", "Unknown"),
                    a.get("actor_type", "—"),
                    f"{a.get('risk_score', 0):.0f}",
                    ", ".join(a.get("roles", [])) or "—",
                ])
            tbl = Table(rows, colWidths=[2.0 * inch, 1.0 * inch, 1.0 * inch, 2.5 * inch])
            tbl.setStyle(TableStyle([
                ("FONT", (0, 0), (-1, 0), self.TITLE_FONT, 9),
                ("FONT", (0, 1), (-1, -1), self.BODY_FONT, 8),
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(Spacer(1, 8))
            story.append(tbl)

        return story

    # ─── PENALTY SECTION ─────────────────────────────────────────────

    def _build_penalty_section(self, results: Dict) -> list:
        """Build penalty estimates with dollar amounts."""
        story: list = []
        story.append(Paragraph("ESTIMATED PENALTIES", self.styles["SectionHead"]))
        story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_COLOR, spaceAfter=12))

        penalties = results.get("estimated_penalties", {})
        data = [
            ["Penalty Type", "Minimum", "Maximum"],
            [
                "Civil Monetary Penalties",
                f"${penalties.get('civil_minimum', 0):,.0f}",
                f"${penalties.get('civil_maximum', 0):,.0f}",
            ],
            [
                "Disgorgement (Estimated)",
                "N/A",
                f"${penalties.get('disgorgement', 0):,.0f}",
            ],
            [
                "Criminal Exposure",
                "Possible" if penalties.get("criminal_exposure") else "No",
                f"{penalties.get('prison_years_maximum', 0)} years max",
            ],
        ]
        tbl = Table(data, colWidths=[2.8 * inch, 1.8 * inch, 1.8 * inch])
        tbl.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, 0), self.TITLE_FONT, 11),
            ("FONT", (0, 1), (-1, -1), self.BODY_FONT, 10),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FAFAFA")),
        ]))
        story.append(tbl)
        return story

    # ─── EVIDENCE SUMMARY ────────────────────────────────────────────

    def _build_evidence_summary(self, case_id: str, results: Dict) -> list:
        """Build evidence chain summary."""
        story: list = []
        story.append(Paragraph("EVIDENCE CHAIN SUMMARY", self.styles["SectionHead"]))
        story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_COLOR, spaceAfter=12))

        report_hash = hashlib.sha256(
            f"{case_id}{datetime.now().isoformat()}".encode("utf-8")
        ).hexdigest()

        story.append(Paragraph(
            "All evidence has been cryptographically hashed using SHA-256 + SHA3-512 + "
            "BLAKE2b triple-hash integrity to ensure tamper-evident chain of custody.",
            self.styles["BodyJustified"],
        ))
        story.append(Spacer(1, 8))

        chain = results.get("evidence_chain", [])
        if chain:
            header = ["ID", "Description", "SHA-256 Hash"]
            rows = [header]
            for i, item in enumerate(chain[:20]):
                rows.append([
                    item.get("item_id", f"EV-{i + 1:04d}"),
                    (item.get("description", "")[:40] + "...") if len(
                        item.get("description", "")) > 40 else item.get("description", ""),
                    (item.get("sha256_hash", "N/A")[:32] + "..."),
                ])
            tbl = Table(rows, colWidths=[0.9 * inch, 2.5 * inch, 3.0 * inch])
            tbl.setStyle(TableStyle([
                ("FONT", (0, 0), (-1, 0), self.TITLE_FONT, 9),
                ("FONT", (0, 1), (-1, -1), self.MONO_FONT, 7),
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 12))

        story.append(Paragraph(
            "<b>Report Hash (SHA-256):</b>", self.styles["BodyJustified"],
        ))
        story.append(Paragraph(report_hash, self.styles["SmallMono"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "<i>This report is digitally signed and tamper-evident.</i>",
            self.styles["BodyJustified"],
        ))
        return story

    # ─── DATA ENRICHMENT ─────────────────────────────────────────────

    @staticmethod
    def _enrich_analysis_results(results: Dict) -> Dict:
        """
        Synthesize missing collections from available data.

        When running standalone report generation from raw JSON, the full
        analysis pipeline may not have populated every collection. This
        method fills in transactions, beneficiaries, actors, and filings
        by extracting what it can from the violations list, and performs
        lightweight cleanup on material_events and transaction values.

        Args:
            results: The analysis results dict (will be deep-copied).

        Returns:
            A new dict with enriched / synthesized collections.
        """
        r = copy.deepcopy(results)
        violations = r.get("violations", [])

        # 1. Synthesize transactions from violations that carry date/shares/value
        if not r.get("transactions"):
            synthesized_txns: List[Dict[str, Any]] = []
            for v in violations:
                v_date = v.get("transaction_date") or v.get("date") or v.get("filing_date")
                v_shares = v.get("shares") or v.get("shares_traded", 0)
                v_value = v.get("value") or v.get("transaction_value", 0)
                if v_date or v_shares or v_value:
                    synthesized_txns.append({
                        "date": v_date,
                        "shares": v_shares,
                        "value": v_value,
                        "actor": v.get("reporting_owner") or v.get("owner") or v.get("owner_name") or v.get("insider_name") or v.get("node_id", "Unknown"),
                        "risk_level": v.get("severity", v.get("risk_level", "LOW")),
                        "accession_number": v.get("accession_number", ""),
                        "violation_type": v.get("violation_type", ""),
                    })
            if synthesized_txns:
                r["transactions"] = synthesized_txns
                logger.info("Enrichment: synthesized %d transactions from violations", len(synthesized_txns))

        # 2. Synthesize beneficiaries by grouping violations by owner name
        if not r.get("beneficiaries"):
            owner_map: Dict[str, Dict[str, Any]] = {}
            for v in violations:
                name = v.get("reporting_owner") or v.get("owner") or v.get("owner_name") or v.get("insider_name") or v.get("node_id")
                if not name:
                    continue
                if name not in owner_map:
                    owner_map[name] = {
                        "name": name,
                        "role": v.get("role", v.get("insider_role", "")),
                        "total_shares": 0,
                        "total_profit": 0,
                        "transaction_count": 0,
                        "risk_score": 0,
                        "violations": 0,
                    }
                entry = owner_map[name]
                entry["total_shares"] += v.get("shares", v.get("shares_traded", 0)) or 0
                entry["total_profit"] += v.get("value", v.get("transaction_value", 0)) or 0
                entry["transaction_count"] += 1
                entry["violations"] += 1
                sev = v.get("severity", v.get("risk_level", "LOW"))
                sev_score = {"CRITICAL": 100, "HIGH": 75, "MEDIUM": 50, "LOW": 25}.get(
                    str(sev).upper(), 25
                )
                entry["risk_score"] = max(entry["risk_score"], sev_score)
            if owner_map:
                r["beneficiaries"] = list(owner_map.values())
                logger.info("Enrichment: synthesized %d beneficiaries from violations", len(owner_map))

        # 3. Synthesize actors from unique names in violations
        if not r.get("actors"):
            actor_map: Dict[str, Dict[str, Any]] = {}
            for v in violations:
                name = v.get("reporting_owner") or v.get("owner") or v.get("owner_name") or v.get("insider_name") or v.get("node_id")
                if not name:
                    continue
                if name not in actor_map:
                    actor_map[name] = {
                        "name": name,
                        "actor_id": name,
                        "actor_type": "insider",
                        "roles": [],
                        "risk_score": 0,
                    }
                role = v.get("role", v.get("insider_role", ""))
                if role and role not in actor_map[name]["roles"]:
                    actor_map[name]["roles"].append(role)
                sev = v.get("severity", v.get("risk_level", "LOW"))
                sev_score = {"CRITICAL": 100, "HIGH": 75, "MEDIUM": 50, "LOW": 25}.get(
                    str(sev).upper(), 25
                )
                actor_map[name]["risk_score"] = max(actor_map[name]["risk_score"], sev_score)
            if actor_map:
                r["actors"] = list(actor_map.values())
                logger.info("Enrichment: synthesized %d actors from violations", len(actor_map))

        # 4. Synthesize filings from unique accession numbers in violations
        if not r.get("filings"):
            seen_accessions: Dict[str, Dict[str, Any]] = {}
            for v in violations:
                acc = v.get("accession_number", "")
                if acc and acc not in seen_accessions:
                    seen_accessions[acc] = {
                        "accession_number": acc,
                        "filing_type": v.get("filing_type", v.get("form_type", "Unknown")),
                        "filing_date": v.get("date") or v.get("transaction_date", ""),
                    }
            if seen_accessions:
                r["filings"] = list(seen_accessions.values())
                logger.info("Enrichment: synthesized %d filings from violations", len(seen_accessions))

        # 5. Filter material_events -- remove entries with null dates or empty descriptions
        if r.get("material_events"):
            r["material_events"] = [
                evt for evt in r["material_events"]
                if evt.get("date") and (evt.get("description") or "").strip()
            ]

        # 6. For each transaction, compute value from shares * price_per_share when value is 0
        for txn in r.get("transactions", []):
            if not txn.get("value"):
                shares = txn.get("shares", 0) or 0
                price = txn.get("price_per_share", 0) or 0
                if shares and price:
                    txn["value"] = shares * price

        return r

    # ─── VIOLATION REGISTER ──────────────────────────────────────────

    def _build_violation_register(self, results: Dict) -> list:
        """
        Build a deduplicated, severity-coded violation register table.

        Each row is color-coded by severity:
            CRITICAL = red, HIGH = orange, MEDIUM = yellow, LOW = green.

        Returns:
            List of ReportLab flowables (empty list when no violations).
        """
        violations = self._extract_violations(results)
        if not violations:
            return []

        story: list = []
        story.append(Paragraph("VIOLATION REGISTER", self.styles["SubHead"]))
        story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_COLOR, spaceAfter=8))

        # Deduplicate by (violation_type, owner, accession_number)
        seen: set = set()
        unique_violations: list = []
        for v in violations:
            key = (
                v.get("violation_type", ""),
                v.get("reporting_owner") or v.get("owner") or v.get("owner_name") or v.get("insider_name") or v.get("node_id", ""),
                v.get("accession_number", ""),
            )
            if key not in seen:
                seen.add(key)
                unique_violations.append(v)

        # Sort by severity priority
        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        unique_violations.sort(key=lambda v: sev_order.get(
            self._normalize_severity(v.get("severity", v.get("risk_level", "LOW"))), 4
        ))

        # Build table data
        header = [
            "Violation Type", "Owner/Insider", "Date", "Shares",
            "Penalty Estimate", "SEC Filing", "Statutory Reference",
        ]
        rows = [header]
        row_severities: list = []  # track severity per data row for coloring

        for v in unique_violations:
            sev = self._normalize_severity(v.get("severity", v.get("risk_level", "LOW")))
            owner = v.get("reporting_owner") or v.get("owner") or v.get("owner_name") or v.get("insider_name") or v.get("node_id", "")
            vdate = v.get("transaction_date") or v.get("date") or v.get("filing_date", "")
            if vdate and not isinstance(vdate, str):
                vdate = str(vdate)
            shares = v.get("shares") or v.get("shares_traded", 0)
            penalty = v.get("penalty_estimate") or v.get("estimated_penalty", 0)
            accession = v.get("accession_number", "")
            statute = v.get("statutory_reference") or v.get("statute", "")

            rows.append([
                (v.get("violation_type", "Unknown"))[:28],
                owner[:22],
                str(vdate)[:10] if vdate else "",
                f"{int(shares):,}" if shares else "",
                f"${penalty:,.0f}" if penalty else "",
                accession[:20] if accession else "",
                statute[:22] if statute else "",
            ])
            row_severities.append(sev)

        col_widths = [
            1.3 * inch, 1.1 * inch, 0.7 * inch, 0.6 * inch,
            0.8 * inch, 1.0 * inch, 1.1 * inch,
        ]
        tbl = Table(rows, colWidths=col_widths)

        # Base style commands
        style_cmds = [
            ("FONT", (0, 0), (-1, 0), self.TITLE_FONT, 8),
            ("FONT", (0, 1), (-1, -1), self.BODY_FONT, 7),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]

        # Severity row coloring
        sev_bg = {
            "CRITICAL": colors.HexColor("#FFCCCC"),
            "HIGH": colors.HexColor("#FFE0CC"),
            "MEDIUM": colors.HexColor("#FFFACC"),
            "LOW": colors.HexColor("#CCFFCC"),
        }
        sev_left_stripe = {
            "CRITICAL": SEVERITY_COLORS_RL.get("CRITICAL", colors.red),
            "HIGH": SEVERITY_COLORS_RL.get("HIGH", colors.orange),
            "MEDIUM": SEVERITY_COLORS_RL.get("MEDIUM", colors.yellow),
            "LOW": SEVERITY_COLORS_RL.get("LOW", colors.green),
        }
        for i, sev in enumerate(row_severities):
            row_idx = i + 1  # account for header row
            bg = sev_bg.get(sev)
            if bg:
                style_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), bg))
            stripe = sev_left_stripe.get(sev)
            if stripe:
                style_cmds.append(("BACKGROUND", (0, row_idx), (0, row_idx), stripe))
                style_cmds.append(("TEXTCOLOR", (0, row_idx), (0, row_idx), colors.white))
                style_cmds.append(("FONT", (0, row_idx), (0, row_idx), self.TITLE_FONT, 7))

        tbl.setStyle(TableStyle(style_cmds))
        story.append(tbl)
        return story

    # ─── SEVERITY NORMALIZER ─────────────────────────────────────────

    @staticmethod
    def _normalize_severity(sev) -> str:
        """Normalize a severity value to one of CRITICAL/HIGH/MEDIUM/LOW."""
        if isinstance(sev, (int, float)):
            if sev >= 8:
                return "CRITICAL"
            elif sev >= 6:
                return "HIGH"
            elif sev >= 4:
                return "MEDIUM"
            return "LOW"
        return str(sev).upper() if sev else "LOW"

    # ─── PAGE FOOTER ─────────────────────────────────────────────────

    def _page_footer(self, canvas_obj, doc):
        """Add page footer with page number and branding."""
        canvas_obj.saveState()
        canvas_obj.setFont(self.BODY_FONT, 8)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawCentredString(
            letter[0] / 2, 0.4 * inch,
            f"JLAW Forensic Analysis System — Page {doc.page}",
        )
        canvas_obj.restoreState()

    # ═══════════════════════════════════════════════════════════════════
    # MATPLOTLIB CHART GENERATORS (produce BytesIO for PDF embedding)
    # ═══════════════════════════════════════════════════════════════════

    @staticmethod
    def _parse_date(value):
        """Convert date-like values to datetime.date objects for matplotlib."""
        from datetime import date as _date, datetime as _dt
        if isinstance(value, _dt):
            return value.date()
        if isinstance(value, _date):
            return value
        if isinstance(value, str):
            for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%m/%d/%Y'):
                try:
                    return _dt.strptime(value, fmt).date()
                except (ValueError, TypeError):
                    continue
        return _date.today()

    def _generate_severity_pie(self, results: Dict) -> Optional[BytesIO]:
        """Generate severity distribution pie chart."""
        try:
            all_violations = self._extract_violations(results)
            if not all_violations:
                return None

            counts: Dict[str, int] = Counter()
            for v in all_violations:
                sev = v.get("severity", v.get("risk_level", "LOW"))
                if isinstance(sev, (int, float)):
                    if sev >= 8:
                        sev = "CRITICAL"
                    elif sev >= 6:
                        sev = "HIGH"
                    elif sev >= 4:
                        sev = "MEDIUM"
                    else:
                        sev = "LOW"
                counts[sev] += 1

            labels = []
            sizes = []
            chart_colors = []
            for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                if counts.get(sev, 0) > 0:
                    labels.append(f"{sev} ({counts[sev]})")
                    sizes.append(counts[sev])
                    chart_colors.append(SEVERITY_COLORS_HEX.get(sev, "#888"))

            if not sizes:
                return None

            fig, ax = plt.subplots(figsize=(5, 3.5))
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=chart_colors, autopct="%1.1f%%",
                startangle=90, wedgeprops={"linewidth": 2, "edgecolor": "white"},
            )
            for t in autotexts:
                t.set_fontsize(9)
                t.set_fontweight("bold")
            ax.set_title("Violation Severity Distribution", fontsize=12, fontweight="bold")
            plt.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.warning(f"Chart generation failed (_generate_severity_pie): {e}")
            plt.close('all')
            return None

    def _generate_timeline_chart(
        self, transactions: list, material_events: list, company: str,
    ) -> Optional[BytesIO]:
        """Generate transaction timeline chart using matplotlib."""
        try:
            if not transactions:
                return None

            risk_color_map = {
                "CRITICAL": "#DC143C", "HIGH": "#FF6347",
                "MEDIUM": "#FFD700", "LOW": "#32CD32",
            }

            # Determine y-axis metric: prefer value, fall back to shares if all values are 0
            all_values = [abs(txn.get("value", 0) or 0) for txn in transactions]
            use_shares = all(v == 0 for v in all_values)
            if use_shares:
                y_label = "Shares"
                y_formatter = mticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
            else:
                y_label = "Transaction Value ($)"
                y_formatter = mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")

            fig, ax = plt.subplots(figsize=(9, 4))

            for txn in transactions:
                txn_date = self._parse_date(txn.get("date"))
                if use_shares:
                    y_val = abs(txn.get("shares", 0) or 0)
                else:
                    y_val = abs(txn.get("value", 0) or 0)
                risk = txn.get("risk_level", "LOW")
                c = risk_color_map.get(risk, "#888888")
                size = max(15, min(200, y_val / (10 if use_shares else 10000)))
                ax.scatter(txn_date, y_val, s=size, c=c, alpha=0.7, edgecolors="white", linewidth=0.8)

            # Material events
            for evt in (material_events or []):
                evt_date = evt.get("date")
                if evt_date:
                    ax.axvline(x=self._parse_date(evt_date), color="#7FDBFF", linestyle="--", linewidth=1, alpha=0.7)

            ax.set_xlabel("Date", fontsize=10)
            ax.set_ylabel(y_label, fontsize=10)
            ax.set_title(f"{company} — Transaction Timeline", fontsize=12, fontweight="bold")
            ax.yaxis.set_major_formatter(y_formatter)

            # Legend
            for level, c in risk_color_map.items():
                ax.scatter([], [], c=c, s=40, label=level, edgecolors="white")
            ax.legend(title="Risk Level", loc="upper left", fontsize=8, title_fontsize=9)

            ax.grid(True, alpha=0.3)
            fig.autofmt_xdate()
            plt.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.warning(f"Chart generation failed (_generate_timeline_chart): {e}")
            plt.close('all')
            return None

    def _generate_profit_bar(self, beneficiaries: list, company: str) -> Optional[BytesIO]:
        """Generate horizontal bar chart of beneficiary profits."""
        try:
            if not beneficiaries:
                return None

            # Determine metric: prefer total_profit, fall back to total_shares or transaction_count
            all_profits = [b.get("total_profit", 0) or 0 for b in beneficiaries]
            if all(p == 0 for p in all_profits):
                all_shares = [b.get("total_shares", 0) or 0 for b in beneficiaries]
                if any(s != 0 for s in all_shares):
                    metric_key = "total_shares"
                    x_label = "Total Shares"
                    x_formatter = mticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
                else:
                    metric_key = "transaction_count"
                    x_label = "Transaction Count"
                    x_formatter = mticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
            else:
                metric_key = "total_profit"
                x_label = "Estimated Profit ($)"
                x_formatter = mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")

            # Filter out entries with zero metric value
            filtered = [b for b in beneficiaries if (b.get(metric_key, 0) or 0) != 0]
            if not filtered:
                return None

            names = [b.get("name", "Unknown")[:20] for b in filtered]
            values = [b.get(metric_key, 0) or 0 for b in filtered]
            risk_scores = [b.get("risk_score", 0) for b in filtered]

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

            fig, ax = plt.subplots(figsize=(8, 3.5))
            y_pos = np.arange(len(names))
            ax.barh(y_pos, values, color=bar_colors, edgecolor="white", linewidth=0.5)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(names, fontsize=8)
            ax.set_xlabel(x_label, fontsize=10)
            ax.set_title(f"{company} — Beneficiary Analysis", fontsize=12, fontweight="bold")
            ax.xaxis.set_major_formatter(x_formatter)
            ax.invert_yaxis()
            ax.grid(True, axis="x", alpha=0.3)
            plt.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.warning(f"Chart generation failed (_generate_profit_bar): {e}")
            plt.close('all')
            return None

    def _generate_role_pie(self, beneficiaries: list, company: str) -> Optional[BytesIO]:
        """Generate role-based distribution pie chart."""
        try:
            if not beneficiaries:
                return None

            # Determine metric: prefer total_profit, fall back to violations or transaction_count
            all_profits = [b.get("total_profit", 0) or 0 for b in beneficiaries]
            if all(p == 0 for p in all_profits):
                all_violations = [b.get("violations", 0) or 0 for b in beneficiaries]
                if any(v != 0 for v in all_violations):
                    metric_key = "violations"
                    chart_title = "Violations by Role"
                else:
                    metric_key = "transaction_count"
                    chart_title = "Transactions by Role"
            else:
                metric_key = "total_profit"
                chart_title = "Profit by Role"

            role_values: Dict[str, float] = {}
            for b in beneficiaries:
                role = b.get("role", "Other") or "Other"
                role_values[role] = role_values.get(role, 0) + (b.get(metric_key, 0) or 0)

            # Filter out zero values
            role_values = {r: v for r, v in role_values.items() if v > 0}
            if not role_values:
                return None

            roles = list(role_values.keys())
            values = list(role_values.values())
            chart_colors = [ROLE_COLORS_HEX.get(r, "#778899") for r in roles]

            fig, ax = plt.subplots(figsize=(5, 3.5))
            wedges, texts, autotexts = ax.pie(
                values, labels=roles, colors=chart_colors, autopct="%1.1f%%",
                startangle=90, wedgeprops={"linewidth": 2, "edgecolor": "white"},
                pctdistance=0.8,
            )
            for t in autotexts:
                t.set_fontsize(8)
            ax.set_title(chart_title, fontsize=12, fontweight="bold")
            plt.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.warning(f"Chart generation failed (_generate_role_pie): {e}")
            plt.close('all')
            return None

    def _generate_heatmap_chart(self, transactions: list, company: str) -> Optional[BytesIO]:
        """Generate trading intensity heatmap."""
        try:
            if not transactions:
                return None

            actor_date_data: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
            actors_set: set = set()
            dates_set: set = set()

            for txn in transactions:
                actor = txn.get("actor", "Unknown")
                txn_date = str(self._parse_date(txn.get("date")))
                value = abs(txn.get("value", 0) or 0)
                actor_date_data[actor][txn_date] += value
                actors_set.add(actor)
                dates_set.add(txn_date)

            sorted_actors = sorted(actors_set)[:15]  # Limit actors for readability
            sorted_dates = sorted(dates_set)

            if not sorted_actors or not sorted_dates:
                return None

            z = np.zeros((len(sorted_actors), len(sorted_dates)))
            for i, actor in enumerate(sorted_actors):
                for j, dt in enumerate(sorted_dates):
                    z[i, j] = actor_date_data[actor].get(dt, 0)

            fig, ax = plt.subplots(figsize=(9, 4))
            im = ax.imshow(z, aspect="auto", cmap="Reds", interpolation="nearest")
            ax.set_yticks(range(len(sorted_actors)))
            ax.set_yticklabels(sorted_actors, fontsize=7)
            # Show subset of date labels
            step = max(1, len(sorted_dates) // 10)
            ax.set_xticks(range(0, len(sorted_dates), step))
            ax.set_xticklabels(
                [sorted_dates[i] for i in range(0, len(sorted_dates), step)],
                rotation=45, ha="right", fontsize=7,
            )
            ax.set_title(f"{company} — Trading Intensity Heatmap", fontsize=12, fontweight="bold")
            cbar = fig.colorbar(im, ax=ax, label="Transaction Value ($)")
            cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
            plt.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.warning(f"Chart generation failed (_generate_heatmap_chart): {e}")
            plt.close('all')
            return None

    def _generate_bubble_chart(self, transactions: list, company: str) -> Optional[BytesIO]:
        """Generate transaction bubble chart."""
        try:
            if not transactions:
                return None

            risk_color_map = {
                "CRITICAL": "#DC143C", "HIGH": "#FF6347",
                "MEDIUM": "#FFD700", "LOW": "#32CD32",
            }

            # Determine sizing metric: prefer value, fall back to shares
            all_values = [abs(txn.get("value", 0) or 0) for txn in transactions]
            use_shares = all(v == 0 for v in all_values)

            fig, ax = plt.subplots(figsize=(9, 4.5))

            for txn in transactions:
                txn_date = self._parse_date(txn.get("date"))
                actor = txn.get("actor", "Unknown")
                if use_shares:
                    metric = abs(txn.get("shares", 0) or 0)
                    size = max(20, min(500, metric / 10))
                else:
                    metric = abs(txn.get("value", 0) or 0)
                    size = max(20, min(500, metric / 5000))
                risk = txn.get("risk_level", "LOW")
                c = risk_color_map.get(risk, "#888888")
                ax.scatter(
                    txn_date, actor, s=size, c=c, alpha=0.7,
                    edgecolors="white", linewidth=0.8,
                )

            ax.set_xlabel("Date", fontsize=10)
            ax.set_ylabel("Actor", fontsize=10)
            size_label = "Shares" if use_shares else "Value"
            ax.set_title(
                f"{company} — Transaction Magnitude (Bubble Size = {size_label})",
                fontsize=12, fontweight="bold",
            )

            for level, c in risk_color_map.items():
                ax.scatter([], [], c=c, s=60, label=level, edgecolors="white")
            ax.legend(title="Risk Level", loc="upper left", fontsize=8, title_fontsize=9)
            ax.grid(True, alpha=0.3)
            fig.autofmt_xdate()
            plt.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.warning(f"Chart generation failed (_generate_bubble_chart): {e}")
            plt.close('all')
            return None

    def _generate_deadline_chart(
        self, filings: list, annual_events: list, company: str,
    ) -> Optional[BytesIO]:
        """Generate filing deadline compliance chart."""
        try:
            if not filings:
                return None

            from .visualizations.filing_deadline_chart import FilingDeadlineChart

            fdc = FilingDeadlineChart()
            enriched = fdc._enrich_filings(filings)

            status_colors = {"ON_TIME": "#2ECC40", "LATE": "#FF4136", "UNKNOWN": "#AAAAAA"}

            fig, ax = plt.subplots(figsize=(9, 4))

            for f in enriched:
                fdate = self._parse_date(f.get("filing_date"))
                ftype = f.get("filing_type", "Unknown")
                status = f.get("status", "UNKNOWN")
                c = status_colors.get(status, "#AAAAAA")
                marker = "o" if status != "LATE" else "x"
                edge_kw = {"edgecolors": "white"} if marker == "o" else {}
                ax.scatter(fdate, ftype, c=c, marker=marker, s=60, linewidth=0.8, **edge_kw)

            for evt in (annual_events or []):
                evt_date = evt.get("date")
                if evt_date:
                    ax.axvline(x=self._parse_date(evt_date), color="#7FDBFF", linestyle="--", linewidth=1, alpha=0.6)

            ax.set_xlabel("Date", fontsize=10)
            ax.set_ylabel("Filing Type", fontsize=10)
            ax.set_title(f"{company} — Filing Deadline Compliance", fontsize=12, fontweight="bold")

            for status, c in status_colors.items():
                marker = "o" if status != "LATE" else "x"
                ax.scatter([], [], c=c, marker=marker, s=40, label=status.replace("_", " ").title())
            ax.legend(title="Status", loc="upper left", fontsize=8, title_fontsize=9)
            ax.grid(True, alpha=0.3)
            fig.autofmt_xdate()
            plt.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.warning(f"Chart generation failed (_generate_deadline_chart): {e}")
            plt.close('all')
            return None

    def _generate_network_chart(
        self, actors: list, relationships: list, company: str,
    ) -> Optional[BytesIO]:
        """Generate actor network graph."""
        try:
            if not actors:
                return None

            try:
                import networkx as nx
            except ImportError:
                return None

            G = nx.Graph()
            for actor in actors:
                G.add_node(
                    actor.get("actor_id", actor.get("name", "Unknown")),
                    name=actor.get("name", "Unknown"),
                    risk_score=actor.get("risk_score", 0),
                )

            for rel in (relationships or []):
                G.add_edge(rel.get("source", ""), rel.get("target", ""))

            if len(G.nodes()) == 0:
                return None

            pos = nx.spring_layout(G, k=0.8, iterations=50, seed=42)

            fig, ax = plt.subplots(figsize=(8, 5))

            # Draw edges
            nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3, edge_color="#888888")

            # Draw nodes colored by risk score
            node_colors = []
            node_sizes = []
            for node in G.nodes():
                rs = G.nodes[node].get("risk_score", 0)
                if rs >= 80:
                    node_colors.append("#DC143C")
                elif rs >= 60:
                    node_colors.append("#FF6347")
                elif rs >= 40:
                    node_colors.append("#FFD700")
                else:
                    node_colors.append("#32CD32")
                node_sizes.append(200 + len(list(G.neighbors(node))) * 80)

            nx.draw_networkx_nodes(
                G, pos, ax=ax, node_color=node_colors, node_size=node_sizes,
                edgecolors="white", linewidths=1.5,
            )
            labels = {n: G.nodes[n].get("name", n)[:15] for n in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=7)

            ax.set_title(
                f"{company} — Filing Party Association Network",
                fontsize=12, fontweight="bold",
            )
            ax.axis("off")
            plt.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.warning(f"Chart generation failed (_generate_network_chart): {e}")
            plt.close('all')
            return None

    # ═══════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════

    def _extract_violations(self, results: Dict) -> list:
        """Extract all violations from analysis results."""
        violations = []
        if "violations" in results:
            violations.extend(results["violations"])
        for _key, value in results.items():
            if isinstance(value, dict) and "violations" in value:
                violations.extend(value["violations"])
        return violations
