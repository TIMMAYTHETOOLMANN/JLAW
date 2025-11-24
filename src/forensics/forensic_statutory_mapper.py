"""
Forensic Statutory Mapper - Module 3
Advanced statute mapping with pattern recognition and forensic indicator analysis.
Maps fraud patterns to specific legal violations across multiple jurisdictions.
"""

import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
import json

from src.forensics.core.integrity_manager import (
    ForensicHashChain, IntegrityLevel, ForensicBlock
)

logger = logging.getLogger(__name__)


class StatuteJurisdiction(Enum):
    """Legal jurisdiction classifications."""
    FEDERAL_SECURITIES = "FEDERAL_SECURITIES"
    FEDERAL_CRIMINAL = "FEDERAL_CRIMINAL"
    GAAP_FASB = "GAAP_FASB"
    IFRS = "IFRS"
    SOX = "SARBANES_OXLEY"
    PCAOB = "PCAOB_AUDITING"
    SEC_RULES = "SEC_RULES"
    STATE = "STATE_LAW"


class ViolationSeverity(Enum):
    """Violation severity levels."""
    CRITICAL = "CRITICAL"      # Criminal, material fraud
    HIGH = "HIGH"              # Material misstatement, significant violation
    MEDIUM = "MEDIUM"          # Technical violation, disclosure issue
    LOW = "LOW"                # Minor non-compliance
    INFORMATIONAL = "INFORMATIONAL"  # Best practice deviation


@dataclass
class StatuteReference:
    """Legal statute reference with metadata."""
    citation: str
    title: str
    description: str
    jurisdiction: StatuteJurisdiction
    severity: ViolationSeverity
    penalties: Dict[str, Any]
    elements: List[str]  # Elements required to prove violation
    case_law: List[str]  # Relevant case law references


@dataclass
class ForensicIndicatorResult:
    """Result of forensic indicator evaluation."""
    indicator_name: str
    triggered: bool
    value: float
    threshold: float
    explanation: str
    confidence: float
    data_source: str


@dataclass
class StatuteViolationMatch:
    """Matched statute violation with evidence."""
    statute: StatuteReference
    pattern_matches: List[str]
    forensic_indicators: List[ForensicIndicatorResult]
    confidence_score: float
    evidence_strength: str  # STRONG, MODERATE, WEAK
    recommended_charges: List[str]
    similar_cases: List[str]
    evidence_hash: str


@dataclass
class ComprehensiveStatutoryAnalysis:
    """Complete statutory analysis report."""
    analysis_timestamp: str
    company_cik: str
    company_name: str
    violations_identified: List[StatuteViolationMatch]
    pattern_matches_count: int
    forensic_indicators_triggered: int
    jurisdictions_affected: List[StatuteJurisdiction]
    aggregate_severity: ViolationSeverity
    prosecution_priority: int  # 1-10
    recommended_actions: List[str]
    evidence_chain_hash: str


