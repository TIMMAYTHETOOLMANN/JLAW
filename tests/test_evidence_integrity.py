"""
Evidence Integrity Tests
========================

Tests to validate evidence packaging and chain of custody integrity.
Ensures cryptographic verification, merkle tree construction,
and tamper detection work correctly.

Verification Points:
- SHA-256 hash generation and verification
- Merkle root computation
- Chain link validation
- Tamper detection
- Export format correctness
"""

import hashlib
import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import List

from src.reporting.evidence_packager import (
    EvidenceItem,
    EvidencePackage,
    EvidencePackager,
)
from src.reporting.chain_of_custody_logger import (
    CustodyAction,
    CustodyEventType,
    CustodyEvent,
    CustodyChain,
    ChainOfCustodyLogger,
    create_custody_logger,
)
from src.reporting.models import (
    SeverityLevel,
    ProsecutorialMerit,
    AgentSource,
    StatutoryReference,
    ExactQuote,
    DamageEstimate,
    ViolationEvidence,
    FilingAnalysisReport,
    ChainOfCustodyRecord,
)


class TestEvidenceItem:
    """Tests for EvidenceItem class."""
    
    def test_evidence_item_creation(self):
        """Test basic evidence item creation."""
        item = EvidenceItem(
            item_id="EV-001",
            item_type="quote",
            description="Test quote from filing",
            source_url="https://www.sec.gov/example",
            source_document="Form 4",
            extraction_timestamp=datetime.utcnow(),
            content="This is a test quote from the SEC filing.",
            content_type="text",
            filing_accession="0001234567-19-000001",
            filing_type="Form 4",
            filing_date="2019-03-22",
            document_section="Transactions",
        )
        
        assert item.item_id == "EV-001"
        assert item.item_type == "quote"
        assert item.content_hash != ""
        assert item.hash_algorithm == "SHA-256"
    
    def test_evidence_item_hash_generation(self):
        """Test automatic hash generation."""
        content = "Test content for hashing"
        expected_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        item = EvidenceItem(
            item_id="EV-002",
            item_type="document",
            description="Hash test",
            source_url="https://example.com",
            source_document="Test Doc",
            extraction_timestamp=datetime.utcnow(),
            content=content,
            content_type="text",
            filing_accession="123",
            filing_type="10-K",
            filing_date="2019-01-01",
            document_section="Test",
        )
        
        assert item.content_hash == expected_hash
    
    def test_evidence_item_to_dict(self):
        """Test serialization to dictionary."""
        item = EvidenceItem(
            item_id="EV-003",
            item_type="violation_record",
            description="Violation evidence",
            source_url="https://example.com",
            source_document="Form 4",
            extraction_timestamp=datetime.utcnow(),
            content="Violation details",
            content_type="json",
            filing_accession="456",
            filing_type="Form 4",
            filing_date="2019-02-01",
            document_section="Violations",
        )
        
        data = item.to_dict()
        
        assert data["item_id"] == "EV-003"
        assert data["item_type"] == "violation_record"
        assert "content_hash" in data
        assert "extraction_timestamp" in data


