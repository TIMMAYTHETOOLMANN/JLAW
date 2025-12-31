"""
Unit Tests for RIM Compliance Validator (RIM Phase 1)
===================================================

Tests RIM Non-Negotiable Execution Standard validation:
- Prohibited hedging language detection
- Statutory binding coverage verification
- Secondary pass coverage checking
- Compliance reporting
"""

import pytest
from src.validation.rim_compliance_validator import (
    RIMComplianceValidator,
    RIMComplianceResult,
    ComplianceDeficiency,
    ComplianceStatus
)


class TestRIMComplianceValidator:
    """Test suite for RIMComplianceValidator."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return RIMComplianceValidator()
    
    @pytest.fixture
    def compliant_dossier(self):
        """Sample compliant dossier."""
        return {
            "case_id": "CASE_001",
            "executive_summary": "Analysis demonstrates violations of federal securities law.",
            "detection_results": {
                "patterns_executed": 23,
                "findings": [
                    {
                        "algorithm": "Insider_Trading_Detection",
                        "description": "Transaction demonstrates insider trading pattern",
                        "confidence": 0.92
                    }
                ]
            },
            "evidence_chain": {
                "total_evidence_items": 10,
                "hash_algorithm": "SHA-256"
            },
            "violations_table": [],
            "transaction_clusters": [],
            "temporal_correlations": [],
            "enforcement_pathways": {},
            "evidence_strength": {
                "overall_confidence": 0.85
            }
        }
    
    @pytest.fixture
    def non_compliant_dossier(self):
        """Sample non-compliant dossier with hedging language."""
        return {
            "case_id": "CASE_002",
            "executive_summary": "Analysis may indicate potential violations that could suggest fraud.",
            "detection_results": {
                "patterns_executed": 23,
                "findings": [
                    {
                        "algorithm": "Insider_Trading_Detection",
                        "description": "Transaction appears to suggest possible insider trading",
                        "confidence": None  # Missing confidence score
                    }
                ]
            }
        }
    
    @pytest.fixture
    def sample_violations(self):
        """Sample violations."""
        return [
            {
                'violation_id': 'V001',
                'violation_type': 'insider_trading_form4_late',
                'confidence': 0.95
            },
            {
                'violation_id': 'V002',
                'violation_type': 'insider_trading_10b5_material_nonpublic',
                'confidence': 0.88
            }
        ]
    
    @pytest.fixture
    def sample_bindings(self):
        """Sample statutory bindings."""
        return [
            {
                'binding_id': 'BIND_V001',
                'violation_id': 'V001',
                'statutes': [{'code': '17 CFR § 240.16a-3(a)'}]
            },
            {
                'binding_id': 'BIND_V002',
                'violation_id': 'V002',
                'statutes': [{'code': '17 CFR § 240.10b-5'}]
            }
        ]
    
    @pytest.fixture
    def sample_recursive_result(self):
        """Sample recursive analysis result."""
        return {
            'primary_findings': [],
            'secondary_findings': [
                {'cluster_violation_id': 'SEC_001', 'violation_type': 'CLUSTERED_SUSPICIOUS_ACTIVITY'}
            ],
            'tertiary_findings': [],
            'transaction_clusters': [],
            'temporal_correlations': []
        }
    
    def test_initialization(self, validator):
        """Test validator initialization."""
        assert validator is not None
        assert len(validator.PROHIBITED_TERMS) > 0
        assert len(validator.prohibited_patterns) > 0
    
    def test_prohibited_terms_list(self, validator):
        """Test prohibited terms are comprehensive."""
        prohibited = validator.PROHIBITED_TERMS
        
        # Check for key hedging terms
        assert 'may indicate' in prohibited
        assert 'could suggest' in prohibited
        assert 'potentially' in prohibited
        assert 'appears to' in prohibited
        assert 'requires further review' in prohibited
    
    def test_scan_prohibited_language_clean(self, validator, compliant_dossier):
        """Test scanning clean text with no prohibited language."""
        count, deficiencies = validator._scan_prohibited_language(compliant_dossier)
        
        assert count == 0
        assert len(deficiencies) == 0
    
    def test_scan_prohibited_language_violations(self, validator, non_compliant_dossier):
        """Test scanning text with prohibited language."""
        count, deficiencies = validator._scan_prohibited_language(non_compliant_dossier)
        
        assert count > 0
        assert len(deficiencies) > 0
        
        # Check deficiency details
        for deficiency in deficiencies:
            assert deficiency.deficiency_type == 'PROHIBITED_LANGUAGE'
            assert deficiency.severity == 'CRITICAL'
            assert deficiency.remediation is not None
    
    def test_validate_statutory_binding_full_coverage(
        self, validator, sample_violations, sample_bindings
    ):
        """Test statutory binding with 100% coverage."""
        coverage, deficiencies = validator._validate_statutory_binding_coverage(
            sample_violations,
            sample_bindings
        )
        
        assert coverage == 1.0
        assert len(deficiencies) == 0
    
    def test_validate_statutory_binding_partial_coverage(self, validator):
        """Test statutory binding with incomplete coverage."""
        violations = [
            {'violation_id': 'V001'},
            {'violation_id': 'V002'},
            {'violation_id': 'V003'}
        ]
        bindings = [
            {'violation_id': 'V001'},
            {'violation_id': 'V002'}
        ]
        
        coverage, deficiencies = validator._validate_statutory_binding_coverage(
            violations,
            bindings
        )
        
        assert coverage < 1.0
        assert len(deficiencies) > 0
        assert deficiencies[0].deficiency_type == 'INCOMPLETE_STATUTORY_BINDING'
        assert deficiencies[0].severity == 'CRITICAL'
    
    def test_validate_secondary_pass_coverage_present(
        self, validator, sample_violations, sample_recursive_result
    ):
        """Test secondary pass coverage when recursive analysis completed."""
        coverage, deficiencies = validator._validate_secondary_pass_coverage(
            sample_violations,
            sample_recursive_result
        )
        
        assert coverage == 1.0
        assert len(deficiencies) == 0
    
    def test_validate_secondary_pass_coverage_missing(self, validator, sample_violations):
        """Test secondary pass coverage when recursive analysis missing."""
        coverage, deficiencies = validator._validate_secondary_pass_coverage(
            sample_violations,
            None
        )
        
        assert coverage == 0.0
        assert len(deficiencies) > 0
        assert deficiencies[0].deficiency_type == 'MISSING_SECONDARY_PASS'
        assert deficiencies[0].severity == 'CRITICAL'
    
    def test_validate_evidence_strength(self, validator, compliant_dossier):
        """Test evidence strength validation."""
        deficiencies = validator._validate_evidence_strength(compliant_dossier)
        
        # Should pass with evidence_strength section
        assert len(deficiencies) == 0
    
    def test_validate_evidence_strength_missing(self, validator):
        """Test evidence strength validation when missing."""
        dossier = {"case_id": "CASE_001"}
        deficiencies = validator._validate_evidence_strength(dossier)
        
        assert len(deficiencies) > 0
        assert any(
            d.deficiency_type == 'MISSING_EVIDENCE_STRENGTH'
            for d in deficiencies
        )
    
    def test_validate_dossier_structure(self, validator, compliant_dossier):
        """Test dossier structure validation."""
        deficiencies = validator._validate_dossier_structure(compliant_dossier)
        
        # May have some missing sections, but shouldn't be critical
        for deficiency in deficiencies:
            assert deficiency.severity in ['MEDIUM', 'LOW']
    
    def test_validate_rim_compliance_pass(
        self, validator, compliant_dossier, sample_violations, 
        sample_bindings, sample_recursive_result
    ):
        """Test RIM compliance validation - PASS scenario."""
        result = validator.validate_rim_compliance(
            dossier_data=compliant_dossier,
            recursive_analysis_result=sample_recursive_result,
            statutory_bindings=sample_bindings,
            primary_violations=sample_violations
        )
        
        assert isinstance(result, RIMComplianceResult)
        assert result.is_compliant == True
        assert result.compliance_status == ComplianceStatus.PASS
        assert result.prohibited_language_count == 0
        assert result.statutory_binding_coverage == 1.0
        assert result.secondary_pass_coverage == 1.0
    
    def test_validate_rim_compliance_fail(
        self, validator, non_compliant_dossier, sample_violations
    ):
        """Test RIM compliance validation - FAIL scenario."""
        result = validator.validate_rim_compliance(
            dossier_data=non_compliant_dossier,
            recursive_analysis_result=None,
            statutory_bindings=[],
            primary_violations=sample_violations
        )
        
        assert isinstance(result, RIMComplianceResult)
        assert result.is_compliant == False
        assert result.compliance_status == ComplianceStatus.FAIL
        assert result.prohibited_language_count > 0
        assert len(result.deficiencies) > 0
    
    def test_generate_compliance_report(self, validator):
        """Test compliance report generation."""
        result = RIMComplianceResult(
            is_compliant=False,
            compliance_status=ComplianceStatus.FAIL,
            deficiencies=[
                ComplianceDeficiency(
                    deficiency_type='PROHIBITED_LANGUAGE',
                    severity='CRITICAL',
                    description='Found prohibited language: may indicate',
                    location='executive_summary',
                    remediation='Replace with: indicates'
                )
            ],
            prohibited_language_count=5,
            statutory_binding_coverage=0.75,
            secondary_pass_coverage=0.50,
            summary='RIM compliance failed'
        )
        
        report = validator.generate_compliance_report(result)
        
        assert isinstance(report, str)
        assert 'RIM COMPLIANCE VALIDATION REPORT' in report
        assert 'FAIL' in report
        assert 'CRITICAL' in report
        assert 'prohibited language' in report.lower()
    
    def test_rim_compliance_result_serialization(self):
        """Test RIMComplianceResult to_dict() method."""
        result = RIMComplianceResult(
            is_compliant=True,
            compliance_status=ComplianceStatus.PASS,
            deficiencies=[],
            prohibited_language_count=0,
            statutory_binding_coverage=1.0,
            secondary_pass_coverage=1.0,
            summary='All checks passed'
        )
        
        data = result.to_dict()
        
        assert data['is_compliant'] == True
        assert data['compliance_status'] == 'PASS'
        assert data['prohibited_language_count'] == 0
        assert data['statutory_binding_coverage'] == 1.0
        assert 'validation_timestamp' in data
    
    def test_compliance_deficiency_serialization(self):
        """Test ComplianceDeficiency to_dict() method."""
        deficiency = ComplianceDeficiency(
            deficiency_type='PROHIBITED_LANGUAGE',
            severity='CRITICAL',
            description='Test deficiency',
            location='test_location',
            remediation='Test remediation'
        )
        
        data = deficiency.to_dict()
        
        assert data['deficiency_type'] == 'PROHIBITED_LANGUAGE'
        assert data['severity'] == 'CRITICAL'
        assert data['description'] == 'Test deficiency'
    
    def test_case_insensitive_prohibited_language(self, validator):
        """Test prohibited language detection is case-insensitive."""
        test_data = {
            "summary": "This May Indicate a violation. Could Suggest fraud. APPEARS TO be suspicious."
        }
        
        count, deficiencies = validator._scan_prohibited_language(test_data)
        
        assert count >= 3  # Should catch all three variants
    
    def test_prosecution_ready_alternatives(self, validator):
        """Test prosecution-ready alternative suggestions."""
        assert 'may indicate' in validator.PROSECUTION_READY_ALTERNATIVES
        assert 'could suggest' in validator.PROSECUTION_READY_ALTERNATIVES
        
        # Alternatives should be direct and definitive
        alt = validator.PROSECUTION_READY_ALTERNATIVES['may indicate']
        assert alt == 'indicates'
    
    def test_missing_confidence_scores(self, validator, non_compliant_dossier):
        """Test detection of missing confidence scores."""
        deficiencies = validator._validate_evidence_strength(non_compliant_dossier)
        
        # Should detect either missing confidence score or missing evidence strength section
        assert len(deficiencies) > 0
        assert any(
            'confidence' in d.description.lower() or 'evidence' in d.description.lower()
            for d in deficiencies
        )
    
    def test_empty_violations_handling(self, validator):
        """Test handling of empty violations list."""
        coverage, deficiencies = validator._validate_statutory_binding_coverage(
            [],
            []
        )
        
        # Empty violations should return 100% coverage
        assert coverage == 1.0
        assert len(deficiencies) == 0
    
    def test_recursive_language_scanning(self, validator):
        """Test that language scanning works recursively through nested structures."""
        nested_data = {
            "level1": {
                "level2": {
                    "level3": "This may indicate a violation"
                },
                "list": [
                    "Could suggest fraud",
                    "Normal text"
                ]
            }
        }
        
        count, deficiencies = validator._scan_prohibited_language(nested_data)
        
        assert count >= 2  # Should find both instances
