"""
Test Suite for SEC Data Resources and Cross-Analysis Engine
============================================================

Tests the comprehensive SEC Data Resources integration including:
- SECDataResourcesClient endpoints
- SECCrossAnalysisEngine functionality
- Data model serialization
- Cross-reference analysis logic
"""

import pytest
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.integrations.sec_edgar.sec_data_resources import (
    SECDataResourcesClient,
    SECDataEndpoint,
    FinancialStatementFact,
    FailsToDeliverRecord,
    InvestmentAdviser,
    MutualFundHolding,
    EnforcementAction,
    MarketStructureMetric,
    FullTextSearchResult,
    RSSFilingEntry
)

from src.integrations.sec_edgar.cross_analysis_engine import (
    SECCrossAnalysisEngine,
    AnalysisType,
    AlertSeverity,
    ForensicAlert,
    DataAcquisitionReport,
    CrossAnalysisResult
)


class TestSECDataEndpoints:
    """Test SEC Data endpoint definitions."""
    
    def test_all_endpoints_defined(self):
        """Verify all required SEC endpoints are defined."""
        endpoints = [
            SECDataEndpoint.SUBMISSIONS,
            SECDataEndpoint.COMPANY_FACTS,
            SECDataEndpoint.COMPANY_CONCEPT,
            SECDataEndpoint.FRAMES,
            SECDataEndpoint.FULL_TEXT_SEARCH,
            SECDataEndpoint.COMPANY_TICKERS,
            SECDataEndpoint.FAILS_TO_DELIVER,
            SECDataEndpoint.IAPD_API,
            SECDataEndpoint.RSS_FILINGS,
            SECDataEndpoint.ENFORCEMENT_RELEASES
        ]
        
        for endpoint in endpoints:
            assert endpoint.value is not None
            assert isinstance(endpoint.value, str)
            assert endpoint.value.startswith("https://")
    
    def test_company_facts_url_format(self):
        """Test company facts URL formatting."""
        url = SECDataEndpoint.COMPANY_FACTS.value.format(cik="0000320193")
        assert "0000320193" in url
        assert "companyfacts" in url
        assert ".json" in url


class TestDataModels:
    """Test SEC data model classes."""
    
    def test_fails_to_deliver_record(self):
        """Test FailsToDeliverRecord creation and serialization."""
        record = FailsToDeliverRecord(
            settlement_date=date(2024, 1, 15),
            cusip="12345678",
            symbol="AAPL",
            quantity=10000,
            description="APPLE INC",
            price=185.50
        )
        
        assert record.symbol == "AAPL"
        assert record.quantity == 10000
        
        data = record.to_dict()
        assert data["settlement_date"] == "2024-01-15"
        assert data["symbol"] == "AAPL"
        assert data["quantity"] == 10000
    
    def test_investment_adviser(self):
        """Test InvestmentAdviser creation and serialization."""
        adviser = InvestmentAdviser(
            firm_crd="12345",
            firm_name="Test Advisers LLC",
            sec_number="801-12345",
            main_office_city="New York",
            main_office_state="NY",
            aum=1000000000.0,
            discretionary_aum=900000000.0,
            non_discretionary_aum=100000000.0,
            total_employees=50,
            registration_status="Active",
            registration_date=date(2010, 1, 1)
        )
        
        assert adviser.firm_name == "Test Advisers LLC"
        assert adviser.aum == 1000000000.0
        
        data = adviser.to_dict()
        assert data["firm_crd"] == "12345"
        assert data["aum"] == 1000000000.0
        assert data["registration_date"] == "2010-01-01"
    
    def test_full_text_search_result(self):
        """Test FullTextSearchResult serialization."""
        result = FullTextSearchResult(
            accession_number="0001234567-24-000001",
            cik="320193",
            company_name="Apple Inc.",
            form_type="10-K",
            filing_date=date(2024, 1, 15),
            file_description="Annual Report",
            document_url="https://www.sec.gov/...",
            score=0.95,
            highlights=["matched text here"]
        )
        
        data = result.to_dict()
        assert data["cik"] == "320193"
        assert data["score"] == 0.95
        assert len(data["highlights"]) == 1
    
    def test_rss_filing_entry(self):
        """Test RSSFilingEntry serialization."""
        entry = RSSFilingEntry(
            accession_number="0001234567-24-000001",
            cik="320193",
            company_name="Apple Inc.",
            form_type="4",
            filing_date=datetime(2024, 1, 15, 10, 30, 0),
            accepted_date=datetime(2024, 1, 15, 10, 25, 0),
            filing_url="https://www.sec.gov/...",
            file_number="001-12345"
        )
        
        data = entry.to_dict()
        assert data["form_type"] == "4"
        assert "2024-01-15" in data["filing_date"]


