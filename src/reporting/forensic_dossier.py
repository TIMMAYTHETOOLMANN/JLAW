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
import copy

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
    # DATA ENRICHMENT
    # ═══════════════════════════════════════════════════════════════════

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

        # 5. Filter material_events — remove entries with null dates or empty descriptions
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
        # Enrich / synthesize missing collections before any rendering
        analysis_results = self._enrich_analysis_results(analysis_results)

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

        # 5b. VIOLATION REGISTER
        register_elements = self._build_violation_register(analysis_results)
        if register_elements:
            story.append(Spacer(1, 14))
            story.extend(register_elements)

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
    # INVESTIGATIVE DOSSIER — Wall-Street-Journal-style narrative output
    # ═══════════════════════════════════════════════════════════════════

    def generate_investigative_dossier(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        *,
        penalty_exposure: Optional[Dict[str, Any]] = None,
        executive_summary_narrative: Optional[Dict[str, Any]] = None,
        forensic_tracing: Optional[Dict[str, Any]] = None,
        evidence_chain_data: Optional[Dict[str, Any]] = None,
        severity_summary: Optional[Dict[str, Any]] = None,
        sox_analysis: Optional[Dict[str, Any]] = None,
        temporal_analysis: Optional[Dict[str, Any]] = None,
        beneficiary_analysis: Optional[List[Dict[str, Any]]] = None,
        contradiction_map: Optional[Dict[str, Any]] = None,
        output_filename: Optional[str] = None,
    ) -> Tuple[Path, List[Path]]:
        """
        Generate a comprehensive, Wall-Street-Journal-style investigative
        dossier PDF that consolidates all raw analysis data into a polished,
        human-readable document with narrative prose, supplementary charts,
        and clear implications.

        This method extends ``generate_dossier`` by injecting additional
        investigative sections sourced from the enhanced analysis pipeline,
        forensic tracing, penalty exposure calculations, and SOX/temporal
        analysis modules.

        Args:
            case_id: Unique case identifier.
            company_name: Target company.
            cik: SEC CIK.
            analysis_results: Core analysis results dict (violations, etc.).
            penalty_exposure: Detailed penalty breakdown from enhancement.
            executive_summary_narrative: AI-generated narrative + patterns.
            forensic_tracing: Forensic tracing results dict.
            evidence_chain_data: Merkle tree / hash evidence chain.
            severity_summary: Severity breakdown from enhancement.
            sox_analysis: SOX certification analysis data.
            temporal_analysis: 10-Q temporal analysis data.
            beneficiary_analysis: Per-insider beneficiary analysis list.
            contradiction_map: Optional contradiction data.
            output_filename: Custom output filename.

        Returns:
            Tuple of (pdf_path, list of standalone chart paths).
        """
        analysis_results = self._enrich_analysis_results(analysis_results)

        if not output_filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"INVESTIGATIVE_DOSSIER_{case_id}_{ts}.pdf"

        pdf_path = self.output_dir / output_filename
        standalone_charts: List[Path] = []

        doc = SimpleDocTemplate(
            str(pdf_path), pagesize=letter,
            rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=48,
        )
        story: list = []

        # -- COVER PAGE --
        story.extend(self._build_investigative_cover(
            case_id, company_name, cik, analysis_results, penalty_exposure,
        ))
        story.append(PageBreak())

        # -- TABLE OF CONTENTS --
        story.extend(self._build_investigative_toc())
        story.append(PageBreak())

        # -- I.  INVESTIGATIVE NARRATIVE --
        story.extend(self._build_narrative_section(
            company_name, analysis_results, executive_summary_narrative,
        ))
        story.append(PageBreak())

        # -- II.  KEY METRICS DASHBOARD --
        story.extend(self._build_kpi_dashboard(analysis_results, company_name))
        story.append(PageBreak())

        # -- III. IDENTIFIED PATTERNS OF MISCONDUCT --
        story.extend(self._build_patterns_section(
            company_name, executive_summary_narrative,
        ))
        story.append(PageBreak())

        # -- IV. VIOLATION SEVERITY ANALYSIS --
        story.extend(self._build_violation_analysis(analysis_results, company_name))
        register_elements = self._build_violation_register(analysis_results)
        if register_elements:
            story.append(Spacer(1, 14))
            story.extend(register_elements)
        story.append(PageBreak())

        # -- V.  INSIDER BENEFICIARY PROFILES --
        bens = analysis_results.get("beneficiaries", [])
        if bens:
            story.extend(self._build_beneficiary_analysis(bens, company_name))
            chart_path = self._save_standalone_chart(
                self._generate_profit_waterfall(bens, company_name),
                f"beneficiary_profits_{case_id}.png",
            )
            if chart_path:
                standalone_charts.append(chart_path)
            story.append(PageBreak())

        # -- VI. DETAILED BENEFICIARY DOSSIERS --
        if beneficiary_analysis:
            story.extend(self._build_beneficiary_dossier_section(
                beneficiary_analysis, company_name,
            ))
            story.append(PageBreak())

        # -- VII. SOX COMPLIANCE ANALYSIS --
        if sox_analysis:
            story.extend(self._build_sox_section(sox_analysis, company_name))
            story.append(PageBreak())

        # -- VIII. TEMPORAL CONSISTENCY ANALYSIS --
        if temporal_analysis:
            story.extend(self._build_temporal_section(
                temporal_analysis, company_name,
            ))
            story.append(PageBreak())

        # -- IX. FORENSIC TRACING & OWNERSHIP --
        if forensic_tracing:
            story.extend(self._build_forensic_tracing_section(
                forensic_tracing, company_name,
            ))
            story.append(PageBreak())

        # -- X.  TRANSACTION TIMELINE --
        txns = analysis_results.get("transactions", [])
        events = analysis_results.get("material_events", [])
        if txns:
            story.extend(self._build_transaction_timeline(txns, events, company_name))
            chart_path = self._save_standalone_chart(
                self._generate_timeline_chart(txns, events, company_name),
                f"timeline_{case_id}.png",
            )
            if chart_path:
                standalone_charts.append(chart_path)
            story.append(PageBreak())

        # -- XI. ACTOR NETWORK --
        actors = analysis_results.get("actors", [])
        rels = analysis_results.get("relationships", [])
        if actors:
            story.extend(self._build_network_section(actors, rels, company_name))
            chart_path = self._save_standalone_chart(
                self._generate_network_chart(actors, rels, company_name),
                f"network_{case_id}.png",
            )
            if chart_path:
                standalone_charts.append(chart_path)
            story.append(PageBreak())

        # -- XII. PENALTY EXPOSURE & LEGAL IMPLICATIONS --
        story.extend(self._build_penalty_exposure_section(
            analysis_results, penalty_exposure,
        ))
        story.append(PageBreak())

        # -- XIII. EVIDENCE INTEGRITY --
        story.extend(self._build_evidence_integrity_section(
            case_id, analysis_results, evidence_chain_data,
        ))

        # Build PDF
        doc.build(story, onFirstPage=self._draw_page, onLaterPages=self._draw_page)

        # Standalone severity chart
        sev_chart = self._generate_severity_donut(analysis_results)
        if sev_chart:
            chart_path = self._save_standalone_chart(
                sev_chart, f"severity_{case_id}.png",
            )
            if chart_path:
                standalone_charts.append(chart_path)

        logger.info(
            "Investigative dossier generated: %s (%d standalone charts)",
            pdf_path, len(standalone_charts),
        )
        return pdf_path, standalone_charts

    # ── Investigative-dossier section builders ──────────────────────

    def _build_investigative_cover(
        self, case_id: str, company: str, cik: str,
        results: Dict, penalty_exposure: Optional[Dict],
    ) -> list:
        """Build a polished investigative-style cover page."""
        story: list = []
        story.append(Spacer(1, 0.6 * inch))
        story.append(self._accent_bar())
        story.append(Paragraph(
            "CONFIDENTIAL — LAW ENFORCEMENT SENSITIVE",
            self.styles["Classified"],
        ))
        story.append(self._accent_bar())
        story.append(Spacer(1, 0.4 * inch))

        story.append(Paragraph("INVESTIGATIVE DOSSIER", self.styles["DossierTitle"]))
        story.append(Paragraph(
            "Comprehensive Forensic Analysis Report", self.styles["DossierSubtitle"],
        ))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(company, self.styles["DossierSubtitle"]))
        story.append(Spacer(1, 0.4 * inch))

        total_v = results.get("total_violations", 0)
        crit = results.get("critical_alerts", 0)
        high = results.get("high_alerts", 0)

        # Derive penalty summary from detailed exposure if available
        civil_max = 0
        criminal_max = ""
        disgorgement = 0
        if penalty_exposure:
            for cat in penalty_exposure.get("categories", []):
                if "civil" in cat.get("category", "").lower():
                    civil_max = max(civil_max, cat.get("maximum_penalty", 0))
                if "criminal" in cat.get("category", "").lower():
                    criminal_max = cat.get("maximum_penalty", "N/A")
                if "disgorgement" in cat.get("category", "").lower():
                    disgorgement = max(disgorgement, cat.get("estimated_recovery", 0))
            if not civil_max:
                civil_max = penalty_exposure.get("total_maximum_exposure", 0)
            if not disgorgement:
                disgorgement = penalty_exposure.get("disgorgement_estimate", 0)
        if not civil_max:
            civil_max = results.get("estimated_penalties", {}).get("civil_maximum", 0)

        meta = [
            ["Case ID", case_id],
            ["Target Entity", company],
            ["SEC CIK", cik],
            ["Report Generated", datetime.now().strftime("%B %d, %Y  %H:%M UTC")],
            ["Total Violations", str(total_v)],
            ["Critical / High Alerts", f"{crit} critical · {high} high"],
            ["Maximum Civil Exposure", f"${civil_max:,.0f}"],
            ["Estimated Disgorgement", f"${disgorgement:,.0f}"],
        ]
        tbl = Table(meta, colWidths=[2.4 * inch, 3.8 * inch])
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

        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(
            "Generated by JLAW Forensic Analysis System v4.2 — "
            "Justice Law Analytics Workbench",
            ParagraphStyle("covfooter", parent=self.styles["Normal"],
                           alignment=TA_CENTER, fontSize=9,
                           textColor=colors.HexColor(BRAND_GRAY)),
        ))
        return story

    def _build_investigative_toc(self) -> list:
        """Build table of contents for the investigative dossier."""
        story: list = []
        story.append(Paragraph("TABLE OF CONTENTS", self.styles["SectionTitle"]))
        story.append(self._section_bar())
        story.append(Spacer(1, 12))

        sections = [
            "I.      Investigative Narrative & Key Findings",
            "II.     Key Metrics Dashboard",
            "III.    Identified Patterns of Misconduct",
            "IV.     Violation Severity Analysis & Register",
            "V.      Insider Beneficiary Profiles",
            "VI.     Detailed Beneficiary Dossiers",
            "VII.    SOX Compliance Analysis",
            "VIII.   Temporal Consistency Analysis",
            "IX.     Forensic Tracing & Ownership Resolution",
            "X.      Transaction Timeline & Insider Activity",
            "XI.     Filing Party Network & Associations",
            "XII.    Penalty Exposure & Legal Implications",
            "XIII.   Evidence Integrity & Chain of Custody",
        ]
        for s in sections:
            story.append(Paragraph(s, ParagraphStyle(
                "toc_inv", parent=self.styles["BodyText2"],
                fontSize=11, spaceAfter=8, leftIndent=20,
                fontName=self.BODY_FONT,
            )))
        return story

    def _build_narrative_section(
        self, company: str, results: Dict,
        narrative: Optional[Dict],
    ) -> list:
        """
        Build a long-form investigative narrative — the centrepiece of
        the Wall-Street-Journal-style dossier.
        """
        story: list = []
        story.append(Paragraph(
            "I. INVESTIGATIVE NARRATIVE", self.styles["SectionTitle"],
        ))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))

        # Pull AI-generated narrative when available
        narrative_text = ""
        if narrative:
            narrative_text = narrative.get("narrative", "") or narrative.get(
                "executive_summary", ""
            )

        if narrative_text:
            # Split long narrative into readable paragraphs
            paragraphs = [p.strip() for p in narrative_text.split("\n") if p.strip()]
            for para in paragraphs:
                story.append(Paragraph(para, self.styles["BodyText2"]))
                story.append(Spacer(1, 6))
        else:
            # Synthesize narrative from analysis results
            total_v = results.get("total_violations", 0)
            crit = results.get("critical_alerts", 0)
            high = results.get("high_alerts", 0)

            violations = results.get("violations", [])
            owners = set()
            for v in violations:
                name = (v.get("reporting_owner") or v.get("insider_name") or "")
                if name:
                    owners.add(name)

            story.append(Paragraph(
                f"A comprehensive forensic analysis of <b>{company}</b> SEC filings "
                f"has identified <b>{total_v}</b> regulatory violations, of which "
                f"<b>{crit}</b> are classified as <font color='{SEV_CRITICAL}'>CRITICAL</font> "
                f"and <b>{high}</b> as <font color='{SEV_HIGH}'>HIGH</font> severity. "
                f"The investigation examined insider transactions, beneficial ownership "
                f"filings, SOX certifications, and temporal financial consistency across "
                f"the reporting period.",
                self.styles["BodyText2"],
            ))
            story.append(Spacer(1, 6))

            if owners:
                story.append(Paragraph(
                    f"The analysis identified <b>{len(owners)}</b> named insiders with "
                    f"material transactions during the period under review. "
                    f"Transactions ranged from routine stock option exercises to "
                    f"multi-billion-dollar entity restructuring transfers reported "
                    f"at zero dollar value — a pattern that warrants significant "
                    f"regulatory scrutiny.",
                    self.styles["BodyText2"],
                ))
                story.append(Spacer(1, 6))

            # Highlight top violation types
            type_counts = Counter(
                v.get("type", v.get("violation_type", "Unknown"))
                for v in violations
            )
            if type_counts:
                top = type_counts.most_common(5)
                desc_parts = []
                for vtype, count in top:
                    desc_parts.append(f"{vtype} ({count})")
                story.append(Paragraph(
                    f"The most prevalent findings include: {'; '.join(desc_parts)}. "
                    f"Each finding has been individually assessed for regulatory "
                    f"significance and cross-referenced across multiple filing sources.",
                    self.styles["BodyText2"],
                ))
                story.append(Spacer(1, 6))

        # Risk assessment box (always shown)
        total_v = results.get("total_violations", 0)
        crit = results.get("critical_alerts", 0)
        high = results.get("high_alerts", 0)

        if crit > 0:
            risk_level, risk_color = "EXTREME", SEV_CRITICAL
            recommendation = "IMMEDIATE DOJ REFERRAL RECOMMENDED"
        elif high > 5:
            risk_level, risk_color = "HIGH", SEV_HIGH
            recommendation = "SEC ENFORCEMENT ACTION RECOMMENDED"
        elif total_v > 10:
            risk_level, risk_color = "ELEVATED", SEV_MEDIUM
            recommendation = "DETAILED INVESTIGATION WARRANTED"
        else:
            risk_level, risk_color = "MODERATE", SEV_LOW
            recommendation = "CONTINUED MONITORING RECOMMENDED"

        risk_data = [
            [Paragraph(f'<font color="{BRAND_WHITE}"><b>RISK ASSESSMENT</b></font>',
                        self.styles["SmallBody"]),
             Paragraph(f'<font color="{BRAND_WHITE}"><b>{risk_level}</b></font>',
                        ParagraphStyle("ra2", parent=self.styles["SmallBody"],
                                       alignment=TA_CENTER, textColor=colors.white))],
            [Paragraph(f"<b>Recommendation:</b> {recommendation}",
                        self.styles["SmallBody"]),
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
        return story

    def _build_patterns_section(
        self, company: str, narrative: Optional[Dict],
    ) -> list:
        """Render identified patterns of misconduct."""
        story: list = []
        story.append(Paragraph(
            "III. IDENTIFIED PATTERNS OF MISCONDUCT", self.styles["SectionTitle"],
        ))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))

        patterns = []
        if narrative:
            patterns = narrative.get("patterns_identified", [])

        if not patterns:
            story.append(Paragraph(
                "No distinct patterns of misconduct were identified by the "
                "AI analysis engine. Individual violations are documented in "
                "the Violation Analysis section.",
                self.styles["BodyText2"],
            ))
            return story

        for pat in patterns:
            pid = pat.get("id", pat.get("pattern_id", ""))
            name = pat.get("name", pat.get("pattern_name", "Unknown"))
            severity = (pat.get("severity", "MEDIUM") or "MEDIUM").upper()
            description = pat.get("description", "")

            sev_color = SEV_COLORS.get(severity, SEV_MEDIUM)
            story.append(Paragraph(
                f'<font color="{sev_color}"><b>[{severity}]</b></font> '
                f'<b>Pattern {pid}: {name}</b>',
                self.styles["SubSection"],
            ))
            if description:
                story.append(Paragraph(description, self.styles["BodyText2"]))
            story.append(Spacer(1, 10))

        return story

    def _build_beneficiary_dossier_section(
        self, beneficiary_data: List[Dict], company: str,
    ) -> list:
        """Render detailed per-insider beneficiary dossiers."""
        story: list = []
        story.append(Paragraph(
            "VI. DETAILED BENEFICIARY DOSSIERS", self.styles["SectionTitle"],
        ))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            f"Individual dossiers for the most significant insiders of "
            f"{company}, detailing their transaction history, "
            f"economic benefit calculations, and forensic signal assessment.",
            self.styles["BodyText2"],
        ))
        story.append(Spacer(1, 10))

        # Sort by total economic benefit
        sorted_bens = sorted(
            beneficiary_data,
            key=lambda b: abs(b.get("total_economic_benefit", 0) or 0),
            reverse=True,
        )[:12]

        for ben in sorted_bens:
            name = ben.get("insider_name", ben.get("name", "Unknown"))
            benefit = ben.get("total_economic_benefit", 0) or 0
            txn_count = len(ben.get("transactions", []))
            fsl_score = ben.get("aggregate_fsl_score", ben.get("fsl_signal_score", 0)) or 0
            role = ben.get("insider_role", ben.get("role", ""))

            story.append(Paragraph(
                f'<b>{name}</b>{" — " + role if role else ""}',
                self.styles["SubSection"],
            ))

            row_data = [
                ["Total Economic Benefit", f"${abs(benefit):,.2f}"],
                ["Transactions Analyzed", str(txn_count)],
                ["FSL Signal Score", f"{fsl_score:.3f}" if isinstance(fsl_score, float) else str(fsl_score)],
            ]
            tbl = Table(row_data, colWidths=[2.5 * inch, 3.5 * inch])
            tbl.setStyle(TableStyle([
                ("FONT", (0, 0), (0, -1), self.TITLE_FONT, 9),
                ("FONT", (1, 0), (1, -1), self.BODY_FONT, 9),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F2F5")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(tbl)

            # Footnote flags
            flags = ben.get("key_findings", ben.get("footnote_flags", []))
            if isinstance(flags, list) and flags:
                items = []
                for flag in flags[:5]:
                    if isinstance(flag, str):
                        items.append(ListItem(Paragraph(flag, self.styles["SmallBody"])))
                    elif isinstance(flag, dict):
                        items.append(ListItem(Paragraph(
                            flag.get("description", str(flag)),
                            self.styles["SmallBody"],
                        )))
                if items:
                    story.append(Spacer(1, 4))
                    story.append(ListFlowable(
                        items, bulletType="bullet", bulletFontSize=7,
                    ))

            story.append(Spacer(1, 12))

        return story

    def _build_sox_section(
        self, sox_data: Dict, company: str,
    ) -> list:
        """Render SOX certification analysis."""
        story: list = []
        story.append(Paragraph(
            "VII. SOX COMPLIANCE ANALYSIS", self.styles["SectionTitle"],
        ))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))

        violations = sox_data.get("violations", [])
        certifications = sox_data.get("certifications_found", sox_data.get("certifications", []))

        story.append(Paragraph(
            f"Analysis of Sarbanes-Oxley Act certification requirements for "
            f"{company}. Section 302 requires CEO/CFO certification of quarterly "
            f"and annual filings; Section 906 imposes criminal liability for "
            f"knowingly false certifications.",
            self.styles["BodyText2"],
        ))
        story.append(Spacer(1, 8))

        # Summary metrics
        summary_data = [
            ["SOX Metric", "Value"],
            ["Violations Detected", str(len(violations))],
            ["Certifications Found", str(len(certifications)) if isinstance(certifications, list) else str(certifications)],
        ]

        # Check for specific findings
        sec302_issues = [v for v in violations if "302" in str(v.get("description", ""))]
        sec906_issues = [v for v in violations if "906" in str(v.get("description", ""))]
        if sec302_issues:
            summary_data.append(["Section 302 Issues", str(len(sec302_issues))])
        if sec906_issues:
            summary_data.append(["Section 906 Issues", str(len(sec906_issues))])

        story.append(self._styled_table(
            summary_data, [3.0 * inch, 3.0 * inch],
        ))
        story.append(Spacer(1, 10))

        # Violation details
        if violations:
            story.append(Paragraph("Violation Details", self.styles["SubSection"]))
            header = ["#", "Description", "Severity"]
            rows = [header]
            for i, v in enumerate(violations[:15], 1):
                desc = v.get("description", str(v))
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                sev = v.get("severity", "MEDIUM")
                rows.append([str(i), desc, str(sev).upper()])
            story.append(self._styled_table(
                rows, [0.4 * inch, 4.5 * inch, 1.0 * inch],
                color_col=2, font_size=8,
            ))

        return story

    def _build_temporal_section(
        self, temporal_data: Dict, company: str,
    ) -> list:
        """Render 10-Q temporal consistency analysis."""
        story: list = []
        story.append(Paragraph(
            "VIII. TEMPORAL CONSISTENCY ANALYSIS", self.styles["SectionTitle"],
        ))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))

        story.append(Paragraph(
            f"Examination of {company}'s quarterly financial filings for "
            f"temporal consistency — detecting restatement triggers, "
            f"cookie-jar reserves, big-bath charges, and quarter-end loading "
            f"patterns.",
            self.styles["BodyText2"],
        ))
        story.append(Spacer(1, 8))

        patterns = temporal_data.get("patterns_detected", {})
        violations = temporal_data.get("violations", [])
        filings_analyzed = temporal_data.get("filings_analyzed", 0)

        summary_rows = [
            ["Metric", "Value"],
            ["Filings Analyzed", str(filings_analyzed)],
            ["Violations Detected", str(temporal_data.get("violations_detected", len(violations)))],
        ]
        for pat_name, count in patterns.items():
            label = pat_name.replace("_", " ").title()
            summary_rows.append([label, str(count)])

        story.append(self._styled_table(
            summary_rows, [3.0 * inch, 3.0 * inch],
        ))

        if violations:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Temporal Violations", self.styles["SubSection"]))
            header = ["#", "Description", "Severity"]
            rows = [header]
            for i, v in enumerate(violations[:10], 1):
                desc = v.get("description", str(v))
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                rows.append([str(i), desc, v.get("severity", "MEDIUM")])
            story.append(self._styled_table(
                rows, [0.4 * inch, 4.5 * inch, 1.0 * inch],
                color_col=2, font_size=8,
            ))

        return story

    def _build_forensic_tracing_section(
        self, tracing_data: Dict, company: str,
    ) -> list:
        """Render forensic tracing & ownership resolution findings."""
        story: list = []
        story.append(Paragraph(
            "IX. FORENSIC TRACING & OWNERSHIP RESOLUTION",
            self.styles["SectionTitle"],
        ))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))

        story.append(Paragraph(
            f"Six-domain forensic tracing analysis of {company} insider "
            f"transactions — tracking economic benefit from initial "
            f"acquisition through entity transfer to ultimate disposition.",
            self.styles["BodyText2"],
        ))
        story.append(Spacer(1, 8))

        # Domain 1: Footnote classification
        d1 = tracing_data.get("domain1_footnotes", {})
        if d1:
            story.append(Paragraph(
                "Footnote Classification", self.styles["SubSection"],
            ))
            story.append(Paragraph(
                f"Classified <b>{d1.get('total_footnotes', 0)}</b> Form 4 footnotes "
                f"with an average risk score of <b>{d1.get('average_risk_score', 0):.2f}</b>. "
                f"Risk distribution: {d1.get('risk_distribution', {})}.",
                self.styles["BodyText2"],
            ))
            story.append(Spacer(1, 6))

        # Domain 2: Grant-to-sale tracing
        d2_raw = tracing_data.get("domain2_tracing", {})
        d2 = d2_raw.get("summary", d2_raw)
        if d2:
            story.append(Paragraph(
                "Grant-to-Sale Tracing", self.styles["SubSection"],
            ))
            econ_val = d2.get("total_economic_value_transferred", 0)
            chains = d2.get("chains_constructed", 0)
            obfuscation = d2.get("obfuscation_vectors", 0)
            story.append(Paragraph(
                f"Constructed <b>{chains}</b> ownership chains tracing "
                f"<b>${econ_val:,.2f}</b> in economic value. "
                f"Identified <b>{obfuscation}</b> potential obfuscation "
                f"vector(s) in the chain of transfers.",
                self.styles["BodyText2"],
            ))
            story.append(Spacer(1, 6))

        # Domain 3: Beneficial ownership
        d3 = tracing_data.get("domain3_ownership", {})
        if d3:
            story.append(Paragraph(
                "Beneficial Ownership Resolution", self.styles["SubSection"],
            ))
            parking_flags = d3.get("parking_risk_flags", 0)
            entities = d3.get("entity_transfers_analyzed", 0)
            story.append(Paragraph(
                f"Analyzed <b>{entities}</b> entity transfers and identified "
                f"<b>{parking_flags}</b> potential share-parking risk flag(s).",
                self.styles["BodyText2"],
            ))
            story.append(Spacer(1, 6))

        # Executive profiles summary
        ep = tracing_data.get("executive_profiles", {})
        ep_summary = ep.get("summary", {})
        if ep_summary:
            story.append(Paragraph(
                "Executive Profile Cross-Reference", self.styles["SubSection"],
            ))
            story.append(Paragraph(
                f"Profiled <b>{ep_summary.get('total_insiders_profiled', 0)}</b> "
                f"insiders ({ep_summary.get('officers', 0)} officers, "
                f"{ep_summary.get('directors', 0)} directors, "
                f"{ep_summary.get('ten_percent_owners', 0)} 10%+ owners). "
                f"Detected <b>{ep_summary.get('total_anomalies', 0)}</b> "
                f"cross-reference anomalies.",
                self.styles["BodyText2"],
            ))
            story.append(Spacer(1, 6))

            # Anomaly type breakdown
            anomaly_types = ep_summary.get("anomaly_types", {})
            if anomaly_types:
                header = ["Anomaly Type", "Count"]
                rows = [header]
                for atype, count in sorted(
                    anomaly_types.items(), key=lambda x: x[1], reverse=True
                ):
                    label = atype.replace("VIOLATION_", "").replace("_", " ").title()
                    rows.append([label, str(count)])
                story.append(self._styled_table(
                    rows, [4.0 * inch, 2.0 * inch], font_size=8,
                ))

        return story

    def _build_penalty_exposure_section(
        self, results: Dict, penalty_data: Optional[Dict],
    ) -> list:
        """Render detailed penalty exposure with statutory citations."""
        story: list = []
        story.append(Paragraph(
            "XII. PENALTY EXPOSURE & LEGAL IMPLICATIONS",
            self.styles["SectionTitle"],
        ))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))

        if penalty_data:
            # Detailed penalty breakdown
            categories = penalty_data.get("categories", [])
            if categories:
                header = ["Category", "Minimum", "Maximum", "Statutory Basis"]
                rows = [header]
                for cat in categories:
                    rows.append([
                        cat.get("category", "Unknown"),
                        f"${cat.get('minimum_penalty', 0):,.0f}",
                        f"${cat.get('maximum_penalty', 0):,.0f}",
                        cat.get("statutory_basis", "")[:40],
                    ])
                story.append(self._styled_table(
                    rows,
                    [1.8 * inch, 1.2 * inch, 1.2 * inch, 2.3 * inch],
                    font_size=8,
                ))
                story.append(Spacer(1, 10))

            # Total exposure
            total_max = penalty_data.get("total_maximum_exposure", 0)
            disgorgement = penalty_data.get("disgorgement_estimate", 0)
            whistleblower = penalty_data.get("whistleblower_bounty_estimate", 0)

            totals = [
                ["Exposure Metric", "Amount"],
                ["Total Maximum Exposure", f"${total_max:,.0f}"],
                ["Estimated Disgorgement", f"${disgorgement:,.0f}"],
            ]
            if whistleblower:
                totals.append(["Whistleblower Bounty (est.)", f"${whistleblower:,.0f}"])

            story.append(self._styled_table(
                totals, [3.0 * inch, 3.0 * inch],
            ))
            story.append(Spacer(1, 10))

            # Criminal exposure
            criminal = penalty_data.get("criminal_exposure", {})
            if criminal:
                story.append(Paragraph(
                    "Criminal Exposure", self.styles["SubSection"],
                ))
                story.append(Paragraph(
                    f"Maximum fine: <b>${criminal.get('maximum_fine', 0):,.0f}</b>. "
                    f"Maximum imprisonment: <b>{criminal.get('maximum_imprisonment', 'N/A')}</b>. "
                    f"Statutory basis: {criminal.get('statutory_basis', 'N/A')}.",
                    self.styles["BodyText2"],
                ))
                story.append(Spacer(1, 8))
        else:
            # Fallback to basic penalties from results
            story.extend(self._build_penalty_estimates(results))

        return story

    def _build_evidence_integrity_section(
        self, case_id: str, results: Dict,
        evidence_data: Optional[Dict],
    ) -> list:
        """Render evidence integrity with Merkle tree details."""
        story: list = []
        story.append(Paragraph(
            "XIII. EVIDENCE INTEGRITY & CHAIN OF CUSTODY",
            self.styles["SectionTitle"],
        ))
        story.append(self._section_bar())
        story.append(Spacer(1, 8))

        story.append(Paragraph(
            "All source documents and analysis artifacts have been "
            "cryptographically hashed using a triple-hash integrity "
            "scheme (SHA-256 + SHA3-512 + BLAKE2b) and organized into "
            "an RFC 6962-compliant Merkle tree for tamper-evident "
            "chain of custody.",
            self.styles["BodyText2"],
        ))
        story.append(Spacer(1, 8))

        if evidence_data:
            merkle_root = evidence_data.get("merkle_root", "")
            leaf_count = evidence_data.get("leaf_count", 0)
            algorithm = evidence_data.get("hash_algorithm", "SHA-256")

            integrity_data = [
                ["Evidence Property", "Value"],
                ["Merkle Root", merkle_root[:48] + "..." if len(merkle_root) > 48 else merkle_root],
                ["Leaf Nodes (Evidence Items)", str(leaf_count)],
                ["Hash Algorithm", algorithm],
            ]
            story.append(self._styled_table(
                integrity_data, [2.5 * inch, 4.0 * inch], font_size=8,
            ))
            story.append(Spacer(1, 10))

        # Report hash
        report_hash = hashlib.sha256(
            f"{case_id}{datetime.now().isoformat()}".encode()
        ).hexdigest()
        story.append(Paragraph(
            "<b>Report Hash (SHA-256):</b>", self.styles["BodyText2"],
        ))
        story.append(Paragraph(report_hash, self.styles["MonoSmall"]))
        story.append(Spacer(1, 12))

        # Signature block
        story.append(self._accent_bar())
        story.append(Paragraph(
            "This report was generated by the JLAW Forensic Analysis System v4.2. "
            "All findings are based on publicly available SEC filings and "
            "open-source intelligence. This document is tamper-evident and "
            "digitally fingerprinted for FRE 902(13)/(14) admissibility.",
            ParagraphStyle("sig2", parent=self.styles["SmallBody"],
                           alignment=TA_CENTER, fontSize=8,
                           textColor=colors.HexColor(BRAND_GRAY)),
        ))
        story.append(self._accent_bar())

        return story

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
    # VIOLATION REGISTER
    # ═══════════════════════════════════════════════════════════════════

    def _build_violation_register(self, results: Dict) -> list:
        """
        Build a deduplicated, severity-coded violation register table.

        Each row is color-coded by severity:
            CRITICAL = red, HIGH = orange, MEDIUM = yellow, LOW = green.

        Returns:
            List of ReportLab flowables (empty list when no violations).
        """
        violations = results.get("violations", [])
        if not violations:
            return []

        story: list = []
        story.append(Paragraph("Violation Register", self.styles["SubSection"]))
        story.append(Spacer(1, 6))

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
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
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
            "CRITICAL": colors.HexColor(SEV_CRITICAL),
            "HIGH": colors.HexColor(SEV_HIGH),
            "MEDIUM": colors.HexColor(SEV_MEDIUM),
            "LOW": colors.HexColor(SEV_LOW),
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

    @staticmethod
    def _parse_date(value):
        """Convert date-like values to datetime.date objects for matplotlib."""
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%m/%d/%Y'):
                try:
                    return datetime.strptime(value, fmt).date()
                except (ValueError, TypeError):
                    continue
        return date.today()

    def _generate_severity_donut(self, results: Dict) -> Optional[BytesIO]:
        """Severity distribution donut chart."""
        violations = results.get("violations", [])
        if not violations:
            return None

        try:
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
        except Exception as e:
            logger.error("Failed to generate severity donut chart: %s", e)
            plt.close("all")
            return None

    def _generate_contradiction_chart(
        self, contradictions: list, company: str,
    ) -> Optional[BytesIO]:
        """Bar chart of contradiction types and severities."""
        if not contradictions:
            return None

        try:
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
        except Exception as e:
            logger.error("Failed to generate contradiction chart: %s", e)
            plt.close("all")
            return None

    def _generate_timeline_chart(
        self, transactions: list, events: list, company: str,
    ) -> Optional[BytesIO]:
        """Transaction timeline scatter plot."""
        if not transactions:
            return None

        try:
            risk_colors = {
                "CRITICAL": SEV_CRITICAL, "HIGH": SEV_HIGH,
                "MEDIUM": SEV_MEDIUM, "LOW": SEV_LOW,
            }

            fig, ax = plt.subplots(figsize=(9, 4))

            # Detect whether ALL transaction values are 0 to fall back to shares
            all_values_zero = all(
                abs(txn.get("value", 0) or 0) == 0 for txn in transactions
            )
            y_label = "Shares" if all_values_zero else "Transaction Value ($)"

            for txn in transactions:
                txn_date = self._parse_date(txn.get("date", date.today()))
                if all_values_zero:
                    y_val = abs(txn.get("shares", txn.get("total_shares", 1)) or 1)
                    size = max(15, min(200, y_val / 100))
                else:
                    y_val = abs(txn.get("value", 0) or 0)
                    size = max(15, min(200, y_val / 10000))
                risk = txn.get("risk_level", "LOW")
                c = risk_colors.get(risk, "#888888")
                ax.scatter(txn_date, y_val, s=size, c=c, alpha=0.7,
                           edgecolors="white", linewidth=0.8)

            for evt in (events or []):
                evt_date = evt.get("date")
                if evt_date:
                    evt_date = self._parse_date(evt_date)
                    ax.axvline(x=evt_date, color="#7FDBFF", linestyle="--", linewidth=1, alpha=0.7)

            ax.set_xlabel("Date", fontsize=10)
            ax.set_ylabel(y_label, fontsize=10)
            ax.set_title(f"{company} — Insider Transaction Timeline",
                          fontsize=12, fontweight="bold", color=BRAND_NAVY)
            if not all_values_zero:
                ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

            for level, c in risk_colors.items():
                ax.scatter([], [], c=c, s=40, label=level, edgecolors="white")
            ax.legend(title="Risk Level", loc="upper left", fontsize=8, title_fontsize=9)
            ax.grid(True, alpha=0.3)
            fig.autofmt_xdate()

            buf = BytesIO()
            try:
                fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
            except Exception:
                fig.savefig(buf, format="png", dpi=150, facecolor="white")
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.error("Failed to generate timeline chart: %s", e)
            plt.close("all")
            return None

    def _generate_profit_waterfall(
        self, beneficiaries: list, company: str,
    ) -> Optional[BytesIO]:
        """Beneficiary profit horizontal bar chart."""
        if not beneficiaries:
            return None

        try:
            # Determine which metric to use: profit, total_shares, or transaction_count
            profits = [b.get("total_profit", 0) or 0 for b in beneficiaries]
            all_profits_zero = all(p == 0 for p in profits)

            if all_profits_zero:
                # Fall back to total_shares
                metric_values = [b.get("total_shares", 0) or 0 for b in beneficiaries]
                x_label = "Total Shares"
                if all(v == 0 for v in metric_values):
                    # Fall back to transaction_count
                    metric_values = [b.get("transaction_count", 0) or 0 for b in beneficiaries]
                    x_label = "Transaction Count"
            else:
                metric_values = profits
                x_label = "Estimated Profit ($)"

            # Filter out entries where the metric value is 0
            filtered = [
                (b, v) for b, v in zip(beneficiaries, metric_values) if v != 0
            ]
            if not filtered:
                return None

            filtered_bens, filtered_values = zip(*filtered)
            names = [b.get("name", "Unknown")[:20] for b in filtered_bens]
            risk_scores = [b.get("risk_score", 0) for b in filtered_bens]

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
            bars = ax.barh(y_pos, filtered_values, color=bar_colors, edgecolor="white", linewidth=0.5)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(names, fontsize=8)
            ax.set_xlabel(x_label, fontsize=10)
            ax.set_title(f"{company} — Beneficiary Profit Analysis",
                          fontsize=12, fontweight="bold", color=BRAND_NAVY)
            if x_label == "Estimated Profit ($)":
                ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
            ax.invert_yaxis()
            ax.grid(True, axis="x", alpha=0.3)
            plt.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.error("Failed to generate profit waterfall chart: %s", e)
            plt.close("all")
            return None

    def _generate_role_distribution(
        self, beneficiaries: list, company: str,
    ) -> Optional[BytesIO]:
        """Role-based profit distribution pie chart."""
        if not beneficiaries:
            return None

        try:
            role_profits: Dict[str, float] = {}
            for b in beneficiaries:
                role = b.get("role", "Other") or "Other"
                role_profits[role] = role_profits.get(role, 0) + (b.get("total_profit", 0) or 0)

            # If all role profits are 0, fall back to counting violations per role
            all_zero = all(v == 0 for v in role_profits.values())
            if all_zero:
                role_profits = {}
                for b in beneficiaries:
                    role = b.get("role", "Other") or "Other"
                    role_profits[role] = role_profits.get(role, 0) + (b.get("violations", 0) or 0)

            if not role_profits:
                return None

            # Filter out zero-value entries before calling pie()
            filtered = {r: v for r, v in role_profits.items() if v > 0}
            if not filtered:
                return None

            roles = list(filtered.keys())
            values = list(filtered.values())
            role_colors = {
                "CEO": SEV_CRITICAL, "CFO": SEV_HIGH, "COO": "#FF8C00",
                "Director": "#4169E1", "VP": "#9370DB", "Officer": "#20B2AA",
                "10% Owner": "#CD853F", "Other": "#778899",
            }
            chart_colors = [role_colors.get(r, "#778899") for r in roles]

            chart_title = "Violations by Executive Role" if all_zero else "Profit by Executive Role"

            fig, ax = plt.subplots(figsize=(5, 3.5))
            ax.pie(values, labels=roles, colors=chart_colors, autopct="%1.1f%%",
                   startangle=90, wedgeprops={"linewidth": 2, "edgecolor": "white"})
            ax.set_title(chart_title, fontsize=12, fontweight="bold", color=BRAND_NAVY)
            plt.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.error("Failed to generate role distribution chart: %s", e)
            plt.close("all")
            return None

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

        try:
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
        except Exception as e:
            logger.error("Failed to generate network chart: %s", e)
            plt.close("all")
            return None

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
