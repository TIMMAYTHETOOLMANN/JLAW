"""
Unit tests for Financial Flow Tracer and Analyzer Modules.
Tests transaction flow analysis, pattern detection, and risk assessment.
"""

import pytest

# ============================================================================
# Test Financial Flow Tracer (tools module)
# ============================================================================

class TestFinancialFlowTracerToolModule:
    """Tests for the financial_flow_tracer tool module."""

    @pytest.fixture
    def sample_transactions(self):
        """Sample transactions for testing."""
        return [
            {
                "reporting_owner": "John Doe",
                "issuer": "ACME Inc",
                "transaction_code": "A",
                "shares": 50000,
                "price_per_share": 0,
                "transaction_date": "2019-01-15",
            },
            {
                "reporting_owner": "John Doe",
                "issuer": "ACME Inc",
                "transaction_code": "S",
                "shares": 25000,
                "price_per_share": 50.0,
                "transaction_date": "2019-01-25",
            },
            {
                "reporting_owner": "Jane Smith",
                "issuer": "ACME Inc",
                "transaction_code": "A",
                "shares": 30000,
                "price_per_share": 0,
                "transaction_date": "2019-01-16",
            },
        ]

    @pytest.fixture
    def flow_tracer_module(self):
        """Load the financial_flow_tracer module."""
        import importlib.util
        import os

        module_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "examples",
            "jarvis_law_sec_auditor",
            "tools",
            "financial_flow_tracer.py",
        )
        spec = importlib.util.spec_from_file_location(
            "financial_flow_tracer", module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_module_loads(self, flow_tracer_module):
        """Test that the module loads successfully."""
        assert hasattr(flow_tracer_module, "FinancialFlowTracer")
        assert hasattr(flow_tracer_module, "trace_flows")
        assert hasattr(flow_tracer_module, "detect_enrichment")
        assert hasattr(flow_tracer_module, "quick_flow_risk")

    def test_financial_flow_tracer_initialization(self, flow_tracer_module):
        """Test FinancialFlowTracer initialization."""
        tracer = flow_tracer_module.FinancialFlowTracer()
        assert tracer is not None
        assert tracer.config is not None
        assert len(tracer.flows) == 0

    def test_add_transaction(self, flow_tracer_module):
        """Test adding a single transaction."""
        tracer = flow_tracer_module.FinancialFlowTracer()
        flow = tracer.add_transaction(
            insider_name="John Doe",
            company_name="ACME Inc",
            transaction_code="P",
            shares=10000,
            price_per_share=50.0,
            transaction_date="2019-01-15",
            is_acquisition=True,
        )
        assert flow is not None
        assert flow.shares == 10000
        assert flow.value == 500000.0
        assert len(tracer.flows) == 1

    def test_trace_flows_function(self, flow_tracer_module, sample_transactions):
        """Test the trace_flows convenience function."""
        result = flow_tracer_module.trace_flows(sample_transactions)
        assert result is not None
        assert result.total_flows == 3
        assert result.risk_score >= 0.0
        assert result.risk_score <= 1.0

    def test_quick_flow_risk_function(self, flow_tracer_module, sample_transactions):
        """Test the quick_flow_risk function."""
        risk = flow_tracer_module.quick_flow_risk(sample_transactions)
        assert risk in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]

    def test_detect_enrichment_function(self, flow_tracer_module, sample_transactions):
        """Test the detect_enrichment function."""
        patterns = flow_tracer_module.detect_enrichment(sample_transactions)
        assert isinstance(patterns, list)
        # Should detect the zero-dollar grant followed by sale.
        assert len(patterns) >= 1
        assert any(p["type"] == "ENRICHMENT_SCHEME" for p in patterns)

    def test_zero_dollar_grant_detection(self, flow_tracer_module):
        """Test detection of zero-dollar high-volume grants."""
        transactions = [
            {
                "reporting_owner": "CEO",
                "issuer": "BigCorp",
                "transaction_code": "A",
                "shares": 100000,
                "price_per_share": 0,
                "transaction_date": "2019-03-01",
            }
        ]
        result = flow_tracer_module.trace_flows(transactions)
        # Should flag zero-dollar high volume.
        pattern_types = [p.pattern_type for p in result.patterns]
        assert "ZERO_DOLLAR_HIGH_VOLUME" in pattern_types

    def test_circular_flow_detection(self, flow_tracer_module):
        """Test detection of circular flows."""
        transactions = [
            {
                "reporting_owner": "Insider A",
                "issuer": "Corp X",
                "transaction_code": "P",
                "shares": 50000,
                "price_per_share": 100.0,
                "transaction_date": "2019-01-10",
            },
            {
                "reporting_owner": "Insider A",
                "issuer": "Corp X",
                "transaction_code": "S",
                "shares": 50000,
                "price_per_share": 105.0,
                "transaction_date": "2019-01-20",
            },
        ]
        result = flow_tracer_module.trace_flows(transactions)
        # Should detect circular flow pattern.
        pattern_types = [p.pattern_type for p in result.patterns]
        assert "CIRCULAR_FLOW" in pattern_types

    def test_flow_types(self, flow_tracer_module):
        """Test flow type classification."""
        assert flow_tracer_module.FlowType.ACQUISITION.value == "acquisition"
        assert flow_tracer_module.FlowType.DISPOSITION.value == "disposition"
        assert flow_tracer_module.FlowType.GRANT.value == "grant"
        assert flow_tracer_module.FlowType.GIFT.value == "gift"

    def test_flow_risk_levels(self, flow_tracer_module):
        """Test flow risk level classification."""
        assert flow_tracer_module.FlowRiskLevel.CRITICAL.value == "critical"
        assert flow_tracer_module.FlowRiskLevel.HIGH.value == "high"
        assert flow_tracer_module.FlowRiskLevel.MEDIUM.value == "medium"
        assert flow_tracer_module.FlowRiskLevel.LOW.value == "low"

    def test_generate_flow_report(self, flow_tracer_module, sample_transactions):
        """Test report generation."""
        tracer = flow_tracer_module.FinancialFlowTracer()
        for tx in sample_transactions:
            tracer.add_transaction(
                insider_name=tx["reporting_owner"],
                company_name=tx["issuer"],
                transaction_code=tx["transaction_code"],
                shares=tx["shares"],
                price_per_share=tx["price_per_share"],
                transaction_date=tx["transaction_date"],
                is_acquisition=tx["transaction_code"] in ["A", "P"],
            )
        report = tracer.generate_flow_report()
        assert "summary" in report
        assert "patterns" in report
        assert "findings" in report
        assert "recommendations" in report


