"""
Tests for AI Cross-Validation of Detection Patterns
===================================================

Tests the cross_validate_pattern_with_ai and batch_cross_validate_patterns
functions that provide dual AI agent validation of quantitative fraud scores.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from src.detection.patterns.advanced_patterns import (
    cross_validate_pattern_with_ai,
    batch_cross_validate_patterns,
    PatternSeverity
)


class TestCrossValidatePatternWithAI:
    """Test suite for cross_validate_pattern_with_ai function."""
    
    @pytest.mark.asyncio
    async def test_successful_validation(self):
        """Test successful pattern validation with dual agents."""
        # Mock DualAgentCoordinator
        mock_dual_agent = MagicMock()
        mock_dual_agent.analyze_text = AsyncMock(return_value={
            "status": "OK",
            "openai": {
                "status": "success",
                "violations": [
                    {
                        "type": "fraud",
                        "confidence": 0.85,
                        "description": "High M-Score indicates manipulation"
                    }
                ]
            },
            "anthropic": {
                "status": "success",
                "violations": [
                    {
                        "type": "fraud",
                        "confidence": 0.90,
                        "description": "M-Score above threshold"
                    }
                ]
            },
            "consensus": {
                "overlap": 1,
                "openai_only": 0,
                "anthropic_only": 0
            }
        })
        
        # Execute validation
        result = await cross_validate_pattern_with_ai(
            pattern_name="Beneish M-Score",
            score=-2.8,
            evidence={"dsri": 1.2, "gmi": 0.95},
            dual_agent=mock_dual_agent,
            threshold=0.7
        )
        
        # Assertions
        assert result["pattern_name"] == "Beneish M-Score"
        assert result["quantitative_score"] == -2.8
        assert result["ai_confidence"] > 0
        assert result["validation_status"] in ["validated", "rejected", "uncertain"]
        assert "reasoning" in result
        assert "supporting_factors" in result
        assert "contradicting_factors" in result
        assert "recommendations" in result
        assert "openai_analysis" in result
        assert "anthropic_analysis" in result
    
    @pytest.mark.asyncio
    async def test_validation_with_high_confidence(self):
        """Test pattern validation returns 'validated' status for high AI confidence."""
        mock_dual_agent = MagicMock()
        mock_dual_agent.analyze_text = AsyncMock(return_value={
            "status": "OK",
            "openai": {
                "status": "success",
                "violations": [{"confidence": 0.95}]
            },
            "anthropic": {
                "status": "success",
                "violations": [{"confidence": 0.90}]
            },
            "consensus": {"overlap": 1}
        })
        
        result = await cross_validate_pattern_with_ai(
            pattern_name="Test Pattern",
            score=0.8,
            evidence={},
            dual_agent=mock_dual_agent,
            threshold=0.7
        )
        
        # High confidence should result in validated status
        assert result["validation_status"] == "validated"
        assert result["ai_confidence"] >= 70
    
    @pytest.mark.asyncio
    async def test_validation_with_low_confidence(self):
        """Test pattern validation returns 'rejected' status for low AI confidence."""
        mock_dual_agent = MagicMock()
        mock_dual_agent.analyze_text = AsyncMock(return_value={
            "status": "OK",
            "openai": {
                "status": "success",
                "violations": [{"confidence": 0.30}]
            },
            "anthropic": {
                "status": "success",
                "violations": [{"confidence": 0.25}]
            },
            "consensus": {"overlap": 0}
        })
        
        result = await cross_validate_pattern_with_ai(
            pattern_name="Test Pattern",
            score=0.3,
            evidence={},
            dual_agent=mock_dual_agent,
            threshold=0.7
        )
        
        # Low confidence should result in rejected status
        assert result["validation_status"] == "rejected"
        assert result["ai_confidence"] < 40
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """Test error handling when dual agent fails."""
        mock_dual_agent = MagicMock()
        mock_dual_agent.analyze_text = AsyncMock(
            side_effect=Exception("Agent unavailable")
        )
        
        result = await cross_validate_pattern_with_ai(
            pattern_name="Test Pattern",
            score=0.5,
            evidence={},
            dual_agent=mock_dual_agent
        )
        
        # Should return error status with details
        assert result["validation_status"] == "error"
        assert "error" in result
        assert result["ai_confidence"] == 0.0
        assert "Agent unavailable" in result["error"]


class TestBatchCrossValidation:
    """Test suite for batch_cross_validate_patterns function."""
    
    @pytest.mark.asyncio
    async def test_batch_validation_filters_by_severity(self):
        """Test that batch validation only processes HIGH and CRITICAL patterns."""
        mock_dual_agent = MagicMock()
        mock_dual_agent.analyze_text = AsyncMock(return_value={
            "status": "OK",
            "openai": {"status": "success", "violations": [{"confidence": 0.85}]},
            "anthropic": {"status": "success", "violations": [{"confidence": 0.90}]},
            "consensus": {"overlap": 1}
        })
        
        # Create pattern results with different severities
        pattern_results = [
            {
                "pattern_name": "Pattern 1",
                "severity": "HIGH",
                "confidence": 0.9,
                "evidence": {}
            },
            {
                "pattern_name": "Pattern 2",
                "severity": "LOW",
                "confidence": 0.8,
                "evidence": {}
            },
            {
                "pattern_name": "Pattern 3",
                "severity": "CRITICAL",
                "confidence": 0.95,
                "evidence": {}
            }
        ]
        
        result = await batch_cross_validate_patterns(
            pattern_results=pattern_results,
            dual_agent=mock_dual_agent,
            severity_filter=["HIGH", "CRITICAL"]
        )
        
        # Should only validate HIGH and CRITICAL (2 patterns)
        assert result["total_patterns"] == 3
        assert result["patterns_evaluated"] == 2
        assert len(result["validated_patterns"]) == 2
    
    @pytest.mark.asyncio
    async def test_batch_validation_statistics(self):
        """Test that batch validation returns correct statistics."""
        mock_dual_agent = MagicMock()
        
        # Mock different confidence levels for different patterns
        call_count = 0
        async def mock_analyze(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                confidence = 0.90  # Validated
            elif call_count == 2:
                confidence = 0.35  # Rejected
            else:
                confidence = 0.60  # Uncertain
            
            return {
                "status": "OK",
                "openai": {"status": "success", "violations": [{"confidence": confidence}]},
                "anthropic": {"status": "success", "violations": [{"confidence": confidence}]},
                "consensus": {"overlap": 1}
            }
        
        mock_dual_agent.analyze_text = mock_analyze
        
        pattern_results = [
            {"pattern_name": "P1", "severity": "HIGH", "confidence": 0.9, "evidence": {}},
            {"pattern_name": "P2", "severity": "HIGH", "confidence": 0.4, "evidence": {}},
            {"pattern_name": "P3", "severity": "HIGH", "confidence": 0.6, "evidence": {}}
        ]
        
        result = await batch_cross_validate_patterns(
            pattern_results=pattern_results,
            dual_agent=mock_dual_agent
        )
        
        # Check statistics
        assert result["patterns_evaluated"] == 3
        assert result["validated_count"] >= 0
        assert result["rejected_count"] >= 0
        assert result["uncertain_count"] >= 0
        assert "average_ai_confidence" in result
        assert "high_confidence_findings" in result
    
    @pytest.mark.asyncio
    async def test_batch_validation_high_confidence_findings(self):
        """Test identification of high confidence findings (>85%)."""
        mock_dual_agent = MagicMock()
        mock_dual_agent.analyze_text = AsyncMock(return_value={
            "status": "OK",
            "openai": {"status": "success", "violations": [{"confidence": 0.95}]},
            "anthropic": {"status": "success", "violations": [{"confidence": 0.90}]},
            "consensus": {"overlap": 1}
        })
        
        pattern_results = [
            {
                "pattern_name": "High Confidence Pattern",
                "severity": "CRITICAL",
                "confidence": 0.95,
                "evidence": {}
            }
        ]
        
        result = await batch_cross_validate_patterns(
            pattern_results=pattern_results,
            dual_agent=mock_dual_agent
        )
        
        # Should identify high confidence findings
        assert result["high_confidence_count"] >= 0
        assert isinstance(result["high_confidence_findings"], list)
    
    @pytest.mark.asyncio
    async def test_batch_validation_with_pattern_severity_enum(self):
        """Test that batch validation handles PatternSeverity enum correctly."""
        mock_dual_agent = MagicMock()
        mock_dual_agent.analyze_text = AsyncMock(return_value={
            "status": "OK",
            "openai": {"status": "success", "violations": [{"confidence": 0.85}]},
            "anthropic": {"status": "success", "violations": [{"confidence": 0.85}]},
            "consensus": {"overlap": 1}
        })
        
        pattern_results = [
            {
                "pattern_name": "Pattern with Enum",
                "severity": PatternSeverity.HIGH,  # Enum instead of string
                "confidence": 0.9,
                "evidence": {}
            }
        ]
        
        result = await batch_cross_validate_patterns(
            pattern_results=pattern_results,
            dual_agent=mock_dual_agent
        )
        
        # Should handle enum conversion
        assert result["patterns_evaluated"] == 1
        assert len(result["validated_patterns"]) == 1
    
    @pytest.mark.asyncio
    async def test_batch_validation_empty_patterns(self):
        """Test batch validation with empty pattern list."""
        mock_dual_agent = MagicMock()
        
        result = await batch_cross_validate_patterns(
            pattern_results=[],
            dual_agent=mock_dual_agent
        )
        
        # Should handle empty list gracefully
        assert result["total_patterns"] == 0
        assert result["patterns_evaluated"] == 0
        assert result["validated_count"] == 0
        assert result["average_ai_confidence"] == 0.0
