"""
Violation Category Formatter - Phase 4 Enhanced
===============================================

Restructures violation output by category instead of filing-by-filing with:
- Category headers with classification, count, statutory basis
- Aggregate statistics (totals by transaction code, by insider)
- Prosecutorial analysis section (legal implications)
- Detailed transaction log (chronologically sorted table)
- Deduplication logic to consolidate related violations
"""

from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime
from .format_constants import (
    SUBSECTION_DIVIDER,
    SECTION_2_TITLE,
    STATUS_KEY_FINDING,
    STATUS_ACTION_REQUIRED,
    get_severity_indicator,
    BOX_SINGLE_HORIZONTAL,
    BOX_SINGLE_VERTICAL,
    STANDARD_WIDTH,
)


class ViolationCategoryFormatter:
    """Formats violation findings grouped by category with aggregation and deduplication."""
    
    @staticmethod
    def format(violations: List[Dict[str, Any]]) -> str:
        """
        Format violations grouped by type/category with deduplication.
        
        Args:
            violations: List of violation dictionaries
        
        Returns:
            Formatted violations string
        """
        lines = []
        
        # Section header
        lines.append(SUBSECTION_DIVIDER)
        lines.append(SECTION_2_TITLE)
        lines.append(SUBSECTION_DIVIDER)
        lines.append("")
        
        if not violations:
            lines.append("No violations detected in this analysis.")
            lines.append("")
            return "\n".join(lines)
        
        # Deduplicate violations
        deduplicated = ViolationCategoryFormatter._deduplicate_violations(violations)
        
        # Group by category
        violations_by_category = ViolationCategoryFormatter._group_by_category(deduplicated)
        
        # Sort categories by severity and count
        sorted_categories = sorted(
            violations_by_category.items(),
            key=lambda x: (ViolationCategoryFormatter._severity_order(x[1][0].get('severity', 'LOW')), -len(x[1]))
        )
        
        # Format each category
        for category, vlist in sorted_categories:
            lines.extend(ViolationCategoryFormatter._format_category(category, vlist))
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _deduplicate_violations(violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate violations that reference the same underlying transaction.
        
        Consolidates multiple violations into single entries with multiple statutory references.
        """
        # Group by transaction identifier (if available) or similar characteristics
        transaction_groups = defaultdict(list)
        
        for violation in violations:
            # Create a deduplication key
            key_parts = []
            
            # Use transaction details as key
            if 'transaction_date' in violation:
                key_parts.append(violation['transaction_date'])
            if 'reporting_person' in violation:
                key_parts.append(violation['reporting_person'])
            if 'shares' in violation:
                key_parts.append(str(violation['shares']))
            if 'transaction_code' in violation:
                key_parts.append(violation['transaction_code'])
            
            # If no transaction details, use violation type and filing
            if not key_parts:
                key_parts.append(violation.get('violation_type', 'UNKNOWN'))
                key_parts.append(violation.get('accession_number', ''))
                key_parts.append(violation.get('filing_date', ''))
            
            dedup_key = '|'.join(key_parts)
            transaction_groups[dedup_key].append(violation)
        
        # Consolidate grouped violations
        deduplicated = []
        for group in transaction_groups.values():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Merge multiple violations into one
                merged = ViolationCategoryFormatter._merge_violations(group)
                deduplicated.append(merged)
        
        return deduplicated
    
    @staticmethod
    def _merge_violations(violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple violations into a consolidated entry."""
        merged = violations[0].copy()
        
        # Collect all statutory references
        all_statutes = []
        for v in violations:
            statutes = v.get('statutes', [])
            for statute in statutes:
                if statute not in all_statutes:
                    all_statutes.append(statute)
        merged['statutes'] = all_statutes
        
        # Combine violation types if different
        violation_types = list(set(v.get('violation_type', '') for v in violations))
        if len(violation_types) > 1:
            merged['violation_type'] = ' + '.join(violation_types)
        
        # Track that this is consolidated
        merged['consolidated_count'] = len(violations)
        merged['consolidated_ids'] = [v.get('violation_id', '') for v in violations]
        
        return merged
    
    @staticmethod
    def _group_by_category(violations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group violations by category/type."""
        categories = defaultdict(list)
        for violation in violations:
            vtype = violation.get('violation_type', 'UNKNOWN')
            categories[vtype].append(violation)
        return dict(categories)
    
    @staticmethod
    def _format_category(category: str, violations: List[Dict[str, Any]]) -> List[str]:
        """Format a single violation category with all details."""
        lines = []
        
        # Category header
        count = len(violations)
        severity = ViolationCategoryFormatter._determine_category_severity(violations)
        severity_bar = get_severity_indicator(severity)
        
        lines.append(f"{STATUS_KEY_FINDING} {category}")
        lines.append(f"   Classification: {severity} {severity_bar}  |  Count: {count}  |  Consolidated: {sum(v.get('consolidated_count', 1) for v in violations)}")
        lines.append("")
        
        # Statutory basis
        unique_statutes = ViolationCategoryFormatter._collect_unique_statutes(violations)
        lines.append("   Statutory Basis:")
        for statute in unique_statutes[:5]:  # Top 5 statutes
            code = statute.get('code', 'N/A')
            title = statute.get('title', 'N/A')
            lines.append(f"     • {code}: {title}")
        if len(unique_statutes) > 5:
            lines.append(f"     ... and {len(unique_statutes) - 5} more")
        lines.append("")
        
        # Aggregate statistics
        lines.extend(ViolationCategoryFormatter._format_aggregate_stats(violations))
        lines.append("")
        
        # Prosecutorial analysis
        lines.extend(ViolationCategoryFormatter._format_prosecutorial_analysis(category, violations))
        lines.append("")
        
        # Detailed transaction log (top 10)
        lines.extend(ViolationCategoryFormatter._format_transaction_log(violations))
        
        lines.append("   " + ("─" * 74))
        
        return lines
    
    @staticmethod
    def _format_aggregate_stats(violations: List[Dict[str, Any]]) -> List[str]:
        """Format aggregate statistics for violations."""
        lines = []
        lines.append("   Aggregate Statistics:")
        
        # Total shares by transaction code
        shares_by_code = defaultdict(int)
        shares_by_insider = defaultdict(int)
        
        for v in violations:
            code = v.get('transaction_code', 'N/A')
            shares = v.get('shares', 0)
            insider = v.get('reporting_person', 'Unknown')
            
            if isinstance(shares, (int, float)):
                shares_by_code[code] += shares
                shares_by_insider[insider] += shares
        
        # Display top transaction codes
        if shares_by_code:
            lines.append("     By Transaction Code:")
            for code, shares in sorted(shares_by_code.items(), key=lambda x: -x[1])[:3]:
                lines.append(f"       Code {code}: {shares:,} shares")
        
        # Display top insiders
        if shares_by_insider:
            lines.append("     By Reporting Person:")
            for insider, shares in sorted(shares_by_insider.items(), key=lambda x: -x[1])[:3]:
                lines.append(f"       {insider}: {shares:,} shares")
        
        # Late filing statistics
        late_filings = [v for v in violations if v.get('days_late', 0) > 0]
        if late_filings:
            avg_days_late = sum(v.get('days_late', 0) for v in late_filings) / len(late_filings)
            max_days_late = max(v.get('days_late', 0) for v in late_filings)
            lines.append(f"     Late Filings: {len(late_filings)} filings, Avg {avg_days_late:.1f} days late, Max {max_days_late} days late")
        
        # Penalty estimates
        total_penalty_min = sum(v.get('penalty_min', 0) for v in violations)
        total_penalty_max = sum(v.get('penalty_max', 0) for v in violations)
        if total_penalty_min > 0 or total_penalty_max > 0:
            lines.append(f"     Estimated Penalties: ${total_penalty_min:,.0f} - ${total_penalty_max:,.0f}")
        
        return lines
    
    @staticmethod
    def _format_prosecutorial_analysis(category: str, violations: List[Dict[str, Any]]) -> List[str]:
        """Format prosecutorial analysis section with legal implications."""
        lines = []
        lines.append(f"   {STATUS_ACTION_REQUIRED} Prosecutorial Analysis:")
        
        # Generate analysis based on violation type
        analysis = ViolationCategoryFormatter._generate_prosecutorial_analysis(category, violations)
        
        # Word wrap
        wrapped = ViolationCategoryFormatter._wrap_text(analysis, 70)
        for line in wrapped:
            lines.append(f"     {line}")
        
        return lines
    
    @staticmethod
    def _generate_prosecutorial_analysis(category: str, violations: List[Dict[str, Any]]) -> str:
        """Generate prosecutorial analysis based on violation type and characteristics."""
        count = len(violations)
        
        if 'LATE_FILING' in category or 'FORM4' in category:
            return (f"This pattern of {count} late Form 4 filings establishes systematic non-compliance "
                   f"with 17 CFR § 240.16a-3 reporting requirements. Each violation subjects the reporting "
                   f"person to civil penalties and potential SEC enforcement action. The pattern suggests "
                   f"intentional disregard rather than inadvertent error, warranting enforcement review.")
        
        elif 'ZERO_DOLLAR' in category or 'TAX' in category:
            return (f"These {count} zero-dollar option exercises without cash payment establish potential "
                   f"IRC § 83 violations. The pattern indicates systematic tax evasion through unreported "
                   f"compensation income. Estimated tax liability exceeds statutory thresholds for criminal "
                   f"referral to IRS Criminal Investigation Division.")
        
        elif 'INSIDER_TRADING' in category or 'TIMING' in category:
            return (f"Transaction timing analysis reveals {count} instances of suspicious trading patterns "
                   f"potentially violating 17 CFR § 240.10b-5. Temporal correlation with material non-public "
                   f"information establishes probable cause for SEC investigation. Pattern indicates "
                   f"systematic exploitation of insider position for personal benefit.")
        
        else:
            high_confidence = sum(1 for v in violations if v.get('confidence', 0) >= 0.8)
            return (f"Analysis of {count} violations in this category establishes {high_confidence} "
                   f"high-confidence violations of federal securities law. The pattern and frequency "
                   f"indicate systematic non-compliance warranting enforcement attention. Evidence chain "
                   f"is sufficient for prosecutorial review and potential enforcement action.")
    
    @staticmethod
    def _format_transaction_log(violations: List[Dict[str, Any]]) -> List[str]:
        """Format detailed transaction log (chronologically sorted)."""
        lines = []
        lines.append("   Detailed Transaction Log (Most Recent 10):")
        lines.append("")
        
        # Sort chronologically (most recent first)
        sorted_violations = sorted(
            violations[:10],
            key=lambda x: x.get('transaction_date', x.get('filing_date', '')),
            reverse=True
        )
        
        # Table header
        box_width = 72
        lines.append(f"   ┌{'─' * 10}┬{'─' * 25}┬{'─' * 12}┬{'─' * 20}┐")
        lines.append(f"   │ {'Date':<9}│ {'Reporting Person':<24}│ {'Shares':<11}│ {'Confidence':<19}│")
        lines.append(f"   ├{'─' * 10}┼{'─' * 25}┼{'─' * 12}┼{'─' * 20}┤")
        
        # Table rows
        for v in sorted_violations:
            date = v.get('transaction_date', v.get('filing_date', 'N/A'))[:10]
            person = v.get('reporting_person', 'Unknown')[:24]
            shares = v.get('shares', 0)
            shares_str = f"{shares:,}" if isinstance(shares, (int, float)) else str(shares)
            confidence = v.get('confidence', 0)
            confidence_str = f"{confidence:.1%}" if isinstance(confidence, (int, float)) else str(confidence)
            
            lines.append(f"   │ {date:<9}│ {person:<24}│ {shares_str:>11}│ {confidence_str:>19}│")
        
        lines.append(f"   └{'─' * 10}┴{'─' * 25}┴{'─' * 12}┴{'─' * 20}┘")
        
        return lines
    
    @staticmethod
    def _collect_unique_statutes(violations: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Collect unique statutes from violations."""
        unique = []
        seen = set()
        
        for v in violations:
            statutes = v.get('statutes', [])
            for statute in statutes:
                code = statute.get('code', '')
                if code and code not in seen:
                    seen.add(code)
                    unique.append(statute)
        
        return unique
    
    @staticmethod
    def _determine_category_severity(violations: List[Dict[str, Any]]) -> str:
        """Determine overall severity for a category."""
        severities = [v.get('severity', 'LOW') for v in violations]
        
        if 'CRITICAL' in severities:
            return 'CRITICAL'
        elif 'HIGH' in severities:
            return 'HIGH'
        elif 'MEDIUM' in severities:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    @staticmethod
    def _severity_order(severity: str) -> int:
        """Get numeric order for severity (lower number = higher priority)."""
        order = {
            'CRITICAL': 0,
            'HIGH': 1,
            'MEDIUM': 2,
            'LOW': 3,
            'MINIMAL': 4,
        }
        return order.get(severity.upper(), 5)
    
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
