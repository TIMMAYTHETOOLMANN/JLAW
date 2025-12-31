"""
Violation Category Formatter - Phase 4
=======================================

Generates deduplicated, aggregated violation findings by category.
"""

from typing import Dict, Any, List
from collections import defaultdict


class ViolationCategoryFormatter:
    """Formats violation findings grouped by category."""
    
    @staticmethod
    def format(violations: List[Dict[str, Any]]) -> str:
        """
        Format violations grouped by type/category.
        
        Args:
            violations: List of violation dictionaries
        
        Returns:
            Formatted violations string
        """
        lines = []
        
        # Section header
        lines.append("─" * 80)
        lines.append("  SECTION 2: VIOLATION ANALYSIS BY CATEGORY")
        lines.append("─" * 80)
        lines.append("")
        
        # Group violations by type
        violations_by_type = defaultdict(list)
        for violation in violations:
            vtype = violation.get('violation_type', 'UNKNOWN')
            violations_by_type[vtype].append(violation)
        
        # Sort by number of violations (descending)
        sorted_types = sorted(
            violations_by_type.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        # Format each category
        for vtype, vlist in sorted_types:
            lines.append(f"◆ {vtype} ({len(vlist)} violations)")
            lines.append("")
            
            # Calculate aggregate confidence
            avg_confidence = sum(v.get('confidence', 0) for v in vlist) / len(vlist)
            
            lines.append(f"  Average Confidence: {avg_confidence:.1%}")
            lines.append("")
            
            # List unique statutes
            unique_statutes = set()
            for v in vlist:
                for statute in v.get('statutes', []):
                    unique_statutes.add(statute['code'])
            
            lines.append("  Applicable Statutes:")
            for statute in sorted(unique_statutes):
                lines.append(f"    • {statute}")
            lines.append("")
            
            # Enforcement pathways
            pathways = set(v.get('enforcement_pathway', 'UNKNOWN') for v in vlist)
            lines.append(f"  Enforcement Pathways: {', '.join(sorted(pathways))}")
            lines.append("")
            
            # Top violations (by confidence)
            top_violations = sorted(vlist, key=lambda x: x.get('confidence', 0), reverse=True)[:3]
            lines.append(f"  Top {len(top_violations)} Violations:")
            for i, v in enumerate(top_violations, 1):
                lines.append(f"    {i}. {v.get('violation_id', 'N/A')} (Confidence: {v.get('confidence', 0):.1%})")
            lines.append("")
            
            lines.append("  ─" * 40)
            lines.append("")
        
        return "\n".join(lines)
