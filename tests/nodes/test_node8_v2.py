"""
Unit Tests for Node 8 v2.0 (Beneficial Ownership Tracker)
"""

import pytest
from datetime import date, datetime
from src.nodes.node8_13d_ownership.beneficial_ownership_tracker_v2 import (
    BeneficialOwnershipTrackerV2,
    Schedule13Filing,
    Schedule13Type,
    Schedule13GCategory,
    IntentSignal,
    Severity
)


class TestBeneficialOwnershipTrackerV2:
    """Test beneficial ownership tracker v2.0."""
    
    def test_intent_analysis_hostile(self):
        """Test intent analysis with hostile indicators."""
        tracker = BeneficialOwnershipTrackerV2()
        
        narrative = """
        The reporting persons acquired the shares to seek representation on the board
        of directors and to propose changes to maximize shareholder value. The company
        is undervalued and we believe management should consider strategic alternatives.
        """
        
        intent = tracker.analyze_intent_v2(narrative)
        
        assert intent.intent_score > 0.3  # Should be hostile
        assert len(intent.hostile_indicators) > 0
        assert intent.primary_intent in [
            IntentSignal.BOARD_REPRESENTATION,
            IntentSignal.STRATEGIC_ALTERNATIVES
        ]
    
    def test_intent_analysis_passive(self):
        """Test intent analysis with passive indicators."""
        tracker = BeneficialOwnershipTrackerV2()
        
        narrative = """
        The shares were acquired for investment purposes only in the ordinary course
        of business. The reporting person is a passive investment entity and has no
        intention to influence or control the company. The investment is purely
        financial in nature with no activist agenda.
        """
        
        intent = tracker.analyze_intent_v2(narrative)
        
        assert intent.intent_score < -0.3  # Should be passive
        assert len(intent.passive_indicators) > 0
        assert intent.primary_intent == IntentSignal.PASSIVE_INVESTMENT
    
    def test_13g_to_13d_conversion_detection(self):
        """Test 13G to 13D conversion detection."""
        tracker = BeneficialOwnershipTrackerV2()
        
        # Create sequence of filings showing conversion
        filings = [
            Schedule13Filing(
                filing_type=Schedule13Type.SC_13G,
                cik="0000123456",
                filer_name="Activist Fund",
                subject_company_cik="0000999999",
                subject_company_name="Target Corp",
                filing_date=date(2024, 1, 15),
                event_date=date(2024, 1, 10),
                shares_owned=5000000,
                percent_owned=5.5,
                voting_power=5.5,
                investment_power=5.5,
                purpose_of_transaction="Investment purposes only",
                source_of_funds="Working capital",
                item4_narrative="Investment purposes only",
                schedule_type="13G",
                filing_deadline_days=45,
                days_from_event_to_filing=5,
                is_deadline_compliant=True,
                schedule_13g_category=Schedule13GCategory.PASSIVE
            ),
            Schedule13Filing(
                filing_type=Schedule13Type.SC_13D,
                cik="0000123456",
                filer_name="Activist Fund",
                subject_company_cik="0000999999",
                subject_company_name="Target Corp",
                filing_date=date(2024, 6, 20),
                event_date=date(2024, 6, 15),
                shares_owned=7500000,
                percent_owned=8.2,
                voting_power=8.2,
                investment_power=8.2,
                purpose_of_transaction="Seek board representation",
                source_of_funds="Working capital",
                item4_narrative="To seek representation on the board and maximize shareholder value",
                schedule_type="13D",
                filing_deadline_days=5,
                days_from_event_to_filing=5,
                is_deadline_compliant=True,
                previous_ownership=5.5
            )
        ]
        
        output = tracker.analyze(filings)
        
        assert output.conversions_detected == 1
        assert len([a for a in output.alerts if a.alert_type.value.startswith("Passive to Active")]) == 1
    
    def test_group_formation_detection(self):
        """Test Section 13(d)(3) group formation detection."""
        tracker = BeneficialOwnershipTrackerV2()
        
        # Create filing with declared group members
        filings = [
            Schedule13Filing(
                filing_type=Schedule13Type.SC_13D,
                cik="0000111111",
                filer_name="Lead Activist",
                subject_company_cik="0000999999",
                subject_company_name="Target Corp",
                filing_date=date(2024, 6, 20),
                event_date=date(2024, 6, 15),
                shares_owned=5000000,
                percent_owned=5.5,
                voting_power=5.5,
                investment_power=5.5,
                purpose_of_transaction="Coordinate with group members",
                source_of_funds="Working capital",
                item4_narrative="Acting in concert with other shareholders",
                schedule_type="13D",
                filing_deadline_days=5,
                days_from_event_to_filing=5,
                is_deadline_compliant=True,
                group_member_ciks=["0000222222", "0000333333"]
            )
        ]
        
        output = tracker.analyze(filings)
        
        assert output.group_formations_detected >= 1
    
    def test_filing_deadline_violation(self):
        """Test filing deadline violation detection."""
        tracker = BeneficialOwnershipTrackerV2()
        
        # Create filing with deadline violation
        filings = [
            Schedule13Filing(
                filing_type=Schedule13Type.SC_13D,
                cik="0000123456",
                filer_name="Tardy Filer",
                subject_company_cik="0000999999",
                subject_company_name="Target Corp",
                filing_date=date(2024, 6, 28),
                event_date=date(2024, 6, 15),
                shares_owned=6000000,
                percent_owned=6.5,
                voting_power=6.5,
                investment_power=6.5,
                purpose_of_transaction="Investment",
                source_of_funds="Working capital",
                item4_narrative="Investment purposes",
                schedule_type="13D",
                filing_deadline_days=5,
                days_from_event_to_filing=13,  # Exceeded 5 business days
                is_deadline_compliant=False
            )
        ]
        
        output = tracker.analyze(filings)
        
        assert output.filing_violations_detected == 1
    
    def test_group_coordination_score(self):
        """Test group coordination score calculation."""
        tracker = BeneficialOwnershipTrackerV2()
        
        # Create temporally clustered filings with similar ownership
        filings = [
            Schedule13Filing(
                filing_type=Schedule13Type.SC_13D,
                cik="0000111111",
                filer_name="Fund A",
                subject_company_cik="0000999999",
                subject_company_name="Target Corp",
                filing_date=date(2024, 6, 15),
                event_date=date(2024, 6, 10),
                shares_owned=4000000,
                percent_owned=4.5,
                voting_power=4.5,
                investment_power=4.5,
                purpose_of_transaction="Investment",
                source_of_funds="Working capital",
                item4_narrative="Strategic investment",
                schedule_type="13D",
                filing_deadline_days=5,
                days_from_event_to_filing=5,
                is_deadline_compliant=True
            ),
            Schedule13Filing(
                filing_type=Schedule13Type.SC_13D,
                cik="0000222222",
                filer_name="Fund B",
                subject_company_cik="0000999999",
                subject_company_name="Target Corp",
                filing_date=date(2024, 6, 16),
                event_date=date(2024, 6, 11),
                shares_owned=4200000,
                percent_owned=4.7,
                voting_power=4.7,
                investment_power=4.7,
                purpose_of_transaction="Investment",
                source_of_funds="Working capital",
                item4_narrative="Strategic investment",
                schedule_type="13D",
                filing_deadline_days=5,
                days_from_event_to_filing=5,
                is_deadline_compliant=True
            )
        ]
        
        score = tracker._calculate_group_coordination_score(filings)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be high due to temporal proximity and similar ownership


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
