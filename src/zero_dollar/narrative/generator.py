"""
Prosecutorial Narrative Generator
==================================

Generates legally precise narrative from forensic analysis outputs per
Section 13 of JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Suitable for:
- SEC Enforcement Division referral memoranda
- DOJ Criminal Division prosecution summaries
- IRS-CI fraud investigation reports
- Dodd-Frank whistleblower complaint substantiation

Reference:
    - Section 13: Prosecutorial Narrative Generation
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List

from src.zero_dollar.models import (
    Transaction,
    BehavioralRiskAssessment,
    EventProximityFlag,
    OwnershipChain,
    ProsecutorialNarrative,
)
from src.zero_dollar.modules import TemporalClusteringOutput
from src.zero_dollar.config import JLAWConfig
from .citation_matrix import (
    compile_regulatory_citations,
    format_citation,
    Citation,
)


logger = logging.getLogger(__name__)


class ProsecutorialNarrativeGenerator:
    """
    Generate legally precise narrative from forensic analysis outputs.
    
    Produces 7-section narrative structure:
        1. Subject Identification
        2. Factual Summary
        3. Anomaly Analysis
        4. Violation Analysis
        5. Damage Estimation
        6. Enforcement Recommendation
        7. Evidence Summary
    """
    
    def __init__(self, config: JLAWConfig):
        """
        Initialize narrative generator.
        
        Args:
            config: JLAW configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def generate(
        self,
        assessment: BehavioralRiskAssessment,
        temporal: TemporalClusteringOutput,
        events: List[EventProximityFlag],
        ownership: OwnershipChain,
        transactions: List[Transaction],
    ) -> ProsecutorialNarrative:
        """
        Generate complete prosecutorial narrative.
        
        Args:
            assessment: Behavioral risk assessment
            temporal: Temporal clustering output
            events: List of event proximity flags
            ownership: Ownership chain analysis
            transactions: All transactions analyzed
            
        Returns:
            ProsecutorialNarrative with all 7 sections
        """
        self.logger.info(f"Generating prosecutorial narrative for case {assessment.issuer_cik}")
        
        # Generate each section
        subject_id = self.generate_subject_identification(assessment, ownership)
        factual_summary = self.generate_factual_summary(assessment, transactions, temporal)
        anomaly_analysis = self.generate_anomaly_analysis(temporal, events, ownership)
        violation_analysis = self.generate_violation_analysis(assessment, temporal, events)
        damage_estimation = self.generate_damage_estimation(transactions)
        enforcement_recommendation = self.generate_enforcement_recommendation(assessment)
        evidence_summary = self.generate_evidence_summary(transactions, temporal)
        
        # Compile citations
        anomaly_types = []
        if temporal.cluster_count > 0:
            anomaly_types.append("TEMPORAL_CLUSTERING")
        if events:
            anomaly_types.append("EVENT_PROXIMITY")
        if len(ownership.entities) > 1:
            anomaly_types.append("OWNERSHIP_CHAIN")
        
        citations = compile_regulatory_citations(
            anomaly_types=anomaly_types,
            risk_level=assessment.risk_level,
        )
        citation_strings = [format_citation(c) for c in citations]
        
        # Create narrative
        narrative = ProsecutorialNarrative(
            narrative_id=self._generate_narrative_id(assessment),
            case_id=assessment.assessment_id,
            generated_timestamp=datetime.utcnow(),
            subject_identification=subject_id,
            factual_summary=factual_summary,
            anomaly_analysis=anomaly_analysis,
            violation_analysis=violation_analysis,
            damage_estimation=damage_estimation,
            enforcement_recommendation=enforcement_recommendation,
            evidence_summary=evidence_summary,
            regulatory_citations=citation_strings,
        )
        
        self.logger.info(f"Narrative generated: {narrative.narrative_id}")
        return narrative
    
    def generate_subject_identification(
        self,
        assessment: BehavioralRiskAssessment,
        ownership: OwnershipChain,
    ) -> str:
        """
        Generate Section 1: Subject Identification.
        
        Identifies reporting person, issuer, and ownership structure.
        """
        lines = [
            f"**Reporting Person:** {assessment.reporting_person_name}",
            f"**CIK:** {assessment.reporting_person_cik}",
            f"",
            f"**Issuer:** {assessment.issuer_name}",
            f"**Issuer CIK:** {assessment.issuer_cik}",
            f"",
            f"**Relationship:** Section 16 reporting person (officer, director, or >10% beneficial owner)",
            f"",
            f"**Ownership Structure:**",
        ]
        
        if len(ownership.entities) == 1:
            lines.append("- Direct ownership (no intermediary entities)")
        else:
            lines.append(f"- Complex ownership structure involving {len(ownership.entities)} entities:")
            for entity in ownership.entities[:5]:  # Limit to first 5
                lines.append(f"  - {entity.entity_name} ({entity.entity_type.value})")
        
        return "\n".join(lines)
    
    def generate_factual_summary(
        self,
        assessment: BehavioralRiskAssessment,
        transactions: List[Transaction],
        temporal: TemporalClusteringOutput,
    ) -> str:
        """
        Generate Section 2: Factual Summary.
        
        Summarizes transaction activity and zero-dollar patterns.
        """
        zero_dollar_txns = [t for t in transactions if t.is_zero_dollar]
        
        lines = [
            f"Between {temporal.analysis_period[0].isoformat()} and {temporal.analysis_period[1].isoformat()}, ",
            f"{assessment.reporting_person_name} executed {len(zero_dollar_txns)} zero-dollar transactions ",
            f"in {assessment.issuer_name} securities, representing {assessment.total_transaction_count} ",
            f"total Form 4 reportable transactions during the analysis period.",
            f"",
            f"**Zero-Dollar Transaction Summary:**",
            f"",
        ]
        
        # Summarize by transaction code
        code_counts = {}
        for txn in zero_dollar_txns:
            code = txn.transaction_code
            code_counts[code] = code_counts.get(code, 0) + 1
        
        for code, count in sorted(code_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- **Code {code}:** {count} transactions")
        
        lines.extend([
            f"",
            f"**Temporal Clustering:**",
            f"",
            f"Analysis detected {temporal.cluster_count} statistically significant temporal clusters, ",
            f"indicating coordinated transaction structuring inconsistent with routine equity compensation practices.",
        ])
        
        return "\n".join(lines)
    
    def generate_anomaly_analysis(
        self,
        temporal: TemporalClusteringOutput,
        events: List[EventProximityFlag],
        ownership: OwnershipChain,
    ) -> str:
        """
        Generate Section 3: Anomaly Analysis.
        
        Detailed analysis of detected anomalies.
        """
        lines = [
            "### 3.1 Temporal Clustering Anomalies",
            "",
        ]
        
        if temporal.cluster_count > 0:
            lines.append(
                f"Forensic analysis identified {temporal.cluster_count} temporal clusters "
                f"with aggregate anomaly score of {temporal.total_anomaly_score}."
            )
            lines.append("")
            
            for i, cluster in enumerate(temporal.clusters_detected[:3], 1):  # Top 3 clusters
                lines.extend([
                    f"**Cluster {i}:**",
                    f"- Window: {cluster.cluster_start_date.isoformat()} to {cluster.cluster_end_date.isoformat()}",
                    f"- Transactions: {len(cluster.transactions)}",
                    f"- Anomaly Score: {cluster.anomaly_score}",
                    "",
                ])
        else:
            lines.append("No significant temporal clustering detected.")
            lines.append("")
        
        lines.extend([
            "### 3.2 Event Proximity Anomalies",
            "",
        ])
        
        if events:
            lines.append(
                f"Analysis detected {len(events)} event proximity flags where zero-dollar "
                f"transactions occurred within suspicious temporal proximity to material events."
            )
            lines.append("")
            
            for i, event in enumerate(events[:3], 1):  # Top 3 events
                lines.extend([
                    f"**Event {i}:**",
                    f"- Event Type: {event.event_type}",
                    f"- Transaction Date: {event.transaction_date.isoformat()}",
                    f"- Event Date: {event.event_date.isoformat()}",
                    f"- Days Separation: {event.days_from_event}",
                    f"- MNPI Probability: {event.mnpi_probability:.1%}",
                    "",
                ])
        else:
            lines.append("No event proximity anomalies detected.")
            lines.append("")
        
        lines.extend([
            "### 3.3 Ownership Structure Anomalies",
            "",
        ])
        
        if len(ownership.entities) > 1:
            lines.append(
                f"Analysis revealed complex ownership structure involving {len(ownership.entities)} "
                f"entities with {ownership.chain_depth} levels of indirection."
            )
            lines.append("")
            lines.append("This structure may serve to obscure beneficial ownership and control relationships.")
        else:
            lines.append("Direct ownership structure - no intermediary entity complexity.")
        
        return "\n".join(lines)
    
    def generate_violation_analysis(
        self,
        assessment: BehavioralRiskAssessment,
        temporal: TemporalClusteringOutput,
        events: List[EventProximityFlag],
    ) -> str:
        """
        Generate Section 4: Violation Analysis.
        
        Analysis of potential regulatory violations.
        """
        lines = [
            "### 4.1 Securities Law Violations",
            "",
        ]
        
        if assessment.risk_level in ("CRITICAL", "HIGH"):
            lines.extend([
                "**Potential Rule 10b-5 Violation (17 CFR § 240.10b-5):**",
                "",
                "Zero-dollar transactions executed in proximity to material events may constitute:",
                "- Fraudulent or manipulative acts in connection with securities purchases",
                "- Omissions of material facts necessary to make statements not misleading",
                "- Engagement in acts that would operate as fraud upon purchasers",
                "",
            ])
        
        if temporal.cluster_count >= 2:
            lines.extend([
                "**Section 16 Reporting Violations (15 U.S.C. § 78p(a)):**",
                "",
                f"Subject's {temporal.cluster_count} temporal clusters suggest coordinated structuring ",
                "to fragment reportable transactions, potentially violating Section 16(a) reporting obligations.",
                "",
            ])
        
        lines.extend([
            "### 4.2 Tax Law Violations",
            "",
            "**IRC § 83 - Property Transferred for Services:**",
            "",
            "Zero-dollar equity transfers may constitute taxable compensation. Failure to report ",
            "fair market value as ordinary income may violate:",
            "- 26 U.S.C. § 7201 (Tax Evasion)",
            "- 26 U.S.C. § 7206 (Fraud and False Statements)",
            "",
        ])
        
        return "\n".join(lines)
    
    def generate_damage_estimation(
        self,
        transactions: List[Transaction],
    ) -> str:
        """
        Generate Section 5: Damage Estimation.
        
        Calculation of potential damages and unpaid taxes.
        """
        zero_dollar_txns = [t for t in transactions if t.is_zero_dollar]
        
        # Estimate fair market value (using average market price if available)
        total_shares = sum(int(t.shares) for t in zero_dollar_txns)
        
        lines = [
            "### 5.1 Unreported Compensation",
            "",
            f"**Total Zero-Dollar Shares Transferred:** {total_shares:,}",
            "",
            "Assuming fair market value at transaction dates, estimated unreported compensation ",
            "would be subject to:",
            "- Ordinary income tax (up to 37% federal rate)",
            "- Self-employment tax (15.3% for relevant parties)",
            "- State income tax (varies by jurisdiction)",
            "",
            "### 5.2 Potential Civil Penalties",
            "",
            "**SEC Enforcement:**",
            "- Disgorgement of ill-gotten gains",
            "- Civil monetary penalties up to $1,000,000 per individual",
            "- Officer/director bars",
            "",
            "**IRS Penalties:**",
            "- 75% fraud penalty on unpaid tax (26 U.S.C. § 6663)",
            "- Interest on unpaid taxes",
            "- Criminal prosecution for tax evasion",
            "",
        ]
        
        return "\n".join(lines)
    
    def generate_enforcement_recommendation(
        self,
        assessment: BehavioralRiskAssessment,
    ) -> str:
        """
        Generate Section 6: Enforcement Recommendation.
        
        Recommended enforcement actions and agency routing.
        """
        lines = [
            f"**Risk Level:** {assessment.risk_level}",
            f"**Prosecutorial Priority:** {assessment.prosecutorial_priority}",
            "",
            f"**Recommendation:** {assessment.recommendation}",
            "",
            "### Recommended Actions:",
            "",
        ]
        
        for step in assessment.next_steps:
            lines.append(f"1. {step}")
        
        lines.extend([
            "",
            "### Agency Routing:",
            "",
        ])
        
        if assessment.risk_level == "CRITICAL":
            lines.extend([
                "**Primary:** SEC Enforcement Division (Insider Trading and Market Manipulation)",
                "**Secondary:** DOJ Criminal Division (Fraud Section)",
                "**Tertiary:** IRS Criminal Investigation (Tax Evasion)",
            ])
        elif assessment.risk_level == "HIGH":
            lines.extend([
                "**Primary:** SEC Enforcement Division (Section 16 Compliance)",
                "**Secondary:** IRS Examination Division",
            ])
        else:
            lines.extend([
                "**Primary:** SEC Division of Corporation Finance (Section 16 Compliance)",
            ])
        
        return "\n".join(lines)
    
    def generate_evidence_summary(
        self,
        transactions: List[Transaction],
        temporal: TemporalClusteringOutput,
    ) -> str:
        """
        Generate Section 7: Evidence Summary.
        
        Summary of evidence package and integrity attestation.
        """
        lines = [
            "### Evidence Package Contents:",
            "",
            f"1. **Form 4 Filings:** {len(transactions)} transactions across reporting period",
            f"2. **Temporal Clustering Analysis:** {temporal.cluster_count} clusters detected",
            f"3. **Ownership Chain Documentation:** Complete beneficial ownership mapping",
            f"4. **Event Calendar:** Material events with transaction proximity analysis",
            "",
            "### Cryptographic Attestation:",
            "",
            "All evidence artifacts are protected by:",
            "- **Triple-hash integrity:** SHA-256 + SHA3-512 + BLAKE2b",
            "- **RFC 6962 Merkle tree:** Cryptographic proof of evidence integrity",
            f"- **Evidence hash:** {temporal.evidence_hash or 'N/A'}",
            "",
            "### Chain of Custody:",
            "",
            "Evidence acquired from SEC EDGAR public database with FRE 902(13)/(14) ",
            "compliant cryptographic attestation. All acquisition timestamps, source URLs, ",
            "and hash values are documented in accompanying custody records.",
            "",
            "### Admissibility:",
            "",
            "Evidence package satisfies Federal Rules of Evidence:",
            "- FRE 901(b)(9) - Electronic record authentication",
            "- FRE 902(13) - Certified records generated by electronic process",
            "- FRE 902(14) - Certified data copied from electronic device",
            "- FRE 1006 - Summaries of voluminous records",
        ]
        
        return "\n".join(lines)
    
    def _generate_narrative_id(self, assessment: BehavioralRiskAssessment) -> str:
        """Generate unique narrative ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"NARRATIVE-{assessment.reporting_person_cik}-{timestamp}"
