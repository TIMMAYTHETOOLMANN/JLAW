"""
Chain of Custody Management
===========================

FRE 902(13)/(14) compliant custody tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import hashlib
import json


class CustodyAction(Enum):
    RETRIEVED = "retrieved"
    VERIFIED = "verified"
    STORED = "stored"
    ACCESSED = "accessed"
    ANALYZED = "analyzed"
    TRANSFERRED = "transferred"
    EXPORTED = "exported"


@dataclass
class CustodyEntry:
    custody_id: str
    evidence_id: str
    custodian: str
    action: CustodyAction
    timestamp: datetime
    hash_at_transfer: str
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "custody_id": self.custody_id,
            "evidence_id": self.evidence_id,
            "custodian": self.custodian,
            "action": self.action.value,
            "timestamp": self.timestamp.isoformat(),
            "hash_at_transfer": self.hash_at_transfer
        }
    
    def compute_hash(self) -> str:
        data = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()


class ChainOfCustody:
    """Chain of custody tracker."""
    
    def __init__(self, evidence_id: str, initial_custodian: str = "JLAW System"):
        self.evidence_id = evidence_id
        self.entries: List[CustodyEntry] = []
        self._counter = 0
    
    def record_action(
        self,
        action: CustodyAction,
        custodian: str,
        evidence_hash: str,
        notes: Optional[str] = None
    ) -> CustodyEntry:
        self._counter += 1
        
        entry = CustodyEntry(
            custody_id=f"COC-{self.evidence_id}-{self._counter:04d}",
            evidence_id=self.evidence_id,
            custodian=custodian,
            action=action,
            timestamp=datetime.utcnow(),
            hash_at_transfer=evidence_hash,
            notes=notes
        )
        
        self.entries.append(entry)
        return entry
    
    def export_for_court(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "custody_chain": [e.to_dict() for e in self.entries],
            "total_entries": len(self.entries),
            "certification": {
                "standard": "FRE 902(13)/(14)",
                "generated_at": datetime.utcnow().isoformat()
            }
        }


@dataclass
class FRECertification:
    """FRE 902(13)/(14) certification generator."""
    certifier_name: str
    certifier_title: str
    organization: str
    
    def generate_902_14_certification(self, evidence_id: str, hash_value: str) -> str:
        return f"""
CERTIFICATION PURSUANT TO FEDERAL RULES OF EVIDENCE 902(14)
============================================================

Evidence ID: {evidence_id}
Hash Value (SHA-256): {hash_value}

I, {self.certifier_name}, {self.certifier_title} of {self.organization},
certify under penalty of perjury that the data identified herein is a
complete and accurate copy of the original electronic data.

Date: {datetime.utcnow().strftime('%Y-%m-%d')}

{self.certifier_name}
{self.certifier_title}
"""

