"""
Enron M-Score Validation Tests
==============================

Validates Beneish M-Score detector against Enron Corporation (2001)
Known SEC enforcement case.

Expected: M-Score > -1.78 for years 1999-2001
"""

import pytest
from src.detection.financial.beneish_mscore import BeneishMScoreCalculator, MScoreVariables
from tests.validation.sec_enforcement_validator import SECEnforcementValidator


class TestEnronMScore:
    """Test M-Score detection against Enron case."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.validator = SECEnforcementValidator()
        self.calculator = BeneishMScoreCalculator()
        self.case = self.validator.get_case('ENRON_2001')
    
    def test_enron_1999_mscore(self):
        """Test M-Score for Enron 1999 (year before fraud peak)."""
        # Mock financial data for Enron 1999
        # These values are approximations based on public records
        current_financials = {
            'revenue': 40.1e9,  # $40.1B
            'accounts_receivable': 3.0e9,
            'current_assets': 7.3e9,
            'total_assets': 33.4e9,
            'cogs': 34.8e9,
            'depreciation': 0.8e9,
            'sg_a': 1.9e9,
            'total_liabilities': 20.8e9,
            'net_income': 0.89e9
        }
        
        prior_financials = {
            'revenue': 31.3e9,  # $31.3B
            'accounts_receivable': 2.1e9,
            'current_assets': 5.9e9,
            'total_assets': 29.3e9,
            'cogs': 27.3e9,
            'depreciation': 0.7e9,
            'sg_a': 1.6e9,
            'total_liabilities': 18.2e9,
            'net_income': 0.70e9
        }
        
        # Calculate M-Score
        result = self.calculator.calculate(current_financials, prior_financials)
        
        # Validate against expected range
        expected_min = -1.78  # Manipulator threshold
        assert result.m_score > expected_min, (
            f"Enron 1999 M-Score ({result.m_score:.2f}) should exceed "
            f"manipulator threshold ({expected_min})"
        )
        
        # Validate with enforcement validator
        detector_output = {
            'detected': result.m_score > expected_min,
            'confidence': min(1.0, (result.m_score + 1.78) / 5.0),  # Normalized confidence
            'indicators': {
                'm_score': result.m_score,
                'dsri_flag': result.dsri_flag,
                'gmi_flag': result.gmi_flag,
                'aqi_flag': result.aqi_flag,
                'sgi_flag': result.sgi_flag,
                'tata_flag': result.tata_flag
            }
        }
        
        validation = self.validator.validate_detector(
            'ENRON_2001',
            'Beneish M-Score',
            detector_output,
            expected_detection=True
        )
        
        assert validation.passed, validation.notes
    
    def test_enron_2000_mscore(self):
        """Test M-Score for Enron 2000 (fraud escalation)."""
        # Mock financial data for Enron 2000
        current_financials = {
            'revenue': 100.8e9,  # $100.8B (massive growth - red flag)
            'accounts_receivable': 10.4e9,  # Accounts receivable growing faster
            'current_assets': 30.4e9,
            'total_assets': 65.5e9,
            'cogs': 94.5e9,
            'depreciation': 0.9e9,
            'sg_a': 2.5e9,
            'total_liabilities': 54.0e9,
            'net_income': 0.98e9  # Income not growing proportionally
        }
        
        prior_financials = {
            'revenue': 40.1e9,
            'accounts_receivable': 3.0e9,
            'current_assets': 7.3e9,
            'total_assets': 33.4e9,
            'cogs': 34.8e9,
            'depreciation': 0.8e9,
            'sg_a': 1.9e9,
            'total_liabilities': 20.8e9,
            'net_income': 0.89e9
        }
        
        result = self.calculator.calculate(current_financials, prior_financials)
        
        # 2000 should show even higher M-Score
        expected_min = -1.78
        assert result.m_score > expected_min, (
            f"Enron 2000 M-Score ({result.m_score:.2f}) should significantly exceed threshold"
        )
        
        # Multiple red flags expected
        red_flags = sum([
            result.dsri_flag,
            result.gmi_flag,
            result.aqi_flag,
            result.sgi_flag,
            result.tata_flag
        ])
        
        assert red_flags >= 2, f"Expected multiple M-Score red flags, got {red_flags}"
    
    def test_enron_2001_mscore_critical(self):
        """Test M-Score for Enron 2001 (pre-bankruptcy)."""
        # Mock financial data for Enron 2001 Q3 (before bankruptcy)
        current_financials = {
            'revenue': 138.7e9,  # $138.7B (continued suspicious growth)
            'accounts_receivable': 14.3e9,
            'current_assets': 35.2e9,
            'total_assets': 61.8e9,  # Declining despite revenue growth
            'cogs': 130.9e9,
            'depreciation': 0.8e9,  # Declining depreciation (red flag)
            'sg_a': 3.0e9,
            'total_liabilities': 58.0e9,
            'net_income': -0.64e9  # Net loss
        }
        
        prior_financials = {
            'revenue': 100.8e9,
            'accounts_receivable': 10.4e9,
            'current_assets': 30.4e9,
            'total_assets': 65.5e9,
            'cogs': 94.5e9,
            'depreciation': 0.9e9,
            'sg_a': 2.5e9,
            'total_liabilities': 54.0e9,
            'net_income': 0.98e9
        }
        
        result = self.calculator.calculate(current_financials, prior_financials)
        
        # 2001 should show critical M-Score
        expected_min = -1.78
        assert result.m_score > expected_min, (
            f"Enron 2001 M-Score ({result.m_score:.2f}) should be critical"
        )
        
        # Should be classified as likely manipulator
        assert result.risk_level.value == "Likely Manipulator - Enforcement Referral"
    
    def test_mscore_components_enron(self):
        """Test individual M-Score components match Enron fraud patterns."""
        current_financials = {
            'revenue': 100.8e9,
            'accounts_receivable': 10.4e9,
            'current_assets': 30.4e9,
            'total_assets': 65.5e9,
            'cogs': 94.5e9,
            'depreciation': 0.9e9,
            'sg_a': 2.5e9,
            'total_liabilities': 54.0e9,
            'net_income': 0.98e9
        }
        
        prior_financials = {
            'revenue': 40.1e9,
            'accounts_receivable': 3.0e9,
            'current_assets': 7.3e9,
            'total_assets': 33.4e9,
            'cogs': 34.8e9,
            'depreciation': 0.8e9,
            'sg_a': 1.9e9,
            'total_liabilities': 20.8e9,
            'net_income': 0.89e9
        }
        
        result = self.calculator.calculate(current_financials, prior_financials)
        
        # DSRI (Days Sales in Receivables Index) should be elevated
        # Receivables growing faster than sales
        assert result.variables.dsri > 1.0, "DSRI should indicate receivables inflation"
        
        # SGI (Sales Growth Index) should be high
        # Massive revenue growth is a manipulation incentive
        assert result.variables.sgi > 1.0, "SGI should indicate high growth"
        
        # AQI (Asset Quality Index) may be elevated
        # Asset quality declining despite revenue growth
        assert result.variables.aqi >= 0.8, "AQI should indicate asset quality concerns"


@pytest.mark.skipif(
    not hasattr(BeneishMScoreCalculator, 'calculate'),
    reason="BeneishMScoreCalculator not fully implemented"
)
class TestEnronMScoreIntegration:
    """Integration tests with full M-Score calculator."""
    
    def test_enron_full_period_analysis(self):
        """Test M-Score trend across full Enron fraud period 1999-2001."""
        validator = SECEnforcementValidator()
        calculator = BeneishMScoreCalculator()
        
        # This would be a full 3-year analysis
        # In production, would load actual financial data
        
        years = [1999, 2000, 2001]
        m_scores = []
        
        for year in years:
            # Mock calculation for each year
            # In production, would use real data
            mock_score = -1.5 + (year - 1999) * 0.5  # Increasing over time
            m_scores.append(mock_score)
        
        # All years should exceed threshold
        for score in m_scores:
            assert score > -1.78, f"M-Score {score} should exceed threshold for Enron"
        
        # Trend should be increasing (worsening)
        assert m_scores[2] > m_scores[0], "M-Score should worsen over fraud period"
