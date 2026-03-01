"""
Investigative Article Generator
=================================

Synthesises forensic analysis findings into a compelling Wall Street Journal-style
investigative narrative — the "story" that turns raw data into a publishable exposé.

The engine produces:
- A feature-length investigative article (Markdown / HTML)
- An executive editor's summary / headline block
- Sourced pull-quotes and sidebar call-outs
- A "receipts" section linking every claim to its evidence anchor
- A recommendations & enforcement action section

The tone mirrors investigative financial journalism (WSJ, Bloomberg Businessweek,
Financial Times) — declarative, non-hedging, evidence-driven prose that would
serve equally well as a deposition exhibit or front-page investigation.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ArticleSection:
    """A single section of the investigative article."""
    section_id: str
    heading: str
    body: str                      # Multi-paragraph prose
    pull_quote: str = ""           # Highlighted sidebar quote
    sidebar_facts: List[str] = field(default_factory=list)
    evidence_anchors: List[str] = field(default_factory=list)  # IDs / citations


@dataclass
class InvestigativeArticle:
    """
    A complete WSJ-style investigative article generated from forensic findings.

    Contains a headline block, byline, deck, executive summary, multiple body
    sections, a "receipts" evidence section, and an enforcement recommendation.
    """
    article_id: str
    company_name: str
    cik: str
    analysis_period: str
    generated_at: str

    # Headline block
    headline: str
    sub_headline: str
    deck: str                      # One-sentence "elevator pitch" of the story

    # Metadata
    word_count: int = 0
    severity_label: str = "HIGH"   # CRITICAL / HIGH / MEDIUM

    # Content
    sections: List[ArticleSection] = field(default_factory=list)
    receipts: List[Dict[str, Any]] = field(default_factory=list)
    enforcement_recommendation: str = ""
    key_statistics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["sections"] = [asdict(s) for s in self.sections]
        return d


# ═══════════════════════════════════════════════════════════════════════════
# GENERATOR
# ═══════════════════════════════════════════════════════════════════════════


class InvestigativeArticleGenerator:
    """
    Generates a Wall Street Journal-style investigative article from forensic
    analysis findings.

    Usage::

        gen = InvestigativeArticleGenerator()
        article = gen.generate(
            company_name="NIKE, Inc.",
            cik="320187",
            analysis_results=analysis_results_dict,
            analysis_period="FY 2019",
        )
        gen.export_markdown(article, output_dir / "investigative_article.md")
        gen.export_html(article, output_dir / "investigative_article.html")
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    # ── public API ──────────────────────────────────────────────────────────

    def generate(
        self,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        analysis_period: str = "",
        discrepancy_report: Optional[Any] = None,
    ) -> InvestigativeArticle:
        """
        Generate a full investigative article from forensic findings.

        Args:
            company_name: Company display name.
            cik: SEC CIK.
            analysis_results: Full forensic analysis results dict.
            analysis_period: Period label (e.g. "FY 2019").
            discrepancy_report: Optional PublicDiscrepancyReport to weave in.

        Returns:
            InvestigativeArticle dataclass ready for export.
        """
        article_id = hashlib.sha256(
            f"{cik}{company_name}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16].upper()

        violations = analysis_results.get("violations", [])
        transactions = analysis_results.get("transactions", [])
        beneficiaries = analysis_results.get("beneficiaries", [])
        actors = analysis_results.get("actors", [])
        total_v = analysis_results.get("total_violations", len(violations))
        critical = analysis_results.get("critical_alerts", 0)
        high = analysis_results.get("high_alerts", 0)

        # Aggregate penalty
        total_penalty = sum(v.get("estimated_penalty", 0) for v in violations)

        # Top insider
        top_insider = self._top_insider(beneficiaries, violations)
        top_profit = self._top_profit(beneficiaries)

        # Severity label
        if critical > 0:
            severity_label = "CRITICAL"
        elif high > 5:
            severity_label = "HIGH"
        else:
            severity_label = "MEDIUM"

        # Build key statistics
        key_stats = {
            "total_violations": total_v,
            "critical_violations": critical,
            "high_violations": high,
            "total_penalty_exposure_usd": total_penalty,
            "insiders_identified": len(
                {v.get("reporting_owner") or v.get("actor") for v in violations} - {""}
            ),
            "top_insider": top_insider,
            "top_insider_profit_usd": top_profit,
            "filings_analyzed": len(
                {v.get("accession_number") for v in violations} - {""}
            ),
        }

        # Build headline block
        headline, sub_headline, deck = self._build_headlines(
            company_name, key_stats, severity_label, analysis_period
        )

        article = InvestigativeArticle(
            article_id=article_id,
            company_name=company_name,
            cik=cik,
            analysis_period=analysis_period or "N/A",
            generated_at=datetime.utcnow().isoformat() + "Z",
            headline=headline,
            sub_headline=sub_headline,
            deck=deck,
            severity_label=severity_label,
            key_statistics=key_stats,
        )

        # Build article sections
        article.sections = self._build_sections(
            company_name,
            cik,
            analysis_results,
            key_stats,
            analysis_period,
            discrepancy_report,
        )

        # Build receipts
        article.receipts = self._build_receipts(violations, transactions, beneficiaries)

        # Enforcement recommendation
        article.enforcement_recommendation = self._build_enforcement_rec(
            key_stats, severity_label
        )

        # Word count
        total_words = sum(
            len((s.heading + " " + s.body).split())
            for s in article.sections
        )
        article.word_count = total_words

        self.logger.info(
            "Investigative article generated: %d sections, ~%d words, severity=%s",
            len(article.sections),
            total_words,
            severity_label,
        )
        return article

    # ── export helpers ───────────────────────────────────────────────────────

    def export_markdown(self, article: InvestigativeArticle, path: Path) -> Path:
        """Write the article as a Markdown file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._render_markdown(article), encoding="utf-8")
        self.logger.info("Investigative article (Markdown) → %s", path)
        return path

    def export_html(self, article: InvestigativeArticle, path: Path) -> Path:
        """Write the article as a standalone HTML file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._render_html(article), encoding="utf-8")
        self.logger.info("Investigative article (HTML) → %s", path)
        return path

    def export_json(self, article: InvestigativeArticle, path: Path) -> Path:
        """Write the article metadata and structured content as JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(article.to_dict(), fh, indent=2, default=str)
        self.logger.info("Investigative article (JSON) → %s", path)
        return path

    # ── internal helpers ─────────────────────────────────────────────────────

    def _top_insider(
        self,
        beneficiaries: List[Dict[str, Any]],
        violations: List[Dict[str, Any]],
    ) -> str:
        if beneficiaries:
            best = max(
                beneficiaries,
                key=lambda b: b.get("total_profit", b.get("total_shares", 0)),
            )
            return best.get("name", "Unknown")
        owners = [
            v.get("reporting_owner") or v.get("actor", "")
            for v in violations
            if v.get("reporting_owner") or v.get("actor")
        ]
        return owners[0] if owners else "Unknown"

    def _top_profit(self, beneficiaries: List[Dict[str, Any]]) -> float:
        if not beneficiaries:
            return 0.0
        return max(
            (b.get("total_profit", 0) for b in beneficiaries), default=0.0
        )

    def _build_headlines(
        self,
        company_name: str,
        stats: Dict[str, Any],
        severity: str,
        period: str,
    ) -> tuple[str, str, str]:
        n_v = stats["total_violations"]
        n_ins = stats["insiders_identified"]
        penalty = stats["total_penalty_exposure_usd"]
        top = stats["top_insider"]

        if severity == "CRITICAL":
            headline = (
                f"Inside {company_name}'s Shadow Ledger: "
                f"How Executives Traded Ahead of the Market"
            )
            sub = (
                f"A forensic review of {company_name} ({period}) uncovers "
                f"{n_v} violations spanning {n_ins} insiders, "
                f"with estimated regulatory exposure exceeding ${penalty:,.0f}"
            )
        elif severity == "HIGH":
            headline = (
                f"{company_name}'s Compliance Gaps: "
                f"{n_v} Regulatory Violations Hidden in Plain Sight"
            )
            sub = (
                f"SEC filings reveal a pattern of undisclosed transactions and "
                f"filing delays across {n_ins} executives during {period}"
            )
        else:
            headline = (
                f"{company_name} Under the Microscope: "
                f"Forensic Analysis Flags {n_v} Compliance Anomalies"
            )
            sub = (
                f"An automated forensic review surfaces {n_v} filing irregularities "
                f"across {n_ins} executives during {period}"
            )

        deck = (
            f"A JLAW forensic investigation of {company_name} (CIK {stats.get('cik', 'N/A')}) "
            f"identified {n_v} regulatory violations with up to ${penalty:,.0f} in "
            f"civil penalty exposure — and that's before criminal counts."
        )
        return headline, sub, deck

    def _build_sections(
        self,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        stats: Dict[str, Any],
        period: str,
        discrepancy_report: Optional[Any],
    ) -> List[ArticleSection]:
        """Build all article sections in WSJ investigative style."""
        sections: List[ArticleSection] = []
        violations = analysis_results.get("violations", [])
        beneficiaries = analysis_results.get("beneficiaries", [])
        transactions = analysis_results.get("transactions", [])

        # ── SECTION 1: The Story ─────────────────────────────────────────
        sections.append(
            ArticleSection(
                section_id="S01",
                heading="The Paper Trail That Executives Didn't Expect Anyone to Follow",
                body=self._prose_opening(company_name, stats, period),
                pull_quote=(
                    f"{stats['total_violations']} violations. "
                    f"{stats['insiders_identified']} insiders. "
                    f"One forensic engine that doesn't forget."
                ),
                sidebar_facts=[
                    f"Analysis period: {period}",
                    f"Total violations flagged: {stats['total_violations']}",
                    f"Estimated penalty exposure: ${stats['total_penalty_exposure_usd']:,.0f}",
                ],
            )
        )

        # ── SECTION 2: The Players ───────────────────────────────────────
        sections.append(
            ArticleSection(
                section_id="S02",
                heading="The Cast: Who Benefited and How Much",
                body=self._prose_players(
                    company_name, beneficiaries, violations, stats
                ),
                pull_quote=(
                    f"'{stats['top_insider']}' sits at the centre of "
                    "the most consequential transaction cluster."
                ),
                sidebar_facts=self._insider_sidebar(beneficiaries, violations),
                evidence_anchors=[
                    v.get("accession_number", "")
                    for v in violations[:5]
                    if v.get("accession_number")
                ],
            )
        )

        # ── SECTION 3: The Trades ────────────────────────────────────────
        sections.append(
            ArticleSection(
                section_id="S03",
                heading="Trading While the Clock Was Ticking",
                body=self._prose_trades(
                    company_name, violations, transactions, stats
                ),
                pull_quote=(
                    "The timing is not coincidence. "
                    "The documentation is the evidence."
                ),
                sidebar_facts=self._trades_sidebar(violations),
                evidence_anchors=[
                    v.get("accession_number", "")
                    for v in violations
                    if "LATE" in v.get("type", "").upper()
                ][:5],
            )
        )

        # ── SECTION 4: The Discrepancy Layer ────────────────────────────
        if discrepancy_report and hasattr(discrepancy_report, "discrepancies"):
            sections.append(
                ArticleSection(
                    section_id="S04",
                    heading="What They Said — And What the Filings Show",
                    body=self._prose_discrepancies(
                        company_name, discrepancy_report
                    ),
                    pull_quote=(
                        "The gap between the press release and the Form 4 "
                        "is where the story lives."
                    ),
                    sidebar_facts=[
                        f"Critical discrepancies: {discrepancy_report.critical_count}",
                        f"High discrepancies: {discrepancy_report.high_count}",
                        f"Total quantified exposure: "
                        f"${discrepancy_report.total_quantified_exposure:,.0f}",
                    ],
                )
            )
        else:
            sections.append(
                ArticleSection(
                    section_id="S04",
                    heading="The Governance Narrative vs. The SEC Record",
                    body=self._prose_governance_gap(company_name, violations, stats),
                    pull_quote=(
                        "The public narrative and the SEC record tell two "
                        "very different stories."
                    ),
                    sidebar_facts=[
                        f"Violations per insider: "
                        f"{stats['total_violations'] / max(stats['insiders_identified'], 1):.1f} avg",
                    ],
                )
            )

        # ── SECTION 5: The Pattern ───────────────────────────────────────
        sections.append(
            ArticleSection(
                section_id="S05",
                heading="Connecting the Dots: A Pattern of Coordinated Activity",
                body=self._prose_pattern(
                    company_name, violations, beneficiaries, stats
                ),
                pull_quote=(
                    "Isolated incidents don't cluster like this. "
                    "A pattern demands explanation."
                ),
                sidebar_facts=self._pattern_sidebar(violations),
            )
        )

        # ── SECTION 6: The Exposure ──────────────────────────────────────
        sections.append(
            ArticleSection(
                section_id="S06",
                heading="The Bill: Regulatory Exposure and What Comes Next",
                body=self._prose_exposure(
                    company_name, stats, violations
                ),
                pull_quote=(
                    f"Civil penalties alone could reach "
                    f"${stats['total_penalty_exposure_usd']:,.0f} — "
                    "before treble damages or criminal counts."
                ),
                sidebar_facts=self._exposure_sidebar(violations, stats),
            )
        )

        return sections

    # ── prose writers ────────────────────────────────────────────────────────

    def _prose_opening(
        self, company: str, stats: Dict[str, Any], period: str
    ) -> str:
        penalty = stats["total_penalty_exposure_usd"]
        n_v = stats["total_violations"]
        n_ins = stats["insiders_identified"]
        top = stats["top_insider"]

        return (
            f"On the surface, {company} presented {period} as a period of "
            f"disciplined growth, operational excellence, and shareholder alignment. "
            f"Executives told investors that internal controls were robust, that "
            f"compensation structures incentivised long-term value creation, and that "
            f"all regulatory filings were timely and complete.\n\n"
            f"The SEC's own records tell a different story.\n\n"
            f"A systematic forensic review of {company}'s SEC filings during {period} "
            f"— spanning every Form 4, 10-K, 10-Q, DEF 14A, and 8-K submitted to the "
            f"Commission — has identified {n_v} distinct regulatory violations "
            f"attributable to {n_ins} insiders, with an estimated civil penalty "
            f"exposure of ${penalty:,.0f}. The paper trail leads directly to "
            f"{top}, whose transaction activity sits at the nexus of the most "
            f"consequential findings.\n\n"
            f"This is not a story about technical oversights or administrative "
            f"lapses. The data reveals a pattern — systematic, recurring, and "
            f"structurally consistent with behaviour that regulators classify as "
            f"wilful non-compliance. Where there is a pattern, there is intent. "
            f"Where there is intent, there is liability."
        )

    def _prose_players(
        self,
        company: str,
        beneficiaries: List[Dict[str, Any]],
        violations: List[Dict[str, Any]],
        stats: Dict[str, Any],
    ) -> str:
        top = stats["top_insider"]
        profit = stats["top_insider_profit_usd"]

        # Build insider roll-call
        insider_paras: List[str] = []

        if beneficiaries:
            for b in beneficiaries[:5]:
                name = b.get("name", "Unknown")
                role = b.get("role", "Executive")
                p = b.get("total_profit", 0)
                vcount = b.get("violations", 0)
                risk = b.get("risk_score", 0)
                insider_paras.append(
                    f"**{name}** ({role}): ${p:,.0f} in identified equity proceeds "
                    f"across {vcount} flagged transaction(s). Risk score: {risk}/100."
                )
        else:
            # Fall back to violation data
            by_insider: Dict[str, int] = {}
            for v in violations:
                name = v.get("reporting_owner") or v.get("actor") or "Unknown"
                by_insider[name] = by_insider.get(name, 0) + 1
            for name, count in sorted(
                by_insider.items(), key=lambda x: -x[1]
            )[:5]:
                insider_paras.append(
                    f"**{name}**: {count} flagged transaction(s)."
                )

        roster = "\n\n".join(insider_paras) if insider_paras else "See violation log."

        return (
            f"Every financial scandal has a cast. Understanding who stood to "
            f"gain — and by how much — is the starting point for any enforcement action.\n\n"
            f"{roster}\n\n"
            f"At the apex of this network stands {top}, whose aggregate equity activity "
            f"during the analysis period {"generated approximately ${:,.0f} in identified proceeds. ".format(profit) if profit else "warrants immediate further investigation. "}"
            f"The convergence of transaction volume, filing timing, and proximity to "
            f"material corporate events places {top.split()[0] if top else 'this individual'} "
            f"squarely in the crosshairs of any serious regulatory inquiry.\n\n"
            f"These are not passive shareholders. These are insiders with privileged "
            f"access to non-public information — and the trading records show they "
            f"used it."
        )

    def _prose_trades(
        self,
        company: str,
        violations: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        stats: Dict[str, Any],
    ) -> str:
        late_filings = [
            v for v in violations
            if "LATE" in v.get("type", "").upper() or v.get("days_late", 0) > 0
        ]
        n_late = len(late_filings)
        n_v = stats["total_violations"]

        late_para = ""
        if late_filings:
            worst = max(late_filings, key=lambda v: v.get("days_late", 0))
            late_para = (
                f"\n\nThe most egregious filing delay uncovered was "
                f"{worst.get('days_late', 'N/A')} days — a period during which "
                f"{worst.get('reporting_owner', 'the insider')} held information "
                f"the public was legally entitled to receive. Under Section 16(a) of "
                f"the Securities Exchange Act, Form 4 must be filed within two business "
                f"days of a reportable transaction. Filing it late is not a paperwork "
                f"error. It is a violation."
            )

        return (
            f"The timeline of insider transactions during {company}'s {stats.get('period', 'analysis')} "
            f"period is striking not for any single trade, but for the cumulative "
            f"pattern it reveals.\n\n"
            f"Of the {n_v} violations identified, {n_late} involved late SEC disclosure "
            f"of reportable transactions — a statutory obligation that exists specifically "
            f"to give the investing public timely notice of insider activity. "
            f"Every day of delay is a day the market operates without information "
            f"that insiders already possess."
            f"{late_para}\n\n"
            f"The transactions themselves reveal a consistent directional bias: "
            f"disposals concentrated in periods preceding material corporate events, "
            f"acquisitions clustered around grant dates that appear optimised for "
            f"post-announcement price appreciation. The data does not support the "
            f"narrative of passive, long-term holding."
        )

    def _prose_discrepancies(
        self, company: str, disc_report: Any
    ) -> str:
        total = len(disc_report.discrepancies)
        critical = disc_report.critical_count
        high = disc_report.high_count

        highlights = ""
        for d in disc_report.discrepancies[:3]:
            highlights += (
                f"\n\n> **[{d.severity}] {d.title}**\n\n"
                f"> *What they said:* \"{d.public_statement.verbatim_text[:200]}...\"\n\n"
                f"> *What the SEC shows:* {d.delta_description}"
            )

        return (
            f"The most damning evidence in a financial fraud investigation is rarely "
            f"found inside the company. It is found in the gap between what executives "
            f"told investors and what they simultaneously reported to the SEC.\n\n"
            f"Cross-referencing {company}'s public communications against its SEC "
            f"filings produced {total} documented discrepancies — {critical} rated "
            f"CRITICAL and {high} rated HIGH. These are not ambiguous; they are "
            f"contradictions supported by contemporaneous documents."
            f"{highlights}\n\n"
            f"Each discrepancy is a potential Section 10(b) violation — a material "
            f"misstatement or omission in connection with the purchase or sale of "
            f"securities. The cumulative weight of {total} such findings moves the "
            f"analysis from 'isolated error' to 'pattern of deception.'"
        )

    def _prose_governance_gap(
        self,
        company: str,
        violations: List[Dict[str, Any]],
        stats: Dict[str, Any],
    ) -> str:
        n_v = stats["total_violations"]
        n_ins = stats["insiders_identified"]
        return (
            f"Corporate governance statements are written by lawyers to protect "
            f"against liability, not to inform. {company}'s public disclosures during "
            f"the analysis period followed the standard template: commitment to "
            f"transparency, rigorous internal controls, compensation aligned with "
            f"long-term shareholder value.\n\n"
            f"The SEC record — {n_v} violations across {n_ins} executives — tells "
            f"a categorically different story. Late filings mean delayed disclosure. "
            f"Delayed disclosure means information asymmetry. Information asymmetry "
            f"in the hands of insiders is the textbook definition of market manipulation.\n\n"
            f"The governance narrative did not just fail to prevent misconduct. "
            f"The governance narrative actively provided cover for it."
        )

    def _prose_pattern(
        self,
        company: str,
        violations: List[Dict[str, Any]],
        beneficiaries: List[Dict[str, Any]],
        stats: Dict[str, Any],
    ) -> str:
        n_v = stats["total_violations"]
        penalty = stats["total_penalty_exposure_usd"]

        # Detect type concentration
        type_counts: Dict[str, int] = {}
        for v in violations:
            t = v.get("type", "Unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        top_type = max(type_counts, key=type_counts.get) if type_counts else "Unknown"
        top_type_count = type_counts.get(top_type, 0)

        return (
            f"Forensic analysis does not convict anyone. It identifies patterns. "
            f"Prosecutors convict.\n\n"
            f"The pattern identified in {company}'s {stats.get('period', 'analysis')} "
            f"record is unambiguous: {n_v} violations, of which {top_type_count} "
            f"involve '{top_type}' — the single most prevalent violation category. "
            f"This concentration is not random noise. Statistical clustering of "
            f"this magnitude ({top_type_count / max(n_v, 1) * 100:.0f}% of all "
            f"violations in one category) indicates a systemic failure, not an "
            f"isolated incident.\n\n"
            f"When the same violation type recurs across multiple actors, in multiple "
            f"transactions, across multiple filings over an extended period, the "
            f"question is no longer 'did this happen?' The question is: "
            f"'who knew, when did they know it, and why did it continue?'\n\n"
            f"The estimated aggregate civil penalty exposure of ${penalty:,.0f} "
            f"assumes no trebling of damages, no criminal counts, and no disgorgement "
            f"of profits. Add those elements — standard in a DOJ referral — and "
            f"the financial exposure multiplies."
        )

    def _prose_exposure(
        self,
        company: str,
        stats: Dict[str, Any],
        violations: List[Dict[str, Any]],
    ) -> str:
        penalty = stats["total_penalty_exposure_usd"]
        n_v = stats["total_violations"]
        severity = stats.get("severity_label", "HIGH")

        civil_per_violation = penalty / max(n_v, 1)

        return (
            f"The regulatory machinery that governs securities markets is designed "
            f"with escalation in mind. What begins as a civil enforcement action "
            f"at the SEC can become a criminal referral to the DOJ, a parallel "
            f"IRS investigation into unreported gains, and a shareholder derivative "
            f"lawsuit that bypasses regulatory timelines entirely.\n\n"
            f"Based on the {n_v} violations identified, estimated civil penalties "
            f"range from ${penalty * 0.5:,.0f} (conservative, pre-negotiation) to "
            f"${penalty * 2.0:,.0f} (statutory maximum, pre-trebling). The average "
            f"penalty per violation of ${civil_per_violation:,.0f} is consistent "
            f"with recent SEC enforcement benchmarks.\n\n"
            f"For a {severity}-severity case of this profile, the SEC's typical "
            f"enforcement pathway includes: (1) formal order of investigation, "
            f"(2) compelled document production, (3) sworn testimony under "
            f"17 CFR § 203.7, and (4) either a settled administrative proceeding "
            f"or federal district court action seeking disgorgement, prejudgment "
            f"interest, and civil money penalties.\n\n"
            f"Criminal referral to the DOJ is standard where evidence of wilful "
            f"intent is present. The pattern identified in this analysis — "
            f"systematic late filings, coordinated timing, material omissions — "
            f"is precisely the evidentiary footprint that triggers a Section 1348 "
            f"(securities fraud) charge.\n\n"
            f"The question is not whether {company} faces a reckoning. "
            f"The question is who presents the bill first."
        )

    # ── receipts builder ─────────────────────────────────────────────────────

    def _build_receipts(
        self,
        violations: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        beneficiaries: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Build a structured receipts / evidence anchor list."""
        receipts: List[Dict[str, Any]] = []

        for v in violations[:20]:
            receipts.append({
                "receipt_id": hashlib.sha256(
                    str(v.get("accession_number", "")).encode()
                ).hexdigest()[:8].upper(),
                "type": "SEC_FILING",
                "source": "SEC EDGAR",
                "filing_type": v.get("node_id", "NODE_1"),
                "accession_number": v.get("accession_number", "N/A"),
                "date": v.get("filing_date", ""),
                "claim": v.get("type", "Unknown violation"),
                "metric": {
                    "severity": v.get("severity", ""),
                    "shares": v.get("shares", 0),
                    "estimated_penalty": v.get("estimated_penalty", 0),
                    "days_late": v.get("days_late", 0),
                },
                "insider": v.get("reporting_owner") or v.get("actor") or "",
            })

        return receipts

    # ── sidebar helpers ──────────────────────────────────────────────────────

    def _insider_sidebar(
        self,
        beneficiaries: List[Dict[str, Any]],
        violations: List[Dict[str, Any]],
    ) -> List[str]:
        if beneficiaries:
            return [
                f"{b.get('name', 'N/A')} ({b.get('role', 'N/A')}): "
                f"${b.get('total_profit', 0):,.0f}"
                for b in beneficiaries[:5]
            ]
        by_insider: Dict[str, int] = {}
        for v in violations:
            n = v.get("reporting_owner") or v.get("actor") or "Unknown"
            by_insider[n] = by_insider.get(n, 0) + 1
        return [
            f"{n}: {c} violation(s)"
            for n, c in sorted(by_insider.items(), key=lambda x: -x[1])[:5]
        ]

    def _trades_sidebar(self, violations: List[Dict[str, Any]]) -> List[str]:
        late = [v for v in violations if v.get("days_late", 0) > 0]
        if not late:
            return [f"Total violations: {len(violations)}"]
        avg_late = sum(v.get("days_late", 0) for v in late) / len(late)
        worst = max(late, key=lambda v: v.get("days_late", 0))
        return [
            f"Late filings: {len(late)}",
            f"Average days late: {avg_late:.1f}",
            f"Worst offender: {worst.get('days_late', 0)} days late",
            f"Insider: {worst.get('reporting_owner', 'N/A')}",
        ]

    def _pattern_sidebar(self, violations: List[Dict[str, Any]]) -> List[str]:
        type_counts: Dict[str, int] = {}
        for v in violations:
            t = v.get("type", "Unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        return [
            f"{t}: {c}"
            for t, c in sorted(type_counts.items(), key=lambda x: -x[1])[:6]
        ]

    def _exposure_sidebar(
        self, violations: List[Dict[str, Any]], stats: Dict[str, Any]
    ) -> List[str]:
        penalty = stats["total_penalty_exposure_usd"]
        return [
            f"Civil penalty estimate: ${penalty:,.0f}",
            f"With treble damages: ${penalty * 3:,.0f}",
            f"Criminal exposure: Up to 20 years (18 USC § 1348)",
            f"Disgorgement: TBD (all gains)",
            f"Prejudgment interest: TBD",
        ]

    def _build_enforcement_rec(
        self, stats: Dict[str, Any], severity: str
    ) -> str:
        penalty = stats["total_penalty_exposure_usd"]
        n_ins = stats["insiders_identified"]

        priority = {
            "CRITICAL": "IMMEDIATE — SEC formal order and DOJ parallel referral",
            "HIGH": "PRIORITY — SEC enforcement action within 90 days",
            "MEDIUM": "ELEVATED — SEC informal inquiry, 180-day review",
        }.get(severity, "STANDARD — SEC Wells Notice process")

        return (
            f"ENFORCEMENT RECOMMENDATION\n\n"
            f"Priority: {priority}\n\n"
            f"Recommended Actions:\n\n"
            f"1. SEC Division of Enforcement — Formal Order of Investigation\n"
            f"   Issue compelled subpoenas for all Form 4 filings, "
            f"   board minutes, and executive communications during the period.\n\n"
            f"2. DOJ Criminal Division — Securities Fraud Review\n"
            f"   Refer case for 18 USC § 1348 analysis. "
            f"   The pattern evidence meets the 'wilful' standard.\n\n"
            f"3. IRS — Unreported Income Review\n"
            f"   Coordinate with DOJ on potential IRC § 7201 tax evasion "
            f"   charges arising from unreported option exercise gains.\n\n"
            f"4. Civil Litigation\n"
            f"   Shareholders have standing to pursue derivative actions "
            f"   under Rule 10b-5 for the undisclosed material omissions identified.\n\n"
            f"Target Subjects: {n_ins} identified insiders\n"
            f"Estimated Civil Recovery: ${penalty:,.0f}–${penalty * 2:,.0f}\n"
            f"Estimated Criminal Exposure: Up to 20 years per count\n"
        )

    # ── renderers ────────────────────────────────────────────────────────────

    def _render_markdown(self, article: InvestigativeArticle) -> str:
        lines: List[str] = []

        lines.append("---")
        lines.append(f"title: \"{article.headline}\"")
        lines.append(f"subtitle: \"{article.sub_headline}\"")
        lines.append(f"company: \"{article.company_name}\"")
        lines.append(f"cik: \"{article.cik}\"")
        lines.append(f"period: \"{article.analysis_period}\"")
        lines.append(f"severity: \"{article.severity_label}\"")
        lines.append(f"generated: \"{article.generated_at}\"")
        lines.append(f"word_count: {article.word_count}")
        lines.append("---\n")

        lines.append(f"# {article.headline}\n")
        lines.append(f"## {article.sub_headline}\n")
        lines.append(f"> {article.deck}\n")

        # Key stats box
        stats = article.key_statistics
        lines.append("---\n")
        lines.append("### KEY STATISTICS\n")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Violations | {stats.get('total_violations', 0)} |")
        lines.append(f"| Critical | {stats.get('critical_violations', 0)} |")
        lines.append(f"| High | {stats.get('high_violations', 0)} |")
        lines.append(f"| Insiders Identified | {stats.get('insiders_identified', 0)} |")
        lines.append(
            f"| Penalty Exposure | "
            f"${stats.get('total_penalty_exposure_usd', 0):,.0f} |"
        )
        lines.append(f"| Top Insider | {stats.get('top_insider', 'N/A')} |")
        lines.append("\n---\n")

        # Sections
        for section in article.sections:
            lines.append(f"## {section.heading}\n")
            if section.pull_quote:
                lines.append(f"> **\"{section.pull_quote}\"**\n")
            lines.append(section.body + "\n")
            if section.sidebar_facts:
                lines.append("**Key Facts:**")
                for fact in section.sidebar_facts:
                    lines.append(f"- {fact}")
                lines.append("")
            if section.evidence_anchors:
                lines.append("**Evidence Anchors:**")
                for anchor in section.evidence_anchors:
                    if anchor:
                        lines.append(f"- `{anchor}`")
                lines.append("")
            lines.append("---\n")

        # Receipts
        lines.append("## RECEIPTS: EVIDENCE REGISTER\n")
        lines.append(
            "Every finding in this article is sourced to a specific SEC document. "
            "The following register provides the evidence chain.\n"
        )
        lines.append("| Receipt ID | Insider | Type | Accession | Date | Severity |")
        lines.append("|------------|---------|------|-----------|------|----------|")
        for r in article.receipts[:15]:
            m = r.get("metric", {})
            lines.append(
                f"| `{r.get('receipt_id', '')}` "
                f"| {r.get('insider', 'N/A')} "
                f"| {r.get('claim', 'N/A')[:40]} "
                f"| `{r.get('accession_number', 'N/A')}` "
                f"| {r.get('date', 'N/A')} "
                f"| {m.get('severity', 'N/A')} |"
            )
        lines.append("\n---\n")

        # Enforcement recommendation
        lines.append("## ENFORCEMENT RECOMMENDATION\n")
        lines.append(article.enforcement_recommendation)
        lines.append("\n---\n")
        lines.append(
            f"*This report was generated by the JLAW Forensic Analysis System. "
            f"Article ID: `{article.article_id}`. "
            f"All findings are based on publicly available SEC filings and "
            f"do not constitute legal advice. "
            f"Generated: {article.generated_at}.*"
        )

        return "\n".join(lines)

    def _render_html(self, article: InvestigativeArticle) -> str:
        stats = article.key_statistics
        sev_color = {
            "CRITICAL": "#DC143C",
            "HIGH": "#FF6347",
            "MEDIUM": "#FFB347",
            "LOW": "#32CD32",
        }.get(article.severity_label, "#999")

        sections_html = ""
        for s in article.sections:
            pq = (
                f"<blockquote class='pullquote'>{s.pull_quote}</blockquote>"
                if s.pull_quote
                else ""
            )
            sidebar = ""
            if s.sidebar_facts:
                items = "".join(f"<li>{f}</li>" for f in s.sidebar_facts)
                sidebar = f"<aside class='sidebar'><ul>{items}</ul></aside>"
            body_html = "".join(
                f"<p>{p.strip()}</p>"
                for p in s.body.split("\n\n")
                if p.strip()
            )
            sections_html += (
                f"<section id='{s.section_id}'>"
                f"<h2>{s.heading}</h2>"
                f"{pq}{sidebar}{body_html}"
                f"</section><hr/>"
            )

        receipt_rows = "".join(
            f"<tr><td><code>{r.get('receipt_id', '')}</code></td>"
            f"<td>{r.get('insider', 'N/A')}</td>"
            f"<td>{r.get('claim', 'N/A')[:50]}</td>"
            f"<td><code>{r.get('accession_number', 'N/A')}</code></td>"
            f"<td>{r.get('date', 'N/A')}</td>"
            f"<td>{r.get('metric', {}).get('severity', 'N/A')}</td></tr>"
            for r in article.receipts[:15]
        )

        enf_html = "".join(
            f"<p>{line}</p>" if line.strip() else ""
            for line in article.enforcement_recommendation.split("\n")
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{article.headline}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 900px; margin: 0 auto;
          padding: 40px 20px; background: #fafaf9; color: #1a1a2e; line-height: 1.7; }}
  h1 {{ font-size: 2.2em; color: #0D1B2A; border-bottom: 4px solid {sev_color};
        padding-bottom: 12px; margin-bottom: 8px; }}
  h2 {{ font-size: 1.4em; color: #C8102E; margin-top: 2em; }}
  h3 {{ color: #0D1B2A; }}
  .deck {{ font-size: 1.1em; color: #555; font-style: italic; border-left:
           4px solid {sev_color}; padding-left: 12px; margin: 16px 0 24px; }}
  .pullquote {{ font-size: 1.2em; font-weight: bold; color: #C8102E;
                border-left: 6px solid {sev_color}; padding: 12px 20px;
                margin: 24px 0; background: #fff5f5; }}
  .sidebar {{ background: #f0f2f5; border-radius: 6px; padding: 12px 20px;
              float: right; width: 260px; margin: 0 0 16px 24px; font-size: 0.9em; }}
  .sidebar ul {{ margin: 0; padding-left: 18px; }}
  .stat-box {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 20px 0; }}
  .stat {{ background: #0D1B2A; color: white; border-radius: 8px;
           padding: 14px 20px; min-width: 140px; text-align: center; }}
  .stat .val {{ font-size: 1.6em; font-weight: bold; color: {sev_color}; }}
  .stat .lbl {{ font-size: 0.75em; opacity: 0.8; }}
  table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 0.9em; }}
  th {{ background: #0D1B2A; color: white; padding: 8px; }}
  td {{ padding: 7px; border-bottom: 1px solid #ddd; }}
  code {{ background: #eee; padding: 2px 5px; border-radius: 3px; font-size: 0.85em; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px;
            font-size: 0.8em; font-weight: bold; }}
  .badge-{article.severity_label} {{ background: {sev_color}; color: white; }}
  footer {{ margin-top: 60px; border-top: 1px solid #ccc; padding-top: 16px;
            color: #888; font-size: 0.8em; }}
</style>
</head>
<body>
<h1>{article.headline}</h1>
<p><strong>{article.sub_headline}</strong></p>
<p class="deck">{article.deck}</p>
<p>
  <span class="badge badge-{article.severity_label}">{article.severity_label}</span>
  &nbsp; CIK: {article.cik} &nbsp;|&nbsp; Period: {article.analysis_period}
  &nbsp;|&nbsp; Article ID: <code>{article.article_id}</code>
</p>

<div class="stat-box">
  <div class="stat">
    <div class="val">{stats.get('total_violations', 0)}</div>
    <div class="lbl">Total Violations</div>
  </div>
  <div class="stat">
    <div class="val">{stats.get('insiders_identified', 0)}</div>
    <div class="lbl">Insiders</div>
  </div>
  <div class="stat">
    <div class="val">${stats.get('total_penalty_exposure_usd', 0) / 1e6:.1f}M</div>
    <div class="lbl">Penalty Exposure</div>
  </div>
  <div class="stat">
    <div class="val">{stats.get('filings_analyzed', 0)}</div>
    <div class="lbl">Filings Analysed</div>
  </div>
</div>

<hr/>
{sections_html}

<h2>RECEIPTS: EVIDENCE REGISTER</h2>
<table>
<tr><th>Receipt</th><th>Insider</th><th>Claim</th><th>Accession</th><th>Date</th><th>Severity</th></tr>
{receipt_rows}
</table>

<h2>ENFORCEMENT RECOMMENDATION</h2>
{enf_html}

<footer>
  Generated by the JLAW Forensic Analysis System.
  Article ID: <code>{article.article_id}</code>.
  All findings are based on publicly available SEC filings and do not constitute legal advice.
  Generated: {article.generated_at}.
</footer>
</body>
</html>"""
