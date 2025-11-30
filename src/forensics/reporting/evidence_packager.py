"""
Evidence Packager - Evidence Compilation and Export
====================================================

Compiles and packages evidence for forensic investigations.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib
import json
import zipfile
import shutil

logger = logging.getLogger(__name__)


@dataclass
class PackagedFile:
    """A file included in the evidence package."""
    original_path: str
    package_path: str
    file_hash: str
    file_size: int
    file_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceManifest:
    """Manifest for an evidence package."""
    package_id: str
    case_id: str
    created_at: datetime
    created_by: str
    files: List[PackagedFile] = field(default_factory=list)
    total_files: int = 0
    total_size: int = 0
    manifest_hash: str = ""


@dataclass
class EvidencePackage:
    """Complete evidence package."""
    package_id: str
    case_id: str
    manifest: EvidenceManifest
    package_path: Optional[Path] = None
    created_at: datetime = field(default_factory=datetime.now)


class EvidencePackager:
    """
    Evidence Packager
    
    Compiles and packages evidence for forensic investigations.
    
    Features:
    - Evidence file collection
    - Hash verification
    - Manifest generation
    - ZIP package creation
    - Chain of custody integration
    
    Example:
        packager = EvidencePackager()
        
        # Create package
        package = packager.create_package("CASE-001")
        
        # Add files
        packager.add_file(package.package_id, "/evidence/doc1.pdf")
        packager.add_file(package.package_id, "/evidence/doc2.pdf")
        
        # Build package
        zip_path = packager.build_package(package.package_id)
    """
    
    def __init__(
        self,
        output_dir: Optional[Path] = None,
        temp_dir: Optional[Path] = None
    ):
        """Initialize the evidence packager."""
        self.output_dir = output_dir or Path("./evidence_packages")
        self.temp_dir = temp_dir or Path("./temp_packaging")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self._packages: Dict[str, EvidencePackage] = {}
        
        logger.info("EvidencePackager initialized")
    
    def create_package(
        self,
        case_id: str,
        created_by: str = "System"
    ) -> EvidencePackage:
        """
        Create a new evidence package.
        
        Args:
            case_id: Case identifier
            created_by: Creator name
            
        Returns:
            Created evidence package
        """
        package_id = f"PKG-{case_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        manifest = EvidenceManifest(
            package_id=package_id,
            case_id=case_id,
            created_at=datetime.now(),
            created_by=created_by
        )
        
        package = EvidencePackage(
            package_id=package_id,
            case_id=case_id,
            manifest=manifest
        )
        
        self._packages[package_id] = package
        
        logger.info(f"Created evidence package: {package_id}")
        return package
    
    def add_file(
        self,
        package_id: str,
        file_path: str,
        package_subdir: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[PackagedFile]:
        """
        Add a file to the evidence package.
        
        Args:
            package_id: Package identifier
            file_path: Path to the file
            package_subdir: Subdirectory within package
            metadata: Additional file metadata
            
        Returns:
            Packaged file info
        """
        package = self._packages.get(package_id)
        if not package:
            logger.error(f"Package not found: {package_id}")
            return None
        
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        # Calculate hash
        file_hash = self._calculate_hash(path)
        
        # Determine package path
        if package_subdir:
            package_path = f"{package_subdir}/{path.name}"
        else:
            package_path = path.name
        
        # Determine file type
        file_type = self._get_file_type(path)
        
        packaged_file = PackagedFile(
            original_path=str(path.absolute()),
            package_path=package_path,
            file_hash=file_hash,
            file_size=path.stat().st_size,
            file_type=file_type,
            metadata=metadata or {}
        )
        
        package.manifest.files.append(packaged_file)
        package.manifest.total_files += 1
        package.manifest.total_size += packaged_file.file_size
        
        logger.debug(f"Added file to package: {path.name}")
        return packaged_file
    
    def add_directory(
        self,
        package_id: str,
        dir_path: str,
        package_subdir: str = "",
        extensions: Optional[List[str]] = None
    ) -> int:
        """
        Add all files from a directory to the package.
        
        Args:
            package_id: Package identifier
            dir_path: Directory path
            package_subdir: Subdirectory within package
            extensions: Optional file extensions filter
            
        Returns:
            Number of files added
        """
        path = Path(dir_path)
        if not path.is_dir():
            return 0
        
        count = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                if extensions and file_path.suffix.lower() not in extensions:
                    continue
                
                rel_path = file_path.relative_to(path)
                subdir = f"{package_subdir}/{rel_path.parent}" if package_subdir else str(rel_path.parent)
                
                if self.add_file(package_id, str(file_path), subdir):
                    count += 1
        
        return count
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type from extension."""
        ext = file_path.suffix.lower()
        type_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.html': 'text/html',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
        }
        return type_map.get(ext, 'application/octet-stream')
    
    def build_package(
        self,
        package_id: str,
        include_manifest: bool = True,
        compress: bool = True
    ) -> Optional[Path]:
        """
        Build the evidence package ZIP file.
        
        Args:
            package_id: Package identifier
            include_manifest: Include manifest.json
            compress: Use compression
            
        Returns:
            Path to created package
        """
        package = self._packages.get(package_id)
        if not package:
            return None
        
        # Create temp directory for staging
        staging_dir = self.temp_dir / package_id
        staging_dir.mkdir(exist_ok=True)
        
        try:
            # Copy files to staging
            for packaged_file in package.manifest.files:
                src_path = Path(packaged_file.original_path)
                if not src_path.exists():
                    logger.warning(f"File not found: {src_path}")
                    continue
                
                dest_path = staging_dir / packaged_file.package_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
            
            # Generate manifest
            if include_manifest:
                manifest_path = staging_dir / "manifest.json"
                self._write_manifest(package.manifest, manifest_path)
                package.manifest.manifest_hash = self._calculate_hash(manifest_path)
            
            # Create ZIP
            zip_path = self.output_dir / f"{package_id}.zip"
            compression = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
            
            with zipfile.ZipFile(zip_path, 'w', compression) as zf:
                for file_path in staging_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(staging_dir)
                        zf.write(file_path, arcname)
            
            package.package_path = zip_path
            
            logger.info(f"Built evidence package: {zip_path}")
            return zip_path
            
        finally:
            # Cleanup staging
            shutil.rmtree(staging_dir, ignore_errors=True)
    
    def _write_manifest(self, manifest: EvidenceManifest, output_path: Path) -> None:
        """Write manifest to JSON file."""
        manifest_dict = {
            "package_id": manifest.package_id,
            "case_id": manifest.case_id,
            "created_at": manifest.created_at.isoformat(),
            "created_by": manifest.created_by,
            "total_files": manifest.total_files,
            "total_size": manifest.total_size,
            "files": [
                {
                    "original_path": f.original_path,
                    "package_path": f.package_path,
                    "file_hash": f.file_hash,
                    "file_size": f.file_size,
                    "file_type": f.file_type,
                    "metadata": f.metadata
                }
                for f in manifest.files
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(manifest_dict, f, indent=2)
    
    def get_package(self, package_id: str) -> Optional[EvidencePackage]:
        """Get a package by ID."""
        return self._packages.get(package_id)
    
    def verify_package(self, package_path: Path) -> Dict[str, Any]:
        """
        Verify an evidence package.
        
        Args:
            package_path: Path to package ZIP
            
        Returns:
            Verification result
        """
        result = {
            "valid": True,
            "files_verified": 0,
            "files_failed": 0,
            "errors": []
        }
        
        try:
            with zipfile.ZipFile(package_path, 'r') as zf:
                # Read manifest
                manifest_data = json.loads(zf.read("manifest.json"))
                
                for file_info in manifest_data.get("files", []):
                    package_path_str = file_info["package_path"]
                    expected_hash = file_info["file_hash"]
                    
                    try:
                        file_data = zf.read(package_path_str)
                        actual_hash = hashlib.sha256(file_data).hexdigest()
                        
                        if actual_hash == expected_hash:
                            result["files_verified"] += 1
                        else:
                            result["files_failed"] += 1
                            result["errors"].append(f"Hash mismatch: {package_path_str}")
                            result["valid"] = False
                            
                    except KeyError:
                        result["files_failed"] += 1
                        result["errors"].append(f"File missing: {package_path_str}")
                        result["valid"] = False
                        
        except Exception as e:
            result["valid"] = False
            result["errors"].append(str(e))
        
        return result
    
    def cleanup(self, package_id: str) -> bool:
        """Remove a package."""
        if package_id in self._packages:
            package = self._packages[package_id]
            if package.package_path and package.package_path.exists():
                package.package_path.unlink()
            del self._packages[package_id]
            return True
        return False
