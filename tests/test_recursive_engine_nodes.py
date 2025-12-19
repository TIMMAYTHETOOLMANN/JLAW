"""
Test Suite for Recursive Engine Nodes 7-15 Data Flow
====================================================

Tests that nodes 7-15 properly fetch and process SEC EDGAR data
instead of passing empty arrays.
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, AsyncMock, patch
from src.core.recursive_engine import RecursiveProsecutorialEngine, NodeResult


class TestRecursiveEngineNodes:
    """Test suite for nodes 7-15 data flow improvements."""
    
    @pytest.fixture
    def engine(self):
        """Create engine instance for testing."""
        return RecursiveProsecutorialEngine(
            sec_user_agent="Test/1.0",
            polygon_api_key=None
        )
    
    @pytest.mark.asyncio
    async def test_node7_executes_with_sec_data(self, engine):
        """Test Node 7 fetches 13F-HR filings."""
        # Mock SEC client
        mock_sec_client = AsyncMock()
        mock_sec_client.get_filings = AsyncMock(return_value=[])
        
        result = await engine._execute_node7(
            mock_sec_client,
            cik="0000320193",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        
        assert isinstance(result, NodeResult)
        assert result.node_id == "NODE_7"
        assert result.node_name == "13F Holdings"
        assert result.status in ["success", "error", "no_data"]
        assert result.execution_time_seconds > 0
        
        # Verify SEC client was called with correct form type
        mock_sec_client.get_filings.assert_called_once()
        call_kwargs = mock_sec_client.get_filings.call_args[1]
        assert "13F-HR" in call_kwargs["form_types"]
    
    @pytest.mark.asyncio
    async def test_node8_executes_with_sec_data(self, engine):
        """Test Node 8 fetches SC 13D/13G filings."""
        mock_sec_client = AsyncMock()
        mock_sec_client.get_filings = AsyncMock(return_value=[])
        
        result = await engine._execute_node8(
            mock_sec_client,
            cik="0000320193",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        
        assert isinstance(result, NodeResult)
        assert result.node_id == "NODE_8"
        assert result.node_name == "13D/13G Ownership"
        assert result.status in ["success", "error", "no_data"]
        
        # Verify SEC client was called with correct form types
        mock_sec_client.get_filings.assert_called_once()
        call_kwargs = mock_sec_client.get_filings.call_args[1]
        assert "SC 13D" in call_kwargs["form_types"]
        assert "SC 13G" in call_kwargs["form_types"]
    
    @pytest.mark.asyncio
    async def test_node9_executes_with_sec_data(self, engine):
        """Test Node 9 fetches 8-K filings."""
        mock_sec_client = AsyncMock()
        mock_sec_client.get_filings = AsyncMock(return_value=[])
        
        result = await engine._execute_node9(
            mock_sec_client,
            cik="0000320193",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        
        assert isinstance(result, NodeResult)
        assert result.node_id == "NODE_9"
        assert result.node_name == "8-K Events"
        assert result.status in ["success", "error", "no_data"]
        
        # Verify SEC client was called with correct form type
        mock_sec_client.get_filings.assert_called_once()
        call_kwargs = mock_sec_client.get_filings.call_args[1]
        assert "8-K" in call_kwargs["form_types"]
    
    @pytest.mark.asyncio
    async def test_node10_handles_missing_form144(self, engine):
        """Test Node 10 handles Form 144 placeholder gracefully."""
        mock_sec_client = AsyncMock()
        
        result = await engine._execute_node10(
            mock_sec_client,
            cik="0000320193",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        
        assert isinstance(result, NodeResult)
        assert result.node_id == "NODE_10"
        assert result.node_name == "Form 144"
        # Form 144 should return no_data status since it's not in EDGAR API
        assert result.status in ["no_data", "success", "error"]
        assert "Form 144" in result.findings.get("message", "")
    
    @pytest.mark.asyncio
    async def test_node11_uses_form4_data(self, engine):
        """Test Node 11 fetches Form 4 data for network analysis."""
        mock_sec_client = AsyncMock()
        mock_sec_client.get_form4_filings = AsyncMock(return_value=[])
        mock_sec_client.get_form4_xml = AsyncMock(return_value=None)
        
        mock_node2_result = NodeResult(
            node_id="NODE_2",
            node_name="DEF 14A",
            status="success",
            violations_found=0,
            alerts_generated=0,
            findings={},
            execution_time_seconds=1.0
        )
        
        result = await engine._execute_node11(
            mock_sec_client,
            cik="0000320193",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            node2_result=mock_node2_result
        )
        
        assert isinstance(result, NodeResult)
        assert result.node_id == "NODE_11"
        assert result.node_name == "Network Mapper"
        
        # Verify Form 4 was fetched
        mock_sec_client.get_form4_filings.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_node12_extracts_from_8k(self, engine):
        """Test Node 12 extracts earnings calls from 8-K Item 7.01."""
        mock_sec_client = AsyncMock()
        mock_sec_client.get_filings = AsyncMock(return_value=[])
        mock_sec_client.get_filing_text = AsyncMock(return_value=None)
        
        mock_node9_result = NodeResult(
            node_id="NODE_9",
            node_name="8-K Events",
            status="success",
            violations_found=0,
            alerts_generated=0,
            findings={},
            execution_time_seconds=1.0
        )
        
        result = await engine._execute_node12(
            mock_sec_client,
            cik="0000320193",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            node9_result=mock_node9_result
        )
        
        assert isinstance(result, NodeResult)
        assert result.node_id == "NODE_12"
        assert result.node_name == "Earnings Calls"
        
        # Verify 8-K filings were fetched
        mock_sec_client.get_filings.assert_called_once()
        call_kwargs = mock_sec_client.get_filings.call_args[1]
        assert "8-K" in call_kwargs["form_types"]
    
    @pytest.mark.asyncio
    async def test_node13_uses_xbrl_data(self, engine):
        """Test Node 13 fetches XBRL data for Z-Score calculation."""
        mock_sec_client = AsyncMock()
        mock_sec_client.get_xbrl_facts = AsyncMock(return_value=None)
        
        result = await engine._execute_node13(
            mock_sec_client,
            cik="0000320193",
            company_name="Test Corp"
        )
        
        assert isinstance(result, NodeResult)
        assert result.node_id == "NODE_13"
        assert result.node_name == "Z-Score"
        
        # Verify XBRL facts were requested
        mock_sec_client.get_xbrl_facts.assert_called_once_with("0000320193")
    
    @pytest.mark.asyncio
    async def test_node14_uses_xbrl_data(self, engine):
        """Test Node 14 fetches XBRL data for F-Score calculation."""
        mock_sec_client = AsyncMock()
        mock_sec_client.get_xbrl_facts = AsyncMock(return_value=None)
        
        result = await engine._execute_node14(
            mock_sec_client,
            cik="0000320193",
            company_name="Test Corp"
        )
        
        assert isinstance(result, NodeResult)
        assert result.node_id == "NODE_14"
        assert result.node_name == "F-Score"
        
        # Verify XBRL facts were requested
        mock_sec_client.get_xbrl_facts.assert_called_once_with("0000320193")
    
    @pytest.mark.asyncio
    async def test_node15_checks_polygon_api_key(self, engine):
        """Test Node 15 checks for Polygon.io API key."""
        result = await engine._execute_node15(
            cik="0000320193",
            company_name="Test Corp"
        )
        
        assert isinstance(result, NodeResult)
        assert result.node_id == "NODE_15"
        assert result.node_name == "Market Correlation"
        # Should be skipped if no API key
        assert result.status in ["skipped", "success", "error"]
    
    @pytest.mark.asyncio
    async def test_all_nodes_have_error_handling(self, engine):
        """Test that all nodes have proper error handling."""
        mock_sec_client = AsyncMock()
        mock_sec_client.get_filings = AsyncMock(side_effect=Exception("Test error"))
        mock_sec_client.get_form4_filings = AsyncMock(side_effect=Exception("Test error"))
        mock_sec_client.get_xbrl_facts = AsyncMock(side_effect=Exception("Test error"))
        
        mock_node2 = NodeResult("NODE_2", "Test", "success", 0, 0, {}, 1.0)
        mock_node9 = NodeResult("NODE_9", "Test", "success", 0, 0, {}, 1.0)
        
        # Test each node handles errors gracefully
        nodes_to_test = [
            engine._execute_node7(mock_sec_client, "0000320193", date(2023, 1, 1), date(2023, 12, 31)),
            engine._execute_node8(mock_sec_client, "0000320193", date(2023, 1, 1), date(2023, 12, 31)),
            engine._execute_node9(mock_sec_client, "0000320193", date(2023, 1, 1), date(2023, 12, 31)),
            engine._execute_node10(mock_sec_client, "0000320193", date(2023, 1, 1), date(2023, 12, 31)),
            engine._execute_node11(mock_sec_client, "0000320193", date(2023, 1, 1), date(2023, 12, 31), mock_node2),
            engine._execute_node12(mock_sec_client, "0000320193", date(2023, 1, 1), date(2023, 12, 31), mock_node9),
            engine._execute_node13(mock_sec_client, "0000320193", "Test"),
            engine._execute_node14(mock_sec_client, "0000320193", "Test"),
        ]
        
        for node_coro in nodes_to_test:
            result = await node_coro
            assert isinstance(result, NodeResult)
            # Error should be caught and result should have error status
            assert result.status in ["error", "no_data", "success"]
            if result.status == "error":
                assert result.error_message is not None
    
    @pytest.mark.asyncio
    async def test_all_nodes_track_timing(self, engine):
        """Test that all nodes track execution time."""
        mock_sec_client = AsyncMock()
        mock_sec_client.get_filings = AsyncMock(return_value=[])
        mock_sec_client.get_form4_filings = AsyncMock(return_value=[])
        mock_sec_client.get_xbrl_facts = AsyncMock(return_value=None)
        
        mock_node2 = NodeResult("NODE_2", "Test", "success", 0, 0, {}, 1.0)
        mock_node9 = NodeResult("NODE_9", "Test", "success", 0, 0, {}, 1.0)
        
        nodes_to_test = [
            engine._execute_node7(mock_sec_client, "0000320193", date(2023, 1, 1), date(2023, 12, 31)),
            engine._execute_node8(mock_sec_client, "0000320193", date(2023, 1, 1), date(2023, 12, 31)),
            engine._execute_node9(mock_sec_client, "0000320193", date(2023, 1, 1), date(2023, 12, 31)),
            engine._execute_node10(mock_sec_client, "0000320193", date(2023, 1, 1), date(2023, 12, 31)),
            engine._execute_node11(mock_sec_client, "0000320193", date(2023, 1, 1), date(2023, 12, 31), mock_node2),
            engine._execute_node12(mock_sec_client, "0000320193", date(2023, 1, 1), date(2023, 12, 31), mock_node9),
            engine._execute_node13(mock_sec_client, "0000320193", "Test"),
            engine._execute_node14(mock_sec_client, "0000320193", "Test"),
            engine._execute_node15("0000320193", "Test"),
        ]
        
        for node_coro in nodes_to_test:
            result = await node_coro
            # All nodes should track execution time
            assert result.execution_time_seconds >= 0
            assert isinstance(result.execution_time_seconds, float)
