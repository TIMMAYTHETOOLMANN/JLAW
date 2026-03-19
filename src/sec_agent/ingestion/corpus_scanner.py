"""
Corpus Scanner — Raw EDGAR Filing Tree Scanner
=================================================

Scans raw SEC EDGAR filing corpus directories (PDFs, XLS, JSON, XML)
and generates a manifest of all available filings for ingestion into
the JLAW forensic analysis pipeline.

Designed to handle the SEC-AGENT corpus structure:
    raw_data/
    ├── primary/        (1,186 filings: 592 PDF + 594 XLS)
    ├── nits_secondary/ (1,068 filings: 527 PDF + 541 XLS)
    └── xbrl/           (CIK Company Facts JSON)
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Supported file extensions for SEC EDGAR filings
SUPPORTED_EXTENSIONS: Set[str] = {
    ".pdf", ".xls", ".xlsx", ".xml", ".txt",
    ".htm", ".html", ".json", ".sgml",
}

# File extension categories
EXTENSION_CATEGORIES: Dict[str, str] = {
    ".pdf": "document",
    ".xls": "spreadsheet",
    ".xlsx": "spreadsheet",
    ".xml": "structured_data",
    ".txt": "text",
    ".htm": "web_document",
    ".html": "web_document",
    ".json": "data_index",
    ".sgml": "structured_data",
}


@dataclass
class FileEntry:
    """Single file entry in the corpus manifest."""

    file_path: str
    file_name: str
    extension: str
    size_bytes: int
    category: str  # "document", "spreadsheet", "structured_data", etc.
    relative_path: str
    parent_directory: str
    sha256: Optional[str] = None
    modified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "category": self.category,
            "relative_path": self.relative_path,
            "parent_directory": self.parent_directory,
            "sha256": self.sha256,
            "modified_at": (
                self.modified_at.isoformat() if self.modified_at else None
            ),
        }


@dataclass
class CorpusManifest:
    """Manifest of all files in the EDGAR corpus."""

    corpus_root: str
    scan_timestamp: datetime
    total_files: int = 0
    total_size_bytes: int = 0
    files: List[FileEntry] = field(default_factory=list)
    extension_counts: Dict[str, int] = field(default_factory=dict)
    category_counts: Dict[str, int] = field(default_factory=dict)
    directory_counts: Dict[str, int] = field(default_factory=dict)
    errors: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "corpus_root": self.corpus_root,
            "scan_timestamp": self.scan_timestamp.isoformat(),
            "total_files": self.total_files,
            "total_size_bytes": self.total_size_bytes,
            "total_size_mb": round(self.total_size_bytes / (1024 * 1024), 2),
            "extension_counts": self.extension_counts,
            "category_counts": self.category_counts,
            "directory_counts": self.directory_counts,
            "error_count": len(self.errors),
        }

    def get_files_by_extension(self, extension: str) -> List[FileEntry]:
        """Get all files with a specific extension."""
        ext = extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        return [f for f in self.files if f.extension == ext]

    def get_files_by_category(self, category: str) -> List[FileEntry]:
        """Get all files in a specific category."""
        return [f for f in self.files if f.category == category]

    def get_files_by_directory(self, directory: str) -> List[FileEntry]:
        """Get all files in a specific directory."""
        return [f for f in self.files if f.parent_directory == directory]


class CorpusScanner:
    """
    Scan raw SEC EDGAR filing corpus directories.

    Generates a manifest of all available filings for classification
    and ingestion into the JLAW forensic pipeline.

    Args:
        corpus_root: Root directory of the EDGAR filing corpus.
        compute_hashes: Whether to compute SHA-256 hashes (slower).
        extensions: Set of file extensions to include.
    """

    def __init__(
        self,
        corpus_root: Path,
        compute_hashes: bool = False,
        extensions: Optional[Set[str]] = None,
    ) -> None:
        self.corpus_root = Path(corpus_root)
        self.compute_hashes = compute_hashes
        self.extensions = extensions or SUPPORTED_EXTENSIONS

        if not self.corpus_root.exists():
            logger.warning("Corpus root does not exist: %s", self.corpus_root)

    def scan(self) -> CorpusManifest:
        """
        Scan the corpus directory and generate a manifest.

        Returns:
            CorpusManifest with all discovered files and statistics.
        """
        manifest = CorpusManifest(
            corpus_root=str(self.corpus_root),
            scan_timestamp=datetime.utcnow(),
        )

        if not self.corpus_root.exists():
            manifest.errors.append({
                "error": f"Corpus root not found: {self.corpus_root}",
                "type": "directory_not_found",
            })
            return manifest

        logger.info("Scanning corpus: %s", self.corpus_root)

        for file_path in self.corpus_root.rglob("*"):
            if not file_path.is_file():
                continue

            ext = file_path.suffix.lower()
            if ext not in self.extensions:
                continue

            try:
                stat = file_path.stat()
                relative = file_path.relative_to(self.corpus_root)
                parent_dir = str(relative.parent) if relative.parent != Path(".") else "root"

                entry = FileEntry(
                    file_path=str(file_path),
                    file_name=file_path.name,
                    extension=ext,
                    size_bytes=stat.st_size,
                    category=EXTENSION_CATEGORIES.get(ext, "other"),
                    relative_path=str(relative),
                    parent_directory=parent_dir,
                    modified_at=datetime.fromtimestamp(stat.st_mtime),
                )

                if self.compute_hashes:
                    entry.sha256 = self._compute_hash(file_path)

                manifest.files.append(entry)
                manifest.total_files += 1
                manifest.total_size_bytes += stat.st_size

                # Update counters
                manifest.extension_counts[ext] = (
                    manifest.extension_counts.get(ext, 0) + 1
                )
                manifest.category_counts[entry.category] = (
                    manifest.category_counts.get(entry.category, 0) + 1
                )
                manifest.directory_counts[parent_dir] = (
                    manifest.directory_counts.get(parent_dir, 0) + 1
                )

            except Exception as e:
                logger.warning("Error scanning %s: %s", file_path, e)
                manifest.errors.append({
                    "file": str(file_path),
                    "error": str(e),
                })

        logger.info(
            "Corpus scan complete: %d files, %.1f MB",
            manifest.total_files,
            manifest.total_size_bytes / (1024 * 1024),
        )

        return manifest

    def export_manifest(
        self,
        manifest: CorpusManifest,
        output_path: Path,
        include_file_list: bool = True,
    ) -> Path:
        """
        Export corpus manifest to JSON.

        Args:
            manifest: CorpusManifest to export.
            output_path: Output JSON file path.
            include_file_list: Whether to include full file listing.

        Returns:
            Path to exported file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = manifest.to_dict()
        if include_file_list:
            data["files"] = [f.to_dict() for f in manifest.files]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info("Manifest exported to %s", output_path)
        return output_path

    @staticmethod
    def _compute_hash(file_path: Path) -> Optional[str]:
        """Compute SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except OSError:
            return None
