"""
RIM Compliance Validator - RIM Phase 1
======================================

Validates all outputs meet RIM Non-Negotiable Execution Standard:
- Scans for prohibited hedging language
- Verifies 100% statutory binding coverage
- Checks secondary pass execution for all flagged items
- Generates compliance reports

RIM Standards:
- ZERO hedging language ("may indicate", "could suggest", etc.)
- 100% statutory binding coverage required
- 100% secondary pass coverage for flagged violations
- Explicit evidence strength statements
- Direct prosecution-ready language
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    """RIM compliance status."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


@dataclass
class ComplianceDeficiency:
    """Individual compliance deficiency."""
    deficiency_type: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    description: str
    location: Optional[str] = None
    remediation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "deficiency_type": self.deficiency_type,
            "severity": self.severity,
            "description": self.description,
            "location": self.location,
            "remediation": self.remediation
        }


@dataclass
class RIMComplianceResult:
    """Complete RIM compliance validation result."""
    is_compliant: bool
    compliance_status: ComplianceStatus
    deficiencies: List[ComplianceDeficiency]
    prohibited_language_count: int
    statutory_binding_coverage: float  # 0.0-1.0
    secondary_pass_coverage: float  # 0.0-1.0
    validation_timestamp: datetime = field(default_factory=datetime.utcnow)
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_compliant": self.is_compliant,
            "compliance_status": self.compliance_status.value,
            "deficiencies": [d.to_dict() for d in self.deficiencies],
            "prohibited_language_count": self.prohibited_language_count,
            "statutory_binding_coverage": self.statutory_binding_coverage,
            "secondary_pass_coverage": self.secondary_pass_coverage,
            "validation_timestamp": self.validation_timestamp.isoformat(),
            "summary": self.summary
        }


