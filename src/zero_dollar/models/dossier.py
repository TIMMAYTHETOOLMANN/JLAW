"""
Forensic Dossier Output Model
==============================

Complete forensic analysis output package for zero-dollar transaction detection.

This module implements the final output structure per Section 13 of JLAW
Zero-Dollar Transaction Forensic Specification v1.0.

The ForensicDossier aggregates all analysis results, prosecutorial narrative,
and cryptographic evidence attestation into a courtroom-ready package.

Reference:
    - Section 13: Prosecutorial Narrative Generation
    - Section 9: Evidence Chain & Custody Protocol
"""

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Tuple

from src.zero_dollar.models import (
    Transaction,
    BehavioralRiskAssessment,
    EventProximityFlag,
    OwnershipChain,
)
from src.zero_dollar.modules import TemporalClusteringOutput


@dataclass
class ProsecutorialNarrative:
    """
    Legally precise prosecutorial narrative.
    
    Generated per Section 13 of specification. Suitable for:
    - SEC Enforcement Division referral memoranda
    - DOJ Criminal Division prosecution summaries
    - IRS-CI fraud investigation reports
    - Dodd-Frank whistleblower complaint substantiation
    
    Attributes:
        narrative_id: Unique narrative identifier
        case_id: Associated case identifier
        generated_timestamp: When narrative was generated
        subject_identification: Section 1 - Subject identification
        factual_summary: Section 2 - Transaction summary
        anomaly_analysis: Section 3 - Detailed anomaly analysis
        violation_analysis: Section 4 - Regulatory violation analysis
        damage_estimation: Section 5 - Damage calculation
        enforcement_recommendation: Section 6 - Agency routing & action
        evidence_summary: Section 7 - Evidence package summary
        regulatory_citations: List of applicable citations
    """
    narrative_id: str
    case_id: str
    generated_timestamp: datetime
    subject_identification: str
    factual_summary: str
    anomaly_analysis: str
    violation_analysis: str
    damage_estimation: str
    enforcement_recommendation: str
    evidence_summary: str
    regulatory_citations: List[str] = field(default_factory=list)
    
    def to_markdown(self) -> str:
        """Export narrative as Markdown document."""
        lines = [
            "# PROSECUTORIAL NARRATIVE",
            "",
            f"**Case ID:** {self.case_id}",
            f"**Narrative ID:** {self.narrative_id}",
            f"**Generated:** {self.generated_timestamp.isoformat()}",
            "",
            "---",
            "",
            "## 1. SUBJECT IDENTIFICATION",
            "",
            self.subject_identification,
            "",
            "---",
            "",
            "## 2. FACTUAL SUMMARY",
            "",
            self.factual_summary,
            "",
            "---",
            "",
            "## 3. ANOMALY ANALYSIS",
            "",
            self.anomaly_analysis,
            "",
            "---",
            "",
            "## 4. VIOLATION ANALYSIS",
            "",
            self.violation_analysis,
            "",
            "---",
            "",
            "## 5. DAMAGE ESTIMATION",
            "",
            self.damage_estimation,
            "",
            "---",
            "",
            "## 6. ENFORCEMENT RECOMMENDATION",
            "",
            self.enforcement_recommendation,
            "",
            "---",
            "",
            "## 7. EVIDENCE SUMMARY",
            "",
            self.evidence_summary,
            "",
            "---",
            "",
            "## REGULATORY CITATIONS",
            "",
        ]
        
        for citation in self.regulatory_citations:
            lines.append(f"- {citation}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'narrative_id': self.narrative_id,
            'case_id': self.case_id,
            'generated_timestamp': self.generated_timestamp.isoformat(),
            'subject_identification': self.subject_identification,
            'factual_summary': self.factual_summary,
            'anomaly_analysis': self.anomaly_analysis,
            'violation_analysis': self.violation_analysis,
            'damage_estimation': self.damage_estimation,
            'enforcement_recommendation': self.enforcement_recommendation,
            'evidence_summary': self.evidence_summary,
            'regulatory_citations': self.regulatory_citations,
        }


