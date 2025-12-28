"""
JLAW CLI Output Formatter
==========================

Console output formatting using Rich library for enhanced readability.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None


class OutputFormatter:
    """Format and display analysis results with rich console output."""
    
    @staticmethod
    def print_header(console: Optional[Console] = None):
        """Print JLAW header banner."""
        if not RICH_AVAILABLE or console is None:
            print("=" * 70)
            print("JLAW - Justice Law Analytics Workbench")
            print("DOJ-Grade SEC Forensic Analysis Platform")
            print("=" * 70)
            return
        
        header_text = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║              JLAW - Justice Law Analytics Workbench             ║
║                                                                  ║
║           DOJ-Grade SEC Forensic Analysis Platform              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """
        console.print(header_text, style="bold cyan")
    
    @staticmethod
    def print_analysis_summary(result: Any, console: Optional[Console] = None):
        """
        Print analysis summary with results.
        
        Args:
            result: Analysis result object
            console: Rich console instance
        """
        if not RICH_AVAILABLE or console is None:
            # Fallback to plain text
            OutputFormatter._print_analysis_summary_plain(result)
            return
        
        # Create summary table
        table = Table(title="Analysis Summary", box=box.ROUNDED)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        # Add rows
        if hasattr(result, 'target_cik'):
            table.add_row("Target CIK", result.target_cik)
        if hasattr(result, 'target_company'):
            table.add_row("Company", result.target_company)
        if hasattr(result, 'status'):
            status_style = "green" if result.status == "success" else "red"
            table.add_row("Status", f"[{status_style}]{result.status}[/{status_style}]")
        if hasattr(result, 'total_violations'):
            table.add_row("Total Violations", str(result.total_violations))
        if hasattr(result, 'execution_time'):
            table.add_row("Execution Time", f"{result.execution_time:.2f}s")
        
        console.print(table)
        
        # Print phase results if available
        if hasattr(result, 'phases') and result.phases:
            OutputFormatter._print_phase_tree(result.phases, console)
    
    @staticmethod
    def _print_analysis_summary_plain(result: Any):
        """Print analysis summary in plain text."""
        print("\n" + "=" * 70)
        print("ANALYSIS SUMMARY")
        print("=" * 70)
        
        if hasattr(result, 'target_cik'):
            print(f"Target CIK: {result.target_cik}")
        if hasattr(result, 'target_company'):
            print(f"Company: {result.target_company}")
        if hasattr(result, 'status'):
            print(f"Status: {result.status}")
        if hasattr(result, 'total_violations'):
            print(f"Total Violations: {result.total_violations}")
        if hasattr(result, 'execution_time'):
            print(f"Execution Time: {result.execution_time:.2f}s")
        
        print("=" * 70)
    
    @staticmethod
    def _print_phase_tree(phases: Dict[str, Any], console: Console):
        """Print phase execution tree."""
        tree = Tree("📊 Execution Phases", guide_style="cyan")
        
        for phase_name, phase_data in phases.items():
            status = phase_data.get('status', 'unknown')
            emoji = "✅" if status == "success" else "❌" if status == "failed" else "⚠️"
            
            phase_node = tree.add(f"{emoji} {phase_name}")
            
            if 'duration' in phase_data:
                phase_node.add(f"⏱️  Duration: {phase_data['duration']:.2f}s")
            if 'findings' in phase_data:
                phase_node.add(f"🔍 Findings: {phase_data['findings']}")
        
        console.print(tree)
    
    @staticmethod
    def print_execution_plan(plan: Any, console: Optional[Console] = None):
        """
        Print execution plan for dry-run mode.
        
        Args:
            plan: Execution plan object
            console: Rich console instance
        """
        if not RICH_AVAILABLE or console is None:
            OutputFormatter._print_execution_plan_plain(plan)
            return
        
        console.print("\n[bold cyan]📋 Execution Plan[/bold cyan]\n")
        
        # Create phases table
        table = Table(title="Planned Phases", box=box.ROUNDED)
        table.add_column("Phase", style="cyan", no_wrap=True)
        table.add_column("Nodes", style="yellow")
        table.add_column("Est. Time", style="green")
        
        if hasattr(plan, 'phases'):
            for phase in plan.phases:
                table.add_row(
                    phase.get('name', 'Unknown'),
                    str(phase.get('node_count', 0)),
                    f"~{phase.get('estimated_time', 0)}s"
                )
        
        console.print(table)
        
        # Print nodes
        if hasattr(plan, 'nodes'):
            console.print(f"\n[bold]Total Nodes: {len(plan.nodes)}[/bold]")
            for node in plan.nodes:
                console.print(f"  • {node}")
    
    @staticmethod
    def _print_execution_plan_plain(plan: Any):
        """Print execution plan in plain text."""
        print("\n" + "=" * 70)
        print("EXECUTION PLAN")
        print("=" * 70)
        
        if hasattr(plan, 'phases'):
            print("\nPlanned Phases:")
            for i, phase in enumerate(plan.phases, 1):
                print(f"  {i}. {phase.get('name', 'Unknown')}")
                print(f"     Nodes: {phase.get('node_count', 0)}")
                print(f"     Est. Time: ~{phase.get('estimated_time', 0)}s")
        
        if hasattr(plan, 'nodes'):
            print(f"\nTotal Nodes: {len(plan.nodes)}")
            for node in plan.nodes:
                print(f"  • {node}")
        
        print("=" * 70)
    
    @staticmethod
    def print_error(message: str, console: Optional[Console] = None):
        """Print error message."""
        if not RICH_AVAILABLE or console is None:
            print(f"ERROR: {message}")
            return
        
        console.print(f"[red]❌ Error:[/red] {message}")
    
    @staticmethod
    def print_warning(message: str, console: Optional[Console] = None):
        """Print warning message."""
        if not RICH_AVAILABLE or console is None:
            print(f"WARNING: {message}")
            return
        
        console.print(f"[yellow]⚠️  Warning:[/yellow] {message}")
    
    @staticmethod
    def print_success(message: str, console: Optional[Console] = None):
        """Print success message."""
        if not RICH_AVAILABLE or console is None:
            print(f"SUCCESS: {message}")
            return
        
        console.print(f"[green]✅ Success:[/green] {message}")
    
    @staticmethod
    def print_info(message: str, console: Optional[Console] = None):
        """Print info message."""
        if not RICH_AVAILABLE or console is None:
            print(f"INFO: {message}")
            return
        
        console.print(f"[cyan]ℹ️  Info:[/cyan] {message}")
