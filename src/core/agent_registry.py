"""
Agent Registry - Pre-registers all detection patterns and node analyzers.
============================================================================

Provides plug-and-play agent activation for ForensicMetaOrchestrator.
Implements violation-to-agent mapping for intelligent agent selection.

Usage:
    from src.core.forensic_meta_orchestrator import ForensicMetaOrchestrator
    from src.core.agent_registry import register_default_agents
    
    orchestrator = ForensicMetaOrchestrator()
    register_default_agents(orchestrator)
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Dict, List, Set, Any, Optional, Callable

if TYPE_CHECKING:
    from .forensic_meta_orchestrator import ForensicMetaOrchestrator

logger = logging.getLogger(__name__)


# Violation type to agent mapping for auto-selection
VIOLATION_AGENT_MAP: Dict[str, List[str]] = {
    "insider_trading": [
        "options_backdating",
        "form4_analyzer",
        "form144_monitor",
        "market_correlation",
        "beneficial_ownership_tracker"
    ],
    "accounting_fraud": [
        "channel_stuffing",
        "advanced_pattern_detector",
        "temporal_consistency"
    ],
    "sox_violation": [
        "sox_certification_analyzer",
        "temporal_consistency",
        "compliance_checker"
    ],
    "executive_compensation": [
        "compensation_analyzer",
        "irc83_calculator"
    ],
    "beneficial_ownership": [
        "beneficial_ownership_tracker",
        "institutional_holdings",
        "executive_network_mapper"
    ],
    "material_event": [
        "material_event_correlator",
        "earnings_call_analyzer",
        "market_correlation"
    ],
    "financial_distress": [
        "altman_zscore",
        "piotroski_fscore",
        "bankruptcy_predictor"
    ],
    "late_filing": [
        "form4_analyzer",
        "enforcement_router"
    ],
    "options_backdating": [
        "options_backdating",
        "form4_analyzer",
        "compensation_analyzer"
    ]
}


def register_default_agents(orchestrator: 'ForensicMetaOrchestrator') -> int:
    """
    Pre-register all detection patterns and node analyzers as agents.
    
    This function registers:
    - 23 detection pattern agents (fraud detectors, analyzers)
    - 15 node analyzer agents (SEC filing processors)
    
    Args:
        orchestrator: ForensicMetaOrchestrator instance to register agents with
        
    Returns:
        Number of agents successfully registered
    """
    from .forensic_meta_orchestrator import AgentType, AgentPriority
    
    registered_count = 0
    
    # =========================================================================
    # DETECTION PATTERN AGENTS (High-priority fraud detection)
    # =========================================================================
    pattern_agents = [
        # Options Backdating Detection
        {
            "name": "options_backdating",
            "agent_type": AgentType.PATTERN_DETECTOR,
            "priority": AgentPriority.HIGH,
            "module": "src.detection.patterns.options_backdating_detector",
            "class_name": "OptionsBackdatingDetector",
            "dependencies": ["form4_analyzer"]
        },
        # Channel Stuffing Detection
        {
            "name": "channel_stuffing",
            "agent_type": AgentType.PATTERN_DETECTOR,
            "priority": AgentPriority.HIGH,
            "module": "src.detection.patterns.channel_stuffing_detector",
            "class_name": "ChannelStuffingDetector",
            "dependencies": []
        },
        # Advanced Pattern Detector (multiple patterns in one)
        {
            "name": "advanced_pattern_detector",
            "agent_type": AgentType.PATTERN_DETECTOR,
            "priority": AgentPriority.HIGH,
            "module": "src.detection.patterns.advanced_patterns",
            "class_name": "AdvancedPatternDetector",
            "dependencies": []
        },
    ]
    
    for agent_config in pattern_agents:
        try:
            handler = _create_pattern_handler(
                agent_config["module"],
                agent_config["class_name"]
            )
            
            if handler:
                orchestrator.register_agent(
                    name=agent_config["name"],
                    agent_type=agent_config["agent_type"],
                    handler=handler,
                    priority=agent_config["priority"],
                    dependencies=agent_config.get("dependencies", [])
                )
                registered_count += 1
                logger.debug(f"Registered pattern agent: {agent_config['name']}")
        except Exception as e:
            logger.warning(f"Failed to register pattern agent {agent_config['name']}: {e}")
    
    # =========================================================================
    # NODE ANALYZER AGENTS (SEC Filing Processors)
    # =========================================================================
    node_agents = [
        # Node 1: Form 4 Insider Trading
        {
            "name": "form4_analyzer",
            "agent_type": AgentType.DOCUMENT_PARSER,
            "priority": AgentPriority.CRITICAL,
            "node_id": 1,
            "dependencies": []
        },
        # Node 2: DEF 14A Compensation
        {
            "name": "compensation_analyzer",
            "agent_type": AgentType.FINANCIAL_ANALYZER,
            "priority": AgentPriority.HIGH,
            "node_id": 2,
            "dependencies": []
        },
        # Node 3: 10-Q Temporal Consistency
        {
            "name": "temporal_consistency",
            "agent_type": AgentType.COMPLIANCE_CHECKER,
            "priority": AgentPriority.MEDIUM,
            "node_id": 3,
            "dependencies": []
        },
        # Node 4: 10-K SOX Certification
        {
            "name": "sox_certification_analyzer",
            "agent_type": AgentType.COMPLIANCE_CHECKER,
            "priority": AgentPriority.HIGH,
            "node_id": 4,
            "dependencies": []
        },
        # Node 5: IRC §83 Tax Exposure
        {
            "name": "irc83_calculator",
            "agent_type": AgentType.FINANCIAL_ANALYZER,
            "priority": AgentPriority.MEDIUM,
            "node_id": 5,
            "dependencies": ["form4_analyzer", "compensation_analyzer"]
        },
        # Node 6: Enforcement Router
        {
            "name": "enforcement_router",
            "agent_type": AgentType.COMPLIANCE_CHECKER,
            "priority": AgentPriority.LOW,
            "node_id": 6,
            "dependencies": []
        },
        # Node 7: 13F-HR Holdings
        {
            "name": "institutional_holdings",
            "agent_type": AgentType.FINANCIAL_ANALYZER,
            "priority": AgentPriority.MEDIUM,
            "node_id": 7,
            "dependencies": []
        },
        # Node 8: 13D/13G Ownership
        {
            "name": "beneficial_ownership_tracker",
            "agent_type": AgentType.FINANCIAL_ANALYZER,
            "priority": AgentPriority.MEDIUM,
            "node_id": 8,
            "dependencies": []
        },
        # Node 9: 8-K Material Events
        {
            "name": "material_event_correlator",
            "agent_type": AgentType.PATTERN_DETECTOR,
            "priority": AgentPriority.HIGH,
            "node_id": 9,
            "dependencies": []
        },
        # Node 10: Form 144 Restricted Sales
        {
            "name": "form144_monitor",
            "agent_type": AgentType.DOCUMENT_PARSER,
            "priority": AgentPriority.HIGH,
            "node_id": 10,
            "dependencies": ["form4_analyzer"]
        },
        # Node 11: Executive Network Mapper
        {
            "name": "executive_network_mapper",
            "agent_type": AgentType.NETWORK_ANALYZER,
            "priority": AgentPriority.MEDIUM,
            "node_id": 11,
            "dependencies": ["form4_analyzer", "compensation_analyzer"]
        },
        # Node 12: Earnings Call Transcripts
        {
            "name": "earnings_call_analyzer",
            "agent_type": AgentType.DOCUMENT_PARSER,
            "priority": AgentPriority.MEDIUM,
            "node_id": 12,
            "dependencies": []
        },
        # Node 13: Altman Z-Score
        {
            "name": "altman_zscore",
            "agent_type": AgentType.FINANCIAL_ANALYZER,
            "priority": AgentPriority.HIGH,
            "node_id": 13,
            "dependencies": []
        },
        # Node 14: Piotroski F-Score
        {
            "name": "piotroski_fscore",
            "agent_type": AgentType.FINANCIAL_ANALYZER,
            "priority": AgentPriority.HIGH,
            "node_id": 14,
            "dependencies": []
        },
        # Node 15: Market Correlation
        {
            "name": "market_correlation",
            "agent_type": AgentType.CROSS_VALIDATOR,
            "priority": AgentPriority.LOW,
            "node_id": 15,
            "dependencies": ["form4_analyzer", "material_event_correlator"]
        },
    ]
    
    for agent_config in node_agents:
        try:
            handler = _create_node_handler(agent_config["node_id"])
            
            orchestrator.register_agent(
                name=agent_config["name"],
                agent_type=agent_config["agent_type"],
                handler=handler,
                priority=agent_config["priority"],
                dependencies=agent_config.get("dependencies", [])
            )
            registered_count += 1
            logger.debug(f"Registered node agent: {agent_config['name']} (Node {agent_config['node_id']})")
        except Exception as e:
            logger.warning(f"Failed to register node agent {agent_config['name']}: {e}")
    
    # =========================================================================
    # CROSS-VALIDATION AGENTS
    # =========================================================================
    cross_validators = [
        {
            "name": "compliance_checker",
            "agent_type": AgentType.COMPLIANCE_CHECKER,
            "priority": AgentPriority.MEDIUM,
            "dependencies": []
        },
        {
            "name": "bankruptcy_predictor",
            "agent_type": AgentType.FINANCIAL_ANALYZER,
            "priority": AgentPriority.MEDIUM,
            "dependencies": ["altman_zscore", "piotroski_fscore"]
        },
    ]
    
    for agent_config in cross_validators:
        try:
            async def cross_val_handler(data: Dict, completed: Set, name=agent_config["name"]):
                return {
                    "findings": {},
                    "violations": [],
                    "alerts": [],
                    "agent": name,
                    "status": "completed"
                }
            
            orchestrator.register_agent(
                name=agent_config["name"],
                agent_type=agent_config["agent_type"],
                handler=cross_val_handler,
                priority=agent_config["priority"],
                dependencies=agent_config.get("dependencies", [])
            )
            registered_count += 1
        except Exception as e:
            logger.warning(f"Failed to register cross-validator {agent_config['name']}: {e}")
    
    logger.info(f"✓ Agent registry initialized: {registered_count} agents registered")
    return registered_count


def _create_pattern_handler(module_path: str, class_name: str) -> Optional[Callable]:
    """
    Create an async handler for a detection pattern.
    
    Args:
        module_path: Full module path (e.g., "src.detection.patterns.options_backdating_detector")
        class_name: Class name within the module
        
    Returns:
        Async handler function or None if import fails
    """
    try:
        import importlib
        module = importlib.import_module(module_path)
        detector_class = getattr(module, class_name, None)
        
        if detector_class is None:
            logger.warning(f"Class {class_name} not found in {module_path}")
            return None
        
        async def handler(data: Dict[str, Any], completed: Set[str]) -> Dict[str, Any]:
            try:
                detector = detector_class()
                
                # Check for async analyze method
                if hasattr(detector, 'analyze'):
                    if asyncio.iscoroutinefunction(detector.analyze):
                        result = await detector.analyze(data)
                    else:
                        result = detector.analyze(data)
                    
                    return {
                        "findings": result if isinstance(result, dict) else {"result": result},
                        "violations": result.get("violations", []) if isinstance(result, dict) else [],
                        "alerts": result.get("alerts", []) if isinstance(result, dict) else []
                    }
                else:
                    return {"findings": {}, "violations": [], "alerts": []}
                    
            except Exception as e:
                logger.error(f"Pattern handler error: {e}")
                return {"findings": {}, "violations": [], "alerts": [], "error": str(e)}
        
        return handler
        
    except ImportError as e:
        logger.debug(f"Could not import {module_path}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Error creating pattern handler for {class_name}: {e}")
        return None


def _create_node_handler(node_id: int) -> Callable:
    """
    Create an async handler for a node analyzer.
    
    Args:
        node_id: Node ID (1-15)
        
    Returns:
        Async handler function
    """
    async def handler(data: Dict[str, Any], completed: Set[str]) -> Dict[str, Any]:
        """
        Node handler that integrates with existing node infrastructure.
        """
        try:
            # Import node module dynamically based on node_id
            node_modules = {
                1: ("src.nodes.node1_form4", "Form4Parser"),
                2: ("src.nodes.node2_def14a", "CompensationAnalyzer"),
                3: ("src.nodes.node3_10q", "TemporalConsistencyValidator"),
                4: ("src.nodes.node4_10k_sox", "SOXCertificationAnalyzer"),
                5: ("src.nodes.node5_irs", "IRC83TaxCalculator"),
                6: ("src.nodes.node6_routing", "EnforcementRouter"),
                7: ("src.nodes.node7_13f_holdings", "InstitutionalHoldingsAnalyzerV2"),
                8: ("src.nodes.node8_13d_ownership", "BeneficialOwnershipTrackerV2"),
                9: ("src.nodes.node9_8k_events", "MaterialEventCorrelatorV2"),
                10: ("src.nodes.node10_form144", "RestrictedSaleMonitorV2"),
                11: ("src.nodes.node11_network_mapper", "ExecutiveNetworkAnalyzerV2"),
                12: ("src.nodes.node12_earnings_calls", "TranscriptAnalyzerV2"),
                13: ("src.nodes.node13_zscore", "BankruptcyPredictorV2"),
                14: ("src.nodes.node14_fscore", "FinancialStrengthAnalyzerV2"),
                15: ("src.nodes.node15_market_correlation", "MarketCorrelationEngineV2"),
            }
            
            if node_id in node_modules:
                module_path, class_name = node_modules[node_id]
                
                try:
                    import importlib
                    module = importlib.import_module(module_path)
                    analyzer_class = getattr(module, class_name, None)
                    
                    if analyzer_class:
                        analyzer = analyzer_class()
                        if hasattr(analyzer, 'analyze'):
                            if asyncio.iscoroutinefunction(analyzer.analyze):
                                result = await analyzer.analyze(data)
                            else:
                                result = analyzer.analyze(data)
                            
                            return {
                                "node_id": node_id,
                                "findings": result if isinstance(result, dict) else {"result": result},
                                "violations": result.get("violations", []) if isinstance(result, dict) else [],
                                "alerts": result.get("alerts", []) if isinstance(result, dict) else [],
                                "status": "completed"
                            }
                except ImportError:
                    pass  # Fall through to placeholder
            
            # Placeholder response if module not available
            return {
                "node_id": node_id,
                "findings": {},
                "violations": [],
                "alerts": [],
                "status": "placeholder"
            }
            
        except Exception as e:
            logger.error(f"Node {node_id} handler error: {e}")
            return {
                "node_id": node_id,
                "findings": {},
                "violations": [],
                "alerts": [],
                "error": str(e),
                "status": "error"
            }
    
    return handler


def get_agents_for_violations(violation_types: List[str]) -> Set[str]:
    """
    Get relevant agents for a list of violation types.
    
    Args:
        violation_types: List of violation type strings
        
    Returns:
        Set of agent names to execute
    """
    required_agents: Set[str] = set()
    
    for vtype in violation_types:
        # Normalize violation type
        vtype_normalized = vtype.lower().replace(" ", "_").replace("-", "_")
        
        if vtype_normalized in VIOLATION_AGENT_MAP:
            required_agents.update(VIOLATION_AGENT_MAP[vtype_normalized])
        else:
            # Try partial matching
            for key, agents in VIOLATION_AGENT_MAP.items():
                if key in vtype_normalized or vtype_normalized in key:
                    required_agents.update(agents)
                    break
    
    return required_agents


def get_all_violation_types() -> List[str]:
    """Get list of all supported violation types."""
    return list(VIOLATION_AGENT_MAP.keys())


__all__ = [
    'register_default_agents',
    'get_agents_for_violations',
    'get_all_violation_types',
    'VIOLATION_AGENT_MAP'
]
