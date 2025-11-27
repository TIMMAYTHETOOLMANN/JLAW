"""
Metadata Enhancer - Phase 1
===========================
Enhanced metadata extraction and document provenance tracking
"""
import logging
import hashlib
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
logger = logging.getLogger(__name__)
@dataclass
class EnhancedMetadata:
    """Enhanced metadata with forensic provenance"""
    document_id: str
    extraction_timestamp: str
    content_hash: str
    file_type: str
    file_size: int
    page_count: Optional[int] = None
    author: Optional[str] = None
    language: str = 'en'
    encoding: str = 'utf-8'
    source_url: Optional[str] = None
    sec_metadata: Dict[str, Any] = field(default_factory=dict)
    chain_of_custody: List[Dict[str, str]] = field(default_factory=list)
    integrity_verified: bool = False
class MetadataEnhancer:
    """Enhanced metadata extraction with chain of custody tracking"""
    def __init__(self):
        self.sec_patterns = {
            'cik': re.compile(r'CIK[:\s]+(\d{10})', re.IGNORECASE),
            'accession': re.compile(r'ACCESSION\s+NUMBER[:\s]+([\d\-]+)', re.IGNORECASE),
            'filing_date': re.compile(r'FILED\s+AS\s+OF\s+DATE[:\s]+(\d{8})', re.IGNORECASE),
            'form_type': re.compile(r'FORM\s+TYPE[:\s]+([A-Z0-9\-]+)', re.IGNORECASE)
        }
        logger.info("✅ Metadata Enhancer initialized")
    async def enhance_metadata(
        self,
        content: str,
        base_metadata: Optional[Dict[str, Any]] = None,
        url: Optional[str] = None
    ) -> EnhancedMetadata:
        """Extract and enhance document metadata"""
        doc_id = self._generate_document_id(content)
        content_hash = self._calculate_content_hash(content)
        sec_metadata = await self._extract_sec_metadata(content)
        chain_of_custody = [{
            'action': 'metadata_extraction',
            'timestamp': datetime.utcnow().isoformat(),
            'operator': 'MetadataEnhancer',
            'hash': content_hash
        }]
        metadata = EnhancedMetadata(
            document_id=doc_id,
            extraction_timestamp=datetime.utcnow().isoformat(),
            content_hash=content_hash,
            file_type=self._detect_file_type(content),
            file_size=len(content.encode('utf-8')),
            source_url=url,
            sec_metadata=sec_metadata,
            chain_of_custody=chain_of_custody,
            integrity_verified=True
        )
        logger.info(f"📋 Enhanced metadata extracted - Doc ID: {doc_id[:16]}...")
        return metadata
    async def _extract_sec_metadata(self, content: str) -> Dict[str, Any]:
        """Extract SEC-specific metadata fields"""
        sec_data = {}
        for field, pattern in self.sec_patterns.items():
            match = pattern.search(content)
            if match:
                sec_data[field] = match.group(1).strip()
        return sec_data
    def _generate_document_id(self, content: str) -> str:
        """Generate unique document ID"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash for integrity verification"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    def _detect_file_type(self, content: str) -> str:
        """Detect file type from content"""
        content_lower = content.lower()
        if '<html' in content_lower:
            return 'html'
        elif '<?xml' in content_lower:
            return 'xml'
        return 'text'
    def verify_integrity(self, content: str, expected_hash: str) -> bool:
        """Verify document integrity against expected hash"""
        actual_hash = self._calculate_content_hash(content)
        return actual_hash == expected_hash
    def add_custody_entry(
        self,
        metadata: EnhancedMetadata,
        action: str,
        operator: str
    ) -> EnhancedMetadata:
        """Add entry to chain of custody"""
        entry = {
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'operator': operator,
            'hash': metadata.content_hash
        }
        metadata.chain_of_custody.append(entry)
        return metadata
