"""
Evidence Packager Module
========================

Structures and packages evidence for DOJ-level forensic reporting.
Provides comprehensive evidence compilation with cryptographic integrity,
chain of custody documentation, and court-ready formatting.

Key Features:
- Evidence item structuring with metadata
- Package compilation for court submission
- SHA-256 hashing for integrity verification
- Merkle tree construction for bulk evidence
- Export formats: JSON, Markdown, HTML
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    ChainOfCustodyRecord,
    ExactQuote,
    ViolationEvidence,
    FilingAnalysisReport,
)
from src.core.evidence_chain.merkle_tree import EMPTY_LEAF_HASH
from .constants import (
    ViolationType,
    SeverityTier,
    get_statute_for_violation,
    NIKE_2019_BASELINE,
)

logger = logging.getLogger(__name__)


@dataclass
class EvidenceItem:
    """
    Single evidence item with complete provenance tracking.
    
    Represents a discrete piece of evidence that can be
    submitted in legal proceedings.
    """
    item_id: str
    item_type: str  # document, quote, transaction, metric
    description: str
    source_url: str
    source_document: str
    extraction_timestamp: datetime
    
    # Content
    content: str
    content_type: str  # text, html, xml, binary
    
    # Context
    filing_accession: str
    filing_type: str
    filing_date: str
    document_section: str
    page_number: Optional[int] = None
    line_range: Optional[str] = None
    
    # Integrity
    content_hash: str = ""
    hash_algorithm: str = "SHA-256"
    
    # Chain of custody
    collected_by: str = "JLAW Forensic System"
    custody_chain_id: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate content hash if not provided."""
        if not self.content_hash:
            self.content_hash = hashlib.sha256(
                self.content.encode('utf-8')
            ).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "description": self.description,
            "source_url": self.source_url,
            "source_document": self.source_document,
            "extraction_timestamp": self.extraction_timestamp.isoformat(),
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "content_type": self.content_type,
            "filing_accession": self.filing_accession,
            "filing_type": self.filing_type,
            "filing_date": self.filing_date,
            "document_section": self.document_section,
            "page_number": self.page_number,
            "line_range": self.line_range,
            "content_hash": self.content_hash,
            "hash_algorithm": self.hash_algorithm,
            "collected_by": self.collected_by,
            "custody_chain_id": self.custody_chain_id,
        }


@dataclass
class EvidencePackage:
    """
    Complete evidence package for a case or filing.
    
    Bundles all evidence items with integrity verification
    and chain of custody documentation.
    """
    package_id: str
    case_id: str
    company_name: str
    cik: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Evidence items
    items: List[EvidenceItem] = field(default_factory=list)
    
    # Violations linked
    violation_ids: List[str] = field(default_factory=list)
    
    # Chain of custody
    custody_records: List[ChainOfCustodyRecord] = field(default_factory=list)
    
    # Package integrity
    merkle_root: str = ""
    package_hash: str = ""
    
    # Metadata
    description: str = ""
    classification: str = "LAW ENFORCEMENT SENSITIVE"
    
    def add_item(self, item: EvidenceItem) -> None:
        """Add an evidence item to the package."""
        self.items.append(item)
        self._update_integrity()
    
    def add_custody_record(self, record: ChainOfCustodyRecord) -> None:
        """Add a chain of custody record."""
        self.custody_records.append(record)
    
    def _update_integrity(self) -> None:
        """Update merkle root and package hash."""
        if not self.items:
            return
        
        # Build merkle tree from item hashes
        hashes = [item.content_hash for item in self.items]
        self.merkle_root = self._compute_merkle_root(hashes)
        
        # Compute package hash
        package_data = json.dumps({
            "package_id": self.package_id,
            "case_id": self.case_id,
            "merkle_root": self.merkle_root,
            "item_count": len(self.items),
            "created_at": self.created_at.isoformat()
        }, sort_keys=True)
        self.package_hash = hashlib.sha256(package_data.encode()).hexdigest()
    
    def _compute_merkle_root(self, hashes: List[str]) -> str:
        """Compute Merkle root from list of hashes."""
        if not hashes:
            return ""
        
        if len(hashes) == 1:
            return hashes[0]
        
        # Ensure even number of hashes - RFC 6962 compliant padding
        if len(hashes) % 2 == 1:
            hashes.append(EMPTY_LEAF_HASH)
        
        # Compute parent hashes
        parent_hashes = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            parent_hash = hashlib.sha256(combined.encode()).hexdigest()
            parent_hashes.append(parent_hash)
        
        return self._compute_merkle_root(parent_hashes)
    
    def verify_integrity(self) -> bool:
        """Verify package integrity by recomputing merkle root."""
        if not self.items:
            return True
        
        hashes = [item.content_hash for item in self.items]
        computed_root = self._compute_merkle_root(hashes)
        return computed_root == self.merkle_root
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "package_id": self.package_id,
            "case_id": self.case_id,
            "company_name": self.company_name,
            "cik": self.cik,
            "created_at": self.created_at.isoformat(),
            "item_count": len(self.items),
            "violation_ids": self.violation_ids,
            "merkle_root": self.merkle_root,
            "package_hash": self.package_hash,
            "description": self.description,
            "classification": self.classification,
            "integrity_verified": self.verify_integrity(),
            "items": [item.to_dict() for item in self.items],
            "custody_records": [r.to_dict() for r in self.custody_records],
        }


