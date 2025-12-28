"""
Performance and load testing for scalability validation.
"""

import pytest
import asyncio
from datetime import date
from pathlib import Path
import time

from src.core.master_execution_controller import MasterExecutionController


@pytest.mark.asyncio
@pytest.mark.slow
async def test_concurrent_analysis_throughput():
    """
    Test system throughput with multiple concurrent analyses
    """
    output_dir = Path("tests/output/load_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    test_companies = [
        ("0000320187", "Apple Inc."),
        ("0000789019", "Microsoft Corporation"),
        ("0001018724", "Amazon.com, Inc."),
        ("0001652044", "Alphabet Inc."),
        ("0001326801", "Meta Platforms, Inc.")
    ]
    
    start_time = time.time()
    
    # Run 5 concurrent analyses with short date range
    tasks = []
    for cik, name in test_companies:
        company_output_dir = output_dir / cik
        company_output_dir.mkdir(parents=True, exist_ok=True)
        
        controller = MasterExecutionController(
            cik=cik,
            company_name=name,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31),  # Short range for speed
            output_dir=company_output_dir,
            strict_mode=False,
            auto_mode=True
        )
        tasks.append(controller.execute_full_analysis())
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    elapsed_time = time.time() - start_time
    
    # Validate results
    successful = sum(1 for r in results if not isinstance(r, Exception) and r is not None)
    
    print(f"\n✅ Load test complete: {successful}/5 successful in {elapsed_time:.2f}s")
    print(f"   Average time per analysis: {elapsed_time/5:.2f}s")
    
    # At least some should succeed
    assert successful >= 1, f"Only {successful}/5 analyses succeeded"
    
    # Performance assertion (should complete in reasonable time)
    # More lenient timeout for CI environments
    assert elapsed_time < 1200, f"Load test took {elapsed_time}s, expected <1200s"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_sequential_analysis_performance():
    """
    Test performance of sequential analyses
    """
    output_dir = Path("tests/output/sequential_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    
    controller = MasterExecutionController(
        cik="0000320187",
        company_name="Test Company",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 3, 31),
        output_dir=output_dir,
        strict_mode=False,
        auto_mode=True
    )
    
    result = await controller.execute_full_analysis()
    
    elapsed_time = time.time() - start_time
    
    assert result is not None, "Analysis should complete"
    
    print(f"\n✅ Sequential analysis complete in {elapsed_time:.2f}s")
    print(f"   Phases: {len(result.phase_results)}")
    print(f"   Nodes: {len(result.node_results)}")
    
    # Should complete in reasonable time for single analysis
    assert elapsed_time < 600, f"Single analysis took {elapsed_time}s, expected <600s"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_large_date_range_performance():
    """
    Test performance with larger date range (full year)
    """
    output_dir = Path("tests/output/large_range_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    
    controller = MasterExecutionController(
        cik="0000320187",
        company_name="Test Company",
        start_date=date(2022, 1, 1),
        end_date=date(2022, 12, 31),  # Full year
        output_dir=output_dir,
        strict_mode=False,
        auto_mode=True
    )
    
    result = await controller.execute_full_analysis()
    
    elapsed_time = time.time() - start_time
    
    assert result is not None, "Analysis should complete"
    
    print(f"\n✅ Large range analysis complete in {elapsed_time:.2f}s")
    print(f"   Date range: 12 months")
    print(f"   Nodes: {len(result.node_results)}")
    
    # Longer timeout for full year analysis
    assert elapsed_time < 900, f"Full year analysis took {elapsed_time}s, expected <900s"
