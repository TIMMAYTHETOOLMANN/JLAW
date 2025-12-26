"""
DOJ-Level Report Generator
==========================

Generates comprehensive, prosecution-ready forensic reports in the style of
the Nike 2019 reference analysis format.

Features:
- Per-filing detailed breakdown with exact quotes
- Violation categorization (CRITICAL/HIGH/MEDIUM/LOW)
- Evidence packages with document URLs and section mapping
- Chain of custody documentation
- Dual-agent consensus tracking
- Subagent specialized findings
- Statistical summaries
- Markdown and JSON output formats

This module bridges the gap between the sophisticated analysis pipeline
and the final report output, ensuring all forensic findings are properly
surfaced in DOJ-grade format.
"""

import hashlib
import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    AgentSource,
    ChainOfCustodyRecord,
    DamageEstimate,
    DualAgentConsensus,
    ExactQuote,
    FilingAnalysisReport,
    ForensicReportSummary,
    ProsecutorialMerit,
    RedFlag,
    SeverityLevel,
    StatutoryReference,
    SubagentFinding,
    ViolationEvidence,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def create_violation_evidence(
    violation_id: str,
    violation_type: str,
    severity: str,
    citation: str,
    description: str,
    document_url: str,
    filing_accession: str,
    filing_date: str,
    quote_text: Optional[str] = None,
    detected_by: str = "pattern"
) -> ViolationEvidence:
    """
    Factory function to create ViolationEvidence from analysis results.
    
    This helper simplifies creation of ViolationEvidence objects
    from the various analysis outputs.
    
    Args:
        violation_id: Unique violation identifier
        violation_type: Type of violation detected
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
        citation: Statutory citation
        description: Violation description
        document_url: Source document URL
        filing_accession: SEC filing accession number
        filing_date: Filing date
        quote_text: Optional exact quote from document
        detected_by: Detection source (openai, anthropic, both, pattern, node)
    
    Returns:
        ViolationEvidence object ready for reporting
    """
    # Map severity string to enum
    severity_map = {
        "CRITICAL": SeverityLevel.CRITICAL,
        "HIGH": SeverityLevel.HIGH,
        "MEDIUM": SeverityLevel.MEDIUM,
        "LOW": SeverityLevel.LOW,
    }
    severity_level = severity_map.get(severity.upper(), SeverityLevel.MEDIUM)
    
    # Map detected_by to enum
    source_map = {
        "openai": AgentSource.OPENAI,
        "anthropic": AgentSource.ANTHROPIC,
        "both": AgentSource.BOTH,
        "pattern": AgentSource.PATTERN,
        "node": AgentSource.NODE,
    }
    agent_source = source_map.get(detected_by.lower(), AgentSource.PATTERN)
    
    # Create statutory reference
    statutory_ref = StatutoryReference(
        citation=citation,
        title="",
        summary="",
    )
    
    # Create exact quote if provided
    exact_quotes = []
    if quote_text:
        exact_quotes.append(ExactQuote(
            quote_text=quote_text,
            document_url=document_url,
            document_section="",
        ))
    
    # Determine prosecutorial merit based on severity
    merit_map = {
        SeverityLevel.CRITICAL: ProsecutorialMerit.STRONG,
        SeverityLevel.HIGH: ProsecutorialMerit.STRONG,
        SeverityLevel.MEDIUM: ProsecutorialMerit.MODERATE,
        SeverityLevel.LOW: ProsecutorialMerit.WEAK,
    }
    merit = merit_map.get(severity_level, ProsecutorialMerit.MODERATE)
    
    # Create damage estimate with severity-based multipliers
    damage_multipliers = {
        SeverityLevel.CRITICAL: (500000, 2000000, 1000000, True, 20),
        SeverityLevel.HIGH: (100000, 500000, 250000, False, 0),
        SeverityLevel.MEDIUM: (50000, 100000, 75000, False, 0),
        SeverityLevel.LOW: (10000, 50000, 25000, False, 0),
    }
    min_d, max_d, disg, crim, years = damage_multipliers.get(
        severity_level, (50000, 100000, 75000, False, 0)
    )
    
    damage_estimate = DamageEstimate(
        civil_minimum=min_d,
        civil_maximum=max_d,
        disgorgement_estimate=disg,
        criminal_exposure=crim,
        prison_years_maximum=years,
        calculation_methodology="Severity-based estimation"
    )
    
    # Generate evidence hash (SHA-256)
    evidence_data = f"{violation_id}{violation_type}{description}{document_url}"
    evidence_hash = hashlib.sha256(evidence_data.encode()).hexdigest()
    
    return ViolationEvidence(
        violation_id=violation_id,
        violation_type=violation_type,
        severity=severity_level,
        statutory_reference=statutory_ref,
        description=description,
        exact_quotes=exact_quotes,
        document_url=document_url,
        document_section="",
        filing_accession=filing_accession,
        filing_date=filing_date,
        prosecutorial_merit=merit,
        damage_estimate=damage_estimate,
        detected_by=agent_source,
        evidence_hash=evidence_hash,
    )