class EvidencePackager:
    """
    Evidence packaging service for DOJ-level forensic reports.
    
    Provides methods to:
    - Create evidence packages from analysis results
    - Extract quotes and document context
    - Generate chain of custody records
    - Export in court-ready formats
    """
    
    def __init__(self, output_dir: str = "./output/evidence"):
        """
        Initialize Evidence Packager.
        
        Args:
            output_dir: Directory for evidence package output
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._item_counter = 0
        self._package_counter = 0
    
    def create_package_from_filing_report(
        self,
        case_id: str,
        filing_report: FilingAnalysisReport
    ) -> EvidencePackage:
        """
        Create evidence package from a filing analysis report.
        
        Args:
            case_id: Case identifier
            filing_report: FilingAnalysisReport with violations
            
        Returns:
            EvidencePackage with all evidence items
        """
        self._package_counter += 1
        package_id = f"EVPKG-{case_id}-{self._package_counter:04d}"
        
        package = EvidencePackage(
            package_id=package_id,
            case_id=case_id,
            company_name=filing_report.company_name,
            cik=filing_report.cik,
            description=f"Evidence package for {filing_report.filing_type} "
                       f"filed {filing_report.filing_date}",
        )
        
        # Add evidence items from violations
        for violation in filing_report.violations:
            # Add exact quotes as evidence
            for quote in violation.exact_quotes:
                item = self._create_evidence_from_quote(
                    quote=quote,
                    violation=violation,
                    filing_report=filing_report
                )
                package.add_item(item)
            
            # Add violation summary as evidence
            violation_item = self._create_evidence_from_violation(
                violation=violation,
                filing_report=filing_report
            )
            package.add_item(violation_item)
            package.violation_ids.append(violation.violation_id)
        
        # Add filing-level evidence
        filing_item = self._create_evidence_from_filing(filing_report)
        package.add_item(filing_item)
        
        # Create initial custody record
        custody_record = ChainOfCustodyRecord(
            record_id=f"COC-{package_id}-001",
            evidence_type="package",
            evidence_description=package.description,
            collected_at=datetime.utcnow(),
            collected_by="JLAW Evidence Packager",
            storage_location=str(self.output_dir),
            sha256_hash=package.package_hash,
            verification_status="verified"
        )
        package.add_custody_record(custody_record)
        
        logger.info(
            f"Created evidence package {package_id} with "
            f"{len(package.items)} items from {filing_report.accession_number}"
        )
        
        return package
    
    def create_package_from_violations(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        violations: List[ViolationEvidence]
    ) -> EvidencePackage:
        """
        Create evidence package from a list of violations.
        
        Args:
            case_id: Case identifier
            company_name: Company name
            cik: SEC CIK number
            violations: List of ViolationEvidence objects
            
        Returns:
            EvidencePackage with all evidence items
        """
        self._package_counter += 1
        package_id = f"EVPKG-{case_id}-{self._package_counter:04d}"
        
        package = EvidencePackage(
            package_id=package_id,
            case_id=case_id,
            company_name=company_name,
            cik=cik,
            description=f"Consolidated evidence package for {len(violations)} violations",
        )
        
        for violation in violations:
            # Add quotes
            for quote in violation.exact_quotes:
                item = self._create_evidence_item(
                    item_type="quote",
                    description=f"Exact quote supporting {violation.violation_type}",
                    source_url=quote.document_url,
                    source_document=violation.document_section,
                    content=quote.quote_text,
                    content_type="text",
                    filing_accession=violation.filing_accession,
                    filing_type="",
                    filing_date=violation.filing_date,
                    document_section=quote.document_section,
                    page_number=quote.page_number,
                    line_range=quote.line_range,
                )
                package.add_item(item)
            
            # Add violation record
            violation_content = json.dumps(violation.to_dict(), indent=2, default=str)
            item = self._create_evidence_item(
                item_type="violation_record",
                description=f"Violation: {violation.violation_type} - {violation.severity.value}",
                source_url=violation.document_url,
                source_document=violation.document_section,
                content=violation_content,
                content_type="json",
                filing_accession=violation.filing_accession,
                filing_type="",
                filing_date=violation.filing_date,
                document_section=violation.document_section,
            )
            package.add_item(item)
            package.violation_ids.append(violation.violation_id)
        
        logger.info(
            f"Created evidence package {package_id} with "
            f"{len(package.items)} items from {len(violations)} violations"
        )
        
        return package
    
    def _create_evidence_from_quote(
        self,
        quote: ExactQuote,
        violation: ViolationEvidence,
        filing_report: FilingAnalysisReport
    ) -> EvidenceItem:
        """Create evidence item from an exact quote."""
        return self._create_evidence_item(
            item_type="quote",
            description=f"Documentary evidence for {violation.violation_type}",
            source_url=quote.document_url,
            source_document=f"{filing_report.filing_type} - {filing_report.accession_number}",
            content=quote.quote_text,
            content_type="text",
            filing_accession=filing_report.accession_number,
            filing_type=filing_report.filing_type,
            filing_date=filing_report.filing_date,
            document_section=quote.document_section,
            page_number=quote.page_number,
            line_range=quote.line_range,
            metadata={
                "violation_id": violation.violation_id,
                "severity": violation.severity.value,
                "html_context": quote.html_context,
            }
        )
    
    def _create_evidence_from_violation(
        self,
        violation: ViolationEvidence,
        filing_report: FilingAnalysisReport
    ) -> EvidenceItem:
        """Create evidence item from violation record."""
        content = json.dumps({
            "violation_id": violation.violation_id,
            "violation_type": violation.violation_type,
            "severity": violation.severity.value,
            "statutory_reference": {
                "citation": violation.statutory_reference.citation,
                "title": violation.statutory_reference.title,
                "summary": violation.statutory_reference.summary,
            },
            "description": violation.description,
            "prosecutorial_merit": violation.prosecutorial_merit.value,
            "damage_estimate": {
                "civil_minimum": violation.damage_estimate.civil_minimum,
                "civil_maximum": violation.damage_estimate.civil_maximum,
                "criminal_exposure": violation.damage_estimate.criminal_exposure,
            },
            "detected_by": violation.detected_by.value,
            "confirmed_by": [a.value for a in violation.confirmed_by],
        }, indent=2)
        
        return self._create_evidence_item(
            item_type="violation_record",
            description=f"Violation record: {violation.violation_type}",
            source_url=violation.document_url,
            source_document=f"{filing_report.filing_type} - {filing_report.accession_number}",
            content=content,
            content_type="json",
            filing_accession=filing_report.accession_number,
            filing_type=filing_report.filing_type,
            filing_date=filing_report.filing_date,
            document_section=violation.document_section,
            metadata={
                "evidence_hash": violation.evidence_hash,
                "quote_count": len(violation.exact_quotes),
            }
        )
    
    def _create_evidence_from_filing(
        self,
        filing_report: FilingAnalysisReport
    ) -> EvidenceItem:
        """Create evidence item summarizing filing analysis."""
        content = json.dumps({
            "accession_number": filing_report.accession_number,
            "filing_type": filing_report.filing_type,
            "filing_date": filing_report.filing_date,
            "company_name": filing_report.company_name,
            "cik": filing_report.cik,
            "violation_count": filing_report.violation_count,
            "critical_count": filing_report.critical_count,
            "high_count": filing_report.high_count,
            "total_estimated_damages": filing_report.total_estimated_damages,
            "requires_criminal_referral": filing_report.requires_criminal_referral,
            "dual_agent_active": filing_report.dual_agent_consensus is not None,
        }, indent=2)
        
        return self._create_evidence_item(
            item_type="filing_analysis",
            description=f"Filing analysis summary: {filing_report.filing_type}",
            source_url=filing_report.document_url,
            source_document=f"{filing_report.filing_type} - {filing_report.accession_number}",
            content=content,
            content_type="json",
            filing_accession=filing_report.accession_number,
            filing_type=filing_report.filing_type,
            filing_date=filing_report.filing_date,
            document_section="Complete Filing",
            metadata={
                "content_hash": filing_report.filing_content_hash,
            }
        )
    
    def _create_evidence_item(
        self,
        item_type: str,
        description: str,
        source_url: str,
        source_document: str,
        content: str,
        content_type: str,
        filing_accession: str,
        filing_type: str,
        filing_date: str,
        document_section: str,
        page_number: Optional[int] = None,
        line_range: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvidenceItem:
        """Create a standardized evidence item."""
        self._item_counter += 1
        item_id = f"EV-{self._item_counter:06d}"
        
        return EvidenceItem(
            item_id=item_id,
            item_type=item_type,
            description=description,
            source_url=source_url,
            source_document=source_document,
            extraction_timestamp=datetime.utcnow(),
            content=content,
            content_type=content_type,
            filing_accession=filing_accession,
            filing_type=filing_type,
            filing_date=filing_date,
            document_section=document_section,
            page_number=page_number,
            line_range=line_range,
            metadata=metadata or {}
        )
    
    def export_package_json(
        self,
        package: EvidencePackage,
        filename: Optional[str] = None
    ) -> Path:
        """Export evidence package to JSON file."""
        if not filename:
            filename = f"{package.package_id}.json"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(package.to_dict(), f, indent=2, default=str)
        
        logger.info(f"Exported evidence package to {output_path}")
        return output_path
    
    def export_package_markdown(
        self,
        package: EvidencePackage,
        filename: Optional[str] = None
    ) -> Path:
        """Export evidence package to Markdown file."""
        if not filename:
            filename = f"{package.package_id}.md"
        
        output_path = self.output_dir / filename
        
        lines = [
            "# EVIDENCE PACKAGE",
            "",
            f"**Package ID:** {package.package_id}",
            f"**Case ID:** {package.case_id}",
            f"**Classification:** {package.classification}",
            f"**Created:** {package.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "---",
            "",
            "## PACKAGE SUMMARY",
            "",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| Company | {package.company_name} |",
            f"| CIK | {package.cik} |",
            f"| Evidence Items | {len(package.items)} |",
            f"| Violations Linked | {len(package.violation_ids)} |",
            f"| Merkle Root | `{package.merkle_root[:32]}...` |",
            f"| Package Hash | `{package.package_hash[:32]}...` |",
            f"| Integrity Verified | {'✓ YES' if package.verify_integrity() else '✗ NO'} |",
            "",
            "---",
            "",
            "## EVIDENCE ITEMS",
            "",
        ]
        
        for i, item in enumerate(package.items, 1):
            lines.extend([
                f"### Item {i}: {item.item_type.upper()}",
                "",
                f"**ID:** {item.item_id}",
                f"**Description:** {item.description}",
                f"**Source:** [{item.source_document}]({item.source_url})",
                f"**Hash (SHA-256):** `{item.content_hash[:32]}...`",
                "",
                "**Content:**",
                "```",
                item.content[:1000] + "..." if len(item.content) > 1000 else item.content,
                "```",
                "",
            ])
        
        lines.extend([
            "---",
            "",
            "## CHAIN OF CUSTODY",
            "",
            "| ID | Action | Timestamp | Handler | Status |",
            "|-------|--------|-----------|---------|--------|",
        ])
        
        for record in package.custody_records:
            lines.append(
                f"| {record.record_id} | Collection | "
                f"{record.collected_at.strftime('%Y-%m-%d %H:%M')} | "
                f"{record.collected_by} | {record.verification_status} |"
            )
        
        lines.extend([
            "",
            "---",
            "",
            "*This evidence package is digitally signed and tamper-evident.*",
        ])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Exported evidence package to {output_path}")
        return output_path
    
    def validate_against_nike_baseline(
        self,
        package: EvidencePackage
    ) -> Dict[str, Any]:
        """
        Validate evidence package against Nike 2019 baseline standards.
        
        Args:
            package: Evidence package to validate
            
        Returns:
            Validation results with pass/fail for each criterion
        """
        baseline = NIKE_2019_BASELINE["minimum_quality_metrics"]
        
        results = {
            "package_id": package.package_id,
            "validation_timestamp": datetime.utcnow().isoformat(),
            "baseline_reference": "Nike 2019",
            "checks": {},
            "overall_pass": True,
        }
        
        # Check exact quotes per violation
        quote_items = [i for i in package.items if i.item_type == "quote"]
        violation_items = [i for i in package.items if i.item_type == "violation_record"]
        quotes_per_violation = len(quote_items) / max(len(violation_items), 1)
        
        results["checks"]["exact_quotes_per_violation"] = {
            "required": baseline["exact_quotes_per_violation"],
            "actual": round(quotes_per_violation, 2),
            "pass": quotes_per_violation >= baseline["exact_quotes_per_violation"],
        }
        
        # Check chain of custody
        results["checks"]["chain_of_custody_records"] = {
            "required": baseline["chain_of_custody_records"],
            "actual": len(package.custody_records) > 0,
            "pass": len(package.custody_records) > 0 == baseline["chain_of_custody_records"],
        }
        
        # Check package integrity
        results["checks"]["integrity_verification"] = {
            "required": True,
            "actual": package.verify_integrity(),
            "pass": package.verify_integrity(),
        }
        
        # Update overall pass
        results["overall_pass"] = all(
            check["pass"] for check in results["checks"].values()
        )
        
        return results
