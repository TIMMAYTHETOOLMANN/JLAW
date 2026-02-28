"""
Executive Financial Profile Cross-Reference Module
====================================================

Builds comprehensive insider financial profiles by cross-referencing
Form 4 transaction data with other SEC EDGAR filing sources:

  - Submissions API: All filings by an insider's CIK (Forms 3, 4, 5, SC 13D/G)
  - DEF 14A proxy statements: Named executive compensation tables
  - Form 3: Initial beneficial ownership on becoming an insider
  - Form 5: Annual changes in beneficial ownership (deferred reporting)
  - 10-K: Director/officer holdings, related-party transactions

The profile aggregates:
  1. Filing history: All filings associated with the insider's CIK
  2. Ownership timeline: Form 3 (initial) -> Form 4 (changes) -> Form 5 (annual)
  3. Compensation context: Role, title, named executive officer status
  4. Cross-filing anomalies: Discrepancies between filings

This module does NOT make live SEC API calls. It operates on data already
fetched by the edgar_client and cached in the pipeline context. It enriches
the existing Form 4 transaction records with cross-reference metadata.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class InsiderFilingRecord:
    """A single filing from the insider's submission history."""
    form_type: str
    filing_date: str
    accession_number: str
    primary_document: str = ""
    description: str = ""


@dataclass
class OwnershipTimeline:
    """Timeline of ownership filings for a single insider."""
    form3_filings: List[InsiderFilingRecord] = field(default_factory=list)
    form4_filings: List[InsiderFilingRecord] = field(default_factory=list)
    form5_filings: List[InsiderFilingRecord] = field(default_factory=list)
    schedule_13d_filings: List[InsiderFilingRecord] = field(default_factory=list)
    schedule_13g_filings: List[InsiderFilingRecord] = field(default_factory=list)
    form144_filings: List[InsiderFilingRecord] = field(default_factory=list)

    @property
    def total_ownership_filings(self) -> int:
        return (len(self.form3_filings) + len(self.form4_filings) +
                len(self.form5_filings) + len(self.schedule_13d_filings) +
                len(self.schedule_13g_filings) + len(self.form144_filings))

    @property
    def has_form3(self) -> bool:
        return len(self.form3_filings) > 0

    @property
    def has_form5(self) -> bool:
        return len(self.form5_filings) > 0

    @property
    def has_schedule_13d(self) -> bool:
        return len(self.schedule_13d_filings) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "form3_count": len(self.form3_filings),
            "form4_count": len(self.form4_filings),
            "form5_count": len(self.form5_filings),
            "schedule_13d_count": len(self.schedule_13d_filings),
            "schedule_13g_count": len(self.schedule_13g_filings),
            "form144_count": len(self.form144_filings),
            "total_ownership_filings": self.total_ownership_filings,
            "has_form3": self.has_form3,
            "has_form5": self.has_form5,
            "has_schedule_13d": self.has_schedule_13d,
            "form3_filings": [f.__dict__ for f in self.form3_filings],
            "form4_filings": [f.__dict__ for f in self.form4_filings],
            "form5_filings": [f.__dict__ for f in self.form5_filings],
        }


@dataclass
class CrossReferenceAnomaly:
    """Discrepancy detected when cross-referencing filings."""
    anomaly_type: str
    severity: str  # LOW, MEDIUM, HIGH
    description: str
    filing_a: str  # accession number or identifier
    filing_b: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "description": self.description,
            "filing_a": self.filing_a,
            "filing_b": self.filing_b,
            "details": self.details,
        }


