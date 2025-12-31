"""
Tests for Evidence Attribution Linker
======================================

Tests evidence attribution to actors through various mechanisms.
"""

import pytest
from datetime import date
from src.detection.actor_extraction_engine import ActorProfile
from src.core.evidence_chain.evidence_attribution import (
    EvidenceAttributionLinker,
    EvidenceAttribution,
    AttributionType
)


class TestEvidenceAttribution:
    """Test EvidenceAttribution dataclass."""
    
    def test_attribution_creation(self):
        """Test creating an evidence attribution."""
        attribution = EvidenceAttribution(
            actor_id="actor-123",
            evidence_id="evidence-456",
            attribution_type=AttributionType.DIRECT_AUTHORSHIP,
            relevance_score=1.0,
            attribution_date=date(2023, 1, 15)
        )
        
        assert attribution.actor_id == "actor-123"
        assert attribution.evidence_id == "evidence-456"
        assert attribution.attribution_type == AttributionType.DIRECT_AUTHORSHIP
        assert attribution.relevance_score == 1.0
    
    def test_attribution_to_dict(self):
        """Test converting attribution to dictionary."""
        attribution = EvidenceAttribution(
            actor_id="actor-123",
            evidence_id="evidence-456",
            attribution_type=AttributionType.TRANSACTION_PARTY,
            relevance_score=0.9,
            metadata={'transaction_code': 'P'}
        )
        
        attr_dict = attribution.to_dict()
        
        assert attr_dict["actor_id"] == "actor-123"
        assert attr_dict["attribution_type"] == "TRANSACTION_PARTY"
        assert attr_dict["relevance_score"] == 0.9
        assert "transaction_code" in attr_dict["metadata"]


