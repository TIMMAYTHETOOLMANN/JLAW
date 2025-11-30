"""
Narrative Analyzer Module - Management Communication Shift Detection
====================================================================

LLM-ready management narrative shift detection for forensic analysis.
Analyzes temporal changes in management communications to detect:
- Tone shifts in earnings calls
- Linguistic pattern changes
- Hedging language increases
- Forward-looking statement modifications

Features:
- Temporal tone analysis
- Linguistic pattern detection
- Severity classification
- Earnings call integration
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ShiftSeverity(Enum):
    """Severity levels for narrative shifts."""

    CRITICAL = "CRITICAL"  # Major tone reversal, potential fraud indicator
    HIGH = "HIGH"  # Significant unexplained shift
    MEDIUM = "MEDIUM"  # Notable change worth investigating
    LOW = "LOW"  # Minor shift, likely normal variation
    NONE = "NONE"  # No significant shift detected


class NarrativeCategory(Enum):
    """Categories of narrative elements analyzed."""

    FORWARD_LOOKING = "FORWARD_LOOKING"
    HEDGING_LANGUAGE = "HEDGING_LANGUAGE"
    CERTAINTY_MARKERS = "CERTAINTY_MARKERS"
    RISK_DISCLOSURE = "RISK_DISCLOSURE"
    PERFORMANCE_ATTRIBUTION = "PERFORMANCE_ATTRIBUTION"
    TEMPORAL_REFERENCES = "TEMPORAL_REFERENCES"
    EXECUTIVE_SENTIMENT = "EXECUTIVE_SENTIMENT"


@dataclass
class NarrativeSegment:
    """A segment of narrative text for analysis."""

    text: str
    source: str  # e.g., "10-K Filing", "Q3 Earnings Call"
    date: datetime
    speaker: Optional[str] = None  # For earnings calls
    section: Optional[str] = None  # e.g., "MD&A", "Risk Factors"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LinguisticMetrics:
    """Linguistic metrics extracted from narrative."""

    word_count: int
    sentence_count: int
    avg_sentence_length: float
    hedging_ratio: float
    certainty_ratio: float
    forward_looking_ratio: float
    passive_voice_ratio: float
    first_person_ratio: float
    complexity_score: float
    sentiment_score: float


@dataclass
class NarrativeShift:
    """Detected shift in narrative patterns."""

    category: NarrativeCategory
    severity: ShiftSeverity
    description: str
    baseline_value: float
    current_value: float
    change_percentage: float
    baseline_period: str
    current_period: str
    supporting_evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NarrativeAnalysisResult:
    """Complete narrative analysis results."""

    segments_analyzed: int
    time_span_days: int
    shifts_detected: List[NarrativeShift]
    overall_severity: ShiftSeverity
    temporal_metrics: Dict[str, List[float]]
    linguistic_summary: Dict[str, LinguisticMetrics]
    risk_score: float
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class NarrativeAnalyzer:
    """
    Analyzes management narratives for significant shifts that may indicate
    potential issues, misdirection, or fraud.

    Uses linguistic analysis to detect:
    - Tone shifts in communications
    - Increases in hedging language
    - Changes in certainty markers
    - Modifications to forward-looking statements
    """

    # Hedging phrases that indicate uncertainty or qualification
    HEDGING_PATTERNS = [
        r"\b(may|might|could|would|should)\b",
        r"\b(possibly|potentially|perhaps|probably)\b",
        r"\b(appears?\sto|seems?\sto|tends?\sto)\b",
        r"\b(in\sour\sopinion|we\sbelieve|we\sthink)\b",
        r"\b(subject\sto|depending\son|contingent)\b",
        r"\b(approximately|about|around|roughly)\b",
        r"\b(certain|some|various|substantial)\b",
        r"\b(generally|typically|usually|often)\b",
    ]

    # Certainty markers that indicate confidence
    CERTAINTY_PATTERNS = [
        r"\b(will|shall|must)\b",
        r"\b(definitely|certainly|absolutely|clearly)\b",
        r"\b(is|are|was|were)\s(committed|dedicated|confident)\b",
        r"\b(guarantee[ds]?|ensure[ds]?|confirm[eds]?)\b",
        r"\b(always|never|every|all)\b",
        r"\b(proven|demonstrated|established)\b",
    ]

    # Forward-looking statement indicators
    FORWARD_LOOKING_PATTERNS = [
        r"\b(expects?|anticipates?|projects?|forecasts?)\b",
        r"\b(guidance|outlook|target[s]?|goal[s]?)\b",
        r"\b(future|upcoming|next\s(year|quarter|fiscal))\b",
        r"\b(plan[s]?|intend[s]?|aim[s]?|seek[s]?)\b",
        r"\b(will\sbe|going\sto|expected\sto)\b",
        r"\b(estimates?|believes?|assumes?)\b",
    ]

    # Risk disclosure patterns
    RISK_PATTERNS = [
        r"\b(risk[s]?|uncertainty|uncertainties)\b",
        r"\b(adverse|negatively?\s?impact|material\seffect)\b",
        r"\b(volatility|fluctuation[s]?|instability)\b",
        r"\b(litigation|regulatory|compliance)\b",
        r"\b(may\snot|cannot|unable\sto)\b",
        r"\b(challenge[s]?|difficulty|difficulties)\b",
    ]

    # Performance attribution patterns
    ATTRIBUTION_PATTERNS = {
        "internal": [
            r"\b(our\steam|management|employees|strategy)\b",
            r"\b(innovation|execution|efficiency|leadership)\b",
            r"\b(investment[s]?|initiative[s]?|improvement[s]?)\b",
        ],
        "external": [
            r"\b(market\sconditions?|economy|industry)\b",
            r"\b(weather|pandemic|macroeconomic)\b",
            r"\b(competition|regulatory|government)\b",
            r"\b(supply\schain|inflation|currency)\b",
        ],
    }

    def __init__(
        self,
        shift_threshold: float = 0.20,
        min_segments: int = 2,
        critical_threshold: float = 0.50,
        high_threshold: float = 0.35,
    ):
        """
        Initialize the narrative analyzer.

        Args:
            shift_threshold: Minimum change percentage to flag a shift
            min_segments: Minimum segments required for comparison
            critical_threshold: Threshold for CRITICAL severity
            high_threshold: Threshold for HIGH severity
        """
        self.shift_threshold = shift_threshold
        self.min_segments = min_segments
        self.critical_threshold = critical_threshold
        self.high_threshold = high_threshold
        self.logger = logging.getLogger(__name__)

        # Compile regex patterns
        self._hedging_re = [re.compile(p, re.IGNORECASE) for p in self.HEDGING_PATTERNS]
        self._certainty_re = [re.compile(p, re.IGNORECASE) for p in self.CERTAINTY_PATTERNS]
        self._forward_re = [re.compile(p, re.IGNORECASE) for p in self.FORWARD_LOOKING_PATTERNS]
        self._risk_re = [re.compile(p, re.IGNORECASE) for p in self.RISK_PATTERNS]

    def analyze(self, segments: List[NarrativeSegment]) -> NarrativeAnalysisResult:
        """
        Analyze narrative segments for shifts and patterns.

        Args:
            segments: List of narrative segments to analyze

        Returns:
            NarrativeAnalysisResult with detected shifts and metrics
        """
        self.logger.info(f"Analyzing {len(segments)} narrative segments")

        if len(segments) < self.min_segments:
            self.logger.warning(f"Insufficient segments for analysis (min: {self.min_segments})")
            return NarrativeAnalysisResult(
                segments_analyzed=len(segments),
                time_span_days=0,
                shifts_detected=[],
                overall_severity=ShiftSeverity.NONE,
                temporal_metrics={},
                linguistic_summary={},
                risk_score=0.0,
                recommendations=["Need more narrative segments for meaningful analysis"],
            )

        # Sort segments by date
        segments = sorted(segments, key=lambda s: s.date)

        # Calculate time span
        time_span = (segments[-1].date - segments[0].date).days

        # Extract metrics for each segment
        metrics_by_period: Dict[str, LinguisticMetrics] = {}
        temporal_metrics: Dict[str, List[float]] = defaultdict(list)

        for segment in segments:
            metrics = self._extract_metrics(segment.text)
            period_key = segment.date.strftime("%Y-%m")
            metrics_by_period[period_key] = metrics

            # Track temporal evolution
            temporal_metrics["hedging"].append(metrics.hedging_ratio)
            temporal_metrics["certainty"].append(metrics.certainty_ratio)
            temporal_metrics["forward_looking"].append(metrics.forward_looking_ratio)
            temporal_metrics["complexity"].append(metrics.complexity_score)
            temporal_metrics["sentiment"].append(metrics.sentiment_score)

        # Detect shifts
        shifts = self._detect_shifts(segments, temporal_metrics)

        # Calculate overall severity
        overall_severity = self._calculate_overall_severity(shifts)

        # Calculate risk score
        risk_score = self._calculate_risk_score(shifts, temporal_metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(shifts, overall_severity)

        return NarrativeAnalysisResult(
            segments_analyzed=len(segments),
            time_span_days=time_span,
            shifts_detected=shifts,
            overall_severity=overall_severity,
            temporal_metrics=dict(temporal_metrics),
            linguistic_summary=metrics_by_period,
            risk_score=risk_score,
            recommendations=recommendations,
        )

    def _extract_metrics(self, text: str) -> LinguisticMetrics:
        """Extract linguistic metrics from text."""
        if not text:
            return LinguisticMetrics(
                word_count=0,
                sentence_count=0,
                avg_sentence_length=0.0,
                hedging_ratio=0.0,
                certainty_ratio=0.0,
                forward_looking_ratio=0.0,
                passive_voice_ratio=0.0,
                first_person_ratio=0.0,
                complexity_score=0.0,
                sentiment_score=0.0,
            )

        # Basic counts
        words = text.split()
        word_count = len(words)
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences) if sentences else 1
        avg_sentence_length = word_count / sentence_count

        # Pattern matching
        hedging_matches = sum(len(p.findall(text)) for p in self._hedging_re)
        certainty_matches = sum(len(p.findall(text)) for p in self._certainty_re)
        forward_matches = sum(len(p.findall(text)) for p in self._forward_re)

        # Calculate ratios (per 1000 words for normalization)
        hedging_ratio = (hedging_matches / word_count * 1000) if word_count > 0 else 0
        certainty_ratio = (certainty_matches / word_count * 1000) if word_count > 0 else 0
        forward_ratio = (forward_matches / word_count * 1000) if word_count > 0 else 0

        # Passive voice detection (simple heuristic)
        passive_pattern = re.compile(r"\b(was|were|been|being|is|are)\s+\w+ed\b", re.IGNORECASE)
        passive_matches = len(passive_pattern.findall(text))
        passive_ratio = (passive_matches / sentence_count * 100) if sentence_count > 0 else 0

        # First person ratio
        first_person = re.compile(r"\b(we|our|us|I|my|me)\b", re.IGNORECASE)
        first_person_matches = len(first_person.findall(text))
        first_person_ratio = (first_person_matches / word_count * 100) if word_count > 0 else 0

        # Complexity score (based on sentence length and vocabulary)
        complexity = min(avg_sentence_length / 20, 1.0)  # Normalize to 0-1

        # Simple sentiment (positive vs negative word ratio)
        sentiment = self._calculate_simple_sentiment(text)

        return LinguisticMetrics(
            word_count=word_count,
            sentence_count=sentence_count,
            avg_sentence_length=avg_sentence_length,
            hedging_ratio=hedging_ratio,
            certainty_ratio=certainty_ratio,
            forward_looking_ratio=forward_ratio,
            passive_voice_ratio=passive_ratio,
            first_person_ratio=first_person_ratio,
            complexity_score=complexity,
            sentiment_score=sentiment,
        )

    def _calculate_simple_sentiment(self, text: str) -> float:
        """Calculate simple sentiment score (-1 to 1)."""
        positive_words = {
            "strong",
            "growth",
            "improve",
            "success",
            "excellent",
            "great",
            "positive",
            "increase",
            "gain",
            "profit",
            "opportunity",
            "achieve",
            "exceed",
            "record",
            "momentum",
            "confident",
            "robust",
            "healthy",
        }
        negative_words = {
            "weak",
            "decline",
            "loss",
            "challenge",
            "difficult",
            "risk",
            "negative",
            "decrease",
            "uncertain",
            "concern",
            "adversely",
            "impact",
            "pressure",
            "headwind",
            "volatile",
            "disappointing",
        }

        words = set(text.lower().split())
        positive_count = len(words & positive_words)
        negative_count = len(words & negative_words)

        total = positive_count + negative_count
        if total == 0:
            return 0.0

        return (positive_count - negative_count) / total

    def _detect_shifts(
        self, segments: List[NarrativeSegment], temporal_metrics: Dict[str, List[float]]
    ) -> List[NarrativeShift]:
        """Detect significant shifts in narrative patterns."""
        shifts = []

        for metric_name, values in temporal_metrics.items():
            if len(values) < 2:
                continue

            # Compare first half vs second half (baseline vs current)
            mid = len(values) // 2
            baseline_values = values[:mid]
            current_values = values[mid:]

            baseline_avg = sum(baseline_values) / len(baseline_values)
            current_avg = sum(current_values) / len(current_values)

            # Calculate change
            if baseline_avg != 0:
                change_pct = (current_avg - baseline_avg) / baseline_avg
            else:
                change_pct = current_avg  # Handle zero baseline

            # Check if significant shift
            if abs(change_pct) >= self.shift_threshold:
                severity = self._classify_severity(abs(change_pct), metric_name)
                category = self._metric_to_category(metric_name)

                # Generate description
                direction = "increased" if change_pct > 0 else "decreased"
                description = self._generate_shift_description(
                    metric_name, direction, abs(change_pct)
                )

                # Get supporting evidence
                evidence = self._extract_evidence(segments, metric_name, change_pct)

                shifts.append(
                    NarrativeShift(
                        category=category,
                        severity=severity,
                        description=description,
                        baseline_value=baseline_avg,
                        current_value=current_avg,
                        change_percentage=change_pct * 100,
                        baseline_period=segments[0].date.strftime("%Y-%m"),
                        current_period=segments[-1].date.strftime("%Y-%m"),
                        supporting_evidence=evidence,
                    )
                )

        # Sort by severity
        severity_order = {
            ShiftSeverity.CRITICAL: 0,
            ShiftSeverity.HIGH: 1,
            ShiftSeverity.MEDIUM: 2,
            ShiftSeverity.LOW: 3,
            ShiftSeverity.NONE: 4,
        }
        shifts.sort(key=lambda s: severity_order[s.severity])

        return shifts

    def _classify_severity(self, change_pct: float, metric_name: str) -> ShiftSeverity:
        """Classify the severity of a shift."""
        # Hedging increases are more concerning
        if metric_name == "hedging":
            if change_pct >= self.critical_threshold:
                return ShiftSeverity.CRITICAL
            elif change_pct >= self.high_threshold:
                return ShiftSeverity.HIGH
            elif change_pct >= self.shift_threshold:
                return ShiftSeverity.MEDIUM

        # Certainty decreases are concerning
        elif metric_name == "certainty":
            if change_pct >= self.critical_threshold:
                return ShiftSeverity.HIGH
            elif change_pct >= self.shift_threshold:
                return ShiftSeverity.MEDIUM

        # Sentiment drops are concerning
        elif metric_name == "sentiment":
            if change_pct >= self.critical_threshold:
                return ShiftSeverity.HIGH
            elif change_pct >= self.high_threshold:
                return ShiftSeverity.MEDIUM

        # General threshold
        if change_pct >= self.critical_threshold:
            return ShiftSeverity.HIGH
        elif change_pct >= self.high_threshold:
            return ShiftSeverity.MEDIUM
        elif change_pct >= self.shift_threshold:
            return ShiftSeverity.LOW

        return ShiftSeverity.NONE

    def _metric_to_category(self, metric_name: str) -> NarrativeCategory:
        """Map metric name to narrative category."""
        mapping = {
            "hedging": NarrativeCategory.HEDGING_LANGUAGE,
            "certainty": NarrativeCategory.CERTAINTY_MARKERS,
            "forward_looking": NarrativeCategory.FORWARD_LOOKING,
            "sentiment": NarrativeCategory.EXECUTIVE_SENTIMENT,
            "complexity": NarrativeCategory.RISK_DISCLOSURE,
        }
        return mapping.get(metric_name, NarrativeCategory.EXECUTIVE_SENTIMENT)

    def _generate_shift_description(
        self, metric_name: str, direction: str, change_pct: float
    ) -> str:
        """Generate human-readable description of shift."""
        # Determine confidence modifier for certainty description
        confidence_modifier = "more" if direction == "increased" else "less"
        # Determine complexity modifier
        complexity_modifier = "more" if direction == "increased" else "less"

        descriptions = {
            "hedging": (
                f"Hedging language {direction} by {change_pct:.1%}. "
                "This may indicate increased uncertainty or defensive positioning."
            ),
            "certainty": (
                f"Certainty markers {direction} by {change_pct:.1%}. "
                f"Management appears {confidence_modifier} confident."
            ),
            "forward_looking": (
                f"Forward-looking statements {direction} by {change_pct:.1%}. "
                "Guidance language has changed significantly."
            ),
            "sentiment": (
                f"Overall sentiment {direction} by {change_pct:.1%}. "
                "Tone of management communications has shifted."
            ),
            "complexity": (
                f"Language complexity {direction} by {change_pct:.1%}. "
                f"Communications have become {complexity_modifier} complex."
            ),
        }
        return descriptions.get(
            metric_name,
            f"{metric_name.replace('_', ' ').title()} {direction} by {change_pct:.1%}.",
        )

    def _extract_evidence(
        self, segments: List[NarrativeSegment], metric_name: str, change_pct: float
    ) -> List[str]:
        """Extract supporting evidence for detected shift."""
        evidence = []

        # Compare first and last segments
        if len(segments) >= 2:
            first = segments[0]
            last = segments[-1]

            evidence.append(f"Baseline period: {first.source} ({first.date.strftime('%Y-%m-%d')})")
            evidence.append(f"Current period: {last.source} ({last.date.strftime('%Y-%m-%d')})")

            # Add sample phrases if hedging increased
            if metric_name == "hedging" and change_pct > 0:
                hedging_phrases = []
                for pattern in self._hedging_re:
                    matches = pattern.findall(last.text)
                    hedging_phrases.extend(matches[:3])  # Limit to 3 per pattern
                if hedging_phrases:
                    evidence.append(f"Sample hedging language: {', '.join(hedging_phrases[:5])}")

        return evidence

    def _calculate_overall_severity(self, shifts: List[NarrativeShift]) -> ShiftSeverity:
        """Calculate overall severity from individual shifts."""
        if not shifts:
            return ShiftSeverity.NONE

        severity_scores = {
            ShiftSeverity.CRITICAL: 4,
            ShiftSeverity.HIGH: 3,
            ShiftSeverity.MEDIUM: 2,
            ShiftSeverity.LOW: 1,
            ShiftSeverity.NONE: 0,
        }

        max_score = max(severity_scores[s.severity] for s in shifts)

        # Multiple high/medium shifts compound to higher severity
        high_count = sum(
            1 for s in shifts if s.severity in [ShiftSeverity.HIGH, ShiftSeverity.CRITICAL]
        )
        if high_count >= 2:
            max_score = min(max_score + 1, 4)

        # Reverse lookup
        for severity, score in severity_scores.items():
            if score == max_score:
                return severity

        return ShiftSeverity.NONE

    def _calculate_risk_score(
        self, shifts: List[NarrativeShift], temporal_metrics: Dict[str, List[float]]
    ) -> float:
        """Calculate overall risk score (0-100)."""
        base_score = 0.0

        # Add points for each shift
        for shift in shifts:
            if shift.severity == ShiftSeverity.CRITICAL:
                base_score += 25
            elif shift.severity == ShiftSeverity.HIGH:
                base_score += 15
            elif shift.severity == ShiftSeverity.MEDIUM:
                base_score += 8
            elif shift.severity == ShiftSeverity.LOW:
                base_score += 3

        # Check for concerning patterns
        hedging_values = temporal_metrics.get("hedging", [])
        if hedging_values and len(hedging_values) >= 2:
            # Monotonically increasing hedging is very concerning
            if all(
                hedging_values[i] <= hedging_values[i + 1] for i in range(len(hedging_values) - 1)
            ):
                base_score += 10

        # Cap at 100
        return min(base_score, 100.0)

    def _generate_recommendations(
        self, shifts: List[NarrativeShift], overall_severity: ShiftSeverity
    ) -> List[str]:
        """Generate investigation recommendations."""
        recommendations = []

        if overall_severity == ShiftSeverity.CRITICAL:
            recommendations.append(
                "URGENT: Critical narrative shifts detected. "
                "Recommend immediate deep-dive investigation."
            )
            recommendations.append(
                "Cross-reference with financial performance and material events."
            )
            recommendations.append("Compare management statements with actual outcomes.")

        elif overall_severity == ShiftSeverity.HIGH:
            recommendations.append("Significant narrative shifts warrant investigation.")
            recommendations.append(
                "Review contemporaneous market conditions for potential explanations."
            )

        elif overall_severity == ShiftSeverity.MEDIUM:
            recommendations.append("Notable narrative changes detected. Consider monitoring.")

        # Specific recommendations based on shifts
        for shift in shifts:
            if (
                shift.category == NarrativeCategory.HEDGING_LANGUAGE
                and shift.change_percentage > 30
            ):
                recommendations.append(
                    "Increased hedging language may indicate management uncertainty. "
                    "Review for undisclosed risks."
                )

            if (
                shift.category == NarrativeCategory.FORWARD_LOOKING
                and shift.change_percentage < -30
            ):
                recommendations.append(
                    "Reduced forward-looking statements may indicate reluctance to commit. "
                    "Compare with guidance history."
                )

        if not recommendations:
            recommendations.append("No significant narrative concerns identified at this time.")

        return recommendations

    def generate_report(self, result: NarrativeAnalysisResult) -> str:
        """Generate a human-readable analysis report."""
        report = []
        report.append("=" * 60)
        report.append("NARRATIVE ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")

        report.append(f"Segments Analyzed: {result.segments_analyzed}")
        report.append(f"Time Span: {result.time_span_days} days")
        report.append(f"Overall Severity: {result.overall_severity.value}")
        report.append(f"Risk Score: {result.risk_score:.1f}/100")
        report.append("")

        if result.shifts_detected:
            report.append("DETECTED SHIFTS:")
            report.append("-" * 40)
            for shift in result.shifts_detected:
                report.append(f"  [{shift.severity.value}] {shift.category.value}")
                report.append(f"    {shift.description}")
                report.append(f"    Change: {shift.change_percentage:+.1f}%")
                report.append(f"    Period: {shift.baseline_period} → {shift.current_period}")
                report.append("")
        else:
            report.append("No significant narrative shifts detected.")
            report.append("")

        report.append("RECOMMENDATIONS:")
        report.append("-" * 40)
        for rec in result.recommendations:
            report.append(f"  • {rec}")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)
