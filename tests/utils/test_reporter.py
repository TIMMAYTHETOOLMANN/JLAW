"""
Test Reporter - Generate comprehensive test reports in multiple formats.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict


class TestSeverity(Enum):
    """Test failure severity levels."""
    CRITICAL = "CRITICAL"  # System cannot run
    HIGH = "HIGH"          # Major functionality broken
    MEDIUM = "MEDIUM"      # Non-critical feature broken
    LOW = "LOW"            # Minor issue, can work around


class TestStatus(Enum):
    """Test execution status."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class TestResult:
    """Individual test result."""
    name: str
    category: str
    status: TestStatus
    duration: float = 0.0
    severity: TestSeverity = TestSeverity.MEDIUM
    error_message: Optional[str] = None
    remediation: Optional[str] = None
    can_skip: bool = False
    dependencies: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'category': self.category,
            'status': self.status.value,
            'duration': self.duration,
            'severity': self.severity.value,
            'error_message': self.error_message,
            'remediation': self.remediation,
            'can_skip': self.can_skip,
            'dependencies': self.dependencies,
            'timestamp': self.timestamp,
        }


@dataclass
class TestSuiteResult:
    """Complete test suite results."""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration: float = 0.0
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    results: List[TestResult] = field(default_factory=list)
    
    def add_result(self, result: TestResult):
        """Add a test result and update counters."""
        self.results.append(result)
        self.total_tests += 1
        
        if result.status == TestStatus.PASSED:
            self.passed += 1
        elif result.status == TestStatus.FAILED:
            self.failed += 1
        elif result.status == TestStatus.SKIPPED:
            self.skipped += 1
        elif result.status == TestStatus.ERROR:
            self.errors += 1
    
    def finalize(self):
        """Finalize suite results."""
        self.end_time = datetime.now().isoformat()
    
    def get_exit_code(self) -> int:
        """
        Get exit code for CI/CD integration.
        
        Returns:
            0: All tests passed, production-ready
            1: Critical failures, cannot deploy
            2: Non-critical failures, can deploy with limitations
            3: Configuration errors, needs user intervention
        """
        if self.passed == self.total_tests:
            return 0
        
        # Check for critical failures
        critical_failures = [
            r for r in self.results
            if r.status in (TestStatus.FAILED, TestStatus.ERROR)
            and r.severity == TestSeverity.CRITICAL
        ]
        
        if critical_failures:
            return 1
        
        # Check for configuration errors
        config_errors = [
            r for r in self.results
            if r.status in (TestStatus.FAILED, TestStatus.ERROR)
            and 'configuration' in r.category.lower()
        ]
        
        if config_errors and self.failed > self.passed:
            return 3
        
        # Non-critical failures
        return 2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'summary': {
                'total_tests': self.total_tests,
                'passed': self.passed,
                'failed': self.failed,
                'skipped': self.skipped,
                'errors': self.errors,
                'duration': self.duration,
                'start_time': self.start_time,
                'end_time': self.end_time,
            },
            'exit_code': self.get_exit_code(),
            'results': [r.to_dict() for r in self.results],
        }


