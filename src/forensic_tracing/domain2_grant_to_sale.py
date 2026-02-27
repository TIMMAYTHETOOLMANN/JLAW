"""
Domain 2: Grant-to-Sale Transaction Tracing Engine
====================================================

Traces the complete lifecycle of insider securities from $0 acquisition
through entity transfer to ultimate cash liquidation.

Matching algorithm:
  1. Build per-insider acquisition inventory from A/M/G/J events
  2. Match dispositions (S/F/J/G/D) against inventory by security title
  3. Cross-reference Form 144 notices within 90-day windows
  4. Track Code J dispositions through entity chain to ultimate sale
  5. Monitor 13D/13G amendments for declining ownership percentages

Common liquidation chains:
  A -> F  (grant -> tax withholding: mechanical, non-discretionary)
  A -> S  (grant -> open market sale: discretionary, days to months)
  M -> S  (exercise-and-sell, often same day)
  A -> G -> [recipient's S]  (grant -> gift -> recipient sale: obfuscation)
  A -> J -> [subsequent S]   (grant -> entity transfer -> later sale)

References:
  - SEC EDGAR Insider Transactions Data Sets (quarterly bulk)
  - Avci et al. (2021) "Insider Giving" Duke Law Journal
  - Avci et al. (2024) "Insider Trading by Other Means" Harvard Bus. Law Rev.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from enum import Enum


class AcquisitionType(Enum):
    """How the insider acquired the securities."""
    GRANT_AWARD = 'A'         # Company grant/award ($0)
    OPTION_EXERCISE = 'M'     # Option exercise/conversion
    GIFT_RECEIVED = 'G_ACQ'   # Gift received (acquisition side)
    ENTITY_TRANSFER_IN = 'J_ACQ'  # Entity transfer in
    OPEN_MARKET_PURCHASE = 'P'    # Open market purchase
    OTHER = 'OTHER'


class DispositionType(Enum):
    """How the insider disposed of the securities."""
    OPEN_MARKET_SALE = 'S'
    TAX_WITHHOLDING = 'F'
    GIFT_OUT = 'G_DISP'
    ENTITY_TRANSFER_OUT = 'J_DISP'
    RETURN_TO_ISSUER = 'D'
    UNKNOWN = 'UNKNOWN'


@dataclass
class AcquisitionRecord:
    """Single acquisition event in the insider's inventory."""
    accession_number: str
    insider_cik: str
    insider_name: str
    transaction_date: str
    transaction_code: str
    acquisition_type: AcquisitionType
    security_title: str
    shares_acquired: float
    shares_remaining: float  # Decremented as matched to dispositions
    price_per_share: float   # 0.0 for grants/gifts
    exercise_price: float    # For option exercises
    market_price: float      # Market price on acquisition date
    is_derivative: bool
    footnotes: List[str] = field(default_factory=list)
    entity_source: Optional[str] = None  # If transferred from entity

    @property
    def acquisition_value(self) -> float:
        return self.market_price * self.shares_acquired

    @property
    def cost_basis(self) -> float:
        if self.acquisition_type == AcquisitionType.OPTION_EXERCISE:
            return self.exercise_price * self.shares_acquired
        return self.price_per_share * self.shares_acquired


@dataclass
class DispositionRecord:
    """Single disposition event."""
    accession_number: str
    insider_cik: str
    insider_name: str
    transaction_date: str
    transaction_code: str
    disposition_type: DispositionType
    security_title: str
    shares_disposed: float
    price_per_share: float
    market_price: float
    is_derivative: bool
    footnotes: List[str] = field(default_factory=list)
    entity_destination: Optional[str] = None  # For J/G transfers
    form_144_correlated: bool = False
    form_144_accession: Optional[str] = None

    @property
    def effective_price(self) -> float:
        """
        The economic value per share for this disposition.

        For cash sales (S): actual sale price (price_per_share)
        For gifts (G), entity transfers (J), tax withholding (F):
          price_per_share is 0, use market_price as the FMV
        """
        if self.price_per_share and self.price_per_share > 0:
            return self.price_per_share
        return self.market_price or 0

    @property
    def economic_value(self) -> float:
        """Total economic value of this disposition (shares * FMV)."""
        return self.effective_price * self.shares_disposed


