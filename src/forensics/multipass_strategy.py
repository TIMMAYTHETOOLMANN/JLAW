"""
Multi-Pass Analysis Strategy for Deep Forensic Investigation
Coordinates multiple AI agents for comprehensive violation detection.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
from dataclasses import dataclass, field

from src.forensics.sec_edgar_analyzer import FilingAnalysis

logger = logging.getLogger(__name__)


@dataclass
class AnalysisPass:
    """Single analysis pass result."""
    pass_number: int
    analyzer_type: str  # 'openai', 'anthropic', 'manual'
    model_used: str
    result: FilingAnalysis
    violations_found: int
    execution_time_seconds: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class MultiPassResult:
    """Result from multi-pass analysis."""
    filing_id: str
    passes: List[AnalysisPass]
    merged_violations: List[Dict[str, Any]]
    unique_violation_count: int
    total_passes: int
    best_pass: Optional[AnalysisPass]
    confidence_score: float


class MultiPassAnalysisStrategy:
    """
    Orchestrates multi-pass analysis using different AI providers.
    
    Pass 1: OpenAI GPT-4 (fast, general-purpose)
    Pass 2: Anthropic Claude (deep reasoning, pattern detection)
    Pass 3: OpenAI + Anthropic combined (consensus building)
    Pass 4: Manual verification (high-confidence violations only)
    """
    
    def __init__(
        self,
        openai_analyzer=None,
        anthropic_analyzer=None,
        manual_analyzer=None,
        enable_multipass: bool = False,
        max_passes: int = 4
    ):
        """
        Initialize multi-pass strategy.
        
        Args:
            openai_analyzer: OpenAI agent analyzer instance
            anthropic_analyzer: Anthropic agent analyzer instance
            manual_analyzer: Manual SEC analyzer instance
            enable_multipass: Enable multi-pass analysis
            max_passes: Maximum number of analysis passes
        """
        self.openai_analyzer = openai_analyzer
        self.anthropic_analyzer = anthropic_analyzer
        self.manual_analyzer = manual_analyzer
        self.enable_multipass = enable_multipass
        self.max_passes = max_passes
        
        logger.info(f"MultiPassStrategy initialized: enable={enable_multipass}, max_passes={max_passes}")
    
    async def analyze_with_multipass(
        self,
        cik: str,
        accession_number: str,
        filing_type: str,
        document_url: str,
        viewer_url: Optional[str] = None,
        filing_date: Optional[str] = None
    ) -> MultiPassResult:
        """
        Execute multi-pass analysis with multiple AI providers.
        
        Args:
            cik: Company CIK
            accession_number: Filing accession number
            filing_type: Form type
            document_url: Document URL
            viewer_url: Viewer URL
            filing_date: Filing date
        
        Returns:
            MultiPassResult with consolidated findings
        """
        filing_id = f"{cik}_{accession_number}"
        logger.info(f"[MultiPass] Starting analysis for {filing_id}")
        
        passes: List[AnalysisPass] = []
        
        # Pass 1: OpenAI (if available)
        if self.openai_analyzer and self.max_passes >= 1:
            try:
                start_time = asyncio.get_event_loop().time()
                result = await self.openai_analyzer.analyze_filing(
                    cik, accession_number, filing_type, document_url, viewer_url, filing_date
                )
                execution_time = asyncio.get_event_loop().time() - start_time
                
                passes.append(AnalysisPass(
                    pass_number=1,
                    analyzer_type='openai',
                    model_used=self.openai_analyzer.model,
                    result=result,
                    violations_found=len(result.red_flags),
                    execution_time_seconds=execution_time
                ))
                logger.info(f"[MultiPass] Pass 1 (OpenAI): {len(result.red_flags)} violations")
            except Exception as e:
                logger.error(f"[MultiPass] Pass 1 (OpenAI) failed: {e}")
        
        # Pass 2: Anthropic (if available and multipass enabled)
        if self.anthropic_analyzer and self.enable_multipass and self.max_passes >= 2:
            try:
                start_time = asyncio.get_event_loop().time()
                result = await self.anthropic_analyzer.analyze_filing(
                    cik, accession_number, filing_type, document_url, viewer_url, filing_date
                )
                execution_time = asyncio.get_event_loop().time() - start_time
                
                passes.append(AnalysisPass(
                    pass_number=2,
                    analyzer_type='anthropic',
                    model_used=self.anthropic_analyzer.model,
                    result=result,
                    violations_found=len(result.red_flags),
                    execution_time_seconds=execution_time
                ))
                logger.info(f"[MultiPass] Pass 2 (Anthropic): {len(result.red_flags)} violations")
            except Exception as e:
                logger.error(f"[MultiPass] Pass 2 (Anthropic) failed: {e}")
        
        # Pass 3: Consensus building (if both analyzers succeeded)
        # TODO: Implement consensus logic for Pass 3
        
        # Pass 4: Manual verification fallback
        if not passes or (self.manual_analyzer and self.max_passes >= 4):
            try:
                start_time = asyncio.get_event_loop().time()
                result = await self.manual_analyzer.analyze_filing(
                    cik, accession_number, filing_type, document_url, viewer_url
                )
                execution_time = asyncio.get_event_loop().time() - start_time
                
                passes.append(AnalysisPass(
                    pass_number=len(passes) + 1,
                    analyzer_type='manual',
                    model_used='regex_pattern_matching',
                    result=result,
                    violations_found=len(result.red_flags),
                    execution_time_seconds=execution_time
                ))
                logger.info(f"[MultiPass] Pass {len(passes)} (Manual): {len(result.red_flags)} violations")
            except Exception as e:
                logger.error(f"[MultiPass] Manual pass failed: {e}")
        
        # Merge and deduplicate violations
        merged = self._merge_violations(passes)
        
        # Find best pass (most violations with highest confidence)
        best_pass = self._find_best_pass(passes)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(passes)
        
        result = MultiPassResult(
            filing_id=filing_id,
            passes=passes,
            merged_violations=merged,
            unique_violation_count=len(merged),
            total_passes=len(passes),
            best_pass=best_pass,
            confidence_score=confidence
        )
        
        logger.info(f"[MultiPass] Complete: {len(passes)} passes, {len(merged)} unique violations")
        return result
    
    def _merge_violations(self, passes: List[AnalysisPass]) -> List[Dict[str, Any]]:
        """
        Merge and deduplicate violations from multiple passes.
        
        Args:
            passes: List of analysis passes
        
        Returns:
            Deduplicated list of violations
        """
        all_violations = []
        seen_fingerprints = set()
        
        for pass_result in passes:
            for violation in pass_result.result.red_flags:
                # Create fingerprint for deduplication
                fingerprint = self._create_violation_fingerprint(violation)
                
                if fingerprint not in seen_fingerprints:
                    seen_fingerprints.add(fingerprint)
                    
                    # Add metadata about which pass found this
                    violation_with_meta = dict(violation) if isinstance(violation, dict) else {
                        'type': violation.get('type'),
                        'description': violation.get('description'),
                        'severity': violation.get('severity')
                    }
                    violation_with_meta['detected_in_pass'] = pass_result.pass_number
                    violation_with_meta['detected_by_analyzer'] = pass_result.analyzer_type
                    
                    all_violations.append(violation_with_meta)
        
        return all_violations
    
    def _create_violation_fingerprint(self, violation: Dict[str, Any]) -> str:
        """
        Create unique fingerprint for violation deduplication.
        
        Args:
            violation: Violation dictionary
        
        Returns:
            Fingerprint string
        """
        # Use type, severity, and description hash for deduplication
        v_type = violation.get('type', 'unknown')
        v_severity = violation.get('severity', 'MEDIUM')
        v_desc = violation.get('description', '')[:100]  # First 100 chars
        v_quote = violation.get('exact_quote', '')[:50]  # First 50 chars
        
        return f"{v_type}_{v_severity}_{hash(v_desc)}_{hash(v_quote)}"
    
    def _find_best_pass(self, passes: List[AnalysisPass]) -> Optional[AnalysisPass]:
        """
        Find the best analysis pass (most violations detected).
        
        Args:
            passes: List of analysis passes
        
        Returns:
            Best pass or None
        """
        if not passes:
            return None
        
        # Sort by violations found (descending)
        sorted_passes = sorted(passes, key=lambda p: p.violations_found, reverse=True)
        return sorted_passes[0]
    
    def _calculate_confidence(self, passes: List[AnalysisPass]) -> float:
        """
        Calculate confidence score based on pass agreement.
        
        Args:
            passes: List of analysis passes
        
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not passes:
            return 0.0
        
        if len(passes) == 1:
            return 0.7  # Single pass has moderate confidence
        
        # Multiple passes increase confidence
        # Agreement between passes boosts confidence
        violation_counts = [p.violations_found for p in passes]
        
        if len(set(violation_counts)) == 1:
            # Perfect agreement
            return 0.95
        
        # Partial agreement
        avg_violations = sum(violation_counts) / len(violation_counts)
        variance = sum((v - avg_violations) ** 2 for v in violation_counts) / len(violation_counts)
        
        # Lower variance = higher confidence
        confidence = max(0.5, min(0.9, 0.8 - (variance / (avg_violations + 1)) * 0.3))
        
        return confidence

