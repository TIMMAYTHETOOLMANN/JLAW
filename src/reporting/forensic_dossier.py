"""
Forensic-Grade Visual Dossier Generator
========================================

Produces a spectacular, prosecution-ready PDF dossier with:
- Professional cover page with classification markings
- Executive Summary with key findings and risk assessment
- KPI dashboard with severity gauges and financial totals
- Complete violation breakdown with color-coded tables
- Contradiction Analysis section (public claims vs SEC findings)
- Transaction timeline with embedded charts
- Beneficiary profit waterfall and executive compensation analysis
- Actor network relationship diagrams
- Filing compliance heatmaps and bubble charts
- Penalty estimates with legal citations
- Evidence chain and chain-of-custody summary
- Standalone chart exports for the analysis bundle

This replaces the basic visual_report_generator with a comprehensive,
forensic-grade output suitable for DOJ referral packages.
"""
from __future__ import annotations

import hashlib
import logging
from collections import Counter, defaultdict
from datetime import datetime, date
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, HRFlowable, KeepTogether, ListFlowable, ListItem,
    )
    from reportlab.graphics.shapes import Drawing, Rect, String, Line
    from reportlab.graphics.charts.piecharts import Pie
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    inch = 72.0

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import matplotlib.patches as mpatches
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# COLOR PALETTE — Professional forensic/law enforcement aesthetic
# ═══════════════════════════════════════════════════════════════════════════

BRAND_NAVY = "#0D1B2A"
BRAND_DARK = "#1B2838"
BRAND_ACCENT = "#C8102E"
BRAND_GOLD = "#D4A843"
BRAND_WHITE = "#FFFFFF"
BRAND_LIGHT = "#F0F2F5"
BRAND_GRAY = "#6C757D"

SEV_CRITICAL = "#DC143C"
SEV_HIGH = "#FF6347"
SEV_MEDIUM = "#FFB347"
SEV_LOW = "#32CD32"
SEV_INFO = "#4A90D9"

SEV_COLORS = {"CRITICAL": SEV_CRITICAL, "HIGH": SEV_HIGH, "MEDIUM": SEV_MEDIUM, "LOW": SEV_LOW}

CONTRADICTION_COLORS = {
    "revenue_mismatch": "#E74C3C",
    "profit_inflation": "#E67E22",
    "growth_vs_decline": "#9B59B6",
    "insider_timing": "#C0392B",
    "compensation_misrepresentation": "#2980B9",
    "timeline_conflict": "#F39C12",
}