class TestForensicAlerts:
    """Test forensic alert models."""
    
    def test_forensic_alert_creation(self):
        """Test ForensicAlert creation and serialization."""
        alert = ForensicAlert(
            alert_id="TEST-ALERT-001",
            severity=AlertSeverity.HIGH,
            analysis_type=AnalysisType.INSIDER_FTD_CORRELATION,
            title="Test Alert",
            description="This is a test alert",
            evidence=[{"type": "test", "data": "sample"}],
            related_entities=["320193"],
            timestamp=datetime(2024, 1, 15, 12, 0, 0),
            statutory_references=["17 CFR § 240.10b-5"],
            recommended_actions=["Review data"],
            confidence_score=0.85
        )
        
        assert alert.severity == AlertSeverity.HIGH
        assert alert.analysis_type == AnalysisType.INSIDER_FTD_CORRELATION
        
        data = alert.to_dict()
        assert data["alert_id"] == "TEST-ALERT-001"
        assert data["severity"] == "high"
        assert data["confidence_score"] == 0.85
    
    def test_alert_severity_ordering(self):
        """Test that all required alert severities are defined."""
        # Test explicit existence of all severity levels
        assert AlertSeverity.CRITICAL is not None
        assert AlertSeverity.HIGH is not None
        assert AlertSeverity.MEDIUM is not None
        assert AlertSeverity.LOW is not None
        assert AlertSeverity.INFORMATIONAL is not None
        
        # Verify the expected count of severity levels
        assert len(list(AlertSeverity)) == 5


class TestAnalysisTypes:
    """Test analysis type enumeration."""
    
    def test_all_analysis_types_defined(self):
        """Verify all analysis types are defined."""
        expected_types = [
            "insider_ftd_correlation",
            "institutional_movement",
            "executive_network",
            "material_event_timing",
            "financial_anomaly",
            "enforcement_history",
            "comprehensive"
        ]
        
        actual_types = [t.value for t in AnalysisType]
        
        for expected in expected_types:
            assert expected in actual_types


