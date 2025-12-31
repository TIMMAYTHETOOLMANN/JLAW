"""
Executive Briefing Formatter - Phase 4 Enhanced
===============================================

Generates structured intelligence briefing with:
- Threat assessment box with visual risk bar
- Key findings at a glance with prosecutorial relevance
- Investigation priority matrix table
"""

from typing import Dict, Any, List
from .format_constants import (
    SUBSECTION_DIVIDER,
    SECTION_1_TITLE,
    STATUS_KEY_FINDING,
    STATUS_ACTION_REQUIRED,
    get_severity_indicator,
    create_progress_bar,
    create_box_header,
    create_box_footer,
    create_box_line,
    BOX_SINGLE_VERTICAL,
    BOX_SINGLE_VERTICAL_RIGHT,
    BOX_SINGLE_VERTICAL_LEFT,
    BOX_SINGLE_HORIZONTAL,
    STANDARD_WIDTH,
)


class ExecutiveBriefingFormatter:
    """Formats executive intelligence briefing with visual threat indicators."""
    
    @staticmethod
    def format(exec_summary: Dict[str, Any]) -> str:
        """
        Format executive intelligence briefing per specification.
        
        Args:
            exec_summary: Executive summary dictionary with:
                - threat_level: CRITICAL/HIGH/MEDIUM/LOW
                - threat_statement: Primary threat assessment
                - total_violations: Total violation count
                - critical_violations: Critical violation count
                - high_violations: High violation count
                - total_actors: Number of actors involved
                - key_findings: List of key findings with relevance
                - enforcement_recommendation: Recommendation text
                - primary_enforcement_agencies: List of agencies
                - priority_matrix: Dict of priority tiers
        
        Returns:
            Formatted intelligence briefing string
        """
        lines = []
        
        # Section header
        lines.append(SUBSECTION_DIVIDER)
        lines.append(SECTION_1_TITLE)
        lines.append(SUBSECTION_DIVIDER)
        lines.append("")
        
        # Threat Assessment Box
        lines.extend(ExecutiveBriefingFormatter._format_threat_assessment(exec_summary))
        lines.append("")
        
        # Key Findings at a Glance
        lines.extend(ExecutiveBriefingFormatter._format_key_findings(exec_summary))
        lines.append("")
        
        # Investigation Priority Matrix
        lines.extend(ExecutiveBriefingFormatter._format_priority_matrix(exec_summary))
        lines.append("")
        
        # Enforcement Recommendation
        lines.append(f"{STATUS_ACTION_REQUIRED} ENFORCEMENT RECOMMENDATION:")
        lines.append("")
        lines.append(exec_summary.get('enforcement_recommendation', 'No recommendation available.'))
        lines.append("")
        
        # Primary enforcement agencies
        agencies = exec_summary.get('primary_enforcement_agencies', [])
        if agencies:
            lines.append(f"{STATUS_ACTION_REQUIRED} PRIMARY ENFORCEMENT AGENCIES:")
            lines.append("")
            for agency in agencies:
                lines.append(f"  • {agency}")
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_threat_assessment(exec_summary: Dict[str, Any]) -> List[str]:
        """Format threat assessment box with visual risk bar."""
        lines = []
        
        threat_level = exec_summary.get('threat_level', 'UNKNOWN')
        threat_bar = get_severity_indicator(threat_level)
        total_violations = exec_summary.get('total_violations', 0)
        critical_violations = exec_summary.get('critical_violations', 0)
        high_violations = exec_summary.get('high_violations', 0)
        
        box_width = STANDARD_WIDTH - 4
        
        lines.append(f"┌{'─' * box_width}┐")
        lines.append(f"│ {'THREAT ASSESSMENT':<{box_width - 2}} │")
        lines.append(f"├{'─' * box_width}┤")
        lines.append(f"│ Threat Level: {threat_level:<{box_width - 17}} {threat_bar} │")
        lines.append(f"│{' ' * box_width}│")
        
        # Threat statement (word-wrapped)
        threat_statement = exec_summary.get('threat_statement', 'No statement available.')
        wrapped_lines = ExecutiveBriefingFormatter._wrap_text(threat_statement, box_width - 4)
        for wrapped_line in wrapped_lines:
            lines.append(f"│  {wrapped_line:<{box_width - 2}}│")
        
        lines.append(f"│{' ' * box_width}│")
        lines.append(f"├{'─' * box_width}┤")
        lines.append(f"│ KEY METRICS{' ' * (box_width - 13)}│")
        lines.append(f"│{' ' * box_width}│")
        
        # Metrics with progress bars
        crit_bar = create_progress_bar(critical_violations, total_violations if total_violations > 0 else 1, 20)
        high_bar = create_progress_bar(high_violations, total_violations if total_violations > 0 else 1, 20)
        
        lines.append(f"│  Total Violations:      {total_violations:>4}{' ' * (box_width - 30)}│")
        lines.append(f"│  Critical Violations:   {critical_violations:>4} {crit_bar}{' ' * (box_width - 52)}│")
        lines.append(f"│  High Violations:       {high_violations:>4} {high_bar}{' ' * (box_width - 52)}│")
        lines.append(f"│  Total Actors:          {exec_summary.get('total_actors', 0):>4}{' ' * (box_width - 30)}│")
        lines.append(f"└{'─' * box_width}┘")
        
        return lines
    
    @staticmethod
    def _format_key_findings(exec_summary: Dict[str, Any]) -> List[str]:
        """Format key findings at a glance with prosecutorial relevance."""
        lines = []
        
        lines.append(f"{STATUS_KEY_FINDING} KEY FINDINGS AT A GLANCE:")
        lines.append("")
        
        key_findings = exec_summary.get('key_findings', [])
        if not key_findings:
            # Generate default findings from summary data
            key_findings = ExecutiveBriefingFormatter._generate_default_findings(exec_summary)
        
        for i, finding in enumerate(key_findings[:5], 1):  # Top 5 findings
            finding_text = finding.get('finding', finding) if isinstance(finding, dict) else finding
            relevance = finding.get('relevance', '') if isinstance(finding, dict) else ''
            
            lines.append(f"  {i}. {finding_text}")
            if relevance:
                lines.append(f"     → Prosecutorial Relevance: {relevance}")
            lines.append("")
        
        return lines
    
    @staticmethod
    def _format_priority_matrix(exec_summary: Dict[str, Any]) -> List[str]:
        """Format investigation priority matrix table."""
        lines = []
        
        lines.append("INVESTIGATION PRIORITY MATRIX:")
        lines.append("")
        
        box_width = STANDARD_WIDTH - 4
        lines.append(f"┌{'─' * 15}┬{'─' * 10}┬{'─' * (box_width - 27)}┐")
        lines.append(f"│ {'Priority Tier':<14}│ {'Count':<9}│ {'Description':<{box_width - 28}}│")
        lines.append(f"├{'─' * 15}┼{'─' * 10}┼{'─' * (box_width - 27)}┤")
        
        # Get priority data
        priority_matrix = exec_summary.get('priority_matrix', {})
        critical_count = priority_matrix.get('CRITICAL', exec_summary.get('critical_violations', 0))
        high_count = priority_matrix.get('HIGH', exec_summary.get('high_violations', 0))
        medium_count = priority_matrix.get('MEDIUM', 0)
        low_count = priority_matrix.get('LOW', 0)
        
        lines.append(f"│ {'CRITICAL':<14}│ {critical_count:>9}│ {'Immediate DOJ/SEC action required':<{box_width - 28}}│")
        lines.append(f"│ {'HIGH':<14}│ {high_count:>9}│ {'Priority enforcement investigation':<{box_width - 28}}│")
        lines.append(f"│ {'MEDIUM':<14}│ {medium_count:>9}│ {'Standard compliance review':<{box_width - 28}}│")
        lines.append(f"│ {'LOW':<14}│ {low_count:>9}│ {'Monitoring and documentation':<{box_width - 28}}│")
        lines.append(f"└{'─' * 15}┴{'─' * 10}┴{'─' * (box_width - 27)}┘")
        
        return lines
    
    @staticmethod
    def _generate_default_findings(exec_summary: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate default key findings from summary data."""
        findings = []
        
        critical = exec_summary.get('critical_violations', 0)
        if critical > 0:
            findings.append({
                'finding': f"{critical} critical violations of federal securities law identified",
                'relevance': "Establishes prosecutable violations under 15 USC § 78"
            })
        
        actors = exec_summary.get('total_actors', 0)
        if actors > 0:
            findings.append({
                'finding': f"{actors} actors involved in violation patterns",
                'relevance': "Identifies potential defendants for enforcement action"
            })
        
        threat_level = exec_summary.get('threat_level', '')
        if threat_level in ['CRITICAL', 'HIGH']:
            findings.append({
                'finding': f"Threat assessment: {threat_level}",
                'relevance': "Warrants immediate regulatory attention"
            })
        
        return findings
    
    @staticmethod
    def _wrap_text(text: str, width: int) -> List[str]:
        """Wrap text to specified width."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + (1 if current_line else 0)
            if current_length + word_length <= width:
                current_line.append(word)
                current_length += word_length
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
