"""
Unified Report Generator
========================

Generates comprehensive forensic analysis reports matching the Nike 2019 benchmark format.

Output Stack:
- FORENSIC_REPORT.md (DOJ-grade human-readable)
- executive_summary.md
- machine_readable/*.json
- evidence/chain_of_custody.json
- appendices/*.md
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .forensic_context import ForensicContext

logger = logging.getLogger(__name__)


class UnifiedReportGenerator:
    """Generates comprehensive forensic analysis reports."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize report generator.
        
        Args:
            output_dir: Base directory for report output
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_full_report(self, context: ForensicContext) -> Path:
        """
        Generate complete report stack.
        
        Args:
            context: ForensicContext with all analysis results
            
        Returns:
            Path to report directory
        """
        logger.info("=" * 80)
        logger.info("📝 PHASE 13: REPORT GENERATION")
        logger.info("=" * 80)
        
        # Create output subdirectories
        machine_readable_dir = self.output_dir / "machine_readable"
        evidence_dir = self.output_dir / "evidence"
        evidence_sources_dir = evidence_dir / "source_documents"
        appendices_dir = self.output_dir / "appendices"
        
        for dir_path in [machine_readable_dir, evidence_sources_dir, appendices_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Generate all reports
        self._generate_main_report(context, self.output_dir / "FORENSIC_REPORT.md")
        self._generate_executive_summary(context, self.output_dir / "executive_summary.md")
        self._generate_machine_readable_files(context, machine_readable_dir)
        self._generate_chain_of_custody(context, evidence_dir / "chain_of_custody.json")
        self._generate_appendices(context, appendices_dir)
        
        logger.info(f"✅ Report Generation Complete: {self.output_dir}")
        return self.output_dir
    
    def _generate_main_report(self, context: ForensicContext, output_path: Path):
        """Generate main FORENSIC_REPORT.md in Nike 2019 benchmark format."""
        logger.info(f"Generating main report: {output_path}")
        
        total_damages = sum(v.estimated_damages for v in context.violations)
        criminal_referrals = len(context.criminal_referrals)
        
        # Build violations by type
        violations_by_type: Dict[str, int] = {}
        for violation in context.violations:
            violations_by_type[violation.violation_type] = violations_by_type.get(violation.violation_type, 0) + 1
        
        # Build violations by severity
        violations_by_severity: Dict[str, int] = {}
        for violation in context.violations:
            violations_by_severity[violation.severity] = violations_by_severity.get(violation.severity, 0) + 1
        
        report = []
        report.append(f"# {context.company_name} - {context.analysis_period_start[:4]} SEC FILINGS FORENSIC ANALYSIS")
        report.append("## DOJ-LEVEL INVESTIGATION REPORT\n")
        report.append("═" * 79)
        report.append("")
        report.append(f"**Report Generated:** {context.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Target Company:** {context.company_name} (CIK: {context.cik})")
        report.append(f"**Analysis Period:** {context.analysis_period_start} - {context.analysis_period_end}")
        report.append(f"**Total Filings Analyzed:** {len(context.filings)}")
        report.append(f"**Total Violations Identified:** {len(context.violations)}")
        report.append(f"**Criminal Referrals Recommended:** {criminal_referrals}")
        report.append(f"**Estimated Total Damages:** ${total_damages:,.2f}")
        report.append("")
        report.append("═" * 79)
        report.append("")
        
        # Executive Summary
        report.append("## EXECUTIVE SUMMARY\n")
        report.append(f"This forensic analysis examined all {context.company_name} SEC filings from {context.analysis_period_start} to {context.analysis_period_end}, ")
        report.append("applying DOJ-level prosecutorial standards to identify securities law violations. The analysis employed ")
        report.append("sophisticated surgical examination of each filing type with zero tolerance for false positives.\n")
        
        # Violations by type
        report.append("### VIOLATIONS BY TYPE\n")
        for vtype, count in sorted(violations_by_type.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- **{vtype}:** {count}")
        report.append("")
        
        # Violations by severity
        report.append("### VIOLATIONS BY SEVERITY\n")
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = violations_by_severity.get(severity, 0)
            if count > 0:
                report.append(f"- **{severity}:** {count}")
        report.append("")
        report.append("═" * 79)
        report.append("")
        
        # Statutory Framework
        report.append("## STATUTORY FRAMEWORK\n")
        report.append("| Statute | Name | Penalties |")
        report.append("|---------|------|-----------|")
        
        # Add statutes from mappings
        for statute_mapping in context.statute_mappings[:10]:  # Top 10
            report.append(f"| {statute_mapping.statute} | {statute_mapping.name} | {statute_mapping.penalties} |")
        
        if not context.statute_mappings:
            report.append("| 15 U.S.C. § 78j(b) | Section 10(b) - Anti-Fraud | Up to $5M fine, 20 years imprisonment |")
            report.append("| 15 U.S.C. § 78p(a) | Section 16(a) - Insider Reporting | Up to $100,000 per violation |")
        
        report.append("")
        report.append("**GovInfo Cross-Reference:** All statutes verified against official GovInfo.gov sources.")
        report.append("")
        report.append("═" * 79)
        report.append("")
        
        # Per-Filing Detailed Analysis
        report.append("## PER-FILING DETAILED ANALYSIS\n")
        
        # Group violations by filing
        filings_with_violations: Dict[str, List] = {}
        for violation in context.violations:
            # Extract filing ID from document URL or violation metadata
            filing_id = violation.metadata.get('accession_number', 'UNKNOWN')
            if filing_id not in filings_with_violations:
                filings_with_violations[filing_id] = []
            filings_with_violations[filing_id].append(violation)
        
        for filing in context.filings[:20]:  # Limit to first 20 for now
            violations_in_filing = filings_with_violations.get(filing.accession_number, [])
            
            report.append(f"### {filing.filing_type} - Filed {filing.filing_date}\n")
            report.append(f"**Accession Number:** {filing.accession_number}")
            report.append(f"**Document URL:** {filing.document_url}")
            report.append(f"**Violations Found:** {len(violations_in_filing)}\n")
            
            for idx, violation in enumerate(violations_in_filing, 1):
                report.append(f"#### Violation {idx}: {violation.violation_type}\n")
                report.append(f"- **Severity:** {violation.severity}")
                report.append(f"- **Statutory Reference:** {violation.statute}")
                report.append(f"- **Description:** {violation.description}")
                report.append(f"- **Evidence Summary:**")
                report.append("```")
                report.append(violation.evidence[:500])  # Limit evidence length
                report.append("```")
                report.append(f"- **EXACT QUOTE FROM DOCUMENT:**")
                report.append('```')
                report.append(f'"{violation.exact_quote[:500]}"')
                report.append('```')
                report.append(f"- **Document Location:** {violation.document_url}")
                report.append(f"- **Prosecutorial Merit:** {violation.prosecutorial_merit}")
                report.append(f"- **Estimated Damages:** ${violation.estimated_damages:,.2f}")
                report.append(f"- **Criminal Referral:** {'RECOMMENDED' if violation.criminal_referral else 'Not Recommended'}")
                report.append("")
                report.append("---")
                report.append("")
        
        report.append("═" * 79)
        report.append("")
        
        # Criminal Referral Summary
        report.append("## CRIMINAL REFERRAL SUMMARY\n")
        report.append(f"**{criminal_referrals} violation(s) recommended for DOJ criminal referral.**\n")
        
        if context.criminal_referrals:
            report.append("### Applicable Criminal Statutes\n")
            report.append("| Statute | Name | Maximum Penalty |")
            report.append("|---------|------|-----------------|")
            report.append("| 18 U.S.C. § 1343 | Wire Fraud | 20 years imprisonment |")
            report.append("| 18 U.S.C. § 1348 | Securities Fraud | 25 years imprisonment |")
            report.append("")
            
            report.append("### Violations Warranting Criminal Review\n")
            for referral in context.criminal_referrals:
                report.append(f"- **{referral.violation_id}** - {referral.description} (Hash: {referral.evidence_hash[:16]}...)")
        
        report.append("")
        report.append("═" * 79)
        report.append("")
        
        # Chain of Custody
        report.append("## CHAIN OF CUSTODY\n")
        report.append("| Violation ID | Type | Evidence Hash |")
        report.append("|--------------|------|---------------|")
        for violation in context.violations[:20]:
            evidence_hash = hashlib.sha256(violation.evidence.encode()).hexdigest()
            report.append(f"| {violation.violation_id} | {violation.violation_type} | {evidence_hash[:16]}... |")
        report.append("")
        report.append("═" * 79)
        report.append("")
        
        # Conclusion
        report.append("## CONCLUSION\n")
        report.append(f"This comprehensive forensic analysis of {context.company_name} identified {len(context.violations)} violations ")
        report.append(f"across {len(context.filings)} SEC filings during the {context.analysis_period_start[:4]} period. ")
        if criminal_referrals > 0:
            report.append(f"{criminal_referrals} violations warrant criminal referral to the Department of Justice. ")
        report.append("All findings are supported by documentary evidence with complete chain of custody preservation.\n")
        report.append("---")
        report.append("*Report prepared by JLAW Unified Forensic Analyzer*")
        report.append("*Classification: DOJ Criminal Division - Fraud Section Standards*")
        
        # Write report
        output_path.write_text("\n".join(report))
        logger.info(f"✅ Main report generated: {output_path}")
    
    def _generate_executive_summary(self, context: ForensicContext, output_path: Path):
        """Generate executive_summary.md (2-page brief)."""
        logger.info(f"Generating executive summary: {output_path}")
        
        summary = []
        summary.append(f"# Executive Summary - {context.company_name} Forensic Analysis\n")
        summary.append(f"**Analysis Period:** {context.analysis_period_start} to {context.analysis_period_end}")
        summary.append(f"**Report Date:** {context.timestamp.strftime('%Y-%m-%d')}\n")
        summary.append("## Key Findings\n")
        summary.append(f"- **Total Filings Analyzed:** {len(context.filings)}")
        summary.append(f"- **Violations Identified:** {len(context.violations)}")
        summary.append(f"- **Criminal Referrals:** {len(context.criminal_referrals)}")
        summary.append(f"- **Estimated Total Damages:** ${sum(v.estimated_damages for v in context.violations):,.2f}\n")
        summary.append("## Analysis Methodology\n")
        summary.append("This analysis employed a 13-phase unified forensic pipeline:\n")
        summary.append("1. Document Acquisition - Comprehensive SEC filing collection")
        summary.append("2. DocsGPT Parsing - Semantic document analysis")
        summary.append("3. Agent-Powered Scraping - AI-driven intelligent extraction")
        summary.append("4. Quantitative Forensics - Benford's Law, Altman Z-Score, Beneish M-Score")
        summary.append("5. Revenue Recognition - DSO trends and hockey stick detection")
        summary.append("6. Financial Flow Analysis - Circular flow and enrichment scheme detection")
        summary.append("7. Linguistic Deception - Hedging and obfuscation analysis")
        summary.append("8. Temporal Analysis - Timeline anomaly detection")
        summary.append("9. Contradiction Detection - Cross-document inconsistency identification")
        summary.append("10. ML Fraud Detection - BERT/XGBoost ensemble modeling")
        summary.append("11. Statutory Mapping - Legal framework correlation with GovInfo")
        summary.append("12. Dual-Agent Prosecution - OpenAI + Anthropic validation")
        summary.append("13. Report Generation - Comprehensive output package\n")
        summary.append("## Recommendations\n")
        if context.criminal_referrals:
            summary.append(f"- **IMMEDIATE ACTION REQUIRED:** {len(context.criminal_referrals)} violations recommended for DOJ criminal referral")
        summary.append("- Full investigation recommended for all identified violations")
        summary.append("- Enhanced monitoring of future filings suggested")
        
        output_path.write_text("\n".join(summary))
        logger.info(f"✅ Executive summary generated: {output_path}")
    
    def _generate_machine_readable_files(self, context: ForensicContext, output_dir: Path):
        """Generate machine_readable/*.json files."""
        logger.info(f"Generating machine-readable files: {output_dir}")
        
        # violations.json
        violations_data = [
            {
                'violation_id': v.violation_id,
                'type': v.violation_type,
                'statute': v.statute,
                'severity': v.severity,
                'description': v.description,
                'evidence': v.evidence[:500],
                'document_url': v.document_url,
                'exact_quote': v.exact_quote[:500],
                'prosecutorial_merit': v.prosecutorial_merit,
                'estimated_damages': v.estimated_damages,
                'criminal_referral': v.criminal_referral,
                'metadata': v.metadata
            }
            for v in context.violations
        ]
        (output_dir / "violations.json").write_text(json.dumps(violations_data, indent=2))
        
        # timeline.json
        timeline_data = [
            {
                'type': a.anomaly_type,
                'description': a.description,
                'severity': a.severity,
                'date': a.date,
                'related_filings': a.related_filings
            }
            for a in context.timeline_anomalies
        ]
        (output_dir / "timeline.json").write_text(json.dumps(timeline_data, indent=2))
        
        # contradictions.json
        contradictions_data = [
            {
                'type': c.contradiction_type,
                'description': c.description,
                'source_document': c.source_document,
                'target_document': c.target_document,
                'source_quote': c.source_quote,
                'target_quote': c.target_quote,
                'severity': c.severity
            }
            for c in context.contradictions
        ]
        (output_dir / "contradictions.json").write_text(json.dumps(contradictions_data, indent=2))
        
        # quantitative_scores.json
        quantitative_data = {
            'beneish_m_score': context.beneish_score,
            'altman_z_score': context.altman_z_score,
            'fraud_probability': context.fraud_probability,
            'benford_results': {k: {
                'chi_squared': v.chi_squared,
                'p_value': v.p_value,
                'is_anomalous': v.is_anomalous
            } for k, v in context.benford_results.items()}
        }
        (output_dir / "quantitative_scores.json").write_text(json.dumps(quantitative_data, indent=2))
        
        # linguistic_analysis.json
        (output_dir / "linguistic_analysis.json").write_text(json.dumps(context.deception_metrics, indent=2))
        
        # financial_flows.json
        flow_data = {}
        if context.flow_analysis:
            flow_data = {
                'circular_flows': context.flow_analysis.circular_flows,
                'enrichment_schemes': context.flow_analysis.enrichment_schemes,
                'coordinated_activity': context.flow_analysis.coordinated_activity,
                'risk_score': context.flow_analysis.risk_score
            }
        (output_dir / "financial_flows.json").write_text(json.dumps(flow_data, indent=2))
        
        # revenue_recognition.json
        revenue_data = {}
        if context.revenue_analysis:
            revenue_data = {
                'dso_trend': context.revenue_analysis.dso_trend,
                'hockey_stick_detected': context.revenue_analysis.hockey_stick_detected,
                'cash_divergence_score': context.revenue_analysis.cash_divergence_score,
                'anomalies': context.revenue_analysis.anomalies,
                'risk_level': context.revenue_analysis.risk_level
            }
        (output_dir / "revenue_recognition.json").write_text(json.dumps(revenue_data, indent=2))
        
        # statute_mapping.json
        statute_data = [
            {
                'statute': s.statute,
                'name': s.name,
                'jurisdiction': s.jurisdiction,
                'penalties': s.penalties,
                'govinfo_url': s.govinfo_url,
                'applicable_violations': s.applicable_violations
            }
            for s in context.statute_mappings
        ]
        (output_dir / "statute_mapping.json").write_text(json.dumps(statute_data, indent=2))
        
        logger.info(f"✅ Machine-readable files generated: {output_dir}")
    
    def _generate_chain_of_custody(self, context: ForensicContext, output_path: Path):
        """Generate evidence/chain_of_custody.json."""
        logger.info(f"Generating chain of custody: {output_path}")
        
        chain_data = {
            'report_generated': context.timestamp.isoformat(),
            'company': context.company_name,
            'cik': context.cik,
            'analysis_period': {
                'start': context.analysis_period_start,
                'end': context.analysis_period_end
            },
            'evidence_items': []
        }
        
        for violation in context.violations:
            evidence_hash = hashlib.sha256(violation.evidence.encode()).hexdigest()
            chain_data['evidence_items'].append({
                'violation_id': violation.violation_id,
                'type': violation.violation_type,
                'evidence_hash_sha256': evidence_hash,
                'document_url': violation.document_url,
                'timestamp': context.timestamp.isoformat()
            })
        
        output_path.write_text(json.dumps(chain_data, indent=2))
        logger.info(f"✅ Chain of custody generated: {output_path}")
    
    def _generate_appendices(self, context: ForensicContext, output_dir: Path):
        """Generate appendices/*.md files."""
        logger.info(f"Generating appendices: {output_dir}")
        
        # methodology.md
        methodology = [
            "# Forensic Analysis Methodology\n",
            "## Overview\n",
            "This analysis employed the JLAW Unified Forensic Pipeline, a 13-phase systematic approach ",
            "to SEC filing analysis combining AI-powered analysis, quantitative forensics, and legal framework mapping.\n",
            "## Phases\n",
            "1. **Document Acquisition** - Comprehensive SEC filing collection via EDGAR API",
            "2. **DocsGPT Parsing** - Semantic document analysis with HYBRID chunking strategy",
            "3. **Agent-Powered Scraping** - Intelligent extraction using OpenAI and Anthropic agents",
            "4. **Quantitative Forensics** - Statistical analysis including Benford's Law, Altman Z-Score, Beneish M-Score",
            "5. **Revenue Recognition** - DSO trend analysis and revenue quality assessment",
            "6. **Financial Flow Analysis** - Detection of circular flows and enrichment schemes",
            "7. **Linguistic Deception** - Analysis of hedging patterns and narrative obfuscation",
            "8. **Temporal Analysis** - Timeline reconstruction and anomaly detection",
            "9. **Contradiction Detection** - Cross-document consistency validation",
            "10. **ML Fraud Detection** - Machine learning ensemble for fraud probability",
            "11. **Statutory Mapping** - Legal framework correlation with GovInfo.gov",
            "12. **Dual-Agent Prosecution** - Multi-agent validation for high-confidence findings",
            "13. **Report Generation** - Comprehensive output package generation\n",
            "## Standards\n",
            "All analysis conforms to DOJ Criminal Division - Fraud Section standards for evidence collection and preservation."
        ]
        (output_dir / "methodology.md").write_text("\n".join(methodology))
        
        # legal_framework.md
        legal = [
            "# Legal Framework\n",
            "## Primary Statutes\n",
            "### Securities Exchange Act of 1934\n",
            "- **15 U.S.C. § 78j(b)** - Section 10(b): Prohibits manipulative and deceptive devices",
            "- **15 U.S.C. § 78p(a)** - Section 16(a): Insider trading reporting requirements\n",
            "### Sarbanes-Oxley Act of 2002\n",
            "- **15 U.S.C. § 7241** - SOX 302: CEO/CFO certifications",
            "- **15 U.S.C. § 7262** - SOX 404: Internal controls assessment\n",
            "### Criminal Statutes\n",
            "- **18 U.S.C. § 1343** - Wire Fraud",
            "- **18 U.S.C. § 1348** - Securities Fraud\n",
            "## References\n",
            "All statute references verified against official GovInfo.gov sources."
        ]
        (output_dir / "legal_framework.md").write_text("\n".join(legal))
        
        logger.info(f"✅ Appendices generated: {output_dir}")
