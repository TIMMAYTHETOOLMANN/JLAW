"""
Test Suite for JLAW Final System Integration Patch v4.1.1
==========================================================

Comprehensive validation of Nodes 13-15 and Linear Orchestrator.

Tests:
- Node 13: Z-Score calculation, classification, forensic hashing
- Node 14: F-Score signals, category subscores, accruals quality
- Node 15: Volume profiles, anomaly detection, market correlation
- Orchestrator: Phase execution, dependency ordering, evidence chain
- Integration: Module imports, serialization, cryptographic verification
"""

import pytest
from datetime import datetime, date, timedelta
import json
import hashlib

# Node 13: Z-Score imports
from src.nodes.node13_zscore import (
    ZScoreClassification,
    ZScoreModel,
    ZScoreInput,
    ZScoreResult,
    AltmanZScoreEngine
)

# Node 14: F-Score imports
from src.nodes.node14_fscore import (
    FScoreClassification,
    SignalCategory,
    FiscalPeriodData,
    FScoreSignal,
    FScoreResult,
    PiotroskiFScoreEngine
)

# Node 15: Market Correlation imports
from src.nodes.node15_market_correlation import (
    AnomalyType,
    SeverityLevel,
    OHLCVBar,
    VolumeProfile,
    MarketAnomaly,
    CorrelationResult,
    PolygonClient,
    MarketCorrelationEngine
)

# Linear Orchestrator imports
from src.core.linear_orchestrator import (
    ExecutionPhase,
    NodeStatus,
    NodeExecutionResult,
    PhaseResult,
    ForensicAnalysisResult,
    LinearExecutionOrchestrator
)


# ============================================================================
# NODE 13: ALTMAN Z-SCORE TESTS
# ============================================================================

