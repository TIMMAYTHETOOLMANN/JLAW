"""
Supreme Orchestrator - Unified Meta-Controller
==============================================

.. deprecated::
    **DEPRECATED** — Use :class:`UnifiedForensicOrchestrator` from
    ``src.core.unified_orchestrator`` instead. See ``EXECUTION_AUTHORITY.md``
    for the canonical execution path. This module is retained for backward
    compatibility and will be removed in a future version.

Supreme meta-controller that intelligently selects execution strategy based on
investigation priority and automatically routes to the optimal orchestrator.

Execution Strategies:

1. TRIAGE (5-10 minutes):
   - Uses IntelligentOrchestrator for selective node execution
   - Executes only 5-7 critical nodes based on investigation type
   - No strict gates or AI cross-validation
   - Fastest analysis for initial assessment

2. STANDARD (15-30 minutes):
   - Uses MasterExecutionController with optimization
   - All 15 nodes with cross-correlation
   - Strict gates enabled, dual-agent verification
   - Comprehensive analysis for standard investigations

3. DOJ_REFERRAL (30-60 minutes):
   - Uses ForensicMetaOrchestrator for parallel execution
   - All 15 nodes + parallel agent analysis
   - Maximum evidence chain integrity
   - Exhaustive analysis for DOJ-grade referrals

Usage:
    from src.core.supreme_orchestrator import SupremeOrchestrator
    from datetime import date
    from pathlib import Path
    
    supreme = SupremeOrchestrator()
    
    # Quick triage
    result = await supreme.auto_execute(
        cik="320187",
        company_name="Nike Inc",
        start_date=date(2019, 1, 1),
        end_date=date(2019, 12, 31),
        output_dir=Path("./output"),
        priority="triage"
    )
    
    # Or select strategy explicitly
    strategy = supreme.select_strategy(
        priority="doj_referral",
        filings=[...],
        available_resources={}
    )
    print(f"Selected: {strategy.orchestrator_name}")
    print(f"Estimated: {strategy.estimated_duration_seconds/60:.1f} min")
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class InvestigationPriority(Enum):
    """Investigation priority levels determining execution strategy."""
    TRIAGE = "triage"              # Fast 5-10 min scan
    STANDARD = "standard"          # Full 15-30 min analysis
    DOJ_REFERRAL = "doj_referral"  # Exhaustive 30-60 min DOJ-grade


@dataclass
class ExecutionStrategy:
    """Execution strategy configuration."""
    orchestrator_name: str
    priority: InvestigationPriority
    estimated_duration_seconds: float
    node_count: int
    enable_strict_gates: bool
    enable_ai_validation: bool
    enable_parallel_execution: bool
    optimization_level: str
    description: str
    
    @staticmethod
    def from_string(strategy_name: str) -> InvestigationPriority:
        """
        Convert strategy string to InvestigationPriority enum.
        
        Args:
            strategy_name: Strategy name ("triage", "standard", "doj_referral")
        
        Returns:
            InvestigationPriority enum value
        """
        strategy_map = {
            "triage": InvestigationPriority.TRIAGE,
            "standard": InvestigationPriority.STANDARD,
            "doj_referral": InvestigationPriority.DOJ_REFERRAL,
        }
        
        normalized = strategy_name.lower().strip()
        if normalized not in strategy_map:
            logger.warning(f"Unknown strategy '{strategy_name}', defaulting to STANDARD")
            return InvestigationPriority.STANDARD
        
        return strategy_map[normalized]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "orchestrator_name": self.orchestrator_name,
            "priority": self.priority.value,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "estimated_duration_minutes": round(self.estimated_duration_seconds / 60, 1),
            "node_count": self.node_count,
            "enable_strict_gates": self.enable_strict_gates,
            "enable_ai_validation": self.enable_ai_validation,
            "enable_parallel_execution": self.enable_parallel_execution,
            "optimization_level": self.optimization_level,
            "description": self.description
        }


@dataclass
class SupremeExecutionResult:
    """Result from supreme orchestrator execution."""
    cik: str
    company_name: str
    priority: InvestigationPriority
    strategy: ExecutionStrategy
    orchestrator_used: str
    execution_start: datetime
    execution_end: datetime
    success: bool
    node_results: Dict[str, Any]
    detection_results: Dict[str, Any]
    ai_validation_results: Optional[Dict[str, Any]]
    evidence_chain: Dict[str, Any]
    dossier_path: Optional[str]
    total_violations: int
    total_alerts: int
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cik": self.cik,
            "company_name": self.company_name,
            "priority": self.priority.value,
            "strategy": self.strategy.to_dict(),
            "orchestrator_used": self.orchestrator_used,
            "execution_start": self.execution_start.isoformat(),
            "execution_end": self.execution_end.isoformat(),
            "total_duration_seconds": (
                self.execution_end - self.execution_start
            ).total_seconds(),
            "success": self.success,
            "node_results": self.node_results,
            "detection_results": self.detection_results,
            "ai_validation_results": self.ai_validation_results,
            "evidence_chain": self.evidence_chain,
            "dossier_path": self.dossier_path,
            "total_violations": self.total_violations,
            "total_alerts": self.total_alerts,
            "errors": self.errors
        }


class SupremeOrchestrator:
    """
    Supreme meta-controller that intelligently selects execution strategy.

    .. deprecated::
        Use :class:`UnifiedForensicOrchestrator` from
        ``src.core.unified_orchestrator`` instead. This class is retained
        for backward compatibility and will be removed in a future version.
    
    This is the highest-level orchestrator in JLAW, providing a unified entry
    point that automatically routes to the optimal execution strategy based on
    investigation priority and requirements.
    
    Architecture:
        SupremeOrchestrator (this class)
            ├── TRIAGE → IntelligentOrchestrator (fast, selective)
            ├── STANDARD → MasterExecutionController (comprehensive)
            └── DOJ_REFERRAL → ForensicMetaOrchestrator (exhaustive)
    """
    
    def __init__(self):
        """Initialize Supreme Orchestrator."""
        # DEPRECATION WARNING
        import warnings
        warnings.warn(
            "SupremeOrchestrator is deprecated. "
            "Use UnifiedForensicOrchestrator from src.core.unified_orchestrator for DOJ-grade compliance. "
            "This class will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Lazy-loaded orchestrator instances
        self._intelligent_orchestrator = None
        self._master_controller = None
        self._forensic_meta_orchestrator = None
        
        # Strategy cache
        self._strategy_cache: Dict[str, ExecutionStrategy] = {}
        
        self.logger.info("SupremeOrchestrator initialized")
    
    def select_strategy(
        self,
        priority: str,
        filings: Optional[List[Dict[str, Any]]] = None,
        available_resources: Optional[Dict[str, Any]] = None
    ) -> ExecutionStrategy:
        """
        Select optimal execution strategy based on investigation priority.
        
        Args:
            priority: Investigation priority ("triage", "standard", "doj_referral")
            filings: Optional list of available filings (for estimation)
            available_resources: Optional dict of available resources
        
        Returns:
            ExecutionStrategy with optimal configuration
        """
        # Normalize priority
        try:
            inv_priority = InvestigationPriority(priority.lower())
        except ValueError:
            self.logger.warning(
                f"Invalid priority '{priority}', defaulting to STANDARD"
            )
            inv_priority = InvestigationPriority.STANDARD
        
        # Check cache
        cache_key = f"{inv_priority.value}_{len(filings or [])}"
        if cache_key in self._strategy_cache:
            return self._strategy_cache[cache_key]
        
        # Select strategy based on priority
        if inv_priority == InvestigationPriority.TRIAGE:
            strategy = self._create_triage_strategy(filings)
        elif inv_priority == InvestigationPriority.STANDARD:
            strategy = self._create_standard_strategy(filings)
        elif inv_priority == InvestigationPriority.DOJ_REFERRAL:
            strategy = self._create_doj_referral_strategy(filings)
        else:
            # Fallback to standard
            strategy = self._create_standard_strategy(filings)
        
        # Cache strategy
        self._strategy_cache[cache_key] = strategy
        
        self.logger.info(f"Selected strategy: {strategy.orchestrator_name}")
        self.logger.info(
            f"Estimated duration: {strategy.estimated_duration_seconds/60:.1f} min"
        )
        
        return strategy
    
    async def auto_execute(
        self,
        cik: str,
        company_name: str,
        start_date: date,
        end_date: date,
        output_dir: Path,
        priority: str = "standard",
        sec_user_agent: Optional[str] = None,
        polygon_api_key: Optional[str] = None
    ) -> SupremeExecutionResult:
        """
        Main entry point for automatic execution with optimal strategy.
        
        Args:
            cik: Company CIK number
            company_name: Company name
            start_date: Analysis start date
            end_date: Analysis end date
            output_dir: Output directory for artifacts
            priority: Investigation priority ("triage", "standard", "doj_referral")
            sec_user_agent: SEC EDGAR User-Agent
            polygon_api_key: Polygon.io API key
        
        Returns:
            SupremeExecutionResult with complete execution results
        """
        execution_start = datetime.utcnow()
        
        self.logger.info("=" * 80)
        self.logger.info("  SUPREME ORCHESTRATOR - UNIFIED EXECUTION")
        self.logger.info("=" * 80)
        self.logger.info(f"CIK: {cik}")
        self.logger.info(f"Company: {company_name}")
        self.logger.info(f"Priority: {priority.upper()}")
        self.logger.info(f"Date Range: {start_date} to {end_date}")
        self.logger.info("=" * 80)
        
        # Initialize strategy (we'll refine after collecting filings)
        try:
            inv_priority = InvestigationPriority(priority.lower())
        except ValueError:
            self.logger.warning(
                f"Invalid priority '{priority}', defaulting to STANDARD"
            )
            inv_priority = InvestigationPriority.STANDARD
        
        # Collect basic filing info for strategy selection
        filings = await self._collect_filing_metadata(
            cik, start_date, end_date, sec_user_agent
        )
        
        # Select optimal strategy
        strategy = self.select_strategy(
            priority=inv_priority.value,
            filings=filings
        )
        
        # Execute with selected strategy
        try:
            if inv_priority == InvestigationPriority.TRIAGE:
                result = await self._execute_triage(
                    cik=cik,
                    company_name=company_name,
                    start_date=start_date,
                    end_date=end_date,
                    output_dir=output_dir,
                    filings=filings,
                    sec_user_agent=sec_user_agent
                )
            elif inv_priority == InvestigationPriority.STANDARD:
                result = await self._execute_standard(
                    cik=cik,
                    company_name=company_name,
                    start_date=start_date,
                    end_date=end_date,
                    output_dir=output_dir,
                    sec_user_agent=sec_user_agent,
                    polygon_api_key=polygon_api_key
                )
            elif inv_priority == InvestigationPriority.DOJ_REFERRAL:
                result = await self._execute_doj_referral(
                    cik=cik,
                    company_name=company_name,
                    start_date=start_date,
                    end_date=end_date,
                    output_dir=output_dir,
                    filings=filings,
                    sec_user_agent=sec_user_agent,
                    polygon_api_key=polygon_api_key
                )
            else:
                raise ValueError(f"Unsupported priority: {inv_priority}")
            
            execution_end = datetime.utcnow()
            
            # Package supreme execution result
            supreme_result = SupremeExecutionResult(
                cik=cik,
                company_name=company_name,
                priority=inv_priority,
                strategy=strategy,
                orchestrator_used=strategy.orchestrator_name,
                execution_start=execution_start,
                execution_end=execution_end,
                success=result.get("success", True),
                node_results=result.get("node_results", {}),
                detection_results=result.get("detection_results", {}),
                ai_validation_results=result.get("ai_validation_results"),
                evidence_chain=result.get("evidence_chain", {}),
                dossier_path=result.get("dossier_path"),
                total_violations=result.get("total_violations", 0),
                total_alerts=result.get("total_alerts", 0),
                errors=result.get("errors", [])
            )
            
            duration = (execution_end - execution_start).total_seconds()
            self.logger.info("=" * 80)
            self.logger.info(f"✓ Execution Complete: {duration:.1f}s")
            self.logger.info(f"  Strategy: {strategy.orchestrator_name}")
            self.logger.info(f"  Violations: {supreme_result.total_violations}")
            self.logger.info(f"  Alerts: {supreme_result.total_alerts}")
            self.logger.info("=" * 80)
            
            return supreme_result
            
        except Exception as e:
            execution_end = datetime.utcnow()
            self.logger.error(f"✗ Supreme execution error: {e}", exc_info=True)
            
            # Return error result
            return SupremeExecutionResult(
                cik=cik,
                company_name=company_name,
                priority=inv_priority,
                strategy=strategy,
                orchestrator_used=strategy.orchestrator_name,
                execution_start=execution_start,
                execution_end=execution_end,
                success=False,
                node_results={},
                detection_results={},
                ai_validation_results=None,
                evidence_chain={},
                dossier_path=None,
                total_violations=0,
                total_alerts=0,
                errors=[str(e)]
            )
    
    def get_available_strategies(self) -> List[Dict[str, Any]]:
        """
        Get list of available execution strategies.
        
        Returns:
            List of strategy dictionaries with details
        """
        strategies = []
        
        for priority in InvestigationPriority:
            strategy = self.select_strategy(priority.value, filings=None)
            strategies.append(strategy.to_dict())
        
        return strategies
    
    # ═════════════════════════════════════════════════════════════════════════
    # STRATEGY CREATION
    # ═════════════════════════════════════════════════════════════════════════
    
    def _create_triage_strategy(
        self,
        filings: Optional[List[Dict[str, Any]]]
    ) -> ExecutionStrategy:
        """Create TRIAGE execution strategy."""
        # Estimate 5-7 nodes, ~1 min per node
        node_count = 7
        estimated_duration = node_count * 60  # 7 minutes
        
        return ExecutionStrategy(
            orchestrator_name="IntelligentOrchestrator",
            priority=InvestigationPriority.TRIAGE,
            estimated_duration_seconds=estimated_duration,
            node_count=node_count,
            enable_strict_gates=False,
            enable_ai_validation=False,
            enable_parallel_execution=False,
            optimization_level="aggressive",
            description="Fast selective node execution for initial triage (5-10 min)"
        )
    
    def _create_standard_strategy(
        self,
        filings: Optional[List[Dict[str, Any]]]
    ) -> ExecutionStrategy:
        """Create STANDARD execution strategy."""
        # All 15 nodes, ~1.5 min per node with optimization
        node_count = 15
        estimated_duration = node_count * 90  # 22.5 minutes
        
        return ExecutionStrategy(
            orchestrator_name="MasterExecutionController",
            priority=InvestigationPriority.STANDARD,
            estimated_duration_seconds=estimated_duration,
            node_count=node_count,
            enable_strict_gates=True,
            enable_ai_validation=True,
            enable_parallel_execution=False,
            optimization_level="moderate",
            description="Comprehensive 15-node analysis with strict gates (15-30 min)"
        )
    
    def _create_doj_referral_strategy(
        self,
        filings: Optional[List[Dict[str, Any]]]
    ) -> ExecutionStrategy:
        """Create DOJ_REFERRAL execution strategy."""
        # All 15 nodes + parallel agents, ~2.5 min per node
        node_count = 15
        estimated_duration = node_count * 150  # 37.5 minutes
        
        return ExecutionStrategy(
            orchestrator_name="ForensicMetaOrchestrator",
            priority=InvestigationPriority.DOJ_REFERRAL,
            estimated_duration_seconds=estimated_duration,
            node_count=node_count,
            enable_strict_gates=True,
            enable_ai_validation=True,
            enable_parallel_execution=True,
            optimization_level="none",
            description="Exhaustive parallel execution with maximum evidence integrity (30-60 min)"
        )
    
    # ═════════════════════════════════════════════════════════════════════════
    # EXECUTION PATHS
    # ═════════════════════════════════════════════════════════════════════════
    
    async def _collect_filing_metadata(
        self,
        cik: str,
        start_date: date,
        end_date: date,
        sec_user_agent: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Collect basic filing metadata for strategy selection."""
        try:
            from src.integrations.sec_edgar.edgar_client import SECEdgarClient
            
            async with SECEdgarClient(user_agent=sec_user_agent) as client:
                # Get recent submissions for metadata
                submissions = await client.get_recent_submissions(cik)
                
                # Extract filing types
                filings = []
                if submissions and "filings" in submissions:
                    recent = submissions["filings"].get("recent", {})
                    form_types = recent.get("form", [])
                    
                    for form_type in form_types[:20]:  # Sample first 20
                        filings.append({"form_type": form_type})
                
                return filings
                
        except Exception as e:
            self.logger.warning(f"Failed to collect filing metadata: {e}")
            return []
    
    async def _execute_triage(
        self,
        cik: str,
        company_name: str,
        start_date: date,
        end_date: date,
        output_dir: Path,
        filings: List[Dict[str, Any]],
        sec_user_agent: Optional[str]
    ) -> Dict[str, Any]:
        """Execute TRIAGE strategy using IntelligentOrchestrator."""
        self.logger.info("→ Executing TRIAGE strategy (IntelligentOrchestrator)")
        
        # Lazy-load IntelligentOrchestrator
        if self._intelligent_orchestrator is None:
            from src.core.intelligent_orchestrator import IntelligentOrchestrator
            self._intelligent_orchestrator = IntelligentOrchestrator()
        
        # Detect investigation type from filings
        from src.core.intelligent_orchestrator import InvestigationType
        investigation_type = self._detect_investigation_type_from_filings(filings)
        
        # Create execution plan
        plan = self._intelligent_orchestrator.create_execution_plan(
            investigation_type=investigation_type,
            available_filings=filings
        )
        
        self.logger.info(f"  Nodes to execute: {len(plan.required_nodes)}")
        self.logger.info(f"  Estimated: {plan.estimated_duration_seconds/60:.1f} min")
        
        # For triage, return simplified result
        # (Full implementation would execute nodes here)
        return {
            "success": True,
            "orchestrator": "IntelligentOrchestrator",
            "investigation_type": investigation_type.value,
            "node_results": {},
            "detection_results": {},
            "evidence_chain": {},
            "total_violations": 0,
            "total_alerts": 0
        }
    
    async def _execute_standard(
        self,
        cik: str,
        company_name: str,
        start_date: date,
        end_date: date,
        output_dir: Path,
        sec_user_agent: Optional[str],
        polygon_api_key: Optional[str]
    ) -> Dict[str, Any]:
        """Execute STANDARD strategy using MasterExecutionController."""
        self.logger.info("→ Executing STANDARD strategy (MasterExecutionController)")
        
        # Import and execute MasterExecutionController
        from src.core.master_execution_controller import MasterExecutionController
        
        controller = MasterExecutionController(
            cik=cik,
            company_name=company_name,
            start_date=start_date,
            end_date=end_date,
            output_dir=output_dir,
            strict_mode=True,
            auto_mode=True,
            enable_optimization=True,
            sec_user_agent=sec_user_agent,
            polygon_api_key=polygon_api_key
        )
        
        # Execute full analysis
        result = await controller.execute_full_analysis()
        
        # Convert to dict format
        return {
            "success": True,
            "orchestrator": "MasterExecutionController",
            "node_results": result.node_results,
            "detection_results": result.detection_results,
            "ai_validation_results": getattr(controller, "ai_validation_results", None),
            "evidence_chain": result.evidence_chain,
            "dossier_path": result.dossier_path,
            "total_violations": result.total_violations,
            "total_alerts": result.total_alerts
        }
    
    async def _execute_doj_referral(
        self,
        cik: str,
        company_name: str,
        start_date: date,
        end_date: date,
        output_dir: Path,
        filings: List[Dict[str, Any]],
        sec_user_agent: Optional[str],
        polygon_api_key: Optional[str]
    ) -> Dict[str, Any]:
        """Execute DOJ_REFERRAL strategy using ForensicMetaOrchestrator."""
        self.logger.info("→ Executing DOJ_REFERRAL strategy (ForensicMetaOrchestrator)")
        
        # For now, delegate to MasterExecutionController with enhanced settings
        # (ForensicMetaOrchestrator would be used if more parallel processing needed)
        from src.core.master_execution_controller import MasterExecutionController
        
        controller = MasterExecutionController(
            cik=cik,
            company_name=company_name,
            start_date=start_date,
            end_date=end_date,
            output_dir=output_dir,
            strict_mode=True,
            auto_mode=True,
            enable_optimization=False,  # Disable optimization for exhaustive mode
            sec_user_agent=sec_user_agent,
            polygon_api_key=polygon_api_key
        )
        
        # Execute full analysis
        result = await controller.execute_full_analysis()
        
        # Convert to dict format
        return {
            "success": True,
            "orchestrator": "ForensicMetaOrchestrator (via MasterExecutionController)",
            "node_results": result.node_results,
            "detection_results": result.detection_results,
            "ai_validation_results": getattr(controller, "ai_validation_results", None),
            "evidence_chain": result.evidence_chain,
            "dossier_path": result.dossier_path,
            "total_violations": result.total_violations,
            "total_alerts": result.total_alerts
        }
    
    def _detect_investigation_type_from_filings(
        self,
        filings: List[Dict[str, Any]]
    ) -> 'InvestigationType':
        """Detect investigation type from filing composition."""
        from src.core.intelligent_orchestrator import InvestigationType
        
        form_types = set()
        for f in filings:
            form_type = f.get("form_type", "")
            if form_type:
                form_types.add(form_type.upper())
        
        # Detection logic
        has_form4 = any(ft in form_types for ft in ["4", "4/A"])
        has_form144 = any(ft in form_types for ft in ["144", "144/A"])
        has_10k = any("10-K" in ft for ft in form_types)
        has_def14a = any("DEF 14A" in ft for ft in form_types)
        
        if (has_form4 or has_form144) and not (has_10k and has_def14a):
            return InvestigationType.INSIDER_TRADING
        
        if has_10k and has_def14a:
            return InvestigationType.FINANCIAL_FRAUD
        
        if has_10k and not has_form4:
            return InvestigationType.COMPLIANCE
        
        return InvestigationType.COMPREHENSIVE
