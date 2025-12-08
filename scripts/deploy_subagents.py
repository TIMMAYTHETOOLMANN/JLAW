#!/usr/bin/env python3
"""
Deploy and verify VoltAgent Claude Code subagents for JLAW forensic platform.

This script:
1. Verifies the .claude/agents/ directory structure
2. Checks that all subagent files exist and are properly formatted
3. Validates frontmatter YAML in each subagent file
4. Provides status reporting on subagent deployment

Usage:
    python scripts/deploy_subagents.py
    python scripts/deploy_subagents.py --verbose
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import re

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class SubagentDeployer:
    """Deploy and verify VoltAgent subagents."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = PROJECT_ROOT
        self.claude_dir = self.project_root / ".claude"
        self.agents_dir = self.claude_dir / "agents"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with appropriate level."""
        prefix = {
            "INFO": "ℹ",
            "SUCCESS": "✓",
            "WARNING": "⚠",
            "ERROR": "✗"
        }.get(level, "•")
        
        if level == "ERROR":
            self.errors.append(message)
        elif level == "WARNING":
            self.warnings.append(message)
            
        if self.verbose or level in ["SUCCESS", "ERROR"]:
            print(f"{prefix} {message}")
    
    def verify_directory_structure(self) -> bool:
        """Verify the required directory structure exists."""
        self.log("Verifying directory structure...")
        
        required_dirs = [
            self.agents_dir / "forensic",
            self.agents_dir / "infrastructure",
            self.agents_dir / "development",
            self.agents_dir / "orchestration"
        ]
        
        all_exist = True
        for directory in required_dirs:
            if directory.exists() and directory.is_dir():
                self.log(f"Found: {directory.relative_to(self.project_root)}", "SUCCESS")
            else:
                self.log(f"Missing: {directory.relative_to(self.project_root)}", "ERROR")
                all_exist = False
                
        return all_exist
    
    def parse_frontmatter(self, file_path: Path) -> Tuple[bool, Dict]:
        """Parse YAML frontmatter from markdown file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # Extract frontmatter between --- markers
            pattern = r'^---\s*\n(.*?)\n---\s*\n'
            match = re.match(pattern, content, re.DOTALL)
            
            if not match:
                self.log(f"No frontmatter found in {file_path.name}", "ERROR")
                return False, {}
            
            frontmatter_yaml = match.group(1)
            frontmatter = yaml.safe_load(frontmatter_yaml)
            
            # Validate required fields
            required_fields = ["name", "description", "tools"]
            for field in required_fields:
                if field not in frontmatter:
                    self.log(
                        f"Missing '{field}' in frontmatter of {file_path.name}",
                        "ERROR"
                    )
                    return False, {}
            
            return True, frontmatter
            
        except Exception as e:
            self.log(f"Error parsing {file_path.name}: {e}", "ERROR")
            return False, {}
    
    def verify_subagent_file(self, file_path: Path) -> bool:
        """Verify a single subagent file."""
        self.log(f"Checking {file_path.relative_to(self.agents_dir)}...", "INFO")
        
        # Check file exists
        if not file_path.exists():
            self.log(f"File not found: {file_path.name}", "ERROR")
            return False
        
        # Check UTF-8 encoding
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            self.log(f"File is not UTF-8 encoded: {file_path.name}", "ERROR")
            return False
        
        # Parse and validate frontmatter
        valid, frontmatter = self.parse_frontmatter(file_path)
        if not valid:
            return False
        
        # Validate tools format
        tools = frontmatter.get("tools", "")
        if isinstance(tools, str):
            tool_list = [t.strip() for t in tools.split(",")]
        else:
            tool_list = tools
            
        valid_tools = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch"]
        for tool in tool_list:
            if tool not in valid_tools:
                self.log(
                    f"Unknown tool '{tool}' in {file_path.name}. Valid: {valid_tools}",
                    "WARNING"
                )
        
        # Check content length
        if len(content) < 1000:
            self.log(
                f"File {file_path.name} seems too short ({len(content)} chars)",
                "WARNING"
            )
        
        self.log(f"✓ {file_path.name} validated", "SUCCESS")
        return True
    
    def verify_all_subagents(self) -> bool:
        """Verify all required subagent files."""
        self.log("\nVerifying subagent files...")
        
        expected_files = {
            "forensic": [
                "forensic-nlp-analyst.md",
                "forensic-financial-analyst.md",
                "forensic-research-specialist.md",
                "forensic-compliance-auditor.md"
            ],
            "orchestration": [
                "forensic-workflow-orchestrator.md",
                "multi-agent-coordinator.md",
                "context-manager.md"
            ],
            "infrastructure": [
                "devops-engineer.md",
                "security-engineer.md",
                "database-administrator.md",
                "cloud-architect.md"
            ],
            "development": [
                "python-pro.md",
                "backend-developer.md",
                "documentation-engineer.md"
            ]
        }
        
        all_valid = True
        for category, files in expected_files.items():
            self.log(f"\n{category.upper()} Subagents:", "INFO")
            for filename in files:
                file_path = self.agents_dir / category / filename
                if not self.verify_subagent_file(file_path):
                    all_valid = False
        
        return all_valid
    
    def generate_status_report(self) -> Dict:
        """Generate a comprehensive status report."""
        report = {
            "status": "SUCCESS" if not self.errors else "FAILED",
            "total_subagents": 0,
            "validated_subagents": 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "categories": {}
        }
        
        # Count subagents by category
        for category_dir in self.agents_dir.iterdir():
            if category_dir.is_dir():
                md_files = list(category_dir.glob("*.md"))
                report["categories"][category_dir.name] = {
                    "count": len(md_files),
                    "files": [f.name for f in md_files]
                }
                report["total_subagents"] += len(md_files)
        
        report["validated_subagents"] = report["total_subagents"] - len(self.errors)
        
        return report
    
    def print_summary(self, report: Dict):
        """Print deployment summary."""
        print("\n" + "=" * 70)
        print("VOLTAGENT SUBAGENT DEPLOYMENT SUMMARY")
        print("=" * 70)
        print(f"Status: {report['status']}")
        print(f"Total Subagents: {report['total_subagents']}")
        print(f"Validated: {report['validated_subagents']}")
        print(f"Errors: {len(report['errors'])}")
        print(f"Warnings: {len(report['warnings'])}")
        print()
        
        print("Subagents by Category:")
        for category, info in report["categories"].items():
            print(f"  {category}: {info['count']} subagents")
            if self.verbose:
                for filename in info["files"]:
                    print(f"    - {filename}")
        
        if report["errors"]:
            print("\nErrors:")
            for error in report["errors"]:
                print(f"  ✗ {error}")
        
        if report["warnings"]:
            print("\nWarnings:")
            for warning in report["warnings"]:
                print(f"  ⚠ {warning}")
        
        print("\n" + "=" * 70)
        
        if report["status"] == "SUCCESS":
            print("✓ All subagents deployed and verified successfully!")
        else:
            print("✗ Deployment completed with errors. Please review above.")
        print("=" * 70)
    
    def deploy(self) -> bool:
        """Main deployment and verification process."""
        print("VoltAgent Subagent Deployment Tool")
        print(f"Project Root: {self.project_root}")
        print()
        
        # Step 1: Verify directory structure
        if not self.verify_directory_structure():
            self.log("Directory structure verification failed!", "ERROR")
            return False
        
        # Step 2: Verify all subagent files
        if not self.verify_all_subagents():
            self.log("Subagent file verification failed!", "ERROR")
        
        # Step 3: Generate and print report
        report = self.generate_status_report()
        self.print_summary(report)
        
        return report["status"] == "SUCCESS"


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Deploy and verify VoltAgent subagents for JLAW"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    deployer = SubagentDeployer(verbose=args.verbose)
    success = deployer.deploy()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