class TestNode13ZScore:
    """Test suite for Node 13: Altman Z-Score Engine."""
    
    def test_zscore_enums(self):
        """Test Z-Score enum definitions."""
        assert ZScoreClassification.SAFE.value == "Safe Zone"
        assert ZScoreClassification.GRAY.value == "Gray Zone"
        assert ZScoreClassification.DISTRESS.value == "Distress Zone"
        
        assert ZScoreModel.ORIGINAL.value == "Original"
        assert ZScoreModel.PRIVATE.value == "Private"
        assert ZScoreModel.NON_MANUFACTURING.value == "Non-Manufacturing"
    
    def test_zscore_input_validation(self):
        """Test Z-Score input validation."""
        # Valid input
        input_data = ZScoreInput(
            cik="0000320193",
            company_name="Apple Inc.",
            fiscal_year=2023,
            fiscal_period="FY",
            current_assets=100000000,
            current_liabilities=50000000,
            total_assets=200000000,
            total_liabilities=80000000,
            retained_earnings=60000000,
            ebit=40000000,
            sales=300000000,
            net_income=35000000,
            market_value_equity=150000000
        )
        assert input_data.total_assets == 200000000
        
        # Invalid input (negative total assets)
        with pytest.raises(ValueError):
            ZScoreInput(
                cik="0000320193",
                company_name="Test",
                fiscal_year=2023,
                fiscal_period="FY",
                current_assets=100000000,
                current_liabilities=50000000,
                total_assets=-200000000,  # Invalid
                total_liabilities=80000000,
                retained_earnings=60000000,
                ebit=40000000,
                sales=300000000,
                net_income=35000000,
                market_value_equity=150000000
            )
    
    def test_zscore_calculation_original(self):
        """Test Z-Score calculation with Original model."""
        engine = AltmanZScoreEngine()
        
        input_data = ZScoreInput(
            cik="0000320193",
            company_name="Apple Inc.",
            fiscal_year=2023,
            fiscal_period="FY",
            current_assets=100000000,
            current_liabilities=50000000,
            total_assets=200000000,
            total_liabilities=80000000,
            retained_earnings=60000000,
            ebit=40000000,
            sales=300000000,
            net_income=35000000,
            market_value_equity=150000000
        )
        
        result = engine.calculate(input_data, ZScoreModel.ORIGINAL)
        
        # Verify result structure
        assert isinstance(result, ZScoreResult)
        assert result.model == ZScoreModel.ORIGINAL
        assert result.z_score > 0
        assert result.classification in [ZScoreClassification.SAFE, ZScoreClassification.GRAY, ZScoreClassification.DISTRESS]
        
        # Verify component ratios
        assert result.x1_working_capital_to_ta == 0.25  # (100M - 50M) / 200M
        assert result.x2_retained_earnings_to_ta == 0.30  # 60M / 200M
        assert result.x3_ebit_to_ta == 0.20  # 40M / 200M
        assert result.x5_sales_to_ta == 1.50  # 300M / 200M
    
    def test_zscore_classification(self):
        """Test Z-Score classification zones."""
        engine = AltmanZScoreEngine()
        
        # Create inputs that should yield different classifications
        # Safe Zone (Z > 2.99)
        safe_input = ZScoreInput(
            cik="0000320193",
            company_name="Safe Company",
            fiscal_year=2023,
            fiscal_period="FY",
            current_assets=150000000,
            current_liabilities=50000000,
            total_assets=200000000,
            total_liabilities=60000000,
            retained_earnings=80000000,
            ebit=50000000,
            sales=400000000,
            net_income=45000000,
            market_value_equity=200000000
        )
        
        safe_result = engine.calculate(safe_input, ZScoreModel.ORIGINAL)
        assert safe_result.classification == ZScoreClassification.SAFE
        assert safe_result.z_score > 2.99
    
    def test_zscore_forensic_hashing(self):
        """Test Z-Score evidence hashing (SHA-256)."""
        engine = AltmanZScoreEngine()
        
        input_data = ZScoreInput(
            cik="0000320193",
            company_name="Test",
            fiscal_year=2023,
            fiscal_period="FY",
            current_assets=100000000,
            current_liabilities=50000000,
            total_assets=200000000,
            total_liabilities=80000000,
            retained_earnings=60000000,
            ebit=40000000,
            sales=300000000,
            net_income=35000000,
            market_value_equity=150000000
        )
        
        result = engine.calculate(input_data)
        
        # Verify hash format
        assert len(result.evidence_hash_sha256) == 64  # SHA-256 produces 64 hex chars
        assert all(c in '0123456789abcdef' for c in result.evidence_hash_sha256)
    
    def test_zscore_serialization(self):
        """Test Z-Score result serialization."""
        engine = AltmanZScoreEngine()
        
        input_data = ZScoreInput(
            cik="0000320193",
            company_name="Test",
            fiscal_year=2023,
            fiscal_period="FY",
            current_assets=100000000,
            current_liabilities=50000000,
            total_assets=200000000,
            total_liabilities=80000000,
            retained_earnings=60000000,
            ebit=40000000,
            sales=300000000,
            net_income=35000000,
            market_value_equity=150000000
        )
        
        result = engine.calculate(input_data)
        result_dict = result.to_dict()
        
        # Verify serialization
        assert isinstance(result_dict, dict)
        assert "z_score" in result_dict
        assert "classification" in result_dict
        assert "forensic_metadata" in result_dict
        
        # Verify JSON serialization
        json_str = json.dumps(result_dict)
        assert len(json_str) > 0


# ============================================================================
# NODE 14: PIOTROSKI F-SCORE TESTS
# ============================================================================

