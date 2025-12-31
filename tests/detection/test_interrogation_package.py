"""
Tests for Interrogation Package Generator
==========================================

Tests DOJ-ready interrogation package generation.
"""

import pytest
from datetime import date, datetime
from src.detection.actor_extraction_engine import ActorProfile
from src.detection.actor_role_classifier import ActorRole
from src.core.evidence_chain.evidence_attribution import EvidenceAttribution, AttributionType
from src.reporting.interrogation_package import (
    InterrogationPackageGenerator,
    InterrogationPackage,
    InterrogationQuestion,
    InterviewPhase
)


class TestInterrogationQuestion:
    """Test InterrogationQuestion dataclass."""
    
    def test_question_creation(self):
        """Test creating an interrogation question."""
        question = InterrogationQuestion(
            phase=InterviewPhase.RAPPORT,
            question_number=1,
            question_text="Can you tell me about your role?",
            legal_purpose="Establish rapport",
            anticipated_response="Cooperative response"
        )
        
        assert question.phase == InterviewPhase.RAPPORT
        assert question.question_number == 1
        assert "role" in question.question_text
    
    def test_question_to_dict(self):
        """Test converting question to dictionary."""
        question = InterrogationQuestion(
            phase=InterviewPhase.ACCUSATION,
            question_number=5,
            question_text="Were you aware of this information?",
            legal_purpose="Establish knowledge",
            anticipated_response="Denial",
            follow_up_questions=["When did you learn?"],
            rebuttal_evidence=["evidence-1"]
        )
        
        q_dict = question.to_dict()
        
        assert q_dict["phase"] == "ACCUSATION"
        assert q_dict["question_number"] == 5
        assert len(q_dict["follow_up_questions"]) == 1
        assert len(q_dict["rebuttal_evidence"]) == 1


class TestInterrogationPackage:
    """Test InterrogationPackage dataclass."""
    
    def test_package_creation(self):
        """Test creating an interrogation package."""
        package = InterrogationPackage(
            actor_id="actor-123",
            actor_name="John Smith",
            actor_role=ActorRole.TARGET,
            risk_score=75.5,
            generation_date=datetime.utcnow()
        )
        
        assert package.actor_id == "actor-123"
        assert package.actor_name == "John Smith"
        assert package.actor_role == ActorRole.TARGET
        assert package.risk_score == 75.5
    
    def test_package_to_dict(self):
        """Test converting package to dictionary."""
        package = InterrogationPackage(
            actor_id="actor-123",
            actor_name="John Smith",
            actor_role=ActorRole.SUBJECT,
            risk_score=95.0,
            generation_date=datetime.utcnow(),
            violations=[
                {'violation_type': 'insider_trading', 'severity': 'HIGH'}
            ]
        )
        
        pkg_dict = package.to_dict()
        
        assert pkg_dict["actor_id"] == "actor-123"
        assert pkg_dict["actor_role"] == "SUBJECT"
        assert pkg_dict["risk_score"] == 95.0
        assert len(pkg_dict["violations"]) == 1


