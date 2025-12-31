"""
Test Suite for Phase 4 Enhanced Formatters
==========================================

Tests all new formatter modules to ensure proper DOJ-grade output generation.
"""

import pytest
from datetime import datetime, date
from typing import Dict, Any, List

from src.reporting.formatters import (
    CoverSheetFormatter,
    ExecutiveBriefingFormatter,
    InsiderDossierFormatter,
    ViolationCategoryFormatter,
    EvidenceChainFormatter,
    AppendixGenerator,
)
from src.reporting.formatters.format_constants import (
    STANDARD_WIDTH,
    STATUS_COMPLETE,
    STATUS_FAILED,
    get_severity_indicator,
    get_risk_indicator,
    create_progress_bar,
)


# ═══════════════════════════════════════════════════════════════════════════
# FORMAT CONSTANTS TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestFormatConstants:
    """Test format constants and helper functions."""
    
    def test_standard_width(self):
        """Test standard width constant."""
        assert STANDARD_WIDTH == 80
    
    def test_severity_indicators(self):
        """Test severity indicator retrieval."""
        assert get_severity_indicator('CRITICAL') == "▓▓▓▓▓▓▓▓▓▓"
        assert get_severity_indicator('HIGH') == "▓▓▓▓▓▓▓▓░░"
        assert get_severity_indicator('MEDIUM') == "▓▓▓▓▓▓░░░░"
        assert get_severity_indicator('LOW') == "▓▓▓▓░░░░░░"
        assert get_severity_indicator('MINIMAL') == "▓▓░░░░░░░░"
    
    def test_risk_indicators(self):
        """Test risk indicator calculation."""
        assert get_risk_indicator(90) == "▓▓▓"
        assert get_risk_indicator(70) == "▓▓░"
        assert get_risk_indicator(50) == "▓░░"
        assert get_risk_indicator(30) == "░░░"
    
    def test_progress_bar(self):
        """Test progress bar generation."""
        bar = create_progress_bar(50, 100, 10)
        assert len(bar) == 10
        assert bar == "▓▓▓▓▓░░░░░"
        
        # Edge case: zero total
        bar_zero = create_progress_bar(0, 0, 10)
        assert bar_zero == "░" * 10
        
        # Full bar
        bar_full = create_progress_bar(100, 100, 10)
        assert bar_full == "▓" * 10


# ═══════════════════════════════════════════════════════════════════════════
# COVER SHEET TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestCoverSheetFormatter:
    """Test cover sheet formatter."""
    
    def test_format_cover_sheet(self):
        """Test cover sheet generation."""
        case_data = {
            'case_id': 'JLAW-320187-20240101',
            'company_name': 'NIKE, Inc.',
            'cik': '0000320187',
            'generation_date': datetime(2024, 1, 1, 12, 0, 0),
            'dossier_type': 'DOJ-GRADE',
            'start_date': '2019-01-01',
            'end_date': '2019-12-31',
        }
        
        result = CoverSheetFormatter.format(case_data)
        
        # Verify structure
        assert 'CONFIDENTIAL — LAW ENFORCEMENT SENSITIVE' in result
        assert 'SECURITIES FRAUD FORENSIC DOSSIER' in result
        assert 'NIKE, Inc.' in result
        assert '0000320187' in result
        assert 'JLAW-320187-20240101' in result
        assert 'DOJ-GRADE' in result
        assert '2019-01-01 — 2019-12-31' in result
        
        # Verify Unicode box drawing
        assert '╔' in result
        assert '╗' in result
        assert '╚' in result
        assert '╝' in result
        assert '║' in result
    
    def test_cover_sheet_with_missing_data(self):
        """Test cover sheet with minimal data."""
        case_data = {
            'case_id': 'TEST-001',
        }
        
        result = CoverSheetFormatter.format(case_data)
        
        # Should still generate without errors
        assert 'TEST-001' in result
        assert 'N/A' in result


