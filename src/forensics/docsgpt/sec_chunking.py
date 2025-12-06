"""
SEC-Optimized Document Chunking
================================

Intelligent chunking strategies specifically designed for SEC filings.
Preserves document structure, maintains context, and optimizes for
semantic search and forensic analysis.

Key Features:
- Token-aware chunking with tiktoken
- SEC section-aware splitting
- Header/footer duplication for context
- Table preservation
- XBRL fact grouping
"""

import re
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import tiktoken, fall back to approximation
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not available, using approximate token counting")


class SECChunkingStrategy(Enum):
    """Available chunking strategies for SEC documents."""
    CLASSIC = "classic"           # Fixed-size token chunks
    SEMANTIC = "semantic"         # Sentence/paragraph-based
    SECTION = "section"           # SEC section-based
    HYBRID = "hybrid"             # Combination of section + semantic
    RECURSIVE = "recursive"       # Recursive character splitting


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""
    chunk_id: str
    chunk_index: int
    total_chunks: int
    token_count: int
    start_char: int
    end_char: int
    section: Optional[str] = None
    contains_table: bool = False
    contains_xbrl: bool = False
    is_continuation: bool = False
    header: str = ""


@dataclass
class DocumentChunk:
    """
    A chunk of a parsed document.
    
    Attributes:
        text: The chunk text content
        doc_id: Parent document ID
        metadata: Chunk metadata
        embedding: Optional pre-computed embedding
    """
    text: str
    doc_id: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            'text': self.text,
            'doc_id': self.doc_id,
            'chunk_id': self.metadata.chunk_id,
            'chunk_index': self.metadata.chunk_index,
            'total_chunks': self.metadata.total_chunks,
            'token_count': self.metadata.token_count,
            'section': self.metadata.section,
            'contains_table': self.metadata.contains_table,
            'contains_xbrl': self.metadata.contains_xbrl,
        }


