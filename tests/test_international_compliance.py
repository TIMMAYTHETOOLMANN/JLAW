"""
Tests for International Compliance Analyzer
===========================================

Tests international securities law analysis for UK, EU, Canada, Australia, etc.
"""

import pytest
from src.compliance.international_compliance import (
    InternationalComplianceAnalyzer,
    InternationalRegulation
)


class TestInternationalRegulation:
    """Test InternationalRegulation dataclass."""
    
    def test_regulation_creation(self):
        """Test creating an international regulation."""
        regulation = InternationalRegulation(
            jurisdiction='United Kingdom',
            regulator='Financial Conduct Authority (FCA)',
            regulation_name='Market Abuse',
            regulation_citation='MAR',
            violation_type='MARKET_MANIPULATION',
            penalties={'criminal': 'Up to 7 years'},
            mutual_legal_assistance=True
        )
        
        assert regulation.jurisdiction == 'United Kingdom'
        assert regulation.mutual_legal_assistance is True
    
    def test_regulation_to_dict(self):
        """Test converting regulation to dictionary."""
        regulation = InternationalRegulation(
            jurisdiction='Canada',
            regulator='IIROC',
            regulation_name='Market Integrity',
            regulation_citation='IIROC Rule 2500',
            violation_type='MARKET_MANIPULATION',
            penalties={'administrative': 'Fines'},
            mutual_legal_assistance=True
        )
        
        reg_dict = regulation.to_dict()
        
        assert reg_dict['jurisdiction'] == 'Canada'
        assert reg_dict['mutual_legal_assistance'] is True


