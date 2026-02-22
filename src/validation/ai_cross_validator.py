"""
AI Cross-Validation Module
===========================

Ensures all 23 detection patterns are cross-validated by dual AI agents
(OpenAI + Anthropic) for consensus-based fraud detection.

This module implements Phase 6 of the JLAW Master Execution Pipeline:
- Dual-agent (OpenAI + Anthropic) validation
- Consensus logic for agreement/disagreement
- Confidence scoring and discrepancy tracking
- Integration with all 23 detection patterns

23 Detection Patterns Covered:
1. SEC EDGAR Anomalies
2. Insider Transaction Triangulation
3. Derivatives vs Earnings
4. Form 144 Volume Violations
5. Round-Tripping Detection
6. Wolf Pack Formation
7. Pre-Announcement Positioning
8. Disclosure Timing Anomaly
9. Channel Stuffing
10. Options Backdating
11. Benford Analysis
12. Beneish M-Score
13. Executive Compensation Anomaly
14. SOX Certification Gaps
15. IRC §83 Exposure
16. 13F Holdings Discrepancy
17. 13D/13G Ownership Shifts
18. 8-K Event Timing
19. Related Party Transactions
20. Revenue Recognition Anomaly
21. Inventory Manipulation
22. Z-Score Bankruptcy Risk
23. F-Score Financial Strength

Legal Framework:
- FRE 702 (Expert testimony)
- FRE 901 (Authenticating evidence)
- Daubert Standard (Scientific evidence admissibility)
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Status of AI cross-validation."""
    CONSENSUS = "CONSENSUS"  # Both agents agree
    PARTIAL_AGREEMENT = "PARTIAL_AGREEMENT"  # Agents partially agree
    DISAGREEMENT = "DISAGREEMENT"  # Agents disagree
    SINGLE_AGENT = "SINGLE_AGENT"  # Only one agent available
    FAILED = "FAILED"  # Validation failed


class DetectionPattern(Enum):
    """All 23 detection patterns in JLAW."""
    SEC_EDGAR_ANOMALIES = "SEC_EDGAR_ANOMALIES"
    INSIDER_TRIANGULATION = "INSIDER_TRIANGULATION"
    DERIVATIVES_VS_EARNINGS = "DERIVATIVES_VS_EARNINGS"
    FORM_144_VOLUME = "FORM_144_VOLUME"
    ROUND_TRIPPING = "ROUND_TRIPPING"
    WOLF_PACK = "WOLF_PACK"
    PRE_ANNOUNCEMENT = "PRE_ANNOUNCEMENT"
    DISCLOSURE_TIMING = "DISCLOSURE_TIMING"
    CHANNEL_STUFFING = "CHANNEL_STUFFING"
    OPTIONS_BACKDATING = "OPTIONS_BACKDATING"
    BENFORD_ANALYSIS = "BENFORD_ANALYSIS"
    BENEISH_MSCORE = "BENEISH_MSCORE"
    EXEC_COMPENSATION = "EXEC_COMPENSATION"
    SOX_CERTIFICATION = "SOX_CERTIFICATION"
    IRC_83_EXPOSURE = "IRC_83_EXPOSURE"
    HOLDINGS_13F = "HOLDINGS_13F"
    OWNERSHIP_13D_13G = "OWNERSHIP_13D_13G"
    EVENT_8K_TIMING = "EVENT_8K_TIMING"
    RELATED_PARTY_TXN = "RELATED_PARTY_TXN"
    REVENUE_RECOGNITION = "REVENUE_RECOGNITION"
    INVENTORY_MANIPULATION = "INVENTORY_MANIPULATION"
    ZSCORE_BANKRUPTCY = "ZSCORE_BANKRUPTCY"
    FSCORE_STRENGTH = "FSCORE_STRENGTH"