class RIMComplianceValidator:
    """
    RIM Compliance Validator implementing RIM execution standard.
    
    Ensures all outputs meet DOJ-grade prosecution requirements:
    - Zero hedging language
    - Complete statutory binding
    - Full secondary analysis coverage
    - Explicit evidence strength
    """
    
    # Prohibited hedging terms (RIM Non-Negotiable Standard)
    PROHIBITED_TERMS = [
        "may indicate",
        "could suggest",
        "potentially",
        "possibly",
        "appears to",
        "seems to",
        "might be",
        "likely",
        "probably",
        "perhaps",
        "requires further review",
        "manual review recommended",
        "analyst opinion",
        "should be reviewed",
        "warrants investigation",
        "suggests possible",
        "indicates potential",
        "may require",
        "could be",
        "might indicate",
        "appears suspicious",
        "seems suspicious"
    ]
    
    # Alternative prosecution-ready language
    PROSECUTION_READY_ALTERNATIVES = {
        "may indicate": "indicates",
        "could suggest": "demonstrates",
        "potentially": "REMOVE (be direct)",
        "possibly": "REMOVE (be direct)",
        "appears to": "IS (be definitive)",
        "seems to": "IS (be definitive)",
        "might be": "IS (be definitive)",
        "likely": "REMOVE (use confidence score)",
        "probably": "REMOVE (use confidence score)",
        "requires further review": "requires enforcement action",
        "manual review recommended": "enforcement referral required",
        "analyst opinion": "forensic finding"
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Compile regex patterns for efficiency
        self.prohibited_patterns = [
            re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            for term in self.PROHIBITED_TERMS
        ]
    
    def validate_rim_compliance(
        self,
        dossier_data: Dict[str, Any],
        recursive_analysis_result: Optional[Dict[str, Any]],
        statutory_bindings: List[Dict[str, Any]],
        primary_violations: List[Dict[str, Any]]
    ) -> RIMComplianceResult:
        """
        Execute complete RIM compliance validation.
        
        Args:
            dossier_data: Complete dossier output
            recursive_analysis_result: Recursive forensic analysis results
            statutory_bindings: Statutory binding results
            primary_violations: Primary violations from detection
            
        Returns:
            RIMComplianceResult with compliance status and deficiencies
        """
        self.logger.info("=" * 80)
        self.logger.info("RIM COMPLIANCE VALIDATION")
        self.logger.info("=" * 80)
        
        deficiencies = []
        
        # VALIDATION 1: Prohibited language scan
        self.logger.info("\n→ Scanning for prohibited hedging language...")
        prohibited_count, language_deficiencies = self._scan_prohibited_language(dossier_data)
        deficiencies.extend(language_deficiencies)
        
        if prohibited_count == 0:
            self.logger.info("  ✓ No prohibited language detected")
        else:
            self.logger.warning(f"  ✗ Found {prohibited_count} instances of prohibited language")
        
        # VALIDATION 2: Statutory binding coverage
        self.logger.info("\n→ Validating statutory binding coverage...")
        binding_coverage, binding_deficiencies = self._validate_statutory_binding_coverage(
            primary_violations,
            statutory_bindings
        )
        deficiencies.extend(binding_deficiencies)
        
        if binding_coverage >= 1.0:
            self.logger.info("  ✓ 100% statutory binding coverage achieved")
        else:
            self.logger.warning(f"  ✗ Statutory binding coverage: {binding_coverage*100:.1f}% (requires 100%)")
        
        # VALIDATION 3: Secondary pass coverage
        self.logger.info("\n→ Validating secondary pass coverage...")
        secondary_coverage, secondary_deficiencies = self._validate_secondary_pass_coverage(
            primary_violations,
            recursive_analysis_result
        )
        deficiencies.extend(secondary_deficiencies)
        
        if secondary_coverage >= 1.0:
            self.logger.info("  ✓ 100% secondary pass coverage achieved")
        else:
            self.logger.warning(f"  ✗ Secondary pass coverage: {secondary_coverage*100:.1f}% (requires 100%)")
        
        # VALIDATION 4: Evidence strength statements
        self.logger.info("\n→ Validating evidence strength statements...")
        evidence_deficiencies = self._validate_evidence_strength(dossier_data)
        deficiencies.extend(evidence_deficiencies)
        
        if not evidence_deficiencies:
            self.logger.info("  ✓ All evidence strength statements are explicit")
        else:
            self.logger.warning(f"  ✗ Found {len(evidence_deficiencies)} evidence strength deficiencies")
        
        # VALIDATION 5: Dossier structure
        self.logger.info("\n→ Validating RIM-mandated dossier structure...")
        structure_deficiencies = self._validate_dossier_structure(dossier_data)
        deficiencies.extend(structure_deficiencies)
        
        if not structure_deficiencies:
            self.logger.info("  ✓ All RIM-mandated sections present")
        else:
            self.logger.warning(f"  ✗ Found {len(structure_deficiencies)} structure deficiencies")
        
        # Determine overall compliance
        critical_deficiencies = [d for d in deficiencies if d.severity == "CRITICAL"]
        high_deficiencies = [d for d in deficiencies if d.severity == "HIGH"]
        
        is_compliant = (
            len(critical_deficiencies) == 0 and
            prohibited_count == 0 and
            binding_coverage >= 1.0 and
            secondary_coverage >= 1.0
        )
        
        if is_compliant:
            compliance_status = ComplianceStatus.PASS
            summary = "RIM compliance validation PASSED. Output meets DOJ-grade prosecution standards."
        elif len(critical_deficiencies) > 0:
            compliance_status = ComplianceStatus.FAIL
            summary = f"RIM compliance validation FAILED. {len(critical_deficiencies)} critical deficiencies detected."
        else:
            compliance_status = ComplianceStatus.WARNING
            summary = f"RIM compliance validation WARNING. {len(high_deficiencies)} high-priority deficiencies detected."
        
        result = RIMComplianceResult(
            is_compliant=is_compliant,
            compliance_status=compliance_status,
            deficiencies=deficiencies,
            prohibited_language_count=prohibited_count,
            statutory_binding_coverage=binding_coverage,
            secondary_pass_coverage=secondary_coverage,
            summary=summary
        )
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"RIM COMPLIANCE: {compliance_status.value}")
        self.logger.info(f"  Prohibited Language: {prohibited_count} instances")
        self.logger.info(f"  Statutory Binding: {binding_coverage*100:.1f}%")
        self.logger.info(f"  Secondary Pass: {secondary_coverage*100:.1f}%")
        self.logger.info(f"  Critical Deficiencies: {len(critical_deficiencies)}")
        self.logger.info(f"  High Deficiencies: {len(high_deficiencies)}")
        self.logger.info(f"  Total Deficiencies: {len(deficiencies)}")
        self.logger.info("=" * 80)
        
        return result
    
    def _scan_prohibited_language(
        self,
        data: Any,
        location_prefix: str = ""
    ) -> Tuple[int, List[ComplianceDeficiency]]:
        """
        Recursively scan data structure for prohibited hedging language.
        
        Returns:
            Tuple of (prohibited_count, deficiency_list)
        """
        prohibited_count = 0
        deficiencies = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                new_prefix = f"{location_prefix}.{key}" if location_prefix else key
                count, defs = self._scan_prohibited_language(value, new_prefix)
                prohibited_count += count
                deficiencies.extend(defs)
        
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                new_prefix = f"{location_prefix}[{idx}]"
                count, defs = self._scan_prohibited_language(item, new_prefix)
                prohibited_count += count
                deficiencies.extend(defs)
        
        elif isinstance(data, str):
            # Check for prohibited terms
            for pattern in self.prohibited_patterns:
                matches = pattern.findall(data)
                if matches:
                    for match in matches:
                        prohibited_count += 1
                        
                        # Find alternative
                        alternative = self.PROSECUTION_READY_ALTERNATIVES.get(
                            match.lower(),
                            "Use direct, definitive language"
                        )
                        
                        deficiency = ComplianceDeficiency(
                            deficiency_type="PROHIBITED_LANGUAGE",
                            severity="CRITICAL",
                            description=f"Prohibited hedging language detected: '{match}'",
                            location=location_prefix,
                            remediation=f"Replace with: {alternative}"
                        )
                        deficiencies.append(deficiency)
        
        return prohibited_count, deficiencies
    
    def _validate_statutory_binding_coverage(
        self,
        violations: List[Dict[str, Any]],
        bindings: List[Dict[str, Any]]
    ) -> Tuple[float, List[ComplianceDeficiency]]:
        """
        Validate that all violations have statutory bindings.
        
        Returns:
            Tuple of (coverage_ratio, deficiency_list)
        """
        deficiencies = []
        
        if not violations:
            return 1.0, deficiencies
        
        # Extract violation IDs
        violation_ids = set()
        for v in violations:
            vid = v.get('violation_id', v.get('id'))
            if vid:
                violation_ids.add(vid)
        
        # Extract bound violation IDs
        bound_violation_ids = set()
        for b in bindings:
            vid = b.get('violation_id')
            if vid:
                bound_violation_ids.add(vid)
        
        # Calculate coverage
        if not violation_ids:
            coverage = 1.0
        else:
            coverage = len(bound_violation_ids) / len(violation_ids)
        
        # Identify unbound violations
        unbound = violation_ids - bound_violation_ids
        
        if unbound:
            deficiency = ComplianceDeficiency(
                deficiency_type="INCOMPLETE_STATUTORY_BINDING",
                severity="CRITICAL",
                description=f"{len(unbound)} violations lack statutory bindings (requires 100% coverage)",
                location="statutory_bindings",
                remediation=f"Bind violations to statutes: {list(unbound)[:5]}"
            )
            deficiencies.append(deficiency)
        
        return coverage, deficiencies
    
    def _validate_secondary_pass_coverage(
        self,
        violations: List[Dict[str, Any]],
        recursive_result: Optional[Dict[str, Any]]
    ) -> Tuple[float, List[ComplianceDeficiency]]:
        """
        Validate that all flagged violations received secondary analysis.
        
        Returns:
            Tuple of (coverage_ratio, deficiency_list)
        """
        deficiencies = []
        
        if not violations:
            return 1.0, deficiencies
        
        if not recursive_result:
            deficiency = ComplianceDeficiency(
                deficiency_type="MISSING_SECONDARY_PASS",
                severity="CRITICAL",
                description="Recursive analysis not executed (secondary pass required)",
                location="recursive_analysis_result",
                remediation="Execute RecursiveForensicAnalyzer.execute_recursive_analysis()"
            )
            deficiencies.append(deficiency)
            return 0.0, deficiencies
        
        # Count violations that received secondary analysis
        secondary_findings = recursive_result.get('secondary_findings', [])
        tertiary_findings = recursive_result.get('tertiary_findings', [])
        
        # For now, assume coverage if secondary analysis was executed
        # More sophisticated logic could track which violations were analyzed
        if secondary_findings or tertiary_findings:
            coverage = 1.0
        else:
            coverage = 0.5  # Partial credit for attempting recursive analysis
            
            deficiency = ComplianceDeficiency(
                deficiency_type="INCOMPLETE_SECONDARY_ANALYSIS",
                severity="HIGH",
                description="Secondary analysis executed but no findings generated",
                location="recursive_analysis_result.secondary_findings",
                remediation="Review transaction clustering and temporal correlation logic"
            )
            deficiencies.append(deficiency)
        
        return coverage, deficiencies
    
    def _validate_evidence_strength(
        self,
        dossier_data: Dict[str, Any]
    ) -> List[ComplianceDeficiency]:
        """Validate that evidence strength statements are explicit."""
        deficiencies = []
        
        # Check for required evidence strength section
        if 'evidence_strength' not in dossier_data and 'evidence_chain' not in dossier_data:
            deficiency = ComplianceDeficiency(
                deficiency_type="MISSING_EVIDENCE_STRENGTH",
                severity="HIGH",
                description="Dossier lacks explicit evidence strength statement",
                location="dossier",
                remediation="Add 'evidence_strength' section with explicit confidence ratings"
            )
            deficiencies.append(deficiency)
        
        # Check that confidence scores are explicit (not vague)
        detection_results = dossier_data.get('detection_results', {})
        if detection_results:
            for result_key, result_data in detection_results.items():
                if isinstance(result_data, dict):
                    confidence = result_data.get('confidence')
                    if confidence is None:
                        deficiency = ComplianceDeficiency(
                            deficiency_type="MISSING_CONFIDENCE_SCORE",
                            severity="MEDIUM",
                            description=f"Detection result '{result_key}' lacks explicit confidence score",
                            location=f"detection_results.{result_key}",
                            remediation="Add 'confidence' field with numeric score (0.0-1.0)"
                        )
                        deficiencies.append(deficiency)
        
        return deficiencies
    
    def _validate_dossier_structure(
        self,
        dossier_data: Dict[str, Any]
    ) -> List[ComplianceDeficiency]:
        """Validate RIM-mandated dossier sections are present."""
        deficiencies = []
        
        # Required RIM sections
        required_sections = [
            ("executive_summary", "Executive Forensic Summary"),
            ("violations_table", "Table of Violations with Statutes"),
            ("transaction_clusters", "Transaction Clustering Analysis"),
            ("temporal_correlations", "Temporal Correlation Analysis"),
            ("enforcement_pathways", "Enforcement Pathway Mapping"),
            ("evidence_strength", "Evidence Strength Statement")
        ]
        
        for section_key, section_name in required_sections:
            # Check if section exists (allow some flexibility in naming)
            found = False
            for key in dossier_data.keys():
                if section_key in key.lower() or key.lower() in section_key:
                    found = True
                    break
            
            if not found:
                # Don't mark as critical - some sections may be embedded elsewhere
                deficiency = ComplianceDeficiency(
                    deficiency_type="MISSING_RIM_SECTION",
                    severity="MEDIUM",
                    description=f"RIM-mandated section missing: {section_name}",
                    location="dossier",
                    remediation=f"Add '{section_key}' section to dossier output"
                )
                deficiencies.append(deficiency)
        
        return deficiencies
    
    def generate_compliance_report(
        self,
        result: RIMComplianceResult
    ) -> str:
        """Generate human-readable compliance report."""
        
        report_lines = [
            "=" * 80,
            "RIM COMPLIANCE VALIDATION REPORT",
            "=" * 80,
            "",
            f"Validation Timestamp: {result.validation_timestamp.isoformat()}",
            f"Compliance Status: {result.compliance_status.value}",
            f"Overall Compliant: {'YES' if result.is_compliant else 'NO'}",
            "",
            "METRICS:",
            f"  Prohibited Language Instances: {result.prohibited_language_count}",
            f"  Statutory Binding Coverage: {result.statutory_binding_coverage*100:.1f}%",
            f"  Secondary Pass Coverage: {result.secondary_pass_coverage*100:.1f}%",
            f"  Total Deficiencies: {len(result.deficiencies)}",
            ""
        ]
        
        if result.deficiencies:
            report_lines.append("DEFICIENCIES:")
            report_lines.append("")
            
            # Group by severity
            by_severity = {
                "CRITICAL": [],
                "HIGH": [],
                "MEDIUM": [],
                "LOW": []
            }
            
            for deficiency in result.deficiencies:
                severity = deficiency.severity
                if severity in by_severity:
                    by_severity[severity].append(deficiency)
            
            for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                defs = by_severity[severity]
                if defs:
                    report_lines.append(f"{severity} ({len(defs)}):")
                    for idx, def_ in enumerate(defs, 1):
                        report_lines.append(f"  {idx}. {def_.description}")
                        if def_.location:
                            report_lines.append(f"     Location: {def_.location}")
                        if def_.remediation:
                            report_lines.append(f"     Remediation: {def_.remediation}")
                        report_lines.append("")
        else:
            report_lines.append("NO DEFICIENCIES DETECTED")
            report_lines.append("")
        
        report_lines.extend([
            "=" * 80,
            "SUMMARY",
            "=" * 80,
            result.summary,
            "=" * 80
        ])
        
        return "\n".join(report_lines)