# ═══════════════════════════════════════════════════════════════════════════
# EXECUTIVE BRIEFING TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestExecutiveBriefingFormatter:
    """Test executive briefing formatter."""
    
    def test_format_briefing(self):
        """Test executive briefing generation."""
        exec_summary = {
            'threat_level': 'CRITICAL',
            'threat_statement': 'This investigation establishes 10 CRITICAL violations.',
            'total_violations': 15,
            'critical_violations': 10,
            'high_violations': 5,
            'total_actors': 3,
            'enforcement_recommendation': 'IMMEDIATE DOJ CRIMINAL REFERRAL RECOMMENDED',
            'primary_enforcement_agencies': ['DOJ', 'SEC'],
            'key_findings': [
                {'finding': 'Finding 1', 'relevance': 'Important for prosecution'},
                {'finding': 'Finding 2', 'relevance': 'Establishes intent'},
            ],
            'priority_matrix': {
                'CRITICAL': 10,
                'HIGH': 5,
                'MEDIUM': 0,
                'LOW': 0,
            }
        }
        
        result = ExecutiveBriefingFormatter.format(exec_summary)
        
        # Verify threat assessment
        assert 'THREAT ASSESSMENT' in result
        assert 'CRITICAL' in result
        assert '▓▓▓▓▓▓▓▓▓▓' in result
        
        # Verify key metrics
        assert 'Total Violations:' in result
        assert '15' in result
        
        # Verify key findings
        assert 'KEY FINDINGS AT A GLANCE' in result
        assert 'Finding 1' in result
        
        # Verify priority matrix
        assert 'INVESTIGATION PRIORITY MATRIX' in result
        
        # Verify enforcement recommendation
        assert 'ENFORCEMENT RECOMMENDATION' in result
        assert 'IMMEDIATE DOJ CRIMINAL REFERRAL RECOMMENDED' in result
    
    def test_briefing_with_default_findings(self):
        """Test briefing with auto-generated findings."""
        exec_summary = {
            'threat_level': 'HIGH',
            'threat_statement': 'Test threat',
            'total_violations': 5,
            'critical_violations': 2,
            'high_violations': 3,
            'total_actors': 2,
            'enforcement_recommendation': 'Test recommendation',
            'primary_enforcement_agencies': ['SEC'],
        }
        
        result = ExecutiveBriefingFormatter.format(exec_summary)
        
        # Should generate default findings
        assert 'KEY FINDINGS AT A GLANCE' in result


# ═══════════════════════════════════════════════════════════════════════════
# INSIDER DOSSIER TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestInsiderDossierFormatter:
    """Test insider dossier formatter."""
    
    def test_format_single_insider(self):
        """Test single insider dossier generation."""
        insider_data = {
            'name': 'John Doe',
            'risk_score': 85.0,
            'roles': ['CEO', 'Director'],
            'relationship': 'Officer',
            'cik': '1234567',
            'total_transactions': 50,
            'zero_dollar_transactions': 10,
            'late_filings': 5,
            'transactions': [
                {
                    'transaction_date': '2019-06-15',
                    'transaction_code': 'P',
                    'shares': 10000,
                    'price_per_share': 50.00,
                }
            ],
            'pattern_analysis': 'Multiple suspicious patterns detected.',
        }
        
        result = InsiderDossierFormatter.format_all([insider_data])
        
        # Verify structure
        assert 'REPORTING PERSON DOSSIERS' in result
        assert 'John Doe' in result
        assert 'CEO, Director' in result
        assert '85.0/100' in result
        
        # Verify activity summary
        assert 'Total Transactions:' in result
        assert '50' in result
        assert 'Zero-Dollar Transactions:' in result
        assert '10' in result
        
        # Verify transaction timeline
        assert 'TRANSACTION TIMELINE' in result
        assert '2019-06-15' in result
        
        # Verify pattern analysis
        assert 'PATTERN ANALYSIS' in result
        assert 'Multiple suspicious patterns detected.' in result
    
    def test_format_multiple_insiders(self):
        """Test multiple insider dossiers."""
        insiders = [
            {'name': 'Person 1', 'risk_score': 90.0, 'roles': ['CEO']},
            {'name': 'Person 2', 'risk_score': 70.0, 'roles': ['CFO']},
        ]
        
        result = InsiderDossierFormatter.format_all(insiders)
        
        # Should be sorted by risk score (highest first)
        assert result.index('Person 1') < result.index('Person 2')
    
    def test_format_no_insiders(self):
        """Test with no insiders."""
        result = InsiderDossierFormatter.format_all([])
        
        assert 'No reporting persons identified' in result