class TestEvidencePackage:
    """Tests for EvidencePackage class."""
    
    @pytest.fixture
    def sample_items(self) -> List[EvidenceItem]:
        """Create sample evidence items."""
        return [
            EvidenceItem(
                item_id=f"EV-{i:04d}",
                item_type="quote",
                description=f"Quote {i}",
                source_url="https://example.com",
                source_document="Form 4",
                extraction_timestamp=datetime.utcnow(),
                content=f"Content for item {i}",
                content_type="text",
                filing_accession="123",
                filing_type="Form 4",
                filing_date="2019-01-01",
                document_section="Transactions",
            )
            for i in range(1, 5)
        ]
    
    def test_package_creation(self, sample_items: List[EvidenceItem]):
        """Test evidence package creation."""
        package = EvidencePackage(
            package_id="PKG-001",
            case_id="JLAW-TEST",
            company_name="Test Corp",
            cik="123456",
        )
        
        for item in sample_items:
            package.add_item(item)
        
        assert len(package.items) == 4
        assert package.merkle_root != ""
        assert package.package_hash != ""
    
    def test_merkle_root_computation(self, sample_items: List[EvidenceItem]):
        """Test merkle root is correctly computed."""
        package = EvidencePackage(
            package_id="PKG-002",
            case_id="JLAW-TEST",
            company_name="Test Corp",
            cik="123456",
        )
        
        for item in sample_items:
            package.add_item(item)
        
        # Manually compute expected merkle root
        hashes = [item.content_hash for item in sample_items]
        
        # Level 1: pair hashes
        h01 = hashlib.sha256((hashes[0] + hashes[1]).encode()).hexdigest()
        h23 = hashlib.sha256((hashes[2] + hashes[3]).encode()).hexdigest()
        
        # Level 2: root
        expected_root = hashlib.sha256((h01 + h23).encode()).hexdigest()
        
        assert package.merkle_root == expected_root
    
    def test_integrity_verification(self, sample_items: List[EvidenceItem]):
        """Test package integrity verification."""
        package = EvidencePackage(
            package_id="PKG-003",
            case_id="JLAW-TEST",
            company_name="Test Corp",
            cik="123456",
        )
        
        for item in sample_items:
            package.add_item(item)
        
        # Package should verify successfully
        assert package.verify_integrity() is True
    
    def test_tamper_detection(self, sample_items: List[EvidenceItem]):
        """Test that tampering is detected."""
        package = EvidencePackage(
            package_id="PKG-004",
            case_id="JLAW-TEST",
            company_name="Test Corp",
            cik="123456",
        )
        
        for item in sample_items:
            package.add_item(item)
        
        original_merkle = package.merkle_root
        
        # Tamper with an item's content hash
        package.items[0].content_hash = "tampered_hash"
        
        # Verification should fail
        assert package.verify_integrity() is False
        
        # Restore and verify passes again
        package.items[0].content_hash = sample_items[0].content_hash
        package._update_integrity()
        assert package.verify_integrity() is True


