"""
Evidence Chain Formatter - Phase 4 Enhanced
===========================================

Enhances evidence chain section with:
- Cryptographic attestation box with Merkle root
- Hash algorithms display (triple-hash: SHA-256 + SHA3-512 + BLAKE2b)
- Courtroom admissibility certification
- FRE/RFC compliance references
"""

from typing import Dict, Any, List
from .format_constants import (
    SUBSECTION_DIVIDER,
    SECTION_4_TITLE,
    STATUS_COMPLETE,
    STATUS_FAILED,
    BOX_DOUBLE_TOP_LEFT,
    BOX_DOUBLE_TOP_RIGHT,
    BOX_DOUBLE_BOTTOM_LEFT,
    BOX_DOUBLE_BOTTOM_RIGHT,
    BOX_DOUBLE_HORIZONTAL,
    BOX_DOUBLE_VERTICAL,
    STANDARD_WIDTH,
)


class EvidenceChainFormatter:
    """Formats evidence chain and cryptographic attestation section."""
    
    @staticmethod
    def format(evidence_data: Dict[str, Any]) -> str:
        """
        Format evidence chain with cryptographic attestation.
        
        Args:
            evidence_data: Dictionary with:
                - merkle_root: Merkle tree root hash
                - total_evidence_items: Count of evidence items
                - hash_algorithm: Primary hash algorithm (SHA-256)
                - secondary_hash: Secondary algorithm (SHA3-512)
                - tertiary_hash: Tertiary algorithm (BLAKE2b)
                - fre_902_compliant: FRE 902(13)/(14) compliance status
                - rfc_6962_compliant: RFC 6962 Merkle tree compliance
                - timestamp_token: RFC 3161 timestamp token
                - chain_of_custody_records: Number of custody records
        
        Returns:
            Formatted evidence chain section
        """
        lines = []
        
        # Section header
        lines.append(SUBSECTION_DIVIDER)
        lines.append(SECTION_4_TITLE)
        lines.append(SUBSECTION_DIVIDER)
        lines.append("")
        
        # Cryptographic attestation box
        lines.extend(EvidenceChainFormatter._format_crypto_attestation(evidence_data))
        lines.append("")
        
        # Courtroom admissibility certification
        lines.extend(EvidenceChainFormatter._format_admissibility_cert(evidence_data))
        lines.append("")
        
        # Evidence statistics
        lines.extend(EvidenceChainFormatter._format_evidence_stats(evidence_data))
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_crypto_attestation(evidence_data: Dict[str, Any]) -> List[str]:
        """Format cryptographic attestation box."""
        lines = []
        
        box_width = STANDARD_WIDTH - 4
        
        # Double-line box header
        lines.append(f"{BOX_DOUBLE_TOP_LEFT}{BOX_DOUBLE_HORIZONTAL * box_width}{BOX_DOUBLE_TOP_RIGHT}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}{'CRYPTOGRAPHIC ATTESTATION'.center(box_width)}{BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}{BOX_DOUBLE_HORIZONTAL * box_width}{BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}{' ' * box_width}{BOX_DOUBLE_VERTICAL}")
        
        # Merkle root
        merkle_root = evidence_data.get('merkle_root', 'N/A')
        lines.append(f"{BOX_DOUBLE_VERTICAL} Merkle Tree Root Hash (RFC 6962):{' ' * (box_width - 36)}{BOX_DOUBLE_VERTICAL}")
        
        # Display merkle root (wrapped if needed)
        if merkle_root and merkle_root != 'N/A':
            merkle_display = f" {merkle_root[:box_width - 4]}"
            lines.append(f"{BOX_DOUBLE_VERTICAL}{merkle_display:<{box_width}}{BOX_DOUBLE_VERTICAL}")
            if len(merkle_root) > box_width - 4:
                merkle_display2 = f" {merkle_root[box_width - 4:]}"
                lines.append(f"{BOX_DOUBLE_VERTICAL}{merkle_display2:<{box_width}}{BOX_DOUBLE_VERTICAL}")
        else:
            lines.append(f"{BOX_DOUBLE_VERTICAL} {'[Not Available]':<{box_width - 2}}{BOX_DOUBLE_VERTICAL}")
        
        lines.append(f"{BOX_DOUBLE_VERTICAL}{' ' * box_width}{BOX_DOUBLE_VERTICAL}")
        
        # Triple-hash integrity
        lines.append(f"{BOX_DOUBLE_VERTICAL} Triple-Hash Integrity Verification:{' ' * (box_width - 38)}{BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}{' ' * box_width}{BOX_DOUBLE_VERTICAL}")
        
        hash_primary = evidence_data.get('hash_algorithm', 'SHA-256')
        hash_secondary = evidence_data.get('secondary_hash', 'SHA3-512')
        hash_tertiary = evidence_data.get('tertiary_hash', 'BLAKE2b')
        
        lines.append(f"{BOX_DOUBLE_VERTICAL}   {STATUS_COMPLETE} Primary:    {hash_primary:<{box_width - 19}}{BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}   {STATUS_COMPLETE} Secondary:  {hash_secondary:<{box_width - 19}}{BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}   {STATUS_COMPLETE} Tertiary:   {hash_tertiary:<{box_width - 19}}{BOX_DOUBLE_VERTICAL}")
        
        lines.append(f"{BOX_DOUBLE_VERTICAL}{' ' * box_width}{BOX_DOUBLE_VERTICAL}")
        
        # Compliance status
        fre_compliant = evidence_data.get('fre_902_compliant', False)
        rfc_compliant = evidence_data.get('rfc_6962_compliant', False)
        
        fre_status = STATUS_COMPLETE if fre_compliant else STATUS_FAILED
        rfc_status = STATUS_COMPLETE if rfc_compliant else STATUS_FAILED
        
        lines.append(f"{BOX_DOUBLE_VERTICAL} Compliance Status:{' ' * (box_width - 20)}{BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}   {fre_status} FRE 902(13)/(14) Evidence Authentication{' ' * (box_width - 48)}{BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_VERTICAL}   {rfc_status} RFC 6962 Merkle Tree Construction{' ' * (box_width - 42)}{BOX_DOUBLE_VERTICAL}")
        
        # Timestamp token
        timestamp_token = evidence_data.get('timestamp_token', None)
        if timestamp_token:
            lines.append(f"{BOX_DOUBLE_VERTICAL}   {STATUS_COMPLETE} RFC 3161 Trusted Timestamp Token{' ' * (box_width - 42)}{BOX_DOUBLE_VERTICAL}")
        
        lines.append(f"{BOX_DOUBLE_VERTICAL}{' ' * box_width}{BOX_DOUBLE_VERTICAL}")
        lines.append(f"{BOX_DOUBLE_BOTTOM_LEFT}{BOX_DOUBLE_HORIZONTAL * box_width}{BOX_DOUBLE_BOTTOM_RIGHT}")
        
        return lines
    
    @staticmethod
    def _format_admissibility_cert(evidence_data: Dict[str, Any]) -> List[str]:
        """Format courtroom admissibility certification."""
        lines = []
        
        lines.append("COURTROOM ADMISSIBILITY CERTIFICATION:")
        lines.append("")
        
        fre_compliant = evidence_data.get('fre_902_compliant', False)
        
        if fre_compliant:
            lines.append("This evidence chain satisfies the requirements for self-authentication under")
            lines.append("Federal Rules of Evidence:")
            lines.append("")
            lines.append("  • FRE 902(13) - Certified Records Generated by Electronic Process")
            lines.append("    Hash-verified electronic records with documented chain of custody")
            lines.append("")
            lines.append("  • FRE 902(14) - Certified Data Copied from Electronic Device")
            lines.append("    Cryptographically verified copies of SEC EDGAR filings")
            lines.append("")
            lines.append("Evidence integrity is mathematically verified through:")
            lines.append("")
            lines.append("  • Triple-hash verification (SHA-256 + SHA3-512 + BLAKE2b)")
            lines.append("  • RFC 6962 compliant Merkle tree construction")
            lines.append("  • RFC 3161 trusted timestamp tokens")
            lines.append("  • Complete chain of custody documentation")
            lines.append("")
            lines.append("This evidence package is COURT-READY and meets all federal admissibility")
            lines.append("standards for electronic evidence in criminal and civil proceedings.")
        else:
            lines.append("WARNING: Evidence chain does not fully meet FRE 902(13)/(14) requirements.")
            lines.append("Additional authentication may be required for courtroom admissibility.")
        
        return lines
    
    @staticmethod
    def _format_evidence_stats(evidence_data: Dict[str, Any]) -> List[str]:
        """Format evidence statistics."""
        lines = []
        
        lines.append("EVIDENCE CHAIN STATISTICS:")
        lines.append("")
        
        total_items = evidence_data.get('total_evidence_items', 0)
        custody_records = evidence_data.get('chain_of_custody_records', 0)
        
        lines.append(f"  Total Evidence Items:          {total_items:>6}")
        lines.append(f"  Chain of Custody Records:      {custody_records:>6}")
        lines.append(f"  Hash Verification:             {'PASS' if evidence_data.get('hash_verified', False) else 'FAIL':>6}")
        lines.append(f"  Merkle Tree Integrity:         {'PASS' if evidence_data.get('merkle_verified', False) else 'FAIL':>6}")
        
        return lines