# ============================================================================
# Test Financial Flow Analyzer (core forensics module)
# ============================================================================

class TestFinancialFlowAnalyzerCoreModule:
    """Tests for the financial_flow_analyzer core forensics module."""

    @pytest.fixture
    def sample_filings(self):
        """Sample SEC filings for testing."""
        return [
            {
                "reporting_owner": {"name": "John Doe"},
                "issuer": {"name": "ACME Inc"},
                "transactions": [
                    {
                        "transaction_code": "A",
                        "shares": 50000,
                        "price_per_share": 0,
                        "transaction_date": "2019-01-15",
                    },
                    {
                        "transaction_code": "S",
                        "shares": 25000,
                        "price_per_share": 50.0,
                        "transaction_date": "2019-01-30",
                    },
                ],
            },
            {
                "reporting_owner": {"name": "Jane Smith"},
                "issuer": {"name": "ACME Inc"},
                "transactions": [
                    {
                        "transaction_code": "A",
                        "shares": 30000,
                        "price_per_share": 0,
                        "transaction_date": "2019-01-16",
                    },
                ],
            },
            {
                "reporting_owner": {"name": "Bob Wilson"},
                "issuer": {"name": "ACME Inc"},
                "transactions": [
                    {
                        "transaction_code": "A",
                        "shares": 20000,
                        "price_per_share": 0,
                        "transaction_date": "2019-01-17",
                    },
                ],
            },
        ]

    @pytest.fixture
    def flow_analyzer_module(self):
        """Load the financial_flow_analyzer module."""
        import importlib.util
        import os

        module_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "src",
            "forensics",
            "financial_forensics",
            "financial_flow_analyzer.py",
        )
        spec = importlib.util.spec_from_file_location(
            "financial_flow_analyzer", module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_module_loads(self, flow_analyzer_module):
        """Test that the module loads successfully."""
        assert hasattr(flow_analyzer_module, "FinancialFlowAnalyzer")
        assert hasattr(flow_analyzer_module, "analyze_filing_flows")
        assert hasattr(flow_analyzer_module, "quick_flow_assessment")

    def test_analyzer_initialization(self, flow_analyzer_module):
        """Test FinancialFlowAnalyzer initialization."""
        analyzer = flow_analyzer_module.FinancialFlowAnalyzer()
        assert analyzer is not None
        assert analyzer.config is not None

    def test_analyze_filings(self, flow_analyzer_module, sample_filings):
        """Test filing analysis."""
        analyzer = flow_analyzer_module.FinancialFlowAnalyzer()
        result = analyzer.analyze_filings(sample_filings)
        assert result is not None
        assert result.filings_analyzed == 3
        assert result.total_transactions == 4
        assert result.overall_risk_score >= 0.0
        assert result.overall_risk_score <= 1.0

    def test_insider_profiles(self, flow_analyzer_module, sample_filings):
        """Test insider profile generation."""
        analyzer = flow_analyzer_module.FinancialFlowAnalyzer()
        result = analyzer.analyze_filings(sample_filings)
        assert len(result.insider_profiles) >= 3
        # Check for John Doe profile.
        john_profile = next(
            (p for p in result.insider_profiles if p.insider_name == "John Doe"),
            None,
        )
        assert john_profile is not None
        assert john_profile.total_grants == 50000
        assert john_profile.total_dispositions == 25000
        assert john_profile.zero_dollar_shares == 50000

    def test_enrichment_scheme_detection(self, flow_analyzer_module):
        """Test enrichment scheme detection."""
        filings = [
            {
                "reporting_owner": {"name": "Executive"},
                "issuer": {"name": "Corp"},
                "transactions": [
                    {
                        "transaction_code": "A",
                        "shares": 100000,
                        "price_per_share": 0,
                        "transaction_date": "2019-01-01",
                    },
                    {
                        "transaction_code": "S",
                        "shares": 50000,
                        "price_per_share": 100.0,
                        "transaction_date": "2019-01-15",
                    },
                ],
            }
        ]
        analyzer = flow_analyzer_module.FinancialFlowAnalyzer()
        result = analyzer.analyze_filings(filings)
        pattern_types = [p.pattern_type.value for p in result.detected_patterns]
        assert "enrichment_scheme" in pattern_types

    def test_coordinated_activity_detection(self, flow_analyzer_module, sample_filings):
        """Test coordinated activity detection."""
        analyzer = flow_analyzer_module.FinancialFlowAnalyzer()
        result = analyzer.analyze_filings(sample_filings)
        # With 3 insiders trading within 2 days, should detect coordination.
        pattern_types = [p.pattern_type.value for p in result.detected_patterns]
        assert "coordinated_trading" in pattern_types

    def test_zero_dollar_high_volume_detection(self, flow_analyzer_module):
        """Test zero-dollar high volume detection."""
        filings = [
            {
                "reporting_owner": {"name": "CEO"},
                "issuer": {"name": "BigCorp"},
                "transactions": [
                    {
                        "transaction_code": "A",
                        "shares": 500000,
                        "price_per_share": 0,
                        "transaction_date": "2019-01-01",
                    },
                ],
            }
        ]
        analyzer = flow_analyzer_module.FinancialFlowAnalyzer()
        result = analyzer.analyze_filings(filings)
        pattern_types = [p.pattern_type.value for p in result.detected_patterns]
        assert "zero_dollar_high_volume" in pattern_types

    def test_analyze_filing_flows_function(self, flow_analyzer_module, sample_filings):
        """Test the analyze_filing_flows convenience function."""
        result = flow_analyzer_module.analyze_filing_flows(sample_filings)
        assert result is not None
        assert result.filings_analyzed == 3

    def test_quick_flow_assessment_function(self, flow_analyzer_module, sample_filings):
        """Test the quick_flow_assessment convenience function."""
        risk = flow_analyzer_module.quick_flow_assessment(sample_filings)
        assert risk in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]

    def test_flow_pattern_types(self, flow_analyzer_module):
        """Test flow pattern type enumeration."""
        assert flow_analyzer_module.FlowPatternType.CIRCULAR_FLOW.value == "circular_flow"
        assert (
            flow_analyzer_module.FlowPatternType.ENRICHMENT_SCHEME.value
            == "enrichment_scheme"
        )
        assert (
            flow_analyzer_module.FlowPatternType.COORDINATED_TRADING.value
            == "coordinated_trading"
        )

    def test_flow_risk_severity(self, flow_analyzer_module):
        """Test flow risk severity enumeration."""
        assert flow_analyzer_module.FlowRiskSeverity.CRITICAL.value == "critical"
        assert flow_analyzer_module.FlowRiskSeverity.HIGH.value == "high"
        assert flow_analyzer_module.FlowRiskSeverity.MEDIUM.value == "medium"

    def test_findings_generation(self, flow_analyzer_module, sample_filings):
        """Test findings generation."""
        analyzer = flow_analyzer_module.FinancialFlowAnalyzer()
        result = analyzer.analyze_filings(sample_filings)
        assert len(result.key_findings) > 0
        assert len(result.recommendations) > 0

    def test_metadata_generation(self, flow_analyzer_module, sample_filings):
        """Test metadata generation."""
        analyzer = flow_analyzer_module.FinancialFlowAnalyzer()
        result = analyzer.analyze_filings(sample_filings)
        assert "analysis_timestamp" in result.metadata
        assert "pattern_counts" in result.metadata

    def test_empty_filings(self, flow_analyzer_module):
        """Test handling of empty filings."""
        analyzer = flow_analyzer_module.FinancialFlowAnalyzer()
        result = analyzer.analyze_filings([])
        assert result.filings_analyzed == 0
        assert result.total_transactions == 0
        assert result.overall_risk_score == 0.0

    def test_custom_config(self, flow_analyzer_module):
        """Test custom configuration."""
        config = {
            "circular_window_days": 60,
            "high_value_threshold": 500000.0,
        }
        analyzer = flow_analyzer_module.FinancialFlowAnalyzer(config=config)
        assert analyzer.config["circular_window_days"] == 60
        assert analyzer.config["high_value_threshold"] == 500000.0


