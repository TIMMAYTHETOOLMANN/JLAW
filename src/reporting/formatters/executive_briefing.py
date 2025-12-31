"""
Executive Briefing Formatter - Phase 4
=======================================

Generates visual threat assessment with progress bars using Unicode characters.
"""

from typing import Dict, Any, List


class ExecutiveBriefingFormatter:
    """Formats executive briefing section with visual threat indicators."""
    
    @staticmethod
    def format(exec_summary: Dict[str, Any]) -> str:
        """
        Format executive briefing with visual threat assessment.
        
        Args:
            exec_summary: Executive summary dictionary
        
        Returns:
            Formatted briefing string
        """
        lines = []
        
        # Section header
        lines.append("─" * 80)
        lines.append("  SECTION 1: EXECUTIVE FORENSIC SUMMARY")
        lines.append("─" * 80)
        lines.append("")
        
        # Threat level indicator
        threat_level = exec_summary.get('threat_level', 'UNKNOWN')
        threat_indicators = {
            'CRITICAL': '▓▓▓▓▓',
            'HIGH': '▓▓▓▓░',
            'MEDIUM': '▓▓▓░░',
            'LOW': '▓▓░░░',
        }
        threat_bar = threat_indicators.get(threat_level, '░░░░░')
        
        lines.append(f"◆ THREAT LEVEL: {threat_level} {threat_bar}")
        lines.append("")
        lines.append(exec_summary.get('threat_statement', 'No statement available.'))
        lines.append("")
        
        # Key metrics with progress bars
        lines.append("┌─────────────────────────────────────────────────────────────────────────────┐")
        lines.append("│ KEY METRICS                                                                  │")
        lines.append("├─────────────────────────────────────────────────────────────────────────────┤")
        
        total_violations = exec_summary.get('total_violations', 0)
        critical_violations = exec_summary.get('critical_violations', 0)
        high_violations = exec_summary.get('high_violations', 0)
        total_actors = exec_summary.get('total_actors', 0)
        
        lines.append(f"│ Total Violations:       {total_violations:>3}                                         │")
        lines.append(f"│ Critical Violations:    {critical_violations:>3} {ExecutiveBriefingFormatter._progress_bar(critical_violations, total_violations if total_violations > 0 else 1):<40} │")
        lines.append(f"│ High Violations:        {high_violations:>3} {ExecutiveBriefingFormatter._progress_bar(high_violations, total_violations if total_violations > 0 else 1):<40} │")
        lines.append(f"│ Total Actors:           {total_actors:>3}                                         │")
        lines.append("└─────────────────────────────────────────────────────────────────────────────┘")
        lines.append("")
        
        # Enforcement recommendation
        lines.append("► ENFORCEMENT RECOMMENDATION:")
        lines.append("")
        lines.append(exec_summary.get('enforcement_recommendation', 'No recommendation available.'))
        lines.append("")
        
        # Primary enforcement agencies
        agencies = exec_summary.get('primary_enforcement_agencies', [])
        if agencies:
            lines.append("► PRIMARY ENFORCEMENT AGENCIES:")
            lines.append("")
            for agency in agencies:
                lines.append(f"  • {agency}")
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _progress_bar(value: int, total: int, width: int = 20) -> str:
        """Generate Unicode progress bar."""
        if total == 0:
            return '░' * width
        
        filled = int((value / total) * width)
        return '▓' * filled + '░' * (width - filled)
