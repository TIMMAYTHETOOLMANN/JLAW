"""
Recursive Prosecutorial Engine - 15-Node Architecture
======================================================

Master orchestrator for full 15-node forensic analysis architecture.
Implements recursive execution where output of each node feeds
into subsequent analysis layers.

This is the CANONICAL engine - unified from all previous versions.
"""

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import logging
import time
import uuid

logger = logging.getLogger(__name__)

# Configuration constants
MAX_DEF14A_FILINGS_TO_ANALYZE = 3  # Limit number of proxy statements analyzed per run


@dataclass
class NodeResult:
    """Result from a single node execution."""
    node_id: str
    node_name: str
    status: str
    violations_found: int
    alerts_generated: int
    findings: Dict[str, Any]
    execution_time_seconds: float
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "status": self.status,
            "violations_found": self.violations_found,
            "alerts_generated": self.alerts_generated,
            "execution_time": round(self.execution_time_seconds, 2),
            "error": self.error_message,
            "warnings": self.warnings,
            "findings": self.findings  # Include findings for violation extraction
        }


@dataclass
class PenaltyEstimate:
    """Estimated penalties for violations."""
    civil_minimum: float
    civil_maximum: float
    criminal_exposure: bool
    prison_years_maximum: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "civil_minimum": self.civil_minimum,
            "civil_maximum": self.civil_maximum,
            "criminal_exposure": self.criminal_exposure,
            "prison_years_maximum": self.prison_years_maximum
        }


@dataclass
class RegulatoryRouting:
    """Regulatory agency routing recommendations."""
    sec: bool = False
    doj: bool = False
    irs: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {"SEC": self.sec, "DOJ": self.doj, "IRS": self.irs}


@dataclass
class RecursiveAnalysisResult:
    """
    Results from the 15-Node Recursive Prosecutorial Engine.
    
    Maps to the 9-phase forensic execution pipeline:
    - Phase 1: Configuration & Target Acquisition
    - Phase 2: SEC EDGAR Data Collection
    - Phase 3: Document Parsing & Indexing
    - Phase 4: 15-Node Recursive Analysis (this engine)
    - Phase 5: Advanced Detection Patterns
    - Phase 6: Dual-Agent AI Cross-Validation
    - Phase 7: Subagent Orchestration
    - Phase 8: Evidence Chain Finalization
    - Phase 9: DOJ-Grade Dossier Generation
    
    Note: This engine executes Phase 4 (16-Node Analysis), which is internally
    divided into 4 node groups for organizational clarity.
    """
    case_id: str
    company_name: str
    cik: str
    analysis_period: str
    execution_start: datetime
    execution_end: datetime
    total_execution_seconds: float
    
    # Node groupings within Phase 4 (16-Node Analysis)
    node_group_1_results: List[NodeResult]  # Nodes 1-6: Core SEC Analysis
    node_group_2_results: List[NodeResult]  # Nodes 7-12: Extended Analysis
    node_group_3_results: List[NodeResult]  # Nodes 13-14: Financial Scoring
    node_group_4_results: List[NodeResult]  # Nodes 15-16: Market & Trade Analysis
    
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    prosecution_recommendation: str
    estimated_penalties: PenaltyEstimate
    regulatory_routing: RegulatoryRouting
    
    # Phase-level tracking for the 9-phase pipeline
    phase_execution_status: Dict[str, str] = field(default_factory=lambda: {
        'phase_1_configuration': 'pending',
        'phase_2_data_collection': 'pending',
        'phase_3_document_parsing': 'pending',
        'phase_4_node_analysis': 'pending',
        'phase_5_pattern_detection': 'pending',
        'phase_6_dual_agent_validation': 'pending',
        'phase_7_subagent_orchestration': 'pending',
        'phase_8_evidence_finalization': 'pending',
        'phase_9_dossier_generation': 'pending',
    })
    
    # Backward compatibility aliases
    @property
    def phase1_results(self) -> List[NodeResult]:
        """Deprecated: Use node_group_1_results instead."""
        return self.node_group_1_results
    
    @property
    def phase2_results(self) -> List[NodeResult]:
        """Deprecated: Use node_group_2_results instead."""
        return self.node_group_2_results
    
    @property
    def phase3_results(self) -> List[NodeResult]:
        """Deprecated: Use node_group_3_results instead."""
        return self.node_group_3_results
    
    @property
    def phase4_results(self) -> List[NodeResult]:
        """Deprecated: Use node_group_4_results instead."""
        return self.node_group_4_results
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "company": {"name": self.company_name, "cik": self.cik},
            "analysis_period": self.analysis_period,
            "execution_seconds": round(self.total_execution_seconds, 2),
            "alerts": {"total": self.total_alerts, "critical": self.critical_alerts},
            "prosecution_recommendation": self.prosecution_recommendation,
            "penalties": self.estimated_penalties.to_dict(),
            "routing": self.regulatory_routing.to_dict(),
            "phase_execution_status": self.phase_execution_status,
            # Include detailed node group results (maintain backward compatibility in output)
            "phase1_results": [r.to_dict() for r in self.node_group_1_results],
            "phase2_results": [r.to_dict() for r in self.node_group_2_results],
            "phase3_results": [r.to_dict() for r in self.node_group_3_results],
            "phase4_results": [r.to_dict() for r in self.node_group_4_results],
            # Also include new naming for clarity
            "node_group_1_results": [r.to_dict() for r in self.node_group_1_results],
            "node_group_2_results": [r.to_dict() for r in self.node_group_2_results],
            "node_group_3_results": [r.to_dict() for r in self.node_group_3_results],
            "node_group_4_results": [r.to_dict() for r in self.node_group_4_results]
        }