@dataclass
class ExecutiveFinancialProfile:
    """
    Comprehensive financial profile for a single insider/executive.

    Aggregates data from multiple SEC filing sources to provide a
    complete picture of an insider's ownership and transaction history.
    """
    insider_name: str
    insider_cik: str
    company_cik: str
    company_name: str = ""

    # Role information (derived from filings)
    is_officer: bool = False
    is_director: bool = False
    is_ten_percent_owner: bool = False
    officer_title: str = ""

    # Ownership timeline
    ownership_timeline: OwnershipTimeline = field(default_factory=OwnershipTimeline)

    # Form 4 transaction summary
    total_form4_transactions: int = 0
    total_shares_acquired: float = 0.0
    total_shares_disposed: float = 0.0
    total_value_acquired: float = 0.0
    total_value_disposed: float = 0.0
    transaction_code_distribution: Dict[str, int] = field(default_factory=dict)
    date_range: Tuple[str, str] = ("", "")

    # Cross-reference anomalies
    anomalies: List[CrossReferenceAnomaly] = field(default_factory=list)

    # Metadata
    profile_generated_at: str = ""
    data_sources_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insider_name": self.insider_name,
            "insider_cik": self.insider_cik,
            "company_cik": self.company_cik,
            "company_name": self.company_name,
            "role": {
                "is_officer": self.is_officer,
                "is_director": self.is_director,
                "is_ten_percent_owner": self.is_ten_percent_owner,
                "officer_title": self.officer_title,
            },
            "ownership_timeline": self.ownership_timeline.to_dict(),
            "form4_summary": {
                "total_transactions": self.total_form4_transactions,
                "total_shares_acquired": self.total_shares_acquired,
                "total_shares_disposed": self.total_shares_disposed,
                "total_value_acquired": round(self.total_value_acquired, 2),
                "total_value_disposed": round(self.total_value_disposed, 2),
                "transaction_code_distribution": self.transaction_code_distribution,
                "date_range": list(self.date_range),
            },
            "anomalies": [a.to_dict() for a in self.anomalies],
            "anomaly_count": len(self.anomalies),
            "profile_generated_at": self.profile_generated_at,
            "data_sources_used": self.data_sources_used,
        }


