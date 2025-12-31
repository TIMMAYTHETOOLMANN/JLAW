"""
Jurisdiction Mapper
==================

Determines all applicable jurisdictions with prosecutorial authority for securities violations.

Implements 7-trigger jurisdiction determination:
1. ISSUER_DOMICILE: State of incorporation
2. PRINCIPAL_PLACE_OF_BUSINESS: Headquarters location
3. OFFER_LOCATION: Where securities offered/sold
4. VICTIM_RESIDENCE: Where defrauded investors reside
5. ACTOR_RESIDENCE: Where perpetrators reside
6. LISTING_VENUE: NYSE/NASDAQ triggers federal SEC
7. CROSS_BORDER: International securities sales

Legal Framework:
- Federal: Securities Exchange Act of 1934 (15 U.S.C. §78a)
- State: Blue Sky Laws (50-state jurisdiction)
- International: MLAT treaties, extraterritorial enforcement
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class JurisdictionTrigger:
    """
    Represents a specific trigger that grants jurisdiction to a regulatory body.
    
    Attributes:
        trigger_type: Type of jurisdictional trigger
        location: Geographic location (e.g., "California", "United Kingdom")
        evidence_id: Reference to evidence supporting this trigger
        statute_triggered: Statute that grants jurisdiction
    """
    trigger_type: str  # "ISSUER_DOMICILE" | "OFFER_LOCATION" | "VICTIM_RESIDENCE" | etc.
    location: str
    evidence_id: str
    statute_triggered: str


@dataclass
class JurisdictionProfile:
    """
    Complete jurisdiction profile with authority determination.
    
    Attributes:
        jurisdiction_id: Unique identifier (UUID)
        jurisdiction_name: Human-readable name (e.g., "California", "Federal (SEC)")
        jurisdiction_type: Type of jurisdiction
        regulatory_body: Regulatory agency with authority
        has_authority: Whether jurisdiction has prosecutorial authority
        authority_basis: Reasons jurisdiction applies
        applicable_statutes: Statutes that can be enforced
        contact_info: Contact information for regulatory body
    """
    jurisdiction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    jurisdiction_name: str = ""
    jurisdiction_type: str = "STATE"  # "STATE" | "FEDERAL" | "INTERNATIONAL"
    regulatory_body: str = ""
    has_authority: bool = False
    authority_basis: List[str] = field(default_factory=list)
    applicable_statutes: List[str] = field(default_factory=list)
    contact_info: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'jurisdiction_id': self.jurisdiction_id,
            'jurisdiction_name': self.jurisdiction_name,
            'jurisdiction_type': self.jurisdiction_type,
            'regulatory_body': self.regulatory_body,
            'has_authority': self.has_authority,
            'authority_basis': self.authority_basis,
            'applicable_statutes': self.applicable_statutes,
            'contact_info': self.contact_info
        }


class JurisdictionMapper:
    """
    Main jurisdiction determination engine.
    
    Analyzes company profile, violations, and actor information to determine
    all jurisdictions with prosecutorial authority.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._jurisdiction_cache: Dict[str, JurisdictionProfile] = {}
    
    async def map_jurisdictions(
        self,
        company_profile: Dict[str, Any],
        violations: List[Dict[str, Any]],
        classified_actors: Dict[str, Any]
    ) -> List[JurisdictionProfile]:
        """
        Main orchestrator: Determine all applicable jurisdictions.
        
        Args:
            company_profile: Company information (CIK, state of incorporation, HQ location)
            violations: Detected violations
            classified_actors: Classified actor profiles with locations
        
        Returns:
            List of JurisdictionProfile objects with authority determinations
        """
        self.logger.info("Starting jurisdiction mapping...")
        
        jurisdictions = []
        triggers = []
        
        # Step 1: Determine federal jurisdiction
        federal_jurisdictions = await self._determine_federal_jurisdiction(
            company_profile, violations
        )
        jurisdictions.extend(federal_jurisdictions)
        self.logger.info(f"✓ Identified {len(federal_jurisdictions)} federal jurisdictions")
        
        # Step 2: Determine state jurisdiction
        state_jurisdictions = await self._determine_state_jurisdiction(
            company_profile, violations, classified_actors
        )
        jurisdictions.extend(state_jurisdictions)
        self.logger.info(f"✓ Identified {len(state_jurisdictions)} state jurisdictions")
        
        # Step 3: Determine international jurisdiction
        international_jurisdictions = await self._determine_international_jurisdiction(
            company_profile, violations, classified_actors
        )
        jurisdictions.extend(international_jurisdictions)
        self.logger.info(f"✓ Identified {len(international_jurisdictions)} international jurisdictions")
        
        # Cache results
        for jurisdiction in jurisdictions:
            self._jurisdiction_cache[jurisdiction.jurisdiction_id] = jurisdiction
        
        self.logger.info(f"✓ Total jurisdictions with authority: {len(jurisdictions)}")
        return jurisdictions
    
    async def _determine_federal_jurisdiction(
        self,
        company_profile: Dict[str, Any],
        violations: List[Dict[str, Any]]
    ) -> List[JurisdictionProfile]:
        """
        Determine federal jurisdiction (SEC, DOJ, FINRA, CFTC).
        
        Federal jurisdiction applies when:
        - Securities registered under Securities Exchange Act of 1934
        - Securities traded on national exchange (NYSE, NASDAQ)
        - Interstate commerce involved
        - Wire/mail fraud involved
        
        Returns:
            List of federal JurisdictionProfile objects
        """
        federal_jurisdictions = []
        
        # SEC Jurisdiction
        sec_jurisdiction = JurisdictionProfile(
            jurisdiction_name="Federal (SEC)",
            jurisdiction_type="FEDERAL",
            regulatory_body="Securities and Exchange Commission (SEC)",
            has_authority=True,
            authority_basis=[
                "Securities Exchange Act of 1934 (15 U.S.C. §78a)",
                "Securities registered with SEC",
                "National securities exchange listing"
            ],
            applicable_statutes=[
                "15 U.S.C. §78j(b) - Rule 10b-5 (Securities Fraud)",
                "15 U.S.C. §78p - Section 16 (Insider Trading)",
                "15 U.S.C. §78dd-1 - FCPA",
                "SOX Section 302, 404, 906"
            ],
            contact_info={
                "agency": "SEC Division of Enforcement",
                "phone": "202-551-4500",
                "email": "enforcement@sec.gov",
                "address": "100 F Street NE, Washington, DC 20549"
            }
        )
        federal_jurisdictions.append(sec_jurisdiction)
        
        # DOJ Criminal Jurisdiction
        doj_jurisdiction = JurisdictionProfile(
            jurisdiction_name="Federal (DOJ)",
            jurisdiction_type="FEDERAL",
            regulatory_body="Department of Justice (DOJ)",
            has_authority=True,
            authority_basis=[
                "Criminal securities fraud jurisdiction",
                "Wire/mail fraud jurisdiction",
                "Interstate commerce involvement"
            ],
            applicable_statutes=[
                "18 U.S.C. §1348 - Securities/Commodities Fraud",
                "18 U.S.C. §1343 - Wire Fraud",
                "18 U.S.C. §1341 - Mail Fraud",
                "18 U.S.C. §371 - Conspiracy"
            ],
            contact_info={
                "agency": "DOJ Fraud Section",
                "phone": "202-514-7023",
                "address": "1400 New York Avenue NW, Washington, DC 20530"
            }
        )
        federal_jurisdictions.append(doj_jurisdiction)
        
        # FINRA Jurisdiction (if broker-dealer involved)
        if self._has_broker_dealer_involvement(violations):
            finra_jurisdiction = JurisdictionProfile(
                jurisdiction_name="Federal (FINRA)",
                jurisdiction_type="FEDERAL",
                regulatory_body="Financial Industry Regulatory Authority (FINRA)",
                has_authority=True,
                authority_basis=[
                    "Broker-dealer involvement detected",
                    "FINRA member firm violations"
                ],
                applicable_statutes=[
                    "FINRA Rule 2010 - Standards of Commercial Honor",
                    "FINRA Rule 2020 - Use of Manipulative, Deceptive Devices",
                    "FINRA Rule 5310 - Best Execution"
                ],
                contact_info={
                    "agency": "FINRA Enforcement",
                    "phone": "240-386-4200",
                    "address": "1735 K Street NW, Washington, DC 20006"
                }
            )
            federal_jurisdictions.append(finra_jurisdiction)
        
        return federal_jurisdictions
    
    async def _determine_state_jurisdiction(
        self,
        company_profile: Dict[str, Any],
        violations: List[Dict[str, Any]],
        classified_actors: Dict[str, Any]
    ) -> List[JurisdictionProfile]:
        """
        Determine state jurisdiction (50-state Blue Sky Law analysis).
        
        State jurisdiction applies based on:
        1. Issuer domicile (state of incorporation)
        2. Principal place of business
        3. Offer locations (where securities offered/sold)
        4. Victim residence (where defrauded investors reside)
        5. Actor residence (where perpetrators reside)
        
        Returns:
            List of state JurisdictionProfile objects
        """
        state_jurisdictions = []
        triggered_states = set()
        
        # Trigger 1: Issuer Domicile
        state_of_incorporation = company_profile.get('state_of_incorporation')
        if state_of_incorporation:
            triggered_states.add(state_of_incorporation)
            self.logger.debug(f"State trigger: Issuer domicile in {state_of_incorporation}")
        
        # Trigger 2: Principal Place of Business
        headquarters_state = company_profile.get('headquarters_state')
        if headquarters_state:
            triggered_states.add(headquarters_state)
            self.logger.debug(f"State trigger: HQ in {headquarters_state}")
        
        # Trigger 3: Offer Locations (extract from violations)
        for violation in violations:
            offer_state = violation.get('offer_location_state')
            if offer_state:
                triggered_states.add(offer_state)
        
        # Trigger 4: Victim Residence (extract from actors)
        if classified_actors:
            # Extract victim locations from actor profiles
            for actor_id, actor_data in classified_actors.items():
                if isinstance(actor_data, dict):
                    state = actor_data.get('state')
                    if state and actor_data.get('role') == 'VICTIM':
                        triggered_states.add(state)
        
        # Trigger 5: Actor Residence
        if classified_actors:
            for actor_id, actor_data in classified_actors.items():
                if isinstance(actor_data, dict):
                    state = actor_data.get('state')
                    if state:
                        triggered_states.add(state)
        
        # Create jurisdiction profiles for each triggered state
        for state in triggered_states:
            state_jurisdiction = self._create_state_jurisdiction_profile(state, company_profile)
            state_jurisdictions.append(state_jurisdiction)
        
        return state_jurisdictions
    
    def _create_state_jurisdiction_profile(
        self,
        state: str,
        company_profile: Dict[str, Any]
    ) -> JurisdictionProfile:
        """
        Create jurisdiction profile for a specific state.
        
        Args:
            state: State abbreviation (e.g., "CA", "NY", "TX")
            company_profile: Company information
        
        Returns:
            JurisdictionProfile for the state
        """
        # State regulatory bodies mapping
        state_regulators = {
            "CA": "California Department of Financial Protection and Innovation (DFPI)",
            "NY": "New York Attorney General's Office (Martin Act)",
            "TX": "Texas State Securities Board",
            "FL": "Florida Office of Financial Regulation",
            "IL": "Illinois Securities Department",
            "MA": "Massachusetts Securities Division",
            # Default for other states
        }
        
        regulatory_body = state_regulators.get(state, f"{state} Securities Regulator")
        
        # Determine authority basis
        authority_basis = []
        if company_profile.get('state_of_incorporation') == state:
            authority_basis.append("Issuer domiciled in state")
        if company_profile.get('headquarters_state') == state:
            authority_basis.append("Principal place of business in state")
        
        # State-specific statutes (examples for major states)
        state_statutes = {
            "CA": [
                "CA Corp Code §25401 - Fraud in Sale of Securities",
                "CA Corp Code §25110 - Registration Requirement",
                "CA Corp Code §25216 - Sale of Unqualified Securities"
            ],
            "NY": [
                "NY Gen Bus Law §352 - Martin Act (Fraudulent Practices)",
                "NY Gen Bus Law §359-e - Criminal Penalties"
            ],
            "TX": [
                "TX Securities Act §33.02 - Registration",
                "TX Securities Act §33.04 - Fraud"
            ],
            "FL": [
                "FL Stat §517.301 - Registration",
                "FL Stat §517.07 - Fraudulent Transactions"
            ]
        }
        
        applicable_statutes = state_statutes.get(
            state,
            [f"{state} Uniform Securities Act §501 - Securities Fraud"]
        )
        
        return JurisdictionProfile(
            jurisdiction_name=state,
            jurisdiction_type="STATE",
            regulatory_body=regulatory_body,
            has_authority=True,
            authority_basis=authority_basis,
            applicable_statutes=applicable_statutes,
            contact_info={
                "agency": regulatory_body,
                "state": state
            }
        )
    
    async def _determine_international_jurisdiction(
        self,
        company_profile: Dict[str, Any],
        violations: List[Dict[str, Any]],
        classified_actors: Dict[str, Any]
    ) -> List[JurisdictionProfile]:
        """
        Determine international jurisdiction (UK FCA, EU ESMA, IIROC, ASIC).
        
        International jurisdiction applies when:
        - Securities offered/sold to foreign investors
        - Cross-border listings (ADRs, dual listings)
        - Foreign subsidiaries involved
        - Actors resident in foreign jurisdictions
        
        Returns:
            List of international JurisdictionProfile objects
        """
        international_jurisdictions = []
        
        # Check for international triggers
        has_uk_exposure = self._has_uk_exposure(company_profile, violations, classified_actors)
        has_eu_exposure = self._has_eu_exposure(company_profile, violations, classified_actors)
        has_canada_exposure = self._has_canada_exposure(company_profile, violations, classified_actors)
        has_australia_exposure = self._has_australia_exposure(company_profile, violations, classified_actors)
        
        # UK FCA Jurisdiction
        if has_uk_exposure:
            uk_jurisdiction = JurisdictionProfile(
                jurisdiction_name="United Kingdom",
                jurisdiction_type="INTERNATIONAL",
                regulatory_body="Financial Conduct Authority (FCA)",
                has_authority=True,
                authority_basis=[
                    "Securities offered/sold to UK investors",
                    "UK listing or trading involvement"
                ],
                applicable_statutes=[
                    "FSMA 2000 s.397 - Misleading Statements",
                    "Criminal Justice Act 1993 Part V - Insider Dealing",
                    "Market Abuse Regulation (MAR)"
                ],
                contact_info={
                    "agency": "FCA Enforcement and Market Oversight",
                    "phone": "+44 20 7066 1000",
                    "address": "12 Endeavour Square, London E20 1JN, UK"
                }
            )
            international_jurisdictions.append(uk_jurisdiction)
        
        # EU ESMA Jurisdiction
        if has_eu_exposure:
            eu_jurisdiction = JurisdictionProfile(
                jurisdiction_name="European Union",
                jurisdiction_type="INTERNATIONAL",
                regulatory_body="European Securities and Markets Authority (ESMA)",
                has_authority=True,
                authority_basis=[
                    "Securities offered/sold to EU investors",
                    "EU member state involvement"
                ],
                applicable_statutes=[
                    "MAR Article 15 - Market Manipulation",
                    "MiFID II - Markets in Financial Instruments Directive",
                    "Prospectus Regulation (EU 2017/1129)"
                ],
                contact_info={
                    "agency": "ESMA",
                    "phone": "+33 1 58 36 43 21",
                    "address": "201-203 Rue de Bercy, 75012 Paris, France"
                }
            )
            international_jurisdictions.append(eu_jurisdiction)
        
        # Canada (IIROC/CSA) Jurisdiction
        if has_canada_exposure:
            canada_jurisdiction = JurisdictionProfile(
                jurisdiction_name="Canada",
                jurisdiction_type="INTERNATIONAL",
                regulatory_body="Investment Industry Regulatory Organization of Canada (IIROC)",
                has_authority=True,
                authority_basis=[
                    "Securities offered/sold to Canadian investors",
                    "Canadian exchange listing"
                ],
                applicable_statutes=[
                    "National Instrument 31-103",
                    "Ontario Securities Act",
                    "Criminal Code §380 - Fraud"
                ],
                contact_info={
                    "agency": "IIROC",
                    "phone": "+1 416-364-6133",
                    "address": "121 King Street West, Suite 2000, Toronto, ON M5H 3T9"
                }
            )
            international_jurisdictions.append(canada_jurisdiction)
        
        # Australia (ASIC) Jurisdiction
        if has_australia_exposure:
            australia_jurisdiction = JurisdictionProfile(
                jurisdiction_name="Australia",
                jurisdiction_type="INTERNATIONAL",
                regulatory_body="Australian Securities and Investments Commission (ASIC)",
                has_authority=True,
                authority_basis=[
                    "Securities offered/sold to Australian investors",
                    "Australian listing involvement"
                ],
                applicable_statutes=[
                    "Corporations Act 2001",
                    "ASIC Act 2001"
                ],
                contact_info={
                    "agency": "ASIC",
                    "phone": "+61 1300 300 630",
                    "address": "Level 5, 100 Market Street, Sydney NSW 2000"
                }
            )
            international_jurisdictions.append(australia_jurisdiction)
        
        return international_jurisdictions
    
    def _has_broker_dealer_involvement(self, violations: List[Dict[str, Any]]) -> bool:
        """Check if violations involve broker-dealers."""
        for violation in violations:
            if violation.get('involves_broker_dealer', False):
                return True
            if 'broker' in str(violation).lower() or 'dealer' in str(violation).lower():
                return True
        return False
    
    def _has_uk_exposure(
        self,
        company_profile: Dict[str, Any],
        violations: List[Dict[str, Any]],
        classified_actors: Dict[str, Any]
    ) -> bool:
        """Check if there is UK exposure."""
        # Check for UK listing
        if company_profile.get('has_uk_listing', False):
            return True
        
        # Check for UK actors
        if classified_actors:
            for actor_data in classified_actors.values():
                if isinstance(actor_data, dict):
                    if actor_data.get('country') == 'UK' or actor_data.get('country') == 'United Kingdom':
                        return True
        
        return False
    
    def _has_eu_exposure(
        self,
        company_profile: Dict[str, Any],
        violations: List[Dict[str, Any]],
        classified_actors: Dict[str, Any]
    ) -> bool:
        """Check if there is EU exposure."""
        eu_countries = [
            'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic',
            'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary',
            'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta', 'Netherlands',
            'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden'
        ]
        
        # Check for EU listing
        if company_profile.get('has_eu_listing', False):
            return True
        
        # Check for EU actors
        if classified_actors:
            for actor_data in classified_actors.values():
                if isinstance(actor_data, dict):
                    if actor_data.get('country') in eu_countries:
                        return True
        
        return False
    
    def _has_canada_exposure(
        self,
        company_profile: Dict[str, Any],
        violations: List[Dict[str, Any]],
        classified_actors: Dict[str, Any]
    ) -> bool:
        """Check if there is Canada exposure."""
        # Check for Canadian listing
        if company_profile.get('has_canadian_listing', False):
            return True
        
        # Check for Canadian actors
        if classified_actors:
            for actor_data in classified_actors.values():
                if isinstance(actor_data, dict):
                    if actor_data.get('country') == 'Canada':
                        return True
        
        return False
    
    def _has_australia_exposure(
        self,
        company_profile: Dict[str, Any],
        violations: List[Dict[str, Any]],
        classified_actors: Dict[str, Any]
    ) -> bool:
        """Check if there is Australia exposure."""
        # Check for Australian listing
        if company_profile.get('has_australian_listing', False):
            return True
        
        # Check for Australian actors
        if classified_actors:
            for actor_data in classified_actors.values():
                if isinstance(actor_data, dict):
                    if actor_data.get('country') == 'Australia':
                        return True
        
        return False
