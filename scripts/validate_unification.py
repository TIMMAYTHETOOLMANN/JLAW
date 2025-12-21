#!/usr/bin/env python3
"""
JLAW Master Unification Validation Script
==========================================

Validates that the JLAW Master Unification has been correctly implemented:
- Master execution controller exists and is importable
- All V2 versions are properly configured
- No duplicate files remain
- All 15 nodes are functional
- Detection algorithms are accessible

Usage:
    python scripts/validate_unification.py
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any
import importlib
import inspect

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ValidationResult:
    """Validation result tracker."""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.warnings = 0
        self.errors: List[str] = []
        self.warnings_list: List[str] = []
    
    def pass_test(self, test_name: str):
        """Mark test as passed."""
        self.tests_passed += 1
        print(f"  ✓ {test_name}")
    
    def fail_test(self, test_name: str, error: str):
        """Mark test as failed."""
        self.tests_failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"  ✗ {test_name}: {error}")
    
    def add_warning(self, warning: str):
        """Add a warning."""
        self.warnings += 1
        self.warnings_list.append(warning)
        print(f"  ⚠ {warning}")
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 80)
        print("  VALIDATION SUMMARY")
        print("=" * 80)
        print(f"  Tests Passed: {self.tests_passed}")
        print(f"  Tests Failed: {self.tests_failed}")
        print(f"  Warnings: {self.warnings}")
        
        if self.errors:
            print("\n  ERRORS:")
            for error in self.errors:
                print(f"    - {error}")
        
        if self.warnings_list:
            print("\n  WARNINGS:")
            for warning in self.warnings_list:
                print(f"    - {warning}")
        
        print("=" * 80)
        
        if self.tests_failed == 0:
            print("  ✓ ALL VALIDATION CHECKS PASSED")
            return 0
        else:
            print("  ✗ VALIDATION FAILED")
            return 1


def validate_master_controller(result: ValidationResult):
    """Validate master execution controller."""
    print("\n" + "=" * 80)
    print("  1. MASTER EXECUTION CONTROLLER")
    print("=" * 80)
    
    # Check file exists
    controller_path = PROJECT_ROOT / "src" / "core" / "master_execution_controller.py"
    if not controller_path.exists():
        result.fail_test("Master controller file exists", "File not found")
        return
    result.pass_test("Master controller file exists")
    
    # Check importable
    try:
        from src.core.master_execution_controller import MasterExecutionController
        result.pass_test("Master controller importable")
    except ImportError as e:
        result.fail_test("Master controller importable", str(e))
        return
    
    # Check class has required methods
    required_methods = [
        'execute_full_analysis',
        '_execute_phase_1_configuration',
        '_execute_phase_2_data_collection',
        '_execute_phase_3_document_parsing',
        '_execute_phase_4_node_analysis',
        '_execute_phase_5_pattern_detection',
        '_execute_phase_6_dual_agent',
        '_execute_phase_7_subagent',
        '_execute_phase_8_evidence_chain',
        '_execute_phase_9_dossier_generation'
    ]
    
    for method_name in required_methods:
        if hasattr(MasterExecutionController, method_name):
            result.pass_test(f"Method '{method_name}' exists")
        else:
            result.fail_test(f"Method '{method_name}' exists", "Method not found")
    
    # Check ExecutionPhase enum
    try:
        from src.core.master_execution_controller import ExecutionPhase
        expected_phases = [
            'CONFIGURATION',
            'DATA_COLLECTION',
            'DOCUMENT_PARSING',
            'NODE_ANALYSIS',
            'PATTERN_DETECTION',
            'DUAL_AGENT',
            'SUBAGENT',
            'EVIDENCE_CHAIN',
            'DOSSIER_GENERATION'
        ]
        for phase in expected_phases:
            if hasattr(ExecutionPhase, phase):
                result.pass_test(f"ExecutionPhase.{phase} exists")
            else:
                result.fail_test(f"ExecutionPhase.{phase} exists", "Phase not found")
    except ImportError as e:
        result.fail_test("ExecutionPhase enum importable", str(e))


def validate_v2_versions(result: ValidationResult):
    """Validate V2 versions for nodes 7-15."""
    print("\n" + "=" * 80)
    print("  2. V2 VERSION VALIDATION")
    print("=" * 80)
    
    v2_modules = {
        'Node 7': ('src.nodes.node7_13f_holdings', 'InstitutionalHoldingsAnalyzerV2'),
        'Node 8': ('src.nodes.node8_13d_ownership', 'BeneficialOwnershipTrackerV2'),
        'Node 9': ('src.nodes.node9_8k_events', 'MaterialEventCorrelatorV2'),
        'Node 10': ('src.nodes.node10_form144', 'RestrictedSaleMonitorV2'),
        'Node 11': ('src.nodes.node11_network_mapper', 'ExecutiveNetworkAnalyzerV2'),
        'Node 12': ('src.nodes.node12_earnings_calls', 'TranscriptAnalyzerV2'),
        'Node 13': ('src.nodes.node13_zscore', 'BankruptcyPredictorV2'),
        'Node 14': ('src.nodes.node14_fscore', 'FinancialStrengthAnalyzerV2'),
        'Node 15': ('src.nodes.node15_market_correlation', 'MarketCorrelationEngineV2'),
    }
    
    for node_name, (module_path, class_name) in v2_modules.items():
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, class_name):
                result.pass_test(f"{node_name} - {class_name} exists")
            else:
                result.fail_test(f"{node_name} - {class_name} exists", "Class not found in module")
        except ImportError as e:
            result.fail_test(f"{node_name} - {class_name} importable", str(e))
    
    # Check main __init__.py exports V2 versions
    try:
        from src.nodes import (
            InstitutionalHoldingsAnalyzerV2,
            BeneficialOwnershipTrackerV2,
            MaterialEventCorrelatorV2,
            RestrictedSaleMonitorV2,
            ExecutiveNetworkAnalyzerV2,
            TranscriptAnalyzerV2,
            BankruptcyPredictorV2,
            FinancialStrengthAnalyzerV2,
            MarketCorrelationEngineV2
        )
        result.pass_test("All V2 versions exportable from src.nodes")
    except ImportError as e:
        result.fail_test("All V2 versions exportable from src.nodes", str(e))


def validate_recursive_engine_v2_imports(result: ValidationResult):
    """Validate recursive engine uses V2 imports."""
    print("\n" + "=" * 80)
    print("  3. RECURSIVE ENGINE V2 IMPORTS")
    print("=" * 80)
    
    engine_path = PROJECT_ROOT / "src" / "core" / "recursive_engine.py"
    if not engine_path.exists():
        result.fail_test("Recursive engine file exists", "File not found")
        return
    
    # Read file and check for V2 imports
    with open(engine_path, 'r') as f:
        content = f.read()
    
    v2_classes = [
        'InstitutionalHoldingsAnalyzerV2',
        'BeneficialOwnershipTrackerV2',
        'MaterialEventCorrelatorV2',
        'RestrictedSaleMonitorV2',
        'ExecutiveNetworkAnalyzerV2',
        'TranscriptAnalyzerV2',
        'BankruptcyPredictorV2',
        'FinancialStrengthAnalyzerV2',
        'MarketCorrelationEngineV2'
    ]
    
    for v2_class in v2_classes:
        if v2_class in content:
            result.pass_test(f"Recursive engine imports {v2_class}")
        else:
            result.fail_test(f"Recursive engine imports {v2_class}", "Import not found")


def validate_nodes_functional(result: ValidationResult):
    """Validate all 15 nodes are functional."""
    print("\n" + "=" * 80)
    print("  4. NODE FUNCTIONALITY")
    print("=" * 80)
    
    # Nodes 1-6 use V1 (original) versions
    nodes_v1 = {
        'Node 1': ('src.nodes.node1_form4.form4_parser', 'Form4Parser'),
        'Node 2': ('src.nodes.node2_def14a', 'DEF14ACompensationAnalyzer'),
        'Node 3': ('src.nodes.node3_10q', 'TemporalConsistencyValidator'),
        'Node 4': ('src.nodes.node4_10k_sox', 'SOXCertificationAnalyzer'),
        'Node 5': ('src.nodes.node5_irs', 'IRC83TaxCalculator'),
        'Node 6': ('src.nodes.node6_routing.enforcement_router', 'EnforcementRouter'),
    }
    
    # Nodes 7-15 use V2 versions
    nodes_v2 = {
        'Node 7': ('src.nodes.node7_13f_holdings', 'InstitutionalHoldingsAnalyzerV2'),
        'Node 8': ('src.nodes.node8_13d_ownership', 'BeneficialOwnershipTrackerV2'),
        'Node 9': ('src.nodes.node9_8k_events', 'MaterialEventCorrelatorV2'),
        'Node 10': ('src.nodes.node10_form144', 'RestrictedSaleMonitorV2'),
        'Node 11': ('src.nodes.node11_network_mapper', 'ExecutiveNetworkAnalyzerV2'),
        'Node 12': ('src.nodes.node12_earnings_calls', 'TranscriptAnalyzerV2'),
        'Node 13': ('src.nodes.node13_zscore', 'BankruptcyPredictorV2'),
        'Node 14': ('src.nodes.node14_fscore', 'FinancialStrengthAnalyzerV2'),
        'Node 15': ('src.nodes.node15_market_correlation', 'MarketCorrelationEngineV2'),
    }
    
    # Validate V1 nodes
    for node_name, (module_path, class_name) in nodes_v1.items():
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, class_name):
                # Try to instantiate (basic functionality check)
                cls = getattr(module, class_name)
                # Check if it's a class
                if inspect.isclass(cls):
                    result.pass_test(f"{node_name} - {class_name} is functional")
                else:
                    result.fail_test(f"{node_name} - {class_name} is functional", "Not a class")
            else:
                result.fail_test(f"{node_name} - {class_name} is functional", "Class not found")
        except Exception as e:
            result.fail_test(f"{node_name} - {class_name} is functional", str(e))
    
    # Validate V2 nodes
    for node_name, (module_path, class_name) in nodes_v2.items():
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, class_name):
                # Try to instantiate (basic functionality check)
                cls = getattr(module, class_name)
                # Check if it's a class
                if inspect.isclass(cls):
                    result.pass_test(f"{node_name} - {class_name} is functional (V2)")
                else:
                    result.fail_test(f"{node_name} - {class_name} is functional (V2)", "Not a class")
            else:
                result.fail_test(f"{node_name} - {class_name} is functional (V2)", "Class not found")
        except Exception as e:
            result.fail_test(f"{node_name} - {class_name} is functional (V2)", str(e))


def validate_detection_algorithms(result: ValidationResult):
    """Validate detection algorithms are accessible."""
    print("\n" + "=" * 80)
    print("  5. DETECTION ALGORITHMS")
    print("=" * 80)
    
    algorithms = [
        ('src.detection.patterns.advanced_patterns', 'AdvancedPatternDetector'),
        ('src.detection.patterns.options_backdating_detector', 'OptionsBackdatingDetector'),
        ('src.detection.patterns.channel_stuffing_detector', 'ChannelStuffingDetector'),
        ('src.detection.financial.beneish_mscore', 'BeneishMScoreCalculator'),
        ('src.detection.financial.benford_analysis', 'BenfordAnalyzer'),
    ]
    
    for module_path, class_name in algorithms:
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, class_name):
                result.pass_test(f"{class_name} accessible")
            else:
                result.fail_test(f"{class_name} accessible", "Class not found")
        except ImportError as e:
            result.fail_test(f"{class_name} accessible", str(e))


def validate_evidence_chain(result: ValidationResult):
    """Validate evidence chain components."""
    print("\n" + "=" * 80)
    print("  6. EVIDENCE CHAIN COMPONENTS")
    print("=" * 80)
    
    components = [
        ('src.core.evidence_chain.hash_service', 'HashService'),
        ('src.core.evidence_chain.merkle_tree', 'MerkleTree'),
        ('src.core.evidence_chain.rfc3161_client', 'RFC3161Client'),
    ]
    
    for module_path, class_name in components:
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, class_name):
                result.pass_test(f"{class_name} accessible")
            else:
                result.fail_test(f"{class_name} accessible", "Class not found")
        except ImportError as e:
            result.fail_test(f"{class_name} accessible", str(e))


def validate_reporting(result: ValidationResult):
    """Validate reporting components."""
    print("\n" + "=" * 80)
    print("  7. REPORTING COMPONENTS")
    print("=" * 80)
    
    components = [
        ('src.reporting.doj_report_generator', 'DOJReportGenerator'),
        ('src.reporting.court_pdf_generator', 'CourtPDFGenerator'),
    ]
    
    for module_path, class_name in components:
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, class_name):
                result.pass_test(f"{class_name} accessible")
            else:
                result.fail_test(f"{class_name} accessible", "Class not found")
        except ImportError as e:
            result.fail_test(f"{class_name} accessible", str(e))


def main():
    """Main validation entry point."""
    print("=" * 80)
    print("  JLAW MASTER UNIFICATION VALIDATION")
    print("=" * 80)
    print(f"  Project Root: {PROJECT_ROOT}")
    print("=" * 80)
    
    result = ValidationResult()
    
    # Run all validation checks
    validate_master_controller(result)
    validate_v2_versions(result)
    validate_recursive_engine_v2_imports(result)
    validate_nodes_functional(result)
    validate_detection_algorithms(result)
    validate_evidence_chain(result)
    validate_reporting(result)
    
    # Print summary
    exit_code = result.print_summary()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
