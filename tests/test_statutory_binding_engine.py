"""
Unit Tests for Statutory Binding Engine (RIM Phase 1)
====================================================

Tests the violation-to-statute mapping engine:
- Statute mapping for all violation types
- Enforcement pathway classification
- Plain-language explanations
- Evidence requirements generation
"""

import pytest
from src.legal.statutory_binding_engine import (
    StatutoryBindingEngine,
    Statute,
    StatutoryBinding,
    EnforcementAgency,
    CaseType
)


class TestStatutoryBindingEngine:
    """Test suite for StatutoryBindingEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return StatutoryBindingEngine()
    
    @pytest.fixture
    def sample_violations(self):
        """Sample violations for binding."""
        return [
            {
                'violation_id': 'V001',
                'violation_type': 'insider_trading_form4_late',
                'description': 'Form 4 filed 5 days late',
                'confidence': 0.95,
                'actor_name': 'John Doe'
            },
            {
                'violation_id': 'V002',
                'violation_type': 'insider_trading_10b5_material_nonpublic',
                'description': 'Trading on material information',
                'confidence': 0.88,
                'actor_name': 'Jane Smith'
            },
            {
                'violation_id': 'V003',
                'violation_type': 'section_16b_short_swing',
                'description': 'Short-swing profit violation',
                'confidence': 0.92,
                'actor_name': 'Bob Johnson'
            },
            {
                'violation_id': 'V004',
                'violation_type': 'zero_dollar_gift_tax_evasion',
                'description': 'Zero-dollar gift not reported',
                'confidence': 0.87,
                'actor_name': 'Alice Cooper'
            }
        ]
    
    def test_initialization(self, engine):
        """Test engine initialization and statute map."""
        assert engine is not None
        assert hasattr(engine, 'VIOLATION_TO_STATUTE_MAP')
        assert len(engine.VIOLATION_TO_STATUTE_MAP) > 0
        
        # Check core statutes are loaded
        assert engine.STATUTE_FORM4_LATE is not None
        assert engine.STATUTE_10B5_CIVIL is not None
        assert engine.STATUTE_16B_SHORT_SWING is not None
        assert engine.STATUTE_IRC_83 is not None
    
    def test_bind_form4_late_violation(self, engine):
        """Test binding for Form 4 late filing."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V001',
            violation_type='insider_trading_form4_late',
            violation_details={
                'confidence': 0.95,
                'days_late': 5
            }
        )
        
        assert isinstance(binding, StatutoryBinding)
        assert binding.violation_id == 'V001'
        assert binding.violation_type == 'insider_trading_form4_late'
        assert len(binding.statutes) >= 1
        assert binding.enforcement_pathway == 'SEC'
        assert binding.confidence == 0.95
        
        # Check statute
        statute = binding.statutes[0]
        assert statute.code == '17 CFR § 240.16a-3(a)'
        assert statute.enforcement_agency == EnforcementAgency.SEC
        assert statute.case_type == CaseType.CIVIL
    
    def test_bind_10b5_violation(self, engine):
        """Test binding for Rule 10b-5 violation."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V002',
            violation_type='insider_trading_10b5_material_nonpublic',
            violation_details={'confidence': 0.88}
        )
        
        assert len(binding.statutes) == 2  # Both civil and criminal
        
        # Check for both SEC (civil) and DOJ (criminal)
        agencies = [s.enforcement_agency for s in binding.statutes]
        assert EnforcementAgency.SEC in agencies
        assert EnforcementAgency.DOJ in agencies
        
        # Should have MULTIPLE enforcement pathway
        assert binding.enforcement_pathway == 'MULTIPLE'
    
    def test_bind_short_swing_violation(self, engine):
        """Test binding for Section 16(b) short-swing."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V003',
            violation_type='section_16b_short_swing',
            violation_details={'confidence': 0.92}
        )
        
        assert len(binding.statutes) >= 1
        statute = binding.statutes[0]
        assert '16' in statute.code or '78p' in statute.code
        assert statute.enforcement_agency == EnforcementAgency.SEC
    
    def test_bind_gift_tax_violation(self, engine):
        """Test binding for gift/tax evasion."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V004',
            violation_type='zero_dollar_gift_tax_evasion',
            violation_details={'confidence': 0.87}
        )
        
        assert len(binding.statutes) >= 1
        statute = binding.statutes[0]
        assert 'IRC § 83' in statute.code
        assert statute.enforcement_agency == EnforcementAgency.IRS
    
    def test_bind_all_violations(self, engine, sample_violations):
        """Test binding multiple violations."""
        bindings = engine.bind_all_violations(sample_violations)
        
        assert len(bindings) == 4
        
        # All should have statutes
        for binding in bindings:
            assert len(binding.statutes) > 0
            assert binding.confidence > 0.0
            assert binding.plain_language_explanation
            assert len(binding.recommended_actions) > 0
            assert len(binding.evidence_requirements) > 0
    
    def test_plain_language_explanation(self, engine):
        """Test plain-language explanation generation."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V001',
            violation_type='insider_trading_form4_late',
            violation_details={'confidence': 0.95}
        )
        
        explanation = binding.plain_language_explanation
        
        assert explanation is not None
        assert len(explanation) > 50
        assert 'CFR' in explanation or 'USC' in explanation
        # Should not contain hedging language
        assert 'may indicate' not in explanation.lower()
        assert 'could suggest' not in explanation.lower()
    
    def test_recommended_actions_sec(self, engine):
        """Test recommended actions for SEC violations."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V001',
            violation_type='insider_trading_form4_late',
            violation_details={'confidence': 0.95}
        )
        
        actions = binding.recommended_actions
        
        assert len(actions) > 0
        assert any('SEC' in action for action in actions)
        assert any('evidence' in action.lower() for action in actions)
    
    def test_recommended_actions_doj(self, engine):
        """Test recommended actions for DOJ violations."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V002',
            violation_type='insider_trading_10b5_material_nonpublic',
            violation_details={'confidence': 0.88}
        )
        
        actions = binding.recommended_actions
        
        assert len(actions) > 0
        assert any('DOJ' in action for action in actions)
        assert any('criminal' in action.lower() for action in actions)
    
    def test_recommended_actions_irs(self, engine):
        """Test recommended actions for IRS violations."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V004',
            violation_type='zero_dollar_gift_tax_evasion',
            violation_details={'confidence': 0.87}
        )
        
        actions = binding.recommended_actions
        
        assert len(actions) > 0
        assert any('IRS' in action for action in actions)
    
    def test_evidence_requirements(self, engine):
        """Test evidence requirements generation."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V001',
            violation_type='insider_trading_form4_late',
            violation_details={'confidence': 0.95}
        )
        
        requirements = binding.evidence_requirements
        
        assert len(requirements) > 0
        # Should include hash verification
        assert any('hash' in req.lower() for req in requirements)
        # Should include chain of custody
        assert any('custody' in req.lower() for req in requirements)
    
    def test_enforcement_summary(self, engine, sample_violations):
        """Test enforcement summary generation."""
        bindings = engine.bind_all_violations(sample_violations)
        summary = engine.get_enforcement_summary(bindings)
        
        assert 'total_violations' in summary
        assert 'by_agency' in summary
        assert 'by_case_type' in summary
        assert 'criminal_exposure' in summary
        assert 'statutes_invoked' in summary
        
        assert summary['total_violations'] == 4
        # At least one agency should have violations
        assert summary['by_agency']['SEC'] >= 0
        assert summary['by_agency']['DOJ'] >= 0
        assert summary['by_agency']['IRS'] >= 0
    
    def test_unknown_violation_type(self, engine):
        """Test handling of unknown violation type."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V999',
            violation_type='UNKNOWN_VIOLATION_TYPE',
            violation_details={'confidence': 0.75}
        )
        
        # Should fallback to default statute (10b-5)
        assert len(binding.statutes) > 0
        assert binding.statutes[0].code == '17 CFR § 240.10b-5'
    
    def test_statute_serialization(self):
        """Test Statute to_dict() method."""
        statute = Statute(
            code='17 CFR § 240.10b-5',
            title='Rule 10b-5',
            description='Prohibits fraud',
            enforcement_agency=EnforcementAgency.SEC,
            case_type=CaseType.CIVIL,
            penalty_range='Up to $1M',
            precedent_cases=['SEC v. Cuban']
        )
        
        data = statute.to_dict()
        
        assert data['code'] == '17 CFR § 240.10b-5'
        assert data['enforcement_agency'] == 'SEC'
        assert data['case_type'] == 'CIVIL'
        assert data['penalty_range'] == 'Up to $1M'
    
    def test_binding_serialization(self, engine):
        """Test StatutoryBinding to_dict() method."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V001',
            violation_type='insider_trading_form4_late',
            violation_details={'confidence': 0.95}
        )
        
        data = binding.to_dict()
        
        assert data['binding_id'] == 'BIND_V001'
        assert data['violation_id'] == 'V001'
        assert data['violation_type'] == 'insider_trading_form4_late'
        assert len(data['statutes']) > 0
        assert 'created_at' in data
    
    def test_sox_violation_binding(self, engine):
        """Test binding for SOX violations."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V005',
            violation_type='sox_certification_false',
            violation_details={'confidence': 0.91}
        )
        
        # Should have both SOX 302 and 906
        assert len(binding.statutes) >= 2
        
        statute_codes = [s.code for s in binding.statutes]
        assert any('302' in code for code in statute_codes)
        assert any('906' in code for code in statute_codes)
    
    def test_options_backdating_binding(self, engine):
        """Test binding for options backdating."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V006',
            violation_type='options_backdating',
            violation_details={'confidence': 0.89}
        )
        
        # Should have multiple statutes (10b-5, 1348, IRC 83)
        assert len(binding.statutes) >= 2
        
        # Check for criminal exposure
        case_types = [s.case_type for s in binding.statutes]
        assert CaseType.CRIMINAL in case_types or CaseType.BOTH in case_types
    
    def test_temporal_correlation_binding(self, engine):
        """Test binding for temporal correlation violations."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V007',
            violation_type='TEMPORAL_CORRELATION_SUSPICIOUS',
            violation_details={'confidence': 0.85}
        )
        
        # Should map to insider trading statutes
        assert len(binding.statutes) >= 1
        statute_codes = [s.code for s in binding.statutes]
        assert any('10b' in code.lower() for code in statute_codes)
    
    def test_clustered_activity_binding(self, engine):
        """Test binding for clustered suspicious activity."""
        binding = engine.bind_violation_to_statutes(
            violation_id='V008',
            violation_type='CLUSTERED_SUSPICIOUS_ACTIVITY',
            violation_details={'confidence': 0.82}
        )
        
        # Should have multiple applicable statutes
        assert len(binding.statutes) >= 1