class TestNode14FScore:
    """Test suite for Node 14: Piotroski F-Score Engine."""
    
    def test_fscore_enums(self):
        """Test F-Score enum definitions."""
        assert FScoreClassification.STRONG.value == "Strong"
        assert FScoreClassification.MODERATE.value == "Moderate"
        assert FScoreClassification.WEAK.value == "Weak"
        
        assert SignalCategory.PROFITABILITY.value == "Profitability"
        assert SignalCategory.LEVERAGE_LIQUIDITY.value == "Leverage/Liquidity"
        assert SignalCategory.OPERATING_EFFICIENCY.value == "Operating Efficiency"
    
    def test_fscore_period_data_validation(self):
        """Test fiscal period data validation."""
        # Valid data
        period = FiscalPeriodData(
            fiscal_year=2023,
            fiscal_period="FY",
            net_income=50000000,
            revenue=500000000,
            cost_of_goods_sold=300000000,
            total_assets=1000000000,
            current_assets=400000000,
            current_liabilities=200000000,
            long_term_debt=300000000,
            cash_flow_from_operations=60000000,
            shares_outstanding=100000000
        )
        assert period.total_assets == 1000000000
        
        # Invalid data (negative total assets)
        with pytest.raises(ValueError):
            FiscalPeriodData(
                fiscal_year=2023,
                fiscal_period="FY",
                net_income=50000000,
                revenue=500000000,
                cost_of_goods_sold=300000000,
                total_assets=-1000000000,  # Invalid
                current_assets=400000000,
                current_liabilities=200000000,
                long_term_debt=300000000,
                cash_flow_from_operations=60000000,
                shares_outstanding=100000000
            )
    
    def test_fscore_calculation(self):
        """Test F-Score calculation with all 9 signals."""
        engine = PiotroskiFScoreEngine()
        
        # Create current period data (strong fundamentals)
        current = FiscalPeriodData(
            fiscal_year=2023,
            fiscal_period="FY",
            net_income=50000000,  # Positive
            revenue=500000000,
            cost_of_goods_sold=250000000,  # 50% gross margin
            total_assets=1000000000,
            current_assets=450000000,  # Increasing liquidity
            current_liabilities=200000000,
            long_term_debt=250000000,  # Decreasing debt
            cash_flow_from_operations=60000000,  # Positive, > NI
            shares_outstanding=100000000  # No dilution
        )
        
        # Create prior period data
        prior = FiscalPeriodData(
            fiscal_year=2022,
            fiscal_period="FY",
            net_income=40000000,  # Lower than current (improving)
            revenue=450000000,
            cost_of_goods_sold=240000000,  # 46.7% gross margin (improving)
            total_assets=950000000,
            current_assets=400000000,
            current_liabilities=200000000,
            long_term_debt=300000000,  # Higher than current (improving)
            cash_flow_from_operations=50000000,
            shares_outstanding=100000000
        )
        
        result = engine.calculate("0000320193", "Test Company", current, prior)
        
        # Verify result structure
        assert isinstance(result, FScoreResult)
        assert len(result.signals) == 9
        assert 0 <= result.f_score <= 9
        assert result.classification in [FScoreClassification.STRONG, FScoreClassification.MODERATE, FScoreClassification.WEAK]
        
        # Verify signal categories
        profitability_signals = [s for s in result.signals if s.category == SignalCategory.PROFITABILITY]
        assert len(profitability_signals) == 4  # F1-F4
        
        leverage_signals = [s for s in result.signals if s.category == SignalCategory.LEVERAGE_LIQUIDITY]
        assert len(leverage_signals) == 3  # F5-F7
        
        efficiency_signals = [s for s in result.signals if s.category == SignalCategory.OPERATING_EFFICIENCY]
        assert len(efficiency_signals) == 2  # F8-F9
    
    def test_fscore_signal_details(self):
        """Test individual F-Score signal calculations."""
        engine = PiotroskiFScoreEngine()
        
        current = FiscalPeriodData(
            fiscal_year=2023,
            fiscal_period="FY",
            net_income=50000000,
            revenue=500000000,
            cost_of_goods_sold=300000000,
            total_assets=1000000000,
            current_assets=400000000,
            current_liabilities=200000000,
            long_term_debt=300000000,
            cash_flow_from_operations=60000000,
            shares_outstanding=100000000
        )
        
        prior = FiscalPeriodData(
            fiscal_year=2022,
            fiscal_period="FY",
            net_income=40000000,
            revenue=450000000,
            cost_of_goods_sold=270000000,
            total_assets=950000000,
            current_assets=380000000,
            current_liabilities=200000000,
            long_term_debt=300000000,
            cash_flow_from_operations=45000000,
            shares_outstanding=100000000
        )
        
        result = engine.calculate("0000320193", "Test", current, prior)
        
        # Verify specific signals
        f1 = next(s for s in result.signals if s.signal_id == "F1")
        assert f1.value == 1  # Positive ROA
        
        f2 = next(s for s in result.signals if s.signal_id == "F2")
        assert f2.value == 1  # Positive CFO
        
        f4 = next(s for s in result.signals if s.signal_id == "F4")
        assert f4.value == 1  # CFO > NI (accruals quality)
    
    def test_fscore_accruals_quality(self):
        """Test accruals quality detection."""
        engine = PiotroskiFScoreEngine()
        
        # Good accruals (CFO > NI)
        current_good = FiscalPeriodData(
            fiscal_year=2023,
            fiscal_period="FY",
            net_income=50000000,
            revenue=500000000,
            cost_of_goods_sold=300000000,
            total_assets=1000000000,
            current_assets=400000000,
            current_liabilities=200000000,
            long_term_debt=300000000,
            cash_flow_from_operations=60000000,  # > NI
            shares_outstanding=100000000
        )
        
        prior = FiscalPeriodData(
            fiscal_year=2022,
            fiscal_period="FY",
            net_income=40000000,
            revenue=450000000,
            cost_of_goods_sold=270000000,
            total_assets=950000000,
            current_assets=380000000,
            current_liabilities=200000000,
            long_term_debt=300000000,
            cash_flow_from_operations=45000000,
            shares_outstanding=100000000
        )
        
        result = engine.calculate("0000320193", "Test", current_good, prior)
        assert result.accruals_quality == "Good"