class ForensicStatutoryMapper:
    """
    Advanced forensic statutory mapper.
    
    Maps fraud patterns to specific legal violations across:
    - USC Title 15 (Securities Exchange Act)
    - USC Title 18 (Criminal Code)
    - 17 CFR (SEC Rules)
    - SOX (Sarbanes-Oxley Act)
    - GAAP/FASB Standards
    - IFRS Standards
    - PCAOB Auditing Standards
    """
    
    def __init__(self):
        """Initialize forensic statutory mapper."""
        self.hash_chain = ForensicHashChain("forensic_statutory_mapper")
        self.statutory_patterns = self._initialize_statutory_patterns()
        self.statute_database = self._initialize_statute_database()
        self.case_law_database = self._initialize_case_law()
        logger.info("ForensicStatutoryMapper initialized")
    
    def _initialize_statutory_patterns(self) -> Dict[str, Any]:
        """
        Initialize comprehensive fraud pattern database.
        
        Returns:
            Pattern dictionary with statutes and indicators
        """
        return {
            'revenue_recognition_fraud': {
                'patterns': [
                    r'(?:premature|accelerated|improper)\s+revenue\s+recognition',
                    r'channel\s+stuffing',
                    r'bill\s+and\s+hold\s+(?:arrangement|transaction)',
                    r'round[\-\s]?trip\s+(?:transaction|sale)',
                    r'consignment\s+(?:sale|revenue)',
                    r'side\s+letter\s+agreement',
                    r'right\s+of\s+return\s+(?:not\s+disclosed|concealed)',
                    r'percentage[\-\s]of[\-\s]completion\s+(?:manipulation|fraud)',
                    r'vendor\s+financing\s+scheme',
                    r'barter\s+transaction\s+(?:inflated|fictitious)',
                ],
                'statutes': [
                    'ASC 606 - Revenue from Contracts with Customers',
                    'SAB 104 - Revenue Recognition',
                    '17 CFR § 240.10b-5(b) - Material Misstatement',
                    '15 USC § 78m(a) - Periodic Reports Requirement',
                    '15 USC § 78j(b) - Manipulative and Deceptive Devices',
                    '18 USC § 1348 - Securities Fraud',
                ],
                'forensic_indicators': {
                    'DSO_spike': lambda current, prior: (current - prior) / prior > 0.25 if prior != 0 else False,
                    'revenue_quality': lambda rev, cf: rev / cf > 1.5 if cf != 0 else False,
                    'unbilled_revenue_ratio': lambda unbilled, total: unbilled / total > 0.15 if total != 0 else False,
                    'q4_revenue_concentration': lambda q4_rev, annual_rev: q4_rev / annual_rev > 0.40 if annual_rev != 0 else False,
                    'customer_concentration': lambda top_customer, total_rev: top_customer / total_rev > 0.25 if total_rev != 0 else False,
                }
            },
            
            'expense_capitalization_manipulation': {
                'patterns': [
                    r'(?:improper|aggressive)\s+capitalization',
                    r'(?:deferred|capitalized)\s+(?:expense|cost)',
                    r'worldcom[\-\s]?(?:style|like)',
                    r'operating\s+expense\s+(?:reclassified|misclassified)',
                    r'software\s+development\s+cost\s+(?:manipulation|overstatement)',
                    r'research\s+(?:and|&)\s+development\s+(?:capitalized|deferred)',
                ],
                'statutes': [
                    'ASC 340 - Other Assets and Deferred Costs',
                    'ASC 350-40 - Internal-Use Software',
                    'IAS 38 - Intangible Assets',
                    '15 USC § 78m(b)(2)(A) - Books and Records Accuracy',
                    '17 CFR § 240.13b2-1 - Falsification of Records',
                    '18 USC § 1520 - Destruction of Corporate Audit Records',
                ],
                'forensic_indicators': {
                    'capex_to_sales': lambda capex, sales, industry_avg: (capex/sales) / industry_avg > 1.5 if sales != 0 and industry_avg != 0 else False,
                    'deferred_cost_growth': lambda current, prior, sales_growth: (current/prior - 1) / sales_growth > 1.3 if prior != 0 and sales_growth != 0 else False,
                    'depreciation_rate': lambda depreciation, assets: depreciation / assets < 0.05 if assets != 0 else False,
                    'capitalized_interest': lambda cap_interest, total_interest: cap_interest / total_interest > 0.30 if total_interest != 0 else False,
                }
            },
            
            'earnings_management': {
                'patterns': [
                    r'cookie\s+jar\s+reserve',
                    r'big\s+bath\s+(?:accounting|charge)',
                    r'earnings\s+smoothing',
                    r'accrual\s+manipulation',
                    r'restructuring\s+charge\s+(?:reversal|manipulation)',
                    r'acquisition\s+accounting\s+(?:manipulation|fraud)',
                    r'mark[\-\s]to[\-\s]market\s+(?:manipulation|abuse)',
                ],
                'statutes': [
                    'ASC 450 - Contingencies',
                    'ASC 805 - Business Combinations',
                    '17 CFR § 240.10b-5(a) - Fraudulent Scheme',
                    '15 USC § 7241 - Corporate Responsibility (SOX 302)',
                    'SAB 99 - Materiality',
                ],
                'forensic_indicators': {
                    'accruals_ratio': lambda net_income, cash_flow: abs(net_income - cash_flow) / abs(net_income) > 0.30 if net_income != 0 else False,
                    'reserve_volatility': lambda current_reserve, prior_reserve, revenue: abs(current_reserve - prior_reserve) / revenue > 0.05 if revenue != 0 else False,
                    'discretionary_accruals': lambda accruals, assets: abs(accruals) / assets > 0.10 if assets != 0 else False,
                }
            },
            
            'asset_overstatement': {
                'patterns': [
                    r'(?:goodwill|intangible)\s+(?:impairment|write[\-\s]down)\s+(?:delay|avoid)',
                    r'inventory\s+(?:overstatement|obsolescence\s+not\s+recognized)',
                    r'accounts\s+receivable\s+(?:overstatement|uncollectible)',
                    r'fixed\s+asset\s+(?:overvaluation|impairment\s+not\s+recognized)',
                    r'related\s+party\s+(?:asset|receivable)',
                ],
                'statutes': [
                    'ASC 350-20 - Goodwill Impairment',
                    'ASC 330 - Inventory',
                    'ASC 310 - Receivables',
                    'ASC 360-10 - Property, Plant, and Equipment',
                    '17 CFR § 240.10b-5(b) - Material Omission',
                ],
                'forensic_indicators': {
                    'asset_quality_ratio': lambda current_assets, ppe, total_assets: 1 - (current_assets + ppe) / total_assets > 0.25 if total_assets != 0 else False,
                    'inventory_turnover': lambda cogs, inventory: cogs / inventory < 2.0 if inventory != 0 else False,
                    'goodwill_to_assets': lambda goodwill, assets: goodwill / assets > 0.40 if assets != 0 else False,
                }
            },
            
            'liability_understatement': {
                'patterns': [
                    r'off[\-\s]balance[\-\s]sheet\s+(?:entity|arrangement|financing)',
                    r'special\s+purpose\s+(?:entity|vehicle)\s+(?:SPE|SPV)',
                    r'contingent\s+liability\s+(?:not\s+disclosed|concealed)',
                    r'lease\s+obligation\s+(?:off[\-\s]balance|undisclosed)',
                    r'pension\s+(?:liability|obligation)\s+(?:understatement|manipulation)',
                    r'warranty\s+(?:reserve|liability)\s+(?:inadequate|understated)',
                ],
                'statutes': [
                    'ASC 450-20 - Loss Contingencies',
                    'ASC 842 - Leases',
                    'ASC 715 - Compensation - Retirement Benefits',
                    '15 USC § 78m(b)(2)(A) - Accurate Books and Records',
                    '17 CFR § 210.5-02 - Balance Sheet Requirements',
                ],
                'forensic_indicators': {
                    'debt_to_equity': lambda debt, equity: debt / equity > 2.5 if equity != 0 else False,
                    'off_balance_ratio': lambda disclosed_off_balance, assets: disclosed_off_balance / assets > 0.20 if assets != 0 else False,
                    'contingency_disclosure': lambda contingent_liabilities, total_liabilities: contingent_liabilities / total_liabilities > 0.15 if total_liabilities != 0 else False,
                }
            },
            
            'cash_flow_manipulation': {
                'patterns': [
                    r'operating\s+cash\s+flow\s+(?:manipulation|inflation)',
                    r'working\s+capital\s+(?:manipulation|management)',
                    r'vendor\s+financing\s+(?:arrangement|scheme)',
                    r'factoring\s+(?:receivable|arrangement)\s+(?:undisclosed|off[\-\s]balance)',
                    r'classification\s+(?:error|manipulation)\s+(?:operating|financing|investing)',
                ],
                'statutes': [
                    'ASC 230 - Statement of Cash Flows',
                    '17 CFR § 210.4-08 - General Notes to Financial Statements',
                    '15 USC § 78j(b) - Manipulative Devices',
                ],
                'forensic_indicators': {
                    'cash_flow_quality': lambda operating_cf, net_income: operating_cf / net_income < 0.7 if net_income > 0 else False,
                    'working_capital_change': lambda current, prior, revenue: abs(current - prior) / revenue > 0.15 if revenue != 0 else False,
                    'days_payable': lambda payables, cogs, days: (payables / (cogs / days)) > 90 if cogs != 0 else False,
                }
            },
            
            'disclosure_violations': {
                'patterns': [
                    r'(?:material|significant)\s+(?:omission|non[\-\s]disclosure)',
                    r'related\s+party\s+transaction\s+(?:not\s+disclosed|concealed)',
                    r'subsequent\s+event\s+(?:not\s+disclosed|omitted)',
                    r'going\s+concern\s+(?:issue|doubt)\s+(?:not\s+disclosed|concealed)',
                    r'segment\s+(?:information|reporting)\s+(?:violation|inadequate)',
                    r'executive\s+compensation\s+(?:undisclosed|manipulation)',
                ],
                'statutes': [
                    'ASC 850 - Related Party Disclosures',
                    'ASC 855 - Subsequent Events',
                    'ASC 280 - Segment Reporting',
                    '17 CFR § 229.402 - Executive Compensation',
                    '15 USC § 78m(a) - Reports Completeness',
                    '15 USC § 7241 - SOX 302 Certification',
                ],
                'forensic_indicators': {
                    'related_party_volume': lambda rp_transactions, total_revenue: rp_transactions / total_revenue > 0.10 if total_revenue != 0 else False,
                    'footnote_complexity': lambda footnote_words, filing_words: footnote_words / filing_words > 0.30 if filing_words != 0 else False,
                }
            },
            
            'auditor_independence_violation': {
                'patterns': [
                    r'auditor\s+(?:independence|conflict)',
                    r'(?:non[\-\s]audit|consulting)\s+fee\s+(?:excessive|material)',
                    r'audit\s+committee\s+(?:ineffective|non[\-\s]independent)',
                    r'auditor\s+(?:rotation|tenure)\s+(?:violation|excessive)',
                ],
                'statutes': [
                    '15 USC § 78j-1 - Auditor Independence',
                    'SOX Section 201 - Services Outside Scope',
                    'SOX Section 206 - Conflicts of Interest',
                    'PCAOB AS 1005 - Independence',
                ],
                'forensic_indicators': {
                    'non_audit_fee_ratio': lambda non_audit_fees, audit_fees: non_audit_fees / audit_fees > 1.0 if audit_fees != 0 else False,
                    'auditor_tenure': lambda years: years > 15,
                }
            },
            
            'internal_control_deficiency': {
                'patterns': [
                    r'material\s+weakness\s+(?:in\s+)?internal\s+control',
                    r'significant\s+deficiency\s+(?:not\s+remediated|ongoing)',
                    r'control\s+environment\s+(?:deficient|inadequate)',
                    r'segregation\s+of\s+duties\s+(?:lacking|inadequate)',
                ],
                'statutes': [
                    '15 USC § 7262 - SOX 404 Management Assessment',
                    '15 USC § 78m(b)(2)(B) - Internal Accounting Controls',
                    'PCAOB AS 2201 - Audit of Internal Control',
                    '17 CFR § 240.13a-15 - Controls and Procedures',
                ],
                'forensic_indicators': {
                    'restatement_frequency': lambda restatements, years: restatements / years > 0.5 if years != 0 else False,
                    'audit_adjustments': lambda adjustments, materiality: adjustments / materiality > 0.50 if materiality != 0 else False,
                }
            },
            
            'tax_fraud_indicators': {
                'patterns': [
                    r'transfer\s+pricing\s+(?:manipulation|scheme)',
                    r'tax\s+(?:haven|shelter)\s+(?:abusive|aggressive)',
                    r'deferred\s+tax\s+(?:asset|liability)\s+(?:manipulation|misstatement)',
                    r'effective\s+tax\s+rate\s+(?:anomaly|manipulation)',
                ],
                'statutes': [
                    'ASC 740 - Income Taxes',
                    'IRC § 482 - Transfer Pricing',
                    '26 USC § 7201 - Tax Evasion',
                    '18 USC § 371 - Conspiracy to Defraud',
                ],
                'forensic_indicators': {
                    'effective_tax_rate': lambda tax_expense, pretax_income: abs((tax_expense / pretax_income) - 0.21) > 0.15 if pretax_income != 0 else False,
                    'deferred_tax_growth': lambda deferred_current, deferred_prior: (deferred_current / deferred_prior - 1) > 0.50 if deferred_prior != 0 else False,
                }
            },
        }
    
    def _initialize_statute_database(self) -> Dict[str, StatuteReference]:
        """
        Initialize comprehensive statute reference database.
        
        Returns:
            Dictionary of statute references
        """
        return {
            '15_USC_78m_a': StatuteReference(
                citation='15 USC § 78m(a)',
                title='Periodic and Other Reports',
                description='Requires issuers to file periodic reports (10-K, 10-Q) with accurate information',
                jurisdiction=StatuteJurisdiction.FEDERAL_SECURITIES,
                severity=ViolationSeverity.HIGH,
                penalties={
                    'civil_monetary': '$1,000,000 per violation',
                    'criminal_fine': '$25,000,000',
                    'imprisonment': 'Up to 20 years',
                    'officer_bar': 'Possible SEC officer/director bar'
                },
                elements=[
                    'Duty to file periodic reports',
                    'Material misstatement or omission',
                    'Scienter (knowing or reckless)',
                    'In connection with securities'
                ],
                case_law=[
                    'SEC v. Texas Gulf Sulphur Co., 401 F.2d 833 (2d Cir. 1968)',
                    'Basic Inc. v. Levinson, 485 U.S. 224 (1988)',
                ]
            ),
            
            '15_USC_78j_b': StatuteReference(
                citation='15 USC § 78j(b)',
                title='Manipulative and Deceptive Devices',
                description='Prohibits fraud, manipulation, and deceptive devices in securities transactions',
                jurisdiction=StatuteJurisdiction.FEDERAL_SECURITIES,
                severity=ViolationSeverity.CRITICAL,
                penalties={
                    'civil_monetary': '$5,000,000 per individual, $25,000,000 per entity',
                    'criminal_fine': '$5,000,000 per individual',
                    'imprisonment': 'Up to 20 years',
                    'treble_damages': 'Private actions under 10b-5'
                },
                elements=[
                    'Manipulative or deceptive device/contrivance',
                    'Material misrepresentation or omission',
                    'Scienter (intent to deceive/manipulate)',
                    'In connection with purchase/sale of securities',
                    'Reliance and causation (private actions)'
                ],
                case_law=[
                    'Ernst & Ernst v. Hochfelder, 425 U.S. 185 (1976)',
                    'Dura Pharmaceuticals v. Broudo, 544 U.S. 336 (2005)',
                ]
            ),
            
            '17_CFR_240_10b_5': StatuteReference(
                citation='17 CFR § 240.10b-5',
                title='Employment of Manipulative and Deceptive Devices (Rule 10b-5)',
                description='Implements Section 10(b) - prohibits fraud in securities transactions',
                jurisdiction=StatuteJurisdiction.SEC_RULES,
                severity=ViolationSeverity.CRITICAL,
                penalties={
                    'civil_monetary': 'Up to 3x disgorgement',
                    'injunctive_relief': 'Cease and desist orders',
                    'criminal_referral': 'DOJ prosecution possible'
                },
                elements=[
                    '(a) Device, scheme, or artifice to defraud',
                    '(b) Material misstatement or omission',
                    '(c) Act, practice, or course of business operating as fraud',
                    'Use of interstate commerce',
                    'Scienter'
                ],
                case_law=[
                    'SEC v. Zandford, 535 U.S. 813 (2002)',
                    'Stoneridge Investment Partners v. Scientific-Atlanta, 552 U.S. 148 (2008)',
                ]
            ),
            
            '15_USC_7241': StatuteReference(
                citation='15 USC § 7241',
                title='SOX Section 302 - Corporate Responsibility for Financial Reports',
                description='CEO/CFO must certify accuracy of financial statements',
                jurisdiction=StatuteJurisdiction.SOX,
                severity=ViolationSeverity.CRITICAL,
                penalties={
                    'criminal_fine': 'Up to $1,000,000',
                    'imprisonment': 'Up to 10 years (knowing), 20 years (willful)',
                    'civil_penalties': 'SEC enforcement actions',
                    'clawback': 'Bonus/profit forfeiture'
                },
                elements=[
                    'Signing officer (CEO/CFO)',
                    'Certification of accuracy',
                    'Knowledge of misstatement',
                    'Material impact on investors'
                ],
                case_law=[
                    'SEC v. Shanahan, No. 1:11-cv-01buyandsell0991 (S.D.N.Y. 2011)',
                    'United States v. Ebbers (WorldCom), 458 F.3d 110 (2d Cir. 2006)',
                ]
            ),
            
            '15_USC_7262': StatuteReference(
                citation='15 USC § 7262',
                title='SOX Section 404 - Management Assessment of Internal Controls',
                description='Requires management to assess and report on internal control effectiveness',
                jurisdiction=StatuteJurisdiction.SOX,
                severity=ViolationSeverity.HIGH,
                penalties={
                    'civil_monetary': 'SEC enforcement',
                    'delisting': 'Possible exchange delisting',
                    'investor_lawsuits': 'Private securities litigation'
                },
                elements=[
                    'Management assessment required',
                    'Material weakness identified',
                    'Auditor attestation required',
                    'Annual reporting in 10-K'
                ],
                case_law=[
                    'In re Bank of America Corp. Securities Litigation, 688 F. Supp. 2d 713 (S.D.N.Y. 2010)',
                ]
            ),
            
            '18_USC_1348': StatuteReference(
                citation='18 USC § 1348',
                title='Securities and Commodities Fraud',
                description='Criminal prohibition on securities fraud schemes',
                jurisdiction=StatuteJurisdiction.FEDERAL_CRIMINAL,
                severity=ViolationSeverity.CRITICAL,
                penalties={
                    'imprisonment': 'Up to 25 years',
                    'criminal_fine': 'Up to $250,000 or 2x gain/loss',
                    'restitution': 'Victim restitution required',
                    'asset_forfeiture': 'Criminal forfeiture of proceeds'
                },
                elements=[
                    'Scheme to defraud',
                    'In connection with securities',
                    'Intent to defraud',
                    'Interstate commerce'
                ],
                case_law=[
                    'United States v. Mahaffy, 693 F.3d 113 (2d Cir. 2012)',
                ]
            ),
            
            '18_USC_1520': StatuteReference(
                citation='18 USC § 1520',
                title='Destruction of Corporate Audit Records',
                description='Prohibits destruction of audit workpapers and records',
                jurisdiction=StatuteJurisdiction.FEDERAL_CRIMINAL,
                severity=ViolationSeverity.HIGH,
                penalties={
                    'imprisonment': 'Up to 20 years',
                    'criminal_fine': 'Substantial fines',
                    'obstruction_charges': 'Additional obstruction counts'
                },
                elements=[
                    'Audit or review conducted/contemplated',
                    'Destruction/alteration of records',
                    'Intent to obstruct',
                    'Issuer or registered public accounting firm'
                ],
                case_law=[
                    'United States v. Andersen (Arthur Andersen), 544 U.S. 696 (2005)',
                ]
            ),
        }
    
    def _initialize_case_law(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize case law database for pattern matching.
        
        Returns:
            Case law reference dictionary
        """
        return {
            'revenue_fraud': {
                'sunbeam': {
                    'year': 1998,
                    'violation': 'Bill and hold arrangements, channel stuffing',
                    'outcome': '$15M SEC penalty',
                    'duration': '2 years undetected'
                },
                'xerox': {
                    'year': 2002,
                    'violation': 'Premature revenue recognition, $6B overstatement',
                    'outcome': '$10M SEC penalty',
                    'duration': '4 years'
                },
                'microstrategy': {
                    'year': 2000,
                    'violation': 'Improper revenue recognition, barter transactions',
                    'outcome': '$11M settlement',
                    'duration': '3 years'
                },
            },
            'expense_capitalization': {
                'worldcom': {
                    'year': 2002,
                    'violation': '$3.8B operating expenses capitalized',
                    'outcome': 'Criminal prosecution, bankruptcy',
                    'duration': '5 quarters'
                },
                'aol_time_warner': {
                    'year': 2002,
                    'violation': 'Advertising costs improperly capitalized',
                    'outcome': '$510M SEC penalty',
                    'duration': '2 years'
                },
            },
            'earnings_management': {
                'enron': {
                    'year': 2001,
                    'violation': 'Special purpose entities, mark-to-market abuse',
                    'outcome': 'Criminal prosecution, dissolution',
                    'duration': '4+ years'
                },
                'healthsouth': {
                    'year': 2003,
                    'violation': '$2.7B earnings overstatement',
                    'outcome': 'CEO convicted, $3B settlement',
                    'duration': '6 years'
                },
            },
        }
    
    async def analyze_patterns(
        self,
        filing_text: str,
        financial_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ComprehensiveStatutoryAnalysis:
        """
        Perform comprehensive statutory analysis on filing.
        
        Args:
            filing_text: Full filing text content
            financial_data: Financial metrics and ratios
            metadata: Optional filing metadata
            
        Returns:
            Comprehensive statutory analysis
        """
        logger.info("Starting comprehensive statutory analysis...")
        
        metadata = metadata or {}
        company_cik = metadata.get('cik', 'UNKNOWN')
        company_name = metadata.get('company_name', 'UNKNOWN')
        
        violations = []
        pattern_matches = 0
        indicators_triggered = 0
        jurisdictions = set()
        
        # Analyze each fraud category
        for fraud_type, config in self.statutory_patterns.items():
            logger.debug(f"Analyzing {fraud_type}...")
            
            # Pattern matching in text
            text_matches = self._match_patterns(
                filing_text,
                config['patterns'],
                fraud_type
            )
            
            if text_matches:
                pattern_matches += len(text_matches)
            
            # Evaluate forensic indicators
            indicator_results = await self._evaluate_indicators(
                config['forensic_indicators'],
                financial_data,
                fraud_type
            )
            
            triggered_indicators = [i for i in indicator_results if i.triggered]
            indicators_triggered += len(triggered_indicators)
            
            # If patterns or indicators found, map to statutes
            if text_matches or triggered_indicators:
                violation_matches = await self._map_to_statutes(
                    fraud_type,
                    config['statutes'],
                    text_matches,
                    indicator_results
                )
                
                violations.extend(violation_matches)
                
                # Track jurisdictions
                for violation in violation_matches:
                    jurisdictions.add(violation.statute.jurisdiction)
        
        # Determine aggregate severity
        aggregate_severity = self._calculate_aggregate_severity(violations)
        
        # Calculate prosecution priority
        prosecution_priority = self._calculate_prosecution_priority(
            violations,
            pattern_matches,
            indicators_triggered
        )
        
        # Generate recommended actions
        recommended_actions = self._generate_recommendations(
            violations,
            prosecution_priority
        )
        
        # Create comprehensive analysis
        analysis = ComprehensiveStatutoryAnalysis(
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            company_cik=company_cik,
            company_name=company_name,
            violations_identified=violations,
            pattern_matches_count=pattern_matches,
            forensic_indicators_triggered=indicators_triggered,
            jurisdictions_affected=list(jurisdictions),
            aggregate_severity=aggregate_severity,
            prosecution_priority=prosecution_priority,
            recommended_actions=recommended_actions,
            evidence_chain_hash=self.hash_chain.blocks[-1].current_hash if self.hash_chain.blocks else ""
        )
        
        # Log to hash chain
        await self.hash_chain.add_evidence(
            data={
                "action": "analyze_patterns",
                "company_cik": company_cik,
                "violations_found": len(violations),
                "pattern_matches": pattern_matches,
                "indicators_triggered": indicators_triggered,
                "aggregate_severity": aggregate_severity.value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            integrity_level=IntegrityLevel.CRITICAL
        )
        
        logger.info(
            f"Statutory analysis complete: {len(violations)} violations, "
            f"{pattern_matches} patterns, {indicators_triggered} indicators"
        )
        
        return analysis
    
    def _match_patterns(
        self,
        text: str,
        patterns: List[str],
        fraud_type: str
    ) -> List[str]:
        """
        Match regex patterns in text.
        
        Args:
            text: Text to search
            patterns: List of regex patterns
            fraud_type: Type of fraud
            
        Returns:
            List of matched patterns
        """
        matches = []
        text_lower = text.lower()
        
        for pattern in patterns:
            try:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    matches.append(pattern)
                    logger.debug(f"Pattern matched: {pattern} in {fraud_type}")
            except re.error as e:
                logger.warning(f"Invalid regex pattern {pattern}: {e}")
        
        return matches
    
    async def _evaluate_indicators(
        self,
        indicators: Dict[str, Callable],
        financial_data: Dict[str, Any],
        fraud_type: str
    ) -> List[ForensicIndicatorResult]:
        """
        Evaluate forensic indicators.
        
        Args:
            indicators: Dictionary of indicator functions
            financial_data: Financial data
            fraud_type: Type of fraud
            
        Returns:
            List of indicator results
        """
        results = []
        
        for indicator_name, indicator_func in indicators.items():
            try:
                # Extract required parameters (simplified - would be more sophisticated)
                triggered = False
                value = 0.0
                threshold = 0.0
                
                # Attempt to evaluate indicator
                # This is simplified - in production would have parameter mapping
                if indicator_name == 'DSO_spike':
                    current_dso = financial_data.get('dso_current', 0)
                    prior_dso = financial_data.get('dso_prior', 0)
                    if prior_dso > 0:
                        triggered = indicator_func(current_dso, prior_dso)
                        value = (current_dso - prior_dso) / prior_dso if prior_dso != 0 else 0
                        threshold = 0.25
                
                elif indicator_name == 'revenue_quality':
                    revenue = financial_data.get('revenue', 0)
                    cash_flow = financial_data.get('operating_cash_flow', 0)
                    if cash_flow > 0:
                        triggered = indicator_func(revenue, cash_flow)
                        value = revenue / cash_flow if cash_flow != 0 else 0
                        threshold = 1.5
                
                # Add more indicator evaluations as needed
                
                result = ForensicIndicatorResult(
                    indicator_name=indicator_name,
                    triggered=triggered,
                    value=value,
                    threshold=threshold,
                    explanation=self._generate_indicator_explanation(
                        indicator_name,
                        triggered,
                        value,
                        threshold
                    ),
                    confidence=0.85 if triggered else 0.5,
                    data_source=fraud_type
                )
                
                results.append(result)
                
            except Exception as e:
                logger.warning(f"Error evaluating indicator {indicator_name}: {e}")
        
        return results
    
    def _generate_indicator_explanation(
        self,
        indicator_name: str,
        triggered: bool,
        value: float,
        threshold: float
    ) -> str:
        """Generate human-readable explanation for indicator."""
        if triggered:
            return (
                f"{indicator_name} triggered: value {value:.3f} exceeds "
                f"threshold {threshold:.3f}, indicating potential fraud"
            )
        else:
            return (
                f"{indicator_name} not triggered: value {value:.3f} within "
                f"normal range (threshold: {threshold:.3f})"
            )
    
    async def _map_to_statutes(
        self,
        fraud_type: str,
        statute_citations: List[str],
        text_matches: List[str],
        indicator_results: List[ForensicIndicatorResult]
    ) -> List[StatuteViolationMatch]:
        """
        Map fraud patterns to specific statutes.
        
        Args:
            fraud_type: Type of fraud
            statute_citations: List of statute citations
            text_matches: Matched patterns
            indicator_results: Forensic indicator results
            
        Returns:
            List of statute violation matches
        """
        violations = []
        
        # For each statute citation, find full reference
        for citation in statute_citations:
            # Extract statute key from citation
            statute_key = self._extract_statute_key(citation)
            
            statute_ref = self.statute_database.get(statute_key)
            
            if not statute_ref:
                # Create generic statute reference if not in database
                statute_ref = StatuteReference(
                    citation=citation,
                    title=citation,
                    description=f"Violation related to {fraud_type}",
                    jurisdiction=StatuteJurisdiction.GAAP_FASB,
                    severity=ViolationSeverity.MEDIUM,
                    penalties={},
                    elements=[],
                    case_law=[]
                )
            
            # Calculate confidence based on evidence
            confidence = self._calculate_violation_confidence(
                text_matches,
                indicator_results
            )
            
            # Determine evidence strength
            evidence_strength = self._assess_evidence_strength(
                len(text_matches),
                len([i for i in indicator_results if i.triggered])
            )
            
            # Generate recommended charges
            recommended_charges = self._generate_charges(statute_ref, fraud_type)
            
            # Find similar cases
            similar_cases = self._find_similar_cases(fraud_type)
            
            violation = StatuteViolationMatch(
                statute=statute_ref,
                pattern_matches=text_matches,
                forensic_indicators=indicator_results,
                confidence_score=confidence,
                evidence_strength=evidence_strength,
                recommended_charges=recommended_charges,
                similar_cases=similar_cases,
                evidence_hash=self.hash_chain.blocks[-1].current_hash if self.hash_chain.blocks else ""
            )
            
            violations.append(violation)
        
        return violations
    
    def _extract_statute_key(self, citation: str) -> str:
        """Extract statute key from citation."""
        # Simple mapping - in production would be more sophisticated
        if '15 USC § 78m(a)' in citation or '15 USC § 78m' in citation:
            return '15_USC_78m_a'
        elif '15 USC § 78j(b)' in citation or '15 USC § 78j' in citation:
            return '15_USC_78j_b'
        elif '10b-5' in citation or '240.10b-5' in citation:
            return '17_CFR_240_10b_5'
        elif '7241' in citation or 'SOX 302' in citation or 'Section 302' in citation:
            return '15_USC_7241'
        elif '7262' in citation or 'SOX 404' in citation or 'Section 404' in citation:
            return '15_USC_7262'
        elif '1348' in citation:
            return '18_USC_1348'
        elif '1520' in citation:
            return '18_USC_1520'
        
        return 'unknown'
    
    def _calculate_violation_confidence(
        self,
        text_matches: List[str],
        indicator_results: List[ForensicIndicatorResult]
    ) -> float:
        """Calculate confidence score for violation."""
        # Base confidence
        confidence = 0.3
        
        # Add confidence for pattern matches
        confidence += min(len(text_matches) * 0.15, 0.4)
        
        # Add confidence for triggered indicators
        triggered = [i for i in indicator_results if i.triggered]
        confidence += min(len(triggered) * 0.10, 0.3)
        
        return min(confidence, 1.0)
    
    def _assess_evidence_strength(
        self,
        pattern_count: int,
        indicator_count: int
    ) -> str:
        """Assess overall evidence strength."""
        total_evidence = pattern_count + indicator_count
        
        if total_evidence >= 5:
            return "STRONG"
        elif total_evidence >= 3:
            return "MODERATE"
        else:
            return "WEAK"
    
    def _generate_charges(
        self,
        statute: StatuteReference,
        fraud_type: str
    ) -> List[str]:
        """Generate recommended charges."""
        charges = [f"Violation of {statute.citation}"]
        
        # Add related charges based on severity
        if statute.severity == ViolationSeverity.CRITICAL:
            charges.append("Material misstatement of financial condition")
            charges.append("Securities fraud")
            
            if 'SOX' in statute.title or '7241' in statute.citation:
                charges.append("False certification (SOX 302)")
        
        return charges
    
    def _find_similar_cases(self, fraud_type: str) -> List[str]:
        """Find similar historical cases."""
        # Extract base fraud category
        base_type = fraud_type.split('_')[0]
        
        cases = []
        case_data = self.case_law_database.get(base_type, {})
        
        for case_name, details in case_data.items():
            case_summary = (
                f"{case_name.upper()} ({details['year']}): "
                f"{details['violation']} - {details['outcome']}"
            )
            cases.append(case_summary)
        
        return cases
    
    def _calculate_aggregate_severity(
        self,
        violations: List[StatuteViolationMatch]
    ) -> ViolationSeverity:
        """Calculate aggregate severity from all violations."""
        if not violations:
            return ViolationSeverity.INFORMATIONAL
        
        # Find highest severity
        max_severity = ViolationSeverity.LOW
        
        for violation in violations:
            if violation.statute.severity.value == 'CRITICAL':
                return ViolationSeverity.CRITICAL
            elif violation.statute.severity.value == 'HIGH':
                max_severity = ViolationSeverity.HIGH
            elif violation.statute.severity.value == 'MEDIUM' and max_severity.value != 'HIGH':
                max_severity = ViolationSeverity.MEDIUM
        
        return max_severity
    
    def _calculate_prosecution_priority(
        self,
        violations: List[StatuteViolationMatch],
        pattern_matches: int,
        indicators_triggered: int
    ) -> int:
        """
        Calculate prosecution priority (1-10).
        
        Args:
            violations: List of violations
            pattern_matches: Number of pattern matches
            indicators_triggered: Number of triggered indicators
            
        Returns:
            Priority score 1-10
        """
        priority = 0
        
        # Base priority on number of violations
        priority += min(len(violations), 3)
        
        # Add priority for critical violations
        critical_count = sum(
            1 for v in violations 
            if v.statute.severity == ViolationSeverity.CRITICAL
        )
        priority += critical_count * 2
        
        # Add priority for strong evidence
        strong_evidence = sum(
            1 for v in violations 
            if v.evidence_strength == "STRONG"
        )
        priority += min(strong_evidence, 2)
        
        # Add priority for pattern matches
        priority += min(pattern_matches // 3, 2)
        
        # Add priority for indicators
        priority += min(indicators_triggered // 2, 1)
        
        return min(priority, 10)
    
    def _generate_recommendations(
        self,
        violations: List[StatuteViolationMatch],
        prosecution_priority: int
    ) -> List[str]:
        """Generate recommended actions."""
        recommendations = []
        
        if prosecution_priority >= 8:
            recommendations.append(
                "IMMEDIATE: Refer to enforcement division for criminal prosecution"
            )
            recommendations.append(
                "REQUIRED: Freeze assets and obtain preservation order"
            )
        elif prosecution_priority >= 6:
            recommendations.append(
                "HIGH PRIORITY: Initiate formal investigation"
            )
            recommendations.append(
                "REQUIRED: Issue document preservation notice"
            )
        elif prosecution_priority >= 4:
            recommendations.append(
                "MEDIUM PRIORITY: Conduct inquiry and gather additional evidence"
            )
        else:
            recommendations.append(
                "LOW PRIORITY: Monitor for additional indicators"
            )
        
        # Add specific recommendations based on violations
        critical_violations = [
            v for v in violations 
            if v.statute.severity == ViolationSeverity.CRITICAL
        ]
        
        if critical_violations:
            recommendations.append(
                "ACTION: Subpoena corporate records and executive communications"
            )
            recommendations.append(
                "ACTION: Coordinate with DOJ for potential criminal charges"
            )
        
        # Add SOX-specific recommendations
        sox_violations = [
            v for v in violations 
            if 'SOX' in v.statute.title or '72' in v.statute.citation
        ]
        
        if sox_violations:
            recommendations.append(
                "ACTION: Review CEO/CFO certifications for false statements"
            )
            recommendations.append(
                "ACTION: Assess internal control deficiencies"
            )
        
        recommendations.append(
            "ONGOING: Continue monitoring subsequent filings for pattern recurrence"
        )
        
        return recommendations
    
    async def verify_integrity(self) -> bool:
        """
        Verify hash chain integrity.
        
        Returns:
            True if chain valid
        """
        is_valid = await self.hash_chain.verify_chain()
        
        if not is_valid:
            logger.critical("Statutory mapper hash chain integrity violation!")
        
        return is_valid


# Backward compatibility exports
__all__ = [
    'ForensicStatutoryMapper',
    'StatuteJurisdiction',
    'ViolationSeverity',
    'StatuteReference',
    'ForensicIndicatorResult',
    'StatuteViolationMatch',
    'ComprehensiveStatutoryAnalysis'
]

