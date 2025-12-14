"""
Unit tests for Node 2: DEF 14A Compensation Analyzer
"""

import pytest
from datetime import date
from decimal import Decimal
from src.nodes.node2_def14a.compensation_analyzer import (
    DEF14ACompensationAnalyzer,
    CompensationAnalysisResult,
    NEOCompensation,
    SayOnPayVote,
    SayOnPayOutcome,
    CEOPayRatio,
    GoldenParachute,
    RelatedPartyTransaction,
    ClawbackPolicy,
    CompensationType,
    AwardVestingType,
    CompensationViolationType
)


class TestDEF14ACompensationAnalyzer:
    """Test suite for DEF 14A compensation analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return DEF14ACompensationAnalyzer(mock_mode=True)
    
    @pytest.mark.asyncio
    async def test_mock_mode_analysis(self, analyzer):
        """Test analysis in mock mode generates complete results."""
        result = await analyzer.analyze_proxy(
            proxy_content="",
            cik="0000320187",
            company_name="Test Corp",
            fiscal_year=2024,
            filing_date=date(2024, 4, 15),
            accession_number="0000320187-24-000001"
        )
        
        assert result.cik == "0000320187"
        assert result.company_name == "Test Corp"
        assert result.fiscal_year == 2024
        assert len(result.neo_compensation) > 0
        assert result.say_on_pay_vote is not None
        assert result.ceo_pay_ratio is not None
        assert result.total_neo_compensation > 0
    
    @pytest.mark.asyncio
    async def test_mock_mode_neo_compensation(self, analyzer):
        """Test NEO compensation extraction in mock mode."""
        result = await analyzer.analyze_proxy(
            proxy_content="",
            cik="0000320187",
            company_name="Test Corp",
            fiscal_year=2024,
            filing_date=date(2024, 4, 15),
            accession_number="0000320187-24-000001"
        )
        
        # Should have at least 3 NEOs
        assert len(result.neo_compensation) >= 3
        
        # Should have a CEO
        ceo = next((neo for neo in result.neo_compensation if neo.is_ceo), None)
        assert ceo is not None
        assert "CEO" in ceo.title or "Chief Executive" in ceo.title
        
        # CEO should have highest compensation
        ceo_comp = ceo.total_compensation
        other_neos = [neo for neo in result.neo_compensation if not neo.is_ceo]
        for neo in other_neos:
            assert ceo_comp >= neo.total_compensation
    
    def test_neo_compensation_validation(self):
        """Test NEO compensation arithmetic validation."""
        neo = NEOCompensation(
            name="John Doe",
            title="CEO",
            fiscal_year=2024,
            base_salary=Decimal("1000000"),
            bonus=Decimal("500000"),
            stock_awards=Decimal("3000000"),
            option_awards=Decimal("1000000"),
            non_equity_incentive=Decimal("750000"),
            pension_change=Decimal("100000"),
            other_compensation=Decimal("150000"),
            total_compensation=Decimal("6500000"),  # Correct total
            performance_based_pct=0.65,
            time_based_pct=0.35,
            is_ceo=True
        )
        
        # Should validate correctly
        assert neo.validate_total() == True
        assert neo.is_ceo == True
        assert neo.performance_based_pct == 0.65
        
        # Test invalid total
        neo_invalid = NEOCompensation(
            name="Jane Smith",
            title="CFO",
            fiscal_year=2024,
            base_salary=Decimal("1000000"),
            bonus=Decimal("500000"),
            stock_awards=Decimal("3000000"),
            option_awards=Decimal("1000000"),
            non_equity_incentive=Decimal("750000"),
            pension_change=Decimal("100000"),
            other_compensation=Decimal("150000"),
            total_compensation=Decimal("9999999"),  # Wrong total
            performance_based_pct=0.60,
            time_based_pct=0.40,
            is_ceo=False
        )
        
        assert neo_invalid.validate_total() == False
    
    def test_say_on_pay_outcome_classification(self):
        """Test Say-on-Pay outcome classification."""
        # Strong support (>90%)
        assert SayOnPayOutcome.STRONG_SUPPORT.value == "strong_support"
        
        # Approved (50-90%)
        assert SayOnPayOutcome.APPROVED.value == "approved"
        
        # Weak support (50-70%)
        assert SayOnPayOutcome.WEAK_SUPPORT.value == "weak_support"
        
        # Rejected (<50%)
        assert SayOnPayOutcome.REJECTED.value == "rejected"
    
    def test_say_on_pay_vote_structure(self):
        """Test Say-on-Pay vote structure."""
        vote = SayOnPayVote(
            fiscal_year=2024,
            filing_date=date(2024, 4, 15),
            votes_for=85000000,
            votes_against=15000000,
            votes_abstain=5000000,
            broker_non_votes=2000000,
            approval_percentage=85.0,
            outcome=SayOnPayOutcome.APPROVED,
            total_votes_cast=0  # Should auto-calculate
        )
        
        assert vote.total_votes_cast == 105000000  # sum of for, against, abstain
        assert vote.outcome == SayOnPayOutcome.APPROVED
    
    def test_ceo_pay_ratio_outlier_detection(self):
        """Test CEO pay ratio outlier detection."""
        # Normal ratio
        normal_ratio = CEOPayRatio(
            fiscal_year=2024,
            ceo_total_compensation=Decimal("10000000"),
            median_worker_compensation=Decimal("50000"),
            pay_ratio=200.0,
            methodology_description="Standard calculation"
        )
        assert normal_ratio.is_outlier() == False
        
        # Outlier ratio (>500:1)
        outlier_ratio = CEOPayRatio(
            fiscal_year=2024,
            ceo_total_compensation=Decimal("30000000"),
            median_worker_compensation=Decimal("50000"),
            pay_ratio=600.0,
            methodology_description="Standard calculation"
        )
        assert outlier_ratio.is_outlier() == True
    
    def test_golden_parachute_excessive_detection(self):
        """Test golden parachute excessive severance detection."""
        # Normal severance
        normal_gp = GoldenParachute(
            executive_name="John Doe",
            trigger_events=["change_in_control"],
            cash_severance_multiple=2.0,
            equity_acceleration=True,
            benefit_continuation_months=12,
            tax_gross_up=False,
            estimated_total_value=Decimal("5000000")
        )
        assert normal_gp.is_excessive() == False
        
        # Excessive severance (>3x)
        excessive_gp = GoldenParachute(
            executive_name="Jane Smith",
            trigger_events=["change_in_control", "termination"],
            cash_severance_multiple=3.5,
            equity_acceleration=True,
            benefit_continuation_months=24,
            tax_gross_up=True,
            estimated_total_value=Decimal("15000000")
        )
        assert excessive_gp.is_excessive() == True
    
    def test_related_party_transaction_materiality(self):
        """Test related party transaction materiality threshold."""
        # Non-material transaction
        small_rpt = RelatedPartyTransaction(
            transaction_date=date(2024, 1, 15),
            related_party_name="Related Company Inc",
            relationship="Executive's family member",
            transaction_description="Consulting services",
            transaction_amount=Decimal("50000"),
            ongoing=False
        )
        assert small_rpt.is_material() == False
        
        # Material transaction (>$120,000)
        large_rpt = RelatedPartyTransaction(
            transaction_date=date(2024, 1, 15),
            related_party_name="Related Company Inc",
            relationship="Executive's family member",
            transaction_description="Consulting services",
            transaction_amount=Decimal("250000"),
            ongoing=True
        )
        assert large_rpt.is_material() == True
    
    def test_clawback_policy_structure(self):
        """Test clawback policy structure."""
        # With policy
        with_policy = ClawbackPolicy(
            policy_exists=True,
            triggers=["financial_restatement", "misconduct"],
            lookback_period_years=3,
            covers_all_neos=True,
            restatement_triggered=False,
            amount_recovered=Decimal("0")
        )
        assert with_policy.policy_exists == True
        assert len(with_policy.triggers) == 2
        
        # Without policy
        without_policy = ClawbackPolicy(
            policy_exists=False,
            triggers=[],
            lookback_period_years=0,
            covers_all_neos=False
        )
        assert without_policy.policy_exists == False
    
    @pytest.mark.asyncio
    async def test_pay_performance_score_calculation(self, analyzer):
        """Test pay-performance alignment score calculation."""
        result = await analyzer.analyze_proxy(
            proxy_content="",
            cik="0000320187",
            company_name="Test Corp",
            fiscal_year=2024,
            filing_date=date(2024, 4, 15),
            accession_number="0000320187-24-000001"
        )
        
        # Score should be in valid range
        assert 0 <= result.pay_performance_alignment_score <= 100
        assert 0 <= result.governance_score <= 100
        assert 0 <= result.disclosure_quality_score <= 100
    
    @pytest.mark.asyncio
    async def test_compensation_types_enum(self):
        """Test compensation type enum values."""
        assert CompensationType.BASE_SALARY.value == "base_salary"
        assert CompensationType.BONUS.value == "bonus"
        assert CompensationType.STOCK_AWARDS.value == "stock_awards"
        assert CompensationType.OPTION_AWARDS.value == "option_awards"
        assert CompensationType.NON_EQUITY_INCENTIVE.value == "non_equity_incentive"
        assert CompensationType.PENSION_CHANGE.value == "pension_change"
        assert CompensationType.OTHER_COMPENSATION.value == "other_compensation"
    
    @pytest.mark.asyncio
    async def test_award_vesting_types_enum(self):
        """Test award vesting type enum values."""
        assert AwardVestingType.PERFORMANCE_BASED.value == "performance_based"
        assert AwardVestingType.TIME_BASED.value == "time_based"
        assert AwardVestingType.MARKET_BASED.value == "market_based"
        assert AwardVestingType.HYBRID.value == "hybrid"
    
    @pytest.mark.asyncio
    async def test_result_to_dict_conversion(self, analyzer):
        """Test conversion of result to dictionary for JSON serialization."""
        result = await analyzer.analyze_proxy(
            proxy_content="",
            cik="0000320187",
            company_name="Test Corp",
            fiscal_year=2024,
            filing_date=date(2024, 4, 15),
            accession_number="0000320187-24-000001"
        )
        
        result_dict = result.to_dict()
        
        # Verify all required fields
        assert "cik" in result_dict
        assert "company_name" in result_dict
        assert "fiscal_year" in result_dict
        assert "filing_date" in result_dict
        assert "total_neo_compensation" in result_dict
        assert "pay_performance_alignment_score" in result_dict
        assert "governance_score" in result_dict
        assert "disclosure_quality_score" in result_dict
        assert "evidence_hash" in result_dict
        
        # Verify types
        assert isinstance(result_dict["pay_performance_alignment_score"], float)
        assert isinstance(result_dict["governance_score"], float)
        assert isinstance(result_dict["disclosure_quality_score"], float)
    
    @pytest.mark.asyncio
    async def test_mock_mode_generates_violations(self, analyzer):
        """Test that mock mode can generate realistic violation scenarios."""
        result = await analyzer.analyze_proxy(
            proxy_content="",
            cik="0000320187",
            company_name="Test Corp",
            fiscal_year=2024,
            filing_date=date(2024, 4, 15),
            accession_number="0000320187-24-000001"
        )
        
        # Mock mode should produce valid results even without violations
        assert isinstance(result.violations, list)
        assert isinstance(result.red_flags, list)
    
    @pytest.mark.asyncio
    async def test_evidence_hash_generation(self, analyzer):
        """Test evidence hash generation for chain of custody."""
        result = await analyzer.analyze_proxy(
            proxy_content="Sample proxy content for testing",
            cik="0000320187",
            company_name="Test Corp",
            fiscal_year=2024,
            filing_date=date(2024, 4, 15),
            accession_number="0000320187-24-000001"
        )
        
        # Should generate a valid SHA-256 hash
        assert result.evidence_hash is not None
        assert len(result.evidence_hash) == 64  # SHA-256 hex length
        assert result.evidence_hash.isalnum()
    
    @pytest.mark.asyncio
    async def test_analyzer_thresholds(self):
        """Test analyzer threshold constants."""
        analyzer = DEF14ACompensationAnalyzer(mock_mode=False)
        
        # ISS/Glass Lewis thresholds
        assert analyzer.ISS_LOW_SUPPORT_THRESHOLD == 0.70
        assert analyzer.GLASS_LEWIS_CONCERN_THRESHOLD == 0.80
        assert analyzer.STRONG_SUPPORT_THRESHOLD == 0.90
        
        # Performance-based compensation
        assert analyzer.PERFORMANCE_BASED_MIN_PCT == 0.50
        
        # Severance multiples
        assert analyzer.EXCESSIVE_SEVERANCE_MULTIPLE == 3.0
        
        # CEO pay ratio
        assert analyzer.CEO_PAY_RATIO_OUTLIER == 500.0
    
    @pytest.mark.asyncio
    async def test_compensation_violation_type_enum(self):
        """Test compensation violation type enum values."""
        assert CompensationViolationType.SAY_ON_PAY_FAILURE.value == "say_on_pay_failure"
        assert CompensationViolationType.PERFORMANCE_MISALIGNMENT.value == "compensation_performance_misalignment"
        assert CompensationViolationType.UNDISCLOSED_PERKS.value == "undisclosed_perquisites"
        assert CompensationViolationType.RELATED_PARTY_TRANSACTION.value == "related_party_transaction"
        assert CompensationViolationType.GOLDEN_PARACHUTE_UNDISCLOSED.value == "golden_parachute_undisclosed"
        assert CompensationViolationType.EXCESSIVE_SEVERANCE.value == "excessive_severance"
        assert CompensationViolationType.BACKDATED_GRANTS.value == "backdated_option_grants"
        assert CompensationViolationType.CLAWBACK_VIOLATION.value == "clawback_policy_violation"
        assert CompensationViolationType.PEER_GROUP_MANIPULATION.value == "peer_group_manipulation"
        assert CompensationViolationType.CD_A_MATERIAL_OMISSION.value == "cd_a_material_omission"


class TestCompensationAnalysisResult:
    """Test suite for CompensationAnalysisResult dataclass."""
    
    def test_result_initialization(self):
        """Test result initialization with minimal data."""
        result = CompensationAnalysisResult(
            cik="0000320187",
            company_name="Test Corp",
            fiscal_year=2024,
            filing_date=date(2024, 4, 15),
            accession_number="0000320187-24-000001",
            neo_compensation=[],
            total_neo_compensation=Decimal("0"),
            say_on_pay_vote=None,
            ceo_pay_ratio=None
        )
        
        assert result.cik == "0000320187"
        assert result.company_name == "Test Corp"
        assert len(result.neo_compensation) == 0
        assert result.total_neo_compensation == Decimal("0")
        assert result.violations == []
        assert result.red_flags == []
        assert result.say_on_pay_vote is None
        assert result.ceo_pay_ratio is None