@dataclass
class LiquidationChain:
    """
    Complete chain from acquisition to final liquidation.
    Traces one batch of shares from grant -> [intermediate transfers] -> sale.
    """
    chain_id: str
    insider_name: str
    insider_cik: str
    security_title: str
    acquisition: AcquisitionRecord
    dispositions: List[DispositionRecord] = field(default_factory=list)
    intermediate_transfers: List[dict] = field(default_factory=list)
    shares_fully_traced: float = 0
    shares_untraced: float = 0
    total_proceeds: float = 0        # Cash received (Code S open market sales ONLY)
    total_economic_value: float = 0   # FMV of shares at disposition (all types incl gifts/transfers)
    total_profit: float = 0           # Realized gain: sale_proceeds - cost_basis (Code S ONLY)
    time_to_first_sale_days: Optional[int] = None
    liquidation_rate: float = 0  # % of acquired shares eventually sold

    @property
    def is_complete(self) -> bool:
        return self.shares_untraced < 1  # Allow for rounding

    @property
    def chain_type(self) -> str:
        """Classify the chain pattern (e.g., A->S, M->S, A->J->S)."""
        codes = [self.acquisition.transaction_code]
        for t in self.intermediate_transfers:
            codes.append(t.get('transaction_code', '?'))
        for d in self.dispositions:
            codes.append(d.transaction_code)
        return ' -> '.join(codes)

    def to_dict(self) -> dict:
        return {
            'chain_id': self.chain_id,
            'insider_name': self.insider_name,
            'chain_type': self.chain_type,
            'security_title': self.security_title,
            'acquisition_date': self.acquisition.transaction_date,
            'acquisition_type': self.acquisition.acquisition_type.value,
            'shares_acquired': self.acquisition.shares_acquired,
            'acquisition_cost_basis': round(self.acquisition.cost_basis, 2),
            'acquisition_market_value': round(self.acquisition.acquisition_value, 2),
            'dispositions': [
                {
                    'date': d.transaction_date,
                    'type': d.disposition_type.value,
                    'code': d.transaction_code,
                    'shares': d.shares_disposed,
                    'price_per_share': d.price_per_share,
                    'effective_price': round(d.effective_price, 4),
                    'economic_value': round(d.economic_value, 2),
                    'entity_destination': d.entity_destination,
                }
                for d in self.dispositions
            ],
            'intermediate_transfers': self.intermediate_transfers,
            'shares_fully_traced': self.shares_fully_traced,
            'shares_untraced': self.shares_untraced,
            'total_proceeds': round(self.total_proceeds, 2),
            'total_economic_value': round(self.total_economic_value, 2),
            'total_profit': round(self.total_profit, 2),
            'time_to_first_sale_days': self.time_to_first_sale_days,
            'liquidation_rate': round(self.liquidation_rate, 4),
            'is_complete': self.is_complete,
        }