class TestReporter:
    """Generate test reports in multiple formats."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize test reporter.
        
        Args:
            output_dir: Directory to store test reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_json_report(self, suite_result: TestSuiteResult, filename: str = "test_results.json") -> Path:
        """
        Generate JSON test report.
        
        Args:
            suite_result: Test suite results
            filename: Output filename
            
        Returns:
            Path to generated report
        """
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(suite_result.to_dict(), f, indent=2)
        
        return output_path
    
    def generate_markdown_report(self, suite_result: TestSuiteResult, filename: str = "test_report.md") -> Path:
        """
        Generate Markdown test report.
        
        Args:
            suite_result: Test suite results
            filename: Output filename
            
        Returns:
            Path to generated report
        """
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            f.write("# JLAW Master Test Suite Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Total Tests:** {suite_result.total_tests}\n")
            f.write(f"- **Passed:** ✅ {suite_result.passed}\n")
            f.write(f"- **Failed:** ❌ {suite_result.failed}\n")
            f.write(f"- **Skipped:** ⏭️ {suite_result.skipped}\n")
            f.write(f"- **Errors:** ⚠️ {suite_result.errors}\n")
            f.write(f"- **Duration:** {suite_result.duration:.2f}s\n")
            f.write(f"- **Exit Code:** {suite_result.get_exit_code()}\n\n")
            
            # Deployment readiness
            exit_code = suite_result.get_exit_code()
            if exit_code == 0:
                f.write("## ✅ Deployment Status: **PRODUCTION READY**\n\n")
            elif exit_code == 1:
                f.write("## ❌ Deployment Status: **CRITICAL FAILURES - CANNOT DEPLOY**\n\n")
            elif exit_code == 2:
                f.write("## ⚠️ Deployment Status: **CAN DEPLOY WITH LIMITATIONS**\n\n")
            else:
                f.write("## 🔧 Deployment Status: **CONFIGURATION REQUIRED**\n\n")
            
            # Group results by category
            by_category = defaultdict(list)
            for result in suite_result.results:
                by_category[result.category].append(result)
            
            # Results by category
            f.write("## Test Results by Category\n\n")
            for category, results in sorted(by_category.items()):
                passed_count = sum(1 for r in results if r.status == TestStatus.PASSED)
                total_count = len(results)
                
                f.write(f"### {category} ({passed_count}/{total_count} passed)\n\n")
                
                for result in results:
                    status_emoji = {
                        TestStatus.PASSED: "✅",
                        TestStatus.FAILED: "❌",
                        TestStatus.SKIPPED: "⏭️",
                        TestStatus.ERROR: "⚠️",
                    }.get(result.status, "❓")
                    
                    f.write(f"- {status_emoji} **{result.name}** ({result.duration:.2f}s)\n")
                    
                    if result.status in (TestStatus.FAILED, TestStatus.ERROR):
                        f.write(f"  - **Severity:** {result.severity.value}\n")
                        if result.error_message:
                            f.write(f"  - **Error:** {result.error_message}\n")
                        if result.remediation:
                            f.write(f"  - **Fix:** {result.remediation}\n")
                        if result.can_skip:
                            f.write(f"  - **Can Skip:** Yes (system can run without this)\n")
                        if result.dependencies:
                            f.write(f"  - **Impacts:** {', '.join(result.dependencies)}\n")
                    
                    f.write("\n")
            
            # Critical failures section
            critical_failures = [
                r for r in suite_result.results
                if r.status in (TestStatus.FAILED, TestStatus.ERROR)
                and r.severity == TestSeverity.CRITICAL
            ]
            
            if critical_failures:
                f.write("## ⚠️ Critical Failures Requiring Immediate Action\n\n")
                for result in critical_failures:
                    f.write(f"### {result.name}\n\n")
                    f.write(f"**Category:** {result.category}\n\n")
                    f.write(f"**Error:** {result.error_message}\n\n")
                    if result.remediation:
                        f.write(f"**Remediation:**\n\n```bash\n{result.remediation}\n```\n\n")
                    if result.dependencies:
                        f.write(f"**This failure impacts:** {', '.join(result.dependencies)}\n\n")
        
        return output_path
    
    def generate_html_report(self, suite_result: TestSuiteResult, filename: str = "test_report.html") -> Path:
        """
        Generate HTML test report.
        
        Args:
            suite_result: Test suite results
            filename: Output filename
            
        Returns:
            Path to generated report
        """
        output_path = self.output_dir / filename
        
        # Group results by category
        by_category = defaultdict(list)
        for result in suite_result.results:
            by_category[result.category].append(result)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JLAW Test Suite Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .category {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .test-item {{
            padding: 15px;
            border-left: 4px solid #ddd;
            margin-bottom: 10px;
            background: #f9f9f9;
        }}
        .test-item.passed {{ border-color: #10b981; }}
        .test-item.failed {{ border-color: #ef4444; }}
        .test-item.error {{ border-color: #f59e0b; }}
        .test-item.skipped {{ border-color: #6b7280; }}
        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status.passed {{ background: #10b981; color: white; }}
        .status.failed {{ background: #ef4444; color: white; }}
        .status.error {{ background: #f59e0b; color: white; }}
        .status.skipped {{ background: #6b7280; color: white; }}
        .severity {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .severity.CRITICAL {{ background: #dc2626; color: white; }}
        .severity.HIGH {{ background: #f59e0b; color: white; }}
        .severity.MEDIUM {{ background: #3b82f6; color: white; }}
        .severity.LOW {{ background: #6b7280; color: white; }}
        .error-details {{
            margin-top: 10px;
            padding: 10px;
            background: #fee;
            border-radius: 5px;
            font-size: 14px;
        }}
        .remediation {{
            margin-top: 10px;
            padding: 10px;
            background: #eff6ff;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
        }}
        .deployment-status {{
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            font-weight: bold;
            text-align: center;
        }}
        .deployment-status.ready {{ background: #d1fae5; color: #065f46; }}
        .deployment-status.critical {{ background: #fee2e2; color: #991b1b; }}
        .deployment-status.limited {{ background: #fef3c7; color: #92400e; }}
        .deployment-status.config {{ background: #dbeafe; color: #1e40af; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>JLAW Master Test Suite Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""
        
        # Deployment status
        exit_code = suite_result.get_exit_code()
        if exit_code == 0:
            html += '<div class="deployment-status ready">✅ PRODUCTION READY</div>'
        elif exit_code == 1:
            html += '<div class="deployment-status critical">❌ CRITICAL FAILURES - CANNOT DEPLOY</div>'
        elif exit_code == 2:
            html += '<div class="deployment-status limited">⚠️ CAN DEPLOY WITH LIMITATIONS</div>'
        else:
            html += '<div class="deployment-status config">🔧 CONFIGURATION REQUIRED</div>'
        
        # Summary cards
        html += '<div class="summary">'
        html += f'<div class="summary-card"><h3>Total Tests</h3><div class="value">{suite_result.total_tests}</div></div>'
        html += f'<div class="summary-card"><h3>Passed</h3><div class="value" style="color: #10b981;">{suite_result.passed}</div></div>'
        html += f'<div class="summary-card"><h3>Failed</h3><div class="value" style="color: #ef4444;">{suite_result.failed}</div></div>'
        html += f'<div class="summary-card"><h3>Duration</h3><div class="value">{suite_result.duration:.1f}s</div></div>'
        html += '</div>'
        
        # Results by category
        for category, results in sorted(by_category.items()):
            passed_count = sum(1 for r in results if r.status == TestStatus.PASSED)
            html += f'<div class="category">'
            html += f'<h2>{category} ({passed_count}/{len(results)} passed)</h2>'
            
            for result in results:
                status_class = result.status.value.lower()
                html += f'<div class="test-item {status_class}">'
                html += f'<span class="status {status_class}">{result.status.value}</span>'
                
                if result.status in (TestStatus.FAILED, TestStatus.ERROR):
                    html += f'<span class="severity {result.severity.value}">{result.severity.value}</span>'
                
                html += f' <strong>{result.name}</strong> ({result.duration:.2f}s)'
                
                if result.error_message:
                    html += f'<div class="error-details"><strong>Error:</strong> {result.error_message}</div>'
                
                if result.remediation:
                    html += f'<div class="remediation"><strong>Fix:</strong><br>{result.remediation}</div>'
                
                html += '</div>'
            
            html += '</div>'
        
        html += """
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html)
        
        return output_path
    
    def print_summary(self, suite_result: TestSuiteResult):
        """Print test summary to console."""
        print("\n" + "=" * 80)
        print("JLAW MASTER TEST SUITE RESULTS")
        print("=" * 80)
        print(f"\nTotal Tests: {suite_result.total_tests}")
        print(f"✅ Passed:   {suite_result.passed}")
        print(f"❌ Failed:   {suite_result.failed}")
        print(f"⏭️  Skipped:  {suite_result.skipped}")
        print(f"⚠️  Errors:   {suite_result.errors}")
        print(f"⏱️  Duration: {suite_result.duration:.2f}s")
        print(f"\nExit Code: {suite_result.get_exit_code()}")
        
        exit_code = suite_result.get_exit_code()
        if exit_code == 0:
            print("\n✅ DEPLOYMENT STATUS: PRODUCTION READY")
        elif exit_code == 1:
            print("\n❌ DEPLOYMENT STATUS: CRITICAL FAILURES - CANNOT DEPLOY")
        elif exit_code == 2:
            print("\n⚠️ DEPLOYMENT STATUS: CAN DEPLOY WITH LIMITATIONS")
        else:
            print("\n🔧 DEPLOYMENT STATUS: CONFIGURATION REQUIRED")
        
        print("=" * 80 + "\n")
