"""
Unified Forensic Orchestrator - Phase 5 Integration
Harmoniously integrates all phases into a single forensic operating system.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import logging

# Phase 1: Document Parsing
from src.forensics.enhanced_parsing import UniversalDocumentExtractor

# Phase 2: Intelligence Gathering
from src.intelligence_gathering import OmniscientIntelligenceGatherer

# Phase 3: Statute Mapping
from src.forensics import StatuteMapper

# Phase 4: Temporal Analysis
from src.forensics.temporal_analysis import ForensicTimelineReconstructor

# Phase 5: Decision Engine
from src.forensics.decision_engine import (
    ProsecutionPathBuilder,
    ForensicEvidenceEvaluator,
    Evidence,
    EvidenceType
)

logger = logging.getLogger(__name__)


@dataclass
class ComprehensiveForensicAnalysis:
    """Complete forensic analysis result from all phases."""
    # Phase 1: Parsed documents
    parsed_documents: List[Any]
    
    # Phase 2: Intelligence
    intelligence_data: Dict[str, Any]
    
    # Phase 3: Statute violations
    statute_violations: List[Any]
    
    # Phase 4: Timeline
    timeline_analysis: Any
    
    # Phase 5: Prosecution path
    prosecution_path: Any
    
    # Metadata
    analysis_timestamp: datetime
    target_entity: str
    case_id: str
    
    # Summary
    executive_summary: str
    key_findings: List[str]
    recommendations: List[str]
    risk_assessment: str


class UnifiedForensicOrchestrator:
    """
    Unified Forensic Orchestrator
    
    Harmoniously integrates all 5 phases:
    1. Enhanced Document Parsing
    2. Omniscient Intelligence Gathering
    3. Statute Integration & Mapping
    4. Temporal Analysis & Timeline Reconstruction
    5. Decision Engine & Prosecution Path Building
    
    Operates as a single, cohesive forensic operating system.
    """
    
    def __init__(self):
        """Initialize unified orchestrator."""
        # Phase 1: Document Parser
        self.document_extractor = UniversalDocumentExtractor()
        
        # Phase 2: Intelligence Gatherer
        self.intelligence_gatherer = OmniscientIntelligenceGatherer()
        
        # Phase 3: Statute Mapper
        self.statute_mapper = StatuteMapper()
        
        # Phase 4: Timeline Reconstructor
        self.timeline_reconstructor = ForensicTimelineReconstructor()
        
        # Phase 5: Prosecution Path Builder
        self.path_builder = ProsecutionPathBuilder()
        self.evidence_evaluator = ForensicEvidenceEvaluator()
        
        logger.info("=" * 80)
        logger.info("UNIFIED FORENSIC ORCHESTRATOR INITIALIZED")
        logger.info("=" * 80)
        logger.info("Phase 1: Enhanced Document Parsing ........... READY")
        logger.info("Phase 2: Intelligence Gathering .............. READY")
        logger.info("Phase 3: Statute Integration ................. READY")
        logger.info("Phase 4: Temporal Analysis ................... READY")
        logger.info("Phase 5: Decision Engine ..................... READY")
        logger.info("=" * 80)
    
    async def comprehensive_investigation(
        self,
        target_entity: str,
        document_sources: List[str],
        case_id: Optional[str] = None,
        objectives: Optional[List[str]] = None
    ) -> ComprehensiveForensicAnalysis:
        """
        Conduct comprehensive forensic investigation.
        
        Executes all 5 phases in harmony to produce complete analysis.
        
        Args:
            target_entity: Entity under investigation
            document_sources: List of document paths/URLs
            case_id: Optional case identifier
            objectives: Prosecution objectives
        
        Returns:
            Complete forensic analysis
        """
        case_id = case_id or f"CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        objectives = objectives or ['ensure_conviction', 'maximize_penalties']
        
        logger.info("")
        logger.info("="*80)
        logger.info(f"COMPREHENSIVE FORENSIC INVESTIGATION: {target_entity}")
        logger.info(f"Case ID: {case_id}")
        logger.info("="*80)
        
        # ===================================================================
        # PHASE 1: ENHANCED DOCUMENT PARSING
        # ===================================================================
        logger.info("")
        logger.info("[PHASE 1] ENHANCED DOCUMENT PARSING")
        logger.info("-" * 80)
        
        parsed_documents = []
        for doc_source in document_sources:
            try:
                logger.info(f"  Parsing: {doc_source}")
                extracted = await self.document_extractor.extract(doc_source)
                parsed_documents.append(extracted)
                logger.info(f"  ✓ Extracted {len(extracted.get('tables', []))} tables, "
                          f"{len(extracted.get('financial_metrics', {}))} financial metrics")
            except Exception as e:
                logger.error(f"  ✗ Failed to parse {doc_source}: {e}")
        
        logger.info(f"✓ Phase 1 Complete: {len(parsed_documents)} documents parsed")
        
        # ===================================================================
        # PHASE 2: OMNISCIENT INTELLIGENCE GATHERING
        # ===================================================================
        logger.info("")
        logger.info("[PHASE 2] OMNISCIENT INTELLIGENCE GATHERING")
        logger.info("-" * 80)
        
        intelligence_data = await self.intelligence_gatherer.gather_comprehensive(
            target_entity,
            include_social_media=True,
            include_news=True,
            include_filings=True
        )
        
        logger.info(f"  ✓ Gathered intelligence from {len(intelligence_data.get('sources', []))} sources")
        logger.info(f"  ✓ Found {len(intelligence_data.get('entities', []))} related entities")
        logger.info(f"  ✓ Identified {len(intelligence_data.get('risk_factors', []))} risk factors")
        logger.info(f"✓ Phase 2 Complete")
        
        # ===================================================================
        # PHASE 3: STATUTE INTEGRATION & MAPPING
        # ===================================================================
        logger.info("")
        logger.info("[PHASE 3] STATUTE INTEGRATION & MAPPING")
        logger.info("-" * 80)
        
        # Extract indicators from documents and intelligence
        indicators = self._extract_forensic_indicators(
            parsed_documents, intelligence_data
        )
        
        statute_violations = await self.statute_mapper.map_indicators_to_statutes(
            indicators
        )
        
        logger.info(f"  ✓ Identified {len(statute_violations)} potential statute violations")
        for violation in statute_violations[:5]:  # Show top 5
            logger.info(f"    - {violation.get('statute')}: {violation.get('severity')}")
        logger.info(f"✓ Phase 3 Complete")
        
        # ===================================================================
        # PHASE 4: TEMPORAL ANALYSIS & TIMELINE RECONSTRUCTION
        # ===================================================================
        logger.info("")
        logger.info("[PHASE 4] TEMPORAL ANALYSIS & TIMELINE RECONSTRUCTION")
        logger.info("-" * 80)
        
        timeline_analysis = await self.timeline_reconstructor.reconstruct_timeline(
            parsed_documents,
            options={
                'resolution': 'day',
                'detect_anomalies': True,
                'correlate_events': True
            }
        )
        
        logger.info(f"  ✓ Reconstructed timeline with {timeline_analysis.total_events} events")
        logger.info(f"  ✓ Detected {len(timeline_analysis.contradictions)} contradictions")
        logger.info(f"  ✓ Found {len(timeline_analysis.anomalies)} temporal anomalies")
        logger.info(f"  ✓ Timeline integrity score: {timeline_analysis.timeline_integrity_score:.2%}")
        logger.info(f"✓ Phase 4 Complete")
        
        # ===================================================================
        # PHASE 5: DECISION ENGINE & PROSECUTION PATH BUILDING
        # ===================================================================
        logger.info("")
        logger.info("[PHASE 5] DECISION ENGINE & PROSECUTION PATH BUILDING")
        logger.info("-" * 80)
        
        # Convert forensic findings to evidence
        evidence = self._convert_to_evidence(
            parsed_documents,
            intelligence_data,
            statute_violations,
            timeline_analysis
        )
        
        logger.info(f"  ✓ Compiled {len(evidence)} pieces of evidence")
        
        # Build prosecution path
        from src.forensics.decision_engine import ProsecutionObjective
        prosecution_objectives = [
            ProsecutionObjective.ENSURE_CONVICTION,
            ProsecutionObjective.MAXIMIZE_PENALTIES
        ]
        
        case_context = {
            'timeline_analysis': timeline_analysis,
            'contradictions': timeline_analysis.contradictions,
            'statute_violations': statute_violations,
            'intelligence_sources': intelligence_data.get('sources', [])
        }
        
        prosecution_path = await self.path_builder.build_prosecution_path(
            evidence,
            target_entity,
            prosecution_objectives,
            case_context
        )
        
        logger.info(f"  ✓ Optimal prosecution path: {prosecution_path.path.expected_outcome.value}")
        logger.info(f"  ✓ Success probability: {prosecution_path.success_probability:.2%}")
        logger.info(f"  ✓ Primary action: {prosecution_path.strategy.primary_action.value}")
        logger.info(f"✓ Phase 5 Complete")
        
        # ===================================================================
        # GENERATE COMPREHENSIVE ANALYSIS
        # ===================================================================
        logger.info("")
        logger.info("[SYNTHESIS] GENERATING COMPREHENSIVE ANALYSIS")
        logger.info("-" * 80)
        
        executive_summary = self._generate_executive_summary(
            target_entity,
            parsed_documents,
            intelligence_data,
            statute_violations,
            timeline_analysis,
            prosecution_path
        )
        
        key_findings = self._extract_key_findings(
            statute_violations,
            timeline_analysis,
            prosecution_path
        )
        
        recommendations = prosecution_path.next_steps
        
        risk_assessment = self._assess_overall_risk(
            statute_violations,
            timeline_analysis,
            prosecution_path
        )
        
        analysis = ComprehensiveForensicAnalysis(
            parsed_documents=parsed_documents,
            intelligence_data=intelligence_data,
            statute_violations=statute_violations,
            timeline_analysis=timeline_analysis,
            prosecution_path=prosecution_path,
            analysis_timestamp=datetime.now(),
            target_entity=target_entity,
            case_id=case_id,
            executive_summary=executive_summary,
            key_findings=key_findings,
            recommendations=recommendations,
            risk_assessment=risk_assessment
        )
        
        logger.info("")
        logger.info("="*80)
        logger.info("COMPREHENSIVE FORENSIC INVESTIGATION COMPLETE")
        logger.info("="*80)
        logger.info(f"✓ Documents Analyzed: {len(parsed_documents)}")
        logger.info(f"✓ Intelligence Sources: {len(intelligence_data.get('sources', []))}")
        logger.info(f"✓ Statute Violations: {len(statute_violations)}")
        logger.info(f"✓ Timeline Events: {timeline_analysis.total_events}")
        logger.info(f"✓ Evidence Pieces: {len(evidence)}")
        logger.info(f"✓ Success Probability: {prosecution_path.success_probability:.2%}")
        logger.info(f"✓ Recommended Action: {prosecution_path.recommended_action}")
        logger.info("="*80)
        
        return analysis
    
    def _extract_forensic_indicators(
        self,
        documents: List[Any],
        intelligence: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract forensic indicators from documents and intelligence."""
        indicators = []
        
        # From documents
        for doc in documents:
            if 'financial_metrics' in doc:
                for metric, value in doc['financial_metrics'].items():
                    if 'revenue' in metric.lower() and value < 0:
                        indicators.append({
                            'type': 'accounting_fraud',
                            'description': f'Negative revenue reported: {value}',
                            'severity': 'high'
                        })
        
        # From intelligence
        risk_factors = intelligence.get('risk_factors', [])
        for risk in risk_factors:
            indicators.append({
                'type': 'disclosure_violation',
                'description': risk,
                'severity': 'medium'
            })
        
        return indicators
    
    def _convert_to_evidence(
        self,
        documents: List[Any],
        intelligence: Dict[str, Any],
        violations: List[Any],
        timeline: Any
    ) -> List[Evidence]:
        """Convert forensic findings to evidence."""
        evidence = []
        
        # Document evidence
        for i, doc in enumerate(documents):
            evidence.append(Evidence(
                id=f"DOC_{i}",
                evidence_type=EvidenceType.DOCUMENT,
                description=f"Parsed document: {doc.get('source', 'unknown')}",
                source=doc.get('source', 'unknown'),
                date_obtained=datetime.now(),
                content=doc,
                metadata={'parsed': True}
            ))
        
        # Timeline evidence
        if timeline:
            evidence.append(Evidence(
                id="TIMELINE_001",
                evidence_type=EvidenceType.TIMELINE,
                description=f"Timeline analysis with {timeline.total_events} events",
                source="Temporal Analysis Module",
                date_obtained=datetime.now(),
                content=timeline,
                metadata={'integrity_score': timeline.timeline_integrity_score}
            ))
        
        # Violation evidence
        for i, violation in enumerate(violations):
            evidence.append(Evidence(
                id=f"VIOLATION_{i}",
                evidence_type=EvidenceType.FORENSIC_ANALYSIS,
                description=f"Statute violation: {violation.get('statute')}",
                source="Statute Mapper",
                date_obtained=datetime.now(),
                content=violation,
                metadata={'severity': violation.get('severity')}
            ))
        
        return evidence
    
    def _generate_executive_summary(
        self,
        target: str,
        documents: List[Any],
        intelligence: Dict[str, Any],
        violations: List[Any],
        timeline: Any,
        path: Any
    ) -> str:
        """Generate executive summary."""
        summary = f"""
EXECUTIVE SUMMARY
Target Entity: {target}
Analysis Date: {datetime.now().strftime('%Y-%m-%d')}

OVERVIEW:
Comprehensive forensic investigation conducted across 5 analytical phases,
processing {len(documents)} documents and {len(intelligence.get('sources', []))} intelligence sources.

KEY FINDINGS:
- {len(violations)} potential statute violations identified
- {timeline.total_events if timeline else 0} timeline events reconstructed
- {len(timeline.contradictions) if timeline else 0} temporal contradictions detected
- {len(timeline.anomalies) if timeline else 0} temporal anomalies found

PROSECUTION ASSESSMENT:
- Recommended Path: {path.path.expected_outcome.value}
- Success Probability: {path.success_probability:.1%}
- Primary Action: {path.strategy.primary_action.value}

RISK LEVEL: {len(violations) * 10}% (Based on violation count)
        """.strip()
        
        return summary
    
    def _extract_key_findings(
        self,
        violations: List[Any],
        timeline: Any,
        path: Any
    ) -> List[str]:
        """Extract key findings."""
        findings = []
        
        # Violation findings
        for violation in violations[:5]:
            findings.append(f"Potential violation: {violation.get('statute')}")
        
        # Timeline findings
        if timeline and timeline.contradictions:
            findings.append(f"Detected {len(timeline.contradictions)} temporal contradictions")
        
        if timeline and timeline.anomalies:
            findings.append(f"Found {len(timeline.anomalies)} temporal anomalies")
        
        # Evidence findings
        admissible = sum(1 for e in path.evidence if e.admissibility.is_admissible)
        findings.append(f"{admissible}/{len(path.evidence)} evidence pieces admissible")
        
        return findings
    
    def _assess_overall_risk(
        self,
        violations: List[Any],
        timeline: Any,
        path: Any
    ) -> str:
        """Assess overall prosecution risk."""
        risk_score = 0
        
        # Violations increase risk for defendant
        risk_score += len(violations) * 10
        
        # Contradictions increase risk
        if timeline:
            risk_score += len(timeline.contradictions) * 5
        
        # Low success probability increases risk for prosecution
        if path.success_probability < 0.5:
            risk_score -= 20
        
        if risk_score > 70:
            return "HIGH RISK - Strong case for prosecution"
        elif risk_score > 40:
            return "MEDIUM RISK - Moderate prosecution viability"
        else:
            return "LOW RISK - Weak case, additional evidence needed"