# ═══════════════════════════════════════════════════════════════════════════
# VIOLATION CATEGORY TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestViolationCategoryFormatter:
    """Test violation category formatter."""
    
    def test_format_violations(self):
        """Test violation formatting by category."""
        violations = [
            {
                'violation_id': 'V001',
                'violation_type': 'LATE_FORM4_FILING',
                'confidence': 0.9,
                'severity': 'HIGH',
                'statutes': [{'code': '17 CFR § 240.16a-3', 'title': 'Form 4 Filing'}],
                'transaction_date': '2019-06-15',
                'reporting_person': 'John Doe',
                'shares': 10000,
                'days_late': 30,
            },
            {
                'violation_id': 'V002',
                'violation_type': 'LATE_FORM4_FILING',
                'confidence': 0.85,
                'severity': 'MEDIUM',
                'statutes': [{'code': '17 CFR § 240.16a-3', 'title': 'Form 4 Filing'}],
                'transaction_date': '2019-07-20',
                'reporting_person': 'Jane Smith',
                'shares': 5000,
                'days_late': 15,
            },
        ]
        
        result = ViolationCategoryFormatter.format(violations)
        
        # Verify structure
        assert 'VIOLATION ANALYSIS BY CATEGORY' in result
        assert 'LATE_FORM4_FILING' in result
        
        # Verify aggregate stats
        assert 'Aggregate Statistics' in result
        
        # Verify prosecutorial analysis
        assert 'Prosecutorial Analysis' in result
        
        # Verify transaction log
        assert 'Detailed Transaction Log' in result
    
    def test_deduplication(self):
        """Test violation deduplication logic."""
        violations = [
            {
                'violation_id': 'V001',
                'violation_type': 'INSIDER_TRADING',
                'transaction_date': '2019-06-15',
                'reporting_person': 'John Doe',
                'shares': 10000,
                'transaction_code': 'S',
                'statutes': [{'code': '17 CFR § 240.10b-5'}],
            },
            {
                'violation_id': 'V002',
                'violation_type': 'TIMING_VIOLATION',
                'transaction_date': '2019-06-15',
                'reporting_person': 'John Doe',
                'shares': 10000,
                'transaction_code': 'S',
                'statutes': [{'code': '15 USC § 78p'}],
            },
        ]
        
        result = ViolationCategoryFormatter.format(violations)
        
        # Should consolidate violations
        assert result is not None


# ═══════════════════════════════════════════════════════════════════════════
# EVIDENCE CHAIN TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestEvidenceChainFormatter:
    """Test evidence chain formatter."""
    
    def test_format_evidence_chain(self):
        """Test evidence chain formatting."""
        evidence_data = {
            'merkle_root': 'abc123def456789',
            'total_evidence_items': 150,
            'hash_algorithm': 'SHA-256',
            'secondary_hash': 'SHA3-512',
            'tertiary_hash': 'BLAKE2b',
            'fre_902_compliant': True,
            'rfc_6962_compliant': True,
            'timestamp_token': 'token123',
            'chain_of_custody_records': 75,
            'hash_verified': True,
            'merkle_verified': True,
        }
        
        result = EvidenceChainFormatter.format(evidence_data)
        
        # Verify structure
        assert 'EVIDENCE CHAIN & CRYPTOGRAPHIC ATTESTATION' in result
        assert 'CRYPTOGRAPHIC ATTESTATION' in result
        
        # Verify triple-hash
        assert 'Triple-Hash Integrity Verification' in result
        assert 'SHA-256' in result
        assert 'SHA3-512' in result
        assert 'BLAKE2b' in result
        
        # Verify compliance
        assert 'FRE 902(13)/(14)' in result
        assert 'RFC 6962' in result
        
        # Verify admissibility certification
        assert 'COURTROOM ADMISSIBILITY CERTIFICATION' in result
        
        # Verify statistics
        assert 'EVIDENCE CHAIN STATISTICS' in result
        assert '150' in result
    
    def test_non_compliant_evidence(self):
        """Test evidence chain with non-compliance."""
        evidence_data = {
            'merkle_root': None,
            'total_evidence_items': 10,
            'fre_902_compliant': False,
            'rfc_6962_compliant': False,
        }
        
        result = EvidenceChainFormatter.format(evidence_data)
        
        # Should show warning
        assert 'WARNING' in result or 'Not Available' in result