@dataclass
class ForensicDossier:
    """
    Complete forensic analysis output package.
    
    Contains all analysis results, narrative, and evidence attestation.
    Suitable for submission to:
        - SEC Enforcement Division
        - DOJ Criminal Division
        - IRS Criminal Investigation (IRS-CI)
        - State securities regulators
        - Whistleblower programs
    
    Attributes:
        case_id: Unique case identifier
        issuer_cik: SEC CIK of issuer company
        issuer_name: Name of issuer company
        issuer_ticker: Stock ticker symbol (if public)
        analysis_period: Tuple of (start_date, end_date)
        total_transactions_analyzed: Total transactions reviewed
        zero_dollar_transactions: Count of zero-dollar transactions
        temporal_analysis: Output from temporal clustering module
        event_proximity_analysis: List of event proximity flags
        ownership_chain_analysis: Ownership chain resolution output
        risk_assessment: Behavioral risk assessment
        prosecutorial_narrative: Generated narrative
        merkle_root_hash: Merkle tree root hash for evidence
        generated_timestamp: When dossier was generated
        system_version: JLAW system version
    """
    case_id: str
    issuer_cik: str
    issuer_name: str
    issuer_ticker: Optional[str]
    
    # Analysis Period
    analysis_period: Tuple[date, date]
    
    # Transaction Summary
    total_transactions_analyzed: int
    zero_dollar_transactions: int
    
    # Module Outputs
    temporal_analysis: TemporalClusteringOutput
    event_proximity_analysis: List[EventProximityFlag]
    ownership_chain_analysis: OwnershipChain
    
    # Risk Assessment
    risk_assessment: BehavioralRiskAssessment
    
    # Narrative
    prosecutorial_narrative: ProsecutorialNarrative
    
    # Evidence Integrity
    merkle_root_hash: str
    
    # Metadata
    generated_timestamp: datetime = field(default_factory=datetime.utcnow)
    system_version: str = "1.0.0"
    
    def export_json(self, path: Path) -> None:
        """
        Export dossier as JSON for API consumption.
        
        Args:
            path: Output file path
        """
        dossier_dict = {
            'case_id': self.case_id,
            'issuer_cik': self.issuer_cik,
            'issuer_name': self.issuer_name,
            'issuer_ticker': self.issuer_ticker,
            'analysis_period': {
                'start_date': self.analysis_period[0].isoformat(),
                'end_date': self.analysis_period[1].isoformat(),
            },
            'transaction_summary': {
                'total_analyzed': self.total_transactions_analyzed,
                'zero_dollar_count': self.zero_dollar_transactions,
            },
            'temporal_analysis': self.temporal_analysis.to_dict(),
            'event_proximity_analysis': [f.to_dict() for f in self.event_proximity_analysis],
            'ownership_chain_analysis': self.ownership_chain_analysis.to_dict(),
            'risk_assessment': self.risk_assessment.to_dict(),
            'prosecutorial_narrative': self.prosecutorial_narrative.to_dict(),
            'evidence_integrity': {
                'merkle_root_hash': self.merkle_root_hash,
            },
            'metadata': {
                'generated_timestamp': self.generated_timestamp.isoformat(),
                'system_version': self.system_version,
            },
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(dossier_dict, f, indent=2, ensure_ascii=False)
    
    def export_markdown(self, path: Path) -> None:
        """
        Export dossier as Markdown document.
        
        Args:
            path: Output file path
        """
        lines = [
            "# FORENSIC DOSSIER",
            "",
            f"**Case ID:** {self.case_id}",
            f"**Issuer:** {self.issuer_name} (CIK: {self.issuer_cik})",
            f"**Ticker:** {self.issuer_ticker or 'N/A'}",
            f"**Generated:** {self.generated_timestamp.isoformat()}",
            f"**System Version:** {self.system_version}",
            "",
            "---",
            "",
            "## EXECUTIVE SUMMARY",
            "",
            f"**Analysis Period:** {self.analysis_period[0].isoformat()} to {self.analysis_period[1].isoformat()}",
            f"**Total Transactions Analyzed:** {self.total_transactions_analyzed}",
            f"**Zero-Dollar Transactions:** {self.zero_dollar_transactions}",
            "",
            "### Risk Assessment",
            "",
            f"- **Risk Level:** {self.risk_assessment.risk_level}",
            f"- **Risk Score:** {self.risk_assessment.risk_score:.1f}/100",
            f"- **Prosecutorial Priority:** {self.risk_assessment.prosecutorial_priority}",
            f"- **Temporal Clusters Detected:** {self.temporal_analysis.cluster_count}",
            f"- **Event Proximity Flags:** {len(self.event_proximity_analysis)}",
            f"- **Ownership Entities:** {len(self.ownership_chain_analysis.entities)}",
            "",
            "---",
            "",
        ]
        
        # Add prosecutorial narrative
        lines.append(self.prosecutorial_narrative.to_markdown())
        
        # Add evidence integrity
        lines.extend([
            "",
            "---",
            "",
            "## EVIDENCE INTEGRITY",
            "",
            f"**Merkle Root Hash:** `{self.merkle_root_hash}`",
            "",
            "This forensic dossier is protected by RFC 6962 compliant Merkle tree",
            "cryptographic attestation. All evidence artifacts are verifiable against",
            "the root hash using provided Merkle proofs.",
            "",
        ])
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def export_evidence_package(self, path: Path) -> None:
        """
        Export complete evidence package as directory structure.
        
        Creates:
            - dossier.json
            - narrative.md
            - evidence_integrity.txt
            - transactions.json
            - temporal_analysis.json
            - event_proximity.json
            - ownership_chain.json
            - risk_assessment.json
        
        Args:
            path: Output directory path
        """
        # Create output directory
        path.mkdir(parents=True, exist_ok=True)
        
        # Export main dossier
        self.export_json(path / "dossier.json")
        
        # Export narrative as Markdown
        self.export_markdown(path / "narrative.md")
        
        # Export evidence integrity
        with open(path / "evidence_integrity.txt", 'w') as f:
            f.write(f"JLAW Forensic Evidence Package\n")
            f.write(f"=" * 80 + "\n\n")
            f.write(f"Case ID: {self.case_id}\n")
            f.write(f"Generated: {self.generated_timestamp.isoformat()}\n")
            f.write(f"System Version: {self.system_version}\n\n")
            f.write(f"Merkle Root Hash (RFC 6962):\n")
            f.write(f"{self.merkle_root_hash}\n\n")
            f.write(f"This hash provides cryptographic attestation for all evidence\n")
            f.write(f"artifacts in this package. Any modification to evidence will\n")
            f.write(f"result in a different root hash, invalidating the chain.\n")
        
        # Export individual components
        with open(path / "temporal_analysis.json", 'w') as f:
            json.dump(self.temporal_analysis.to_dict(), f, indent=2)
        
        with open(path / "event_proximity.json", 'w') as f:
            json.dump([e.to_dict() for e in self.event_proximity_analysis], f, indent=2)
        
        with open(path / "ownership_chain.json", 'w') as f:
            json.dump(self.ownership_chain_analysis.to_dict(), f, indent=2)
        
        with open(path / "risk_assessment.json", 'w') as f:
            json.dump(self.risk_assessment.to_dict(), f, indent=2)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'case_id': self.case_id,
            'issuer_cik': self.issuer_cik,
            'issuer_name': self.issuer_name,
            'issuer_ticker': self.issuer_ticker,
            'analysis_period': {
                'start_date': self.analysis_period[0].isoformat(),
                'end_date': self.analysis_period[1].isoformat(),
            },
            'total_transactions_analyzed': self.total_transactions_analyzed,
            'zero_dollar_transactions': self.zero_dollar_transactions,
            'temporal_analysis': self.temporal_analysis.to_dict(),
            'event_proximity_analysis': [f.to_dict() for f in self.event_proximity_analysis],
            'ownership_chain_analysis': self.ownership_chain_analysis.to_dict(),
            'risk_assessment': self.risk_assessment.to_dict(),
            'prosecutorial_narrative': self.prosecutorial_narrative.to_dict(),
            'merkle_root_hash': self.merkle_root_hash,
            'generated_timestamp': self.generated_timestamp.isoformat(),
            'system_version': self.system_version,
        }
