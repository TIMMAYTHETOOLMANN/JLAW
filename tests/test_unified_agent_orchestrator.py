"""
Tests for Unified Agent Orchestrator
====================================

Validates multi-tier investigation workflow, result aggregation,
violation deduplication, and consensus computation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestUnifiedAgentOrchestrator:
    """Test unified agent orchestrator functionality."""
    
    def test_orchestrator_initialization(self):
        """Test that orchestrator initializes correctly."""
        from src.core.unified_agent_orchestrator import UnifiedAgentOrchestrator
        
        orchestrator = UnifiedAgentOrchestrator()
        
        assert orchestrator is not None
        assert orchestrator.tasks_executed == 0
        assert orchestrator.total_tokens_used == 0
        assert len(orchestrator.tier_invocation_counts) == 4
        print("✓ Orchestrator initialized successfully")
    
    @pytest.mark.asyncio
    async def test_execute_investigation_no_filings(self):
        """Test investigation with no filings."""
        from src.core.unified_agent_orchestrator import UnifiedAgentOrchestrator
        
        orchestrator = UnifiedAgentOrchestrator()
        
        result = await orchestrator.execute_investigation(
            investigation_type="full_forensic",
            filings=[],
            context={"cik": "000000", "company_name": "Test Company"},
            enable_subagents=False,
            enable_patterns=False
        )
        
        assert result is not None
        assert result.status in ("success", "partial", "failure")
        assert isinstance(result.aggregated_violations, list)
        assert isinstance(result.consensus_score, float)
        print(f"✓ Handled empty filings: status={result.status}")
    
    @pytest.mark.asyncio
    async def test_execute_investigation_with_mock_dual_agent(self):
        """Test investigation with mocked dual-agent."""
        from src.core.unified_agent_orchestrator import UnifiedAgentOrchestrator
        
        # Mock DualAgentCoordinator
        mock_dual_agent = MagicMock()
        mock_dual_agent.investigate_with_cross_reference = AsyncMock(return_value={
            'merged_violations': [
                {
                    'type': 'insider_trading',
                    'severity': 'HIGH',
                    'description': 'Mock violation',
                    'statute': '10b-5'
                }
            ],
            'investigation_summary': {
                'confidence_level': 0.85
            }
        })
        
        with patch('src.forensics.dual_agent.DualAgentCoordinator', return_value=mock_dual_agent):
            orchestrator = UnifiedAgentOrchestrator()
            
            filings = [
                {
                    'form_type': '4',
                    'filing_date': '2024-01-01',
                    'content': 'Test filing content',
                    'cik': '000000'
                }
            ]
            
            result = await orchestrator.execute_investigation(
                investigation_type="form4",
                filings=filings,
                context={"cik": "000000", "company_name": "Test Company"},
                enable_subagents=False,
                enable_patterns=False
            )
            
            assert result.status in ("success", "partial")
            assert len(result.aggregated_violations) > 0
            assert result.consensus_score > 0
            assert "primary" in result.tiers_executed
            print(f"✓ Dual-agent tier executed: {len(result.aggregated_violations)} violations")
    
    def test_deduplicate_violations(self):
        """Test violation deduplication logic."""
        from src.core.unified_agent_orchestrator import UnifiedAgentOrchestrator
        
        orchestrator = UnifiedAgentOrchestrator()
        
        violations = [
            {
                'type': 'insider_trading',
                'statute': '10b-5',
                'description': 'Suspicious trade pattern',
                'severity': 'HIGH'
            },
            {
                'type': 'insider_trading',
                'statute': '10b-5',
                'description': 'Suspicious trade pattern',
                'severity': 'MEDIUM'  # Duplicate with lower severity
            },
            {
                'type': 'accounting_fraud',
                'statute': 'SOX-404',
                'description': 'Financial statement irregularity',
                'severity': 'CRITICAL'
            }
        ]
        
        deduplicated = orchestrator._deduplicate_violations(violations)
        
        # Should keep only 2 violations (duplicate removed)
        assert len(deduplicated) == 2
        # Should keep the HIGH severity version (sorted first)
        insider_trades = [v for v in deduplicated if v['type'] == 'insider_trading']
        assert len(insider_trades) == 1
        assert insider_trades[0]['severity'] == 'HIGH'
        print(f"✓ Deduplicated {len(violations)} → {len(deduplicated)} violations")
    
    def test_compute_unified_consensus(self):
        """Test unified consensus computation."""
        from src.core.unified_agent_orchestrator import UnifiedAgentOrchestrator, AgentTier
        
        orchestrator = UnifiedAgentOrchestrator()
        
        # Test with all tiers
        tier_results = {
            AgentTier.PRIMARY.value: {
                'status': 'success',
                'consensus': 0.85
            },
            AgentTier.SUBAGENT.value: {
                'status': 'success',
                'consensus_score': 0.90
            },
            AgentTier.PATTERN.value: {
                'status': 'success',
                'patterns_executed': 20  # 20/23 = 0.87
            }
        }
        
        consensus = orchestrator._compute_unified_consensus(tier_results)
        
        # Expected: (0.85 * 0.4) + (0.90 * 0.4) + (0.87 * 0.2) = 0.874
        assert consensus > 0.0
        assert consensus <= 1.0
        assert 0.85 <= consensus <= 0.90  # Should be in reasonable range
        print(f"✓ Unified consensus: {consensus:.2%}")
    
    def test_compute_unified_consensus_partial_tiers(self):
        """Test consensus with only some tiers executed."""
        from src.core.unified_agent_orchestrator import UnifiedAgentOrchestrator, AgentTier
        
        orchestrator = UnifiedAgentOrchestrator()
        
        # Only primary tier
        tier_results = {
            AgentTier.PRIMARY.value: {
                'status': 'success',
                'consensus': 0.75
            }
        }
        
        consensus = orchestrator._compute_unified_consensus(tier_results)
        
        # Should return 0.75 (100% weight on single tier)
        assert consensus == 0.75
        print(f"✓ Partial consensus (1 tier): {consensus:.2%}")
    
    def test_count_tokens(self):
        """Test token counting across tiers."""
        from src.core.unified_agent_orchestrator import UnifiedAgentOrchestrator, AgentTier
        
        orchestrator = UnifiedAgentOrchestrator()
        
        tier_results = {
            AgentTier.PRIMARY.value: {
                'tokens_used': 1500
            },
            AgentTier.SUBAGENT.value: {
                'total_tokens': 2500
            },
            AgentTier.PATTERN.value: {
                'token_count': 500
            }
        }
        
        total_tokens = orchestrator._count_tokens(tier_results)
        
        assert total_tokens == 4500
        print(f"✓ Total tokens counted: {total_tokens}")
    
    def test_get_metrics(self):
        """Test metrics retrieval."""
        from src.core.unified_agent_orchestrator import UnifiedAgentOrchestrator
        
        orchestrator = UnifiedAgentOrchestrator()
        orchestrator.tasks_executed = 5
        orchestrator.total_tokens_used = 10000
        
        metrics = orchestrator.get_metrics()
        
        assert metrics['tasks_executed'] == 5
        assert metrics['total_tokens_used'] == 10000
        assert metrics['avg_tokens_per_task'] == 2000
        assert 'tier_invocation_counts' in metrics
        assert 'sdk_availability' in metrics
        print(f"✓ Metrics retrieved: {metrics['tasks_executed']} tasks")
    
    @pytest.mark.asyncio
    async def test_tier_1_execution_with_error(self):
        """Test Tier 1 execution with error handling."""
        from src.core.unified_agent_orchestrator import UnifiedAgentOrchestrator
        
        # Mock DualAgentCoordinator that raises error
        with patch('src.forensics.dual_agent.DualAgentCoordinator') as mock_class:
            mock_class.side_effect = Exception("Mock dual-agent error")
            
            orchestrator = UnifiedAgentOrchestrator()
            
            result = await orchestrator.execute_investigation(
                investigation_type="full_forensic",
                filings=[{'form_type': '4', 'content': 'test'}],
                context={"cik": "000000"},
                enable_subagents=False,
                enable_patterns=False
            )
            
            # Should handle error gracefully
            assert result is not None
            assert len(result.errors) > 0
            assert result.status in ("partial", "failure")
            print(f"✓ Error handled gracefully: {result.status}")
    
    @pytest.mark.asyncio
    async def test_subagent_routing_integration(self):
        """Test Tier 2 subagent routing integration."""
        from src.core.unified_agent_orchestrator import UnifiedAgentOrchestrator
        
        # Mock both DualAgentCoordinator and IntelligentSubagentRouter
        mock_dual_agent = MagicMock()
        mock_dual_agent.investigate_with_cross_reference = AsyncMock(return_value={
            'merged_violations': [{'type': 'test', 'severity': 'HIGH'}],
            'investigation_summary': {'confidence_level': 0.8}
        })
        
        mock_router = MagicMock()
        mock_router.plan_execution = MagicMock(return_value=MagicMock(
            selected_agents=[],
            execution_plan=[],
            agent_scores={}
        ))
        mock_router.execute = AsyncMock(return_value={
            'combined_findings': [{'finding_type': 'test', 'severity': 'HIGH'}],
            'agents_executed': ['forensic-financial-analyst'],
            'consensus_score': 0.85,
            'conflicts': []
        })
        
        with patch('src.forensics.dual_agent.DualAgentCoordinator', return_value=mock_dual_agent), \
             patch('src.forensics.intelligent_router.IntelligentSubagentRouter', return_value=mock_router):
            
            orchestrator = UnifiedAgentOrchestrator()
            
            result = await orchestrator.execute_investigation(
                investigation_type="full_forensic",
                filings=[{'form_type': '4', 'content': 'test'}],
                context={"cik": "000000"},
                enable_subagents=True,
                enable_patterns=False
            )
            
            assert result.status in ("success", "partial")
            assert "primary" in result.tiers_executed
            assert "subagent" in result.tiers_executed
            print(f"✓ Multi-tier execution: {len(result.tiers_executed)} tiers")


class TestExecutionMetrics:
    """Test execution metrics collector."""
    
    def test_metrics_collector_initialization(self):
        """Test metrics collector initialization."""
        from src.forensics.execution_metrics import ExecutionMetricsCollector
        
        collector = ExecutionMetricsCollector()
        
        assert len(collector.metrics) == 0
        assert len(collector.active_metrics) == 0
        print("✓ Metrics collector initialized")
    
    def test_start_and_end_agent(self):
        """Test agent tracking lifecycle."""
        from src.forensics.execution_metrics import ExecutionMetricsCollector
        
        collector = ExecutionMetricsCollector()
        
        # Start tracking
        metric = collector.start_agent("test-agent", "subagent", tier="subagent")
        
        assert metric.agent_name == "test-agent"
        assert metric.status == "pending"
        assert len(collector.metrics) == 1
        assert "test-agent" in collector.active_metrics
        
        # Update metrics
        metric.tokens_used = 1000
        metric.violations_found = 5
        
        # End tracking
        collector.end_agent(metric, status="success")
        
        assert metric.status == "success"
        assert metric.duration_seconds > 0
        assert "test-agent" not in collector.active_metrics
        print(f"✓ Agent tracked: {metric.duration_seconds:.3f}s, {metric.tokens_used} tokens")
    
    def test_get_summary(self):
        """Test summary statistics."""
        from src.forensics.execution_metrics import ExecutionMetricsCollector
        
        collector = ExecutionMetricsCollector()
        
        # Track multiple agents
        for i in range(3):
            metric = collector.start_agent(f"agent-{i}", "subagent", tier="subagent")
            metric.tokens_used = 1000 * (i + 1)
            metric.violations_found = i + 1
            collector.end_agent(metric, status="success")
        
        summary = collector.get_summary()
        
        assert summary['total_agents'] == 3
        assert summary['total_tokens'] == 6000  # 1000 + 2000 + 3000
        assert summary['total_violations'] == 6  # 1 + 2 + 3
        assert summary['success_count'] == 3
        assert summary['error_count'] == 0
        print(f"✓ Summary: {summary['total_agents']} agents, {summary['total_tokens']} tokens")
    
    def test_export_metrics(self, tmp_path):
        """Test metrics export to JSON."""
        from src.forensics.execution_metrics import ExecutionMetricsCollector
        
        collector = ExecutionMetricsCollector()
        
        metric = collector.start_agent("test-agent", "subagent")
        metric.tokens_used = 500
        collector.end_agent(metric, status="success")
        
        # Export to temp file
        output_file = tmp_path / "metrics.json"
        collector.export_metrics(str(output_file))
        
        assert output_file.exists()
        
        # Verify JSON content
        import json
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert 'export_timestamp' in data
        assert 'summary' in data
        assert 'metrics' in data
        assert len(data['metrics']) == 1
        print(f"✓ Metrics exported to {output_file}")
    
    def test_get_failed_agents(self):
        """Test filtering failed agents."""
        from src.forensics.execution_metrics import ExecutionMetricsCollector
        
        collector = ExecutionMetricsCollector()
        
        # Add successful agent
        metric1 = collector.start_agent("success-agent", "subagent")
        collector.end_agent(metric1, status="success")
        
        # Add failed agent
        metric2 = collector.start_agent("failed-agent", "subagent")
        collector.end_agent(metric2, status="error", error="Test error")
        
        failed = collector.get_failed_agents()
        
        assert len(failed) == 1
        assert failed[0].agent_name == "failed-agent"
        assert failed[0].error == "Test error"
        print(f"✓ Found {len(failed)} failed agents")


if __name__ == "__main__":
    # Run basic tests without pytest
    print("Running basic tests...")
    
    # Test orchestrator initialization
    test = TestUnifiedAgentOrchestrator()
    test.test_orchestrator_initialization()
    test.test_deduplicate_violations()
    test.test_compute_unified_consensus()
    test.test_compute_unified_consensus_partial_tiers()
    test.test_count_tokens()
    test.test_get_metrics()
    
    # Test metrics collector
    metrics_test = TestExecutionMetrics()
    metrics_test.test_metrics_collector_initialization()
    metrics_test.test_start_and_end_agent()
    metrics_test.test_get_summary()
    metrics_test.test_get_failed_agents()
    
    print("\n✓ All basic tests passed!")