# ============================================================================
# NODE 15: MARKET CORRELATION TESTS
# ============================================================================

class TestNode15MarketCorrelation:
    """Test suite for Node 15: Market Correlation Engine."""
    
    def test_anomaly_enums(self):
        """Test market anomaly enum definitions."""
        assert AnomalyType.VOLUME_SPIKE.value == "Volume Spike"
        assert AnomalyType.PRICE_MOVEMENT.value == "Price Movement"
        assert AnomalyType.PRE_ANNOUNCEMENT.value == "Pre-Announcement Trading"
        
        assert SeverityLevel.LOW.value == "Low"
        assert SeverityLevel.MODERATE.value == "Moderate"
        assert SeverityLevel.HIGH.value == "High"
        assert SeverityLevel.CRITICAL.value == "Critical"
    
    def test_ohlcv_bar_calculations(self):
        """Test OHLCV bar calculated properties."""
        bar = OHLCVBar(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        assert bar.price_change == 3.0  # 103 - 100
        assert bar.price_change_percent == 3.0  # (3/100) * 100
    
    def test_volume_profile_anomaly_detection(self):
        """Test volume profile Z-score anomaly detection."""
        # Normal volume
        normal_profile = VolumeProfile(
            symbol="AAPL",
            date=date(2023, 1, 1),
            current_volume=1000000,
            mean_volume=1000000,
            std_volume=100000
        )
        assert normal_profile.z_score == 0.0
        assert normal_profile.is_anomalous is False
        
        # Anomalous volume (Z > 2.5)
        anomaly_profile = VolumeProfile(
            symbol="AAPL",
            date=date(2023, 1, 2),
            current_volume=1300000,
            mean_volume=1000000,
            std_volume=100000
        )
        assert anomaly_profile.z_score == 3.0  # (1.3M - 1M) / 100k
        assert anomaly_profile.is_anomalous is True
    
    def test_polygon_client_mock_mode(self):
        """Test Polygon client in mock mode."""
        client = PolygonClient()  # No API key = mock mode
        assert client.mock_mode is True
        
        # Get mock data
        bars = client.get_aggregates(
            symbol="AAPL",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 5)
        )
        
        assert len(bars) > 0
        assert all(isinstance(bar, OHLCVBar) for bar in bars)
    
    def test_market_correlation_engine(self):
        """Test market correlation engine analysis."""
        engine = MarketCorrelationEngine()  # No API key = mock mode
        
        result = engine.analyze(
            symbol="AAPL",
            cik="0000320193",
            company_name="Apple Inc.",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31)
        )
        
        assert isinstance(result, CorrelationResult)
        assert result.symbol == "AAPL"
        assert result.bars_analyzed > 0
        assert isinstance(result.anomalies, list)
    
    def test_market_anomaly_hashing(self):
        """Test market anomaly forensic hashing."""
        anomaly = MarketAnomaly(
            anomaly_type=AnomalyType.VOLUME_SPIKE,
            severity=SeverityLevel.HIGH,
            symbol="AAPL",
            detection_date=date(2023, 1, 1),
            description="Test anomaly",
            metrics={"z_score": 3.5}
        )
        
        # Verify hash generation
        assert len(anomaly.evidence_hash_sha256) == 64
        assert all(c in '0123456789abcdef' for c in anomaly.evidence_hash_sha256)


