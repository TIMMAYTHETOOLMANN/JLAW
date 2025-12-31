"""
Tests for Actor Extraction Engine
==================================

Tests actor extraction from multiple node types, deduplication, and fuzzy matching.
"""

import pytest
from datetime import date
from src.detection.actor_extraction_engine import (
    ActorExtractionEngine,
    ActorProfile
)


class TestActorProfile:
    """Test ActorProfile dataclass."""
    
    def test_actor_profile_creation(self):
        """Test creating an actor profile."""
        actor = ActorProfile(
            actor_id="test-123",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO", "Director"],
            cik="0001234567"
        )
        
        assert actor.actor_id == "test-123"
        assert actor.name == "John Smith"
        assert actor.actor_type == "INDIVIDUAL"
        assert "CEO" in actor.roles
        assert actor.cik == "0001234567"
    
    def test_actor_profile_to_dict(self):
        """Test converting actor profile to dictionary."""
        actor = ActorProfile(
            actor_id="test-123",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"],
            risk_score=75.5
        )
        
        actor_dict = actor.to_dict()
        
        assert actor_dict["actor_id"] == "test-123"
        assert actor_dict["name"] == "John Smith"
        assert actor_dict["risk_score"] == 75.5
    
    def test_actor_profile_merge(self):
        """Test merging two actor profiles."""
        actor1 = ActorProfile(
            actor_id="test-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"],
            evidence_items=["evidence-1"],
            violations=["violation-1"],
            risk_score=50.0,
            first_appearance=date(2020, 1, 1)
        )
        
        actor2 = ActorProfile(
            actor_id="test-2",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["Director"],
            evidence_items=["evidence-2"],
            violations=["violation-2"],
            risk_score=60.0,
            last_appearance=date(2023, 12, 31),
            cik="0001234567"
        )
        
        actor1.merge(actor2)
        
        # Check merged roles
        assert "CEO" in actor1.roles
        assert "Director" in actor1.roles
        
        # Check merged evidence
        assert "evidence-1" in actor1.evidence_items
        assert "evidence-2" in actor1.evidence_items
        
        # Check merged violations
        assert "violation-1" in actor1.violations
        assert "violation-2" in actor1.violations
        
        # Check dates
        assert actor1.first_appearance == date(2020, 1, 1)
        assert actor1.last_appearance == date(2023, 12, 31)
        
        # Check CIK
        assert actor1.cik == "0001234567"
        
        # Check risk score (should take maximum)
        assert actor1.risk_score == 60.0


