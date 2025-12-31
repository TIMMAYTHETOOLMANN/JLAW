"""
Tests for Jurisdiction Mapper
==============================

Tests jurisdiction determination logic for federal, state, and international authorities.
"""

import pytest
from src.compliance.jurisdiction_mapper import (
    JurisdictionMapper,
    JurisdictionProfile,
    JurisdictionTrigger
)


class TestJurisdictionProfile:
    """Test JurisdictionProfile dataclass."""
    
    def test_jurisdiction_profile_creation(self):
        """Test creating a jurisdiction profile."""
        profile = JurisdictionProfile(
            jurisdiction_name="California",
            jurisdiction_type="STATE",
            regulatory_body="California DFPI",
            has_authority=True,
            authority_basis=["Issuer domiciled in state"],
            applicable_statutes=["CA Corp Code §25401"]
        )
        
        assert profile.jurisdiction_name == "California"
        assert profile.jurisdiction_type == "STATE"
        assert profile.has_authority is True
        assert len(profile.authority_basis) == 1
    
    def test_jurisdiction_profile_to_dict(self):
        """Test converting jurisdiction profile to dictionary."""
        profile = JurisdictionProfile(
            jurisdiction_name="Federal (SEC)",
            jurisdiction_type="FEDERAL",
            regulatory_body="SEC",
            has_authority=True
        )
        
        profile_dict = profile.to_dict()
        
        assert profile_dict["jurisdiction_name"] == "Federal (SEC)"
        assert profile_dict["jurisdiction_type"] == "FEDERAL"
        assert profile_dict["has_authority"] is True


class TestJurisdictionTrigger:
    """Test JurisdictionTrigger dataclass."""
    
    def test_trigger_creation(self):
        """Test creating a jurisdiction trigger."""
        trigger = JurisdictionTrigger(
            trigger_type="ISSUER_DOMICILE",
            location="California",
            evidence_id="evidence-001",
            statute_triggered="CA Corp Code §25401"
        )
        
        assert trigger.trigger_type == "ISSUER_DOMICILE"
        assert trigger.location == "California"
        assert trigger.evidence_id == "evidence-001"


@pytest.mark.asyncio
class TestJurisdictionMapper:
    """Test JurisdictionMapper class."""
    
    async def test_mapper_initialization(self):
        """Test jurisdiction mapper initialization."""
        mapper = JurisdictionMapper()
        
        assert mapper is not None
        assert mapper._jurisdiction_cache == {}
    
    async def test_federal_jurisdiction_determination(self):
        """Test federal jurisdiction determination."""
        mapper = JurisdictionMapper()
        
        company_profile = {
            'cik': '0001234567',
            'company_name': 'Test Corp',
            'state_of_incorporation': 'CA'
        }
        
        violations = [
            {'type': 'SECURITIES_FRAUD', 'severity': 'CRITICAL'}
        ]
        
        federal_jurisdictions = await mapper._determine_federal_jurisdiction(
            company_profile, violations
        )
        
        assert len(federal_jurisdictions) >= 2  # At least SEC and DOJ
        assert any(j.jurisdiction_name == "Federal (SEC)" for j in federal_jurisdictions)
        assert any(j.jurisdiction_name == "Federal (DOJ)" for j in federal_jurisdictions)
    
    async def test_state_jurisdiction_determination(self):
        """Test state jurisdiction determination."""
        mapper = JurisdictionMapper()
        
        company_profile = {
            'cik': '0001234567',
            'state_of_incorporation': 'CA',
            'headquarters_state': 'NY'
        }
        
        violations = []
        classified_actors = {}
        
        state_jurisdictions = await mapper._determine_state_jurisdiction(
            company_profile, violations, classified_actors
        )
        
        # Should have at least CA and NY
        assert len(state_jurisdictions) >= 2
        state_names = [j.jurisdiction_name for j in state_jurisdictions]
        assert 'CA' in state_names
        assert 'NY' in state_names
    
    async def test_international_jurisdiction_determination(self):
        """Test international jurisdiction determination."""
        mapper = JurisdictionMapper()
        
        company_profile = {
            'has_uk_listing': True,
            'has_eu_listing': False
        }
        
        violations = []
        classified_actors = {}
        
        intl_jurisdictions = await mapper._determine_international_jurisdiction(
            company_profile, violations, classified_actors
        )
        
        # Should have UK jurisdiction
        assert len(intl_jurisdictions) >= 1
        assert any(j.jurisdiction_name == "United Kingdom" for j in intl_jurisdictions)
    
    async def test_map_jurisdictions_integration(self):
        """Test full jurisdiction mapping integration."""
        mapper = JurisdictionMapper()
        
        company_profile = {
            'cik': '0001234567',
            'company_name': 'Test Corp',
            'state_of_incorporation': 'CA',
            'headquarters_state': 'CA'
        }
        
        violations = [
            {'type': 'SECURITIES_FRAUD', 'severity': 'CRITICAL'}
        ]
        
        classified_actors = {}
        
        jurisdictions = await mapper.map_jurisdictions(
            company_profile, violations, classified_actors
        )
        
        # Should have federal + state jurisdictions
        assert len(jurisdictions) >= 3  # SEC, DOJ, CA minimum
        
        # Check types
        federal = [j for j in jurisdictions if j.jurisdiction_type == 'FEDERAL']
        state = [j for j in jurisdictions if j.jurisdiction_type == 'STATE']
        
        assert len(federal) >= 2
        assert len(state) >= 1
    
    async def test_broker_dealer_involvement(self):
        """Test broker-dealer involvement detection."""
        mapper = JurisdictionMapper()
        
        violations_with_broker = [
            {'type': 'BROKER_DEALER_FRAUD', 'involves_broker_dealer': True}
        ]
        
        violations_without_broker = [
            {'type': 'SECURITIES_FRAUD'}
        ]
        
        assert mapper._has_broker_dealer_involvement(violations_with_broker) is True
        assert mapper._has_broker_dealer_involvement(violations_without_broker) is False
    
    def test_state_jurisdiction_profile_creation(self):
        """Test state jurisdiction profile creation."""
        mapper = JurisdictionMapper()
        
        profile = mapper._create_state_jurisdiction_profile(
            'CA',
            {'state_of_incorporation': 'CA', 'headquarters_state': 'CA'}
        )
        
        assert profile.jurisdiction_name == 'CA'
        assert profile.jurisdiction_type == 'STATE'
        assert len(profile.applicable_statutes) > 0
        assert 'CA Corp Code' in profile.applicable_statutes[0]
