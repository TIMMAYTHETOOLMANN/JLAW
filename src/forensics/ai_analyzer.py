"""
AI-Powered SEC Filing Analyzer
===============================

Implements map-reduce pattern for large document analysis with:
- Token counting via tiktoken for proper chunking
- 10-K section chunking by SEC Item patterns
- Dual SDK support (OpenAI + Anthropic Claude)
- Structured output extraction

Use Cases:
- Extract risk factors from Item 1A
- Analyze MD&A (Item 7) for red flags
- Identify contingencies in Item 8
- Extract executive compensation details
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SDKProvider(Enum):
    """AI SDK provider options."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class AnalysisChunk:
    """A chunk of document for analysis."""
    chunk_id: str
    text: str
    section: Optional[str] = None
    token_count: int = 0
    start_position: int = 0
    end_position: int = 0


@dataclass
class AnalysisResult:
    """Result of AI-powered analysis."""
    summary: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    red_flags: List[Dict[str, Any]] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=dict)
    model_used: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "findings": self.findings,
            "risk_factors": self.risk_factors,
            "red_flags": self.red_flags,
            "token_usage": self.token_usage,
            "model_used": self.model_used
        }


class SECFilingAnalyzer:
    """
    AI-powered analyzer for SEC filings using map-reduce pattern.
    
    Supports both OpenAI and Anthropic Claude for cross-validation.
    """
    
    # SEC 10-K section patterns
    SEC_10K_SECTIONS = {
        'Item 1': r'(?i)ITEM\s*1[\.\:\s]+(?:BUSINESS|Description\s+of\s+Business)',
        'Item 1A': r'(?i)ITEM\s*1A[\.\:\s]+RISK\s*FACTORS',
        'Item 1B': r'(?i)ITEM\s*1B[\.\:\s]+UNRESOLVED\s*STAFF\s*COMMENTS',
        'Item 2': r'(?i)ITEM\s*2[\.\:\s]+PROPERTIES',
        'Item 3': r'(?i)ITEM\s*3[\.\:\s]+LEGAL\s*PROCEEDINGS',
        'Item 4': r'(?i)ITEM\s*4[\.\:\s]+MINE\s*SAFETY',
        'Item 5': r'(?i)ITEM\s*5[\.\:\s]+MARKET\s+FOR\s+REGISTRANT',
        'Item 6': r'(?i)ITEM\s*6[\.\:\s]+(?:SELECTED\s*FINANCIAL\s*DATA|Reserved)',
        'Item 7': r'(?i)ITEM\s*7[\.\:\s]+MANAGEMENT',
        'Item 7A': r'(?i)ITEM\s*7A[\.\:\s]+QUANTITATIVE\s+AND\s+QUALITATIVE',
        'Item 8': r'(?i)ITEM\s*8[\.\:\s]+FINANCIAL\s*STATEMENTS',
        'Item 9': r'(?i)ITEM\s*9[\.\:\s]+CHANGES\s+IN\s+AND\s+DISAGREEMENTS',
        'Item 9A': r'(?i)ITEM\s*9A[\.\:\s]+CONTROLS\s+AND\s+PROCEDURES',
        'Item 9B': r'(?i)ITEM\s*9B[\.\:\s]+OTHER\s*INFORMATION',
        'Item 10': r'(?i)ITEM\s*10[\.\:\s]+DIRECTORS',
        'Item 11': r'(?i)ITEM\s*11[\.\:\s]+EXECUTIVE\s*COMPENSATION',
        'Item 12': r'(?i)ITEM\s*12[\.\:\s]+SECURITY\s*OWNERSHIP',
        'Item 13': r'(?i)ITEM\s*13[\.\:\s]+CERTAIN\s*RELATIONSHIPS',
        'Item 14': r'(?i)ITEM\s*14[\.\:\s]+PRINCIPAL\s*ACCOUNTANT',
        'Item 15': r'(?i)ITEM\s*15[\.\:\s]+EXHIBITS',
        'Item 16': r'(?i)ITEM\s*16[\.\:\s]+FORM\s*10-K\s*SUMMARY',
    }
    
    def __init__(self, provider: SDKProvider = SDKProvider.OPENAI, api_key: Optional[str] = None):
        """
        Initialize SEC filing analyzer.
        
        Args:
            provider: AI SDK provider (OpenAI or Anthropic)
            api_key: API key for the provider (optional if set in environment)
        """
        self.provider = provider
        self.api_key = api_key
        
        # Initialize token counter
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
            logger.info("Initialized tiktoken for token counting")
        except ImportError:
            logger.warning("tiktoken not installed, using character-based estimation")
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Rough estimation: 1 token ≈ 4 characters
            return len(text) // 4
    
    def chunk_by_sections(
        self,
        content: str,
        max_chunk_size: int = 100000
    ) -> List[AnalysisChunk]:
        """
        Chunk 10-K filing by SEC sections (Item 1, 1A, 2, etc.).
        
        Args:
            content: Full filing content
            max_chunk_size: Maximum token count per chunk
            
        Returns:
            List of AnalysisChunk objects
        """
        chunks = []
        
        # Find all section boundaries
        section_matches = []
        for section_name, pattern in self.SEC_10K_SECTIONS.items():
            for match in re.finditer(pattern, content):
                section_matches.append({
                    'name': section_name,
                    'start': match.start(),
                    'end': match.end()
                })
        
        # Sort by start position
        section_matches.sort(key=lambda x: x['start'])
        
        if not section_matches:
            # No sections found, chunk by size
            return self._chunk_by_size(content, max_chunk_size)
        
        # Extract sections
        for i, section in enumerate(section_matches):
            start = section['end']
            end = section_matches[i + 1]['start'] if i + 1 < len(section_matches) else len(content)
            
            section_text = content[start:end].strip()
            section_tokens = self.count_tokens(section_text)
            
            if section_tokens > max_chunk_size:
                # Split large section into smaller chunks
                sub_chunks = self._chunk_by_size(section_text, max_chunk_size)
                for j, sub_chunk in enumerate(sub_chunks):
                    sub_chunk.section = f"{section['name']} (part {j+1})"
                    chunks.append(sub_chunk)
            else:
                chunks.append(AnalysisChunk(
                    chunk_id=f"section_{i}",
                    text=section_text,
                    section=section['name'],
                    token_count=section_tokens,
                    start_position=start,
                    end_position=end
                ))
        
        logger.info(f"Chunked filing into {len(chunks)} sections")
        return chunks
    
    def _chunk_by_size(self, content: str, max_chunk_size: int) -> List[AnalysisChunk]:
        """
        Chunk content by token size with overlap.
        
        Args:
            content: Text to chunk
            max_chunk_size: Maximum tokens per chunk
            
        Returns:
            List of AnalysisChunk objects
        """
        chunks = []
        overlap = max_chunk_size // 10  # 10% overlap
        
        words = content.split()
        current_chunk = []
        current_tokens = 0
        chunk_id = 0
        
        for word in words:
            word_tokens = self.count_tokens(word + " ")
            
            if current_tokens + word_tokens > max_chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append(AnalysisChunk(
                    chunk_id=f"chunk_{chunk_id}",
                    text=chunk_text,
                    token_count=current_tokens,
                    start_position=0,
                    end_position=0
                ))
                
                # Start new chunk with overlap
                overlap_words = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_words + [word]
                current_tokens = self.count_tokens(" ".join(current_chunk))
                chunk_id += 1
            else:
                current_chunk.append(word)
                current_tokens += word_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append(AnalysisChunk(
                chunk_id=f"chunk_{chunk_id}",
                text=" ".join(current_chunk),
                token_count=current_tokens,
                start_position=0,
                end_position=0
            ))
        
        return chunks
    
    def map_reduce_analyze(
        self,
        full_content: str,
        map_prompt: str,
        reduce_prompt: str,
        max_chunk_size: int = 50000
    ) -> AnalysisResult:
        """
        Analyze large document using map-reduce pattern.
        
        Map phase: Analyze each chunk independently
        Reduce phase: Combine chunk analyses into final result
        
        Args:
            full_content: Full document content
            map_prompt: Prompt for analyzing individual chunks
            reduce_prompt: Prompt for combining chunk results
            max_chunk_size: Maximum tokens per chunk
            
        Returns:
            AnalysisResult with findings
        """
        # Chunk the document
        chunks = self.chunk_by_sections(full_content, max_chunk_size)
        
        logger.info(f"Map phase: Analyzing {len(chunks)} chunks")
        
        # Map phase: Analyze each chunk
        chunk_results = []
        total_tokens_used = {"prompt": 0, "completion": 0}
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Analyzing chunk {i+1}/{len(chunks)}: {chunk.section or chunk.chunk_id}")
            
            try:
                result = self._analyze_chunk(chunk, map_prompt)
                chunk_results.append({
                    "chunk_id": chunk.chunk_id,
                    "section": chunk.section,
                    "result": result
                })
                
                # Track token usage
                if "token_usage" in result:
                    for key in ["prompt", "completion"]:
                        total_tokens_used[key] += result["token_usage"].get(key, 0)
            
            except Exception as e:
                logger.error(f"Error analyzing chunk {chunk.chunk_id}: {e}")
                chunk_results.append({
                    "chunk_id": chunk.chunk_id,
                    "section": chunk.section,
                    "error": str(e)
                })
        
        # Reduce phase: Combine results
        logger.info(f"Reduce phase: Combining {len(chunk_results)} chunk results")
        
        try:
            final_result = self._combine_results(chunk_results, reduce_prompt)
            final_result.token_usage = total_tokens_used
            return final_result
        except Exception as e:
            logger.error(f"Error in reduce phase: {e}")
            return AnalysisResult(
                summary=f"Analysis failed: {e}",
                token_usage=total_tokens_used
            )
    
    def _analyze_chunk(self, chunk: AnalysisChunk, prompt: str) -> Dict[str, Any]:
        """
        Analyze a single chunk using AI.
        
        Args:
            chunk: Chunk to analyze
            prompt: Analysis prompt
            
        Returns:
            Analysis result dict
        """
        # This is a placeholder - actual implementation would call OpenAI/Anthropic
        logger.warning("AI analysis not implemented - returning mock result")
        
        return {
            "summary": f"Analysis of {chunk.section or chunk.chunk_id}",
            "findings": [],
            "token_usage": {"prompt": chunk.token_count, "completion": 100}
        }
    
    def _combine_results(
        self,
        chunk_results: List[Dict[str, Any]],
        reduce_prompt: str
    ) -> AnalysisResult:
        """
        Combine chunk results into final analysis.
        
        Args:
            chunk_results: Results from individual chunks
            reduce_prompt: Prompt for combining results
            
        Returns:
            Combined AnalysisResult
        """
        # This is a placeholder - actual implementation would call OpenAI/Anthropic
        logger.warning("AI result combination not implemented - returning mock result")
        
        all_findings = []
        for result in chunk_results:
            if "result" in result and "findings" in result["result"]:
                all_findings.extend(result["result"]["findings"])
        
        return AnalysisResult(
            summary="Combined analysis of all sections",
            findings=all_findings,
            model_used=self.provider.value
        )
    
    def extract_risk_factors(self, content: str) -> List[str]:
        """
        Extract risk factors from Item 1A section.
        
        Args:
            content: Full filing content
            
        Returns:
            List of risk factor statements
        """
        # Find Item 1A section
        pattern = self.SEC_10K_SECTIONS['Item 1A']
        match = re.search(pattern, content)
        
        if not match:
            logger.warning("Item 1A (Risk Factors) section not found")
            return []
        
        # Extract section content
        start = match.end()
        # Find next section
        next_section_match = None
        for section_name, section_pattern in self.SEC_10K_SECTIONS.items():
            if section_name == 'Item 1A':
                continue
            next_match = re.search(section_pattern, content[start:])
            if next_match:
                if next_section_match is None or next_match.start() < next_section_match.start():
                    next_section_match = next_match
        
        end = start + next_section_match.start() if next_section_match else len(content)
        risk_section = content[start:end]
        
        # Extract individual risk factors (basic heuristic)
        # Risk factors often start with bullet points or headers
        risk_factors = []
        for paragraph in risk_section.split('\n\n'):
            paragraph = paragraph.strip()
            if len(paragraph) > 100 and ('risk' in paragraph.lower() or 'may' in paragraph.lower()):
                risk_factors.append(paragraph[:500])  # Limit length
        
        logger.info(f"Extracted {len(risk_factors)} risk factors from Item 1A")
        return risk_factors[:50]  # Limit to 50 risk factors
