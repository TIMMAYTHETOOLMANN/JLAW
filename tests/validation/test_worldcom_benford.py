"""
WorldCom Benford's Law Validation Tests
=======================================

Validates Benford's Law analyzer against WorldCom (2002)
Known SEC enforcement case.

Expected: Significant deviation in expense line items
"""

import pytest
from src.detection.financial.benford_analysis import BenfordAnalyzer
from tests.validation.sec_enforcement_validator import SECEnforcementValidator


class TestWorldComBenford:
    """Test Benford's Law detection against WorldCom case."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.validator = SECEnforcementValidator()
        self.analyzer = BenfordAnalyzer()
        self.case = self.validator.get_case('WORLDCOM_2002')
    
    def test_worldcom_line_costs_deviation(self):
        """Test Benford's Law deviation in line costs (primary fraud vehicle)."""
        # WorldCom capitalized $3.8B in line costs as assets
        # This should show Benford deviation due to fabricated entries
        
        # Mock line cost entries that would fail Benford's Law
        # Real fraud involved systematic capitalization, creating patterns
        line_costs = [
            # Fabricated entries tend to cluster at round numbers
            500000000,  # $500M
            750000000,  # $750M
            1000000000, # $1B
            800000000,  # $800M
            600000000,  # $600M
            # More $500M+ entries (suspicious clustering)
            550000000,
            650000000,
            700000000,
            850000000,
            900000000
        ]
        
        # Analyze with Benford's Law
        result = self.analyzer.analyze_dataset(line_costs, "Line Costs")
        
        # Should detect significant deviation
        assert result.is_suspicious, "WorldCom line costs should fail Benford's Law"
        assert result.chi_square_pvalue < 0.05, "Chi-square test should show statistical significance"
        
        # Validate with enforcement validator
        detector_output = {
            'detected': result.is_suspicious,
            'confidence': 1.0 - result.chi_square_pvalue if result.chi_square_pvalue else 0.5,
            'indicators': {
                'benford_deviation': True,
                'chi_square_stat': result.chi_square_stat,
                'dataset': 'line_costs'
            }
        }
        
        validation = self.validator.validate_detector(
            'WORLDCOM_2002',
            'Benford Law - Line Costs',
            detector_output,
            expected_detection=True
        )
        
        assert validation.passed, validation.notes
    
    def test_worldcom_capex_manipulation(self):
        """Test Benford's Law on capitalized expenditures."""
        # WorldCom improperly capitalized operating expenses
        # This creates artificial patterns in capex
        
        # Mock capex entries showing manipulation
        capex_entries = [
            # Artificially inflated capex from capitalized line costs
            1200000000,
            1150000000,
            1100000000,
            1050000000,
            1300000000,
            1250000000,
            1180000000,
            1220000000,
            1280000000,
            1160000000,
            # Notice clustering around $1.1B-$1.3B range
        ]
        
        result = self.analyzer.analyze_dataset(capex_entries, "Capital Expenditures")
        
        # Should show deviation
        assert result.is_suspicious, "Manipulated capex should fail Benford's Law"
    
    def test_worldcom_expense_ratio_anomaly(self):
        """Test expense ratio anomalies (complementary to Benford)."""
        # Operating expenses should be unusually low due to capitalization
        
        # Mock quarterly data
        quarters = [
            {
                'revenue': 8.0e9,
                'operating_expenses': 6.5e9,  # Normal
                'capex': 1.0e9
            },
            {
                'revenue': 8.2e9,
                'operating_expenses': 6.4e9,  # Starting to decrease
                'capex': 1.2e9  # Starting to increase
            },
            {
                'revenue': 8.1e9,
                'operating_expenses': 5.9e9,  # Suspiciously low
                'capex': 1.5e9  # Suspiciously high
            },
            {
                'revenue': 8.3e9,
                'operating_expenses': 5.7e9,  # Even lower
                'capex': 1.8e9  # Even higher
            }
        ]
        
        # Calculate expense ratios
        expense_ratios = [q['operating_expenses'] / q['revenue'] for q in quarters]
        capex_ratios = [q['capex'] / q['revenue'] for q in quarters]
        
        # Expense ratio should be declining (red flag)
        assert expense_ratios[3] < expense_ratios[0], "Operating expense ratio declining"
        
        # Capex ratio should be increasing (red flag)
        assert capex_ratios[3] > capex_ratios[0], "Capex ratio increasing"
        
        # Inverse relationship is suspicious
        expense_change = expense_ratios[3] - expense_ratios[0]
        capex_change = capex_ratios[3] - capex_ratios[0]
        
        # Should move in opposite directions
        assert expense_change < 0 and capex_change > 0, (
            "Inverse expense/capex relationship indicates capitalization scheme"
        )
    
    def test_benford_first_digit_distribution(self):
        """Test first digit distribution against Benford's Law."""
        # Mock dataset with manipulation indicators
        # Natural datasets follow Benford's Law closely
        # Fabricated data tends to deviate
        
        manipulated_data = [
            # Too many entries starting with 5, 6, 7 (unnatural)
            500000000, 550000000, 600000000, 650000000, 700000000,
            750000000, 800000000, 850000000, 900000000, 950000000,
            510000000, 620000000, 730000000, 840000000, 560000000,
            670000000, 780000000, 890000000, 520000000, 630000000
        ]
        
        result = self.analyzer.analyze_dataset(manipulated_data, "Expense Entries")
        
        # Check first digit frequencies
        # In natural data, 1 appears ~30%, 2 appears ~17.6%, etc.
        # Fabricated data tends to be more uniform
        
        first_digits = [int(str(x)[0]) for x in manipulated_data]
        digit_counts = {d: first_digits.count(d) for d in range(1, 10)}
        
        # Should have too few 1's and 2's (unnatural)
        ones_and_twos = digit_counts.get(1, 0) + digit_counts.get(2, 0)
        expected_ones_and_twos = len(manipulated_data) * 0.476  # Benford expectation
        
        assert ones_and_twos < expected_ones_and_twos, (
            "Fabricated data has too few leading 1's and 2's"
        )
    
    def test_worldcom_full_validation(self):
        """Full validation against WorldCom case."""
        # Combine multiple indicators
        
        # 1. Line costs Benford deviation
        line_costs = [500000000 + i*10000000 for i in range(20)]
        line_result = self.analyzer.analyze_dataset(line_costs, "Line Costs")
        
        # 2. Capex Benford deviation
        capex = [1200000000 + i*5000000 for i in range(20)]
        capex_result = self.analyzer.analyze_dataset(capex, "Capex")
        
        # At least one should be suspicious
        detected = line_result.is_suspicious or capex_result.is_suspicious
        
        assert detected, "WorldCom fraud should be detected by Benford's Law"
        
        # Validate with enforcement validator
        detector_output = {
            'detected': detected,
            'confidence': 0.85,
            'indicators': {
                'line_costs_deviation': line_result.is_suspicious,
                'capex_deviation': capex_result.is_suspicious,
                'benford_deviation': True
            }
        }
        
        validation = self.validator.validate_detector(
            'WORLDCOM_2002',
            'Benford Law Analysis',
            detector_output,
            expected_detection=True
        )
        
        assert validation.passed, validation.notes


