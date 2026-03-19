"""
Intelligent Orchestrator - Meta-agent for dynamic execution optimization.

.. deprecated::
    **DEPRECATED** — Use :class:`UnifiedForensicOrchestrator` from
    ``src.core.unified_orchestrator`` instead. See ``EXECUTION_AUTHORITY.md``
    for the canonical execution path. This module is retained for backward
    compatibility and will be removed in a future version.

Selects optimal execution strategy based on:
- Investigation type (insider trading, financial fraud, compliance)
- Available data (which filing types exist)
- Resource constraints
- Prior node findings

Achieves 30-50% execution speedup for focused investigations.
"""

import logging
from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class InvestigationType(Enum):
    """Investigation type determines node prioritization."""
    INSIDER_TRADING = "insider_trading"
    FINANCIAL_FRAUD = "financial_fraud"
    COMPLIANCE = "compliance"
    COMPREHENSIVE = "comprehensive"


@dataclass
class ExecutionPlan:
    """Optimized execution plan."""
    required_nodes: List[int] = field(default_factory=list)
    optional_nodes: List[int] = field(default_factory=list)
    skipped_nodes: List[int] = field(default_factory=list)
    estimated_duration_seconds: float = 0.0
    reason: str = ""
    investigation_type: str = ""
    optimization_percentage: float = 0.0


