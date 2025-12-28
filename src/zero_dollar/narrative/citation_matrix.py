"""
Regulatory Citation Matrix
===========================

Comprehensive citation database for regulatory violations and evidence standards
per Section 10 of JLAW Zero-Dollar Transaction Forensic Specification v1.0.

This module provides structured citations for:
- Securities Law (Section 10.1)
- Tax Law (Section 10.2)
- Antitrust Law (Section 10.3)
- Evidence Law (Section 10.4)

Reference:
    - Section 10: Regulatory Citation Matrix
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Citation:
    """
    Structured regulatory or statutory citation.
    
    Attributes:
        code: Legal code reference (e.g., "17 CFR § 240.10b-5")
        title: Short title of provision
        description: Brief description of applicability
        agency: Enforcing agency (SEC, IRS, DOJ, FTC)
    """
    code: str
    title: str
    description: str
    agency: str
    
    def format(self) -> str:
        """Format citation for narrative inclusion."""
        return f"{self.code} - {self.title} ({self.agency})"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'code': self.code,
            'title': self.title,
            'description': self.description,
            'agency': self.agency,
        }


# =============================================================================
# Section 10.1: Securities Law Citations
# =============================================================================

SECURITIES_CITATIONS = {
    "10b-5": Citation(
        code="17 CFR § 240.10b-5",
        title="Rule 10b-5 - Employment of Manipulative and Deceptive Devices",
        description="Prohibits fraud, misrepresentation, and omissions in securities transactions; covers MNPI-based trading",
        agency="SEC"
    ),
    "16a-3": Citation(
        code="17 CFR § 240.16a-3",
        title="Rule 16a-3 - Initial Statements of Beneficial Ownership",
        description="Requires insiders to file Form 3 within 10 days of becoming an insider",
        agency="SEC"
    ),
    "16a-2": Citation(
        code="17 CFR § 240.16a-2",
        title="Rule 16a-2 - Persons and Transactions Subject to Section 16",
        description="Defines reporting persons and transactions subject to Form 4 filing requirements",
        agency="SEC"
    ),
    "13d-1": Citation(
        code="17 CFR § 240.13d-1",
        title="Rule 13d-1 - Filing of Schedule 13D",
        description="Requires disclosure of beneficial ownership exceeding 5% within 10 days",
        agency="SEC"
    ),
    "13d-3": Citation(
        code="17 CFR § 240.13d-3",
        title="Rule 13d-3 - Determination of Beneficial Owner",
        description="Defines beneficial ownership as voting or investment power",
        agency="SEC"
    ),
    "section-16a": Citation(
        code="15 U.S.C. § 78p(a)",
        title="Section 16(a) - Directors, Officers, and Principal Stockholders",
        description="Imposes reporting requirements for insiders holding >10% equity",
        agency="SEC"
    ),
    "section-16b": Citation(
        code="15 U.S.C. § 78p(b)",
        title="Section 16(b) - Short-Swing Profit Recovery",
        description="Liability for profits from purchase and sale within 6 months",
        agency="SEC"
    ),
    "section-10b": Citation(
        code="15 U.S.C. § 78j(b)",
        title="Section 10(b) - Manipulative and Deceptive Devices",
        description="Prohibits use of manipulative or deceptive devices in securities trading",
        agency="SEC"
    ),
    "section-13d": Citation(
        code="15 U.S.C. § 78m(d)",
        title="Section 13(d) - Public Availability of Information",
        description="Requires disclosure of beneficial ownership >5%",
        agency="SEC"
    ),
}

# =============================================================================
# Section 10.2: Tax Law Citations
# =============================================================================

TAX_CITATIONS = {
    "7201": Citation(
        code="26 U.S.C. § 7201",
        title="Tax Evasion",
        description="Willful attempt to evade or defeat any tax; applies to unreported compensation",
        agency="IRS"
    ),
    "7206": Citation(
        code="26 U.S.C. § 7206",
        title="Fraud and False Statements",
        description="Making false statements in tax returns; covers disguised compensation",
        agency="IRS"
    ),
    "section-83": Citation(
        code="26 U.S.C. § 83",
        title="Property Transferred in Connection with Performance of Services",
        description="Taxation of property transferred for services; zero-dollar transfers may constitute taxable compensation",
        agency="IRS"
    ),
    "section-61": Citation(
        code="26 U.S.C. § 61",
        title="Gross Income Defined",
        description="All income from whatever source derived, including compensation for services",
        agency="IRS"
    ),
    "section-162m": Citation(
        code="26 U.S.C. § 162(m)",
        title="Deduction Limit on Executive Compensation",
        description="$1M deduction limit on executive compensation; incentive to structure non-salary compensation",
        agency="IRS"
    ),
    "section-409a": Citation(
        code="26 U.S.C. § 409A",
        title="Inclusion in Gross Income of Deferred Compensation",
        description="Nonqualified deferred compensation rules; zero-dollar equity may trigger penalties",
        agency="IRS"
    ),
}

# =============================================================================
# Section 10.3: Antitrust Law Citations
# =============================================================================

ANTITRUST_CITATIONS = {
    "hsr-act": Citation(
        code="15 U.S.C. § 18a",
        title="Hart-Scott-Rodino Antitrust Improvements Act",
        description="Premerger notification for transactions exceeding thresholds; fragmented zero-dollar transfers may circumvent",
        agency="FTC/DOJ"
    ),
    "clayton-act-7": Citation(
        code="15 U.S.C. § 18",
        title="Clayton Act § 7 - Mergers and Acquisitions",
        description="Prohibits acquisitions that substantially lessen competition",
        agency="FTC/DOJ"
    ),
}

# =============================================================================
# Section 10.4: Evidence Law Citations
# =============================================================================

EVIDENCE_CITATIONS = {
    "fre-901": Citation(
        code="Fed. R. Evid. 901",
        title="Authenticating or Identifying Evidence",
        description="Requirement to authenticate evidence through witness testimony or distinctive characteristics",
        agency="Federal Courts"
    ),
    "fre-902-13": Citation(
        code="Fed. R. Evid. 902(13)",
        title="Certified Records Generated by Electronic Process",
        description="Self-authentication of electronic records with hash verification and certification",
        agency="Federal Courts"
    ),
    "fre-902-14": Citation(
        code="Fed. R. Evid. 902(14)",
        title="Certified Data Copied from Electronic Device",
        description="Self-authentication of data copied from electronic devices with hash verification",
        agency="Federal Courts"
    ),
    "fre-1006": Citation(
        code="Fed. R. Evid. 1006",
        title="Summaries to Prove Content",
        description="Allows summaries of voluminous records that cannot be conveniently examined in court",
        agency="Federal Courts"
    ),
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_citations_for_anomaly(anomaly_type: str) -> List[Citation]:
    """
    Get relevant citations for specific anomaly type.
    
    Args:
        anomaly_type: Type of anomaly (e.g., "TEMPORAL_CLUSTERING", "EVENT_PROXIMITY")
        
    Returns:
        List of applicable Citation objects
    """
    citations = []
    
    if anomaly_type == "TEMPORAL_CLUSTERING":
        citations.extend([
            SECURITIES_CITATIONS["10b-5"],
            SECURITIES_CITATIONS["section-16a"],
            TAX_CITATIONS["section-83"],
        ])
    elif anomaly_type == "EVENT_PROXIMITY":
        citations.extend([
            SECURITIES_CITATIONS["10b-5"],
            SECURITIES_CITATIONS["section-10b"],
        ])
    elif anomaly_type == "OWNERSHIP_CHAIN":
        citations.extend([
            SECURITIES_CITATIONS["13d-3"],
            SECURITIES_CITATIONS["section-13d"],
        ])
    elif anomaly_type == "LATE_FILING":
        citations.extend([
            SECURITIES_CITATIONS["16a-3"],
            SECURITIES_CITATIONS["section-16a"],
        ])
    elif anomaly_type == "HSR_CIRCUMVENTION":
        citations.extend([
            ANTITRUST_CITATIONS["hsr-act"],
            ANTITRUST_CITATIONS["clayton-act-7"],
        ])
    
    # Always include evidence authentication
    citations.extend([
        EVIDENCE_CITATIONS["fre-902-13"],
        EVIDENCE_CITATIONS["fre-902-14"],
    ])
    
    return citations


def get_citations_for_risk_tier(risk_level: str) -> List[Citation]:
    """
    Get citations based on risk level.
    
    Args:
        risk_level: Risk level (CRITICAL, HIGH, MODERATE, LOW)
        
    Returns:
        List of applicable Citation objects
    """
    citations = []
    
    if risk_level in ("CRITICAL", "HIGH"):
        # Include all primary violation citations
        citations.extend([
            SECURITIES_CITATIONS["10b-5"],
            SECURITIES_CITATIONS["section-10b"],
            SECURITIES_CITATIONS["section-16a"],
            SECURITIES_CITATIONS["section-16b"],
            TAX_CITATIONS["7201"],
            TAX_CITATIONS["section-83"],
        ])
    elif risk_level == "MODERATE":
        citations.extend([
            SECURITIES_CITATIONS["16a-3"],
            SECURITIES_CITATIONS["section-16a"],
            TAX_CITATIONS["section-83"],
        ])
    else:  # LOW
        citations.extend([
            SECURITIES_CITATIONS["section-16a"],
        ])
    
    # Always include evidence standards
    citations.extend([
        EVIDENCE_CITATIONS["fre-902-13"],
        EVIDENCE_CITATIONS["fre-1006"],
    ])
    
    return citations


def format_citation(citation: Citation) -> str:
    """
    Format citation for narrative inclusion.
    
    Args:
        citation: Citation object
        
    Returns:
        Formatted citation string
    """
    return f"**{citation.code}** - {citation.title}\n    {citation.description}"


def compile_regulatory_citations(
    anomaly_types: List[str],
    risk_level: str,
) -> List[Citation]:
    """
    Compile all applicable citations for case.
    
    Args:
        anomaly_types: List of detected anomaly types
        risk_level: Overall risk level
        
    Returns:
        Deduplicated list of all applicable citations
    """
    citations = []
    
    # Add citations for each anomaly type
    for anomaly_type in anomaly_types:
        citations.extend(get_citations_for_anomaly(anomaly_type))
    
    # Add risk-based citations
    citations.extend(get_citations_for_risk_tier(risk_level))
    
    # Deduplicate by code
    seen_codes = set()
    unique_citations = []
    for citation in citations:
        if citation.code not in seen_codes:
            seen_codes.add(citation.code)
            unique_citations.append(citation)
    
    return unique_citations


def get_all_citations() -> Dict[str, Dict[str, Citation]]:
    """
    Get all citation categories.
    
    Returns:
        Dictionary with citation categories
    """
    return {
        'securities': SECURITIES_CITATIONS,
        'tax': TAX_CITATIONS,
        'antitrust': ANTITRUST_CITATIONS,
        'evidence': EVIDENCE_CITATIONS,
    }
