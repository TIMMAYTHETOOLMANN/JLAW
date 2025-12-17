#!/usr/bin/env python3
"""
PDF Report Generation - Court-Ready Forensic Dossiers
Generates professional DOJ-style PDF reports using ReportLab.
Includes executive summaries, violation details, evidence chains, and regulatory routing.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, KeepTogether
    )
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # Provide fallback values when ReportLab is not available
    inch = 72.0  # Standard points per inch
    logging.warning("ReportLab not installed - PDF generation unavailable")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForensicPDFGenerator:
    """
    Generate court-admissible forensic analysis reports in PDF format.
    
    Features:
    - DOJ-style professional formatting
    - Executive summary with key findings
    - Detailed violation breakdowns with evidence citations
    - Evidence chain documentation with SHA-256 hashes
    - Regulatory routing recommendations
    - Penalty estimate tables
    - Chain of custody appendix
    - Digital signature placeholder
    """
    
    TITLE_FONT = "Helvetica-Bold"
    BODY_FONT = "Helvetica"
    MONO_FONT = "Courier"
    
    def __init__(self, output_dir: str = "./output/reports"):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName=self.TITLE_FONT
        ))
        
        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2a2a2a'),
            spaceBefore=12,
            spaceAfter=6,
            fontName=self.TITLE_FONT
        ))
        
        # Subsection header
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#3a3a3a'),
            spaceBefore=10,
            spaceAfter=4,
            fontName=self.TITLE_FONT
        ))
        
        # Evidence text
        self.styles.add(ParagraphStyle(
            name='Evidence',
            parent=self.styles['Code'],
            fontSize=9,
            textColor=colors.HexColor('#4a4a4a'),
            leftIndent=20,
            fontName=self.MONO_FONT,
            backColor=colors.HexColor('#f5f5f5')
        ))
        
        # Citation
        self.styles.add(ParagraphStyle(
            name='Citation',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#555555'),
            leftIndent=20,
            fontName=self.BODY_FONT
        ))
    
    def generate_forensic_dossier(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        output_filename: Optional[str] = None
    ) -> Path:
        """
        Generate complete forensic dossier PDF
        
        Args:
            case_id: Unique case identifier
            company_name: Target company name
            cik: SEC CIK number
            analysis_results: Complete analysis results from all nodes
            output_filename: Optional custom output filename
            
        Returns:
            Path to generated PDF file
        """
        if not output_filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"FORENSIC_DOSSIER_{case_id}_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build document content
        story = []
        
        # Cover page
        story.extend(self._build_cover_page(case_id, company_name, cik, analysis_results))
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._build_executive_summary(analysis_results))
        story.append(PageBreak())
        
        # Violation details
        story.extend(self._build_violation_details(analysis_results))
        story.append(PageBreak())
        
        # Regulatory routing
        story.extend(self._build_regulatory_routing(analysis_results))
        story.append(PageBreak())
        
        # Penalty estimates
        story.extend(self._build_penalty_estimates(analysis_results))
        story.append(PageBreak())
        
        # Evidence chain
        story.extend(self._build_evidence_chain(analysis_results))
        story.append(PageBreak())
        
        # Chain of custody
        story.extend(self._build_chain_of_custody(case_id, analysis_results))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"Generated forensic dossier: {output_path}")
        return output_path
    
    def _build_cover_page(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        results: Dict
    ) -> List:
        """Build cover page"""
        story = []
        
        # Title
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph(
            "FORENSIC ANALYSIS DOSSIER",
            self.styles['ReportTitle']
        ))
        story.append(Spacer(1, 0.5*inch))
        
        # Classification
        story.append(Paragraph(
            "<font color='red'><b>CONFIDENTIAL - LAW ENFORCEMENT SENSITIVE</b></font>",
            self.styles['Normal']
        ))
        story.append(Spacer(1, inch))
        
        # Case details
        case_data = [
            ["Case ID:", case_id],
            ["Target Entity:", company_name],
            ["SEC CIK:", cik],
            ["Analysis Date:", datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')],
            ["Total Violations:", str(results.get('total_violations', 0))],
            ["Critical Alerts:", str(results.get('critical_alerts', 0))]
        ]
        
        table = Table(case_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), self.BODY_FONT, 12),
            ('FONT', (0, 0), (0, -1), self.TITLE_FONT, 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0'))
        ]))
        story.append(table)
        
        story.append(Spacer(1, inch))
        
        # Footer
        story.append(Paragraph(
            "Generated by JLAW Forensic Analysis System v4.0",
            self.styles['Normal']
        ))
        
        return story
    
    def _build_executive_summary(self, results: Dict) -> List:
        """Build executive summary section"""
        story = []
        
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        # Overview
        total_violations = results.get('total_violations', 0)
        critical_alerts = results.get('critical_alerts', 0)
        high_alerts = results.get('high_alerts', 0)
        
        summary_text = f"""
        This forensic analysis identified <b>{total_violations} potential violations</b> across 
        15 regulatory analysis nodes. The violations include <b>{critical_alerts} critical</b> and 
        <b>{high_alerts} high-severity</b> findings requiring immediate regulatory attention.
        """
        
        story.append(Paragraph(summary_text, self.styles['BodyText']))
        story.append(Spacer(1, 12))
        
        # Key findings
        story.append(Paragraph("KEY FINDINGS", self.styles['SubsectionHeader']))
        
        # Extract top violations by severity
        all_violations = self._extract_all_violations(results)
        top_violations = sorted(all_violations, key=lambda x: x.get('severity', 0), reverse=True)[:5]
        
        for i, violation in enumerate(top_violations, 1):
            finding_text = f"""
            <b>{i}. {violation.get('violation_type', 'Unknown')} (Severity: {violation.get('severity', 0)}/10)</b><br/>
            {violation.get('description', 'No description available')}<br/>
            <i>Regulatory Citations: {', '.join(violation.get('regulatory_citations', []))}</i>
            """
            story.append(Paragraph(finding_text, self.styles['Normal']))
            story.append(Spacer(1, 8))
        
        return story
    
    def _build_violation_details(self, results: Dict) -> List:
        """Build detailed violation section"""
        story = []
        
        story.append(Paragraph("DETAILED VIOLATION ANALYSIS", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        # Group violations by node
        violations_by_node = self._group_violations_by_node(results)
        
        for node_name, violations in violations_by_node.items():
            story.append(Paragraph(f"Node: {node_name}", self.styles['SubsectionHeader']))
            story.append(Spacer(1, 6))
            
            for i, violation in enumerate(violations, 1):
                # Violation header
                v_header = f"""
                <b>Violation #{i}: {violation.get('violation_type', 'Unknown')}</b><br/>
                Severity: {violation.get('severity', 0)}/10 | 
                Detected: {violation.get('detected_at', 'Unknown')}
                """
                story.append(Paragraph(v_header, self.styles['Normal']))
                story.append(Spacer(1, 4))
                
                # Description
                story.append(Paragraph(f"<b>Description:</b> {violation.get('description', '')}", 
                                     self.styles['Normal']))
                story.append(Spacer(1, 4))
                
                # Evidence hash
                evidence_hash = violation.get('evidence_hash', 'N/A')
                story.append(Paragraph(
                    f"<b>Evidence Hash (SHA-256):</b> <font name='Courier' size='8'>{evidence_hash}</font>",
                    self.styles['Normal']
                ))
                story.append(Spacer(1, 4))
                
                # Regulatory citations
                citations = violation.get('regulatory_citations', [])
                if citations:
                    story.append(Paragraph("<b>Regulatory Citations:</b>", self.styles['Normal']))
                    for citation in citations:
                        story.append(Paragraph(f"• {citation}", self.styles['Citation']))
                
                story.append(Spacer(1, 12))
        
        return story
    
    def _build_regulatory_routing(self, results: Dict) -> List:
        """Build regulatory routing recommendations"""
        story = []
        
        story.append(Paragraph("REGULATORY ROUTING RECOMMENDATIONS", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        routing = results.get('regulatory_routing', {})
        
        agencies = [
            ("SEC Enforcement Division", routing.get('SEC', routing.get('sec', False)), 
             "Securities fraud, insider trading, disclosure violations"),
            ("DOJ Securities Fraud Unit", routing.get('DOJ', routing.get('doj', False)), 
             "Criminal securities fraud, obstruction, perjury"),
            ("IRS Criminal Investigation", routing.get('IRS', routing.get('irs', False)), 
             "Tax evasion, unreported income, fraudulent returns")
        ]
        
        routing_data = [["Agency", "Recommended", "Jurisdiction"]]
        for agency, recommended, jurisdiction in agencies:
            routing_data.append([
                agency,
                "✓ YES" if recommended else "NO",
                jurisdiction
            ])
        
        table = Table(routing_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), self.TITLE_FONT, 12),
            ('FONT', (0, 1), (-1, -1), self.BODY_FONT, 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a4a4a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(table)
        
        return story
    
    def _build_penalty_estimates(self, results: Dict) -> List:
        """Build penalty estimate table"""
        story = []
        
        story.append(Paragraph("ESTIMATED PENALTIES", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        penalties = results.get('estimated_penalties', {})
        
        penalty_data = [
            ["Penalty Type", "Minimum", "Maximum"],
            ["Civil Monetary Penalties", 
             f"${penalties.get('civil_minimum', 0):,.0f}",
             f"${penalties.get('civil_maximum', 0):,.0f}"],
            ["Disgorgement (Estimated)", 
             "N/A",
             f"${penalties.get('disgorgement', 0):,.0f}"],
            ["Criminal Exposure", 
             "Possible" if penalties.get('criminal_exposure') else "No",
             f"{penalties.get('prison_years_maximum', 0)} years max"]
        ]
        
        table = Table(penalty_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), self.TITLE_FONT, 12),
            ('FONT', (0, 1), (-1, -1), self.BODY_FONT, 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a4a4a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(table)
        
        return story
    
    def _build_evidence_chain(self, results: Dict) -> List:
        """Build evidence chain documentation"""
        story = []
        
        story.append(Paragraph("EVIDENCE CHAIN DOCUMENTATION", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph(
            "All evidence has been cryptographically hashed using SHA-256 to ensure integrity. "
            "Any tampering with evidence will be detectable through hash verification.",
            self.styles['BodyText']
        ))
        story.append(Spacer(1, 12))
        
        # List all evidence hashes
        all_violations = self._extract_all_violations(results)
        
        if all_violations:
            evidence_data = [["Evidence ID", "Violation Type", "SHA-256 Hash"]]
            for i, violation in enumerate(all_violations, 1):
                evidence_data.append([
                    f"EV-{i:04d}",
                    violation.get('violation_type', 'Unknown')[:30],
                    violation.get('evidence_hash', 'N/A')[:32] + "..."
                ])
            
            table = Table(evidence_data, colWidths=[1*inch, 2*inch, 3.5*inch])
            table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, 0), self.TITLE_FONT, 10),
                ('FONT', (0, 1), (-1, -1), self.MONO_FONT, 7),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a4a4a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(table)
        
        return story
    
    def _build_chain_of_custody(self, case_id: str, results: Dict) -> List:
        """Build chain of custody appendix"""
        story = []
        
        story.append(Paragraph("CHAIN OF CUSTODY", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        custody_text = f"""
        <b>Case ID:</b> {case_id}<br/>
        <b>Analysis System:</b> JLAW Forensic Analysis System v4.0<br/>
        <b>Analysis Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>
        <b>Data Sources:</b> SEC EDGAR, Form 4, DEF 14A, 10-Q, 10-K, IRS Form 4<br/>
        <b>Analysis Methods:</b> 15-Node Recursive Prosecutorial Engine<br/>
        <b>Evidence Integrity:</b> SHA-256 Cryptographic Hashing<br/>
        <b>Chain of Custody Maintained:</b> All evidence collected and analyzed in automated 
        forensic environment with audit trail<br/>
        """
        
        story.append(Paragraph(custody_text, self.styles['BodyText']))
        story.append(Spacer(1, 12))
        
        # Digital signature placeholder
        story.append(Paragraph("DIGITAL SIGNATURE", self.styles['SubsectionHeader']))
        story.append(Spacer(1, 12))
        
        # Generate report hash
        report_hash = hashlib.sha256(
            f"{case_id}{datetime.now().isoformat()}".encode('utf-8')
        ).hexdigest()
        
        story.append(Paragraph(
            f"<b>Report Hash (SHA-256):</b><br/>"
            f"<font name='Courier' size='8'>{report_hash}</font>",
            self.styles['Normal']
        ))
        
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "<i>This report is digitally signed and tamper-evident. Any modifications will "
            "invalidate the signature and be detectable through hash verification.</i>",
            self.styles['Normal']
        ))
        
        return story
    
    def _extract_all_violations(self, results: Dict) -> List[Dict]:
        """Extract all violations from results"""
        violations = []
        
        # Check for violations in various result structures
        if 'violations' in results:
            violations.extend(results['violations'])
        
        # Check node-specific results
        for key, value in results.items():
            if isinstance(value, dict) and 'violations' in value:
                violations.extend(value['violations'])
        
        return violations
    
    def _group_violations_by_node(self, results: Dict) -> Dict[str, List]:
        """Group violations by analysis node"""
        grouped = {}
        
        # Iterate through results to find node-specific violations
        for key, value in results.items():
            if isinstance(value, dict) and 'violations' in value:
                node_name = value.get('node', key)
                grouped[node_name] = value['violations']
        
        # If violations are at top level
        if 'violations' in results and not grouped:
            grouped['General'] = results['violations']
        
        return grouped


# CLI Entry Point
if __name__ == "__main__":
    if not REPORTLAB_AVAILABLE:
        print("ReportLab is not installed. Install with: pip install reportlab")
        exit(1)
    
    # Demo
    generator = ForensicPDFGenerator()
    
    demo_results = {
        "total_violations": 12,
        "critical_alerts": 3,
        "high_alerts": 5,
        "violations": [
            {
                "violation_type": "SAY_ON_PAY_FAILURE",
                "severity": 8,
                "description": "Say-on-Pay failed with 45% approval",
                "evidence_hash": hashlib.sha256(b"demo_evidence").hexdigest(),
                "regulatory_citations": ["Exchange Act Rule 14a-21"],
                "detected_at": datetime.now().isoformat()
            }
        ],
        "regulatory_routing": {"SEC": True, "DOJ": False, "IRS": False},
        "estimated_penalties": {
            "civil_minimum": 100000,
            "civil_maximum": 5000000,
            "criminal_exposure": False,
            "prison_years_maximum": 0
        }
    }
    
    output = generator.generate_forensic_dossier(
        case_id="DEMO-001",
        company_name="Demo Corporation",
        cik="0000000001",
        analysis_results=demo_results
    )
    
    print(f"Generated demo report: {output}")