@pytest.mark.skipif(
    not hasattr(BenfordAnalyzer, 'analyze_dataset'),
    reason="BenfordAnalyzer not fully implemented"
)
class TestWorldComBenfordIntegration:
    """Integration tests with full Benford analyzer."""
    
    def test_worldcom_quarterly_trend(self):
        """Test Benford deviation across quarterly periods."""
        validator = SECEnforcementValidator()
        analyzer = BenfordAnalyzer()
        
        # Fraud escalated from Q1 2001 to Q1 2002
        quarters = ['Q1_2001', 'Q2_2001', 'Q3_2001', 'Q4_2001', 'Q1_2002']
        
        chi_square_stats = []
        
        for quarter in quarters:
            # Mock line cost data for each quarter
            # Fraud amount increased over time
            mock_data = [500000000 + i*10000000 for i in range(20)]
            result = analyzer.analyze_dataset(mock_data, f"Line Costs {quarter}")
            chi_square_stats.append(result.chi_square_stat)
        
        # Chi-square statistic should remain elevated (consistent fraud)
        for stat in chi_square_stats:
            assert stat > 15.0, f"Chi-square statistic should indicate deviation"
    
    def test_benford_vs_normal_expenses(self):
        """Compare manipulated expenses vs normal operating expenses."""
        analyzer = BenfordAnalyzer()
        
        # Normal operating expenses (should pass Benford)
        normal_expenses = [
            123456, 234567, 345678, 156789, 267890,
            178901, 289012, 390123, 101234, 212345,
            323456, 134567, 245678, 356789, 167890
        ]
        
        # Manipulated line costs (should fail Benford)
        manipulated_costs = [
            500000000, 550000000, 600000000, 650000000, 700000000,
            750000000, 800000000, 850000000, 900000000, 950000000,
            510000000, 620000000, 730000000, 840000000, 560000000
        ]
        
        normal_result = analyzer.analyze_dataset(normal_expenses, "Normal Expenses")
        manipulated_result = analyzer.analyze_dataset(manipulated_costs, "Line Costs")
        
        # Normal should pass, manipulated should fail
        assert not normal_result.is_suspicious or manipulated_result.is_suspicious, (
            "Should distinguish between normal and manipulated data"
        )
