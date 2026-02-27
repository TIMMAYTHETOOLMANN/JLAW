"""
MODULE 3: VIOLATION DEDUPLICATION ENGINE (DEF-006)

Comstock Elizabeth J late filing appears 3x identically in analysis_results.json.
Root cause: the same accession number generates multiple violation records
when a single Form 4 filing contains multiple transactions. Fix: deduplicate
by composite key (accession_number + violation_type + insider).
"""


class ViolationDeduplicator:
    """Deduplicate violations using composite key."""

    @staticmethod
    def _compute_key(violation: dict) -> str:
        parts = [
            violation.get('accession_number', ''),
            violation.get('violation_type') or violation.get('type', ''),
            violation.get('reporting_owner', ''),
            violation.get('transaction_date', ''),
        ]
        return '|'.join(p.lower() for p in parts)

    @classmethod
    def deduplicate(cls, violations: list) -> dict:
        """
        Deduplicate violations. A single late Form 4 filing (one accession number)
        should produce exactly ONE late filing violation, not one per transaction.
        """
        seen = {}
        deduplicated = []
        duplicates_removed = 0

        for v in violations:
            key = cls._compute_key(v)
            if key in seen:
                duplicates_removed += 1
                existing = seen[key]
                # Merge: keep higher share count
                if (v.get('shares', 0) or 0) > (existing.get('shares', 0) or 0):
                    existing['shares'] = v['shares']
                existing.setdefault('_merged_count', 1)
                existing['_merged_count'] += 1
                continue

            seen[key] = v
            deduplicated.append(v)

        return {
            'violations': deduplicated,
            'original_count': len(violations),
            'deduplicated_count': len(deduplicated),
            'duplicates_removed': duplicates_removed,
        }
