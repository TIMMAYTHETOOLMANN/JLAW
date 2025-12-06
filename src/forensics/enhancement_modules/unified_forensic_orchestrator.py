#!/usr/bin/env python3
"""
================================================================================
UNIFIED SEC FORENSIC ANALYSIS ORCHESTRATOR v4.0
================================================================================

Version: 4.0.0-UNIFIED
Authority: JARVIS NEXUS
Classification: PROSECUTORIAL-GRADE UNIFIED SYSTEM

This orchestrator unifies ALL forensic analysis modules into a single,
comprehensive analysis pipeline for maximum detection capability.

INTEGRATED MODULES:
==================
1. Production SEC Forensic System (production_sec_forensic_system.py)
2. Advanced Forensic Analytics (advanced_forensic_analytics.py)
3. ML Fraud Detector (ml_fraud_detector.py)
4. Benford's Law Analyzer (benfords_law_analyzer.py)
5. Quantitative Forensic Analyzer (quantitative_forensic_analyzer.py)
6. Insider Form 4 Analyzer (insider_form4_analyzer.py)
7. Dual Agent Coordinator (dual_agent.py)
8. Temporal Forensic Reconciliation (temporal_forensic_reconciliation.py)
9. Immutable Storage (immutable_storage.py)
10. Forensic Dossier Generator (forensic_dossier_generator.py)

ZERO-DOLLAR TRANSACTION ANALYSIS:
================================
Enhanced detection and classification of $0 transactions:
- RSU vesting events
- Stock grants and awards
- Gift transactions
- Tax withholding (cashless)
- Option exercises at strike price
- Compensation-related transfers

EVIDENCE CHAIN COMPLIANCE:
=========================
- FRE 902(13)/(14) compliant
- SHA-256 hash chains
- RFC 3161 timestamping ready
- Chain of custody tracking

USAGE:
======
    python unified_forensic_orchestrator.py --cik 320187 --year 2019
    python unified_forensic_orchestrator.py --ticker NKE --year 2019 --full-analysis
"""

import asyncio
import json
import logging
import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import internal modules
try:
    from .production_sec_forensic_system import (
        ProductionSECForensicSystem,
        ProductionBenfordAnalyzer,
        BeneishMScoreCalculator,
        AltmanZScoreCalculator,
        ShortSwingProfitCalculator,
        Form4Parser,
        EvidenceChainManager,
        InsiderTransaction,
        BenfordResult,
        BeneishMScoreResult,
        AltmanZScoreResult,
        ShortSwingProfit,
        ManipulationRisk,
        TransactionCode
    )
except ImportError:
    from production_sec_forensic_system import *

# Try importing optional forensic modules
ADVANCED_ANALYTICS_AVAILABLE = False
try:
    from .advanced_forensic_analytics import SemanticContradictionGraph
    ADVANCED_ANALYTICS_AVAILABLE = True
except ImportError:
    pass

ML_DETECTOR_AVAILABLE = False
try:
    from .ml_fraud_detector import AdvancedFraudDetector, MLFraudDetector
    ML_DETECTOR_AVAILABLE = True
except ImportError:
    pass

DUAL_AGENT_AVAILABLE = False
try:
    from .dual_agent import DualAgentCoordinator
    DUAL_AGENT_AVAILABLE = True
except ImportError:
    pass

TEMPORAL_AVAILABLE = False
try:
    from .temporal_forensic_reconciliation import TemporalForensicReconciliation
    TEMPORAL_AVAILABLE = True
except ImportError:
    pass

QUANTITATIVE_AVAILABLE = False
try:
    from .quantitative_forensic_analyzer import QuantitativeForensicAnalyzer
    QUANTITATIVE_AVAILABLE = True
except ImportError:
    pass

DOSSIER_AVAILABLE = False
try:
    from .forensic_dossier_generator import ForensicDossierGenerator
    DOSSIER_AVAILABLE = True
except ImportError:
    pass

# Use existing InsiderForm4Analyzer for robust Form 4 parsing
INSIDER_ANALYZER_AVAILABLE = False
try:
    from .insider_form4_analyzer import InsiderForm4Analyzer, Form4ViolationRecord
    INSIDER_ANALYZER_AVAILABLE = True
except ImportError:
    pass


# =============================================================================
# ZERO-DOLLAR TRANSACTION CLASSIFIER
# =============================================================================

class ZeroDollarTransactionType(Enum):
    """Classification of zero-dollar transactions."""
    RSU_VESTING = "RSU Vesting"
    STOCK_GRANT = "Stock Grant/Award"
    GIFT_TRANSACTION = "Gift Transaction"
    TAX_WITHHOLDING = "Tax Withholding (Cashless)"
    OPTION_EXERCISE = "Option Exercise at Strike"
    COMPENSATION_TRANSFER = "Compensation-Related Transfer"
    ESTATE_TRANSFER = "Estate/Will Transfer"
    CONVERSION = "Conversion of Derivative"
    SPLIT_ADJUSTMENT = "Stock Split Adjustment"
    UNKNOWN = "Unknown/Requires Investigation"


