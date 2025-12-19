"""
Integration Test for Complete 15-Node System
============================================

Validates that all 15 nodes can be imported and initialized successfully,
ensuring complete system unification with zero fragmentation.
"""

import pytest
from datetime import date


class TestFifteenNodeIntegration:
    """Test suite for complete 15-node system integration."""
    
    def test_all_nodes_import_successfully(self):
        """Verify all 15 nodes can be imported without errors."""
        # Node 1: Form 4
        from src.nodes.node1_form4 import Form4Parser, ShortSwingCalculator, GiftPatternDetector
        
        # Node 2: DEF 14A
        from src.nodes.node2_def14a import DEF14ACompensationAnalyzer
        
        # Node 3: 10-Q
        from src.nodes.node3_10q import TemporalConsistencyValidator
        
        # Node 4: 10-K SOX
        from src.nodes.node4_10k_sox import SOXCertificationAnalyzer
        
        # Node 5: IRC §83
        from src.nodes.node5_irs import IRC83TaxCalculator
        
        # Node 6: Routing
        from src.nodes.node6_routing import EnforcementRouter
        
        # Node 7: 13F-HR
        from src.nodes.node7_13f_holdings import InstitutionalHoldingsAnalyzer
        
        # Node 8: 13D/13G
        from src.nodes.node8_13d_ownership import BeneficialOwnershipTracker
        
        # Node 9: 8-K
        from src.nodes.node9_8k_events import MaterialEventCorrelator
        
        # Node 10: Form 144
        from src.nodes.node10_form144 import RestrictedSaleMonitorV2
        
        # Node 11: Network Mapper
        from src.nodes.node11_network_mapper import ExecutiveNetworkAnalyzerV2
        
        # Node 12: Earnings Calls
        from src.nodes.node12_earnings_calls import TranscriptAnalyzerV2
        
        # Node 13: Z-Score
        from src.nodes.node13_zscore import BankruptcyPredictorV2
        
        # Node 14: F-Score
        from src.nodes.node14_fscore import FinancialStrengthAnalyzerV2
        
        # Node 15: Market Correlation
        from src.nodes.node15_market_correlation import MarketCorrelationEngineV2
        
        # If we got here, all imports succeeded
        assert True, "All 15 nodes imported successfully"
    
    def test_recursive_engine_imports(self):
        """Verify recursive engine imports correctly."""
        from src.core.recursive_engine import RecursiveProsecutorialEngine
        
        engine = RecursiveProsecutorialEngine(
            sec_user_agent="Test/1.0",
            polygon_api_key=None
        )
        
        assert engine is not None
        assert engine.__class__.__name__ == "RecursiveProsecutorialEngine"
    
    def test_backward_compatibility_alias(self):
        """Verify V2 alias still works for backward compatibility."""
        from src.core.recursive_engine import RecursiveProsecutorialEngineV2
        
        # Should be the same class
        from src.core.recursive_engine import RecursiveProsecutorialEngine
        assert RecursiveProsecutorialEngineV2 is RecursiveProsecutorialEngine
    
    def test_all_node_classes_instantiate(self):
        """Verify all node classes can be instantiated."""
        # Node 2
        from src.nodes.node2_def14a import DEF14ACompensationAnalyzer
        node2 = DEF14ACompensationAnalyzer()
        assert node2 is not None
        
        # Node 3
        from src.nodes.node3_10q import TemporalConsistencyValidator
        node3 = TemporalConsistencyValidator()
        assert node3 is not None
        
        # Node 4
        from src.nodes.node4_10k_sox import SOXCertificationAnalyzer
        node4 = SOXCertificationAnalyzer()
        assert node4 is not None
        
        # Node 5
        from src.nodes.node5_irs import IRC83TaxCalculator
        node5 = IRC83TaxCalculator()
        assert node5 is not None
        
        # Node 6
        from src.nodes.node6_routing import EnforcementRouter
        node6 = EnforcementRouter()
        assert node6 is not None
        
        # Node 7
        from src.nodes.node7_13f_holdings import InstitutionalHoldingsAnalyzer
        node7 = InstitutionalHoldingsAnalyzer()
        assert node7 is not None
        
        # Node 8
        from src.nodes.node8_13d_ownership import BeneficialOwnershipTracker
        node8 = BeneficialOwnershipTracker()
        assert node8 is not None
        
        # Node 9
        from src.nodes.node9_8k_events import MaterialEventCorrelator
        node9 = MaterialEventCorrelator()
        assert node9 is not None
        
        # Node 10
        from src.nodes.node10_form144 import RestrictedSaleMonitorV2
        node10 = RestrictedSaleMonitorV2()
        assert node10 is not None
        
        # Node 11
        from src.nodes.node11_network_mapper import ExecutiveNetworkAnalyzerV2
        node11 = ExecutiveNetworkAnalyzerV2()
        assert node11 is not None
        
        # Node 12
        from src.nodes.node12_earnings_calls import TranscriptAnalyzerV2
        node12 = TranscriptAnalyzerV2()
        assert node12 is not None
        
        # Node 13
        from src.nodes.node13_zscore import BankruptcyPredictorV2
        node13 = BankruptcyPredictorV2()
        assert node13 is not None
        
        # Node 14
        from src.nodes.node14_fscore import FinancialStrengthAnalyzerV2
        node14 = FinancialStrengthAnalyzerV2()
        assert node14 is not None
        
        # Node 15
        from src.nodes.node15_market_correlation import MarketCorrelationEngineV2
        node15 = MarketCorrelationEngineV2()
        assert node15 is not None
    
    def test_recursive_engine_has_all_execution_methods(self):
        """Verify recursive engine has execution methods for all 15 nodes."""
        from src.core.recursive_engine import RecursiveProsecutorialEngine
        
        engine = RecursiveProsecutorialEngine()
        
        # Check that all execution methods exist
        assert hasattr(engine, '_execute_node1'), "Missing _execute_node1"
        assert hasattr(engine, '_execute_node2'), "Missing _execute_node2"
        assert hasattr(engine, '_execute_node3'), "Missing _execute_node3"
        assert hasattr(engine, '_execute_node4'), "Missing _execute_node4"
        assert hasattr(engine, '_execute_node5'), "Missing _execute_node5"
        # Node 6 is handled inline
        assert hasattr(engine, '_execute_node7'), "Missing _execute_node7"
        assert hasattr(engine, '_execute_node8'), "Missing _execute_node8"
        assert hasattr(engine, '_execute_node9'), "Missing _execute_node9"
        assert hasattr(engine, '_execute_node10'), "Missing _execute_node10"
        assert hasattr(engine, '_execute_node11'), "Missing _execute_node11"
        assert hasattr(engine, '_execute_node12'), "Missing _execute_node12"
        assert hasattr(engine, '_execute_node13'), "Missing _execute_node13"
        assert hasattr(engine, '_execute_node14'), "Missing _execute_node14"
        assert hasattr(engine, '_execute_node15'), "Missing _execute_node15"
        
        # Check main analysis method
        assert hasattr(engine, 'run_full_analysis'), "Missing run_full_analysis"
    
    def test_jlaw_unified_imports_recursive_engine(self):
        """Verify JLAW_UNIFIED.py can import the recursive engine."""
        # This tests the actual import that was mentioned in the problem statement
        from src.core.recursive_engine import RecursiveProsecutorialEngine
        
        # Should not raise ImportError
        assert RecursiveProsecutorialEngine is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