class TestEvidencePackager:
    """Tests for EvidencePackager service."""
    
    @pytest.fixture
    def output_dir(self, tmp_path: Path) -> Path:
        """Create temporary output directory."""
        output = tmp_path / "evidence"
        output.mkdir(parents=True, exist_ok=True)
        return output
    
    @pytest.fixture
    def sample_violation(self) -> ViolationEvidence:
        """Create sample violation."""
        return ViolationEvidence(
            violation_id="V-TEST-001",
            violation_type="LATE_FORM4",
            severity=SeverityLevel.HIGH,
            statutory_reference=StatutoryReference(
                citation="15 U.S.C. § 78p(a)",
                title="Section 16(a)",
                summary="Insider reporting",
            ),
            description="Late Form 4 filing",
            exact_quotes=[
                ExactQuote(
                    quote_text="Filed 5 days late",
                    document_url="https://example.com",
                    document_section="Transaction Table",
                )
            ],
            document_url="https://example.com",
            document_section="Transactions",
            filing_accession="0001234567-19-000001",
            filing_date="2019-03-22",
            prosecutorial_merit=ProsecutorialMerit.STRONG,
            damage_estimate=DamageEstimate(
                civil_minimum=5000.0,
                civil_maximum=25000.0,
                disgorgement_estimate=0.0,
                criminal_exposure=False,
                prison_years_maximum=0,
                calculation_methodology="Standard"
            ),
            detected_by=AgentSource.BOTH,
            evidence_hash="abc123",
        )
    
    @pytest.fixture
    def sample_filing_report(self, sample_violation: ViolationEvidence) -> FilingAnalysisReport:
        """Create sample filing report."""
        return FilingAnalysisReport(
            accession_number="0001234567-19-000001",
            filing_type="Form 4",
            filing_date="2019-03-22",
            company_name="Test Corp",
            cik="123456",
            document_url="https://example.com",
            violations=[sample_violation],
            red_flags=[],
        )
    
    def test_packager_initialization(self, output_dir: Path):
        """Test packager initialization."""
        packager = EvidencePackager(output_dir=str(output_dir))
        assert packager.output_dir.exists()
    
    def test_create_package_from_filing(
        self,
        output_dir: Path,
        sample_filing_report: FilingAnalysisReport
    ):
        """Test package creation from filing report."""
        packager = EvidencePackager(output_dir=str(output_dir))
        
        package = packager.create_package_from_filing_report(
            case_id="JLAW-TEST",
            filing_report=sample_filing_report
        )
        
        assert package.package_id.startswith("EVPKG-")
        assert len(package.items) > 0
        assert len(package.custody_records) > 0
        assert package.verify_integrity() is True
    
    def test_create_package_from_violations(
        self,
        output_dir: Path,
        sample_violation: ViolationEvidence
    ):
        """Test package creation from violations list."""
        packager = EvidencePackager(output_dir=str(output_dir))
        
        package = packager.create_package_from_violations(
            case_id="JLAW-TEST",
            company_name="Test Corp",
            cik="123456",
            violations=[sample_violation]
        )
        
        assert len(package.items) >= 2  # Quote + violation record
        assert package.violation_ids == ["V-TEST-001"]
    
    def test_export_json(
        self,
        output_dir: Path,
        sample_filing_report: FilingAnalysisReport
    ):
        """Test JSON export."""
        packager = EvidencePackager(output_dir=str(output_dir))
        
        package = packager.create_package_from_filing_report(
            case_id="JLAW-TEST",
            filing_report=sample_filing_report
        )
        
        json_path = packager.export_package_json(package)
        
        assert json_path.exists()
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        assert data["package_id"] == package.package_id
        assert "items" in data
        assert "custody_records" in data
    
    def test_export_markdown(
        self,
        output_dir: Path,
        sample_filing_report: FilingAnalysisReport
    ):
        """Test Markdown export."""
        packager = EvidencePackager(output_dir=str(output_dir))
        
        package = packager.create_package_from_filing_report(
            case_id="JLAW-TEST",
            filing_report=sample_filing_report
        )
        
        md_path = packager.export_package_markdown(package)
        
        assert md_path.exists()
        
        with open(md_path, 'r') as f:
            content = f.read()
        
        assert "EVIDENCE PACKAGE" in content
        assert package.package_id in content
        assert "Merkle Root" in content


