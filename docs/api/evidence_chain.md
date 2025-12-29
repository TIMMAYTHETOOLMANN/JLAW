# Evidence Chain API Reference

API reference for JLAW's evidence chain components.

## Hash Service

```python
from src.core.evidence_chain.hash_service import HashService

hash_service = HashService()
hashes = hash_service.compute_triple_hash(document_content)

# Returns:
# {
#   'sha256': 'a3f8...',
#   'sha3_512': 'b7e9...',
#   'blake2b': 'c2d4...'
# }
```

## Merkle Tree

```python
from src.core.evidence_chain.merkle_tree import MerkleTree

merkle_tree = MerkleTree()
for doc_hash in document_hashes:
    merkle_tree.add_leaf(bytes.fromhex(doc_hash))

root_hash = merkle_tree.get_root()
proof = merkle_tree.get_proof(leaf_index)
is_valid = merkle_tree.verify_proof(leaf_hash, proof, root_hash)
```

## RFC 3161 Client

```python
from src.core.evidence_chain.rfc3161_client import RFC3161Client

client = RFC3161Client(tsa_url="https://freetsa.org/tsr")
timestamp_token = await client.timestamp_data(document_content)
is_valid = await client.verify_timestamp(timestamp_token, document_content)
```

## Chain of Custody Logger

```python
from src.core.custody.chain_of_custody import CustodyLogger

custody_logger = CustodyLogger(output_dir="evidence_chain/custody")
custody_logger.log_acquisition(
    document_id="form4_320187_2019-01-15",
    document_url="https://www.sec.gov/...",
    hashes=triple_hashes,
    timestamp_token=timestamp_token
)
```

---

See [Evidence Chain Architecture](../architecture/evidence_chain.md) for details.
