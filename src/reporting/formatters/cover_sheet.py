"""
Cover Sheet Formatter - Phase 4 Enhanced
=========================================

Generates DOJ-grade confidential cover sheet with case metadata using Unicode box drawing.

Format matches exact specification with proper case identifier, analysis period,
and classification fields.
"""

from datetime import datetime
from typing import Dict, Any
from .format_constants import (
    BOX_DOUBLE_HORIZONTAL,
    BOX_DOUBLE_VERTICAL,
    BOX_DOUBLE_TOP_LEFT,
    BOX_DOUBLE_TOP_RIGHT,
    BOX_DOUBLE_BOTTOM_LEFT,
    BOX_DOUBLE_BOTTOM_RIGHT,
    BOX_SINGLE_HORIZONTAL,
    BOX_SINGLE_VERTICAL,
    BOX_SINGLE_TOP_LEFT,
    BOX_SINGLE_TOP_RIGHT,
    BOX_SINGLE_BOTTOM_LEFT,
    BOX_SINGLE_BOTTOM_RIGHT,
    CLASSIFICATION_CONFIDENTIAL,
    STANDARD_WIDTH,
)


class CoverSheetFormatter:
    """Formats DOJ-grade cover sheet for prosecutorial dossiers."""
    
    @staticmethod
    def format(case_data: Dict[str, Any]) -> str:
        """
        Format cover sheet with case metadata per specification.
        
        Args:
            case_data: Dictionary with keys:
                - case_id: JLAW case identifier
                - company_name: Company under investigation
                - cik: SEC CIK number
                - generation_date: Report generation timestamp
                - dossier_type: Classification (DOJ-GRADE/SEC REFERRAL READY)
                - start_date: Analysis period start
                - end_date: Analysis period end
        
        Returns:
            Formatted cover sheet string with Unicode box drawing
        """
        lines = []
        
        # Double-line outer box header
        lines.append(f"{BOX_DOUBLE_TOP_LEFT}{BOX_DOUBLE_HORIZONTAL * (STANDARD_WIDTH - 2)}{BOX_DOUBLE_TOP_RIGHT}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}{' ' * (STANDARD_WIDTH - 2)}{BOX_DOUBLE_VERTICAL}")
        
        # Classification header
        classification_text = CLASSIFICATION_CONFIDENTIAL
        padding = (STANDARD_WIDTH - 2 - len(classification_text)) // 2
        lines.append(f"{BOX_DOUBLE_VERTICAL}{' ' * padding}{classification_text}{' ' * (STANDARD_WIDTH - 2 - padding - len(classification_text))}{BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}{' ' * (STANDARD_WIDTH - 2)}{BOX_DOUBLE_VERTICAL}")
        
        # Inner box for title
        inner_box_width = STANDARD_WIDTH - 8
        lines.append(f"{BOX_DOUBLE_VERTICAL}  {BOX_SINGLE_TOP_LEFT}{BOX_SINGLE_HORIZONTAL * inner_box_width}{BOX_SINGLE_TOP_RIGHT}  {BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}  {BOX_SINGLE_VERTICAL}{' ' * inner_box_width}{BOX_SINGLE_VERTICAL}  {BOX_DOUBLE_VERTICAL}")
        
        title = "SECURITIES FRAUD FORENSIC DOSSIER"
        title_padding = (inner_box_width - len(title)) // 2
        lines.append(f"{BOX_DOUBLE_VERTICAL}  {BOX_SINGLE_VERTICAL}{' ' * title_padding}{title}{' ' * (inner_box_width - title_padding - len(title))}{BOX_SINGLE_VERTICAL}  {BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}  {BOX_SINGLE_VERTICAL}{' ' * inner_box_width}{BOX_SINGLE_VERTICAL}  {BOX_DOUBLE_VERTICAL}")
        
        # Company name and CIK
        company_name = case_data.get('company_name', 'N/A')
        cik = case_data.get('cik', 'N/A')
        company_padding = (inner_box_width - len(company_name)) // 2
        cik_text = f"CIK: {cik}"
        cik_padding = (inner_box_width - len(cik_text)) // 2
        
        lines.append(f"{BOX_DOUBLE_VERTICAL}  {BOX_SINGLE_VERTICAL}{' ' * company_padding}{company_name}{' ' * (inner_box_width - company_padding - len(company_name))}{BOX_SINGLE_VERTICAL}  {BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}  {BOX_SINGLE_VERTICAL}{' ' * cik_padding}{cik_text}{' ' * (inner_box_width - cik_padding - len(cik_text))}{BOX_SINGLE_VERTICAL}  {BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}  {BOX_SINGLE_VERTICAL}{' ' * inner_box_width}{BOX_SINGLE_VERTICAL}  {BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}  {BOX_SINGLE_BOTTOM_LEFT}{BOX_SINGLE_HORIZONTAL * inner_box_width}{BOX_SINGLE_BOTTOM_RIGHT}  {BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}{' ' * (STANDARD_WIDTH - 2)}{BOX_DOUBLE_VERTICAL}")
        
        # Metadata table
        case_id = case_data.get('case_id', 'N/A')
        start_date = case_data.get('start_date', 'N/A')
        end_date = case_data.get('end_date', 'N/A')
        analysis_period = f"{start_date} — {end_date}"
        classification = case_data.get('dossier_type', 'DOJ-GRADE')
        generation_date = case_data.get('generation_date', 'N/A')
        if isinstance(generation_date, datetime):
            generation_date = generation_date.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        lines.append(f"{BOX_DOUBLE_VERTICAL}     Analysis Period     │  {analysis_period:<52}{BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}     Case Identifier     │  {case_id:<52}{BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}     Classification      │  {classification:<52}{BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}     Generation Date     │  {generation_date:<52}{BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}{' ' * (STANDARD_WIDTH - 2)}{BOX_DOUBLE_VERTICAL}")
        
        # Double-line outer box footer
        lines.append(f"{BOX_DOUBLE_BOTTOM_LEFT}{BOX_DOUBLE_HORIZONTAL * (STANDARD_WIDTH - 2)}{BOX_DOUBLE_BOTTOM_RIGHT}")
        lines.append("")
        
        return "\n".join(lines)