class TokenCounter:
    """Token counting utility with tiktoken or approximation."""
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self._encoder = None
        
        if TIKTOKEN_AVAILABLE:
            try:
                self._encoder = tiktoken.encoding_for_model(model)
            except KeyError:
                self._encoder = tiktoken.get_encoding("cl100k_base")
    
    def count(self, text: str) -> int:
        """Count tokens in text."""
        if self._encoder:
            return len(self._encoder.encode(text))
        else:
            # Approximate: ~4 characters per token
            return len(text) // 4
    
    def encode(self, text: str) -> List[int]:
        """Encode text to tokens."""
        if self._encoder:
            return self._encoder.encode(text)
        else:
            # Return character-based pseudo-tokens
            return list(range(len(text) // 4))
    
    def decode(self, tokens: List[int]) -> str:
        """Decode tokens to text (only works with tiktoken)."""
        if self._encoder:
            return self._encoder.decode(tokens)
        else:
            raise NotImplementedError("Decoding requires tiktoken")


class SECChunker:
    """
    SEC-optimized document chunker.
    
    Provides intelligent chunking strategies that preserve document
    structure and maintain context for forensic analysis.
    
    Usage:
        chunker = SECChunker(max_tokens=2000, strategy=SECChunkingStrategy.HYBRID)
        chunks = chunker.chunk_document(parsed_doc)
    """
    
    # SEC section patterns for section-based chunking
    SEC_SECTION_PATTERNS = [
        # 10-K/10-Q items
        (r'(?:PART|Part)\s+(I+|IV|V|[1-4])\s*[-–—]?\s*$', 'PART'),
        (r'(?:ITEM|Item)\s*(\d+[A-Z]?)\.?\s*[-–—]?\s*(.{0,100})', 'ITEM'),
        # Common sections
        (r'(?:RISK\s*FACTORS?)', 'RISK_FACTORS'),
        (r'(?:MANAGEMENT.S\s*DISCUSSION)', 'MD&A'),
        (r'(?:FINANCIAL\s*STATEMENTS)', 'FINANCIALS'),
        (r'(?:NOTES\s*TO\s*(?:CONSOLIDATED\s*)?FINANCIAL\s*STATEMENTS)', 'NOTES'),
        (r'(?:SIGNATURES?)', 'SIGNATURES'),
        (r'(?:EXHIBITS?)', 'EXHIBITS'),
    ]
    
    def __init__(
        self,
        max_tokens: int = 2000,
        min_tokens: int = 150,
        overlap_tokens: int = 100,
        strategy: SECChunkingStrategy = SECChunkingStrategy.HYBRID,
        duplicate_headers: bool = True,
        preserve_tables: bool = True,
        model: str = "gpt-4"
    ):
        """
        Initialize SEC chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk
            min_tokens: Minimum tokens per chunk
            overlap_tokens: Token overlap between chunks
            strategy: Chunking strategy to use
            duplicate_headers: Whether to duplicate section headers
            preserve_tables: Whether to keep tables intact
            model: Model for token counting
        """
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens
        self.overlap_tokens = overlap_tokens
        self.strategy = strategy
        self.duplicate_headers = duplicate_headers
        self.preserve_tables = preserve_tables
        self.token_counter = TokenCounter(model)
        
        logger.info(f"SECChunker initialized: strategy={strategy.value}, max_tokens={max_tokens}")
    
    def chunk_document(self, document) -> List[DocumentChunk]:
        """
        Chunk a parsed document.
        
        Args:
            document: ParsedDocument instance
            
        Returns:
            List of DocumentChunk instances
        """
        if self.strategy == SECChunkingStrategy.CLASSIC:
            return self._classic_chunk(document)
        elif self.strategy == SECChunkingStrategy.SEMANTIC:
            return self._semantic_chunk(document)
        elif self.strategy == SECChunkingStrategy.SECTION:
            return self._section_chunk(document)
        elif self.strategy == SECChunkingStrategy.HYBRID:
            return self._hybrid_chunk(document)
        elif self.strategy == SECChunkingStrategy.RECURSIVE:
            return self._recursive_chunk(document)
        else:
            raise ValueError(f"Unknown chunking strategy: {self.strategy}")
    
    def _classic_chunk(self, document) -> List[DocumentChunk]:
        """Classic fixed-size token chunking."""
        text = document.raw_text
        chunks = []
        
        # Split into tokens
        current_pos = 0
        chunk_index = 0
        
        while current_pos < len(text):
            # Calculate end position
            chunk_text = text[current_pos:]
            token_count = self.token_counter.count(chunk_text)
            
            if token_count <= self.max_tokens:
                # Rest of document fits in one chunk
                end_pos = len(text)
            else:
                # Find approximate end position
                char_per_token = len(chunk_text) / token_count
                end_pos = current_pos + int(self.max_tokens * char_per_token)
                
                # Find sentence boundary
                end_pos = self._find_sentence_boundary(text, end_pos)
            
            chunk_text = text[current_pos:end_pos]
            token_count = self.token_counter.count(chunk_text)
            
            if token_count >= self.min_tokens or current_pos == 0:
                chunk = DocumentChunk(
                    text=chunk_text,
                    doc_id=document.doc_id,
                    metadata=ChunkMetadata(
                        chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                        chunk_index=chunk_index,
                        total_chunks=0,  # Updated later
                        token_count=token_count,
                        start_char=current_pos,
                        end_char=end_pos,
                        is_continuation=(chunk_index > 0)
                    )
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move position with overlap
            current_pos = end_pos - int(self.overlap_tokens * (len(chunk_text) / token_count))
            current_pos = max(current_pos, end_pos - 100)  # Minimum progress
        
        # Update total chunks
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
        
        logger.info(f"Classic chunking: {len(chunks)} chunks created")
        return chunks
    
    def _semantic_chunk(self, document) -> List[DocumentChunk]:
        """Sentence and paragraph-based chunking."""
        text = document.raw_text
        
        # Split by paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk_text = ""
        current_tokens = 0
        chunk_index = 0
        start_char = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_tokens = self.token_counter.count(para)
            
            if current_tokens + para_tokens <= self.max_tokens:
                # Add paragraph to current chunk
                if current_chunk_text:
                    current_chunk_text += "\n\n"
                current_chunk_text += para
                current_tokens += para_tokens
            else:
                # Save current chunk and start new one
                if current_chunk_text and current_tokens >= self.min_tokens:
                    chunk = DocumentChunk(
                        text=current_chunk_text,
                        doc_id=document.doc_id,
                        metadata=ChunkMetadata(
                            chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                            chunk_index=chunk_index,
                            total_chunks=0,
                            token_count=current_tokens,
                            start_char=start_char,
                            end_char=start_char + len(current_chunk_text)
                        )
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Start new chunk
                start_char += len(current_chunk_text) + 2
                current_chunk_text = para
                current_tokens = para_tokens
        
        # Save last chunk
        if current_chunk_text and current_tokens >= self.min_tokens:
            chunk = DocumentChunk(
                text=current_chunk_text,
                doc_id=document.doc_id,
                metadata=ChunkMetadata(
                    chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                    chunk_index=chunk_index,
                    total_chunks=0,
                    token_count=current_tokens,
                    start_char=start_char,
                    end_char=start_char + len(current_chunk_text)
                )
            )
            chunks.append(chunk)
        
        # Update total chunks
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
        
        logger.info(f"Semantic chunking: {len(chunks)} chunks created")
        return chunks
    
    def _section_chunk(self, document) -> List[DocumentChunk]:
        """SEC section-based chunking."""
        text = document.raw_text
        
        # Find all section boundaries
        sections = self._identify_sections(text)
        
        if not sections:
            # Fall back to semantic chunking
            logger.warning("No SEC sections found, falling back to semantic chunking")
            return self._semantic_chunk(document)
        
        chunks = []
        chunk_index = 0
        
        for section_name, section_text, start_pos, end_pos in sections:
            section_tokens = self.token_counter.count(section_text)
            
            if section_tokens <= self.max_tokens:
                # Section fits in one chunk
                chunk = DocumentChunk(
                    text=section_text,
                    doc_id=document.doc_id,
                    metadata=ChunkMetadata(
                        chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                        chunk_index=chunk_index,
                        total_chunks=0,
                        token_count=section_tokens,
                        start_char=start_pos,
                        end_char=end_pos,
                        section=section_name
                    )
                )
                chunks.append(chunk)
                chunk_index += 1
            else:
                # Split large section
                sub_chunks = self._split_section(
                    section_text, section_name, document.doc_id, chunk_index, start_pos
                )
                chunks.extend(sub_chunks)
                chunk_index += len(sub_chunks)
        
        # Update total chunks
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
        
        logger.info(f"Section chunking: {len(chunks)} chunks from {len(sections)} sections")
        return chunks
    
    def _hybrid_chunk(self, document) -> List[DocumentChunk]:
        """
        Hybrid chunking: section-aware with semantic fallback.
        Best for comprehensive SEC filing analysis.
        """
        text = document.raw_text
        
        # First, identify sections
        sections = self._identify_sections(text)
        
        chunks = []
        chunk_index = 0
        
        if sections:
            # Process each section
            for section_name, section_text, start_pos, end_pos in sections:
                section_tokens = self.token_counter.count(section_text)
                
                if section_tokens <= self.max_tokens:
                    # Section fits in one chunk
                    chunk = DocumentChunk(
                        text=section_text,
                        doc_id=document.doc_id,
                        metadata=ChunkMetadata(
                            chunk_id=f"{document.doc_id}_chunk_{chunk_index}",
                            chunk_index=chunk_index,
                            total_chunks=0,
                            token_count=section_tokens,
                            start_char=start_pos,
                            end_char=end_pos,
                            section=section_name,
                            header=self._extract_header(section_text)
                        )
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                else:
                    # Apply semantic chunking within section
                    header = self._extract_header(section_text)
                    sub_chunks = self._semantic_chunk_section(
                        section_text, section_name, document.doc_id, 
                        chunk_index, start_pos, header
                    )
                    chunks.extend(sub_chunks)
                    chunk_index += len(sub_chunks)
        else:
            # No sections found, use pure semantic chunking
            chunks = self._semantic_chunk(document)
        
        # Update total chunks
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
        
        logger.info(f"Hybrid chunking: {len(chunks)} chunks created")
        return chunks
    
    def _recursive_chunk(self, document) -> List[DocumentChunk]:
        """Recursive character splitting with multiple separators."""
        separators = ["\n\n", "\n", ". ", " ", ""]
        
        def recursive_split(text: str, separators: List[str]) -> List[str]:
            if not separators:
                return [text]
            
            separator = separators[0]
            if separator == "":
                # Character-level splitting
                chunks = []
                for i in range(0, len(text), self.max_tokens * 4):
                    chunks.append(text[i:i + self.max_tokens * 4])
                return chunks
            
            splits = text.split(separator)
            chunks = []
            current = ""
            
            for split in splits:
                if self.token_counter.count(current + split) <= self.max_tokens:
                    current += (separator if current else "") + split
                else:
                    if current:
                        if self.token_counter.count(current) > self.max_tokens:
                            # Need finer splitting
                            chunks.extend(recursive_split(current, separators[1:]))
                        else:
                            chunks.append(current)
                    current = split
            
            if current:
                if self.token_counter.count(current) > self.max_tokens:
                    chunks.extend(recursive_split(current, separators[1:]))
                else:
                    chunks.append(current)
            
            return chunks
        
        text_chunks = recursive_split(document.raw_text, separators)
        
        chunks = []
        pos = 0
        for i, text in enumerate(text_chunks):
            chunk = DocumentChunk(
                text=text,
                doc_id=document.doc_id,
                metadata=ChunkMetadata(
                    chunk_id=f"{document.doc_id}_chunk_{i}",
                    chunk_index=i,
                    total_chunks=len(text_chunks),
                    token_count=self.token_counter.count(text),
                    start_char=pos,
                    end_char=pos + len(text)
                )
            )
            chunks.append(chunk)
            pos += len(text)
        
        logger.info(f"Recursive chunking: {len(chunks)} chunks created")
        return chunks
    
    def _identify_sections(self, text: str) -> List[Tuple[str, str, int, int]]:
        """Identify SEC sections in document text."""
        sections = []
        last_end = 0
        
        # Find all section matches
        matches = []
        for pattern, section_type in self.SEC_SECTION_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                matches.append((match.start(), match.end(), section_type, match.group(0)))
        
        # Sort by position
        matches.sort(key=lambda x: x[0])
        
        # Extract section content
        for i, (start, end, section_type, header) in enumerate(matches):
            # Section ends at next section or document end
            if i + 1 < len(matches):
                section_end = matches[i + 1][0]
            else:
                section_end = len(text)
            
            section_text = text[start:section_end].strip()
            section_name = f"{section_type}: {header[:50]}"
            
            if section_text:
                sections.append((section_name, section_text, start, section_end))
        
        # Add content before first section
        if matches and matches[0][0] > 0:
            preamble = text[:matches[0][0]].strip()
            if preamble:
                sections.insert(0, ("PREAMBLE", preamble, 0, matches[0][0]))
        
        return sections
    
    def _split_section(
        self, 
        section_text: str, 
        section_name: str, 
        doc_id: str, 
        start_index: int,
        start_char: int
    ) -> List[DocumentChunk]:
        """Split a large section into smaller chunks."""
        chunks = []
        paragraphs = re.split(r'\n\s*\n', section_text)
        
        current_text = ""
        current_tokens = 0
        chunk_idx = start_index
        current_start = start_char
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_tokens = self.token_counter.count(para)
            
            if current_tokens + para_tokens <= self.max_tokens:
                if current_text:
                    current_text += "\n\n"
                current_text += para
                current_tokens += para_tokens
            else:
                if current_text:
                    chunk = DocumentChunk(
                        text=current_text,
                        doc_id=doc_id,
                        metadata=ChunkMetadata(
                            chunk_id=f"{doc_id}_chunk_{chunk_idx}",
                            chunk_index=chunk_idx,
                            total_chunks=0,
                            token_count=current_tokens,
                            start_char=current_start,
                            end_char=current_start + len(current_text),
                            section=section_name,
                            is_continuation=(chunk_idx > start_index)
                        )
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                
                current_start += len(current_text) + 2
                current_text = para
                current_tokens = para_tokens
        
        # Save remaining
        if current_text:
            chunk = DocumentChunk(
                text=current_text,
                doc_id=doc_id,
                metadata=ChunkMetadata(
                    chunk_id=f"{doc_id}_chunk_{chunk_idx}",
                    chunk_index=chunk_idx,
                    total_chunks=0,
                    token_count=current_tokens,
                    start_char=current_start,
                    end_char=current_start + len(current_text),
                    section=section_name,
                    is_continuation=(chunk_idx > start_index)
                )
            )
            chunks.append(chunk)
        
        return chunks
    
    def _semantic_chunk_section(
        self,
        section_text: str,
        section_name: str,
        doc_id: str,
        start_index: int,
        start_char: int,
        header: str = ""
    ) -> List[DocumentChunk]:
        """Apply semantic chunking within a section."""
        chunks = []
        
        # Use header duplication if enabled
        header_tokens = self.token_counter.count(header) if self.duplicate_headers else 0
        effective_max = self.max_tokens - header_tokens
        
        paragraphs = re.split(r'\n\s*\n', section_text)
        
        current_text = ""
        current_tokens = 0
        chunk_idx = start_index
        current_start = start_char
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_tokens = self.token_counter.count(para)
            
            if current_tokens + para_tokens <= effective_max:
                if current_text:
                    current_text += "\n\n"
                current_text += para
                current_tokens += para_tokens
            else:
                if current_text:
                    # Add header if enabled and not first chunk
                    final_text = current_text
                    if self.duplicate_headers and header and chunk_idx > start_index:
                        final_text = header + "\n\n" + current_text
                    
                    chunk = DocumentChunk(
                        text=final_text,
                        doc_id=doc_id,
                        metadata=ChunkMetadata(
                            chunk_id=f"{doc_id}_chunk_{chunk_idx}",
                            chunk_index=chunk_idx,
                            total_chunks=0,
                            token_count=self.token_counter.count(final_text),
                            start_char=current_start,
                            end_char=current_start + len(current_text),
                            section=section_name,
                            header=header,
                            is_continuation=(chunk_idx > start_index)
                        )
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                
                current_start += len(current_text) + 2
                current_text = para
                current_tokens = para_tokens
        
        # Save remaining
        if current_text:
            final_text = current_text
            if self.duplicate_headers and header and chunk_idx > start_index:
                final_text = header + "\n\n" + current_text
            
            chunk = DocumentChunk(
                text=final_text,
                doc_id=doc_id,
                metadata=ChunkMetadata(
                    chunk_id=f"{doc_id}_chunk_{chunk_idx}",
                    chunk_index=chunk_idx,
                    total_chunks=0,
                    token_count=self.token_counter.count(final_text),
                    start_char=current_start,
                    end_char=current_start + len(current_text),
                    section=section_name,
                    header=header,
                    is_continuation=(chunk_idx > start_index)
                )
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_header(self, text: str) -> str:
        """Extract header from section text."""
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            # Look for section headers
            for pattern, _ in self.SEC_SECTION_PATTERNS:
                if re.match(pattern, line, re.IGNORECASE):
                    return line
        return lines[0].strip() if lines else ""
    
    def _find_sentence_boundary(self, text: str, target_pos: int) -> int:
        """Find nearest sentence boundary to target position."""
        # Look forward for sentence end
        forward_match = re.search(r'[.!?]\s+', text[target_pos:target_pos + 200])
        forward_pos = target_pos + forward_match.end() if forward_match else len(text)
        
        # Look backward for sentence end
        backward_text = text[max(0, target_pos - 200):target_pos]
        backward_match = list(re.finditer(r'[.!?]\s+', backward_text))
        backward_pos = target_pos - 200 + backward_match[-1].end() if backward_match else target_pos
        
        # Choose closest boundary
        if abs(forward_pos - target_pos) < abs(backward_pos - target_pos):
            return forward_pos
        else:
            return max(backward_pos, target_pos)

