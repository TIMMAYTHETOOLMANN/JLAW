"""
Node 16: Customs & Trade Fraud Detection
==========================================

Implements detection of international trade fraud vectors including:
1. Tariff evasion and HS code misclassification
2. Valuation fraud (under/over-invoicing)
3. Country of origin fraud
4. Transfer pricing abuse
5. Trade-based money laundering (TBML)
6. OFAC sanctions violations
7. Phantom shipment detection
8. Free trade zone abuse and round-tripping

Legal Framework:
- 19 U.S.C. § 1592 (Customs fraud penalties)
- 19 U.S.C. § 1595a (Seizure and forfeiture)
- 18 U.S.C. § 545 (Smuggling)
- 31 U.S.C. § 5318(g) (TBML reporting)
- 50 U.S.C. § 1705 (OFAC violations)
- 26 U.S.C. § 482 (Transfer pricing allocation)

Regulatory Routing:
- CBP (U.S. Customs and Border Protection)
- FinCEN (Financial Crimes Enforcement Network)
- OFAC (Office of Foreign Assets Control)
- SEC (for public company disclosure violations)
- DOJ (for criminal prosecution)
- IRS (for tax evasion via transfer pricing)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class CustomsViolationType(Enum):
    """Types of customs and trade violations."""
    TARIFF_EVASION = "TARIFF_EVASION"
    HS_CODE_MISCLASSIFICATION = "HS_CODE_MISCLASSIFICATION"
    VALUATION_FRAUD = "VALUATION_FRAUD"
    COUNTRY_OF_ORIGIN_FRAUD = "COUNTRY_OF_ORIGIN_FRAUD"
    TRANSFER_PRICING_ABUSE = "TRANSFER_PRICING_ABUSE"
    TBML = "TRADE_BASED_MONEY_LAUNDERING"
    OFAC_SANCTIONS = "OFAC_SANCTIONS_VIOLATION"
    PHANTOM_SHIPMENT = "PHANTOM_SHIPMENT"
    FTZ_ABUSE = "FREE_TRADE_ZONE_ABUSE"
    ROUND_TRIPPING = "ROUND_TRIPPING"


class TradeSeverity(Enum):
    """Severity levels for trade violations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class TradeTransaction:
    """Represents an international trade transaction."""
    transaction_id: str
    transaction_date: date
    importer: str
    exporter: str
    country_of_origin: str
    hs_code: str
    declared_value: float
    quantity: int
    description: str
    shipping_method: Optional[str] = None
    ftz_location: Optional[str] = None
    related_party: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "transaction_date": self.transaction_date.isoformat() if isinstance(self.transaction_date, date) else self.transaction_date,
            "importer": self.importer,
            "exporter": self.exporter,
            "country_of_origin": self.country_of_origin,
            "hs_code": self.hs_code,
            "declared_value": self.declared_value,
            "quantity": self.quantity,
            "description": self.description,
            "shipping_method": self.shipping_method,
            "ftz_location": self.ftz_location,
            "related_party": self.related_party
        }


@dataclass
class CustomsViolation:
    """Represents a detected customs/trade violation."""
    violation_type: CustomsViolationType
    severity: TradeSeverity
    confidence: float
    description: str
    evidence: Dict[str, Any]
    transactions_involved: List[str]
    estimated_loss: float
    regulatory_citations: List[str]
    recommended_agencies: List[str]
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "violation_type": self.violation_type.value,
            "severity": self.severity.value,
            "confidence": round(self.confidence, 3),
            "description": self.description,
            "evidence": self.evidence,
            "transactions_involved": self.transactions_involved,
            "estimated_loss": round(self.estimated_loss, 2),
            "regulatory_citations": self.regulatory_citations,
            "recommended_agencies": self.recommended_agencies,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class CustomsTradeResult:
    """Result from customs and trade fraud analysis."""
    analysis_date: datetime
    company_name: str
    cik: str
    transactions_analyzed: int
    violations_found: int
    violations: List[CustomsViolation]
    total_estimated_loss: float
    high_risk_countries: List[str]
    suspicious_hs_codes: List[str]
    alerts: List[str]
    execution_time_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_date": self.analysis_date.isoformat(),
            "company_name": self.company_name,
            "cik": self.cik,
            "transactions_analyzed": self.transactions_analyzed,
            "violations_found": self.violations_found,
            "violations": [v.to_dict() for v in self.violations],
            "total_estimated_loss": round(self.total_estimated_loss, 2),
            "high_risk_countries": self.high_risk_countries,
            "suspicious_hs_codes": self.suspicious_hs_codes,
            "alerts": self.alerts,
            "execution_time_seconds": round(self.execution_time_seconds, 2)
        }


