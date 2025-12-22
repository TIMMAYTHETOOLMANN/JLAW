"""
Remediation Engine - Provide intelligent debugging and fix suggestions.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class RemediationType(Enum):
    """Type of remediation action."""
    COMMAND = "COMMAND"  # Run a command
    CONFIG = "CONFIG"    # Update configuration
    INSTALL = "INSTALL"  # Install package/dependency
    MANUAL = "MANUAL"    # Manual intervention required


@dataclass
class RemediationAdvice:
    """Remediation advice for a test failure."""
    issue: str
    root_cause: str
    remediation_steps: List[str]
    remediation_type: RemediationType
    commands: List[str]
    impact: str
    can_skip: bool
    dependencies_affected: List[str]
    
    def to_string(self) -> str:
        """Convert to human-readable string."""
        lines = [
            f"ISSUE: {self.issue}",
            f"ROOT CAUSE: {self.root_cause}",
            "",
            "REMEDIATION STEPS:",
        ]
        
        for i, step in enumerate(self.remediation_steps, 1):
            lines.append(f"  {i}. {step}")
        
        if self.commands:
            lines.append("")
            lines.append("COMMANDS TO RUN:")
            for cmd in self.commands:
                lines.append(f"  $ {cmd}")
        
        lines.extend([
            "",
            f"IMPACT: {self.impact}",
            f"CAN SKIP: {'Yes - system can run without this' if self.can_skip else 'No - critical for operation'}",
        ])
        
        if self.dependencies_affected:
            lines.append(f"DEPENDENCIES AFFECTED: {', '.join(self.dependencies_affected)}")
        
        return "\n".join(lines)


class RemediationEngine:
    """
    Intelligent debugging and remediation suggestion engine.
    
    Analyzes test failures and provides actionable fix suggestions with:
    - Root cause analysis
    - Specific remediation steps
    - Exact commands to execute
    - Dependency chain impact
    - Severity classification
    - Skip recommendations
    """
    
    def __init__(self):
        """Initialize remediation engine."""
        self.remediation_rules = self._load_remediation_rules()
    
    def _load_remediation_rules(self) -> Dict[str, RemediationAdvice]:
        """Load remediation rules for common failure patterns."""
        return {
            # Python version issues
            "python_version_too_old": RemediationAdvice(
                issue="Python version too old",
                root_cause="JLAW requires Python 3.10+ for async features and type hints",
                remediation_steps=[
                    "Install Python 3.10 or later",
                    "Create a new virtual environment with Python 3.10+",
                    "Reinstall dependencies in new environment",
                ],
                remediation_type=RemediationType.MANUAL,
                commands=[
                    "python3.10 -m venv venv",
                    "source venv/bin/activate",
                    "pip install -r requirements.txt",
                ],
                impact="CRITICAL - System cannot run without Python 3.10+",
                can_skip=False,
                dependencies_affected=["All modules"],
            ),
            
            # Missing dependencies
            "missing_package": RemediationAdvice(
                issue="Required Python package not installed",
                root_cause="Package listed in requirements.txt is not installed in current environment",
                remediation_steps=[
                    "Ensure virtual environment is activated",
                    "Install missing package(s)",
                    "Verify installation",
                ],
                remediation_type=RemediationType.INSTALL,
                commands=[
                    "pip install -r requirements.txt",
                    "pip list | grep <package_name>",
                ],
                impact="HIGH - Affected modules will not function",
                can_skip=False,
                dependencies_affected=["Dependent modules"],
            ),
            
            # SEC EDGAR configuration
            "sec_user_agent_invalid": RemediationAdvice(
                issue="SEC EDGAR User-Agent not configured",
                root_cause="SEC requires User-Agent header with organization name and contact email",
                remediation_steps=[
                    "Copy .env.example to .env",
                    "Update SEC_USER_AGENT with your organization name and email",
                    "Format: 'CompanyName/Version (contact@company.com)'",
                ],
                remediation_type=RemediationType.CONFIG,
                commands=[
                    "cp .env.example .env",
                    "# Edit .env and set SEC_USER_AGENT=YourOrg/1.0 (contact@yourorg.com)",
                ],
                impact="CRITICAL - Cannot access SEC EDGAR API without valid User-Agent",
                can_skip=False,
                dependencies_affected=["All SEC filing analysis nodes (1-6, 7-10)"],
            ),
            
            # OpenAI API
            "openai_api_key_missing": RemediationAdvice(
                issue="OpenAI API key not configured",
                root_cause="OPENAI_API_KEY environment variable not set or contains placeholder",
                remediation_steps=[
                    "Get API key from https://platform.openai.com/api-keys",
                    "Update OPENAI_API_KEY in .env file",
                    "Ensure key starts with 'sk-proj-' or 'sk-'",
                ],
                remediation_type=RemediationType.CONFIG,
                commands=[
                    "# Edit .env and set OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE",
                ],
                impact="HIGH - Dual-agent AI validation will not work",
                can_skip=True,
                dependencies_affected=["Phase 6: Dual-Agent AI Cross-Validation"],
            ),
            
            # Anthropic API
            "anthropic_api_key_missing": RemediationAdvice(
                issue="Anthropic API key not configured",
                root_cause="ANTHROPIC_API_KEY environment variable not set or contains placeholder",
                remediation_steps=[
                    "Get API key from https://console.anthropic.com/settings/keys",
                    "Update ANTHROPIC_API_KEY in .env file",
                    "Ensure key starts with 'sk-ant-'",
                ],
                remediation_type=RemediationType.CONFIG,
                commands=[
                    "# Edit .env and set ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE",
                ],
                impact="HIGH - Subagent orchestration will not work",
                can_skip=True,
                dependencies_affected=["Phase 7: Subagent Orchestration", "Node 12: Earnings Call Analysis"],
            ),
            
            # Neo4j
            "neo4j_connection_failed": RemediationAdvice(
                issue="Neo4j database connection failed",
                root_cause="Neo4j is not running or connection credentials are incorrect",
                remediation_steps=[
                    "Ensure Neo4j is running (docker-compose up -d or systemctl start neo4j)",
                    "Verify connection credentials in .env",
                    "Test connection: bolt://localhost:7687",
                ],
                remediation_type=RemediationType.MANUAL,
                commands=[
                    "docker-compose up -d neo4j",
                    "# OR: systemctl start neo4j",
                    "# Verify credentials in .env: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD",
                ],
                impact="MEDIUM - Node 11 (Executive Network Mapping) will not work",
                can_skip=True,
                dependencies_affected=["Node 11: Executive Network Analysis"],
            ),
            
            # TimescaleDB
            "timescaledb_connection_failed": RemediationAdvice(
                issue="TimescaleDB connection failed",
                root_cause="PostgreSQL/TimescaleDB is not running or connection credentials are incorrect",
                remediation_steps=[
                    "Ensure TimescaleDB is running",
                    "Verify connection credentials in .env",
                    "Create database if it doesn't exist",
                ],
                remediation_type=RemediationType.MANUAL,
                commands=[
                    "docker-compose up -d timescaledb",
                    "# OR: systemctl start postgresql",
                    "psql -U postgres -c 'CREATE DATABASE jlaw_forensics;'",
                ],
                impact="MEDIUM - Time-series analysis features will not work",
                can_skip=True,
                dependencies_affected=["Node 15: Market Correlation", "Time-series storage"],
            ),
            
            # Polygon.io
            "polygon_api_key_missing": RemediationAdvice(
                issue="Polygon.io API key not configured",
                root_cause="POLYGON_API_KEY environment variable not set",
                remediation_steps=[
                    "Get API key from https://polygon.io/dashboard/api-keys",
                    "Update POLYGON_API_KEY in .env file",
                ],
                remediation_type=RemediationType.CONFIG,
                commands=[
                    "# Edit .env and set POLYGON_API_KEY=YOUR_KEY_HERE",
                ],
                impact="MEDIUM - Node 15 (Market Correlation) will not work",
                can_skip=True,
                dependencies_affected=["Node 15: Market Correlation Engine"],
            ),
            
            # Heavy ML dependencies
            "torch_not_available": RemediationAdvice(
                issue="PyTorch not available",
                root_cause="PyTorch installation failed or not compatible with system",
                remediation_steps=[
                    "Install PyTorch using official installation instructions",
                    "Visit https://pytorch.org/get-started/locally/ for platform-specific instructions",
                    "System will gracefully degrade without PyTorch",
                ],
                remediation_type=RemediationType.INSTALL,
                commands=[
                    "# For CPU-only: pip install torch --index-url https://download.pytorch.org/whl/cpu",
                    "# For CUDA: Visit https://pytorch.org for platform-specific command",
                ],
                impact="LOW - System will degrade gracefully, XGBoost models will still work",
                can_skip=True,
                dependencies_affected=["DeBERTa Contradiction Detector", "Some advanced ML patterns"],
            ),
            
            # DeBERTa
            "deberta_not_available": RemediationAdvice(
                issue="DeBERTa model not available",
                root_cause="Transformers library or DeBERTa model not properly installed",
                remediation_steps=[
                    "Install transformers library",
                    "System will gracefully degrade without DeBERTa",
                    "Alternative NLP methods will be used",
                ],
                remediation_type=RemediationType.INSTALL,
                commands=[
                    "pip install transformers>=4.30.0",
                ],
                impact="LOW - System degrades gracefully, alternative NLP methods used",
                can_skip=True,
                dependencies_affected=["Node 12: DeBERTa Contradiction Detection"],
            ),
            
            # Node import failures
            "node_import_failed": RemediationAdvice(
                issue="Node module import failed",
                root_cause="Node implementation file is missing or has syntax errors",
                remediation_steps=[
                    "Check if node file exists in src/nodes/",
                    "Verify Python syntax in node file",
                    "Check for missing dependencies",
                    "Review import statements",
                ],
                remediation_type=RemediationType.MANUAL,
                commands=[
                    "python -m py_compile src/nodes/node<N>_*/analyzer.py",
                ],
                impact="HIGH - Affected node will not function",
                can_skip=False,
                dependencies_affected=["Dependent nodes and patterns"],
            ),
            
            # Detection pattern failures
            "pattern_detector_failed": RemediationAdvice(
                issue="Detection pattern failed to load",
                root_cause="Pattern detector module has errors or missing dependencies",
                remediation_steps=[
                    "Check if pattern file exists in src/detection/",
                    "Verify all required dependencies are installed",
                    "Check for missing data files or models",
                ],
                remediation_type=RemediationType.MANUAL,
                commands=[
                    "python -c 'from src.detection.patterns import <PatternName>'",
                ],
                impact="MEDIUM - Specific fraud pattern will not be detected",
                can_skip=True,
                dependencies_affected=["Phase 5: Pattern Detection"],
            ),
            
            # Evidence chain
            "hash_service_failed": RemediationAdvice(
                issue="Evidence chain hash service failed",
                root_cause="Cryptography library issue or hash algorithm not supported",
                remediation_steps=[
                    "Reinstall cryptography package",
                    "Verify Python version supports required hash algorithms",
                ],
                remediation_type=RemediationType.INSTALL,
                commands=[
                    "pip install --upgrade cryptography",
                ],
                impact="CRITICAL - Evidence chain integrity cannot be guaranteed",
                can_skip=False,
                dependencies_affected=["Phase 8: Evidence Chain Finalization", "All forensic output"],
            ),
        }
    
    def get_remediation(self, error_category: str, error_message: str = "") -> Optional[RemediationAdvice]:
        """
        Get remediation advice for a specific error.
        
        Args:
            error_category: Category of error (from error patterns)
            error_message: Detailed error message
            
        Returns:
            RemediationAdvice or None if no remediation found
        """
        # Try exact match first
        if error_category in self.remediation_rules:
            return self.remediation_rules[error_category]
        
        # Try pattern matching in error message
        error_lower = error_message.lower()
        
        if "python" in error_lower and "version" in error_lower:
            return self.remediation_rules["python_version_too_old"]
        elif "modulenotfounderror" in error_lower or "importerror" in error_lower:
            return self.remediation_rules["missing_package"]
        elif "sec_user_agent" in error_lower:
            return self.remediation_rules["sec_user_agent_invalid"]
        elif "openai" in error_lower and "api" in error_lower:
            return self.remediation_rules["openai_api_key_missing"]
        elif "anthropic" in error_lower and "api" in error_lower:
            return self.remediation_rules["anthropic_api_key_missing"]
        elif "neo4j" in error_lower:
            return self.remediation_rules["neo4j_connection_failed"]
        elif "timescale" in error_lower or "postgres" in error_lower:
            return self.remediation_rules["timescaledb_connection_failed"]
        elif "polygon" in error_lower:
            return self.remediation_rules["polygon_api_key_missing"]
        elif "torch" in error_lower or "pytorch" in error_lower:
            return self.remediation_rules["torch_not_available"]
        elif "deberta" in error_lower:
            return self.remediation_rules["deberta_not_available"]
        elif "node" in error_lower and "import" in error_lower:
            return self.remediation_rules["node_import_failed"]
        elif "hash" in error_lower or "merkle" in error_lower:
            return self.remediation_rules["hash_service_failed"]
        
        return None
    
    def generate_remediation_report(self, failures: List[Dict]) -> str:
        """
        Generate comprehensive remediation report for multiple failures.
        
        Args:
            failures: List of failure dictionaries with 'category' and 'message'
            
        Returns:
            Formatted remediation report
        """
        lines = [
            "=" * 80,
            "JLAW MASTER TEST SUITE - REMEDIATION REPORT",
            "=" * 80,
            "",
            f"Total Failures: {len(failures)}",
            "",
        ]
        
        for i, failure in enumerate(failures, 1):
            category = failure.get('category', 'unknown')
            message = failure.get('message', '')
            
            remediation = self.get_remediation(category, message)
            
            lines.append(f"[{i}] {failure.get('name', 'Unknown Test')}")
            lines.append("-" * 80)
            
            if remediation:
                lines.append(remediation.to_string())
            else:
                lines.extend([
                    f"ISSUE: {message}",
                    "ROOT CAUSE: Unknown - manual investigation required",
                    "",
                    "SUGGESTED STEPS:",
                    "  1. Check error logs for detailed stack trace",
                    "  2. Verify all dependencies are installed",
                    "  3. Review configuration files",
                    "  4. Consult JLAW documentation",
                ])
            
            lines.append("")
            lines.append("")
        
        lines.extend([
            "=" * 80,
            "END OF REMEDIATION REPORT",
            "=" * 80,
        ])
        
        return "\n".join(lines)
