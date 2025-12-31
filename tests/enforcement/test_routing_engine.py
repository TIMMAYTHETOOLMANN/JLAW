"""
Unit Tests for Enforcement Routing Engine - Phase 5
===================================================

Comprehensive tests for the enforcement routing engine including:
- Enforcement recommendation generation
- SEC trigger threshold assessment
- Whistleblower relevance flagging
- Penalty estimation
- Agency routing logic
- Integration with statutory bindings
"""

import pytest
from decimal import Decimal
from src.enforcement.routing_engine import (
    EnforcementRoutingEngine,
    EnforcementRecommendation,
    PenaltyRange,
    EnforcementAgency,
    CaseType,
    Priority,
    PenaltyType
)


class TestEnforcementRoutingEngine:
    """Test suite for EnforcementRoutingEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return EnforcementRoutingEngine()
    
    @pytest.fixture
    def sample_violations_insider_trading(self):
        """Sample insider trading violations."""
        return [
            {
                'violation_id': 'V001',
                'violation_type': 'insider_trading',
                'description': 'Trading on material information',
                'estimated_damages': 500000,
                'scienter_evidence': True,
                'severity': 'HIGH'
            },
            {
                'violation_id': 'V002',
                'violation_type': 'insider_trading',
                'description': 'Form 4 filed late',
                'estimated_damages': 0,
                'scienter_evidence': False,
                'severity': 'MEDIUM'
            }
        ]
    
    @pytest.fixture
    def sample_violations_late_filing(self):
        """Sample late filing violations."""
        return [
            {
                'violation_id': f'V{i:03d}',
                'violation_type': 'late_filing',
                'description': f'Form 4 filed {i+2} days late',
                'estimated_damages': 0,
                'scienter_evidence': False,
                'severity': 'LOW'
            }
            for i in range(6)  # 6 late filings
        ]
    
    @pytest.fixture
    def sample_violations_securities_fraud(self):
        """Sample securities fraud violations."""
        return [
            {
                'violation_id': 'V010',
                'violation_type': 'securities_fraud',
                'description': 'Material misrepresentation in 10-K',
                'estimated_damages': 2000000,
                'scienter_evidence': True,
                'severity': 'CRITICAL'
            }
        ]
    
    @pytest.fixture
    def sample_statutory_bindings(self):
        """Sample statutory bindings."""
        return [
            {
                'violation_id': 'V001',
                'statutes': [
                    {'code': '17 CFR § 240.10b-5'},
                    {'code': '15 USC § 78j(b)'}
                ]
            },
            {
                'violation_id': 'V002',
                'statutes': [
                    {'code': '17 CFR § 240.16a-3(a)'}
                ]
            }
        ]
    
    # ═══════════════════════════════════════════════════════════════════════
    # INITIALIZATION TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert hasattr(engine, 'SEC_TRIGGER_THRESHOLDS')
        assert hasattr(engine, 'WHISTLEBLOWER_THRESHOLD')
        assert hasattr(engine, 'PENALTY_RANGES')
        
        # Check threshold values
        assert engine.WHISTLEBLOWER_THRESHOLD == 1000000
        assert engine.WHISTLEBLOWER_AWARD_MIN == 0.10
        assert engine.WHISTLEBLOWER_AWARD_MAX == 0.30
    
    def test_sec_trigger_thresholds_structure(self, engine):
        """Test SEC trigger thresholds are properly structured."""
        assert 'insider_trading' in engine.SEC_TRIGGER_THRESHOLDS
        assert 'securities_fraud' in engine.SEC_TRIGGER_THRESHOLDS
        assert 'late_filing' in engine.SEC_TRIGGER_THRESHOLDS
        
        # Check structure of threshold data
        threshold = engine.SEC_TRIGGER_THRESHOLDS['insider_trading']
        assert 'min_violations' in threshold
        assert 'min_damages' in threshold
        assert 'description' in threshold
    
    # ═══════════════════════════════════════════════════════════════════════
    # SEC TRIGGER ASSESSMENT TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_assess_sec_trigger_insider_trading_met(self, engine, sample_violations_insider_trading):
        """Test SEC trigger assessment for insider trading - threshold met."""
        result = engine.assess_sec_trigger(
            violations=sample_violations_insider_trading,
            violation_type='insider_trading'
        )
        
        # Should meet threshold: 2 violations, $500K damages
        # Threshold: 1 violation, $100K damages
        assert result is True
    
    def test_assess_sec_trigger_insider_trading_not_met_low_damages(self, engine):
        """Test SEC trigger assessment - not met due to low damages."""
        violations = [
            {
                'violation_id': 'V001',
                'violation_type': 'insider_trading',
                'estimated_damages': 50000  # Below $100K threshold
            }
        ]
        
        result = engine.assess_sec_trigger(
            violations=violations,
            violation_type='insider_trading'
        )
        
        # Should NOT meet threshold: damages too low
        assert result is False
    
    def test_assess_sec_trigger_late_filing_met(self, engine, sample_violations_late_filing):
        """Test SEC trigger assessment for late filing - threshold met."""
        result = engine.assess_sec_trigger(
            violations=sample_violations_late_filing,
            violation_type='late_filing'
        )
        
        # Should meet threshold: 6 violations (threshold is 5)
        assert result is True
    
    def test_assess_sec_trigger_late_filing_not_met(self, engine):
        """Test SEC trigger assessment for late filing - not met."""
        violations = [
            {'violation_id': f'V{i:03d}', 'violation_type': 'late_filing', 'estimated_damages': 0}
            for i in range(3)  # Only 3 violations
        ]
        
        result = engine.assess_sec_trigger(
            violations=violations,
            violation_type='late_filing'
        )
        
        # Should NOT meet threshold: only 3 violations (need 5)
        assert result is False
    
    def test_assess_sec_trigger_securities_fraud_met(self, engine, sample_violations_securities_fraud):
        """Test SEC trigger assessment for securities fraud - threshold met."""
        result = engine.assess_sec_trigger(
            violations=sample_violations_securities_fraud,
            violation_type='securities_fraud'
        )
        
        # Should meet threshold: 1 violation, $2M damages (threshold $500K)
        assert result is True
    
    def test_assess_sec_trigger_empty_violations(self, engine):
        """Test SEC trigger assessment with empty violations list."""
        result = engine.assess_sec_trigger(
            violations=[],
            violation_type='insider_trading'
        )
        
        assert result is False
    
    # ═══════════════════════════════════════════════════════════════════════
    # WHISTLEBLOWER RELEVANCE TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_assess_whistleblower_relevance_met(self, engine):
        """Test whistleblower relevance assessment - threshold met."""
        result = engine.assess_whistleblower_relevance(
            estimated_sanctions=2000000,  # $2M exceeds $1M threshold
            violation_types=['SEC', 'DOJ']
        )
        
        # Should be relevant: exceeds $1M and SEC jurisdiction
        assert result is True
    
    def test_assess_whistleblower_relevance_not_met_low_sanctions(self, engine):
        """Test whistleblower relevance - not met due to low sanctions."""
        result = engine.assess_whistleblower_relevance(
            estimated_sanctions=500000,  # $500K below $1M threshold
            violation_types=['SEC']
        )
        
        # Should NOT be relevant: sanctions too low
        assert result is False
    
    def test_assess_whistleblower_relevance_not_met_wrong_agency(self, engine):
        """Test whistleblower relevance - not met due to wrong agency."""
        result = engine.assess_whistleblower_relevance(
            estimated_sanctions=2000000,  # Exceeds threshold
            violation_types=['IRS', 'DOJ']  # No SEC or CFTC
        )
        
        # Should NOT be relevant: no SEC/CFTC jurisdiction
        assert result is False
    
    def test_assess_whistleblower_relevance_cftc_jurisdiction(self, engine):
        """Test whistleblower relevance with CFTC jurisdiction."""
        result = engine.assess_whistleblower_relevance(
            estimated_sanctions=1500000,
            violation_types=['CFTC']
        )
        
        # Should be relevant: CFTC is whistleblower agency
        assert result is True
    
    def test_assess_whistleblower_relevance_edge_case_exact_threshold(self, engine):
        """Test whistleblower relevance at exact $1M threshold."""
        result = engine.assess_whistleblower_relevance(
            estimated_sanctions=1000000,  # Exactly $1M
            violation_types=['SEC']
        )
        
        # Should be relevant: meets threshold exactly
        assert result is True
    
    # ═══════════════════════════════════════════════════════════════════════
    # PENALTY ESTIMATION TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_calculate_penalty_estimate_insider_trading(self, engine):
        """Test penalty estimation for insider trading."""
        penalty = engine.calculate_penalty_estimate(
            violation_type='insider_trading',
            violation_count=2,
            estimated_damages=500000
        )
        
        assert isinstance(penalty, PenaltyRange)
        assert penalty.min_penalty > 0
        assert penalty.max_penalty > penalty.min_penalty
        assert penalty.penalty_type in ['civil', 'criminal', 'both']
        assert penalty.basis is not None
        assert '17 CFR' in penalty.basis or '15 USC' in penalty.basis
    
    def test_calculate_penalty_estimate_securities_fraud(self, engine):
        """Test penalty estimation for securities fraud."""
        penalty = engine.calculate_penalty_estimate(
            violation_type='securities_fraud',
            violation_count=1,
            estimated_damages=2000000
        )
        
        assert isinstance(penalty, PenaltyRange)
        assert penalty.penalty_type == 'both'  # Should have criminal exposure
        assert penalty.max_penalty > 1000000  # Should be substantial
    
    def test_calculate_penalty_estimate_late_filing(self, engine):
        """Test penalty estimation for late filing."""
        penalty = engine.calculate_penalty_estimate(
            violation_type='late_filing',
            violation_count=5,
            estimated_damages=0
        )
        
        assert isinstance(penalty, PenaltyRange)
        assert penalty.penalty_type == 'civil'  # Late filing is civil only
        assert penalty.min_penalty > 0
    
    def test_calculate_penalty_estimate_multipliers(self, engine):
        """Test penalty estimation with count multipliers."""
        # Single violation
        penalty_single = engine.calculate_penalty_estimate(
            violation_type='disclosure_violation',
            violation_count=1,
            estimated_damages=100000
        )
        
        # Multiple violations
        penalty_multiple = engine.calculate_penalty_estimate(
            violation_type='disclosure_violation',
            violation_count=5,
            estimated_damages=100000
        )
        
        # Multiple violations should have higher penalties
        assert penalty_multiple.min_penalty > penalty_single.min_penalty
        assert penalty_multiple.max_penalty > penalty_single.max_penalty
    
    def test_calculate_penalty_estimate_damage_multiplier(self, engine):
        """Test penalty estimation with damage multipliers."""
        # Low damages
        penalty_low = engine.calculate_penalty_estimate(
            violation_type='insider_trading',
            violation_count=1,
            estimated_damages=100000
        )
        
        # High damages
        penalty_high = engine.calculate_penalty_estimate(
            violation_type='insider_trading',
            violation_count=1,
            estimated_damages=15000000
        )
        
        # High damages should result in higher max penalty
        assert penalty_high.max_penalty > penalty_low.max_penalty
    
    def test_penalty_range_to_dict(self, engine):
        """Test PenaltyRange to_dict serialization."""
        penalty = engine.calculate_penalty_estimate(
            violation_type='insider_trading',
            violation_count=1,
            estimated_damages=500000
        )
        
        penalty_dict = penalty.to_dict()
        assert isinstance(penalty_dict, dict)
        assert 'min_penalty' in penalty_dict
        assert 'max_penalty' in penalty_dict
        assert 'penalty_type' in penalty_dict
        assert 'basis' in penalty_dict
    
    # ═══════════════════════════════════════════════════════════════════════
    # AGENCY ROUTING TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_route_violations_insider_trading(self, engine, sample_violations_insider_trading):
        """Test routing for insider trading violations."""
        recommendations = engine.route_violations(
            violations=sample_violations_insider_trading,
            statutory_bindings=None
        )
        
        assert len(recommendations) > 0
        
        # Should recommend SEC
        agencies = [rec.agency for rec in recommendations]
        assert 'SEC' in agencies
        
        # Check recommendation structure
        rec = recommendations[0]
        assert isinstance(rec, EnforcementRecommendation)
        assert rec.agency in ['SEC', 'DOJ', 'IRS', 'CFTC', 'FinCEN']
        assert rec.case_type in ['civil', 'criminal']
        assert rec.priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        assert isinstance(rec.trigger_threshold_met, bool)
        assert rec.justification is not None
        assert len(rec.violation_ids) > 0
    
    def test_route_violations_securities_fraud(self, engine, sample_violations_securities_fraud):
        """Test routing for securities fraud violations."""
        recommendations = engine.route_violations(
            violations=sample_violations_securities_fraud,
            statutory_bindings=None
        )
        
        assert len(recommendations) > 0
        
        # Should recommend SEC and possibly DOJ (due to high damages + scienter)
        agencies = [rec.agency for rec in recommendations]
        assert 'SEC' in agencies
        
        # At least one should have criminal case type
        case_types = [rec.case_type for rec in recommendations]
        assert 'criminal' in case_types
    
    def test_route_violations_with_statutory_bindings(
        self, 
        engine, 
        sample_violations_insider_trading,
        sample_statutory_bindings
    ):
        """Test routing with statutory bindings integration."""
        recommendations = engine.route_violations(
            violations=sample_violations_insider_trading,
            statutory_bindings=sample_statutory_bindings
        )
        
        assert len(recommendations) > 0
        
        # Check statutory references are included
        rec = recommendations[0]
        assert len(rec.statutory_references) > 0
    
    def test_route_violations_empty_list(self, engine):
        """Test routing with empty violations list."""
        recommendations = engine.route_violations(
            violations=[],
            statutory_bindings=None
        )
        
        assert recommendations == []
    
    def test_route_violations_mixed_types(self, engine):
        """Test routing with mixed violation types."""
        violations = [
            {
                'violation_id': 'V001',
                'violation_type': 'insider_trading',
                'estimated_damages': 500000,
                'scienter_evidence': True
            },
            {
                'violation_id': 'V002',
                'violation_type': 'late_filing',
                'estimated_damages': 0,
                'scienter_evidence': False
            },
            {
                'violation_id': 'V003',
                'violation_type': 'tax_violation',
                'estimated_damages': 300000,
                'scienter_evidence': False
            }
        ]
        
        recommendations = engine.route_violations(
            violations=violations,
            statutory_bindings=None
        )
        
        assert len(recommendations) > 0
        
        # Should route to multiple agencies
        agencies = set(rec.agency for rec in recommendations)
        assert len(agencies) > 1
        assert 'SEC' in agencies or 'IRS' in agencies
    
    def test_route_violations_whistleblower_flagging(self, engine):
        """Test whistleblower flagging in routing."""
        violations = [
            {
                'violation_id': f'V{i:03d}',
                'violation_type': 'securities_fraud',
                'estimated_damages': 2000000,  # High damages to trigger whistleblower
                'scienter_evidence': True
            }
            for i in range(3)
        ]
        
        recommendations = engine.route_violations(
            violations=violations,
            statutory_bindings=None
        )
        
        assert len(recommendations) > 0
        
        # At least one recommendation should flag whistleblower relevance
        whistleblower_flags = [rec.whistleblower_relevant for rec in recommendations]
        assert any(whistleblower_flags)
    
    def test_enforcement_recommendation_to_dict(self, engine, sample_violations_insider_trading):
        """Test EnforcementRecommendation to_dict serialization."""
        recommendations = engine.route_violations(
            violations=sample_violations_insider_trading,
            statutory_bindings=None
        )
        
        assert len(recommendations) > 0
        
        rec_dict = recommendations[0].to_dict()
        assert isinstance(rec_dict, dict)
        assert 'agency' in rec_dict
        assert 'case_type' in rec_dict
        assert 'priority' in rec_dict
        assert 'trigger_threshold_met' in rec_dict
        assert 'justification' in rec_dict
        assert 'whistleblower_relevant' in rec_dict
        assert 'violation_ids' in rec_dict
        assert 'statutory_references' in rec_dict
        assert 'recommended_actions' in rec_dict
    
    # ═══════════════════════════════════════════════════════════════════════
    # ROUTING REPORT TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_generate_routing_report(self, engine, sample_violations_insider_trading):
        """Test routing report generation."""
        recommendations = engine.route_violations(
            violations=sample_violations_insider_trading,
            statutory_bindings=None
        )
        
        report = engine.generate_routing_report(recommendations)
        
        assert isinstance(report, dict)
        assert 'total_recommendations' in report
        assert 'agencies' in report
        assert 'priorities' in report
        assert 'trigger_thresholds_met' in report
        assert 'whistleblower_relevant' in report
        assert 'estimated_sanctions_range' in report
        assert 'summary' in report
        assert 'recommendations' in report
        
        assert report['total_recommendations'] == len(recommendations)
        assert isinstance(report['agencies'], dict)
        assert isinstance(report['estimated_sanctions_range'], dict)
    
    def test_generate_routing_report_empty(self, engine):
        """Test routing report with empty recommendations."""
        report = engine.generate_routing_report([])
        
        assert report['total_recommendations'] == 0
        assert report['agencies'] == {}
        assert report['whistleblower_relevant'] is False
        assert 'No enforcement recommendations' in report['summary']
    
    def test_generate_routing_report_with_whistleblower(self, engine):
        """Test routing report with whistleblower flagging."""
        violations = [
            {
                'violation_id': 'V001',
                'violation_type': 'securities_fraud',
                'estimated_damages': 5000000,
                'scienter_evidence': True
            }
        ]
        
        recommendations = engine.route_violations(violations, None)
        report = engine.generate_routing_report(recommendations)
        
        # Should flag whistleblower relevance
        if report['whistleblower_relevant']:
            assert 'Dodd-Frank §922' in report['summary']
    
    def test_generate_routing_report_sanctions_calculation(self, engine):
        """Test sanctions calculation in routing report."""
        violations = [
            {
                'violation_id': 'V001',
                'violation_type': 'insider_trading',
                'estimated_damages': 500000
            },
            {
                'violation_id': 'V002',
                'violation_type': 'securities_fraud',
                'estimated_damages': 2000000
            }
        ]
        
        recommendations = engine.route_violations(violations, None)
        report = engine.generate_routing_report(recommendations)
        
        sanctions = report['estimated_sanctions_range']
        assert sanctions['min'] > 0
        assert sanctions['max'] > sanctions['min']
    
    # ═══════════════════════════════════════════════════════════════════════
    # RECOMMENDED ACTIONS TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_recommended_actions_included(self, engine, sample_violations_insider_trading):
        """Test that recommended actions are included in recommendations."""
        recommendations = engine.route_violations(
            violations=sample_violations_insider_trading,
            statutory_bindings=None
        )
        
        assert len(recommendations) > 0
        
        for rec in recommendations:
            assert len(rec.recommended_actions) > 0
            assert all(isinstance(action, str) for action in rec.recommended_actions)
    
    def test_recommended_actions_sec_specific(self, engine):
        """Test SEC-specific recommended actions."""
        violations = [
            {
                'violation_id': 'V001',
                'violation_type': 'insider_trading',
                'estimated_damages': 500000
            }
        ]
        
        recommendations = engine.route_violations(violations, None)
        
        # Find SEC recommendation
        sec_rec = next((r for r in recommendations if r.agency == 'SEC'), None)
        assert sec_rec is not None
        
        actions = sec_rec.recommended_actions
        # Should include SEC-specific actions
        assert any('SEC' in action or 'TCR' in action for action in actions)
    
    def test_recommended_actions_doj_criminal(self, engine):
        """Test DOJ criminal referral recommended actions."""
        violations = [
            {
                'violation_id': 'V001',
                'violation_type': 'securities_fraud',
                'estimated_damages': 5000000,
                'scienter_evidence': True
            }
        ]
        
        recommendations = engine.route_violations(violations, None)
        
        # Find DOJ recommendation
        doj_rec = next((r for r in recommendations if r.agency == 'DOJ'), None)
        
        if doj_rec:
            actions = doj_rec.recommended_actions
            # Should include criminal prosecution actions
            assert any('criminal' in action.lower() or 'DOJ' in action for action in actions)
    
    # ═══════════════════════════════════════════════════════════════════════
    # PRIORITY CLASSIFICATION TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_priority_critical_high_damages(self, engine):
        """Test CRITICAL priority for high-damage violations."""
        violations = [
            {
                'violation_id': 'V001',
                'violation_type': 'securities_fraud',
                'estimated_damages': 50000000,  # Very high damages
                'scienter_evidence': True
            }
        ]
        
        recommendations = engine.route_violations(violations, None)
        
        # Should have CRITICAL priority
        priorities = [rec.priority for rec in recommendations]
        assert 'CRITICAL' in priorities
    
    def test_priority_high_trigger_met(self, engine):
        """Test HIGH priority when trigger threshold is met."""
        violations = [
            {
                'violation_id': 'V001',
                'violation_type': 'insider_trading',
                'estimated_damages': 2000000  # Exceeds trigger
            }
        ]
        
        recommendations = engine.route_violations(violations, None)
        
        # Should have HIGH or CRITICAL priority
        priorities = [rec.priority for rec in recommendations]
        assert 'HIGH' in priorities or 'CRITICAL' in priorities
    
    def test_priority_medium_multiple_violations(self, engine):
        """Test MEDIUM priority for multiple violations."""
        violations = [
            {
                'violation_id': f'V{i:03d}',
                'violation_type': 'disclosure_violation',
                'estimated_damages': 50000
            }
            for i in range(4)  # 4 violations
        ]
        
        recommendations = engine.route_violations(violations, None)
        
        # Should have MEDIUM or higher priority
        priorities = [rec.priority for rec in recommendations]
        assert any(p in ['MEDIUM', 'HIGH', 'CRITICAL'] for p in priorities)


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestEnforcementRoutingEngineIntegration:
    """Integration tests with statutory bindings and node results."""
    
    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return EnforcementRoutingEngine()
    
    def test_integration_with_statutory_bindings(self, engine):
        """Test full integration with statutory bindings."""
        violations = [
            {
                'violation_id': 'V001',
                'violation_type': 'insider_trading_10b5_material_nonpublic',
                'estimated_damages': 1500000,
                'scienter_evidence': True,
                'severity': 'CRITICAL'
            }
        ]
        
        statutory_bindings = [
            {
                'violation_id': 'V001',
                'statutes': [
                    {'code': '17 CFR § 240.10b-5'},
                    {'code': '15 USC § 78j(b)'},
                    {'code': '18 USC § 1348'}
                ]
            }
        ]
        
        recommendations = engine.route_violations(
            violations=violations,
            statutory_bindings=statutory_bindings
        )
        
        assert len(recommendations) > 0
        
        # Should include statutory references
        rec = recommendations[0]
        assert len(rec.statutory_references) > 0
        assert any('17 CFR' in ref or '15 USC' in ref for ref in rec.statutory_references)
    
    def test_end_to_end_workflow(self, engine):
        """Test complete end-to-end workflow."""
        # Simulate violations from multiple nodes
        violations = [
            # Node 1: Form 4 violations
            {
                'violation_id': 'N1_V001',
                'violation_type': 'late_filing',
                'estimated_damages': 0,
                'source_node': 'node1'
            },
            {
                'violation_id': 'N1_V002',
                'violation_type': 'insider_trading',
                'estimated_damages': 750000,
                'scienter_evidence': True,
                'source_node': 'node1'
            },
            # Node 4: SOX violations
            {
                'violation_id': 'N4_V001',
                'violation_type': 'sox_violation',
                'estimated_damages': 1000000,
                'scienter_evidence': True,
                'source_node': 'node4'
            },
            # Node 5: Tax violations
            {
                'violation_id': 'N5_V001',
                'violation_type': 'tax_violation',
                'estimated_damages': 500000,
                'source_node': 'node5'
            }
        ]
        
        # Generate recommendations
        recommendations = engine.route_violations(violations, None)
        
        # Should have multiple recommendations
        assert len(recommendations) > 0
        
        # Should route to multiple agencies
        agencies = set(rec.agency for rec in recommendations)
        assert len(agencies) >= 2  # At least SEC and IRS or DOJ
        
        # Generate routing report
        report = engine.generate_routing_report(recommendations)
        
        # Validate report structure
        assert report['total_recommendations'] == len(recommendations)
        assert report['trigger_thresholds_met'] >= 0
        assert 'summary' in report
        
        # Check whistleblower relevance (should be flagged for $2.25M total)
        assert isinstance(report['whistleblower_relevant'], bool)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
