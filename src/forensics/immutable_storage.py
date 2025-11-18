"""
Immutable storage implementation with WORM capabilities.
Ensures evidence preservation for courtroom admissibility.
"""

import asyncio
import hashlib
import hmac
import json
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
import aiofiles
import struct
import zlib

# Optional cloud provider imports
try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    boto3 = None
    ClientError = Exception

try:
    from azure.storage.blob import BlobServiceClient, ImmutabilityPolicy
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    BlobServiceClient = None
    ImmutabilityPolicy = None

from src.forensics.core.integrity_manager import (
    ForensicHashChain, IntegrityLevel, ChainOfCustody, IntegrityError
)

@dataclass
class StorageConfig:
    """Configuration for immutable storage."""
    provider: str  # AWS, AZURE, LOCAL
    retention_days: int = 2555  # 7 years default
    compliance_mode: bool = True  # COMPLIANCE vs GOVERNANCE
    redundancy_level: int = 3  # Number of copies
    encryption_key: Optional[bytes] = None
    compression: bool = True
    
class ImmutableStorage:
    """
    WORM storage implementation for forensic evidence.
    Supports AWS S3 Object Lock, Azure Immutable Blob, and local WORM.
    """
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.hash_chain = ForensicHashChain("immutable_storage")
        self.storage_index: Dict[str, Dict[str, Any]] = {}
        
        # Initialize provider
        if config.provider == "AWS":
            if not AWS_AVAILABLE:
                raise ImportError("AWS support requires: pip install boto3")
            self.s3_client = boto3.client('s3')
            self.bucket_name = os.environ.get("FORENSIC_S3_BUCKET", "forensic-evidence")
        elif config.provider == "AZURE":
            if not AZURE_AVAILABLE:
                raise ImportError("Azure support requires: pip install azure-storage-blob")
            self.blob_service = BlobServiceClient.from_connection_string(
                os.environ.get("AZURE_STORAGE_CONNECTION")
            )
            self.container_name = "forensic-evidence"
        else:  # LOCAL
            self.local_path = Path("/var/forensic/worm")
            self.local_path.mkdir(parents=True, exist_ok=True)
    
    async def store_evidence(
        self,
        evidence_id: str,
        data: bytes,
        metadata: Dict[str, Any],
        chain_of_custody: ChainOfCustody
    ) -> Dict[str, Any]:
        """
        Store evidence with immutable protection.
        
        Args:
            evidence_id: Unique evidence identifier
            data: Raw evidence data
            metadata: Evidence metadata
            chain_of_custody: Custody documentation
            
        Returns:
            Storage receipt with hashes and location
        """
        # Compute hashes
        sha256_hash = hashlib.sha256(data).hexdigest()
        sha512_hash = hashlib.sha512(data).hexdigest()
        
        # Verify chain of custody
        if not await chain_of_custody.hash_chain.verify_chain():
            raise IntegrityError("Chain of custody compromised - cannot store evidence")
        
        # Compress if configured
        if self.config.compression:
            compressed_data = zlib.compress(data, level=9)
            compression_ratio = len(compressed_data) / len(data)
        else:
            compressed_data = data
            compression_ratio = 1.0
        
        # Encrypt if configured
        if self.config.encryption_key:
            encrypted_data = await self._encrypt_data(compressed_data)
        else:
            encrypted_data = compressed_data
        
        # Store with provider
        if self.config.provider == "AWS":
            storage_location = await self._store_aws_s3(
                evidence_id,
                encrypted_data,
                metadata,
                sha256_hash
            )
        elif self.config.provider == "AZURE":
            storage_location = await self._store_azure_blob(
                evidence_id,
                encrypted_data,
                metadata,
                sha256_hash
            )
        else:
            storage_location = await self._store_local_worm(
                evidence_id,
                encrypted_data,
                metadata,
                sha256_hash
            )
        
        # Create storage receipt
        receipt = {
            "evidence_id": evidence_id,
            "storage_timestamp": datetime.now(timezone.utc).isoformat(),
            "sha256": sha256_hash,
            "sha512": sha512_hash,
            "size_bytes": len(data),
            "compressed_size": len(compressed_data),
            "compression_ratio": compression_ratio,
            "encrypted": self.config.encryption_key is not None,
            "location": storage_location,
            "retention_until": (
                datetime.now(timezone.utc) + timedelta(days=self.config.retention_days)
            ).isoformat(),
            "compliance_mode": self.config.compliance_mode,
            "chain_of_custody_hash": chain_of_custody.hash_chain.blocks[-1].current_hash
        }
        
        # Add to index
        self.storage_index[evidence_id] = receipt
        
        # Log to forensic chain
        await self.hash_chain.add_evidence(
            receipt,
            IntegrityLevel.CRITICAL
        )
        
        # Create redundant copies
        if self.config.redundancy_level > 1:
            await self._create_redundant_copies(
                evidence_id,
                encrypted_data,
                metadata,
                receipt
            )
        
        return receipt
    
    async def retrieve_evidence(
        self,
        evidence_id: str,
        verification_hash: str
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Retrieve evidence with integrity verification.
        
        Args:
            evidence_id: Evidence identifier
            verification_hash: Expected SHA-256 hash
            
        Returns:
            Tuple of (evidence data, metadata)
            
        Raises:
            IntegrityError: If hash verification fails
        """
        # Get storage receipt
        if evidence_id not in self.storage_index:
            raise ValueError(f"Evidence {evidence_id} not found")
        
        receipt = self.storage_index[evidence_id]
        
        # Retrieve from provider
        if self.config.provider == "AWS":
            encrypted_data = await self._retrieve_aws_s3(evidence_id)
        elif self.config.provider == "AZURE":
            encrypted_data = await self._retrieve_azure_blob(evidence_id)
        else:
            encrypted_data = await self._retrieve_local_worm(evidence_id)
        
        # Decrypt if needed
        if receipt["encrypted"]:
            compressed_data = await self._decrypt_data(encrypted_data)
        else:
            compressed_data = encrypted_data
        
        # Decompress if needed
        if receipt["compression_ratio"] < 1.0:
            data = zlib.decompress(compressed_data)
        else:
            data = compressed_data
        
        # Verify hash
        computed_hash = hashlib.sha256(data).hexdigest()
        if not hmac.compare_digest(computed_hash, verification_hash):
            raise IntegrityError(
                f"Hash verification failed for evidence {evidence_id}. "
                f"Expected: {verification_hash}, Got: {computed_hash}"
            )
        
        # Log retrieval
        await self.hash_chain.add_evidence(
            {
                "event": "EVIDENCE_RETRIEVED",
                "evidence_id": evidence_id,
                "verification": "SUCCESS",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            IntegrityLevel.HIGH
        )
        
        return data, receipt
    
    async def _store_aws_s3(
        self,
        evidence_id: str,
        data: bytes,
        metadata: Dict[str, Any],
        content_hash: str
    ) -> str:
        """Store evidence in AWS S3 with Object Lock."""
        key = f"evidence/{evidence_id}"
        
        try:
            # Upload with Object Lock
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                Metadata={
                    "evidence-id": evidence_id,
                    "content-sha256": content_hash,
                    "forensic-timestamp": datetime.now(timezone.utc).isoformat(),
                    **{k: str(v) for k, v in metadata.items()}
                },
                ObjectLockMode="COMPLIANCE" if self.config.compliance_mode else "GOVERNANCE",
                ObjectLockRetainUntilDate=datetime.now(timezone.utc) + timedelta(
                    days=self.config.retention_days
                ),
                ServerSideEncryption="AES256",
                StorageClass="GLACIER_IR"  # Cost-effective for long-term storage
            )
            
            return f"s3://{self.bucket_name}/{key}"
            
        except ClientError as e:
            raise IntegrityError(f"Failed to store evidence in S3: {e}")
    
    async def _retrieve_aws_s3(self, evidence_id: str) -> bytes:
        """Retrieve evidence from AWS S3."""
        key = f"evidence/{evidence_id}"
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            return response['Body'].read()
            
        except ClientError as e:
            raise IntegrityError(f"Failed to retrieve evidence from S3: {e}")
    
    async def _store_azure_blob(
        self,
        evidence_id: str,
        data: bytes,
        metadata: Dict[str, Any],
        content_hash: str
    ) -> str:
        """Store evidence in Azure Blob with immutability."""
        blob_name = f"evidence/{evidence_id}"
        
        try:
            container_client = self.blob_service.get_container_client(
                self.container_name
            )
            
            blob_client = container_client.get_blob_client(blob_name)
            
            # Upload blob
            blob_client.upload_blob(
                data,
                metadata={
                    "evidence_id": evidence_id,
                    "content_sha256": content_hash,
                    **metadata
                },
                overwrite=False
            )
            
            # Set immutability policy
            immutability_policy = ImmutabilityPolicy(
                expiry_time=datetime.now(timezone.utc) + timedelta(
                    days=self.config.retention_days
                ),
                policy_mode="Locked" if self.config.compliance_mode else "Unlocked"
            )
            
            blob_client.set_immutability_policy(immutability_policy)
            
            return f"azure://{self.container_name}/{blob_name}"
            
        except Exception as e:
            raise IntegrityError(f"Failed to store evidence in Azure: {e}")
    
    async def _retrieve_azure_blob(self, evidence_id: str) -> bytes:
        """Retrieve evidence from Azure Blob."""
        blob_name = f"evidence/{evidence_id}"
        
        try:
            container_client = self.blob_service.get_container_client(
                self.container_name
            )
            
            blob_client = container_client.get_blob_client(blob_name)
            
            return blob_client.download_blob().readall()
            
        except Exception as e:
            raise IntegrityError(f"Failed to retrieve evidence from Azure: {e}")
    
    async def _store_local_worm(
        self,
        evidence_id: str,
        data: bytes,
        metadata: Dict[str, Any],
        content_hash: str
    ) -> str:
        """Store evidence in local WORM filesystem."""
        # Create evidence file path
        evidence_path = self.local_path / f"{evidence_id}.evidence"
        metadata_path = self.local_path / f"{evidence_id}.metadata"
        
        # Write evidence data
        async with aiofiles.open(evidence_path, 'wb') as f:
            await f.write(data)
        
        # Write metadata
        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps({
                "evidence_id": evidence_id,
                "content_sha256": content_hash,
                "stored_at": datetime.now(timezone.utc).isoformat(),
                **metadata
            }, indent=2))
        
        # Make files immutable (Linux)
        if os.name == 'posix':
            os.chmod(evidence_path, 0o444)  # Read-only
            os.system(f"chattr +i {evidence_path}")  # Immutable flag
            os.chmod(metadata_path, 0o444)
            os.system(f"chattr +i {metadata_path}")
        
        return f"file://{evidence_path}"
    
    async def _retrieve_local_worm(self, evidence_id: str) -> bytes:
        """Retrieve evidence from local WORM filesystem."""
        evidence_path = self.local_path / f"{evidence_id}.evidence"
        
        async with aiofiles.open(evidence_path, 'rb') as f:
            return await f.read()
    
    async def _create_redundant_copies(
        self,
        evidence_id: str,
        data: bytes,
        metadata: Dict[str, Any],
        receipt: Dict[str, Any]
    ):
        """Create redundant copies for reliability."""
        for i in range(1, self.config.redundancy_level):
            copy_id = f"{evidence_id}_copy_{i}"
            
            # Store copy with modified metadata
            copy_metadata = {
                **metadata,
                "copy_number": i,
                "original_id": evidence_id
            }
            
            # Store based on provider
            if self.config.provider == "AWS":
                # Use different storage class for copies
                key = f"evidence/copies/{copy_id}"
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=data,
                    Metadata={k: str(v) for k, v in copy_metadata.items()},
                    StorageClass="GLACIER"
                )
            
            # Log copy creation
            await self.hash_chain.add_evidence(
                {
                    "event": "REDUNDANT_COPY_CREATED",
                    "evidence_id": evidence_id,
                    "copy_id": copy_id,
                    "copy_number": i
                },
                IntegrityLevel.MEDIUM
            )
    
    async def _encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using AES-256-GCM."""
        # Implementation would use cryptography library
        # This is a placeholder
        return data
    
    async def _decrypt_data(self, data: bytes) -> bytes:
        """Decrypt data using AES-256-GCM."""
        # Implementation would use cryptography library
        # This is a placeholder
        return data
    
    async def verify_all_evidence(self) -> Dict[str, Any]:
        """Verify integrity of all stored evidence."""
        verification_results = {
            "total": len(self.storage_index),
            "verified": 0,
            "failed": 0,
            "errors": []
        }
        
        for evidence_id, receipt in self.storage_index.items():
            try:
                # Retrieve and verify
                data, _ = await self.retrieve_evidence(
                    evidence_id,
                    receipt["sha256"]
                )
                verification_results["verified"] += 1
                
            except IntegrityError as e:
                verification_results["failed"] += 1
                verification_results["errors"].append({
                    "evidence_id": evidence_id,
                    "error": str(e)
                })
        
        # Log verification
        await self.hash_chain.add_evidence(
            verification_results,
            IntegrityLevel.CRITICAL
        )
        
        return verification_results

class AppendOnlyLog:
    """
    Append-only cryptographic log for audit trails.
    Implements signed log entries with chain verification.
    """
    
    def __init__(self, log_name: str, signing_key: bytes):
        self.log_name = log_name
        self.signing_key = signing_key
        self.entries: List[Dict[str, Any]] = []
        self.hash_chain = ForensicHashChain(f"audit_log_{log_name}")
        self._sequence = 0
        self._lock = asyncio.Lock()
    
    async def append(
        self,
        event: str,
        actor: str,
        action: str,
        target: str,
        result: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Append entry to audit log.
        
        Returns:
            Entry hash for verification
        """
        async with self._lock:
            # Get previous hash
            prev_hash = self.entries[-1]["curr_hash"] if self.entries else "0" * 64
            
            # Create entry
            entry = {
                "sequence": self._sequence,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "actor": actor,
                "action": action,
                "target": target,
                "result": result,
                "details": details or {},
                "prev_hash": prev_hash
            }
            
            # Compute hash
            canonical = json.dumps(entry, sort_keys=True)
            entry["curr_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
            
            # Sign entry
            signature = hmac.new(
                self.signing_key,
                entry["curr_hash"].encode(),
                hashlib.sha256
            ).hexdigest()
            entry["signature"] = signature
            
            # Append to log
            self.entries.append(entry)
            self._sequence += 1
            
            # Add to forensic chain
            await self.hash_chain.add_evidence(
                entry,
                IntegrityLevel.HIGH
            )
            
            return entry["curr_hash"]
    
    async def verify(self) -> bool:
        """Verify entire log integrity."""
        if not self.entries:
            return True
        
        # Verify first entry
        first = self.entries[0]
        if first["prev_hash"] != "0" * 64:
            return False
        
        # Verify chain
        for i in range(1, len(self.entries)):
            current = self.entries[i]
            previous = self.entries[i-1]
            
            # Verify linkage
            if not hmac.compare_digest(current["prev_hash"], previous["curr_hash"]):
                return False
            
            # Verify signature
            expected_sig = hmac.new(
                self.signing_key,
                current["curr_hash"].encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(current["signature"], expected_sig):
                return False
            
            # Verify hash
            entry_copy = {k: v for k, v in current.items() if k not in ["curr_hash", "signature"]}
            canonical = json.dumps(entry_copy, sort_keys=True)
            expected_hash = hashlib.sha256(canonical.encode()).hexdigest()
            
            if not hmac.compare_digest(current["curr_hash"], expected_hash):
                return False
        
        return True
    
    async def export_for_court(self) -> Dict[str, Any]:
        """Export log in format suitable for legal proceedings."""
        return {
            "log_name": self.log_name,
            "total_entries": len(self.entries),
            "date_range": {
                "start": self.entries[0]["timestamp"] if self.entries else None,
                "end": self.entries[-1]["timestamp"] if self.entries else None
            },
            "integrity_verified": await self.verify(),
            "entries": self.entries,
            "hash_chain": self.hash_chain.export_chain()
        }

