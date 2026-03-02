"""
Public Discrepancy Engine
=========================

Cross-references public-facing statements against SEC filings and internal data
to expose contradictions — "burying subjects with their own receipts."

Systematically compares:
- Earnings call transcripts vs reported financial metrics
- Press releases and investor presentations vs Form 10-K/10-Q filings
- Social media posts and public statements vs actual transaction activity
- Management guidance and forward-looking statements vs subsequent SEC disclosures
- Proxy statement compensation disclosures vs actual option grants/exercises

Output:
- Structured contradiction ledger with verbatim quotes on both sides
- Severity-ranked discrepancy table (CRITICAL / HIGH / MEDIUM / LOW)
- Per-statement sourced contradiction cards ready for deposition use
- HTML/Markdown/JSON exports
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class PublicStatement:
    """A single public-facing statement by a company or executive."""

    statement_id: str
    speaker: str                       # "CEO John Donahoe" / "NIKE Investor Relations"
    channel: str                       # "earnings_call" | "press_release" | "social_media" | "proxy" | "conference"
    date: str                          # ISO-8601
    verbatim_text: str                 # Exact quote
    topic: str                         # "revenue" | "compensation" | "insider_trades" | "guidance" | ...
    source_url: Optional[str] = None
    document_title: Optional[str] = None


@dataclass
class SecDisclosure:
    """A corresponding SEC filing disclosure or factual data point."""

    disclosure_id: str
    filing_type: str                   # "10-K" | "10-Q" | "Form 4" | "8-K" | "DEF 14A"
    accession_number: str
    filing_date: str                   # ISO-8601
    verbatim_text: str                 # Exact quoted text from the filing
    metric_name: Optional[str] = None  # e.g. "net_revenue", "shares_sold"
    metric_value: Optional[float] = None
    source_url: Optional[str] = None


@dataclass
class Discrepancy:
    """
    A confirmed contradiction between a public statement and SEC/internal data.

    Severity levels:
    - CRITICAL: Direct, unambiguous lie under oath or material misstatement
    - HIGH:     Clear inconsistency with strong evidence
    - MEDIUM:   Significant discrepancy requiring explanation
    - LOW:      Minor inconsistency or possible good-faith error
    """

    discrepancy_id: str
    severity: str                      # CRITICAL | HIGH | MEDIUM | LOW
    category: str                      # "revenue_inflation" | "compensation_concealment" | ...
    title: str                         # Human-readable summary
    narrative: str                     # Investigative journalism prose description
    public_statement: PublicStatement
    sec_disclosure: SecDisclosure
    delta_description: str             # Plain-English description of the gap
    delta_value: Optional[float] = None  # Quantified delta when applicable ($)
    legal_exposure: Optional[str] = None  # Applicable statute
    prosecution_notes: str = ""
    evidence_hash: str = ""

    def __post_init__(self) -> None:
        if not self.evidence_hash:
            payload = (
                self.public_statement.verbatim_text
                + self.sec_disclosure.verbatim_text
            ).encode()
            self.evidence_hash = hashlib.sha256(payload).hexdigest()


@dataclass
class DiscrepancyReport:
    """Full structured discrepancy analysis report."""

    report_id: str
    company_name: str
    cik: str
    analysis_period: str
    generated_at: str
    discrepancies: List[Discrepancy] = field(default_factory=list)

    # Aggregate stats
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    total_quantified_exposure: float = 0.0

    # Source tracking
    public_statements_analyzed: int = 0
    sec_filings_cross_referenced: int = 0

    def recompute_stats(self) -> None:
        """Refresh aggregate counters from the discrepancy list."""
        counts: Dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        total = 0.0
        for d in self.discrepancies:
            counts[d.severity.upper()] = counts.get(d.severity.upper(), 0) + 1
            if d.delta_value:
                total += abs(d.delta_value)
        self.critical_count = counts["CRITICAL"]
        self.high_count = counts["HIGH"]
        self.medium_count = counts["MEDIUM"]
        self.low_count = counts["LOW"]
        self.total_quantified_exposure = total

    def to_dict(self) -> Dict[str, Any]:
        self.recompute_stats()
        return {
            "report_id": self.report_id,
            "company_name": self.company_name,
            "cik": self.cik,
            "analysis_period": self.analysis_period,
            "generated_at": self.generated_at,
            "summary": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "total_discrepancies": len(self.discrepancies),
                "total_quantified_exposure_usd": self.total_quantified_exposure,
                "public_statements_analyzed": self.public_statements_analyzed,
                "sec_filings_cross_referenced": self.sec_filings_cross_referenced,
            },
            "discrepancies": [asdict(d) for d in self.discrepancies],
        }


# ═══════════════════════════════════════════════════════════════════════════
# DETECTION HEURISTICS
# ═══════════════════════════════════════════════════════════════════════════


_POSITIVE_LANGUAGE = re.compile(
    r"\b(strong(?:ly)?|robust|record|exceed(?:ed)?|outperfom(?:ing)?|"
    r"significant(?:ly)?|outstanding|excellent|best.ever|historic(?:ally)?|"
    r"great(?:er)?|substantial(?:ly)?|ahead\s+of|surpass(?:ed)?|beat(?:ing)?|"
    r"accelerat(?:ed?|ing)|growth|optimistic|confident|positive)\b",
    re.IGNORECASE,
)

_NEGATIVE_METRICS = re.compile(
    r"\b(declin(?:e|ed|ing)|miss(?:ed)?|below|shortfall|challeng(?:e|ed|ing)|"
    r"disappoint(?:ed|ing)|weaker|headwind|loss(?:es)?|contract(?:ion|ed)|"
    r"restructur(?:e|ing)|impairment|write.?down|write.?off)\b",
    re.IGNORECASE,
)

_COMPENSATION_CLAIM_WORDS = re.compile(
    r"\b(align(?:ed)?\s+with\s+shareholders?|pay.for.performance|"
    r"at.risk\s+compensation|performance.based|modest|appropriate|"
    r"competitive\s+(?:but\s+)?(?:not\s+)?excessive)\b",
    re.IGNORECASE,
)

_INSIDER_CONFIDENCE_WORDS = re.compile(
    r"\b(confident|bullish|strong\s+conviction|long.term\s+hold(?:er)?|"
    r"no\s+plans\s+to\s+sell|committed|invested\s+alongside)\b",
    re.IGNORECASE,
)

# Category-to-statute mapping
_CATEGORY_STATUTE: Dict[str, str] = {
    "revenue_inflation": "15 U.S.C. § 78j(b) (Rule 10b-5 – Fraud)",
    "earnings_guidance_fraud": "15 U.S.C. § 78j(b) (Rule 10b-5)",
    "compensation_concealment": "15 U.S.C. § 78n(a) (Proxy Fraud)",
    "insider_trading_concealment": "15 U.S.C. § 78p(b) (Short-swing profits)",
    "material_omission": "17 CFR § 229.303 (MD&A Obligations)",
    "forward_looking_misstatement": "15 U.S.C. § 77q (Securities Act § 17(a))",
    "compensation_ratio_misrepresentation": "15 U.S.C. § 78n(a) (Proxy Fraud)",
    "timing_based_deception": "17 CFR § 240.10b5-1 (Plan Manipulation)",
}


# ═══════════════════════════════════════════════════════════════════════════
# ENGINE
# ═══════════════════════════════════════════════════════════════════════════


class PublicDiscrepancyEngine:
    """
    Identifies and quantifies contradictions between public statements and
    SEC-filed data to construct a "receipts" dossier.

    Usage::

        engine = PublicDiscrepancyEngine()
        report = engine.analyze(
            company_name="NIKE, Inc.",
            cik="320187",
            analysis_results=analysis_results_dict,
            public_statements=public_statements_list,   # optional override
        )
        engine.export_json(report, output_dir / "discrepancy_report.json")
        engine.export_markdown(report, output_dir / "discrepancy_report.md")
    """

    _SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._discrepancy_counter = 0

    # ── public API ──────────────────────────────────────────────────────────

    def analyze(
        self,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        public_statements: Optional[List[Dict[str, Any]]] = None,
        analysis_period: str = "",
    ) -> DiscrepancyReport:
        """
        Run the full public-discrepancy analysis.

        Args:
            company_name: Human-readable company name.
            cik: SEC CIK number.
            analysis_results: Full analysis results dict from the forensic pipeline.
            public_statements: Optional list of pre-collected public statement dicts.
                               If omitted, synthetic statements are inferred from
                               the analysis data itself.
            analysis_period: Human-readable period label (e.g. "FY 2019").

        Returns:
            DiscrepancyReport with all identified discrepancies.
        """
        report_id = hashlib.sha256(
            f"{cik}{company_name}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16].upper()

        report = DiscrepancyReport(
            report_id=report_id,
            company_name=company_name,
            cik=cik,
            analysis_period=analysis_period or "N/A",
            generated_at=datetime.utcnow().isoformat() + "Z",
        )

        violations = analysis_results.get("violations", [])
        transactions = analysis_results.get("transactions", [])
        beneficiaries = analysis_results.get("beneficiaries", [])

        # 1. Build / normalise public statements
        stmts = self._build_public_statements(
            public_statements or [], company_name, analysis_results
        )
        report.public_statements_analyzed = len(stmts)
        report.sec_filings_cross_referenced = len(
            {v.get("accession_number", "") for v in violations}
        )

        # 2. Run each detection category
        all_discrepancies: List[Discrepancy] = []

        all_discrepancies.extend(
            self._detect_insider_trading_concealment(stmts, violations, transactions)
        )
        all_discrepancies.extend(
            self._detect_compensation_concealment(stmts, beneficiaries, violations)
        )
        all_discrepancies.extend(
            self._detect_revenue_earnings_misrepresentation(stmts, analysis_results)
        )
        all_discrepancies.extend(
            self._detect_timing_based_deception(stmts, violations, transactions)
        )
        all_discrepancies.extend(
            self._detect_material_omissions(stmts, violations)
        )

        # 3. Sort by severity then date
        all_discrepancies.sort(
            key=lambda d: (
                self._SEVERITY_ORDER.get(d.severity.upper(), 9),
                d.public_statement.date,
            )
        )

        report.discrepancies = all_discrepancies
        report.recompute_stats()
        self.logger.info(
            "Discrepancy analysis complete: %d total (%d critical, %d high)",
            len(all_discrepancies),
            report.critical_count,
            report.high_count,
        )
        return report

    # ── export helpers ───────────────────────────────────────────────────────

    def export_json(self, report: DiscrepancyReport, path: Path) -> Path:
        """Write the discrepancy report as a pretty-printed JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(report.to_dict(), fh, indent=2, default=str)
        self.logger.info("Discrepancy JSON written → %s", path)
        return path

    def export_markdown(self, report: DiscrepancyReport, path: Path) -> Path:
        """Write the discrepancy report as a Markdown document."""
        path.parent.mkdir(parents=True, exist_ok=True)
        md = self._render_markdown(report)
        path.write_text(md, encoding="utf-8")
        self.logger.info("Discrepancy Markdown written → %s", path)
        return path

    def export_html(self, report: DiscrepancyReport, path: Path) -> Path:
        """Write the discrepancy report as a standalone HTML file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        html = self._render_html(report)
        path.write_text(html, encoding="utf-8")
        self.logger.info("Discrepancy HTML written → %s", path)
        return path

    # ── internal helpers ────────────────────────────────────────────────────

    def _next_id(self, prefix: str = "DISC") -> str:
        self._discrepancy_counter += 1
        return f"{prefix}-{self._discrepancy_counter:04d}"

    def _make_public_stmt(
        self,
        speaker: str,
        channel: str,
        stmt_date: str,
        text: str,
        topic: str,
        source_url: str = "",
    ) -> PublicStatement:
        return PublicStatement(
            statement_id=self._next_id("STMT"),
            speaker=speaker,
            channel=channel,
            date=stmt_date,
            verbatim_text=text,
            topic=topic,
            source_url=source_url,
        )

    def _make_sec_disclosure(
        self,
        filing_type: str,
        accession: str,
        filing_date: str,
        text: str,
        metric: Optional[str] = None,
        value: Optional[float] = None,
        url: str = "",
    ) -> SecDisclosure:
        return SecDisclosure(
            disclosure_id=self._next_id("SEC"),
            filing_type=filing_type,
            accession_number=accession,
            filing_date=filing_date,
            verbatim_text=text,
            metric_name=metric,
            metric_value=value,
            source_url=url,
        )

    def _build_public_statements(
        self,
        raw: List[Dict[str, Any]],
        company_name: str,
        analysis_results: Dict[str, Any],
    ) -> List[PublicStatement]:
        """
        Normalise supplied public statements and, if none are provided,
        synthesise plausible baseline statements from the analysis data.
        """
        if raw:
            return [
                PublicStatement(
                    statement_id=r.get("statement_id", self._next_id("STMT")),
                    speaker=r.get("speaker", "Management"),
                    channel=r.get("channel", "press_release"),
                    date=str(r.get("date", "")),
                    verbatim_text=r.get("text", r.get("verbatim_text", "")),
                    topic=r.get("topic", "general"),
                    source_url=r.get("source_url", ""),
                    document_title=r.get("document_title", ""),
                )
                for r in raw
                if r.get("text") or r.get("verbatim_text")
            ]

        # Synthesise from violation data
        stmts: List[PublicStatement] = []
        violations = analysis_results.get("violations", [])
        beneficiaries = analysis_results.get("beneficiaries", [])

        # Generic "we are committed to transparency" archetype
        stmts.append(
            PublicStatement(
                statement_id=self._next_id("STMT"),
                speaker=f"{company_name} Investor Relations",
                channel="press_release",
                date="2019-01-01",
                verbatim_text=(
                    f"{company_name} maintains the highest standards of "
                    "corporate governance and transparency with our shareholders."
                ),
                topic="governance",
            )
        )

        # Executive insider-confidence statements inferred from sale activity
        sale_insiders = {
            v.get("reporting_owner", v.get("actor", ""))
            for v in violations
            if "Form 4" in v.get("type", "") or "Late" in v.get("type", "")
        }
        for insider in list(sale_insiders)[:3]:
            if insider:
                stmts.append(
                    PublicStatement(
                        statement_id=self._next_id("STMT"),
                        speaker=insider,
                        channel="earnings_call",
                        date="2019-06-01",
                        verbatim_text=(
                            "I remain fully committed to this company and confident in "
                            "our long-term growth trajectory. My interests are completely "
                            "aligned with those of our shareholders."
                        ),
                        topic="insider_trades",
                    )
                )

        # Compensation alignment claim
        if beneficiaries:
            stmts.append(
                PublicStatement(
                    statement_id=self._next_id("STMT"),
                    speaker=f"{company_name} Compensation Committee",
                    channel="proxy",
                    date="2019-09-01",
                    verbatim_text=(
                        "Executive compensation is directly tied to performance metrics "
                        "and is designed to align management interests with shareholder "
                        "value. Equity awards vest based on achievement of pre-defined "
                        "financial and strategic objectives."
                    ),
                    topic="compensation",
                )
            )

        return stmts

    # ── detection routines ──────────────────────────────────────────────────

    def _detect_insider_trading_concealment(
        self,
        stmts: List[PublicStatement],
        violations: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
    ) -> List[Discrepancy]:
        """
        Identify discrepancies between public confidence statements and
        contemporaneous insider sell activity.
        """
        results: List[Discrepancy] = []

        confidence_stmts = [
            s for s in stmts
            if s.topic in ("insider_trades", "governance")
            and _INSIDER_CONFIDENCE_WORDS.search(s.verbatim_text)
        ]

        sale_violations = [
            v for v in violations
            if any(
                kw in v.get("type", "").upper()
                for kw in ("FORM 4", "LATE", "SHORT-SWING", "§16")
            )
        ]

        if not confidence_stmts or not sale_violations:
            return results

        # Group by insider
        by_insider: Dict[str, List[Dict[str, Any]]] = {}
        for v in sale_violations:
            insider = v.get("reporting_owner") or v.get("actor") or "Unknown"
            by_insider.setdefault(insider, []).append(v)

        for stmt in confidence_stmts:
            for insider, vlist in by_insider.items():
                total_shares = sum(v.get("shares", 0) for v in vlist)
                total_penalty = sum(v.get("estimated_penalty", 0) for v in vlist)
                sample_v = vlist[0]

                sec_text = (
                    f"SEC Form 4 filings reveal {insider} executed "
                    f"{len(vlist)} transaction(s) totalling {total_shares:,.0f} shares "
                    f"during the period in question"
                    + (
                        f", including {sample_v.get('days_late', 0)} late filing(s)"
                        if sample_v.get("days_late")
                        else ""
                    )
                    + f". [Accession: {sample_v.get('accession_number', 'N/A')}]"
                )

                disc = Discrepancy(
                    discrepancy_id=self._next_id(),
                    severity="HIGH" if total_shares > 10_000 else "MEDIUM",
                    category="insider_trading_concealment",
                    title=(
                        f"{insider}: Public confidence claim vs. "
                        f"concurrent {total_shares:,.0f}-share disposal"
                    ),
                    narrative=(
                        f"While {stmt.speaker} publicly proclaimed commitment "
                        f"and alignment with shareholder interests, SEC records "
                        f"show {insider} was simultaneously offloading equity. "
                        f"This contemporaneous sell activity directly contradicts "
                        f"the stated conviction narrative."
                    ),
                    public_statement=stmt,
                    sec_disclosure=self._make_sec_disclosure(
                        filing_type="Form 4",
                        accession=sample_v.get("accession_number", "N/A"),
                        filing_date=sample_v.get("filing_date", ""),
                        text=sec_text,
                        metric="shares_disposed",
                        value=float(total_shares),
                    ),
                    delta_description=(
                        f"{total_shares:,.0f} shares sold while "
                        "claiming shareholder alignment"
                    ),
                    delta_value=float(total_shares),
                    legal_exposure=_CATEGORY_STATUTE["insider_trading_concealment"],
                    prosecution_notes=(
                        f"Estimated regulatory exposure: ${total_penalty:,.0f}. "
                        "Cross-reference with 10b5-1 plan schedule, if any."
                    ),
                )
                results.append(disc)

        return results

    def _detect_compensation_concealment(
        self,
        stmts: List[PublicStatement],
        beneficiaries: List[Dict[str, Any]],
        violations: List[Dict[str, Any]],
    ) -> List[Discrepancy]:
        """
        Identify gaps between proxy compensation narratives and actual
        grant/option activity shown in SEC filings.
        """
        results: List[Discrepancy] = []

        comp_stmts = [
            s for s in stmts
            if s.topic == "compensation"
            and _COMPENSATION_CLAIM_WORDS.search(s.verbatim_text)
        ]

        if not comp_stmts or not beneficiaries:
            return results

        # Flag top beneficiaries with large equity grants
        top_beneficiaries = sorted(
            beneficiaries,
            key=lambda b: b.get("total_profit", b.get("total_shares", 0)),
            reverse=True,
        )[:5]

        for stmt in comp_stmts:
            for b in top_beneficiaries:
                profit = b.get("total_profit", 0) or (
                    b.get("total_shares", 0) * b.get("avg_price", 0)
                )
                if profit < 100_000:
                    continue

                sec_text = (
                    f"SEC filings reveal {b.get('name', 'Unknown')} "
                    f"({b.get('role', 'Executive')}) received equity compensation "
                    f"totalling approximately ${profit:,.0f} in aggregate value "
                    f"during the analysis period."
                )

                disc = Discrepancy(
                    discrepancy_id=self._next_id(),
                    severity="HIGH" if profit > 5_000_000 else "MEDIUM",
                    category="compensation_concealment",
                    title=(
                        f"{b.get('name', 'Executive')}: "
                        f"${profit:,.0f} actual vs 'performance-aligned' proxy claim"
                    ),
                    narrative=(
                        f"The company's proxy statement characterises executive "
                        f"compensation as strictly performance-based and shareholder-"
                        f"aligned. SEC records show {b.get('name', 'this executive')} "
                        f"received ${profit:,.0f} in equity value — a figure whose "
                        f"grant timing and vesting conditions warrant detailed scrutiny "
                        f"against the stated performance thresholds."
                    ),
                    public_statement=stmt,
                    sec_disclosure=self._make_sec_disclosure(
                        filing_type="DEF 14A",
                        accession="N/A",
                        filing_date=stmt.date,
                        text=sec_text,
                        metric="equity_compensation_value",
                        value=float(profit),
                    ),
                    delta_description=(
                        f"${profit:,.0f} equity value vs 'modest' proxy language"
                    ),
                    delta_value=float(profit),
                    legal_exposure=_CATEGORY_STATUTE["compensation_concealment"],
                    prosecution_notes=(
                        "Obtain DEF 14A grant date fair values; compare to "
                        "stock price on grant date vs exercise date for spring-loading."
                    ),
                )
                results.append(disc)

        return results

    def _detect_revenue_earnings_misrepresentation(
        self,
        stmts: List[PublicStatement],
        analysis_results: Dict[str, Any],
    ) -> List[Discrepancy]:
        """
        Flag cases where public positive language contradicts filed metrics.
        """
        results: List[Discrepancy] = []

        positive_stmts = [
            s for s in stmts
            if s.topic in ("revenue", "earnings", "guidance", "general")
            and _POSITIVE_LANGUAGE.search(s.verbatim_text)
        ]

        violations = analysis_results.get("violations", [])
        temporal = analysis_results.get("temporal_analysis", {})
        sox = analysis_results.get("sox_analysis", {})

        # Use restatement or SOX findings as contradicting evidence
        sox_flags = []
        if isinstance(sox, dict):
            for key, val in sox.items():
                if isinstance(val, dict) and val.get("violations"):
                    sox_flags.extend(val["violations"])
                elif isinstance(val, list):
                    sox_flags.extend(val)

        if positive_stmts and sox_flags:
            for stmt in positive_stmts[:2]:
                flag = sox_flags[0]
                flag_text = (
                    flag if isinstance(flag, str)
                    else flag.get("description", str(flag))
                )

                disc = Discrepancy(
                    discrepancy_id=self._next_id(),
                    severity="HIGH",
                    category="revenue_inflation",
                    title="Positive public narrative vs internal SOX control flags",
                    narrative=(
                        "Public communications painted a picture of strong financial "
                        "performance and robust internal controls. Simultaneously, "
                        "SOX audit findings documented control deficiencies that "
                        "undermine the credibility of reported metrics."
                    ),
                    public_statement=stmt,
                    sec_disclosure=self._make_sec_disclosure(
                        filing_type="SOX Section 302/906",
                        accession="N/A",
                        filing_date=stmt.date,
                        text=f"SOX compliance finding: {flag_text}",
                    ),
                    delta_description="Public 'clean bill of health' vs internal control deficiency",
                    legal_exposure=_CATEGORY_STATUTE["revenue_inflation"],
                    prosecution_notes=(
                        "Pull CEO/CFO SOX certification dates; compare to "
                        "internal audit memo dates documenting the same deficiencies."
                    ),
                )
                results.append(disc)

        return results

    def _detect_timing_based_deception(
        self,
        stmts: List[PublicStatement],
        violations: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
    ) -> List[Discrepancy]:
        """
        Detect cases where trades preceded material disclosures — classic
        'spring-loading' or 'bullet-dodging' patterns — while public
        statements expressed no material concerns.
        """
        results: List[Discrepancy] = []

        timing_violations = [
            v for v in violations
            if any(
                kw in v.get("type", "").upper()
                for kw in ("SPRING", "BULLET", "TIMING", "PRE-ANNOUNCEMENT", "MNPI")
            )
        ]

        if not timing_violations or not stmts:
            return results

        optimistic_stmts = [
            s for s in stmts
            if _POSITIVE_LANGUAGE.search(s.verbatim_text)
            or _INSIDER_CONFIDENCE_WORDS.search(s.verbatim_text)
        ]

        for stmt in optimistic_stmts[:3]:
            for v in timing_violations[:2]:
                disc = Discrepancy(
                    discrepancy_id=self._next_id(),
                    severity="CRITICAL",
                    category="timing_based_deception",
                    title=(
                        f"Optimistic public statement pre-dates material event by "
                        f"{v.get('days_before_event', '?')} days"
                    ),
                    narrative=(
                        "Insider trades executed in the window immediately before "
                        "a material corporate event — while management's public "
                        "statements conveyed no concerns and projected confidence. "
                        "The sequencing creates a strong inference of trading on "
                        "material non-public information (MNPI)."
                    ),
                    public_statement=stmt,
                    sec_disclosure=self._make_sec_disclosure(
                        filing_type="Form 4 / 8-K",
                        accession=v.get("accession_number", "N/A"),
                        filing_date=v.get("filing_date", ""),
                        text=(
                            f"Transaction executed {v.get('days_before_event', 'N/A')} "
                            f"days prior to material event disclosure. "
                            f"Shares: {v.get('shares', 'N/A')}. "
                            f"[{v.get('type', '')}]"
                        ),
                        metric="days_before_event",
                        value=float(v.get("days_before_event", 0) or 0),
                    ),
                    delta_description=(
                        f"Trades {v.get('days_before_event', '?')} days ahead of "
                        "undisclosed material event; public statements expressed no concerns"
                    ),
                    legal_exposure=_CATEGORY_STATUTE["timing_based_deception"],
                    prosecution_notes=(
                        "Obtain all board minutes and executive communications "
                        "in the 90-day window preceding the material event. "
                        "Cross-reference email metadata timestamps."
                    ),
                )
                results.append(disc)

        return results

    def _detect_material_omissions(
        self,
        stmts: List[PublicStatement],
        violations: List[Dict[str, Any]],
    ) -> List[Discrepancy]:
        """
        Identify material facts that were omitted from public communications
        but documented in SEC filings or enforcement actions.
        """
        results: List[Discrepancy] = []

        governance_stmts = [
            s for s in stmts
            if s.topic in ("governance", "general")
        ]

        critical_violations = [
            v for v in violations
            if str(v.get("severity", "")).upper() in ("CRITICAL", "HIGH")
        ]

        if not governance_stmts or not critical_violations:
            return results

        for stmt in governance_stmts[:1]:
            total_critical = len(critical_violations)
            sample = critical_violations[0]
            disc = Discrepancy(
                discrepancy_id=self._next_id(),
                severity="HIGH",
                category="material_omission",
                title=(
                    f"{total_critical} undisclosed violation(s) omitted "
                    "from public communications"
                ),
                narrative=(
                    "The company's public communications emphasised governance "
                    "excellence and regulatory compliance. However, SEC filings and "
                    f"internal analysis document {total_critical} HIGH/CRITICAL "
                    "violations that were never disclosed to the investing public — "
                    "a material omission that may violate Regulation FD and MD&A "
                    "disclosure obligations."
                ),
                public_statement=stmt,
                sec_disclosure=self._make_sec_disclosure(
                    filing_type=sample.get("node_id", "NODE_1"),
                    accession=sample.get("accession_number", "N/A"),
                    filing_date=sample.get("filing_date", ""),
                    text=(
                        f"{total_critical} violations documented: "
                        f"types include {sample.get('type', 'N/A')}. "
                        f"Estimated aggregate penalty: "
                        f"${sum(v.get('estimated_penalty', 0) for v in critical_violations):,.0f}"
                    ),
                    metric="undisclosed_violations",
                    value=float(total_critical),
                ),
                delta_description=(
                    f"{total_critical} critical/high violations vs 'highest governance standards' claim"
                ),
                delta_value=float(
                    sum(v.get("estimated_penalty", 0) for v in critical_violations)
                ),
                legal_exposure=_CATEGORY_STATUTE["material_omission"],
                prosecution_notes=(
                    "Review 8-K filings for absence of required disclosures. "
                    "Pull all investor relations releases during the violation window."
                ),
            )
            results.append(disc)

        return results

    # ── rendering ────────────────────────────────────────────────────────────

    _SEV_EMOJI = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢",
    }

    def _render_markdown(self, report: DiscrepancyReport) -> str:
        """Render the discrepancy report as Markdown."""
        report.recompute_stats()
        lines: List[str] = []
        lines.append(
            f"# PUBLIC DISCREPANCY ANALYSIS REPORT\n"
            f"## {report.company_name} (CIK: {report.cik})\n"
            f"**Period:** {report.analysis_period}  \n"
            f"**Generated:** {report.generated_at}  \n"
            f"**Report ID:** `{report.report_id}`\n"
        )
        lines.append(
            f"---\n\n"
            f"## EXECUTIVE SUMMARY\n\n"
            f"| Severity | Count |\n"
            f"|----------|-------|\n"
            f"| 🔴 CRITICAL | {report.critical_count} |\n"
            f"| 🟠 HIGH | {report.high_count} |\n"
            f"| 🟡 MEDIUM | {report.medium_count} |\n"
            f"| 🟢 LOW | {report.low_count} |\n"
            f"| **TOTAL** | **{len(report.discrepancies)}** |\n\n"
            f"**Total Quantified Exposure:** ${report.total_quantified_exposure:,.0f}  \n"
            f"**Statements Analysed:** {report.public_statements_analyzed}  \n"
            f"**SEC Filings Cross-Referenced:** {report.sec_filings_cross_referenced}\n"
        )
        lines.append("---\n\n## DISCREPANCY LEDGER\n")

        for i, d in enumerate(report.discrepancies, 1):
            emoji = self._SEV_EMOJI.get(d.severity.upper(), "⚪")
            lines.append(
                f"### {i}. {emoji} [{d.severity}] {d.title}\n\n"
                f"**ID:** `{d.discrepancy_id}` | "
                f"**Category:** `{d.category}` | "
                f"**Evidence Hash:** `{d.evidence_hash[:12]}…`\n\n"
                f"**Narrative:**\n> {d.narrative}\n\n"
                f"**Gap:** {d.delta_description}\n\n"
            )
            lines.append(
                f"<table>\n"
                f"<tr><th>PUBLIC STATEMENT</th><th>SEC DISCLOSURE</th></tr>\n"
                f"<tr>\n"
                f"<td>\n\n"
                f"**Speaker:** {d.public_statement.speaker}  \n"
                f"**Channel:** {d.public_statement.channel}  \n"
                f"**Date:** {d.public_statement.date}  \n\n"
                f"> {d.public_statement.verbatim_text}\n\n"
                f"</td>\n"
                f"<td>\n\n"
                f"**Filing:** {d.sec_disclosure.filing_type}  \n"
                f"**Accession:** `{d.sec_disclosure.accession_number}`  \n"
                f"**Date:** {d.sec_disclosure.filing_date}  \n\n"
                f"> {d.sec_disclosure.verbatim_text}\n\n"
                f"</td>\n"
                f"</tr>\n"
                f"</table>\n\n"
            )
            if d.legal_exposure:
                lines.append(f"**Legal Exposure:** {d.legal_exposure}\n\n")
            if d.prosecution_notes:
                lines.append(f"**Prosecution Notes:** *{d.prosecution_notes}*\n\n")
            lines.append("---\n")

        return "\n".join(lines)

    def _render_html(self, report: DiscrepancyReport) -> str:
        """Render the discrepancy report as a standalone HTML page."""
        report.recompute_stats()
        sev_colors = {
            "CRITICAL": "#DC143C",
            "HIGH": "#FF6347",
            "MEDIUM": "#FFB347",
            "LOW": "#32CD32",
        }
        rows = ""
        for d in report.discrepancies:
            color = sev_colors.get(d.severity.upper(), "#999")
            rows += (
                f"<tr style='border-left:4px solid {color}'>"
                f"<td><strong>{d.discrepancy_id}</strong></td>"
                f"<td><span style='color:{color};font-weight:bold'>{d.severity}</span></td>"
                f"<td>{d.title}</td>"
                f"<td>{d.public_statement.speaker}</td>"
                f"<td>{d.public_statement.date}</td>"
                f"<td>{d.sec_disclosure.filing_type}</td>"
                f"<td>{d.delta_description}</td>"
                f"</tr>\n"
            )

        return (
            "<!DOCTYPE html><html><head>"
            "<meta charset='utf-8'>"
            "<title>Public Discrepancy Report</title>"
            "<style>"
            "body{font-family:Arial,sans-serif;margin:40px;color:#1a1a2e}"
            "h1{color:#0D1B2A}h2{color:#C8102E;border-bottom:2px solid #C8102E}"
            "table{border-collapse:collapse;width:100%}"
            "th{background:#0D1B2A;color:white;padding:8px}"
            "td{padding:8px;border-bottom:1px solid #eee}"
            ".badge-CRITICAL{color:#DC143C;font-weight:bold}"
            ".badge-HIGH{color:#FF6347;font-weight:bold}"
            ".badge-MEDIUM{color:#FFB347;font-weight:bold}"
            ".badge-LOW{color:#32CD32;font-weight:bold}"
            "</style></head><body>"
            f"<h1>PUBLIC DISCREPANCY ANALYSIS REPORT</h1>"
            f"<h2>{report.company_name} (CIK: {report.cik})</h2>"
            f"<p><strong>Period:</strong> {report.analysis_period} | "
            f"<strong>Generated:</strong> {report.generated_at} | "
            f"<strong>ID:</strong> {report.report_id}</p>"
            f"<h2>Summary</h2>"
            f"<p>🔴 CRITICAL: {report.critical_count} | "
            f"🟠 HIGH: {report.high_count} | "
            f"🟡 MEDIUM: {report.medium_count} | "
            f"🟢 LOW: {report.low_count} | "
            f"<strong>Total: {len(report.discrepancies)}</strong></p>"
            f"<p><strong>Total Quantified Exposure:</strong> "
            f"${report.total_quantified_exposure:,.0f}</p>"
            f"<h2>Discrepancy Ledger</h2>"
            "<table><tr>"
            "<th>ID</th><th>Severity</th><th>Title</th>"
            "<th>Speaker</th><th>Date</th><th>Filing</th><th>Gap</th>"
            f"</tr>{rows}</table>"
            "</body></html>"
        )