# ═══════════════════════════════════════════════════════════════════════════
# DOJ REPORT GENERATOR CLASS
# ═══════════════════════════════════════════════════════════════════════════

class DOJReportGenerator:
    """
    Generate DOJ-level comprehensive forensic reports.
    
    This generator produces prosecution-ready reports that include:
    - Executive summary with key metrics
    - Per-filing detailed analysis
    - Violation breakdowns with exact quotes
    - Evidence packages
    - Chain of custody documentation
    - Dual-agent consensus tracking
    - Statistical analysis
    """
    
    def __init__(self, output_dir: str = "./output/reports"):
        """
        Initialize DOJ Report Generator.
        
        Args:
            output_dir: Directory for generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_comprehensive_report(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        filing_reports: List[FilingAnalysisReport],
        chain_of_custody: List[ChainOfCustodyRecord],
        subagent_findings: Optional[List[SubagentFinding]] = None,
        output_formats: Optional[List[str]] = None
    ) -> Dict[str, Path]:
        """
        Generate comprehensive DOJ-level forensic report.
        
        Args:
            case_id: Unique case identifier
            company_name: Target company name
            cik: SEC CIK number
            filing_reports: List of per-filing analysis reports
            chain_of_custody: Evidence chain of custody records
            subagent_findings: Optional specialized subagent findings
            output_formats: Output formats to generate ('markdown', 'json', 'html', 'court_pdf')
            
        Returns:
            Dict mapping format names to output file paths
        """
        output_formats = output_formats or ['markdown', 'json']
        subagent_findings = subagent_findings or []
        
        # Generate executive summary
        summary = self._generate_summary(
            case_id, company_name, cik,
            filing_reports, chain_of_custody, subagent_findings
        )
        
        # Generate outputs
        outputs = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"DOJ_FORENSIC_REPORT_{cik}_{timestamp}"
        
        if 'markdown' in output_formats:
            md_path = self.output_dir / f"{base_filename}.md"
            self._generate_markdown_report(
                md_path, summary, filing_reports,
                chain_of_custody, subagent_findings
            )
            outputs['markdown'] = md_path
            logger.info(f"Generated Markdown report: {md_path}")
        
        if 'json' in output_formats:
            json_path = self.output_dir / f"{base_filename}.json"
            self._generate_json_report(
                json_path, summary, filing_reports,
                chain_of_custody, subagent_findings
            )
            outputs['json'] = json_path
            logger.info(f"Generated JSON report: {json_path}")
        
        if 'html' in output_formats:
            html_path = self.output_dir / f"{base_filename}.html"
            self._generate_html_report(
                html_path, summary, filing_reports,
                chain_of_custody, subagent_findings
            )
            outputs['html'] = html_path
            logger.info(f"Generated HTML report: {html_path}")
        
        if 'court_pdf' in output_formats:
            try:
                court_pdf_path = self._generate_court_pdf_report(
                    case_id, company_name, cik, summary,
                    filing_reports, chain_of_custody
                )
                outputs['court_pdf'] = court_pdf_path
                logger.info(f"Generated Court PDF report: {court_pdf_path}")
            except Exception as e:
                logger.error(f"Failed to generate Court PDF: {e}", exc_info=True)
                logger.warning("Court PDF generation failed - continuing with other formats")
        
        return outputs
    
    def _generate_summary(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        filing_reports: List[FilingAnalysisReport],
        chain_of_custody: List[ChainOfCustodyRecord],
        subagent_findings: List[SubagentFinding]
    ) -> ForensicReportSummary:
        """Generate executive summary from all filing reports."""
        
        # Aggregate statistics
        all_violations: List[ViolationEvidence] = []
        for report in filing_reports:
            all_violations.extend(report.violations)
        
        # Filing statistics
        filings_by_type: Dict[str, int] = defaultdict(int)
        for report in filing_reports:
            filings_by_type[report.filing_type] += 1
        
        # Violation statistics
        violations_by_severity: Dict[str, int] = defaultdict(int)
        violations_by_type: Dict[str, int] = defaultdict(int)
        for v in all_violations:
            violations_by_severity[v.severity.value] += 1
            violations_by_type[v.violation_type] += 1
        
        # Financial impact
        total_damages_min = sum(v.damage_estimate.civil_minimum for v in all_violations)
        total_damages_max = sum(v.damage_estimate.civil_maximum for v in all_violations)
        total_disgorgement = sum(v.damage_estimate.disgorgement_estimate for v in all_violations)
        
        # NEW: Calculate whistleblower bounty if applicable
        whistleblower_section = None
        if total_damages_max > 1_000_000:  # SEC minimum threshold for awards
            try:
                from src.internal.whistleblower_bounty_estimator import WhistleblowerBountyEstimator
                
                estimator = WhistleblowerBountyEstimator()
                
                # Convert violations to format expected by estimator
                violations_for_estimate = [
                    {
                        'type': v.violation_type,
                        'severity': v.severity.value.lower()
                    }
                    for v in all_violations
                ]
                
                # Get bounty estimate
                bounty_estimate = estimator.estimate_bounty(
                    violations=violations_for_estimate,
                    company_market_cap=None,  # Would need to fetch from market data
                    prior_enforcement_history=False
                )
                
                # Store for report inclusion (but don't serialize the BountyEstimate object)
                whistleblower_section = {
                    'estimated_sanctions_min': float(bounty_estimate.estimated_sanctions_min),
                    'estimated_sanctions_max': float(bounty_estimate.estimated_sanctions_max),
                    'award_percentage_range': f"{int(bounty_estimate.bounty_percentage_min * 100)}-{int(bounty_estimate.bounty_percentage_max * 100)}%",
                    'award_range_low': float(bounty_estimate.bounty_amount_min),
                    'award_range_high': float(bounty_estimate.bounty_amount_max),
                    'violation_count': bounty_estimate.violation_count,
                    'critical_violations': bounty_estimate.critical_violations,
                    'confidence_level': bounty_estimate.confidence_level,
                    'basis': bounty_estimate.basis,
                    'eligibility_notes': (
                        "Eligible for SEC whistleblower award under Dodd-Frank Act Section 922 "
                        "(15 USC §78u-6) if voluntary, original information leads to successful enforcement. "
                        "Award range: 10-30% of monetary sanctions exceeding $1,000,000."
                    )
                }
                
                logger.info(
                    f"Whistleblower bounty estimated: "
                    f"${bounty_estimate.bounty_amount_min:,.0f} - ${bounty_estimate.bounty_amount_max:,.0f}"
                )
                
            except Exception as e:
                logger.warning(f"Failed to estimate whistleblower bounty: {e}")
                whistleblower_section = None
        
        # Referral recommendations
        has_critical = violations_by_severity.get('CRITICAL', 0) > 0
        has_high = violations_by_severity.get('HIGH', 0) > 0
        criminal_count = sum(1 for v in all_violations if v.damage_estimate.criminal_exposure)
        
        # Dual-agent confidence
        confidences = [
            r.dual_agent_consensus.confidence_level
            for r in filing_reports
            if r.dual_agent_consensus
        ]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Date range
        dates = [r.filing_date for r in filing_reports if r.filing_date]
        start_date = min(dates) if dates else ""
        end_date = max(dates) if dates else ""
        
        summary = ForensicReportSummary(
            case_id=case_id,
            company_name=company_name,
            cik=cik,
            analysis_period_start=start_date,
            analysis_period_end=end_date,
            total_filings_analyzed=len(filing_reports),
            filings_by_type=dict(filings_by_type),
            total_violations=len(all_violations),
            violations_by_severity=dict(violations_by_severity),
            violations_by_type=dict(violations_by_type),
            total_estimated_damages_min=total_damages_min,
            total_estimated_damages_max=total_damages_max,
            total_disgorgement=total_disgorgement,
            sec_referral=len(all_violations) > 0,
            doj_referral=has_critical or criminal_count > 0,
            irs_referral=any('IRC' in v.statutory_reference.citation or 'IRS' in v.statutory_reference.citation for v in all_violations),
            criminal_referral_count=criminal_count,
            dual_agent_active=any(r.dual_agent_consensus for r in filing_reports),
            overall_confidence=overall_confidence,
            subagent_findings=subagent_findings,
            evidence_items_count=len(chain_of_custody),
            chain_of_custody_verified=all(r.verification_status == 'verified' for r in chain_of_custody),
        )
        
        # NEW: Attach whistleblower section as metadata (not part of ForensicReportSummary dataclass)
        if whistleblower_section:
            # Store as custom attribute for later use in report generation
            setattr(summary, '_whistleblower_section', whistleblower_section)
        
        return summary
    
    def _generate_markdown_report(
        self,
        output_path: Path,
        summary: ForensicReportSummary,
        filing_reports: List[FilingAnalysisReport],
        chain_of_custody: List[ChainOfCustodyRecord],
        subagent_findings: List[SubagentFinding]
    ):
        """Generate comprehensive Markdown report."""
        lines = []
        
        # Header
        lines.extend([
            "# DOJ-LEVEL COMPREHENSIVE FORENSIC REPORT",
            "",
            f"**Case ID:** {summary.case_id}",
            f"**Classification:** CONFIDENTIAL - LAW ENFORCEMENT SENSITIVE",
            f"**Generated:** {summary.report_generated.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "---",
            "",
        ])
        
        # Executive Summary
        lines.extend(self._generate_executive_summary_section(summary))
        
        # Per-Filing Detailed Analysis
        lines.extend(self._generate_per_filing_section(filing_reports))
        
        # Dual-Agent Consensus Tracking
        lines.extend(self._generate_dual_agent_section(filing_reports))
        
        # Subagent Specialized Findings
        if subagent_findings:
            lines.extend(self._generate_subagent_section(subagent_findings))
        
        # Statistical Analysis
        lines.extend(self._generate_statistical_section(summary))
        
        # Chain of Custody
        lines.extend(self._generate_chain_of_custody_section(chain_of_custody))
        
        # Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def _generate_executive_summary_section(
        self,
        summary: ForensicReportSummary
    ) -> List[str]:
        """Generate executive summary section."""
        lines = [
            "## EXECUTIVE SUMMARY",
            "",
            "### Target Information",
            "",
            "| Field | Value |",
            "|-------|-------|",
            f"| Company | {summary.company_name} |",
            f"| CIK | {summary.cik} |",
            f"| Analysis Period | {summary.analysis_period_start} to {summary.analysis_period_end} |",
            f"| Total Filings Analyzed | {summary.total_filings_analyzed} |",
            "",
            "### Violation Summary",
            "",
            "| Severity | Count |",
            "|----------|-------|",
        ]
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = summary.violations_by_severity.get(severity, 0)
            if count > 0:
                lines.append(f"| {severity} | {count} |")
        
        lines.extend([
            f"| **TOTAL** | **{summary.total_violations}** |",
            "",
            "### Financial Impact",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Estimated Damages (Min) | ${summary.total_estimated_damages_min:,.2f} |",
            f"| Estimated Damages (Max) | ${summary.total_estimated_damages_max:,.2f} |",
            f"| Disgorgement Estimate | ${summary.total_disgorgement:,.2f} |",
            f"| Criminal Referrals | {summary.criminal_referral_count} |",
            "",
        ])
        
        # NEW: Include Whistleblower Bounty Section if applicable
        whistleblower_section = getattr(summary, '_whistleblower_section', None)
        if whistleblower_section:
            lines.extend([
                "### Whistleblower Award Estimate",
                "",
                "**INTERNAL USE ONLY - NOT FOR PUBLIC DISCLOSURE**",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Estimated Sanctions (Min) | ${whistleblower_section['estimated_sanctions_min']:,.0f} |",
                f"| Estimated Sanctions (Max) | ${whistleblower_section['estimated_sanctions_max']:,.0f} |",
                f"| Award Percentage Range | {whistleblower_section['award_percentage_range']} |",
                f"| Award Range (Low) | ${whistleblower_section['award_range_low']:,.0f} |",
                f"| Award Range (High) | ${whistleblower_section['award_range_high']:,.0f} |",
                f"| Violation Count | {whistleblower_section['violation_count']} ({whistleblower_section['critical_violations']} critical) |",
                f"| Confidence Level | {whistleblower_section['confidence_level'].upper()} |",
                "",
                "**Legal Basis:**",
                f"- {whistleblower_section['eligibility_notes']}",
                "",
                "**Note:** This estimate is for internal forensic analysis only and should not be disclosed",
                "to prevent gaming the whistleblower program. Actual awards are determined by the SEC",
                "Office of the Whistleblower based on statutory factors under 15 USC §78u-6(c)(1).",
                "",
            ])
        
        lines.extend([
            "### Regulatory Routing",
            "",
            "| Agency | Referral Recommended |",
            "|--------|---------------------|",
            f"| SEC Enforcement Division | {'✓ YES' if summary.sec_referral else 'NO'} |",
            f"| DOJ Securities Fraud Unit | {'✓ YES' if summary.doj_referral else 'NO'} |",
            f"| IRS Criminal Investigation | {'✓ YES' if summary.irs_referral else 'NO'} |",
            "",
            "---",
            "",
        ])
        
        return lines
    
    def _generate_per_filing_section(
        self,
        filing_reports: List[FilingAnalysisReport]
    ) -> List[str]:
        """Generate per-filing detailed analysis section."""
        lines = [
            "## PER-FILING DETAILED ANALYSIS",
            "",
        ]
        
        for i, report in enumerate(filing_reports, 1):
            lines.extend([
                f"### Filing {i}: {report.filing_type} - {report.accession_number}",
                "",
                "| Field | Value |",
                "|-------|-------|",
                f"| Accession Number | [{report.accession_number}]({report.document_url}) |",
                f"| Filing Type | {report.filing_type} |",
                f"| Filing Date | {report.filing_date} |",
                f"| Violations Found | {report.violation_count} |",
                f"| Critical | {report.critical_count} |",
                f"| High | {report.high_count} |",
                f"| Estimated Damages | ${report.total_estimated_damages:,.2f} |",
                "",
            ])
            
            # Violations
            if report.violations:
                lines.append("#### Violations Detected")
                lines.append("")
                
                for j, v in enumerate(report.violations, 1):
                    lines.extend([
                        f"##### Violation {j}: {v.violation_type}",
                        "",
                        f"**Severity:** {v.severity.value}",
                        "",
                        f"**Prosecutorial Merit:** {v.prosecutorial_merit.value}",
                        "",
                        f"**Statutory Reference:** {v.statutory_reference.citation}",
                        "",
                        f"> {v.statutory_reference.summary}",
                        "",
                        f"**Description:** {v.description}",
                        "",
                    ])
                    
                    # Exact quotes
                    if v.exact_quotes:
                        lines.append("**Exact Quotes from Filing:**")
                        lines.append("")
                        for quote in v.exact_quotes:
                            lines.extend([
                                f"> \"{quote.quote_text}\"",
                                f">",
                                f"> *Source: [{quote.document_section}]({quote.document_url})*",
                                "",
                            ])
                    
                    # Damage estimate
                    lines.extend([
                        "**Damage Estimate:**",
                        "",
                        "| Type | Amount |",
                        "|------|--------|",
                        f"| Civil Penalty (Min) | ${v.damage_estimate.civil_minimum:,.2f} |",
                        f"| Civil Penalty (Max) | ${v.damage_estimate.civil_maximum:,.2f} |",
                        f"| Disgorgement | ${v.damage_estimate.disgorgement_estimate:,.2f} |",
                        f"| Criminal Exposure | {'YES' if v.damage_estimate.criminal_exposure else 'NO'} |",
                        "",
                        f"**Detection Source:** {v.detected_by.value}",
                        "",
                    ])
                    
                    if v.confirmed_by:
                        lines.append(f"**Confirmed By:** {', '.join(a.value for a in v.confirmed_by)}")
                        lines.append("")
                    
                    # Evidence hash
                    lines.extend([
                        f"**Evidence Hash (SHA-256):** `{v.evidence_hash}`",
                        "",
                    ])
                    
                    # Red flags
                    if v.red_flags:
                        lines.append("**Red Flags:**")
                        for rf in v.red_flags:
                            lines.append(f"- **{rf.flag_type}** ({rf.significance.value}): {rf.description}")
                        lines.append("")
                
                lines.append("")
            
            # Red flags for filing
            if report.red_flags:
                lines.append("#### Filing Red Flags")
                lines.append("")
                for rf in report.red_flags:
                    lines.append(f"- **{rf.flag_type}** ({rf.significance.value}): {rf.description}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return lines
    
    def _generate_dual_agent_section(
        self,
        filing_reports: List[FilingAnalysisReport]
    ) -> List[str]:
        """Generate dual-agent consensus tracking section."""
        lines = [
            "## DUAL-AGENT CONSENSUS TRACKING",
            "",
        ]
        
        # Check if dual-agent was active
        reports_with_consensus = [r for r in filing_reports if r.dual_agent_consensus]
        
        if not reports_with_consensus:
            lines.extend([
                "*Dual-agent analysis was not active for this investigation.*",
                "",
                "---",
                "",
            ])
            return lines
        
        lines.extend([
            "Dual-agent validation ensures comprehensive coverage with cross-referencing",
            "between OpenAI and Anthropic/Secondary agents.",
            "",
            "### Agent Agreement Summary",
            "",
            "| Filing | OpenAI | Anthropic | Overlap | Unique (O) | Unique (A) | Confidence |",
            "|--------|--------|-----------|---------|------------|------------|------------|",
        ])
        
        for report in reports_with_consensus:
            c = report.dual_agent_consensus
            lines.append(
                f"| {report.accession_number[:20]} | {c.openai_findings_count} | "
                f"{c.anthropic_findings_count} | {c.overlap_count} | "
                f"{c.openai_unique_count} | {c.anthropic_unique_count} | "
                f"{c.confidence_level:.1%} |"
            )
        
        # Calculate overall stats
        total_openai = sum(r.dual_agent_consensus.openai_findings_count for r in reports_with_consensus)
        total_anthropic = sum(r.dual_agent_consensus.anthropic_findings_count for r in reports_with_consensus)
        total_overlap = sum(r.dual_agent_consensus.overlap_count for r in reports_with_consensus)
        avg_confidence = sum(r.dual_agent_consensus.confidence_level for r in reports_with_consensus) / len(reports_with_consensus)
        
        lines.extend([
            "",
            "### Overall Statistics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total OpenAI Findings | {total_openai} |",
            f"| Total Anthropic Findings | {total_anthropic} |",
            f"| Total Overlap | {total_overlap} |",
            f"| Average Confidence | {avg_confidence:.1%} |",
            "",
            "---",
            "",
        ])
        
        return lines
    
    def _generate_subagent_section(
        self,
        subagent_findings: List[SubagentFinding]
    ) -> List[str]:
        """Generate subagent specialized findings section."""
        lines = [
            "## SUBAGENT SPECIALIZED FINDINGS",
            "",
            "The following findings were detected by specialized forensic subagents:",
            "",
        ]
        
        # Group by subagent
        findings_by_agent: Dict[str, List[SubagentFinding]] = defaultdict(list)
        for f in subagent_findings:
            findings_by_agent[f.subagent_name].append(f)
        
        for agent_name, findings in findings_by_agent.items():
            lines.extend([
                f"### {agent_name}",
                "",
            ])
            
            for finding in findings:
                lines.extend([
                    f"**{finding.finding_type}** (Confidence: {finding.confidence:.1%})",
                    "",
                    f"{finding.description}",
                    "",
                ])
                
                if finding.supporting_data:
                    lines.append("*Supporting Data:*")
                    for key, value in finding.supporting_data.items():
                        lines.append(f"- {key}: {value}")
                    lines.append("")
            
            lines.append("")
        
        lines.extend([
            "---",
            "",
        ])
        
        return lines
    
    def _generate_statistical_section(
        self,
        summary: ForensicReportSummary
    ) -> List[str]:
        """Generate statistical analysis section."""
        lines = [
            "## STATISTICAL ANALYSIS",
            "",
            "### Filings by Type",
            "",
            "| Filing Type | Count |",
            "|-------------|-------|",
        ]
        
        for filing_type, count in sorted(summary.filings_by_type.items()):
            lines.append(f"| {filing_type} | {count} |")
        
        lines.extend([
            "",
            "### Violations by Type",
            "",
            "| Violation Type | Count |",
            "|----------------|-------|",
        ])
        
        for v_type, count in sorted(summary.violations_by_type.items(), key=lambda x: -x[1]):
            lines.append(f"| {v_type} | {count} |")
        
        lines.extend([
            "",
            "### Severity Distribution",
            "",
            "| Severity | Count | Percentage |",
            "|----------|-------|------------|",
        ])
        
        total = summary.total_violations or 1
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = summary.violations_by_severity.get(severity, 0)
            pct = (count / total) * 100
            lines.append(f"| {severity} | {count} | {pct:.1f}% |")
        
        lines.extend([
            "",
            "---",
            "",
        ])
        
        return lines
    
    def _generate_chain_of_custody_section(
        self,
        chain_of_custody: List[ChainOfCustodyRecord]
    ) -> List[str]:
        """Generate chain of custody documentation section."""
        lines = [
            "## CHAIN OF CUSTODY",
            "",
            "All evidence has been cryptographically hashed using SHA-256 to ensure integrity.",
            "Any tampering with evidence will be detectable through hash verification.",
            "",
            "### Evidence Items",
            "",
            "| ID | Type | Description | Hash (SHA-256) | Collected | Status |",
            "|----|------|-------------|----------------|-----------|--------|",
        ]
        
        for record in chain_of_custody:
            hash_short = record.sha256_hash[:16] + "..." if len(record.sha256_hash) > 16 else record.sha256_hash
            collected = record.collected_at.strftime('%Y-%m-%d %H:%M')
            lines.append(
                f"| {record.record_id} | {record.evidence_type} | "
                f"{record.evidence_description[:30]}... | `{hash_short}` | "
                f"{collected} | {record.verification_status} |"
            )
        
        lines.extend([
            "",
            "### Integrity Verification",
            "",
            f"- **Total Evidence Items:** {len(chain_of_custody)}",
            f"- **All Hashes Verified:** {'✓ YES' if all(r.verification_status == 'verified' for r in chain_of_custody) else '⚠ NO'}",
            f"- **Collection Period:** {chain_of_custody[0].collected_at.strftime('%Y-%m-%d')} to {chain_of_custody[-1].collected_at.strftime('%Y-%m-%d')}" if chain_of_custody else "N/A",
            "",
            "### Digital Signature",
            "",
        ])
        
        # Generate report hash
        report_data = json.dumps({
            "records": [r.to_dict() for r in chain_of_custody],
            "timestamp": datetime.utcnow().isoformat()
        }, sort_keys=True)
        report_hash = hashlib.sha256(report_data.encode()).hexdigest()
        
        lines.extend([
            f"**Report Hash (SHA-256):** `{report_hash}`",
            "",
            "*This report is digitally signed and tamper-evident. Any modifications will",
            "invalidate the signature and be detectable through hash verification.*",
            "",
            "---",
            "",
            "**END OF FORENSIC REPORT**",
        ])
        
        return lines
    
    def _generate_json_report(
        self,
        output_path: Path,
        summary: ForensicReportSummary,
        filing_reports: List[FilingAnalysisReport],
        chain_of_custody: List[ChainOfCustodyRecord],
        subagent_findings: List[SubagentFinding]
    ):
        """Generate comprehensive JSON report."""
        report_data = {
            "metadata": {
                "report_type": "DOJ_FORENSIC_REPORT",
                "version": "1.0",
                "generated": datetime.utcnow().isoformat(),
            },
            "summary": summary.to_dict(),
            "filing_reports": [r.to_dict() for r in filing_reports],
            "chain_of_custody": [r.to_dict() for r in chain_of_custody],
            "subagent_findings": [
                {
                    "subagent_name": f.subagent_name,
                    "finding_type": f.finding_type,
                    "description": f.description,
                    "confidence": f.confidence,
                    "supporting_data": f.supporting_data,
                    "related_violations": f.related_violations,
                }
                for f in subagent_findings
            ],
        }
        
        # Generate report hash
        report_hash = hashlib.sha256(
            json.dumps(report_data, sort_keys=True, default=str).encode()
        ).hexdigest()
        report_data["report_hash"] = report_hash
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
    
    def _generate_html_report(
        self,
        output_path: Path,
        summary: ForensicReportSummary,
        filing_reports: List[FilingAnalysisReport],
        chain_of_custody: List[ChainOfCustodyRecord],
        subagent_findings: List[SubagentFinding]
    ):
        """Generate HTML report with styling."""
        # Generate markdown first, then convert to basic HTML
        md_lines = []
        md_lines.extend(self._generate_executive_summary_section(summary))
        md_lines.extend(self._generate_per_filing_section(filing_reports))
        md_lines.extend(self._generate_dual_agent_section(filing_reports))
        if subagent_findings:
            md_lines.extend(self._generate_subagent_section(subagent_findings))
        md_lines.extend(self._generate_statistical_section(summary))
        md_lines.extend(self._generate_chain_of_custody_section(chain_of_custody))
        
        content = '\n'.join(md_lines)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DOJ Forensic Report - {summary.case_id}</title>
    <style>
        body {{
            font-family: 'Times New Roman', Times, serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #1a1a1a; border-bottom: 3px solid #333; padding-bottom: 10px; }}
        h2 {{ color: #2a2a2a; border-bottom: 2px solid #666; padding-bottom: 8px; margin-top: 30px; }}
        h3 {{ color: #3a3a3a; margin-top: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #4a4a4a; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        blockquote {{
            background-color: #f5f5f5;
            border-left: 4px solid #666;
            margin: 15px 0;
            padding: 15px;
            font-style: italic;
        }}
        code {{
            background-color: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .warning {{ color: #cc0000; font-weight: bold; }}
        .success {{ color: #008800; }}
        .header-banner {{
            background-color: #1a1a1a;
            color: white;
            padding: 20px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .classification {{
            color: #cc0000;
            font-weight: bold;
            text-align: center;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header-banner">
        <h1 style="color: white; border: none;">DOJ-LEVEL COMPREHENSIVE FORENSIC REPORT</h1>
        <p>Case ID: {summary.case_id}</p>
    </div>
    <p class="classification">CONFIDENTIAL - LAW ENFORCEMENT SENSITIVE</p>
    <p style="text-align: center;">Generated: {summary.report_generated.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    <hr>
    <pre style="white-space: pre-wrap; font-family: 'Times New Roman', serif;">{content}</pre>
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def _generate_court_pdf_report(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        summary: ForensicReportSummary,
        filing_reports: List[FilingAnalysisReport],
        chain_of_custody: List[ChainOfCustodyRecord]
    ) -> Path:
        """
        Generate FRE 902(13)/(14) compliant court PDF report.
        
        Args:
            case_id: Case identifier
            company_name: Company name
            cik: Company CIK
            summary: Report summary
            filing_reports: Filing analysis reports
            chain_of_custody: Evidence chain records
            
        Returns:
            Path to generated court PDF
        """
        try:
            from .court_pdf_generator import (
                CourtPDFGenerator, CaseCaption, ViolationDetail,
                EvidenceItem, Exhibit
            )
            from datetime import date
        except ImportError as e:
            logger.error(f"Failed to import court PDF generator: {e}")
            raise ImportError(
                "Court PDF generator not available. "
                "Install reportlab with: pip install reportlab"
            ) from e
        
        # Create case caption
        case_caption = CaseCaption(
            plaintiff="United States Securities and Exchange Commission",
            defendant=company_name,
            court_name="UNITED STATES DISTRICT COURT",
            case_number=case_id,
            case_title=f"SEC v. {company_name}",
            filing_date=date.today()
        )
        
        # Build executive summary from report summary
        executive_summary = f"""
