"""
Enhanced Forensic System - Master Orchestration Layer
===================================================

Unified orchestration of all forensic analysis capabilities:
- Document extraction and parsing
- Entity extraction
- Benford's Law analysis
- Temporal analysis
- Contradiction detection
- Legal statute correlation
- Prosecution case building
- Evidence chain management
- Reporting and visualization

This is the main entry point for comprehensive forensic analysis.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from .benfords_law_analyzer import BenfordsLawAnalyzer, BenfordsAnalysisResult
from .financial_entity_extractor import FinancialEntityExtractor, ExtractionResult
from .rfc3161_timestamper import RFC3161Timestamper, TimestampToken

logger = logging.getLogger(__name__)


@dataclass
class ForensicCase:
    """Complete forensic investigation case"""
    case_id: str
    target: str
    case_type: str  # sec_filing, contract, financial_statement
    created_at: datetime
    
    # Source documents
    documents: List[Dict[str, Any]] = field(default_factory=list)
    
    # Extraction results
    entities: Optional[ExtractionResult] = None
    
    # Analysis results
    benfords_analysis: Optional[BenfordsAnalysisResult] = None
    temporal_analysis: Optional[Dict[str, Any]] = None
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    legal_violations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Evidence chain
    evidence_chain: List[Dict[str, Any]] = field(default_factory=list)
    timestamps: List[TimestampToken] = field(default_factory=list)
    
    # Results
    findings: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    prosecutability_score: float = 0.0
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ForensicReport:
    """Comprehensive forensic analysis report"""
    case: ForensicCase
    executive_summary: str
    detailed_findings: List[Dict[str, Any]]
    evidence_summary: Dict[str, Any]
    legal_analysis: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime
    report_type: str = "full"
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedForensicSystem:
    """
    Master forensic analysis orchestration system
    """
    
    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        enable_timestamps: bool = True
    ):
        """
        Initialize enhanced forensic system
        
        Args:
            storage_dir: Directory for storing case data
            enable_timestamps: Enable RFC3161 timestamping
        """
        self.storage_dir = storage_dir or Path("./forensic_storage")
        self.storage_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize analyzers
        self.entity_extractor = FinancialEntityExtractor()
        self.benfords_analyzer = BenfordsLawAnalyzer()
        
        # Initialize timestamper if enabled
        self.timestamper = RFC3161Timestamper() if enable_timestamps else None
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Enhanced Forensic System initialized")
    
    async def create_case(
        self,
        target: str,
        case_type: str = "sec_filing",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ForensicCase:
        """
        Create new forensic investigation case
        
        Args:
            target: Target entity (company, individual, etc.)
            case_type: Type of investigation
            metadata: Additional case metadata
            
        Returns:
            ForensicCase instance
        """
        case_id = self._generate_case_id(target)
        
        case = ForensicCase(
            case_id=case_id,
            target=target,
            case_type=case_type,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Create case directory
        case_dir = self.storage_dir / case_id
        case_dir.mkdir(exist_ok=True, parents=True)
        
        # Save initial case
        self._save_case(case)
        
        self.logger.info(f"Created case {case_id} for {target}")
        return case
    
    async def analyze_document(
        self,
        case: ForensicCase,
        document_path: str,
        document_type: str = "unknown"
    ) -> ForensicCase:
        """
        Analyze document and add to case
        
        Args:
            case: Forensic case
            document_path: Path to document
            document_type: Type of document
            
        Returns:
            Updated case
        """
        self.logger.info(f"Analyzing document: {document_path}")
        
        # Read document
        with open(document_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Timestamp document if enabled
        if self.timestamper:
            timestamp = self.timestamper.timestamp_data(content.encode('utf-8'))
            case.timestamps.append(timestamp)
        
        # Extract entities
        extraction = self.entity_extractor.extract(content)
        case.entities = extraction
        
        # Analyze financial data with Benford's Law
        if 'money' in extraction.entities_by_type:
            amounts = [
                e.value for e in extraction.entities_by_type['money']
                if e.value
            ]
            if amounts:
                benfords = self.benfords_analyzer.analyze(
                    amounts,
                    dataset_name=f"{case.target} - {document_type}"
                )
                case.benfords_analysis = benfords
                
                # Add finding if suspicious
                if benfords.is_suspicious:
                    case.findings.append(
                        f"Benford's Law analysis indicates potential anomalies "
                        f"(confidence: {benfords.confidence_level*100:.1f}%)"
                    )
        
        # Add document to case
        case.documents.append({
            'path': document_path,
            'type': document_type,
            'analyzed_at': datetime.utcnow().isoformat(),
            'entity_count': len(extraction.entities)
        })
        
        # Update risk score
        case.risk_score = self._calculate_risk_score(case)
        
        # Save case
        self._save_case(case)
        
        return case
    
    async def detect_contradictions(
        self,
        case: ForensicCase
    ) -> ForensicCase:
        """
        Detect contradictions in case data
        
        Args:
            case: Forensic case
            
        Returns:
            Updated case with contradictions
        """
        self.logger.info(f"Detecting contradictions in case {case.case_id}")
        
        # Placeholder for contradiction detection
        # In production, this would use the contradiction engine
        
        contradictions = []
        
        # Check for numerical contradictions
        if case.entities and 'money' in case.entities.entities_by_type:
            amounts = case.entities.entities_by_type['money']
            # Look for duplicate amounts with different contexts
            seen = {}
            for entity in amounts:
                key = entity.value
                if key in seen:
                    if seen[key].context != entity.context:
                        contradictions.append({
                            'type': 'numerical',
                            'severity': 'medium',
                            'description': f"Same amount ${entity.value:,.2f} in different contexts",
                            'entities': [seen[key], entity]
                        })
                else:
                    seen[key] = entity
        
        case.contradictions = contradictions
        
        if contradictions:
            case.findings.append(
                f"Found {len(contradictions)} potential contradictions"
            )
        
        # Update risk score
        case.risk_score = self._calculate_risk_score(case)
        
        # Save case
        self._save_case(case)
        
        return case
    
    async def generate_report(
        self,
        case: ForensicCase,
        report_type: str = "full"
    ) -> ForensicReport:
        """
        Generate comprehensive forensic report
        
        Args:
            case: Forensic case
            report_type: Type of report (full, summary, executive)
            
        Returns:
            ForensicReport
        """
        self.logger.info(f"Generating {report_type} report for case {case.case_id}")
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(case)
        
        # Compile detailed findings
        detailed_findings = self._compile_detailed_findings(case)
        
        # Generate evidence summary
        evidence_summary = {
            'document_count': len(case.documents),
            'entity_count': len(case.entities.entities) if case.entities else 0,
            'timestamp_count': len(case.timestamps),
            'contradiction_count': len(case.contradictions),
            'violation_count': len(case.legal_violations)
        }
        
        # Generate legal analysis
        legal_analysis = {
            'violations': case.legal_violations,
            'prosecutability': case.prosecutability_score,
            'burden_of_proof': 'Preponderance of Evidence' if case.prosecutability_score > 0.7 else 'Beyond Reasonable Doubt'
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(case)
        
        report = ForensicReport(
            case=case,
            executive_summary=executive_summary,
            detailed_findings=detailed_findings,
            evidence_summary=evidence_summary,
            legal_analysis=legal_analysis,
            recommendations=recommendations,
            generated_at=datetime.utcnow(),
            report_type=report_type
        )
        
        # Save report
        self._save_report(report)
        
        return report
    
    def _generate_case_id(self, target: str) -> str:
        """Generate unique case ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        target_clean = "".join(c for c in target if c.isalnum())[:20]
        return f"CASE_{target_clean}_{timestamp}"
    
    def _calculate_risk_score(self, case: ForensicCase) -> float:
        """Calculate overall risk score for case"""
        score = 0.0
        
        # Benford's Law analysis
        if case.benfords_analysis and case.benfords_analysis.is_suspicious:
            score += 0.3 * case.benfords_analysis.confidence_level
        
        # Contradictions
        if case.contradictions:
            score += 0.2 * min(len(case.contradictions) / 5.0, 1.0)
        
        # Legal violations
        if case.legal_violations:
            score += 0.3 * min(len(case.legal_violations) / 3.0, 1.0)
        
        # Evidence chain integrity
        if case.timestamps:
            score += 0.2  # Bonus for timestamped evidence
        
        return min(score, 1.0)
    
    def _generate_executive_summary(self, case: ForensicCase) -> str:
        """Generate executive summary"""
        lines = []
        lines.append(f"FORENSIC ANALYSIS SUMMARY")
        lines.append(f"Target: {case.target}")
        lines.append(f"Case ID: {case.case_id}")
        lines.append(f"Risk Score: {case.risk_score*100:.1f}%")
        lines.append(f"\nDocuments Analyzed: {len(case.documents)}")
        
        if case.entities:
            lines.append(f"Entities Extracted: {len(case.entities.entities)}")
        
        if case.benfords_analysis:
            status = "SUSPICIOUS" if case.benfords_analysis.is_suspicious else "NORMAL"
            lines.append(f"Benford's Law: {status}")
        
        lines.append(f"Contradictions: {len(case.contradictions)}")
        lines.append(f"Violations: {len(case.legal_violations)}")
        
        lines.append(f"\nKey Findings:")
        for finding in case.findings[:5]:
            lines.append(f"  • {finding}")
        
        return "\n".join(lines)
    
    def _compile_detailed_findings(self, case: ForensicCase) -> List[Dict[str, Any]]:
        """Compile detailed findings"""
        findings = []
        
        # Benford's analysis findings
        if case.benfords_analysis and case.benfords_analysis.is_suspicious:
            findings.append({
                'category': 'statistical',
                'type': 'benfords_law',
                'severity': 'high' if case.benfords_analysis.confidence_level > 0.8 else 'medium',
                'description': f"Financial data deviates from Benford's Law distribution",
                'confidence': case.benfords_analysis.confidence_level,
                'details': {
                    'chi_square_p': case.benfords_analysis.chi_square_p_value,
                    'mad': case.benfords_analysis.mean_absolute_deviation,
                    'suspicious_digits': case.benfords_analysis.suspicious_digits
                }
            })
        
        # Contradiction findings
        for contradiction in case.contradictions:
            findings.append({
                'category': 'contradiction',
                'type': contradiction['type'],
                'severity': contradiction['severity'],
                'description': contradiction['description'],
                'confidence': 0.8
            })
        
        return findings
    
    def _generate_recommendations(self, case: ForensicCase) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if case.risk_score > 0.7:
            recommendations.append("Recommend immediate deep-dive investigation")
            recommendations.append("Engage external auditors for verification")
        elif case.risk_score > 0.4:
            recommendations.append("Monitor situation and conduct follow-up analysis")
        else:
            recommendations.append("Continue routine monitoring")
        
        if case.benfords_analysis and case.benfords_analysis.is_suspicious:
            recommendations.append("Request detailed financial records for specific accounts")
        
        if len(case.contradictions) > 3:
            recommendations.append("Conduct interviews with key personnel regarding contradictions")
        
        return recommendations
    
    def _save_case(self, case: ForensicCase):
        """Save case to storage"""
        case_dir = self.storage_dir / case.case_id
        case_file = case_dir / "case.json"
        
        # Convert case to dict (simplified)
        case_data = {
            'case_id': case.case_id,
            'target': case.target,
            'case_type': case.case_type,
            'created_at': case.created_at.isoformat(),
            'documents': case.documents,
            'findings': case.findings,
            'risk_score': case.risk_score,
            'metadata': case.metadata
        }
        
        with open(case_file, 'w') as f:
            json.dump(case_data, f, indent=2)
    
    def _save_report(self, report: ForensicReport):
        """Save report to storage"""
        case_dir = self.storage_dir / report.case.case_id
        report_file = case_dir / f"report_{report.report_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w') as f:
            f.write(report.executive_summary)
            f.write("\n\n" + "="*80 + "\n\n")
            f.write("DETAILED FINDINGS\n\n")
            for finding in report.detailed_findings:
                f.write(f"• {finding.get('description', 'N/A')}\n")
            f.write("\n\nRECOMMENDATIONS\n\n")
            for rec in report.recommendations:
                f.write(f"• {rec}\n")

