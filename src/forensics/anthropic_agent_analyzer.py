"""
. 
Anthropic Claude Agent Analyzer for Deep Forensic Analysis
Uses Anthropic's Claude models for multi-pass deep analysis and reasoning.
"""

import asyncio
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json
import logging

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

from src.forensics.sec_edgar_analyzer import FilingAnalysis, SECForensicAnalyzer
from src.forensics.config_manager import get_config
from src.forensics.sdk_manager import get_sdk_manager_sync

logger = logging.getLogger(__name__)


class AnthropicAgentAnalyzer:
    """
    SEC forensic analyzer powered by Anthropic Claude.
    Specialized for deep reasoning, multi-pass analysis, and complex pattern detection.
    """
    
    def __init__(self, api_key: Optional[str] = None, user_agent: Optional[str] = None):
        """
        Initialize Anthropic agent analyzer.
        
        Args:
            api_key: Anthropic API key (if not provided, loads from config)
            user_agent: SEC-compliant User-Agent string
        """
        config = get_config()
        
        # Configuration
        self.user_agent = user_agent or config.config.sec.user_agent
        self.model = config.config.anthropic.model
        self.max_tokens = config.config.anthropic.max_tokens
        
        # Use unified SDK manager for Claude client (async)
        self._sdk_manager = get_sdk_manager_sync()
        self.client = None  # Will be lazily accessed via SDK manager
        self.using_openrouter = config.config.anthropic.openrouter_mode
        
        # Fallback to manual analyzer for compatibility
        self.manual_analyzer = SECForensicAnalyzer(user_agent=self.user_agent)
        
        logger.info(f"✅ Anthropic agent analyzer initialized with model: {self.model}")
    
    @property
    def anthropic_client(self):
        """Lazily access Claude client from SDK manager (OpenRouter or direct Anthropic)."""
        if self.client is None:
            if self.using_openrouter:
                openrouter_client = self._sdk_manager.openrouter
                if openrouter_client:
                    self.client = openrouter_client
                    logger.info("Claude client loaded via OpenRouter")
                    return self.client
            # Fallback to direct Anthropic SDK
            anthropic_client = self._sdk_manager.anthropic
            if anthropic_client:
                self.client = anthropic_client
                self.using_openrouter = False
                logger.debug("Anthropic client loaded from SDK manager")
            else:
                logger.warning("No Claude client available from SDK manager")
        return self.client

    async def analyze_text(self, content: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze arbitrary text content using Claude's deep reasoning path.

        Returns a dict with status, violations (if any), and raw analysis fields.
        """
        try:
            return await self.analyze_filing_deep(
                content=content,
                filing_type=context.get("filing_type", "TEXT") if context else "TEXT",
                document_url=context.get("document_url", "inline://content") if context else "inline://content",
                filing_date=context.get("filing_date") if context else None,
                context=context,
            )
        except Exception as e:
            logger.error("[Anthropic Text] Analysis failed: %s", e)
            return {"status": "error", "analyzer": "anthropic_claude", "violations": [], "error": str(e)}
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for forensic SEC analysis with Claude."""
        return """You are an elite forensic SEC filing analyzer with deep expertise in:
- Securities law violations (15 USC § 78 series)
- Financial statement fraud patterns
- Insider trading indicators
- SOX compliance deficiencies
- Material misstatement detection

Your analysis must be:
1. **Precise**: Cite exact statutes, dates, and dollar amounts
2. **Evidence-based**: Quote directly from documents
3. **Comprehensive**: Consider multiple violation angles
4. **Prosecutorial**: Focus on actionable, criminal-grade evidence
5. **Chain-of-custody aware**: Preserve forensic integrity

Key violation patterns to detect:
- Late Form 4 filings (>2 business days from transaction)
- Zero-dollar transactions (gifts, RSU vesting without disclosure)
- SOX 302/404 certification deficiencies
- Revenue manipulation (pull-forward, channel stuffing, cut-off)
- Earnings management and restatements
- Related party transaction concealment
- Beneficial ownership disclosure failures

Analysis framework:
1. Extract all transaction dates, prices, codes
2. Calculate business days (exclude weekends/holidays)
3. Identify anomalies (zero prices, unusual timing, large volumes)
4. Cross-reference with regulations
5. Generate violation records with evidence

Output format: JSON with structured violations including:
- type (late_form4, zero_dollar_transaction, sox_deficiency, etc.)
- severity (CRITICAL, HIGH, MEDIUM, LOW)
- statute (15 USC § 78p(a), 18 USC § 1350, etc.)
- description (concise, actionable)
- exact_quote (verbatim from document)
- evidence_chain (URLs, dates, hashes)
- prosecutorial_merit (STRONG, MODERATE, WEAK)
- estimated_damages (dollar amount if applicable)
"""
    
    async def analyze_filing_deep(
        self,
        content: str,
        filing_type: str,
        document_url: str,
        filing_date: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Perform deep analysis using Claude's reasoning capabilities.
        
        Args:
            content: Filing document content
            filing_type: Form type (4, 10-K, 10-Q)
            document_url: Document URL
            filing_date: Filing date string
            context: Optional context from previous passes
        
        Returns:
            Analysis results with detected violations
        """
        logger.info(f"[Anthropic Deep] Analyzing {filing_type} with Claude")
        
        # Prepare analysis request
        user_message = f"""Analyze this SEC {filing_type} filing for violations.

Filing Date: {filing_date or 'Unknown'}
Document URL: {document_url}
Previous Context: {json.dumps(context) if context else 'None (first pass)'}

Document Content (first 15000 chars):
{content[:15000]}

Provide a JSON response with detected violations following this structure:
{{
  "violations": [
    {{
      "type": "violation_type",
      "severity": "HIGH|MEDIUM|LOW|CRITICAL",
      "statute": "statute_reference",
      "description": "detailed_description",
      "exact_quote": "quote_from_document",
      "evidence": {{
        "transaction_date": "YYYY-MM-DD",
        "filing_date": "YYYY-MM-DD",
        "business_days_late": 0,
        "transaction_price": 0.0,
        "transaction_shares": 0,
        "transaction_code": "code"
      }},
      "prosecutorial_merit": "STRONG|MODERATE|WEAK",
      "estimated_damages": 25000
    }}
  ],
  "analysis_summary": "summary_of_findings",
  "risk_indicators": ["indicator1", "indicator2"],
  "recommended_actions": ["action1", "action2"]
}}
"""
        
        try:
            # Call Claude API - route via OpenRouter or direct Anthropic
            if self.using_openrouter:
                message = await self.anthropic_client.chat.completions.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": user_message},
                    ],
                    extra_headers={
                        "HTTP-Referer": "https://jlaw-forensics.com",
                        "X-Title": "JLAW Forensic Analysis Platform",
                    },
                )
                response_text = message.choices[0].message.content if message.choices else ""
            else:
                message = await self.anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=self._get_system_prompt(),
                    messages=[{"role": "user", "content": user_message}],
                )
                response_text = message.content[0].text

            logger.info(f"[Claude Deep] Received {len(response_text)} chars via {'OpenRouter' if self.using_openrouter else 'Anthropic'}")
            
            # Parse JSON response
            try:
                # Try to extract JSON from markdown code blocks if present
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                analysis_result = json.loads(response_text)
                
                logger.info(f"[Anthropic Deep] ✓ Detected {len(analysis_result.get('violations', []))} violations")
                
                return {
                    'status': 'success',
                    'analyzer': 'anthropic_claude',
                    'model': self.model,
                    'violations': analysis_result.get('violations', []),
                    'summary': analysis_result.get('analysis_summary', ''),
                    'risk_indicators': analysis_result.get('risk_indicators', []),
                    'recommended_actions': analysis_result.get('recommended_actions', []),
                    'usage': {
                        'input_tokens': getattr(message.usage, 'prompt_tokens', 0) or getattr(message.usage, 'input_tokens', 0),
                        'output_tokens': getattr(message.usage, 'completion_tokens', 0) or getattr(message.usage, 'output_tokens', 0),
                    }
                }
            
            except json.JSONDecodeError as e:
                logger.error(f"[Anthropic Deep] JSON parse error: {e}")
                logger.debug(f"[Anthropic Deep] Raw response: {response_text[:500]}")
                
                # Fallback: extract violations from text
                return {
                    'status': 'partial',
                    'analyzer': 'anthropic_claude',
                    'violations': [],
                    'raw_analysis': response_text,
                    'error': f'JSON parse failed: {str(e)}'
                }
        
        except Exception as e:
            logger.error(f"[Anthropic Deep] Analysis failed: {e}")
            return {
                'status': 'error',
                'analyzer': 'anthropic_claude',
                'violations': [],
                'error': str(e)
            }
    
    async def analyze_filing(
        self,
        cik: str,
        accession_number: str,
        filing_type: str,
        document_url: str,
        viewer_url: Optional[str] = None,
        filing_date: Optional[str] = None
    ) -> FilingAnalysis:
        """
        Analyze SEC filing using Anthropic Claude with deep reasoning.
        Falls back to manual analyzer if Claude analysis fails.
        
        Args:
            cik: Company CIK
            accession_number: Filing accession number
            filing_type: Form type
            document_url: Primary document URL
            viewer_url: Optional viewer URL
            filing_date: Optional filing date
        
        Returns:
            FilingAnalysis with detected violations
        """
        logger.info(f"[Anthropic Analyzer] Analyzing {filing_type} for CIK {cik}")
        
        try:
            # Fetch document content using SDK manager
            import aiohttp
            response = await self._sdk_manager.sec_request(
                document_url,
                self.user_agent,
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            if response.status != 200:
                logger.warning(f"[Anthropic Analyzer] Failed to fetch {document_url}: {response.status}")
                raise Exception(f"HTTP {response.status}")
            
            content = await response.text()
            
            # Perform deep analysis with Claude
            analysis_result = await self.analyze_filing_deep(
                content=content,
                filing_type=filing_type,
                document_url=document_url,
                filing_date=filing_date
            )
            
            if analysis_result.get('status') == 'success':
                # Convert Claude violations to FilingAnalysis format
                violations = analysis_result.get('violations', [])
                
                filing_dt = datetime.fromisoformat(filing_date + "T00:00:00") if filing_date else datetime.now(timezone.utc)
                
                analysis = FilingAnalysis(
                    cik=cik,
                    filing_type=filing_type,
                    filing_date=filing_dt,
                    period_end_date=filing_dt,
                    delay_days=0,
                    amendments=[],
                    red_flags=[{
                        'type': v.get('type', 'unknown'),
                        'severity': v.get('severity', 'MEDIUM'),
                        'description': v.get('description', ''),
                        'exact_quote': v.get('exact_quote', ''),
                        'document_url': document_url,
                        'viewer_url': viewer_url,
                        'section': 'claude_analysis',
                        'prosecutorial_merit': v.get('prosecutorial_merit', 'MODERATE'),
                        'estimated_damages': v.get('estimated_damages'),
                        'evidence_refs': [document_url],
                        'statute': v.get('statute', ''),
                        'analyzer': 'anthropic_claude'
                    } for v in violations],
                    fraud_indicators={
                        'anthropic_violations': len(violations),
                        'risk_indicators': analysis_result.get('risk_indicators', []),
                        'claude_summary': analysis_result.get('summary', ''),
                        'token_usage': analysis_result.get('usage', {})
                    },
                    cross_reference_issues=[],
                    revenue_anomalies=[],
                    benford_analysis={},
                    narrative_consistency=1.0 if len(violations) == 0 else 0.5,
                    integrity_hash=""
                )
                
                logger.info(f"[Anthropic Analyzer] ✓ Detected {len(violations)} violations using Claude")
                return analysis
            
            else:
                logger.warning("[Anthropic Analyzer] Claude analysis failed, falling back to manual analyzer")
                return await self.manual_analyzer.analyze_filing(
                    cik=cik,
                    accession_number=accession_number,
                    filing_type=filing_type,
                    document_url=document_url,
                    viewer_url=viewer_url
                )
        
        except Exception as e:
            logger.error(f"[Anthropic Analyzer] Error during analysis: {e}, falling back to manual")
            return await self.manual_analyzer.analyze_filing(
                cik=cik,
                accession_number=accession_number,
                filing_type=filing_type,
                document_url=document_url,
                viewer_url=viewer_url
            )