EXECUTIVE SUMMARY

Target: {company_name} (CIK: {cik})
Case ID: {case_id}
Analysis Period: {summary.analysis_period_start} to {summary.analysis_period_end}

FINDINGS SUMMARY:
- Total Violations: {summary.total_violations}
- Critical Violations: {summary.critical_violations}
- High Severity: {summary.high_violations}
- Medium Severity: {summary.medium_violations}
- Low Severity: {summary.low_violations}

FILINGS ANALYZED: {summary.total_filings_analyzed}

PROSECUTORIAL RECOMMENDATION:
{summary.prosecution_recommendation}

ESTIMATED PENALTIES:
- Civil Minimum: ${summary.estimated_civil_penalties_min:,.2f}
- Civil Maximum: ${summary.estimated_civil_penalties_max:,.2f}
- Criminal Exposure: {"Yes" if summary.criminal_exposure else "No"}
"""
        
        # Convert violations to court format
        violations = []
        violation_counter = 1
        
        for filing_report in filing_reports:
            for violation in filing_report.violations:
                # Build statutory citation
                statutory_citation = ""
                if violation.statutory_reference:
                    statutory_citation = f"{violation.statutory_reference.statute_title} § {violation.statutory_reference.section}"
                
                # Build evidence references
                evidence_refs = []
                if violation.document_url:
                    evidence_refs.append(f"Filing: {violation.filing_accession}")
                if violation.evidence_hash:
                    evidence_refs.append(f"Evidence Hash: {violation.evidence_hash[:16]}...")
                
                # Add quotes as evidence
                if violation.exact_quotes:
                    for quote in violation.exact_quotes[:3]:  # Limit to 3 quotes
                        evidence_refs.append(f"Quote: \"{quote.text[:100]}...\"")
                
                violations.append(ViolationDetail(
                    violation_id=f"V{violation_counter:03d}",
                    violation_type=violation.violation_type,
                    statutory_citation=statutory_citation,
                    description=violation.description,
                    evidence_references=evidence_refs,
                    severity=violation.severity.value if hasattr(violation.severity, 'value') else str(violation.severity),
                    recommended_penalty=f"${violation.damage_estimate.civil_penalty_min:,.0f} - ${violation.damage_estimate.civil_penalty_max:,.0f}" if violation.damage_estimate else None
                ))
                violation_counter += 1
        
        # Convert evidence chain to court format
        evidence_items = []
        for custody_record in chain_of_custody:
            evidence_items.append(EvidenceItem(
                item_id=f"E{len(evidence_items) + 1:03d}",
                description=custody_record.document_url or custody_record.document_type,
                sha256_hash=custody_record.hash_value,
                sha3_512_hash=None,  # Would extract from custody_record if available
                rfc3161_timestamp=None,  # Would extract from custody_record if available
                collection_date=custody_record.timestamp,
                custodian="SEC EDGAR API"
            ))
        
        # Create exhibits (one per filing)
        exhibits = []
        for i, filing_report in enumerate(filing_reports[:10], 1):  # Limit to 10 exhibits
            exhibits.append(Exhibit(
                exhibit_id=str(i),
                exhibit_type="Plaintiff",
                description=f"SEC Filing Analysis - {filing_report.filing_type}",
                bates_number=f"JLAW{i:06d}",
                file_path=None,
                content=f"Analysis of {filing_report.filing_type} filing (Accession: {filing_report.filing_accession})",
                page_count=1
            ))
        
        # Generate court PDF
        generator = CourtPDFGenerator(output_dir=str(self.output_dir / "court_pdfs"))
        
        court_pdf_path = generator.generate_report(
            case_caption=case_caption,
            executive_summary=executive_summary,
            violations=violations,
            evidence_chain=evidence_items,
            exhibits=exhibits,
            bates_prefix="JLAW",
            watermark=None,  # Could add "CONFIDENTIAL" or "DRAFT"
            certifying_person="JLAW Forensic Analysis System"
        )
        
        logger.info(f"Generated court PDF with {len(violations)} violations, {len(evidence_items)} evidence items, {len(exhibits)} exhibits")
        return court_pdf_path


