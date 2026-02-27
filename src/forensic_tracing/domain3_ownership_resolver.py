"""
Domain 3: Enhanced Beneficial Ownership Chain Resolver
=======================================================

Extends the existing ownership chain module with:
  - Dual beneficial ownership test (Rule 13d-3 vs Rule 16a-1(a)(2))
  - Stock parking detection (SEC v. Drexel Burnham Lambert red flags)
  - Knight/Swoosh paradigm entity chain analysis
  - Anti-evasion provision analysis (Rule 13d-3(b))

Two competing definitions of beneficial ownership:
  Rule 13d-3:      Voting power OR investment power test
  Rule 16a-1(a)(2): Pecuniary interest (profit opportunity) test

References:
  - Rule 13d-3: 17 CFR 240.13d-3 (voting/investment power)
  - Rule 16a-1(a)(2): 17 CFR 240.16a-1(a)(2) (pecuniary interest)
  - Rule 13d-3(b): Anti-evasion provision
  - SEC v. Drexel Burnham Lambert (parking arrangement precedent)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict
from datetime import datetime


class OwnershipTestResult(Enum):
    """Result of applying a beneficial ownership test."""
    BENEFICIAL_OWNER = 'beneficial_owner'
    NOT_BENEFICIAL_OWNER = 'not_beneficial_owner'
    PRESUMED_OWNER = 'presumed_owner'
    DEEMED_OWNER_ANTI_EVASION = 'deemed_owner_anti_evasion'
    INDETERMINATE = 'indeterminate'


class ParkingRedFlag(Enum):
    """Red flags for stock parking arrangements (SEC v. Drexel)."""
    GUARANTEE_AGAINST_LOSS = 'guarantee_against_loss'
    CIRCULAR_TRANSFER = 'circular_transfer'
    DEADLINE_COINCIDENCE = 'reporting_deadline_coincidence'
    ABOVE_BELOW_MARKET_PRICE = 'above_below_market_pricing'
    SHARED_ADDRESS = 'shared_address_or_counsel'
    INCOMPLETE_13D_ITEM6 = 'incomplete_schedule_13d_item6'
    SHORT_HOLD_PERIOD = 'short_holding_period'
    REPURCHASE_AGREEMENT = 'repurchase_agreement'


@dataclass
class BeneficialOwnershipTest:
    """Result of applying both ownership tests to an entity relationship."""
    entity_name: str
    entity_type: str  # LLC, Trust, GRAT, FLP, etc.
    insider_name: str
    insider_cik: str
    shares_involved: float

    # Rule 13d-3 test (voting/investment power)
    rule_13d3_result: OwnershipTestResult = OwnershipTestResult.INDETERMINATE
    has_voting_power: bool = False
    has_investment_power: bool = False
    can_acquire_within_60_days: bool = False
    anti_evasion_triggered: bool = False
    rule_13d3_evidence: List[str] = field(default_factory=list)

    # Rule 16a-1(a)(2) test (pecuniary interest)
    rule_16a1_result: OwnershipTestResult = OwnershipTestResult.INDETERMINATE
    has_direct_pecuniary_interest: bool = False
    has_indirect_pecuniary_interest: bool = False
    pecuniary_interest_basis: str = ''
    rule_16a1_evidence: List[str] = field(default_factory=list)

    # Combined assessment
    overall_beneficial_owner: bool = False
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            'entity_name': self.entity_name,
            'entity_type': self.entity_type,
            'insider_name': self.insider_name,
            'shares_involved': self.shares_involved,
            'rule_13d3': {
                'result': self.rule_13d3_result.value,
                'voting_power': self.has_voting_power,
                'investment_power': self.has_investment_power,
                'acquire_within_60d': self.can_acquire_within_60_days,
                'anti_evasion': self.anti_evasion_triggered,
                'evidence': self.rule_13d3_evidence,
            },
            'rule_16a1': {
                'result': self.rule_16a1_result.value,
                'direct_pecuniary': self.has_direct_pecuniary_interest,
                'indirect_pecuniary': self.has_indirect_pecuniary_interest,
                'pecuniary_basis': self.pecuniary_interest_basis,
                'evidence': self.rule_16a1_evidence,
            },
            'overall_beneficial_owner': self.overall_beneficial_owner,
            'confidence': round(self.confidence, 3),
        }


@dataclass
class ParkingAnalysis:
    """Analysis results for potential stock parking arrangement."""
    entity_a: str
    entity_b: str
    red_flags: List[ParkingRedFlag] = field(default_factory=list)
    red_flag_details: List[str] = field(default_factory=list)
    risk_score: float = 0.0  # 0.0 to 1.0
    transfers_examined: List[dict] = field(default_factory=list)
    conclusion: str = ''

    def to_dict(self) -> dict:
        return {
            'entity_a': self.entity_a,
            'entity_b': self.entity_b,
            'red_flags': [f.value for f in self.red_flags],
            'red_flag_details': self.red_flag_details,
            'risk_score': round(self.risk_score, 3),
            'transfers_examined': len(self.transfers_examined),
            'conclusion': self.conclusion,
        }


class EnhancedOwnershipResolver:
    """
    Enhanced beneficial ownership chain resolver with dual-test framework.

    Applies both Rule 13d-3 (voting/investment power) and Rule 16a-1(a)(2)
    (pecuniary interest) tests to each entity relationship, with anti-evasion
    analysis under Rule 13d-3(b).
    """

    # Entity type -> presumed control characteristics
    ENTITY_CONTROL_PROFILES = {
        'LLC': {
            'voting_power_presumed': True,
            'investment_power_presumed': True,
            'pecuniary_interest_presumed': True,
            'basis': 'Managing member/manager typically retains both voting and investment power',
        },
        'Trust_Revocable': {
            'voting_power_presumed': True,
            'investment_power_presumed': True,
            'pecuniary_interest_presumed': True,
            'basis': 'Settlor retains full power over revocable trust; can revoke within 60 days',
        },
        'Trust_Irrevocable': {
            'voting_power_presumed': False,
            'investment_power_presumed': False,
            'pecuniary_interest_presumed': True,
            'basis': 'Settlor relinquishes legal control but may retain beneficial interest',
        },
        'GRAT': {
            'voting_power_presumed': True,
            'investment_power_presumed': True,
            'pecuniary_interest_presumed': True,
            'basis': 'Grantor retains annuity interest during GRAT term; GP interest in underlying',
        },
        'FLP': {
            'voting_power_presumed': True,
            'investment_power_presumed': True,
            'pecuniary_interest_presumed': True,
            'basis': 'General partner proportionate interest per Rule 16a-1(a)(2)(ii)(B)',
        },
        'Foundation': {
            'voting_power_presumed': True,
            'investment_power_presumed': True,
            'pecuniary_interest_presumed': False,
            'basis': 'Board control but no pecuniary interest; tax deduction at FMV',
        },
        'DAF': {
            'voting_power_presumed': False,
            'investment_power_presumed': False,
            'pecuniary_interest_presumed': False,
            'basis': 'Advisory privileges only; legal ownership transferred to sponsoring org',
        },
        'Spouse': {
            'voting_power_presumed': True,
            'investment_power_presumed': True,
            'pecuniary_interest_presumed': True,
            'basis': 'Rule 16a-1(a)(2)(ii)(A) — securities held by immediate family sharing household',
        },
    }

    @classmethod
    def apply_dual_test(cls, entity_name: str, entity_type: str,
                        insider_name: str, insider_cik: str,
                        shares: float, footnotes: list = None,
                        indicators: list = None) -> BeneficialOwnershipTest:
        """
        Apply both beneficial ownership tests to an entity relationship.

        Args:
            entity_name: Name of the entity
            entity_type: Type (LLC, Trust_Revocable, GRAT, FLP, etc.)
            insider_name: Name of the reporting insider
            insider_cik: CIK of the insider
            shares: Number of shares involved
            footnotes: Relevant footnote text
            indicators: Control indicator strings

        Returns:
            BeneficialOwnershipTest with both test results
        """
        test = BeneficialOwnershipTest(
            entity_name=entity_name,
            entity_type=entity_type,
            insider_name=insider_name,
            insider_cik=insider_cik,
            shares_involved=shares,
        )

        profile = cls.ENTITY_CONTROL_PROFILES.get(entity_type, {})
        footnote_text = ' '.join(footnotes or []).lower()
        indicator_text = ' '.join(indicators or []).lower()

        # --- Rule 13d-3 Test: Voting Power OR Investment Power ---
        test.has_voting_power = profile.get('voting_power_presumed', False)
        test.has_investment_power = profile.get('investment_power_presumed', False)

        # Override based on footnote/indicator evidence
        if 'sole voting power' in indicator_text or 'sole voting power' in footnote_text:
            test.has_voting_power = True
            test.rule_13d3_evidence.append('Sole voting power disclosed')
        if 'shared voting power' in indicator_text:
            test.has_voting_power = True
            test.rule_13d3_evidence.append('Shared voting power disclosed')
        if 'sole dispositive power' in indicator_text or 'investment control' in indicator_text:
            test.has_investment_power = True
            test.rule_13d3_evidence.append('Sole dispositive/investment power disclosed')
        if 'disclaims beneficial ownership' in footnote_text:
            test.rule_13d3_evidence.append(
                'Disclaimer filed — but anti-evasion Rule 13d-3(b) may override'
            )

        # Anti-evasion analysis: Rule 13d-3(b)
        if 'disclaim' in footnote_text and (test.has_voting_power or test.has_investment_power):
            test.anti_evasion_triggered = True
            test.rule_13d3_evidence.append(
                'Anti-evasion triggered: disclaimer + retained voting/investment power'
            )

        # Can acquire within 60 days (revocable trusts, option exercise)
        if entity_type in ('Trust_Revocable', 'GRAT'):
            test.can_acquire_within_60_days = True
            test.rule_13d3_evidence.append(
                f'{entity_type}: can revoke/acquire within 60 days'
            )

        # Rule 13d-3 determination
        if test.has_voting_power or test.has_investment_power:
            test.rule_13d3_result = OwnershipTestResult.BENEFICIAL_OWNER
        elif test.anti_evasion_triggered:
            test.rule_13d3_result = OwnershipTestResult.DEEMED_OWNER_ANTI_EVASION
        elif test.can_acquire_within_60_days:
            test.rule_13d3_result = OwnershipTestResult.PRESUMED_OWNER
        else:
            test.rule_13d3_result = OwnershipTestResult.NOT_BENEFICIAL_OWNER

        # --- Rule 16a-1(a)(2) Test: Pecuniary Interest ---
        test.has_direct_pecuniary_interest = profile.get('pecuniary_interest_presumed', False)

        # Check indirect pecuniary interest
        if 'performance' in footnote_text or 'carried interest' in footnote_text:
            test.has_indirect_pecuniary_interest = True
            test.pecuniary_interest_basis = 'Performance-related fees'
            test.rule_16a1_evidence.append('Performance-related fees indicate pecuniary interest')

        if entity_type == 'Spouse':
            test.has_indirect_pecuniary_interest = True
            test.pecuniary_interest_basis = 'Immediate family member sharing household'
            test.rule_16a1_evidence.append(
                'Rule 16a-1(a)(2)(ii)(A): household family member'
            )

        if entity_type == 'FLP':
            test.pecuniary_interest_basis = 'General partner proportionate interest'
            test.rule_16a1_evidence.append(
                'Rule 16a-1(a)(2)(ii)(B): GP proportionate interest'
            )

        if 'except to the extent of' in footnote_text and 'pecuniary interest' in footnote_text:
            test.has_direct_pecuniary_interest = True
            test.rule_16a1_evidence.append(
                'Pecuniary interest disclaimer confirms some retained interest'
            )

        # Rule 16a-1 determination
        if test.has_direct_pecuniary_interest or test.has_indirect_pecuniary_interest:
            test.rule_16a1_result = OwnershipTestResult.BENEFICIAL_OWNER
        else:
            test.rule_16a1_result = OwnershipTestResult.NOT_BENEFICIAL_OWNER

        # --- Combined Assessment ---
        test.overall_beneficial_owner = (
            test.rule_13d3_result in (
                OwnershipTestResult.BENEFICIAL_OWNER,
                OwnershipTestResult.DEEMED_OWNER_ANTI_EVASION,
                OwnershipTestResult.PRESUMED_OWNER,
            )
            or test.rule_16a1_result == OwnershipTestResult.BENEFICIAL_OWNER
        )

        # Confidence score
        confidence = 0.0
        if test.has_voting_power:
            confidence += 0.25
        if test.has_investment_power:
            confidence += 0.25
        if test.has_direct_pecuniary_interest:
            confidence += 0.25
        if test.has_indirect_pecuniary_interest:
            confidence += 0.15
        if test.anti_evasion_triggered:
            confidence += 0.10
        test.confidence = min(confidence, 1.0)

        return test


class ParkingDetector:
    """
    Detect potential stock parking arrangements.

    Stock parking: temporarily transferring nominal ownership while retaining
    actual beneficial ownership. Violates Sections 10(b), 13(d), and Rule 10b-5.

    Red flags (SEC v. Drexel Burnham Lambert):
      - Guarantee against loss provisions
      - Circular transfers (A->B->A) within short timeframes
      - Transfers coinciding with reporting deadlines
      - Above/below-market repurchase pricing
      - Shared addresses or legal counsel
      - Incomplete Schedule 13D Item 6 disclosure
    """

    @classmethod
    def analyze_for_parking(cls, transactions: list,
                            entity_addresses: dict = None) -> List[ParkingAnalysis]:
        """
        Analyze transactions for stock parking red flags.

        Args:
            transactions: All transaction records
            entity_addresses: Optional dict mapping entity names to addresses

        Returns:
            List of ParkingAnalysis results
        """
        results = []
        addresses = entity_addresses or {}

        # Group transactions by insider
        by_insider = {}
        for txn in transactions:
            name = txn.get('reporting_owner') or txn.get('insider_name') or ''
            by_insider.setdefault(name, []).append(txn)

        for insider_name, txns in by_insider.items():
            # Sort by date
            txns.sort(key=lambda t: t.get('transaction_date', ''))

            # Check for circular transfers: outgoing J/G followed by incoming J/G
            outgoing = [t for t in txns if t.get('transaction_code', '').upper() in ('J', 'G')
                        and (t.get('acquired_disposed', '') == 'D'
                             or t.get('shares', 0) < 0)]
            incoming = [t for t in txns if t.get('transaction_code', '').upper() in ('J', 'G')
                        and (t.get('acquired_disposed', '') == 'A'
                             or t.get('shares', 0) > 0)]

            for out_txn in outgoing:
                for in_txn in incoming:
                    analysis = cls._check_pair(
                        out_txn, in_txn, insider_name, addresses
                    )
                    if analysis and analysis.risk_score > 0.20:
                        results.append(analysis)

            # Check for same-date entity transfers between related parties
            by_date = {}
            for t in txns:
                d = t.get('transaction_date', '')
                by_date.setdefault(d, []).append(t)

            for date_str, date_txns in by_date.items():
                if len(date_txns) >= 3:
                    j_txns = [t for t in date_txns
                              if t.get('transaction_code', '').upper() == 'J']
                    if len(j_txns) >= 2:
                        analysis = ParkingAnalysis(
                            entity_a=insider_name,
                            entity_b=f'Multiple entities on {date_str}',
                        )
                        analysis.red_flags.append(ParkingRedFlag.CIRCULAR_TRANSFER)
                        analysis.red_flag_details.append(
                            f'{len(j_txns)} J-code transfers on same date ({date_str}) — '
                            f'potential coordinated restructuring or parking'
                        )
                        analysis.risk_score = 0.30 + (0.10 * len(j_txns))
                        analysis.transfers_examined = j_txns
                        analysis.conclusion = (
                            'Multiple same-date entity transfers detected. '
                            'Requires manual review of entity relationships '
                            'to determine if parking arrangement exists.'
                        )
                        results.append(analysis)

        return results

    @classmethod
    def _check_pair(cls, out_txn: dict, in_txn: dict,
                    insider_name: str, addresses: dict) -> Optional[ParkingAnalysis]:
        """Check a pair of transactions for parking red flags."""
        out_date = out_txn.get('transaction_date', '')
        in_date = in_txn.get('transaction_date', '')

        if not out_date or not in_date:
            return None

        try:
            out_dt = datetime.strptime(out_date, '%Y-%m-%d')
            in_dt = datetime.strptime(in_date, '%Y-%m-%d')
            days_between = (in_dt - out_dt).days
        except ValueError:
            return None

        # Only analyze if incoming is after outgoing and within 180 days
        if days_between < 0 or days_between > 180:
            return None

        analysis = ParkingAnalysis(
            entity_a=insider_name,
            entity_b=out_txn.get('entity_destination', 'Unknown entity'),
        )

        # Red flag: circular transfer within short timeframe
        if days_between <= 90:
            analysis.red_flags.append(ParkingRedFlag.CIRCULAR_TRANSFER)
            analysis.red_flag_details.append(
                f'Shares returned within {days_between} days — potential parking'
            )
            analysis.risk_score += 0.25

        # Red flag: short holding period
        if days_between <= 30:
            analysis.red_flags.append(ParkingRedFlag.SHORT_HOLD_PERIOD)
            analysis.red_flag_details.append(
                f'Only {days_between} days between transfer out and transfer back'
            )
            analysis.risk_score += 0.20

        # Red flag: shared address
        entity_name = out_txn.get('entity_destination', '')
        if entity_name in addresses and insider_name in addresses:
            if addresses[entity_name] == addresses[insider_name]:
                analysis.red_flags.append(ParkingRedFlag.SHARED_ADDRESS)
                analysis.red_flag_details.append(
                    f'Entity address matches insider address'
                )
                analysis.risk_score += 0.20

        analysis.transfers_examined = [out_txn, in_txn]
        analysis.risk_score = min(analysis.risk_score, 1.0)

        if analysis.risk_score > 0:
            analysis.conclusion = (
                f'Potential parking arrangement detected with risk score '
                f'{analysis.risk_score:.2f}. {len(analysis.red_flags)} red flags identified. '
                f'Requires further investigation of entity relationship and economic terms.'
            )

        return analysis
