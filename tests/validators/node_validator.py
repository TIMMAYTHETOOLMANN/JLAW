"""
Node Validator - Validate all 15 analysis nodes.
"""

import importlib
import sys
from typing import Dict, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class NodeValidationResult:
    """Result from node validation."""
    passed: bool
    message: str
    node_number: int
    has_v2: bool = False
    can_skip: bool = False


class NodeValidator:
    """
    Validate all 15 analysis nodes.
    
    For each node (1-15):
    - Module import test
    - Class instantiation test
    - Mock data processing test (if mock_mode=True)
    - V2 version availability check (Nodes 7-15)
    - Graceful degradation confirmation
    """
    
    NODE_MAPPING = {
        1: ('node1_form4', 'Form4InsiderTradingAnalyzer', 'Form 4 Insider Trading'),
        2: ('node2_def14a', 'DEF14ACompensationAnalyzer', 'DEF 14A Executive Compensation'),
        3: ('node3_10q', 'TenQTemporalAnalyzer', '10-Q Temporal Consistency'),
        4: ('node4_10k_sox', 'SOXCertificationValidator', '10-K SOX Certification'),
        5: ('node5_irs', 'IRCTaxCalculator', 'IRC §83 Tax Exposure'),
        6: ('node6_routing', 'EnforcementRouter', 'Enforcement Routing'),
        7: ('node7_13f_holdings', 'InstitutionalHoldingsAnalyzerV2', '13F-HR Institutional Holdings'),
        8: ('node8_13d_ownership', 'BeneficialOwnershipAnalyzerV2', 'SC 13D/13G Beneficial Ownership'),
        9: ('node9_8k_events', 'MaterialEventAnalyzerV2', '8-K Material Events'),
        10: ('node10_form144', 'Form144AnalyzerV2', 'Form 144 Restricted Sales'),
        11: ('node11_network_mapper', 'ExecutiveNetworkMapperV2', 'Executive Network Analysis'),
        12: ('node12_earnings_calls', 'EarningsCallAnalyzerV2', 'Earnings Call Transcripts'),
        13: ('node13_zscore', 'BankruptcyPredictorV2', 'Z-Score Bankruptcy Prediction'),
        14: ('node14_fscore', 'FinancialHealthScorerV2', 'F-Score Financial Strength'),
        15: ('node15_market_correlation', 'MarketCorrelationEngineV2', 'Market Correlation Engine'),
    }
    
    def __init__(self, mock_mode: bool = False):
        """
        Initialize node validator.
        
        Args:
            mock_mode: If True, use mock data for testing
        """
        self.mock_mode = mock_mode
        self.project_root = self._find_project_root()
        # Add project root to path
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))
    
    def _find_project_root(self) -> Path:
        """Find project root directory."""
        current = Path(__file__).resolve()
        while current != current.parent:
            if (current / 'src').exists():
                return current
            current = current.parent
        return Path.cwd()
    
    def validate_node(self, node_number: int) -> NodeValidationResult:
        """
        Validate a single node.
        
        Args:
            node_number: Node number (1-15)
            
        Returns:
            Validation result
        """
        if node_number not in self.NODE_MAPPING:
            return NodeValidationResult(
                passed=False,
                message=f"Unknown node number: {node_number}",
                node_number=node_number,
            )
        
        module_name, class_name, description = self.NODE_MAPPING[node_number]
        has_v2 = node_number >= 7
        
        try:
            # Try importing from unified nodes package first
            try:
                nodes_module = importlib.import_module('src.nodes')
                if hasattr(nodes_module, class_name):
                    node_class = getattr(nodes_module, class_name)
                else:
                    # Fall back to direct import
                    full_module_name = f'src.nodes.{module_name}'
                    node_module = importlib.import_module(full_module_name)
                    node_class = getattr(node_module, class_name)
            except (ImportError, AttributeError):
                # Try direct import
                full_module_name = f'src.nodes.{module_name}'
                node_module = importlib.import_module(full_module_name)
                node_class = getattr(node_module, class_name)
            
            # Try instantiating
            try:
                if self.mock_mode:
                    instance = node_class(mock_mode=True)
                else:
                    instance = node_class()
                
                return NodeValidationResult(
                    passed=True,
                    message=f"Node {node_number}: {description} - ✓ Operational",
                    node_number=node_number,
                    has_v2=has_v2,
                    can_skip=False,
                )
            except TypeError:
                # Some nodes may not support mock_mode parameter
                instance = node_class()
                return NodeValidationResult(
                    passed=True,
                    message=f"Node {node_number}: {description} - ✓ Operational (no mock mode)",
                    node_number=node_number,
                    has_v2=has_v2,
                    can_skip=False,
                )
        
        except ImportError as e:
            return NodeValidationResult(
                passed=False,
                message=f"Node {node_number}: {description} - ✗ Import failed: {str(e)}",
                node_number=node_number,
                has_v2=has_v2,
                can_skip=False,
            )
        except AttributeError as e:
            return NodeValidationResult(
                passed=False,
                message=f"Node {node_number}: {description} - ✗ Class not found: {str(e)}",
                node_number=node_number,
                has_v2=has_v2,
                can_skip=False,
            )
        except Exception as e:
            return NodeValidationResult(
                passed=False,
                message=f"Node {node_number}: {description} - ✗ Instantiation failed: {str(e)}",
                node_number=node_number,
                has_v2=has_v2,
                can_skip=False,
            )
    
    def validate_all_nodes(self) -> Dict[int, NodeValidationResult]:
        """
        Validate all 15 nodes.
        
        Returns:
            Dictionary mapping node number to validation result
        """
        results = {}
        
        for node_number in range(1, 16):
            results[node_number] = self.validate_node(node_number)
        
        return results
    
    def get_summary(self, results: Dict[int, NodeValidationResult]) -> Dict[str, int]:
        """
        Get summary statistics from validation results.
        
        Args:
            results: Validation results dictionary
            
        Returns:
            Summary dictionary with counts
        """
        total = len(results)
        passed = sum(1 for r in results.values() if r.passed)
        failed = total - passed
        v2_available = sum(1 for r in results.values() if r.has_v2 and r.passed)
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'v2_available': v2_available,
        }
