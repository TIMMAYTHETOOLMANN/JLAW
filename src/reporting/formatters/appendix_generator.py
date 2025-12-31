"""
Appendix Generator - Phase 4 Enhanced
=====================================

Generates appendices A-D for the prosecutorial dossier with proper formatting:

Appendices:
- A: Complete Violation Evidence Records (per-violation boxes)
- B: 15-Node Recursive Engine Analysis Matrix (table format)
- C: Raw SEC Filing Index (chronological list)
- D: Algorithm Execution Log (23 patterns status)
"""

from typing import Dict, Any, List
from .format_constants import (
    DOUBLE_LINE,
    SUBSECTION_DIVIDER,
    APPENDIX_A_TITLE,
    APPENDIX_B_TITLE,
    APPENDIX_C_TITLE,
    APPENDIX_D_TITLE,
    STATUS_COMPLETE,
    STATUS_FAILED,
    STATUS_INCOMPLETE,
    BOX_SINGLE_HORIZONTAL,
    BOX_SINGLE_VERTICAL,
    STANDARD_WIDTH,
)


class AppendixGenerator:
    """Generates enhanced appendices for prosecutorial dossiers."""
    
    @staticmethod
    def format_all(appendices_data: Dict[str, Any]) -> str:
        """
        Format all appendices with enhanced formatting.
        
        Args:
            appendices_data: Dictionary with appendix_a, appendix_b, appendix_c, appendix_d
        
        Returns:
            Formatted appendices string
        """
        lines = []
        
        # Appendix A
        lines.extend(AppendixGenerator._format_appendix_a(appendices_data.get('appendix_a', {})))
        lines.append("")
        lines.append("")
        
        # Appendix B
        lines.extend(AppendixGenerator._format_appendix_b(appendices_data.get('appendix_b', {})))
        lines.append("")
        lines.append("")
        
        # Appendix C
        lines.extend(AppendixGenerator._format_appendix_c(appendices_data.get('appendix_c', {})))
        lines.append("")
        lines.append("")
        
        # Appendix D
        lines.extend(AppendixGenerator._format_appendix_d(appendices_data.get('appendix_d', {})))
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_appendix_a(data: Dict[str, Any]) -> List[str]:
        """Format Appendix A: Complete Violation Evidence Records with per-violation boxes."""
        lines = []
        
        lines.append(DOUBLE_LINE)
        lines.append(APPENDIX_A_TITLE)
        lines.append(DOUBLE_LINE)
        lines.append("")
        
        violations = data.get('violations', data.get('primary_violations', []))
        
        lines.append(f"Total Violations Documented: {len(violations)}")
        lines.append("")
        
        if not violations:
            lines.append("No violations recorded.")
            return lines
        
        # Format each violation in a box
        for i, violation in enumerate(violations[:50], 1):  # Limit to first 50
            lines.extend(AppendixGenerator._format_violation_box(violation, i))
            lines.append("")
        
        if len(violations) > 50:
            lines.append(f"... and {len(violations) - 50} additional violations (see full JSON export)")
            lines.append("")
        
        return lines
    
    @staticmethod
    def _format_violation_box(violation: Dict[str, Any], index: int) -> List[str]:
        """Format a single violation in a box."""
        lines = []
        
        box_width = STANDARD_WIDTH - 4
        
        lines.append(f"┌{'─' * box_width}┐")
        lines.append(f"│ VIOLATION #{index}: {violation.get('violation_type', 'UNKNOWN'):<{box_width - 18}} │")
        lines.append(f"├{'─' * box_width}┤")
        lines.append(f"│ Violation ID:     {violation.get('violation_id', 'N/A'):<{box_width - 20}} │")
        lines.append(f"│ Confidence:       {violation.get('confidence', 0):.1%:<{box_width - 20}} │")
        lines.append(f"│ Severity:         {violation.get('severity', 'UNKNOWN'):<{box_width - 20}} │")
        
        # Statutes
        statutes = violation.get('statutes', [])
        if statutes:
            lines.append(f"│ Statutes:{' ' * (box_width - 11)}│")
            for statute in statutes[:3]:  # First 3 statutes
                code = statute.get('code', 'N/A')[:box_width - 20]
                lines.append(f"│   • {code:<{box_width - 7}} │")
        
        # Evidence hash
        evidence_hash = violation.get('evidence_hash', 'N/A')
        if evidence_hash and evidence_hash != 'N/A':
            hash_display = evidence_hash[:box_width - 20]
            lines.append(f"│ Evidence Hash:    {hash_display:<{box_width - 20}} │")
        
        lines.append(f"└{'─' * box_width}┘")
        
        return lines
    
    @staticmethod
    def _format_appendix_b(data: Dict[str, Any]) -> List[str]:
        """Format Appendix B: 15-Node Recursive Engine Analysis Matrix in table format."""
        lines = []
        
        lines.append(DOUBLE_LINE)
        lines.append(APPENDIX_B_TITLE)
        lines.append(DOUBLE_LINE)
        lines.append("")
        
        exec_summary = data.get('execution_summary', {})
        total_nodes = exec_summary.get('total_nodes', 15)
        successful = exec_summary.get('successful_nodes', 0)
        failed = exec_summary.get('failed_nodes', 0)
        
        lines.append(f"Total Nodes:      {total_nodes}")
        lines.append(f"Successful:       {successful} ({STATUS_COMPLETE})")
        lines.append(f"Failed:           {failed} ({STATUS_FAILED if failed > 0 else STATUS_COMPLETE})")
        lines.append(f"Success Rate:     {(successful / total_nodes * 100) if total_nodes > 0 else 0:.1f}%")
        lines.append("")
        
        # Node execution matrix table
        lines.append("NODE EXECUTION MATRIX:")
        lines.append("")
        lines.append(f"┌{'─' * 30}┬{'─' * 12}┬{'─' * 10}┬{'─' * 20}┐")
        lines.append(f"│ {'Node Name':<29}│ {'Status':<11}│ {'Findings':<9}│ {'Exec Time (s)':<19}│")
        lines.append(f"├{'─' * 30}┼{'─' * 12}┼{'─' * 10}┼{'─' * 20}┤")
        
        node_results = data.get('node_results', {})
        
        # Define standard node order
        standard_nodes = [
            'Node 1: Form 4 Insider Trading',
            'Node 2: DEF 14A Compensation',
            'Node 3: 10-Q Consistency',
            'Node 4: 10-K SOX Certification',
            'Node 5: IRC §83 Tax Exposure',
            'Node 6: Enforcement Routing',
            'Node 7: 13F Holdings',
            'Node 8: Beneficial Ownership',
            'Node 9: 8-K Material Events',
            'Node 10: Form 144 Sales',
            'Node 11: Executive Networks',
            'Node 12: Earnings Transcripts',
            'Node 13: Z-Score Bankruptcy',
            'Node 14: F-Score Financial',
            'Node 15: Market Correlation',
        ]
        
        # Display results
        for node_name in standard_nodes:
            result = node_results.get(node_name, node_results.get(node_name.split(':')[0], {}))
            
            status = result.get('status', 'NOT_RUN')
            status_symbol = STATUS_COMPLETE if status == 'success' else STATUS_FAILED if status == 'error' else STATUS_INCOMPLETE
            status_display = f"{status_symbol} {status.upper()}"
            
            findings = result.get('violations_found', result.get('findings_count', 0))
            exec_time = result.get('execution_time', 0.0)
            
            node_short = node_name[:29]
            lines.append(f"│ {node_short:<29}│ {status_display:<11}│ {findings:>9}│ {exec_time:>19.2f}│")
        
        lines.append(f"└{'─' * 30}┴{'─' * 12}┴{'─' * 10}┴{'─' * 20}┘")
        
        return lines
    
    @staticmethod
    def _format_appendix_c(data: Dict[str, Any]) -> List[str]:
        """Format Appendix C: Raw SEC Filing Index in chronological list."""
        lines = []
        
        lines.append(DOUBLE_LINE)
        lines.append(APPENDIX_C_TITLE)
        lines.append(DOUBLE_LINE)
        lines.append("")
        
        filings = data.get('filings', [])
        
        if not filings:
            lines.append("No SEC filings indexed.")
            return lines
        
        lines.append(f"Total Filings: {len(filings)}")
        lines.append("")
        
        # Sort chronologically (most recent first)
        sorted_filings = sorted(
            filings,
            key=lambda x: x.get('filing_date', ''),
            reverse=True
        )
        
        lines.append("CHRONOLOGICAL INDEX:")
        lines.append("")
        lines.append(f"┌{'─' * 12}┬{'─' * 15}┬{'─' * 45}┐")
        lines.append(f"│ {'Filing Date':<11}│ {'Form Type':<14}│ {'Accession Number':<44}│")
        lines.append(f"├{'─' * 12}┼{'─' * 15}┼{'─' * 45}┤")
        
        for filing in sorted_filings[:100]:  # First 100
            date = filing.get('filing_date', 'N/A')[:11]
            form_type = filing.get('form_type', 'N/A')[:14]
            accession = filing.get('accession_number', 'N/A')[:44]
            
            lines.append(f"│ {date:<11}│ {form_type:<14}│ {accession:<44}│")
        
        lines.append(f"└{'─' * 12}┴{'─' * 15}┴{'─' * 45}┘")
        
        if len(filings) > 100:
            lines.append("")
            lines.append(f"... and {len(filings) - 100} additional filings")
        
        return lines
    
    @staticmethod
    def _format_appendix_d(data: Dict[str, Any]) -> List[str]:
        """Format Appendix D: Algorithm Execution Log for 23 detection patterns."""
        lines = []
        
        lines.append(DOUBLE_LINE)
        lines.append(APPENDIX_D_TITLE)
        lines.append(DOUBLE_LINE)
        lines.append("")
        
        algorithms = data.get('algorithms', {})
        
        if not algorithms:
            lines.append("No algorithm execution data available.")
            return lines
        
        total_algorithms = len(algorithms)
        successful = sum(1 for algo in algorithms.values() if algo.get('status') == 'success')
        failed = sum(1 for algo in algorithms.values() if algo.get('status') == 'error')
        
        lines.append(f"Total Detection Algorithms: {total_algorithms}")
        lines.append(f"Successfully Executed:      {successful} ({STATUS_COMPLETE})")
        lines.append(f"Failed:                     {failed} ({STATUS_FAILED if failed > 0 else STATUS_COMPLETE})")
        lines.append(f"Success Rate:               {(successful / total_algorithms * 100) if total_algorithms > 0 else 0:.1f}%")
        lines.append("")
        
        lines.append("ALGORITHM EXECUTION LOG:")
        lines.append("")
        lines.append(f"┌{'─' * 35}┬{'─' * 12}┬{'─' * 10}┬{'─' * 15}┐")
        lines.append(f"│ {'Algorithm Name':<34}│ {'Status':<11}│ {'Detections':<9}│ {'Exec Time (s)':<14}│")
        lines.append(f"├{'─' * 35}┼{'─' * 12}┼{'─' * 10}┼{'─' * 15}┤")
        
        # Sort by status (failed first) then by name
        sorted_algos = sorted(
            algorithms.items(),
            key=lambda x: (x[1].get('status') != 'error', x[0])
        )
        
        for algo_name, algo_data in sorted_algos:
            status = algo_data.get('status', 'UNKNOWN')
            status_symbol = STATUS_COMPLETE if status == 'success' else STATUS_FAILED if status == 'error' else STATUS_INCOMPLETE
            status_display = f"{status_symbol} {status.upper()}"
            
            detections = algo_data.get('detections', 0)
            exec_time = algo_data.get('execution_time', 0.0)
            
            algo_short = algo_name[:34]
            lines.append(f"│ {algo_short:<34}│ {status_display:<11}│ {detections:>9}│ {exec_time:>14.2f}│")
        
        lines.append(f"└{'─' * 35}┴{'─' * 12}┴{'─' * 10}┴{'─' * 15}┘")
        
        return lines

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