class TestInterrogationPackageGenerator:
    """Test InterrogationPackageGenerator functionality."""
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        generator = InterrogationPackageGenerator()
        assert generator is not None
    
    def test_generate_package_subject(self):
        """Test generating package for SUBJECT actor."""
        generator = InterrogationPackageGenerator()
        
        actor = ActorProfile(
            actor_id="actor-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO", "Director"],
            violations=["securities_fraud", "insider_trading"],
            evidence_items=["evidence-1", "evidence-2"],
            risk_score=95.0,
            first_appearance=date(2020, 1, 1),
            metadata={'total_compensation': 10000000, 'salary': 2000000}
        )
        
        violations = [
            {
                'violation_type': 'securities_fraud',
                'severity': 'HIGH',
                'financial_impact': 5000000,
                'description': 'Material misstatement in 10-K'
            }
        ]
        
        evidence_attributions = [
            EvidenceAttribution(
                actor_id="actor-1",
                evidence_id="evidence-1",
                attribution_type=AttributionType.DIRECT_AUTHORSHIP,
                relevance_score=1.0,
                attribution_date=date(2023, 3, 1)
            )
        ]
        
        evidence_items = [
            {
                'id': 'evidence-1',
                'type': '10-K',
                'content': '/s/ John Smith\nChief Executive Officer',
                'filing_date': '2023-03-01',
                'description': '2022 Annual Report'
            }
        ]
        
        package = generator.generate_package(
            actor=actor,
            actor_role=ActorRole.SUBJECT,
            violations=violations,
            evidence_attributions=evidence_attributions,
            evidence_items=evidence_items
        )
        
        assert package is not None
        assert package.actor_id == "actor-1"
        assert package.actor_name == "John Smith"
        assert package.actor_role == ActorRole.SUBJECT
        assert package.risk_score == 95.0
    
    def test_build_positions_section(self):
        """Test building corporate positions section."""
        generator = InterrogationPackageGenerator()
        
        actor = ActorProfile(
            actor_id="actor-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO", "Director", "Board Member"],
            first_appearance=date(2020, 1, 1),
            last_appearance=date(2023, 12, 31)
        )
        
        positions = generator._build_positions_section(actor)
        
        assert len(positions) == 3
        assert any(p['title'] == 'CEO' for p in positions)
        assert any(p['title'] == 'Director' for p in positions)
        assert all('start_date' in p for p in positions)
    
    def test_build_compensation_section(self):
        """Test building compensation history section."""
        generator = InterrogationPackageGenerator()
        
        actor = ActorProfile(
            actor_id="actor-1",
            name="Jane Doe",
            actor_type="INDIVIDUAL",
            roles=["CFO"],
            metadata={
                'total_compensation': 5000000,
                'salary': 1000000,
                'bonus': 500000,
                'stock_awards': 3000000
            }
        )
        
        compensation = generator._build_compensation_section(actor)
        
        assert len(compensation) > 0
        assert compensation[0]['total_compensation'] == 5000000
        assert compensation[0]['salary'] == 1000000
    
    def test_build_violations_section(self):
        """Test building violations attributed section."""
        generator = InterrogationPackageGenerator()
        
        actor = ActorProfile(
            actor_id="actor-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"]
        )
        
        violations = [
            {
                'violation_type': 'insider_trading',
                'severity': 'HIGH',
                'description': 'Trading on material non-public information',
                'financial_impact': 2000000
            },
            {
                'violation_type': 'sox_302',
                'severity': 'MEDIUM',
                'description': 'False SOX certification',
                'financial_impact': 0
            }
        ]
        
        violation_entries = generator._build_violations_section(actor, violations)
        
        assert len(violation_entries) == 2
        assert any(v['violation_type'] == 'insider_trading' for v in violation_entries)
        assert any(v['violation_type'] == 'sox_302' for v in violation_entries)
        assert all('actor_role' in v for v in violation_entries)
    
    def test_build_evidence_section(self):
        """Test building evidence exhibits section."""
        generator = InterrogationPackageGenerator()
        
        actor = ActorProfile(
            actor_id="actor-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"]
        )
        
        evidence_attributions = [
            EvidenceAttribution(
                actor_id="actor-1",
                evidence_id="evidence-1",
                attribution_type=AttributionType.DIRECT_AUTHORSHIP,
                relevance_score=1.0,
                attribution_date=date(2023, 3, 1)
            ),
            EvidenceAttribution(
                actor_id="actor-1",
                evidence_id="evidence-2",
                attribution_type=AttributionType.TRANSACTION_PARTY,
                relevance_score=0.9,
                attribution_date=date(2023, 1, 15)
            )
        ]
        
        evidence_items = [
            {
                'id': 'evidence-1',
                'type': '10-K',
                'content': '/s/ John Smith\nCEO',
                'description': 'Annual Report'
            },
            {
                'id': 'evidence-2',
                'type': 'Form 4',
                'content': 'Transaction details',
                'description': 'Insider transaction'
            }
        ]
        
        exhibits = generator._build_evidence_section(
            actor, evidence_attributions, evidence_items
        )
        
        assert len(exhibits) == 2
        # Should be sorted by date (earlier first)
        assert exhibits[0]['evidence_id'] == 'evidence-2'
        assert 'exhibit_number' in exhibits[0]
        assert 'fre_902_authentication' in exhibits[0]
    
    def test_build_objectives(self):
        """Test building interview objectives."""
        generator = InterrogationPackageGenerator()
        
        actor = ActorProfile(
            actor_id="actor-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"]
        )
        
        violations = [
            {
                'violation_type': 'insider_trading',
                'severity': 'HIGH'
            },
            {
                'violation_type': 'sox_302',
                'severity': 'MEDIUM'
            }
        ]
        
        objectives = generator._build_objectives(actor, violations)
        
        assert len(objectives) > 0
        # Should include objectives for both violation types
        assert any('material non-public' in obj.lower() for obj in objectives)
        assert any('sox' in obj.lower() or 'certification' in obj.lower() for obj in objectives)
    
    def test_build_question_tree(self):
        """Test building interview question tree."""
        generator = InterrogationPackageGenerator()
        
        actor = ActorProfile(
            actor_id="actor-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"],
            violations=["insider_trading"]
        )
        
        violations = [
            {
                'violation_type': 'insider_trading',
                'severity': 'HIGH',
                'description': 'Trading before earnings announcement',
                'date': '2023-01-15'
            }
        ]
        
        evidence_attributions = [
            EvidenceAttribution(
                actor_id="actor-1",
                evidence_id="evidence-1",
                attribution_type=AttributionType.DIRECT_AUTHORSHIP,
                relevance_score=1.0
            )
        ]
        
        questions = generator._build_question_tree(actor, violations, evidence_attributions)
        
        assert len(questions) > 0
        
        # Should have questions from different phases
        phases = set(q.phase for q in questions)
        assert InterviewPhase.RAPPORT in phases
        assert InterviewPhase.BASELINE in phases
        
        # Questions should be numbered sequentially
        question_numbers = [q.question_number for q in questions]
        assert question_numbers == sorted(question_numbers)
        
        # All questions should have legal purpose
        assert all(q.legal_purpose for q in questions)
    
    def test_build_defenses_section(self):
        """Test building anticipated defenses section."""
        generator = InterrogationPackageGenerator()
        
        actor = ActorProfile(
            actor_id="actor-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"]
        )
        
        violations = [
            {
                'violation_type': 'insider_trading',
                'severity': 'HIGH'
            }
        ]
        
        defenses = generator._build_defenses_section(actor, violations)
        
        assert len(defenses) > 0
        
        # Should include common defenses
        defense_types = [d['defense'].lower() for d in defenses]
        assert any('good faith' in dt or 'reliance' in dt for dt in defense_types)
        assert any('lack of knowledge' in dt for dt in defense_types)
        
        # For insider trading, should include 10b5-1 defense
        assert any('10b5-1' in dt for dt in defense_types)
        
        # All defenses should have rebuttals
        assert all('rebuttal' in d for d in defenses)
    
    def test_build_statutes_section(self):
        """Test building applicable statutes section."""
        generator = InterrogationPackageGenerator()
        
        violations = [
            {'violation_type': 'securities_fraud', 'severity': 'HIGH'},
            {'violation_type': 'insider_trading', 'severity': 'HIGH'},
            {'violation_type': 'sox_302', 'severity': 'MEDIUM'}
        ]
        
        statutes = generator._build_statutes_section(violations)
        
        assert len(statutes) >= 3
        
        # Check key fields present
        assert all('citation' in s for s in statutes)
        assert all('title' in s for s in statutes)
        assert all('elements' in s for s in statutes)
        assert all('max_penalty' in s for s in statutes)
    
    def test_calculate_element_strength(self):
        """Test calculating evidence strength per legal element."""
        generator = InterrogationPackageGenerator()
        
        violations = [
            {'violation_type': 'securities_fraud', 'severity': 'HIGH'}
        ]
        
        evidence_attributions = [
            EvidenceAttribution(
                actor_id="actor-1",
                evidence_id="evidence-1",
                attribution_type=AttributionType.DIRECT_AUTHORSHIP,
                relevance_score=1.0
            ),
            EvidenceAttribution(
                actor_id="actor-1",
                evidence_id="evidence-2",
                attribution_type=AttributionType.TRANSACTION_PARTY,
                relevance_score=0.9
            )
        ]
        
        element_strength = generator._calculate_element_strength(violations, evidence_attributions)
        
        assert 'knowledge' in element_strength
        assert 'intent' in element_strength
        assert 'materiality' in element_strength
        
        # All strengths should be between 0 and 1
        assert all(0 <= v <= 1 for v in element_strength.values())
    
    def test_calculate_ussg_sentencing(self):
        """Test USSG sentencing guidelines calculation."""
        generator = InterrogationPackageGenerator()
        
        actor = ActorProfile(
            actor_id="actor-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"]
        )
        
        violations = [
            {'financial_impact': 15000000},  # > $10M
            {'financial_impact': 5000000}
        ]
        
        ussg = generator._calculate_ussg_sentencing(actor, violations)
        
        assert 'base_offense_level' in ussg
        assert 'estimated_loss_amount' in ussg
        assert 'leadership_enhancement' in ussg
        
        # CEO should have leadership enhancement
        assert ussg['leadership_enhancement'] == 4
        
        # Large loss should increase offense level
        assert ussg['base_offense_level'] > 20
    
    def test_determine_actor_role_in_violation(self):
        """Test determining actor's specific role in violation."""
        generator = InterrogationPackageGenerator()
        
        # Test CEO as primary architect
        actor_ceo = ActorProfile(
            actor_id="actor-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"]
        )
        role_ceo = generator._determine_actor_role_in_violation(actor_ceo, {})
        assert role_ceo == "Primary Architect"
        
        # Test officer as key participant
        actor_officer = ActorProfile(
            actor_id="actor-2",
            name="Jane Doe",
            actor_type="INDIVIDUAL",
            roles=["Vice President", "Officer"]
        )
        role_officer = generator._determine_actor_role_in_violation(actor_officer, {})
        assert role_officer == "Key Participant"
        
        # Test certifying officer
        actor_cert = ActorProfile(
            actor_id="actor-3",
            name="Bob Williams",
            actor_type="INDIVIDUAL",
            roles=["Certifying Officer"]
        )
        role_cert = generator._determine_actor_role_in_violation(actor_cert, {})
        assert role_cert == "Certifying Officer"
    
    def test_extract_key_excerpts(self):
        """Test extracting key excerpts mentioning actor."""
        generator = InterrogationPackageGenerator()
        
        actor = ActorProfile(
            actor_id="actor-1",
            name="John Smith",
            actor_type="INDIVIDUAL",
            roles=["CEO"]
        )
        
        evidence_item = {
            'content': """
            The Board of Directors met on January 15, 2023. 
            John Smith, Chief Executive Officer, presented the annual results.
            The committee reviewed compensation for John Smith and other executives.
            John Smith certified the accuracy of the financial statements.
            """
        }
        
        excerpts = generator._extract_key_excerpts(actor, evidence_item)
        
        # Should extract sentences mentioning John Smith
        assert len(excerpts) > 0
        assert all('john smith' in e.lower() for e in excerpts)
        
        # Should limit number of excerpts
        assert len(excerpts) <= 3
    
    def test_empty_violations(self):
        """Test package generation with no violations."""
        generator = InterrogationPackageGenerator()
        
        actor = ActorProfile(
            actor_id="actor-1",
            name="Jane Doe",
            actor_type="INDIVIDUAL",
            roles=["Witness"],
            violations=[]
        )
        
        package = generator.generate_package(
            actor=actor,
            actor_role=ActorRole.WITNESS,
            violations=[],
            evidence_attributions=[],
            evidence_items=[]
        )
        
        # Should still generate package
        assert package is not None
        assert len(package.violations) == 0
        # Should still have basic questions
        assert len(package.questions) > 0
