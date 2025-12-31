"""
Appendix Generator - Phase 4
=============================

Generates appendices A-D for the prosecutorial dossier.

Appendices:
- A: Complete Violation Evidence Records
- B: 15-Node Recursive Engine Analysis Matrix
- C: Raw SEC Filing Index
- D: Algorithm Execution Log
"""

from typing import Dict, Any, List


class AppendixGenerator:
    """Generates appendices for prosecutorial dossiers."""
    
    @staticmethod
    def format_all(appendices_data: Dict[str, Any]) -> str:
        """
        Format all appendices.
        
        Args:
            appendices_data: Dictionary with appendix_a, appendix_b, appendix_c, appendix_d
        
        Returns:
            Formatted appendices string
        """
        lines = []
        
        # Appendix A
        lines.extend(AppendixGenerator._format_appendix_a(appendices_data.get('appendix_a', {})))
        lines.append("")
        
        # Appendix B
        lines.extend(AppendixGenerator._format_appendix_b(appendices_data.get('appendix_b', {})))
        lines.append("")
        
        # Appendix C
        lines.extend(AppendixGenerator._format_appendix_c(appendices_data.get('appendix_c', {})))
        lines.append("")
        
        # Appendix D
        lines.extend(AppendixGenerator._format_appendix_d(appendices_data.get('appendix_d', {})))
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_appendix_a(data: Dict[str, Any]) -> List[str]:
        """Format Appendix A: Complete Violation Evidence Records."""
        lines = []
        
        lines.append("═" * 80)
        lines.append("  APPENDIX A: COMPLETE VIOLATION EVIDENCE RECORDS")
        lines.append("═" * 80)
        lines.append("")
        
        lines.append(f"Total Primary Violations: {len(data.get('primary_violations', []))}")
        lines.append(f"Total Secondary Findings: {data.get('secondary_findings', 0)}")
        lines.append(f"Total Tertiary Findings: {data.get('tertiary_findings', 0)}")
        lines.append("")
        
        # List primary violations (truncated)
        primary = data.get('primary_violations', [])
        if primary:
            lines.append("Primary Violations (first 10):")
            for i, v in enumerate(primary[:10], 1):
                violation_id = v.get('violation_id', 'N/A')
                violation_type = v.get('violation_type', 'N/A')
                lines.append(f"  {i}. {violation_id}: {violation_type}")
            if len(primary) > 10:
                lines.append(f"  ... and {len(primary) - 10} more")
        
        return lines
    
    @staticmethod
    def _format_appendix_b(data: Dict[str, Any]) -> List[str]:
        """Format Appendix B: 15-Node Recursive Engine Analysis Matrix."""
        lines = []
        
        lines.append("═" * 80)
        lines.append("  APPENDIX B: 15-NODE RECURSIVE ENGINE ANALYSIS MATRIX")
        lines.append("═" * 80)
        lines.append("")
        
        exec_summary = data.get('execution_summary', {})
        lines.append(f"Total Nodes Executed: {exec_summary.get('total_nodes', 0)}")
        lines.append(f"Successful Nodes: {exec_summary.get('successful_nodes', 0)}")
        lines.append(f"Failed Nodes: {exec_summary.get('failed_nodes', 0)}")
        lines.append("")
        
        # List node results (truncated)
        node_results = data.get('node_results', {})
        if node_results:
            lines.append("Node Execution Results:")
            for node_name, result in sorted(node_results.items())[:10]:
                status = result.get('status', 'unknown')
                lines.append(f"  • {node_name}: {status}")
            if len(node_results) > 10:
                lines.append(f"  ... and {len(node_results) - 10} more")
        
        return lines
    
    @staticmethod
    def _format_appendix_c(data: Dict[str, Any]) -> List[str]:
        """Format Appendix C: Raw SEC Filing Index."""
        lines = []
        
        lines.append("═" * 80)
        lines.append("  APPENDIX C: RAW SEC FILING INDEX")
        lines.append("═" * 80)
        lines.append("")
        
        lines.append(f"Total Filings Analyzed: {data.get('total_filings', 0)}")
        lines.append("")
        
        # List filings (truncated)
        filings = data.get('filings_analyzed', [])
        if filings:
            lines.append("Filings Analyzed (first 20):")
            for i, filing in enumerate(filings[:20], 1):
                if isinstance(filing, dict):
                    form_type = filing.get('form_type', 'N/A')
                    filing_date = filing.get('filing_date', 'N/A')
                    lines.append(f"  {i}. {form_type} - {filing_date}")
                else:
                    lines.append(f"  {i}. {filing}")
            if len(filings) > 20:
                lines.append(f"  ... and {len(filings) - 20} more")
        
        return lines
    
    @staticmethod
    def _format_appendix_d(data: Dict[str, Any]) -> List[str]:
        """Format Appendix D: Algorithm Execution Log."""
        lines = []
        
        lines.append("═" * 80)
        lines.append("  APPENDIX D: ALGORITHM EXECUTION LOG")
        lines.append("═" * 80)
        lines.append("")
        
        lines.append(f"Total Patterns Executed: {data.get('total_patterns', 0)}")
        lines.append("")
        
        # List patterns (truncated)
        patterns = data.get('patterns_executed', [])
        if patterns:
            lines.append("Patterns Executed (first 20):")
            for i, pattern in enumerate(patterns[:20], 1):
                if isinstance(pattern, dict):
                    pattern_name = pattern.get('name', 'N/A')
                    status = pattern.get('status', 'N/A')
                    lines.append(f"  {i}. {pattern_name}: {status}")
                else:
                    lines.append(f"  {i}. {pattern}")
            if len(patterns) > 20:
                lines.append(f"  ... and {len(patterns) - 20} more")
        
        return lines
