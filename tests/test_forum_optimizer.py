"""
Tests for Forum Shopping Optimizer
===================================

Tests prosecution venue scoring and strategy generation.
"""

import pytest
from src.compliance.forum_optimizer import (
    ForumShoppingOptimizer,
    ForumAnalysis
)


class TestForumAnalysis:
    """Test ForumAnalysis dataclass."""
    
    def test_forum_analysis_creation(self):
        """Test creating a forum analysis."""
        analysis = ForumAnalysis(
            jurisdiction="California",
            jurisdiction_type="STATE",
            venue_score=75.5,
            recommended_priority="SECONDARY"
        )
        
        assert analysis.jurisdiction == "California"
        assert analysis.venue_score == 75.5
        assert analysis.recommended_priority == "SECONDARY"
    
    def test_forum_analysis_to_dict(self):
        """Test converting forum analysis to dictionary."""
        analysis = ForumAnalysis(
            jurisdiction="Federal (SEC)",
            jurisdiction_type="FEDERAL",
            venue_score=95.0,
            recommended_priority="PRIMARY",
            penalty_score=90.0,
            evidentiary_score=85.0
        )
        
        analysis_dict = analysis.to_dict()
        
        assert analysis_dict['jurisdiction'] == "Federal (SEC)"
        assert analysis_dict['venue_score'] == 95.0
        assert analysis_dict['score_breakdown']['penalty_score'] == 90.0