class TestSECDataResourcesClient:
    """Test SECDataResourcesClient methods."""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return SECDataResourcesClient(
            user_agent="Test/1.0 test@example.com",
            enable_caching=False
        )
    
    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.user_agent == "Test/1.0 test@example.com"
        assert client.enable_caching is False
    
    def test_taxonomy_constants(self, client):
        """Test taxonomy constants are defined."""
        assert client.TAXONOMY_US_GAAP == "us-gaap"
        assert client.TAXONOMY_IFRS == "ifrs-full"
        assert client.TAXONOMY_DEI == "dei"
    
    def test_concept_lists_defined(self, client):
        """Test that concept lists are properly defined."""
        assert len(client.CONCEPTS_INCOME_STATEMENT) > 0
        assert len(client.CONCEPTS_BALANCE_SHEET) > 0
        assert len(client.CONCEPTS_CASH_FLOW) > 0
        
        assert "Revenues" in client.CONCEPTS_INCOME_STATEMENT
        assert "Assets" in client.CONCEPTS_BALANCE_SHEET
        assert "NetCashProvidedByUsedInOperatingActivities" in client.CONCEPTS_CASH_FLOW
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality."""
        client = SECDataResourcesClient(
            user_agent="Test/1.0 test@example.com",
            enable_caching=False
        )
        
        async with client as c:
            assert c.session is not None
        
        # Session should be closed after exiting
        assert client.session is None or client.session.closed


class TestSECCrossAnalysisEngine:
    """Test SECCrossAnalysisEngine functionality."""
    
    @pytest.fixture
    def engine(self):
        """Create a test engine instance."""
        return SECCrossAnalysisEngine(
            user_agent="Test/1.0 test@example.com",
            enable_caching=False
        )
    
    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.user_agent == "Test/1.0 test@example.com"
        assert engine.enable_caching is False
    
    def test_generate_analysis_id(self, engine):
        """Test analysis ID generation."""
        analysis_id = engine._generate_analysis_id(
            cik="320193",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        
        assert analysis_id.startswith("XANA-")
        assert "320193" in analysis_id
        assert "20230101" in analysis_id
        assert "20231231" in analysis_id
    
    def test_categorize_filings(self, engine):
        """Test filing categorization."""
        # Create mock filings
        from src.integrations.sec_edgar import SECFiling
        
        filings = [
            SECFiling(
                accession_number="0001-24-001",
                form_type="10-K",
                filing_date=date(2024, 1, 15),
                report_date=date(2023, 12, 31),
                primary_document="doc.htm",
                file_number="001-12345",
                cik="320193",
                company_name="Test Corp",
                document_url="https://example.com/doc.htm",
                index_url="https://example.com/index.json"
            ),
            SECFiling(
                accession_number="0001-24-002",
                form_type="4",
                filing_date=date(2024, 1, 16),
                report_date=date(2024, 1, 15),
                primary_document="form4.xml",
                file_number="001-12345",
                cik="320193",
                company_name="Test Corp",
                document_url="https://example.com/form4.xml",
                index_url="https://example.com/index.json"
            ),
            SECFiling(
                accession_number="0001-24-003",
                form_type="4",
                filing_date=date(2024, 1, 17),
                report_date=date(2024, 1, 16),
                primary_document="form4.xml",
                file_number="001-12345",
                cik="320193",
                company_name="Test Corp",
                document_url="https://example.com/form4.xml",
                index_url="https://example.com/index.json"
            )
        ]
        
        categories = engine._categorize_filings(filings)
        
        assert "10-K" in categories
        assert "4" in categories
        assert len(categories["10-K"]) == 1
        assert len(categories["4"]) == 2
    
    def test_generate_summary_statistics(self, engine):
        """Test summary statistics generation."""
        data = {
            "filings": [{"form_type": "10-K"}] * 5,
            "form4_filings": [{"form_type": "4"}] * 10,
            "fails_to_deliver": [{"quantity": 1000}] * 3,
            "related_advisers": [{"name": "Test"}] * 2,
            "financial_metrics": {"Revenues": 100, "Assets": 200},
            "filings_by_type": {"10-K": [{}] * 5, "4": [{}] * 10}
        }
        
        alerts = [
            ForensicAlert(
                alert_id="A1",
                severity=AlertSeverity.HIGH,
                analysis_type=AnalysisType.INSIDER_FTD_CORRELATION,
                title="Test",
                description="Test",
                evidence=[],
                related_entities=[],
                timestamp=datetime.now(timezone.utc)
            ),
            ForensicAlert(
                alert_id="A2",
                severity=AlertSeverity.MEDIUM,
                analysis_type=AnalysisType.FINANCIAL_ANOMALY,
                title="Test",
                description="Test",
                evidence=[],
                related_entities=[],
                timestamp=datetime.now(timezone.utc)
            )
        ]
        
        stats = engine._generate_summary_statistics(data, alerts)
        
        assert stats["total_filings"] == 5
        assert stats["form4_transactions"] == 10
        assert stats["ftd_records"] == 3
        assert stats["ftd_total_quantity"] == 3000
        assert stats["total_alerts"] == 2
        assert stats["high_alerts"] == 1
        assert stats["medium_alerts"] == 1


class TestDataAcquisitionReport:
    """Test DataAcquisitionReport model."""
    
    def test_report_creation(self):
        """Test report creation and serialization."""
        report = DataAcquisitionReport(
            acquisition_id="ACQ-123-20240115120000",
            target_cik="320193",
            company_name="Apple Inc.",
            start_time=datetime(2024, 1, 15, 12, 0, 0),
            end_time=datetime(2024, 1, 15, 12, 5, 30),
            sources_queried=["company_facts_api", "submissions_api", "fails_to_deliver_data"],
            records_acquired={"filings": 50, "form4": 10, "ftd": 100},
            integrity_hashes={
                "sha256": "abc123",
                "sha3_512": "def456",
                "blake2b": "ghi789"
            },
            errors=[]
        )
        
        data = report.to_dict()
        
        assert data["acquisition_id"] == "ACQ-123-20240115120000"
        assert data["target_cik"] == "320193"
        assert data["duration_seconds"] == 330.0  # 5 min 30 sec
        assert len(data["sources_queried"]) == 3
        assert data["records_acquired"]["filings"] == 50


class TestCrossAnalysisResult:
    """Test CrossAnalysisResult model."""
    
    def test_result_creation(self):
        """Test result creation and serialization."""
        alert = ForensicAlert(
            alert_id="A1",
            severity=AlertSeverity.HIGH,
            analysis_type=AnalysisType.INSIDER_FTD_CORRELATION,
            title="Test Alert",
            description="Test description",
            evidence=[],
            related_entities=["320193"],
            timestamp=datetime.now(timezone.utc),
            confidence_score=0.8
        )
        
        report = DataAcquisitionReport(
            acquisition_id="ACQ-123",
            target_cik="320193",
            company_name="Test Corp",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            sources_queried=["test"],
            records_acquired={"test": 1},
            integrity_hashes={"sha256": "abc"},
            errors=[]
        )
        
        result = CrossAnalysisResult(
            analysis_id="XANA-123",
            target_cik="320193",
            company_name="Test Corp",
            analysis_types=[AnalysisType.COMPREHENSIVE],
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            alerts=[alert],
            acquisition_report=report,
            summary_statistics={"total_alerts": 1},
            raw_data={}
        )
        
        data = result.to_dict()
        
        assert data["analysis_id"] == "XANA-123"
        assert data["total_alerts"] == 1
        assert data["alerts_by_severity"]["high"] == 1
        assert "comprehensive" in data["analysis_types"]


# Integration test that can be run with live API (marked for skip by default)
@pytest.mark.skip(reason="Requires live SEC API access")
class TestLiveIntegration:
    """Integration tests with live SEC API."""
    
    @pytest.mark.asyncio
    async def test_get_company_facts(self):
        """Test live company facts retrieval."""
        async with SECDataResourcesClient() as client:
            facts = await client.get_company_facts("320193")  # Apple
            
            assert facts is not None
            assert "entityName" in facts
            assert "APPLE" in facts["entityName"].upper()
    
    @pytest.mark.asyncio
    async def test_get_all_company_tickers(self):
        """Test live ticker mapping retrieval."""
        async with SECDataResourcesClient() as client:
            tickers = await client.get_all_company_tickers()
            
            assert tickers is not None
            assert len(tickers) > 1000  # Should have many companies
            assert "AAPL" in tickers


# ====================================================================
# New Tests for Enhanced SEC Data Resources
# ====================================================================

class TestNewSECDataEndpoints:
    """Test new SEC data endpoint definitions."""
    
    def test_insider_transactions_endpoint(self):
        """Verify insider transactions endpoint is defined."""
        assert SECDataEndpoint.INSIDER_TRANSACTIONS is not None
        assert isinstance(SECDataEndpoint.INSIDER_TRANSACTIONS.value, str)
    
    def test_crowdfunding_offerings_endpoint(self):
        """Verify crowdfunding offerings endpoint is defined."""
        assert SECDataEndpoint.CROWDFUNDING_OFFERINGS is not None
        url = SECDataEndpoint.CROWDFUNDING_OFFERINGS.value
        assert url.startswith("https://")
        assert "crowdfund" in url.lower()
    
    def test_form_d_offerings_endpoint(self):
        """Verify Form D offerings endpoint is defined."""
        assert SECDataEndpoint.FORM_D_OFFERINGS is not None
        url = SECDataEndpoint.FORM_D_OFFERINGS.value
        assert "type=D" in url
    
    def test_sec_orders_endpoint(self):
        """Verify SEC orders endpoint is defined."""
        assert SECDataEndpoint.SEC_ORDERS is not None
        url = SECDataEndpoint.SEC_ORDERS.value
        assert url.startswith("https://")
    
    def test_broker_dealer_data_endpoint(self):
        """Verify broker-dealer data endpoint is defined."""
        assert SECDataEndpoint.BROKER_DEALER_DATA is not None
    
    def test_municipal_adviser_data_endpoint(self):
        """Verify municipal adviser data endpoint is defined."""
        assert SECDataEndpoint.MUNICIPAL_ADVISER_DATA is not None
    
    def test_edgar_company_search_endpoint(self):
        """Verify EDGAR company search endpoint supports formatting."""
        url = SECDataEndpoint.EDGAR_COMPANY_SEARCH.value.format(
            company="Apple", cik="320193", form_type="10-K"
        )
        assert "Apple" in url
        assert "320193" in url
        assert "10-K" in url


class TestNewDataModels:
    """Test new SEC data model classes."""
    
    def test_crowdfunding_offering_creation(self):
        """Test CrowdfundingOffering creation and serialization."""
        from src.integrations.sec_edgar.sec_data_resources import CrowdfundingOffering
        
        offering = CrowdfundingOffering(
            cik="123456",
            company_name="Test Startup Inc.",
            offering_amount=1000000.0,
            offering_date=date(2024, 6, 15),
            file_number="024-12345",
            state="CA",
            industry_group="Technology"
        )
        
        assert offering.company_name == "Test Startup Inc."
        assert offering.offering_amount == 1000000.0
        
        data = offering.to_dict()
        assert data["cik"] == "123456"
        assert data["offering_date"] == "2024-06-15"
        assert data["state"] == "CA"
    
    def test_crowdfunding_offering_no_date(self):
        """Test CrowdfundingOffering with no date."""
        from src.integrations.sec_edgar.sec_data_resources import CrowdfundingOffering
        
        offering = CrowdfundingOffering(
            cik="123456",
            company_name="Test Corp",
            offering_amount=None,
            offering_date=None,
            file_number=None,
            state=None,
            industry_group=None
        )
        
        data = offering.to_dict()
        assert data["offering_date"] is None
        assert data["offering_amount"] is None
    
    def test_form_d_offering_creation(self):
        """Test FormDOffering creation and serialization."""
        from src.integrations.sec_edgar.sec_data_resources import FormDOffering
        
        offering = FormDOffering(
            cik="789012",
            company_name="Private Fund LLC",
            form_type="D",
            filing_date=date(2024, 3, 1),
            offering_amount=5000000.0,
            total_amount_sold=2500000.0,
            total_remaining=2500000.0,
            accession_number="0001234567-24-000001",
            file_number="021-54321"
        )
        
        assert offering.form_type == "D"
        assert offering.offering_amount == 5000000.0
        
        data = offering.to_dict()
        assert data["filing_date"] == "2024-03-01"
        assert data["total_amount_sold"] == 2500000.0
    
    def test_insider_transaction_record_creation(self):
        """Test InsiderTransactionRecord creation and serialization."""
        from src.integrations.sec_edgar.sec_data_resources import InsiderTransactionRecord
        
        record = InsiderTransactionRecord(
            accession_number="0001234567-24-000001",
            cik="320193",
            company_name="Apple Inc.",
            insider_cik="1234567",
            insider_name="Tim Cook",
            form_type="4",
            filing_date=date(2024, 2, 15),
            transaction_date=date(2024, 2, 14),
            transaction_code="S",
            shares=50000.0,
            price_per_share=185.50,
            ownership_type="D"
        )
        
        assert record.insider_name == "Tim Cook"
        assert record.transaction_code == "S"
        assert record.shares == 50000.0
        
        data = record.to_dict()
        assert data["cik"] == "320193"
        assert data["filing_date"] == "2024-02-15"
        assert data["transaction_date"] == "2024-02-14"
        assert data["ownership_type"] == "D"
    
    def test_insider_transaction_no_transaction_date(self):
        """Test InsiderTransactionRecord with no transaction date."""
        from src.integrations.sec_edgar.sec_data_resources import InsiderTransactionRecord
        
        record = InsiderTransactionRecord(
            accession_number="0001234567-24-000001",
            cik="320193",
            company_name="Test Corp",
            insider_cik="",
            insider_name="",
            form_type="3",
            filing_date=date(2024, 1, 1),
            transaction_date=None,
            transaction_code=None,
            shares=None,
            price_per_share=None,
            ownership_type="D"
        )
        
        data = record.to_dict()
        assert data["transaction_date"] is None
        assert data["shares"] is None


class TestSECConfigurationValidation:
    """Test enhanced SEC configuration validation."""
    
    def test_validate_sec_config_rate_limit(self):
        """Test SEC rate limit validation."""
        import os
        from config.secure_config import validate_sec_configuration
        
        # Valid rate limit
        os.environ['SEC_USER_AGENT'] = "TestCo/1.0 test@example.com"
        os.environ['SEC_RATE_LIMIT'] = "6.0"
        is_valid, errors = validate_sec_configuration()
        rate_errors = [e for e in errors if 'SEC_RATE_LIMIT' in e]
        assert len(rate_errors) == 0
        
        # Cleanup
        del os.environ['SEC_USER_AGENT']
        del os.environ['SEC_RATE_LIMIT']
    
    def test_validate_sec_config_invalid_rate_limit(self):
        """Test that invalid rate limit generates error."""
        import os
        from config.secure_config import validate_sec_configuration
        
        os.environ['SEC_USER_AGENT'] = "TestCo/1.0 test@example.com"
        os.environ['SEC_RATE_LIMIT'] = "15.0"
        is_valid, errors = validate_sec_configuration()
        rate_errors = [e for e in errors if 'SEC_RATE_LIMIT' in e]
        assert len(rate_errors) == 1
        
        # Cleanup
        del os.environ['SEC_USER_AGENT']
        del os.environ['SEC_RATE_LIMIT']
    
    def test_validate_sec_config_invalid_retries(self):
        """Test that invalid max retries generates error."""
        import os
        from config.secure_config import validate_sec_configuration
        
        os.environ['SEC_USER_AGENT'] = "TestCo/1.0 test@example.com"
        os.environ['SEC_MAX_RETRIES'] = "abc"
        is_valid, errors = validate_sec_configuration()
        retry_errors = [e for e in errors if 'SEC_MAX_RETRIES' in e]
        assert len(retry_errors) == 1
        
        # Cleanup
        del os.environ['SEC_USER_AGENT']
        del os.environ['SEC_MAX_RETRIES']
    
    def test_validate_sec_config_invalid_retry_strategy(self):
        """Test that invalid retry strategy generates error."""
        import os
        from config.secure_config import validate_sec_configuration
        
        os.environ['SEC_USER_AGENT'] = "TestCo/1.0 test@example.com"
        os.environ['SEC_RETRY_STRATEGY'] = "random"
        is_valid, errors = validate_sec_configuration()
        strategy_errors = [e for e in errors if 'SEC_RETRY_STRATEGY' in e]
        assert len(strategy_errors) == 1
        
        # Cleanup
        del os.environ['SEC_USER_AGENT']
        del os.environ['SEC_RETRY_STRATEGY']
    
    def test_validate_sec_config_valid_complete(self):
        """Test that valid configuration passes validation."""
        import os
        from config.secure_config import validate_sec_configuration
        
        os.environ['SEC_USER_AGENT'] = "TestCo/1.0 test@example.com"
        os.environ['SEC_RATE_LIMIT'] = "6.0"
        os.environ['SEC_MAX_RETRIES'] = "5"
        os.environ['SEC_RETRY_STRATEGY'] = "exponential"
        
        is_valid, errors = validate_sec_configuration()
        assert is_valid is True
        assert len(errors) == 0
        
        # Cleanup
        for key in ['SEC_USER_AGENT', 'SEC_RATE_LIMIT', 'SEC_MAX_RETRIES', 'SEC_RETRY_STRATEGY']:
            if key in os.environ:
                del os.environ[key]


class TestSECDataResourcesClientNewMethods:
    """Test new methods on SECDataResourcesClient."""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return SECDataResourcesClient(
            user_agent="Test/1.0 test@example.com",
            enable_caching=False
        )
    
    @pytest.mark.asyncio
    async def test_get_insider_transactions_returns_list(self, client):
        """Test that get_insider_transactions returns a list."""
        # Without live API, test that method exists and returns correct type
        with patch.object(client, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "name": "Test Corp",
                "filings": {
                    "recent": {
                        "form": ["4", "10-K", "4", "3"],
                        "filingDate": ["2024-01-15", "2024-01-20", "2024-02-01", "2024-03-01"],
                        "accessionNumber": ["001-24-001", "001-24-002", "001-24-003", "001-24-004"],
                        "primaryDocument": ["doc1.xml", "doc2.htm", "doc3.xml", "doc4.xml"]
                    }
                }
            }
            
            records = await client.get_insider_transactions(
                "320193",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31)
            )
            
            assert isinstance(records, list)
            assert len(records) == 3  # 2 Form 4s + 1 Form 3
            assert records[0].form_type == "4"
            assert records[2].form_type == "3"
    
    @pytest.mark.asyncio
    async def test_get_form_d_filings_by_cik(self, client):
        """Test Form D filings retrieval by CIK."""
        with patch.object(client, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "name": "Private Fund LLC",
                "filings": {
                    "recent": {
                        "form": ["D", "10-K", "D/A", "SC 13D"],
                        "filingDate": ["2024-02-01", "2024-03-01", "2024-04-01", "2024-05-01"],
                        "accessionNumber": ["001-24-001", "001-24-002", "001-24-003", "001-24-004"],
                        "primaryDocument": ["d1.htm", "d2.htm", "d3.htm", "d4.htm"]
                    }
                }
            }
            
            filings = await client.get_form_d_filings(
                cik="789012",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31)
            )
            
            assert isinstance(filings, list)
            assert len(filings) == 2  # D and D/A only
            assert filings[0].form_type == "D"
            assert filings[1].form_type == "D/A"
    
    @pytest.mark.asyncio
    async def test_get_crowdfunding_offerings_empty(self, client):
        """Test crowdfunding offerings with no data."""
        with patch.object(client, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            
            offerings = await client.get_crowdfunding_offerings()
            assert offerings == []
    
    @pytest.mark.asyncio
    async def test_search_companies(self, client):
        """Test EDGAR company search."""
        with patch.object(client, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = """
            <feed>
                <entry>
                    <title>10-K - APPLE INC (0000320193)</title>
                    <link href="https://www.sec.gov/Archives/edgar/data/320193/test"/>
                    <updated>2024-01-15T10:00:00Z</updated>
                    <summary>Annual Report</summary>
                </entry>
            </feed>
            """
            
            results = await client.search_companies(company="Apple")
            assert isinstance(results, list)
            assert len(results) == 1
            assert "APPLE" in results[0]["title"]


class TestCrossAnalysisEngineSummaryStats:
    """Test updated summary statistics with new data sources."""
    
    def test_summary_includes_new_sources(self):
        """Test that summary statistics include insider transactions and Form D."""
        engine = SECCrossAnalysisEngine(
            user_agent="Test/1.0 test@example.com",
            enable_caching=False
        )
        
        data = {
            "filings": [{"form_type": "10-K"}] * 5,
            "form4_filings": [{"form_type": "4"}] * 10,
            "fails_to_deliver": [{"quantity": 1000}] * 3,
            "related_advisers": [{"name": "Test"}] * 2,
            "financial_metrics": {"Revenues": 100},
            "filings_by_type": {"10-K": [{}] * 5},
            "insider_transactions": [{"form_type": "4"}] * 7,
            "form_d_filings": [{"form_type": "D"}] * 2
        }
        
        alerts = []
        stats = engine._generate_summary_statistics(data, alerts)
        
        assert stats["insider_transactions"] == 7
        assert stats["form_d_filings"] == 2
        assert stats["total_filings"] == 5
        assert stats["form4_transactions"] == 10
