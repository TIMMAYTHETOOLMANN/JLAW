"""
MODULE 2: SEVERITY AGGREGATION FIX (DEF-002)

The cover page says "0 Critical, 0 High" because the top-level aggregation
only counts NODE_1 violations (which use string severity) and ignores the
SOX node violations that carry CRITICAL severity on a numeric 1-10 scale.
Fix: unified severity rollup across ALL nodes.
"""


class SeverityAggregator:
    """Unified severity rollup across all 15 analysis nodes."""

    SEVERITY_RANK = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}

    @classmethod
    def normalize_severity(cls, violation: dict) -> str:
        """
        Normalize severity across different node output formats.
        Node 1 uses string "HIGH"/"MEDIUM", Node 4 SOX uses numeric 1-10.
        """
        severity = violation.get('severity')

        if isinstance(severity, (int, float)):
            if severity >= 9:
                return 'critical'
            if severity >= 7:
                return 'high'
            if severity >= 4:
                return 'medium'
            return 'low'

        s = str(severity).upper()
        if s == 'CRITICAL':
            return 'critical'
        if s == 'HIGH':
            return 'high'
        if s == 'MEDIUM':
            return 'medium'
        return 'low'

    @classmethod
    def compute_unified_severity(cls, all_node_results: list) -> dict:
        """
        Unified severity rollup across all analysis nodes.
        Fixes the bug where analysis_results.json calculates critical_alerts
        and high_alerts ONLY from Node 1 Form 4 violations.
        """
        unified = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'total': 0}
        violations_by_type = {}

        for node_result in all_node_results:
            if not node_result:
                continue
            violations = node_result.get('violations', [])
            for v in violations:
                severity = cls.normalize_severity(v)
                unified[severity] += 1
                unified['total'] += 1

                vtype = v.get('violation_type') or v.get('type', 'unknown')
                if vtype not in violations_by_type:
                    violations_by_type[vtype] = {
                        'count': 0,
                        'max_severity': 'low',
                        'instances': [],
                    }
                violations_by_type[vtype]['count'] += 1
                violations_by_type[vtype]['instances'].append(v)

                if cls.SEVERITY_RANK.get(severity, 0) > cls.SEVERITY_RANK.get(
                    violations_by_type[vtype]['max_severity'], 0
                ):
                    violations_by_type[vtype]['max_severity'] = severity

        return {
            'unified': unified,
            'violations_by_type': violations_by_type,
        }
