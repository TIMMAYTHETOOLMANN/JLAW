"""
NODE 12: Earnings Call Transcript Analyzer v2.0 (FORTIFIED)
============================================================

Enhanced version with:
- DeBERTa-v3-large transformer for semantic contradiction detection
- Seeking Alpha / Refinitiv API integration for live transcripts
- Contextual hedging analysis with speaker attribution
- Automated 10-K/10-Q narrative comparison
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

from .deberta_detector import DeBERTaContradictionDetector, ContradictionResult
from .transcript_source_client import TranscriptSourceClient, TranscriptData
from .contextual_hedging_analyzer import ContextualHedgingAnalyzer, HedgingAnalysis
from .filing_narrative_comparator import FilingNarrativeComparator, NarrativeComparison

logger = logging.getLogger(__name__)


class AlertType(Enum):
    CONTRADICTION_DETECTED = "Contradiction Detected"
    HIGH_HEDGING = "High Hedging Language"
    NARRATIVE_DISCREPANCY = "Narrative Discrepancy"
    SENTIMENT_SHIFT = "Sentiment Shift"


class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class TranscriptAlertV2:
    alert_type: AlertType
    severity: Severity
    description: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Node12OutputV2:
    transcripts_analyzed: int
    contradictions_detected: int
    high_hedging_count: int
    narrative_discrepancies: int
    alerts: List[TranscriptAlertV2]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "transcripts_analyzed": self.transcripts_analyzed,
                "contradictions_detected": self.contradictions_detected,
                "high_hedging_count": self.high_hedging_count,
                "narrative_discrepancies": self.narrative_discrepancies
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class TranscriptAnalyzerV2:
    def __init__(
        self,
        deberta_model: str = "microsoft/deberta-v3-large",
        seeking_alpha_key: Optional[str] = None,
        refinitiv_key: Optional[str] = None
    ):
        self.contradiction_detector = DeBERTaContradictionDetector(deberta_model)
        self.transcript_client = TranscriptSourceClient(seeking_alpha_key, refinitiv_key)
        self.hedging_analyzer = ContextualHedgingAnalyzer()
        self.narrative_comparator = FilingNarrativeComparator()
        self.logger = logger
    
    def analyze(
        self,
        transcripts: List[TranscriptData],
        filings: Optional[List[Dict[str, Any]]] = None
    ) -> Node12OutputV2:
        alerts = []
        
        # Analyze each transcript
        for transcript in transcripts:
            # Detect contradictions
            contradictions = self.contradiction_detector.detect_contradictions_in_transcript(
                transcript.statements
            )
            for contradiction in contradictions:
                if contradiction.is_contradiction:
                    alerts.append(TranscriptAlertV2(
                        alert_type=AlertType.CONTRADICTION_DETECTED,
                        severity=Severity.HIGH,
                        description=f"Contradiction detected in {transcript.company_ticker} transcript",
                        details=contradiction.to_dict()
                    ))
            
            # Analyze hedging
            hedging_analyses = self.hedging_analyzer.analyze_transcript(transcript.statements)
            high_hedging = [h for h in hedging_analyses if h.hedging_score > 0.7]
            for hedging in high_hedging:
                alerts.append(TranscriptAlertV2(
                    alert_type=AlertType.HIGH_HEDGING,
                    severity=Severity.MEDIUM,
                    description=f"High hedging language from {hedging.speaker}",
                    details=hedging.to_dict()
                ))
            
            # Compare with filings if provided
            if filings:
                filing_text = next((f.get('text', '') for f in filings 
                                   if f.get('company_cik') == transcript.company_cik), '')
                if filing_text:
                    comparisons = self.narrative_comparator.compare(
                        transcript.transcript_text,
                        filing_text
                    )
                    for comp in comparisons:
                        if comp.discrepancy_detected:
                            alerts.append(TranscriptAlertV2(
                                alert_type=AlertType.NARRATIVE_DISCREPANCY,
                                severity=Severity.HIGH,
                                description=f"Narrative discrepancy on {comp.topic}",
                                details=comp.to_dict()
                            ))
        
        return Node12OutputV2(
            transcripts_analyzed=len(transcripts),
            contradictions_detected=len([a for a in alerts if a.alert_type == AlertType.CONTRADICTION_DETECTED]),
            high_hedging_count=len([a for a in alerts if a.alert_type == AlertType.HIGH_HEDGING]),
            narrative_discrepancies=len([a for a in alerts if a.alert_type == AlertType.NARRATIVE_DISCREPANCY]),
            alerts=alerts
        )