@dataclass
class CrossValidationResult:
    """Result from AI cross-validation of a detection pattern."""
    pattern_name: str
    pattern_type: DetectionPattern
    status: ValidationStatus
    openai_confidence: Optional[float]
    anthropic_confidence: Optional[float]
    consensus_confidence: float
    openai_verdict: Optional[str]
    anthropic_verdict: Optional[str]
    consensus_verdict: str
    discrepancies: List[str]
    evidence_summary: Dict[str, Any]
    validation_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_name": self.pattern_name,
            "pattern_type": self.pattern_type.value,
            "status": self.status.value,
            "openai_confidence": round(self.openai_confidence, 3) if self.openai_confidence else None,
            "anthropic_confidence": round(self.anthropic_confidence, 3) if self.anthropic_confidence else None,
            "consensus_confidence": round(self.consensus_confidence, 3),
            "openai_verdict": self.openai_verdict,
            "anthropic_verdict": self.anthropic_verdict,
            "consensus_verdict": self.consensus_verdict,
            "discrepancies": self.discrepancies,
            "evidence_summary": self.evidence_summary,
            "validation_timestamp": self.validation_timestamp.isoformat()
        }


@dataclass
class AICrossValidationReport:
    """Complete AI cross-validation report for all patterns."""
    analysis_date: datetime
    company_name: str
    cik: str
    patterns_validated: int
    consensus_count: int
    disagreement_count: int
    validation_results: List[CrossValidationResult]
    overall_confidence: float
    high_confidence_violations: List[str]
    flagged_for_review: List[str]
    execution_time_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_date": self.analysis_date.isoformat(),
            "company_name": self.company_name,
            "cik": self.cik,
            "patterns_validated": self.patterns_validated,
            "consensus_count": self.consensus_count,
            "disagreement_count": self.disagreement_count,
            "validation_results": [v.to_dict() for v in self.validation_results],
            "overall_confidence": round(self.overall_confidence, 3),
            "high_confidence_violations": self.high_confidence_violations,
            "flagged_for_review": self.flagged_for_review,
            "execution_time_seconds": round(self.execution_time_seconds, 2)
        }