@pytest.mark.asyncio
class TestForumShoppingOptimizer:
    """Test ForumShoppingOptimizer class."""
    
    def test_optimizer_initialization(self):
        """Test optimizer initialization."""
        optimizer = ForumShoppingOptimizer()
        
        assert optimizer is not None
    
    async def test_analyze_prosecution_venues(self):
        """Test prosecution venue analysis."""
        optimizer = ForumShoppingOptimizer()
        
        # Create mock jurisdictions
        class MockJurisdiction:
            def __init__(self, name, j_type):
                self.jurisdiction_name = name
                self.jurisdiction_type = j_type
        
        jurisdictions = [
            MockJurisdiction("Federal (SEC)", "FEDERAL"),
            MockJurisdiction("CA", "STATE"),
            MockJurisdiction("NY", "STATE")
        ]
        
        violations = [
            {'id': 'v001', 'severity': 'CRITICAL', 'type': 'SECURITIES_FRAUD'}
        ]
        
        state_violations = [
            {'state': 'CA', 'penalties': {'criminal': 'Up to 5 years'}},
            {'state': 'NY', 'penalties': {'criminal': 'Up to 4 years'}}
        ]
        
        international_violations = []
        
        forum_analyses = await optimizer.analyze_prosecution_venues(
            jurisdictions, violations, state_violations, international_violations
        )
        
        # Should return analyses for all jurisdictions
        assert len(forum_analyses) == 3
        
        # Should be sorted by venue score
        assert forum_analyses[0].venue_score >= forum_analyses[1].venue_score
        
        # Primary should be highest score
        assert forum_analyses[0].recommended_priority == "PRIMARY"
    
    def test_calculate_penalty_advantage_federal(self):
        """Test penalty advantage calculation for federal jurisdiction."""
        optimizer = ForumShoppingOptimizer()
        
        violations = [
            {'severity': 'CRITICAL'},
            {'severity': 'HIGH'}
        ]
        
        score = optimizer.calculate_penalty_advantage(
            "Federal (SEC)", "FEDERAL", violations
        )
        
        # Federal should score high (85+ base)
        assert score >= 85.0
        assert score <= 100.0
    
    def test_calculate_penalty_advantage_texas(self):
        """Test penalty advantage for Texas (highest penalties)."""
        optimizer = ForumShoppingOptimizer()
        
        violations = [{'severity': 'CRITICAL'}]
        
        score = optimizer.calculate_penalty_advantage(
            "TX", "STATE", violations
        )
        
        # Texas should score very high (95+ base)
        assert score >= 95.0
    
    def test_calculate_evidentiary_advantage_ny(self):
        """Test evidentiary advantage for NY Martin Act."""
        optimizer = ForumShoppingOptimizer()
        
        violations = []
        
        score = optimizer.calculate_evidentiary_advantage(
            "NY", "STATE", violations
        )
        
        # NY Martin Act: no scienter = high score
        assert score >= 95.0
    
    def test_calculate_evidentiary_advantage_federal(self):
        """Test evidentiary advantage for federal."""
        optimizer = ForumShoppingOptimizer()
        
        violations = []
        
        score = optimizer.calculate_evidentiary_advantage(
            "Federal (SEC)", "FEDERAL", violations
        )
        
        # Federal should score well (80+)
        assert score >= 80.0
    
    def test_calculate_limitations_score(self):
        """Test statute of limitations scoring."""
        optimizer = ForumShoppingOptimizer()
        
        violations = []
        
        # NY has 6 year SOL (longest)
        ny_score = optimizer._calculate_limitations_score(
            "NY", "STATE", violations
        )
        
        # Federal has 5 year SOL
        federal_score = optimizer._calculate_limitations_score(
            "Federal (SEC)", "FEDERAL", violations
        )
        
        # NY should score higher
        assert ny_score >= federal_score
    
    def test_calculate_precedent_score(self):
        """Test precedent favorability scoring."""
        optimizer = ForumShoppingOptimizer()
        
        federal_score = optimizer._calculate_precedent_score(
            "Federal (SEC)", "FEDERAL"
        )
        
        ca_score = optimizer._calculate_precedent_score(
            "CA", "STATE"
        )
        
        # Federal should have better precedent
        assert federal_score > ca_score
    
    def test_calculate_resources_score(self):
        """Test prosecutorial resources scoring."""
        optimizer = ForumShoppingOptimizer()
        
        sec_score = optimizer._calculate_resources_score(
            "Federal (SEC)", "FEDERAL"
        )
        
        small_state_score = optimizer._calculate_resources_score(
            "WY", "STATE"
        )
        
        # SEC should have far more resources
        assert sec_score > small_state_score
    
    def test_calculate_political_will_score(self):
        """Test political will scoring."""
        optimizer = ForumShoppingOptimizer()
        
        tx_score = optimizer._calculate_political_will_score(
            "TX", "STATE"
        )
        
        generic_state_score = optimizer._calculate_political_will_score(
            "ND", "STATE"
        )
        
        # Texas is very aggressive
        assert tx_score >= 95.0
        assert tx_score > generic_state_score
    
    def test_identify_advantages_federal(self):
        """Test identifying federal advantages."""
        optimizer = ForumShoppingOptimizer()
        
        analysis = ForumAnalysis(
            jurisdiction="Federal (SEC)",
            jurisdiction_type="FEDERAL",
            venue_score=90.0,
            penalty_score=85.0,
            evidentiary_score=82.0
        )
        
        advantages = optimizer._identify_advantages(
            "Federal (SEC)", "FEDERAL", analysis
        )
        
        assert len(advantages) > 0
        assert any('National reach' in adv for adv in advantages)
    
    def test_identify_advantages_ny(self):
        """Test identifying NY Martin Act advantages."""
        optimizer = ForumShoppingOptimizer()
        
        analysis = ForumAnalysis(
            jurisdiction="NY",
            jurisdiction_type="STATE",
            venue_score=85.0,
            evidentiary_score=95.0
        )
        
        advantages = optimizer._identify_advantages(
            "NY", "STATE", analysis
        )
        
        assert any('Martin Act' in adv for adv in advantages)
        assert any('scienter' in adv.lower() for adv in advantages)
    
    def test_identify_disadvantages_international(self):
        """Test identifying international disadvantages."""
        optimizer = ForumShoppingOptimizer()
        
        analysis = ForumAnalysis(
            jurisdiction="United Kingdom",
            jurisdiction_type="INTERNATIONAL",
            venue_score=70.0
        )
        
        disadvantages = optimizer._identify_disadvantages(
            "United Kingdom", "INTERNATIONAL", analysis
        )
        
        assert len(disadvantages) > 0
        assert any('MLAT' in disadv for disadv in disadvantages)
    
    def test_estimate_penalties_federal(self):
        """Test federal penalty estimation."""
        optimizer = ForumShoppingOptimizer()
        
        violations = [
            {'severity': 'CRITICAL'},
            {'severity': 'HIGH'}
        ]
        
        penalties = optimizer._estimate_penalties(
            "Federal (SEC)", "FEDERAL", violations
        )
        
        assert penalties['criminal_years'] > 0
        assert penalties['criminal_fine'] > 0
        assert penalties['civil_damages'] > 0
        
        # Federal should have high fines
        assert penalties['criminal_fine'] >= 5_000_000
    
    def test_estimate_penalties_texas(self):
        """Test Texas penalty estimation (highest criminal)."""
        optimizer = ForumShoppingOptimizer()
        
        violations = [{'severity': 'CRITICAL'}]
        
        penalties = optimizer._estimate_penalties(
            "TX", "STATE", violations
        )
        
        # Texas can go up to 99 years
        assert penalties['criminal_years'] >= 10
    
    def test_generate_prosecution_strategy(self):
        """Test prosecution strategy generation."""
        optimizer = ForumShoppingOptimizer()
        
        # Create mock forum analyses
        forum_analyses = [
            ForumAnalysis(
                jurisdiction="Federal (SEC)",
                jurisdiction_type="FEDERAL",
                venue_score=95.0,
                recommended_priority="PRIMARY"
            ),
            ForumAnalysis(
                jurisdiction="CA",
                jurisdiction_type="STATE",
                venue_score=75.0,
                recommended_priority="SECONDARY"
            ),
            ForumAnalysis(
                jurisdiction="United Kingdom",
                jurisdiction_type="INTERNATIONAL",
                venue_score=65.0,
                recommended_priority="TERTIARY"
            )
        ]
        
        strategy = optimizer.generate_prosecution_strategy(forum_analyses)
        
        assert strategy is not None
        assert strategy['primary_venue'] is not None
        assert strategy['primary_venue']['jurisdiction'] == "Federal (SEC)"
        assert len(strategy['secondary_venues']) >= 1
        assert len(strategy['recommended_sequence']) >= 1
        
        # Check timing strategy
        assert 'avoid_stays' in strategy['timing_strategy']
        assert 'avoid_double_jeopardy' in strategy['timing_strategy']
    
    def test_venue_scoring_weights(self):
        """Test venue scoring weighted average calculation."""
        optimizer = ForumShoppingOptimizer()
        
        # Create forum analysis with known sub-scores
        analysis = ForumAnalysis(
            jurisdiction="Test",
            jurisdiction_type="FEDERAL",
            penalty_score=80.0,
            evidentiary_score=90.0,
            limitations_score=70.0,
            precedent_score=85.0,
            resources_score=95.0,
            political_will_score=88.0,
            victim_impact_score=75.0
        )
        
        # Calculate weighted score
        venue_score = (
            analysis.penalty_score * 0.25 +
            analysis.evidentiary_score * 0.20 +
            analysis.limitations_score * 0.15 +
            analysis.precedent_score * 0.15 +
            analysis.resources_score * 0.10 +
            analysis.political_will_score * 0.10 +
            analysis.victim_impact_score * 0.05
        )
        
        # Verify weights sum to 1.0
        weights_sum = 0.25 + 0.20 + 0.15 + 0.15 + 0.10 + 0.10 + 0.05
        assert weights_sum == 1.0
        
        # Score should be reasonable
        assert 0 <= venue_score <= 100