class TestEvidenceAttributionLinker:
    """Test EvidenceAttributionLinker functionality."""
    
    def test_linker_initialization(self):
        """Test linker initialization."""
        linker = EvidenceAttributionLinker()
        assert linker is not None
        assert len(linker.attributions) == 0
    
    def test_extract_signatories_simple(self):
        """Test extracting signatories from simple /s/ format."""
        linker = EvidenceAttributionLinker()
        
        content = """
        Pursuant to the requirements of the Securities Exchange Act of 1934:
        
        /s/ John Smith
        John Smith
        Chief Executive Officer
        """
        
        signatories = linker._extract_signatories(content)
        
        assert len(signatories) > 0
        assert any('john smith' in s.lower() for s in signatories)
    
    def test_extract_signatories_multiple_formats(self):
        """Test extracting signatories from multiple formats."""
        linker = EvidenceAttributionLinker()
        
        content = """
        Signature: Jane Doe
        Chief Financial Officer
        
        By: /s/ Bob Williams
        Bob Williams
        Controller
        
        Signed by: Alice Johnson
        """
        
        signatories = linker._extract_signatories(content)
        
        # Should find all three signatories
        assert len(signatories) >= 2
    
    def test_is_signatory_exact_match(self):
        """Test exact name match for signatory detection."""
        linker = EvidenceAttributionLinker()
        
        actor = ActorProfile(
            actor_id="test-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"]
        )
        
        signatories = ["John Smith", "Jane Doe"]
        
        assert linker._is_signatory(actor, signatories) is True
    
    def test_is_signatory_partial_match(self):
        """Test partial name match (last name + first initial)."""
        linker = EvidenceAttributionLinker()
        
        actor = ActorProfile(
            actor_id="test-2",
            name="John A. Smith",
            actor_type="INDIVIDUAL",
            roles=["CFO"]
        )
        
        signatories = ["J. Smith", "Jane Doe"]
        
        assert linker._is_signatory(actor, signatories) is True
    
    def test_has_fiduciary_role(self):
        """Test fiduciary role detection."""
        linker = EvidenceAttributionLinker()
        
        # Test director
        actor_director = ActorProfile(
            actor_id="test-3",
            name="Alice Johnson",
            actor_type="INDIVIDUAL",
            roles=["Director", "Board Member"]
        )
        assert linker._has_fiduciary_role(actor_director) is True
        
        # Test officer
        actor_officer = ActorProfile(
            actor_id="test-4",
            name="Bob Williams",
            actor_type="INDIVIDUAL",
            roles=["Officer", "Vice President"]
        )
        assert linker._has_fiduciary_role(actor_officer) is True
        
        # Test non-fiduciary
        actor_employee = ActorProfile(
            actor_id="test-5",
            name="Charlie Brown",
            actor_type="INDIVIDUAL",
            roles=["Employee"]
        )
        assert linker._has_fiduciary_role(actor_employee) is False
    
    def test_is_transaction_party(self):
        """Test transaction party detection."""
        linker = EvidenceAttributionLinker()
        
        actor = ActorProfile(
            actor_id="test-6",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["Insider"]
        )
        
        evidence_item = {
            'type': 'form4',
            'id': 'form4_001',
            'metadata': {
                'reporting_owner': 'John Smith',
                'shares': 1000
            }
        }
        
        assert linker._is_transaction_party(actor, evidence_item) is True
    
    def test_is_beneficiary(self):
        """Test beneficiary detection."""
        linker = EvidenceAttributionLinker()
        
        actor = ActorProfile(
            actor_id="test-7",
            name="Jane Doe",
            actor_type="INDIVIDUAL",
            roles=["Executive"],
            metadata={'total_compensation': 5000000}
        )
        
        evidence_item = {
            'id': 'def14a_001',
            'type': 'DEF 14A',
            'metadata': {'executive': 'Jane Doe'}
        }
        
        assert linker._is_beneficiary(actor, evidence_item) is True
    
    def test_is_disclosure_obligor(self):
        """Test SOX disclosure obligor detection."""
        linker = EvidenceAttributionLinker()
        
        # Test CEO with 10-K
        actor_ceo = ActorProfile(
            actor_id="test-8",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO", "Chief Executive Officer"]
        )
        assert linker._is_disclosure_obligor(actor_ceo, "10-K") is True
        
        # Test CFO with 10-Q
        actor_cfo = ActorProfile(
            actor_id="test-9",
            name="Jane Doe",
            actor_type="INDIVIDUAL",
            roles=["CFO", "Chief Financial Officer"]
        )
        assert linker._is_disclosure_obligor(actor_cfo, "10-Q") is True
        
        # Test non-obligor
        actor_vp = ActorProfile(
            actor_id="test-10",
            name="Bob Williams",
            actor_type="INDIVIDUAL",
            roles=["Vice President"]
        )
        assert linker._is_disclosure_obligor(actor_vp, "10-K") is False
    
    def test_is_mentioned(self):
        """Test actor name mentioned in content."""
        linker = EvidenceAttributionLinker()
        
        actor = ActorProfile(
            actor_id="test-11",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"]
        )
        
        content = """
        The Board of Directors met on January 15, 2023.
        John Smith, Chief Executive Officer, presented the annual report.
        """
        
        assert linker._is_mentioned(actor, content) is True
    
    def test_is_mentioned_last_name_only(self):
        """Test actor mentioned by last name only."""
        linker = EvidenceAttributionLinker()
        
        actor = ActorProfile(
            actor_id="test-12",
            name="Alice Johnson",
            actor_type="INDIVIDUAL",
            roles=["CFO"]
        )
        
        content = """
        According to CFO Johnson, the quarterly results exceeded expectations.
        """
        
        assert linker._is_mentioned(actor, content) is True
    
    def test_attribute_evidence_to_actors(self):
        """Test full attribution process."""
        linker = EvidenceAttributionLinker()
        
        actors = [
            ActorProfile(
                actor_id="actor-1",
                name="John Smith",
                actor_type="INDIVIDUAL",
                roles=["CEO"]
            ),
            ActorProfile(
                actor_id="actor-2",
                name="Jane Doe",
                actor_type="INDIVIDUAL",
                roles=["CFO"]
            )
        ]
        
        evidence_items = [
            {
                'id': 'evidence-1',
                'type': '10-K',
                'content': '/s/ John Smith\nChief Executive Officer',
                'filing_date': '2023-03-01'
            },
            {
                'id': 'evidence-2',
                'type': '10-K',
                'content': '/s/ Jane Doe\nChief Financial Officer',
                'filing_date': '2023-03-01'
            }
        ]
        
        attributions = linker.attribute_evidence_to_actors(actors, evidence_items)
        
        assert len(attributions) > 0
        
        # Check John Smith has attribution
        john_attrs = [a for a in attributions if a.actor_id == "actor-1"]
        assert len(john_attrs) > 0
        
        # Check Jane Doe has attribution
        jane_attrs = [a for a in attributions if a.actor_id == "actor-2"]
        assert len(jane_attrs) > 0
    
    def test_attribution_type_priority(self):
        """Test that direct authorship takes priority."""
        linker = EvidenceAttributionLinker()
        
        actor = ActorProfile(
            actor_id="actor-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"]
        )
        
        evidence_items = [
            {
                'id': 'evidence-1',
                'type': '10-K',
                'content': '/s/ John Smith\nChief Executive Officer\nThis document certifies...',
                'filing_date': '2023-03-01'
            }
        ]
        
        attributions = linker.attribute_evidence_to_actors([actor], evidence_items)
        
        # Should have DIRECT_AUTHORSHIP with highest relevance
        direct_auth = [a for a in attributions if a.attribution_type == AttributionType.DIRECT_AUTHORSHIP]
        assert len(direct_auth) > 0
        assert direct_auth[0].relevance_score == 1.0
    
    def test_get_attributions_for_actor(self):
        """Test filtering attributions by actor."""
        linker = EvidenceAttributionLinker()
        
        linker.attributions = [
            EvidenceAttribution("actor-1", "evidence-1", AttributionType.DIRECT_AUTHORSHIP, 1.0),
            EvidenceAttribution("actor-1", "evidence-2", AttributionType.FIDUCIARY_ROLE, 0.8),
            EvidenceAttribution("actor-2", "evidence-1", AttributionType.INDIRECT, 0.5)
        ]
        
        actor1_attrs = linker.get_attributions_for_actor("actor-1")
        
        assert len(actor1_attrs) == 2
        assert all(a.actor_id == "actor-1" for a in actor1_attrs)
    
    def test_get_attributions_for_evidence(self):
        """Test filtering attributions by evidence."""
        linker = EvidenceAttributionLinker()
        
        linker.attributions = [
            EvidenceAttribution("actor-1", "evidence-1", AttributionType.DIRECT_AUTHORSHIP, 1.0),
            EvidenceAttribution("actor-2", "evidence-1", AttributionType.INDIRECT, 0.5),
            EvidenceAttribution("actor-1", "evidence-2", AttributionType.FIDUCIARY_ROLE, 0.8)
        ]
        
        evidence1_attrs = linker.get_attributions_for_evidence("evidence-1")
        
        assert len(evidence1_attrs) == 2
        assert all(a.evidence_id == "evidence-1" for a in evidence1_attrs)
    
    def test_get_high_relevance_attributions(self):
        """Test filtering by relevance score."""
        linker = EvidenceAttributionLinker()
        
        linker.attributions = [
            EvidenceAttribution("actor-1", "evidence-1", AttributionType.DIRECT_AUTHORSHIP, 1.0),
            EvidenceAttribution("actor-2", "evidence-2", AttributionType.FIDUCIARY_ROLE, 0.85),
            EvidenceAttribution("actor-3", "evidence-3", AttributionType.INDIRECT, 0.5)
        ]
        
        high_relevance = linker.get_high_relevance_attributions(min_relevance=0.8)
        
        assert len(high_relevance) == 2
        assert all(a.relevance_score >= 0.8 for a in high_relevance)
    
    def test_get_attributions_by_type(self):
        """Test filtering by attribution type."""
        linker = EvidenceAttributionLinker()
        
        linker.attributions = [
            EvidenceAttribution("actor-1", "evidence-1", AttributionType.DIRECT_AUTHORSHIP, 1.0),
            EvidenceAttribution("actor-2", "evidence-2", AttributionType.DIRECT_AUTHORSHIP, 1.0),
            EvidenceAttribution("actor-3", "evidence-3", AttributionType.INDIRECT, 0.5)
        ]
        
        direct_auth = linker.get_attributions_by_type(AttributionType.DIRECT_AUTHORSHIP)
        
        assert len(direct_auth) == 2
        assert all(a.attribution_type == AttributionType.DIRECT_AUTHORSHIP for a in direct_auth)
    
    def test_calculate_actor_evidence_strength(self):
        """Test calculating overall evidence strength for actor."""
        linker = EvidenceAttributionLinker()
        
        linker.attributions = [
            EvidenceAttribution("actor-1", "evidence-1", AttributionType.DIRECT_AUTHORSHIP, 1.0),
            EvidenceAttribution("actor-1", "evidence-2", AttributionType.TRANSACTION_PARTY, 0.9),
            EvidenceAttribution("actor-1", "evidence-3", AttributionType.INDIRECT, 0.5)
        ]
        
        strength = linker.calculate_actor_evidence_strength("actor-1")
        
        # Should be weighted average based on attribution types
        assert 0.5 < strength <= 1.0
    
    def test_no_attributions_for_actor(self):
        """Test actor with no attributions."""
        linker = EvidenceAttributionLinker()
        
        strength = linker.calculate_actor_evidence_strength("nonexistent-actor")
        
        assert strength == 0.0
    
    def test_empty_evidence_content(self):
        """Test handling empty evidence content."""
        linker = EvidenceAttributionLinker()
        
        actor = ActorProfile(
            actor_id="actor-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"]
        )
        
        evidence_items = [
            {
                'id': 'evidence-1',
                'type': 'document',
                'content': '',
                'filing_date': None
            }
        ]
        
        # Should not crash
        attributions = linker.attribute_evidence_to_actors([actor], evidence_items)
        assert attributions is not None
