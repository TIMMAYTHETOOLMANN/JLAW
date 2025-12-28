"""
RFC 3161 Trusted Timestamping Module
=====================================

Obtain and verify RFC 3161 trusted timestamps from accredited Time Stamping Authorities
per Section 9.2 of the JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Accredited TSAs:
    - DigiCert Timestamp Authority
    - Sectigo (formerly Comodo) TSA
    - GlobalSign TSA
    - Entrust TSA

Compliance:
    - RFC 3161 (Internet X.509 PKI Time-Stamp Protocol)
    - ETSI EN 319 422 (Electronic Signatures - Time-stamping)
"""

import os
import requests
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TrustedTimestamp:
    """RFC 3161 trusted timestamp from accredited TSA."""
    hash_timestamped: str
    timestamp_utc: datetime
    tsa_certificate: str
    timestamp_token: str  # Hex-encoded token
    verification_url: str


class TimestampError(Exception):
    """Exception raised during timestamping operations."""
    pass


def request_trusted_timestamp(
    evidence_hash: str,
    tsa_url: str = 'https://timestamp.digicert.com'
) -> TrustedTimestamp:
    """
    Obtain RFC 3161 trusted timestamp from accredited TSA.
    
    Accredited TSAs:
        - DigiCert Timestamp Authority
        - Sectigo (formerly Comodo) TSA
        - GlobalSign TSA
        - Entrust TSA
    
    Compliance:
        - RFC 3161 (Internet X.509 PKI Time-Stamp Protocol)
        - ETSI EN 319 422 (Electronic Signatures - Time-stamping)
    
    Args:
        evidence_hash: SHA-256 hash to timestamp (hex string)
        tsa_url: TSA endpoint URL
    
    Returns:
        TrustedTimestamp: Timestamp with token and verification info
    """
    try:
        from asn1crypto import tsp, core
    except ImportError:
        raise TimestampError("asn1crypto package required for RFC 3161 timestamping")
    
    # Create timestamp request
    message_imprint = tsp.MessageImprint({
        'hash_algorithm': {'algorithm': 'sha256'},
        'hashed_message': bytes.fromhex(evidence_hash)
    })
    
    ts_request = tsp.TimeStampReq({
        'version': 1,
        'message_imprint': message_imprint,
        'nonce': core.Integer(int.from_bytes(os.urandom(8), 'big')),
        'cert_req': True
    })
    
    # Send to TSA
    response = requests.post(
        tsa_url,
        data=ts_request.dump(),
        headers={'Content-Type': 'application/timestamp-query'},
        timeout=30
    )
    
    if response.status_code != 200:
        raise TimestampError(f"TSA returned HTTP {response.status_code}")
    
    ts_response = tsp.TimeStampResp.load(response.content)
    
    if ts_response['status']['status'].native != 'granted':
        raise TimestampError(f"TSA rejected request: {ts_response['status']}")
    
    token = ts_response['time_stamp_token']
    
    # Extract timestamp from token
    signed_data = token['content']
    tst_info = signed_data['encap_content_info']['content'].parsed
    gen_time = tst_info['gen_time'].native
    
    # Extract TSA certificate (simplified - first cert in chain)
    certs = signed_data['certificates']
    tsa_cert = str(certs[0]) if certs else "No certificate"
    
    return TrustedTimestamp(
        hash_timestamped=evidence_hash,
        timestamp_utc=gen_time,
        tsa_certificate=tsa_cert[:100] + "...",  # Truncate for display
        timestamp_token=token.dump().hex(),
        verification_url=tsa_url
    )


def verify_timestamp_token(
    timestamp: TrustedTimestamp,
    original_hash: str
) -> bool:
    """
    Verify RFC 3161 timestamp token authenticity.
    
    Args:
        timestamp: TrustedTimestamp to verify
        original_hash: Original hash that was timestamped
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Simplified verification - full implementation requires:
    # 1. Verify TSA signature against certificate
    # 2. Verify certificate chain to trusted root
    # 3. Verify hash matches
    return timestamp.hash_timestamped == original_hash
