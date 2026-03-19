"""
State Securities Law Engine
===========================

50-state Blue Sky Law database and violation analysis engine.

Implements comprehensive state securities law framework including:
- Uniform Securities Act (USA) states (40 states)
- California custom framework (Corp Code §25401, §25110, §25216)
- New York Martin Act (Gen Bus Law §352, §359-e)
- Texas Securities Act (§33.02, §33.04)
- Florida Statutes (§517.301, §517.07)
- All remaining states with specific statutes

Legal Framework:
- Uniform Securities Act (2002) - adopted by 40 states
- State-specific fraud statutes
- Registration requirements
- Broker-dealer regulations
- Extraterritorial reach provisions
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class StateSecuritiesLaw:
    """
    Represents a state securities law statute.
    
    Attributes:
        state: State abbreviation (e.g., "CA", "NY")
        statute_citation: Full statutory citation
        statute_name: Human-readable statute name
        statute_type: Type of statute
        elements: Legal elements that must be proven
        penalties: Penalties by type (criminal, civil, administrative)
        statute_of_limitations: Limitations period
        extraterritorial_reach: Whether state asserts extraterritorial jurisdiction
    """
    state: str
    statute_citation: str
    statute_name: str
    statute_type: str  # "REGISTRATION" | "FRAUD" | "BROKER_DEALER"
    elements: List[str]
    penalties: Dict[str, str]
    statute_of_limitations: str
    extraterritorial_reach: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'state': self.state,
            'statute_citation': self.statute_citation,
            'statute_name': self.statute_name,
            'statute_type': self.statute_type,
            'elements': self.elements,
            'penalties': self.penalties,
            'statute_of_limitations': self.statute_of_limitations,
            'extraterritorial_reach': self.extraterritorial_reach
        }


class StateSecuritiesLawEngine:
    """
    50-state Blue Sky Law analysis engine.
    
    Loads comprehensive state securities law database and analyzes violations
    under state-specific statutes.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.state_laws: Dict[str, List[StateSecuritiesLaw]] = {}
        self._laws_loaded = False
    
    def _load_all_state_laws(self):
        """
        Load complete 50-state securities law database.
        
        Loads from JSON file if available, otherwise uses built-in database.
        """
        if self._laws_loaded:
            return
        
        # Try to load from JSON file
        data_dir = Path(__file__).parent / "data"
        json_path = data_dir / "state_securities_laws.json"
        
        if json_path.exists():
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    self._parse_json_data(data)
                    self.logger.info(f"✓ Loaded state laws from {json_path}")
                    self._laws_loaded = True
                    return
            except Exception as e:
                self.logger.warning(f"Failed to load JSON database: {e}, using built-in")
        
        # Fallback: Use built-in database
        self._load_builtin_state_laws()
        self._laws_loaded = True
    
    def _parse_json_data(self, data: Dict[str, Any]):
        """Parse JSON data into StateSecuritiesLaw objects."""
        for state_name, state_data in data.items():
            statutes = []
            for statute_data in state_data.get('statutes', []):
                statute = StateSecuritiesLaw(
                    state=state_data.get('abbreviation', state_name[:2].upper()),
                    statute_citation=statute_data['citation'],
                    statute_name=statute_data['name'],
                    statute_type=statute_data['type'],
                    elements=statute_data['elements'],
                    penalties=statute_data['penalties'],
                    statute_of_limitations=statute_data['statute_of_limitations'],
                    extraterritorial_reach=statute_data.get('extraterritorial', False)
                )
                statutes.append(statute)
            
            state_abbr = state_data.get('abbreviation', state_name[:2].upper())
            self.state_laws[state_abbr] = statutes
    
    def _load_builtin_state_laws(self):
        """
        Load built-in state securities law database.
        
        Includes major states and Uniform Securities Act framework for others.
        """
        # California
        self.state_laws['CA'] = [
            StateSecuritiesLaw(
                state='CA',
                statute_citation='CA Corp Code §25401',
                statute_name='Fraud in Sale of Securities',
                statute_type='FRAUD',
                elements=[
                    'Material misrepresentation or omission',
                    'In connection with offer/sale of security',
                    'Scienter (intent to deceive)'
                ],
                penalties={
                    'criminal': 'Up to 5 years imprisonment + $10M fine',
                    'civil': 'Rescission + damages + attorney fees',
                    'administrative': 'Cease and desist + disgorgement'
                },
                statute_of_limitations='3 years from violation, 1 year from discovery',
                extraterritorial_reach=True
            ),
            StateSecuritiesLaw(
                state='CA',
                statute_citation='CA Corp Code §25110',
                statute_name='Registration of Securities',
                statute_type='REGISTRATION',
                elements=[
                    'Offer or sale of security',
                    'Security not registered or exempt'
                ],
                penalties={
                    'criminal': 'Up to 3 years imprisonment',
                    'civil': 'Rescission',
                    'administrative': 'Cease and desist'
                },
                statute_of_limitations='3 years',
                extraterritorial_reach=False
            )
        ]
        
        # New York
        self.state_laws['NY'] = [
            StateSecuritiesLaw(
                state='NY',
                statute_citation='NY Gen Bus Law §352',
                statute_name='Martin Act - Fraudulent Practices',
                statute_type='FRAUD',
                elements=[
                    'Fraudulent practices in securities dealings',
                    'No scienter required (strict liability)'
                ],
                penalties={
                    'criminal': 'Felony: up to 4 years + $5,000 fine',
                    'civil': 'Restitution + penalties',
                    'administrative': 'Broad AG powers'
                },
                statute_of_limitations='6 years',
                extraterritorial_reach=True
            )
        ]
        
        # Texas
        self.state_laws['TX'] = [
            StateSecuritiesLaw(
                state='TX',
                statute_citation='TX Securities Act §33.04',
                statute_name='Fraud in Securities Transactions',
                statute_type='FRAUD',
                elements=[
                    'Material misrepresentation or omission',
                    'In connection with offer/sale/purchase',
                    'Scienter required'
                ],
                penalties={
                    'criminal': 'Up to 99 years or life imprisonment + $10K fine',
                    'civil': 'Actual damages + attorney fees',
                    'administrative': 'Cease and desist + civil penalties'
                },
                statute_of_limitations='3 years from violation',
                extraterritorial_reach=True
            )
        ]
        
        # Florida
        self.state_laws['FL'] = [
            StateSecuritiesLaw(
                state='FL',
                statute_citation='FL Stat §517.07',
                statute_name='Fraudulent Transactions',
                statute_type='FRAUD',
                elements=[
                    'Material misrepresentation or omission',
                    'In connection with securities transaction',
                    'Scienter required'
                ],
                penalties={
                    'criminal': 'Up to 5 years imprisonment',
                    'civil': 'Rescission + damages',
                    'administrative': 'Cease and desist + fines'
                },
                statute_of_limitations='3 years',
                extraterritorial_reach=False
            )
        ]
        
        # Uniform Securities Act states (template for remaining 46 states)
        usa_states = [
            'AL', 'AK', 'AZ', 'AR', 'CO', 'CT', 'DE', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA',
            'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV',
            'NH', 'NJ', 'NM', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN',
            'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]
        
        for state in usa_states:
            self.state_laws[state] = [
                StateSecuritiesLaw(
                    state=state,
                    statute_citation=f'{state} Uniform Securities Act §501',
                    statute_name='Securities Fraud',
                    statute_type='FRAUD',
                    elements=[
                        'Material misrepresentation or omission',
                        'In connection with offer/sale of security',
                        'Scienter required'
                    ],
                    penalties={
                        'criminal': 'Up to 5 years imprisonment + fines',
                        'civil': 'Rescission + damages',
                        'administrative': 'Cease and desist + civil penalties'
                    },
                    statute_of_limitations='3 years',
                    extraterritorial_reach=False
                )
            ]
        
        self.logger.info(f"✓ Loaded laws for {len(self.state_laws)} states")
    
    async def analyze_state_violations(
        self,
        violations: List[Dict[str, Any]],
        jurisdictions: List[Any]  # List of JurisdictionProfile objects
    ) -> List[Dict[str, Any]]:
        """
        Analyze violations under state securities laws.
        
        Args:
            violations: Detected violations from node analysis
            jurisdictions: State jurisdictions with authority
        
        Returns:
            List of state-specific violation analyses
        """
        # Ensure laws are loaded
        self._load_all_state_laws()
        
        state_violations = []
        
        # Extract state jurisdictions
        state_jurisdictions = [
            j for j in jurisdictions 
            if hasattr(j, 'jurisdiction_type') and j.jurisdiction_type == 'STATE'
        ]
        
        self.logger.info(f"Analyzing violations for {len(state_jurisdictions)} states")
        
        for jurisdiction in state_jurisdictions:
            state = jurisdiction.jurisdiction_name if hasattr(jurisdiction, 'jurisdiction_name') else str(jurisdiction)
            
            # Get state laws
            state_laws = self.state_laws.get(state, [])
            if not state_laws:
                self.logger.warning(f"No laws found for state: {state}")
                continue
            
            # Analyze each violation against state laws
            for violation in violations:
                for law in state_laws:
                    # Check if violation matches statute type
                    if self._violation_matches_statute(violation, law):
                        state_violation = {
                            'violation_id': violation.get('id', 'unknown'),
                            'state': state,
                            'statute_citation': law.statute_citation,
                            'statute_name': law.statute_name,
                            'violation_description': violation.get('description', ''),
                            'elements_met': self._check_elements(violation, law),
                            'penalties': law.penalties,
                            'statute_of_limitations': law.statute_of_limitations,
                            'jurisdiction_basis': jurisdiction.authority_basis if hasattr(jurisdiction, 'authority_basis') else []
                        }
                        state_violations.append(state_violation)
        
        self.logger.info(f"✓ Identified {len(state_violations)} state-level violations")
        return state_violations
    
    def _violation_matches_statute(
        self,
        violation: Dict[str, Any],
        law: StateSecuritiesLaw
    ) -> bool:
        """
        Check if violation type matches statute type.
        
        Args:
            violation: Violation data
            law: State securities law
        
        Returns:
            True if violation matches statute, False otherwise
        """
        violation_type = violation.get('type', '').upper()
        
        # Fraud violations match FRAUD statutes
        if law.statute_type == 'FRAUD':
            fraud_keywords = ['FRAUD', 'MISREPRESENTATION', 'OMISSION', 'MANIPULATION', 'INSIDER']
            return any(keyword in violation_type for keyword in fraud_keywords)
        
        # Registration violations match REGISTRATION statutes
        if law.statute_type == 'REGISTRATION':
            registration_keywords = ['REGISTRATION', 'UNREGISTERED', 'OFFERING']
            return any(keyword in violation_type for keyword in registration_keywords)
        
        # Broker-dealer violations match BROKER_DEALER statutes
        if law.statute_type == 'BROKER_DEALER':
            broker_keywords = ['BROKER', 'DEALER', 'SUITABILITY']
            return any(keyword in violation_type for keyword in broker_keywords)
        
        return False
    
    def _check_elements(
        self,
        violation: Dict[str, Any],
        law: StateSecuritiesLaw
    ) -> List[str]:
        """
        Check which legal elements are met by the violation.
        
        Args:
            violation: Violation data
            law: State securities law
        
        Returns:
            List of elements that appear to be met
        """
        met_elements = []
        
        violation_desc = str(violation.get('description', '')).lower()
        
        for element in law.elements:
            element_lower = element.lower()
            
            # Check for key terms
            if 'misrepresentation' in element_lower:
                if 'false' in violation_desc or 'misleading' in violation_desc:
                    met_elements.append(element)
            elif 'omission' in element_lower:
                if 'omit' in violation_desc or 'failed to disclose' in violation_desc:
                    met_elements.append(element)
            elif 'scienter' in element_lower or 'intent' in element_lower:
                if 'knowing' in violation_desc or 'intentional' in violation_desc:
                    met_elements.append(element)
            elif 'security' in element_lower:
                if 'stock' in violation_desc or 'securities' in violation_desc:
                    met_elements.append(element)
        
        return met_elements
    
    def compare_state_vs_federal(
        self,
        state_violations: List[Dict[str, Any]],
        federal_violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare state law penalties to federal penalties for forum shopping.
        
        Args:
            state_violations: State-level violations
            federal_violations: Federal-level violations
        
        Returns:
            Comparison analysis for prosecutorial strategy
        """
        comparison = {
            'state_advantages': [],
            'federal_advantages': [],
            'recommended_primary_forum': 'FEDERAL'
        }
        
        # Analyze state penalties
        state_criminal_max = 0
        for sv in state_violations:
            penalties = sv.get('penalties', {})
            criminal = penalties.get('criminal', '')
            
            # Extract years from penalty string
            if 'years' in criminal:
                try:
                    years_str = criminal.split('years')[0].split()[-1]
                    years = int(years_str)
                    state_criminal_max = max(state_criminal_max, years)
                except (ValueError, IndexError):
                    pass
        
        # Federal typically has longer sentences for securities fraud (up to 25 years)
        # But some states like Texas have extremely harsh penalties (up to 99 years)
        
        if state_criminal_max > 25:
            comparison['state_advantages'].append(
                f"State criminal penalties up to {state_criminal_max} years exceed federal"
            )
            comparison['recommended_primary_forum'] = 'STATE'
        else:
            comparison['federal_advantages'].append(
                "Federal criminal penalties (up to 25 years) exceed most state penalties"
            )
        
        # New York Martin Act advantage: No scienter requirement
        ny_violations = [sv for sv in state_violations if sv.get('state') == 'NY']
        if ny_violations:
            comparison['state_advantages'].append(
                "NY Martin Act: No scienter requirement (strict liability)"
            )
        
        # Federal advantages
        comparison['federal_advantages'].extend([
            "National reach and uniformity",
            "SEC civil enforcement + DOJ criminal prosecution",
            "Federal sentencing guidelines consistency",
            "Interstate commerce jurisdiction"
        ])
        
        return comparison