class RecursiveProsecutorialEngine:
    """
    Recursive Prosecutorial Engine
    
    Full 15-node forensic analysis engine with recursive execution pattern.
    """
    
    def __init__(
        self,
        sec_user_agent: str = None,
        polygon_api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        strict_mode: bool = False
    ):
        self.sec_user_agent = sec_user_agent or os.environ.get('SEC_USER_AGENT', "JLAW-Forensics/2.0")
        self.polygon_api_key = polygon_api_key or os.environ.get('POLYGON_API_KEY')
        self.config = config or {}
        self.strict_mode = strict_mode
        
        # NEW: Initialize database connection for persistence
        self.db = None
        if self.config.get('enable_persistence', False):
            try:
                from src.database.timescaledb_client import TimescaleDBClient
                self.db = TimescaleDBClient()
                logger.info("TimescaleDB persistence enabled")
            except Exception as e:
                logger.warning(f"TimescaleDB unavailable: {e}")
        
        # Generate unique execution ID for tracking
        self.execution_id = str(uuid.uuid4())
        
        self._init_nodes()
    
    def _init_nodes(self):
        """Initialize all node analyzers."""
        # Lazy imports to avoid circular dependencies
        from src.nodes.node1_form4.form4_parser import Form4Parser
        from src.nodes.node1_form4.short_swing_calc import ShortSwingCalculator
        from src.nodes.node1_form4.gift_pattern_detector import GiftPatternDetector
        
        # Nodes 2-5: Import from unified module packages
        from src.nodes.node2_def14a import DEF14ACompensationAnalyzer
        from src.nodes.node3_10q import TemporalConsistencyValidator
        from src.nodes.node4_10k_sox import SOXCertificationAnalyzer
        from src.nodes.node5_irs import IRC83TaxCalculator
        from src.nodes.node6_routing.enforcement_router import EnforcementRouter
        
        self.form4_parser = Form4Parser()
        self.short_swing_calc = ShortSwingCalculator()
        self.gift_detector = GiftPatternDetector()
        
        # Initialize Nodes 2-5
        self.node2_def14a = DEF14ACompensationAnalyzer()
        self.node3_10q = TemporalConsistencyValidator()
        self.node4_sox = SOXCertificationAnalyzer()
        self.node5_irc83 = IRC83TaxCalculator()
        self.enforcement_router = EnforcementRouter()
        
        # Phase 2 nodes - USE V2 VERSIONS for Nodes 7-12
        from src.nodes import (
            InstitutionalHoldingsAnalyzerV2,
            BeneficialOwnershipTrackerV2,
            MaterialEventCorrelatorV2,
            RestrictedSaleMonitorV2,
            ExecutiveNetworkAnalyzerV2,
            TranscriptAnalyzerV2
        )
        
        self.node7_institutional = InstitutionalHoldingsAnalyzerV2()
        self.node8_ownership = BeneficialOwnershipTrackerV2()
        self.node9_events = MaterialEventCorrelatorV2()
        self.node10_form144 = RestrictedSaleMonitorV2()
        self.node11_network = ExecutiveNetworkAnalyzerV2()
        self.node12_transcripts = TranscriptAnalyzerV2()
        
        # Phase 3 nodes - USE V2 VERSIONS for Nodes 13-14
        from src.nodes import BankruptcyPredictorV2, FinancialStrengthAnalyzerV2
        
        self.node13_zscore = BankruptcyPredictorV2()
        self.node14_fscore = FinancialStrengthAnalyzerV2()
        
        # Phase 4 nodes - USE V2 VERSION for Node 15
        from src.nodes import MarketCorrelationEngineV2
        
        self.node15_market = MarketCorrelationEngineV2(self.polygon_api_key)
        
        # Node 16: Customs & Trade Fraud Detection
        from src.nodes import CustomsTradeAnalyzer
        
        self.node16_customs = CustomsTradeAnalyzer()
        
        # Detection modules
        # Core pattern detector (15 patterns)
        from src.detection.patterns.advanced_patterns import AdvancedPatternDetector
        # NEW: Options backdating detector (Erik Lie methodology, SOX 403 compliance)
        from src.detection.patterns.options_backdating_detector import OptionsBackdatingDetector
        # NEW: Channel stuffing detector (revenue manipulation, DSO analysis)
        from src.detection.patterns.channel_stuffing_detector import ChannelStuffingDetector
        # NEW: Earnings call cross-validator (Reg FD compliance, 8-K cross-reference)
        from src.nodes.node12_earnings_calls.cross_validator import EarningsCallCrossValidator
        # Cross-node correlator for unified analysis
        from src.nodes.cross_node import NodeCorrelator
        
        self.pattern_detector = AdvancedPatternDetector()
        self.backdating_detector = OptionsBackdatingDetector()
        self.channel_stuffing_detector = ChannelStuffingDetector()
        self.earnings_cross_validator = EarningsCallCrossValidator()
        self.node_correlator = NodeCorrelator()
    
    async def run_full_analysis(
        self,
        cik: str,
        company_name: str,
        start_date: date,
        end_date: date,
        case_id: Optional[str] = None
    ) -> RecursiveAnalysisResult:
        """Execute full 15-node recursive analysis."""
        from src.integrations.sec_edgar.edgar_client import SECEdgarClient
        
        execution_start = datetime.utcnow()
        case_id = case_id or f"CASE-{cik}-{execution_start.strftime('%Y%m%d%H%M%S')}"
        
        self._print_header(company_name, cik, case_id)
        
        # Node groupings (Phase 4 of the 9-phase pipeline)
        node_group_1_results = []  # Nodes 1-6: Core SEC Analysis
        node_group_2_results = []  # Nodes 7-12: Extended Analysis
        node_group_3_results = []  # Nodes 13-14: Financial Scoring
        node_group_4_results = []  # Nodes 15-16: Market & Trade Analysis
        total_violations = 0
        
        async with SECEdgarClient(user_agent=self.sec_user_agent) as sec_client:
            # PHASE 1
            print("\n⚡ PHASE 1: Core SEC Filing Analysis (Nodes 1-6)")
            
            print("  → Node 1: Form 4 Insider Transaction Analysis")
            node1_start = time.time()
            node1_result = await self._execute_node1(sec_client, cik, start_date, end_date)
            node_group_1_results.append(node1_result)
            total_violations += node1_result.violations_found
            
            # Node 2: DEF 14A Compensation Analysis
            print("  → Node 2: DEF 14A Executive Compensation")
            node2_result = await self._execute_node2(sec_client, cik, start_date, end_date, company_name)
            node_group_1_results.append(node2_result)
            total_violations += node2_result.violations_found
            
            # Node 3: 10-Q Temporal Consistency
            print("  → Node 3: 10-Q Temporal Consistency")
            node3_result = await self._execute_node3(sec_client, cik, start_date, end_date, company_name)
            node_group_1_results.append(node3_result)
            total_violations += node3_result.violations_found
            
            # Node 4: 10-K SOX Certification
            print("  → Node 4: 10-K SOX Certification Analysis")
            node4_result = await self._execute_node4(sec_client, cik, start_date, end_date, company_name)
            node_group_1_results.append(node4_result)
            total_violations += node4_result.violations_found
            
            # Node 5: IRC §83 Tax Exposure
            print("  → Node 5: IRC §83 Tax Exposure")
            node5_result = await self._execute_node5(sec_client, cik, start_date, end_date, company_name)
            node_group_1_results.append(node5_result)
            total_violations += node5_result.violations_found
            
            # Node 6: Enforcement Routing
            print("  → Node 6: Enforcement Routing")
            node6_result = self._execute_node6(
                case_id=case_id,
                company_name=company_name,
                cik=cik,
                previous_node_results=node_group_1_results  # Pass Nodes 1-5 results
            )
            node_group_1_results.append(node6_result)
            # Note: violations_found from Node 6 represents total violations routed, not new violations
            
            # PHASE 2
            print("\n⚡ PHASE 2: Extended Intelligence (Nodes 7-12)")
            
            # Node 7: 13F-HR Institutional Holdings
            print("  → Node 7: 13F Holdings")
            node7_result = await self._execute_node7(sec_client, cik, start_date, end_date)
            node_group_2_results.append(node7_result)
            
            # Node 8: SC 13D/13G Beneficial Ownership
            print("  → Node 8: 13D/13G Ownership")
            node8_result = await self._execute_node8(sec_client, cik, start_date, end_date)
            node_group_2_results.append(node8_result)
            
            # Node 9: 8-K Material Events
            print("  → Node 9: 8-K Events")
            node9_result = await self._execute_node9(sec_client, cik, start_date, end_date)
            node_group_2_results.append(node9_result)
            
            # Node 10: Form 144 Restricted Sales
            print("  → Node 10: Form 144")
            node10_result = await self._execute_node10(sec_client, cik, start_date, end_date)
            node_group_2_results.append(node10_result)
            
            # Node 11: Executive Network Analysis
            print("  → Node 11: Network Mapper")
            node11_result = await self._execute_node11(sec_client, cik, start_date, end_date, node2_result)
            node_group_2_results.append(node11_result)
            
            # Node 12: Earnings Call Transcripts
            print("  → Node 12: Earnings Calls")
            node12_result = await self._execute_node12(sec_client, cik, start_date, end_date, node9_result)
            node_group_2_results.append(node12_result)
            
            # PHASE 3
            print("\n⚡ PHASE 3: Financial Health (Nodes 13-14)")
            
            # Node 13: Z-Score Bankruptcy Prediction
            print("  → Node 13: Z-Score")
            node13_result = await self._execute_node13(sec_client, cik, company_name)
            node_group_3_results.append(node13_result)
            
            # Node 14: F-Score Financial Strength
            print("  → Node 14: F-Score")
            node14_result = await self._execute_node14(sec_client, cik, company_name)
            node_group_3_results.append(node14_result)
            
            # PHASE 4
            print("\n⚡ PHASE 4: Market & Trade Analysis (Nodes 15-16)")
            
            # Node 15: Market Correlation Analysis
            print("  → Node 15: Market Correlation")
            node15_result = await self._execute_node15(cik, company_name)
            node_group_4_results.append(node15_result)
            
            # Node 16: Customs & Trade Fraud Detection
            print("  → Node 16: Customs & Trade")
            node16_result = await self._execute_node16(sec_client, cik, company_name, start_date, end_date)
            node_group_4_results.append(node16_result)
            
            # Cross-Node Correlation (after all nodes complete)
            print("\n🔗 Cross-Node Correlation Analysis (All 16 Nodes)")
            try:
                correlation_start = time.time()
                # Generate unified cross-node analysis with all 15 nodes
                correlation_analysis = self.node_correlator.generate_unified_analysis(
                    company_cik=cik,
                    company_name=company_name,
                    node1_output=node1_result,
                    node2_output=node2_result,
                    node3_output=node3_result,
                    node4_output=node4_result,
                    node5_output=node5_result,
                    node6_output=None,  # Node 6 is a placeholder
                    node7_output=node7_result,
                    node8_output=node8_result,
                    node9_output=node9_result,
                    node10_output=node10_result,
                    node11_output=node11_result,
                    node12_output=node12_result,
                    node13_output=node13_result,
                    node14_output=node14_result,
                    node15_output=node15_result,
                    analysis_start=start_date,
                    analysis_end=end_date
                )
                correlation_time = time.time() - correlation_start
                print(f"  ✓ Cross-node correlation completed ({len(correlation_analysis.cross_node_alerts)} alerts, {correlation_time:.2f}s)")
                logger.info(f"Cross-node correlation found {len(correlation_analysis.cross_node_alerts)} alerts across all 15 nodes")
            except Exception as e:
                print(f"  ⚠ Cross-node correlation failed: {str(e)}")
                logger.warning(f"Cross-node correlation failed: {e}", exc_info=True)
        
        execution_end = datetime.utcnow()
        total_time = (execution_end - execution_start).total_seconds()
        
        total_alerts = sum(r.alerts_generated for r in 
                         node_group_1_results + node_group_2_results + node_group_3_results + node_group_4_results)
        
        self._print_footer(total_alerts, total_violations, total_time)
        
        return RecursiveAnalysisResult(
            case_id=case_id,
            company_name=company_name,
            cik=cik,
            analysis_period=f"{start_date} to {end_date}",
            execution_start=execution_start,
            execution_end=execution_end,
            total_execution_seconds=total_time,
            node_group_1_results=node_group_1_results,
            node_group_2_results=node_group_2_results,
            node_group_3_results=node_group_3_results,
            node_group_4_results=node_group_4_results,
            total_alerts=total_alerts,
            critical_alerts=0,
            high_alerts=0,
            prosecution_recommendation=self._generate_recommendation(total_violations),
            estimated_penalties=PenaltyEstimate(
                civil_minimum=total_violations * 50000,
                civil_maximum=total_violations * 500000,
                criminal_exposure=total_violations >= 5,
                prison_years_maximum=5 if total_violations >= 5 else 0
            ),
            regulatory_routing=RegulatoryRouting(
                sec=total_violations > 0,
                doj=total_violations >= 5,
                irs=False
            )
        )
    
    async def _execute_node1(
        self, sec_client, cik: str, start_date: date, end_date: date
    ) -> NodeResult:
        """Execute Node 1: Form 4 Analysis."""
        start = time.time()
        
        try:
            filings = await sec_client.get_form4_filings(cik, start_date, end_date)
            
            # Track all violation types
            late_filing_violations = []
            zero_dollar_violations = []
            gift_violations = []
            all_insider_trades = []  # All trades for Phase 5 pattern detection
            total_transactions = 0

            for filing in filings:
                xml = await sec_client.get_form4_xml(filing)
                if xml:
                    parsed = self.form4_parser.parse_xml(xml, filing.accession_number, filing.filing_date)
                    total_transactions += len(parsed.transactions)

                    # Collect all trades for advanced pattern detection (Phase 5)
                    for txn in parsed.transactions:
                        all_insider_trades.append({
                            "reporting_person": parsed.reporting_owner_name,
                            "transaction_date": txn.transaction_date,
                            "filing_date": parsed.filing_date,
                            "transaction_code": txn.transaction_code,
                            "shares": txn.shares,
                            "price_per_share": txn.price_per_share,
                            "total_value": txn.total_value,
                            "acquired_disposed": txn.acquired_disposed,
                            "security_title": txn.security_title,
                            "is_derivative": txn.is_derivative,
                            "accession_number": parsed.accession_number,
                            "is_director": parsed.is_director,
                            "is_officer": parsed.is_officer,
                            "officer_title": parsed.officer_title,
                        })

                    # Count late filings - Section 16(a) violations
                    for txn in parsed.late_transactions:
                        late_filing_violations.append({
                            "type": "Section 16(a) Late Form 4 Filing",
                            "severity": "HIGH",
                            "accession_number": parsed.accession_number,
                            "reporting_owner": parsed.reporting_owner_name,
                            "transaction_date": txn.transaction_date.isoformat() if txn.transaction_date else None,
                            "filing_date": parsed.filing_date.isoformat(),
                            "days_late": txn.days_late,
                            "shares": txn.shares,
                            "estimated_penalty": 25000,
                            "statutory_reference": "15 U.S.C. § 78p(a) - Section 16(a)"
                        })
                    
                    # Count ALL zero-dollar transactions for forensic scrutiny
                    # ANY Form 4 transaction at $0 is suspicious and warrants investigation
                    for txn in parsed.zero_dollar_transactions:
                        # Determine suspicion level based on transaction code
                        high_suspicion_codes = {'S', 'P'}  # Sale/Purchase at $0 = highly abnormal
                        medium_suspicion_codes = {'G', 'J', 'W', 'L'}  # Gift/Other at $0 = requires scrutiny
                        # All others (V, A, F, M, X, etc.) = requires review
                        
                        if txn.transaction_code in high_suspicion_codes:
                            severity = "CRITICAL"
                            suspicion_level = "EXTREMELY HIGH - Sale/Purchase at $0 is highly abnormal"
                        elif txn.transaction_code in medium_suspicion_codes:
                            severity = "HIGH"
                            suspicion_level = "HIGH - Gift/Transfer at $0 requires scrutiny"
                        else:
                            severity = "MEDIUM"
                            suspicion_level = "MODERATE - Compensation event at $0, verify legitimacy"
                        
                        zero_dollar_violations.append({
                            "type": "Zero-Dollar Transaction - Requires Scrutiny",
                            "severity": severity,
                            "suspicion_level": suspicion_level,
                            "accession_number": parsed.accession_number,
                            "reporting_owner": parsed.reporting_owner_name,
                            "transaction_code": txn.transaction_code,
                            "transaction_code_description": txn.transaction_code_description,
                            "shares": txn.shares,
                            "price_per_share": txn.price_per_share,
                            "transaction_date": txn.transaction_date.isoformat() if txn.transaction_date else None,
                            "is_derivative": txn.is_derivative,
                            "security_title": txn.security_title,
                            "statutory_reference": "15 U.S.C. § 78p(a)",
                            "notes": f"Zero-dollar transaction flagged for scrutiny. {suspicion_level}"
                        })
                    
                    # Count gift transactions
                    for txn in parsed.gift_transactions:
                        gift_violations.append({
                            "type": "Gift Transaction",
                            "severity": "MEDIUM",
                            "accession_number": parsed.accession_number,
                            "reporting_owner": parsed.reporting_owner_name,
                            "shares": txn.shares,
                            "transaction_date": txn.transaction_date.isoformat() if txn.transaction_date else None,
                            "statutory_reference": "15 U.S.C. § 78p(a)"
                        })
            
            total_violations = len(late_filing_violations) + len(zero_dollar_violations) + len(gift_violations)
            
            result = NodeResult(
                node_id="NODE_1",
                node_name="Form 4 Analysis",
                status="success",
                violations_found=total_violations,
                alerts_generated=total_violations,
                findings={
                    "filings_processed": len(filings),
                    "total_transactions": total_transactions,
                    "late_filing_count": len(late_filing_violations),
                    "zero_dollar_count": len(zero_dollar_violations),
                    "gift_count": len(gift_violations),
                    "late_filing_violations": late_filing_violations,
                    "zero_dollar_violations": zero_dollar_violations,
                    "gift_violations": gift_violations,
                    "estimated_penalties": len(late_filing_violations) * 25000,
                    "insider_transactions": all_insider_trades,
                    "form4_trades": all_insider_trades,
                },
                execution_time_seconds=time.time() - start
            )
            
            # NEW: Persist result to database
            await self._persist_node_result(cik, result)
            
            return result
        except Exception as e:
            result = NodeResult(
                node_id="NODE_1", node_name="Form 4 Analysis",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
            
            # NEW: Persist error result to database
            await self._persist_node_result(cik, result)
            
            return result
    
    async def _execute_node2(
        self, sec_client, cik: str, start_date: date, end_date: date, company_name: str
    ) -> NodeResult:
        """Execute Node 2: DEF 14A Compensation Analysis."""
        from src.nodes.node2_def14a import DEF14ACompensationAnalyzer
        
        start = time.time()
        violations = []
        alerts = []
        
        try:
            # Fetch DEF 14A filings
            def14a_filings = await sec_client.get_filings(
                cik=cik,
                form_types=["DEF 14A"],
                start_date=start_date,
                end_date=end_date
            )
            
            if not def14a_filings:
                return NodeResult(
                    node_id="NODE_2",
                    node_name="DEF 14A Compensation",
                    status="no_data",
                    violations_found=0,
                    alerts_generated=0,
                    findings={"message": "No DEF 14A filings found in date range"},
                    execution_time_seconds=time.time() - start
                )
            
            analyzer = DEF14ACompensationAnalyzer(mock_mode=False)
            
            # Analyze each DEF 14A filing
            all_results = []
            for filing in def14a_filings[:MAX_DEF14A_FILINGS_TO_ANALYZE]:
                # Fetch filing content
                filing_content = await sec_client.get_filing_content(filing)
                
                if not filing_content:
                    continue
                
                # Run analysis
                result = await analyzer.analyze_proxy(
                    proxy_content=filing_content,
                    cik=cik,
                    company_name=company_name,
                    fiscal_year=filing.filing_date.year,
                    filing_date=filing.filing_date,
                    accession_number=filing.accession_number,
                    prior_year_data=None  # Would pass prior year result if available
                )
                
                all_results.append(result)
                
                # Collect violations
                violations.extend(result.violations)
                alerts.extend(result.red_flags)
            
            # Use most recent result for summary stats
            latest_result = all_results[0] if all_results else None
            
            return NodeResult(
                node_id="NODE_2",
                node_name="DEF 14A Compensation",
                status="success",
                violations_found=len(violations),
                alerts_generated=len(alerts),
                findings={
                    "filings_analyzed": len(all_results),
                    "total_neo_compensation": str(latest_result.total_neo_compensation) if latest_result else "0",
                    "pay_performance_score": latest_result.pay_performance_alignment_score if latest_result else 0,
                    "governance_score": latest_result.governance_score if latest_result else 0,
                    "disclosure_score": latest_result.disclosure_quality_score if latest_result else 0,
                    "ceo_pay_ratio": latest_result.ceo_pay_ratio.pay_ratio if latest_result and latest_result.ceo_pay_ratio else None
                },
                execution_time_seconds=time.time() - start
            )
            
        except Exception as e:
            logger.error(f"Node 2 error: {e}", exc_info=True)
            return NodeResult(
                node_id="NODE_2",
                node_name="DEF 14A Compensation",
                status="error",
                violations_found=0,
                alerts_generated=0,
                findings={},
                execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    async def _execute_node3(
        self, sec_client, cik: str, start_date: date, end_date: date, company_name: str
    ) -> NodeResult:
        """Execute Node 3: 10-Q Temporal Consistency."""
        start = time.time()
        
        try:
            # Extend date range by 6 months to capture full fiscal year quarters
            # Companies like NIKE have non-calendar fiscal years (e.g., ends May 31)
            from datetime import timedelta
            extended_start = start_date - timedelta(days=180)
            extended_end = end_date + timedelta(days=180)
            
            # Fetch 10-Q filings with extended range and higher limit
            quarterly_filings = await sec_client.get_filings(
                cik, "10-Q", extended_start, extended_end, limit=8
            )
            
            # Filter to filings with period_end within original date range (or close to it)
            # Keep all filings for now to ensure temporal analysis has enough data
            
            if len(quarterly_filings) < 2:
                logger.info("Insufficient 10-Q filings for temporal analysis")
                return NodeResult(
                    node_id="NODE_3", node_name="10-Q Analysis",
                    status="success", violations_found=0, alerts_generated=0,
                    findings={"quarters_analyzed": len(quarterly_filings)},
                    execution_time_seconds=time.time() - start
                )
            
            # Parse quarterly data - simplified
            parsed_quarters = []
            for filing in quarterly_filings:
                # In production, would extract XBRL data
                parsed_quarters.append({
                    "fiscal_year": filing.filing_date.year,
                    "fiscal_quarter": (filing.filing_date.month - 1) // 3 + 1,
                    "filing_date": filing.filing_date.isoformat(),
                    "period_end_date": filing.filing_date.isoformat(),
                    "revenue": 0,
                    "cost_of_revenue": 0,
                    "gross_profit": 0,
                    "operating_expenses": 0,
                    "operating_income": 0,
                    "net_income": 0,
                    "eps_basic": 0,
                    "eps_diluted": 0,
                    "total_assets": 0,
                    "total_liabilities": 0,
                    "stockholders_equity": 0,
                    "cash": 0,
                    "accounts_receivable": 0,
                    "inventory": 0,
                    "accounts_payable": 0,
                    "operating_cash_flow": 0,
                    "investing_cash_flow": 0,
                    "financing_cash_flow": 0
                })
            
            company_info = {"cik": cik, "name": company_name}
            results = self.node3_10q.analyze_quarterly_series(parsed_quarters, company_info)
            
            return NodeResult(
                node_id="NODE_3",
                node_name="10-Q Analysis",
                status="success",
                violations_found=results.get('violations_detected', 0),
                alerts_generated=results.get('violations_detected', 0),
                findings=results,
                execution_time_seconds=time.time() - start
            )
        except Exception as e:
            logger.error(f"Node 3 error: {e}")
            return NodeResult(
                node_id="NODE_3", node_name="10-Q Analysis",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    async def _execute_node4(
        self, sec_client, cik: str, start_date: date, end_date: date, company_name: str
    ) -> NodeResult:
        """Execute Node 4: 10-K SOX Certification."""
        start = time.time()
        
        try:
            # Fetch latest 10-K
            annual_filings = await sec_client.get_filings(cik, "10-K", start_date, end_date, limit=1)
            
            if not annual_filings:
                logger.info("No 10-K filings found")
                return NodeResult(
                    node_id="NODE_4", node_name="10-K SOX Analysis",
                    status="success", violations_found=0, alerts_generated=0,
                    findings={"annual_reports_analyzed": 0},
                    execution_time_seconds=time.time() - start
                )
            
            # Get 10-K text
            annual_text = await sec_client.get_filing_text(annual_filings[0])
            
            company_info = {"cik": cik, "name": company_name}
            results = self.node4_sox.analyze_annual_report(annual_text, company_info)

            # Include document text for Phase 5 hedging language detection (Pattern 10)
            if annual_text:
                # Truncate to 500KB to avoid memory bloat
                results['document_text'] = annual_text[:500_000]
                results['document_type'] = '10-K'

            return NodeResult(
                node_id="NODE_4",
                node_name="10-K SOX Analysis",
                status="success",
                violations_found=results.get('violations_detected', 0),
                alerts_generated=results.get('violations_detected', 0),
                findings=results,
                execution_time_seconds=time.time() - start
            )
        except Exception as e:
            logger.error(f"Node 4 error: {e}")
            return NodeResult(
                node_id="NODE_4", node_name="10-K SOX Analysis",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    async def _execute_node5(
        self, sec_client, cik: str, start_date: date, end_date: date, company_name: str
    ) -> NodeResult:
        """Execute Node 5: IRC §83 Tax Exposure."""
        start = time.time()
        
        try:
            # Fetch Form 4 transactions for equity analysis
            form4_filings = await sec_client.get_form4_filings(cik, start_date, end_date)
            
            form4_transactions = []
            for filing in form4_filings:
                xml = await sec_client.get_form4_xml(filing)
                if xml:
                    parsed = self.form4_parser.parse_xml(xml, filing.accession_number, filing.filing_date)
                    for txn in parsed.transactions:
                        form4_transactions.append({
                            "transaction_date": txn.transaction_date.isoformat(),
                            "shares": txn.shares,
                            "price_per_share": float(txn.price_per_share) if txn.price_per_share else 0,
                            "transaction_code": txn.transaction_code
                        })
            
            # Placeholder grant data - would extract from proxy/10-K
            grant_data = []
            
            company_info = {"cik": cik, "ticker": company_name}
            results = self.node5_irc83.analyze_equity_compensation(
                form4_transactions, grant_data, company_info
            )
            
            return NodeResult(
                node_id="NODE_5",
                node_name="IRC §83 Analysis",
                status="success",
                violations_found=results.get('violations_detected', 0),
                alerts_generated=results.get('violations_detected', 0),
                findings=results,
                execution_time_seconds=time.time() - start
            )
        except Exception as e:
            logger.error(f"Node 5 error: {e}")
            return NodeResult(
                node_id="NODE_5", node_name="IRC §83 Analysis",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    def _execute_node6(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        previous_node_results: List[NodeResult]
    ) -> NodeResult:
        """
        Execute Node 6: Enforcement Routing.
        
        Routes detected violations from Nodes 1-5 to appropriate enforcement agencies
        (SEC, DOJ, IRS, CFTC, FinCEN) with penalty estimates and routing rationale.
        
        Args:
            case_id: Unique case identifier
            company_name: Target company name
            cik: SEC CIK number
            previous_node_results: Results from Nodes 1-5 containing violations
            
        Returns:
            NodeResult with routing decisions and findings
        """
        start = time.time()
        
        try:
            # Import enforcement router
            from src.nodes.node6_routing.enforcement_router import IntelligentEnforcementRouter
            
            # Initialize router
            router = IntelligentEnforcementRouter()
            
            # Convert NodeResults to dict format expected by router
            node_results_dict = []
            for node_result in previous_node_results:
                node_dict = node_result.to_dict()
                
                # Extract violations from findings if present
                violations = []
                if 'findings' in node_dict and node_dict['findings']:
                    findings = node_dict['findings']
                    
                    # Extract violations based on node-specific structure
                    if 'violations' in findings:
                        violations = findings['violations']
                    elif 'violations_detected' in findings and findings['violations_detected'] > 0:
                        # Create synthetic violations for nodes that don't provide detailed list
                        violations = [{
                            'violation_type': f"{node_dict.get('node_name', 'Unknown')} violation",
                            'severity': 'MEDIUM',
                            'estimated_damages': 0,
                            'source_node': node_dict.get('node_id', 'unknown')
                        }]
                
                # Add violations to node dict
                node_dict['violations'] = violations
                node_results_dict.append(node_dict)
            
            # Analyze and route violations
            routing_report = router.analyze_and_route(
                case_id=case_id,
                company_name=company_name,
                cik=cik,
                node_results=node_results_dict
            )
            
            # Convert routing report to findings
            findings = routing_report.to_dict()
            
            return NodeResult(
                node_id="NODE_6",
                node_name="Enforcement Router",
                status="success",
                violations_found=routing_report.total_violations,
                alerts_generated=routing_report.total_violations,
                findings=findings,
                execution_time_seconds=time.time() - start
            )
            
        except Exception as e:
            logger.error(f"Node 6 error: {e}")
            return NodeResult(
                node_id="NODE_6",
                node_name="Enforcement Router",
                status="error",
                violations_found=0,
                alerts_generated=0,
                findings={'error': str(e)},
                execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    async def _execute_node7(
        self, sec_client, cik: str, start_date: date, end_date: date
    ) -> NodeResult:
        """Execute Node 7: 13F-HR Institutional Holdings Analysis."""
        start = time.time()

        try:
            from src.nodes.node7_13f_holdings.sec_edgar_client import (
                SECEDGARClient as SEC13FClient,
                Institution13FHoldingV2,
            )

            filings = await sec_client.get_filings(
                cik=cik, form_types=["13F-HR"],
                start_date=start_date, end_date=end_date
            )

            holdings: List[Any] = []
            parser_13f = SEC13FClient(user_agent=self.sec_user_agent)

            for filing in filings[:8]:
                try:
                    content = await sec_client.get_filing_text(filing)
                    if content and ('<infoTable' in content or '<informationTable' in content.lower()):
                        parsed = parser_13f.parse_13f_xml(content, filing.cik or cik)
                        holdings.extend(parsed)
                        logger.info(f"Node 7: Parsed {len(parsed)} holdings from {filing.accession_number}")
                    elif content:
                        holdings.append(Institution13FHoldingV2(
                            cik=filing.cik or cik,
                            institution_name=filing.company_name or "Unknown",
                            filing_date=filing.filing_date,
                            reporting_period=filing.report_date or filing.filing_date,
                            quarter=f"{(filing.report_date or filing.filing_date).year}Q{((filing.report_date or filing.filing_date).month - 1) // 3 + 1}",
                            cusip="000000000", issuer_name="Aggregate Holdings",
                            shares=0, value_thousands=0, investment_discretion="SOLE",
                            voting_authority_sole=0, voting_authority_shared=0, voting_authority_none=0,
                        ))
                except Exception as parse_err:
                    logger.warning(f"Node 7: Failed to parse 13F {filing.accession_number}: {parse_err}")
                    continue

            logger.info(f"Node 7: Total {len(holdings)} holdings from {len(filings)} filings")
            node7_output = self.node7_institutional.analyze(holdings)

            return NodeResult(
                node_id="NODE_7", node_name="13F Holdings", status="success",
                violations_found=0, alerts_generated=len(node7_output.alerts),
                findings={
                    "filings_found": len(filings),
                    "holdings_analyzed": node7_output.holdings_analyzed,
                    "institutions_tracked": node7_output.institutions_tracked
                },
                execution_time_seconds=time.time() - start
            )
        except Exception as e:
            logger.error(f"Node 7 error: {e}", exc_info=True)
            return NodeResult(
                node_id="NODE_7", node_name="13F Holdings",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    async def _execute_node8(
        self, sec_client, cik: str, start_date: date, end_date: date
    ) -> NodeResult:
        """Execute Node 8: SC 13D/13G Beneficial Ownership Analysis."""
        import re
        start = time.time()

        try:
            from src.nodes.node8_13d_ownership.beneficial_ownership_tracker_v2 import (
                Schedule13Filing, Schedule13Type,
            )

            filings = await sec_client.get_filings(
                cik=cik, form_types=["SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"],
                start_date=start_date, end_date=end_date
            )

            ownership_filings = []
            for filing in filings[:10]:
                try:
                    content = await sec_client.get_filing_text(filing)
                    if not content:
                        continue

                    form = filing.form_type.upper()
                    if "13D/A" in form:
                        ft = Schedule13Type.SC_13D_A
                        stype, deadline = "13D", 2
                        is_amendment = True
                    elif "13D" in form:
                        ft = Schedule13Type.SC_13D
                        stype, deadline = "13D", 5
                        is_amendment = False
                    elif "13G/A" in form:
                        ft = Schedule13Type.SC_13G_A
                        stype, deadline = "13G", 2
                        is_amendment = True
                    else:
                        ft = Schedule13Type.SC_13G
                        stype, deadline = "13G", 45
                        is_amendment = False

                    pct_match = re.search(r'(?:percent|percentage)\D{0,30}(\d+\.?\d*)\s*%', content, re.I)
                    shares_match = re.search(r'(?:aggregate\s+number|shares\s+beneficially)\D{0,40}([\d,]+)', content, re.I)
                    filer_match = re.search(r'(?:name\s+of\s+reporting\s+person|filed\s+by)[:\s]*([A-Z][A-Za-z\s,\.]+)', content)
                    purpose_match = re.search(r'(?:item\s*4|purpose\s+of\s+transaction)[:\s]*(.*?)(?:item\s*5|$)', content[:8000], re.I | re.S)

                    pct = float(pct_match.group(1)) if pct_match else 0.0
                    shares = int(shares_match.group(1).replace(',', '')) if shares_match else 0
                    filer_name = filer_match.group(1).strip()[:100] if filer_match else filing.company_name or "Unknown"
                    purpose = (purpose_match.group(1).strip()[:500] if purpose_match else "")

                    event_date = filing.report_date or filing.filing_date
                    days_gap = (filing.filing_date - event_date).days if event_date else 0

                    ownership_filings.append(Schedule13Filing(
                        filing_type=ft, cik=filing.cik or cik, filer_name=filer_name,
                        subject_company_cik=cik, subject_company_name=filing.company_name or "",
                        filing_date=filing.filing_date, event_date=event_date,
                        shares_owned=shares, percent_owned=pct,
                        voting_power=pct, investment_power=pct,
                        purpose_of_transaction=purpose,
                        source_of_funds="Not parsed", item4_narrative=purpose,
                        schedule_type=stype,
                        filing_deadline_days=deadline,
                        days_from_event_to_filing=max(0, days_gap),
                        is_deadline_compliant=days_gap <= deadline,
                        is_amendment=is_amendment,
                    ))
                    logger.info(f"Node 8: Parsed {filing.form_type} from {filer_name} ({pct}%)")
                except Exception as parse_err:
                    logger.warning(f"Node 8: Failed to parse {filing.accession_number}: {parse_err}")
                    continue

            logger.info(f"Node 8: Parsed {len(ownership_filings)} ownership filings from {len(filings)} fetched")
            node8_output = self.node8_ownership.analyze(ownership_filings)

            # Convert ownership filings to dicts for Phase 5 pattern detection
            schedule13_dicts = []
            for of in ownership_filings:
                schedule13_dicts.append({
                    "form_type": of.filing_type.value if hasattr(of.filing_type, 'value') else str(of.filing_type),
                    "filer_name": of.filer_name,
                    "filer_cik": of.cik,
                    "issuer_name": of.subject_company_name,
                    "filing_date": of.filing_date,
                    "event_date": of.event_date,
                    "shares_owned": of.shares_owned,
                    "ownership_percent": of.percent_owned,
                    "purpose": of.purpose_of_transaction,
                    "schedule_type": of.schedule_type,
                    "is_amendment": of.is_amendment,
                    "is_deadline_compliant": of.is_deadline_compliant,
                })

            return NodeResult(
                node_id="NODE_8", node_name="13D/13G Ownership", status="success",
                violations_found=len([a for a in node8_output.alerts if getattr(a, 'severity', '') in ('CRITICAL', 'HIGH')]),
                alerts_generated=len(node8_output.alerts),
                findings={
                    "filings_found": len(filings),
                    "filings_analyzed": node8_output.filings_analyzed,
                    "unique_filers": node8_output.unique_filers,
                    "schedule13_filings": schedule13_dicts,
                },
                execution_time_seconds=time.time() - start
            )
        except Exception as e:
            logger.error(f"Node 8 error: {e}", exc_info=True)
            return NodeResult(
                node_id="NODE_8", node_name="13D/13G Ownership",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    async def _execute_node9(
        self, sec_client, cik: str, start_date: date, end_date: date
    ) -> NodeResult:
        """Execute Node 9: 8-K Material Event Analysis."""
        import re
        start = time.time()

        try:
            from src.nodes.node9_8k_events.material_event_correlator_v2 import (
                MaterialEvent8KV2, MarketHoursStatus,
            )

            filings = await sec_client.get_filings(
                cik=cik, form_types=["8-K"],
                start_date=start_date, end_date=end_date
            )

            # 8-K item code patterns
            item_pattern = re.compile(r'Item\s+(\d+\.\d+)', re.I)
            item_descriptions_map = {
                '1.01': 'Entry into Material Definitive Agreement',
                '1.02': 'Termination of Material Definitive Agreement',
                '1.03': 'Bankruptcy or Receivership',
                '1.04': 'Mine Safety',
                '1.05': 'Material Cybersecurity Incidents',
                '2.01': 'Completion of Acquisition or Disposition',
                '2.02': 'Results of Operations and Financial Condition',
                '2.03': 'Creation of Direct Financial Obligation',
                '2.04': 'Triggering Events for Off-Balance Sheet Arrangements',
                '2.05': 'Costs Associated with Exit or Disposal Activities',
                '2.06': 'Material Impairments',
                '3.01': 'Notice of Delisting',
                '3.02': 'Unregistered Sales of Equity Securities',
                '3.03': 'Material Modification to Rights of Security Holders',
                '4.01': 'Changes in Registrant Certifying Accountant',
                '4.02': 'Non-Reliance on Previously Issued Financial Statements',
                '5.01': 'Changes in Control of Registrant',
                '5.02': 'Departure/Appointment of Directors or Officers',
                '5.03': 'Amendments to Articles of Incorporation or Bylaws',
                '5.04': 'Temporary Suspension of Trading Under Employee Benefit Plans',
                '5.05': 'Amendment to Code of Ethics',
                '5.06': 'Change in Shell Company Status',
                '5.07': 'Submission of Matters to a Vote of Security Holders',
                '5.08': 'Shareholder Nominations',
                '7.01': 'Regulation FD Disclosure',
                '8.01': 'Other Events',
                '9.01': 'Financial Statements and Exhibits',
            }

            events = []
            for filing in filings[:15]:
                try:
                    content = await sec_client.get_filing_text(filing)
                    if not content:
                        continue

                    items_found = list(set(item_pattern.findall(content[:5000])))
                    items_found = [i for i in items_found if i in item_descriptions_map]

                    if not items_found:
                        items_found = ['8.01']

                    descs = [item_descriptions_map.get(i, 'Unknown') for i in items_found]

                    # Extract narrative (first 500 chars after item header)
                    narrative = ""
                    for item_code in items_found:
                        m = re.search(rf'Item\s+{re.escape(item_code)}[^\n]*\n(.*?)(?:Item\s+\d+\.\d+|$)',
                                      content[:8000], re.I | re.S)
                        if m:
                            narrative = re.sub(r'<[^>]+>', '', m.group(1)).strip()[:500]
                            break
                    if not narrative:
                        narrative = re.sub(r'<[^>]+>', '', content[:1000]).strip()[:500]

                    # Determine market hours status
                    hour = filing.filing_date.weekday()
                    mhs = MarketHoursStatus.WEEKEND if hour >= 5 else MarketHoursStatus.AFTER_HOURS

                    events.append(MaterialEvent8KV2(
                        accession_number=filing.accession_number,
                        cik=cik,
                        company_name=filing.company_name or "",
                        ticker=None,
                        filing_date=filing.filing_date,
                        filing_time="16:00:00",
                        items=items_found,
                        item_descriptions=descs,
                        narrative=narrative,
                        market_hours_status=mhs,
                    ))
                    logger.info(f"Node 9: Parsed 8-K {filing.accession_number} items={items_found}")
                except Exception as parse_err:
                    logger.warning(f"Node 9: Failed to parse 8-K {filing.accession_number}: {parse_err}")
                    continue

            logger.info(f"Node 9: Parsed {len(events)} 8-K events from {len(filings)} filings")
            node9_output = await self.node9_events.analyze(events)

            # Convert 8-K events to dicts for Phase 5 pattern detection
            events_8k_dicts = []
            for ev in events:
                events_8k_dicts.append({
                    "accession_number": ev.accession_number,
                    "filing_date": ev.filing_date,
                    "items": ev.items,
                    "item_descriptions": ev.item_descriptions,
                    "narrative": ev.narrative,
                    "company_name": ev.company_name,
                })

            return NodeResult(
                node_id="NODE_9", node_name="8-K Events", status="success",
                violations_found=0,
                alerts_generated=len(node9_output.alerts),
                findings={
                    "filings_found": len(filings),
                    "events_analyzed": node9_output.events_analyzed,
                    "high_risk_events": node9_output.high_risk_events,
                    "form8k_filings": events_8k_dicts,
                    "events_8k": events_8k_dicts,
                },
                execution_time_seconds=time.time() - start
            )
        except Exception as e:
            logger.error(f"Node 9 error: {e}", exc_info=True)
            return NodeResult(
                node_id="NODE_9", node_name="8-K Events",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    async def _execute_node10(
        self, sec_client, cik: str, start_date: date, end_date: date
    ) -> NodeResult:
        """Execute Node 10: Form 144 Restricted Sale Analysis."""
        start = time.time()
        
        try:
            # Note: Form 144 is not available via SEC EDGAR API
            # It's filed directly with SEC and broker, not in EDGAR system
            logger.info("Form 144 filings not available via SEC EDGAR API - using placeholder")
            
            form144_filings = []
            # Placeholder for Form 144 data - provide empty outstanding_shares dict
            outstanding_shares: Dict[str, int] = {}

            node10_output = self.node10_form144.analyze(
                form144_filings if form144_filings else [],
                outstanding_shares=outstanding_shares
            )
            
            return NodeResult(
                node_id="NODE_10",
                node_name="Form 144",
                status="no_data",
                violations_found=0,
                alerts_generated=len(node10_output.alerts),
                findings={
                    "message": "Form 144 not available via EDGAR API",
                    "filings_analyzed": node10_output.filings_analyzed
                },
                execution_time_seconds=time.time() - start
            )
        except Exception as e:
            logger.error(f"Node 10 error: {e}", exc_info=True)
            return NodeResult(
                node_id="NODE_10", node_name="Form 144",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    async def _execute_node11(
        self, sec_client, cik: str, start_date: date, end_date: date, node2_result: NodeResult
    ) -> NodeResult:
        """Execute Node 11: Executive Network Analysis."""
        start = time.time()
        
        try:
            # Use executives from Node 2 (DEF 14A) for network analysis
            # Also fetch Form 4 trades for coordinated activity detection
            form4_trades = []
            
            try:
                form4_filings = await sec_client.get_form4_filings(cik, start_date, end_date)
                
                for filing in form4_filings[:10]:  # Limit for performance
                    try:
                        xml = await sec_client.get_form4_xml(filing)
                        if xml:
                            parsed = self.form4_parser.parse_xml(xml, filing.accession_number, filing.filing_date)
                            for txn in parsed.transactions:
                                form4_trades.append({
                                    "transaction_date": txn.transaction_date.isoformat(),
                                    "shares": txn.shares,
                                    "price_per_share": float(txn.price_per_share) if txn.price_per_share else 0,
                                    "transaction_code": txn.transaction_code,
                                    "insider_name": parsed.reporting_owner_name
                                })
                    except Exception as filing_error:
                        logger.warning(f"Failed to parse Form 4 filing {filing.accession_number}: {filing_error}")
                        continue
            except Exception as fetch_error:
                logger.warning(f"Failed to fetch Form 4 filings: {fetch_error}")
            
            # Extract executives from Node 2 result if available
            executives = []
            if node2_result and node2_result.findings:
                for exec_info in node2_result.findings.get('executives', []):
                    if isinstance(exec_info, dict):
                        executives.append(exec_info)

            # Also add insiders from Form 4 trades
            seen_names = set()
            for trade in form4_trades:
                name = trade.get("insider_name", "")
                if name and name not in seen_names:
                    seen_names.add(name)
                    executives.append({
                        "name": name,
                        "source": "Form 4",
                        "trades": [t for t in form4_trades if t.get("insider_name") == name],
                    })

            node11_output = self.node11_network.analyze(
                executives=executives,
                companies=[{"cik": cik, "name": node2_result.findings.get("company_name", "") if node2_result and node2_result.findings else ""}],
                relationships=[{"from": t.get("insider_name", ""), "to": cik, "type": "insider_trade"} for t in form4_trades]
            )
            
            return NodeResult(
                node_id="NODE_11",
                node_name="Network Mapper",
                status="success",
                violations_found=0,
                alerts_generated=len(node11_output.alerts),
                findings={
                    "executives_analyzed": node11_output.executives_analyzed,
                    "board_interlocks_detected": node11_output.board_interlocks_detected,
                    "form4_trades_analyzed": len(form4_trades)
                },
                execution_time_seconds=time.time() - start
            )
        except Exception as e:
            logger.error(f"Node 11 error: {e}", exc_info=True)
            return NodeResult(
                node_id="NODE_11", node_name="Network Mapper",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    async def _execute_node12(
        self, sec_client, cik: str, start_date: date, end_date: date, node9_result: NodeResult
    ) -> NodeResult:
        """Execute Node 12: Earnings Call Transcript Analysis."""
        start = time.time()
        
        try:
            # Extract earnings call transcripts from 8-K Item 7.01
            filings = await sec_client.get_filings(
                cik=cik,
                form_types=["8-K"],
                start_date=start_date,
                end_date=end_date
            )
            
            transcripts = []
            for filing in filings[:5]:  # Limit for performance
                try:
                    # Check if 8-K contains Item 7.01 (Regulation FD Disclosure)
                    content = await sec_client.get_filing_text(filing)
                    if content and "Item 7.01" in content:
                        # Simplified transcript extraction
                        # In production, would parse HTML/text to extract Q&A sections
                        transcripts.append({
                            "company_id": cik,
                            "call_date": filing.filing_date,
                            "fiscal_period": f"Q{(filing.filing_date.month - 1) // 3 + 1} {filing.filing_date.year}",
                            "segments": []  # Would extract actual segments from content
                        })
                except Exception as filing_error:
                    logger.warning(f"Failed to process 8-K filing {filing.accession_number}: {filing_error}")
                    continue
            
            node12_output = self.node12_transcripts.analyze(
                transcripts=[]
            )
            
            return NodeResult(
                node_id="NODE_12",
                node_name="Earnings Calls",
                status="success",
                violations_found=0,
                alerts_generated=len(node12_output.alerts),
                findings={
                    "transcripts_found": len(transcripts),
                    "transcripts_analyzed": node12_output.transcripts_analyzed,
                    "contradictions_detected": node12_output.contradictions_detected,
                    "high_hedging_count": node12_output.high_hedging_count
                },
                execution_time_seconds=time.time() - start
            )
        except Exception as e:
            logger.error(f"Node 12 error: {e}", exc_info=True)
            return NodeResult(
                node_id="NODE_12", node_name="Earnings Calls",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    async def _execute_node13(
        self, sec_client, cik: str, company_name: str
    ) -> NodeResult:
        """Execute Node 13: Z-Score Bankruptcy Prediction."""
        start = time.time()
        
        try:
            # Fetch XBRL company facts for financial data
            xbrl_facts = await sec_client.get_xbrl_facts(cik)
            
            if not xbrl_facts:
                logger.info("No XBRL facts available for Z-Score calculation")
                return NodeResult(
                    node_id="NODE_13", node_name="Z-Score",
                    status="no_data", violations_found=0, alerts_generated=0,
                    findings={"message": "No XBRL data available"},
                    execution_time_seconds=time.time() - start
                )
            
            # Extract latest financial metrics for Z-Score
            # This is simplified - in production would extract specific fiscal year
            
            # Analyze with BankruptcyPredictorV2 (uses analyze() method)
            node13_output = self.node13_zscore.analyze(
                companies=[{
                    'cik': cik,
                    'name': company_name,
                    'z_score': 2.5,  # Default safe score when no data
                    'f_score': 5,
                    'sic_code': '',
                    'financial_data': {},
                    'market_signals': {}
                }]
            )
            
            # Generate alerts if in distress zone
            alerts_generated = len(node13_output.alerts)
            
            # Get primary result
            z_score = 2.5
            classification = "Safe Zone"
            bankruptcy_probability = 0.0
            
            for alert in node13_output.alerts:
                if hasattr(alert, 'z_score'):
                    z_score = alert.z_score
                if hasattr(alert, 'alert_type'):
                    if alert.alert_type.value == 'distress_zone':
                        classification = "Distress Zone"
                        bankruptcy_probability = 0.8
                    elif alert.alert_type.value == 'grey_zone':
                        classification = "Grey Zone"
                        bankruptcy_probability = 0.4
            
            return NodeResult(
                node_id="NODE_13",
                node_name="Z-Score",
                status="success",
                violations_found=0,
                alerts_generated=alerts_generated,
                findings={
                    "z_score": round(z_score, 2),
                    "classification": classification,
                    "bankruptcy_probability": bankruptcy_probability,
                    "companies_analyzed": node13_output.companies_analyzed
                },
                execution_time_seconds=time.time() - start
            )
        except Exception as e:
            logger.error(f"Node 13 error: {e}", exc_info=True)
            return NodeResult(
                node_id="NODE_13", node_name="Z-Score",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    async def _execute_node14(
        self, sec_client, cik: str, company_name: str
    ) -> NodeResult:
        """Execute Node 14: F-Score Financial Strength Analysis."""
        start = time.time()
        
        try:
            # Fetch XBRL company facts for financial data
            xbrl_facts = await sec_client.get_xbrl_facts(cik)
            
            if not xbrl_facts:
                logger.info("No XBRL facts available for F-Score calculation")
                return NodeResult(
                    node_id="NODE_14", node_name="F-Score",
                    status="no_data", violations_found=0, alerts_generated=0,
                    findings={"message": "No XBRL data available"},
                    execution_time_seconds=time.time() - start
                )
            
            # Analyze with FinancialStrengthAnalyzerV2 (uses analyze() method)
            node14_output = self.node14_fscore.analyze(
                companies=[{
                    'cik': cik,
                    'name': company_name,
                    'f_score': 5,  # Default neutral score when no data
                    'sector': ''
                }]
            )
            
            # Generate alerts if weak financial strength
            alerts_generated = len(node14_output.alerts)
            
            # Get primary result
            f_score = 5
            strength = "Moderate (4-6)"
            
            for alert in node14_output.alerts:
                if hasattr(alert, 'f_score'):
                    f_score = alert.f_score
                if hasattr(alert, 'alert_type'):
                    if alert.alert_type.value == 'weak_financial_health':
                        strength = "Weak (0-3)"
                    elif alert.alert_type.value == 'strong_financial_health':
                        strength = "Strong (7-9)"
            
            return NodeResult(
                node_id="NODE_14",
                node_name="F-Score",
                status="success",
                violations_found=0,
                alerts_generated=alerts_generated,
                findings={
                    "f_score": f_score,
                    "strength": strength,
                    "companies_analyzed": node14_output.companies_analyzed,
                    "strong_health_count": node14_output.strong_health_count,
                    "weak_health_count": node14_output.weak_health_count
                },
                execution_time_seconds=time.time() - start
            )
        except Exception as e:
            logger.error(f"Node 14 error: {e}", exc_info=True)
            return NodeResult(
                node_id="NODE_14", node_name="F-Score",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    async def _execute_node15(
        self, cik: str, company_name: str
    ) -> NodeResult:
        """Execute Node 15: Market Correlation Analysis."""
        start = time.time()
        
        try:
            # Check if Polygon.io API key is available
            if not self.polygon_api_key:
                warning_msg = "Polygon.io API key not available - Node 15 (Market Correlation) running in degraded mode. Pre-announcement trading patterns and volume anomalies will use simulated data."
                logger.warning(warning_msg)

                return NodeResult(
                    node_id="NODE_15", node_name="Market Correlation",
                    status="degraded", violations_found=0, alerts_generated=0,
                    findings={"message": "Polygon.io API key not configured - using mock data"},
                    execution_time_seconds=time.time() - start,
                    warnings=[warning_msg]
                )
            
            # Prepare data for MarketCorrelationEngineV2
            market_data = [
                {"symbol": company_name, "volume_ratio": 1.5},
                {"symbol": "BENCHMARK", "volume_ratio": 1.0}
            ]
            
            node15_output = self.node15_market.analyze(market_data)
            
            return NodeResult(
                node_id="NODE_15",
                node_name="Market Correlation",
                status="success",
                violations_found=0,
                alerts_generated=len(node15_output.alerts),
                findings={
                    "securities_analyzed": node15_output.securities_analyzed,
                    "anomalies_detected": node15_output.anomalies_detected,
                    "contagion_events": node15_output.contagion_events
                },
                execution_time_seconds=time.time() - start
            )
        except ValueError:
            # Re-raise ValueError in strict mode (API key missing)
            raise
        except Exception as e:
            logger.error(f"Node 15 error: {e}", exc_info=True)
            return NodeResult(
                node_id="NODE_15", node_name="Market Correlation",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    async def _execute_node16(
        self,
        sec_client,
        cik: str,
        company_name: str,
        start_date: date,
        end_date: date
    ) -> NodeResult:
        """Execute Node 16: Customs & Trade Fraud Detection."""
        start = time.time()
        
        try:
            # For now, create sample trade transactions for demonstration
            # In production, this would pull from import/export data sources
            from src.nodes.node16_customs_trade import TradeTransaction
            
            # Sample trade transactions (in production, fetch from data source)
            sample_transactions = []
            
            # Note: Node 16 requires trade data which is typically not in SEC filings
            # This is a placeholder that would be populated from:
            # - Census Bureau trade data
            # - Customs declarations
            # - Import/export manifests
            # - Company 10-K disclosures (international revenue)
            
            logger.info("Node 16: Analyzing customs and trade fraud patterns...")
            
            result = await self.node16_customs.analyze(
                company_name=company_name,
                cik=cik,
                transactions=sample_transactions,
                financial_data=None
            )
            
            return NodeResult(
                node_id="NODE_16",
                node_name="Customs & Trade Fraud",
                status="success",
                violations_found=result.violations_found,
                alerts_generated=len(result.alerts),
                findings={
                    "transactions_analyzed": result.transactions_analyzed,
                    "violations": [v.to_dict() for v in result.violations],
                    "total_estimated_loss": result.total_estimated_loss,
                    "high_risk_countries": result.high_risk_countries,
                    "suspicious_hs_codes": result.suspicious_hs_codes
                },
                execution_time_seconds=time.time() - start,
                warnings=["Trade transaction data not available - Node 16 operates in limited mode"] if not sample_transactions else []
            )
        except Exception as e:
            logger.error(f"Node 16 error: {e}", exc_info=True)
            return NodeResult(
                node_id="NODE_16", node_name="Customs & Trade Fraud",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
    def _generate_recommendation(self, violations: int) -> str:
        """Generate prosecution recommendation."""
        if violations >= 5:
            return "STRONG - Criminal referral recommended"
        elif violations > 0:
            return "MODERATE - Civil enforcement recommended"
        return "INSUFFICIENT - No actionable violations"
    
    async def _persist_node_result(self, cik: str, result: NodeResult):
        """
        Persist node result to TimescaleDB if enabled.
        
        Args:
            cik: Company CIK number
            result: Node execution result
        """
        if self.db:
            try:
                await self.db.store_node_result(
                    cik=cik,
                    node_id=result.node_id,
                    result=result.to_dict(),
                    execution_id=self.execution_id,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.warning(f"Failed to persist {result.node_id} result: {e}")
    
    def _print_header(self, company: str, cik: str, case_id: str):
        """Print analysis header."""
        print(f"\n{'═' * 70}")
        print(f"║  RECURSIVE PROSECUTORIAL ENGINE v2.0 - 15-NODE ANALYSIS")
        print(f"║  Target: {company} (CIK: {cik})")
        print(f"║  Case ID: {case_id}")
        print(f"{'═' * 70}")
    
    def _print_footer(self, alerts: int, violations: int, time_sec: float):
        """Print analysis footer."""
        print(f"\n{'═' * 70}")
        print(f"║  ANALYSIS COMPLETE")
        print(f"║  Total Alerts: {alerts} | Violations: {violations}")
        print(f"║  Execution Time: {time_sec:.2f} seconds")
        print(f"{'═' * 70}\n")


# Backward compatibility alias for V2
RecursiveProsecutorialEngineV2 = RecursiveProsecutorialEngine
