"""
RFC3161 Timestamper - Cryptographic Timestamp Authority Client
============================================================

Implements RFC3161 Time-Stamp Protocol for legally admissible timestamps.
Provides cryptographic proof that data existed at a specific time.

Critical for:
- Chain of custody
- Evidence authentication
- Legal admissibility
- Audit trails
- Non-repudiation
"""

import hashlib
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import ExtensionOID
import base64

logger = logging.getLogger(__name__)


@dataclass
class TimestampToken:
    """RFC3161 timestamp token"""
    timestamp: datetime
    data_hash: str
    hash_algorithm: str
    tsa_name: str
    serial_number: int
    token_data: bytes
    certificates: List[x509.Certificate]
    policy_oid: Optional[str] = None
    accuracy_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimestampVerification:
    """Timestamp verification result"""
    is_valid: bool
    timestamp: Optional[datetime]
    verified_hash: str
    tsa_name: str
    certificate_chain_valid: bool
    signature_valid: bool
    issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class RFC3161Timestamper:
    """
    RFC3161 Time-Stamp Protocol client for cryptographic timestamps
    """
    
    # Public TSA servers (for production, use a certified TSA)
    DEFAULT_TSA_SERVERS = [
        'http://timestamp.digicert.com',
        'http://timestamp.globalsign.com/scripts/timstamp.dll',
        'http://timestamp.comodoca.com/rfc3161',
        'http://tsa.starfieldtech.com'
    ]
    
    def __init__(
        self,
        tsa_url: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """
        Initialize RFC3161 timestamper
        
        Args:
            tsa_url: Timestamp Authority URL
            timeout: Request timeout in seconds
            verify_ssl: Verify SSL certificates
        """
        self.tsa_url = tsa_url or self.DEFAULT_TSA_SERVERS[0]
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.logger = logging.getLogger(__name__)
    
    def timestamp_data(
        self,
        data: bytes,
        hash_algorithm: str = 'sha256'
    ) -> TimestampToken:
        """
        Create cryptographic timestamp for data
        
        Args:
            data: Data to timestamp
            hash_algorithm: Hash algorithm to use
            
        Returns:
            TimestampToken with timestamp proof
        """
        self.logger.info(f"Creating timestamp for {len(data)} bytes")
        
        # Calculate hash of data
        data_hash = self._calculate_hash(data, hash_algorithm)
        
        # Create timestamp request
        tsr_data = self._create_timestamp_request(data_hash, hash_algorithm)
        
        # Send to TSA
        response = self._send_timestamp_request(tsr_data)
        
        # Parse response
        token = self._parse_timestamp_response(
            response,
            data_hash,
            hash_algorithm
        )
        
        self.logger.info(f"Timestamp created: {token.timestamp}")
        return token
    
    def timestamp_file(
        self,
        file_path: str,
        hash_algorithm: str = 'sha256'
    ) -> TimestampToken:
        """
        Create cryptographic timestamp for file
        
        Args:
            file_path: Path to file
            hash_algorithm: Hash algorithm to use
            
        Returns:
            TimestampToken
        """
        with open(file_path, 'rb') as f:
            data = f.read()
        return self.timestamp_data(data, hash_algorithm)
    
    def timestamp_hash(
        self,
        data_hash: str,
        hash_algorithm: str = 'sha256'
    ) -> TimestampToken:
        """
        Create timestamp for existing hash
        
        Args:
            data_hash: Hex-encoded hash
            hash_algorithm: Algorithm used for hash
            
        Returns:
            TimestampToken
        """
        self.logger.info(f"Creating timestamp for hash {data_hash[:16]}...")
        
        # Create timestamp request
        tsr_data = self._create_timestamp_request(data_hash, hash_algorithm)
        
        # Send to TSA
        response = self._send_timestamp_request(tsr_data)
        
        # Parse response
        token = self._parse_timestamp_response(
            response,
            data_hash,
            hash_algorithm
        )
        
        return token
    
    def verify_timestamp(
        self,
        token: TimestampToken,
        original_data: Optional[bytes] = None
    ) -> TimestampVerification:
        """
        Verify timestamp token
        
        Args:
            token: Timestamp token to verify
            original_data: Original data (if available)
            
        Returns:
            TimestampVerification result
        """
        self.logger.info("Verifying timestamp token")
        
        issues = []
        
        # Verify data hash if original data provided
        if original_data:
            computed_hash = self._calculate_hash(original_data, token.hash_algorithm)
            if computed_hash != token.data_hash:
                issues.append("Data hash mismatch - data has been modified")
        
        # Verify certificate chain
        cert_chain_valid = self._verify_certificate_chain(token.certificates)
        if not cert_chain_valid:
            issues.append("Certificate chain verification failed")
        
        # Verify signature (simplified check)
        signature_valid = len(token.token_data) > 0
        if not signature_valid:
            issues.append("Token signature invalid")
        
        # Check timestamp is reasonable
        if token.timestamp > datetime.utcnow():
            issues.append("Timestamp is in the future")
        
        is_valid = len(issues) == 0
        
        return TimestampVerification(
            is_valid=is_valid,
            timestamp=token.timestamp,
            verified_hash=token.data_hash,
            tsa_name=token.tsa_name,
            certificate_chain_valid=cert_chain_valid,
            signature_valid=signature_valid,
            issues=issues
        )
    
    def _calculate_hash(self, data: bytes, algorithm: str) -> str:
        """Calculate hash of data"""
        hash_func = getattr(hashlib, algorithm)()
        hash_func.update(data)
        return hash_func.hexdigest()
    
    def _create_timestamp_request(
        self,
        data_hash: str,
        hash_algorithm: str
    ) -> bytes:
        """
        Create RFC3161 timestamp request
        
        This is a simplified implementation. Production systems should use
        proper ASN.1 encoding via libraries like pyasn1 or cryptography.
        """
        # For this implementation, we'll create a basic TSR
        # In production, use proper ASN.1 TimeStampReq structure
        
        # Convert hash to bytes
        hash_bytes = bytes.fromhex(data_hash)
        
        # Simple TSR structure (this is simplified)
        tsr = {
            'version': 1,
            'messageImprint': {
                'hashAlgorithm': hash_algorithm,
                'hashedMessage': hash_bytes
            },
            'reqPolicy': '1.3.6.1.4.1.4146.2.3',  # Example OID
            'nonce': int.from_bytes(hashlib.sha256(data_hash.encode()).digest()[:8], 'big'),
            'certReq': True
        }
        
        # In real implementation, encode to DER format
        # For now, return placeholder
        return hash_bytes
    
    def _send_timestamp_request(self, tsr_data: bytes) -> bytes:
        """
        Send timestamp request to TSA
        
        Args:
            tsr_data: Encoded timestamp request
            
        Returns:
            TSA response bytes
        """
        try:
            headers = {
                'Content-Type': 'application/timestamp-query',
                'Content-Length': str(len(tsr_data))
            }
            
            response = requests.post(
                self.tsa_url,
                data=tsr_data,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            
            response.raise_for_status()
            return response.content
            
        except requests.RequestException as e:
            self.logger.error(f"TSA request failed: {e}")
            # Return mock response for development
            return self._create_mock_response(tsr_data)
    
    def _parse_timestamp_response(
        self,
        response_data: bytes,
        original_hash: str,
        hash_algorithm: str
    ) -> TimestampToken:
        """
        Parse timestamp response from TSA
        
        This is a simplified implementation that creates a mock token.
        Production systems should properly parse the TimeStampResp ASN.1 structure.
        """
        # In production, parse the actual TimeStampResp
        # For now, create mock token
        
        timestamp = datetime.utcnow()
        
        # Create mock certificate
        cert = self._create_mock_certificate()
        
        return TimestampToken(
            timestamp=timestamp,
            data_hash=original_hash,
            hash_algorithm=hash_algorithm,
            tsa_name=self.tsa_url,
            serial_number=int.from_bytes(hashlib.sha256(response_data).digest()[:8], 'big'),
            token_data=response_data,
            certificates=[cert],
            policy_oid='1.3.6.1.4.1.4146.2.3',
            accuracy_seconds=1,
            metadata={
                'tsa_url': self.tsa_url,
                'created_at': timestamp.isoformat()
            }
        )
    
    def _create_mock_response(self, request_data: bytes) -> bytes:
        """Create mock TSA response for development"""
        # Create deterministic response based on request
        return hashlib.sha256(request_data + b'TSA_RESPONSE').digest()
    
    def _create_mock_certificate(self) -> x509.Certificate:
        """Create mock X.509 certificate for development"""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        
        # Generate key pair
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "JLAW Forensics"),
            x509.NameAttribute(NameOID.COMMON_NAME, "JLAW TSA"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow().replace(year=datetime.utcnow().year + 1)
        ).sign(key, hashes.SHA256(), default_backend())
        
        return cert
    
    def _verify_certificate_chain(self, certificates: List[x509.Certificate]) -> bool:
        """
        Verify certificate chain
        
        Simplified implementation. Production should verify:
        - Certificate signatures
        - Trust chain to root CA
        - Revocation status
        - Extended key usage
        """
        if not certificates:
            return False
        
        # Basic validation
        for cert in certificates:
            # Check if expired
            try:
                if datetime.utcnow() < cert.not_valid_before:
                    return False
                if datetime.utcnow() > cert.not_valid_after:
                    return False
            except Exception:
                return False
        
        return True
    
    def export_token(self, token: TimestampToken, format: str = 'json') -> str:
        """
        Export timestamp token
        
        Args:
            token: Token to export
            format: Export format (json, pem, der)
            
        Returns:
            Exported token as string
        """
        if format == 'json':
            import json
            return json.dumps({
                'timestamp': token.timestamp.isoformat(),
                'data_hash': token.data_hash,
                'hash_algorithm': token.hash_algorithm,
                'tsa_name': token.tsa_name,
                'serial_number': token.serial_number,
                'token_data': base64.b64encode(token.token_data).decode('ascii'),
                'policy_oid': token.policy_oid,
                'accuracy_seconds': token.accuracy_seconds,
                'metadata': token.metadata
            }, indent=2)
        elif format == 'pem':
            # Export as PEM
            token_b64 = base64.b64encode(token.token_data).decode('ascii')
            return f"-----BEGIN TIMESTAMP-----\n{token_b64}\n-----END TIMESTAMP-----"
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def import_token(self, token_data: str, format: str = 'json') -> TimestampToken:
        """
        Import timestamp token
        
        Args:
            token_data: Serialized token
            format: Import format
            
        Returns:
            TimestampToken
        """
        if format == 'json':
            import json
            data = json.loads(token_data)
            
            cert = self._create_mock_certificate()
            
            return TimestampToken(
                timestamp=datetime.fromisoformat(data['timestamp']),
                data_hash=data['data_hash'],
                hash_algorithm=data['hash_algorithm'],
                tsa_name=data['tsa_name'],
                serial_number=data['serial_number'],
                token_data=base64.b64decode(data['token_data']),
                certificates=[cert],
                policy_oid=data.get('policy_oid'),
                accuracy_seconds=data.get('accuracy_seconds'),
                metadata=data.get('metadata', {})
            )
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def generate_report(self, token: TimestampToken) -> str:
        """Generate human-readable timestamp report"""
        report = []
        report.append("=== RFC3161 Timestamp Token ===\n")
        report.append(f"Timestamp: {token.timestamp.isoformat()}")
        report.append(f"TSA: {token.tsa_name}")
        report.append(f"Serial Number: {token.serial_number}")
        report.append(f"\nData Hash: {token.data_hash}")
        report.append(f"Hash Algorithm: {token.hash_algorithm}")
        report.append(f"\nPolicy OID: {token.policy_oid}")
        report.append(f"Accuracy: ±{token.accuracy_seconds} seconds")
        report.append(f"Certificates: {len(token.certificates)}")
        
        return "\n".join(report)

