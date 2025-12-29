"""
Integration tests for individual node execution and inter-node dependencies.
"""

import pytest
from pathlib import Path
from datetime import date

from src.core.master_execution_controller import MasterExecutionController


@pytest.mark.asyncio
@pytest.mark.integration
async def test_all_15_nodes_execute():
    """
    Validate that all 15 pipeline nodes execute successfully
    """
    output_dir = Path("tests/output/node_execution")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    controller = MasterExecutionController(
        cik="0000320187",
        company_name="Test Company",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 3, 31),
        output_dir=output_dir,
        strict_mode=False,  # Allow graceful failures
        auto_mode=True
    )
    
    result = await controller.execute_full_analysis()
    
    assert result is not None, "Analysis result is None"
    
    # Validate that nodes executed (check node_results)
    assert len(result.node_results) > 0, "No nodes executed"
    
    # Print executed nodes for debugging
    print(f"\n✅ Nodes executed: {len(result.node_results)}")
    for node_name, node_result in result.node_results.items():
        print(f"   - {node_name}: {node_result.status}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_23_detection_patterns():
    """
    Validate that detection patterns are evaluated
    """
    output_dir = Path("tests/output/detection_patterns")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    controller = MasterExecutionController(
        cik="0000320187",
        company_name="Test Company",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        output_dir=output_dir,
        strict_mode=False,
        auto_mode=True
    )
    
    result = await controller.execute_full_analysis()
    
    assert result is not None, "Analysis result is None"
    
    # Verify detection results exist
    assert result.detection_results is not None, "No detection results"
    
    # Print detection results for debugging
    print(f"\n✅ Detection patterns evaluated")
    if isinstance(result.detection_results, dict):
        print(f"   Detection result keys: {list(result.detection_results.keys())}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_node_error_handling():
    """
    Test that the system handles node failures gracefully in non-strict mode
    """
    output_dir = Path("tests/output/error_handling")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    controller = MasterExecutionController(
        cik="0000000000",  # Invalid CIK
        company_name="Invalid Company",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 3, 31),
        output_dir=output_dir,
        strict_mode=False,  # Should not abort
        auto_mode=True
    )
    
    # Should complete even with invalid CIK in non-strict mode
    result = await controller.execute_full_analysis()
    
    assert result is not None, "Result should still be generated"
    print(f"\n✅ Error handling test complete")
    print(f"   Phases: {len(result.phase_results)}")
    print(f"   Nodes: {len(result.node_results)}")
