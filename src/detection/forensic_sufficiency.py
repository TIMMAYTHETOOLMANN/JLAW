"""
Forensic Sufficiency Layer (FSL)
================================

Every flagged $0 transaction gets classified into an investigable disposition:

    A) Likely benign (comp/admin) — document why
    B) Needs footnote extraction (classification depends on it)
    C) Needs price reconciliation (price should exist but doesn't)
    D) Needs cross-form reconciliation (material beneficial ownership change)
    E) Needs event correlation (timing vs disclosures is the risk)

Additionally, each transaction is enriched with:
    - price_required: Whether this code/table/security type demands a price
    - price_value_source: Where the price came from (table_field, footnote, derived, missing)
    - Footnote classification signals (10b5-1, tax withholding, entity transfer, etc.)
    - Late filing repeat offender scoring
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from collections import defaultdict
import logging
import re

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# FSL DISPOSITION CATEGORIES
# ═══════════════════════════════════════════════════════════════════

class FSLDisposition(Enum):
    """Forensic Sufficiency Layer — outcome classification."""
    A_LIKELY_BENIGN = "A"       # Comp/admin event — document why
    B_NEEDS_FOOTNOTE = "B"      # Classification depends on footnote content
    C_NEEDS_PRICE_RECON = "C"   # Price should exist but is missing/zero
    D_NEEDS_CROSS_FORM = "D"    # Changes beneficial ownership materially
    E_NEEDS_EVENT_CORR = "E"    # Timing vs disclosures is the risk


FSL_LABELS = {
    FSLDisposition.A_LIKELY_BENIGN:   "Likely benign (comp/admin) — document why",
    FSLDisposition.B_NEEDS_FOOTNOTE:  "Needs footnote extraction — classification depends on it",
    FSLDisposition.C_NEEDS_PRICE_RECON: "Needs price reconciliation — price should exist",
    FSLDisposition.D_NEEDS_CROSS_FORM:  "Needs cross-form reconciliation — material ownership change",
    FSLDisposition.E_NEEDS_EVENT_CORR:  "Needs event correlation — timing vs disclosures is the risk",
}


# ═══════════════════════════════════════════════════════════════════
# PRICE REQUIRED RULES
# ═══════════════════════════════════════════════════════════════════

# True = price MUST exist for this code; False = $0 may be expected
PRICE_REQUIRED_BY_CODE = {
    'S': True,    # Open-market sale — must have price
    'P': True,    # Open-market purchase — must have price
    'M': True,    # Option exercise — exercise price expected
    'C': True,    # Conversion of derivative — conversion price expected
    'X': True,    # Exercise of in-the-money derivative
    'E': True,    # Expiration of short derivative position
    'G': False,   # Gift — $0 is the expected norm
    'A': False,   # Award/grant — $0 typical for equity comp
    'I': False,   # Discretionary 16b-3 transaction
    'F': False,   # Tax withholding — $0 typical (shares surrendered)
    'V': False,   # Vesting — $0 expected
    'J': False,   # Other acquisition/disposition
    'K': False,   # Equity swap
    'L': False,   # Small acquisition under Rule 16a-6
    'W': False,   # Acquisition/disposition by will/laws of descent
    'Z': False,   # Deposit into/withdrawal from voting trust
    'D': False,   # Disposition to issuer
    'H': False,   # Expiration/conversion of derivative security
    'O': False,   # Exercise of out-of-the-money derivative
    'U': False,   # Disposition under tender offer
}


class PriceValueSource(Enum):
    """Where the price value came from in the filing."""
    TABLE_FIELD = "table_field"      # Populated in the XML price element
    FOOTNOTE = "footnote"            # Price referenced in footnotes only
    DERIVED = "derived"              # Calculated from exercise_price or other fields
    MISSING = "missing"              # Should exist but doesn't


def determine_price_required(transaction_code: str, is_derivative: bool) -> bool:
    """Determine whether a price is required for this transaction type."""
    code = transaction_code.upper()
    required = PRICE_REQUIRED_BY_CODE.get(code)
    if required is not None:
        return required
    # Derivative exercises generally require a price
    if is_derivative and code in ('M', 'C', 'X', 'E'):
        return True
    return False


def determine_price_source(
    price_per_share: float,
    exercise_price: Optional[float],
    footnotes: List[str],
    transaction_code: str,
) -> PriceValueSource:
    """Determine where the price value came from."""
    if price_per_share > 0:
        return PriceValueSource.TABLE_FIELD

    # Check if exercise price is available as a derived source
    if exercise_price and exercise_price > 0:
        return PriceValueSource.DERIVED

    # Check if footnotes mention a price
    price_patterns = re.compile(
        r'\$[\d,]+\.?\d*|per\s+share|price\s+of|exercise\s+price|'
        r'weighted.average|fair\s+market\s+value',
        re.IGNORECASE
    )
    combined = ' '.join(str(f) for f in footnotes)
    if price_patterns.search(combined):
        return PriceValueSource.FOOTNOTE

    return PriceValueSource.MISSING


# ═══════════════════════════════════════════════════════════════════
# FOOTNOTE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════

@dataclass
class FootnoteClassification:
    """Structured classification of Form 4 footnotes."""
    has_footnotes: bool = False
    mentions_10b5_1: bool = False
    plan_adoption_date_present: bool = False
    tax_withholding: bool = False
    conversion_ratio_present: bool = False
    entity_transfer: bool = False
    beneficial_control_retained: bool = False
    footnote_count: int = 0
    raw_footnotes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_footnotes": self.has_footnotes,
            "mentions_10b5_1": self.mentions_10b5_1,
            "plan_adoption_date_present": self.plan_adoption_date_present,
            "tax_withholding": self.tax_withholding,
            "conversion_ratio_present": self.conversion_ratio_present,
            "entity_transfer": self.entity_transfer,
            "beneficial_control_retained": self.beneficial_control_retained,
            "footnote_count": self.footnote_count,
        }


_FOOTNOTE_PATTERNS = {
    'mentions_10b5_1': re.compile(
        r'10b5-1|10b-5-1|rule\s+10b5|trading\s+plan|pre-arranged\s+plan',
        re.IGNORECASE
    ),
    'plan_adoption_date_present': re.compile(
        r'adopt(?:ed|ion)\s+(?:on|date)|plan\s+enter(?:ed|ing)|'
        r'established\s+(?:on|in)|effective\s+(?:date|as\s+of)',
        re.IGNORECASE
    ),
    'tax_withholding': re.compile(
        r'tax(?:es)?\s+withh(?:old|eld)|withh(?:old|eld)\s+(?:for|to)\s+(?:satisfy|cover|pay)\s+tax|'
        r'shares?\s+(?:surrendered|withheld)\s+(?:for|to)\s+(?:satisfy|cover|pay)|'
        r'net\s+settlement|tax\s+obligation',
        re.IGNORECASE
    ),
    'conversion_ratio_present': re.compile(
        r'conver(?:sion|t(?:ed|ing))\s+(?:at|ratio|rate|into)|'
        r'exchange\s+ratio|one-for-one|(?:\d+\.?\d*)\s*(?:to|:)\s*(?:\d+\.?\d*)',
        re.IGNORECASE
    ),
    'entity_transfer': re.compile(
        r'trust|llc|limited\s+liability|partnership|foundation|'
        r'transfer(?:red)?\s+to|entity|family\s+(?:trust|limited)',
        re.IGNORECASE
    ),
    'beneficial_control_retained': re.compile(
        r'beneficial(?:ly)?\s+own|indirect(?:ly)?\s+(?:own|held|control)|'
        r'control(?:led)?\s+by|voting\s+(?:power|control)|retained\s+(?:control|interest)|'
        r'deemed\s+(?:to\s+)?(?:be\s+)?(?:the\s+)?beneficial',
        re.IGNORECASE
    ),
}


def classify_footnotes(footnotes: List[str]) -> FootnoteClassification:
    """Classify footnote content into structured forensic signals."""
    result = FootnoteClassification()

    if not footnotes:
        return result

    result.has_footnotes = True
    result.footnote_count = len(footnotes)
    result.raw_footnotes = footnotes

    combined = ' '.join(str(f) for f in footnotes)

    for attr, pattern in _FOOTNOTE_PATTERNS.items():
        if pattern.search(combined):
            setattr(result, attr, True)

    return result


# ═══════════════════════════════════════════════════════════════════
# LATE FILING REPEAT OFFENDER ANALYSIS
# ═══════════════════════════════════════════════════════════════════

@dataclass
class RepeatOffenderProfile:
    """Late filing pattern analysis for a single insider."""
    insider_name: str
    role: str                      # "officer", "director", "10pct_owner"
    total_transactions: int = 0
    late_filings: int = 0
    late_pct: float = 0.0
    max_days_late: int = 0
    avg_days_late: float = 0.0
    is_repeat_offender: bool = False   # 2+ late filings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insider_name": self.insider_name,
            "role": self.role,
            "total_transactions": self.total_transactions,
            "late_filings": self.late_filings,
            "late_pct": round(self.late_pct, 1),
            "max_days_late": self.max_days_late,
            "avg_days_late": round(self.avg_days_late, 1),
            "is_repeat_offender": self.is_repeat_offender,
        }


def build_repeat_offender_profiles(
    filings: List[Any],
) -> Dict[str, RepeatOffenderProfile]:
    """
    Build repeat-offender profiles from parsed Form 4 filings.

    Args:
        filings: List of Form4Filing objects (must have
                 reporting_owner_name, is_officer, is_director,
                 is_ten_percent_owner, transactions attributes).
    Returns:
        Dict mapping insider name → RepeatOffenderProfile.
    """
    profiles: Dict[str, RepeatOffenderProfile] = {}

    for filing in filings:
        name = getattr(filing, 'reporting_owner_name', None)
        if not name:
            continue

        if name not in profiles:
            role = "officer" if getattr(filing, 'is_officer', False) else (
                "director" if getattr(filing, 'is_director', False) else (
                    "10pct_owner" if getattr(filing, 'is_ten_percent_owner', False) else "other"
                )
            )
            profiles[name] = RepeatOffenderProfile(insider_name=name, role=role)

        profile = profiles[name]
        for txn in getattr(filing, 'transactions', []):
            profile.total_transactions += 1
            if getattr(txn, 'is_late_filed', False):
                profile.late_filings += 1
                dl = getattr(txn, 'days_late', 0)
                if dl > profile.max_days_late:
                    profile.max_days_late = dl

    for profile in profiles.values():
        if profile.total_transactions > 0:
            profile.late_pct = (profile.late_filings / profile.total_transactions) * 100
        if profile.late_filings > 0:
            profile.avg_days_late = profile.max_days_late / profile.late_filings
        profile.is_repeat_offender = profile.late_filings >= 2

    return profiles


# ═══════════════════════════════════════════════════════════════════
# FSL CLASSIFICATION ENGINE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class FSLAssessment:
    """Full Forensic Sufficiency Layer assessment for one $0 transaction."""
    # Identity
    insider_name: str = ""
    accession_number: str = ""
    transaction_date: str = ""
    transaction_code: str = ""
    transaction_code_description: str = ""
    shares: float = 0.0
    security_title: str = ""

    # Table classification
    is_derivative: bool = False
    direct_indirect: str = "D"

    # Price analysis
    price_required: bool = False
    price_value_source: str = "missing"

    # Footnote analysis
    footnote_present: bool = False
    mentions_10b5_1: bool = False
    plan_adoption_date_present: bool = False
    tax_withholding_fn: bool = False
    entity_transfer_fn: bool = False
    beneficial_control_retained_fn: bool = False

    # Late filing
    is_late: bool = False
    days_late: int = 0
    is_repeat_offender: bool = False

    # FSL disposition
    disposition: str = ""
    disposition_label: str = ""
    disposition_reasons: List[str] = field(default_factory=list)

    # Signal score (0.0 = benign, 1.0 = maximum signal)
    signal_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insider_name": self.insider_name,
            "accession_number": self.accession_number,
            "transaction_date": self.transaction_date,
            "transaction_code": self.transaction_code,
            "transaction_code_description": self.transaction_code_description,
            "shares": self.shares,
            "security_title": self.security_title,
            "is_derivative": self.is_derivative,
            "direct_indirect": self.direct_indirect,
            "price_required": self.price_required,
            "price_value_source": self.price_value_source,
            "footnote_present": self.footnote_present,
            "mentions_10b5_1": self.mentions_10b5_1,
            "tax_withholding": self.tax_withholding_fn,
            "entity_transfer": self.entity_transfer_fn,
            "beneficial_control_retained": self.beneficial_control_retained_fn,
            "is_late": self.is_late,
            "days_late": self.days_late,
            "is_repeat_offender": self.is_repeat_offender,
            "disposition": self.disposition,
            "disposition_label": self.disposition_label,
            "disposition_reasons": self.disposition_reasons,
            "signal_score": round(self.signal_score, 3),
        }

    def to_table_row(self) -> Dict[str, str]:
        """Condensed row for diagnostic table output."""
        return {
            "Insider": self.insider_name,
            "Date": self.transaction_date,
            "Code": self.transaction_code,
            "Deriv": "Y" if self.is_derivative else "N",
            "Shares": f"{self.shares:,.0f}",
            "PriceReq": "Y" if self.price_required else "N",
            "PriceSrc": self.price_value_source,
            "FN": "Y" if self.footnote_present else "N",
            "10b5-1": "Y" if self.mentions_10b5_1 else "N",
            "Late": "Y" if self.is_late else "N",
            "FSL": self.disposition,
            "Signal": f"{self.signal_score:.2f}",
        }


def classify_fsl(
    txn_data: Dict[str, Any],
    footnote_cls: FootnoteClassification,
    repeat_offender: bool = False,
    cluster_member: bool = False,
    near_material_event: bool = False,
) -> FSLAssessment:
    """
    Classify a single $0 transaction into its FSL disposition.

    Decision tree (ordered by signal strength):
      C) price_required=True and price_source=missing → price reconciliation
      E) near material event OR cluster member → event correlation
      D) entity_transfer OR beneficial_control_retained → cross-form needed
      B) no footnotes on a non-benign code → needs footnote extraction
      A) everything else → likely benign (comp/admin)
    """
    code = txn_data.get('transaction_code', '').upper()
    is_derivative = txn_data.get('is_derivative', False)
    shares = txn_data.get('shares', 0.0)

    price_req = determine_price_required(code, is_derivative)
    price_src = determine_price_source(
        txn_data.get('price_per_share', 0.0),
        txn_data.get('exercise_price'),
        footnote_cls.raw_footnotes,
        code,
    )

    assessment = FSLAssessment(
        insider_name=txn_data.get('reporting_owner', ''),
        accession_number=txn_data.get('accession_number', ''),
        transaction_date=txn_data.get('transaction_date', ''),
        transaction_code=code,
        transaction_code_description=txn_data.get('transaction_code_description', ''),
        shares=shares,
        security_title=txn_data.get('security_title', ''),
        is_derivative=is_derivative,
        direct_indirect=txn_data.get('direct_indirect', 'D'),
        price_required=price_req,
        price_value_source=price_src.value,
        footnote_present=footnote_cls.has_footnotes,
        mentions_10b5_1=footnote_cls.mentions_10b5_1,
        plan_adoption_date_present=footnote_cls.plan_adoption_date_present,
        tax_withholding_fn=footnote_cls.tax_withholding,
        entity_transfer_fn=footnote_cls.entity_transfer,
        beneficial_control_retained_fn=footnote_cls.beneficial_control_retained,
        is_late=txn_data.get('is_late_filed', False),
        days_late=txn_data.get('days_late', 0),
        is_repeat_offender=repeat_offender,
    )

    # --- Disposition decision tree ---
    reasons = []
    signal = 0.0

    # C) Price reconciliation (highest technical signal)
    if price_req and price_src == PriceValueSource.MISSING:
        assessment.disposition = FSLDisposition.C_NEEDS_PRICE_RECON.value
        reasons.append(f"Code {code} requires price but price_value_source=missing")
        signal += 0.40

    # E) Event correlation
    elif near_material_event or cluster_member:
        assessment.disposition = FSLDisposition.E_NEEDS_EVENT_CORR.value
        if near_material_event:
            reasons.append("Transaction proximate to material corporate event")
            signal += 0.30
        if cluster_member:
            reasons.append("Part of multi-insider same-window cluster")
            signal += 0.25

    # D) Cross-form reconciliation
    elif footnote_cls.entity_transfer or footnote_cls.beneficial_control_retained:
        assessment.disposition = FSLDisposition.D_NEEDS_CROSS_FORM.value
        if footnote_cls.entity_transfer:
            reasons.append("Footnote references entity transfer (trust/LLC/partnership)")
        if footnote_cls.beneficial_control_retained:
            reasons.append("Footnote suggests beneficial control retained despite transfer")
        signal += 0.25

    # B) Needs footnote extraction
    elif not footnote_cls.has_footnotes and code not in ('A', 'F', 'V'):
        assessment.disposition = FSLDisposition.B_NEEDS_FOOTNOTE.value
        reasons.append(f"No footnotes present for Code {code} — classification depends on footnote content")
        signal += 0.20

    # A) Likely benign
    else:
        assessment.disposition = FSLDisposition.A_LIKELY_BENIGN.value
        if code in ('A', 'V', 'F'):
            reasons.append(f"Code {code} is standard compensation/admin event")
        elif footnote_cls.tax_withholding:
            reasons.append("Footnote confirms tax withholding")
        elif footnote_cls.has_footnotes:
            reasons.append("Footnotes present and no adverse signals detected")
        else:
            reasons.append("Transaction pattern consistent with routine activity")
        signal += 0.05

    # --- Signal modifiers ---
    if repeat_offender:
        reasons.append("Insider is a repeat late filer")
        signal += 0.15

    if assessment.is_late:
        reasons.append(f"Filed {assessment.days_late} business days late")
        signal += 0.10

    if footnote_cls.mentions_10b5_1 and not footnote_cls.plan_adoption_date_present:
        reasons.append("References 10b5-1 plan but no adoption date disclosed")
        signal += 0.10

    if code in ('S', 'P') and price_src == PriceValueSource.MISSING:
        reasons.append(f"Open-market {code} at $0 is extremely abnormal")
        signal += 0.30

    if code == 'M' and price_src == PriceValueSource.MISSING:
        reasons.append("Option exercise (M) at $0 with no exercise price — likely parser error or misclassification")
        signal += 0.20

    assessment.signal_score = min(1.0, signal)
    assessment.disposition_reasons = reasons
    assessment.disposition_label = FSL_LABELS.get(
        FSLDisposition(assessment.disposition), assessment.disposition
    )

    return assessment


# ═══════════════════════════════════════════════════════════════════
# DIAGNOSTIC TABLE GENERATION
# ═══════════════════════════════════════════════════════════════════

def generate_fsl_diagnostic_table(assessments: List[FSLAssessment]) -> str:
    """Generate a formatted text table of FSL assessments for all $0 transactions."""
    if not assessments:
        return "No zero-dollar transactions to assess."

    headers = ["#", "Insider", "Date", "Code", "D/ND", "Shares",
               "PriceReq?", "PriceSrc", "FN?", "10b5-1?", "Late?", "FSL", "Signal"]

    rows = []
    for i, a in enumerate(sorted(assessments, key=lambda x: -x.signal_score), 1):
        rows.append([
            str(i),
            a.insider_name[:25],
            a.transaction_date or "N/A",
            a.transaction_code,
            "D" if a.is_derivative else "ND",
            f"{a.shares:,.0f}",
            "Y" if a.price_required else "N",
            a.price_value_source[:8],
            "Y" if a.footnote_present else "N",
            "Y" if a.mentions_10b5_1 else "N",
            "Y" if a.is_late else "N",
            a.disposition,
            f"{a.signal_score:.2f}",
        ])

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(cells):
        return " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells))

    lines = [fmt_row(headers), "-+-".join("-" * w for w in widths)]
    for row in rows:
        lines.append(fmt_row(row))

    return "\n".join(lines)


def extract_top_signals(
    assessments: List[FSLAssessment],
    n: int = 10
) -> List[FSLAssessment]:
    """
    Extract the top N highest-signal items matching any of:
      - Code M with $0 and no footnote
      - Any S/P with $0
      - Clustered multi-insider events
      - Repeat late filers
    Falls back to raw signal_score ranking.
    """
    priority = []
    for a in assessments:
        hits = 0
        if a.transaction_code == 'M' and not a.footnote_present:
            hits += 3
        if a.transaction_code in ('S', 'P'):
            hits += 4
        if a.is_repeat_offender:
            hits += 2
        if a.disposition == FSLDisposition.C_NEEDS_PRICE_RECON.value:
            hits += 2
        if a.disposition == FSLDisposition.E_NEEDS_EVENT_CORR.value:
            hits += 1
        priority.append((hits, a.signal_score, a))

    priority.sort(key=lambda x: (-x[0], -x[1]))
    return [item[2] for item in priority[:n]]


def format_top_signals_report(top: List[FSLAssessment]) -> str:
    """Format a human-readable report of the top signal items."""
    if not top:
        return "No high-signal items identified."

    lines = []
    lines.append("=" * 80)
    lines.append("TOP FORENSIC SIGNALS — ITEMS REQUIRING IMMEDIATE INVESTIGATION")
    lines.append("=" * 80)

    for i, a in enumerate(top, 1):
        lines.append(f"\n{'─' * 70}")
        lines.append(f"  #{i}  {a.insider_name}")
        lines.append(f"  Date: {a.transaction_date}  |  Code: {a.transaction_code} "
                      f"({a.transaction_code_description})")
        lines.append(f"  Shares: {a.shares:,.0f}  |  Security: {a.security_title}")
        lines.append(f"  Derivative: {'Yes' if a.is_derivative else 'No'}  |  "
                      f"Direct/Indirect: {a.direct_indirect}")
        lines.append(f"  Price Required: {'YES' if a.price_required else 'No'}  |  "
                      f"Price Source: {a.price_value_source}")
        lines.append(f"  Footnote Present: {'Yes' if a.footnote_present else 'NO'}  |  "
                      f"10b5-1 Mentioned: {'Yes' if a.mentions_10b5_1 else 'No'}")
        lines.append(f"  Late Filed: {'YES (' + str(a.days_late) + ' days)' if a.is_late else 'No'}  |  "
                      f"Repeat Offender: {'YES' if a.is_repeat_offender else 'No'}")
        lines.append(f"  FSL Disposition: [{a.disposition}] {a.disposition_label}")
        lines.append(f"  Signal Score: {a.signal_score:.3f}")
        lines.append(f"  Reasons:")
        for reason in a.disposition_reasons:
            lines.append(f"    • {reason}")

    lines.append(f"\n{'=' * 80}")
    return "\n".join(lines)
