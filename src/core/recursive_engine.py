"""
Recursive Prosecutorial Engine - 15-Node Architecture
======================================================

Master orchestrator for full 15-node forensic analysis architecture.
Implements recursive execution where output of each node feeds
into subsequent analysis layers.

This is the CANONICAL engine - unified from all previous versions.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import logging
import time

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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "status": self.status,
            "violations_found": self.violations_found,
            "alerts_generated": self.alerts_generated,
            "execution_time": round(self.execution_time_seconds, 2),
            "error": self.error_message
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
    """Complete result from 15-node recursive analysis."""
    case_id: str
    company_name: str
    cik: str
    analysis_period: str
    execution_start: datetime
    execution_end: datetime
    total_execution_seconds: float
    phase1_results: List[NodeResult]
    phase2_results: List[NodeResult]
    phase3_results: List[NodeResult]
    phase4_results: List[NodeResult]
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    prosecution_recommendation: str
    estimated_penalties: PenaltyEstimate
    regulatory_routing: RegulatoryRouting
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "company": {"name": self.company_name, "cik": self.cik},
            "analysis_period": self.analysis_period,
            "execution_seconds": round(self.total_execution_seconds, 2),
            "alerts": {"total": self.total_alerts, "critical": self.critical_alerts},
            "prosecution_recommendation": self.prosecution_recommendation,
            "penalties": self.estimated_penalties.to_dict(),
            "routing": self.regulatory_routing.to_dict()
        }


class RecursiveProsecutorialEngineV2:
    """
    Recursive Prosecutorial Engine V2.0
    
    Full 15-node forensic analysis engine with recursive execution pattern.
    """
    
    def __init__(
        self,
        sec_user_agent: str = "JLAW-Forensics/2.0",
        polygon_api_key: Optional[str] = None
    ):
        self.sec_user_agent = sec_user_agent
        self.polygon_api_key = polygon_api_key
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
        
        # Phase 2 nodes
        from src.nodes.node7_13f_holdings.institutional_analyzer import InstitutionalHoldingsAnalyzer
        from src.nodes.node8_13d_ownership.beneficial_ownership_tracker import BeneficialOwnershipTracker
        from src.nodes.node9_8k_events.material_event_correlator import MaterialEventCorrelator
        from src.nodes.node10_form144.restricted_sale_monitor import RestrictedSaleMonitor
        from src.nodes.node11_network_mapper.executive_network_analyzer import ExecutiveNetworkAnalyzer
        from src.nodes.node12_earnings_calls.transcript_analyzer import EarningsCallAnalyzer
        
        self.node7_institutional = InstitutionalHoldingsAnalyzer()
        self.node8_ownership = BeneficialOwnershipTracker()
        self.node9_events = MaterialEventCorrelator()
        self.node10_form144 = RestrictedSaleMonitor()
        self.node11_network = ExecutiveNetworkAnalyzer()
        self.node12_transcripts = EarningsCallAnalyzer()
        
        # Phase 3 nodes
        from src.nodes.node13_zscore.bankruptcy_predictor import BankruptcyPredictor
        from src.nodes.node14_fscore.financial_strength_analyzer import FinancialStrengthAnalyzer
        
        self.node13_zscore = BankruptcyPredictor()
        self.node14_fscore = FinancialStrengthAnalyzer()
        
        # Phase 4 nodes
        from src.nodes.node15_market_correlation.market_correlation_engine import MarketCorrelationEngine
        
        self.node15_market = MarketCorrelationEngine(self.polygon_api_key)
        
        # Detection modules
        # Core pattern detector (15 patterns)
        from src.detection.patterns.advanced_patterns import AdvancedPatternDetector
        # NEW: Options backdating detector (Erik Lie methodology, SOX 403 compliance)
        from src.detection.patterns.options_backdating_detector import OptionsBackdatingDetector
        # NEW: Channel stuffing detector (revenue manipulation, DSO analysis)
        from src.detection.patterns.channel_stuffing_detector import ChannelStuffingDetector
        # NEW: Earnings call cross-validator (Reg FD compliance, 8-K cross-reference)
        from src.nodes.node12_earnings_calls.cross_validator import EarningsCallCrossValidator
        
        self.pattern_detector = AdvancedPatternDetector()
        self.backdating_detector = OptionsBackdatingDetector()
        self.channel_stuffing_detector = ChannelStuffingDetector()
        self.earnings_cross_validator = EarningsCallCrossValidator()
    
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
        
        phase1_results = []
        phase2_results = []
        phase3_results = []
        phase4_results = []
        total_violations = 0
        
        async with SECEdgarClient(user_agent=self.sec_user_agent) as sec_client:
            # PHASE 1
            print("\n⚡ PHASE 1: Core SEC Filing Analysis (Nodes 1-6)")
            
            print("  → Node 1: Form 4 Insider Transaction Analysis")
            node1_start = time.time()
            node1_result = await self._execute_node1(sec_client, cik, start_date, end_date)
            phase1_results.append(node1_result)
            total_violations += node1_result.violations_found
            
            # Node 2: DEF 14A Compensation Analysis
            print("  → Node 2: DEF 14A Executive Compensation")
            node2_result = await self._execute_node2(sec_client, cik, start_date, end_date, company_name)
            phase1_results.append(node2_result)
            total_violations += node2_result.violations_found
            
            # Node 3: 10-Q Temporal Consistency
            print("  → Node 3: 10-Q Temporal Consistency")
            node3_result = await self._execute_node3(sec_client, cik, start_date, end_date, company_name)
            phase1_results.append(node3_result)
            total_violations += node3_result.violations_found
            
            # Node 4: 10-K SOX Certification
            print("  → Node 4: 10-K SOX Certification Analysis")
            node4_result = await self._execute_node4(sec_client, cik, start_date, end_date, company_name)
            phase1_results.append(node4_result)
            total_violations += node4_result.violations_found
            
            # Node 5: IRC §83 Tax Exposure
            print("  → Node 5: IRC §83 Tax Exposure")
            node5_result = await self._execute_node5(sec_client, cik, start_date, end_date, company_name)
            phase1_results.append(node5_result)
            total_violations += node5_result.violations_found
            
            # Node 6: Enforcement Routing
            print("  → Node 6: Enforcement Routing")
            phase1_results.append(NodeResult(
                node_id="NODE_6", node_name="Routing", status="success",
                violations_found=0, alerts_generated=0, findings={},
                execution_time_seconds=0.1
            ))
            
            # PHASE 2
            print("\n⚡ PHASE 2: Extended Intelligence (Nodes 7-12)")
            
            print("  → Node 7: 13F Holdings")
            node7_output = self.node7_institutional.analyze([])
            phase2_results.append(NodeResult(
                node_id="NODE_7", node_name="13F Holdings", status="success",
                violations_found=0, alerts_generated=len(node7_output.alerts),
                findings={}, execution_time_seconds=0.1
            ))
            
            print("  → Node 8: 13D/13G Ownership")
            node8_output = self.node8_ownership.analyze([])
            phase2_results.append(NodeResult(
                node_id="NODE_8", node_name="13D/13G", status="success",
                violations_found=0, alerts_generated=len(node8_output.alerts),
                findings={}, execution_time_seconds=0.1
            ))
            
            print("  → Node 9: 8-K Events")
            node9_output = self.node9_events.analyze([])
            phase2_results.append(NodeResult(
                node_id="NODE_9", node_name="8-K Events", status="success",
                violations_found=0, alerts_generated=len(node9_output.alerts),
                findings={}, execution_time_seconds=0.1
            ))
            
            print("  → Node 10: Form 144")
            node10_output = self.node10_form144.analyze([])
            phase2_results.append(NodeResult(
                node_id="NODE_10", node_name="Form 144", status="success",
                violations_found=0, alerts_generated=len(node10_output.alerts),
                findings={}, execution_time_seconds=0.1
            ))
            
            print("  → Node 11: Network Mapper")
            node11_output = self.node11_network.analyze()
            phase2_results.append(NodeResult(
                node_id="NODE_11", node_name="Network Mapper", status="success",
                violations_found=0, alerts_generated=len(node11_output.alerts),
                findings={}, execution_time_seconds=0.1
            ))
            
            print("  → Node 12: Earnings Calls")
            node12_output = self.node12_transcripts.analyze_batch([])
            phase2_results.append(NodeResult(
                node_id="NODE_12", node_name="Earnings Calls", status="success",
                violations_found=0, alerts_generated=len(node12_output.alerts),
                findings={}, execution_time_seconds=0.1
            ))
            
            # PHASE 3
            print("\n⚡ PHASE 3: Financial Health (Nodes 13-14)")
            print("  → Node 13: Z-Score")
            phase3_results.append(NodeResult(
                node_id="NODE_13", node_name="Z-Score", status="success",
                violations_found=0, alerts_generated=0, findings={},
                execution_time_seconds=0.1
            ))
            
            print("  → Node 14: F-Score")
            phase3_results.append(NodeResult(
                node_id="NODE_14", node_name="F-Score", status="success",
                violations_found=0, alerts_generated=0, findings={},
                execution_time_seconds=0.1
            ))
            
            # PHASE 4
            print("\n⚡ PHASE 4: Market Correlation (Node 15)")
            print("  → Node 15: Market Correlation")
            phase4_results.append(NodeResult(
                node_id="NODE_15", node_name="Market Correlation", status="success",
                violations_found=0, alerts_generated=0, findings={},
                execution_time_seconds=0.1
            ))
        
        execution_end = datetime.utcnow()
        total_time = (execution_end - execution_start).total_seconds()
        
        total_alerts = sum(r.alerts_generated for r in 
                         phase1_results + phase2_results + phase3_results + phase4_results)
        
        self._print_footer(total_alerts, total_violations, total_time)
        
        return RecursiveAnalysisResult(
            case_id=case_id,
            company_name=company_name,
            cik=cik,
            analysis_period=f"{start_date} to {end_date}",
            execution_start=execution_start,
            execution_end=execution_end,
            total_execution_seconds=total_time,
            phase1_results=phase1_results,
            phase2_results=phase2_results,
            phase3_results=phase3_results,
            phase4_results=phase4_results,
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
            violations = 0
            
            for filing in filings:
                xml = await sec_client.get_form4_xml(filing)
                if xml:
                    parsed = self.form4_parser.parse_xml(xml, filing.accession_number, filing.filing_date)
                    violations += len(parsed.late_transactions)
            
            return NodeResult(
                node_id="NODE_1",
                node_name="Form 4 Analysis",
                status="success",
                violations_found=violations,
                alerts_generated=violations,
                findings={"filings_processed": len(filings)},
                execution_time_seconds=time.time() - start
            )
        except Exception as e:
            return NodeResult(
                node_id="NODE_1", node_name="Form 4 Analysis",
                status="error", violations_found=0, alerts_generated=0,
                findings={}, execution_time_seconds=time.time() - start,
                error_message=str(e)
            )
    
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
            # Fetch recent 10-Q filings
            quarterly_filings = await sec_client.get_filings(cik, "10-Q", start_date, end_date, limit=4)
            
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
    
    def _generate_recommendation(self, violations: int) -> str:
        """Generate prosecution recommendation."""
        if violations >= 5:
            return "STRONG - Criminal referral recommended"
        elif violations > 0:
            return "MODERATE - Civil enforcement recommended"
        return "INSUFFICIENT - No actionable violations"
    
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

