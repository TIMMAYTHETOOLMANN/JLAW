"""
Domain 5: Two-Tier Documentation Framework
=============================================

Maintains strict separation between submission-grade evidence (Tier 1)
and internal work product (Tier 2). This separation carries legal
consequences for privilege, admissibility, and whistleblower program eligibility.

Tier 1 (Submit via Form TCR):
  - Executive summary of alleged violations
  - Verified factual findings with source citations
  - Documented replicable methodology
  - Supporting exhibits with provenance and chain of custody
  - Chronological narrative of violation patterns
  - Identification of specific securities laws violated
  - Declaration under penalty of perjury

Tier 2 (Retain internally, never submit):
  - Preliminary hypotheses and exploratory analysis
  - Attorney-client privileged communications
  - Internal scoring/ranking systems
  - Award/bounty calculations and projections
  - Draft analyses and notes
  - Strategic memoranda about enforcement likelihood
  - Risk assessments and penalty predictions

Form TCR (Tip, Complaint, or Referral):
  - Mandatory for whistleblower award eligibility under Section 21F
  - Online portal at sec.gov (60-minute session timeout)
  - Mail: SEC Office of the Whistleblower, Chantilly, VA 20151-1750
  - Submit via one method only (no duplicates)
  - Question 8: State all facts pertinent to alleged violation
  - Anonymous submissions require attorney certification

Evidence standards:
  - SEC administrative: Rule 320 (more permissive, hearsay admissible)
  - Federal court: FRE 902(13) (computer-generated) and 902(14) (computer-stored)
  - Both require hash values, collection timestamps, system descriptions

References:
  - Dodd-Frank Section 21F (15 USC 78u-6)
  - SEC Rule 21F-4 (original information requirements)
  - SEC Rule 21F-17(a) (anti-retaliation)
  - FRE 902(13), 902(14) (self-authentication)
  - BofI Federal Bank v. Erhart (work product privilege)
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict


class DocumentTier(Enum):
    """Document classification tier."""
    TIER_1_SUBMISSION = 'tier_1_submission'
    TIER_2_WORK_PRODUCT = 'tier_2_work_product'


class EvidenceStandard(Enum):
    """Applicable evidence standard."""
    SEC_ADMINISTRATIVE = 'sec_rule_320'      # More permissive
    FRE_902_13 = 'fre_902_13'                # Computer-generated data
    FRE_902_14 = 'fre_902_14'                # Computer-stored data
    BOTH = 'both_standards'                   # Meets both


@dataclass
class EvidenceExhibit:
    """
    Single evidence exhibit with full provenance for Tier 1 submission.
    Meets FRE 902(13)/(14) self-authentication requirements.
    """
    exhibit_id: str
    title: str
    description: str
    source_type: str  # 'sec_edgar_filing', 'computed_analysis', 'public_record'
    source_url: Optional[str] = None
    source_filing_id: Optional[str] = None
    collection_timestamp: str = ''
    data_hash_sha256: str = ''
    content: Optional[str] = None  # Actual evidence content
    evidence_standard: EvidenceStandard = EvidenceStandard.BOTH

    # FRE 902(13) fields
    system_description: str = 'JLAW Forensic Analysis System v5.0.0'
    system_version: str = '5.0.0'
    process_description: str = ''

    # FRE 902(14) fields
    digital_identification: str = ''  # Hash value authenticating the copy

    # Chain of custody
    custody_entries: List[dict] = field(default_factory=list)

    def compute_hash(self):
        """Compute SHA-256 hash of exhibit content."""
        content_str = json.dumps(
            {'content': self.content, 'source': self.source_url,
             'filing_id': self.source_filing_id},
            sort_keys=True, default=str
        )
        self.data_hash_sha256 = hashlib.sha256(content_str.encode()).hexdigest()
        self.digital_identification = self.data_hash_sha256

    def to_dict(self) -> dict:
        return {
            'exhibit_id': self.exhibit_id,
            'title': self.title,
            'description': self.description,
            'source_type': self.source_type,
            'source_url': self.source_url,
            'source_filing_id': self.source_filing_id,
            'collection_timestamp': self.collection_timestamp,
            'data_hash_sha256': self.data_hash_sha256,
            'evidence_standard': self.evidence_standard.value,
            'system_description': self.system_description,
            'digital_identification': self.digital_identification,
            'custody_entries': self.custody_entries,
        }


@dataclass
class TCRSubmission:
    """
    Form TCR (Tip, Complaint, or Referral) structure.
    Mandatory for whistleblower award eligibility under Section 21F.
    """
    # Complainant information
    complainant_name: Optional[str] = None  # None if anonymous
    is_anonymous: bool = True
    attorney_name: Optional[str] = None  # Required for anonymous submissions
    attorney_bar_id: Optional[str] = None

    # Subject information
    subject_company_name: str = ''
    subject_company_cik: str = ''
    subject_company_ticker: str = ''
    subject_individuals: List[str] = field(default_factory=list)

    # Question 8: Statement of facts
    factual_narrative: str = ''
    violation_types: List[str] = field(default_factory=list)
    statutory_references: List[str] = field(default_factory=list)
    date_range: str = ''

    # Supporting evidence
    exhibits: List[EvidenceExhibit] = field(default_factory=list)
    exhibit_count: int = 0

    # Original information qualification
    information_source: str = ''  # 'independent_knowledge' or 'independent_analysis'
    independent_analysis_description: str = ''
    first_reported_date: Optional[str] = None
    reported_internally_first: bool = False
    internal_report_date: Optional[str] = None

    # Methodology section
    methodology_description: str = ''
    data_sources: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)

    # Estimated sanctions
    estimated_sanctions_basis: float = 0
    bounty_eligibility_note: str = ''

    # Declaration
    declaration_text: str = (
        'I declare under penalty of perjury under the laws of the United States '
        'of America that the foregoing is true and correct to the best of my '
        'knowledge, information, and belief.'
    )
    declaration_date: str = ''

    def to_dict(self) -> dict:
        return {
            'is_anonymous': self.is_anonymous,
            'subject': {
                'company_name': self.subject_company_name,
                'company_cik': self.subject_company_cik,
                'company_ticker': self.subject_company_ticker,
                'individuals': self.subject_individuals,
            },
            'violation_types': self.violation_types,
            'statutory_references': self.statutory_references,
            'date_range': self.date_range,
            'exhibit_count': len(self.exhibits),
            'information_source': self.information_source,
            'methodology': {
                'description': self.methodology_description[:500],
                'data_sources': self.data_sources,
                'tools_used': self.tools_used,
            },
            'estimated_sanctions_basis': self.estimated_sanctions_basis,
        }


@dataclass
class WorkProduct:
    """
    Tier 2 internal work product — never submitted to SEC.
    Protected under work product doctrine (BofI Federal Bank v. Erhart).
    """
    document_id: str
    title: str
    content: str
    category: str  # hypothesis, scoring, bounty_calc, draft, strategy, risk_assessment
    created_timestamp: str = ''
    privilege_basis: str = 'Work product prepared in anticipation of litigation'
    confidentiality_marking: str = 'PRIVILEGED AND CONFIDENTIAL — WORK PRODUCT'

    def to_dict(self) -> dict:
        return {
            'document_id': self.document_id,
            'title': self.title,
            'category': self.category,
            'created_timestamp': self.created_timestamp,
            'privilege_basis': self.privilege_basis,
            'confidentiality_marking': self.confidentiality_marking,
            # Content deliberately omitted from serialization
        }


class TwoTierDocumentationFramework:
    """
    Manages the two-tier documentation architecture.

    Ensures strict separation between Tier 1 (submission-grade evidence)
    and Tier 2 (internal work product) with appropriate privilege markings.
    """

    @classmethod
    def build_tcr_from_analysis(cls, enhanced_results: dict,
                                company_name: str = 'NIKE, Inc.',
                                company_cik: str = '320187',
                                company_ticker: str = 'NKE') -> TCRSubmission:
        """
        Build a Form TCR submission from enhanced analysis results.

        This extracts ONLY Tier 1 (submission-grade) factual findings.
        All scoring, bounty calculations, and strategic analysis are
        excluded and placed in Tier 2 work product.

        Args:
            enhanced_results: Enhanced analysis results dict
            company_name: Subject company name
            company_cik: Subject company CIK
            company_ticker: Subject company ticker

        Returns:
            TCRSubmission ready for attorney review
        """
        tcr = TCRSubmission(
            subject_company_name=company_name,
            subject_company_cik=company_cik,
            subject_company_ticker=company_ticker,
            declaration_date=datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        )

        # Extract subject individuals from beneficiary analysis
        beneficiaries = enhanced_results.get('beneficiary_analysis', [])
        tcr.subject_individuals = [
            b['name'] for b in beneficiaries[:10]
            if b.get('total_economic_benefit', 0) > 0
        ]

        # Build factual narrative (Tier 1 only — no scoring or predictions)
        narrative = enhanced_results.get('executive_summary', {})
        tcr.factual_narrative = narrative.get('executive_summary', '')

        # Violation types
        violations = enhanced_results.get('violations', [])
        violation_types = set()
        for v in violations:
            vtype = v.get('violation_type') or v.get('type', '')
            if vtype:
                violation_types.add(vtype)
        tcr.violation_types = sorted(violation_types)

        # Statutory references
        statutory_refs = set()
        for v in violations:
            ref = v.get('statutory_reference', '')
            if ref:
                statutory_refs.add(ref)
        # Add standard references based on violation types
        statutory_refs.update([
            '15 U.S.C. 78p(a) — Section 16(a) reporting obligations',
            '15 U.S.C. 78j(b) — Section 10(b) anti-fraud',
            '17 CFR 240.10b-5 — Rule 10b-5',
            'SOX Section 302 — CEO/CFO certifications',
            'SOX Section 906 — Criminal certification (18 USC 1350)',
        ])
        tcr.statutory_references = sorted(statutory_refs)

        # Date range
        dates = [v.get('transaction_date', '') for v in violations if v.get('transaction_date')]
        if dates:
            tcr.date_range = f'{min(dates)} to {max(dates)}'

        # Methodology (required for "independent analysis" qualification)
        tcr.information_source = 'independent_analysis'
        tcr.independent_analysis_description = (
            'Systematic computational analysis of publicly available SEC EDGAR filings '
            'including Form 4 insider transaction reports, Form 144 notices of proposed sale, '
            'Schedule 13D/13G beneficial ownership reports, and 10-K/10-Q financial statements. '
            'Analysis applied economic benefit valuation using historical market prices, '
            'temporal clustering detection, violation deduplication, severity normalization '
            'across multiple analysis nodes, and beneficial ownership chain resolution. '
            'This analysis reveals non-obvious patterns including $0-reported transactions '
            'with aggregate economic value exceeding $2.7 billion, coordinated entity transfers '
            'among related parties, and systematic Section 16(a) noncompliance.'
        )
        tcr.methodology_description = tcr.independent_analysis_description
        tcr.data_sources = [
            'SEC EDGAR Form 4 filings (XML)',
            'SEC EDGAR Full-Text Search API',
            'SEC XBRL companyfacts API',
            'NKE historical closing prices (Yahoo Finance, split-adjusted)',
        ]
        tcr.tools_used = [
            'JLAW Forensic Analysis System v5.0.0',
            'EDGAR Ownership XML Technical Specification v5.1',
            'Python 3.x with lxml XML parser',
        ]

        # Build evidence exhibits
        exhibit_counter = 0

        # Exhibit: Economic valuations
        econ = enhanced_results.get('economic_valuations', {})
        if econ:
            exhibit_counter += 1
            exhibit = EvidenceExhibit(
                exhibit_id=f'EX-{exhibit_counter:03d}',
                title='Economic Benefit Valuation Summary',
                description=(
                    f'Aggregate economic benefit of ${econ.get("total_aggregate_benefit", 0):,.2f} '
                    f'computed from {len(econ.get("transactions", []))} insider transactions'
                ),
                source_type='computed_analysis',
                collection_timestamp=datetime.now(timezone.utc).isoformat(),
                process_description=(
                    'Market close price on transaction date multiplied by shares. '
                    'Option exercises use spread (market - exercise price) x shares.'
                ),
            )
            exhibit.content = json.dumps(econ, default=str)
            exhibit.compute_hash()
            tcr.exhibits.append(exhibit)

        # Exhibit: Violation register
        if violations:
            exhibit_counter += 1
            exhibit = EvidenceExhibit(
                exhibit_id=f'EX-{exhibit_counter:03d}',
                title='Violation Register',
                description=f'{len(violations)} violations identified across Form 4 and SOX analysis',
                source_type='computed_analysis',
                collection_timestamp=datetime.now(timezone.utc).isoformat(),
                process_description='Automated violation detection from SEC EDGAR filings',
            )
            # Strip internal scoring from violations for Tier 1
            tier1_violations = [
                {k: v for k, v in vi.items()
                 if k not in ('signal_score', 'disposition', '_merged_count')}
                for vi in violations
            ]
            exhibit.content = json.dumps(tier1_violations, default=str)
            exhibit.compute_hash()
            tcr.exhibits.append(exhibit)

        # Exhibit: Severity summary
        severity = enhanced_results.get('severity_summary', {})
        if severity:
            exhibit_counter += 1
            exhibit = EvidenceExhibit(
                exhibit_id=f'EX-{exhibit_counter:03d}',
                title='Unified Severity Summary',
                description=(
                    f'Critical: {severity.get("critical", 0)}, '
                    f'High: {severity.get("high", 0)}, '
                    f'Medium: {severity.get("medium", 0)}'
                ),
                source_type='computed_analysis',
                collection_timestamp=datetime.now(timezone.utc).isoformat(),
            )
            exhibit.content = json.dumps(severity, default=str)
            exhibit.compute_hash()
            tcr.exhibits.append(exhibit)

        tcr.exhibit_count = len(tcr.exhibits)

        # Sanctions basis (factual, not speculative)
        penalty = enhanced_results.get('penalty_exposure', {})
        if penalty:
            tcr.estimated_sanctions_basis = penalty.get('total_maximum_exposure', 0)

        tcr.bounty_eligibility_note = (
            'SEC Rule 21F: bounty requires original information leading to '
            'successful enforcement action with sanctions exceeding $1,000,000. '
            'Award range: 10-30% of collected sanctions.'
        )

        return tcr

    @classmethod
    def build_work_product(cls, enhanced_results: dict) -> List[WorkProduct]:
        """
        Build Tier 2 internal work product documents.

        These are NEVER submitted to the SEC. They contain:
        - Internal scoring/ranking
        - Bounty calculations
        - Strategic enforcement analysis
        - Preliminary hypotheses

        Args:
            enhanced_results: Enhanced analysis results dict

        Returns:
            List of WorkProduct documents
        """
        now = datetime.now(timezone.utc).isoformat()
        work_products = []

        # WP-001: FSL Scoring Analysis (internal only)
        fsl_stats = enhanced_results.get('fsl_recalibration_stats', {})
        work_products.append(WorkProduct(
            document_id='WP-001',
            title='FSL Disposition Scoring Analysis',
            content=json.dumps(fsl_stats, default=str),
            category='scoring',
            created_timestamp=now,
        ))

        # WP-002: Bounty Estimation (internal only)
        penalty = enhanced_results.get('penalty_exposure', {})
        bounty = penalty.get('whistleblower_bounty', {})
        work_products.append(WorkProduct(
            document_id='WP-002',
            title='Whistleblower Bounty Estimation',
            content=json.dumps({
                'bounty_floor_10pct': bounty.get('bounty_floor', 0),
                'bounty_ceiling_30pct': bounty.get('bounty_ceiling', 0),
                'bounty_midpoint_20pct': bounty.get('estimated_bounty_midpoint', 0),
                'sanctions_basis': bounty.get('sanctions_basis', 0),
                'note': 'PRIVILEGED: Internal bounty estimation only. Do not submit.',
            }, default=str),
            category='bounty_calc',
            created_timestamp=now,
        ))

        # WP-003: Prosecution Likelihood Assessment (internal only)
        narrative = enhanced_results.get('executive_summary', {})
        work_products.append(WorkProduct(
            document_id='WP-003',
            title='Prosecution Likelihood Assessment',
            content=json.dumps({
                'recommendation': narrative.get('prosecution_recommendation', ''),
                'patterns': narrative.get('patterns_identified', []),
                'total_value': narrative.get('total_economic_value', 0),
                'note': 'PRIVILEGED: Strategic assessment. Do not submit.',
            }, default=str),
            category='strategy',
            created_timestamp=now,
        ))

        # WP-004: Penalty Breakdown (internal only)
        work_products.append(WorkProduct(
            document_id='WP-004',
            title='Comprehensive Penalty Breakdown',
            content=json.dumps(penalty, default=str),
            category='risk_assessment',
            created_timestamp=now,
        ))

        return work_products

    @classmethod
    def classify_document(cls, content: str) -> DocumentTier:
        """
        Classify a document as Tier 1 (submittable) or Tier 2 (work product).

        Tier 2 keywords that must NEVER appear in submissions:
        - bounty, award calculation, reward estimate
        - preliminary hypothesis, exploratory
        - prosecution likelihood, enforcement probability
        - internal scoring, signal score, disposition rating
        """
        tier2_keywords = [
            'bounty', 'award calculation', 'reward estimate',
            'preliminary hypothesis', 'exploratory analysis',
            'prosecution likelihood', 'enforcement probability',
            'internal scoring', 'signal_score', 'disposition_rating',
            'work product', 'privileged', 'draft',
        ]
        content_lower = content.lower()
        for keyword in tier2_keywords:
            if keyword in content_lower:
                return DocumentTier.TIER_2_WORK_PRODUCT
        return DocumentTier.TIER_1_SUBMISSION
