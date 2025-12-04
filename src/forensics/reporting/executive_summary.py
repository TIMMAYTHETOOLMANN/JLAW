"""
Executive Summary Generator
============================

Generates high-level executive summaries for forensic investigations.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SummaryLevel(Enum):
    """Summary detail levels."""
    BRIEF = "brief"  # 1-2 paragraphs
    STANDARD = "standard"  # Half page
    DETAILED = "detailed"  # Full page


class RecommendationType(Enum):
    """Types of recommendations."""
    IMMEDIATE_ACTION = "immediate_action"
    FURTHER_INVESTIGATION = "further_investigation"
    REGULATORY_FILING = "regulatory_filing"
    LEGAL_CONSULTATION = "legal_consultation"
    EVIDENCE_PRESERVATION = "evidence_preservation"
    NO_ACTION = "no_action"


@dataclass
class KeyFinding:
    """A key finding for the executive summary."""
    title: str
    description: str
    severity: str  # critical, high, medium, low
    evidence_refs: List[str] = field(default_factory=list)
    implications: str = ""


@dataclass
class Recommendation:
    """An actionable recommendation."""
    recommendation_type: RecommendationType
    title: str
    description: str
    priority: int  # 1 = highest
    timeline: str = ""
    resources_required: str = ""


@dataclass
class ExecutiveSummary:
    """Complete executive summary."""
    case_id: str
    target: str
    generated_at: datetime
    level: SummaryLevel
    
    # Overview
    investigation_period: str = ""
    documents_analyzed: int = 0
    
    # Key metrics
    risk_level: str = ""
    case_strength: str = ""
    conviction_probability: float = 0.0
    
    # Findings
    key_findings: List[KeyFinding] = field(default_factory=list)
    total_violations: int = 0
    total_contradictions: int = 0
    
    # Recommendations
    recommendations: List[Recommendation] = field(default_factory=list)
    
    # Narrative
    overview_text: str = ""
    findings_text: str = ""
    recommendations_text: str = ""
    conclusion_text: str = ""


class ExecutiveSummaryGenerator:
    """
    Executive Summary Generator
    
    Creates high-level executive summaries for forensic investigations
    suitable for presentation to stakeholders and decision-makers.
    
    Features:
    - Multiple summary levels
    - Key findings extraction
    - Actionable recommendations
    - Risk assessment summary
    
    Example:
        generator = ExecutiveSummaryGenerator()
        
        summary = generator.generate(
            case_id="CASE-001",
            target="Company XYZ",
            investigation_results=results,
            level=SummaryLevel.STANDARD
        )
        
        text = generator.render_text(summary)
    """
    
    def __init__(self):
        """Initialize the executive summary generator."""
        logger.info("ExecutiveSummaryGenerator initialized")
    
    def generate(
        self,
        case_id: str,
        target: str,
        investigation_results: Dict[str, Any],
        level: SummaryLevel = SummaryLevel.STANDARD
    ) -> ExecutiveSummary:
        """
        Generate an executive summary.
        
        Args:
            case_id: Case identifier
            target: Investigation target
            investigation_results: Complete investigation results
            level: Summary detail level
            
        Returns:
            Executive summary
        """
        summary = ExecutiveSummary(
            case_id=case_id,
            target=target,
            generated_at=datetime.now(),
            level=level
        )
        
        # Extract metrics
        self._extract_metrics(summary, investigation_results)
        
        # Extract key findings
        summary.key_findings = self._extract_key_findings(investigation_results)
        
        # Generate recommendations
        summary.recommendations = self._generate_recommendations(summary, investigation_results)
        
        # Generate narrative text
        self._generate_narrative(summary)
        
        logger.info(f"Generated executive summary for case {case_id}")
        return summary
    
    def _extract_metrics(
        self,
        summary: ExecutiveSummary,
        results: Dict[str, Any]
    ) -> None:
        """Extract key metrics from investigation results."""
        # Get from summary section
        if "summary" in results:
            overall = results["summary"].get("overall", {})
            summary.risk_level = overall.get("risk_level", "Unknown")
            summary.case_strength = overall.get("case_strength", "Unknown")
            summary.conviction_probability = overall.get("conviction_probability", 0.0)
        
        # Count violations and contradictions
        phases = results.get("phases", {})
        
        for phase_name, phase_data in phases.items():
            phase_results = phase_data.get("results", {})
            
            if "potential_violations" in phase_results:
                summary.total_violations += phase_results["potential_violations"]
            
            if "contradictions_detected" in phase_results:
                summary.total_contradictions += phase_results["contradictions_detected"]
            
            if "documents_processed" in phase_results:
                summary.documents_analyzed += phase_results["documents_processed"]
    
    def _extract_key_findings(
        self,
        results: Dict[str, Any]
    ) -> List[KeyFinding]:
        """Extract key findings from investigation results."""
        findings = []
        
        phases = results.get("phases", {})
        
        # Legal violations
        legal_results = phases.get("phase_3_legal_correlation", {}).get("results", {})
        if legal_results.get("potential_violations", 0) > 0:
            findings.append(KeyFinding(
                title="Legal Violations Identified",
                description=f"Analysis identified {legal_results['potential_violations']} potential legal violations.",
                severity="high",
                evidence_refs=legal_results.get("usc_citations", []),
                implications="May warrant regulatory filing or criminal referral."
            ))
        
        # Contradictions
        contradict_results = phases.get("phase_6_contradiction_detection", {}).get("results", {})
        if contradict_results.get("high_severity_contradictions", 0) > 0:
            findings.append(KeyFinding(
                title="Significant Contradictions Detected",
                description=f"Found {contradict_results['high_severity_contradictions']} high-severity contradictions in analyzed documents.",
                severity="high",
                implications="Contradictions may indicate intentional misrepresentation."
            ))
        
        # Prosecution viability
        prosecution_results = phases.get("phase_5_prosecution_path", {}).get("results", {})
        if prosecution_results.get("success_probability", 0) > 0.7:
            findings.append(KeyFinding(
                title="Strong Case for Prosecution",
                description=f"Prosecution success probability estimated at {prosecution_results['success_probability']*100:.0f}%.",
                severity="critical",
                implications=f"Recommended path: {prosecution_results.get('recommended_path', 'N/A')}"
            ))
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        findings.sort(key=lambda f: severity_order.get(f.severity, 4))
        
        return findings[:5]  # Top 5 findings
    
    def _generate_recommendations(
        self,
        summary: ExecutiveSummary,
        results: Dict[str, Any]
    ) -> List[Recommendation]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Based on risk level
        if summary.risk_level in ["critical", "high"]:
            recommendations.append(Recommendation(
                recommendation_type=RecommendationType.IMMEDIATE_ACTION,
                title="Escalate to Senior Leadership",
                description="Given the high risk level, immediate escalation to senior leadership is recommended.",
                priority=1,
                timeline="Within 24 hours"
            ))
        
        # Based on violations
        if summary.total_violations > 0:
            recommendations.append(Recommendation(
                recommendation_type=RecommendationType.REGULATORY_FILING,
                title="Prepare Regulatory Filing",
                description="Consider preparing SEC TCR or other appropriate regulatory filing based on identified violations.",
                priority=2,
                timeline="Within 2 weeks"
            ))
        
        # Based on conviction probability
        if summary.conviction_probability >= 0.7:
            recommendations.append(Recommendation(
                recommendation_type=RecommendationType.LEGAL_CONSULTATION,
                title="Engage Legal Counsel",
                description="Strong case metrics suggest formal legal consultation for prosecution planning.",
                priority=2,
                timeline="Within 1 week"
            ))
        elif summary.conviction_probability >= 0.5:
            recommendations.append(Recommendation(
                recommendation_type=RecommendationType.FURTHER_INVESTIGATION,
                title="Continue Investigation",
                description="Moderate case strength indicates additional evidence gathering may strengthen the case.",
                priority=3,
                timeline="Ongoing"
            ))
        
        # Evidence preservation
        recommendations.append(Recommendation(
            recommendation_type=RecommendationType.EVIDENCE_PRESERVATION,
            title="Preserve Evidence Chain",
            description="Ensure all evidence is properly documented and preserved with chain of custody.",
            priority=3,
            timeline="Immediate and ongoing"
        ))
        
        # Sort by priority
        recommendations.sort(key=lambda r: r.priority)
        
        return recommendations
    
    def _generate_narrative(self, summary: ExecutiveSummary) -> None:
        """Generate narrative text sections."""
        # Overview
        summary.overview_text = self._generate_overview(summary)
        
        # Findings
        summary.findings_text = self._generate_findings_text(summary)
        
        # Recommendations
        summary.recommendations_text = self._generate_recommendations_text(summary)
        
        # Conclusion
        summary.conclusion_text = self._generate_conclusion(summary)
    
    def _generate_overview(self, summary: ExecutiveSummary) -> str:
        """Generate overview text."""
        return f"""This executive summary presents the findings of the forensic investigation 
