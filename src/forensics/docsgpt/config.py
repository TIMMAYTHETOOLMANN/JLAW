"""
DocsGPT Integration Configuration
=================================

Centralized configuration for DocsGPT integration with JLAW.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChunkingConfig:
    """Configuration for document chunking."""
    max_tokens: int = 2000
    min_tokens: int = 150
    overlap_tokens: int = 100
    duplicate_headers: bool = True
    strategy: str = "sec_optimized"


@dataclass
class EmbeddingConfig:
    """Configuration for document embeddings."""
    model_name: str = "sentence-transformers/all-mpnet-base-v2"
    dimension: int = 768
    batch_size: int = 32
    normalize: bool = True
    cache_embeddings: bool = True


@dataclass
class VectorStoreConfig:
    """Configuration for vector storage."""
    store_type: str = "faiss"  # faiss, mongodb, elasticsearch, qdrant
    index_path: str = "forensic_storage/vector_indices"
    
    # MongoDB settings
    mongodb_uri: Optional[str] = None
    mongodb_database: str = "jlaw_forensics"
    mongodb_collection: str = "sec_embeddings"
    
    # FAISS settings
    faiss_index_type: str = "IVF"  # Flat, IVF, HNSW
    faiss_nlist: int = 100
    
    # Elasticsearch settings
    elasticsearch_url: Optional[str] = None
    elasticsearch_index: str = "sec-filings"


@dataclass
class ParserConfig:
    """Configuration for document parsing."""
    pdf_as_image: bool = False  # Use vision model for PDFs
    ocr_enabled: bool = True
    ocr_language: str = "eng"
    extract_tables: bool = True
    extract_images: bool = True
    preserve_formatting: bool = True
    
    # SEC-specific settings
    extract_xbrl_facts: bool = True
    extract_exhibits: bool = True
    extract_signatures: bool = True


@dataclass
class LLMConfig:
    """Configuration for LLM integration."""
    provider: str = "openai"  # openai, anthropic, google, local
    model_name: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 4096
    
    # API keys (loaded from environment)
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    google_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))


@dataclass
class DocsGPTConfig:
    """
    Master configuration for DocsGPT integration.
    
    Usage:
        config = DocsGPTConfig()
        config.chunking.max_tokens = 3000
    """
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    parser: ParserConfig = field(default_factory=ParserConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    # Path to DocsGPT repository
    docsgpt_path: str = field(default_factory=lambda: str(
        Path(__file__).parent.parent.parent.parent / "external_repos" / "DocsGPT"
    ))
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_paths()
        self._setup_logging()
    
    def _validate_paths(self):
        """Validate that required paths exist."""
        docsgpt_path = Path(self.docsgpt_path)
        if not docsgpt_path.exists():
            logger.warning(f"DocsGPT path does not exist: {docsgpt_path}")
        
        # Create vector store path if needed
        vector_path = Path(self.vector_store.index_path)
        vector_path.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Configure logging based on settings."""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    @classmethod
    def from_env(cls) -> 'DocsGPTConfig':
        """Create configuration from environment variables."""
        return cls(
            chunking=ChunkingConfig(
                max_tokens=int(os.getenv("DOCSGPT_MAX_TOKENS", "2000")),
                min_tokens=int(os.getenv("DOCSGPT_MIN_TOKENS", "150")),
            ),
            vector_store=VectorStoreConfig(
                store_type=os.getenv("DOCSGPT_VECTOR_STORE", "faiss"),
                mongodb_uri=os.getenv("MONGODB_URI"),
                elasticsearch_url=os.getenv("ELASTICSEARCH_URL"),
            ),
            llm=LLMConfig(
                provider=os.getenv("DOCSGPT_LLM_PROVIDER", "openai"),
                model_name=os.getenv("DOCSGPT_LLM_MODEL", "gpt-4o"),
            ),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        from dataclasses import asdict
        return asdict(self)


# Global configuration instance
_global_config: Optional[DocsGPTConfig] = None


def get_config() -> DocsGPTConfig:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = DocsGPTConfig.from_env()
    return _global_config


def set_config(config: DocsGPTConfig):
    """Set the global configuration instance."""
    global _global_config
    _global_config = config