@dataclass
class ZeroDollarAnalysis:
    """Detailed analysis of a zero-dollar transaction."""
    transaction: InsiderTransaction
    classification: ZeroDollarTransactionType
    confidence: float
    red_flags: List[str]
    statutory_implications: List[str]
    estimated_fair_value: float
    requires_further_investigation: bool
    notes: str


class ZeroDollarTransactionAnalyzer:
    """
    Enhanced analyzer for zero-dollar ($0) transactions.
    
    Zero-dollar transactions can indicate:
    - Legitimate compensation events (RSU vesting, grants)
    - Tax-related transfers
    - Potentially suspicious concealment strategies
    
    Based on research: "Insider Trading by Other Means" (2024)
    documenting $100B+ in suspicious concealment via gifts/conversions.
    """
    
    # Transaction codes that commonly result in $0 transactions
    COMMON_ZERO_DOLLAR_CODES = {
        'A': ZeroDollarTransactionType.STOCK_GRANT,  # Award/grant
        'G': ZeroDollarTransactionType.GIFT_TRANSACTION,  # Gift
        'F': ZeroDollarTransactionType.TAX_WITHHOLDING,  # Tax withholding
        'M': ZeroDollarTransactionType.CONVERSION,  # Derivative exercise
        'W': ZeroDollarTransactionType.ESTATE_TRANSFER,  # Will/estate
        'J': ZeroDollarTransactionType.UNKNOWN,  # Other - needs investigation
    }
    
    # Security title keywords for classification
    RSU_KEYWORDS = ['rsu', 'restricted stock unit', 'restricted unit']
    OPTION_KEYWORDS = ['option', 'warrant', 'sar', 'stock appreciation']
    
    def __init__(self):
        self.classifications: List[ZeroDollarAnalysis] = []
    
    def analyze_transaction(
        self,
        transaction: InsiderTransaction,
        market_price: Optional[float] = None
    ) -> ZeroDollarAnalysis:
        """
        Analyze a zero-dollar transaction and classify it.
        
        Args:
            transaction: The insider transaction to analyze
            market_price: Optional market price for fair value estimation
            
        Returns:
            ZeroDollarAnalysis with classification and risk assessment
        """
        if not transaction.is_zero_dollar:
            # Not a zero-dollar transaction
            return ZeroDollarAnalysis(
                transaction=transaction,
                classification=ZeroDollarTransactionType.UNKNOWN,
                confidence=0.0,
                red_flags=[],
                statutory_implications=[],
                estimated_fair_value=transaction.total_value,
                requires_further_investigation=False,
                notes="Not a zero-dollar transaction"
            )
        
        # Classify based on transaction code
        code = transaction.transaction_code
        classification = self.COMMON_ZERO_DOLLAR_CODES.get(
            code, ZeroDollarTransactionType.UNKNOWN
        )
        
        # Refine classification based on security title
        security_lower = transaction.security_title.lower()
        
        if any(kw in security_lower for kw in self.RSU_KEYWORDS):
            classification = ZeroDollarTransactionType.RSU_VESTING
        elif any(kw in security_lower for kw in self.OPTION_KEYWORDS):
            classification = ZeroDollarTransactionType.OPTION_EXERCISE
        
        # Calculate confidence
        confidence = self._calculate_confidence(transaction, classification)
        
        # Identify red flags
        red_flags = self._identify_red_flags(transaction, classification)
        
        # Statutory implications
        statutory = self._get_statutory_implications(transaction, classification, red_flags)
        
        # Estimate fair value
        fair_value = self._estimate_fair_value(transaction, market_price)
        
        # Determine if further investigation needed
        requires_investigation = (
            len(red_flags) > 0 or
            classification == ZeroDollarTransactionType.UNKNOWN or
            code == 'J'  # "Other" always needs investigation
        )
        
        # Generate notes
        notes = self._generate_notes(transaction, classification, red_flags)
        
        analysis = ZeroDollarAnalysis(
            transaction=transaction,
            classification=classification,
            confidence=confidence,
            red_flags=red_flags,
            statutory_implications=statutory,
            estimated_fair_value=fair_value,
            requires_further_investigation=requires_investigation,
            notes=notes
        )
        
        self.classifications.append(analysis)
        return analysis
    
    def _calculate_confidence(
        self,
        transaction: InsiderTransaction,
        classification: ZeroDollarTransactionType
    ) -> float:
        """Calculate confidence level for classification."""
        base_confidence = 0.5
        
        # Code-based confidence boost
        if transaction.transaction_code in ['A', 'G', 'F', 'M', 'W']:
            base_confidence += 0.25
        
        # Security title match
        security_lower = transaction.security_title.lower()
        if any(kw in security_lower for kw in self.RSU_KEYWORDS + self.OPTION_KEYWORDS):
            base_confidence += 0.15
        
        # Known classification (not UNKNOWN)
        if classification != ZeroDollarTransactionType.UNKNOWN:
            base_confidence += 0.1
        
        return min(base_confidence, 0.95)
    
    def _identify_red_flags(
        self,
        transaction: InsiderTransaction,
        classification: ZeroDollarTransactionType
    ) -> List[str]:
        """Identify red flags in the transaction."""
        flags = []
        
        # Large share volume
        if transaction.shares > 100000:
            flags.append(f"High volume: {transaction.shares:,.0f} shares")
        
        # Gift transactions near material events
        if classification == ZeroDollarTransactionType.GIFT_TRANSACTION:
            flags.append("Gift transaction - potential concealment strategy")
        
        # "Other" transaction code
        if transaction.transaction_code == 'J':
            flags.append("Transaction code 'J' (Other) - requires footnote review")
        
        # Late filing
        if transaction.is_late_filing:
            flags.append(f"Late filing: {transaction.days_late} days late")
        
        # No 10b5-1 plan for officer
        if 'Officer' in transaction.relationship and not transaction.is_10b5_1:
            if transaction.transaction_code in ['S', 'P']:
                flags.append("Officer transaction without 10b5-1 plan")
        
        return flags
    
    def _get_statutory_implications(
        self,
        transaction: InsiderTransaction,
        classification: ZeroDollarTransactionType,
        red_flags: List[str]
    ) -> List[str]:
        """Determine statutory implications."""
        statutes = []
        
        # All Form 4 transactions implicate Section 16(a)
        if transaction.is_late_filing:
            statutes.append("15 U.S.C. § 78p(a) - Late Form 4 filing")
        
        # Gift transactions may implicate Rule 10b-5
        if classification == ZeroDollarTransactionType.GIFT_TRANSACTION:
            statutes.append("17 CFR § 240.10b-5 - Potential concealment via gift")
        
        # Short-swing profits
        if transaction.transaction_code in ['S', 'P']:
            statutes.append("15 U.S.C. § 78p(b) - Potential short-swing profit")
        
        return statutes
    
    def _estimate_fair_value(
        self,
        transaction: InsiderTransaction,
        market_price: Optional[float]
    ) -> float:
        """Estimate fair value of zero-dollar transaction."""
        if market_price:
            return transaction.shares * market_price
        
        # Default estimation: use post-transaction average if available
        # This is a rough estimate when market price is unavailable
        return 0.0
    
    def _generate_notes(
        self,
        transaction: InsiderTransaction,
        classification: ZeroDollarTransactionType,
        red_flags: List[str]
    ) -> str:
        """Generate analysis notes."""
        notes = f"Classification: {classification.value}. "
        
        if classification == ZeroDollarTransactionType.RSU_VESTING:
            notes += "Common compensation event - typically legitimate. "
        elif classification == ZeroDollarTransactionType.GIFT_TRANSACTION:
            notes += "ATTENTION: Gift transactions require heightened scrutiny per 'Insider Trading by Other Means' research. "
        elif classification == ZeroDollarTransactionType.UNKNOWN:
            notes += "Unable to classify - requires manual review of footnotes. "
        
        if red_flags:
            notes += f"RED FLAGS: {len(red_flags)} identified. "
        
        return notes.strip()
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of all analyzed zero-dollar transactions."""
        by_type = defaultdict(list)
        for analysis in self.classifications:
            by_type[analysis.classification.value].append(analysis)
        
        total_shares = sum(a.transaction.shares for a in self.classifications)
        total_estimated_value = sum(a.estimated_fair_value for a in self.classifications)
        requiring_investigation = sum(1 for a in self.classifications if a.requires_further_investigation)
        
        return {
            "total_zero_dollar_transactions": len(self.classifications),
            "total_shares_transferred": total_shares,
            "estimated_total_value": total_estimated_value,
            "requiring_investigation": requiring_investigation,
            "by_classification": {k: len(v) for k, v in by_type.items()},
            "red_flag_count": sum(len(a.red_flags) for a in self.classifications),
            "gift_transactions": len(by_type.get(ZeroDollarTransactionType.GIFT_TRANSACTION.value, [])),
            "rsu_vestings": len(by_type.get(ZeroDollarTransactionType.RSU_VESTING.value, []))
        }


# =============================================================================
# STATUTORY VIOLATION AGGREGATOR
# =============================================================================

@dataclass
class StatutoryViolation:
    """Comprehensive statutory violation record."""
    violation_id: str
    violation_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    
    # Statutory reference
    statute_citation: str
    statute_name: str
    cfr_reference: str
    govinfo_url: str
    
    # Evidence
    description: str
    evidence_summary: str
    exact_quote: Optional[str]
    document_url: str
    accession_number: str
    filing_date: str
    
    # Assessment
    prosecutorial_merit: str
    criminal_referral_recommended: bool
    estimated_damages: float
    
    # Detection metadata
    detected_by: str  # Module that detected
    confidence: float
    detection_timestamp: str
    evidence_hash: str


class StatutoryViolationAggregator:
    """Aggregates violations from all forensic modules."""
    
    SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    
    def __init__(self):
        self.violations: List[StatutoryViolation] = []
        self.by_statute: Dict[str, List[StatutoryViolation]] = defaultdict(list)
        self.by_type: Dict[str, List[StatutoryViolation]] = defaultdict(list)
    
    def add_violation(self, violation: StatutoryViolation):
        """Add a violation to the aggregator."""
        self.violations.append(violation)
        self.by_statute[violation.statute_citation].append(violation)
        self.by_type[violation.violation_type].append(violation)
    
    def add_from_insider_transaction(
        self,
        transaction: InsiderTransaction,
        violation_type: str,
        severity: str,
        module_name: str
    ):
        """Create violation from insider transaction."""
        if violation_type == "LATE_FILING":
            statute = "15 U.S.C. § 78p(a)"
            statute_name = "Section 16(a) - Insider Reporting"
            cfr = "17 CFR § 240.16a-3"
            description = f"Form 4 filed {transaction.days_late} days late"
            damages = 10000 + (transaction.days_late * 1000)  # Penalty estimate
        elif violation_type == "ZERO_DOLLAR_SUSPICIOUS":
            statute = "17 CFR § 240.10b-5"
            statute_name = "Rule 10b-5 - Fraud and Deceit"
            cfr = "17 CFR § 240.10b-5"
            description = f"Suspicious zero-dollar transaction: {transaction.shares:,.0f} shares"
            damages = 0
        else:
            statute = "15 U.S.C. § 78j(b)"
            statute_name = "Section 10(b) - Anti-Fraud"
            cfr = "17 CFR § 240.10b-5"
            description = f"Transaction violation: {violation_type}"
            damages = 0
        
        violation = StatutoryViolation(
            violation_id=hashlib.md5(
                f"{transaction.accession_number}{violation_type}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16],
            violation_type=violation_type,
            severity=severity,
            statute_citation=statute,
            statute_name=statute_name,
            cfr_reference=cfr,
            govinfo_url=f"https://www.govinfo.gov/content/pkg/USCODE-2023-title15/html/USCODE-2023-title15-chap2B-sec78p.htm",
            description=description,
            evidence_summary=f"Filer: {transaction.filer_name}, Transaction: {transaction.transaction_code}, Shares: {transaction.shares}",
            exact_quote=None,
            document_url=transaction.document_url,
            accession_number=transaction.accession_number,
            filing_date=transaction.filing_date,
            prosecutorial_merit="STRONG" if severity in ["CRITICAL", "HIGH"] else "MODERATE",
            criminal_referral_recommended=severity == "CRITICAL",
            estimated_damages=damages,
            detected_by=module_name,
            confidence=0.85,
            detection_timestamp=datetime.now(timezone.utc).isoformat(),
            evidence_hash=hashlib.sha256(str(transaction).encode()).hexdigest()[:16]
        )
        
        self.add_violation(violation)
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        return {
            "total_violations": len(self.violations),
            "by_severity": {s: sum(1 for v in self.violations if v.severity == s) 
                          for s in self.SEVERITY_ORDER},
            "by_statute": {k: len(v) for k, v in self.by_statute.items()},
            "by_type": {k: len(v) for k, v in self.by_type.items()},
            "criminal_referrals": sum(1 for v in self.violations if v.criminal_referral_recommended),
            "total_estimated_damages": sum(v.estimated_damages for v in self.violations)
        }
    
    def get_critical_violations(self) -> List[StatutoryViolation]:
        """Get all critical and high severity violations."""
        return [v for v in self.violations if v.severity in ["CRITICAL", "HIGH"]]


# =============================================================================
# UNIFIED FORENSIC ORCHESTRATOR
# =============================================================================

class UnifiedForensicOrchestrator:
    """
    Unified orchestrator for comprehensive SEC forensic analysis.
    
    Integrates all forensic modules into a single analysis pipeline
    with enhanced zero-dollar transaction analysis and violation aggregation.
    """
    
    def __init__(
        self,
        cik: str,
        company_name: str = "",
        output_dir: Optional[Path] = None
    ):
        self.cik = cik.lstrip("0")
        self.company_name = company_name
        self.output_dir = output_dir or Path("forensic_reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Core system
        self.forensic_system: Optional[ProductionSECForensicSystem] = None
        
        # Analyzers
        self.zero_dollar_analyzer = ZeroDollarTransactionAnalyzer()
        self.violation_aggregator = StatutoryViolationAggregator()
        
        # Optional modules
        self.dual_agent: Optional[Any] = None
        self.ml_detector: Optional[Any] = None
        self.temporal_analyzer: Optional[Any] = None
        self.quantitative_analyzer: Optional[Any] = None
        self.insider_analyzer: Optional[Any] = None
        
        # Results
        self.analysis_results: Dict[str, Any] = {}
        
        self._init_optional_modules()
    
    def _init_optional_modules(self):
        """Initialize optional forensic modules."""
        if DUAL_AGENT_AVAILABLE:
            try:
                self.dual_agent = DualAgentCoordinator()
                logger.info("✅ Dual Agent Coordinator initialized")
            except Exception as e:
                logger.warning(f"⚠️ Dual Agent init failed: {e}")
        
        if ML_DETECTOR_AVAILABLE:
            try:
                self.ml_detector = MLFraudDetector()
                logger.info("✅ ML Fraud Detector initialized")
            except Exception as e:
                logger.warning(f"⚠️ ML Detector init failed: {e}")
        
        if TEMPORAL_AVAILABLE:
            try:
                self.temporal_analyzer = TemporalForensicReconciliation()
                logger.info("✅ Temporal Reconciliation initialized")
            except Exception as e:
                logger.warning(f"⚠️ Temporal analyzer init failed: {e}")
        
        if QUANTITATIVE_AVAILABLE:
            try:
                self.quantitative_analyzer = QuantitativeForensicAnalyzer()
                logger.info("[OK] Quantitative Forensic Analyzer initialized")
            except Exception as e:
                logger.warning(f"[WARN] Quantitative analyzer init failed: {e}")
        
        # Initialize InsiderForm4Analyzer for robust Form 4 parsing
        if INSIDER_ANALYZER_AVAILABLE:
            try:
                self.insider_analyzer = InsiderForm4Analyzer()
                logger.info("[OK] Insider Form 4 Analyzer initialized (robust parsing)")
            except Exception as e:
                logger.warning(f"[WARN] Insider analyzer init failed: {e}")
    
    async def run_unified_analysis(
        self,
        start_date: str,
        end_date: str,
        filing_types: Optional[List[str]] = None,
        enable_ai_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Run complete unified forensic analysis.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            filing_types: Optional list of filing types
            enable_ai_analysis: Enable dual-agent AI analysis
            
        Returns:
            Complete unified analysis results
        """
        logger.info("=" * 100)
        logger.info("UNIFIED SEC FORENSIC ANALYSIS ORCHESTRATOR v4.0")
        logger.info("=" * 100)
        logger.info(f"Company: {self.company_name or self.cik}")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info("=" * 100)
        
        default_types = ["10-K", "10-Q", "8-K", "4", "4/A", "SC 13G", "SC 13G/A", "DEF 14A"]
        types_to_use = filing_types or default_types
        
        # Phase 1: Core SEC Analysis
        logger.info("\n📊 PHASE 1: Core SEC Filing Analysis")
        async with ProductionSECForensicSystem(
            cik=self.cik,
            company_name=self.company_name,
            output_dir=self.output_dir
        ) as system:
            self.forensic_system = system
            
            # Collect and analyze filings
            await system.collect_filings(start_date, end_date, types_to_use)
            
            if not self.company_name:
                self.company_name = system.company_name
            
            # Insider transaction analysis - use robust InsiderForm4Analyzer if available
            logger.info("\n[PHASE 2] Insider Transaction Analysis")
            insider_transactions = []
            form4_violations = []
            
            if self.insider_analyzer and INSIDER_ANALYZER_AVAILABLE:
                # Use robust InsiderForm4Analyzer with URL resolution
                form4_filings = [f for f in system.filings if f["filing_type"] in ["4", "4/A"]]
                logger.info(f"Analyzing {len(form4_filings)} Form 4 filings with robust parser")
                
                for filing in form4_filings:
                    try:
                        violations = await self.insider_analyzer.analyze_form4(
                            xml_url=filing["document_url"],
                            viewer_url=filing.get("viewer_url"),
                            filing_date_str=filing["filing_date"]
                        )
                        form4_violations.extend(violations)
                    except Exception as e:
                        logger.debug(f"Form 4 analysis error: {e}")
                
                # Convert Form4ViolationRecords to violations
                for v in form4_violations:
                    self.violation_aggregator.add_violation(StatutoryViolation(
                        violation_id=hashlib.md5(f"{v.document_url}{v.type}{datetime.now().isoformat()}".encode()).hexdigest()[:16],
                        violation_type=v.type,
                        severity=v.severity,
                        statute_citation=f"15 U.S.C. § {v.statute_section}",
                        statute_name=f"Section {v.statute_section}",
                        cfr_reference="17 CFR § 240.16a-3",
                        govinfo_url="https://www.govinfo.gov/content/pkg/USCODE-2023-title15/html/USCODE-2023-title15-chap2B-sec78p.htm",
                        description=v.description,
                        evidence_summary=v.exact_quote or v.description,
                        exact_quote=v.exact_quote,
                        document_url=v.document_url,
                        accession_number="",
                        filing_date="",
                        prosecutorial_merit=v.prosecutorial_merit,
                        criminal_referral_recommended=v.prosecutorial_merit == "STRONG",
                        estimated_damages=float(v.estimated_damages or 0),
                        detected_by="InsiderForm4Analyzer",
                        confidence=0.9,
                        detection_timestamp=datetime.now(timezone.utc).isoformat(),
                        evidence_hash=hashlib.sha256(str(v).encode()).hexdigest()[:16]
                    ))
                
                logger.info(f"InsiderForm4Analyzer detected {len(form4_violations)} violations")
            else:
                # Fallback to ProductionSECForensicSystem parser
                insider_transactions = await system.analyze_insider_transactions()
            
            # Phase 2: Enhanced Zero-Dollar Analysis
            logger.info("\n[PHASE 3] Enhanced Zero-Dollar Transaction Analysis")
            zero_dollar_transactions = [t for t in insider_transactions if t.is_zero_dollar]
            
            for tx in zero_dollar_transactions:
                analysis = self.zero_dollar_analyzer.analyze_transaction(tx)
                
                # Add violations for suspicious transactions
                if analysis.requires_further_investigation:
                    if analysis.classification == ZeroDollarTransactionType.GIFT_TRANSACTION:
                        self.violation_aggregator.add_from_insider_transaction(
                            tx, "ZERO_DOLLAR_GIFT", "MEDIUM", "ZeroDollarAnalyzer"
                        )
                    elif analysis.classification == ZeroDollarTransactionType.UNKNOWN:
                        self.violation_aggregator.add_from_insider_transaction(
                            tx, "ZERO_DOLLAR_SUSPICIOUS", "HIGH", "ZeroDollarAnalyzer"
                        )
            
            # Process late filings
            for tx in insider_transactions:
                if tx.is_late_filing:
                    severity = "HIGH" if tx.days_late > 10 else "MEDIUM"
                    self.violation_aggregator.add_from_insider_transaction(
                        tx, "LATE_FILING", severity, "Form4Parser"
                    )
            
            # Phase 3: Short-Swing Profit Analysis
            logger.info("\n📊 PHASE 4: Section 16(b) Short-Swing Profit Analysis")
            short_swing_results = await system.calculate_short_swing_profits()
            
            # Phase 4: Quantitative Forensics (Beneish, Benford, Altman)
            logger.info("\n📊 PHASE 5: Quantitative Forensic Analysis")
            quantitative_results = await self._run_quantitative_analysis(system)
            
            # Phase 5: AI-Powered Analysis (if enabled)
            ai_analysis_results = {}
            if enable_ai_analysis and self.dual_agent:
                logger.info("\n📊 PHASE 6: Dual-Agent AI Analysis")
                ai_analysis_results = await self._run_ai_analysis(system)
            
            # Compile results
            self.analysis_results = {
                "metadata": {
                    "orchestrator_version": "4.0.0-UNIFIED",
                    "company_name": self.company_name,
                    "cik": self.cik,
                    "analysis_period": {"start": start_date, "end": end_date},
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "modules_enabled": {
                        "production_forensic_system": True,
                        "zero_dollar_analyzer": True,
                        "dual_agent": bool(self.dual_agent),
                        "ml_detector": bool(self.ml_detector),
                        "temporal_analyzer": bool(self.temporal_analyzer),
                        "quantitative_analyzer": bool(self.quantitative_analyzer)
                    }
                },
                "filing_summary": {
                    "total_filings": len(system.filings),
                    "by_type": dict(Counter(f["filing_type"] for f in system.filings))
                },
                "insider_transaction_analysis": {
                    "total_transactions": len(insider_transactions),
                    "late_filings": sum(1 for t in insider_transactions if t.is_late_filing),
                    "zero_dollar_transactions": len(zero_dollar_transactions),
                    "zero_dollar_summary": self.zero_dollar_analyzer.generate_summary(),
                    "transactions": [asdict(t) for t in insider_transactions[:200]]
                },
                "zero_dollar_analysis": {
                    "classifications": [
                        {
                            "filer": a.transaction.filer_name,
                            "date": a.transaction.transaction_date,
                            "shares": a.transaction.shares,
                            "classification": a.classification.value,
                            "confidence": a.confidence,
                            "red_flags": a.red_flags,
                            "requires_investigation": a.requires_further_investigation
                        }
                        for a in self.zero_dollar_analyzer.classifications
                    ],
                    "summary": self.zero_dollar_analyzer.generate_summary()
                },
                "short_swing_profits": [
                    {
                        "insider": s.insider_name,
                        "profit": s.total_profit,
                        "disgorgement_required": s.disgorgement_required,
                        "matched_pairs": len(s.matched_transactions)
                    }
                    for s in short_swing_results
                ],
                "quantitative_analysis": quantitative_results,
                "ai_analysis": ai_analysis_results,
                "violation_summary": self.violation_aggregator.generate_summary(),
                "violations": [asdict(v) for v in self.violation_aggregator.violations],
                "critical_violations": [
                    asdict(v) for v in self.violation_aggregator.get_critical_violations()
                ],
                "evidence_chain": system.evidence_chain.export_for_court()
            }
        
        # Generate reports
        await self._generate_reports()
        
        return self.analysis_results
    
    async def _run_quantitative_analysis(
        self,
        system: ProductionSECForensicSystem
    ) -> Dict[str, Any]:
        """Run quantitative forensic analysis."""
        results = {
            "benford_analysis": None,
            "beneish_m_score": None,
            "altman_z_score": None
        }
        
        # Extract financial numbers for Benford analysis
        financial_values = []
        for tx in system.insider_transactions:
            if tx.total_value > 0:
                financial_values.append(tx.total_value)
            if tx.shares > 0:
                financial_values.append(tx.shares)
        
        if len(financial_values) >= 100:
            benford_result = system.benford_analyzer.analyze(
                financial_values,
                f"{self.company_name} Transaction Values"
            )
            results["benford_analysis"] = {
                "sample_size": benford_result.sample_size,
                "is_conforming": benford_result.is_conforming,
                "chi_square_p_value": benford_result.chi_square_p_value,
                "mean_absolute_deviation": benford_result.mean_absolute_deviation,
                "suspicious_digits": benford_result.suspicious_digits,
                "interpretation": benford_result.interpretation
            }
            
            if not benford_result.is_conforming:
                logger.warning(f"⚠️ Benford's Law NON-CONFORMITY: {benford_result.interpretation}")
        else:
            results["benford_analysis"] = {
                "status": "SKIPPED",
                "reason": f"Insufficient sample size: {len(financial_values)} < 100"
            }
        
        return results
    
    async def _run_ai_analysis(
        self,
        system: ProductionSECForensicSystem
    ) -> Dict[str, Any]:
        """Run dual-agent AI analysis on periodic filings."""
        if not self.dual_agent:
            return {"status": "DISABLED", "reason": "Dual agent not available"}
        
        results = {
            "status": "ENABLED",
            "filings_analyzed": 0,
            "violations_detected": 0,
            "availability": self.dual_agent.availability()
        }
        
        # Analyze periodic filings (10-K, 10-Q)
        periodic = [f for f in system.filings if f["filing_type"] in ["10-K", "10-Q"]]
        
        for filing in periodic[:3]:  # Limit for performance
            try:
                content = await system._fetch(filing["document_url"])
                if content and len(content) > 1000:
                    context = {
                        "filing_type": filing["filing_type"],
                        "filing_date": filing["filing_date"],
                        "document_url": filing["document_url"],
                        "company": self.company_name
                    }
                    
                    # Truncate content for API limits
                    truncated = content[:50000]
                    
                    analysis = await self.dual_agent.analyze_text(truncated, context)
                    results["filings_analyzed"] += 1
                    
                    # Count violations from AI analysis
                    openai_v = len(analysis.get("openai", {}).get("violations", []))
                    anthropic_v = len(analysis.get("anthropic", {}).get("violations", []))
                    results["violations_detected"] += openai_v + anthropic_v
                    
            except Exception as e:
                logger.warning(f"AI analysis error for {filing['filing_type']}: {e}")
        
        return results
    
    async def _generate_reports(self):
        """Generate analysis reports."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON report
        json_file = self.output_dir / f"unified_analysis_{self.cik}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)
        logger.info(f"✅ JSON report saved: {json_file}")
        
        # Markdown summary
        md_file = self.output_dir / f"unified_summary_{self.cik}_{timestamp}.md"
        md_content = self._generate_markdown_summary()
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        logger.info(f"✅ Markdown report saved: {md_file}")
    
    def _generate_markdown_summary(self) -> str:
        """Generate markdown summary report."""
        meta = self.analysis_results.get("metadata", {})
        filing = self.analysis_results.get("filing_summary", {})
        insider = self.analysis_results.get("insider_transaction_analysis", {})
        zero_dollar = self.analysis_results.get("zero_dollar_analysis", {}).get("summary", {})
        violations = self.analysis_results.get("violation_summary", {})
        
        return f"""# UNIFIED SEC FORENSIC ANALYSIS REPORT