class ForensicDossierGenerator:
    """
    Generates a comprehensive, forensic-grade visual PDF dossier.

    This is the primary output generator for JLAW, producing dense,
    professional, prosecution-ready reports with embedded analytics
    and visual representations.
    """

    TITLE_FONT = "Helvetica-Bold"
    BODY_FONT = "Helvetica"
    MONO_FONT = "Courier"

    def __init__(self, output_dir: str = "./output/reports"):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab required: pip install reportlab")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chart_dir = self.output_dir / "charts"
        self.chart_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Configure professional forensic document styles."""
        styles_to_add = [
            ("DossierTitle", "Heading1", 28, BRAND_NAVY, 20, TA_CENTER, self.TITLE_FONT),
            ("DossierSubtitle", "Heading2", 16, BRAND_GRAY, 8, TA_CENTER, self.BODY_FONT),
            ("SectionTitle", "Heading2", 18, BRAND_NAVY, 14, TA_LEFT, self.TITLE_FONT),
            ("SubSection", "Heading3", 14, BRAND_DARK, 10, TA_LEFT, self.TITLE_FONT),
            ("BodyText2", "BodyText", 10, "#2C2C2C", 6, TA_JUSTIFY, self.BODY_FONT),
            ("SmallBody", "BodyText", 9, "#444444", 4, TA_LEFT, self.BODY_FONT),
            ("KPIValue", "Normal", 32, BRAND_ACCENT, 4, TA_CENTER, self.TITLE_FONT),
            ("KPILabel", "Normal", 10, BRAND_GRAY, 6, TA_CENTER, self.BODY_FONT),
            ("Classified", "Normal", 12, BRAND_ACCENT, 4, TA_CENTER, self.TITLE_FONT),
            ("MonoSmall", "Code", 7, "#555555", 2, TA_LEFT, self.MONO_FONT),
        ]
        for name, parent, size, color, space_after, align, font in styles_to_add:
            self.styles.add(ParagraphStyle(
                name=name, parent=self.styles[parent],
                fontSize=size, textColor=colors.HexColor(color),
                spaceAfter=space_after, alignment=align, fontName=font,
                leading=size * 1.3,
            ))

    # ═══════════════════════════════════════════════════════════════════
    # MAIN ENTRY POINT
    # ═══════════════════════════════════════════════════════════════════

    def generate_dossier(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        contradiction_map: Optional[Dict[str, Any]] = None,
        output_filename: Optional[str] = None,
    ) -> Tuple[Path, List[Path]]:
        """
        Generate the full forensic dossier PDF plus standalone chart exports.

        Args:
            case_id: Unique case identifier
            company_name: Target company
            cik: SEC CIK
            analysis_results: Full analysis results dict
            contradiction_map: Optional contradiction mapping results
            output_filename: Custom output filename

        Returns:
            Tuple of (pdf_path, list of standalone chart paths)
        """
        if not output_filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"FORENSIC_DOSSIER_{case_id}_{ts}.pdf"

        pdf_path = self.output_dir / output_filename
        standalone_charts: List[Path] = []

        doc = SimpleDocTemplate(
            str(pdf_path), pagesize=letter,
            rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=48,
        )

        story: list = []

        # 1. COVER PAGE
        story.extend(self._build_cover_page(case_id, company_name, cik, analysis_results))
        story.append(PageBreak())

        # 2. TABLE OF CONTENTS
        story.extend(self._build_toc(contradiction_map is not None))
        story.append(PageBreak())

        # 3. EXECUTIVE SUMMARY
        story.extend(self._build_executive_summary(
            case_id, company_name, cik, analysis_results, contradiction_map
        ))
        story.append(PageBreak())

        # 4. KPI DASHBOARD
        kpi_charts = self._build_kpi_dashboard(analysis_results, company_name)
        story.extend(kpi_charts)
        story.append(PageBreak())

        # 5. VIOLATION ANALYSIS
        story.extend(self._build_violation_analysis(analysis_results, company_name))
        story.append(PageBreak())

        # 6. CONTRADICTION ANALYSIS (if available)
        if contradiction_map:
            story.extend(self._build_contradiction_section(contradiction_map, company_name))
            story.append(PageBreak())

        # 7. TRANSACTION TIMELINE
        txns = analysis_results.get("transactions", [])
        events = analysis_results.get("material_events", [])
        if txns:
            story.extend(self._build_transaction_timeline(txns, events, company_name))
            chart_path = self._save_standalone_chart(
                self._generate_timeline_chart(txns, events, company_name),
                f"timeline_{case_id}.png"
            )
            if chart_path:
                standalone_charts.append(chart_path)
            story.append(PageBreak())

        # 8. BENEFICIARY ANALYSIS
        bens = analysis_results.get("beneficiaries", [])
        if bens:
            story.extend(self._build_beneficiary_analysis(bens, company_name))
            chart_path = self._save_standalone_chart(
                self._generate_profit_waterfall(bens, company_name),
                f"beneficiary_profits_{case_id}.png"
            )
            if chart_path:
                standalone_charts.append(chart_path)
            story.append(PageBreak())

        # 9. ACTOR NETWORK
        actors = analysis_results.get("actors", [])
        rels = analysis_results.get("relationships", [])
        if actors:
            story.extend(self._build_network_section(actors, rels, company_name))
            chart_path = self._save_standalone_chart(
                self._generate_network_chart(actors, rels, company_name),
                f"network_{case_id}.png"
            )
            if chart_path:
                standalone_charts.append(chart_path)
            story.append(PageBreak())

        # 10. FILING COMPLIANCE
        filings = analysis_results.get("filings", [])
        if filings:
            story.extend(self._build_filing_compliance(filings, company_name))
            story.append(PageBreak())

        # 11. PENALTY ESTIMATES
        story.extend(self._build_penalty_estimates(analysis_results))
        story.append(PageBreak())

        # 12. EVIDENCE CHAIN & SIGNATURES
        story.extend(self._build_evidence_chain(case_id, analysis_results))

        # Build PDF
        doc.build(story, onFirstPage=self._draw_page, onLaterPages=self._draw_page)

        # Save severity pie as standalone
        sev_chart = self._generate_severity_donut(analysis_results)
        if sev_chart:
            chart_path = self._save_standalone_chart(sev_chart, f"severity_{case_id}.png")
            if chart_path:
                standalone_charts.append(chart_path)

        logger.info(f"Forensic dossier generated: {pdf_path} ({len(standalone_charts)} standalone charts)")
        return pdf_path, standalone_charts

    # ═══════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════════════════════════════

    def _build_cover_page(
        self, case_id: str, company: str, cik: str, results: Dict,
    ) -> list:
        story: list = []
        story.append(Spacer(1, 0.8 * inch))

        # Classification banner
        story.append(self._accent_bar())
        story.append(Paragraph(
            "CONFIDENTIAL — LAW ENFORCEMENT SENSITIVE",
            self.styles["Classified"],
        ))
        story.append(self._accent_bar())
        story.append(Spacer(1, 0.5 * inch))

        # Title block
        story.append(Paragraph("FORENSIC ANALYSIS", self.styles["DossierTitle"]))
        story.append(Paragraph("PROSECUTION DOSSIER", self.styles["DossierTitle"]))
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph(company, self.styles["DossierSubtitle"]))
        story.append(Spacer(1, 0.5 * inch))

        # Case metadata table
        total_v = results.get("total_violations", 0)
        crit = results.get("critical_alerts", 0)
        high = results.get("high_alerts", 0)
        penalties = results.get("estimated_penalties", {})
        civil_max = penalties.get("civil_maximum", 0)

        data = [
            ["Case ID", case_id],
            ["Target Entity", company],
            ["SEC CIK", cik],
            ["Report Generated", datetime.now().strftime("%B %d, %Y  %H:%M UTC")],
            ["Total Violations", str(total_v)],
            ["Critical Alerts", str(crit)],
            ["High-Priority Alerts", str(high)],
            ["Maximum Civil Exposure", f"${civil_max:,.0f}"],
        ]
        tbl = Table(data, colWidths=[2.4 * inch, 3.8 * inch])
        tbl.setStyle(TableStyle([
            ("FONT", (0, 0), (0, -1), self.TITLE_FONT, 10),
            ("FONT", (1, 0), (1, -1), self.BODY_FONT, 10),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F2F5")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(tbl)

        story.append(Spacer(1, 0.6 * inch))
        story.append(Paragraph(
            "Generated by JLAW Forensic Analysis System v4.2",
            ParagraphStyle("footer", parent=self.styles["Normal"],
                           alignment=TA_CENTER, fontSize=9,
                           textColor=colors.HexColor(BRAND_GRAY)),
        ))
        story.append(Paragraph(
            "Justice Law Analytics Workbench — DOJ-Grade SEC Intelligence Platform",
            ParagraphStyle("footer2", parent=self.styles["Normal"],
                           alignment=TA_CENTER, fontSize=8,
                           textColor=colors.HexColor(BRAND_GRAY)),
        ))

        return story

    # ═══════════════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ═══════════════════════════════════════════════════════════════════

    def _build_toc(self, has_contradictions: bool) -> list:
        story: list = []
        story.append(Paragraph("TABLE OF CONTENTS", self.styles["SectionTitle"]))
        story.append(self._section_bar())
        story.append(Spacer(1, 12))

        sections = [
            "I.     Executive Summary & Risk Assessment",
            "II.    Key Metrics Dashboard",
            "III.   Violation Severity Analysis",
        ]
        if has_contradictions:
            sections.append("IV.    Contradiction Analysis — Public Statements vs. SEC Findings")
            sections.extend([
                "V.     Transaction Timeline & Insider Activity",
                "VI.    Financial Beneficiary Analysis",
                "VII.   Filing Party Network & Associations",
                "VIII.  Filing Deadline Compliance",
                "IX.    Estimated Penalties & Legal Exposure",
                "X.     Evidence Chain & Digital Signatures",
            ])
        else:
            sections.extend([
                "IV.    Transaction Timeline & Insider Activity",
                "V.     Financial Beneficiary Analysis",
                "VI.    Filing Party Network & Associations",
                "VII.   Filing Deadline Compliance",
                "VIII.  Estimated Penalties & Legal Exposure",
                "IX.    Evidence Chain & Digital Signatures",
            ])

        for s in sections:
            story.append(Paragraph(s, ParagraphStyle(
                "toc_entry", parent=self.styles["BodyText2"],
                fontSize=11, spaceAfter=8, leftIndent=20,
                fontName=self.BODY_FONT,
            )))

        return story

    # ═══════════════════════════════════════════════════════════════════
    # EXECUTIVE SUMMARY
    # ═══════════════════════════════════════════════════════════════════

    def _build_executive_summary(
        self, case_id: str, company: str, cik: str,
        results: Dict, contradiction_map: Optional[Dict] = None,
    ) -> list:
        story: list = []
        story.append(Paragraph("I. EXECUTIVE SUMMARY", self.styles["SectionTitle"]))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))

        # Summary text
        summary = results.get("executive_summary_text", "")
        if summary:
            story.append(Paragraph(summary, self.styles["BodyText2"]))
            story.append(Spacer(1, 10))

        # Risk assessment box
        total_v = results.get("total_violations", 0)
        crit = results.get("critical_alerts", 0)
        high = results.get("high_alerts", 0)

        if crit > 0:
            risk_level = "EXTREME"
            risk_color = SEV_CRITICAL
            recommendation = "IMMEDIATE DOJ REFERRAL RECOMMENDED"
        elif high > 5:
            risk_level = "HIGH"
            risk_color = SEV_HIGH
            recommendation = "SEC ENFORCEMENT ACTION RECOMMENDED"
        elif total_v > 10:
            risk_level = "ELEVATED"
            risk_color = SEV_MEDIUM
            recommendation = "DETAILED INVESTIGATION WARRANTED"
        else:
            risk_level = "MODERATE"
            risk_color = SEV_LOW
            recommendation = "CONTINUED MONITORING RECOMMENDED"

        risk_data = [
            [Paragraph(f'<font color="{BRAND_WHITE}"><b>RISK ASSESSMENT</b></font>',
                        self.styles["SmallBody"]),
             Paragraph(f'<font color="{BRAND_WHITE}"><b>{risk_level}</b></font>',
                        ParagraphStyle("ra", parent=self.styles["SmallBody"],
                                       alignment=TA_CENTER, textColor=colors.white))],
            [Paragraph(f"<b>Recommendation:</b> {recommendation}", self.styles["SmallBody"]),
             Paragraph(f"<b>Violations:</b> {total_v} ({crit} critical, {high} high)",
                        self.styles["SmallBody"])],
        ]
        risk_tbl = Table(risk_data, colWidths=[3.6 * inch, 3.0 * inch])
        risk_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(risk_color)),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F8F9FA")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONT", (0, 0), (-1, 0), self.TITLE_FONT, 11),
            ("FONT", (0, 1), (-1, 1), self.BODY_FONT, 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(risk_tbl)
        story.append(Spacer(1, 14))

        # Contradiction summary (if available)
        if contradiction_map:
            c_total = contradiction_map.get("total_contradictions_found", 0)
            c_crit = contradiction_map.get("critical_contradictions", 0)
            c_high = contradiction_map.get("high_contradictions", 0)
            stmts = contradiction_map.get("total_statements_collected", 0)

            story.append(Paragraph("Contradiction Analysis Summary", self.styles["SubSection"]))
            story.append(Paragraph(
                f"The Web Intelligence Engine collected <b>{stmts}</b> public statements "
                f"and identified <b>{c_total}</b> contradiction(s) between public claims "
                f"and SEC filing analysis. Of these, <b>{c_crit}</b> are CRITICAL and "
                f"<b>{c_high}</b> are HIGH severity.",
                self.styles["BodyText2"],
            ))
            story.append(Spacer(1, 10))

        # Key findings bullets
        story.append(Paragraph("Key Findings", self.styles["SubSection"]))
        violations = results.get("violations", [])
        if violations:
            top_types = Counter(
                v.get("violation_type", "Unknown") for v in violations
            ).most_common(5)
            items = []
            for vtype, count in top_types:
                items.append(ListItem(Paragraph(
                    f"<b>{vtype}</b>: {count} occurrence(s) detected",
                    self.styles["SmallBody"],
                )))
            story.append(ListFlowable(items, bulletType="bullet", bulletFontSize=8))

        return story

    # ═══════════════════════════════════════════════════════════════════
    # KPI DASHBOARD
    # ═══════════════════════════════════════════════════════════════════

    def _build_kpi_dashboard(self, results: Dict, company: str) -> list:
        story: list = []
        story.append(Paragraph("II. KEY METRICS DASHBOARD", self.styles["SectionTitle"]))
        story.append(self._section_bar())
        story.append(Spacer(1, 12))

        total_v = results.get("total_violations", 0)
        crit = results.get("critical_alerts", 0)
        high = results.get("high_alerts", 0)
        penalties = results.get("estimated_penalties", {})
        civil_max = penalties.get("civil_maximum", 0)
        disgorgement = penalties.get("disgorgement", 0)

        # KPI cards (2 rows of 3)
        kpi_data = [
            [
                self._kpi_cell(str(total_v), "Total Violations", SEV_CRITICAL if total_v > 20 else SEV_MEDIUM),
                self._kpi_cell(str(crit), "Critical Alerts", SEV_CRITICAL),
                self._kpi_cell(str(high), "High Alerts", SEV_HIGH),
            ],
            [
                self._kpi_cell(f"${civil_max:,.0f}", "Max Civil Penalty", BRAND_NAVY),
                self._kpi_cell(f"${disgorgement:,.0f}", "Est. Disgorgement", BRAND_DARK),
                self._kpi_cell(
                    f"{penalties.get('prison_years_maximum', 0)}yr",
                    "Criminal Exposure",
                    SEV_CRITICAL if penalties.get("criminal_exposure") else SEV_LOW,
                ),
            ],
        ]
        kpi_table = Table(kpi_data, colWidths=[2.2 * inch] * 3)
        kpi_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#DEE2E6")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 16))

        # Severity donut chart
        if MATPLOTLIB_AVAILABLE:
            chart = self._generate_severity_donut(results)
            if chart:
                story.append(Paragraph("Violation Severity Distribution", self.styles["SubSection"]))
                story.append(Image(chart, width=4.5 * inch, height=3.2 * inch))

        return story

    def _kpi_cell(self, value: str, label: str, color: str) -> Table:
        """Build a single KPI card cell."""
        data = [
            [Paragraph(f'<font color="{color}"><b>{value}</b></font>',
                        ParagraphStyle("kv", parent=self.styles["Normal"],
                                       fontSize=24, alignment=TA_CENTER,
                                       fontName=self.TITLE_FONT))],
            [Paragraph(label, self.styles["KPILabel"])],
        ]
        t = Table(data, colWidths=[2.0 * inch])
        t.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFBFC")),
        ]))
        return t

    # ═══════════════════════════════════════════════════════════════════
    # VIOLATION ANALYSIS
    # ═══════════════════════════════════════════════════════════════════

    def _build_violation_analysis(self, results: Dict, company: str) -> list:
        story: list = []
        story.append(Paragraph("III. VIOLATION SEVERITY ANALYSIS", self.styles["SectionTitle"]))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))

        violations = results.get("violations", [])
        if not violations:
            story.append(Paragraph("No violations detected.", self.styles["BodyText2"]))
            return story

        # Group by severity
        by_sev: Dict[str, list] = {}
        for v in violations:
            sev = self._normalize_severity(v.get("severity", v.get("risk_level", "LOW")))
            by_sev.setdefault(sev, []).append(v)

        # Severity summary table
        header = ["Severity", "Count", "Top Violation Types", "Action Required"]
        rows = [header]
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            viols = by_sev.get(sev, [])
            if not viols:
                continue
            types = Counter(v.get("violation_type", "Unknown") for v in viols)
            top = ", ".join(f"{t} ({c})" for t, c in types.most_common(3))
            action = {"CRITICAL": "DOJ Referral", "HIGH": "SEC Priority",
                      "MEDIUM": "Civil Action", "LOW": "Monitoring"}.get(sev, "")
            rows.append([sev, str(len(viols)), top, action])

        tbl = self._styled_table(rows, [1.0*inch, 0.7*inch, 3.5*inch, 1.3*inch], color_col=0)
        story.append(tbl)
        story.append(Spacer(1, 16))

        # Detailed violation list (top 20)
        story.append(Paragraph("Top Violations Detail", self.styles["SubSection"]))
        sorted_viols = sorted(violations, key=lambda v: (
            {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(
                self._normalize_severity(v.get("severity", "LOW")), 4
            )
        ))[:20]

        detail_rows = [["#", "Severity", "Type", "Description", "Node"]]
        for i, v in enumerate(sorted_viols, 1):
            sev = self._normalize_severity(v.get("severity", "LOW"))
            desc = v.get("description", "")
            if len(desc) > 60:
                desc = desc[:57] + "..."
            detail_rows.append([
                str(i), sev,
                v.get("violation_type", "Unknown")[:25],
                desc,
                v.get("node_id", ""),
            ])

        detail_tbl = self._styled_table(
            detail_rows, [0.4*inch, 0.8*inch, 1.5*inch, 2.8*inch, 1.0*inch],
            color_col=1, font_size=8,
        )
        story.append(detail_tbl)

        return story

    # ═══════════════════════════════════════════════════════════════════
    # CONTRADICTION ANALYSIS
    # ═══════════════════════════════════════════════════════════════════

    def _build_contradiction_section(self, cmap: Dict, company: str) -> list:
        story: list = []
        story.append(Paragraph(
            "IV. CONTRADICTION ANALYSIS",
            self.styles["SectionTitle"],
        ))
        story.append(self._section_bar())
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "Cross-reference of public statements, earnings calls, and press releases "
            "against SEC filing analysis findings. Contradictions indicate potential "
            "securities fraud, misleading statements, or material misrepresentations.",
            self.styles["BodyText2"],
        ))
        story.append(Spacer(1, 10))

        contradictions = cmap.get("contradictions", [])
        if not contradictions:
            story.append(Paragraph(
                "No contradictions detected between public statements and SEC findings.",
                self.styles["BodyText2"],
            ))
            return story

        # Summary stats
        c_total = cmap.get("total_contradictions_found", 0)
        c_crit = cmap.get("critical_contradictions", 0)
        c_high = cmap.get("high_contradictions", 0)
        sources = cmap.get("source_breakdown", {})

        summary_data = [
            ["Metric", "Value"],
            ["Total Public Statements Analyzed", str(cmap.get("total_statements_collected", 0))],
            ["Contradictions Found", str(c_total)],
            ["Critical Contradictions", str(c_crit)],
            ["High-Severity Contradictions", str(c_high)],
        ]
        for src, count in sorted(sources.items(), key=lambda x: -x[1]):
            summary_data.append([f"Source: {src.replace('_', ' ').title()}", str(count)])

        summary_tbl = self._styled_table(summary_data, [3.2*inch, 2.5*inch])
        story.append(summary_tbl)
        story.append(Spacer(1, 14))

        # Contradiction type chart
        if MATPLOTLIB_AVAILABLE and contradictions:
            chart = self._generate_contradiction_chart(contradictions, company)
            if chart:
                story.append(Image(chart, width=5.5 * inch, height=3.0 * inch))
                story.append(Spacer(1, 10))

        # Detailed contradiction entries
        story.append(Paragraph("Detailed Contradiction Entries", self.styles["SubSection"]))
        story.append(Spacer(1, 6))

        for i, c in enumerate(contradictions[:15], 1):
            entry_data = self._build_contradiction_entry(i, c)
            story.extend(entry_data)
            story.append(Spacer(1, 8))

        return story

    def _build_contradiction_entry(self, idx: int, c: Dict) -> list:
        """Build a single contradiction entry block."""
        items: list = []

        sev = c.get("severity", "MEDIUM")
        sev_color = SEV_COLORS.get(sev, SEV_MEDIUM)
        ctype = c.get("contradiction_type", "unknown").replace("_", " ").title()
        confidence = c.get("confidence", 0)

        # Header row
        header_text = (
            f'<font color="{sev_color}"><b>[{sev}]</b></font> '
            f'Contradiction #{idx}: <b>{ctype}</b> '
            f'(Confidence: {confidence:.0%})'
        )
        items.append(Paragraph(header_text, ParagraphStyle(
            f"ch_{idx}", parent=self.styles["SmallBody"],
            fontSize=10, spaceAfter=4, fontName=self.TITLE_FONT,
        )))

        # Public statement
        pub = c.get("public_statement", {})
        stmt_text = pub.get("text", "N/A")
        if len(stmt_text) > 200:
            stmt_text = stmt_text[:197] + "..."
        stmt_src = pub.get("source_type", "unknown").replace("_", " ").title()
        stmt_speaker = pub.get("speaker", "")
        stmt_date = pub.get("date", "")

        items.append(Paragraph(
            f'<b>Public Statement</b> ({stmt_src}'
            f'{" — " + stmt_speaker if stmt_speaker else ""}'
            f'{" — " + str(stmt_date)[:10] if stmt_date else ""}):<br/>'
            f'<i>"{stmt_text}"</i>',
            self.styles["SmallBody"],
        ))

        # SEC Finding
        explanation = c.get("explanation", "")
        items.append(Paragraph(
            f"<b>SEC Finding:</b> {explanation}",
            self.styles["SmallBody"],
        ))

        # Dollar discrepancy
        dollar = c.get("dollar_discrepancy")
        pct = c.get("percentage_discrepancy")
        if dollar or pct:
            disc_parts = []
            if dollar:
                disc_parts.append(f"${dollar:,.0f}")
            if pct:
                disc_parts.append(f"{pct:.1f}%")
            items.append(Paragraph(
                f'<b>Discrepancy:</b> <font color="{SEV_CRITICAL}">{" / ".join(disc_parts)}</font>',
                self.styles["SmallBody"],
            ))

        # Legal implications
        legal = c.get("legal_implications", "")
        if legal:
            items.append(Paragraph(
                f"<b>Legal Implications:</b> {legal}",
                ParagraphStyle("legal", parent=self.styles["SmallBody"],
                               fontSize=8, textColor=colors.HexColor("#555555")),
            ))

        # Applicable statutes
        statutes = c.get("applicable_statutes", [])
        if statutes:
            items.append(Paragraph(
                f"<b>Applicable Statutes:</b> {' | '.join(statutes)}",
                ParagraphStyle("stat", parent=self.styles["SmallBody"],
                               fontSize=8, textColor=colors.HexColor(BRAND_NAVY)),
            ))

        # Separator
        items.append(HRFlowable(
            width="100%", thickness=0.5, color=colors.HexColor("#E0E0E0"),
            spaceAfter=4, spaceBefore=4,
        ))

        return items

    # ═══════════════════════════════════════════════════════════════════
    # TRANSACTION TIMELINE
    # ═══════════════════════════════════════════════════════════════════

    def _build_transaction_timeline(
        self, transactions: list, events: list, company: str,
    ) -> list:
        story: list = []
        num = "V" if not hasattr(self, '_has_contradictions') else "V"
        story.append(Paragraph("TRANSACTION TIMELINE & INSIDER ACTIVITY", self.styles["SectionTitle"]))
        story.append(self._section_bar())
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "Chronological view of insider transactions color-coded by risk level. "
            "Marker size reflects transaction value. Dashed vertical lines indicate material events.",
            self.styles["BodyText2"],
        ))
        story.append(Spacer(1, 8))

        if MATPLOTLIB_AVAILABLE:
            chart = self._generate_timeline_chart(transactions, events, company)
            if chart:
                story.append(Image(chart, width=6.5 * inch, height=3.5 * inch))
                story.append(Spacer(1, 10))

        # Transaction summary table
        story.append(Paragraph("Transaction Summary", self.styles["SubSection"]))
        total_val = sum(abs(t.get("value", 0)) for t in transactions)
        by_risk = Counter(t.get("risk_level", "LOW") for t in transactions)

        summary_data = [
            ["Metric", "Value"],
            ["Total Transactions", str(len(transactions))],
            ["Total Value", f"${total_val:,.0f}"],
        ]
        for risk in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if by_risk.get(risk, 0) > 0:
                summary_data.append([f"{risk} Risk Transactions", str(by_risk[risk])])

        story.append(self._styled_table(summary_data, [3.2*inch, 2.5*inch]))

        return story

    # ═══════════════════════════════════════════════════════════════════
    # BENEFICIARY ANALYSIS
    # ═══════════════════════════════════════════════════════════════════

    def _build_beneficiary_analysis(self, beneficiaries: list, company: str) -> list:
        story: list = []
        story.append(Paragraph("FINANCIAL BENEFICIARY ANALYSIS", self.styles["SectionTitle"]))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))

        sorted_bens = sorted(beneficiaries, key=lambda b: b.get("total_profit", 0), reverse=True)[:15]

        header = ["Name", "Role", "Total Profit", "Transactions", "Risk Score", "Violations"]
        rows = [header]
        for b in sorted_bens:
            rows.append([
                b.get("name", "Unknown")[:25],
                b.get("role", "—")[:15],
                f"${b.get('total_profit', 0):,.0f}",
                str(b.get("transaction_count", 0)),
                f"{b.get('risk_score', 0):.0f}",
                str(b.get("violations", 0)),
            ])

        tbl = self._styled_table(
            rows, [1.5*inch, 0.8*inch, 1.1*inch, 0.9*inch, 0.8*inch, 0.8*inch],
        )
        story.append(tbl)
        story.append(Spacer(1, 14))

        if MATPLOTLIB_AVAILABLE and sorted_bens:
            chart = self._generate_profit_waterfall(sorted_bens, company)
            if chart:
                story.append(Paragraph("Profit by Beneficiary", self.styles["SubSection"]))
                story.append(Image(chart, width=6.0 * inch, height=3.0 * inch))
                story.append(Spacer(1, 10))

            role_chart = self._generate_role_distribution(beneficiaries, company)
            if role_chart:
                story.append(Paragraph("Profit Distribution by Role", self.styles["SubSection"]))
                story.append(Image(role_chart, width=4.5 * inch, height=3.0 * inch))

        return story

    # ═══════════════════════════════════════════════════════════════════
    # NETWORK SECTION
    # ═══════════════════════════════════════════════════════════════════

    def _build_network_section(self, actors: list, relationships: list, company: str) -> list:
        story: list = []
        story.append(Paragraph("FILING PARTY NETWORK & ASSOCIATIONS", self.styles["SectionTitle"]))
        story.append(self._section_bar())
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "Network graph showing relationships between filing parties. "
            "Node color indicates risk score; size reflects connection count.",
            self.styles["BodyText2"],
        ))
        story.append(Spacer(1, 8))

        if MATPLOTLIB_AVAILABLE:
            chart = self._generate_network_chart(actors, relationships, company)
            if chart:
                story.append(Image(chart, width=6.0 * inch, height=4.0 * inch))
                story.append(Spacer(1, 10))

        # Actor table
        if actors:
            header = ["Name", "Type", "Risk Score", "Roles"]
            rows = [header]
            sorted_actors = sorted(actors, key=lambda a: a.get("risk_score", 0), reverse=True)
            for a in sorted_actors[:15]:
                roles = a.get("roles", [])
                roles_str = ", ".join(roles) if isinstance(roles, list) else str(roles)
                rows.append([
                    a.get("name", "Unknown")[:25],
                    a.get("actor_type", "—"),
                    f"{a.get('risk_score', 0):.0f}",
                    roles_str[:40] or "—",
                ])
            story.append(self._styled_table(rows, [2.0*inch, 1.0*inch, 0.8*inch, 2.7*inch]))

        return story

    # ═══════════════════════════════════════════════════════════════════
    # FILING COMPLIANCE
    # ═══════════════════════════════════════════════════════════════════

    def _build_filing_compliance(self, filings: list, company: str) -> list:
        story: list = []
        story.append(Paragraph("FILING DEADLINE COMPLIANCE", self.styles["SectionTitle"]))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))

        # Filing summary table
        filing_types = Counter(f.get("filing_type", "Unknown") for f in filings)
        header = ["Filing Type", "Count"]
        rows = [header]
        for ft, count in filing_types.most_common():
            rows.append([ft, str(count)])

        story.append(self._styled_table(rows, [3.2*inch, 2.0*inch]))

        return story

    # ═══════════════════════════════════════════════════════════════════
    # PENALTY ESTIMATES
    # ═══════════════════════════════════════════════════════════════════

    def _build_penalty_estimates(self, results: Dict) -> list:
        story: list = []
        story.append(Paragraph("ESTIMATED PENALTIES & LEGAL EXPOSURE", self.styles["SectionTitle"]))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))

        penalties = results.get("estimated_penalties", {})
        routing = results.get("regulatory_routing", {})

        data = [
            ["Penalty Category", "Minimum", "Maximum"],
            ["Civil Monetary Penalties",
             f"${penalties.get('civil_minimum', 0):,.0f}",
             f"${penalties.get('civil_maximum', 0):,.0f}"],
            ["Disgorgement (Estimated)", "N/A",
             f"${penalties.get('disgorgement', 0):,.0f}"],
            ["Criminal Exposure",
             "Possible" if penalties.get("criminal_exposure") else "No",
             f"{penalties.get('prison_years_maximum', 0)} years max"],
        ]
        tbl = self._styled_table(data, [2.8*inch, 1.6*inch, 1.6*inch])
        story.append(tbl)
        story.append(Spacer(1, 14))

        # Regulatory routing
        if routing:
            story.append(Paragraph("Regulatory Routing", self.styles["SubSection"]))
            route_data = [["Agency / Division", "Priority"]]
            agencies = routing.get("agencies", [])
            if isinstance(agencies, list):
                for agency in agencies:
                    if isinstance(agency, dict):
                        route_data.append([
                            agency.get("name", "Unknown"),
                            agency.get("priority", "Normal"),
                        ])
                    elif isinstance(agency, str):
                        route_data.append([agency, "Flagged"])
            if len(route_data) > 1:
                story.append(self._styled_table(route_data, [4.0*inch, 2.0*inch]))

        return story

    # ═══════════════════════════════════════════════════════════════════
    # EVIDENCE CHAIN
    # ═══════════════════════════════════════════════════════════════════

    def _build_evidence_chain(self, case_id: str, results: Dict) -> list:
        story: list = []
        story.append(Paragraph("EVIDENCE CHAIN & DIGITAL SIGNATURES", self.styles["SectionTitle"]))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))

        report_hash = hashlib.sha256(
            f"{case_id}{datetime.now().isoformat()}".encode()
        ).hexdigest()

        story.append(Paragraph(
            "All evidence has been cryptographically hashed using SHA-256 + SHA3-512 + "
            "BLAKE2b triple-hash integrity to ensure tamper-evident chain of custody. "
            "This report is digitally fingerprinted for court admissibility.",
            self.styles["BodyText2"],
        ))
        story.append(Spacer(1, 10))

        chain = results.get("evidence_chain", [])
        if chain:
            header = ["Evidence ID", "Description", "SHA-256 Hash"]
            rows = [header]
            for i, item in enumerate(chain[:20]):
                desc = item.get("description", "")
                if len(desc) > 40:
                    desc = desc[:37] + "..."
                rows.append([
                    item.get("item_id", f"EV-{i+1:04d}"),
                    desc,
                    (item.get("sha256_hash", "N/A")[:32] + "..."),
                ])
            story.append(self._styled_table(rows, [0.9*inch, 2.5*inch, 3.0*inch], font_size=7))
            story.append(Spacer(1, 12))

        story.append(Paragraph("<b>Report Hash (SHA-256):</b>", self.styles["BodyText2"]))
        story.append(Paragraph(report_hash, self.styles["MonoSmall"]))
        story.append(Spacer(1, 12))

        # Signature block
        story.append(self._accent_bar())
        story.append(Paragraph(
            "This report was generated by the JLAW Forensic Analysis System v4.2. "
            "All findings are based on publicly available SEC filings and open-source intelligence. "
            "This document is tamper-evident and digitally fingerprinted.",
            ParagraphStyle("sig", parent=self.styles["SmallBody"],
                           alignment=TA_CENTER, fontSize=8,
                           textColor=colors.HexColor(BRAND_GRAY)),
        ))
        story.append(self._accent_bar())

        return story

    # ═══════════════════════════════════════════════════════════════════
    # CHART GENERATORS
    # ═══════════════════════════════════════════════════════════════════

    def _generate_severity_donut(self, results: Dict) -> Optional[BytesIO]:
        """Severity distribution donut chart."""
        violations = results.get("violations", [])
        if not violations:
            return None

        counts: Dict[str, int] = Counter()
        for v in violations:
            sev = self._normalize_severity(v.get("severity", v.get("risk_level", "LOW")))
            counts[sev] += 1

        labels, sizes, chart_colors = [], [], []
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if counts.get(sev, 0) > 0:
                labels.append(f"{sev}\n({counts[sev]})")
                sizes.append(counts[sev])
                chart_colors.append(SEV_COLORS.get(sev, "#888"))

        if not sizes:
            return None

        fig, ax = plt.subplots(figsize=(5.5, 3.5))
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=chart_colors, autopct="%1.1f%%",
            startangle=90, pctdistance=0.75,
            wedgeprops={"linewidth": 2, "edgecolor": "white", "width": 0.4},
        )
        for t in autotexts:
            t.set_fontsize(9)
            t.set_fontweight("bold")
        for t in texts:
            t.set_fontsize(9)
        ax.set_title("Violation Severity Distribution", fontsize=13, fontweight="bold",
                      color=BRAND_NAVY, pad=15)
        plt.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return buf

    def _generate_contradiction_chart(
        self, contradictions: list, company: str,
    ) -> Optional[BytesIO]:
        """Bar chart of contradiction types and severities."""
        if not contradictions:
            return None

        types = Counter(c.get("contradiction_type", "unknown") for c in contradictions)
        labels = [t.replace("_", " ").title() for t in types.keys()]
        values = list(types.values())
        bar_colors = [CONTRADICTION_COLORS.get(t, "#888") for t in types.keys()]

        fig, ax = plt.subplots(figsize=(7, 3.5))
        y_pos = np.arange(len(labels))
        bars = ax.barh(y_pos, values, color=bar_colors, edgecolor="white", linewidth=0.5)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel("Count", fontsize=10)
        ax.set_title(f"{company} — Contradiction Types Detected",
                      fontsize=12, fontweight="bold", color=BRAND_NAVY)
        ax.invert_yaxis()
        ax.grid(True, axis="x", alpha=0.3)

        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                    str(val), va="center", fontsize=9, fontweight="bold")

        plt.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return buf

    def _generate_timeline_chart(
        self, transactions: list, events: list, company: str,
    ) -> Optional[BytesIO]:
        """Transaction timeline scatter plot."""
        if not transactions:
            return None

        risk_colors = {
            "CRITICAL": SEV_CRITICAL, "HIGH": SEV_HIGH,
            "MEDIUM": SEV_MEDIUM, "LOW": SEV_LOW,
        }

        fig, ax = plt.subplots(figsize=(9, 4))

        for txn in transactions:
            txn_date = txn.get("date", date.today())
            value = abs(txn.get("value", 0))
            risk = txn.get("risk_level", "LOW")
            c = risk_colors.get(risk, "#888888")
            size = max(15, min(200, value / 10000))
            ax.scatter(txn_date, value, s=size, c=c, alpha=0.7,
                       edgecolors="white", linewidth=0.8)

        for evt in (events or []):
            evt_date = evt.get("date")
            if evt_date:
                ax.axvline(x=evt_date, color="#7FDBFF", linestyle="--", linewidth=1, alpha=0.7)

        ax.set_xlabel("Date", fontsize=10)
        ax.set_ylabel("Transaction Value ($)", fontsize=10)
        ax.set_title(f"{company} — Insider Transaction Timeline",
                      fontsize=12, fontweight="bold", color=BRAND_NAVY)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

        for level, c in risk_colors.items():
            ax.scatter([], [], c=c, s=40, label=level, edgecolors="white")
        ax.legend(title="Risk Level", loc="upper left", fontsize=8, title_fontsize=9)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return buf

    def _generate_profit_waterfall(
        self, beneficiaries: list, company: str,
    ) -> Optional[BytesIO]:
        """Beneficiary profit horizontal bar chart."""
        if not beneficiaries:
            return None

        names = [b.get("name", "Unknown")[:20] for b in beneficiaries]
        profits = [b.get("total_profit", 0) for b in beneficiaries]
        risk_scores = [b.get("risk_score", 0) for b in beneficiaries]

        bar_colors = []
        for rs in risk_scores:
            if rs >= 80:
                bar_colors.append(SEV_CRITICAL)
            elif rs >= 60:
                bar_colors.append(SEV_HIGH)
            elif rs >= 40:
                bar_colors.append(SEV_MEDIUM)
            else:
                bar_colors.append(SEV_LOW)

        fig, ax = plt.subplots(figsize=(8, max(3, len(names) * 0.4)))
        y_pos = np.arange(len(names))
        bars = ax.barh(y_pos, profits, color=bar_colors, edgecolor="white", linewidth=0.5)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names, fontsize=8)
        ax.set_xlabel("Estimated Profit ($)", fontsize=10)
        ax.set_title(f"{company} — Beneficiary Profit Analysis",
                      fontsize=12, fontweight="bold", color=BRAND_NAVY)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax.invert_yaxis()
        ax.grid(True, axis="x", alpha=0.3)
        plt.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return buf

    def _generate_role_distribution(
        self, beneficiaries: list, company: str,
    ) -> Optional[BytesIO]:
        """Role-based profit distribution pie chart."""
        if not beneficiaries:
            return None

        role_profits: Dict[str, float] = {}
        for b in beneficiaries:
            role = b.get("role", "Other")
            role_profits[role] = role_profits.get(role, 0) + b.get("total_profit", 0)

        if not role_profits:
            return None

        roles = list(role_profits.keys())
        values = list(role_profits.values())
        role_colors = {
            "CEO": SEV_CRITICAL, "CFO": SEV_HIGH, "COO": "#FF8C00",
            "Director": "#4169E1", "VP": "#9370DB", "Officer": "#20B2AA",
            "10% Owner": "#CD853F", "Other": "#778899",
        }
        chart_colors = [role_colors.get(r, "#778899") for r in roles]

        fig, ax = plt.subplots(figsize=(5, 3.5))
        ax.pie(values, labels=roles, colors=chart_colors, autopct="%1.1f%%",
               startangle=90, wedgeprops={"linewidth": 2, "edgecolor": "white"})
        ax.set_title("Profit by Executive Role", fontsize=12, fontweight="bold", color=BRAND_NAVY)
        plt.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return buf

    def _generate_network_chart(
        self, actors: list, relationships: list, company: str,
    ) -> Optional[BytesIO]:
        """Actor network graph visualization."""
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
            src = rel.get("source", "")
            tgt = rel.get("target", "")
            if src and tgt:
                G.add_edge(src, tgt)

        if not G.nodes():
            return None

        pos = nx.spring_layout(G, k=0.8, iterations=50, seed=42)
        fig, ax = plt.subplots(figsize=(8, 5))

        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3, edge_color="#888888")

        node_colors, node_sizes = [], []
        for node in G.nodes():
            rs = G.nodes[node].get("risk_score", 0)
            if rs >= 80:
                node_colors.append(SEV_CRITICAL)
            elif rs >= 60:
                node_colors.append(SEV_HIGH)
            elif rs >= 40:
                node_colors.append(SEV_MEDIUM)
            else:
                node_colors.append(SEV_LOW)
            node_sizes.append(200 + len(list(G.neighbors(node))) * 80)

        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                                node_size=node_sizes, edgecolors="white", linewidths=1.5)
        labels = {n: G.nodes[n].get("name", n)[:15] for n in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=7)
        ax.set_title(f"{company} — Filing Party Network",
                      fontsize=12, fontweight="bold", color=BRAND_NAVY)
        ax.axis("off")
        plt.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return buf

    # ═══════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════

    def _styled_table(
        self, rows: list, col_widths: list,
        color_col: int = -1, font_size: int = 9,
    ) -> Table:
        """Build a professionally styled table."""
        tbl = Table(rows, colWidths=col_widths)
        style_cmds = [
            ("FONT", (0, 0), (-1, 0), self.TITLE_FONT, font_size + 1),
            ("FONT", (0, 1), (-1, -1), self.BODY_FONT, font_size),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
        ]

        # Color-code severity column
        if color_col >= 0:
            for i in range(1, len(rows)):
                cell_val = rows[i][color_col] if color_col < len(rows[i]) else ""
                sev_color = SEV_COLORS.get(cell_val, None)
                if sev_color:
                    style_cmds.append(("BACKGROUND", (color_col, i), (color_col, i),
                                       colors.HexColor(sev_color)))
                    style_cmds.append(("TEXTCOLOR", (color_col, i), (color_col, i), colors.white))
                    style_cmds.append(("FONT", (color_col, i), (color_col, i),
                                       self.TITLE_FONT, font_size))

        tbl.setStyle(TableStyle(style_cmds))
        return tbl

    def _accent_bar(self) -> HRFlowable:
        return HRFlowable(
            width="100%", thickness=3, color=colors.HexColor(BRAND_ACCENT),
            spaceAfter=8, spaceBefore=8,
        )

    def _section_bar(self) -> HRFlowable:
        return HRFlowable(
            width="100%", thickness=2, color=colors.HexColor(BRAND_ACCENT),
            spaceAfter=10, spaceBefore=2,
        )

    @staticmethod
    def _normalize_severity(sev) -> str:
        if isinstance(sev, (int, float)):
            if sev >= 8:
                return "CRITICAL"
            elif sev >= 6:
                return "HIGH"
            elif sev >= 4:
                return "MEDIUM"
            return "LOW"
        return str(sev).upper() if sev else "LOW"

    def _save_standalone_chart(self, chart_buf: Optional[BytesIO], filename: str) -> Optional[Path]:
        """Save a chart buffer as a standalone PNG file."""
        if not chart_buf:
            return None
        path = self.chart_dir / filename
        with open(path, "wb") as f:
            f.write(chart_buf.getvalue())
        chart_buf.seek(0)  # Reset for PDF embedding
        logger.info(f"Standalone chart saved: {path}")
        return path

    def _draw_page(self, canvas_obj, doc):
        """Page header/footer with branding."""
        canvas_obj.saveState()
        # Header line
        canvas_obj.setStrokeColor(colors.HexColor(BRAND_ACCENT))
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(48, letter[1] - 36, letter[0] - 48, letter[1] - 36)
        # Header text
        canvas_obj.setFont(self.BODY_FONT, 7)
        canvas_obj.setFillColor(colors.HexColor(BRAND_GRAY))
        canvas_obj.drawString(48, letter[1] - 32, "JLAW FORENSIC ANALYSIS SYSTEM — CONFIDENTIAL")
        canvas_obj.drawRightString(letter[0] - 48, letter[1] - 32,
                                    datetime.now().strftime("%Y-%m-%d"))
        # Footer
        canvas_obj.setFont(self.BODY_FONT, 8)
        canvas_obj.setFillColor(colors.HexColor(BRAND_GRAY))
        canvas_obj.drawCentredString(
            letter[0] / 2, 28,
            f"Page {doc.page} — CONFIDENTIAL — LAW ENFORCEMENT SENSITIVE",
        )
        canvas_obj.restoreState()
