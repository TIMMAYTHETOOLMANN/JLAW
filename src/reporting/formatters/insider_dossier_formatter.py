"""
Insider Dossier Formatter - Phase 4 Enhanced
============================================

Creates individual dossier sections for each reporting person BEFORE per-filing details.

Includes:
- Role and relationship information
- Activity summary (transaction counts, zero-dollar transactions, late filings, risk score bar)
- Transaction timeline (chronological with codes)
- Pattern analysis narrative
"""

from typing import Dict, Any, List
from datetime import datetime
from .format_constants import (
    SUBSECTION_DIVIDER,
    SECTION_3_TITLE,
    STATUS_KEY_FINDING,
    get_risk_indicator,
    create_progress_bar,
    BOX_SINGLE_TOP_LEFT,
    BOX_SINGLE_TOP_RIGHT,
    BOX_SINGLE_BOTTOM_LEFT,
    BOX_SINGLE_BOTTOM_RIGHT,
    BOX_SINGLE_HORIZONTAL,
    BOX_SINGLE_VERTICAL,
    BOX_SINGLE_VERTICAL_RIGHT,
    BOX_SINGLE_VERTICAL_LEFT,
    STANDARD_WIDTH,
)


class InsiderDossierFormatter:
    """Formats individual insider/reporting person dossiers."""
    
    @staticmethod
    def format_all(insiders_data: List[Dict[str, Any]]) -> str:
        """
        Format all insider dossiers.
        
        Args:
            insiders_data: List of insider profile dictionaries
        
        Returns:
            Formatted dossiers for all insiders
        """
        lines = []
        
        # Section header
        lines.append(SUBSECTION_DIVIDER)
        lines.append(SECTION_3_TITLE)
        lines.append(SUBSECTION_DIVIDER)
        lines.append("")
        
        if not insiders_data:
            lines.append("No reporting persons identified in this analysis.")
            lines.append("")
            return "\n".join(lines)
        
        # Sort by risk score (highest first)
        sorted_insiders = sorted(
            insiders_data,
            key=lambda x: x.get('risk_score', 0),
            reverse=True
        )
        
        for i, insider in enumerate(sorted_insiders, 1):
            lines.extend(InsiderDossierFormatter._format_single_dossier(insider, i))
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_single_dossier(insider: Dict[str, Any], index: int) -> List[str]:
        """Format a single insider dossier."""
        lines = []
        
        name = insider.get('name', 'Unknown')
        risk_score = insider.get('risk_score', 0.0)
        risk_indicator = get_risk_indicator(risk_score)
        
        box_width = STANDARD_WIDTH - 4
        
        # Dossier header with risk indicator
        lines.append(f"┌{'─' * box_width}┐")
        lines.append(f"│ {risk_indicator} REPORTING PERSON #{index}: {name:<{box_width - 30}} │")
        lines.append(f"├{'─' * box_width}┤")
        
        # Role and Relationship
        lines.append(f"│ {'ROLE & RELATIONSHIP':<{box_width - 2}} │")
        lines.append(f"│{' ' * box_width}│")
        
        roles = insider.get('roles', [])
        roles_str = ', '.join(roles) if roles else 'Not Specified'
        lines.append(f"│  Position:        {roles_str:<{box_width - 20}} │")
        
        relationship = insider.get('relationship', 'N/A')
        lines.append(f"│  Relationship:    {relationship:<{box_width - 20}} │")
        
        cik = insider.get('cik', 'N/A')
        lines.append(f"│  CIK:             {cik:<{box_width - 20}} │")
        
        lines.append(f"│{' ' * box_width}│")
        lines.append(f"├{'─' * box_width}┤")
        
        # Activity Summary
        lines.append(f"│ {'ACTIVITY SUMMARY':<{box_width - 2}} │")
        lines.append(f"│{' ' * box_width}│")
        
        total_transactions = insider.get('total_transactions', 0)
        zero_dollar_transactions = insider.get('zero_dollar_transactions', 0)
        late_filings = insider.get('late_filings', 0)
        
        lines.append(f"│  Total Transactions:          {total_transactions:>6}{' ' * (box_width - 38)} │")
        lines.append(f"│  Zero-Dollar Transactions:    {zero_dollar_transactions:>6}{' ' * (box_width - 38)} │")
        lines.append(f"│  Late Filings (§16(a)):       {late_filings:>6}{' ' * (box_width - 38)} │")
        lines.append(f"│{' ' * box_width}│")
        
        # Risk score with progress bar
        risk_bar = create_progress_bar(int(risk_score), 100, 30)
        lines.append(f"│  Risk Score:  {risk_score:>5.1f}/100  {risk_bar}{' ' * (box_width - 48)} │")
        
        lines.append(f"│{' ' * box_width}│")
        lines.append(f"├{'─' * box_width}┤")
        
        # Transaction Timeline (if available)
        transactions = insider.get('transactions', [])
        if transactions:
            lines.append(f"│ {'TRANSACTION TIMELINE (Most Recent 10)':<{box_width - 2}} │")
            lines.append(f"│{' ' * box_width}│")
            
            # Sort by date (most recent first)
            sorted_transactions = sorted(
                transactions[:10],
                key=lambda x: x.get('transaction_date', ''),
                reverse=True
            )
            
            for txn in sorted_transactions:
                date = txn.get('transaction_date', 'N/A')
                code = txn.get('transaction_code', 'N/A')
                shares = txn.get('shares', 0)
                price = txn.get('price_per_share', 0.0)
                
                txn_line = f"{date} | Code {code} | {shares:,} shares @ ${price:.2f}"
                lines.append(f"│  {txn_line:<{box_width - 2}} │")
            
            lines.append(f"│{' ' * box_width}│")
            lines.append(f"├{'─' * box_width}┤")
        
        # Pattern Analysis
        lines.append(f"│ {'PATTERN ANALYSIS':<{box_width - 2}} │")
        lines.append(f"│{' ' * box_width}│")
        
        pattern_analysis = insider.get('pattern_analysis', '')
        if pattern_analysis:
            # Word wrap the pattern analysis
            wrapped = InsiderDossierFormatter._wrap_text(pattern_analysis, box_width - 4)
            for line in wrapped:
                lines.append(f"│  {line:<{box_width - 2}} │")
        else:
            # Generate default pattern analysis
            default_analysis = InsiderDossierFormatter._generate_pattern_analysis(insider)
            wrapped = InsiderDossierFormatter._wrap_text(default_analysis, box_width - 4)
            for line in wrapped:
                lines.append(f"│  {line:<{box_width - 2}} │")
        
        lines.append(f"│{' ' * box_width}│")
        lines.append(f"└{'─' * box_width}┘")
        
        return lines
    
    @staticmethod
    def _generate_pattern_analysis(insider: Dict[str, Any]) -> str:
        """Generate default pattern analysis from insider data."""
        findings = []
        
        zero_dollar = insider.get('zero_dollar_transactions', 0)
        if zero_dollar > 0:
            findings.append(f"{zero_dollar} zero-dollar transactions detected (potential §83 tax evasion)")
        
        late_filings = insider.get('late_filings', 0)
        if late_filings > 0:
            findings.append(f"{late_filings} late Form 4 filings (§16(a) violations)")
        
        risk_score = insider.get('risk_score', 0.0)
        if risk_score >= 80:
            findings.append("HIGH RISK: Multiple violation patterns suggest systematic non-compliance")
        elif risk_score >= 60:
            findings.append("ELEVATED RISK: Pattern indicates potential intentional violations")
        
        total_transactions = insider.get('total_transactions', 0)
        if total_transactions > 20:
            findings.append(f"High transaction volume ({total_transactions} transactions) warrants detailed review")
        
        if not findings:
            findings.append("Standard transaction pattern detected. No immediate red flags identified.")
        
        return ". ".join(findings) + "."
    
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
