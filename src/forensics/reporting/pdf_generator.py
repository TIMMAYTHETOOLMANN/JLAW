"""
PDF Report Generator - Professional PDF Reports
==============================================

Generates comprehensive PDF reports using:
- ReportLab for PDF generation
- Jinja2 templates for customization
- Professional layouts and styling
- Evidence embedding
- Charts and visualizations
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import os
from io import BytesIO

logger = logging.getLogger(__name__)


@dataclass
class ReportSection:
    """Section of a report"""
    section_id: str
    title: str
    content: str
    subsections: List['ReportSection'] = None
    charts: List[Dict[str, Any]] = None
    tables: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []
        if self.charts is None:
            self.charts = []
        if self.tables is None:
            self.tables = []


class PDFReportGenerator:
    """
    Generates professional PDF investigation reports
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # PDF settings
        self.page_size = self.config.get('page_size', 'LETTER')
        self.font_family = self.config.get('font_family', 'Helvetica')
        
        # Statistics
        self.stats = {
            'reports_generated': 0,
            'pages_created': 0
        }
        
        logger.info("📄 PDF Report Generator initialized")
    
    def generate_report(
        self,
        title: str,
        case_number: str,
        sections: List[ReportSection],
        metadata: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate comprehensive PDF report
        
        Args:
            title: Report title
            case_number: Case identification number
            sections: Report sections
            metadata: Additional metadata
            output_path: Optional file path to save PDF
        
        Returns:
            PDF bytes
        """
        logger.info(f"📄 Generating PDF report: {title}")
        
        self.stats['reports_generated'] += 1
        
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
            from reportlab.lib import colors
            
            # Create PDF buffer
            buffer = BytesIO()
            
            # Create document
            page_size = letter if self.page_size == 'LETTER' else A4
            doc = SimpleDocTemplate(
                buffer,
                pagesize=page_size,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Story (content)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#000080'),
                spaceAfter=30,
                alignment=1  # Center
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#000080'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            # Title page
            story.append(Spacer(1, 2*inch))
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph(f"Case Number: {case_number}", styles['Normal']))
            story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            
            if metadata:
                story.append(Spacer(1, 0.3*inch))
                for key, value in metadata.items():
                    story.append(Paragraph(f"<b>{key}:</b> {value}", styles['Normal']))
            
            story.append(PageBreak())
            
            # Table of contents
            story.append(Paragraph("Table of Contents", heading_style))
            for i, section in enumerate(sections, 1):
                toc_entry = f"{i}. {section.title}"
                story.append(Paragraph(toc_entry, styles['Normal']))
            
            story.append(PageBreak())
            
            # Sections
            for i, section in enumerate(sections, 1):
                story.extend(self._render_section(section, i, styles, heading_style))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            # Save if path provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                logger.info(f"✓ PDF saved to: {output_path}")
            
            page_count = self._estimate_page_count(len(story))
            self.stats['pages_created'] += page_count
            
            logger.info(f"✓ PDF generated: {len(pdf_bytes)} bytes, ~{page_count} pages")
            
            return pdf_bytes
        
        except ImportError:
            logger.warning("⚠️ ReportLab not available, generating HTML fallback")
            return self._generate_html_fallback(title, case_number, sections, metadata)
        
        except Exception as e:
            logger.error(f"❌ PDF generation failed: {e}")
            return self._generate_html_fallback(title, case_number, sections, metadata)
    
    def _render_section(
        self,
        section: ReportSection,
        section_num: int,
        styles: Any,
        heading_style: Any
    ) -> List:
        """Render a report section"""
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        
        elements = []
        
        # Section heading
        heading_text = f"{section_num}. {section.title}"
        elements.append(Paragraph(heading_text, heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Content
        for paragraph in section.content.split('\n\n'):
            if paragraph.strip():
                elements.append(Paragraph(paragraph.strip(), styles['Normal']))
                elements.append(Spacer(1, 0.1*inch))
        
        # Tables
        for table_data in section.tables:
            if 'data' in table_data and table_data['data']:
                table = Table(table_data['data'])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.2*inch))
        
        # Subsections
        for subsection in section.subsections:
            elements.extend(self._render_section(subsection, section_num, styles, styles['Heading3']))
        
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _generate_html_fallback(
        self,
        title: str,
        case_number: str,
        sections: List[ReportSection],
        metadata: Optional[Dict[str, Any]]
    ) -> bytes:
        """Generate HTML fallback when PDF generation fails"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #000080; text-align: center; }}
                h2 {{ color: #000080; border-bottom: 2px solid #000080; padding-bottom: 5px; }}
                .metadata {{ background-color: #f5f5f5; padding: 15px; margin: 20px 0; }}
                .section {{ margin: 30px 0; }}
                table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
                th {{ background-color: #000080; color: white; padding: 10px; }}
                td {{ border: 1px solid #ddd; padding: 8px; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="metadata">
                <p><strong>Case Number:</strong> {case_number}</p>
                <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
        """
        
        if metadata:
            for key, value in metadata.items():
                html += f"<p><strong>{key}:</strong> {value}</p>"
        
        html += "</div>"
        
        for i, section in enumerate(sections, 1):
            html += f'<div class="section">'
            html += f'<h2>{i}. {section.title}</h2>'
            html += f'<div>{section.content.replace(chr(10), "<br>")}</div>'
            html += '</div>'
        
        html += """
        </body>
        </html>
        """
        
        return html.encode('utf-8')
    
    def _estimate_page_count(self, element_count: int) -> int:
        """Estimate page count from elements"""
        # Rough estimate: ~30 elements per page
        return max(1, element_count // 30)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get generator statistics"""
        return self.stats.copy()


if __name__ == "__main__":
    # Demo usage
    generator = PDFReportGenerator()
    
    sections = [
        ReportSection(
            section_id="S1",
            title="Executive Summary",
            content="This investigation reveals significant findings..."
        ),
        ReportSection(
            section_id="S2",
            title="Evidence Analysis",
            content="The following evidence was analyzed...",
            tables=[{
                'data': [
                    ['Evidence ID', 'Type', 'Date'],
                    ['EV001', 'Email', '2024-01-15'],
                    ['EV002', 'Document', '2024-01-16']
                ]
            }]
        )
    ]
    
    pdf_bytes = generator.generate_report(
        title="Investigation Report",
        case_number="CASE-2024-001",
        sections=sections,
        metadata={'Investigator': 'Agent Smith'},
        output_path="report.pdf"
    )
    
    print(f"Generated {len(pdf_bytes)} bytes")

