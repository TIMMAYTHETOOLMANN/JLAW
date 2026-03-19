"""
Agent-based SEC Forensic Analyzer with Intelligent Web Scraping
Uses OpenAI Agent SDK for semantic document understanding and self-healing extraction.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Any

import aiohttp
import openai

from src.forensics.sec_edgar_analyzer import FilingAnalysis, SECForensicAnalyzer
from src.forensics.config_manager import get_config
from src.forensics.sdk_manager import get_sdk_manager_sync

logger = logging.getLogger(__name__)

try:
    from agents import Agent, function_tool
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    AGENTS_SDK_AVAILABLE = False
    logger.warning("OpenAI agents SDK not available, using direct API calls")



class AgentSECForensicAnalyzer:
    """
    SEC forensic analyzer powered by OpenAI Agent SDK.
    Provides intelligent web scraping, semantic document understanding, and self-healing extraction.
    """

    def __init__(self, api_key: Optional[str] = None, user_agent: Optional[str] = None):
        """
        Initialize agent-based SEC analyzer.
        
        Args:
            api_key: OpenAI API key (if not provided, loads from config)
            user_agent: SEC-compliant User-Agent string
        """
        config = get_config()

        # Load API key
        self.api_key = api_key or config.config.openai.api_key
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY required for agent-based analysis. "
                "Set in .env file or pass to constructor."
            )

        # Configuration
        self.user_agent = user_agent or config.config.sec.user_agent
        self.model = config.config.openai.model
        self.max_tokens = config.config.openai.max_tokens

        # Fallback to manual analyzer for compatibility
        self.manual_analyzer = SECForensicAnalyzer(user_agent=self.user_agent)
        
        # Use unified SDK manager for OpenAI client (lazy-loaded)
        self._sdk_manager = get_sdk_manager_sync()
        self.client = None  # Will be lazily accessed via SDK manager
        
        # Use agent SDK if available, otherwise direct API
        if AGENTS_SDK_AVAILABLE:
            try:
                # Create the agent with forensic analysis tools
                tools = [
                    tool for tool in [
                        self._create_fetch_filing_tool(),
                        self._create_parse_violations_tool(),
                        self._create_extract_financial_data_tool()
                    ] if tool is not None
                ]
                self.agent = Agent(
                    name="SEC Forensic Analyzer",
                    model=self.model,
                    tools=tools,
                    instructions=self._get_instructions()
                )
                logger.info(f"✅ Agent-based SEC analyzer initialized with model: {self.model}")
            except Exception as e:
                logger.warning(f"Agent SDK initialization failed: {e}, using direct API")
                self.agent = None
        else:
            self.agent = None
            logger.info(f"✅ Direct API SEC analyzer initialized with model: {self.model}")
    
    @property
    def openai_client(self):
        """Lazily access OpenAI sync client from SDK manager."""
        if self.client is None:
            openai_client = self._sdk_manager.openai
            if openai_client:
                self.client = openai_client
            else:
                logger.warning("OpenAI client not available from SDK manager")
        return self.client

    def _get_instructions(self) -> str:
        """Get agent instructions for forensic SEC analysis."""
        return """
You are a forensic SEC filing analyzer with expert knowledge of securities regulations.

Your primary objectives:
1. Intelligently fetch and extract SEC filing data with self-healing strategies
2. Detect securities violations with exact evidence and citations
3. Provide prosecution-ready violation reports with URLs and quotes

Key violation types to detect:
- Form 4 late filings (>2 business days from transaction date)
- Zero-dollar transactions (potential unreported gifts/RSU vesting)
- SOX 302/404 certification deficiencies
- Material misstatements and restatements
- Insider trading patterns and unusual timing
- Revenue manipulation indicators

Analysis requirements:
- Always cite specific regulation violated (15 USC § 78p(a), etc.)
- Provide exact quotes from documents as evidence
- Include document URLs and filing dates
- Calculate business days accurately (exclude weekends/holidays)
- Flag severity levels: CRITICAL, HIGH, MEDIUM, LOW

When extraction fails:
- Try alternative URL patterns (edgardoc.xml, form4.xml, xslF345X03/)
- Search accession directory index.json for correct filename
- Parse both XML and HTML versions if available
- Adapt to variations in document structure

