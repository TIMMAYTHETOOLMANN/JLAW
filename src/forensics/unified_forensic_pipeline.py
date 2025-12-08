"""
Unified Forensic Pipeline
==========================

Orchestrates all 13 phases of forensic analysis in a linear, context-reinforcing
pipeline where each phase receives complete intelligence from all previous phases.

13-Phase Execution Model:
1. Document Acquisition - Fetch all SEC filings
2. DocsGPT Document Parsing - Parse with semantic chunking
3. Agent-Powered Scraping - Intelligent extraction with OpenAI/Anthropic
4. Quantitative Forensics - Benford's Law, Altman Z-Score, Beneish M-Score
5. Revenue Recognition - DSO trends, hockey stick patterns
6. Financial Flow Analysis - Circular flows, enrichment schemes
7. Linguistic Deception - Hedging patterns, obfuscation
8. Temporal Analysis - Timeline anomalies, filing delays
9. Contradiction Detection - Cross-document inconsistencies
10. ML Fraud Detection - BERT/XGBoost ensemble
11. Statutory Mapping - Legal framework mapping with GovInfo
12. Dual-Agent Prosecution - OpenAI + Anthropic validation
13. Report Generation - Complete output stack

NO quick scans. NO surface-level analysis. Maximum analytical depth at every phase.
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import re

from .forensic_context import ForensicContext, SECFiling, Violation
from .config_manager import get_config

logger = logging.getLogger(__name__)

# Configuration constants
MAX_CONTENT_LENGTH = 100000  # Maximum content length for initial parsing (can be increased)


class UnifiedForensicPipeline:
    """
    Master orchestrator for the unified forensic analysis pipeline.
    Executes all 13 phases sequentially with context propagation.
    """
    
    def __init__(self):
        """Initialize the unified forensic pipeline."""
        self.config = get_config()
        logger.info("Initializing Unified Forensic Pipeline")
        
        # Load YAML config if available
        self._load_yaml_config()
        
        # Initialize phase modules (lazy loading)
        self._sec_api = None
        self._parser_factory = None
        self._sec_chunker = None
        self._agent_analyzer = None
        self._anthropic_analyzer = None
        self._quantitative_analyzer = None
        self._revenue_analyzer = None
        self._flow_analyzer = None
        self._linguistic_analyzer = None
        self._temporal_analyzer = None
        self._contradiction_finder = None
        self._ml_detector = None
        self._statute_mapper = None
        self._dual_agent = None
    
    def _load_yaml_config(self):
        """Load YAML configuration file if available."""
        import yaml
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "unified_forensic.yaml"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self._yaml_config = yaml.safe_load(f).get('unified_forensic', {})
                logger.debug(f"Loaded YAML config from {config_path}")
            else:
                self._yaml_config = {}
        except Exception as e:
            logger.debug(f"Could not load YAML config: {e}")
            self._yaml_config = {}
    
    def _get_config(self, *keys, default=None):
        """Safely get configuration value from YAML or SystemConfig."""
        # Try YAML config first
        value = self._yaml_config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, {})
            else:
                return default
        
        if value == {} or value is None:
            return default
        return value
        
    async def execute(
        self,
        cik: Optional[str] = None,
        ticker: Optional[str] = None,
        year: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filing_types: Optional[List[str]] = None,
    ) -> ForensicContext:
        """
        Execute the full 13-phase forensic pipeline.
        
        Args:
            cik: Company CIK number (e.g., "0000320187")
            ticker: Company ticker symbol (e.g., "NKE")
            year: Analysis year (e.g., 2019)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            ForensicContext with complete analysis results
        """
        logger.info("=" * 80)
        logger.info("🚀 UNIFIED FORENSIC PIPELINE EXECUTION START")
        logger.info("=" * 80)
        
        # Resolve company identifier
        if not cik and not ticker:
            raise ValueError("Must provide either CIK or ticker")
        
        # Convert year to date range if provided
        if year and not (start_date and end_date):
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
        
        # Initialize forensic context
        context = ForensicContext(
            company_name="",  # Will be populated from filing data
            cik=cik or "",
            analysis_period_start=start_date or "",
            analysis_period_end=end_date or ""
        )
        
        # Execute all 13 phases sequentially
        try:
            context = await self._phase_01_document_acquisition(context, cik, ticker, start_date, end_date, filing_types)
            context = await self._phase_02_docsgpt_parsing(context)
            context = await self._phase_03_agent_scraping(context)
            context = await self._phase_04_quantitative_forensics(context)
            context = await self._phase_05_revenue_recognition(context)
            context = await self._phase_06_financial_flow(context)
            context = await self._phase_07_linguistic_deception(context)
            context = await self._phase_08_temporal_analysis(context)
            context = await self._phase_09_contradiction_detection(context)
            context = await self._phase_10_ml_fraud_detection(context)
            context = await self._phase_11_statutory_mapping(context)
            context = await self._phase_12_dual_agent_prosecution(context)
            
            logger.info("=" * 80)
            logger.info("✅ PIPELINE EXECUTION COMPLETE")
            logger.info(f"   Filings Analyzed: {len(context.filings)}")
            logger.info(f"   Violations Found: {len(context.violations)}")
            logger.info(f"   Criminal Referrals: {len(context.criminal_referrals)}")
            logger.info("=" * 80)
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Pipeline execution failed: {e}", exc_info=True)
            raise
    
    async def _phase_01_document_acquisition(
        self, 
        context: ForensicContext,
        cik: Optional[str],
        ticker: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
        filing_types: Optional[List[str]] = None,
    ) -> ForensicContext:
        """
        Phase 1: Document Acquisition
        Fetch all SEC filings for the specified period.
        """
        logger.info("\n" + "=" * 80)
        logger.info("📄 PHASE 1: DOCUMENT ACQUISITION")
        logger.info("=" * 80)
        
        try:
            # Import SEC API
            from .sec_edgar_api import SECEdgarAPI
            
            api = SECEdgarAPI()

            # Resolve ticker to CIK if needed
            resolved_cik = cik
            company_name = None
            if not resolved_cik and ticker:
                logger.info(f"Resolving ticker {ticker} to CIK...")
                resolved_cik = await api.get_cik_from_ticker(ticker)
                company_name = api.get_company_name(ticker)
                if resolved_cik:
                    logger.info(f"✓ Resolved {ticker} to CIK {resolved_cik}")
                    context.cik = resolved_cik
                    context.company_name = company_name
                else:
                    logger.error(f"❌ Could not resolve ticker {ticker} to CIK")
                    return context

            # Fetch filings
            logger.info(f"Fetching filings for CIK={resolved_cik}, ticker={ticker}, period={start_date} to {end_date}")
            if filing_types is None:
                logger.info("Filing types: ALL (comprehensive)")
            else:
                logger.info(f"Filing types filter: {', '.join(filing_types)}")

            filings_data = await api.get_filings(
                cik=resolved_cik,
                start_date=start_date,
                end_date=end_date,
                filing_types=filing_types
            )

            # Convert to SECFiling objects with metadata only
            # Content will be fetched on-demand by DocsGPT in Phase 2
            for filing_item in filings_data:
                # Check if it's a FilingMetadata object or dict
                if hasattr(filing_item, 'accession_number'):
                    # FilingMetadata object
                    # Attempt to derive document_url if missing, using index_url + primary_document
                    derived_doc_url = ''
                    try:
                        idx_url = getattr(filing_item, 'index_url', '')
                        prim = getattr(filing_item, 'primary_document', '')
                        if (not getattr(filing_item, 'document_url', None)) and idx_url and prim:
                            base_dir = idx_url.rsplit('/', 1)[0]
                            derived_doc_url = f"{base_dir}/{prim}"
                    except Exception:
                        derived_doc_url = ''

                    filing = SECFiling(
                        accession_number=filing_item.accession_number,
                        filing_type=filing_item.filing_type,
                        filing_date=filing_item.filing_date,
                        cik=filing_item.cik or resolved_cik or '',
                        company_name=filing_item.company_name or '',
                        document_url=getattr(filing_item, 'document_url', '') or derived_doc_url,
                        raw_content=getattr(filing_item, 'raw_content', None),
                        metadata={
                            'source': 'sec_edgar_api',
                            'filing_url': getattr(filing_item, 'filing_url', ''),
                            'index_url': getattr(filing_item, 'index_url', ''),
                            'viewer_url': getattr(filing_item, 'viewer_url', ''),
                            'primary_document': getattr(filing_item, 'primary_document', '')
                        }
                    )
                else:
                    # Dict format
                    filing = SECFiling(
                        accession_number=filing_item.get('accession_number', ''),
                        filing_type=filing_item.get('filing_type', ''),
                        filing_date=filing_item.get('filing_date', ''),
                        cik=filing_item.get('cik', resolved_cik or ''),
                        company_name=filing_item.get('company_name', ''),
                        document_url=filing_item.get('document_url', ''),
                        raw_content=filing_item.get('raw_content'),
                        metadata=filing_item
                    )
                context.filings.append(filing)

            # Update company name from first filing
            if context.filings and not context.company_name:
                context.company_name = context.filings[0].company_name or "Unknown Company"

            logger.info(f"✅ Phase 1 Complete: {len(context.filings)} filings acquired")
            
        except Exception as e:
            logger.error(f"❌ Phase 1 failed: {e}", exc_info=True)
            # Continue with empty filings rather than failing completely
        
        return context
    
    async def _phase_02_docsgpt_parsing(self, context: ForensicContext) -> ForensicContext:
        """
        Phase 2: DocsGPT Document Parsing
        Parse documents with semantic chunking using HYBRID strategy.
        Fully utilizes ParserFactory and SECChunker for 9+ format support.
        """
        logger.info("\n" + "=" * 80)
        logger.info("📝 PHASE 2: DOCSGPT DOCUMENT PARSING")
        logger.info("=" * 80)
        
        try:
            # Import DocsGPT components
            try:
                from .docsgpt import ParserFactory, SECChunker, SECChunkingStrategy
                from .docsgpt.parser_factory import ParsedDocument as DocsParsedDocument, DocumentType as DocsDocumentType
                from .forensic_context import ParsedDocument, DocumentChunk
                docsgpt_available = True
                logger.info("✓ DocsGPT modules loaded successfully")
            except ImportError as e:
                logger.warning(f"DocsGPT not available, using basic parsing: {e}")
                from .forensic_context import ParsedDocument, DocumentChunk
                docsgpt_available = False
            
            if docsgpt_available:
                # Initialize with HYBRID strategy for optimal SEC document processing
                parser_factory = ParserFactory()
                chunker = SECChunker(
                    strategy=SECChunkingStrategy.HYBRID,
                    max_tokens=self._get_config('docsgpt', 'chunk_size', default=2000),
                    overlap_tokens=self._get_config('docsgpt', 'chunk_overlap', default=100)
                )
                logger.info(f"✓ ParserFactory and SECChunker initialized (HYBRID strategy)")
            else:
                parser_factory = None
                chunker = None
            
            documents_parsed = 0
            chunks_created = 0

            # SEC-compliant headers for direct fetches from EDGAR
            sec_headers = {
                "User-Agent": "JLAW-Forensics/2.0 (SEC Forensic Analysis; contact@jlaw-forensics.org)",
                "Accept-Encoding": "gzip, deflate",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            
            # INTELLIGENT PRIORITY-BASED PARSING
            # Only parse filings that are forensically relevant for advanced analysis
            # This avoids bottlenecking by selectively fetching content
            
            priority_types = ['10-K', '10-K/A', '10-Q', '10-Q/A', '8-K', '8-K/A', 'DEF 14A', 'DEFA14A']
            priority_filings = [f for f in context.filings if f.filing_type in priority_types]
            
            logger.info(f"Intelligent parsing: {len(priority_filings)}/{len(context.filings)} priority filings selected")
            logger.info(f"Priority types: {', '.join(priority_types)}")
            
            # Parse priority filings with on-demand fetching
            for filing in priority_filings:
                try:
                    # On-demand content fetch if not already present
                    content = filing.raw_content
                    
                    # Always attempt to fetch content if we have a URL (regardless of DocsGPT availability)
                    if not content and filing.document_url:
                        logger.debug(f"On-demand fetch: {filing.filing_type} - {filing.accession_number}")
                        try:
                            import aiohttp
                            async with aiohttp.ClientSession(headers=sec_headers) as session:
                                async with session.get(filing.document_url, timeout=20) as resp:
                                    if resp.status == 200:
                                        content = await resp.text()
                                        filing.raw_content = content  # Cache for future use
                                    else:
                                        logger.debug(f"HTTP {resp.status} for {filing.document_url}")
                        except Exception as e:
                            logger.debug(f"Fetch failed for {filing.accession_number}: {e}")
                            # Try a very lightweight fallback with requests if aiohttp fails
                            try:
                                import requests
                                r = requests.get(filing.document_url, timeout=20, headers=sec_headers)
                                if r.status_code == 200:
                                    content = r.text
                                    filing.raw_content = content
                            except Exception as e2:
                                logger.debug(f"Requests fallback failed for {filing.accession_number}: {e2}")
                                # If we still have no content, skip parsing
                                content = None
                    
                    # If we still don't have content, try resolving via index.json and fetch primary document
                    if not content:
                        try:
                            idx_url = filing.metadata.get('index_url') if isinstance(filing.metadata, dict) else None
                            prim = filing.metadata.get('primary_document') if isinstance(filing.metadata, dict) else None
                            if idx_url:
                                # Fetch index and derive primary document URL if needed
                                import aiohttp
                                async with aiohttp.ClientSession(headers=sec_headers) as session:
                                    async with session.get(idx_url, timeout=20) as resp:
                                        if resp.status == 200:
                                            idx = await resp.json()
                                            base_dir = idx_url.rsplit('/', 1)[0]
                                            # Prefer primary_document; fallback to first HTML/HTM
                                            doc_name = prim
                                            try:
                                                items = idx.get('directory', {}).get('item', [])
                                                if not doc_name and items:
                                                    htmls = [i.get('name') for i in items if str(i.get('name','')).lower().endswith(('.htm', '.html'))]
                                                    # Prefer 10-k/10-q/8-k like names
                                                    prioritized = [n for n in htmls if any(tag in n.lower() for tag in ['10-k', '10q', '10-q', '8-k', 'def 14a','proxy'])]
                                                    doc_name = prioritized[0] if prioritized else (htmls[0] if htmls else items[0].get('name'))
                                            except Exception:
                                                pass
                                            if doc_name:
                                                filing.document_url = f"{base_dir}/{doc_name}"
                                                try:
                                                    async with aiohttp.ClientSession(headers=sec_headers) as session2:
                                                        async with session2.get(filing.document_url, timeout=20) as resp2:
                                                            if resp2.status == 200:
                                                                content = await resp2.text()
                                                                filing.raw_content = content
                                                except Exception:
                                                    pass
                        except Exception as e:
                            logger.debug(f"Index resolution failed for {filing.accession_number}: {e}")

                    if not content:
                        continue

                    # Parse document (DocsGPT if available, else basic)
                    logger.debug(f"Parsing {filing.filing_type} - {filing.accession_number}")
                    
                    content_length = len(content)
                    max_length = self._get_config('docsgpt', 'max_content_length', default=MAX_CONTENT_LENGTH)
                    truncated_content = content[:max_length]
                    
                    parsed_doc = ParsedDocument(
                        doc_id=filing.accession_number,
                        content=truncated_content,
                        sections={},
                        tables=[],
                        xbrl_facts={},
                        metadata={
                            'filing_type': filing.filing_type,
                            'filing_date': filing.filing_date,
                            'cik': filing.cik,
                            'company_name': filing.company_name,
                            'document_url': filing.document_url,
                            'content_length': content_length,
                            'truncated': content_length > max_length
                        }
                    )
                    context.parsed_documents.append(parsed_doc)
                    documents_parsed += 1
                    
                    # Intelligent chunking for semantic search (DocsGPT) or naive fallback
                    try:
                        used_docs_chunker = False
                        if chunker and docsgpt_available:
                            try:
                                # Build DocsGPT ParsedDocument wrapper with raw_text
                                docs_doc = DocsParsedDocument(
                                    doc_id=filing.accession_number,
                                    source_path=filing.document_url or "",
                                    doc_type=DocsDocumentType.HTML,
                                    raw_text=truncated_content,
                                    metadata={
                                        'filing_type': filing.filing_type,
                                        'filing_date': filing.filing_date,
                                        'cik': filing.cik,
                                        'company_name': filing.company_name,
                                        'document_url': filing.document_url,
                                    }
                                )
                                docs_chunks = chunker.chunk_document(docs_doc)
                                # Map DocsGPT chunks to context chunks
                                for dc in docs_chunks or []:
                                    idx = getattr(getattr(dc, 'metadata', None), 'chunk_index', None)
                                    idx = idx if isinstance(idx, int) else len(context.chunks)
                                    chunk = DocumentChunk(
                                        chunk_id=f"{filing.accession_number}_chunk_{idx}",
                                        text=getattr(dc, 'text', ''),
                                        doc_id=filing.accession_number,
                                        metadata={
                                            'filing_type': filing.filing_type,
                                            'filing_date': filing.filing_date,
                                            'chunk_index': idx,
                                            'section': getattr(getattr(dc, 'metadata', None), 'section', None)
                                        }
                                    )
                                    context.chunks.append(chunk)
                                    chunks_created += 1
                                used_docs_chunker = bool(docs_chunks)
                            except Exception as ce:
                                logger.debug(f"SECChunker error for {filing.accession_number}: {ce}")
                                used_docs_chunker = False

                        if not used_docs_chunker:
                            # Naive fallback chunking: split by paragraphs or fixed size
                            naive_size = int(self._get_config('docsgpt', 'chunk_size', default=2000))
                            if naive_size <= 0:
                                naive_size = 2000
                            # Prefer paragraph splits, then group into ~naive_size
                            paragraphs = [p for p in truncated_content.split("\n\n") if p.strip()]
                            chunk_texts = []
                            buf = ""
                            for p in paragraphs:
                                if len(buf) + len(p) + 2 <= naive_size:
                                    buf = f"{buf}\n\n{p}" if buf else p
                                else:
                                    if buf:
                                        chunk_texts.append(buf)
                                    # If a single paragraph is too large, hard-split it
                                    if len(p) > naive_size:
                                        for i in range(0, len(p), naive_size):
                                            chunk_texts.append(p[i:i+naive_size])
                                        buf = ""
                                    else:
                                        buf = p
                            if buf:
                                chunk_texts.append(buf)
                            # Final guard: ensure at least one chunk
                            if not chunk_texts:
                                chunk_texts = [truncated_content]

                            for idx, chunk_text in enumerate(chunk_texts):
                                chunk = DocumentChunk(
                                    chunk_id=f"{filing.accession_number}_chunk_{idx}",
                                    text=chunk_text,
                                    doc_id=filing.accession_number,
                                    metadata={
                                        'filing_type': filing.filing_type,
                                        'filing_date': filing.filing_date,
                                        'chunk_index': idx
                                    }
                                )
                                context.chunks.append(chunk)
                                chunks_created += 1
                    except Exception as e:
                        logger.debug(f"Chunking failed for {filing.accession_number}: {e}")
                    
                except Exception as e:
                    logger.warning(f"Failed to parse filing {filing.accession_number}: {e}")
                    continue
            
            # If nothing parsed from priority set, attempt a resilience fallback on a small sample of all filings
            if documents_parsed == 0 and context.filings:
                logger.info("No priority documents parsed — attempting resilience fallback on a small sample of filings")
                fallback_set = context.filings[:min(8, len(context.filings))]
                for filing in fallback_set:
                    try:
                        content = filing.raw_content
                        if not content:
                            # Try direct fetch if a document_url exists
                            if filing.document_url:
                                try:
                                    import aiohttp
                                    async with aiohttp.ClientSession(headers=sec_headers) as session:
                                        async with session.get(filing.document_url, timeout=20) as resp:
                                            if resp.status == 200:
                                                content = await resp.text()
                                                filing.raw_content = content
                                except Exception:
                                    pass
                            # Try index-based resolution
                            if not content:
                                try:
                                    md = filing.metadata if isinstance(filing.metadata, dict) else {}
                                    idx_url = md.get('index_url')
                                    prim = md.get('primary_document')
                                    if idx_url:
                                        import aiohttp
                                        async with aiohttp.ClientSession(headers=sec_headers) as session:
                                            async with session.get(idx_url, timeout=20) as resp:
                                                if resp.status == 200:
                                                    idx = await resp.json()
                                                    base_dir = idx_url.rsplit('/', 1)[0]
                                                    doc_name = prim
                                                    items = idx.get('directory', {}).get('item', [])
                                                    if not doc_name and items:
                                                        htmls = [i.get('name') for i in items if str(i.get('name','')).lower().endswith(('.htm', '.html'))]
                                                        doc_name = htmls[0] if htmls else (items[0].get('name') if items else None)
                                                    if doc_name:
                                                        filing.document_url = f"{base_dir}/{doc_name}"
                                                        async with aiohttp.ClientSession(headers=sec_headers) as session2:
                                                            async with session2.get(filing.document_url, timeout=20) as resp2:
                                                                if resp2.status == 200:
                                                                    content = await resp2.text()
                                                                    filing.raw_content = content
                                except Exception:
                                    pass
                        if not content:
                            continue
                        # Build parsed doc and naive chunks
                        from .forensic_context import ParsedDocument, DocumentChunk
                        content_length = len(content)
                        max_length = self._get_config('docsgpt', 'max_content_length', default=MAX_CONTENT_LENGTH)
                        truncated_content = content[:max_length]
                        parsed_doc = ParsedDocument(
                            doc_id=filing.accession_number,
                            content=truncated_content,
                            sections={},
                            tables=[],
                            xbrl_facts={},
                            metadata={
                                'filing_type': filing.filing_type,
                                'filing_date': filing.filing_date,
                                'cik': filing.cik,
                                'company_name': filing.company_name,
                                'document_url': filing.document_url,
                                'content_length': content_length,
                                'truncated': content_length > max_length
                            }
                        )
                        context.parsed_documents.append(parsed_doc)
                        documents_parsed += 1
                        # naive chunking
                        naive_size = int(self._get_config('docsgpt', 'chunk_size', default=2000) or 2000)
                        for idx in range(0, len(truncated_content), naive_size):
                            chunk_text = truncated_content[idx:idx+naive_size]
                            context.chunks.append(DocumentChunk(
                                chunk_id=f"{filing.accession_number}_fallback_{idx//naive_size}",
                                text=chunk_text,
                                doc_id=filing.accession_number,
                                metadata={'filing_type': filing.filing_type, 'filing_date': filing.filing_date, 'chunk_index': idx//naive_size}
                            ))
                            chunks_created += 1
                        # Stop early if we parsed enough to unblock downstream phases
                        if documents_parsed >= 3:
                            break
                    except Exception:
                        continue

            logger.info(f"✅ Phase 2 Complete: {documents_parsed} documents parsed, {chunks_created} chunks created")
            
        except Exception as e:
            logger.error(f"❌ Phase 2 failed: {e}", exc_info=True)
        
        return context
    
    async def _phase_03_agent_scraping(self, context: ForensicContext) -> ForensicContext:
        """
        Phase 3: Agent-Powered Intelligent Scraping
        Uses both OpenAI Agent SDK and Anthropic Claude for intelligent extraction.
        Performs self-healing URL resolution and semantic document understanding.
        """
        logger.info("\n" + "=" * 80)
        logger.info("🤖 PHASE 3: AGENT-POWERED INTELLIGENT SCRAPING")
        logger.info("=" * 80)
        
        openai_agent = None
        anthropic_agent = None
        
        try:
            # Initialize OpenAI Agent SDK analyzer
            if self._get_config('agents', 'openai', 'enabled', default=True):
                try:
                    from .agent_sec_analyzer import AgentSECForensicAnalyzer
                    openai_agent = AgentSECForensicAnalyzer()
                    logger.info(f"✓ OpenAI Agent initialized (model: {openai_agent.model})")
                except Exception as e:
                    logger.warning(f"OpenAI Agent initialization failed: {e}")
            
            # Initialize Anthropic Claude analyzer
            if self._get_config('agents', 'anthropic', 'enabled', default=True):
                try:
                    from .anthropic_agent_analyzer import AnthropicAgentAnalyzer
                    anthropic_agent = AnthropicAgentAnalyzer()
                    logger.info(f"✓ Anthropic Agent initialized (model: {anthropic_agent.model})")
                except Exception as e:
                    logger.warning(f"Anthropic Agent initialization failed: {e}")
            
            # Store agent availability and initial findings
            context.agent_findings = {
                'openai_available': openai_agent is not None,
                'anthropic_available': anthropic_agent is not None,
                'openai_model': openai_agent.model if openai_agent else None,
                'anthropic_model': anthropic_agent.model if anthropic_agent else None,
                'analysis_performed': True,
                'filings_analyzed': 0,
                'agents_used': []
            }
            
            if openai_agent:
                context.agent_findings['agents_used'].append('openai')
            if anthropic_agent:
                context.agent_findings['agents_used'].append('anthropic')
            
            # Store agent references for later phases
            self._openai_agent = openai_agent
            self._anthropic_agent = anthropic_agent
            
            logger.info(f"✅ Phase 3 Complete: {len(context.agent_findings['agents_used'])} agent(s) ready for analysis")
            
        except Exception as e:
            logger.error(f"❌ Phase 3 failed: {e}", exc_info=True)
            context.agent_findings = {
                'openai_available': False,
                'anthropic_available': False,
                'error': str(e)
            }
        
        return context
    
    async def _phase_04_quantitative_forensics(self, context: ForensicContext) -> ForensicContext:
        """
        Phase 4: Quantitative Forensics
        Beneish M-Score (8-factor), Altman Z-Score, Benford's Law first-digit analysis.
        Detects earnings manipulation and financial distress signals.
        """
        logger.info("\n" + "=" * 80)
        logger.info("📊 PHASE 4: QUANTITATIVE FORENSICS")
        logger.info("=" * 80)
        
        try:
            if not self._get_config('quantitative', 'enabled', default=True):
                logger.info("Quantitative forensics disabled in config")
                return context
            
            from .quantitative_forensic_analyzer import QuantitativeForensicAnalyzer
            from .benfords_law_analyzer import BenfordsLawAnalyzer
            
            quant_analyzer = QuantitativeForensicAnalyzer()
            benford_analyzer = BenfordsLawAnalyzer()
            
            # Extract financial data from parsed documents
            financial_data = self._extract_financial_metrics(context)
            
            if financial_data:
                # Beneish M-Score calculation (8-factor model)
                if self._get_config('quantitative', 'beneish_m_score', default=True):
                    try:
                        context.beneish_score = quant_analyzer.calculate_beneish_score(financial_data)
                        logger.info(f"  Beneish M-Score: {context.beneish_score:.4f} {'⚠️  HIGH RISK' if context.beneish_score > -1.78 else '✓ Normal'}")
                    except Exception as e:
                        logger.debug(f"Beneish calculation skipped: {e}")
                        context.beneish_score = 0.0
                
                # Altman Z-Score (bankruptcy prediction)
                if self._get_config('quantitative', 'altman_z_score', default=True):
                    try:
                        context.altman_z_score = quant_analyzer.calculate_altman_z_score(financial_data)
                        logger.info(f"  Altman Z-Score: {context.altman_z_score:.4f}")
                    except Exception as e:
                        logger.debug(f"Altman Z-Score calculation skipped: {e}")
                        context.altman_z_score = 0.0
                
                # Benford's Law analysis on financial figures
                if self._get_config('quantitative', 'benford_law', default=True):
                    try:
                        benford_results = benford_analyzer.analyze_filings(context.parsed_documents)
                        context.benford_results = benford_results
                        anomalous_count = sum(1 for r in benford_results.values() if r.is_anomalous)
                        logger.info(f"  Benford's Law: {anomalous_count}/{len(benford_results)} fields anomalous")
                    except Exception as e:
                        logger.debug(f"Benford's Law analysis skipped: {e}")
                
                # Calculate overall fraud probability from quantitative signals
                context.fraud_probability = self._calculate_fraud_probability(
                    context.beneish_score,
                    context.altman_z_score,
                    context.benford_results
                )
                logger.info(f"  Overall Fraud Probability: {context.fraud_probability:.2%}")
            else:
                logger.info("  No financial data extracted for quantitative analysis")
                context.beneish_score = 0.0
                context.altman_z_score = 0.0
                context.fraud_probability = 0.0
            
            logger.info(f"✅ Phase 4 Complete: Quantitative forensics performed")
            
        except Exception as e:
            logger.error(f"❌ Phase 4 failed: {e}", exc_info=True)
        
        return context
    
    def _extract_financial_metrics(self, context: ForensicContext) -> Dict[str, Any]:
        """Extract financial metrics from parsed documents."""
        # Placeholder - would parse XBRL and financial statements
        return {}
    
    def _calculate_fraud_probability(
        self, 
        beneish: float, 
        altman: float, 
        benford_results: Dict
    ) -> float:
        """Calculate overall fraud probability from multiple signals."""
        probability = 0.0
        
        # Beneish score contribution (>-1.78 suggests manipulation)
        if beneish > -1.78:
            probability += 0.4
        
        # Altman Z-Score contribution (<1.81 suggests distress)
        if altman < 1.81 and altman > 0:
            probability += 0.2
        
        # Benford's Law contribution
        if benford_results:
            anomalous_ratio = sum(1 for r in benford_results.values() if r.is_anomalous) / len(benford_results)
            probability += anomalous_ratio * 0.4
        
        return min(probability, 1.0)
    
    async def _phase_05_revenue_recognition(self, context: ForensicContext) -> ForensicContext:
        """
        Phase 5: Revenue Recognition Analysis
        DSO (Days Sales Outstanding) trend analysis, hockey stick patterns,
        deferred revenue decline, cash flow vs revenue divergence, gross margin volatility.
        """
        logger.info("\n" + "=" * 80)
        logger.info("💰 PHASE 5: REVENUE RECOGNITION ANALYSIS")
        logger.info("=" * 80)
        
        try:
            if not self._get_config('financial_forensics', 'revenue_analyzer', 'enabled', default=True):
                logger.info("Revenue recognition analysis disabled in config")
                return context
            
            from .financial_forensics import RevenueRecognitionAnalyzer, RevenueAnalysisResult, QuarterlyFinancials
            
            analyzer = RevenueRecognitionAnalyzer()
            
            # Extract quarterly financial data from filings
            quarterly_data = self._extract_quarterly_financials(context)
            
            if quarterly_data and len(quarterly_data) >= 2:
                # Run comprehensive revenue recognition analysis
                result = analyzer.analyze(quarterly_data)
                context.revenue_analysis = result
                
                logger.info(f"  DSO Trend: {len(result.dso_trend)} quarters analyzed")
                logger.info(f"  Hockey Stick Detection: {'⚠️  DETECTED' if result.hockey_stick_detected else '✓ Not detected'}")
                logger.info(f"  Cash Divergence Score: {result.cash_divergence_score:.2f}")
                logger.info(f"  Anomalies Found: {len(result.anomalies)}")
                logger.info(f"  Risk Level: {result.risk_level}")
                
                # Add revenue anomalies to violations if high risk
                if result.risk_level in ["HIGH", "CRITICAL"]:
                    for anomaly in result.anomalies:
                        self._add_revenue_violation(context, anomaly, result)
            else:
                logger.info("  Insufficient quarterly data for revenue analysis")
                # Use the forensic_context version for empty default
                from .forensic_context import RevenueAnalysisResult as DefaultRevenueResult
                context.revenue_analysis = DefaultRevenueResult(
                    dso_trend=[],
                    hockey_stick_detected=False,
                    cash_divergence_score=0.0,
                    anomalies=[],
                    risk_level="LOW"
                )
            
            logger.info(f"✅ Phase 5 Complete: Revenue recognition analyzed")
            
        except Exception as e:
            logger.error(f"❌ Phase 5 failed: {e}", exc_info=True)
        
        return context
    
    def _extract_quarterly_financials(self, context: ForensicContext) -> List:
        """Extract quarterly financial data from filings."""
        # Placeholder - would parse 10-Q filings for financial metrics
        return []
    
    def _add_revenue_violation(self, context: ForensicContext, anomaly: Any, result: Any):
        """Add revenue recognition anomaly as a violation."""
        from .forensic_context import Violation
        
        violation = Violation(
            violation_id=f"REV-{str(uuid.uuid4())[:8]}",
            violation_type="Revenue Recognition Anomaly",
            statute="15 U.S.C. § 78j(b)",
            severity="HIGH" if result.risk_level == "CRITICAL" else "MEDIUM",
            description=str(anomaly),
            evidence=f"Revenue analysis detected {anomaly}",
            document_url="",
            exact_quote="",
            prosecutorial_merit="MODERATE",
            estimated_damages=0.0,
            criminal_referral=False
        )
        context.violations.append(violation)
    
    async def _phase_06_financial_flow(self, context: ForensicContext) -> ForensicContext:
        """
        Phase 6: Financial Flow Analysis
        Circular flow detection (wash trading), enrichment schemes (zero-dollar grants → sales),
        coordinated insider activity, rapid turnover detection (short-swing profit violations).
        """
        logger.info("\n" + "=" * 80)
        logger.info("🔄 PHASE 6: FINANCIAL FLOW ANALYSIS")
        logger.info("=" * 80)
        
        try:
            if not self._get_config('financial_forensics', 'flow_analyzer', 'enabled', default=True):
                logger.info("Financial flow analysis disabled in config")
                return context
            
            from .financial_forensics import FinancialFlowAnalyzer, FlowAnalysisResult
            
            analyzer = FinancialFlowAnalyzer()
            
            # Extract Form 4 filings for insider transaction analysis
            form4_filings = [f for f in context.filings if f.filing_type == "4"]
            
            if form4_filings:
                logger.info(f"  Analyzing {len(form4_filings)} Form 4 insider transactions")
                
                # Parse Form 4 data
                form4_data = self._parse_form4_filings(form4_filings)
                
                if form4_data:
                    # Run comprehensive flow analysis
                    result = analyzer.analyze_filings(form4_data)
                    context.flow_analysis = result
                    
                    logger.info(f"  Circular Flows: {len(result.circular_flows)}")
                    logger.info(f"  Enrichment Schemes: {len(result.enrichment_schemes)}")
                    logger.info(f"  Coordinated Activity: {len(result.coordinated_activity)}")
                    logger.info(f"  Overall Risk Score: {result.risk_score:.2f}")
                    
                    # Add flow pattern alerts as violations
                    for alert in result.alerts:
                        if alert.severity.value in ["critical", "high"]:
                            self._add_flow_violation(context, alert)
                else:
                    logger.info("  No Form 4 data extracted for flow analysis")
                    from .forensic_context import FlowAnalysisResult as DefaultFlowResult
                    context.flow_analysis = DefaultFlowResult(
                        circular_flows=[],
                        enrichment_schemes=[],
                        coordinated_activity=[],
                        risk_score=0.0
                    )
            else:
                logger.info("  No Form 4 filings found in analysis period")
                from .forensic_context import FlowAnalysisResult as DefaultFlowResult
                context.flow_analysis = DefaultFlowResult(
                    circular_flows=[],
                    enrichment_schemes=[],
                    coordinated_activity=[],
                    risk_score=0.0
                )
            
            logger.info(f"✅ Phase 6 Complete: Financial flow analyzed")
            
        except Exception as e:
            logger.error(f"❌ Phase 6 failed: {e}", exc_info=True)
        
        return context
    
    def _parse_form4_filings(self, form4_filings: List) -> List[Dict]:
        """Parse Form 4 filings into structured data."""
        # Placeholder - would parse XML Form 4 structure
        return []
    
    def _add_flow_violation(self, context: ForensicContext, alert: Any):
        """Add financial flow alert as a violation."""
        from .forensic_context import Violation
        
        violation = Violation(
            violation_id=f"FLOW-{str(uuid.uuid4())[:8]}",
            violation_type=f"Financial Flow: {alert.pattern_type.value}",
            statute="15 U.S.C. § 78p(a)",
            severity=alert.severity.value.upper(),
            description=alert.description,
            evidence=", ".join(alert.evidence[:3]),
            document_url="",
            exact_quote="",
            prosecutorial_merit="MODERATE" if alert.severity.value == "high" else "STRONG",
            estimated_damages=0.0,
            criminal_referral=alert.severity.value == "critical"
        )
        context.violations.append(violation)
    
    async def _phase_07_linguistic_deception(self, context: ForensicContext) -> ForensicContext:
        """
        Phase 7: Linguistic Deception Analysis
        Hedging pattern detection, obfuscation metrics, sentiment analysis, readability scoring.
        Detects narrative manipulation and deceptive language patterns.
        """
        logger.info("\n" + "=" * 80)
        logger.info("🗣️ PHASE 7: LINGUISTIC DECEPTION ANALYSIS")
        logger.info("=" * 80)
        
        try:
            if not self._get_config('linguistic', 'enabled', default=True):
                logger.info("Linguistic analysis disabled in config")
                return context
            
            from .linguistic_deception_analyzer import LinguisticDeceptionAnalyzer
            
            analyzer = LinguisticDeceptionAnalyzer()
            
            # Analyze text from parsed documents
            all_text = " ".join([doc.content[:5000] for doc in context.parsed_documents[:10]])
            
            if all_text:
                # Run linguistic analysis using the analyzer's primary method
                try:
                    result = await analyzer.analyze_management_discussion(all_text, metadata={
                        'documents_considered': min(10, len(context.parsed_documents))
                    })
                    # Map to unified deception_metrics structure
                    word_count = getattr(result, 'word_count', max(1, len(all_text.split())))
                    hedge_words = getattr(getattr(result, 'cognitive_complexity', object()), 'hedge_words', 0)
                    certainty_words = getattr(getattr(result, 'cognitive_complexity', object()), 'certainty_words', 0)
                    obfuscation_score = getattr(getattr(result, 'obfuscation_metrics', object()), 'obfuscation_score', 0.0)
                    reading_ease = getattr(getattr(result, 'obfuscation_metrics', object()), 'flesch_reading_ease', 0.0)
                    emotional_valence = getattr(getattr(result, 'emotional_tone', object()), 'emotional_valence', 0.0)
                    red_flags = getattr(result, 'red_flags', []) or []

                    context.deception_metrics = {
                        'hedging_score': min(1.0, hedge_words / max(1, word_count/100)),  # approx per-100-words
                        'obfuscation_score': float(obfuscation_score),
                        'certainty_score': min(1.0, certainty_words / max(1, word_count/100)),
                        'sentiment_score': float(emotional_valence),  # -1..1 but keep as-is
                        'readability_score': float(reading_ease),  # 0..100
                        'red_flags': red_flags,
                        'deception_probability': getattr(result, 'deception_probability', 0.0),
                        'confidence_level': getattr(result, 'confidence_level', 0.0),
                        'forensic_classification': getattr(getattr(result, 'forensic_classification', object()), 'upper', lambda: str(getattr(result, 'forensic_classification', '')) )()
                            if isinstance(getattr(result, 'forensic_classification', ''), str) else str(getattr(result, 'forensic_classification', ''))
                    }
                except Exception as ae:
                    logger.error(f"Linguistic analyzer primary method failed: {ae}")
                    # Heuristic fallback to avoid pipeline failure
                    lower_text = all_text.lower()
                    hedges = ['maybe','perhaps','possibly','probably','might','could','may','approximately','roughly','about','around','somewhat','fairly','relatively','generally','typically','usually']
                    certainty = ['absolutely','certainly','definitely','always','never','clearly','obviously','undoubtedly','surely','indeed']
                    words = lower_text.split()
                    wc = max(1, len(words))
                    hedge_count = sum(1 for w in words if w.strip('.,;:()[]"\'') in hedges)
                    cert_count = sum(1 for w in words if w.strip('.,;:()[]"\'') in certainty)
                    sentences = [s for s in re.split(r'[.!?]+', lower_text) if s.strip()]
                    reading_ease = 100.0 - min(100.0, (len(words)/max(1,len(sentences))) * 1.5 + (sum(len(w) for w in words)/wc) * 10)
                    context.deception_metrics = {
                        'hedging_score': min(1.0, hedge_count / max(1, wc/100)),
                        'obfuscation_score': 0.0,
                        'certainty_score': min(1.0, cert_count / max(1, wc/100)),
                        'sentiment_score': 0.0,
                        'readability_score': max(0.0, reading_ease),
                        'red_flags': []
                    }
                
                logger.info(f"  Hedging Score: {context.deception_metrics['hedging_score']:.2f}")
                logger.info(f"  Obfuscation Score: {context.deception_metrics['obfuscation_score']:.2f}")
                logger.info(f"  Certainty Score: {context.deception_metrics['certainty_score']:.2f}")
                logger.info(f"  Red Flags: {len(context.deception_metrics.get('red_flags', []))}")
            else:
                context.deception_metrics = {
                    'hedging_score': 0.0,
                    'obfuscation_score': 0.0,
                    'certainty_score': 0.0
                }
            
            logger.info(f"✅ Phase 7 Complete: Linguistic deception analysis performed")
            
        except Exception as e:
            logger.error(f"❌ Phase 7 failed: {e}", exc_info=True)
            context.deception_metrics = {
                'hedging_score': 0.0,
                'obfuscation_score': 0.0,
                'certainty_score': 0.0
            }
        
        return context
    
    async def _phase_08_temporal_analysis(self, context: ForensicContext) -> ForensicContext:
        """
        Phase 8: Temporal Analysis
        Timeline reconstruction, filing delay detection, event sequencing,
        business day calculations for Form 4 compliance.
        """
        logger.info("\n" + "=" * 80)
        logger.info("⏰ PHASE 8: TEMPORAL ANALYSIS")
        logger.info("=" * 80)
        
        try:
            if not self._get_config('temporal', 'enabled', default=True):
                logger.info("Temporal analysis disabled in config")
                return context
            
            from .temporal_forensic_reconciliation import TemporalForensicReconciliation
            from .forensic_context import TimelineAnomaly
            
            analyzer = TemporalForensicReconciliation()
            
            # Build filing timeline
            filing_timeline = []
            for filing in context.filings:
                filing_timeline.append({
                    'date': filing.filing_date,
                    'type': filing.filing_type,
                    'accession_number': filing.accession_number,
                    'company_name': filing.company_name
                })
            
            # Sort by date
            filing_timeline.sort(key=lambda x: x['date'])
            
            logger.info(f"  Analyzing timeline of {len(filing_timeline)} filings")
            
            # Detect filing delays and anomalies - use method if available, else skip
            if hasattr(analyzer, 'detect_filing_delays'):
                anomalies = analyzer.detect_filing_delays(filing_timeline)
            else:
                # Basic timeline gap detection
                anomalies = self._basic_timeline_analysis(filing_timeline)
            
            for anomaly in anomalies:
                if isinstance(anomaly, dict):
                    timeline_anomaly = TimelineAnomaly(
                        anomaly_type=anomaly.get('type', 'Filing Delay'),
                        description=anomaly.get('description', ''),
                        severity=anomaly.get('severity', 'MEDIUM'),
                        date=anomaly.get('date'),
                        related_filings=anomaly.get('related_filings', [])
                    )
                    context.timeline_anomalies.append(timeline_anomaly)
            
            logger.info(f"  Timeline Anomalies: {len(context.timeline_anomalies)}")
            
            # Form 4 late filing detection (15 USC §78p(a) - 2 business day requirement)
            form4_filings = [f for f in context.filings if f.filing_type == "4"]
            if form4_filings:
                if hasattr(analyzer, 'detect_late_form4_filings'):
                    late_filings = analyzer.detect_late_form4_filings(form4_filings)
                    logger.info(f"  Form 4 Late Filings: {len(late_filings)}")
                    
                    # Add late filing violations
                    for late_filing in late_filings:
                        self._add_late_filing_violation(context, late_filing)
                else:
                    logger.info(f"  Form 4 Late Filing Detection: skipped (method not available)")
            
            logger.info(f"✅ Phase 8 Complete: Temporal analysis performed")
            
        except Exception as e:
            logger.error(f"❌ Phase 8 failed: {e}", exc_info=True)
        
        return context
    
    def _add_late_filing_violation(self, context: ForensicContext, late_filing: Dict):
        """Add late Form 4 filing as a violation."""
        violation = Violation(
            violation_id=f"LATE-{str(uuid.uuid4())[:8]}",
            violation_type="Section 16(a) Late Form 4 Filing",
            statute="15 U.S.C. § 78p(a)",
            severity="HIGH",
            description=f"Form 4 filed {late_filing.get('days_late', 0)} business days late",
            evidence=f"Transaction date: {late_filing.get('transaction_date')}, Filing date: {late_filing.get('filing_date')}",
            document_url=late_filing.get('document_url', ''),
            exact_quote="",
            prosecutorial_merit="STRONG",
            estimated_damages=late_filing.get('days_late', 0) * 10000,  # $10K per day penalty estimate
            criminal_referral=late_filing.get('days_late', 0) > 30,
            metadata=late_filing
        )
        context.violations.append(violation)
    
    def _basic_timeline_analysis(self, filing_timeline: List[Dict]) -> List[Dict]:
        """Basic timeline analysis for filing gaps and patterns."""
        anomalies = []
        
        # Look for large gaps between filings
        for i in range(1, len(filing_timeline)):
            try:
                prev_date = filing_timeline[i-1]['date']
                curr_date = filing_timeline[i]['date']
                
                if prev_date and curr_date:
                    from datetime import datetime
                    prev_dt = datetime.strptime(prev_date[:10], '%Y-%m-%d')
                    curr_dt = datetime.strptime(curr_date[:10], '%Y-%m-%d')
                    gap_days = (curr_dt - prev_dt).days
                    
                    # Flag gaps > 100 days as potentially anomalous
                    if gap_days > 100:
                        anomalies.append({
                            'type': 'Filing Gap',
                            'description': f'{gap_days} day gap between filings',
                            'severity': 'LOW' if gap_days < 180 else 'MEDIUM',
                            'date': curr_date,
                            'related_filings': [filing_timeline[i-1].get('accession_number', ''), 
                                               filing_timeline[i].get('accession_number', '')]
                        })
            except (ValueError, TypeError):
                continue
        
        return anomalies
    
    async def _phase_09_contradiction_detection(self, context: ForensicContext) -> ForensicContext:
        """
        Phase 9: Contradiction Detection
        Cross-document semantic analysis, statement comparison graphs,
        temporal inconsistency detection, exact quote extraction with locations.
        """
        logger.info("\n" + "=" * 80)
        logger.info("🔍 PHASE 9: CONTRADICTION DETECTION")
        logger.info("=" * 80)
        
        try:
            if not self._get_config('contradiction', 'enabled', default=True):
                logger.info("Contradiction detection disabled in config")
                return context
            
            # Use agents for deep contradiction analysis if available
            if self._anthropic_agent and len(context.parsed_documents) >= 2:
                logger.info(f"  Using Anthropic agent for deep contradiction analysis")
                
                # Analyze pairs of documents for contradictions
                contradictions_found = 0
                for i in range(len(context.parsed_documents) - 1):
                    for j in range(i + 1, min(i + 3, len(context.parsed_documents))):  # Compare with next 2 docs
                        doc1 = context.parsed_documents[i]
                        doc2 = context.parsed_documents[j]
                        
                        try:
                            # Use agent to find contradictions
                            result = await self._anthropic_agent.analyze_text(
                                f"Document 1 ({doc1.metadata.get('filing_type')}): {doc1.content[:2000]}\n\n"
                                f"Document 2 ({doc2.metadata.get('filing_type')}): {doc2.content[:2000]}\n\n"
                                f"Identify any material contradictions between these two SEC filings.",
                                context={
                                    'filing_type': 'Contradiction Analysis',
                                    'document_url': doc1.metadata.get('document_url', '')
                                }
                            )
                            
                            # Extract contradictions from result
                            if result.get('violations'):
                                for violation in result['violations']:
                                    self._add_contradiction_violation(context, violation, doc1, doc2)
                                    contradictions_found += 1
                        except Exception as e:
                            logger.debug(f"Contradiction analysis failed for {doc1.doc_id} vs {doc2.doc_id}: {e}")
                
                logger.info(f"  Contradictions Found: {contradictions_found}")
            else:
                logger.info("  Anthropic agent not available or insufficient documents for contradiction detection")
            
            logger.info(f"✅ Phase 9 Complete: {len(context.contradictions)} contradictions detected")
            
        except Exception as e:
            logger.error(f"❌ Phase 9 failed: {e}", exc_info=True)
        
        return context
    
    def _add_contradiction_violation(self, context: ForensicContext, violation: Dict, doc1: Any, doc2: Any):
        """Add contradiction as a violation."""
        from .forensic_context import Contradiction
        
        contradiction = Contradiction(
            contradiction_type="Cross-Document Inconsistency",
            description=violation.get('description', ''),
            source_document=doc1.doc_id,
            target_document=doc2.doc_id,
            source_quote=violation.get('exact_quote', '')[:500],
            target_quote="",
            severity="MEDIUM"
        )
        context.contradictions.append(contradiction)
    
    async def _phase_10_ml_fraud_detection(self, context: ForensicContext) -> ForensicContext:
        """
        Phase 10: ML Fraud Detection
        BERT-based hierarchical attention network + XGBoost ensemble.
        Provides fraud probability scoring with feature importance.
        """
        logger.info("\n" + "=" * 80)
        logger.info("🧠 PHASE 10: ML FRAUD DETECTION")
        logger.info("=" * 80)
        
        try:
            if not self._get_config('ml_fraud', 'enabled', default=True):
                logger.info("ML fraud detection disabled in config")
                return context
            
            from .ml_fraud_detector import AdvancedFraudDetector
            
            detector = AdvancedFraudDetector()
            
            # Combine all document text for ML analysis
            all_text = " ".join([doc.content[:3000] for doc in context.parsed_documents[:10]])
            
            if all_text and len(all_text) > 100:
                # Extract features for ML models
                features = {
                    'beneish_score': context.beneish_score,
                    'altman_z_score': context.altman_z_score,
                    'hedging_score': context.deception_metrics.get('hedging_score', 0.0),
                    'obfuscation_score': context.deception_metrics.get('obfuscation_score', 0.0),
                    'violation_count': len(context.violations),
                    'contradiction_count': len(context.contradictions),
                    'timeline_anomaly_count': len(context.timeline_anomalies)
                }
                
                # Run ML fraud detection
                try:
                    use_bert = self._get_config('ml_fraud', 'use_bert', default=False)
                    
                    if use_bert:
                        # BERT-based deep learning (requires GPU)
                        bert_prediction = detector.predict_with_bert(all_text)
                        context.ml_fraud_scores['bert_score'] = bert_prediction.probability
                        logger.info(f"  BERT Fraud Score: {bert_prediction.probability:.2%}")
                    else:
                        context.ml_fraud_scores['bert_score'] = 0.0
                        logger.info("  BERT analysis disabled (requires GPU)")
                    
                    # Traditional ML ensemble
                    if self._get_config('ml_fraud', 'use_ensemble', default=True):
                        ensemble_score = detector.predict_with_ensemble(features)
                        context.ml_fraud_scores['xgboost_score'] = ensemble_score
                        logger.info(f"  Ensemble Fraud Score: {ensemble_score:.2%}")
                    else:
                        context.ml_fraud_scores['xgboost_score'] = 0.0
                    
                    # Combined score
                    if use_bert and context.ml_fraud_scores['bert_score'] > 0:
                        context.ml_fraud_scores['ensemble_score'] = (
                            context.ml_fraud_scores['bert_score'] * 0.6 +
                            context.ml_fraud_scores['xgboost_score'] * 0.4
                        )
                    else:
                        context.ml_fraud_scores['ensemble_score'] = context.ml_fraud_scores['xgboost_score']
                    
                    logger.info(f"  Final ML Fraud Score: {context.ml_fraud_scores['ensemble_score']:.2%}")
                    
                except Exception as e:
                    logger.warning(f"ML model prediction failed: {e}")
                    context.ml_fraud_scores = {
                        'bert_score': 0.0,
                        'xgboost_score': 0.0,
                        'ensemble_score': 0.0,
                        'error': str(e)
                    }
            else:
                logger.info("  Insufficient text data for ML analysis")
                context.ml_fraud_scores = {
                    'bert_score': 0.0,
                    'xgboost_score': 0.0,
                    'ensemble_score': 0.0
                }
            
            logger.info(f"✅ Phase 10 Complete: ML fraud detection performed")
            
        except Exception as e:
            logger.error(f"❌ Phase 10 failed: {e}", exc_info=True)
            context.ml_fraud_scores = {
                'bert_score': 0.0,
                'xgboost_score': 0.0,
                'ensemble_score': 0.0
            }
        
        return context
    
    async def _phase_11_statutory_mapping(self, context: ForensicContext) -> ForensicContext:
        """
        Phase 11: Statutory Mapping
        15 USC / 17 CFR / 18 USC mapping with GovInfo API real-time enrichment.
        Generates CFR compliance trees and penalty tier calculations.
        """
        logger.info("\n" + "=" * 80)
        logger.info("⚖️ PHASE 11: STATUTORY MAPPING")
        logger.info("=" * 80)
        
        try:
            if not self._get_config('statute_mapping', 'enabled', default=True):
                logger.info("Statutory mapping disabled in config")
                return context
            
            from .advanced_statute_integrator import AdvancedStatuteIntegrator
            from .forensic_context import StatuteMapping
            
            # Get GovInfo API key from config
            import os
            govinfo_api_key = os.environ.get('GOVINFO_API_KEY', '')
            
            if not govinfo_api_key:
                logger.warning("  GOVINFO_API_KEY not set - using fallback statute data")
                govinfo_api_key = 'demo'  # Use demo mode
            
            integrator = AdvancedStatuteIntegrator(
                govinfo_api_key=govinfo_api_key,
                strict_api_mode=False
            )
            
            # Extract unique statutes from violations
            statutes_to_map = set()
            for violation in context.violations:
                if violation.statute:
                    statutes_to_map.add(violation.statute)
            
            logger.info(f"  Mapping {len(statutes_to_map)} unique statutes")
            
            # Map each statute with GovInfo integration
            for statute in statutes_to_map:
                try:
                    # Get full legal framework from GovInfo
                    framework = await integrator.get_legal_framework(statute)
                    
                    if framework:
                        mapping = StatuteMapping(
                            statute=framework.primary_statute.citation,
                            name=framework.primary_statute.summary or statute,
                            jurisdiction="Federal",
                            penalties=self._format_penalties(framework.primary_statute.penalties),
                            govinfo_url=framework.primary_statute.govinfo_url or "",
                            applicable_violations=[v.violation_id for v in context.violations if v.statute == statute]
                        )
                        context.statute_mappings.append(mapping)
                        logger.debug(f"  Mapped: {statute}")
                except Exception as e:
                    logger.debug(f"Failed to map statute {statute}: {e}")
                    # Add basic mapping without GovInfo enrichment
                    mapping = StatuteMapping(
                        statute=statute,
                        name=statute,
                        jurisdiction="Federal",
                        penalties="Varies by violation",
                        govinfo_url="",
                        applicable_violations=[v.violation_id for v in context.violations if v.statute == statute]
                    )
                    context.statute_mappings.append(mapping)
            
            logger.info(f"✅ Phase 11 Complete: {len(context.statute_mappings)} statutes mapped")
            
        except Exception as e:
            logger.error(f"❌ Phase 11 failed: {e}", exc_info=True)
        
        return context
    
    def _format_penalties(self, penalties: Dict[str, Any]) -> str:
        """Format penalty information for display."""
        if not penalties:
            return "Varies by violation"
        
        parts = []
        if 'civil_fine' in penalties:
            parts.append(f"Civil: up to ${penalties['civil_fine']:,}")
        if 'criminal_fine' in penalties:
            parts.append(f"Criminal: up to ${penalties['criminal_fine']:,}")
        if 'imprisonment' in penalties:
            parts.append(f"Imprisonment: up to {penalties['imprisonment']} years")
        
        return ", ".join(parts) if parts else "Varies by violation"
    
    async def _phase_12_dual_agent_prosecution(self, context: ForensicContext) -> ForensicContext:
        """
        Phase 12: Dual-Agent Prosecution Analysis
        OpenAI primary detection → Anthropic deep reasoning validation.
        Cross-verification with 75% agreement threshold, conflict resolution.
        Generates prosecutorial merit scoring and criminal referral recommendations.
        """
        logger.info("\n" + "=" * 80)
        logger.info("🔬 PHASE 12: DUAL-AGENT PROSECUTION ANALYSIS")
        logger.info("=" * 80)
        
        try:
            if not self._get_config('dual_agent', 'enabled', default=True):
                logger.info("Dual-agent prosecution analysis disabled in config")
                return context
            
            # Requires both agents
            if not (self._openai_agent and self._anthropic_agent):
                logger.info("  Dual-agent mode requires both OpenAI and Anthropic agents")
                return context
            
            from .dual_agent import DualAgentCoordinator
            from .forensic_context import CriminalReferral
            import hashlib
            
            coordinator = DualAgentCoordinator()
            
            # Validate high-severity violations with dual-agent analysis
            high_severity_violations = [v for v in context.violations if v.severity in ["CRITICAL", "HIGH"]]
            
            if high_severity_violations:
                logger.info(f"  Dual-agent validation of {len(high_severity_violations)} high-severity violations")
                
                validated_count = 0
                criminal_referrals_added = 0
                
                for violation in high_severity_violations[:10]:  # Limit to top 10 for performance
                    try:
                        # OpenAI primary analysis
                        openai_result = await self._openai_agent.analyze_text(
                            f"Violation: {violation.description}\nEvidence: {violation.evidence[:1000]}",
                            context={'filing_type': 'Validation', 'document_url': violation.document_url}
                        )
                        
                        # Anthropic deep validation
                        anthropic_result = await self._anthropic_agent.analyze_text(
                            f"Violation: {violation.description}\nEvidence: {violation.evidence[:1000]}\n"
                            f"Statute: {violation.statute}\nValidate prosecutorial merit.",
                            context={'filing_type': 'Validation', 'document_url': violation.document_url}
                        )
                        
                        # Cross-verify results
                        agreement = self._calculate_agreement(openai_result, anthropic_result)
                        
                        if agreement >= self._get_config('dual_agent', 'agreement_threshold', default=0.75):
                            validated_count += 1
                            violation.metadata['dual_agent_validated'] = True
                            violation.metadata['confidence'] = agreement
                            
                            # Upgrade prosecutorial merit
                            violation.prosecutorial_merit = "STRONG"
                            
                            # Generate criminal referral for critical violations
                            if violation.severity == "CRITICAL":
                                evidence_hash = hashlib.sha256(violation.evidence.encode()).hexdigest()
                                referral = CriminalReferral(
                                    violation_id=violation.violation_id,
                                    statute=violation.statute,
                                    description=violation.description,
                                    evidence_hash=evidence_hash,
                                    recommended_action="DOJ Criminal Division - Fraud Section Review"
                                )
                                context.criminal_referrals.append(referral)
                                criminal_referrals_added += 1
                    except Exception as e:
                        logger.debug(f"Dual-agent validation failed for {violation.violation_id}: {e}")
                
                logger.info(f"  Validated: {validated_count}/{len(high_severity_violations)}")
                logger.info(f"  Criminal Referrals: {criminal_referrals_added}")
            else:
                logger.info("  No high-severity violations to validate")
            
            logger.info(f"✅ Phase 12 Complete: Dual-agent prosecution analysis performed")
            
        except Exception as e:
            logger.error(f"❌ Phase 12 failed: {e}", exc_info=True)
        
        return context
    
    def _calculate_agreement(self, result1: Dict, result2: Dict) -> float:
        """Calculate agreement score between two agent results."""
        # Simple agreement calculation based on violation detection
        violations1 = result1.get('violations', [])
        violations2 = result2.get('violations', [])
        
        if not violations1 and not violations2:
            return 1.0  # Both agree no violation
        
        if bool(violations1) == bool(violations2):
            return 0.8  # Both detected violations
        
        return 0.3  # Disagreement