# ============================================================================
# LINEAR ORCHESTRATOR TESTS
# ============================================================================

class TestLinearOrchestrator:
    """Test suite for Linear Execution Orchestrator."""
    
    def test_execution_phase_enum(self):
        """Test execution phase enum."""
        assert ExecutionPhase.PHASE_1.value == 1
        assert ExecutionPhase.PHASE_2.value == 2
        assert ExecutionPhase.PHASE_3.value == 3
        assert ExecutionPhase.PHASE_4.value == 4
    
    def test_node_status_enum(self):
        """Test node status enum."""
        assert NodeStatus.PENDING.value == "Pending"
        assert NodeStatus.RUNNING.value == "Running"
        assert NodeStatus.COMPLETED.value == "Completed"
        assert NodeStatus.FAILED.value == "Failed"
        assert NodeStatus.SKIPPED.value == "Skipped"
    
    def test_node_config_dependencies(self):
        """Test node configuration and dependencies."""
        config = LinearExecutionOrchestrator.NODE_CONFIG
        
        # Verify all 15 nodes are configured
        assert len(config) == 15
        
        # Verify dependency structure
        assert config[1]["deps"] == []  # Node 1 has no dependencies
        assert config[5]["deps"] == [1, 2]  # Node 5 depends on 1 and 2
        assert config[15]["deps"] == [1, 9]  # Node 15 depends on 1 and 9
        
        # Verify phase assignments
        assert config[1]["phase"] == 1  # Phase 1
        assert config[7]["phase"] == 2  # Phase 2
        assert config[13]["phase"] == 3  # Phase 3
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = LinearExecutionOrchestrator(
            sec_user_agent="Test/1.0",
            polygon_api_key=None
        )
        
        assert orchestrator.sec_user_agent == "Test/1.0"
        assert orchestrator.polygon_api_key is None
        assert len(orchestrator.node_results) == 0
    
    @pytest.mark.asyncio
    async def test_orchestrator_execution(self):
        """Test complete orchestrator execution."""
        orchestrator = LinearExecutionOrchestrator(
            sec_user_agent="Test/1.0",
            polygon_api_key=None
        )
        
        result = await orchestrator.execute_analysis(
            company_cik="0000320193",
            company_name="Apple Inc.",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        
        # Verify result structure
        assert isinstance(result, ForensicAnalysisResult)
        assert result.company_cik == "0000320193"
        assert result.total_nodes_executed == 16  # 15 nodes + 1 Phase 4 correlation node
        
        # Verify phases executed
        assert result.phase_1_result.phase == ExecutionPhase.PHASE_1
        assert result.phase_2_result.phase == ExecutionPhase.PHASE_2
        assert result.phase_3_result.phase == ExecutionPhase.PHASE_3
        assert result.phase_4_result.phase == ExecutionPhase.PHASE_4
    
    def test_triple_hash_evidence_chain(self):
        """Test triple-hash evidence chain generation."""
        # Create mock phase results
        phase_1 = PhaseResult(
            phase=ExecutionPhase.PHASE_1,
            phase_name="Test Phase 1",
            nodes_executed=[]
        )
        phase_2 = PhaseResult(
            phase=ExecutionPhase.PHASE_2,
            phase_name="Test Phase 2",
            nodes_executed=[]
        )
        phase_3 = PhaseResult(
            phase=ExecutionPhase.PHASE_3,
            phase_name="Test Phase 3",
            nodes_executed=[]
        )
        phase_4 = PhaseResult(
            phase=ExecutionPhase.PHASE_4,
            phase_name="Test Phase 4",
            nodes_executed=[]
        )
        
        result = ForensicAnalysisResult(
            case_id="TEST-001",
            company_cik="0000320193",
            company_name="Test",
            analysis_period="2023",
            execution_start=datetime.utcnow(),
            execution_end=datetime.utcnow(),
            total_execution_seconds=10.0,
            phase_1_result=phase_1,
            phase_2_result=phase_2,
            phase_3_result=phase_3,
            phase_4_result=phase_4
        )
        
        # Verify triple-hash
        assert len(result.evidence_chain_sha256) == 64  # SHA-256
        assert len(result.evidence_chain_sha3_512) == 128  # SHA3-512
        assert len(result.evidence_chain_blake2b) == 128  # BLAKE2b
        
        # Verify hashes are different
        assert result.evidence_chain_sha256 != result.evidence_chain_sha3_512
        assert result.evidence_chain_sha256 != result.evidence_chain_blake2b
    
    def test_forensic_result_serialization(self):
        """Test forensic analysis result JSON serialization."""
        # Create mock phase results
        phase_1 = PhaseResult(
            phase=ExecutionPhase.PHASE_1,
            phase_name="Test Phase 1",
            nodes_executed=[]
        )
        phase_2 = PhaseResult(
            phase=ExecutionPhase.PHASE_2,
            phase_name="Test Phase 2",
            nodes_executed=[]
        )
        phase_3 = PhaseResult(
            phase=ExecutionPhase.PHASE_3,
            phase_name="Test Phase 3",
            nodes_executed=[]
        )
        phase_4 = PhaseResult(
            phase=ExecutionPhase.PHASE_4,
            phase_name="Test Phase 4",
            nodes_executed=[]
        )
        
        result = ForensicAnalysisResult(
            case_id="TEST-001",
            company_cik="0000320193",
            company_name="Test",
            analysis_period="2023",
            execution_start=datetime.utcnow(),
            execution_end=datetime.utcnow(),
            total_execution_seconds=10.0,
            phase_1_result=phase_1,
            phase_2_result=phase_2,
            phase_3_result=phase_3,
            phase_4_result=phase_4
        )
        
        result_dict = result.to_dict()
        
        # Verify serialization
        assert isinstance(result_dict, dict)
        assert "case_identification" in result_dict
        assert "execution_summary" in result_dict
        assert "findings_summary" in result_dict
        assert "forensic_evidence_chain" in result_dict
        
        # Verify JSON serialization
        json_str = json.dumps(result_dict)
        assert len(json_str) > 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for complete system."""
    
    def test_all_modules_import(self):
        """Test that all modules import successfully."""
        # Already imported at top of file
        # If we got here, all imports succeeded
        assert True
    
    def test_node13_v2_compatibility(self):
        """Test backward compatibility with existing Node 13 v2 implementation."""
        from src.nodes.node13_zscore import BankruptcyPredictorV2, Node13OutputV2
        
        predictor = BankruptcyPredictorV2()
        assert predictor is not None
    
    def test_node14_v2_compatibility(self):
        """Test backward compatibility with existing Node 14 v2 implementation."""
        from src.nodes.node14_fscore import FinancialStrengthAnalyzerV2, Node14OutputV2
        
        analyzer = FinancialStrengthAnalyzerV2()
        assert analyzer is not None
    
    def test_node15_v2_compatibility(self):
        """Test backward compatibility with existing Node 15 v2 implementation."""
        from src.nodes.node15_market_correlation import MarketCorrelationEngineV2, Node15OutputV2
        
        engine = MarketCorrelationEngineV2()
        assert engine is not None
    
    def test_cryptographic_functions_available(self):
        """Test that cryptographic functions are available."""
        import hashlib
        
        # Test SHA-256
        hash_sha256 = hashlib.sha256(b"test").hexdigest()
        assert len(hash_sha256) == 64
        
        # Test SHA3-512
        hash_sha3 = hashlib.sha3_512(b"test").hexdigest()
        assert len(hash_sha3) == 128
        
        # Test BLAKE2b
        hash_blake2b = hashlib.blake2b(b"test").hexdigest()
        assert len(hash_blake2b) == 128


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