class IntelligentOrchestrator:
    """
    Meta-orchestrator that dynamically selects nodes based on:
    - Filing types available
    - Investigation objectives
    - Resource constraints
    - Prior node findings

    .. deprecated::
        Use :class:`UnifiedForensicOrchestrator` from
        ``src.core.unified_orchestrator`` instead.  This class is retained
        for backward compatibility and will be removed in a future version.
    """
    
    # Node requirements by investigation type
    NODE_PRIORITIES = {
        InvestigationType.INSIDER_TRADING: {
            "required": [1, 10, 15],  # Form 4, Form 144, Market
            "recommended": [7, 8, 9, 11],  # 13F, 13D, 8-K, Network
            "optional": [2, 3, 4, 5, 6, 12, 13, 14]
        },
        InvestigationType.FINANCIAL_FRAUD: {
            "required": [2, 3, 4, 5, 13, 14],  # DEF 14A, 10-Q, 10-K, IRC, Z/F-Score
            "recommended": [1, 9, 12],  # Form 4, 8-K, Earnings
            "optional": [6, 7, 8, 10, 11, 15]
        },
        InvestigationType.COMPLIANCE: {
            "required": [3, 4, 9],  # 10-Q, 10-K SOX, 8-K
            "recommended": [2, 6, 12],  # DEF 14A, Routing, Earnings
            "optional": [1, 5, 7, 8, 10, 11, 13, 14, 15]
        },
        InvestigationType.COMPREHENSIVE: {
            "required": list(range(1, 16)),  # All 15 nodes
            "recommended": [],
            "optional": []
        }
    }
    
    # Filing type to node mapping
    FILING_NODE_MAP = {
        "4": [1],
        "FORM 4": [1],
        "DEF 14A": [2, 11],
        "10-Q": [3, 13, 14],
        "10-K": [4, 13, 14],
        "13F-HR": [7],
        "13F": [7],
        "SC 13D": [8],
        "SC 13G": [8],
        "13D": [8],
        "13G": [8],
        "8-K": [9],
        "144": [10],
        "FORM 144": [10],
    }
    
    # Nodes that can run on derived data (don't need direct filings)
    DERIVED_DATA_NODES = [5, 6, 11, 13, 14, 15]
    
    def __init__(self):
        # DEPRECATION WARNING
        import warnings
        warnings.warn(
            "IntelligentOrchestrator is deprecated. "
            "Use UnifiedForensicOrchestrator from src.core.unified_orchestrator for DOJ-grade compliance. "
            "This class will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )

        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_execution_plan(
        self,
        investigation_type: InvestigationType,
        available_filings: List[Dict[str, Any]],
        resource_constraints: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        Create optimized execution plan based on investigation type and available data.
        
        Args:
            investigation_type: Type of investigation
            available_filings: List of available SEC filings
            resource_constraints: Optional resource limits (max_nodes, max_time_seconds)
            
        Returns:
            ExecutionPlan with required, optional, and skipped nodes
        """
        # Get available filing types
        available_types = set()
        for f in available_filings:
            form_type = f.get("form_type", "") or f.get("type", "")
            if form_type:
                available_types.add(form_type.upper().strip())
        
        self.logger.info(f"Available filing types: {available_types}")
        
        # Determine which nodes have data
        nodes_with_data = self._get_nodes_with_data(available_types)
        self.logger.info(f"Nodes with data: {nodes_with_data}")
        
        # Get node priorities for investigation type
        priorities = self.NODE_PRIORITIES[investigation_type]
        
        # Build execution plan
        required_nodes = []
        optional_nodes = []
        skipped_nodes = []
        
        for node_id in range(1, 16):
            has_data = node_id in nodes_with_data or node_id in self.DERIVED_DATA_NODES
            
            if node_id in priorities["required"]:
                if has_data:
                    required_nodes.append(node_id)
                else:
                    self.logger.warning(f"Required node {node_id} has no data - marking optional")
                    optional_nodes.append(node_id)
            elif node_id in priorities["recommended"]:
                if has_data:
                    optional_nodes.append(node_id)
                else:
                    skipped_nodes.append(node_id)
            else:  # optional priority
                if has_data:
                    optional_nodes.append(node_id)
                else:
                    skipped_nodes.append(node_id)
        
        # Apply resource constraints
        if resource_constraints:
            max_nodes = resource_constraints.get("max_nodes", 15)
            total_planned = len(required_nodes) + len(optional_nodes)
            if total_planned > max_nodes:
                # If required nodes already exceed max, we can't help
                if len(required_nodes) >= max_nodes:
                    # Move all optional nodes to skipped
                    skipped_nodes.extend(optional_nodes)
                    optional_nodes = []
                else:
                    # Trim optional nodes to fit constraint
                    available_slots = max_nodes - len(required_nodes)
                    nodes_to_skip = optional_nodes[available_slots:]
                    optional_nodes = optional_nodes[:available_slots]
                    skipped_nodes.extend(nodes_to_skip)
        
        # Calculate optimization
        total_nodes = len(required_nodes) + len(optional_nodes)
        optimization_pct = ((15 - total_nodes) / 15) * 100 if total_nodes < 15 else 0
        
        # Estimate duration (rough: 5 seconds per required node, 3 per optional)
        estimated_duration = (len(required_nodes) * 5.0) + (len(optional_nodes) * 3.0)
        
        plan = ExecutionPlan(
            required_nodes=sorted(required_nodes),
            optional_nodes=sorted(optional_nodes),
            skipped_nodes=sorted(skipped_nodes),
            estimated_duration_seconds=estimated_duration,
            reason=f"{investigation_type.value} investigation with {len(available_types)} filing types",
            investigation_type=investigation_type.value,
            optimization_percentage=optimization_pct
        )
        
        self.logger.info(f"Execution plan created: {len(required_nodes)} required, {len(optional_nodes)} optional, {len(skipped_nodes)} skipped")
        self.logger.info(f"Optimization: {optimization_pct:.1f}% fewer nodes than comprehensive")
        
        return plan
    
    def _get_nodes_with_data(self, available_types: Set[str]) -> Set[int]:
        """Determine which nodes have data based on available filing types."""
        nodes_with_data = set()
        
        for filing_type in available_types:
            # Normalize filing type
            normalized = filing_type.upper().strip()
            
            # Check exact match
            if normalized in self.FILING_NODE_MAP:
                nodes_with_data.update(self.FILING_NODE_MAP[normalized])
            else:
                # Check partial matches
                for key, node_ids in self.FILING_NODE_MAP.items():
                    if key in normalized or normalized in key:
                        nodes_with_data.update(node_ids)
        
        return nodes_with_data
    
    def should_skip_node(
        self,
        node_id: int,
        prior_results: Dict[int, Any]
    ) -> Tuple[bool, str]:
        """
        Determine if a node should be skipped based on prior results.
        
        Args:
            node_id: Node to evaluate
            prior_results: Results from previously executed nodes
            
        Returns:
            Tuple of (should_skip, reason)
        """
        # Node 10 (Form 144) - skip if Node 1 found no insider activity
        if node_id == 10 and 1 in prior_results:
            node1_result = prior_results[1]
            trades = node1_result.get("trades", []) or node1_result.get("transactions", [])
            if not trades:
                return True, "No insider trades found in Node 1 (Form 4)"
        
        # Node 5 (IRC §83) - skip if Nodes 1 and 2 have no compensation data
        if node_id == 5:
            has_compensation = False
            if 1 in prior_results:
                grants = prior_results[1].get("grants", []) or prior_results[1].get("option_grants", [])
                if grants:
                    has_compensation = True
            if 2 in prior_results:
                comp = prior_results[2].get("compensation", {}) or prior_results[2].get("executive_compensation", {})
                if comp:
                    has_compensation = True
            if not has_compensation:
                return True, "No compensation data from Nodes 1/2"
        
        # Node 11 (Network) - skip if no executive data from prior nodes
        if node_id == 11:
            has_executive_data = False
            for prior_node in [1, 2, 7, 8]:
                if prior_node in prior_results:
                    result = prior_results[prior_node]
                    if result.get("executives") or result.get("insiders") or result.get("officers"):
                        has_executive_data = True
                        break
            if not has_executive_data:
                return True, "No executive data from Nodes 1/2/7/8"
        
        # Node 12 (Earnings) - skip if no transcript data available
        if node_id == 12:
            # Node 12 gracefully degrades, so don't skip automatically
            pass
        
        # Node 15 (Market) - skip if no trades to correlate
        if node_id == 15:
            has_trades = False
            if 1 in prior_results:
                trades = prior_results[1].get("trades", []) or prior_results[1].get("transactions", [])
                if trades:
                    has_trades = True
            if 9 in prior_results:
                events = prior_results[9].get("events", []) or prior_results[9].get("material_events", [])
                if events:
                    has_trades = True
            if not has_trades:
                return True, "No trades or events to correlate with market data"
        
        return False, ""
    
    def get_investigation_summary(self, plan: ExecutionPlan) -> str:
        """Generate human-readable summary of execution plan."""
        lines = [
            f"═══════════════════════════════════════════════════════════════",
            f"  INTELLIGENT ORCHESTRATOR - EXECUTION PLAN",
            f"═══════════════════════════════════════════════════════════════",
            f"  Investigation Type: {plan.investigation_type.upper()}",
            f"  Optimization: {plan.optimization_percentage:.1f}% faster than comprehensive",
            f"  Estimated Duration: {plan.estimated_duration_seconds:.1f}s",
            f"",
            f"  Required Nodes ({len(plan.required_nodes)}): {plan.required_nodes}",
            f"  Optional Nodes ({len(plan.optional_nodes)}): {plan.optional_nodes}",
            f"  Skipped Nodes ({len(plan.skipped_nodes)}): {plan.skipped_nodes}",
            f"",
            f"  Reason: {plan.reason}",
            f"═══════════════════════════════════════════════════════════════",
        ]
        return "\n".join(lines)