class AICrossValidator:
    """
    AI Cross-Validation Engine
    
    Validates all 23 detection patterns using dual AI agents (OpenAI + Anthropic)
    to ensure consensus-based fraud detection with minimal false positives.
    """
    
    # Pattern-to-Node mapping for evidence extraction
    PATTERN_NODE_MAPPING = {
        DetectionPattern.SEC_EDGAR_ANOMALIES: ["Node1", "Node2", "Node3", "Node4"],
        DetectionPattern.INSIDER_TRIANGULATION: ["Node1"],
        DetectionPattern.DERIVATIVES_VS_EARNINGS: ["Node12", "Node15"],
        DetectionPattern.FORM_144_VOLUME: ["Node10"],
        DetectionPattern.ROUND_TRIPPING: ["Detection"],
        DetectionPattern.WOLF_PACK: ["Detection"],
        DetectionPattern.PRE_ANNOUNCEMENT: ["Detection"],
        DetectionPattern.DISCLOSURE_TIMING: ["Detection"],
        DetectionPattern.CHANNEL_STUFFING: ["Detection"],
        DetectionPattern.OPTIONS_BACKDATING: ["Detection"],
        DetectionPattern.BENFORD_ANALYSIS: ["Detection"],
        DetectionPattern.BENEISH_MSCORE: ["Detection"],
        DetectionPattern.EXEC_COMPENSATION: ["Node2"],
        DetectionPattern.SOX_CERTIFICATION: ["Node4"],
        DetectionPattern.IRC_83_EXPOSURE: ["Node5"],
        DetectionPattern.HOLDINGS_13F: ["Node7"],
        DetectionPattern.OWNERSHIP_13D_13G: ["Node8"],
        DetectionPattern.EVENT_8K_TIMING: ["Node9"],
        DetectionPattern.RELATED_PARTY_TXN: ["Node2"],
        DetectionPattern.REVENUE_RECOGNITION: ["Node3"],
        DetectionPattern.INVENTORY_MANIPULATION: ["Node3"],
        DetectionPattern.ZSCORE_BANKRUPTCY: ["Node13"],
        DetectionPattern.FSCORE_STRENGTH: ["Node14"]
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._openai_available = False
        self._anthropic_available = False
        self._dual_agent = None
        
        # Initialize dual agent coordinator
        try:
            from src.forensics.dual_agent import DualAgentCoordinator
            self._dual_agent = DualAgentCoordinator()
            availability = self._dual_agent.availability()
            self._openai_available = availability.get('openai', False)
            self._anthropic_available = availability.get('anthropic', False)
            
            if self._openai_available or self._anthropic_available:
                self.logger.info(f"✓ AI agents initialized: OpenAI={self._openai_available}, Anthropic={self._anthropic_available}")
            else:
                self.logger.warning("⚠ No AI agents available for cross-validation")
        except Exception as e:
            self.logger.warning(f"AI cross-validator initialization warning: {e}")
    
    async def validate_all_patterns(
        self,
        company_name: str,
        cik: str,
        pattern_results: Dict[str, Any],
        node_results: Optional[Dict[str, Any]] = None
    ) -> AICrossValidationReport:
        """
        Validate all 23 detection patterns using dual AI agents.
        
        Args:
            company_name: Target company name
            cik: SEC Central Index Key
            pattern_results: Results from pattern detection (Phase 5)
            node_results: Results from 15-node analysis (Phase 4)
        
        Returns:
            AICrossValidationReport with validation results for all patterns
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"=== AI Cross-Validation for {company_name} ===")
        self.logger.info("Validating all 23 detection patterns with dual AI agents...")
        
        validation_results: List[CrossValidationResult] = []
        
        # Validate each pattern
        for pattern in DetectionPattern:
            try:
                result = await self._validate_pattern(
                    pattern=pattern,
                    pattern_results=pattern_results,
                    node_results=node_results,
                    company_name=company_name
                )
                validation_results.append(result)
            except Exception as e:
                self.logger.error(f"Error validating pattern {pattern.name}: {e}", exc_info=True)
                # Create failed validation result
                failed_result = CrossValidationResult(
                    pattern_name=pattern.name,
                    pattern_type=pattern,
                    status=ValidationStatus.FAILED,
                    openai_confidence=None,
                    anthropic_confidence=None,
                    consensus_confidence=0.0,
                    openai_verdict=None,
                    anthropic_verdict=None,
                    consensus_verdict="VALIDATION_FAILED",
                    discrepancies=[f"Validation error: {str(e)}"],
                    evidence_summary={}
                )
                validation_results.append(failed_result)
        
        # Calculate aggregate metrics
        consensus_count = len([v for v in validation_results if v.status == ValidationStatus.CONSENSUS])
        disagreement_count = len([v for v in validation_results if v.status == ValidationStatus.DISAGREEMENT])
        
        # Calculate overall confidence (average of consensus confidence)
        overall_confidence = (
            sum(v.consensus_confidence for v in validation_results) / len(validation_results)
            if validation_results else 0.0
        )
        
        # Identify high-confidence violations (consensus confidence > 0.80)
        high_confidence_violations = [
            v.pattern_name for v in validation_results
            if v.consensus_confidence > 0.80 and v.consensus_verdict not in ["NO_VIOLATION", "VALIDATION_FAILED"]
        ]
        
        # Flag disagreements for manual review
        flagged_for_review = [
            v.pattern_name for v in validation_results
            if v.status == ValidationStatus.DISAGREEMENT
        ]
        
        execution_time = time.time() - start_time
        
        report = AICrossValidationReport(
            analysis_date=datetime.utcnow(),
            company_name=company_name,
            cik=cik,
            patterns_validated=len(validation_results),
            consensus_count=consensus_count,
            disagreement_count=disagreement_count,
            validation_results=validation_results,
            overall_confidence=overall_confidence,
            high_confidence_violations=high_confidence_violations,
            flagged_for_review=flagged_for_review,
            execution_time_seconds=execution_time
        )
        
        self.logger.info(f"✓ AI cross-validation complete: {consensus_count}/{len(validation_results)} consensus in {execution_time:.2f}s")
        return report
    
    async def _validate_pattern(
        self,
        pattern: DetectionPattern,
        pattern_results: Dict[str, Any],
        node_results: Optional[Dict[str, Any]],
        company_name: str
    ) -> CrossValidationResult:
        """Validate a single detection pattern using dual AI agents."""
        
        # Extract evidence for this pattern
        evidence = self._extract_pattern_evidence(pattern, pattern_results, node_results)
        
        if not evidence or not evidence.get('has_findings'):
            # No findings for this pattern
            return CrossValidationResult(
                pattern_name=pattern.name,
                pattern_type=pattern,
                status=ValidationStatus.CONSENSUS,
                openai_confidence=1.0,
                anthropic_confidence=1.0,
                consensus_confidence=1.0,
                openai_verdict="NO_VIOLATION",
                anthropic_verdict="NO_VIOLATION",
                consensus_verdict="NO_VIOLATION",
                discrepancies=[],
                evidence_summary={"status": "no_findings"}
            )
        
        # Prepare validation prompt
        prompt = self._build_validation_prompt(pattern, evidence, company_name)
        
        # Get verdicts from both agents
        openai_verdict, openai_confidence = await self._get_openai_verdict(prompt)
        anthropic_verdict, anthropic_confidence = await self._get_anthropic_verdict(prompt)
        
        # Calculate consensus
        status, consensus_verdict, consensus_confidence, discrepancies = self._calculate_consensus(
            openai_verdict, openai_confidence,
            anthropic_verdict, anthropic_confidence
        )
        
        return CrossValidationResult(
            pattern_name=pattern.name,
            pattern_type=pattern,
            status=status,
            openai_confidence=openai_confidence,
            anthropic_confidence=anthropic_confidence,
            consensus_confidence=consensus_confidence,
            openai_verdict=openai_verdict,
            anthropic_verdict=anthropic_verdict,
            consensus_verdict=consensus_verdict,
            discrepancies=discrepancies,
            evidence_summary=evidence
        )
    
    def _extract_pattern_evidence(
        self,
        pattern: DetectionPattern,
        pattern_results: Dict[str, Any],
        node_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract evidence for a specific pattern from results."""
        evidence = {"pattern": pattern.name, "has_findings": False}
        
        # Map detection pattern enum names to Phase 5 result keys
        PATTERN_KEY_MAP = {
            "ROUND_TRIPPING": "round_tripping",
            "WOLF_PACK": "wolf_pack",
            "PRE_ANNOUNCEMENT": "pre_announcement",
            "DISCLOSURE_TIMING": "disclosure_timing",
            "BENFORD_ANALYSIS": "benford_analysis",
            "BENEISH_MSCORE": "beneish_mscore",
            "CHANNEL_STUFFING": "channel_stuffing",
            "OPTIONS_BACKDATING": "options_backdating",
            "HOLDINGS_13F": "wolf_pack",  # Wolf pack uses 13F data
            "OWNERSHIP_13D_13G": "13g_to_13d",
            "EVENT_8K_TIMING": "adverse_events",
        }

        # Check pattern-specific results from Phase 5
        if pattern_results:
            pattern_key = PATTERN_KEY_MAP.get(pattern.name, pattern.name.lower())
            if pattern_key in pattern_results:
                pattern_data = pattern_results[pattern_key]
                evidence["pattern_data"] = pattern_data
                if isinstance(pattern_data, list) and len(pattern_data) > 0:
                    evidence["has_findings"] = True
                elif pattern_data:
                    evidence["has_findings"] = True
        
        # Check node results - keys are like NODE_1, NODE_2, etc.
        if node_results:
            relevant_nodes = self.PATTERN_NODE_MAPPING.get(pattern, [])
            for node in relevant_nodes:
                # Normalize: "Node1" -> "NODE_1", "Node12" -> "NODE_12", "Detection" -> skip
                if node.startswith("Node"):
                    node_num = node[4:]  # "1", "12", etc.
                    node_key = f"NODE_{node_num}"
                else:
                    node_key = node.upper()

                if node_key in node_results:
                    node_data = node_results[node_key]
                    evidence[node_key] = node_data
                    # Check for any meaningful data in the findings
                    if isinstance(node_data, dict):
                        has_violations = node_data.get('violations_found', 0) > 0
                        has_alerts = node_data.get('alerts_generated', 0) > 0
                        has_data = any(
                            isinstance(v, list) and len(v) > 0
                            for v in node_data.values()
                        )
                        if has_violations or has_alerts or has_data:
                            evidence["has_findings"] = True
        
        return evidence
    
    def _build_validation_prompt(
        self,
        pattern: DetectionPattern,
        evidence: Dict[str, Any],
        company_name: str
    ) -> str:
        """Build validation prompt for AI agents."""
        prompt = f"""You are a forensic securities fraud analyst reviewing pattern detection results.

Company: {company_name}
Detection Pattern: {pattern.name}

Evidence Summary:
{self._format_evidence(evidence)}

Task: Analyze this evidence and provide:
1. A verdict: VIOLATION_CONFIRMED, LIKELY_VIOLATION, UNCERTAIN, or NO_VIOLATION
2. A confidence score (0.0 to 1.0)
3. A brief explanation (2-3 sentences)

Respond in JSON format:
{{
    "verdict": "VIOLATION_CONFIRMED|LIKELY_VIOLATION|UNCERTAIN|NO_VIOLATION",
    "confidence": 0.85,
    "explanation": "Brief explanation here"
}}
"""
        return prompt
    
    def _format_evidence(self, evidence: Dict[str, Any]) -> str:
        """Format evidence dictionary for display in prompt."""
        import json
        try:
            return json.dumps(evidence, indent=2, default=str)
        except Exception:
            return str(evidence)
    
    async def _get_openai_verdict(
        self,
        prompt: str
    ) -> Tuple[Optional[str], Optional[float]]:
        """Get verdict from OpenAI agent."""
        if not self._openai_available or not self._dual_agent:
            return None, None

        try:
            analyzer = self._dual_agent.openai_analyzer
            if not analyzer:
                return None, None

            # AgentSECForensicAnalyzer uses parse_violations_from_content (sync)
            if hasattr(analyzer, 'parse_violations_from_content'):
                response = analyzer.parse_violations_from_content(
                    prompt, "VALIDATION_PROMPT", "inline://cross-validation", None
                )
                return self._parse_verdict_response(response)
            # Fallback: try analyze_text (async)
            elif hasattr(analyzer, 'analyze_text'):
                response = await analyzer.analyze_text(prompt)
                return self._parse_verdict_response(response)
        except Exception as e:
            self.logger.debug(f"OpenAI verdict error: {e}")

        return None, None

    async def _get_anthropic_verdict(
        self,
        prompt: str
    ) -> Tuple[Optional[str], Optional[float]]:
        """Get verdict from Anthropic agent."""
        if not self._anthropic_available or not self._dual_agent:
            return None, None

        try:
            analyzer = self._dual_agent.anthropic_analyzer
            if not analyzer:
                return None, None

            # AnthropicAgentAnalyzer uses analyze_text (async)
            if hasattr(analyzer, 'analyze_text'):
                response = await analyzer.analyze_text(prompt)
                return self._parse_verdict_response(response)
            # Fallback: try analyze_filing_deep (async)
            elif hasattr(analyzer, 'analyze_filing_deep'):
                response = await analyzer.analyze_filing_deep(prompt, "cross-validation")
                return self._parse_verdict_response(response)
        except Exception as e:
            self.logger.debug(f"Anthropic verdict error: {e}")

        return None, None
    
    def _parse_verdict_response(
        self,
        response: Any
    ) -> Tuple[Optional[str], Optional[float]]:
        """Parse verdict and confidence from agent response."""
        import json
        
        try:
            # If response is a dict with 'analysis' or 'content' key
            if isinstance(response, dict):
                text = response.get('analysis') or response.get('content') or str(response)
            else:
                text = str(response)
            
            # Try to parse JSON from response
            # Look for JSON block in text
            if '{' in text and '}' in text:
                json_start = text.find('{')
                json_end = text.rfind('}') + 1
                json_str = text[json_start:json_end]
                data = json.loads(json_str)
                
                verdict = data.get('verdict', 'UNCERTAIN')
                confidence = float(data.get('confidence', 0.5))
                
                return verdict, confidence
        except Exception as e:
            self.logger.debug(f"Error parsing verdict response: {e}")
        
        # Default fallback
        return "UNCERTAIN", 0.5
    
    def _calculate_consensus(
        self,
        openai_verdict: Optional[str],
        openai_confidence: Optional[float],
        anthropic_verdict: Optional[str],
        anthropic_confidence: Optional[float]
    ) -> Tuple[ValidationStatus, str, float, List[str]]:
        """Calculate consensus between two AI agents."""
        discrepancies = []
        
        # Case 1: Both agents available
        if openai_verdict and anthropic_verdict:
            # Check for agreement
            if openai_verdict == anthropic_verdict:
                # Full consensus
                avg_confidence = (openai_confidence + anthropic_confidence) / 2.0
                return ValidationStatus.CONSENSUS, openai_verdict, avg_confidence, []
            
            # Check for partial agreement (both say violation or both say no violation)
            violation_verdicts = {"VIOLATION_CONFIRMED", "LIKELY_VIOLATION"}
            no_violation_verdicts = {"NO_VIOLATION", "UNCERTAIN"}
            
            if (openai_verdict in violation_verdicts and anthropic_verdict in violation_verdicts):
                # Both see violation, but different confidence
                avg_confidence = (openai_confidence + anthropic_confidence) / 2.0
                consensus = "LIKELY_VIOLATION"
                discrepancies.append(f"Agents agree on violation but differ in severity")
                return ValidationStatus.PARTIAL_AGREEMENT, consensus, avg_confidence, discrepancies
            
            if (openai_verdict in no_violation_verdicts and anthropic_verdict in no_violation_verdicts):
                # Both see no violation
                avg_confidence = (openai_confidence + anthropic_confidence) / 2.0
                consensus = "NO_VIOLATION"
                return ValidationStatus.PARTIAL_AGREEMENT, consensus, avg_confidence, discrepancies
            
            # Disagreement
            discrepancies.append(f"OpenAI: {openai_verdict}, Anthropic: {anthropic_verdict}")
            # Use more conservative verdict (favor no violation in disagreement)
            if openai_verdict in no_violation_verdicts or anthropic_verdict in no_violation_verdicts:
                consensus = "UNCERTAIN"
                avg_confidence = min(openai_confidence or 0.5, anthropic_confidence or 0.5)
            else:
                consensus = "LIKELY_VIOLATION"
                avg_confidence = (openai_confidence + anthropic_confidence) / 2.0
            
            return ValidationStatus.DISAGREEMENT, consensus, avg_confidence, discrepancies
        
        # Case 2: Only OpenAI available
        if openai_verdict:
            return ValidationStatus.SINGLE_AGENT, openai_verdict, openai_confidence or 0.5, ["Only OpenAI agent available"]
        
        # Case 3: Only Anthropic available
        if anthropic_verdict:
            return ValidationStatus.SINGLE_AGENT, anthropic_verdict, anthropic_confidence or 0.5, ["Only Anthropic agent available"]
        
        # Case 4: No agents available
        return ValidationStatus.FAILED, "NO_VALIDATION", 0.0, ["No AI agents available"]
    
    def is_available(self) -> bool:
        """Check if at least one AI agent is available."""
        return self._openai_available or self._anthropic_available
    
    def get_availability_status(self) -> Dict[str, bool]:
        """Get detailed availability status of AI agents."""
        return {
            "openai": self._openai_available,
            "anthropic": self._anthropic_available,
            "any_available": self.is_available()
        }