class TestChainOfCustodyLogger:
    """Tests for ChainOfCustodyLogger service."""
    
    @pytest.fixture
    def output_dir(self, tmp_path: Path) -> Path:
        """Create temporary output directory."""
        output = tmp_path / "custody"
        output.mkdir(parents=True, exist_ok=True)
        return output
    
    def test_logger_initialization(self, output_dir: Path):
        """Test logger initialization."""
        logger = ChainOfCustodyLogger(output_dir=str(output_dir))
        assert logger.output_dir.exists()
    
    def test_create_chain(self, output_dir: Path):
        """Test chain creation."""
        logger = ChainOfCustodyLogger(output_dir=str(output_dir))
        
        chain = logger.create_chain(
            case_id="JLAW-TEST",
            description="Test custody chain"
        )
        
        assert chain.chain_id.startswith("COC-")
        assert chain.case_id == "JLAW-TEST"
        assert chain.genesis_hash != ""
    
    def test_record_events(self, output_dir: Path):
        """Test recording custody events."""
        logger = ChainOfCustodyLogger(output_dir=str(output_dir))
        chain = logger.create_chain(case_id="JLAW-TEST")
        
        # Record collection
        event1 = logger.record_collection(
            chain_id=chain.chain_id,
            evidence_id="DOC-001",
            source="SEC EDGAR",
            content_hash="abc123"
        )
        
        assert event1.action == CustodyAction.COLLECTION
        assert event1.sequence_number == 1
        
        # Record analysis
        event2 = logger.record_analysis(
            chain_id=chain.chain_id,
            evidence_id="DOC-001",
            analyzer="OpenAI Agent",
            findings_hash="def456"
        )
        
        assert event2.action == CustodyAction.ANALYSIS
        assert event2.sequence_number == 2
        assert event2.previous_event_hash == event1.event_hash
    
    def test_chain_linking(self, output_dir: Path):
        """Test cryptographic chain linking."""
        logger = ChainOfCustodyLogger(output_dir=str(output_dir))
        chain = logger.create_chain(case_id="JLAW-TEST")
        
        # Record multiple events
        for i in range(5):
            logger.record_event(
                chain_id=chain.chain_id,
                action=CustodyAction.ANALYSIS,
                event_type=CustodyEventType.DOCUMENT,
                evidence_id=f"DOC-{i:03d}",
                evidence_description=f"Document {i}",
            )
        
        # Verify chain links
        for i, event in enumerate(chain.events):
            if i == 0:
                assert event.previous_event_hash == chain.genesis_hash
            else:
                assert event.previous_event_hash == chain.events[i - 1].event_hash
    
    def test_chain_verification(self, output_dir: Path):
        """Test chain integrity verification."""
        logger = ChainOfCustodyLogger(output_dir=str(output_dir))
        chain = logger.create_chain(case_id="JLAW-TEST")
        
        # Record events
        for i in range(3):
            logger.record_collection(
                chain_id=chain.chain_id,
                evidence_id=f"DOC-{i:03d}",
                source="SEC EDGAR",
            )
        
        # Verify chain
        is_valid, errors = logger.verify_chain(chain.chain_id)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_tamper_detection_in_chain(self, output_dir: Path):
        """Test that chain tampering is detected."""
        logger = ChainOfCustodyLogger(output_dir=str(output_dir))
        chain = logger.create_chain(case_id="JLAW-TEST")
        
        # Record events
        for i in range(3):
            logger.record_collection(
                chain_id=chain.chain_id,
                evidence_id=f"DOC-{i:03d}",
                source="SEC EDGAR",
            )
        
        # Ensure we have enough events
        assert len(chain.events) >= 2, "Need at least 2 events for tamper test"
        
        # Tamper with a field that IS included in the hash (evidence_id)
        original_evidence_id = chain.events[1].evidence_id
        chain.events[1].evidence_id = "TAMPERED-ID"
        
        # Verification should fail because the event hash won't match
        is_valid, errors = logger.verify_chain(chain.chain_id)
        
        assert is_valid is False
        assert len(errors) > 0
        
        # Alternative: tamper with the hash directly
        chain.events[1].evidence_id = original_evidence_id  # Restore
        chain.events[1].event_hash = "forged_hash_12345"
        
        # Verification should still fail
        is_valid, errors = logger.verify_chain(chain.chain_id)
        assert is_valid is False
    
    def test_seal_chain(self, output_dir: Path):
        """Test chain sealing."""
        logger = ChainOfCustodyLogger(output_dir=str(output_dir))
        chain = logger.create_chain(case_id="JLAW-TEST")
        
        logger.record_collection(
            chain_id=chain.chain_id,
            evidence_id="DOC-001",
            source="SEC EDGAR",
        )
        
        # Seal the chain
        seal_event = logger.seal_chain(chain.chain_id)
        
        assert chain.is_sealed is True
        assert seal_event.action == CustodyAction.SEAL
        
        # Cannot add more events to sealed chain
        with pytest.raises(ValueError, match="sealed"):
            logger.record_collection(
                chain_id=chain.chain_id,
                evidence_id="DOC-002",
                source="SEC EDGAR",
            )
    
    def test_export_markdown(self, output_dir: Path):
        """Test Markdown export of custody chain."""
        logger = ChainOfCustodyLogger(output_dir=str(output_dir))
        chain = logger.create_chain(case_id="JLAW-TEST")
        
        logger.record_collection(
            chain_id=chain.chain_id,
            evidence_id="DOC-001",
            source="SEC EDGAR",
        )
        logger.record_analysis(
            chain_id=chain.chain_id,
            evidence_id="DOC-001",
            analyzer="Test Analyzer",
        )
        
        md_path = logger.export_markdown(chain.chain_id)
        
        assert md_path.exists()
        
        with open(md_path, 'r') as f:
            content = f.read()
        
        assert "CHAIN OF CUSTODY" in content
        assert chain.chain_id in content
        assert "COLLECTION" in content
        assert "ANALYSIS" in content
    
    def test_persist_and_load_chain(self, output_dir: Path):
        """Test chain persistence and loading."""
        logger = ChainOfCustodyLogger(output_dir=str(output_dir))
        chain = logger.create_chain(case_id="JLAW-TEST")
        
        # Record events
        logger.record_collection(
            chain_id=chain.chain_id,
            evidence_id="DOC-001",
            source="SEC EDGAR",
        )
        
        # Persist
        json_path = logger.persist_chain(chain.chain_id)
        assert json_path.exists()
        
        # Create new logger and load
        logger2 = ChainOfCustodyLogger(output_dir=str(output_dir))
        loaded_chain = logger2.load_chain(str(json_path))
        
        assert loaded_chain.chain_id == chain.chain_id
        assert loaded_chain.event_count == chain.event_count
        assert loaded_chain.genesis_hash == chain.genesis_hash
    
    def test_convert_to_custody_records(self, output_dir: Path):
        """Test conversion to ChainOfCustodyRecord models."""
        logger = ChainOfCustodyLogger(output_dir=str(output_dir))
        chain = logger.create_chain(case_id="JLAW-TEST")
        
        logger.record_collection(
            chain_id=chain.chain_id,
            evidence_id="DOC-001",
            source="SEC EDGAR",
        )
        
        records = logger.convert_to_custody_records(chain.chain_id)
        
        assert len(records) == 1
        assert isinstance(records[0], ChainOfCustodyRecord)
        assert records[0].record_id.startswith("EVT-")


