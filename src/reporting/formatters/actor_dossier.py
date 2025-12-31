"""
Actor Dossier Formatter - Phase 4
==================================

Generates individual actor profiles with activity summaries.
"""

from typing import Dict, Any, List


class ActorDossierFormatter:
    """Formats individual actor dossier sections."""
    
    @staticmethod
    def format(actor_data: Dict[str, Any]) -> str:
        """
        Format actor dossier section.
        
        Args:
            actor_data: Actor profile dictionary
        
        Returns:
            Formatted actor dossier string
        """
        lines = []
        
        # Actor header
        actor_name = actor_data.get('actor_name', 'Unknown')
        risk_score = actor_data.get('risk_score', 0)
        risk_indicator = ActorDossierFormatter._risk_indicator(risk_score)
        
        lines.append("┌─────────────────────────────────────────────────────────────────────────────┐")
        lines.append(f"│ {risk_indicator} ACTOR: {actor_name:<68} │")
        lines.append("├─────────────────────────────────────────────────────────────────────────────┤")
        
        # Basic information
        lines.append(f"│ Actor ID:         {actor_data.get('actor_id', 'N/A'):<60} │")
        lines.append(f"│ Actor Type:       {actor_data.get('actor_type', 'N/A'):<60} │")
        lines.append(f"│ CIK:              {actor_data.get('cik', 'N/A'):<60} │")
        lines.append(f"│ Risk Score:       {risk_score:.1f}/100 {ActorDossierFormatter._progress_bar(int(risk_score), 100):<40} │")
        lines.append("├─────────────────────────────────────────────────────────────────────────────┤")
        
        # Roles
        roles = actor_data.get('roles', [])
        if roles:
            lines.append(f"│ Roles:            {', '.join(roles):<60} │")
        
        # Activity summary
        lines.append(f"│ Total Violations: {actor_data.get('total_violations', 0):<60} │")
        lines.append(f"│ Evidence Items:   {actor_data.get('evidence_items', 0):<60} │")
        lines.append(f"│ Interrogation:    {'✓ Available' if actor_data.get('has_interrogation_package') else '✗ Not Available':<60} │")
        
        lines.append("└─────────────────────────────────────────────────────────────────────────────┘")
        lines.append("")
        
        # Primary statutes
        statutes = actor_data.get('primary_statutes', [])
        if statutes:
            lines.append("  PRIMARY STATUTES:")
            for statute in statutes:
                lines.append(f"    • {statute}")
            lines.append("")
        
        # Violation IDs (truncated)
        violation_ids = actor_data.get('violation_ids', [])
        if violation_ids:
            lines.append(f"  VIOLATIONS ({len(violation_ids)} total):")
            for vid in violation_ids[:5]:  # Show first 5
                lines.append(f"    • {vid}")
            if len(violation_ids) > 5:
                lines.append(f"    ... and {len(violation_ids) - 5} more")
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _risk_indicator(risk_score: float) -> str:
        """Generate risk level indicator."""
        if risk_score >= 80:
            return "▓▓▓"
        elif risk_score >= 60:
            return "▓▓░"
        elif risk_score >= 40:
            return "▓░░"
        else:
            return "░░░"
    
    @staticmethod
    def _progress_bar(value: int, total: int, width: int = 20) -> str:
        """Generate Unicode progress bar."""
        if total == 0:
            return '░' * width
        
        filled = int((value / total) * width)
        return '▓' * filled + '░' * (width - filled)