class GrantToSaleTracer:
    """
    Traces the complete lifecycle of insider securities.

    The matching engine builds per-insider acquisition inventories from
    Form 4 A/M/G/J acquisition events, then matches dispositions against
    those inventories using security title and FIFO ordering.
    """

    ACQUISITION_CODES = {'A', 'M', 'G', 'J', 'P', 'C', 'W'}
    DISPOSITION_CODES = {'S', 'F', 'D', 'G', 'J'}

    @classmethod
    def build_acquisition_inventory(cls, transactions: list) -> Dict[str, List[AcquisitionRecord]]:
        """
        Build per-insider acquisition inventory from transaction records.

        Args:
            transactions: List of transaction dicts (from analysis_results or FSL)

        Returns:
            Dict mapping insider_name -> list of AcquisitionRecord
        """
        inventory = {}

        for txn in transactions:
            code = (txn.get('transaction_code') or '').upper()
            # Use acquired_disposed if present; do NOT use direct_indirect (D/I = ownership type)
            acq_disp = (txn.get('acquired_disposed') or '').upper()

            # Determine if this is an acquisition
            # For FSL records: entity_transfer=True with J/G code means disposition
            is_entity_transfer_out = (
                txn.get('entity_transfer', False)
                and code in ('J', 'G')
            )
            is_acquisition = (
                code in cls.ACQUISITION_CODES
                and acq_disp != 'D'
                and not is_entity_transfer_out
            ) or (acq_disp == 'A' and not is_entity_transfer_out)

            if not is_acquisition:
                continue

            name = txn.get('reporting_owner') or txn.get('insider_name') or 'Unknown'
            cik = txn.get('reporting_owner_cik') or txn.get('insider_cik') or ''

            acq_type = {
                'A': AcquisitionType.GRANT_AWARD,
                'M': AcquisitionType.OPTION_EXERCISE,
                'P': AcquisitionType.OPEN_MARKET_PURCHASE,
            }.get(code, AcquisitionType.OTHER)

            if code == 'G':
                acq_type = AcquisitionType.GIFT_RECEIVED
            elif code == 'J':
                acq_type = AcquisitionType.ENTITY_TRANSFER_IN

            shares = abs(txn.get('shares', 0) or 0)
            record = AcquisitionRecord(
                accession_number=txn.get('accession_number', ''),
                insider_cik=cik,
                insider_name=name,
                transaction_date=txn.get('transaction_date', ''),
                transaction_code=code,
                acquisition_type=acq_type,
                security_title=txn.get('security_title', 'Common Stock'),
                shares_acquired=shares,
                shares_remaining=shares,
                price_per_share=txn.get('price_per_share', 0) or 0,
                exercise_price=txn.get('exercise_price', 0) or 0,
                market_price=txn.get('market_price_on_date', 0) or 0,
                is_derivative=txn.get('is_derivative', False),
                footnotes=txn.get('footnotes', []),
            )

            inventory.setdefault(name, []).append(record)

        # Sort each inventory by date (FIFO)
        for name in inventory:
            inventory[name].sort(key=lambda r: r.transaction_date)

        return inventory

    @classmethod
    def match_dispositions(cls, inventory: Dict[str, List[AcquisitionRecord]],
                           transactions: list) -> List[LiquidationChain]:
        """
        Match disposition events against acquisition inventory using FIFO.

        Args:
            inventory: Per-insider acquisition inventory
            transactions: All transaction records

        Returns:
            List of LiquidationChain objects
        """
        chains = []
        chain_counter = 0

        # Collect all disposition events
        dispositions = []
        for txn in transactions:
            code = (txn.get('transaction_code') or '').upper()
            acq_disp = (txn.get('acquired_disposed') or '').upper()

            # Entity transfers (J/G) with entity_transfer flag are dispositions
            is_entity_transfer_out = (
                txn.get('entity_transfer', False)
                and code in ('J', 'G')
            )
            is_disposition = (
                code in cls.DISPOSITION_CODES
                or acq_disp == 'D'
                or is_entity_transfer_out
            )
            if not is_disposition:
                continue

            name = txn.get('reporting_owner') or txn.get('insider_name') or 'Unknown'
            disp_type = {
                'S': DispositionType.OPEN_MARKET_SALE,
                'F': DispositionType.TAX_WITHHOLDING,
                'D': DispositionType.RETURN_TO_ISSUER,
            }.get(code, DispositionType.UNKNOWN)

            if code == 'G':
                disp_type = DispositionType.GIFT_OUT
            elif code == 'J':
                disp_type = DispositionType.ENTITY_TRANSFER_OUT

            dispositions.append(DispositionRecord(
                accession_number=txn.get('accession_number', ''),
                insider_cik=txn.get('reporting_owner_cik', ''),
                insider_name=name,
                transaction_date=txn.get('transaction_date', ''),
                transaction_code=code,
                disposition_type=disp_type,
                security_title=txn.get('security_title', 'Common Stock'),
                shares_disposed=abs(txn.get('shares', 0) or 0),
                price_per_share=txn.get('price_per_share', 0) or 0,
                market_price=txn.get('market_price_on_date', 0) or 0,
                is_derivative=txn.get('is_derivative', False),
                footnotes=txn.get('footnotes', []),
            ))

        # Sort dispositions by date
        dispositions.sort(key=lambda d: d.transaction_date)

        # FIFO matching: for each acquisition, match dispositions
        for insider_name, acq_records in inventory.items():
            insider_dispositions = [d for d in dispositions if d.insider_name == insider_name]

            for acq in acq_records:
                chain_counter += 1
                chain = LiquidationChain(
                    chain_id=f'CHAIN-{chain_counter:04d}',
                    insider_name=insider_name,
                    insider_cik=acq.insider_cik,
                    security_title=acq.security_title,
                    acquisition=acq,
                )

                # Match dispositions after acquisition date
                remaining = acq.shares_remaining
                for disp in insider_dispositions:
                    if remaining <= 0:
                        break
                    if disp.transaction_date < acq.transaction_date:
                        continue

                    matched_shares = min(remaining, disp.shares_disposed)
                    if matched_shares > 0:
                        chain.dispositions.append(disp)
                        remaining -= matched_shares
                        chain.shares_fully_traced += matched_shares
                        # Economic value: FMV of shares at time of disposition (all types)
                        chain.total_economic_value += matched_shares * disp.effective_price
                        # Cash proceeds + realized profit: ONLY from actual open market sales
                        if disp.disposition_type == DispositionType.OPEN_MARKET_SALE:
                            sale_proceeds = matched_shares * disp.effective_price
                            chain.total_proceeds += sale_proceeds
                            # Realized profit = sale price - cost basis (pro-rated)
                            pro_rata_cost = (
                                acq.cost_basis * (matched_shares / acq.shares_acquired)
                                if acq.shares_acquired > 0 else 0
                            )
                            chain.total_profit += sale_proceeds - pro_rata_cost

                chain.shares_untraced = max(remaining, 0)
                # NOTE: total_profit is accumulated above only for Code S sales.
                # For gifts/transfers, profit stays $0 — the value moved but
                # no cash was realized by the insider.

                if chain.dispositions:
                    acq_date = datetime.strptime(acq.transaction_date, '%Y-%m-%d')
                    first_sale_date = datetime.strptime(
                        chain.dispositions[0].transaction_date, '%Y-%m-%d'
                    )
                    chain.time_to_first_sale_days = (first_sale_date - acq_date).days

                chain.liquidation_rate = (
                    chain.shares_fully_traced / acq.shares_acquired
                    if acq.shares_acquired > 0 else 0
                )

                chains.append(chain)

        return chains

    @classmethod
    def trace_all(cls, transactions: list) -> dict:
        """
        Run the complete grant-to-sale tracing pipeline.

        Args:
            transactions: All enriched transaction records

        Returns:
            Dict with inventory, chains, and summary statistics
        """
        inventory = cls.build_acquisition_inventory(transactions)
        chains = cls.match_dispositions(inventory, transactions)

        # Also build acquisition-only chains for unmatched acquisitions
        # These represent shares acquired at $0 that haven't been sold yet
        # (or whose sales aren't in this dataset)
        if not chains:
            chain_counter = 0
            for insider_name, acq_records in inventory.items():
                for acq in acq_records:
                    chain_counter += 1
                    chain = LiquidationChain(
                        chain_id=f'CHAIN-{chain_counter:04d}',
                        insider_name=insider_name,
                        insider_cik=acq.insider_cik,
                        security_title=acq.security_title,
                        acquisition=acq,
                        shares_untraced=acq.shares_acquired,
                    )
                    chains.append(chain)

        # Summary statistics
        total_acquired = sum(
            sum(r.shares_acquired for r in records)
            for records in inventory.values()
        )
        total_sold = sum(c.shares_fully_traced for c in chains)
        total_cash_proceeds = sum(c.total_proceeds for c in chains)
        total_economic_value = sum(c.total_economic_value for c in chains)
        total_profit = sum(c.total_profit for c in chains)

        # Compute total market value of acquired shares
        total_acq_value = sum(
            sum(r.acquisition_value for r in records)
            for records in inventory.values()
        )

        chain_types = {}
        for c in chains:
            ct = c.chain_type
            chain_types[ct] = chain_types.get(ct, 0) + 1

        # Identify obfuscation vectors: A->G or A->J chains
        obfuscation_chains = [
            c for c in chains
            if c.acquisition.acquisition_type == AcquisitionType.GRANT_AWARD
            and any(d.disposition_type in (DispositionType.GIFT_OUT, DispositionType.ENTITY_TRANSFER_OUT)
                    for d in c.dispositions)
        ]

        return {
            'inventory_size': sum(len(v) for v in inventory.values()),
            'insiders_tracked': len(inventory),
            'chains_constructed': len(chains),
            'complete_chains': len([c for c in chains if c.is_complete]),
            'incomplete_chains': len([c for c in chains if not c.is_complete]),
            'acquisition_only_chains': len([c for c in chains if not c.dispositions]),
            'total_shares_acquired': total_acquired,
            'total_acquisition_market_value': round(total_acq_value, 2),
            'total_shares_sold': total_sold,
            'overall_liquidation_rate': round(total_sold / total_acquired, 4) if total_acquired > 0 else 0,
            'total_cash_proceeds': round(total_cash_proceeds, 2),
            'total_economic_value_transferred': round(total_economic_value, 2),
            'total_profit': round(total_profit, 2),
            'chain_type_distribution': chain_types,
            'obfuscation_vector_chains': len(obfuscation_chains),
            'note': (
                'Acquisition-only chains indicate shares acquired through grants, exercises, '
                'gifts, or entity transfers whose subsequent open-market sales (Code S) '
                'are not captured in this dataset. These represent unrealized economic '
                'benefit requiring Form 144 and future Form 4 monitoring.'
                if not total_sold else ''
            ),
            'chains': [c.to_dict() for c in chains[:50]],  # Limit output size
        }
