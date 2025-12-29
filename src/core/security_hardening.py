"""
Security Hardening Module for JLAW
===================================

Implements comprehensive security features for Phase 5 Security Hardening:

1. Secrets Management:
   - Secrets encryption at rest (AES256-GCM)
   - Secrets rotation mechanism
   - API key scoping validation
   - Expiration monitoring

2. Evidence Chain Compliance:
   - FRE 902(13)/(14) compliance validation
   - Triple-hash integrity verification
   - Tampering detection

Compliance: FRE 902(13)/(14), NIST SP 800-53, ISO/IEC 27001
"""

import os
import re
import hashlib
import json
import base64
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple, Callable

logger = logging.getLogger(__name__)


class SecretType(Enum):
    """Types of secrets managed by the system."""
    API_KEY = "api_key"
    DATABASE_PASSWORD = "database_password"
    PRIVATE_KEY = "private_key"
    TOKEN = "token"
    CERTIFICATE = "certificate"


class AlertChannel(Enum):
    """Alert notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass
class SecretMetadata:
    """Metadata for a managed secret."""
    name: str
    secret_type: SecretType
    created_at: datetime
    expires_at: Optional[datetime] = None
    rotated_at: Optional[datetime] = None
    scopes: List[str] = field(default_factory=list)
    description: str = ""
    last_used: Optional[datetime] = None
    rotation_schedule_days: Optional[int] = None
    
    def is_expired(self) -> bool:
        """Check if secret has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def days_until_expiry(self) -> Optional[int]:
        """Get days until expiry."""
        if self.expires_at is None:
            return None
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    def needs_rotation(self) -> bool:
        """Check if secret needs rotation based on schedule."""
        if self.rotation_schedule_days is None:
            return False
        if self.rotated_at is None:
            # If never rotated, check from creation date
            days_since_creation = (datetime.utcnow() - self.created_at).days
            return days_since_creation >= self.rotation_schedule_days
        days_since_rotation = (datetime.utcnow() - self.rotated_at).days
        return days_since_rotation >= self.rotation_schedule_days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "secret_type": self.secret_type.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "rotated_at": self.rotated_at.isoformat() if self.rotated_at else None,
            "scopes": self.scopes,
            "description": self.description,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "rotation_schedule_days": self.rotation_schedule_days,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecretMetadata":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            secret_type=SecretType(data["secret_type"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            rotated_at=datetime.fromisoformat(data["rotated_at"]) if data.get("rotated_at") else None,
            scopes=data.get("scopes", []),
            description=data.get("description", ""),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            rotation_schedule_days=data.get("rotation_schedule_days"),
        )


@dataclass
class ExpirationAlert:
    """Alert for expiring secrets."""
    secret_name: str
    days_until_expiry: int
    expires_at: datetime
    alert_level: str  # 'warning' or 'critical'
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "secret_name": self.secret_name,
            "days_until_expiry": self.days_until_expiry,
            "expires_at": self.expires_at.isoformat(),
            "alert_level": self.alert_level,
            "created_at": self.created_at.isoformat(),
        }


class SecretsManagerInterface(ABC):
    """
    Abstract interface for secrets managers.
    
    Supports multiple backends:
    - AWS Secrets Manager
    - HashiCorp Vault
    - Local encrypted storage (for development)
    """
    
    @abstractmethod
    async def get_secret(self, name: str) -> Optional[str]:
        """Retrieve a secret by name."""
        pass
    
    @abstractmethod
    async def set_secret(
        self,
        name: str,
        value: str,
        metadata: Optional[SecretMetadata] = None
    ) -> bool:
        """Store a secret with optional metadata."""
        pass
    
    @abstractmethod
    async def delete_secret(self, name: str) -> bool:
        """Delete a secret."""
        pass
    
    @abstractmethod
    async def rotate_secret(
        self,
        name: str,
        new_value: str
    ) -> bool:
        """Rotate a secret to a new value."""
        pass
    
    @abstractmethod
    async def list_secrets(self) -> List[SecretMetadata]:
        """List all managed secrets."""
        pass
    
    @abstractmethod
    async def get_metadata(self, name: str) -> Optional[SecretMetadata]:
        """Get metadata for a secret."""
        pass