into {summary.target} (Case ID: {summary.case_id}). The investigation analyzed 
{summary.documents_analyzed} documents and identified {summary.total_violations} potential 
violations and {summary.total_contradictions} contradictions. The overall risk level is 
assessed as {summary.risk_level.upper()} with a case strength rating of {summary.case_strength}."""
    
    def _generate_findings_text(self, summary: ExecutiveSummary) -> str:
        """Generate findings text."""
        if not summary.key_findings:
            return "No significant findings were identified during this investigation."
        
        text_parts = ["Key findings from the investigation include:\n"]
        
        for i, finding in enumerate(summary.key_findings, 1):
            text_parts.append(f"\n{i}. {finding.title} ({finding.severity.upper()})")
            text_parts.append(f"\n   {finding.description}")
            if finding.implications:
                text_parts.append(f"\n   Implications: {finding.implications}")
        
        return "".join(text_parts)
    
    def _generate_recommendations_text(self, summary: ExecutiveSummary) -> str:
        """Generate recommendations text."""
        if not summary.recommendations:
            return "No specific recommendations at this time."
        
        text_parts = ["Based on the investigation findings, the following actions are recommended:\n"]
        
        for rec in summary.recommendations:
            text_parts.append(f"\n• {rec.title}")
            text_parts.append(f"\n  {rec.description}")
            if rec.timeline:
                text_parts.append(f"\n  Timeline: {rec.timeline}")
        
        return "".join(text_parts)
    
    def _generate_conclusion(self, summary: ExecutiveSummary) -> str:
        """Generate conclusion text."""
        if summary.conviction_probability >= 0.7:
            outlook = "The investigation has yielded strong evidence supporting prosecution."
        elif summary.conviction_probability >= 0.5:
            outlook = "The investigation shows moderate evidence that may support further action with additional investigation."
        else:
            outlook = "Current evidence may be insufficient for prosecution; continued monitoring is recommended."
        
        return f"""{outlook}

