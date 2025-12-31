"""
Tests for Actor Role Classifier
================================

Tests DOJ 6-tier role classification and risk score calculation.
"""

import pytest
from datetime import date
from src.detection.actor_extraction_engine import ActorProfile
from src.detection.actor_role_classifier import (
    ActorRoleClassifier,
    ActorRole,
    RiskScoreComponents
)


class TestActorRoleClassifier:
    """Test ActorRoleClassifier functionality."""
    
    def test_classifier_initialization(self):
        """Test classifier initialization."""
        classifier = ActorRoleClassifier()
        assert classifier is not None
    
    def test_classify_subject_ceo_high_violations(self):
        """Test classification of CEO with high violations as SUBJECT."""
        classifier = ActorRoleClassifier()
        
        actor = ActorProfile(
            actor_id="test-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO", "Director"],
            violations=["securities_fraud", "insider_trading", "sox_violation"]
        )
        
        violations = [
            {
                'violation_type': 'securities_fraud',
                'severity': 'HIGH',
                'financial_impact': 10000000
            },
            {
                'violation_type': 'insider_trading',
                'severity': 'CRITICAL',
                'financial_impact': 5000000
            }
        ]
        
        evidence = [
            {'type': 'signature', 'strength': 'STRONG'},
            {'type': 'certification', 'strength': 'DIRECT'}
        ]
        
        role = classifier.classify_actor(actor, violations, evidence)
        
        assert role == ActorRole.SUBJECT
        assert actor.risk_score >= 90.0
    
    def test_classify_target_officer_substantial_evidence(self):
        """Test classification of officer with substantial evidence as TARGET."""
        classifier = ActorRoleClassifier()
        
        actor = ActorProfile(
            actor_id="test-2",
            name="Jane Doe",
            actor_type="INDIVIDUAL",
            roles=["Vice President", "Officer"],
            violations=["disclosure_failure"]
        )
        
        violations = [
            {
                'violation_type': 'disclosure_failure',
                'severity': 'MEDIUM',
                'financial_impact': 500000
            }
        ]
        
        evidence = [
            {'type': 'transaction', 'strength': 'MODERATE'},
            {'type': 'document', 'strength': 'MODERATE'}
        ]
        
        role = classifier.classify_actor(actor, violations, evidence)
        
        assert role == ActorRole.TARGET
        assert 70.0 <= actor.risk_score < 90.0
    
    def test_classify_witness_transaction_participant(self):
        """Test classification of transaction participant as WITNESS."""
        classifier = ActorRoleClassifier()
        
        actor = ActorProfile(
            actor_id="test-3",
            name="Bob Williams",
            actor_type="INDIVIDUAL",
            roles=["Manager"],
            violations=[]
        )
        
        violations = []
        
        evidence = [
            {'type': 'transaction', 'strength': 'MODERATE'},
            {'type': 'document', 'strength': 'WEAK'}
        ]
        
        role = classifier.classify_actor(actor, violations, evidence)
        
        assert role == ActorRole.WITNESS
        assert 50.0 <= actor.risk_score < 70.0
    
    def test_classify_person_of_interest_peripheral(self):
        """Test classification of peripheral involvement as PERSON_OF_INTEREST."""
        classifier = ActorRoleClassifier()
        
        actor = ActorProfile(
            actor_id="test-4",
            name="Alice Johnson",
            actor_type="INDIVIDUAL",
            roles=["Employee"],
            violations=[]
        )
        
        violations = []
        evidence = []
        
        role = classifier.classify_actor(actor, violations, evidence)
        
        assert role == ActorRole.PERSON_OF_INTEREST
        assert 30.0 <= actor.risk_score < 50.0
    
    def test_classify_enabler_professional_services(self):
        """Test classification of professional enabler."""
        classifier = ActorRoleClassifier()
        
        actor = ActorProfile(
            actor_id="test-5",
            name="Smith & Associates",
            actor_type="ENTITY",
            roles=["Auditor", "Accountant"],
            violations=[],
            evidence_items=["audit_report_1", "audit_report_2"]
        )
        
        violations = []
        evidence = []
        
        role = classifier.classify_actor(actor, violations, evidence)
        
        assert role == ActorRole.ENABLER
    
    def test_calculate_risk_score_components(self):
        """Test risk score component calculation."""
        classifier = ActorRoleClassifier()
        
        actor = ActorProfile(
            actor_id="test-6",
            name="Test Actor",
            actor_type="INDIVIDUAL",
            roles=["CFO"],
            violations=["sox_302"],
            evidence_items=["cert_1", "cert_2"],
            metadata={'total_compensation': 2000000}
        )
        
        violations = [
            {
                'violation_type': 'sox_302',
                'severity': 'HIGH',
                'financial_impact': 1000000
            }
        ]
        
        evidence = [
            {'type': 'certification', 'strength': 'STRONG'},
            {'type': 'signature', 'strength': 'DIRECT'}
        ]
        
        components = classifier.calculate_risk_score(actor, violations, evidence)
        
        assert isinstance(components, RiskScoreComponents)
        assert 0 <= components.violation_severity <= 30
        assert 0 <= components.evidence_strength <= 25
        assert 0 <= components.corporate_position <= 25
        assert 0 <= components.financial_benefit <= 20
        assert components.total_score == (
            components.violation_severity + 
            components.evidence_strength + 
            components.corporate_position + 
            components.financial_benefit
        )
    
    def test_violation_severity_calculation(self):
        """Test violation severity score calculation."""
        classifier = ActorRoleClassifier()
        
        actor = ActorProfile(
            actor_id="test-7",
            name="Test Actor",
            actor_type="INDIVIDUAL",
            roles=["CEO"],
            violations=["v1", "v2", "v3", "v4"]
        )
        
        violations = [
            {'violation_type': 'securities_fraud', 'severity': 'CRITICAL'},
            {'violation_type': 'insider_trading', 'severity': 'HIGH'},
            {'violation_type': 'sox_violation', 'severity': 'HIGH'},
            {'violation_type': 'disclosure_failure', 'severity': 'MEDIUM'}
        ]
        
        score = classifier._calculate_violation_severity(actor, violations)
        
        # Should be maximum (30.0) for multiple high-severity violations
        assert score == 30.0
    
    def test_evidence_strength_calculation(self):
        """Test evidence strength score calculation."""
        classifier = ActorRoleClassifier()
        
        actor = ActorProfile(
            actor_id="test-8",
            name="Test Actor",
            actor_type="INDIVIDUAL",
            roles=["CEO"],
            evidence_items=["e1", "e2", "e3"]
        )
        
        evidence = [
            {'type': 'signature', 'strength': 'STRONG'},
            {'type': 'certification', 'strength': 'DIRECT'},
            {'type': 'transaction', 'strength': 'STRONG'}
        ]
        
        score = classifier._calculate_evidence_strength(actor, evidence)
        
        # Should be maximum (25.0) for direct evidence
        assert score == 25.0
    
    def test_corporate_position_score(self):
        """Test corporate position score calculation."""
        classifier = ActorRoleClassifier()
        
        # Test C-suite (25 points)
        actor_ceo = ActorProfile(
            actor_id="test-9",
            name="CEO Actor",
            actor_type="INDIVIDUAL",
            roles=["CEO"]
        )
        assert classifier._calculate_corporate_position_score(actor_ceo) == 25.0
        
        # Test CFO (25 points)
        actor_cfo = ActorProfile(
            actor_id="test-10",
            name="CFO Actor",
            actor_type="INDIVIDUAL",
            roles=["CFO"]
        )
        assert classifier._calculate_corporate_position_score(actor_cfo) == 25.0
        
        # Test Officer (Vice President matches officer pattern, which is 20 points)
        actor_officer = ActorProfile(
            actor_id="test-11",
            name="Officer Actor",
            actor_type="INDIVIDUAL",
            roles=["Vice President"]
        )
        # Vice President matches "vice president" in OFFICER_DIRECTOR_POSITIONS
        score_officer = classifier._calculate_corporate_position_score(actor_officer)
        assert score_officer >= 20.0  # At least 20 points for officer role
        
        # Test Director (18 points)
        actor_director = ActorProfile(
            actor_id="test-12",
            name="Director Actor",
            actor_type="INDIVIDUAL",
            roles=["Board Member"]
        )
        assert classifier._calculate_corporate_position_score(actor_director) == 18.0
    
    def test_financial_benefit_score(self):
        """Test financial benefit score calculation."""
        classifier = ActorRoleClassifier()
        
        # Test high compensation (20 points)
        actor_high = ActorProfile(
            actor_id="test-13",
            name="High Comp Actor",
            actor_type="INDIVIDUAL",
            roles=["CEO"],
            metadata={'total_compensation': 15000000}
        )
        assert classifier._calculate_financial_benefit_score(actor_high) == 20.0
        
        # Test medium compensation (15 points)
        actor_med = ActorProfile(
            actor_id="test-14",
            name="Med Comp Actor",
            actor_type="INDIVIDUAL",
            roles=["VP"],
            metadata={'total_compensation': 2000000}
        )
        assert classifier._calculate_financial_benefit_score(actor_med) == 15.0
        
        # Test low compensation (10 points)
        actor_low = ActorProfile(
            actor_id="test-15",
            name="Low Comp Actor",
            actor_type="INDIVIDUAL",
            roles=["Manager"],
            metadata={'total_compensation': 200000}
        )
        assert classifier._calculate_financial_benefit_score(actor_low) == 10.0
    
    def test_classify_multiple_actors(self):
        """Test batch classification of multiple actors."""
        classifier = ActorRoleClassifier()
        
        actors = [
            ActorProfile(
                actor_id="a1",
                name="CEO Actor",
                actor_type="INDIVIDUAL",
                roles=["CEO"],
                violations=["v1", "v2"]
            ),
            ActorProfile(
                actor_id="a2",
                name="Officer Actor",
                actor_type="INDIVIDUAL",
                roles=["VP"],
                violations=["v1"]
            ),
            ActorProfile(
                actor_id="a3",
                name="Employee Actor",
                actor_type="INDIVIDUAL",
                roles=["Employee"],
                violations=[]
            )
        ]
        
        classifications = classifier.classify_multiple_actors(actors)
        
        assert len(classifications) == 3
        assert "a1" in classifications
        assert "a2" in classifications
        assert "a3" in classifications
    
    def test_get_priority_actors(self):
        """Test filtering priority actors by risk score."""
        classifier = ActorRoleClassifier()
        
        actors = [
            ActorProfile(actor_id="a1", name="High Risk", actor_type="INDIVIDUAL", 
                        roles=["CEO"], violations=["v1", "v2"], risk_score=85.0),
            ActorProfile(actor_id="a2", name="Medium Risk", actor_type="INDIVIDUAL",
                        roles=["VP"], violations=["v1"], risk_score=55.0),
            ActorProfile(actor_id="a3", name="Low Risk", actor_type="INDIVIDUAL",
                        roles=["Employee"], violations=[], risk_score=25.0)
        ]
        
        priority = classifier.get_priority_actors(actors, min_risk_score=50.0)
        
        assert len(priority) == 2
        assert priority[0].risk_score == 85.0  # Sorted descending
        assert priority[1].risk_score == 55.0
    
    def test_zero_dollar_transaction_bonus(self):
        """Test bonus score for zero-dollar transactions."""
        classifier = ActorRoleClassifier()
        
        actor = ActorProfile(
            actor_id="test-16",
            name="Zero Dollar Actor",
            actor_type="INDIVIDUAL",
            roles=["Executive"],
            metadata={'is_zero_dollar': True, 'total_compensation': 100000}
        )
        
        score = classifier._calculate_financial_benefit_score(actor)
        
        # Should have base score (10.0 for $100K) + zero-dollar bonus (5.0)
        assert score >= 15.0
    
    def test_is_enabler_detection(self):
        """Test enabler detection logic."""
        classifier = ActorRoleClassifier()
        
        # Test auditor as enabler
        actor_auditor = ActorProfile(
            actor_id="test-17",
            name="Auditor Firm",
            actor_type="ENTITY",
            roles=["Auditor"],
            evidence_items=["audit-1"]
        )
        assert classifier._is_enabler(actor_auditor, None) is True
        
        # Test accountant as enabler
        actor_accountant = ActorProfile(
            actor_id="test-18",
            name="Accounting Firm",
            actor_type="ENTITY",
            roles=["Accountant", "Consultant"],
            evidence_items=["report-1"]
        )
        assert classifier._is_enabler(actor_accountant, None) is True
        
        # Test non-enabler
        actor_exec = ActorProfile(
            actor_id="test-19",
            name="Executive",
            actor_type="INDIVIDUAL",
            roles=["CEO"]
        )
        assert classifier._is_enabler(actor_exec, None) is False
