#!/usr/bin/env python3
"""
NODE 5: IRC §83 Tax Exposure Calculator
Calculates tax exposure from equity compensation grants and transactions.
Detects: Late §83(b) elections, unreported income, valuation discrepancies,
excessive deferrals, Section 409A violations.

Legal Basis: IRC §83, IRC §409A, IRS Revenue Ruling 2005-48
"""

import re
import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IRC83ViolationType(Enum):
    """Classification of IRC §83 violations"""
    LATE_83B_ELECTION = "late_83b_election"
    UNREPORTED_INCOME = "unreported_ordinary_income"
    VALUATION_DISCREPANCY = "fmv_exercise_price_discrepancy"
    EXCESSIVE_DEFERRAL = "excessive_compensation_deferral"
    SECTION_409A_VIOLATION = "section_409a_nonqualified_deferred_comp_violation"


class GrantType(Enum):
    """Types of equity grants"""
    RESTRICTED_STOCK = "restricted_stock"
    STOCK_OPTION_ISO = "incentive_stock_option"
    STOCK_OPTION_NSO = "non_qualified_stock_option"
    RSU = "restricted_stock_unit"
    PERFORMANCE_SHARES = "performance_shares"
    SAR = "stock_appreciation_right"


@dataclass
class EquityGrant:
    """Individual equity compensation grant"""
    grant_id: str
    recipient_name: str
    grant_type: GrantType
    grant_date: date
    grant_price: Decimal  # Exercise price or $0 for restricted stock
    shares_granted: int
    vesting_schedule: str
    vesting_complete_date: Optional[date] = None
    
    # Fair market value tracking
    fmv_at_grant: Decimal = Decimal("0")
    fmv_at_vesting: Decimal = Decimal("0")
    fmv_at_exercise: Decimal = Decimal("0")
    
    # Transaction details
    vested: bool = False
    vesting_date: Optional[date] = None
    exercised: bool = False
    exercise_date: Optional[date] = None
    
    # Tax attributes
    section_83b_elected: bool = False
    section_83b_election_date: Optional[date] = None
    ordinary_income_recognized: Decimal = Decimal("0")
    capital_gains_potential: Decimal = Decimal("0")
    
    def calculate_ordinary_income_at_vesting(self) -> Decimal:
        """Calculate ordinary income at vesting if no 83(b) election"""
        if self.section_83b_elected:
            # Income recognized at grant
            return max(self.fmv_at_grant - self.grant_price, Decimal("0"))
        else:
            # Income recognized at vesting
            return max(self.fmv_at_vesting - self.grant_price, Decimal("0")) if self.vested else Decimal("0")
    
    def is_83b_timely(self) -> bool:
        """Check if 83(b) election was filed within 30 days"""
        if not self.section_83b_elected or not self.section_83b_election_date:
            return True  # N/A
        return (self.section_83b_election_date - self.grant_date).days <= 30


@dataclass
class Section83bElection:
    """IRC §83(b) election to include property in income"""
    election_id: str
    taxpayer_name: str
    taxpayer_ssn: str
    election_date: date
    property_transfer_date: date
    property_description: str
    number_of_shares: int
    
    # Valuation
    fmv_at_transfer: Decimal
    amount_paid: Decimal
    
    # Filing details
    filed_with_irs: bool = False
    filed_with_employer: bool = False
    copy_attached_to_return: bool = False
    
    # Validation
    timely_filed: bool = False
    
    def __post_init__(self):
        """Validate timeliness"""
        self.timely_filed = (self.election_date - self.property_transfer_date).days <= 30


@dataclass
class TaxExposure:
    """Calculated tax exposure from equity compensation"""
    taxpayer_name: str
    tax_year: int
    
    # Ordinary income (taxed at ordinary rates up to 37%)
    ordinary_income_total: Decimal = Decimal("0")
    ordinary_income_items: List[Dict] = field(default_factory=list)
    
    # Capital gains (0%, 15%, or 20% depending on bracket)
    short_term_capital_gains: Decimal = Decimal("0")
    long_term_capital_gains: Decimal = Decimal("0")
    
    # Tax calculations (simplified - actual rates vary)
    estimated_ordinary_tax: Decimal = Decimal("0")  # Assume 37% max
    estimated_capital_gains_tax: Decimal = Decimal("0")  # Assume 20%
    total_estimated_tax: Decimal = Decimal("0")
    
    # AMT exposure (for ISOs)
    amt_preference_items: Decimal = Decimal("0")
    
    def calculate_total_exposure(self):
        """Calculate total tax exposure"""
        self.estimated_ordinary_tax = self.ordinary_income_total * Decimal("0.37")
        self.estimated_capital_gains_tax = (
            self.short_term_capital_gains * Decimal("0.37") +
            self.long_term_capital_gains * Decimal("0.20")
        )
        self.total_estimated_tax = (
            self.estimated_ordinary_tax + 
            self.estimated_capital_gains_tax
        )