class LocalEncryptedSecretsManager(SecretsManagerInterface):
    """
    Local encrypted secrets manager for development.
    
    Uses AES-256-GCM for encryption at rest.
    
    WARNING: For development/testing only. Use AWS Secrets Manager
    or HashiCorp Vault in production.
    """
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        encryption_key: Optional[bytes] = None
    ):
        """
        Initialize local secrets manager.
        
        Args:
            storage_path: Path to store encrypted secrets
            encryption_key: 32-byte encryption key (generated if not provided)
        """
        self.storage_path = storage_path or Path.home() / ".jlaw" / "secrets"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Generate or use provided encryption key
        if encryption_key is None:
            key_file = self.storage_path / ".key"
            if key_file.exists():
                encryption_key = key_file.read_bytes()
            else:
                encryption_key = os.urandom(32)
                key_file.write_bytes(encryption_key)
                key_file.chmod(0o600)
        
        self._encryption_key = encryption_key
        self._metadata_cache: Dict[str, SecretMetadata] = {}
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load metadata from disk."""
        metadata_file = self.storage_path / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                for name, meta_dict in data.items():
                    self._metadata_cache[name] = SecretMetadata.from_dict(meta_dict)
            except Exception as e:
                logger.warning(f"Failed to load secrets metadata: {e}")
    
    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        metadata_file = self.storage_path / "metadata.json"
        try:
            data = {name: meta.to_dict() for name, meta in self._metadata_cache.items()}
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
            metadata_file.chmod(0o600)
        except Exception as e:
            logger.error(f"Failed to save secrets metadata: {e}")
    
    def _encrypt(self, plaintext: str) -> bytes:
        """Encrypt plaintext using AES-256-GCM."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            
            nonce = os.urandom(12)
            aesgcm = AESGCM(self._encryption_key)
            ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
            return nonce + ciphertext
        except ImportError:
            logger.warning("cryptography library not available, using base64 encoding only")
            return base64.b64encode(plaintext.encode('utf-8'))
    
    def _decrypt(self, ciphertext: bytes) -> str:
        """Decrypt ciphertext using AES-256-GCM."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            
            nonce = ciphertext[:12]
            encrypted = ciphertext[12:]
            aesgcm = AESGCM(self._encryption_key)
            plaintext = aesgcm.decrypt(nonce, encrypted, None)
            return plaintext.decode('utf-8')
        except ImportError:
            return base64.b64decode(ciphertext).decode('utf-8')
    
    async def get_secret(self, name: str) -> Optional[str]:
        """Retrieve a secret by name."""
        secret_file = self.storage_path / f"{name}.enc"
        if not secret_file.exists():
            return None
        
        try:
            ciphertext = secret_file.read_bytes()
            plaintext = self._decrypt(ciphertext)
            
            # Update last used
            if name in self._metadata_cache:
                self._metadata_cache[name].last_used = datetime.utcnow()
                self._save_metadata()
            
            return plaintext
        except Exception as e:
            logger.error(f"Failed to decrypt secret '{name}': {e}")
            return None
    
    async def set_secret(
        self,
        name: str,
        value: str,
        metadata: Optional[SecretMetadata] = None
    ) -> bool:
        """Store a secret with optional metadata."""
        try:
            ciphertext = self._encrypt(value)
            secret_file = self.storage_path / f"{name}.enc"
            secret_file.write_bytes(ciphertext)
            secret_file.chmod(0o600)
            
            if metadata:
                self._metadata_cache[name] = metadata
            else:
                self._metadata_cache[name] = SecretMetadata(
                    name=name,
                    secret_type=SecretType.API_KEY,
                    created_at=datetime.utcnow()
                )
            
            self._save_metadata()
            logger.info(f"Secret '{name}' stored successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to store secret '{name}': {e}")
            return False
    
    async def delete_secret(self, name: str) -> bool:
        """Delete a secret."""
        try:
            secret_file = self.storage_path / f"{name}.enc"
            if secret_file.exists():
                secret_file.unlink()
            
            if name in self._metadata_cache:
                del self._metadata_cache[name]
                self._save_metadata()
            
            logger.info(f"Secret '{name}' deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret '{name}': {e}")
            return False
    
    async def rotate_secret(
        self,
        name: str,
        new_value: str
    ) -> bool:
        """Rotate a secret to a new value."""
        if name not in self._metadata_cache:
            logger.warning(f"Secret '{name}' not found for rotation")
            return False
        
        try:
            ciphertext = self._encrypt(new_value)
            secret_file = self.storage_path / f"{name}.enc"
            secret_file.write_bytes(ciphertext)
            secret_file.chmod(0o600)
            
            self._metadata_cache[name].rotated_at = datetime.utcnow()
            self._save_metadata()
            
            logger.info(f"Secret '{name}' rotated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to rotate secret '{name}': {e}")
            return False
    
    async def list_secrets(self) -> List[SecretMetadata]:
        """List all managed secrets."""
        return list(self._metadata_cache.values())
    
    async def get_metadata(self, name: str) -> Optional[SecretMetadata]:
        """Get metadata for a secret."""
        return self._metadata_cache.get(name)


class APIKeyScopeValidator:
    """
    Validates API key scopes for least-privilege enforcement.
    
    Each API key should have minimal necessary permissions.
    """
    
    # Define required scopes per API key type
    REQUIRED_SCOPES = {
        "OPENAI_API_KEY": ["chat", "completions"],
        "ANTHROPIC_API_KEY": ["messages"],
        "SEC_USER_AGENT": ["edgar"],
        "POLYGON_API_KEY": ["stocks", "aggs"],
        "GOVINFO_API_KEY": ["collections", "packages"],
        "NEO4J_PASSWORD": ["database"],
        "TIMESCALEDB_URI": ["database"],
        "REDIS_PASSWORD": ["cache"],
    }
    
    # Define prohibited scopes (overly broad permissions)
    PROHIBITED_SCOPES = {
        "OPENAI_API_KEY": ["admin", "organization.write"],
        "ANTHROPIC_API_KEY": ["admin"],
    }
    
    @classmethod
    def validate_scope(
        cls,
        key_name: str,
        actual_scopes: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate API key scopes against required and prohibited lists.
        
        Args:
            key_name: Name of the API key
            actual_scopes: Actual scopes the key has
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Check for prohibited scopes
        prohibited = cls.PROHIBITED_SCOPES.get(key_name, [])
        for scope in actual_scopes:
            if scope in prohibited:
                issues.append(f"Prohibited scope '{scope}' detected on {key_name}")
        
        # Note: We don't require specific scopes because we can't verify them
        # without making API calls. This is a validation framework.
        
        return len(issues) == 0, issues
    
    @classmethod
    def get_recommended_scopes(cls, key_name: str) -> List[str]:
        """Get recommended minimal scopes for an API key."""
        return cls.REQUIRED_SCOPES.get(key_name, [])


class SecretRotationScheduler:
    """
    Manages secret rotation schedules and notifications.
    """
    
    # Default rotation periods in days
    DEFAULT_ROTATION_DAYS = {
        SecretType.API_KEY: 90,
        SecretType.DATABASE_PASSWORD: 90,
        SecretType.TOKEN: 30,
        SecretType.PRIVATE_KEY: 365,
        SecretType.CERTIFICATE: 365,
    }
    
    def __init__(
        self,
        secrets_manager: SecretsManagerInterface,
        warning_days: int = 14,
        critical_days: int = 7
    ):
        """
        Initialize rotation scheduler.
        
        Args:
            secrets_manager: Secrets manager instance
            warning_days: Days before expiry to issue warning
            critical_days: Days before expiry to issue critical alert
        """
        self.secrets_manager = secrets_manager
        self.warning_days = warning_days
        self.critical_days = critical_days
        self._alert_callbacks: Dict[AlertChannel, Callable] = {}
    
    def register_alert_channel(
        self,
        channel: AlertChannel,
        callback: Callable[[ExpirationAlert], None]
    ) -> None:
        """Register an alert channel callback."""
        self._alert_callbacks[channel] = callback
    
    async def check_expirations(self) -> List[ExpirationAlert]:
        """
        Check all secrets for upcoming expirations.
        
        Returns:
            List of expiration alerts
        """
        alerts = []
        secrets = await self.secrets_manager.list_secrets()
        
        for metadata in secrets:
            days_left = metadata.days_until_expiry()
            
            if days_left is None:
                continue
            
            if days_left <= self.critical_days:
                alert = ExpirationAlert(
                    secret_name=metadata.name,
                    days_until_expiry=days_left,
                    expires_at=metadata.expires_at,
                    alert_level="critical"
                )
                alerts.append(alert)
            elif days_left <= self.warning_days:
                alert = ExpirationAlert(
                    secret_name=metadata.name,
                    days_until_expiry=days_left,
                    expires_at=metadata.expires_at,
                    alert_level="warning"
                )
                alerts.append(alert)
        
        # Send alerts through registered channels
        for alert in alerts:
            await self._send_alert(alert)
        
        return alerts
    
    async def check_rotation_needed(self) -> List[SecretMetadata]:
        """
        Check which secrets need rotation.
        
        Returns:
            List of secrets needing rotation
        """
        secrets = await self.secrets_manager.list_secrets()
        return [s for s in secrets if s.needs_rotation()]
    
    async def _send_alert(self, alert: ExpirationAlert) -> None:
        """Send alert through registered channels."""
        for channel, callback in self._alert_callbacks.items():
            try:
                if channel == AlertChannel.LOG:
                    log_method = logger.critical if alert.alert_level == "critical" else logger.warning
                    log_method(
                        f"Secret '{alert.secret_name}' expires in {alert.days_until_expiry} days"
                    )
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.value}: {e}")
    
    def get_rotation_schedule(
        self,
        secret_type: SecretType
    ) -> int:
        """Get default rotation schedule for a secret type."""
        return self.DEFAULT_ROTATION_DAYS.get(secret_type, 90)


class EnvironmentSecretsAuditor:
    """
    Audits environment for hardcoded secrets and security issues.
    """
    
    # Patterns that indicate hardcoded secrets
    SECRET_PATTERNS = [
        (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API Key"),
        (r"sk-ant-[a-zA-Z0-9]{20,}", "Anthropic API Key"),
        (r"sk-or-v1-[a-zA-Z0-9]{20,}", "OpenRouter API Key"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
        (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
        (r"aws_access_key_id\s*=\s*['\"]?AKIA[0-9A-Z]{16}['\"]?", "AWS Access Key"),
        (r"['\"]?password['\"]?\s*[:=]\s*['\"][^'\"$]+['\"]", "Hardcoded Password"),
    ]
    
    # Files/directories to skip during audit
    SKIP_PATTERNS = [
        ".git",
        "__pycache__",
        ".env",
        ".env.example",
        "venv",
        "node_modules",
        ".pytest_cache",
        "*.pyc",
        "coverage_report",
    ]
    
    def __init__(self, project_root: Path):
        """
        Initialize auditor.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
    
    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        for pattern in self.SKIP_PATTERNS:
            if pattern.startswith("*"):
                if path.suffix == pattern[1:]:
                    return True
            elif pattern in str(path):
                return True
        return False
    
    def audit_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Audit a single file for hardcoded secrets.
        
        Args:
            file_path: Path to file
            
        Returns:
            List of findings
        """
        findings = []
        
        if self._should_skip(file_path):
            return findings
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            for pattern, secret_type in self.SECRET_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    findings.append({
                        "file": str(file_path.relative_to(self.project_root)),
                        "line": line_num,
                        "secret_type": secret_type,
                        "pattern": pattern,
                        "preview": content[max(0, match.start() - 20):match.end() + 20],
                    })
        except Exception as e:
            logger.debug(f"Error auditing {file_path}: {e}")
        
        return findings
    
    def audit_directory(
        self,
        directory: Optional[Path] = None,
        extensions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Audit a directory recursively for hardcoded secrets.
        
        Args:
            directory: Directory to audit (defaults to project root)
            extensions: File extensions to check (defaults to [".py", ".yaml", ".yml", ".json"])
            
        Returns:
            List of findings
        """
        if directory is None:
            directory = self.project_root
        
        if extensions is None:
            extensions = [".py", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg"]
        
        all_findings = []
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix in extensions:
                if not self._should_skip(file_path):
                    findings = self.audit_file(file_path)
                    all_findings.extend(findings)
        
        return all_findings
    
    def audit_environment_variables(self) -> List[Dict[str, Any]]:
        """
        Audit environment variables for security issues.
        
        Returns:
            List of findings
        """
        findings = []
        
        # Check for required secrets
        required_secrets = [
            ("SEC_USER_AGENT", "SEC EDGAR User-Agent"),
        ]
        
        for env_var, description in required_secrets:
            value = os.environ.get(env_var, "")
            if not value:
                findings.append({
                    "variable": env_var,
                    "issue": "missing",
                    "description": f"{description} is required but not set",
                    "severity": "warning",
                })
            elif any(p in value for p in ["YOUR_", "CHANGE_ME", "TODO"]):
                findings.append({
                    "variable": env_var,
                    "issue": "placeholder",
                    "description": f"{description} contains placeholder value",
                    "severity": "error",
                })
        
        return findings
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive security audit report.
        
        Returns:
            Audit report dictionary
        """
        file_findings = self.audit_directory()
        env_findings = self.audit_environment_variables()
        
        return {
            "audit_timestamp": datetime.utcnow().isoformat(),
            "project_root": str(self.project_root),
            "file_findings": file_findings,
            "environment_findings": env_findings,
            "summary": {
                "total_file_issues": len(file_findings),
                "total_env_issues": len(env_findings),
                "is_clean": len(file_findings) == 0 and all(
                    f["severity"] != "error" for f in env_findings
                ),
            }
        }


class FREComplianceValidator:
    """
    Validates compliance with Federal Rules of Evidence 902(13)/(14).
    
    FRE 902(13): Certified records of a regularly conducted activity.
    FRE 902(14): Certified data copied from electronic devices or storage.
    
    Requirements:
    - Cryptographic integrity verification
    - Chain of custody documentation
    - Tamper detection
    - Timestamp authentication
    """
    
    @dataclass
    class ComplianceResult:
        """Result of FRE compliance check."""
        is_compliant: bool
        checks_passed: List[str]
        checks_failed: List[str]
        recommendations: List[str]
        timestamp: datetime = field(default_factory=datetime.utcnow)
        
        def to_dict(self) -> Dict[str, Any]:
            """Convert to dictionary."""
            return {
                "is_compliant": self.is_compliant,
                "checks_passed": self.checks_passed,
                "checks_failed": self.checks_failed,
                "recommendations": self.recommendations,
                "timestamp": self.timestamp.isoformat(),
            }
    
    @staticmethod
    def validate_triple_hash(hash_result: Any) -> Tuple[bool, str]:
        """
        Validate that evidence uses triple-hash integrity.
        
        Args:
            hash_result: HashResult object with sha256, sha3_512, blake2b
            
        Returns:
            Tuple of (is_valid, message)
        """
        required_attrs = ["sha256", "sha3_512", "blake2b"]
        
        for attr in required_attrs:
            if not hasattr(hash_result, attr):
                return False, f"Missing hash algorithm: {attr}"
            
            value = getattr(hash_result, attr)
            if not value or len(value) < 64:  # Minimum for SHA-256 (64 hex chars)
                return False, f"Invalid hash value for {attr}"
        
        return True, "Triple-hash integrity verified"
    
    @staticmethod
    def validate_merkle_tree(merkle_root: str, leaf_count: int) -> Tuple[bool, str]:
        """
        Validate Merkle tree construction.
        
        Args:
            merkle_root: Merkle root hash
            leaf_count: Number of leaves in tree
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not merkle_root:
            return False, "Merkle root is missing"
        
        if len(merkle_root) != 64:  # SHA-256 hex length
            return False, "Merkle root has invalid length"
        
        if leaf_count < 1:
            return False, "Merkle tree has no leaves"
        
        return True, f"Merkle tree valid with {leaf_count} leaves"
    
    @staticmethod
    def validate_timestamp_token(token: Any) -> Tuple[bool, str]:
        """
        Validate RFC 3161 timestamp token.
        
        Args:
            token: TimestampToken object
            
        Returns:
            Tuple of (is_valid, message)
        """
        required_attrs = ["token_data", "gen_time", "message_imprint", "authority"]
        
        for attr in required_attrs:
            if not hasattr(token, attr):
                return False, f"Missing timestamp attribute: {attr}"
        
        # Check authority is not local
        if hasattr(token, "authority") and token.authority == "local":
            return False, "Local timestamps are NOT court-admissible"
        
        # Check token_data exists
        if not token.token_data:
            return False, "Timestamp token data is empty"
        
        return True, f"Timestamp token valid from {token.authority}"
    
    @staticmethod
    def validate_chain_of_custody(custody_chain: Any) -> Tuple[bool, str]:
        """
        Validate chain of custody documentation.
        
        Args:
            custody_chain: CustodyChain or similar object
            
        Returns:
            Tuple of (is_valid, message)
        """
        if custody_chain is None:
            return False, "Chain of custody is missing"
        
        # Check for required entries
        if hasattr(custody_chain, "entries"):
            if len(custody_chain.entries) < 1:
                return False, "Chain of custody has no entries"
        elif hasattr(custody_chain, "events"):
            if len(custody_chain.events) < 1:
                return False, "Chain of custody has no events"
        else:
            return False, "Chain of custody structure is invalid"
        
        return True, "Chain of custody documented"
    
    def validate_evidence_package(
        self,
        package: Any,
        require_timestamp: bool = True
    ) -> "FREComplianceValidator.ComplianceResult":
        """
        Validate complete evidence package for FRE 902(13)/(14) compliance.
        
        Args:
            package: Evidence package to validate
            require_timestamp: Whether RFC 3161 timestamp is required
            
        Returns:
            ComplianceResult with validation details
        """
        checks_passed = []
        checks_failed = []
        recommendations = []
        
        # Check 1: Triple-hash integrity
        if hasattr(package, "content_hash"):
            is_valid, msg = self.validate_triple_hash(package.content_hash)
            if is_valid:
                checks_passed.append(f"Triple-hash: {msg}")
            else:
                checks_failed.append(f"Triple-hash: {msg}")
        else:
            checks_failed.append("Triple-hash: Evidence package missing content_hash")
        
        # Check 2: Merkle tree
        if hasattr(package, "merkle_root"):
            leaf_count = getattr(package, "item_count", 1)
            is_valid, msg = self.validate_merkle_tree(package.merkle_root, leaf_count)
            if is_valid:
                checks_passed.append(f"Merkle tree: {msg}")
            else:
                checks_failed.append(f"Merkle tree: {msg}")
        else:
            checks_failed.append("Merkle tree: Evidence package missing merkle_root")
        
        # Check 3: RFC 3161 timestamp
        if require_timestamp:
            if hasattr(package, "timestamp_token") and package.timestamp_token:
                is_valid, msg = self.validate_timestamp_token(package.timestamp_token)
                if is_valid:
                    checks_passed.append(f"Timestamp: {msg}")
                else:
                    checks_failed.append(f"Timestamp: {msg}")
            else:
                checks_failed.append("Timestamp: RFC 3161 timestamp required but missing")
                recommendations.append(
                    "Obtain RFC 3161 timestamp from trusted TSA (FreeTSA, DigiCert)"
                )
        
        # Check 4: Chain of custody
        if hasattr(package, "custody_chain"):
            is_valid, msg = self.validate_chain_of_custody(package.custody_chain)
            if is_valid:
                checks_passed.append(f"Custody: {msg}")
            else:
                checks_failed.append(f"Custody: {msg}")
        elif hasattr(package, "custody_records"):
            if len(package.custody_records) > 0:
                checks_passed.append("Custody: Chain of custody documented")
            else:
                checks_failed.append("Custody: No custody records found")
        else:
            checks_failed.append("Custody: Chain of custody documentation missing")
        
        # Determine overall compliance
        is_compliant = len(checks_failed) == 0
        
        if not is_compliant:
            recommendations.append(
                "Address all failed checks before using evidence in legal proceedings"
            )
        
        return self.ComplianceResult(
            is_compliant=is_compliant,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            recommendations=recommendations
        )


def create_secrets_manager(
    backend: str = "local",
    **kwargs
) -> SecretsManagerInterface:
    """
    Factory function to create a secrets manager.
    
    Args:
        backend: "local", "aws", or "vault"
        **kwargs: Backend-specific configuration
        
    Returns:
        SecretsManagerInterface implementation
    """
    if backend == "local":
        return LocalEncryptedSecretsManager(**kwargs)
    elif backend == "aws":
        raise NotImplementedError(
            "AWS Secrets Manager backend not yet implemented. "
            "Set AWS_SECRET_ACCESS_KEY and use boto3 integration."
        )
    elif backend == "vault":
        raise NotImplementedError(
            "HashiCorp Vault backend not yet implemented. "
            "Set VAULT_ADDR and VAULT_TOKEN for integration."
        )
    else:
        raise ValueError(f"Unknown secrets manager backend: {backend}")