class TestCustodyEvent:
    """Tests for CustodyEvent class."""
    
    def test_event_creation(self):
        """Test event creation with auto hash."""
        event = CustodyEvent(
            event_id="EVT-001",
            sequence_number=1,
            action=CustodyAction.COLLECTION,
            event_type=CustodyEventType.DOCUMENT,
            evidence_id="DOC-001",
            evidence_description="Test document",
            actor="Test System",
            actor_type="system",
            previous_event_hash="genesis",
        )
        
        assert event.event_hash != ""
        assert event.verify() is True
    
    def test_event_verification(self):
        """Test event hash verification."""
        event = CustodyEvent(
            event_id="EVT-002",
            sequence_number=2,
            action=CustodyAction.ANALYSIS,
            event_type=CustodyEventType.ANALYSIS_RESULT,
            evidence_id="DOC-001",
            evidence_description="Analysis result",
            actor="Analyzer",
            actor_type="agent",
            previous_event_hash="previous123",
            content_hash="content456",
        )
        
        # Event should verify successfully when not tampered
        assert event.verify() is True
        
        # Tamper with a field that IS included in the hash (evidence_id)
        original_hash = event.event_hash
        event.evidence_id = "TAMPERED-ID"
        # Now verify() should fail because the recomputed hash won't match
        assert event.verify() is False
        
        # Restore and verify passes again
        event.evidence_id = "DOC-001"
        # But now the event_hash is still the original, and we're computing a new hash
        # with the original evidence_id - they should match
        assert event.verify() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
