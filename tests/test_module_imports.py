"""
Module Import Verification Test
===============================

Validates that all documented modules can be imported without errors.
This test ensures the integrity of the module structure and proper __init__.py exports.
"""

import glob
import os
import pytest


def test_core_modules():
    """Test core engine imports."""
    from src.core.recursive_engine import RecursiveProsecutorialEngine
    from src.core.linear_orchestrator import LinearExecutionOrchestrator
    from src.core.evidence_chain.hash_service import HashService
    from src.core.custody.custody import ChainOfCustody
    
    assert RecursiveProsecutorialEngine is not None
    assert LinearExecutionOrchestrator is not None
    assert HashService is not None
    assert ChainOfCustody is not None


def test_node_modules():
    """Test all 15 node module files exist."""
    # Note: Full node imports require networkx, numpy, and other dependencies
    # This test verifies the module structure is in place
    
    node_modules = [
        'src/nodes/node1_form4/form4_parser.py',
        'src/nodes/node2_def14a/compensation_analyzer.py',
        'src/nodes/node3_10q/temporal_consistency_validator.py',
        'src/nodes/node4_10k_sox/sox_certification_analyzer.py',
        'src/nodes/node5_irs/irc83_tax_calculator.py',
        'src/nodes/node6_routing/enforcement_router.py',
        'src/nodes/node7_13f_holdings/institutional_analyzer.py',
        'src/nodes/node8_13d_ownership/beneficial_ownership_tracker.py',
        'src/nodes/node9_8k_events/material_event_correlator.py',
        'src/nodes/node10_form144/restricted_sale_monitor.py',
        'src/nodes/node11_network_mapper/executive_network_analyzer.py',
        'src/nodes/node12_earnings_calls/transcript_analyzer.py',
        'src/nodes/node13_zscore/bankruptcy_predictor.py',
        'src/nodes/node14_fscore/financial_strength_analyzer.py',
        'src/nodes/node15_market_correlation/market_correlation_engine.py',
    ]
    
    for module_path in node_modules:
        assert os.path.exists(module_path), f"Node module not found: {module_path}"
    
    # Verify __init__.py files exist
    assert os.path.exists('src/nodes/__init__.py')
    for i in range(1, 16):
        node_dir = f'src/nodes/node{i}_*'
        matches = glob.glob(node_dir)
        assert len(matches) > 0, f"Node {i} directory not found"


def test_reporting_modules():
    """Test reporting system imports."""
    from src.reporting import (
        DOJReportGenerator,
        EvidencePackager,
        ChainOfCustodyLogger,
    )
    from src.reporting.models import ViolationEvidence
    from src.reporting.constants import ViolationType
    
    assert DOJReportGenerator is not None
    assert EvidencePackager is not None
    assert ChainOfCustodyLogger is not None
    assert ViolationEvidence is not None
    assert ViolationType is not None


def test_graph_modules():
    """Test graph analytics imports."""
    import src.graph.graph_analytics as graph_analytics
    
    assert graph_analytics is not None


def test_cross_node_modules():
    """Test cross-node correlation module exists."""
    # Note: NodeCorrelator requires networkx and other dependencies
    # Verify the module file exists
    import os
    cross_node_path = os.path.join('src', 'nodes', 'cross_node', 'node_correlator.py')
    assert os.path.exists(cross_node_path), f"cross_node module not found at {cross_node_path}"


def test_forensics_modules():
    """Test forensics system imports."""
    from src.forensics.dual_agent import DualAgentCoordinator
    # Note: DocumentParser requires numpy/FAISS dependencies
    # from src.forensics.docsgpt.document_parser import DocumentParser
    from src.forensics.subagents.orchestrator import SubagentOrchestrator
    
    assert DualAgentCoordinator is not None
    # assert DocumentParser is not None
    assert SubagentOrchestrator is not None


def test_detection_modules():
    """Test detection pattern imports."""
    from src.detection.patterns.advanced_patterns import AdvancedPatternDetector
    from src.detection.financial.beneish_mscore import BeneishMScoreCalculator
    
    assert AdvancedPatternDetector is not None
    assert BeneishMScoreCalculator is not None


def test_integration_modules():
    """Test external integration imports."""
    from src.integrations.sec_edgar.edgar_client import SECEdgarClient
    
    assert SECEdgarClient is not None


def test_config_modules():
    """Test configuration imports."""
    from config import (
        get_api_key,
        validate_configuration,
        load_all_keys,
    )
    
    assert get_api_key is not None
    assert validate_configuration is not None
    assert load_all_keys is not None


def test_internal_modules():
    """Test internal access-controlled modules."""
    from src.internal import get_internal_module
    
    assert get_internal_module is not None
    
    # Test that access control works (should raise PermissionError without acknowledgment)
    with pytest.raises(PermissionError):
        get_internal_module('whistleblower_bounty_estimator')
    
    # Test that access works with acknowledgment
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        bounty_module = get_internal_module(
            'whistleblower_bounty_estimator',
            acknowledge_internal_use=True
        )
        assert bounty_module is not None