The estimated conviction probability is {summary.conviction_probability*100:.0f}%. This assessment 
is based on the totality of evidence gathered, including {len(summary.key_findings)} key findings 
and comprehensive analysis across all investigation phases.

For questions regarding this summary or the underlying investigation, please contact the 
forensic analysis team."""
    
    def render_text(self, summary: ExecutiveSummary) -> str:
        """
        Render executive summary as plain text.
        
        Args:
            summary: Executive summary
            
        Returns:
            Formatted text
        """
        lines = [
            "=" * 80,
            "EXECUTIVE SUMMARY",
            "=" * 80,
            "",
            f"Case ID: {summary.case_id}",
            f"Target: {summary.target}",
            f"Generated: {summary.generated_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "-" * 40,
            "OVERVIEW",
            "-" * 40,
            summary.overview_text,
            "",
            "-" * 40,
            "KEY METRICS",
            "-" * 40,
            f"Risk Level: {summary.risk_level.upper()}",
            f"Case Strength: {summary.case_strength}",
            f"Conviction Probability: {summary.conviction_probability*100:.0f}%",
            f"Documents Analyzed: {summary.documents_analyzed}",
            f"Violations Identified: {summary.total_violations}",
            f"Contradictions Found: {summary.total_contradictions}",
            "",
            "-" * 40,
            "KEY FINDINGS",
            "-" * 40,
            summary.findings_text,
            "",
            "-" * 40,
            "RECOMMENDATIONS",
            "-" * 40,
            summary.recommendations_text,
            "",
            "-" * 40,
            "CONCLUSION",
            "-" * 40,
            summary.conclusion_text,
            "",
            "=" * 80,
        ]
        
        return "\n".join(lines)
    
    def render_html(self, summary: ExecutiveSummary) -> str:
        """Render executive summary as HTML."""
        findings_html = ""
        for finding in summary.key_findings:
            findings_html += f"""
            <div class="finding {finding.severity}">
                <h4>{finding.title}</h4>
                <p>{finding.description}</p>
                {f'<p class="implications"><em>Implications: {finding.implications}</em></p>' if finding.implications else ''}
            </div>"""
        
        recommendations_html = ""
        for rec in summary.recommendations:
            recommendations_html += f"""
            <div class="recommendation">
                <h4>{rec.title}</h4>
                <p>{rec.description}</p>
                {f'<p class="timeline"><strong>Timeline:</strong> {rec.timeline}</p>' if rec.timeline else ''}
            </div>"""
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Executive Summary - {summary.case_id}</title>
    <style>
        body {{ font-family: Georgia, serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }}
        h1 {{ color: #1a1a2e; border-bottom: 2px solid #1a1a2e; padding-bottom: 10px; }}
        h2 {{ color: #333; margin-top: 30px; }}
        .meta {{ color: #666; font-size: 14px; margin-bottom: 20px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .metric .value {{ font-size: 28px; font-weight: bold; color: #1a1a2e; }}
        .metric .label {{ font-size: 12px; color: #666; }}
        .finding {{ padding: 15px; margin: 10px 0; border-left: 4px solid #ccc; background: #f9f9f9; }}
        .finding.critical {{ border-color: #dc2626; background: #fef2f2; }}
        .finding.high {{ border-color: #f59e0b; background: #fffbeb; }}
        .recommendation {{ padding: 15px; margin: 10px 0; background: #eff6ff; border-radius: 8px; }}
        .conclusion {{ background: #f0fdf4; padding: 20px; border-radius: 8px; margin-top: 20px; }}
    </style>
</head>
<body>
    <h1>Executive Summary</h1>
    <div class="meta">
        <strong>Case ID:</strong> {summary.case_id} | 
        <strong>Target:</strong> {summary.target} | 
        <strong>Generated:</strong> {summary.generated_at.strftime('%Y-%m-%d %H:%M')}
    </div>
    
    <h2>Overview</h2>
    <p>{summary.overview_text}</p>
    
    <h2>Key Metrics</h2>
    <div class="metrics">
        <div class="metric">
            <div class="value">{summary.risk_level.upper()}</div>
            <div class="label">Risk Level</div>
        </div>
        <div class="metric">
            <div class="value">{summary.conviction_probability*100:.0f}%</div>
            <div class="label">Conviction Probability</div>
        </div>
        <div class="metric">
            <div class="value">{summary.total_violations}</div>
            <div class="label">Violations</div>
        </div>
    </div>
    
    <h2>Key Findings</h2>
    {findings_html if findings_html else '<p>No significant findings identified.</p>'}
    
    <h2>Recommendations</h2>
    {recommendations_html if recommendations_html else '<p>No specific recommendations at this time.</p>'}
    
    <h2>Conclusion</h2>
    <div class="conclusion">
        <p>{summary.conclusion_text.replace(chr(10), '</p><p>')}</p>
    </div>
</body>
</html>"""
