"""
Cover Sheet Formatter - Phase 4
================================

Generates confidential cover sheet with case metadata using Unicode box drawing.

Format:
  ═══════════════════════════════════════════════════════════════════════════
    PROSECUTORIAL FORENSIC DOSSIER
    ** CONFIDENTIAL - LAW ENFORCEMENT USE ONLY **
  ═══════════════════════════════════════════════════════════════════════════
"""

from datetime import datetime
from typing import Dict, Any


class CoverSheetFormatter:
    """Formats cover sheet for prosecutorial dossiers."""
    
    @staticmethod
    def format(case_data: Dict[str, Any]) -> str:
        """
        Format cover sheet with case metadata.
        
        Args:
            case_data: Dictionary with keys: case_id, company_name, cik,
                      generation_date, dossier_type, rim_compliance_status
        
        Returns:
            Formatted cover sheet string
        """
        lines = []
        
        # Header
        lines.append("═" * 80)
        lines.append("  PROSECUTORIAL FORENSIC DOSSIER".center(80))
        lines.append("  ** CONFIDENTIAL - LAW ENFORCEMENT USE ONLY **".center(80))
        lines.append("═" * 80)
        lines.append("")
        
        # Case metadata
        lines.append("┌─────────────────────────────────────────────────────────────────────────────┐")
        lines.append("│ CASE INFORMATION                                                             │")
        lines.append("├─────────────────────────────────────────────────────────────────────────────┤")
        lines.append(f"│ Case ID:          {case_data.get('case_id', 'N/A'):<60} │")
        lines.append(f"│ Company:          {case_data.get('company_name', 'N/A'):<60} │")
        lines.append(f"│ CIK:              {case_data.get('cik', 'N/A'):<60} │")
        lines.append(f"│ Generated:        {case_data.get('generation_date', 'N/A'):<60} │")
        lines.append(f"│ Dossier Type:     {case_data.get('dossier_type', 'N/A'):<60} │")
        lines.append(f"│ RIM Compliance:   {case_data.get('rim_compliance_status', 'N/A'):<60} │")
        lines.append("└─────────────────────────────────────────────────────────────────────────────┘")
        lines.append("")
        
        # Classification warning
        lines.append("┌─────────────────────────────────────────────────────────────────────────────┐")
        lines.append("│ CLASSIFICATION & DISTRIBUTION                                                │")
        lines.append("├─────────────────────────────────────────────────────────────────────────────┤")
        lines.append("│ ▓▓▓ CONFIDENTIAL ▓▓▓                                                         │")
        lines.append("│                                                                              │")
        lines.append("│ This document contains privileged and confidential information intended     │")
        lines.append("│ solely for law enforcement use. Unauthorized disclosure, copying, or        │")
        lines.append("│ distribution is strictly prohibited.                                        │")
        lines.append("│                                                                              │")
        lines.append("│ Distribution: DOJ, SEC, IRS enforcement personnel only                       │")
        lines.append("└─────────────────────────────────────────────────────────────────────────────┘")
        lines.append("")
        
        return "\n".join(lines)