class CustomsTradeAnalyzer:
    """
    Node 16: Customs & Trade Fraud Detection Engine
    
    Analyzes international trade transactions for indicators of:
    - Customs fraud
    - Trade-based money laundering
    - Sanctions violations
    - Transfer pricing manipulation
    """
    
    # OFAC Sanctioned Countries (as of 2024)
    OFAC_SANCTIONED_COUNTRIES = {
        'IRAN', 'CUBA', 'NORTH KOREA', 'SYRIA', 'CRIMEA', 'RUSSIA',
        'BELARUS', 'VENEZUELA', 'MYANMAR', 'ZIMBABWE', 'LEBANON'
    }
    
    # High-risk Free Trade Zones
    HIGH_RISK_FTZ = {
        'COLON FREE ZONE, PANAMA',
        'JEBEL ALI FREE ZONE, UAE',
        'PORT KLANG FREE ZONE, MALAYSIA',
        'GUANGZHOU FREE TRADE ZONE, CHINA',
        'DUBAI MULTI COMMODITIES CENTRE, UAE'
    }
    
    # Evasion-prone HS codes (commonly misclassified for tariff evasion)
    EVASION_PRONE_HS_CODES = {
        '6403': 'Footwear (often misclassified)',
        '6204': 'Women\'s suits (textile classification games)',
        '8471': 'Computers (component unbundling)',
        '8517': 'Telecom equipment (splitting strategies)',
        '8528': 'Monitors/displays (false declarations)',
        '9503': 'Toys (lead to furniture reclassification)',
        '6110': 'Knitted sweaters (fiber content fraud)',
        '9401': 'Seats/furniture (material misrepresentation)'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def analyze(
        self,
        company_name: str,
        cik: str,
        transactions: List[TradeTransaction],
        financial_data: Optional[Dict[str, Any]] = None
    ) -> CustomsTradeResult:
        """
        Execute Node 16 customs and trade fraud analysis.
        
        Args:
            company_name: Target company name
            cik: SEC Central Index Key
            transactions: List of trade transactions to analyze
            financial_data: Optional financial data for transfer pricing analysis
        
        Returns:
            CustomsTradeResult with detected violations
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"=== Node 16: Customs & Trade Analysis for {company_name} ===")
        self.logger.info(f"Analyzing {len(transactions)} trade transactions...")
        
        violations: List[CustomsViolation] = []
        alerts: List[str] = []
        
        # Run all detection vectors
        try:
            # Vector 1: Tariff Evasion & HS Code Misclassification
            tariff_violations = self._detect_tariff_evasion(transactions)
            violations.extend(tariff_violations)
            if tariff_violations:
                alerts.append(f"Detected {len(tariff_violations)} potential tariff evasion cases")
            
            # Vector 2: Valuation Fraud (Under/Over-invoicing)
            valuation_violations = self._detect_valuation_fraud(transactions)
            violations.extend(valuation_violations)
            if valuation_violations:
                alerts.append(f"Detected {len(valuation_violations)} valuation fraud indicators")
            
            # Vector 3: Country of Origin Fraud
            origin_violations = self._detect_country_of_origin_fraud(transactions)
            violations.extend(origin_violations)
            if origin_violations:
                alerts.append(f"Detected {len(origin_violations)} country of origin issues")
            
            # Vector 4: Transfer Pricing Abuse
            transfer_pricing_violations = self._detect_transfer_pricing_abuse(
                transactions, financial_data
            )
            violations.extend(transfer_pricing_violations)
            if transfer_pricing_violations:
                alerts.append(f"Detected {len(transfer_pricing_violations)} transfer pricing anomalies")
            
            # Vector 5: Trade-Based Money Laundering (TBML)
            tbml_violations = self._detect_tbml(transactions)
            violations.extend(tbml_violations)
            if tbml_violations:
                alerts.append(f"Detected {len(tbml_violations)} TBML red flags")
            
            # Vector 6: OFAC Sanctions Violations
            sanctions_violations = self._detect_sanctions_violations(transactions)
            violations.extend(sanctions_violations)
            if sanctions_violations:
                alerts.append(f"CRITICAL: {len(sanctions_violations)} OFAC sanctions violations")
            
            # Vector 7: Phantom Shipment Detection
            phantom_violations = self._detect_phantom_shipments(transactions)
            violations.extend(phantom_violations)
            if phantom_violations:
                alerts.append(f"Detected {len(phantom_violations)} phantom shipment indicators")
            
            # Vector 8: Free Trade Zone Abuse & Round-Tripping
            ftz_violations = self._detect_ftz_abuse(transactions)
            violations.extend(ftz_violations)
            if ftz_violations:
                alerts.append(f"Detected {len(ftz_violations)} FTZ abuse patterns")
            
        except Exception as e:
            self.logger.error(f"Error during customs analysis: {e}", exc_info=True)
            alerts.append(f"Analysis error: {str(e)}")
        
        # Calculate aggregate metrics
        total_loss = sum(v.estimated_loss for v in violations)
        high_risk_countries = list(set(
            t.country_of_origin.upper() for t in transactions
            if t.country_of_origin.upper() in self.OFAC_SANCTIONED_COUNTRIES
        ))
        suspicious_hs_codes = list(set(
            t.hs_code for t in transactions
            if t.hs_code[:4] in self.EVASION_PRONE_HS_CODES
        ))
        
        execution_time = time.time() - start_time
        
        result = CustomsTradeResult(
            analysis_date=datetime.utcnow(),
            company_name=company_name,
            cik=cik,
            transactions_analyzed=len(transactions),
            violations_found=len(violations),
            violations=violations,
            total_estimated_loss=total_loss,
            high_risk_countries=high_risk_countries,
            suspicious_hs_codes=suspicious_hs_codes,
            alerts=alerts,
            execution_time_seconds=execution_time
        )
        
        self.logger.info(f"✓ Node 16 complete: {len(violations)} violations detected in {execution_time:.2f}s")
        return result
    
    def _detect_tariff_evasion(
        self,
        transactions: List[TradeTransaction]
    ) -> List[CustomsViolation]:
        """Detect tariff evasion via HS code misclassification."""
        violations = []
        
        # Check for transactions using evasion-prone HS codes
        for transaction in transactions:
            hs_prefix = transaction.hs_code[:4]
            if hs_prefix in self.EVASION_PRONE_HS_CODES:
                # Flag for review
                violation = CustomsViolation(
                    violation_type=CustomsViolationType.HS_CODE_MISCLASSIFICATION,
                    severity=TradeSeverity.MEDIUM,
                    confidence=0.65,
                    description=f"HS code {transaction.hs_code} is evasion-prone: {self.EVASION_PRONE_HS_CODES[hs_prefix]}",
                    evidence={
                        "transaction_id": transaction.transaction_id,
                        "hs_code": transaction.hs_code,
                        "description": transaction.description,
                        "declared_value": transaction.declared_value,
                        "evasion_category": self.EVASION_PRONE_HS_CODES[hs_prefix]
                    },
                    transactions_involved=[transaction.transaction_id],
                    estimated_loss=transaction.declared_value * 0.15,  # Assume 15% tariff loss
                    regulatory_citations=[
                        "19 U.S.C. § 1592 (Customs fraud)",
                        "19 CFR § 177 (HS classification rulings)"
                    ],
                    recommended_agencies=["CBP", "DOJ"]
                )
                violations.append(violation)
        
        return violations
    
    def _detect_valuation_fraud(
        self,
        transactions: List[TradeTransaction]
    ) -> List[CustomsViolation]:
        """Detect under-invoicing or over-invoicing."""
        violations = []
        
        # Group transactions by HS code to detect outliers
        hs_groups: Dict[str, List[TradeTransaction]] = {}
        for t in transactions:
            if t.hs_code not in hs_groups:
                hs_groups[t.hs_code] = []
            hs_groups[t.hs_code].append(t)
        
        # Check for valuation anomalies within each HS code group
        for hs_code, group in hs_groups.items():
            if len(group) < 3:
                continue  # Need sufficient samples
            
            # Calculate average unit value
            unit_values = [t.declared_value / t.quantity for t in group if t.quantity > 0]
            if not unit_values:
                continue
            
            avg_value = sum(unit_values) / len(unit_values)
            
            # Flag transactions with unit values significantly below average
            for transaction in group:
                if transaction.quantity > 0:
                    unit_value = transaction.declared_value / transaction.quantity
                    
                    # Under-invoicing: unit value < 50% of average
                    if unit_value < avg_value * 0.5:
                        violation = CustomsViolation(
                            violation_type=CustomsViolationType.VALUATION_FRAUD,
                            severity=TradeSeverity.HIGH,
                            confidence=0.75,
                            description=f"Potential under-invoicing: Unit value ${unit_value:.2f} is {((1 - unit_value/avg_value) * 100):.1f}% below average",
                            evidence={
                                "transaction_id": transaction.transaction_id,
                                "unit_value": unit_value,
                                "average_unit_value": avg_value,
                                "deviation_percent": ((1 - unit_value/avg_value) * 100)
                            },
                            transactions_involved=[transaction.transaction_id],
                            estimated_loss=transaction.declared_value * 0.30,  # Estimate 30% loss
                            regulatory_citations=[
                                "19 U.S.C. § 1592 (False statements)",
                                "19 U.S.C. § 1401a (Transaction value)"
                            ],
                            recommended_agencies=["CBP", "DOJ"]
                        )
                        violations.append(violation)
                    
                    # Over-invoicing: unit value > 200% of average (potential TBML)
                    elif unit_value > avg_value * 2.0:
                        violation = CustomsViolation(
                            violation_type=CustomsViolationType.VALUATION_FRAUD,
                            severity=TradeSeverity.HIGH,
                            confidence=0.72,
                            description=f"Potential over-invoicing (TBML indicator): Unit value ${unit_value:.2f} is {((unit_value/avg_value - 1) * 100):.1f}% above average",
                            evidence={
                                "transaction_id": transaction.transaction_id,
                                "unit_value": unit_value,
                                "average_unit_value": avg_value,
                                "deviation_percent": ((unit_value/avg_value - 1) * 100)
                            },
                            transactions_involved=[transaction.transaction_id],
                            estimated_loss=0.0,  # Over-invoicing doesn't reduce duties
                            regulatory_citations=[
                                "31 U.S.C. § 5318(g) (TBML)",
                                "18 U.S.C. § 1956 (Money laundering)"
                            ],
                            recommended_agencies=["FinCEN", "DOJ"]
                        )
                        violations.append(violation)
        
        return violations
    
    def _detect_country_of_origin_fraud(
        self,
        transactions: List[TradeTransaction]
    ) -> List[CustomsViolation]:
        """Detect fraudulent country of origin declarations."""
        violations = []
        
        # Look for transshipment patterns (goods routed through intermediary)
        exporter_country_map: Dict[str, Set[str]] = {}
        for t in transactions:
            if t.exporter not in exporter_country_map:
                exporter_country_map[t.exporter] = set()
            exporter_country_map[t.exporter].add(t.country_of_origin.upper())
        
        # Flag exporters declaring multiple countries of origin (transshipment risk)
        for exporter, countries in exporter_country_map.items():
            if len(countries) > 2:
                related_txns = [
                    t.transaction_id for t in transactions
                    if t.exporter == exporter
                ]
                violation = CustomsViolation(
                    violation_type=CustomsViolationType.COUNTRY_OF_ORIGIN_FRAUD,
                    severity=TradeSeverity.MEDIUM,
                    confidence=0.68,
                    description=f"Exporter '{exporter}' declares {len(countries)} different countries of origin (transshipment risk)",
                    evidence={
                        "exporter": exporter,
                        "countries": list(countries),
                        "transaction_count": len(related_txns)
                    },
                    transactions_involved=related_txns,
                    estimated_loss=50000.0,  # Estimated circumvention loss
                    regulatory_citations=[
                        "19 U.S.C. § 3592 (Country of origin marking)",
                        "19 CFR § 134 (Origin marking rules)"
                    ],
                    recommended_agencies=["CBP"]
                )
                violations.append(violation)
        
        return violations
    
    def _detect_transfer_pricing_abuse(
        self,
        transactions: List[TradeTransaction],
        financial_data: Optional[Dict[str, Any]]
    ) -> List[CustomsViolation]:
        """Detect transfer pricing manipulation in related-party transactions."""
        violations = []
        
        # Focus on related-party transactions
        related_party_txns = [t for t in transactions if t.related_party]
        
        if not related_party_txns:
            return violations
        
        # Calculate average related-party vs arm's-length pricing
        related_values = [
            t.declared_value / t.quantity
            for t in related_party_txns if t.quantity > 0
        ]
        
        arm_length_txns = [t for t in transactions if not t.related_party]
        arm_length_values = [
            t.declared_value / t.quantity
            for t in arm_length_txns if t.quantity > 0
        ]
        
        if related_values and arm_length_values:
            avg_related = sum(related_values) / len(related_values)
            avg_arm_length = sum(arm_length_values) / len(arm_length_values)
            
            # Flag if related-party prices are significantly lower (profit shifting)
            if avg_related < avg_arm_length * 0.7:
                deviation = ((1 - avg_related / avg_arm_length) * 100)
                violation = CustomsViolation(
                    violation_type=CustomsViolationType.TRANSFER_PRICING_ABUSE,
                    severity=TradeSeverity.HIGH,
                    confidence=0.78,
                    description=f"Related-party prices {deviation:.1f}% below arm's-length (profit shifting indicator)",
                    evidence={
                        "related_party_avg_price": avg_related,
                        "arms_length_avg_price": avg_arm_length,
                        "deviation_percent": deviation,
                        "transaction_count": len(related_party_txns)
                    },
                    transactions_involved=[t.transaction_id for t in related_party_txns],
                    estimated_loss=sum(t.declared_value for t in related_party_txns) * 0.20,
                    regulatory_citations=[
                        "26 U.S.C. § 482 (Transfer pricing allocation)",
                        "Treas. Reg. § 1.482-1 (Arm's-length standard)"
                    ],
                    recommended_agencies=["IRS", "SEC"]
                )
                violations.append(violation)
        
        return violations
    
    def _detect_tbml(
        self,
        transactions: List[TradeTransaction]
    ) -> List[CustomsViolation]:
        """Detect trade-based money laundering indicators."""
        violations = []
        
        # TBML Indicator 1: Multiple high-value transactions with same parties
        party_pairs: Dict[tuple, List[TradeTransaction]] = {}
        for t in transactions:
            pair = (t.importer, t.exporter)
            if pair not in party_pairs:
                party_pairs[pair] = []
            party_pairs[pair].append(t)
        
        for (importer, exporter), txns in party_pairs.items():
            if len(txns) >= 5:  # Multiple transactions
                total_value = sum(t.declared_value for t in txns)
                if total_value > 1_000_000:  # High aggregate value
                    violation = CustomsViolation(
                        violation_type=CustomsViolationType.TBML,
                        severity=TradeSeverity.HIGH,
                        confidence=0.70,
                        description=f"High-frequency, high-value trade between {importer} and {exporter} (${total_value:,.0f} across {len(txns)} transactions)",
                        evidence={
                            "importer": importer,
                            "exporter": exporter,
                            "transaction_count": len(txns),
                            "total_value": total_value
                        },
                        transactions_involved=[t.transaction_id for t in txns],
                        estimated_loss=0.0,  # TBML is money movement, not duty evasion
                        regulatory_citations=[
                            "31 U.S.C. § 5318(g) (TBML reporting)",
                            "18 U.S.C. § 1956 (Money laundering)"
                        ],
                        recommended_agencies=["FinCEN", "DOJ"]
                    )
                    violations.append(violation)
        
        # TBML Indicator 2: Transactions through high-risk FTZ locations
        ftz_txns = [t for t in transactions if t.ftz_location and t.ftz_location.upper() in self.HIGH_RISK_FTZ]
        if ftz_txns:
            total_ftz_value = sum(t.declared_value for t in ftz_txns)
            violation = CustomsViolation(
                violation_type=CustomsViolationType.TBML,
                severity=TradeSeverity.MEDIUM,
                confidence=0.65,
                description=f"{len(ftz_txns)} transactions through high-risk FTZ locations (${total_ftz_value:,.0f})",
                evidence={
                    "ftz_locations": list(set(t.ftz_location for t in ftz_txns if t.ftz_location)),
                    "transaction_count": len(ftz_txns),
                    "total_value": total_ftz_value
                },
                transactions_involved=[t.transaction_id for t in ftz_txns],
                estimated_loss=0.0,
                regulatory_citations=[
                    "31 U.S.C. § 5318(g) (TBML)",
                    "19 U.S.C. § 81c (FTZ operations)"
                ],
                recommended_agencies=["FinCEN", "CBP"]
            )
            violations.append(violation)
        
        return violations
    
    def _detect_sanctions_violations(
        self,
        transactions: List[TradeTransaction]
    ) -> List[CustomsViolation]:
        """Detect OFAC sanctions violations."""
        violations = []
        
        for transaction in transactions:
            country = transaction.country_of_origin.upper()
            if country in self.OFAC_SANCTIONED_COUNTRIES:
                violation = CustomsViolation(
                    violation_type=CustomsViolationType.OFAC_SANCTIONS,
                    severity=TradeSeverity.CRITICAL,
                    confidence=0.95,
                    description=f"CRITICAL: Transaction with OFAC-sanctioned country {country}",
                    evidence={
                        "transaction_id": transaction.transaction_id,
                        "country": country,
                        "exporter": transaction.exporter,
                        "value": transaction.declared_value,
                        "date": transaction.transaction_date.isoformat() if isinstance(transaction.transaction_date, date) else transaction.transaction_date
                    },
                    transactions_involved=[transaction.transaction_id],
                    estimated_loss=transaction.declared_value,  # Full value at risk
                    regulatory_citations=[
                        "50 U.S.C. § 1705 (OFAC violations)",
                        "31 CFR Chapter V (OFAC regulations)",
                        "E.O. 13224 (Terrorism sanctions)"
                    ],
                    recommended_agencies=["OFAC", "DOJ", "SEC"]
                )
                violations.append(violation)
        
        return violations
    
    def _detect_phantom_shipments(
        self,
        transactions: List[TradeTransaction]
    ) -> List[CustomsViolation]:
        """Detect phantom (non-existent) shipments."""
        violations = []
        
        # Look for transactions with no shipping method specified (red flag)
        no_shipping = [t for t in transactions if not t.shipping_method]
        if no_shipping:
            total_value = sum(t.declared_value for t in no_shipping)
            violation = CustomsViolation(
                violation_type=CustomsViolationType.PHANTOM_SHIPMENT,
                severity=TradeSeverity.MEDIUM,
                confidence=0.60,
                description=f"{len(no_shipping)} transactions with no shipping method (phantom shipment risk)",
                evidence={
                    "transaction_count": len(no_shipping),
                    "total_value": total_value,
                    "sample_transactions": [t.transaction_id for t in no_shipping[:5]]
                },
                transactions_involved=[t.transaction_id for t in no_shipping],
                estimated_loss=total_value * 0.50,  # Assume 50% fraudulent
                regulatory_citations=[
                    "18 U.S.C. § 1343 (Wire fraud)",
                    "19 U.S.C. § 1592 (Customs fraud)"
                ],
                recommended_agencies=["CBP", "DOJ"]
            )
            violations.append(violation)
        
        return violations
    
    def _detect_ftz_abuse(
        self,
        transactions: List[TradeTransaction]
    ) -> List[CustomsViolation]:
        """Detect free trade zone abuse and round-tripping."""
        violations = []
        
        # Check for round-tripping (goods exported from US, reimported after minimal processing)
        # This would require tracking US exports, but we can flag FTZ activity as risk
        ftz_transactions = [t for t in transactions if t.ftz_location]
        
        if len(ftz_transactions) > 10:  # High FTZ usage
            # Check for potential round-tripping (same HS codes in/out)
            hs_codes = [t.hs_code for t in ftz_transactions]
            unique_hs = len(set(hs_codes))
            
            if unique_hs < len(hs_codes) * 0.5:  # Many duplicates
                violation = CustomsViolation(
                    violation_type=CustomsViolationType.FTZ_ABUSE,
                    severity=TradeSeverity.MEDIUM,
                    confidence=0.68,
                    description=f"Potential FTZ round-tripping: {len(ftz_transactions)} FTZ transactions with {unique_hs} unique HS codes",
                    evidence={
                        "ftz_transaction_count": len(ftz_transactions),
                        "unique_hs_codes": unique_hs,
                        "repetition_rate": (1 - unique_hs / len(hs_codes)) * 100
                    },
                    transactions_involved=[t.transaction_id for t in ftz_transactions],
                    estimated_loss=sum(t.declared_value for t in ftz_transactions) * 0.10,
                    regulatory_citations=[
                        "19 U.S.C. § 81c (FTZ Board)",
                        "19 CFR § 146 (FTZ regulations)"
                    ],
                    recommended_agencies=["CBP"]
                )
                violations.append(violation)
        
        return violations
    
    def get_routing_matrix(
        self,
        violations: List[CustomsViolation]
    ) -> Dict[str, bool]:
        """
        Generate agency routing matrix based on detected violations.
        
        Returns:
            Dictionary with agency routing flags (CBP, FinCEN, OFAC, SEC, DOJ, IRS)
        """
        routing = {
            "CBP": False,
            "FinCEN": False,
            "OFAC": False,
            "SEC": False,
            "DOJ": False,
            "IRS": False
        }
        
        for violation in violations:
            for agency in violation.recommended_agencies:
                if agency in routing:
                    routing[agency] = True
        
        return routing
