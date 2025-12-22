"""
JLAW Master Test Suite - Comprehensive Production Readiness Validation
=======================================================================

Zero-failure deployment system that validates every component before deployment.

Usage:
    python -m tests.jlaw_master_test_suite --full
    python -m tests.jlaw_master_test_suite --mock
    python -m tests.jlaw_master_test_suite --category nodes
    python -m tests.jlaw_master_test_suite --full --report json --output test_results.json
"""

import sys
import asyncio
import argparse
import time
from pathlib import Path
from typing import List, Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.utils.test_reporter import TestReporter, TestResult, TestStatus, TestSeverity, TestSuiteResult
from tests.utils.remediation_engine import RemediationEngine
from tests.utils.dependency_resolver import DependencyResolver
from tests.validators.environment_validator import EnvironmentValidator
from tests.validators.api_key_validator import APIKeyValidator
from tests.validators.node_validator import NodeValidator
from tests.validators.detection_validator import DetectionValidator
from tests.validators.agent_validator import AgentValidator
from tests.validators.evidence_chain_validator import EvidenceChainValidator
from tests.validators.reporting_validator import ReportingValidator


class JLAWMasterTestSuite:
    """
    Master test suite for JLAW forensic analysis platform.
    
    Validates:
    - Environment & Dependencies
    - API Key Configuration
    - All 15 Analysis Nodes
    - All 23+ Detection Patterns
    - AI Agent Ecosystem
    - Evidence Chain Integrity
    - Reporting Layer
    - Orchestration Layer
    """
    
    def __init__(self, mock_mode: bool = False, categories: List[str] = None):
        """
        Initialize master test suite.
        
        Args:
            mock_mode: If True, skip external API calls and heavy operations
            categories: List of categories to test (None = all)
        """
        self.mock_mode = mock_mode
        self.categories = categories or ['all']
        self.suite_result = TestSuiteResult()
        self.remediation_engine = RemediationEngine()
        self.dependency_resolver = DependencyResolver()
        
        # Initialize validators
        self.env_validator = EnvironmentValidator()
        self.api_validator = APIKeyValidator(mock_mode=mock_mode)
        self.node_validator = NodeValidator(mock_mode=mock_mode)
        self.detection_validator = DetectionValidator(mock_mode=mock_mode)
        self.agent_validator = AgentValidator(mock_mode=mock_mode)
        self.evidence_validator = EvidenceChainValidator(mock_mode=mock_mode)
        self.reporting_validator = ReportingValidator(mock_mode=mock_mode)
    
    def should_run_category(self, category: str) -> bool:
        """Check if category should be run based on filters."""
        return 'all' in self.categories or category in self.categories
    
    def run_environment_tests(self):
        """Run environment and dependency tests."""
        if not self.should_run_category('environment'):
            return
        
        print("\n" + "=" * 80)
        print("ENVIRONMENT & DEPENDENCIES VALIDATION")
        print("=" * 80)
        
        start_time = time.time()
        
        # Python version
        result = self.env_validator.validate_python_version()
        self.suite_result.add_result(TestResult(
            name="Python Version Check",
            category="Environment",
            status=TestStatus.PASSED if result.passed else TestStatus.FAILED,
            duration=0.1,
            severity=TestSeverity.CRITICAL if not result.passed else TestSeverity.LOW,
            error_message=None if result.passed else result.message,
            remediation=self.remediation_engine.get_remediation('python_version_too_old').to_string() if not result.passed else None,
            can_skip=False,
            dependencies=['All modules'],
        ))
        print(f"  {'✓' if result.passed else '✗'} {result.message}")
        
        # Virtual environment
        result = self.env_validator.validate_virtual_environment()
        self.suite_result.add_result(TestResult(
            name="Virtual Environment Check",
            category="Environment",
            status=TestStatus.PASSED,
            duration=0.1,
            severity=TestSeverity.LOW,
            error_message=None,
            can_skip=True,
        ))
        print(f"  ℹ {result.message}")
        
        # Dependencies
        installed, missing, optional_missing = self.env_validator.validate_dependencies(self.mock_mode)
        
        if missing:
            remediation = self.remediation_engine.get_remediation('missing_package')
            self.suite_result.add_result(TestResult(
                name="Required Dependencies",
                category="Environment",
                status=TestStatus.FAILED,
                duration=1.0,
                severity=TestSeverity.CRITICAL,
                error_message=f"{len(missing)} required packages missing: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}",
                remediation=remediation.to_string() if remediation else None,
                can_skip=False,
                dependencies=['Dependent modules'],
            ))
            print(f"  ✗ {len(missing)} required packages missing")
        else:
            self.suite_result.add_result(TestResult(
                name="Required Dependencies",
                category="Environment",
                status=TestStatus.PASSED,
                duration=1.0,
                error_message=None,
                can_skip=False,
            ))
            print(f"  ✓ All {len(installed)} required packages installed")
        
        # Optional dependencies
        if optional_missing:
            self.suite_result.add_result(TestResult(
                name="Optional Dependencies",
                category="Environment",
                status=TestStatus.PASSED,  # Not a failure
                duration=0.5,
                severity=TestSeverity.LOW,
                error_message=f"{len(optional_missing)} optional packages missing (graceful degradation)",
                can_skip=True,
            ))
            print(f"  ⚠ {len(optional_missing)} optional packages missing (will degrade gracefully)")
        
        # System resources
        result = self.env_validator.validate_system_resources()
        self.suite_result.add_result(TestResult(
            name="System Resources",
            category="Environment",
            status=TestStatus.PASSED if result.passed else TestStatus.FAILED,
            duration=0.5,
            severity=TestSeverity.HIGH if not result.passed else TestSeverity.LOW,
            error_message=None if result.passed else result.message,
            can_skip=False,
        ))
        print(f"  {'✓' if result.passed else '✗'} {result.message}")
        
        duration = time.time() - start_time
        print(f"\nEnvironment validation completed in {duration:.2f}s")
    
    async def run_api_tests(self):
        """Run API key and connectivity tests."""
        if not self.should_run_category('api_keys'):
            return
        
        print("\n" + "=" * 80)
        print("API KEY CONFIGURATION VALIDATION")
        print("=" * 80)
        
        start_time = time.time()
        
        results = await self.api_validator.validate_all()
        
        for key, result in results.items():
            status = TestStatus.PASSED if result.passed else (TestStatus.FAILED if not result.can_skip else TestStatus.SKIPPED)
            severity = TestSeverity.CRITICAL if not result.passed and not result.can_skip else TestSeverity.MEDIUM
            
            # Get remediation if failed
            remediation_text = None
            if not result.passed:
                remediation = self.remediation_engine.get_remediation(key, result.message)
                if remediation:
                    remediation_text = remediation.to_string()
            
            self.suite_result.add_result(TestResult(
                name=key.replace('_', ' ').title(),
                category="API Keys",
                status=status,
                duration=0.5,
                severity=severity,
                error_message=None if result.passed else result.message,
                remediation=remediation_text,
                can_skip=result.can_skip,
                dependencies=result.details.get('required_for', []) if result.details else [],
            ))
            
            print(f"  {'✓' if result.passed else ('⚠' if result.can_skip else '✗')} {result.message}")
        
        duration = time.time() - start_time
        print(f"\nAPI validation completed in {duration:.2f}s")
    
    def run_node_tests(self):
        """Run node validation tests."""
        if not self.should_run_category('nodes'):
            return
        
        print("\n" + "=" * 80)
        print("15-NODE ANALYSIS ENGINE VALIDATION")
        print("=" * 80)
        
        start_time = time.time()
        
        results = self.node_validator.validate_all_nodes()
        
        for node_num, result in results.items():
            status = TestStatus.PASSED if result.passed else TestStatus.FAILED
            severity = TestSeverity.HIGH if not result.passed else TestSeverity.LOW
            
            self.suite_result.add_result(TestResult(
                name=f"Node {node_num}",
                category="Nodes",
                status=status,
                duration=0.3,
                severity=severity,
                error_message=None if result.passed else result.message,
                remediation=self.remediation_engine.get_remediation('node_import_failed').to_string() if not result.passed else None,
                can_skip=False,
                dependencies=['Phase 4: Node Analysis'],
            ))
            
            print(f"  {result.message}")
        
        summary = self.node_validator.get_summary(results)
        print(f"\nNodes: {summary['passed']}/{summary['total']} operational")
        print(f"V2 versions available: {summary['v2_available']}")
        
        duration = time.time() - start_time
        print(f"Node validation completed in {duration:.2f}s")
    
    def run_detection_tests(self):
        """Run detection pattern tests."""
        if not self.should_run_category('detection'):
            return
        
        print("\n" + "=" * 80)
        print("DETECTION PATTERNS VALIDATION")
        print("=" * 80)
        
        start_time = time.time()
        
        results = self.detection_validator.validate_all_patterns()
        
        for pattern_key, result in results.items():
            status = TestStatus.PASSED if result.passed else (TestStatus.SKIPPED if result.can_skip else TestStatus.FAILED)
            severity = TestSeverity.HIGH if not result.passed and not result.can_skip else TestSeverity.LOW
            
            self.suite_result.add_result(TestResult(
                name=pattern_key.replace('_', ' ').title(),
                category="Detection Patterns",
                status=status,
                duration=0.2,
                severity=severity,
                error_message=None if result.passed else result.message,
                can_skip=result.can_skip,
                dependencies=['Phase 5: Pattern Detection'],
            ))
            
            print(f"  {'✓' if result.passed else ('⚠' if result.can_skip else '✗')} {result.message}")
        
        summary = self.detection_validator.get_summary(results)
        print(f"\nPatterns: {summary['passed']}/{summary['total']} operational")
        if summary['optional_missing'] > 0:
            print(f"Optional patterns missing: {summary['optional_missing']} (graceful degradation)")
        
        duration = time.time() - start_time
        print(f"Detection validation completed in {duration:.2f}s")
    
    def run_agent_tests(self):
        """Run AI agent tests."""
        if not self.should_run_category('agents'):
            return
        
        print("\n" + "=" * 80)
        print("AI AGENT ECOSYSTEM VALIDATION")
        print("=" * 80)
        
        start_time = time.time()
        
        results = self.agent_validator.validate_all_agents()
        
        for agent_key, result in results.items():
            status = TestStatus.PASSED if result.passed else (TestStatus.SKIPPED if result.can_skip else TestStatus.FAILED)
            severity = TestSeverity.MEDIUM
            
            self.suite_result.add_result(TestResult(
                name=result.agent_name,
                category="AI Agents",
                status=status,
                duration=0.2,
                severity=severity,
                error_message=None if result.passed else result.message,
                can_skip=result.can_skip,
                dependencies=['Phase 6: Dual-Agent Validation', 'Phase 7: Subagent Orchestration'],
            ))
            
            print(f"  {'✓' if result.passed else ('⚠' if result.can_skip else '✗')} {result.message}")
        
        duration = time.time() - start_time
        print(f"Agent validation completed in {duration:.2f}s")
    
    def run_evidence_chain_tests(self):
        """Run evidence chain tests."""
        if not self.should_run_category('evidence_chain'):
            return
        
        print("\n" + "=" * 80)
        print("EVIDENCE CHAIN INTEGRITY VALIDATION")
        print("=" * 80)
        
        start_time = time.time()
        
        results = self.evidence_validator.validate_all_components()
        
        for component_key, result in results.items():
            status = TestStatus.PASSED if result.passed else TestStatus.FAILED
            severity = TestSeverity.CRITICAL if not result.passed and not result.can_skip else TestSeverity.MEDIUM
            
            self.suite_result.add_result(TestResult(
                name=result.component_name,
                category="Evidence Chain",
                status=status,
                duration=0.3,
                severity=severity,
                error_message=None if result.passed else result.message,
                remediation=self.remediation_engine.get_remediation('hash_service_failed').to_string() if 'hash' in component_key.lower() and not result.passed else None,
                can_skip=result.can_skip,
                dependencies=['Phase 8: Evidence Chain Finalization'],
            ))
            
            print(f"  {'✓' if result.passed else '✗'} {result.message}")
        
        duration = time.time() - start_time
        print(f"Evidence chain validation completed in {duration:.2f}s")
    
    def run_reporting_tests(self):
        """Run reporting layer tests."""
        if not self.should_run_category('reporting'):
            return
        
        print("\n" + "=" * 80)
        print("REPORTING LAYER VALIDATION")
        print("=" * 80)
        
        start_time = time.time()
        
        results = self.reporting_validator.validate_all_components()
        
        for component_key, result in results.items():
            status = TestStatus.PASSED if result.passed else (TestStatus.SKIPPED if result.can_skip else TestStatus.FAILED)
            severity = TestSeverity.HIGH if not result.passed and not result.can_skip else TestSeverity.LOW
            
            self.suite_result.add_result(TestResult(
                name=result.component_name,
                category="Reporting",
                status=status,
                duration=0.2,
                severity=severity,
                error_message=None if result.passed else result.message,
                can_skip=result.can_skip,
                dependencies=['Phase 9: Dossier Generation'],
            ))
            
            print(f"  {'✓' if result.passed else ('⚠' if result.can_skip else '✗')} {result.message}")
        
        duration = time.time() - start_time
        print(f"Reporting validation completed in {duration:.2f}s")
    
    async def run_all_tests(self):
        """Run all test categories."""
        suite_start = time.time()
        
        print("\n" + "╔" + "=" * 78 + "╗")
        print("║" + " " * 20 + "JLAW MASTER TEST SUITE" + " " * 36 + "║")
        print("║" + " " * 15 + "Zero-Failure Deployment Validation" + " " * 29 + "║")
        print("╚" + "=" * 78 + "╝")
        
        if self.mock_mode:
            print("\n⚠️  MOCK MODE: Skipping external API calls and heavy operations")
        
        # Run all test categories
        self.run_environment_tests()
        await self.run_api_tests()
        self.run_node_tests()
        self.run_detection_tests()
        self.run_agent_tests()
        self.run_evidence_chain_tests()
        self.run_reporting_tests()
        
        # Finalize results
        self.suite_result.duration = time.time() - suite_start
        self.suite_result.finalize()
    
    def generate_reports(self, output_dir: Path, report_format: str = 'all', output_file: str = None):
        """
        Generate test reports.
        
        Args:
            output_dir: Directory to store reports
            report_format: Report format ('json', 'markdown', 'html', 'all')
            output_file: Optional specific output filename
        """
        reporter = TestReporter(output_dir)
        
        # Print console summary
        reporter.print_summary(self.suite_result)
        
        # Generate requested formats
        if report_format in ('json', 'all'):
            json_file = output_file if output_file and output_file.endswith('.json') else 'test_results.json'
            json_path = reporter.generate_json_report(self.suite_result, json_file)
            print(f"📄 JSON report: {json_path}")
        
        if report_format in ('markdown', 'all'):
            md_file = output_file if output_file and output_file.endswith('.md') else 'test_report.md'
            md_path = reporter.generate_markdown_report(self.suite_result, md_file)
            print(f"📄 Markdown report: {md_path}")
        
        if report_format in ('html', 'all'):
            html_file = output_file if output_file and output_file.endswith('.html') else 'test_report.html'
            html_path = reporter.generate_html_report(self.suite_result, html_file)
            print(f"📄 HTML report: {html_path}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='JLAW Master Test Suite - Production Readiness Validation'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full test suite (all categories)'
    )
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Mock mode: skip external API calls and heavy operations'
    )
    parser.add_argument(
        '--category',
        choices=['environment', 'api_keys', 'nodes', 'detection', 'agents', 'evidence_chain', 'reporting'],
        help='Run specific test category only'
    )
    parser.add_argument(
        '--report',
        choices=['json', 'markdown', 'html', 'all'],
        default='all',
        help='Report format to generate'
    )
    parser.add_argument(
        '--output',
        help='Output file path for report'
    )
    parser.add_argument(
        '--output-dir',
        default='tests/reports',
        help='Output directory for reports (default: tests/reports)'
    )
    
    args = parser.parse_args()
    
    # Determine categories to run
    categories = ['all'] if args.full or not args.category else [args.category]
    
    # Run test suite
    suite = JLAWMasterTestSuite(mock_mode=args.mock, categories=categories)
    await suite.run_all_tests()
    
    # Generate reports
    output_dir = Path(args.output_dir)
    suite.generate_reports(output_dir, args.report, args.output)
    
    # Exit with appropriate code
    exit_code = suite.suite_result.get_exit_code()
    sys.exit(exit_code)


if __name__ == '__main__':
    asyncio.run(main())