@pytest.mark.asyncio
class TestInternationalComplianceAnalyzer:
    """Test InternationalComplianceAnalyzer class."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = InternationalComplianceAnalyzer()
        
        assert analyzer is not None
        assert analyzer._regulations_loaded is False
    
    def test_load_builtin_regulations(self):
        """Test loading built-in international regulations."""
        analyzer = InternationalComplianceAnalyzer()
        analyzer._load_builtin_regulations()
        
        # Check major jurisdictions are loaded
        assert 'United Kingdom' in analyzer.regulations
        assert 'European Union' in analyzer.regulations
        assert 'Canada' in analyzer.regulations
        assert 'Australia' in analyzer.regulations
        assert 'Switzerland' in analyzer.regulations
    
    def test_uk_fca_regulations(self):
        """Test UK FCA regulations."""
        analyzer = InternationalComplianceAnalyzer()
        analyzer._load_builtin_regulations()
        
        uk_regulations = analyzer.regulations['United Kingdom']
        
        # Check FSMA and MAR
        assert len(uk_regulations) >= 2
        assert any('FSMA' in reg.regulation_citation for reg in uk_regulations)
        assert any('MAR' in reg.regulation_citation for reg in uk_regulations)
        
        # All should have MLAT
        assert all(reg.mutual_legal_assistance for reg in uk_regulations)
    
    def test_eu_esma_regulations(self):
        """Test EU ESMA regulations."""
        analyzer = InternationalComplianceAnalyzer()
        analyzer._load_builtin_regulations()
        
        eu_regulations = analyzer.regulations['European Union']
        
        # Check MiFID II and MAR
        assert len(eu_regulations) >= 2
        assert any('MiFID' in reg.regulation_name for reg in eu_regulations)
        assert any('MAR' in reg.regulation_citation for reg in eu_regulations)
    
    def test_canada_iiroc_regulations(self):
        """Test Canada IIROC/CSA regulations."""
        analyzer = InternationalComplianceAnalyzer()
        analyzer._load_builtin_regulations()
        
        canada_regulations = analyzer.regulations['Canada']
        
        # Check National Instrument and Criminal Code
        assert len(canada_regulations) >= 2
        assert any('National Instrument' in reg.regulation_name for reg in canada_regulations)
        assert any('Criminal Code' in reg.regulation_citation for reg in canada_regulations)
    
    def test_australia_asic_regulations(self):
        """Test Australia ASIC regulations."""
        analyzer = InternationalComplianceAnalyzer()
        analyzer._load_builtin_regulations()
        
        australia_regulations = analyzer.regulations['Australia']
        
        # Check Corporations Act
        assert len(australia_regulations) >= 2
        assert any('Corporations Act' in reg.regulation_citation for reg in australia_regulations)
    
    async def test_analyze_cross_border_violations(self):
        """Test cross-border violation analysis."""
        analyzer = InternationalComplianceAnalyzer()
        
        company_profile = {
            'has_uk_listing': True,
            'has_eu_listing': False
        }
        
        violations = [
            {
                'id': 'v001',
                'type': 'MARKET_MANIPULATION',
                'description': 'Manipulative trading activity',
                'severity': 'CRITICAL'
            }
        ]
        
        investor_locations = ['United Kingdom', 'France']
        
        intl_violations = await analyzer.analyze_cross_border_violations(
            company_profile, violations, investor_locations
        )
        
        # Should find UK violations
        assert len(intl_violations) > 0
        assert any(v['jurisdiction'] == 'United Kingdom' for v in intl_violations)
    
    def test_identify_relevant_jurisdictions(self):
        """Test relevant jurisdiction identification."""
        analyzer = InternationalComplianceAnalyzer()
        
        # UK listing
        company_profile_uk = {'has_uk_listing': True}
        jurisdictions_uk = analyzer._identify_relevant_jurisdictions(
            company_profile_uk, None
        )
        assert 'United Kingdom' in jurisdictions_uk
        
        # Canadian investors
        investor_locations = ['Canada']
        jurisdictions_ca = analyzer._identify_relevant_jurisdictions(
            {}, investor_locations
        )
        assert 'Canada' in jurisdictions_ca
        
        # EU investors (France triggers EU)
        investor_locations_eu = ['France', 'Germany']
        jurisdictions_eu = analyzer._identify_relevant_jurisdictions(
            {}, investor_locations_eu
        )
        assert 'European Union' in jurisdictions_eu
    
    def test_violation_matches_regulation(self):
        """Test violation matching to regulation types."""
        analyzer = InternationalComplianceAnalyzer()
        
        market_manip_violation = {'type': 'MARKET_MANIPULATION'}
        insider_violation = {'type': 'INSIDER_TRADING'}
        
        market_manip_reg = InternationalRegulation(
            jurisdiction='UK',
            regulator='FCA',
            regulation_name='MAR',
            regulation_citation='MAR',
            violation_type='MARKET_MANIPULATION',
            penalties={}
        )
        
        insider_reg = InternationalRegulation(
            jurisdiction='UK',
            regulator='FCA',
            regulation_name='Insider Dealing',
            regulation_citation='CJA 1993',
            violation_type='INSIDER_TRADING',
            penalties={}
        )
        
        assert analyzer._violation_matches_regulation(
            market_manip_violation, market_manip_reg
        ) is True
        assert analyzer._violation_matches_regulation(
            insider_violation, market_manip_reg
        ) is False
        assert analyzer._violation_matches_regulation(
            insider_violation, insider_reg
        ) is True
    
    def test_determine_extraterritorial_basis(self):
        """Test extraterritorial basis determination."""
        analyzer = InternationalComplianceAnalyzer()
        
        company_profile = {'has_uk_listing': True}
        violation = {'type': 'FRAUD'}
        
        basis = analyzer._determine_extraterritorial_basis(
            'United Kingdom', company_profile, violation
        )
        
        assert len(basis) > 0
        assert any('UK securities listing' in b for b in basis)
        assert any('Effects doctrine' in b for b in basis)
    
    def test_generate_mlat_request_template(self):
        """Test MLAT request template generation."""
        analyzer = InternationalComplianceAnalyzer()
        analyzer._load_builtin_regulations()
        
        violation = {
            'type': 'SECURITIES_FRAUD',
            'description': 'Fraudulent misrepresentation',
            'severity': 'CRITICAL'
        }
        
        evidence_needed = [
            'Bank records from UK financial institution',
            'Trading records from London Stock Exchange'
        ]
        
        mlat_request = analyzer.generate_mlat_request_template(
            'United Kingdom', violation, evidence_needed
        )
        
        assert mlat_request['request_type'] == 'MLAT'
        assert mlat_request['requesting_country'] == 'United States'
        assert mlat_request['requested_country'] == 'United Kingdom'
        assert mlat_request['urgency'] == 'HIGH'
        assert len(mlat_request['evidence_requested']) == 2
    
    def test_mlat_contact_information(self):
        """Test MLAT central authority contact info."""
        analyzer = InternationalComplianceAnalyzer()
        
        uk_contact = analyzer._get_mlat_contact('United Kingdom')
        assert 'UK Central Authority' in uk_contact.get('agency', '')
        
        canada_contact = analyzer._get_mlat_contact('Canada')
        assert 'Department of Justice Canada' in canada_contact.get('department', '')
        
        australia_contact = analyzer._get_mlat_contact('Australia')
        assert 'Attorney-General' in australia_contact.get('department', '')
    
    def test_mlat_availability(self):
        """Test MLAT treaty availability check."""
        analyzer = InternationalComplianceAnalyzer()
        analyzer._load_builtin_regulations()
        
        # All major jurisdictions should have MLAT
        for jurisdiction in ['United Kingdom', 'Canada', 'Australia', 'Switzerland']:
            regulations = analyzer.regulations[jurisdiction]
            assert any(reg.mutual_legal_assistance for reg in regulations), \
                f"Expected MLAT for {jurisdiction}"