@dataclass
class IRC83Violation:
    """Detected IRC §83 violation"""
    violation_type: IRC83ViolationType
    severity: int  # 1-10
    description: str
    affected_individual: str
    tax_exposure: Decimal
    penalty_exposure: Decimal
    regulatory_citations: List[str]
    evidence_text: str
    evidence_hash: str
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['violation_type'] = self.violation_type.value
        result['tax_exposure'] = str(self.tax_exposure)
        result['penalty_exposure'] = str(self.penalty_exposure)
        result['detected_at'] = self.detected_at.isoformat()
        return result


class IRC83TaxCalculator:
    """
    IRC §83 Tax Exposure Calculator
    
    Analyzes Form 4 transactions, equity grant data, and tax filings to:
    - Calculate ordinary income from stock compensation
    - Validate §83(b) election timeliness
    - Detect FMV vs. exercise price discrepancies
    - Identify Section 409A deferred compensation violations
    - Quantify tax exposure
    """
    
    # Tax rates (simplified - actual rates depend on bracket)
    ORDINARY_INCOME_RATE = Decimal("0.37")  # Max federal rate
    LTCG_RATE = Decimal("0.20")  # Max LTCG rate
    
    # IRC 409A safe harbors
    SECTION_409A_DEFERRAL_LIMIT_PCT = Decimal("0.02")  # 2% of compensation
    
    def __init__(self, output_dir: str = "./output/node5_irs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.grants: List[EquityGrant] = []
        self.elections: List[Section83bElection] = []
        self.violations: List[IRC83Violation] = []
    
    def analyze_equity_compensation(
        self,
        form4_transactions: List[Dict[str, Any]],
        grant_data: List[Dict[str, Any]],
        company_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Main entry point for IRC §83 analysis
        
        Args:
            form4_transactions: Parsed Form 4 insider transactions
            grant_data: Equity grant details from proxy/10-K
            company_info: Company metadata (ticker, name)
            
        Returns:
            Complete analysis with violations and tax exposure
        """
        logger.info("Beginning IRC §83 tax exposure analysis")
        
        # Phase 1: Parse equity grants
        self.grants = self._parse_equity_grants(grant_data, company_info)
        logger.info(f"Parsed {len(self.grants)} equity grants")
        
        # Phase 2: Match Form 4 transactions to grants
        self._match_form4_transactions(form4_transactions)
        
        # Phase 3: Validate §83(b) elections
        self._validate_83b_elections()
        
        # Phase 4: Detect FMV discrepancies
        self._detect_valuation_discrepancies()
        
        # Phase 5: Calculate tax exposure
        tax_exposures = self._calculate_tax_exposures()
        
        # Phase 6: Detect Section 409A violations
        self._detect_409a_violations()
        
        # Phase 7: Identify unreported income
        self._identify_unreported_income()
        
        return self._compile_results(tax_exposures)
    
    def _parse_equity_grants(
        self,
        grant_data: List[Dict],
        company_info: Dict
    ) -> List[EquityGrant]:
        """Parse equity grant records"""
        grants = []
        
        for g in grant_data:
            try:
                grant_type_str = g.get('grant_type', 'restricted_stock').lower()
                if 'iso' in grant_type_str or 'incentive' in grant_type_str:
                    grant_type = GrantType.STOCK_OPTION_ISO
                elif 'nso' in grant_type_str or 'non' in grant_type_str:
                    grant_type = GrantType.STOCK_OPTION_NSO
                elif 'rsu' in grant_type_str:
                    grant_type = GrantType.RSU
                else:
                    grant_type = GrantType.RESTRICTED_STOCK
                
                grant = EquityGrant(
                    grant_id=g.get('grant_id', f"GRANT_{len(grants)}"),
                    recipient_name=g.get('recipient_name', ''),
                    grant_type=grant_type,
                    grant_date=self._parse_date(g.get('grant_date')),
                    grant_price=Decimal(str(g.get('grant_price', 0))),
                    shares_granted=int(g.get('shares_granted', 0)),
                    vesting_schedule=g.get('vesting_schedule', ''),
                    fmv_at_grant=Decimal(str(g.get('fmv_at_grant', 0))),
                    fmv_at_vesting=Decimal(str(g.get('fmv_at_vesting', 0))),
                    vested=g.get('vested', False),
                    vesting_date=self._parse_date(g.get('vesting_date')) if g.get('vesting_date') else None,
                    section_83b_elected=g.get('section_83b_elected', False),
                    section_83b_election_date=self._parse_date(g.get('section_83b_election_date')) if g.get('section_83b_election_date') else None
                )
                grants.append(grant)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse grant: {e}")
                continue
        
        return grants
    
    def _parse_date(self, date_val: Any) -> date:
        """Parse date from various formats"""
        if isinstance(date_val, date):
            return date_val
        if isinstance(date_val, str):
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y%m%d']:
                try:
                    return datetime.strptime(date_val, fmt).date()
                except ValueError:
                    continue
        return date.today()
    
    def _match_form4_transactions(self, transactions: List[Dict]) -> None:
        """Match Form 4 transactions to equity grants"""
        # Simplified matching logic - production would use grant IDs
        for txn in transactions:
            txn_date = self._parse_date(txn.get('transaction_date'))
            shares = txn.get('shares', 0)
            price = Decimal(str(txn.get('price_per_share', 0)))
            transaction_code = txn.get('transaction_code', '')
            
            # Match to grants by date proximity and share count
            for grant in self.grants:
                if abs((grant.grant_date - txn_date).days) < 7:
                    if transaction_code == 'A':  # Acquisition (grant)
                        grant.fmv_at_grant = price
                    elif transaction_code == 'M':  # Option exercise
                        grant.exercised = True
                        grant.exercise_date = txn_date
                        grant.fmv_at_exercise = price
    
    def _validate_83b_elections(self) -> None:
        """Validate §83(b) election timeliness"""
        for grant in self.grants:
            if grant.section_83b_elected:
                if not grant.is_83b_timely():
                    # Late election is invalid - income recognized at vesting
                    ordinary_income = grant.calculate_ordinary_income_at_vesting()
                    
                    self.violations.append(IRC83Violation(
                        violation_type=IRC83ViolationType.LATE_83B_ELECTION,
                        severity=8,
                        description=f"§83(b) election filed {(grant.section_83b_election_date - grant.grant_date).days} "
                                   f"days after grant (>30 day deadline). Election invalid.",
                        affected_individual=grant.recipient_name,
                        tax_exposure=ordinary_income * self.ORDINARY_INCOME_RATE,
                        penalty_exposure=ordinary_income * Decimal("0.20"),  # 20% accuracy penalty
                        regulatory_citations=[
                            "IRC §83(b)",
                            "Treas. Reg. §1.83-2",
                            "IRC §6662 (accuracy penalty)"
                        ],
                        evidence_text=f"Grant: {grant.grant_date}, Election: {grant.section_83b_election_date}",
                        evidence_hash=self._hash_evidence(f"{grant.grant_id}:{grant.section_83b_election_date}")
                    ))
    
    def _detect_valuation_discrepancies(self) -> None:
        """Detect FMV vs. exercise price discrepancies"""
        for grant in self.grants:
            if grant.grant_type in [GrantType.STOCK_OPTION_NSO, GrantType.STOCK_OPTION_ISO]:
                # Options should be granted at FMV
                if grant.fmv_at_grant > 0 and grant.grant_price > 0:
                    discount_pct = (grant.fmv_at_grant - grant.grant_price) / grant.fmv_at_grant * 100
                    
                    if discount_pct > 5:  # >5% discount from FMV
                        # Discount stock option - ordinary income at grant
                        discount_value = (grant.fmv_at_grant - grant.grant_price) * grant.shares_granted
                        
                        self.violations.append(IRC83Violation(
                            violation_type=IRC83ViolationType.VALUATION_DISCREPANCY,
                            severity=7,
                            description=f"Stock option granted {discount_pct:.1f}% below FMV "
                                       f"(${grant.grant_price} vs ${grant.fmv_at_grant}). "
                                       f"Discount triggers ordinary income recognition.",
                            affected_individual=grant.recipient_name,
                            tax_exposure=discount_value * self.ORDINARY_INCOME_RATE,
                            penalty_exposure=discount_value * Decimal("0.20"),
                            regulatory_citations=[
                                "IRC §83(a)",
                                "IRC §409A(b)",
                                "Treas. Reg. §1.409A-1(b)(5)(i)"
                            ],
                            evidence_text=f"Grant Price: ${grant.grant_price}, FMV: ${grant.fmv_at_grant}",
                            evidence_hash=self._hash_evidence(f"{grant.grant_id}:DISCOUNT:{discount_value}")
                        ))
    
    def _calculate_tax_exposures(self) -> List[TaxExposure]:
        """Calculate aggregate tax exposure by individual"""
        exposures_by_person: Dict[str, TaxExposure] = {}
        
        for grant in self.grants:
            if grant.recipient_name not in exposures_by_person:
                exposures_by_person[grant.recipient_name] = TaxExposure(
                    taxpayer_name=grant.recipient_name,
                    tax_year=grant.grant_date.year
                )
            
            exposure = exposures_by_person[grant.recipient_name]
            
            # Calculate ordinary income
            ordinary_income = grant.calculate_ordinary_income_at_vesting()
            if ordinary_income > 0:
                exposure.ordinary_income_total += ordinary_income
                exposure.ordinary_income_items.append({
                    "grant_id": grant.grant_id,
                    "grant_date": grant.grant_date.isoformat(),
                    "vesting_date": grant.vesting_date.isoformat() if grant.vesting_date else None,
                    "amount": str(ordinary_income)
                })
            
            # Calculate capital gains (if exercised/sold)
            if grant.exercised and grant.fmv_at_exercise > 0:
                basis = grant.grant_price + ordinary_income / grant.shares_granted
                gain_per_share = grant.fmv_at_exercise - basis
                total_gain = gain_per_share * grant.shares_granted
                
                # Determine if long-term (>1 year holding)
                holding_period = (grant.exercise_date - grant.vesting_date).days if grant.vesting_date else 0
                if holding_period > 365:
                    exposure.long_term_capital_gains += total_gain
                else:
                    exposure.short_term_capital_gains += total_gain
        
        # Calculate totals
        for exposure in exposures_by_person.values():
            exposure.calculate_total_exposure()
        
        return list(exposures_by_person.values())
    
    def _detect_409a_violations(self) -> None:
        """Detect Section 409A nonqualified deferred compensation violations"""
        # Check for excessive deferrals
        total_comp_by_person: Dict[str, Decimal] = {}
        deferred_comp_by_person: Dict[str, Decimal] = {}
        
        for grant in self.grants:
            if grant.grant_type in [GrantType.RSU, GrantType.PERFORMANCE_SHARES]:
                # These are deferred compensation under 409A
                if grant.recipient_name not in deferred_comp_by_person:
                    deferred_comp_by_person[grant.recipient_name] = Decimal("0")
                
                deferred_value = grant.fmv_at_grant * grant.shares_granted
                deferred_comp_by_person[grant.recipient_name] += deferred_value
        
        # Check if deferrals exceed safe harbor
        for person, deferred_amount in deferred_comp_by_person.items():
            # Simplified check - would need total W-2 compensation
            estimated_total_comp = deferred_amount * 5  # Assume 20% deferral rate
            
            if deferred_amount / estimated_total_comp > self.SECTION_409A_DEFERRAL_LIMIT_PCT:
                self.violations.append(IRC83Violation(
                    violation_type=IRC83ViolationType.SECTION_409A_VIOLATION,
                    severity=8,
                    description=f"Deferred compensation of ${deferred_amount:,.0f} may violate "
                               f"Section 409A substantial risk of forfeiture requirements",
                    affected_individual=person,
                    tax_exposure=deferred_amount * self.ORDINARY_INCOME_RATE,
                    penalty_exposure=deferred_amount * Decimal("0.20"),  # 20% additional tax
                    regulatory_citations=[
                        "IRC §409A",
                        "Treas. Reg. §1.409A-1 through §1.409A-6"
                    ],
                    evidence_text=f"Deferred: ${deferred_amount:,.0f}",
                    evidence_hash=self._hash_evidence(f"409A:{person}:{deferred_amount}")
                ))
    
    def _identify_unreported_income(self) -> None:
        """Identify potentially unreported ordinary income from vesting"""
        for grant in self.grants:
            if grant.vested and not grant.section_83b_elected:
                ordinary_income = grant.calculate_ordinary_income_at_vesting()
                
                if ordinary_income > Decimal("1000"):  # Material amount
                    # Check if income appears reported (simplified - would need actual W-2)
                    # For now, flag all vested grants as requiring reporting
                    
                    self.violations.append(IRC83Violation(
                        violation_type=IRC83ViolationType.UNREPORTED_INCOME,
                        severity=6,
                        description=f"Vested restricted stock generated ${ordinary_income:,.0f} "
                                   f"of ordinary income requiring W-2 reporting",
                        affected_individual=grant.recipient_name,
                        tax_exposure=ordinary_income * self.ORDINARY_INCOME_RATE,
                        penalty_exposure=ordinary_income * self.ORDINARY_INCOME_RATE * Decimal("0.05"),  # 5% per month
                        regulatory_citations=[
                            "IRC §83(a)",
                            "IRC §3401 (wage withholding)",
                            "IRC §6651(a)(2) (failure to pay penalty)"
                        ],
                        evidence_text=f"Grant: {grant.grant_id}, Vesting: {grant.vesting_date}",
                        evidence_hash=self._hash_evidence(f"UNREPORTED:{grant.grant_id}:{ordinary_income}")
                    ))
    
    def _hash_evidence(self, evidence: str) -> str:
        """Generate SHA-256 hash of evidence"""
        return hashlib.sha256(evidence.encode('utf-8')).hexdigest()
    
    def _compile_results(self, tax_exposures: List[TaxExposure]) -> Dict[str, Any]:
        """Compile analysis results"""
        results = {
            "node": "NODE_5_IRC83",
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
            "grants_analyzed": len(self.grants),
            "grants": [
                {
                    "grant_id": g.grant_id,
                    "recipient": g.recipient_name,
                    "grant_type": g.grant_type.value,
                    "grant_date": g.grant_date.isoformat(),
                    "shares": g.shares_granted,
                    "fmv_at_grant": str(g.fmv_at_grant),
                    "section_83b_elected": g.section_83b_elected,
                    "vested": g.vested
                }
                for g in self.grants
            ],
            "tax_exposures": [
                {
                    "taxpayer": te.taxpayer_name,
                    "tax_year": te.tax_year,
                    "ordinary_income": str(te.ordinary_income_total),
                    "estimated_ordinary_tax": str(te.estimated_ordinary_tax),
                    "long_term_gains": str(te.long_term_capital_gains),
                    "estimated_ltcg_tax": str(te.estimated_capital_gains_tax),
                    "total_tax_exposure": str(te.total_estimated_tax)
                }
                for te in tax_exposures
            ],
            "violations_detected": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
            "severity_summary": {
                "critical": len([v for v in self.violations if v.severity >= 8]),
                "high": len([v for v in self.violations if 6 <= v.severity < 8]),
                "medium": len([v for v in self.violations if 4 <= v.severity < 6]),
                "low": len([v for v in self.violations if v.severity < 4])
            },
            "total_tax_exposure": str(sum(te.total_estimated_tax for te in tax_exposures)),
            "total_penalty_exposure": str(sum(v.penalty_exposure for v in self.violations))
        }
        
        # Write results
        output_path = self.output_dir / f"irc83_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"IRC §83 analysis complete. Results: {output_path}")
        
        return results


# CLI Entry Point
if __name__ == "__main__":
    calculator = IRC83TaxCalculator()
    
    # Demo data
    grant_data = [
        {
            "grant_id": "GRANT_2024_001",
            "recipient_name": "John Smith",
            "grant_type": "restricted_stock",
            "grant_date": "2024-01-15",
            "grant_price": 0,
            "shares_granted": 10000,
            "fmv_at_grant": 50.00,
            "fmv_at_vesting": 75.00,
            "vested": True,
            "vesting_date": "2024-12-15",
            "section_83b_elected": False
        },
        {
            "grant_id": "GRANT_2024_002",
            "recipient_name": "Jane Doe",
            "grant_type": "stock_option_nso",
            "grant_date": "2024-03-01",
            "grant_price": 45.00,  # Below FMV - discount option
            "shares_granted": 50000,
            "fmv_at_grant": 50.00,
            "vested": False
        }
    ]
    
    form4_transactions = [
        {
            "transaction_date": "2024-01-15",
            "shares": 10000,
            "price_per_share": 50.00,
            "transaction_code": "A"
        }
    ]
    
    company_info = {"cik": "0000320187", "ticker": "NIKE"}
    
    results = calculator.analyze_equity_compensation(form4_transactions, grant_data, company_info)
    print(json.dumps(results, indent=2, default=str))
