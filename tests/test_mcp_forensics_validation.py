"""
JARVIS 2.0 - MCP Forensics Validation Test
Quick validation script to verify forensic system is operational.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_imports():
    """Test that all forensic modules can be imported."""
    print("=" * 80)
    print("TEST 1: Import Validation")
    print("=" * 80)
    
    try:
        from agents.mcp import (
            enable_forensics,
            disable_forensics,
            is_forensics_enabled,
            get_global_forensic_summary,
            get_server_forensic_summary,
            get_tool_execution_profiles,
            export_forensic_data_to_json,
            export_forensic_report_to_markdown,
            ForensicManager,
            ServerState,
        )
        print("✓ All forensic imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_enable_disable():
    """Test enable/disable functionality."""
    print("\n" + "=" * 80)
    print("TEST 2: Enable/Disable Functionality")
    print("=" * 80)
    
    try:
        from agents.mcp import (
            enable_forensics,
            disable_forensics,
            is_forensics_enabled,
        )
        
        # Test enable
        enable_forensics()
        assert is_forensics_enabled() == True, "Enable failed"
        print("✓ enable_forensics() works")
        
        # Test disable
        disable_forensics()
        assert is_forensics_enabled() == False, "Disable failed"
        print("✓ disable_forensics() works")
        
        # Re-enable for remaining tests
        enable_forensics()
        print("✓ Re-enabled for remaining tests")
        
        return True
    except Exception as e:
        print(f"✗ Enable/disable test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_forensic_classes():
    """Test that forensic classes can be instantiated."""
    print("\n" + "=" * 80)
    print("TEST 3: Forensic Classes Instantiation")
    print("=" * 80)
    
    try:
        from agents.mcp.forensics import (
            AuditTracker,
            ToolExecutionProfile,
            ExecutionProfiler,
            ForensicStateTracker,
            ForensicArchive,
            ErrorForensics,
            ServerState,
        )
        
        # Test AuditTracker
        audit = AuditTracker("test_server")
        print("✓ AuditTracker instantiated")
        
        # Test ToolExecutionProfile
        profile = ToolExecutionProfile("test_tool")
        print("✓ ToolExecutionProfile instantiated")
        
        # Test ForensicStateTracker
        state_tracker = ForensicStateTracker("test_server")
        print("✓ ForensicStateTracker instantiated")
        
        # Test ForensicArchive
        archive = ForensicArchive()
        print("✓ ForensicArchive instantiated")
        
        # Test ErrorForensics
        error_tracker = ErrorForensics("test_server")
        print("✓ ErrorForensics instantiated")
        
        # Test ServerState enum
        assert hasattr(ServerState, "UNINITIALIZED")
        assert hasattr(ServerState, "CONNECTING")
        assert hasattr(ServerState, "CONNECTED")
        print("✓ ServerState enum accessible")
        
        return True
    except Exception as e:
        print(f"✗ Class instantiation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_audit_tracking():
    """Test audit tracking functionality."""
    print("\n" + "=" * 80)
    print("TEST 4: Audit Tracking")
    print("=" * 80)
    
    try:
        from agents.mcp.forensics import AuditTracker
        
        tracker = AuditTracker("test_server", max_buffer_size=100)
        
        # Record some audits
        for i in range(5):
            await tracker.record_audit(
                operation=f"test_op_{i}",
                start_time=asyncio.get_event_loop().time(),
                tool_name="test_tool",
                arguments={"arg": i},
                result={"result": f"value_{i}"},
                retry_count=0,
                cache_state="clean",
                tools_cached=10,
            )
        
        print(f"✓ Recorded 5 audit entries")
        
        # Get summary
        summary = tracker.get_audit_summary()
        assert summary["total_operations"] == 5
        assert summary["error_count"] == 0
        print(f"✓ Audit summary correct: {summary['total_operations']} operations")
        
        return True
    except Exception as e:
        print(f"✗ Audit tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_execution_profiling():
    """Test execution profiling functionality."""
    print("\n" + "=" * 80)
    print("TEST 5: Execution Profiling")
    print("=" * 80)
    
    try:
        from agents.mcp.forensics import ExecutionProfiler
        
        # Get or create profile
        profile = await ExecutionProfiler.get_or_create_profile("test_tool")
        
        # Record some executions
        start_time = asyncio.get_event_loop().time()
        profile.record_execution(
            start_time=start_time,
            duration_ms=100.0,
            input_json='{"test": "input"}',
            output="test output",
            error=None,
        )
        
        print(f"✓ Recorded execution in profile")
        
        # Get summary
        summary = profile.get_profile_summary()
        assert summary["execution_count"] == 1
        assert summary["error_count"] == 0
        print(f"✓ Profile summary correct: {summary['execution_count']} executions")
        
        # Test global summary
        all_profiles = ExecutionProfiler.get_all_profiles_summary()
        assert "test_tool" in all_profiles
        print(f"✓ Global profile summary contains test_tool")
        
        return True
    except Exception as e:
        print(f"✗ Execution profiling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_state_tracking():
    """Test state tracking functionality."""
    print("\n" + "=" * 80)
    print("TEST 6: State Tracking")
    print("=" * 80)
    
    try:
        from agents.mcp.forensics import ForensicStateTracker, ServerState
        
        tracker = ForensicStateTracker("test_server")
        
        # Transition through states
        await tracker.transition(
            ServerState.CONNECTING,
            "test_trigger",
            {"metadata": "test"},
        )
        assert tracker.current_state == ServerState.CONNECTING
        print(f"✓ Transitioned to CONNECTING")
        
        await tracker.transition(
            ServerState.CONNECTED,
            "connection_established",
            {"metadata": "test"},
        )
        assert tracker.current_state == ServerState.CONNECTED
        print(f"✓ Transitioned to CONNECTED")
        
        # Get summary
        summary = tracker.get_state_summary()
        assert summary["current_state"] == "connected"
        assert summary["total_transitions"] == 2
        print(f"✓ State summary correct: {summary['total_transitions']} transitions")
        
        return True
    except Exception as e:
        print(f"✗ State tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_archive():
    """Test archive functionality."""
    print("\n" + "=" * 80)
    print("TEST 7: Archive System")
    print("=" * 80)
    
    try:
        from agents.mcp.forensics import ForensicArchive
        
        archive = ForensicArchive(max_entries=100)
        
        # Archive some operations
        for i in range(5):
            await archive.archive_operation(
                operation_type=f"test_op_{i}",
                server_name="test_server",
                tool_name="test_tool",
                request_data={"arg": i},
                response_data={"result": f"value_{i}"},
                metadata={"test": True},
            )
        
        print(f"✓ Archived 5 operations")
        
        # Get summary
        summary = archive.get_archive_summary()
        assert summary["total_entries"] == 5
        print(f"✓ Archive summary correct: {summary['total_entries']} entries")
        
        return True
    except Exception as e:
        print(f"✗ Archive test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_forensics():
    """Test error forensics functionality."""
    print("\n" + "=" * 80)
    print("TEST 8: Error Forensics")
    print("=" * 80)
    
    try:
        from agents.mcp.forensics import ErrorForensics
        
        tracker = ErrorForensics("test_server", max_errors=100)
        
        # Record some errors
        for i in range(3):
            error = ValueError(f"Test error {i}")
            await tracker.record_error(
                error=error,
                context={"operation": "test_op", "attempt": i},
                stack_trace="test stack trace",
            )
        
        print(f"✓ Recorded 3 errors")
        
        # Get summary
        summary = tracker.get_error_summary()
        assert summary["total_errors"] == 3
        print(f"✓ Error summary correct: {summary['total_errors']} errors")
        
        return True
    except Exception as e:
        print(f"✗ Error forensics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_export_functions():
    """Test export functionality."""
    print("\n" + "=" * 80)
    print("TEST 9: Export Functions")
    print("=" * 80)
    
    try:
        from agents.mcp import (
            get_global_forensic_summary,
            get_tool_execution_profiles,
        )
        
        # Test global summary
        global_summary = get_global_forensic_summary()
        assert "enabled" in global_summary
        print(f"✓ get_global_forensic_summary() works")
        
        # Test tool profiles
        tool_profiles = get_tool_execution_profiles()
        assert isinstance(tool_profiles, dict)
        print(f"✓ get_tool_execution_profiles() works")
        
        return True
    except Exception as e:
        print(f"✗ Export functions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all validation tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "JARVIS 2.0 - FORENSICS VALIDATION" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Enable/Disable", test_enable_disable),
        ("Class Instantiation", test_forensic_classes),
        ("Audit Tracking", test_audit_tracking),
        ("Execution Profiling", test_execution_profiling),
        ("State Tracking", test_state_tracking),
        ("Archive System", test_archive),
        ("Error Forensics", test_error_forensics),
        ("Export Functions", test_export_functions),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print("=" * 80)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 80)
    
    if passed == total:
        print()
        print("🎉 ALL TESTS PASSED - FORENSICS SYSTEM OPERATIONAL")
        print()
        print("Next steps:")
        print("  1. Review documentation: docs/mcp_forensics.md")
        print("  2. Try the example: examples/mcp/forensic_analysis_example.py")
        print("  3. Check quick reference: FORENSICS_QUICK_REFERENCE.md")
        print()
        return 0
    else:
        print()
        print("⚠ SOME TESTS FAILED - REVIEW OUTPUT ABOVE")
        print()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