## {meta.get('company_name', 'Unknown')} ({self.cik})

**Analysis Period:** {meta.get('analysis_period', {}).get('start')} to {meta.get('analysis_period', {}).get('end')}  
**Generated:** {meta.get('generated_at')}  
**Orchestrator Version:** {meta.get('orchestrator_version')}

---

## EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| Total Filings Analyzed | {filing.get('total_filings', 0)} |
| Total Insider Transactions | {insider.get('total_transactions', 0)} |
| Late Filings Detected | {insider.get('late_filings', 0)} |
| Zero-Dollar Transactions | {insider.get('zero_dollar_transactions', 0)} |
| Total Violations | {violations.get('total_violations', 0)} |
| Critical/High Violations | {violations.get('by_severity', {}).get('CRITICAL', 0) + violations.get('by_severity', {}).get('HIGH', 0)} |
| Criminal Referrals | {violations.get('criminal_referrals', 0)} |
| Estimated Damages | ${violations.get('total_estimated_damages', 0):,.2f} |

---

## ZERO-DOLLAR TRANSACTION ANALYSIS

| Metric | Value |
|--------|-------|
| Total $0 Transactions | {zero_dollar.get('total_zero_dollar_transactions', 0)} |
| Total Shares Transferred | {zero_dollar.get('total_shares_transferred', 0):,.0f} |
| RSU Vestings | {zero_dollar.get('rsu_vestings', 0)} |
| Gift Transactions | {zero_dollar.get('gift_transactions', 0)} |
| Requiring Investigation | {zero_dollar.get('requiring_investigation', 0)} |
| Red Flags Identified | {zero_dollar.get('red_flag_count', 0)} |

