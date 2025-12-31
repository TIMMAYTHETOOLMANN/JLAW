"""
International Compliance Analyzer
=================================

Cross-border securities law analysis for international jurisdictions.

Implements international securities regulatory frameworks:
- United Kingdom (FCA): FSMA 2000, MAR, Criminal Justice Act 1993
- European Union (ESMA): MiFID II, MAR, Prospectus Regulation
- Canada (IIROC/CSA): NI 31-103, Ontario Securities Act
- Australia (ASIC): Corporations Act 2001
- Switzerland (FINMA): FMIA, FinSA

Features:
- Cross-border violation detection
- MLAT (Mutual Legal Assistance Treaty) analysis
- Extraterritorial reach determination
- International cooperation frameworks
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class InternationalRegulation:
    """
    Represents an international securities regulation.
    
    Attributes:
        jurisdiction: Country/region name
        regulator: Regulatory agency
        regulation_name: Name of regulation
        regulation_citation: Legal citation
        violation_type: Type of violation covered
        penalties: Penalties by type
        mutual_legal_assistance: Whether MLAT treaty exists with U.S.
    """
    jurisdiction: str
    regulator: str
    regulation_name: str
    regulation_citation: str
    violation_type: str
    penalties: Dict[str, str]
    mutual_legal_assistance: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'jurisdiction': self.jurisdiction,
            'regulator': self.regulator,
            'regulation_name': self.regulation_name,
            'regulation_citation': self.regulation_citation,
            'violation_type': self.violation_type,
            'penalties': self.penalties,
            'mutual_legal_assistance': self.mutual_legal_assistance
        }


class InternationalComplianceAnalyzer:
    """
    International securities law compliance analyzer.
    
    Analyzes violations under international regulatory frameworks and
    generates MLAT requests for cross-border evidence.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.regulations: Dict[str, List[InternationalRegulation]] = {}
        self._regulations_loaded = False
    
    def _load_international_regulations(self):
        """Load international regulations database."""
        if self._regulations_loaded:
            return
        
        # Try to load from JSON file
        data_dir = Path(__file__).parent / "data"
        json_path = data_dir / "international_regulations.json"
        
        if json_path.exists():
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    self._parse_json_data(data)
                    self.logger.info(f"✓ Loaded international regulations from {json_path}")
                    self._regulations_loaded = True
                    return
            except Exception as e:
                self.logger.warning(f"Failed to load JSON database: {e}, using built-in")
        
        # Fallback: Use built-in database
        self._load_builtin_regulations()
        self._regulations_loaded = True
    
    def _parse_json_data(self, data: Dict[str, Any]):
        """Parse JSON data into InternationalRegulation objects."""
        for jurisdiction, jurisdiction_data in data.items():
            regulations = []
            for reg_data in jurisdiction_data.get('regulations', []):
                regulation = InternationalRegulation(
                    jurisdiction=jurisdiction,
                    regulator=jurisdiction_data['regulator'],
                    regulation_name=reg_data['name'],
                    regulation_citation=reg_data['citation'],
                    violation_type=reg_data['violation_type'],
                    penalties=reg_data['penalties'],
                    mutual_legal_assistance=reg_data.get('mlat_treaty', False)
                )
                regulations.append(regulation)
            
            self.regulations[jurisdiction] = regulations
    
    def _load_builtin_regulations(self):
        """Load built-in international regulations database."""
        # United Kingdom (FCA)
        self.regulations['United Kingdom'] = [
            InternationalRegulation(
                jurisdiction='United Kingdom',
                regulator='Financial Conduct Authority (FCA)',
                regulation_name='Misleading statements and practices',
                regulation_citation='FSMA 2000 s.397',
                violation_type='MARKET_MANIPULATION',
                penalties={
                    'criminal': 'Up to 7 years imprisonment + unlimited fine',
                    'civil': 'Unlimited fines + disgorgement'
                },
                mutual_legal_assistance=True
            ),
            InternationalRegulation(
                jurisdiction='United Kingdom',
                regulator='Financial Conduct Authority (FCA)',
                regulation_name='Insider Dealing',
                regulation_citation='Criminal Justice Act 1993 Part V',
                violation_type='INSIDER_TRADING',
                penalties={
                    'criminal': 'Up to 7 years imprisonment + unlimited fine'
                },
                mutual_legal_assistance=True
            ),
            InternationalRegulation(
                jurisdiction='United Kingdom',
                regulator='Financial Conduct Authority (FCA)',
                regulation_name='Market Abuse Regulation',
                regulation_citation='MAR',
                violation_type='MARKET_ABUSE',
                penalties={
                    'criminal': 'Up to 7 years imprisonment',
                    'civil': 'Unlimited fines',
                    'administrative': 'Public censure + disgorgement'
                },
                mutual_legal_assistance=True
            )
        ]
        
        # European Union (ESMA)
        self.regulations['European Union'] = [
            InternationalRegulation(
                jurisdiction='European Union',
                regulator='European Securities and Markets Authority (ESMA)',
                regulation_name='Market Manipulation',
                regulation_citation='MAR Article 15',
                violation_type='MARKET_MANIPULATION',
                penalties={
                    'criminal': 'Varies by member state',
                    'civil': 'Up to €5M or 10% of annual turnover',
                    'administrative': '€5M or 15% of annual turnover'
                },
                mutual_legal_assistance=True
            ),
            InternationalRegulation(
                jurisdiction='European Union',
                regulator='European Securities and Markets Authority (ESMA)',
                regulation_name='Markets in Financial Instruments Directive',
                regulation_citation='MiFID II',
                violation_type='CONDUCT_VIOLATIONS',
                penalties={
                    'administrative': 'Up to €5M or 10% of annual turnover'
                },
                mutual_legal_assistance=True
            ),
            InternationalRegulation(
                jurisdiction='European Union',
                regulator='European Securities and Markets Authority (ESMA)',
                regulation_name='Prospectus Regulation',
                regulation_citation='EU 2017/1129',
                violation_type='DISCLOSURE_VIOLATIONS',
                penalties={
                    'administrative': 'Up to €5M or 3% of annual turnover'
                },
                mutual_legal_assistance=True
            )
        ]
        
        # Canada (IIROC/CSA)
        self.regulations['Canada'] = [
            InternationalRegulation(
                jurisdiction='Canada',
                regulator='Investment Industry Regulatory Organization of Canada (IIROC)',
                regulation_name='Registration and Compliance',
                regulation_citation='National Instrument 31-103',
                violation_type='REGISTRATION_VIOLATIONS',
                penalties={
                    'administrative': 'Fines up to $5M CAD per violation',
                    'civil': 'Disgorgement + damages'
                },
                mutual_legal_assistance=True
            ),
            InternationalRegulation(
                jurisdiction='Canada',
                regulator='Ontario Securities Commission',
                regulation_name='Securities Fraud',
                regulation_citation='Ontario Securities Act',
                violation_type='FRAUD',
                penalties={
                    'criminal': 'Up to 5 years imprisonment',
                    'civil': 'Disgorgement + damages'
                },
                mutual_legal_assistance=True
            ),
            InternationalRegulation(
                jurisdiction='Canada',
                regulator='Canadian Criminal Justice System',
                regulation_name='Fraud',
                regulation_citation='Criminal Code §380',
                violation_type='FRAUD',
                penalties={
                    'criminal': 'Up to 14 years imprisonment'
                },
                mutual_legal_assistance=True
            )
        ]
        
        # Australia (ASIC)
        self.regulations['Australia'] = [
            InternationalRegulation(
                jurisdiction='Australia',
                regulator='Australian Securities and Investments Commission (ASIC)',
                regulation_name='Market Misconduct',
                regulation_citation='Corporations Act 2001',
                violation_type='MARKET_MANIPULATION',
                penalties={
                    'criminal': 'Up to 10 years imprisonment + fines',
                    'civil': 'Pecuniary penalties + disgorgement'
                },
                mutual_legal_assistance=True
            ),
            InternationalRegulation(
                jurisdiction='Australia',
                regulator='Australian Securities and Investments Commission (ASIC)',
                regulation_name='ASIC Act Violations',
                regulation_citation='ASIC Act 2001',
                violation_type='CONDUCT_VIOLATIONS',
                penalties={
                    'civil': 'Pecuniary penalties up to $1M AUD',
                    'administrative': 'Banning orders + enforceable undertakings'
                },
                mutual_legal_assistance=True
            )
        ]
        
        # Switzerland (FINMA)
        self.regulations['Switzerland'] = [
            InternationalRegulation(
                jurisdiction='Switzerland',
                regulator='Swiss Financial Market Supervisory Authority (FINMA)',
                regulation_name='Market Manipulation',
                regulation_citation='Financial Market Infrastructure Act (FMIA)',
                violation_type='MARKET_MANIPULATION',
                penalties={
                    'criminal': 'Up to 3 years imprisonment + fines',
                    'administrative': 'Disgorgement + fines'
                },
                mutual_legal_assistance=True
            ),
            InternationalRegulation(
                jurisdiction='Switzerland',
                regulator='Swiss Financial Market Supervisory Authority (FINMA)',
                regulation_name='Financial Services Violations',
                regulation_citation='Financial Services Act (FinSA)',
                violation_type='CONDUCT_VIOLATIONS',
                penalties={
                    'administrative': 'Fines up to CHF 10M'
                },
                mutual_legal_assistance=True
            )
        ]
        
        self.logger.info(f"✓ Loaded regulations for {len(self.regulations)} jurisdictions")
    
    async def analyze_cross_border_violations(
        self,
        company_profile: Dict[str, Any],
        violations: List[Dict[str, Any]],
        investor_locations: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze violations under international regulatory frameworks.
        
        Args:
            company_profile: Company information
            violations: Detected violations
            investor_locations: List of investor location countries
        
        Returns:
            List of international violation analyses
        """
        # Ensure regulations are loaded
        self._load_international_regulations()
        
        international_violations = []
        
        # Determine relevant jurisdictions
        relevant_jurisdictions = self._identify_relevant_jurisdictions(
            company_profile, investor_locations
        )
        
        self.logger.info(f"Analyzing violations for {len(relevant_jurisdictions)} international jurisdictions")
        
        for jurisdiction in relevant_jurisdictions:
            jurisdiction_regs = self.regulations.get(jurisdiction, [])
            
            if not jurisdiction_regs:
                self.logger.warning(f"No regulations found for: {jurisdiction}")
                continue
            
            # Analyze each violation against jurisdiction's regulations
            for violation in violations:
                for regulation in jurisdiction_regs:
                    if self._violation_matches_regulation(violation, regulation):
                        intl_violation = {
                            'violation_id': violation.get('id', 'unknown'),
                            'jurisdiction': jurisdiction,
                            'regulator': regulation.regulator,
                            'regulation_citation': regulation.regulation_citation,
                            'regulation_name': regulation.regulation_name,
                            'violation_description': violation.get('description', ''),
                            'violation_type': regulation.violation_type,
                            'penalties': regulation.penalties,
                            'mlat_available': regulation.mutual_legal_assistance,
                            'extraterritorial_basis': self._determine_extraterritorial_basis(
                                jurisdiction, company_profile, violation
                            )
                        }
                        international_violations.append(intl_violation)
        
        self.logger.info(f"✓ Identified {len(international_violations)} international violations")
        return international_violations
    
    def _identify_relevant_jurisdictions(
        self,
        company_profile: Dict[str, Any],
        investor_locations: Optional[List[str]] = None
    ) -> List[str]:
        """Identify relevant international jurisdictions."""
        jurisdictions = set()
        
        # Check for international listings
        if company_profile.get('has_uk_listing'):
            jurisdictions.add('United Kingdom')
        if company_profile.get('has_eu_listing'):
            jurisdictions.add('European Union')
        if company_profile.get('has_canadian_listing'):
            jurisdictions.add('Canada')
        if company_profile.get('has_australian_listing'):
            jurisdictions.add('Australia')
        
        # Check investor locations
        if investor_locations:
            for location in investor_locations:
                if location in ['UK', 'United Kingdom']:
                    jurisdictions.add('United Kingdom')
                elif location in ['Canada']:
                    jurisdictions.add('Canada')
                elif location in ['Australia']:
                    jurisdictions.add('Australia')
                elif location in ['Switzerland']:
                    jurisdictions.add('Switzerland')
                # EU member states
                elif location in ['France', 'Germany', 'Italy', 'Spain', 'Netherlands']:
                    jurisdictions.add('European Union')
        
        return list(jurisdictions)
    
    def _violation_matches_regulation(
        self,
        violation: Dict[str, Any],
        regulation: InternationalRegulation
    ) -> bool:
        """Check if violation matches regulation type."""
        violation_type = violation.get('type', '').upper()
        regulation_type = regulation.violation_type.upper()
        
        # Direct match
        if regulation_type in violation_type:
            return True
        
        # Keyword matching
        if regulation_type == 'MARKET_MANIPULATION':
            return any(kw in violation_type for kw in ['MANIPULATION', 'FRAUD', 'SCHEME'])
        elif regulation_type == 'INSIDER_TRADING':
            return 'INSIDER' in violation_type
        elif regulation_type == 'FRAUD':
            return any(kw in violation_type for kw in ['FRAUD', 'MISREPRESENTATION'])
        elif regulation_type == 'MARKET_ABUSE':
            return any(kw in violation_type for kw in ['ABUSE', 'MANIPULATION', 'INSIDER'])
        
        return False
    
    def _determine_extraterritorial_basis(
        self,
        jurisdiction: str,
        company_profile: Dict[str, Any],
        violation: Dict[str, Any]
    ) -> List[str]:
        """Determine basis for extraterritorial jurisdiction."""
        basis = []
        
        # Listing basis
        if jurisdiction == 'United Kingdom' and company_profile.get('has_uk_listing'):
            basis.append('UK securities listing')
        elif jurisdiction == 'European Union' and company_profile.get('has_eu_listing'):
            basis.append('EU securities listing')
        elif jurisdiction == 'Canada' and company_profile.get('has_canadian_listing'):
            basis.append('Canadian securities listing')
        elif jurisdiction == 'Australia' and company_profile.get('has_australian_listing'):
            basis.append('Australian securities listing')
        
        # Effects doctrine: Conduct outside jurisdiction that has effects within it
        basis.append('Effects doctrine: U.S. conduct affecting local investors')
        
        # Protective principle: Protection of nationals/residents
        basis.append('Protective principle: Protection of local investors')
        
        return basis
    
    def generate_mlat_request_template(
        self,
        jurisdiction: str,
        violation: Dict[str, Any],
        evidence_needed: List[str]
    ) -> Dict[str, Any]:
        """
        Generate Mutual Legal Assistance Treaty (MLAT) request template.
        
        Args:
            jurisdiction: Target jurisdiction for MLAT request
            violation: Violation requiring international evidence
            evidence_needed: List of evidence items to request
        
        Returns:
            MLAT request template dictionary
        """
        # Get regulation info for jurisdiction
        regulations = self.regulations.get(jurisdiction, [])
        if not regulations:
            self.logger.warning(f"No MLAT treaty info available for {jurisdiction}")
            return {}
        
        # Check if MLAT available
        has_mlat = any(reg.mutual_legal_assistance for reg in regulations)
        if not has_mlat:
            self.logger.warning(f"No MLAT treaty with {jurisdiction}")
            return {}
        
        mlat_request = {
            'request_type': 'MLAT',
            'requesting_country': 'United States',
            'requested_country': jurisdiction,
            'treaty_basis': f'U.S.-{jurisdiction} Mutual Legal Assistance Treaty',
            'case_description': violation.get('description', ''),
            'violation_type': violation.get('type', ''),
            'evidence_requested': evidence_needed,
            'urgency': 'HIGH' if violation.get('severity') == 'CRITICAL' else 'MEDIUM',
            'contact_agency': self._get_mlat_contact(jurisdiction),
            'template_sections': {
                'introduction': f"Request for mutual legal assistance pursuant to the U.S.-{jurisdiction} MLAT",
                'case_summary': f"Investigation of securities fraud violations: {violation.get('type', '')}",
                'evidence_description': f"Evidence requested: {', '.join(evidence_needed)}",
                'legal_basis': f"U.S. securities laws: 15 U.S.C. §78j(b), 18 U.S.C. §1348",
                'dual_criminality': "The conduct under investigation constitutes a criminal offense in both jurisdictions",
                'confidentiality': "Evidence will be used solely for criminal prosecution purposes"
            }
        }
        
        return mlat_request
    
    def _get_mlat_contact(self, jurisdiction: str) -> Dict[str, str]:
        """Get MLAT central authority contact information."""
        mlat_contacts = {
            'United Kingdom': {
                'agency': 'UK Central Authority',
                'department': 'Home Office',
                'address': '2 Marsham Street, London SW1P 4DF',
                'email': 'mlat@homeoffice.gov.uk'
            },
            'Canada': {
                'agency': 'International Assistance Group',
                'department': 'Department of Justice Canada',
                'address': '284 Wellington Street, Ottawa, ON K1A 0H8',
                'email': 'MLATCanada@justice.gc.ca'
            },
            'Australia': {
                'agency': 'International Crime Cooperation Central Authority',
                'department': 'Attorney-General\'s Department',
                'address': '3-5 National Circuit, Barton ACT 2600',
                'email': 'ICCCA@ag.gov.au'
            },
            'European Union': {
                'agency': 'Eurojust',
                'address': 'Maanweg 174, 2516 AB The Hague, Netherlands',
                'email': 'info@eurojust.europa.eu'
            },
            'Switzerland': {
                'agency': 'Federal Office of Justice',
                'department': 'International Legal Assistance Division',
                'address': 'Bundesrain 20, 3003 Bern',
                'email': 'irh@bj.admin.ch'
            }
        }
        
        return mlat_contacts.get(jurisdiction, {
            'agency': f'{jurisdiction} Central Authority',
            'note': 'Contact information to be determined'
        })