class TestActorExtractionEngine:
    """Test ActorExtractionEngine functionality."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = ActorExtractionEngine()
        assert engine is not None
        assert len(engine.actors) == 0
    
    def test_extract_from_node1_form4(self):
        """Test extracting actors from Node 1 (Form 4) findings."""
        engine = ActorExtractionEngine()
        
        node_results = {
            'node1': {
                'findings': {
                    'transactions': [
                        {
                            'reporting_owner': 'John Smith',
                            'transaction_code': 'P',
                            'transaction_date': '2023-01-15',
                            'shares': 1000,
                            'price_per_share': 50.0,
                            'accession_number': '0001234567-23-000001'
                        }
                    ],
                    'violations': [
                        {
                            'reporting_owner': 'Jane Doe',
                            'violation_type': 'late_filing',
                            'transaction_date': '2023-02-01'
                        }
                    ]
                }
            }
        }
        
        actors = engine.extract_actors_from_nodes(node_results)
        
        assert len(actors) >= 2
        
        # Check John Smith was extracted
        john = next((a for a in actors if a.name == 'John Smith'), None)
        assert john is not None
        assert "Insider" in john.roles or "Reporting Owner" in john.roles
        
        # Check Jane Doe was extracted
        jane = next((a for a in actors if a.name == 'Jane Doe'), None)
        assert jane is not None
        assert "Violation Subject" in jane.roles
    
    def test_extract_from_node2_def14a(self):
        """Test extracting actors from Node 2 (DEF 14A) findings."""
        engine = ActorExtractionEngine()
        
        node_results = {
            'node2': {
                'findings': {
                    'executives': [
                        {
                            'name': 'Alice Johnson',
                            'position': 'CEO',
                            'total_compensation': 5000000,
                            'salary': 1000000
                        }
                    ],
                    'board_members': [
                        {
                            'name': 'Bob Williams',
                            'committees': ['Audit', 'Compensation']
                        }
                    ]
                }
            }
        }
        
        actors = engine.extract_actors_from_nodes(node_results)
        
        assert len(actors) >= 2
        
        # Check Alice Johnson
        alice = next((a for a in actors if a.name == 'Alice Johnson'), None)
        assert alice is not None
        assert "Executive" in alice.roles
        assert alice.metadata.get('total_compensation') == 5000000
        
        # Check Bob Williams
        bob = next((a for a in actors if a.name == 'Bob Williams'), None)
        assert bob is not None
        assert "Board Member" in bob.roles or "Director" in bob.roles
    
    def test_deduplication_exact_match(self):
        """Test deduplication with exact name match."""
        engine = ActorExtractionEngine()
        
        # Add same actor twice with different evidence
        node_results = {
            'node1': {
                'findings': {
                    'transactions': [
                        {
                            'reporting_owner': 'John Smith',
                            'transaction_date': '2023-01-15',
                            'accession_number': '001'
                        }
                    ]
                }
            },
            'node2': {
                'findings': {
                    'executives': [
                        {
                            'name': 'John Smith',
                            'position': 'CEO',
                            'total_compensation': 1000000
                        }
                    ]
                }
            }
        }
        
        actors = engine.extract_actors_from_nodes(node_results)
        
        # Should be deduplicated to one actor
        john_smiths = [a for a in actors if 'john smith' in a.name.lower()]
        assert len(john_smiths) == 1
        
        john = john_smiths[0]
        # Should have roles from both sources
        assert len(john.roles) >= 2
    
    def test_fuzzy_name_matching(self):
        """Test fuzzy name matching for deduplication."""
        engine = ActorExtractionEngine()
        
        # Add actors with similar names
        actor1 = engine._add_or_update_actor(
            name="John A. Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"],
            evidence_id="evidence-1"
        )
        
        actor2 = engine._add_or_update_actor(
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["Director"],
            evidence_id="evidence-2"
        )
        
        # Should be same actor (fuzzy match)
        assert actor1.actor_id == actor2.actor_id
        assert "CEO" in actor1.roles
        assert "Director" in actor1.roles
    
    def test_cik_based_deduplication(self):
        """Test CIK-based deduplication overrides name differences."""
        engine = ActorExtractionEngine()
        
        # Add actors with same CIK but different names
        actor1 = engine._add_or_update_actor(
            name="ACME Corporation",
            actor_type="ENTITY",
            roles=["Institutional Holder"],
            cik="0001234567",
            evidence_id="evidence-1"
        )
        
        actor2 = engine._add_or_update_actor(
            name="ACME Corp",
            actor_type="ENTITY",
            roles=["Beneficial Owner"],
            cik="0001234567",
            evidence_id="evidence-2"
        )
        
        # Should be same actor (CIK match)
        assert actor1.actor_id == actor2.actor_id
        assert len(actor1.roles) == 2
    
    def test_normalize_name(self):
        """Test name normalization."""
        engine = ActorExtractionEngine()
        
        # Test removing titles
        assert engine._normalize_name("Mr. John Smith") == "john smith"
        assert engine._normalize_name("Dr. Jane Doe, Jr.") == "jane doe"
        
        # Test extra whitespace
        assert engine._normalize_name("  John   Smith  ") == "john smith"
    
    def test_extract_actors_from_patterns(self):
        """Test extracting actors from pattern detection results."""
        engine = ActorExtractionEngine()
        
        pattern_results = {
            'insider_trading': {
                'findings': [
                    {
                        'actor': 'Michael Brown',
                        'pattern_type': 'suspicious_timing'
                    }
                ],
                'violations': [
                    {
                        'actor': 'Sarah Davis',
                        'violation_type': 'material_nonpublic'
                    }
                ]
            }
        }
        
        actors = engine.extract_actors_from_patterns(pattern_results)
        
        # Should extract both actors
        michael = next((a for a in actors if 'michael brown' in a.name.lower()), None)
        assert michael is not None
        
        sarah = next((a for a in actors if 'sarah davis' in a.name.lower()), None)
        assert sarah is not None
    
    def test_get_actors_by_role(self):
        """Test filtering actors by role."""
        engine = ActorExtractionEngine()
        
        engine._add_or_update_actor("Alice", "INDIVIDUAL", ["CEO"], evidence_id="e1")
        engine._add_or_update_actor("Bob", "INDIVIDUAL", ["CFO"], evidence_id="e2")
        engine._add_or_update_actor("Charlie", "INDIVIDUAL", ["CEO", "Director"], evidence_id="e3")
        
        ceos = engine.get_actors_by_role("CEO")
        assert len(ceos) == 2
        assert all("CEO" in a.roles for a in ceos)
    
    def test_empty_node_results(self):
        """Test handling empty node results."""
        engine = ActorExtractionEngine()
        
        actors = engine.extract_actors_from_nodes({})
        assert len(actors) == 0
    
    def test_malformed_node_data(self):
        """Test handling malformed node data gracefully."""
        engine = ActorExtractionEngine()
        
        # Malformed data should not crash
        node_results = {
            'node1': {
                'findings': {
                    'transactions': [
                        None,  # Null transaction
                        {},  # Empty transaction
                        {'invalid': 'data'}  # Missing required fields
                    ]
                }
            }
        }
        
        # Should not raise exception
        actors = engine.extract_actors_from_nodes(node_results)
        assert actors is not None