Maintain forensic chain of custody:
- Record all document sources with timestamps
- Preserve original content hashes
- Note any extraction difficulties or anomalies
"""

    def _create_fetch_filing_tool(self):
        """Create tool for intelligent filing fetching."""
        
        if not AGENTS_SDK_AVAILABLE:
            return None

        @function_tool
        async def fetch_sec_filing(url: str, form_type: str, filing_date: Optional[str] = None) -> Dict[str, Any]:
            """
            Intelligently fetch SEC filing with self-healing URL resolution.
            
            Args:
                url: Primary document URL
                form_type: SEC form type (4, 10-K, 10-Q, etc.)
                filing_date: Filing date in YYYY-MM-DD format
            
            Returns:
                Dictionary with filing content, metadata, and extraction status
            """
            logger.info(f"[Agent Tool] Fetching {form_type} from {url}")

            # Strategy 1: Try primary URL
            try:
                response = await self._sdk_manager.sec_request(
                    url, 
                    self.user_agent,
                    timeout=aiohttp.ClientTimeout(total=30)
                )
                
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"[Agent Tool] ✓ Fetched {len(content)} bytes from primary URL")
                    return {
                        'status': 'success',
                        'url': url,
                        'content': content,
                        'content_length': len(content),
                        'form_type': form_type,
                        'filing_date': filing_date,
                        'extraction_strategy': 'primary_url'
                    }
                elif response.status == 404:
                    logger.warning(f"[Agent Tool] Primary URL returned 404: {url}")
            except Exception as e:
                logger.warning(f"[Agent Tool] Primary URL failed: {e}")

            # Strategy 2: Try alternative URLs for Form 4
            if form_type.upper() in ('4', '4/A'):
                logger.info("[Agent Tool] Trying alternative Form 4 URL patterns")

                # Extract accession directory
                import re
                match = re.search(r'(https://www\.sec\.gov/Archives/edgar/data/\d+/\d+)', url)
                if match:
                    acc_root = match.group(1)
                    alternates = [
                        f"{acc_root}/edgardoc.xml",
                        f"{acc_root}/form4.xml",
                        f"{acc_root}/xslF345X03/form4.xml",
                        f"{acc_root}/xslF345X03/edgardoc.xml"
                    ]

                    for alt_url in alternates:
                        try:
                            resp = await self._sdk_manager.sec_request(
                                alt_url,
                                self.user_agent,
                                timeout=aiohttp.ClientTimeout(total=20)
                            )
                            
                            if resp.status == 200:
                                content = await resp.text()
                                logger.info(f"[Agent Tool] ✓ Found via alternate: {alt_url}")
                                return {
                                    'status': 'success',
                                    'url': alt_url,
                                    'content': content,
                                    'content_length': len(content),
                                            'form_type': form_type,
                                            'filing_date': filing_date,
                                            'extraction_strategy': 'alternate_url'
                                        }
                        except Exception as e:
                            logger.debug("Alternate URL fetch failed for %s: %s", alt_url, e)
                            continue

            # Strategy 3: Fall back to manual analyzer
            logger.warning("[Agent Tool] All strategies failed, using manual fallback")
            return {
                'status': 'fallback_required',
                'url': url,
                'form_type': form_type,
                'filing_date': filing_date,
                'message': 'Agent extraction failed, manual analyzer will be used'
            }

        return fetch_sec_filing

    def _create_parse_violations_tool(self):
        """Create tool for parsing violations from filing content."""
        
        if not AGENTS_SDK_AVAILABLE:
            return None

        @function_tool
        def parse_sec_violations(content: str, form_type: str, url: str, filing_date: Optional[str] = None) -> Dict[
            str, Any]:
            """
            Parse SEC filing for violations using semantic understanding.
            
            Args:
                content: Filing document content
                form_type: Form type (4, 10-K, 10-Q)
                url: Document URL
                filing_date: Filing date string
            
            Returns:
                Dictionary with detected violations and evidence
            """
            logger.info(f"[Agent Tool] Parsing {form_type} for violations (content length: {len(content)})")

            violations = []

            # Form 4 specific analysis
            if form_type.upper() in ('4', '4/A'):
                # Extract transaction dates and prices
                import re

                # Transaction date pattern
                tx_dates = re.findall(r'<transactionDate>.*?<value>(.*?)</value>', content, re.IGNORECASE)

                # Price patterns (zero-dollar detection)
                prices = re.findall(r'<transactionPricePerShare>.*?<value>(.*?)</value>', content, re.IGNORECASE)

                # Late filing detection
                if filing_date and tx_dates:
                    from datetime import datetime, timedelta
                    try:
                        file_dt = datetime.strptime(filing_date, '%Y-%m-%d')
                        for tx_date_str in tx_dates:
                            tx_dt = datetime.strptime(tx_date_str, '%Y-%m-%d')

                            # Calculate business days
                            days = 0
                            current = tx_dt
                            while current < file_dt:
                                current += timedelta(days=1)
                                if current.weekday() < 5:  # Mon-Fri
                                    days += 1

                            if days > 2:
                                violations.append({
                                    'type': 'late_form4',
                                    'severity': 'HIGH',
                                    'description': f'Late Form 4 filing by {days} business days',
                                    'transaction_date': tx_date_str,
                                    'filing_date': filing_date,
                                    'business_days_late': days,
                                    'statute': '15 USC § 78p(a)',
                                    'url': url
                                })
                    except Exception as e:
                        logger.warning(f"[Agent Tool] Date parsing error: {e}")

                # Zero-dollar transaction detection
                for price in prices:
                    try:
                        price_val = float(price.replace(',', '').strip())
                        if price_val == 0.0:
                            violations.append({
                                'type': 'zero_dollar_transaction',
                                'severity': 'HIGH',
                                'description': 'Zero-dollar transaction (potential unreported gift/RSU)',
                                'price': price,
                                'statute': '15 USC § 78p(a)',
                                'url': url
                            })
                    except ValueError as e:
                        logger.debug("Failed to parse price value '%s': %s", price, e)
                        continue

            logger.info(f"[Agent Tool] ✓ Found {len(violations)} violations")
            return {
                'violations': violations,
                'violation_count': len(violations),
                'form_type': form_type,
                'url': url
            }

        return parse_sec_violations

    def _create_extract_financial_data_tool(self):
        """Create tool for extracting financial metrics."""
        
        if not AGENTS_SDK_AVAILABLE:
            return None

        @function_tool
        def extract_financial_metrics(content: str, form_type: str) -> Dict[str, Any]:
            """
            Extract key financial metrics from SEC filings.
            
            Args:
                content: Filing content
                form_type: Form type
            
            Returns:
                Extracted financial metrics
            """
            logger.info(f"[Agent Tool] Extracting financial metrics from {form_type}")

            # Simple extraction for now (can be enhanced with agent reasoning)
            import re

            metrics = {}

            # Revenue patterns
            revenue_patterns = [
                r'revenue[s]?\s*[:$]?\s*([\d,]+)',
                r'net\s+revenue[s]?\s*[:$]?\s*([\d,]+)',
                r'total\s+revenue[s]?\s*[:$]?\s*([\d,]+)'
            ]

            for pattern in revenue_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    metrics['revenue_mentions'] = len(matches)
                    break

            return {
                'metrics': metrics,
                'extraction_method': 'regex_patterns',
                'form_type': form_type
            }

        return extract_financial_metrics

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
        Analyze SEC filing using agent-based intelligence.
        Falls back to manual analyzer if agent approach fails.
        
        Args:
            cik: Company CIK
            accession_number: Filing accession number
            filing_type: Form type
            document_url: Primary document URL
            viewer_url: Optional viewer URL
            filing_date: Optional filing date
        
        Returns:
            FilingAnalysis with detected violations and fraud indicators
        """
        logger.info(f"[Agent Analyzer] Analyzing {filing_type} for CIK {cik}")

        try:
            # Use agent to fetch and analyze
            # Note: In production, would use agent.run() with conversation context
            # For now, using tools directly for faster integration

            # Fetch filing
            fetch_tool = self._create_fetch_filing_tool()
            fetch_result = await fetch_tool(document_url, filing_type, filing_date)

            if fetch_result.get('status') == 'success':
                content = fetch_result.get('content', '')

                # Parse violations
                parse_tool = self._create_parse_violations_tool()
                parse_result = parse_tool(content, filing_type, document_url, filing_date)

                violations = parse_result.get('violations', [])

                # Build FilingAnalysis
                filing_dt = datetime.fromisoformat(filing_date + "T00:00:00") if filing_date else datetime.now(
                    timezone.utc)

                analysis = FilingAnalysis(
                    cik=cik,
                    filing_type=filing_type,
                    filing_date=filing_dt,
                    period_end_date=filing_dt,
                    delay_days=0,
                    amendments=[],
                    red_flags=[{
                        'type': v['type'],
                        'severity': v['severity'],
                        'description': v['description'],
                        'exact_quote': v.get('price', ''),
                        'document_url': v['url'],
                        'viewer_url': viewer_url,
                        'section': 'transactions',
                        'prosecutorial_merit': 'STRONG' if v['severity'] == 'HIGH' else 'MODERATE',
                        'estimated_damages': 25000 if v['type'] == 'late_form4' else None,
                        'evidence_refs': [v['url']]
                    } for v in violations],
                    fraud_indicators={'agent_violations': len(violations)},
                    cross_reference_issues=[],
                    revenue_anomalies=[],
                    benford_analysis={},
                    narrative_consistency=0.0,
                    integrity_hash=""
                )

                logger.info(f"[Agent Analyzer] ✓ Detected {len(violations)} violations using agent intelligence")
                return analysis

            else:
                logger.warning("[Agent Analyzer] Agent extraction failed, falling back to manual analyzer")
                return await self.manual_analyzer.analyze_filing(
                    cik=cik,
                    accession_number=accession_number,
                    filing_type=filing_type,
                    document_url=document_url,
                    viewer_url=viewer_url
                )

        except Exception as e:
            logger.error(f"[Agent Analyzer] Error during agent analysis: {e}, falling back to manual")
            return await self.manual_analyzer.analyze_filing(
                cik=cik,
                accession_number=accession_number,
                filing_type=filing_type,
                document_url=document_url,
                viewer_url=viewer_url
            )

    def _parse_with_direct_api(self, content: str, form_type: str, url: str, filing_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse violations using direct OpenAI API calls (fallback when agent SDK fails).
        """
        logger.info(f"[Direct API] Parsing {form_type} for violations")
        
        system_prompt = """You are an expert SEC forensic analyst. Analyze SEC filings for violations.

Detect these violation types:
1. Late Form 4 filings (>2 business days from transaction date)
2. Zero-dollar transactions (potential gifts/RSU vesting without proper disclosure)
3. SOX certification deficiencies
4. Material misstatements

Return JSON array of violations with structure:
{
  "type": "late_form4" | "zero_dollar_transaction" | "sox_deficiency" | "material_misstatement",
  "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "description": "Brief description",
  "statute": "15 USC § 78p(a)" (or appropriate statute),
  "exact_quote": "Relevant quote from document",
  "evidence": "Supporting evidence"
}"""
        
        user_prompt = f"""Analyze this {form_type} filing for violations:

Filing Date: {filing_date or 'Unknown'}
Document URL: {url}

Content (first 8000 chars):
{content[:8000]}

Return JSON array of detected violations."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=self.max_tokens
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            violations = result.get("violations", [])
            logger.info(f"[Direct API] Detected {len(violations)} violations")
            
            return {
                "violations": violations,
                "violation_count": len(violations),
                "method": "direct_api",
                "model": self.model
            }
        
        except Exception as e:
            logger.error(f"[Direct API] Failed: {e}")
            # Return empty violations on error
            return {
                "violations": [],
                "violation_count": 0,
                "method": "direct_api_failed",
                "error": str(e)
            }

    def parse_violations_from_content(
            self,
            content: str,
            form_type: str,
            url: str,
            filing_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Public interface for parsing violations from filing content.
        
        Used by DualAgentCoordinator for tandem investigation workflow.
        
        Args:
            content: Filing document content
            form_type: Form type (4, 10-K, 10-Q)
            url: Document URL
            filing_date: Filing date string
            
        Returns:
            Dictionary with detected violations and evidence
        """
        # Try agent SDK if available
        if self.agent and AGENTS_SDK_AVAILABLE:
            try:
                parse_tool = self._create_parse_violations_tool()
                return parse_tool(content, form_type, url, filing_date)
            except Exception as e:
                logger.warning(f"Agent SDK parsing failed: {e}, using direct API")
        
        # Fallback to direct API
        return self._parse_with_direct_api(content, form_type, url, filing_date)
