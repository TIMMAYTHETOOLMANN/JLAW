"""
NODE 12: Earnings Call Transcript Analyzer
==========================================

NLP analysis of earnings call transcripts to detect:
- Management hedging language and uncertainty indicators
- Sentiment shifts between quarters
- Contradictions with 10-K/10-Q narratives
- Question avoidance patterns
- Forward-looking statement reliability tracking
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import hashlib
import logging
import re

logger = logging.getLogger(__name__)


class TranscriptAlertType(Enum):
    SENTIMENT_SHIFT = "Sentiment Shift"
    EXCESSIVE_HEDGING = "Excessive Hedging"
    CONTRADICTION_DETECTED = "Contradiction Detected"
    QUESTION_AVOIDANCE = "Question Avoidance"
    GUIDANCE_INCONSISTENCY = "Guidance Inconsistency"


class SpeakerRole(Enum):
    CEO = "CEO"
    CFO = "CFO"
    COO = "COO"
    IR = "Investor Relations"
    ANALYST = "Analyst"
    OTHER = "Other"


# NLP Pattern Libraries
HEDGING_PHRASES = [
    'we believe', 'we think', 'we expect', 'we anticipate',
    'potentially', 'possibly', 'might', 'may', 'could',
    'uncertain', 'uncertainty', 'challenging environment',
    'headwinds', 'subject to', 'dependent on',
    'not at this time', 'looking into', 'still evaluating',
    'too early to tell', 'cannot comment', 'going forward',
    'normalized basis', 'adjusted', 'non-gaap', 'pro forma',
    'approximately', 'roughly', 'in the range of'
]

AVOIDANCE_PATTERNS = [
    "i can't comment on",
    "we don't disclose",
    "that's not something we",
    "i'll have to get back to you",
    "let me redirect",
    "i think the better question",
    "what i can tell you is",
    "without getting into specifics",
    "we're not going to get into",
    "that's proprietary"
]

NEGATIVE_INDICATORS = [
    'miss', 'missed', 'decline', 'declined', 'decrease', 'decreased',
    'disappointing', 'shortfall', 'weakness', 'weak', 'soft', 'softer',
    'challenging', 'difficult', 'pressure', 'headwind', 'deteriorating',
    'revised down', 'lowered guidance', 'below expectations',
    'downturn', 'slowdown', 'contraction', 'loss', 'deficit'
]

POSITIVE_INDICATORS = [
    'beat', 'exceeded', 'growth', 'growing', 'increase', 'increased',
    'strong', 'robust', 'accelerating', 'momentum', 'record',
    'outperformed', 'raised guidance', 'above expectations',
    'improvement', 'recovery', 'expansion', 'profit', 'gain'
]

FORWARD_LOOKING_PATTERNS = [
    'we expect', 'we anticipate', 'we project', 'guidance',
    'forecast', 'outlook', 'next quarter', 'next year', 'going forward',
    'full year', 'fiscal year', 'targets', 'goals', 'plan to'
]


@dataclass
class TranscriptSegment:
    """Single segment of transcript (one speaker turn)."""
    speaker: str
    role: SpeakerRole
    text: str
    timestamp: Optional[str] = None
    is_response: bool = False
    question_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "speaker": self.speaker,
            "role": self.role.value,
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "is_response": self.is_response
        }


@dataclass
class FlaggedStatement:
    """Statement flagged for review."""
    text: str
    issue: str  # HEDGING, CONTRADICTION, AVOIDANCE, UNUSUAL_LANGUAGE
    confidence: float
    context: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "issue": self.issue,
            "confidence": round(self.confidence, 3),
            "context": self.context
        }


@dataclass
class DocumentContradiction:
    """Contradiction between transcript and filed document."""
    transcript_statement: str
    filed_statement: str
    filing_type: str
    contradiction_type: str  # NUMERICAL, QUALITATIVE, TEMPORAL
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transcript": self.transcript_statement[:150],
            "filed": self.filed_statement[:150],
            "filing_type": self.filing_type,
            "type": self.contradiction_type,
            "confidence": round(self.confidence, 3)
        }


@dataclass
class TranscriptAnalysis:
    """Complete analysis of a single earnings call."""
    company_id: str
    call_date: date
    fiscal_period: str
    segment_count: int
    
    # NLP Metrics
    sentiment_score: float  # -1 to +1
    uncertainty_score: float  # 0 to 1
    hedging_phrase_count: int
    forward_looking_count: int
    question_avoidance_score: float
    
    # Detected Issues
    flagged_statements: List[FlaggedStatement]
    document_contradictions: List[DocumentContradiction]
    
    evidence_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_id": self.company_id,
            "call_date": self.call_date.isoformat(),
            "fiscal_period": self.fiscal_period,
            "metrics": {
                "sentiment_score": round(self.sentiment_score, 3),
                "uncertainty_score": round(self.uncertainty_score, 3),
                "hedging_phrase_count": self.hedging_phrase_count,
                "forward_looking_count": self.forward_looking_count,
                "question_avoidance_score": round(self.question_avoidance_score, 3)
            },
            "flagged_statements": [f.to_dict() for f in self.flagged_statements[:10]],
            "contradictions": [c.to_dict() for c in self.document_contradictions]
        }


@dataclass
class TranscriptAlert:
    """Alert from transcript analysis."""
    alert_type: TranscriptAlertType
    call_date: date
    company_id: str
    severity: str
    details: List[str]
    flagged_statements: List[str]
    evidence_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "call_date": self.call_date.isoformat(),
            "company_id": self.company_id,
            "severity": self.severity,
            "details": self.details,
            "flagged_count": len(self.flagged_statements)
        }


@dataclass
class Node12Output:
    """Output from Node 12 analysis."""
    transcripts_analyzed: int
    alerts: List[TranscriptAlert]
    sentiment_shifts: int
    excessive_hedging_count: int
    contradictions_found: int
    question_avoidance_count: int
    average_sentiment: float
    average_uncertainty: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "transcripts_analyzed": self.transcripts_analyzed,
                "sentiment_shifts": self.sentiment_shifts,
                "excessive_hedging": self.excessive_hedging_count,
                "contradictions_found": self.contradictions_found,
                "question_avoidance": self.question_avoidance_count,
                "average_sentiment": round(self.average_sentiment, 3),
                "average_uncertainty": round(self.average_uncertainty, 3)
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class EarningsCallAnalyzer:
    """
    Earnings Call Transcript Analyzer.
    
    Applies NLP analysis to detect:
    1. Management hedging and uncertainty language
    2. Sentiment shifts between quarters
    3. Contradictions with SEC filings
    4. Question avoidance patterns
    5. Forward-looking statement tracking
    """
    
    # Thresholds
    EXCESSIVE_HEDGING_THRESHOLD = 15  # phrases
    UNCERTAINTY_THRESHOLD = 0.5
    SENTIMENT_SHIFT_THRESHOLD = 0.3
    
    def __init__(self):
        self._analyses: Dict[str, List[TranscriptAnalysis]] = {}  # company_id -> analyses
    
    def analyze_transcript(
        self,
        segments: List[TranscriptSegment],
        company_id: str,
        call_date: date,
        fiscal_period: str
    ) -> TranscriptAnalysis:
        """
        Analyze a single earnings call transcript.
        
        Args:
            segments: List of transcript segments
            company_id: Company CIK or identifier
            call_date: Date of earnings call
            fiscal_period: Fiscal period (e.g., "Q3 2024")
            
        Returns:
            TranscriptAnalysis with all metrics
        """
        logger.info(f"[NODE 12] Analyzing transcript: {company_id} - {fiscal_period}")
        
        # Combine all text
        full_text = ' '.join(s.text for s in segments).lower()
        word_count = len(full_text.split())
        
        # Calculate sentiment
        positive_count = sum(1 for p in POSITIVE_INDICATORS if p in full_text)
        negative_count = sum(1 for n in NEGATIVE_INDICATORS if n in full_text)
        total_sentiment = positive_count + negative_count
        sentiment_score = (positive_count - negative_count) / max(total_sentiment, 1)
        
        # Calculate hedging/uncertainty
        hedging_count = sum(1 for h in HEDGING_PHRASES if h in full_text)
        uncertainty_score = min(hedging_count / 20, 1.0)
        
        # Calculate question avoidance
        avoidance_count = sum(1 for a in AVOIDANCE_PATTERNS if a in full_text)
        question_count = len([s for s in segments if not s.is_response])
        avoidance_score = avoidance_count / max(question_count, 1)
        
        # Count forward-looking statements
        forward_count = sum(1 for f in FORWARD_LOOKING_PATTERNS if f in full_text)
        
        # Flag specific statements
        flagged = self._flag_statements(segments)
        
        analysis = TranscriptAnalysis(
            company_id=company_id,
            call_date=call_date,
            fiscal_period=fiscal_period,
            segment_count=len(segments),
            sentiment_score=sentiment_score,
            uncertainty_score=uncertainty_score,
            hedging_phrase_count=hedging_count,
            forward_looking_count=forward_count,
            question_avoidance_score=avoidance_score,
            flagged_statements=flagged,
            document_contradictions=[],
            evidence_hash=self._generate_hash({'company': company_id, 'date': str(call_date)})
        )
        
        # Store for trend analysis
        if company_id not in self._analyses:
            self._analyses[company_id] = []
        self._analyses[company_id].append(analysis)
        
        return analysis
    
    def analyze_batch(
        self,
        transcripts: List[Dict[str, Any]]
    ) -> Node12Output:
        """
        Analyze multiple transcripts and generate alerts.
        
        Args:
            transcripts: List of transcript data with segments
            
        Returns:
            Node12Output with all analysis results
        """
        logger.info(f"[NODE 12] Analyzing {len(transcripts)} transcripts")
        
        alerts = []
        analyses = []
        
        for transcript in transcripts:
            segments = []
            for seg in transcript.get('segments', []):
                segments.append(TranscriptSegment(
                    speaker=seg.get('speaker', 'Unknown'),
                    role=SpeakerRole(seg.get('role', 'Other')),
                    text=seg.get('text', ''),
                    timestamp=seg.get('timestamp'),
                    is_response=seg.get('is_response', False)
                ))
            
            if not segments:
                continue
            
            analysis = self.analyze_transcript(
                segments=segments,
                company_id=transcript.get('company_id', 'Unknown'),
                call_date=transcript.get('call_date', date.today()),
                fiscal_period=transcript.get('fiscal_period', '')
            )
            analyses.append(analysis)
            
            # Check for excessive hedging
            hedging_alert = self.detect_excessive_hedging(analysis)
            if hedging_alert:
                alerts.append(hedging_alert)
        
        # Check for sentiment shifts (requires multiple transcripts per company)
        for company_id, company_analyses in self._analyses.items():
            if len(company_analyses) >= 2:
                shift_alerts = self._detect_sentiment_shifts(company_analyses)
                alerts.extend(shift_alerts)
        
        # Calculate averages
        avg_sentiment = (
            sum(a.sentiment_score for a in analyses) / len(analyses)
            if analyses else 0
        )
        avg_uncertainty = (
            sum(a.uncertainty_score for a in analyses) / len(analyses)
            if analyses else 0
        )
        
        return Node12Output(
            transcripts_analyzed=len(analyses),
            alerts=alerts,
            sentiment_shifts=len([a for a in alerts if a.alert_type == TranscriptAlertType.SENTIMENT_SHIFT]),
            excessive_hedging_count=len([a for a in alerts if a.alert_type == TranscriptAlertType.EXCESSIVE_HEDGING]),
            contradictions_found=sum(len(a.document_contradictions) for a in analyses),
            question_avoidance_count=len([a for a in alerts if a.alert_type == TranscriptAlertType.QUESTION_AVOIDANCE]),
            average_sentiment=avg_sentiment,
            average_uncertainty=avg_uncertainty
        )
    
    def detect_excessive_hedging(self, analysis: TranscriptAnalysis) -> Optional[TranscriptAlert]:
        """
        Detect excessive hedging language in transcript.
        """
        if analysis.hedging_phrase_count > self.EXCESSIVE_HEDGING_THRESHOLD or \
           analysis.uncertainty_score > self.UNCERTAINTY_THRESHOLD:
            
            severity = 'HIGH' if analysis.uncertainty_score > 0.7 else 'MEDIUM'
            
            return TranscriptAlert(
                alert_type=TranscriptAlertType.EXCESSIVE_HEDGING,
                call_date=analysis.call_date,
                company_id=analysis.company_id,
                severity=severity,
                details=[
                    f'Hedging phrase count: {analysis.hedging_phrase_count}',
                    f'Uncertainty score: {analysis.uncertainty_score:.2f}',
                    'High hedging language may indicate undisclosed risks'
                ],
                flagged_statements=[
                    f.text[:100] for f in analysis.flagged_statements
                    if f.issue == 'HEDGING'
                ][:5],
                evidence_hash=analysis.evidence_hash
            )
        
        return None
    
    def detect_sentiment_shift(
        self,
        current: TranscriptAnalysis,
        previous: TranscriptAnalysis
    ) -> Optional[TranscriptAlert]:
        """
        Detect significant sentiment shifts between quarters.
        """
        sentiment_change = current.sentiment_score - previous.sentiment_score
        uncertainty_change = current.uncertainty_score - previous.uncertainty_score
        
        if sentiment_change < -self.SENTIMENT_SHIFT_THRESHOLD and uncertainty_change > 0.2:
            return TranscriptAlert(
                alert_type=TranscriptAlertType.SENTIMENT_SHIFT,
                call_date=current.call_date,
                company_id=current.company_id,
                severity='HIGH' if sentiment_change < -0.5 else 'MEDIUM',
                details=[
                    f'Sentiment dropped from {previous.sentiment_score:.2f} to {current.sentiment_score:.2f}',
                    f'Uncertainty increased from {previous.uncertainty_score:.2f} to {current.uncertainty_score:.2f}',
                    f'Previous period: {previous.fiscal_period}',
                    f'Current period: {current.fiscal_period}'
                ],
                flagged_statements=[f.text[:100] for f in current.flagged_statements[:5]],
                evidence_hash=self._generate_hash({
                    'current': current.evidence_hash,
                    'previous': previous.evidence_hash
                })
            )
        
        return None
    
    def cross_reference_filings(
        self,
        analysis: TranscriptAnalysis,
        filings: List[Dict[str, Any]]
    ) -> List[DocumentContradiction]:
        """
        Cross-reference transcript with SEC filings for contradictions.
        
        Args:
            analysis: Transcript analysis
            filings: List of SEC filings with sections
            
        Returns:
            List of detected contradictions
        """
        contradictions = []
        
        # Extract numbers from flagged statements
        number_pattern = r'\$?[\d,]+\.?\d*[BMK]?%?'
        
        transcript_numbers = {}
        for stmt in analysis.flagged_statements:
            matches = re.findall(number_pattern, stmt.text)
            for match in matches:
                context = stmt.text[:100]
                transcript_numbers[match] = context
        
        # Compare with filing numbers
        for filing in filings:
            filing_text = ' '.join(
                section.get('text', '')
                for section in filing.get('sections', [])
            )
            
            filing_numbers = re.findall(number_pattern, filing_text)
            
            for trans_num, context in transcript_numbers.items():
                for filing_num in filing_numbers:
                    if self._are_same_metric(context, filing_text):
                        trans_val = self._normalize_number(trans_num)
                        filing_val = self._normalize_number(filing_num)
                        
                        if trans_val > 0 and filing_val > 0:
                            diff = abs(trans_val - filing_val) / max(trans_val, filing_val)
                            
                            if diff > 0.1:  # >10% difference
                                contradictions.append(DocumentContradiction(
                                    transcript_statement=context,
                                    filed_statement=filing_text[:150],
                                    filing_type=filing.get('type', '10-Q'),
                                    contradiction_type='NUMERICAL',
                                    confidence=0.75
                                ))
        
        analysis.document_contradictions = contradictions
        return contradictions
    
    def _flag_statements(self, segments: List[TranscriptSegment]) -> List[FlaggedStatement]:
        """Flag statements for review based on NLP patterns."""
        flagged = []
        
        for segment in segments:
            lower_text = segment.text.lower()
            
            # Check hedging
            hedging_found = [h for h in HEDGING_PHRASES if h in lower_text]
            if len(hedging_found) >= 2:
                flagged.append(FlaggedStatement(
                    text=segment.text[:200],
                    issue='HEDGING',
                    confidence=min(len(hedging_found) / 3, 1.0),
                    context=f'Speaker: {segment.speaker} ({segment.role.value})'
                ))
            
            # Check avoidance
            avoidance_found = [a for a in AVOIDANCE_PATTERNS if a in lower_text]
            if avoidance_found:
                flagged.append(FlaggedStatement(
                    text=segment.text[:200],
                    issue='AVOIDANCE',
                    confidence=0.8,
                    context=f'Speaker: {segment.speaker} ({segment.role.value})'
                ))
        
        return flagged
    
    def _detect_sentiment_shifts(
        self,
        analyses: List[TranscriptAnalysis]
    ) -> List[TranscriptAlert]:
        """Detect sentiment shifts across multiple transcripts."""
        alerts = []
        
        sorted_analyses = sorted(analyses, key=lambda a: a.call_date)
        
        for i in range(1, len(sorted_analyses)):
            alert = self.detect_sentiment_shift(sorted_analyses[i], sorted_analyses[i-1])
            if alert:
                alerts.append(alert)
        
        return alerts
    
    def _normalize_number(self, num_str: str) -> float:
        """Normalize number string to float."""
        try:
            num = float(re.sub(r'[$,%]', '', num_str).replace(',', ''))
            if 'B' in num_str:
                num *= 1e9
            elif 'M' in num_str:
                num *= 1e6
            elif 'K' in num_str:
                num *= 1e3
            return num
        except ValueError:
            return 0.0
    
    def _are_same_metric(self, context1: str, context2: str) -> bool:
        """Check if two contexts refer to the same metric."""
        metrics = ['revenue', 'earnings', 'profit', 'margin', 'eps', 'guidance', 'forecast']
        lower1 = context1.lower()
        lower2 = context2.lower()
        return any(m in lower1 and m in lower2 for m in metrics)
    
    def _generate_hash(self, data: Any) -> str:
        """Generate SHA-256 evidence hash."""
        return hashlib.sha256(str(data).encode()).hexdigest()