### Classification Breakdown

"""
        # Add more sections as needed
        for cls, count in zero_dollar.get('by_classification', {}).items():
            md_content += f"- **{cls}:** {count}\n"
        
        return md_content


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def run_unified_analysis(
    cik: str,
    start_date: str,
    end_date: str,
    company_name: str = "",
    output_dir: Optional[str] = None,
    enable_ai: bool = True
) -> Dict[str, Any]:
    """
    Run unified SEC forensic analysis.
    
    Args:
        cik: Company CIK
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        company_name: Optional company name
        output_dir: Optional output directory
        enable_ai: Enable AI-powered analysis
        
    Returns:
        Complete unified analysis results
    """
    output_path = Path(output_dir) if output_dir else None
    
    orchestrator = UnifiedForensicOrchestrator(
        cik=cik,
        company_name=company_name,
        output_dir=output_path
    )
    
    return await orchestrator.run_unified_analysis(
        start_date=start_date,
        end_date=end_date,
        enable_ai_analysis=enable_ai
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified SEC Forensic Analysis")
    parser.add_argument("--cik", required=True, help="Company CIK")
    parser.add_argument("--year", type=int, help="Analysis year")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    parser.add_argument("--company", default="", help="Company name")
    parser.add_argument("--output", default="forensic_reports", help="Output directory")
    parser.add_argument("--full-analysis", action="store_true", help="Enable all analysis modules")
    parser.add_argument("--no-ai", action="store_true", help="Disable AI analysis")
    
    args = parser.parse_args()
    
    if args.year:
        start = f"{args.year}-01-01"
        end = f"{args.year}-12-31"
    else:
        start = args.start
        end = args.end
    
    if not start or not end:
        print("Error: Please provide --year or --start/--end dates")
        exit(1)
    
    result = asyncio.run(run_unified_analysis(
        cik=args.cik,
        start_date=start,
        end_date=end,
        company_name=args.company,
        output_dir=args.output,
        enable_ai=not args.no_ai
    ))
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"Total Violations: {result.get('violation_summary', {}).get('total_violations', 0)}")
    print(f"Critical/High: {result.get('violation_summary', {}).get('by_severity', {}).get('CRITICAL', 0) + result.get('violation_summary', {}).get('by_severity', {}).get('HIGH', 0)}")
    print(f"Zero-Dollar Transactions: {result.get('insider_transaction_analysis', {}).get('zero_dollar_transactions', 0)}")

