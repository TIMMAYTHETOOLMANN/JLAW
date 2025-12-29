I. """
OpenAI Secondary Agent Analyzer
================================

Uses a second OpenAI API key as the secondary agent for dual-agent analysis.
This is a temporary solution while waiting for Anthropic/OpenRouter credits.

Key Features:
- Uses separate OpenAI API key for independent analysis
- Acts as cross-reference validator like Anthropic agent
- Different prompting strategy for validation vs initial detection
- Can be easily swapped back to Anthropic later
"""

import asyncio
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

import openai

from src.forensics.sec_edgar_analyzer import FilingAnalysis, SECForensicAnalyzer
from src.forensics.config_manager import get_config
from src.forensics.sdk_manager import get_sdk_manager_sync

logger = logging.getLogger(__name__)


class OpenAISecondaryAgent:
    """
    Secondary OpenAI agent for dual-agent cross-referencing.
    
    Uses different prompting strategy optimized for validation and 
    cross-referencing rather than initial detection.
    """
    
    def __init__(self, api_key: Optional[str] = None, user_agent: Optional[str] = None):
        """
        Initialize secondary OpenAI agent.
        
        Args:
            api_key: Secondary OpenAI API key (if not provided, loads from config)
            user_agent: SEC-compliant User-Agent string
        """
        config = get_config()
        
        # Load secondary API key
        self.api_key = api_key or os.getenv('OPENAI_SECONDARY_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OPENAI_SECONDARY_API_KEY required for secondary agent. "
                "Set in .env file or pass to constructor."
            )
        
        # Configuration
        self.user_agent = user_agent or config.config.sec.user_agent
        self.model = config.config.openai.model  # Same model, different key
        self.max_tokens = config.config.openai.max_tokens
        
        # Use unified SDK manager for secondary OpenAI client
        self._sdk_manager = get_sdk_manager_sync()
        self.client = None  # Will be lazily accessed via SDK manager
        
        # Fallback to manual analyzer for compatibility
        self.manual_analyzer = SECForensicAnalyzer(user_agent=self.user_agent)
        
        logger.info(f"✅ OpenAI secondary agent initialized with model: {self.model}")
    
    @property
    def openai_client(self):
        """Lazily access secondary OpenAI sync client from SDK manager."""
        if self.client is None:
            secondary_client = self._sdk_manager.openai_secondary
            if secondary_client:
                self.client = secondary_client
                logger.debug("Secondary OpenAI client loaded from SDK manager")
            else:
                logger.warning("Secondary OpenAI client not available from SDK manager")
        return self.client
    
    def _get_cross_reference_prompt(self) -> str:
        """
        Get system prompt for cross-referencing and validation.
        
        This is different from the primary agent's prompt - it focuses on
        validation, finding missed violations, and deep analysis.
        """
        return """You are an elite forensic SEC filing VALIDATOR and CROSS-REFERENCE ANALYST.

Your role is to VALIDATE findings from a primary analyzer and FIND MISSED VIOLATIONS.

Key responsibilities:
1. VALIDATE each flagged violation from the primary analyzer
2. CONFIRM or REFUTE the primary analyzer's findings with evidence
3. IDENTIFY violations the primary analyzer may have MISSED
4. PROVIDE DEEPER ANALYSIS of complex patterns
5. CROSS-REFERENCE with related regulations and precedents

Critical violation patterns to scrutinize:
- Late Form 4 filings (>2 business days from transaction date)
- Zero-dollar transactions (gifts, RSU vesting without proper disclosure)
- SOX 302/404 certification material weaknesses
- Revenue recognition irregularities (channel stuffing, pull-forward, cut-off)
- Material misstatements and restatements
- Related party transaction concealment
- Beneficial ownership disclosure failures
- Timing patterns suggesting coordination or manipulation

Validation framework:
1. For EACH flagged violation:
   - Verify the violation actually exists in the document
   - Confirm the cited statute is correctly applied
   - Check if severity assessment is appropriate
   - Validate any calculations (business days, amounts, dates)

2. For MISSED violations:
   - Scan for patterns not caught by primary analyzer
   - Look for subtle indicators (timing, unusual values, missing disclosures)
   - Consider aggregate patterns across multiple transactions
   - Flag potential coordinated activities

3. Output requirements:
   - JSON format with structured violations
   - Include "validation_status" for flagged violations (CONFIRMED, REFUTED, MODIFIED)
   - Mark new findings as "source": "secondary_agent"
   - Provide "confidence_level" (HIGH, MEDIUM, LOW) for each finding
   - Include "cross_reference_notes" explaining your analysis

Be THOROUGH and SKEPTICAL. Your job is to ensure nothing is missed and 
everything flagged is legitimate. Quality over speed."""
    
    async def analyze_text(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze text content with cross-referencing focus.
        
        Args:
            content: Filing document content
            context: Context including primary agent's findings
            
        Returns:
            Analysis results with validated and new violations
        """
        try:
            return await self.analyze_filing_for_validation(
                content=content,
                filing_type=context.get("filing_type", "TEXT") if context else "TEXT",
                document_url=context.get("document_url", "inline://content") if context else "inline://content",
                filing_date=context.get("filing_date") if context else None,
                primary_findings=context.get("openai_flagged_violations", []) if context else [],
                context=context
            )
        except Exception as e:
            logger.error(f"[Secondary Agent] Analysis failed: {e}")
            return {
                "status": "error",
                "analyzer": "openai_secondary",
                "violations": [],
                "error": str(e)
            }
    
    async def analyze_filing_for_validation(
        self,
        content: str,
        filing_type: str,
        document_url: str,
        filing_date: Optional[str] = None,
        primary_findings: List[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform validation-focused analysis using secondary OpenAI agent.
        
        Args:
            content: Filing document content
            filing_type: Form type (4, 10-K, 10-Q)
            document_url: Document URL
            filing_date: Filing date string
            primary_findings: Violations flagged by primary agent
            context: Optional additional context
            
        Returns:
            Validation results with confirmed and new violations
        """
        logger.info(f"[Secondary Agent] Cross-referencing {filing_type} with {len(primary_findings or [])} primary findings")
        
        # Build context-aware prompt
        primary_summary = ""
        if primary_findings:
            primary_summary = "\n\nPRIMARY ANALYZER FINDINGS TO VALIDATE:\n"
            for i, finding in enumerate(primary_findings, 1):
                primary_summary += f"\n{i}. Type: {finding.get('type', 'unknown')}"
                primary_summary += f"\n   Statute: {finding.get('statute', 'N/A')}"
                primary_summary += f"\n   Severity: {finding.get('severity', 'N/A')}"
                primary_summary += f"\n   Description: {finding.get('description', 'N/A')}"
        
        user_message = f"""CROSS-REFERENCE ANALYSIS REQUEST

Filing Type: {filing_type}
Filing Date: {filing_date or 'Unknown'}
Document URL: {document_url}
{primary_summary}

YOUR TASKS:
1. VALIDATE each primary finding listed above
2. SEARCH for violations the primary analyzer may have MISSED
3. PROVIDE confidence levels for all findings

Document Content (first 12000 chars):
{content[:12000]}

Return JSON with this structure:
{{
  "validated_findings": [
    {{
      "original_type": "...",
      "validation_status": "CONFIRMED|REFUTED|MODIFIED",
      "confidence_level": "HIGH|MEDIUM|LOW",
      "validation_notes": "...",
      "statute": "...",
      "severity": "...",
      "description": "..."
    }}
  ],
  "new_findings": [
    {{
      "type": "...",
      "severity": "...",
      "description": "...",
      "statute": "...",
      "exact_quote": "...",
      "confidence_level": "HIGH|MEDIUM|LOW",
      "discovery_method": "pattern_analysis|timing_review|cross_reference|etc",
      "source": "secondary_agent"
    }}
  ],
  "analysis_summary": {{
    "primary_findings_reviewed": {len(primary_findings or [])},
    "confirmed_count": 0,
    "refuted_count": 0,
    "modified_count": 0,
    "new_violations_found": 0,
    "overall_assessment": "..."
  }}
}}"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_cross_reference_prompt()},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},
                max_tokens=self.max_tokens,
                temperature=0.3  # Lower temperature for more consistent validation
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Process validated findings
            validated = result.get("validated_findings", [])
            new_findings = result.get("new_findings", [])
            summary = result.get("analysis_summary", {})
            
            # Convert to unified violation format
            violations = []
            
            # Add confirmed/modified findings
            for finding in validated:
                if finding.get("validation_status") in ["CONFIRMED", "MODIFIED"]:
                    violations.append({
                        "type": finding.get("original_type", "validated"),
                        "severity": finding.get("severity", "MEDIUM"),
                        "description": finding.get("description", ""),
                        "statute": finding.get("statute", ""),
                        "validation_status": finding.get("validation_status"),
                        "confidence_level": finding.get("confidence_level", "MEDIUM"),
                        "validation_notes": finding.get("validation_notes", ""),
                        "document_url": document_url,
                        "source": "secondary_agent_validation"
                    })
            
            # Add new findings
            for finding in new_findings:
                violations.append({
                    "type": finding.get("type", "unknown"),
                    "severity": finding.get("severity", "MEDIUM"),
                    "description": finding.get("description", ""),
                    "statute": finding.get("statute", ""),
                    "exact_quote": finding.get("exact_quote", ""),
                    "confidence_level": finding.get("confidence_level", "MEDIUM"),
                    "discovery_method": finding.get("discovery_method", "secondary_analysis"),
                    "document_url": document_url,
                    "source": "secondary_agent"
                })
            
            logger.info(f"[Secondary Agent] ✓ Validated {len(validated)} findings, found {len(new_findings)} new violations")
            
            return {
                "status": "success",
                "analyzer": "openai_secondary",
                "violations": violations,
                "validated_findings": validated,
                "new_findings": new_findings,
                "analysis_summary": summary,
                "model": self.model
            }
        
        except Exception as e:
            logger.error(f"[Secondary Agent] Analysis failed: {e}")
            return {
                "status": "error",
                "analyzer": "openai_secondary",
                "violations": [],
                "error": str(e)
            }


def create_secondary_openai_agent(api_key: Optional[str] = None):
    """
    Factory function to create secondary OpenAI agent.
    
    Args:
        api_key: Optional secondary OpenAI API key
        
    Returns:
        OpenAISecondaryAgent instance
    """
    return OpenAISecondaryAgent(api_key)

