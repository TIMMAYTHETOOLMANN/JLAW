"""
MODULE 9: EVIDENCE CHAIN ENHANCEMENT (DEF-023)

Add Merkle tree root for batch verification of all evidence hashes.
"""

import hashlib
import json
from datetime import datetime, timezone


class MerkleTreeBuilder:
    """Build Merkle tree for evidence chain integrity verification."""

    @classmethod
    def build_merkle_tree(cls, evidence_hashes: list) -> dict:
        """Build SHA-256 binary Merkle tree from evidence hashes."""
        if not evidence_hashes:
            return {'root': None, 'tree': [], 'leaf_count': 0}

        # Normalize: ensure all items are hex strings
        leaves = []
        for h in evidence_hashes:
            if isinstance(h, str):
                leaves.append(h)
            else:
                leaves.append(
                    hashlib.sha256(json.dumps(h, sort_keys=True).encode()).hexdigest()
                )

        # Pad to power of 2
        while len(leaves) & (len(leaves) - 1):
            leaves.append(leaves[-1])

        level = list(leaves)
        tree = [level[:]]

        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                combined = level[i] + level[i + 1]
                h = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(h)
            level = next_level
            tree.append(level[:])

        return {
            'root': level[0],
            'tree_depth': len(tree),
            'leaf_count': len(evidence_hashes),
            'algorithm': 'SHA-256 binary Merkle tree',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