class ExecutiveProfileBuilder:
    """
    Builds executive financial profiles from pipeline data.

    Operates on data already collected during the 15-node engine execution:
    - insider_trades: Form 4 parsed transaction records
    - submissions_cache: Submissions JSON from data.sec.gov/submissions/
    - fsl_assessments: Forensic Sufficiency Layer assessments

    Does NOT make live SEC API calls.
    """

    # Ownership-related form types
    OWNERSHIP_FORMS = {"3", "4", "5", "3/A", "4/A", "5/A"}
    BENEFICIAL_OWNERSHIP_FORMS = {"SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"}
    FORM_144_TYPES = {"144", "144/A"}
    PROXY_FORMS = {"DEF 14A", "DEFA14A", "DEF 14C"}

    @classmethod
    def build_profiles(
        cls,
        insider_trades: List[Dict[str, Any]],
        fsl_assessments: List[Dict[str, Any]] = None,
        submissions_cache: Dict[str, Dict] = None,
        company_cik: str = "",
        company_name: str = "",
    ) -> Dict[str, ExecutiveFinancialProfile]:
        """
        Build financial profiles for all insiders found in the data.

        Args:
            insider_trades: Form 4 parsed transaction records from the engine
            fsl_assessments: Optional FSL assessment dicts
            submissions_cache: Optional dict mapping CIK -> submissions JSON
            company_cik: Company CIK for context
            company_name: Company name for context

        Returns:
            Dict mapping insider CIK -> ExecutiveFinancialProfile
        """
        profiles: Dict[str, ExecutiveFinancialProfile] = {}
        submissions_cache = submissions_cache or {}
        fsl_assessments = fsl_assessments or []

        # Step 1: Group trades by insider CIK
        trades_by_cik = cls._group_trades_by_cik(insider_trades)

        # Step 2: Extract role info from trades
        for cik, trades in trades_by_cik.items():
            if not cik:
                continue

            profile = cls._build_single_profile(
                cik=cik,
                trades=trades,
                submissions=submissions_cache.get(cik),
                company_cik=company_cik,
                company_name=company_name,
            )
            profiles[cik] = profile

        # Step 3: Enrich with FSL assessment data
        cls._enrich_with_fsl(profiles, fsl_assessments)

        # Step 4: Run cross-reference anomaly detection
        for profile in profiles.values():
            cls._detect_anomalies(profile)

        logger.info(
            f"Built {len(profiles)} executive financial profiles "
            f"({sum(p.total_form4_transactions for p in profiles.values())} total transactions)"
        )

        return profiles

    @classmethod
    def _group_trades_by_cik(
        cls, trades: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group insider trades by reporting_owner_cik."""
        by_cik: Dict[str, List[Dict[str, Any]]] = {}
        for trade in trades:
            cik = str(trade.get("reporting_owner_cik", "") or
                       trade.get("insider_cik", "") or "").strip()
            if not cik:
                # Fall back to name-based grouping
                name = trade.get("reporting_person", "") or trade.get("reporting_owner", "")
                cik = f"NAME:{name}" if name else ""
            if cik:
                by_cik.setdefault(cik, []).append(trade)
        return by_cik

    @classmethod
    def _build_single_profile(
        cls,
        cik: str,
        trades: List[Dict[str, Any]],
        submissions: Optional[Dict] = None,
        company_cik: str = "",
        company_name: str = "",
    ) -> ExecutiveFinancialProfile:
        """Build profile for a single insider from their trades and submissions."""
        # Extract name from first trade
        first_trade = trades[0] if trades else {}
        insider_name = (first_trade.get("reporting_person", "") or
                        first_trade.get("reporting_owner", "") or
                        first_trade.get("insider_name", ""))

        profile = ExecutiveFinancialProfile(
            insider_name=insider_name,
            insider_cik=cik,
            company_cik=company_cik,
            company_name=company_name,
            profile_generated_at=datetime.utcnow().isoformat() + "Z",
        )

        # Extract role from trades metadata
        for trade in trades:
            if trade.get("is_officer"):
                profile.is_officer = True
                profile.officer_title = trade.get("officer_title", "") or profile.officer_title
            if trade.get("is_director"):
                profile.is_director = True
            if trade.get("is_ten_percent_owner"):
                profile.is_ten_percent_owner = True

        # Summarize Form 4 transactions
        cls._summarize_transactions(profile, trades)

        # Build ownership timeline from submissions
        if submissions:
            cls._build_timeline_from_submissions(profile, submissions)
            profile.data_sources_used.append("SEC EDGAR Submissions API")

        profile.data_sources_used.append("Form 4 XML (parsed)")

        return profile

    @classmethod
    def _summarize_transactions(
        cls,
        profile: ExecutiveFinancialProfile,
        trades: List[Dict[str, Any]],
    ) -> None:
        """Summarize Form 4 transactions into the profile."""
        dates = []
        code_dist: Dict[str, int] = {}

        for trade in trades:
            code = (trade.get("transaction_code", "") or "").upper()
            if code:
                code_dist[code] = code_dist.get(code, 0) + 1

            shares = abs(trade.get("shares", 0) or 0)
            price = trade.get("price_per_share", 0) or 0
            value = shares * price
            ad = (trade.get("acquired_disposed", "") or "").upper()

            if ad == "A":
                profile.total_shares_acquired += shares
                profile.total_value_acquired += value
            elif ad == "D":
                profile.total_shares_disposed += shares
                profile.total_value_disposed += value

            txn_date = trade.get("transaction_date", "")
            if txn_date:
                if isinstance(txn_date, (date, datetime)):
                    txn_date = txn_date.isoformat()
                dates.append(str(txn_date))

        profile.total_form4_transactions = len(trades)
        profile.transaction_code_distribution = code_dist

        if dates:
            dates.sort()
            profile.date_range = (dates[0], dates[-1])

    @classmethod
    def _build_timeline_from_submissions(
        cls,
        profile: ExecutiveFinancialProfile,
        submissions: Dict,
    ) -> None:
        """
        Parse the SEC EDGAR submissions JSON to build ownership timeline.

        The submissions endpoint returns:
        {
            "cik": "...",
            "name": "...",
            "filings": {
                "recent": {
                    "accessionNumber": [...],
                    "form": [...],
                    "filingDate": [...],
                    "primaryDocument": [...],
                    "primaryDocDescription": [...]
                }
            }
        }
        """
        recent = submissions.get("filings", {}).get("recent", {})
        accessions = recent.get("accessionNumber", [])
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        primary_docs = recent.get("primaryDocument", [])
        descriptions = recent.get("primaryDocDescription", [])

        timeline = profile.ownership_timeline

        for i in range(len(accessions)):
            form = forms[i] if i < len(forms) else ""
            filing_date = filing_dates[i] if i < len(filing_dates) else ""
            accession = accessions[i] if i < len(accessions) else ""
            doc = primary_docs[i] if i < len(primary_docs) else ""
            desc = descriptions[i] if i < len(descriptions) else ""

            record = InsiderFilingRecord(
                form_type=form,
                filing_date=filing_date,
                accession_number=accession,
                primary_document=doc,
                description=desc,
            )

            if form in ("3", "3/A"):
                timeline.form3_filings.append(record)
            elif form in ("4", "4/A"):
                timeline.form4_filings.append(record)
            elif form in ("5", "5/A"):
                timeline.form5_filings.append(record)
            elif form in ("SC 13D", "SC 13D/A"):
                timeline.schedule_13d_filings.append(record)
            elif form in ("SC 13G", "SC 13G/A"):
                timeline.schedule_13g_filings.append(record)
            elif form in ("144", "144/A"):
                timeline.form144_filings.append(record)

        # Update company name from submissions if available
        if not profile.company_name:
            profile.company_name = submissions.get("name", "")

    @classmethod
    def _enrich_with_fsl(
        cls,
        profiles: Dict[str, ExecutiveFinancialProfile],
        fsl_assessments: List[Dict[str, Any]],
    ) -> None:
        """Enrich profiles with data from FSL assessments."""
        for assessment in fsl_assessments:
            cik = str(assessment.get("insider_cik", "") or "").strip()
            if not cik or cik not in profiles:
                continue

            profile = profiles[cik]

            # FSL assessments may have role data not in Form 4 records
            if assessment.get("is_officer") and not profile.is_officer:
                profile.is_officer = True
                profile.officer_title = assessment.get("officer_title", "")
            if assessment.get("is_director") and not profile.is_director:
                profile.is_director = True

            if "FSL Assessment" not in profile.data_sources_used:
                profile.data_sources_used.append("FSL Assessment")

    @classmethod
    def _detect_anomalies(cls, profile: ExecutiveFinancialProfile) -> None:
        """
        Detect cross-reference anomalies in the profile.

        Checks:
        1. Missing Form 3: Insider has Form 4s but no initial Form 3
        2. Form 5 gaps: Officer/director with no Form 5 filings
        3. Filing frequency anomalies: Burst trading patterns
        4. Large dispositions without Form 144
        """
        timeline = profile.ownership_timeline

        # Anomaly 1: Missing Form 3
        if timeline.form4_filings and not timeline.form3_filings:
            if not profile.insider_cik.startswith("NAME:"):
                profile.anomalies.append(CrossReferenceAnomaly(
                    anomaly_type="MISSING_FORM_3",
                    severity="MEDIUM",
                    description=(
                        f"Insider {profile.insider_name} has "
                        f"{len(timeline.form4_filings)} Form 4 filing(s) but no "
                        f"Form 3 (Initial Statement of Beneficial Ownership). "
                        f"Section 16(a) requires Form 3 within 10 days of becoming "
                        f"an insider."
                    ),
                    filing_a="Form 4 (earliest)",
                    filing_b="Form 3 (missing)",
                    details={
                        "statutory_reference": "15 U.S.C. § 78p(a); Rule 16a-3(a)",
                        "form4_count": len(timeline.form4_filings),
                        "earliest_form4": (timeline.form4_filings[0].filing_date
                                           if timeline.form4_filings else ""),
                    },
                ))

        # Anomaly 2: Officer/Director without Form 5
        if (profile.is_officer or profile.is_director) and not timeline.form5_filings:
            # Form 5 is only required if there are transactions/holdings not
            # reported on Form 4. This is a low-severity informational flag.
            if profile.total_form4_transactions > 5:
                profile.anomalies.append(CrossReferenceAnomaly(
                    anomaly_type="NO_FORM_5_FILED",
                    severity="LOW",
                    description=(
                        f"Officer/Director {profile.insider_name} has "
                        f"{profile.total_form4_transactions} Form 4 transactions "
                        f"but no Form 5 annual statement. Form 5 is required if "
                        f"any transactions or holdings were not reported on Form 4."
                    ),
                    filing_a="Form 4 (multiple)",
                    filing_b="Form 5 (none filed)",
                    details={
                        "statutory_reference": "17 CFR § 240.16a-3(f)",
                        "is_officer": profile.is_officer,
                        "is_director": profile.is_director,
                    },
                ))

        # Anomaly 3: Burst trading pattern
        cls._check_burst_trading(profile)

        # Anomaly 4: Large dispositions without Form 144 notice
        cls._check_form144_coverage(profile)

    @classmethod
    def _check_burst_trading(cls, profile: ExecutiveFinancialProfile) -> None:
        """Detect burst trading patterns (many Form 4s in a short window)."""
        form4s = profile.ownership_timeline.form4_filings
        if len(form4s) < 5:
            return

        # Sort by filing date
        dated = []
        for f in form4s:
            try:
                dt = datetime.strptime(f.filing_date, "%Y-%m-%d").date()
                dated.append((dt, f))
            except (ValueError, TypeError):
                continue

        dated.sort(key=lambda x: x[0])

        # Sliding window: check for 5+ filings within 14 days
        for i in range(len(dated)):
            window_end = dated[i][0]
            window_start = window_end
            count = 0
            for j in range(i, -1, -1):
                if (window_end - dated[j][0]).days <= 14:
                    count += 1
                    window_start = dated[j][0]
                else:
                    break

            if count >= 5:
                profile.anomalies.append(CrossReferenceAnomaly(
                    anomaly_type="BURST_TRADING_PATTERN",
                    severity="MEDIUM",
                    description=(
                        f"{count} Form 4 filings within 14 days "
                        f"({window_start} to {window_end}). May indicate "
                        f"accelerated trading activity requiring closer review."
                    ),
                    filing_a=f"Window start: {window_start}",
                    filing_b=f"Window end: {window_end}",
                    details={
                        "filings_in_window": count,
                        "window_days": 14,
                        "window_start": str(window_start),
                        "window_end": str(window_end),
                    },
                ))
                # Only flag once per insider
                return

    @classmethod
    def _check_form144_coverage(cls, profile: ExecutiveFinancialProfile) -> None:
        """
        Check if large dispositions have corresponding Form 144 notices.

        Rule 144 requires filing Form 144 for proposed sales exceeding
        5,000 shares or $50,000 in aggregate during any 3-month period
        when the seller is an affiliate.
        """
        if profile.total_shares_disposed < 5000 and profile.total_value_disposed < 50000:
            return

        form144_count = len(profile.ownership_timeline.form144_filings)
        sale_codes = profile.transaction_code_distribution.get("S", 0)

        if sale_codes > 0 and form144_count == 0:
            # Only flag for affiliates (officers/directors/10% owners)
            if profile.is_officer or profile.is_director or profile.is_ten_percent_owner:
                profile.anomalies.append(CrossReferenceAnomaly(
                    anomaly_type="MISSING_FORM_144",
                    severity="MEDIUM",
                    description=(
                        f"Affiliate {profile.insider_name} disposed of "
                        f"{profile.total_shares_disposed:,.0f} shares "
                        f"(${profile.total_value_disposed:,.2f}) across "
                        f"{sale_codes} sale transaction(s) but no Form 144 "
                        f"notice of proposed sale was found. Rule 144(h) requires "
                        f"Form 144 for sales exceeding 5,000 shares or $50,000."
                    ),
                    filing_a=f"Form 4 sales: {sale_codes}",
                    filing_b="Form 144 (none found)",
                    details={
                        "statutory_reference": "17 CFR § 230.144(h)",
                        "total_shares_disposed": profile.total_shares_disposed,
                        "total_value_disposed": profile.total_value_disposed,
                        "sale_transactions": sale_codes,
                        "note": (
                            "Form 144 electronic filing became mandatory "
                            "April 13, 2023. For pre-2023 analysis periods, "
                            "paper Form 144 filings may not appear in EDGAR."
                        ),
                    },
                ))


def build_executive_profiles_from_pipeline(
    enhanced_results: Dict[str, Any],
    insider_trades: List[Dict[str, Any]],
    fsl_assessments: List[Dict[str, Any]] = None,
    submissions_cache: Dict[str, Dict] = None,
) -> Dict[str, Any]:
    """
    Top-level entry point for building executive profiles from pipeline data.

    Called by the forensic tracing orchestrator after all 15 nodes have run.

    Args:
        enhanced_results: Output from JLAWEnhancementOrchestrator.enhance()
        insider_trades: Raw insider trade records from the engine
        fsl_assessments: Optional FSL assessment dicts
        submissions_cache: Optional CIK -> submissions JSON cache

    Returns:
        Dict with profile results suitable for inclusion in tracing output
    """
    company_cik = enhanced_results.get("company_cik", "")
    company_name = enhanced_results.get("company_name", "")

    # Extract ticker from metadata if available
    metadata = enhanced_results.get("_metadata", {})
    if not company_name:
        company_name = metadata.get("company_name", "")
    if not company_cik:
        company_cik = metadata.get("company_cik", "")

    profiles = ExecutiveProfileBuilder.build_profiles(
        insider_trades=insider_trades,
        fsl_assessments=fsl_assessments or [],
        submissions_cache=submissions_cache,
        company_cik=company_cik,
        company_name=company_name,
    )

    # Build summary
    total_anomalies = sum(len(p.anomalies) for p in profiles.values())
    anomaly_types: Dict[str, int] = {}
    for p in profiles.values():
        for a in p.anomalies:
            anomaly_types[a.anomaly_type] = anomaly_types.get(a.anomaly_type, 0) + 1

    return {
        "profiles": {cik: p.to_dict() for cik, p in profiles.items()},
        "summary": {
            "total_insiders_profiled": len(profiles),
            "officers": sum(1 for p in profiles.values() if p.is_officer),
            "directors": sum(1 for p in profiles.values() if p.is_director),
            "ten_percent_owners": sum(1 for p in profiles.values() if p.is_ten_percent_owner),
            "total_transactions": sum(p.total_form4_transactions for p in profiles.values()),
            "total_anomalies": total_anomalies,
            "anomaly_types": anomaly_types,
        },
    }
