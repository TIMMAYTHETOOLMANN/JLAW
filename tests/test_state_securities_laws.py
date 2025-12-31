"""
Tests for State Securities Law Engine
======================================

Tests 50-state Blue Sky Law database and violation analysis.
"""

import pytest
from src.compliance.state_securities_laws import (
    StateSecuritiesLawEngine,
    StateSecuritiesLaw
)


class TestStateSecuritiesLaw:
    """Test StateSecuritiesLaw dataclass."""
    
    def test_state_law_creation(self):
        """Test creating a state securities law."""
        law = StateSecuritiesLaw(
            state='CA',
            statute_citation='CA Corp Code §25401',
            statute_name='Fraud in Sale of Securities',
            statute_type='FRAUD',
            elements=['Material misrepresentation', 'Scienter'],
            penalties={'criminal': 'Up to 5 years', 'civil': 'Rescission'},
            statute_of_limitations='3 years',
            extraterritorial_reach=True
        )
        
        assert law.state == 'CA'
        assert law.statute_type == 'FRAUD'
        assert law.extraterritorial_reach is True
    
    def test_state_law_to_dict(self):
        """Test converting state law to dictionary."""
        law = StateSecuritiesLaw(
            state='NY',
            statute_citation='NY Gen Bus Law §352',
            statute_name='Martin Act',
            statute_type='FRAUD',
            elements=['Fraudulent practices'],
            penalties={'criminal': 'Up to 4 years'},
            statute_of_limitations='6 years'
        )
        
        law_dict = law.to_dict()
        
        assert law_dict['state'] == 'NY'
        assert law_dict['statute_citation'] == 'NY Gen Bus Law §352'


@pytest.mark.asyncio
class TestStateSecuritiesLawEngine:
    """Test StateSecuritiesLawEngine class."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = StateSecuritiesLawEngine()
        
        assert engine is not None
        assert engine._laws_loaded is False
    
    def test_load_builtin_state_laws(self):
        """Test loading built-in state laws."""
        engine = StateSecuritiesLawEngine()
        engine._load_builtin_state_laws()
        
        # Check major states are loaded
        assert 'CA' in engine.state_laws
        assert 'NY' in engine.state_laws
        assert 'TX' in engine.state_laws
        assert 'FL' in engine.state_laws
        
        # Check law details
        ca_laws = engine.state_laws['CA']
        assert len(ca_laws) >= 1
        assert any(law.statute_citation == 'CA Corp Code §25401' for law in ca_laws)
    
    def test_california_laws(self):
        """Test California-specific laws."""
        engine = StateSecuritiesLawEngine()
        engine._load_builtin_state_laws()
        
        ca_laws = engine.state_laws['CA']
        
        # Check fraud statute
        fraud_law = next((law for law in ca_laws if law.statute_type == 'FRAUD'), None)
        assert fraud_law is not None
        assert fraud_law.extraterritorial_reach is True
        assert 'Scienter' in fraud_law.elements or 'scienter' in str(fraud_law.elements).lower()
    
    def test_new_york_martin_act(self):
        """Test New York Martin Act (strict liability)."""
        engine = StateSecuritiesLawEngine()
        engine._load_builtin_state_laws()
        
        ny_laws = engine.state_laws['NY']
        
        # Check Martin Act
        martin_act = next((law for law in ny_laws if 'Martin Act' in law.statute_name), None)
        assert martin_act is not None
        assert 'No scienter required' in martin_act.elements or 'strict liability' in str(martin_act.elements).lower()
        assert martin_act.statute_of_limitations == '6 years'
    
    def test_texas_harsh_penalties(self):
        """Test Texas harsh criminal penalties."""
        engine = StateSecuritiesLawEngine()
        engine._load_builtin_state_laws()
        
        tx_laws = engine.state_laws['TX']
        
        # Check fraud statute
        fraud_law = next((law for law in tx_laws if law.statute_type == 'FRAUD'), None)
        assert fraud_law is not None
        assert '99 years' in fraud_law.penalties.get('criminal', '')
    
    async def test_analyze_state_violations(self):
        """Test state violation analysis."""
        engine = StateSecuritiesLawEngine()
        
        # Create mock violations
        violations = [
            {
                'id': 'v001',
                'type': 'FRAUD',
                'description': 'Material misrepresentation in offering document'
            }
        ]
        
        # Create mock jurisdictions
        class MockJurisdiction:
            def __init__(self, name):
                self.jurisdiction_name = name
                self.jurisdiction_type = 'STATE'
                self.authority_basis = ['Issuer domicile']
        
        jurisdictions = [
            MockJurisdiction('CA'),
            MockJurisdiction('NY')
        ]
        
        state_violations = await engine.analyze_state_violations(
            violations, jurisdictions
        )
        
        # Should find violations for both states
        assert len(state_violations) > 0
    
    def test_violation_matches_statute(self):
        """Test violation matching to statute types."""
        engine = StateSecuritiesLawEngine()
        
        fraud_violation = {'type': 'SECURITIES_FRAUD'}
        registration_violation = {'type': 'UNREGISTERED_OFFERING'}
        
        fraud_law = StateSecuritiesLaw(
            state='CA',
            statute_citation='CA Corp Code §25401',
            statute_name='Fraud',
            statute_type='FRAUD',
            elements=[],
            penalties={},
            statute_of_limitations='3 years'
        )
        
        registration_law = StateSecuritiesLaw(
            state='CA',
            statute_citation='CA Corp Code §25110',
            statute_name='Registration',
            statute_type='REGISTRATION',
            elements=[],
            penalties={},
            statute_of_limitations='3 years'
        )
        
        assert engine._violation_matches_statute(fraud_violation, fraud_law) is True
        assert engine._violation_matches_statute(fraud_violation, registration_law) is False
        assert engine._violation_matches_statute(registration_violation, registration_law) is True
    
    def test_check_elements(self):
        """Test checking which legal elements are met."""
        engine = StateSecuritiesLawEngine()
        
        violation = {
            'description': 'Company made false statements about earnings'
        }
        
        law = StateSecuritiesLaw(
            state='CA',
            statute_citation='CA Corp Code §25401',
            statute_name='Fraud',
            statute_type='FRAUD',
            elements=[
                'Material misrepresentation or omission',
                'In connection with offer/sale of security',
                'Scienter (intent to deceive)'
            ],
            penalties={},
            statute_of_limitations='3 years'
        )
        
        met_elements = engine._check_elements(violation, law)
        
        # Should detect misrepresentation element
        assert len(met_elements) > 0
    
    def test_compare_state_vs_federal(self):
        """Test state vs federal penalty comparison."""
        engine = StateSecuritiesLawEngine()
        
        state_violations = [
            {
                'state': 'TX',
                'penalties': {'criminal': 'Up to 99 years imprisonment'}
            }
        ]
        
        federal_violations = [
            {'penalties': {'criminal': 'Up to 25 years'}}
        ]
        
        comparison = engine.compare_state_vs_federal(
            state_violations, federal_violations
        )
        
        # Texas should be recommended over federal
        assert 'State criminal penalties' in str(comparison.get('state_advantages', []))
    
    def test_uniform_securities_act_states(self):
        """Test USA states have default statutes."""
        engine = StateSecuritiesLawEngine()
        engine._load_builtin_state_laws()
        
        # Check a few USA states
        for state in ['AL', 'CO', 'OH']:
            assert state in engine.state_laws
            laws = engine.state_laws[state]
            assert len(laws) > 0
            assert any('Uniform Securities Act' in law.statute_citation for law in laws)