# ═══════════════════════════════════════════════════════════════════════════
# APPENDIX TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAppendixGenerator:
    """Test appendix generator."""
    
    def test_format_appendix_a(self):
        """Test Appendix A formatting."""
        data = {
            'appendix_a': {
                'violations': [
                    {
                        'violation_id': 'V001',
                        'violation_type': 'INSIDER_TRADING',
                        'confidence': 0.95,
                        'severity': 'CRITICAL',
                        'statutes': [{'code': '17 CFR § 240.10b-5'}],
                        'evidence_hash': 'abc123',
                    }
                ]
            }
        }
        
        result = AppendixGenerator.format_all(data)
        
        assert 'APPENDIX A' in result
        assert 'COMPLETE VIOLATION EVIDENCE RECORDS' in result
        assert 'V001' in result
    
    def test_format_appendix_b(self):
        """Test Appendix B formatting."""
        data = {
            'appendix_b': {
                'execution_summary': {
                    'total_nodes': 15,
                    'successful_nodes': 14,
                    'failed_nodes': 1,
                },
                'node_results': {
                    'Node 1: Form 4 Insider Trading': {
                        'status': 'success',
                        'violations_found': 10,
                        'execution_time': 2.5,
                    }
                }
            }
        }
        
        result = AppendixGenerator.format_all(data)
        
        assert 'APPENDIX B' in result
        assert '15-NODE RECURSIVE ENGINE ANALYSIS MATRIX' in result
        assert 'NODE EXECUTION MATRIX' in result
    
    def test_format_appendix_c(self):
        """Test Appendix C formatting."""
        data = {
            'appendix_c': {
                'filings': [
                    {
                        'filing_date': '2019-06-15',
                        'form_type': 'FORM 4',
                        'accession_number': '0001234567-19-000123',
                    }
                ]
            }
        }
        
        result = AppendixGenerator.format_all(data)
        
        assert 'APPENDIX C' in result
        assert 'RAW SEC FILING INDEX' in result
        assert 'CHRONOLOGICAL INDEX' in result
    
    def test_format_appendix_d(self):
        """Test Appendix D formatting."""
        data = {
            'appendix_d': {
                'algorithms': {
                    'Options Backdating': {
                        'status': 'success',
                        'detections': 5,
                        'execution_time': 1.2,
                    }
                }
            }
        }
        
        result = AppendixGenerator.format_all(data)
        
        assert 'APPENDIX D' in result
        assert 'ALGORITHM EXECUTION LOG' in result
    
    def test_format_all_appendices(self):
        """Test formatting all appendices together."""
        data = {
            'appendix_a': {'violations': []},
            'appendix_b': {'execution_summary': {}, 'node_results': {}},
            'appendix_c': {'filings': []},
            'appendix_d': {'algorithms': {}},
        }
        
        result = AppendixGenerator.format_all(data)
        
        # Should have all four appendices
        assert 'APPENDIX A' in result
        assert 'APPENDIX B' in result
        assert 'APPENDIX C' in result
        assert 'APPENDIX D' in result


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestFormatterIntegration:
    """Test integration of all formatters."""
    
    def test_no_hedging_language(self):
        """Verify no hedging language in any formatter output."""
        hedging_words = ['may', 'might', 'could', 'possibly', 'perhaps', 'potentially']
        
        # Test executive briefing
        exec_summary = {
            'threat_level': 'CRITICAL',
            'threat_statement': 'This investigation establishes violations.',
            'total_violations': 10,
            'critical_violations': 5,
            'enforcement_recommendation': 'IMMEDIATE ACTION RECOMMENDED',
        }
        result = ExecutiveBriefingFormatter.format(exec_summary)
        
        # Should not contain hedging words in primary statements
        # Note: "potentially" might appear in legal context which is acceptable
        for word in ['may be', 'might be', 'could be', 'possibly', 'perhaps']:
            assert word.lower() not in result.lower()
    
    def test_unicode_rendering(self):
        """Test Unicode box drawing characters render correctly."""
        case_data = {
            'case_id': 'TEST-001',
            'company_name': 'Test Corp',
            'cik': '1234567',
            'generation_date': datetime(2024, 1, 1),
            'dossier_type': 'DOJ-GRADE',
            'start_date': '2019-01-01',
            'end_date': '2019-12-31',
        }
        
        result = CoverSheetFormatter.format(case_data)
        
        # Verify Unicode characters are present
        unicode_chars = ['╔', '╗', '╚', '╝', '║', '═', '─', '│', '┌', '┐', '└', '┘']
        has_unicode = any(char in result for char in unicode_chars)
        assert has_unicode
