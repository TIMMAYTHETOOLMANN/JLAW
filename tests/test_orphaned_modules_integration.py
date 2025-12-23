"""
Test Orphaned Modules Integration
==================================

Validates that previously orphaned modules are now properly integrated
into their V2 parent implementations.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestNode13Integration:
    """Test Node 13 Z-Score bankruptcy predictor integration."""
    
    def test_ensemble_predictor_integration(self):
        """Verify ensemble_predictor is imported and used in V2."""
        from src.nodes.node13_zscore.bankruptcy_predictor_v2 import (
            BankruptcyPredictorV2,
            ENSEMBLE_AVAILABLE
        )
        
        # Should be available (we have the module)
        assert ENSEMBLE_AVAILABLE is True
        
        # Should initialize with ensemble
        predictor = BankruptcyPredictorV2(use_ensemble=True)
        assert predictor.ensemble_predictor is not None
    
    def test_industry_calibration_integration(self):
        """Verify industry_calibration is imported and used in V2."""
        from src.nodes.node13_zscore.bankruptcy_predictor_v2 import (
            BankruptcyPredictorV2,
            INDUSTRY_CALIBRATION_AVAILABLE
        )
        
        assert INDUSTRY_CALIBRATION_AVAILABLE is True
        
        predictor = BankruptcyPredictorV2(use_industry_calibration=True)
        assert predictor.industry_calculator is not None
    
    def test_zscore_validator_integration(self):
        """Verify zscore_validator is imported and used in V2."""
        from src.nodes.node13_zscore.bankruptcy_predictor_v2 import (
            BankruptcyPredictorV2,
            VALIDATOR_AVAILABLE
        )
        
        assert VALIDATOR_AVAILABLE is True
        
        predictor = BankruptcyPredictorV2()
        assert predictor.validator is not None
    
    def test_analyze_with_enhanced_features(self):
        """Test analyze method uses enhanced features."""
        from src.nodes.node13_zscore.bankruptcy_predictor_v2 import BankruptcyPredictorV2
        
        predictor = BankruptcyPredictorV2(
            use_ensemble=True,
            use_industry_calibration=True
        )
        
        # Test with minimal data
        companies = [
            {
                'cik': '0000320187',
                'name': 'Test Company',
                'z_score': 1.5,
                'f_score': 3,
                'sic_code': '2834',
                'market_signals': {
                    'volume_anomaly': False,
                    'price_decline_30d': -5.0
                },
                'financial_data': {
                    'working_capital': 1000000,
                    'retained_earnings': 500000,
                    'ebit': 200000,
                    'market_value_equity': 5000000,
                    'total_assets': 10000000,
                    'sales': 8000000,
                    'total_liabilities': 4000000
                }
            }
        ]
        
        result = predictor.analyze(companies)
        
        # Should process company
        assert result.companies_analyzed == 1
        # Should detect distress zone (z_score < 1.81)
        assert result.distress_zone_count >= 1
        # Should have alerts
        assert len(result.alerts) > 0


class TestNode14Integration:
    """Test Node 14 F-Score financial strength analyzer integration."""
    
    def test_piotroski_validator_integration(self):
        """Verify piotroski_validator is imported and used in V2."""
        from src.nodes.node14_fscore.financial_strength_analyzer_v2 import (
            FinancialStrengthAnalyzerV2,
            VALIDATOR_AVAILABLE
        )
        
        assert VALIDATOR_AVAILABLE is True
        
        analyzer = FinancialStrengthAnalyzerV2(use_validator=True)
        assert analyzer.validator is not None
    
    def test_sector_relative_fscore_integration(self):
        """Verify sector_relative_fscore is imported and used in V2."""
        from src.nodes.node14_fscore.financial_strength_analyzer_v2 import (
            FinancialStrengthAnalyzerV2,
            SECTOR_RELATIVE_AVAILABLE
        )
        
        assert SECTOR_RELATIVE_AVAILABLE is True
        
        analyzer = FinancialStrengthAnalyzerV2(use_sector_relative=True)
        assert analyzer.sector_calculator is not None
    
    def test_analyze_with_sector_relative(self):
        """Test analyze method uses sector-relative features."""
        from src.nodes.node14_fscore.financial_strength_analyzer_v2 import (
            FinancialStrengthAnalyzerV2
        )
        
        analyzer = FinancialStrengthAnalyzerV2(use_sector_relative=True)
        
        companies = [
            {
                'cik': '0000320187',
                'name': 'Test Company',
                'f_score': 8,
                'sector': 'Information Technology'
            }
        ]
        
        sector_fscores = {
            'Information Technology': [5, 6, 7, 7, 8, 8, 9]
        }
        
        result = analyzer.analyze(companies, sector_fscores=sector_fscores)
        
        assert result.companies_analyzed == 1
        assert result.strong_health_count >= 1


class TestNode15Integration:
    """Test Node 15 market correlation engine integration."""
    
    def test_cross_security_correlator_integration(self):
        """Verify cross_security_correlator is imported and used in V2."""
        from src.nodes.node15_market_correlation.market_correlation_engine_v2 import (
            MarketCorrelationEngineV2,
            CORRELATOR_AVAILABLE
        )
        
        assert CORRELATOR_AVAILABLE is True
        
        engine = MarketCorrelationEngineV2(use_cross_security=True)
        assert engine.cross_correlator is not None
    
    def test_intraday_event_analyzer_integration(self):
        """Verify intraday_event_analyzer is imported and used in V2."""
        from src.nodes.node15_market_correlation.market_correlation_engine_v2 import (
            MarketCorrelationEngineV2,
            INTRADAY_ANALYZER_AVAILABLE
        )
        
        assert INTRADAY_ANALYZER_AVAILABLE is True
        
        engine = MarketCorrelationEngineV2(use_intraday=True)
        assert engine.intraday_analyzer is not None
    
    def test_analyze_with_cross_security(self):
        """Test analyze method uses cross-security correlation."""
        from src.nodes.node15_market_correlation.market_correlation_engine_v2 import (
            MarketCorrelationEngineV2
        )
        from datetime import datetime
        
        engine = MarketCorrelationEngineV2(
            use_cross_security=True,
            use_intraday=True
        )
        
        market_data = [
            {'symbol': 'AAPL', 'volume_ratio': 2.5}
        ]
        
        securities_returns = {
            'AAPL': [0.01, 0.02, -0.01, 0.03, 0.01],
            'MSFT': [0.01, 0.02, -0.01, 0.03, 0.01]
        }
        
        event_data = [
            {
                'symbol': 'AAPL',
                'event_time': datetime.now(),
                'price_data': [
                    {'time': datetime.now(), 'price': 150.0},
                    {'time': datetime.now(), 'price': 155.0}
                ]
            }
        ]
        
        result = engine.analyze(
            market_data=market_data,
            securities_returns=securities_returns,
            event_data=event_data
        )
        
        assert result.securities_analyzed == 1
        assert result.anomalies_detected >= 1


class TestMasterControllerIntegration:
    """Test master execution controller ChainValidator integration."""
    
    def test_evidence_chain_integrity_error_defined(self):
        """Verify EvidenceChainIntegrityError is defined."""
        from src.core.master_execution_controller import EvidenceChainIntegrityError
        
        # Should be an Exception subclass
        assert issubclass(EvidenceChainIntegrityError, Exception)
        
        # Should be raisable
        with pytest.raises(EvidenceChainIntegrityError):
            raise EvidenceChainIntegrityError("Test error")
    
    def test_chain_validator_imports_available(self):
        """Verify ChainValidator can be imported in Phase 8 context."""
        # This tests that the imports would work at runtime
        from src.core.evidence_chain.chain_validator import ChainValidator
        from src.core.evidence_chain.hash_service import EvidenceRecord, HashService
        
        # Should be able to instantiate
        validator = ChainValidator()
        assert validator is not None
        
        # Should be able to create hash service
        hash_service = HashService()
        assert hash_service is not None


class TestDeprecatedFilesRemoved:
    """Test that deprecated files have been removed."""
    
    def test_linear_orchestrator_removed(self):
        """Verify linear_orchestrator.py has been deleted."""
        import os
        
        orchestrator_path = Path(__file__).parent.parent / "src" / "core" / "linear_orchestrator.py"
        assert not orchestrator_path.exists(), "linear_orchestrator.py should be deleted"
    
    def test_linear_orchestrator_test_removed(self):
        """Verify test_linear_orchestrator_deprecation.py has been deleted."""
        test_path = Path(__file__).parent / "test_linear_orchestrator_deprecation.py"
        assert not test_path.exists(), "test_linear_orchestrator_deprecation.py should be deleted"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