# ============================================================================
# Integration Tests
# ============================================================================

class TestFinancialFlowIntegration:
    """Integration tests for financial flow modules."""

    @pytest.fixture
    def flow_tracer_module(self):
        """Load the financial_flow_tracer module."""
        import importlib.util
        import os

        module_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "examples",
            "jarvis_law_sec_auditor",
            "tools",
            "financial_flow_tracer.py",
        )
        spec = importlib.util.spec_from_file_location(
            "financial_flow_tracer", module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @pytest.fixture
    def flow_analyzer_module(self):
        """Load the financial_flow_analyzer module."""
        import importlib.util
        import os

        module_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "src",
            "forensics",
            "financial_forensics",
            "financial_flow_analyzer.py",
        )
        spec = importlib.util.spec_from_file_location(
            "financial_flow_analyzer", module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_both_modules_detect_same_patterns(
        self, flow_tracer_module, flow_analyzer_module
    ):
        """Test that both modules detect similar patterns."""
        # Same data in different formats.
        transactions = [
            {
                "reporting_owner": "John Doe",
                "issuer": "Corp",
                "transaction_code": "A",
                "shares": 50000,
                "price_per_share": 0,
                "transaction_date": "2019-01-15",
            },
            {
                "reporting_owner": "John Doe",
                "issuer": "Corp",
                "transaction_code": "S",
                "shares": 25000,
                "price_per_share": 50.0,
                "transaction_date": "2019-01-25",
            },
        ]
        filings = [
            {
                "reporting_owner": {"name": "John Doe"},
                "issuer": {"name": "Corp"},
                "transactions": [
                    {
                        "transaction_code": "A",
                        "shares": 50000,
                        "price_per_share": 0,
                        "transaction_date": "2019-01-15",
                    },
                    {
                        "transaction_code": "S",
                        "shares": 25000,
                        "price_per_share": 50.0,
                        "transaction_date": "2019-01-25",
                    },
                ],
            }
        ]

        tracer_result = flow_tracer_module.trace_flows(transactions)
        analyzer_result = flow_analyzer_module.analyze_filing_flows(filings)

        # Both should detect enrichment and zero-dollar patterns.
        tracer_patterns = set(p.pattern_type for p in tracer_result.patterns)
        analyzer_patterns = set(p.pattern_type.value for p in analyzer_result.detected_patterns)

        assert "ENRICHMENT_SCHEME" in tracer_patterns
        assert "enrichment_scheme" in analyzer_patterns

    def test_high_risk_detection_consistency(
        self, flow_tracer_module, flow_analyzer_module
    ):
        """Test that high-risk scenarios are consistently flagged."""
        # Obvious high-risk scenario.
        transactions = [
            {
                "reporting_owner": "CEO",
                "issuer": "Corp",
                "transaction_code": "A",
                "shares": 1000000,
                "price_per_share": 0,
                "transaction_date": "2019-01-01",
            },
            {
                "reporting_owner": "CEO",
                "issuer": "Corp",
                "transaction_code": "S",
                "shares": 1000000,
                "price_per_share": 100.0,
                "transaction_date": "2019-01-10",
            },
        ]
        filings = [
            {
                "reporting_owner": {"name": "CEO"},
                "issuer": {"name": "Corp"},
                "transactions": [
                    {
                        "transaction_code": "A",
                        "shares": 1000000,
                        "price_per_share": 0,
                        "transaction_date": "2019-01-01",
                    },
                    {
                        "transaction_code": "S",
                        "shares": 1000000,
                        "price_per_share": 100.0,
                        "transaction_date": "2019-01-10",
                    },
                ],
            }
        ]

        tracer_risk = flow_tracer_module.quick_flow_risk(transactions)
        analyzer_risk = flow_analyzer_module.quick_flow_assessment(filings)

        # Both should flag as high or critical risk.
        assert tracer_risk in ["CRITICAL", "HIGH"]
        assert analyzer_risk in ["CRITICAL", "HIGH"]
